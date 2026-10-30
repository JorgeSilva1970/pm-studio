"""Generative agent (Claude API, Anthropic) specialised in Project Cycle Management.

Set ANTHROPIC_API_KEY (and optionally ANTHROPIC_MODEL) as environment variables (Render → Environment)."""
from __future__ import annotations

import json
import os
import re

from . import analysis as AN
from . import finance as F
from . import schedule as S
from .i18n import OPTIONS, get_lang
from .model import TABLES, _coerce_row, empty_row, ensure_ids, normalize

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MODELS = ["claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-5-5"]


def api_key() -> str | None:
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        return None


def available() -> bool:
    return bool(api_key())


def _client():
    import anthropic
    return anthropic.Anthropic(api_key=api_key())


METHOD = """You are an expert project manager and evaluator who coaches students and practitioners in Project Cycle Management (PCM).
Ground your advice in: EuropeAid PCM Guidelines (2004) and the Logical Framework Approach; the European Commission PM² methodology (2016);
Hivos Theory of Change guidelines (2015); Morra Imas & Rist, The Road to Results (World Bank, 2009); EC DG INTPA Evaluation Handbook (2025); PMBOK.
Key rules used in this course:
- Project design is top-down: the impact is a contribution to a Government/sponsor strategic goal; impact indicators come from that strategy.
- Stakeholder analysis has 4 layers: basic characteristics; how interests are affected (someone benefits from the problem); capacity & motivation to change; possible actions. Target group ⊂ beneficiaries ⊂ stakeholders.
- Behavioural patterns of the target group: perception, opportunity, ability, motivation (between outputs and outcomes).
- Problem tree: core problem in the middle, causes below, effects above; objective tree turns causes into means (outputs), core problem into outcome, effects into ends (impact).
- Vertical logic: Inputs (4 Ms: materials, machinery, manpower, money) → Activities → Outputs (full control) → Outcomes (direct influence) → Impact (indirect influence).
- Diagonal logic: OUTPUTS = ACTIVITIES + OPERATIONAL ASSUMPTIONS; OUTCOMES = OUTPUTS + BEHAVIOURAL ASSUMPTIONS; IMPACTS = OUTCOMES + POLITICAL ASSUMPTIONS. Assumptions are positive statements backed by evidence (political ← policy analysis; behavioural ← target-group patterns; operational ← lessons learned). PCM flowchart: important? will it hold? almost certainly → leave out; possibly → include; unlikely → redesign or killer assumption.
- Risks are negative statements; exposure = likelihood (1-4) × impact (1-4); likelihood depends on evidence quality; impact depends on the vertical-logic level affected. Preventive measures become support activities.
- Horizontal logic: indicators (neutral wording), baseline, target, sources of verification. Indicators must be SMART (Specific, Measurable, Available at reasonable cost, Relevant, Timely) and CREAM. No baseline → no target. Targets must be evidence-based (benchmarking with peers, top performers, time series).
- Efficiency ← input/output indicators; Effectiveness ← outcome; Impact & Sustainability ← impact; Relevance ← alignment with strategic goals.
- Activities: production (per output) and support (communication, M&E, events, management, risk prevention). CPM/PERT: tₑ=(a+4m+b)/6, σ²=((b−a)/6)², critical path = zero total float.
- Budget by activity and cost category, per phase (inception, implementation, completion), time-phased cash flow; contingency budget; procurement plan (competitive bidding, RFP, RFQ, sole sourcing, framework agreements).
- Finance: WACC, NPV, IRR, MIRR (prefer MIRR when IRR is unreliable), payback. Earned Value: PV, EV, AC, CV, SV, CPI, SPI, EAC, ETC, VAC, TCPI.
Be precise, structured, practical and honest about weaknesses. Never invent statistics presented as real facts: when you suggest figures (baselines, peers, costs), label them clearly as illustrative estimates to be validated."""


def _lang_instr() -> str:
    return "Answer in European Portuguese (pt-PT)." if get_lang() == "pt" else "Answer in English."


def project_context(p: dict, max_chars: int = 60000) -> str:
    sched = S.compute(p)
    ctx = {"meta": p["meta"], "policy": p["policy"], "policy_goals": p["policy_goals"], "stakeholders": p["stakeholders"],
           "behaviour": p["behaviour"], "problems": p["problems"], "strategies": p["strategies"], "objectives": p["objectives"],
           "indicators": p["indicators"], "assumptions": p["assumptions"], "toc": p["toc"], "activities": p["activities"],
           "risks": p["risks"], "procurement": p["procurement"], "cashflows": p["cashflows"]}
    if sched.get("ok"):
        e = S.evm(p, sched)
        ctx["computed"] = {"duration": sched["cpm"]["duration"], "time_unit": sched["unit"], "critical_path": sched["cpm"]["critical_path"],
                           "finish": str(sched["finish"]), "BAC": sched["bac"], "contingency": sched["contingency"],
                           "EVM": {k: (round(v, 4) if isinstance(v, float) else str(v)) for k, v in e.items() if k != "table"}}
    fa = F.analyse(p.get("cashflows", []), p["finance"], float(p["finance"].get("residual_value") or 0))
    if fa:
        ctx.setdefault("computed", {})["finance"] = {"rate": fa["rate"], "npv": fa["npv"], "irr": fa["irr"], "mirr": fa["mirr"], "payback": fa["payback"]}
    s = json.dumps(ctx, ensure_ascii=False, default=str)
    return s[:max_chars]


def schema_text(tables: list[str]) -> str:
    lines = []
    for t in tables:
        cols = []
        for f, kind, _d in TABLES[t]:
            if kind.startswith("sel:"):
                codes = [str(o[0]) for o in OPTIONS[kind[4:]]]
                cols.append(f'{f} (one of: {" | ".join(codes)})')
            elif kind in ("scale5",):
                cols.append(f"{f} (integer 1-5)")
            elif kind == "scale4":
                cols.append(f"{f} (integer 1-4)")
            else:
                cols.append(f"{f} ({kind})")
        lines.append(f"- {t}: list of objects with fields: " + ", ".join(cols))
    return "\n".join(lines)


GEN_TABLES = ["policy_goals", "stakeholders", "behaviour", "problems", "objectives", "indicators", "benchmarks", "assumptions",
              "activities", "risks", "budget", "procurement", "evaluation", "preconditions"]


def _extract_json(text: str) -> dict:
    m = re.search(r"<json>(.*?)</json>", text, re.S) or re.search(r"```json\s*(.*?)```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(raw)


def _call(system: str, user: str, model: str | None = None, max_tokens: int = 8000) -> str:
    cl = _client()
    with cl.messages.stream(model=model or DEFAULT_MODEL, max_tokens=max_tokens, system=system,
                            messages=[{"role": "user", "content": user}]) as stream:
        msg = stream.get_final_message()
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def chat_stream(history: list[dict], p: dict, model: str | None = None):
    """Yield text chunks for the chat assistant."""
    system = METHOD + "\n" + _lang_instr() + "\n\nCurrent project (JSON):\n" + project_context(p)
    cl = _client()
    with cl.messages.stream(model=model or DEFAULT_MODEL, max_tokens=4000, system=system, messages=history) as stream:
        for t in stream.text_stream:
            yield t


def generate(description: str, p: dict, tables: list[str] | None = None, model: str | None = None, source_text: str | None = None) -> dict:
    """Draft (or extract from a document) the requested modules. Returns a dict {table: rows, meta?, policy?, toc?}."""
    tables = tables or GEN_TABLES
    lang = "European Portuguese (pt-PT)" if get_lang() == "pt" else "English"
    sys = METHOD + f"\nWrite all free-text content in {lang}. Keep enumerated codes exactly as specified (they are English codes)."
    doc_block = ("DOCUMENT:\n" + source_text[:60000]) if source_text else ""
    user = f"""Task: {"extract from the document below" if source_text else "design a complete, coherent draft"} the following project modules.
Project description / instructions from the user:
{description}

{doc_block}

Existing project context (may be empty; keep consistent with it where useful):
{project_context(p, 20000)}

Return ONLY a JSON object inside <json></json> tags with these optional keys:
- meta: object with name, industry, organisation, sponsor, country, description, time_unit (days|weeks|months), start_date (YYYY-MM-DD)
- policy: object with context, content, consequences
- toc: object with vision, context, actors, strategic_choices, learning
{schema_text(tables)}

Rules: ids are short (S1.., P1.., I1.., H1.., A1.., R1.., Q1..). Objectives use codes IMP (Impact), OC1, OC2 (Outcome), 1.1, 1.2, 2.1 (Output) with 'parent' pointing to the upper level.
Problem 'parent' = id(s) of the upper level (comma separated); levels Effect/Core problem/Cause. Activities: production activities grouped by output (output_code) plus support activities;
predecessors as comma-separated ids forming a valid acyclic network; optimistic ≤ most_likely ≤ pessimistic in {p['meta'].get('time_unit', 'weeks')}; realistic costs in {p['meta'].get('currency', 'EUR')}.
Assumptions: objective_code is the objective the assumption conditions (Output→Operational, Outcome→Behavioural, Impact→Political). Risks link to assumption_id where relevant.
Indicators: neutral wording, numeric baseline/target, years, sources of verification; benchmarks give 3-4 illustrative peers for key indicators.
Only include the keys requested; omit keys you cannot fill."""
    text = _call(sys, user, model, max_tokens=16000)
    return _extract_json(text)


def apply(p: dict, data: dict, mode: str = "replace") -> list[str]:
    """Merge agent output into the project. mode: replace (per table) | append."""
    done = []
    for k in ("meta", "policy", "toc"):
        if isinstance(data.get(k), dict):
            p[k].update({kk: vv for kk, vv in data[k].items() if vv not in (None, "")})
            done.append(k)
    for t in TABLES:
        if t in data and isinstance(data[t], list):
            rows = []
            for r in data[t]:
                if not isinstance(r, dict):
                    continue
                x = empty_row(t)
                x.update({kk: vv for kk, vv in r.items() if kk in x})
                rows.append(_coerce_row(t, x))
            p[t] = ensure_ids(rows if mode == "replace" else p[t] + rows, t)
            done.append(f"{t} ({len(rows)})")
    np_ = normalize(p)
    p.clear()
    p.update(np_)
    return done


def review(p: dict, model: str | None = None) -> str:
    sys = METHOD + "\n" + _lang_instr()
    user = ("Review this project critically as a demanding PCM evaluator. Structure the answer with headings: 1) Vertical logic, 2) Diagonal logic (assumptions & risks), "
            "3) Horizontal logic (SMART indicators, baselines, evidence-based targets), 4) Stakeholders & behaviour, 5) Planning (CPM/PERT, budget, contingency, procurement), "
            "6) Financial feasibility, 7) Top 10 concrete improvements (prioritised). Quote ids/codes.\n\nPROJECT:\n" + project_context(p))
    return _call(sys, user, model, 6000)


def synthesis(p: dict, model: str | None = None) -> str:
    sys = METHOD + "\n" + _lang_instr()
    user = ("Write an interpretive executive synthesis (max ~450 words) of this project for decision makers: relevance, feasibility (schedule, budget, risks, NPV/IRR/MIRR) and effectiveness (EVM, indicators), "
            "ending with 3-5 recommendations. Plain paragraphs, use **bold** for key numbers.\n\nPROJECT:\n" + project_context(p))
    return _call(sys, user, model, 3000)


def suggest_indicators(p: dict, model: str | None = None) -> dict:
    return generate("Propose SMART indicators (2 per objective at most) with baselines, targets, years, sources of verification and illustrative benchmarks for every objective without indicators."
                    if get_lang() == "pt" else "Propose SMART indicators for every objective without indicators.", p, ["indicators", "benchmarks"], model)


def docx_text(file) -> str:
    import docx
    d = docx.Document(file)
    parts = [para.text for para in d.paragraphs if para.text.strip()]
    for t in d.tables:
        for row in t.rows:
            parts.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n".join(parts)


def pdf_text(file, max_pages: int = 40) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    r = PdfReader(file)
    return "\n".join((pg.extract_text() or "") for pg in r.pages[:max_pages])
