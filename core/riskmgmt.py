"""Risk management following the professor's 'Monitoring Tools' slides (assumptions → risks):

* Risk management matrix (slide 10): Risk | Potential adverse impact | Level | Strategy | Responsible | Internal/External.
  The assumption type gives the adverse impact (logframe row), the suggested responsible and the scope:
  Political → Outcome · PMT + Sponsor · External; Behavioural → Outputs · PMT + Target group + Stakeholders · External;
  Operational → Activities · PMT · Internal.
* Suggested impact (risk classification slide): consequence grows with the level hit —
  Activity (low) < activity on the critical path (medium-low) < Output (medium-high) < Outcome/Impact (high).
  The likelihood keeps coming from the evidence of the assumption.
* Corrective actions triggered 'if and when' the risk materialises; contingency = cost of the risk management strategies.
* Risk threshold (5% / 10% / 15% of the budget): the organisation's sensitivity to risk; above it the project may not be feasible.
"""
from __future__ import annotations

import html

from . import schedule as S
from . import wbs as W
from .analysis import exposure, risk_color, risk_level
from .fmt import money, pct
from .i18n import opt_label, tr
from .model import MATRIX_ROW_OF_ASSUMPTION, adverse_level, objective_level

LEVEL_TO_TYPE = {"Activity": "Operational", "Input": "Operational", "Output": "Behavioural", "Outcome": "Political", "Impact": "Political"}
SCOPE = {  # assumption type → (internal?, responsible pt/en, abbreviation)
    "Political": (False, ("Equipa de gestão + Patrocinador", "Project management team + Sponsor"), "PMT + Sponsor"),
    "Behavioural": (False, ("Equipa de gestão + Grupo-alvo + Stakeholders", "Project management team + Target group + Stakeholders"), "PMT + TG + STK"),
    "Operational": (True, ("Equipa de gestão do projeto", "Project management team"), "PMT"),
}
THRESHOLDS = [0.05, 0.10, 0.15]
IMPACT_BY_LEVEL = {"Input": 1, "Activity": 1, "Output": 3, "Outcome": 4, "Impact": 4}


# ----------------------------------------------------------------------------- classification
def risk_assumption(p: dict, r: dict) -> dict | None:
    aid = str(r.get("assumption_id") or "").strip()
    return next((h for h in p.get("assumptions", []) if str(h.get("id")) == aid), None) if aid else None


def risk_kind(p: dict, r: dict) -> str:
    """Assumption type behind the risk (from the linked assumption, otherwise from the level affected)."""
    h = risk_assumption(p, r)
    if h and h.get("type") in SCOPE:
        return h["type"]
    return LEVEL_TO_TYPE.get(r.get("level_affected") or "Output", "Behavioural")


def risk_scope(p: dict, r: dict) -> dict:
    k = risk_kind(p, r)
    internal, resp, short = SCOPE[k]
    return {"kind": k, "internal": internal, "scope": tr("Interno", "Internal") if internal else tr("Externo", "External"),
            "responsible": tr(*resp), "short": short}


def floats(p: dict, sched: dict | None = None) -> dict:
    """{activity id: total float} from the CPM (critical = zero float)."""
    sched = sched or S.compute(p)
    if not sched.get("ok"):
        return {}
    return {str(r["id"]): float(r["TF"]) for r in sched["acts"].to_dict("records")}


def risk_activities(p: dict, r: dict) -> list:
    """Activities hit by the risk: those under its WBS element and, for an operational assumption, those producing the output it conditions."""
    ids = []
    code = str(r.get("wbs_code") or "").strip()
    if code:
        ids += [str(a["id"]) for a in p.get("activities", []) if a.get("wbs_code") and W.is_under(str(a["wbs_code"]), code)]
    h = risk_assumption(p, r)
    if h and (r.get("level_affected") or "") == "Activity":
        oc = str(h.get("objective_code") or "")
        ids += [str(a["id"]) for a in p.get("activities", []) if str(a.get("output_code") or "") == oc]
    return list(dict.fromkeys(ids))


def suggested_impact(p: dict, r: dict, tf: dict | None = None) -> tuple[int, str]:
    """(impact 1-4, reason). Activity 1 · activity on the critical path 2 · Output 3 · Outcome/Impact 4."""
    lvl = r.get("level_affected") or "Output"
    lab = opt_label("level", lvl)
    if lvl != "Activity":
        v = IMPACT_BY_LEVEL.get(lvl, 3)
        return v, tr(f"afeta {lab} → {opt_label('impact', v)}", f"hits {lab} → {opt_label('impact', v)}")
    tf = floats(p) if tf is None else tf
    acts = risk_activities(p, r)
    on_cp = [a for a in acts if a in tf and tf[a] <= 1e-9]
    if on_cp:
        return 2, tr(f"atividade(s) {', '.join(on_cp)} no caminho crítico (folga 0) → {opt_label('impact', 2)}",
                     f"activity(ies) {', '.join(on_cp)} on the critical path (zero float) → {opt_label('impact', 2)}")
    if acts:
        known = [tf[a] for a in acts if a in tf]
        m = min(known) if known else 0
        unit = tr(*{"days": ("dias", "days"), "weeks": ("semanas", "weeks"), "months": ("meses", "months")}.get(p["meta"].get("time_unit", "weeks"), ("", "")))
        mn = f"{m:.1f}".replace(".", "," if tr("pt", "en") == "pt" else ".")
        return 1, tr(f"atividade(s) {', '.join(acts)} com folga (mínima {mn} {unit}) → {opt_label('impact', 1)}",
                     f"activity(ies) {', '.join(acts)} with float (minimum {mn} {unit}) → {opt_label('impact', 1)}")
    return 1, tr("atividades sem ligação (associa o risco a um elemento da WBS para avaliar o caminho crítico) → " + opt_label("impact", 1),
                 "no linked activities (link the risk to a WBS element to assess the critical path) → " + opt_label("impact", 1))


def suggestions(p: dict) -> list[dict]:
    tf = floats(p)
    out = []
    for r in p.get("risks", []):
        v, why = suggested_impact(p, r, tf)
        out.append({"id": r["id"], "current": int(r.get("impact") or 0), "suggested": v, "why": why})
    return out


# ----------------------------------------------------------------------------- diagonal logic sentence
def if_then(p: dict, h: dict) -> str:
    """'If … and … then …' (vertical logic = theory of action; the assumption = diagonal logic)."""
    code = str(h.get("objective_code") or "")
    lvl = objective_level(p, code)
    obj = next((o for o in p.get("objectives", []) if str(o.get("code")) == code), None)
    target = f"{code} – {obj.get('text', '')}" if obj else code or "…"
    cond = h.get("text") or "…"
    row = MATRIX_ROW_OF_ASSUMPTION.get(lvl) or adverse_level(p, h)
    if row == "Activity":
        return tr(f"**Se** realizarmos as atividades **e** se confirmar que «{cond}», **então** entregamos o output {target}.",
                  f"**If** we perform the activities **and** «{cond}» holds, **then** we deliver output {target}.")
    if row == "Output":
        return tr(f"**Se** produzirmos os outputs **e** se confirmar que «{cond}», **então** alcançamos o outcome {target}.",
                  f"**If** we produce the outputs **and** «{cond}» holds, **then** we achieve outcome {target}.")
    return tr(f"**Se** alcançarmos o outcome **e** se confirmar que «{cond}», **então** contribuímos para o impacto {target}.",
              f"**If** we achieve the outcome **and** «{cond}» holds, **then** we contribute to impact {target}.")


def risk_if_then(p: dict, r: dict) -> str:
    h = risk_assumption(p, r)
    return if_then(p, h) if h else ""


# ----------------------------------------------------------------------------- matrix
def matrix_rows(p: dict) -> list[dict]:
    rows = []
    for r in sorted(p.get("risks", []), key=lambda r: (-exposure(r), str(r.get("id")))):
        sc = risk_scope(p, r)
        e = exposure(r)
        prev = (r.get("proposed_mitigation") or "").strip()
        if r.get("preventive_activity") and str(r["preventive_activity"]) not in prev:
            prev = (prev + " " if prev else "") + tr(f"(atividade {r['preventive_activity']})", f"(activity {r['preventive_activity']})")
        corr = (r.get("corrective_action") or "").strip()
        if r.get("trigger"):
            corr = (corr + " — " if corr else "") + tr("se e quando ", "if and when ") + str(r["trigger"]).strip()
        rows.append({"id": r["id"], "risk": r.get("description", ""), "kind": sc["kind"], "adverse": r.get("level_affected") or "Output",
                     "L": int(r.get("likelihood") or 0), "I": int(r.get("impact") or 0), "E": e, "level": risk_level(e), "color": risk_color(e),
                     "strategy": opt_label("risk_strategy", r.get("strategy")), "preventive": prev, "corrective": corr,
                     "cost": float(r.get("contingency") or 0), "responsible_sugg": sc["responsible"], "short": sc["short"],
                     "owner": r.get("risk_owner") or r.get("risk_manager") or "", "scope": sc["scope"], "internal": sc["internal"],
                     "if_then": risk_if_then(p, r)})
    return rows


def matrix_html(p: dict) -> str:
    """Risk management matrix in the professor's 5-column format (+ internal/external), for the page, the report and PNG export."""
    cur = p["meta"].get("currency", "EUR")
    hdr = [tr("Risco", "Risk"), tr("Impacto adverso potencial", "Potential adverse impact"), tr("Nível", "Level"),
           tr("Estratégia de gestão do risco", "Risk management strategy"), tr("Responsável", "Responsible"), tr("Âmbito", "Scope")]
    th = "".join(f"<th style='background:#13A3B5;color:#fff;padding:8px;border-radius:6px;font-size:14px'>{h}</th>" for h in hdr)
    kind_lab = {"Political": tr("Político (P)", "Political (P)"), "Behavioural": tr("Comportamental (B)", "Behavioural (B)"), "Operational": tr("Operacional (OP)", "Operational (OP)")}
    body = []
    for x in matrix_rows(p):
        strat = f"<b>{html.escape(x['strategy'])}</b>"
        if x["preventive"]:
            strat += f"<br><span style='color:#1E8449'>▲ {tr('Preventiva', 'Preventive')}:</span> {html.escape(x['preventive'])}"
        if x["corrective"]:
            strat += f"<br><span style='color:#B03A2E'>▼ {tr('Corretiva', 'Corrective')}:</span> {html.escape(x['corrective'])}"
        if x["cost"]:
            strat += f"<br><span style='color:#555'>{tr('Custo (contingência)', 'Cost (contingency)')}: {money(x['cost'], cur)}</span>"
        resp = f"{html.escape(x['owner'])}<br><span style='color:#777;font-size:12px'>{tr('Sugerido', 'Suggested')}: {html.escape(x['responsible_sugg'])}</span>" if x["owner"] \
            else html.escape(x["responsible_sugg"])
        td = "padding:7px;border:1px dotted #13A3B5;vertical-align:top;font-size:13px"
        body.append(f"<tr><td style='{td}'><b>{html.escape(str(x['id']))}</b> · {kind_lab[x['kind']]}<br>{html.escape(x['risk'])}</td>"
                    f"<td style='{td}' title='{html.escape(x['if_then'].replace('**', ''), quote=True)}'>{html.escape(opt_label('level', x['adverse']))}"
                    + (f"<br><span style='color:#777;font-size:11.5px'>{html.escape(x['if_then'].replace('**', ''))}</span>" if x["if_then"] else "") + "</td>"
                    f"<td style='{td};text-align:center'><span style='background:{x['color']};color:#fff;border-radius:4px;padding:2px 6px;font-weight:600'>{x['E']}</span>"
                    f"<br><span style='font-size:12px'>{x['L']}×{x['I']} · {html.escape(x['level'])}</span></td>"
                    f"<td style='{td}'>{strat}</td><td style='{td}'>{resp}</td>"
                    f"<td style='{td};text-align:center'><b>{x['scope']}</b></td></tr>")
    return (f"<table style='border-collapse:separate;border-spacing:4px;width:100%;font-family:Helvetica,Arial,sans-serif'>"
            f"<thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>")


# ----------------------------------------------------------------------------- risk threshold
def threshold_check(p: dict, bac: float | None = None) -> dict:
    """Cost of the risk management strategies vs the organisation's risk threshold (% of the budget)."""
    m = p["meta"]
    if bac is None:
        bac = S.compute(p).get("bac", 0) or 0
    thr = float(m.get("risk_threshold") or 0.10)
    per_risk = sum(float(r.get("contingency") or 0) for r in p.get("risks", []))
    if per_risk > 0:
        cost, src = per_risk, "risk"
    else:
        cost, src = S.contingency_amount(p, bac), "percent"
    ratio = cost / bac if bac else 0.0
    status = "over" if ratio > thr else "near" if ratio >= 0.8 * thr else "ok"
    cur = m.get("currency", "EUR")
    icon = {"ok": "✅", "near": "⚠️", "over": "❌"}[status]
    base = tr("soma dos custos das estratégias por risco", "sum of per-risk strategy costs") if src == "risk" else tr("contingência em % do BAC (sem custos por risco)", "contingency as % of BAC (no per-risk costs)")
    if status == "over":
        msg = tr(f"{icon} O custo do risco ({money(cost, cur)}, {pct(ratio)} do BAC) **ultrapassa o limiar de {pct(thr)}**: a organização não tolera este nível de risco — "
                 "o projeto pode não ser viável sem reduzir riscos (redesenho, estratégias preventivas mais baratas) ou rever o orçamento.",
                 f"{icon} The cost of risk ({money(cost, cur)}, {pct(ratio)} of BAC) **exceeds the {pct(thr)} threshold**: the organisation does not tolerate this level of risk — "
                 "the project may not be feasible unless risks are reduced (redesign, cheaper preventive strategies) or the budget is revised.")
    elif status == "near":
        msg = tr(f"{icon} O custo do risco ({money(cost, cur)}, {pct(ratio)} do BAC) está **perto do limiar de {pct(thr)}** (≥ 80%): margem curta para riscos novos.",
                 f"{icon} The cost of risk ({money(cost, cur)}, {pct(ratio)} of BAC) is **close to the {pct(thr)} threshold** (≥ 80%): little room for new risks.")
    else:
        msg = tr(f"{icon} O custo do risco ({money(cost, cur)}, {pct(ratio)} do BAC) está **abaixo do limiar de {pct(thr)}**: nível de risco tolerável para a organização.",
                 f"{icon} The cost of risk ({money(cost, cur)}, {pct(ratio)} of BAC) is **below the {pct(thr)} threshold**: risk level tolerable for the organisation.")
    return {"threshold": thr, "cost": cost, "bac": bac, "ratio": ratio, "status": status, "source": src, "basis": base, "icon": icon, "text": msg,
            "limit": thr * bac}


THRESHOLD_HELP = (
    "Limiar de risco (risk threshold) = sensibilidade da organização ao risco, em % do orçamento (tipicamente 5%, 10% ou 15%). "
    "Custo do risco = Σ custos das estratégias de gestão de risco (contingência por risco); se não houver custos por risco, usa a contingência em % do BAC. "
    "Rácio = custo do risco ÷ BAC. ✅ abaixo de 80% do limiar · ⚠️ entre 80% e 100% · ❌ acima: o projeto pode não ser viável.",
    "Risk threshold = the organisation's sensitivity to risk, as a % of the budget (typically 5%, 10% or 15%). "
    "Cost of risk = Σ costs of the risk management strategies (per-risk contingency); without per-risk costs, the contingency as % of BAC is used. "
    "Ratio = cost of risk ÷ BAC. ✅ below 80% of the threshold · ⚠️ between 80% and 100% · ❌ above: the project may not be feasible.")

MATRIX_HELP = (
    "Formato do professor (slide 10). Impacto adverso potencial = linha do logframe onde está o pressuposto (Operacional → Atividades; "
    "Comportamental → Outputs; Político → Outcome). Nível = P × I. Estratégia: preventiva (baixa a probabilidade, entra no plano como atividade) "
    "e corretiva (baixa a consequência, acionada «se e quando» o risco ocorre). Responsável e âmbito sugeridos pelo tipo: "
    "P → Equipa + Patrocinador (externo); B → Equipa + Grupo-alvo + Stakeholders (externo); OP → Equipa de gestão (interno).",
    "Professor's format (slide 10). Potential adverse impact = logframe row where the assumption sits (Operational → Activities; "
    "Behavioural → Outputs; Political → Outcome). Level = L × I. Strategy: preventive (lowers likelihood, enters the plan as an activity) "
    "and corrective (lowers consequence, triggered 'if and when' the risk occurs). Responsible and scope suggested by type: "
    "P → Team + Sponsor (external); B → Team + Target group + Stakeholders (external); OP → Management team (internal).")
