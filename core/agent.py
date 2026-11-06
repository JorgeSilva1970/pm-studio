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
EFFORT = os.environ.get("ANTHROPIC_EFFORT", "medium")  # low | medium | high — controls reasoning length/latency


def _extra():
    return {"extra_body": {"output_config": {"effort": EFFORT}}} if EFFORT else {}


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
                            messages=[{"role": "user", "content": user}], **_extra()) as stream:
        msg = stream.get_final_message()
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    if not text.strip():
        raise RuntimeError("O agente não devolveu texto (limite de tokens atingido durante o raciocínio). Tente de novo. / "
                           f"The agent returned no text (token limit reached while reasoning). Try again. [{msg.stop_reason}]")
    return text


def _tool_schema(tables: list[str]) -> dict:
    """JSON schema of the structured draft (forces valid, typed output)."""
    def col(kind):
        if kind.startswith("sel:"):
            return {"type": "string", "enum": [str(o[0]) for o in OPTIONS[kind[4:]]]}
        if kind in ("num",):
            return {"type": "number"}
        if kind in ("int", "scale5", "scale4"):
            return {"type": "integer"}
        if kind == "bool":
            return {"type": "boolean"}
        return {"type": "string"}
    props = {
        "meta": {"type": "object", "properties": {k: {"type": "string"} for k in
                 ("name", "industry", "organisation", "sponsor", "country", "description", "time_unit", "start_date")}},
        "policy": {"type": "object", "properties": {k: {"type": "string"} for k in ("context", "content", "consequences")}},
        "toc": {"type": "object", "properties": {k: {"type": "string"} for k in ("vision", "context", "actors", "strategic_choices", "learning")}},
    }
    for t in tables:
        props[t] = {"type": "array", "items": {"type": "object", "properties": {f: col(k) for f, k, _d in TABLES[t]}}}
    return {"type": "object", "properties": props}


def _call_tool(system: str, user: str, tables: list[str], model: str | None = None, max_tokens: int = 32000, schema_keys=None) -> dict:
    cl = _client()
    schema = _tool_schema(tables)
    if schema_keys is not None:
        schema["properties"] = {k: v for k, v in schema["properties"].items() if k in schema_keys}
    tool = {"name": "save_project_draft", "description": "Save the structured project draft (all requested modules).",
            "input_schema": schema}
    with cl.messages.stream(model=model or DEFAULT_MODEL, max_tokens=max_tokens, system=system, tools=[tool],
                            tool_choice={"type": "auto"},
                            messages=[{"role": "user", "content": user}], **_extra()) as stream:
        msg = stream.get_final_message()
    for b in msg.content:
        if getattr(b, "type", "") == "tool_use":
            data = b.input if isinstance(b.input, dict) else json.loads(b.input)
            if msg.stop_reason == "max_tokens":
                raise RuntimeError("A resposta do agente ficou incompleta (limite de tamanho). Gere menos módulos de cada vez. / "
                                   "The agent's answer was cut off (size limit). Generate fewer modules at a time.")
            return data
    text = "".join(getattr(b, "text", "") for b in msg.content)
    try:
        return _extract_json(text)
    except Exception:
        raise RuntimeError(("O agente não devolveu um rascunho estruturado. Tente de novo ou com menos módulos. / "
                            "The agent did not return a structured draft. Try again or with fewer modules.") + f" [{msg.stop_reason}] {text[:300]}")


def chat_stream(history: list[dict], p: dict, model: str | None = None):
    """Yield text chunks for the chat assistant."""
    system = METHOD + "\n" + _lang_instr() + "\n\nCurrent project (JSON):\n" + project_context(p)
    cl = _client()
    with cl.messages.stream(model=model or DEFAULT_MODEL, max_tokens=12000, system=system, messages=history, **_extra()) as stream:
        for t in stream.text_stream:
            yield t


GEN_STAGES = [
    ["policy_goals", "stakeholders", "behaviour", "problems"],
    ["objectives", "indicators", "benchmarks", "assumptions", "preconditions"],
    ["activities", "budget", "procurement"],
    ["risks", "evaluation"],
]
MAX_ROWS = {"policy_goals": 3, "stakeholders": 8, "behaviour": 3, "problems": 10, "objectives": 8, "indicators": 8, "benchmarks": 10,
            "assumptions": 6, "preconditions": 3, "activities": 14, "budget": 10, "procurement": 4, "risks": 7, "evaluation": 5}


def generate(description: str, p: dict, tables: list[str] | None = None, model: str | None = None, source_text: str | None = None,
             progress=None, with_meta: bool = True) -> dict:
    """Draft (or extract from a document) the requested modules, in chained stages so each answer stays within
    the output limit. Returns {table: rows, meta?, policy?, toc?}. `progress(i, n, tables)` is called before each stage."""
    tables = tables or GEN_TABLES
    stages = [[t for t in st if t in tables] for st in GEN_STAGES]
    rest = [t for t in tables if not any(t in st for st in GEN_STAGES)]
    stages = [st for st in stages if st] + ([rest] if rest else [])
    want_meta = with_meta and "Do not return meta/policy/toc" not in description
    out: dict = {}
    for i, st in enumerate(stages):
        if progress:
            progress(i, len(stages), st)
        data = _generate_stage(description, p, st, model, source_text, out, with_meta=(i == 0 and want_meta))
        for k, v in data.items():
            if k in ("meta", "policy", "toc") and not (i == 0 and want_meta):
                continue
            if k in st or k in ("meta", "policy", "toc"):
                out[k] = v
    return out


def _generate_stage(description, p, tables, model, source_text, draft, with_meta):
    lang = "European Portuguese (pt-PT)" if get_lang() == "pt" else "English"
    sys = METHOD + f"\nWrite all free-text content in {lang}. Keep enumerated codes exactly as specified (they are English codes). Be concise: short sentences in text fields."
    doc_block = ("DOCUMENT:\n" + source_text[:60000]) if source_text else ""
    limits = ", ".join(f"{t} ≤ {MAX_ROWS.get(t, 10)} rows" for t in tables)
    meta_block = ("- meta: object with name, industry, organisation, sponsor, country, description, time_unit (days|weeks|months), start_date (YYYY-MM-DD)\n"
                  "- policy: object with context, content, consequences\n- toc: object with vision, context, actors, strategic_choices, learning\n") if with_meta else ""
    user = f"""Task: {"extract from the document below" if source_text else "design a coherent draft of"} the following project modules: {", ".join(tables)}.
Project description / instructions from the user:
{description}

{doc_block}

Draft already produced in previous steps (stay fully consistent with its ids and codes):
{json.dumps(draft, ensure_ascii=False)[:30000] if draft else "(none)"}

Existing project context (may be empty):
{project_context(p, 12000)}

Call the tool `save_project_draft` once with these keys:
{meta_block}{schema_text(tables)}

Size limits: {limits}.
Rules: ids are short (S1.., P1.., I1.., H1.., A1.., R1.., Q1..). Objectives use codes IMP (Impact), OC1, OC2 (Outcome), 1.1, 1.2, 2.1 (Output) with 'parent' pointing to the upper level.
Problem 'parent' = id(s) of the upper level (comma separated); levels Effect/Core problem/Cause. Activities: production activities grouped by output (output_code) plus support activities;
predecessors as comma-separated ids forming a valid acyclic network; optimistic ≤ most_likely ≤ pessimistic in {p['meta'].get('time_unit', 'weeks')}; realistic costs in {p['meta'].get('currency', 'EUR')}.
Assumptions: objective_code is the objective the assumption conditions (Output→Operational, Outcome→Behavioural, Impact→Political). Risks link to assumption_id where relevant.
Indicators: neutral wording, numeric baseline/target, years, sources of verification; benchmarks give 3-4 illustrative peers for key indicators.
Do not ask questions and do not answer in prose: make reasonable assumptions and call the tool `save_project_draft` exactly once."""
    keys = tables + (["meta", "policy", "toc"] if with_meta else [])
    return _call_tool(sys, user, tables, model, schema_keys=keys)


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
    _fix_refs(p)
    np_ = normalize(p)
    p.clear()
    p.update(np_)
    return done


def _fix_refs(p: dict) -> None:
    """Keep only valid ids in reference fields (the model sometimes writes 'A3 – description' or a wrong prefix)."""
    def pick(value, valid, multi=False):
        toks = re.findall(r"[A-Za-z]*\d+(?:\.\d+)*|IMP|OC\d+", str(value or ""))
        good = [t for t in toks if t in valid]
        return ", ".join(dict.fromkeys(good)) if multi else (good[0] if good else "")
    acts = {str(a.get("id")) for a in p.get("activities", [])}
    asm = {str(h.get("id")) for h in p.get("assumptions", [])}
    objs = {str(o.get("code")) for o in p.get("objectives", [])}
    probs = {str(x.get("id")) for x in p.get("problems", [])}
    inds = {str(i.get("id")) for i in p.get("indicators", [])}
    for r in p.get("risks", []):
        r["preventive_activity"] = pick(r.get("preventive_activity"), acts)
        r["assumption_id"] = pick(r.get("assumption_id"), asm)
    for t in ("budget", "procurement"):
        for r in p.get(t, []):
            r["activity_id"] = pick(r.get("activity_id"), acts)
    for a in p.get("activities", []):
        a["predecessors"] = pick(a.get("predecessors"), acts - {str(a.get("id"))}, multi=True)
        if a.get("output_code") and str(a["output_code"]) not in objs:
            a["output_code"] = pick(a.get("output_code"), objs)
        for k in ("crash_duration", "crash_cost"):
            if not a.get(k):
                a[k] = None
    for h in p.get("assumptions", []):
        h["objective_code"] = pick(h.get("objective_code"), objs) or h.get("objective_code", "")
    for o in p.get("objectives", []):
        o["parent"] = pick(o.get("parent"), objs - {str(o.get("code"))})
    for x in p.get("problems", []):
        x["parent"] = pick(x.get("parent"), probs - {str(x.get("id"))}, multi=True)
    for t in ("benchmarks", "timeseries"):
        for r in p.get(t, []):
            if str(r.get("indicator_id")) not in inds:
                r["indicator_id"] = pick(r.get("indicator_id"), inds)


def review(p: dict, model: str | None = None) -> str:
    sys = METHOD + "\n" + _lang_instr()
    user = ("Review this project critically as a demanding PCM evaluator. Structure the answer with headings: 1) Vertical logic, 2) Diagonal logic (assumptions & risks), "
            "3) Horizontal logic (SMART indicators, baselines, evidence-based targets), 4) Stakeholders & behaviour, 5) Planning (CPM/PERT, budget, contingency, procurement), "
            "6) Financial feasibility, 7) Top 10 concrete improvements (prioritised). Quote ids/codes.\n\nPROJECT:\n" + project_context(p))
    return _call(sys, user, model, 24000)


def synthesis(p: dict, model: str | None = None) -> str:
    sys = METHOD + "\n" + _lang_instr()
    user = ("Write an interpretive executive synthesis (max ~450 words) of this project for decision makers: relevance, feasibility (schedule, budget, risks, NPV/IRR/MIRR) and effectiveness (EVM, indicators), "
            "ending with 3-5 recommendations. Plain paragraphs, use **bold** for key numbers.\n\nPROJECT:\n" + project_context(p))
    return _call(sys, user, model, 12000)


def suggest_indicators(p: dict, model: str | None = None) -> dict:
    return generate("Propose SMART indicators (2 per objective at most) with baselines, targets, years, sources of verification and illustrative benchmarks for every objective without indicators."
                    if get_lang() == "pt" else "Propose SMART indicators for every objective without indicators.", p, ["indicators", "benchmarks"], model, with_meta=False)


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
