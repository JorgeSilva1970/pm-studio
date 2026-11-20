"""Implementation, monitoring, evaluation & closure engines (course modules Monitoring 1–16 and Evaluation 1b–19b).

Every function is pure (no Streamlit) so it can be unit-tested and reused by the report and the AI agent.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from . import analysis as AN
from . import schedule as S
from .i18n import OPTIONS, opt_label, tr
from .model import activity_cost, objective_level


def _d(v) -> date | None:
    if not v:
        return None
    try:
        return S.to_date(v)
    except Exception:
        return None


def _yearfrac(d: date) -> float:
    return d.year + (d.timetuple().tm_yday - 1) / 365.25


def _f(v):
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


# ============================================================================ M1 · indicator monitoring
def expected_value(ind: dict, when: date) -> float | None:
    """Linear target trajectory baseline (baseline_year) → target (target_year)."""
    b, t = _f(ind.get("baseline")), _f(ind.get("target"))
    by, ty = _f(ind.get("baseline_year")), _f(ind.get("target_year"))
    if None in (b, t, by, ty) or ty <= by:
        return None
    x = min(max(_yearfrac(when), by), ty)
    return b + (t - b) * (x - by) / (ty - by)


def indicator_series(p: dict, iid: str) -> list[dict]:
    rows = [r for r in p.get("ind_reviews", []) if str(r.get("indicator_id")) == str(iid) and r.get("value") is not None and _d(r.get("date"))]
    return sorted(rows, key=lambda r: _d(r["date"]))


def indicator_status(ind: dict, value: float | None, when: date | None) -> tuple[str, float | None, float | None]:
    """Return (status code, expected, achievement). status: on_track | watch | off_track | no_data | no_target."""
    if value is None or when is None:
        return "no_data", None, None
    exp = expected_value(ind, when)
    b, t = _f(ind.get("baseline")), _f(ind.get("target"))
    if exp is None or b is None or t is None or t == b:
        return "no_target", exp, None
    ach = (value - b) / (t - b)
    exp_ach = (exp - b) / (t - b)
    if exp_ach <= 0:
        return ("on_track" if ach >= 0 else "watch"), exp, ach
    ratio = ach / exp_ach
    return ("on_track" if ratio >= 0.95 else "watch" if ratio >= 0.75 else "off_track"), exp, ach


STATUS_ICON = {"on_track": "🟢", "watch": "🟡", "off_track": "🔴", "no_data": "⚪", "no_target": "⚪"}


def status_label(code: str) -> str:
    return {"on_track": tr("No bom caminho", "On track"), "watch": tr("Atenção", "Watch"), "off_track": tr("Fora da trajetória", "Off track"),
            "no_data": tr("Sem medições", "No measurements"), "no_target": tr("Sem baseline/meta/anos", "No baseline/target/years")}[code]


def indicators_overview(p: dict) -> list[dict]:
    out = []
    for ind in p.get("indicators", []):
        ser = indicator_series(p, ind["id"])
        if ser:
            last = ser[-1]
            val, when = last["value"], _d(last["date"])
        else:
            val, when = _f(ind.get("current")), _d(p["meta"].get("status_date")) if ind.get("current") is not None else None
        st_, exp, ach = indicator_status(ind, val, when)
        out.append({"id": ind["id"], "indicator": ind.get("indicator", ""), "level": objective_level(p, ind.get("objective_code")),
                    "baseline": _f(ind.get("baseline")), "target": _f(ind.get("target")), "last_value": val,
                    "last_date": when, "expected": exp, "achievement": ach, "status": st_, "n": len(ser)})
    return out


def indicators_text(p: dict) -> str:
    ov = indicators_overview(p)
    if not ov:
        return ""
    cnt = {k: sum(1 for o in ov if o["status"] == k) for k in STATUS_ICON}
    off = [o["id"] for o in ov if o["status"] == "off_track"]
    nod = [o["id"] for o in ov if o["status"] == "no_data"]
    txt = tr(f"De {len(ov)} indicadores: **{cnt['on_track']} no bom caminho**, {cnt['watch']} em atenção, **{cnt['off_track']} fora da trajetória** e {cnt['no_data']} sem medições. ",
             f"Of {len(ov)} indicators: **{cnt['on_track']} on track**, {cnt['watch']} to watch, **{cnt['off_track']} off track** and {cnt['no_data']} without measurements. ")
    if off:
        txt += tr(f"Para {', '.join(off)} analise as causas (atividades atrasadas? pressupostos que falharam?) e decida ações corretivas; se a meta deixar de ser realista, a sua alteração exige um **pedido de alteração aprovado** — não se mudam metas sem justificação. ",
                  f"For {', '.join(off)} analyse the causes (delayed activities? failed assumptions?) and decide corrective actions; if the target is no longer realistic, changing it requires an **approved change request** — targets are never changed without justification. ")
    if nod:
        txt += tr(f"Sem dados: {', '.join(nod)} — confirme a fonte, a frequência e o responsável pela recolha.", f"No data: {', '.join(nod)} — confirm the source, frequency and who collects it.")
    return txt


# ============================================================================ M2 · milestones
def milestone_rows(p: dict, sched: dict | None = None) -> list[dict]:
    status = _d(p["meta"].get("status_date")) or date.today()
    fin = {}
    if sched and sched.get("ok"):
        fin = dict(zip(sched["acts"]["id"], sched["acts"]["finish"]))
    out = []
    for m in p.get("milestones", []):
        planned = _d(m.get("planned_date")) or fin.get(m.get("activity_id"))
        actual, fc = _d(m.get("actual_date")), _d(m.get("forecast_date"))
        ref = actual or fc
        dev = (ref - planned).days if (ref and planned) else None
        if actual:
            code = "done_on_time" if (dev or 0) <= 0 else "done_late"
        elif planned and planned < status:
            code = "overdue"
        elif dev and dev > 0:
            code = "forecast_late"
        else:
            code = "upcoming"
        out.append({**m, "planned": planned, "actual": actual, "forecast": fc, "deviation": dev, "code": code})
    return out


MS_LABEL = {"done_on_time": ("✅ Atingido a tempo", "✅ Achieved on time"), "done_late": ("🟠 Atingido com atraso", "🟠 Achieved late"),
            "overdue": ("🔴 Em atraso", "🔴 Overdue"), "forecast_late": ("🟡 Previsão de atraso", "🟡 Forecast late"), "upcoming": ("⚪ Por vir", "⚪ Upcoming")}


def milestones_text(rows: list[dict]) -> str:
    if not rows:
        return ""
    done = [r for r in rows if r["actual"]]
    on = sum(1 for r in done if r["code"] == "done_on_time")
    over = [r["id"] for r in rows if r["code"] == "overdue"]
    late_fc = [r["id"] for r in rows if r["code"] == "forecast_late"]
    noacc = [r["id"] for r in done if not r.get("accepted")]
    txt = tr(f"{len(done)} de {len(rows)} marcos atingidos ({on} a tempo). ", f"{len(done)} of {len(rows)} milestones achieved ({on} on time). ")
    if over:
        txt += tr(f"🔴 Em atraso: {', '.join(over)} — registe a causa e a ação corretiva e avalie o impacto no caminho crítico. ",
                  f"🔴 Overdue: {', '.join(over)} — record the cause and corrective action and assess the impact on the critical path. ")
    if late_fc:
        txt += tr(f"🟡 Previsão de atraso: {', '.join(late_fc)}. ", f"🟡 Forecast late: {', '.join(late_fc)}. ")
    if noacc:
        txt += tr(f"Marcos atingidos ainda sem aceitação formal: {', '.join(noacc)} — um marco só conta quando o entregável é aceite.",
                  f"Milestones achieved but not yet formally accepted: {', '.join(noacc)} — a milestone only counts once the deliverable is accepted.")
    return txt


# ============================================================================ M3 · change control
STRATEGIC = {"Outcome", "Impact"}


def change_class(c: dict) -> tuple[str, str]:
    """Tactical changes (inputs, activities, outputs, budget, schedule) can be approved by project management/steering;
    changes to the outcome or impact change the project's purpose → new project or closure decision."""
    el = c.get("element_type")
    if el in STRATEGIC:
        return "strategic", tr("Estratégica: altera o propósito do projeto → decidir entre **encerrar** e formular um **novo projeto**; requer a autoridade que aprovou o projeto.",
                               "Strategic: changes the project's purpose → decide between **closing** and formulating a **new project**; requires the authority that approved the project.")
    if el == "Target":
        return "target", tr("Alteração de meta: só com evidência (nova baseline, benchmarking) e aprovação formal; manter o registo da meta original.",
                            "Target change: only with evidence (new baseline, benchmarking) and formal approval; keep a record of the original target.")
    return "tactical", tr("Tática: ajuste de meios (inputs/atividades/outputs/orçamento/prazo) — aprovação pelo gestor/comité de acompanhamento conforme o nível de delegação.",
                          "Tactical: adjustment of means (inputs/activities/outputs/budget/schedule) — approval by the manager/steering committee according to delegation.")


def changes_by_wbs(p: dict) -> list[dict]:
    """Approved/implemented change impacts propagated up the WBS (element_ref = WBS code or activity id)."""
    from . import wbs as W
    els = {e["code"]: e for e in W.elements(p)}
    if not els:
        return []
    act_wbs = {a["id"]: a.get("wbs_code") for a in p.get("activities", [])}
    agg = {}
    for c in p.get("changes", []):
        if c.get("status") not in ("Approved", "Implemented"):
            continue
        ref = str(c.get("element_ref") or "").strip()
        code = ref if ref in els else act_wbs.get(ref)
        if not code or code not in els:
            continue
        cc = code
        while cc != "0":
            a = agg.setdefault(cc, {"code": cc, "name": els[cc].get("name", ""), "cost": 0.0, "days": 0.0, "changes": []})
            a["cost"] += _f(c.get("impact_cost")) or 0
            a["days"] += _f(c.get("impact_time")) or 0
            a["changes"].append(c["id"])
            cc = W.parent_of(cc)
    return sorted(agg.values(), key=lambda r: W.key(r["code"]))


def changes_summary(p: dict) -> dict:
    rows = p.get("changes", [])
    appr = [c for c in rows if c.get("status") in ("Approved", "Implemented")]
    return {"n": len(rows), "approved": len(appr), "pending": sum(1 for c in rows if c.get("status") == "Proposed"),
            "rejected": sum(1 for c in rows if c.get("status") == "Rejected"),
            "time": sum(_f(c.get("impact_time")) or 0 for c in appr), "cost": sum(_f(c.get("impact_cost")) or 0 for c in appr),
            "strategic": [c["id"] for c in rows if change_class(c)[0] == "strategic"],
            "no_justif": [c["id"] for c in rows if not str(c.get("justification") or "").strip()],
            "target_unapproved": [c["id"] for c in rows if c.get("element_type") == "Target" and c.get("status") not in ("Approved", "Implemented", "Rejected")]}


def changes_text(p: dict, cur: str = "EUR") -> str:
    s = changes_summary(p)
    if not s["n"]:
        return tr("Sem pedidos de alteração registados. Todas as alterações (inputs, atividades, outputs, metas, orçamento, prazo) devem passar por um registo formal com justificação, impacto e aprovação.",
                  "No change requests recorded. Every change (inputs, activities, outputs, targets, budget, schedule) should go through a formal log with justification, impact and approval.")
    from .fmt import money
    txt = tr(f"{s['n']} pedidos: {s['approved']} aprovados/implementados, {s['pending']} pendentes, {s['rejected']} rejeitados. Impacto acumulado aprovado: **{s['time']:+.0f} dias** e **{money(s['cost'], cur)}**. ",
             f"{s['n']} requests: {s['approved']} approved/implemented, {s['pending']} pending, {s['rejected']} rejected. Cumulative approved impact: **{s['time']:+.0f} days** and **{money(s['cost'], cur)}**. ")
    if s["strategic"]:
        txt += tr(f"⚠️ {', '.join(s['strategic'])} mexem no outcome/impacto — já não é um ajuste, é outro projeto (reavaliar necessidades e decidir encerramento/reformulação). ",
                  f"⚠️ {', '.join(s['strategic'])} touch the outcome/impact — this is no longer an adjustment but a different project (reassess needs and decide closure/reformulation). ")
    if s["target_unapproved"]:
        txt += tr(f"Metas alteradas sem aprovação: {', '.join(s['target_unapproved'])}. ", f"Targets changed without approval: {', '.join(s['target_unapproved'])}. ")
    if s["no_justif"]:
        txt += tr(f"Sem justificação: {', '.join(s['no_justif'])}.", f"No justification: {', '.join(s['no_justif'])}.")
    return txt


# ============================================================================ M4 · risk & assumption reviews
def risk_history(p: dict) -> list[dict]:
    out = []
    for r in p.get("risks", []):
        revs = sorted([x for x in p.get("risk_reviews", []) if str(x.get("risk_id")) == str(r["id"])], key=lambda x: str(x.get("date")))
        e0 = AN.exposure(r)
        last = revs[-1] if revs else None
        e1 = int(last["likelihood"] or 0) * int(last["impact"] or 0) if last else e0
        out.append({"id": r["id"], "description": r.get("description", ""), "initial": e0, "latest": e1, "trend": e1 - e0,
                    "status": last.get("status") if last else "Open", "n": len(revs), "contingency": _f(r.get("contingency")) or 0,
                    "materialised": any(x.get("status") == "Materialised" for x in revs),
                    "cost_impact": sum(_f(x.get("cost_impact")) or 0 for x in revs), "delay": sum(_f(x.get("delay")) or 0 for x in revs),
                    "target": _f(r.get("target_exposure"))})
    return out


def risks_review_text(p: dict, cur: str = "EUR") -> str:
    h = risk_history(p)
    if not h:
        return ""
    from .fmt import money
    up = [x["id"] for x in h if x["trend"] > 0]
    down = [x["id"] for x in h if x["trend"] < 0]
    mat = [x for x in h if x["materialised"]]
    norev = [x["id"] for x in h if x["n"] == 0 and x["status"] != "Closed"]
    tgt = [x["id"] for x in h if x["target"] and x["latest"] <= x["target"]]
    txt = tr(f"Exposição total: inicial **{sum(x['initial'] for x in h)}** → atual **{sum(x['latest'] for x in h)}**. ",
             f"Total exposure: initial **{sum(x['initial'] for x in h)}** → current **{sum(x['latest'] for x in h)}**. ")
    if down:
        txt += tr(f"A mitigação reduziu {', '.join(down)}. ", f"Mitigation reduced {', '.join(down)}. ")
    if tgt:
        txt += tr(f"Atingiram a exposição-alvo: {', '.join(tgt)}. ", f"Reached the target exposure: {', '.join(tgt)}. ")
    if up:
        txt += tr(f"⚠️ Exposição a subir: {', '.join(up)} — rever as medidas e escalar ao dono do risco. ", f"⚠️ Exposure rising: {', '.join(up)} — review measures and escalate to the risk owner. ")
    if mat:
        ci = sum(x["cost_impact"] for x in mat)
        cont = sum(x["contingency"] for x in mat)
        txt += tr(f"Riscos materializados: {', '.join(x['id'] for x in mat)}, custo {money(ci, cur)} vs contingência alocada {money(cont, cur)}" + (" — **contingência insuficiente**. " if ci > cont else ". "),
                  f"Materialised risks: {', '.join(x['id'] for x in mat)}, cost {money(ci, cur)} vs allocated contingency {money(cont, cur)}" + (" — **insufficient contingency**. " if ci > cont else ". "))
    if norev:
        txt += tr(f"Sem revisão registada: {', '.join(norev)} — o registo de riscos é um documento vivo (rever pelo menos mensalmente).",
                  f"No review recorded: {', '.join(norev)} — the risk register is a living document (review at least monthly).")
    return txt


def assumption_latest(p: dict) -> list[dict]:
    out = []
    for h in p.get("assumptions", []):
        revs = sorted([x for x in p.get("assumption_reviews", []) if str(x.get("assumption_id")) == str(h["id"])], key=lambda x: str(x.get("date")))
        last = revs[-1] if revs else None
        out.append({"id": h["id"], "text": h.get("text", ""), "level": objective_level(p, h.get("objective_code")),
                    "status": last.get("status") if last else None, "date": last.get("date") if last else None, "review": last, "n": len(revs)})
    return out


def assumptions_text(p: dict) -> str:
    rows = assumption_latest(p)
    if not rows:
        return ""
    bad = [r for r in rows if r["status"] == "Not confirmed"]
    risk = [r["id"] for r in rows if r["status"] == "At risk"]
    nor = [r["id"] for r in rows if r["n"] == 0]
    txt = ""
    for r in bad:
        rv = r["review"] or {}
        eff = [n for k, n in (("affects_relevance", tr("relevância", "relevance")), ("affects_feasibility", tr("viabilidade", "feasibility")),
                              ("affects_sustainability", tr("sustentabilidade", "sustainability"))) if rv.get(k)]
        txt += tr(f"🔴 {r['id']} não se confirmou" + (f" (afeta {', '.join(eff)})" if eff else "") + " — reavaliar necessidades e a lógica de intervenção; se o outcome deixar de ser alcançável, propor alteração estratégica. ",
                  f"🔴 {r['id']} did not hold" + (f" (affects {', '.join(eff)})" if eff else "") + " — reassess needs and the intervention logic; if the outcome is no longer achievable, propose a strategic change. ")
    if risk:
        txt += tr(f"🟡 Em risco: {', '.join(risk)} — reforçar a monitorização e preparar resposta. ", f"🟡 At risk: {', '.join(risk)} — step up monitoring and prepare a response. ")
    if nor:
        txt += tr(f"Pressupostos ainda não revistos: {', '.join(nor)}.", f"Assumptions not yet reviewed: {', '.join(nor)}.")
    return txt or tr("Todos os pressupostos revistos se confirmam — a lógica de intervenção mantém-se válida.", "All reviewed assumptions hold — the intervention logic remains valid.")


# ============================================================================ M4 · contingency drawdown
def contingency_status(p: dict, bac: float | None = None) -> dict:
    m = p["meta"]
    if bac is None:
        bac = sum(activity_cost(p, a) for a in p.get("activities", []))
    cr0 = S.contingency_amount(p, bac)
    mr0 = bac * float(m.get("mgmt_reserve_pct") or 0)
    res = {}
    for key, init in (("Contingency reserve", cr0), ("Management reserve", mr0)):
        log = [x for x in p.get("contingency_log", []) if x.get("reserve") == key]
        used = sum(_f(x.get("amount")) or 0 for x in log if x.get("movement") == "Use")
        rel = sum(_f(x.get("amount")) or 0 for x in log if x.get("movement") == "Release")
        rein = sum(_f(x.get("amount")) or 0 for x in log if x.get("movement") == "Reinforcement")
        res[key] = {"initial": init, "used": used, "released": rel, "reinforced": rein, "available": init + rein - used - rel}
    return {"bac": bac, **res}


def contingency_text(p: dict, cs: dict, progress: float | None, cur: str = "EUR") -> str:
    from .fmt import money, pct
    c = cs["Contingency reserve"]
    tot = c["initial"] + c["reinforced"]
    burn = c["used"] / tot if tot else 0
    txt = tr(f"Reserva de contingência: {money(tot, cur)}, utilizados {money(c['used'], cur)} ({pct(burn)}), libertados {money(c['released'], cur)}, disponível **{money(c['available'], cur)}**. ",
             f"Contingency reserve: {money(tot, cur)}, used {money(c['used'], cur)} ({pct(burn)}), released {money(c['released'], cur)}, available **{money(c['available'], cur)}**. ")
    if progress is not None:
        if burn > progress + 0.15:
            txt += tr(f"⚠️ O consumo da reserva ({pct(burn)}) está muito acima do progresso do projeto ({pct(progress)}) — risco de esgotar a contingência antes do fim. ",
                      f"⚠️ Reserve burn ({pct(burn)}) is well above project progress ({pct(progress)}) — risk of running out of contingency before the end. ")
        elif progress > 0.6 and burn < 0.3:
            txt += tr("Com mais de 60% do projeto executado e pouca contingência usada, considere **libertar** parte da reserva associada a riscos já fechados. ",
                      "With over 60% of the project done and little contingency used, consider **releasing** part of the reserve tied to closed risks. ")
    if c["available"] < 0:
        txt += tr("🔴 Reserva negativa: é necessário reforço (reserva de gestão) ou pedido de alteração orçamental. ", "🔴 Negative reserve: reinforcement (management reserve) or a budget change request is needed. ")
    mr = cs["Management reserve"]
    if mr["initial"] or mr["used"]:
        txt += tr(f"Reserva de gestão (riscos desconhecidos, fora da baseline): disponível {money(mr['available'], cur)}.", f"Management reserve (unknown unknowns, outside the baseline): available {money(mr['available'], cur)}.")
    return txt


# ============================================================================ M10 · cash flow & funding
def cash_position(p: dict, sched: dict) -> pd.DataFrame:
    per = sched["periods"][["period", "period_end", "pv_cum"]].copy()
    rec, plan = [], []
    for _, r in per.iterrows():
        pe = r["period_end"]
        rec.append(sum(_f(f.get("amount")) or 0 for f in p.get("funding", []) if f.get("status") == "Received" and _d(f.get("date")) and _d(f["date"]) <= pe))
        plan.append(sum(_f(f.get("amount")) or 0 for f in p.get("funding", []) if _d(f.get("date")) and _d(f["date"]) <= pe))
    per["funds_received_cum"] = rec
    per["funds_all_cum"] = plan
    per["gap"] = per["funds_all_cum"] - per["pv_cum"]
    return per


def cash_text(df: pd.DataFrame, cur: str = "EUR") -> str:
    from .fmt import money
    if df is None or df.empty or df["funds_all_cum"].max() == 0:
        return tr("Registe as tranches de financiamento (previstas e recebidas) para comparar com as necessidades de liquidez (PV acumulado).",
                  "Record funding tranches (planned and received) to compare with liquidity needs (cumulative PV).")
    neg = df[df["gap"] < -0.5]
    if neg.empty:
        return tr("✅ O financiamento previsto cobre as necessidades acumuladas em todos os períodos.", "✅ Planned funding covers cumulative needs in every period.")
    w = neg.loc[neg["gap"].idxmin()]
    return tr(f"⚠️ Défice de tesouraria a partir de **{neg.iloc[0]['period']}**; o maior défice é {money(-w['gap'], cur)} em {w['period']}. Antecipar tranches, negociar adiantamentos ou reprogramar atividades não críticas — falta de liquidez é uma causa típica de atraso.",
              f"⚠️ Cash shortfall from **{neg.iloc[0]['period']}**; the largest gap is {money(-w['gap'], cur)} in {w['period']}. Bring tranches forward, negotiate advances or reschedule non-critical activities — lack of liquidity is a typical cause of delay.")


# ============================================================================ M8 · tenders & contracts
CONTRACTS = {  # type: (risk mostly on, when to use pt, when to use en)
    "Lump sum / Fixed price": ("seller", "Âmbito claro e estável; o fornecedor assume o risco de custo.", "Clear, stable scope; the supplier bears the cost risk."),
    "Cost reimbursement": ("buyer", "Âmbito incerto (I&D, inovação); paga custos + fee (fixa, incentivo ou prémio).", "Uncertain scope (R&D, innovation); pays costs + fee (fixed, incentive or award)."),
    "Time and materials": ("buyer", "Trabalho de curta duração ou âmbito indefinido; usar tetos (not-to-exceed).", "Short work or undefined scope; use not-to-exceed caps."),
    "Unit price": ("shared", "Quantidades incertas mas preço unitário conhecido (ex.: m³, horas, inquéritos).", "Uncertain quantities but known unit price (e.g. m³, hours, surveys)."),
    "Fixed price incentive fee": ("shared", "Âmbito razoavelmente definido; partilha de poupanças/derrapagens até um teto.", "Reasonably defined scope; savings/overruns shared up to a ceiling."),
    "Guaranteed maximum price": ("seller", "Obras/construção: custos reembolsados até um máximo garantido.", "Works/construction: costs reimbursed up to a guaranteed maximum."),
    "IDIQ": ("shared", "Necessidades recorrentes de quantidade/data indefinidas dentro de um período.", "Recurring needs with undefined quantity/timing within a period."),
    "Framework agreement": ("shared", "Várias aquisições repetidas com condições pré-acordadas (ordens de compra).", "Several repeated purchases under pre-agreed terms (call-offs)."),
    "Master service agreement": ("shared", "Relação de longo prazo; cada trabalho é definido num SOW.", "Long-term relationship; each job defined in a SOW."),
}


def contract_advice(certainty: str) -> list[str]:
    return {"High": ["Lump sum / Fixed price", "Unit price"], "Medium": ["Fixed price incentive fee", "Guaranteed maximum price", "Unit price"],
            "Low": ["Cost reimbursement", "Time and materials", "IDIQ"]}.get(certainty, [])


def bid_scores(bids: list[dict], w: float) -> list[dict]:
    w = min(max(_f(w) if _f(w) is not None else 0.7, 0), 1)
    ok = [b for b in bids if b.get("compliant") and _f(b.get("price")) and _f(b.get("technical_score")) is not None]
    if not ok:
        return []
    pmin = min(_f(b["price"]) for b in ok)
    out = []
    for b in ok:
        fs = 100 * pmin / _f(b["price"])
        out.append({"bidder": b.get("bidder"), "technical": _f(b["technical_score"]), "financial": fs, "price": _f(b["price"]),
                    "total": w * _f(b["technical_score"]) + (1 - w) * fs})
    out.sort(key=lambda r: -r["total"])
    for i, r in enumerate(out):
        r["rank"] = i + 1
    return out


def procurement_text(p: dict, cur: str = "EUR") -> str:
    from .fmt import money
    rows = p.get("procurement", [])
    if not rows:
        return ""
    txt = ""
    mism = [q["id"] for q in rows if q.get("contract_type") and contract_advice(q.get("scope_certainty")) and q["contract_type"] not in contract_advice(q.get("scope_certainty"))]
    if mism:
        txt += tr(f"O tipo de contrato de {', '.join(mism)} não é o mais adequado ao grau de certeza do âmbito (ver recomendação). ",
                  f"The contract type of {', '.join(mism)} is not the best fit for the scope certainty (see recommendation). ")
    for q in rows:
        sc = bid_scores([b for b in p.get("bids", []) if str(b.get("procurement_id")) == str(q["id"])], q.get("tech_weight"))
        if sc and q.get("awarded_to") and q["awarded_to"] != sc[0]["bidder"]:
            txt += tr(f"⚠️ {q['id']}: adjudicado a {q['awarded_to']}, mas a melhor proposta pela grelha é {sc[0]['bidder']} — fundamentar. ",
                      f"⚠️ {q['id']}: awarded to {q['awarded_to']} but the best bid by the grid is {sc[0]['bidder']} — justify. ")
        cv, ec = _f(q.get("contract_value")), _f(q.get("estimated_cost"))
        if cv and ec and cv > ec * 1.05:
            txt += tr(f"{q['id']}: contrato {money(cv, cur)} acima da estimativa ({money(ec, cur)}) — rever orçamento/contingência. ",
                      f"{q['id']}: contract {money(cv, cur)} above estimate ({money(ec, cur)}) — review budget/contingency. ")
    return txt or tr("Os tipos de contrato são coerentes com a certeza do âmbito e as adjudicações seguem a grelha de avaliação.",
                     "Contract types fit scope certainty and awards follow the evaluation grid.")


def closure_progress(p: dict, pid: str) -> tuple[int, int]:
    rows = [c for c in p.get("closure", []) if str(c.get("procurement_id")) == str(pid)]
    return sum(1 for c in rows if c.get("done")), 15


# ============================================================================ M6/M7 · engagement, feedback & communication
def feedback_summary(p: dict) -> dict:
    fb = p.get("feedback", [])
    sat = [int(x["satisfaction"]) for x in fb if x.get("satisfaction")]
    by = {}
    for x in fb:
        g = x.get("stakeholder_group") or "—"
        by.setdefault(g, []).append(int(x.get("satisfaction") or 0))
    return {"n": len(fb), "avg": sum(sat) / len(sat) if sat else None, "open": sum(1 for x in fb if x.get("status") == "Open"),
            "no_action": [x["id"] for x in fb if not str(x.get("action_taken") or "").strip()],
            "by_group": {k: sum(v) / len(v) for k, v in by.items() if v}}


def feedback_text(p: dict) -> str:
    s = feedback_summary(p)
    if not s["n"]:
        return tr("Ainda não há feedback registado. Fechar o ciclo (recolher → responder → mostrar o que mudou) aumenta a apropriação pelos stakeholders.",
                  "No feedback recorded yet. Closing the loop (collect → respond → show what changed) increases stakeholder ownership.")
    low = [g for g, v in s["by_group"].items() if v < 3]
    txt = tr(f"{s['n']} registos de feedback, satisfação média **{s['avg']:.1f}/5**, {s['open']} em aberto. ", f"{s['n']} feedback entries, average satisfaction **{s['avg']:.1f}/5**, {s['open']} open. ")
    if low:
        txt += tr(f"Grupos insatisfeitos (<3): {', '.join(low)} — rever a estratégia de envolvimento. ", f"Dissatisfied groups (<3): {', '.join(low)} — revisit the engagement strategy. ")
    if s["no_action"]:
        txt += tr(f"Sem resposta/ação: {', '.join(s['no_action'][:8])}.", f"No response/action: {', '.join(s['no_action'][:8])}.")
    return txt


def engagement_text(p: dict) -> str:
    rows = p.get("engagement", [])
    key = [s for s in p.get("stakeholders", []) if int(s.get("influence") or 0) >= 4]
    covered = {str(r.get("stakeholder")).strip().lower() for r in rows}
    miss = [s["name"] for s in key if str(s.get("name")).strip().lower() not in covered]
    late = [r["id"] for r in rows if r.get("status") == "Delayed"]
    txt = tr(f"{len(rows)} ações de envolvimento planeadas. ", f"{len(rows)} engagement actions planned. ")
    if miss:
        txt += tr(f"Stakeholders de alta influência sem ação de envolvimento: {', '.join(miss[:6])}. ", f"High-influence stakeholders without an engagement action: {', '.join(miss[:6])}. ")
    if late:
        txt += tr(f"Atrasadas: {', '.join(late)}.", f"Delayed: {', '.join(late)}.")
    return txt


def comm_text(p: dict, cur: str = "EUR") -> str:
    from .fmt import money, pct
    rows = p.get("comm_plan", [])
    if not rows:
        return ""
    circles = {str(r.get("circle")) for r in rows}
    bud = sum(_f(r.get("budget")) or 0 for r in rows)
    reach = [((_f(r.get("actual")) or 0) / _f(r["target"])) for r in rows if _f(r.get("target"))]
    noind = [r["id"] for r in rows if not str(r.get("indicator") or "").strip()]
    noact = [r["id"] for r in rows if not str(r.get("activity_id") or "").strip()]
    txt = tr(f"Plano com {len(rows)} ações ({money(bud, cur)}), cobrindo os círculos {', '.join(sorted(circles))}. ",
             f"Plan with {len(rows)} actions ({money(bud, cur)}), covering circles {', '.join(sorted(circles))}. ")
    if "1" not in circles:
        txt += tr("⚠️ Falta o 1.º círculo (stakeholders locais/multiplicadores) — é o mais importante para a apropriação. ", "⚠️ The 1st circle (local stakeholders/multipliers) is missing — it is the most important for ownership. ")
    if reach:
        txt += tr(f"Alcance médio face às metas: {pct(sum(reach) / len(reach))}. ", f"Average reach vs targets: {pct(sum(reach) / len(reach))}. ")
    if noind:
        txt += tr(f"Sem indicador: {', '.join(noind)}. ", f"No indicator: {', '.join(noind)}. ")
    if noact:
        txt += tr(f"Não ligadas a uma atividade de apoio de comunicação: {', '.join(noact)} (o custo deve estar no orçamento).",
                  f"Not linked to a communication support activity: {', '.join(noact)} (cost must be in the budget).")
    return txt


# ============================================================================ E · evaluation
def me_quality_score(p: dict) -> float | None:
    v = {"Yes": 1, "Partial": 0.5, "No": 0}
    a = [v[r["answer"]] for r in p.get("me_quality", []) if r.get("answer") in v]
    return sum(a) / len(a) if a else None


def me_budget_share(p: dict) -> float | None:
    acts = p.get("activities", [])
    tot = sum(activity_cost(p, a) for a in acts)
    if not tot:
        return None
    return sum(activity_cost(p, a) for a in acts if a.get("type") == "Support - M&E") / tot


def evaluation_text(p: dict) -> str:
    from .model import DAC_CRITERIA
    rows = p.get("evaluation", [])
    covered = {r["criterion"] for r in rows}
    miss = [c for c in DAC_CRITERIA if c not in covered]
    qt = {k: sum(1 for r in rows if r.get("q_type") == k) for k in ("Descriptive", "Normative", "Cause-effect")}
    nojc = [r["id"] for r in rows if not str(r.get("judgement_criteria") or "").strip()]
    txt = tr(f"A matriz cobre {len(covered)} dos 6 critérios OCDE-CAD" + (f"; faltam: {', '.join(miss)}. " if miss else ". "),
             f"The matrix covers {len(covered)} of the 6 OECD-DAC criteria" + (f"; missing: {', '.join(miss)}. " if miss else ". "))
    if rows:
        txt += tr(f"Perguntas: {qt['Descriptive']} descritivas, {qt['Normative']} normativas, {qt['Cause-effect']} de causa-efeito. ",
                  f"Questions: {qt['Descriptive']} descriptive, {qt['Normative']} normative, {qt['Cause-effect']} cause-effect. ")
        if not qt["Cause-effect"] and any(r["criterion"] == "Impact" for r in rows):
            txt += tr("Para o impacto são necessárias perguntas de causa-efeito (atribuição/contribuição, contrafactual). ", "Impact needs cause-effect questions (attribution/contribution, counterfactual). ")
        if nojc:
            txt += tr(f"Sem critérios de juízo: {', '.join(nojc)} — sem eles não há avaliação, só descrição.", f"No judgement criteria: {', '.join(nojc)} — without them there is no evaluation, only description.")
    return txt


def sustainability_scores(p: dict) -> dict:
    out = {}
    for r in p.get("sustainability", []):
        out.setdefault(r.get("pillar"), []).append(int(r.get("score") or 0))
    return {k: sum(v) / len(v) for k, v in out.items() if v}


def sustainability_text(p: dict) -> str:
    sc = sustainability_scores(p)
    if not sc:
        return ""
    weak = [opt_label("pillar", k) for k, v in sc.items() if v < 3]
    avg = sum(sc.values()) / len(sc)
    sdgs = sorted({s.strip() for r in p.get("sustainability", []) for s in str(r.get("sdg") or "").replace(";", ",").split(",") if s.strip()})
    txt = tr(f"Sustentabilidade média **{avg:.1f}/5** em {len(sc)} pilares. ", f"Average sustainability **{avg:.1f}/5** across {len(sc)} pillars. ")
    if weak:
        txt += tr(f"Pilares frágeis: {', '.join(weak)} — prever estratégia de saída (exit strategy), apropriação institucional e financiamento pós-projeto. ",
                  f"Weak pillars: {', '.join(weak)} — plan an exit strategy, institutional ownership and post-project funding. ")
    missing = [opt_label("pillar", k) for k in ("Economic", "Social", "Environmental", "Institutional", "Technological") if k not in sc]
    if missing:
        txt += tr(f"Por avaliar: {', '.join(missing)}. ", f"Not assessed: {', '.join(missing)}. ")
    if sdgs:
        txt += tr(f"Contribuição para os ODS: {', '.join(sdgs)}.", f"Contribution to SDGs: {', '.join(sdgs)}.")
    return txt


def efficiency_panel(p: dict, sched: dict | None) -> dict:
    out = {"CPI": None, "SPI": None, "budget_var": None, "ms_on_time": None, "satisfaction": None, "ind_on_track": None, "progress": None}
    if sched and sched.get("ok"):
        e = S.evm(p, sched)
        out.update(CPI=e["CPI"], SPI=e["SPI"], budget_var=(e["EAC"] - e["BAC"]) / e["BAC"] if e["BAC"] else None,
                   progress=e["EV"] / e["BAC"] if e["BAC"] else None)
    ms = milestone_rows(p, sched)
    done = [m for m in ms if m["actual"]]
    if done:
        out["ms_on_time"] = sum(1 for m in done if m["code"] == "done_on_time") / len(done)
    out["satisfaction"] = feedback_summary(p)["avg"]
    ov = [o for o in indicators_overview(p) if o["status"] in ("on_track", "watch", "off_track")]
    if ov:
        out["ind_on_track"] = sum(1 for o in ov if o["status"] == "on_track") / len(ov)
    return out


def efficiency_text(ep: dict) -> str:
    from .fmt import pct
    parts = []
    if ep["CPI"] is not None and ep["CPI"] == ep["CPI"]:
        parts.append(tr(f"CPI {ep['CPI']:.2f} ({'eficiente' if ep['CPI'] >= 1 else 'derrapagem de custos'})", f"CPI {ep['CPI']:.2f} ({'efficient' if ep['CPI'] >= 1 else 'cost overrun'})"))
    if ep["SPI"] is not None and ep["SPI"] == ep["SPI"]:
        parts.append(tr(f"SPI {ep['SPI']:.2f} ({'no prazo' if ep['SPI'] >= 1 else 'atrasado'})", f"SPI {ep['SPI']:.2f} ({'on schedule' if ep['SPI'] >= 1 else 'behind'})"))
    if ep["ms_on_time"] is not None:
        parts.append(tr(f"{pct(ep['ms_on_time'], 0)} dos marcos a tempo", f"{pct(ep['ms_on_time'], 0)} of milestones on time"))
    if ep["ind_on_track"] is not None:
        parts.append(tr(f"{pct(ep['ind_on_track'], 0)} dos indicadores na trajetória", f"{pct(ep['ind_on_track'], 0)} of indicators on track"))
    if ep["satisfaction"] is not None:
        parts.append(tr(f"satisfação {ep['satisfaction']:.1f}/5", f"satisfaction {ep['satisfaction']:.1f}/5"))
    if not parts:
        return ""
    return tr("**Eficiência e eficácia:** ", "**Efficiency and effectiveness:** ") + "; ".join(parts) + ". " + tr(
        "A eficiência compara recursos usados com resultados (custo, prazo); a eficácia compara resultados obtidos com as metas dos outcomes.",
        "Efficiency compares resources used with results (cost, time); effectiveness compares results achieved with outcome targets.")


def lessons_text(p: dict) -> str:
    rows = p.get("lessons", [])
    if not rows:
        return tr("Sem lições registadas. As lições alimentam o próximo ciclo (PDCA) e devem ser formuladas como recomendações acionáveis.",
                  "No lessons recorded. Lessons feed the next cycle (PDCA) and should be phrased as actionable recommendations.")
    cats = {}
    for r in rows:
        cats[r.get("category")] = cats.get(r.get("category"), 0) + 1
    miss = [opt_label("lesson_cat", o[0]) for o in OPTIONS["lesson_cat"] if o[0] not in cats]
    norec = [r["id"] for r in rows if not str(r.get("recommendation") or "").strip()]
    txt = tr(f"{len(rows)} lições em {len(cats)} das 8 categorias. ", f"{len(rows)} lessons in {len(cats)} of the 8 categories. ")
    if miss:
        txt += tr(f"Categorias sem lições: {', '.join(miss)}. ", f"Categories without lessons: {', '.join(miss)}. ")
    if norec:
        txt += tr(f"Sem recomendação: {', '.join(norec)} — uma lição sem recomendação não é transferível.", f"No recommendation: {', '.join(norec)} — a lesson without a recommendation is not transferable.")
    return txt


def closure_text(p: dict) -> str:
    txt = ""
    pend = [a["id"] for a in p.get("audits", []) if a.get("status") not in ("Done", "Cancelled") and str(a.get("findings") or "").strip()]
    if pend:
        txt += tr(f"Auditorias com constatações por resolver: {', '.join(pend)}. ", f"Audits with unresolved findings: {', '.join(pend)}. ")
    noagr = [o["id"] for o in p.get("ownership", []) if o.get("regime") in ("Shared", "Joint") and not str(o.get("agreement_ref") or "").strip()]
    if noagr:
        txt += tr(f"Propriedade partilhada/conjunta sem acordo formal: {', '.join(noagr)} — definir direitos de uso e publicação antes do encerramento. ",
                  f"Shared/joint ownership without a formal agreement: {', '.join(noagr)} — define use and publication rights before closure. ")
    open_c = []
    for q in p.get("procurement", []):
        if q.get("awarded_to"):
            done, tot = closure_progress(p, q["id"])
            if done < tot:
                open_c.append(f"{q['id']} ({done}/{tot})")
    if open_c:
        txt += tr(f"Contratos por encerrar: {', '.join(open_c)}.", f"Contracts not yet closed: {', '.join(open_c)}.")
    return txt or tr("Encerramento sem pendências registadas (auditorias, propriedade, contratos).", "Closure with no outstanding items (audits, ownership, contracts).")


# ============================================================================ checks used by the report and home page
def checks(p: dict, sched: dict | None = None) -> list[dict]:
    out = []

    def add(sev, module, pt, en):
        out.append({"sev": sev, "module": module, "msg": tr(pt, en)})
    for o in indicators_overview(p):
        if o["status"] == "off_track":
            add("warn", tr("Monitorização", "Monitoring"), f"{o['id']} está fora da trajetória para a meta.", f"{o['id']} is off its target trajectory.")
    for m in milestone_rows(p, sched):
        if m["code"] == "overdue":
            add("warn", tr("Marcos", "Milestones"), f"Marco {m['id']} em atraso.", f"Milestone {m['id']} is overdue.")
    s = changes_summary(p)
    for c in s["strategic"]:
        add("error", tr("Alterações", "Changes"), f"{c} altera outcome/impacto — decisão estratégica (novo projeto/encerramento).", f"{c} changes outcome/impact — strategic decision (new project/closure).")
    for c in s["target_unapproved"]:
        add("warn", tr("Alterações", "Changes"), f"{c}: meta alterada sem aprovação.", f"{c}: target changed without approval.")
    for r in assumption_latest(p):
        if r["status"] == "Not confirmed":
            add("error", tr("Pressupostos", "Assumptions"), f"{r['id']} não se confirmou na revisão.", f"{r['id']} did not hold at review.")
    cs = contingency_status(p)
    if cs["Contingency reserve"]["available"] < 0:
        add("error", tr("Contingências", "Contingencies"), "A reserva de contingência está esgotada.", "The contingency reserve is exhausted.")
    sh = me_budget_share(p)
    if sh is not None and p.get("activities") and sh < 0.03:
        add("info", tr("M&A", "M&E"), f"O M&A representa {sh:.1%} do orçamento (referência: 5–10%).", f"M&E is {sh:.1%} of the budget (reference: 5–10%).")
    if p.get("activities") and not p.get("comm_plan"):
        add("info", tr("Comunicação", "Communication"), "Sem plano de comunicação (audiências, mensagens, ferramentas, indicadores).", "No communication plan (audiences, messages, tools, indicators).")
    return out
