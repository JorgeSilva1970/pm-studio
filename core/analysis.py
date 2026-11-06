"""Analytical tools: diagrams (Graphviz DOT), assumption flowchart, stakeholder grid,
risk matrix, strategy scoring, benchmarking and quality checklist."""
from __future__ import annotations

import html
import math
import statistics
import textwrap

import numpy as np

from .i18n import tr
from .model import expected_assumption_type, indicator_dimension, objective_level

COL = {"Impact": "#B03A2E", "Outcome": "#D9822B", "Output": "#E3B23C", "Activity": "#3C8DBC", "Input": "#2E4A7D",
       "Effect": "#3B8EA5", "Core problem": "#C8763B", "Cause": "#3B8EA5"}


def _w(s, width=22) -> str:
    s = html.escape(str(s or "").strip())
    return "<BR/>".join(textwrap.wrap(s, width)) or " "


# ----------------------------------------------------------------------------- problem / objective trees
def tree_dot(problems: list[dict], objective: bool = False) -> str:
    """Effects on top, core problem(s) in the middle, causes at the bottom (PCM Figure 21/22)."""
    lines = ['digraph G {', 'rankdir=BT; splines=ortho; nodesep=0.35; ranksep=0.55;',
             'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, fontcolor="white", penwidth=0];',
             'edge [color="#555555", arrowsize=0.6];']
    lvl_label = {"Effect": tr("Fins (objetivos globais)", "Ends (overall objectives)") if objective else tr("Efeitos", "Effects"),
                 "Core problem": tr("Problema resolvido (Outcome)", "Problem solved (Outcome)") if objective else tr("Problema central", "Core problem"),
                 "Cause": tr("Meios (Outputs)", "Means (Outputs)") if objective else tr("Causas", "Causes")}
    colors = {"Effect": "#C8763B" if objective else "#3B8EA5", "Core problem": "#B79A3B" if objective else "#C8763B",
              "Cause": "#3B8EA5"}
    ids = {str(p.get("id")) for p in problems}
    for lvl in ("Effect", "Core problem", "Cause"):
        group = [p for p in problems if p.get("level") == lvl]
        if not group:
            continue
        lines.append(f'subgraph cluster_{lvl.replace(" ", "_")} {{ label="{lvl_label[lvl]}"; fontname="Helvetica"; fontsize=12; color="#BBBBBB"; style="dashed";')
        for p in group:
            text = (p.get("objective") or tr("(reformular pela positiva)", "(rephrase positively)")) if objective else p.get("text")
            fill = colors[lvl]
            if objective and not p.get("in_scope", True):
                fill = "#9AA5AE"
            lines.append(f'"{p["id"]}" [label=<<B>{html.escape(str(p["id"]))}</B><BR/>{_w(text)}>, fillcolor="{fill}"];')
        lines.append("}")
    for p in problems:
        par = str(p.get("parent") or "").strip()
        for target in [x.strip() for x in par.replace(";", ",").split(",") if x.strip()]:
            if target in ids:
                lines.append(f'"{p["id"]}" -> "{target}";')
    lines.append("}")
    return "\n".join(lines)


# ----------------------------------------------------------------------------- logic model / ToC
def results_chain_dot(p: dict, show_assumptions: bool = True) -> str:
    objs = p.get("objectives", [])
    acts = p.get("activities", [])
    lines = ['digraph G {', 'rankdir=BT; nodesep=0.25; ranksep=0.6; newrank=true;',
             'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, fontcolor="white", penwidth=0];',
             'edge [color="#666666", arrowsize=0.6];']
    levels = [("Input", tr("Recursos (4 Ms)", "Inputs (4 Ms)")), ("Activity", tr("Atividades", "Activities")),
              ("Output", tr("Produtos (Outputs) — controlo total", "Outputs — full control")),
              ("Outcome", tr("Resultados (Outcomes) — influência direta", "Outcomes — direct influence")),
              ("Impact", tr("Impacto — influência indireta", "Impact — indirect influence"))]
    for lvl, lab in levels:
        lines.append(f'subgraph cluster_{lvl} {{ label="{lab}"; fontname="Helvetica"; fontsize=11; style="filled"; fillcolor="#F6F6F6"; color="#DDDDDD";')
        if lvl == "Input":
            total = sum(float(a.get("cost") or 0) for a in acts)
            lines.append(f'"INPUTS" [label=<{_w(tr("Materiais · Maquinaria · Mão de obra · Money", "Materials · Machinery · Manpower · Money"), 30)}>, fillcolor="{COL["Input"]}"];')
        elif lvl == "Activity":
            for a in acts[:40]:
                lines.append(f'"ACT_{a["id"]}" [label=<<B>{html.escape(a["id"])}</B> {_w(a.get("name"), 20)}>, fillcolor="{COL["Activity"]}", fontsize=9];')
        else:
            for o in [o for o in objs if o.get("level") == lvl]:
                lines.append(f'"OBJ_{o["code"]}" [label=<<B>{html.escape(str(o["code"]))}</B><BR/>{_w(o.get("text"), 26)}>, fillcolor="{COL[lvl]}"];')
        lines.append("}")
    codes = {str(o["code"]) for o in objs}
    for a in acts[:40]:
        lines.append(f'"INPUTS" -> "ACT_{a["id"]}" [style=invis];')
        oc = str(a.get("output_code") or "")
        if oc in codes:
            lines.append(f'"ACT_{a["id"]}" -> "OBJ_{oc}";')
    for o in objs:
        par = str(o.get("parent") or "")
        if par in codes:
            lines.append(f'"OBJ_{o["code"]}" -> "OBJ_{par}";')
    if show_assumptions:
        for h in p.get("assumptions", []):
            oc = str(h.get("objective_code") or "")
            if oc in codes or oc.startswith("A"):
                node = f'"H_{h["id"]}"'
                lines.append(f'{node} [shape=note, style="filled", fillcolor="#FFF4C2", fontcolor="#333333", fontsize=9, '
                             f'label=<<B>{html.escape(h["id"])} · {html.escape(_type_label(h.get("type")))}</B><BR/>{_w(h.get("text"), 26)}>];')
                tgt = f'"OBJ_{oc}"' if oc in codes else None
                if tgt:
                    lines.append(f'{node} -> {tgt} [style=dashed, color="#C9A227", arrowhead=none];')
    lines.append("}")
    return "\n".join(lines)


def toc_dot(p: dict) -> str:
    """Theory of Change: pathways from preconditions/outputs to outcomes and impact, with assumptions."""
    objs = p.get("objectives", [])
    toc = p.get("toc", {})
    codes = {str(o["code"]) for o in objs}
    lines = ['digraph G {', 'rankdir=BT; nodesep=0.3; ranksep=0.7;',
             'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, fontcolor="white", penwidth=0];',
             'edge [color="#4A6572", arrowsize=0.7];']
    vision = toc.get("vision") or next((o.get("text") for o in objs if o.get("level") == "Impact"), "")
    lines.append(f'"VISION" [shape=ellipse, fillcolor="#6D2E46", label=<<B>{tr("Visão de sucesso", "Vision of success")}</B><BR/>{_w(vision, 34)}>];')
    for o in objs:
        lines.append(f'"OBJ_{o["code"]}" [label=<<B>{html.escape(str(o["code"]))}</B><BR/>{_w(o.get("text"), 24)}>, fillcolor="{COL.get(o.get("level"), "#777")}"];')
        par = str(o.get("parent") or "")
        if par in codes:
            lines.append(f'"OBJ_{o["code"]}" -> "OBJ_{par}";')
        if o.get("level") == "Impact":
            lines.append(f'"OBJ_{o["code"]}" -> "VISION" [style=dashed];')
    pre_ids = {str(c.get("id")) for c in p.get("preconditions", [])}
    for c in p.get("preconditions", []):
        lines.append(f'"PRE_{c["id"]}" [fillcolor="#5B8E7D", label=<<B>{html.escape(c["id"])}</B><BR/>{_w(c.get("text"), 22)}>];')
        tgt = str(c.get("leads_to") or "")
        dest = f'"OBJ_{tgt}"' if tgt in codes else (f'"PRE_{tgt}"' if tgt in pre_ids else None)
        if dest:
            lab = f' [label=<{_w(c.get("assumption"), 18)}>, fontsize=8, fontname="Helvetica", fontcolor="#8A6D00"]' if c.get("assumption") else ""
            lines.append(f'"PRE_{c["id"]}" -> {dest}{lab};')
    for h in p.get("assumptions", []):
        oc = str(h.get("objective_code") or "")
        if oc in codes:
            lines.append(f'"H_{h["id"]}" [shape=note, style=filled, fillcolor="#FFF4C2", fontcolor="#333333", fontsize=8, label=<{html.escape(h["id"])}: {_w(h.get("text"), 22)}>];')
            lines.append(f'"H_{h["id"]}" -> "OBJ_{oc}" [style=dotted, arrowhead=none, color="#C9A227"];')
    lines.append("}")
    return "\n".join(lines)


def _type_label(t):
    return {"Operational": tr("Operacional", "Operational"), "Behavioural": tr("Comportamental", "Behavioural"),
            "Political": tr("Político", "Political")}.get(t, t or "")


# ----------------------------------------------------------------------------- network diagram (AoN)
def network_dot(sched: dict, unit_label: str = "") -> str:
    """Activity-on-node boxes like the professor's figure: ES | ID | EF  /  LS | D | LF, TF on top."""
    df = sched["acts"]
    lines = ['digraph G {', 'rankdir=LR; nodesep=0.3; ranksep=0.5;',
             'node [shape=plaintext, fontname="Helvetica", fontsize=10];', 'edge [arrowsize=0.7];']

    def f(x):
        return f"{x:.1f}".rstrip("0").rstrip(".")
    for _, r in df.iterrows():
        c = "#E4572E" if r["critical"] else "#5A7D8C"
        bg = "#FDECE7" if r["critical"] else "#EEF3F5"
        label = (f'<<TABLE BORDER="2" COLOR="{c}" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white">'
                 f'<TR><TD COLSPAN="3" BORDER="0"><FONT COLOR="{c}" POINT-SIZE="9">TF = {f(r["TF"])}</FONT></TD></TR>'
                 f'<TR><TD><FONT COLOR="#1B7F79">{f(r["ES"])}</FONT></TD><TD><B>{html.escape(str(r["id"]))}</B></TD><TD><FONT COLOR="#1B7F79">{f(r["EF"])}</FONT></TD></TR>'
                 f'<TR><TD BGCOLOR="{bg}"><FONT COLOR="{c}">{f(r["LS"])}</FONT></TD><TD BGCOLOR="{bg}">{f(r["D"])}</TD><TD BGCOLOR="{bg}"><FONT COLOR="{c}">{f(r["LF"])}</FONT></TD></TR>'
                 f'<TR><TD COLSPAN="3" BORDER="0"><FONT POINT-SIZE="8">{html.escape(str(r["name"])[:28])}</FONT></TD></TR></TABLE>>')
        lines.append(f'"{r["id"]}" [label={label}];')
    tab = sched["cpm"]["table"]
    from .cpm import parse_preds
    for _, r in df.iterrows():
        for pr in parse_preds(r["predecessors"]):
            crit = tab[pr]["critical"] and tab[r["id"]]["critical"] and abs(tab[pr]["EF"] - tab[r["id"]]["ES"]) < 1e-6
            lines.append(f'"{pr}" -> "{r["id"]}" [color="{"#E4572E" if crit else "#7A8B94"}", penwidth={2.4 if crit else 1}];')
    lines.append("}")
    return "\n".join(lines)


# ----------------------------------------------------------------------------- assumptions (PCM Fig. 30)
def assumption_decision(h: dict) -> tuple[str, str]:
    """Return (code, explanation) following the PCM 'Assessment of Assumptions' flowchart."""
    if not h.get("important", True):
        return "drop", tr("Não é importante → não incluir no logframe.", "Not important → do not include in the logframe.")
    holds = h.get("holds", "Possibly")
    if holds == "Almost certainly":
        return "drop", tr("Quase certo que se verifica → não incluir no logframe.", "Almost certain to hold → do not include in the logframe.")
    if holds == "Possibly":
        return "include", tr("Possivelmente verifica-se → incluir como pressuposto e monitorizar.", "Possibly holds → include as an assumption and monitor it.")
    if h.get("redesign_possible"):
        return "redesign", tr("Improvável → redesenhar o projeto (acrescentar atividades/resultados ou reformular o objetivo).",
                              "Unlikely → redesign the project (add activities/results or reformulate the purpose).")
    return "killer", tr("Improvável e sem redesenho possível → pressuposto 'killer': o projeto não é viável.",
                        "Unlikely and no redesign possible → killer assumption: the project is not feasible.")


def assumption_risk_probability(h: dict) -> int:
    """Professor: the lower the quantity/quality of evidence, the higher the probability of the risk (1-4)."""
    q = int(h.get("evidence_quality") or 2)
    return max(1, min(4, 5 - q))


def assumption_type_check(p: dict, h: dict) -> str | None:
    lvl = objective_level(p, h.get("objective_code"))
    exp = expected_assumption_type(lvl)
    if exp and h.get("type") and h.get("type") != exp:
        return exp
    return None


# ----------------------------------------------------------------------------- stakeholders
def mendelow(influence: int, interest: int) -> str:
    hi_inf, hi_int = influence >= 3, interest >= 3
    if hi_inf and hi_int:
        return tr("Gerir de perto", "Manage closely")
    if hi_inf:
        return tr("Manter satisfeito", "Keep satisfied")
    if hi_int:
        return tr("Manter informado", "Keep informed")
    return tr("Monitorizar", "Monitor")


def circle_of(stype: str) -> str:
    return {"Target group": "Target group", "Beneficiary": "Beneficiaries"}.get(stype, "Stakeholders")


# ----------------------------------------------------------------------------- risks
def exposure(r: dict) -> int:
    return int(r.get("likelihood") or 0) * int(r.get("impact") or 0)


def risk_level(e: int) -> str:
    if e >= 12:
        return tr("Crítico", "Critical")
    if e >= 8:
        return tr("Alto", "High")
    if e >= 4:
        return tr("Médio", "Medium")
    return tr("Baixo", "Low")


RISK_ZONES = [  # (min exposure, colour, level pt/en, required action pt/en)
    (12, "#C0392B", ("Crítico", "Critical"), ("Ação imediata: tratar já, escalar ao comité de pilotagem/patrocinador e rever semanalmente.",
                                             "Immediate action: treat now, escalate to the steering committee/sponsor and review weekly.")),
    (8, "#E67E22", ("Alto", "High"), ("Mitigação ativa: medidas preventivas com responsável e prazo; incluir atividade de prevenção no plano.",
                                      "Active mitigation: preventive measures with owner and deadline; add a prevention activity to the plan.")),
    (4, "#F1C40F", ("Médio", "Medium"), ("Atenção: planear contingência (custo/tempo) e rever em cada período de reporte.",
                                         "Attention: plan contingency (cost/time) and review at every reporting period.")),
    (0, "#27AE60", ("Baixo", "Low"), ("Tolerável: aceitar e apenas monitorizar.", "Tolerable: accept and monitor only.")),
]


def risk_zone(e: int) -> tuple:
    return next(z for z in RISK_ZONES if e >= z[0])


def risk_action(e: int) -> str:
    z = risk_zone(e)
    return tr(*z[3])


def risk_color(e: int) -> str:
    return "#C0392B" if e >= 12 else "#E67E22" if e >= 8 else "#F1C40F" if e >= 4 else "#27AE60"


# ----------------------------------------------------------------------------- strategy selection
def strategy_scores(strat: dict) -> list[dict]:
    crit = [c for c in strat.get("criteria", []) if c.get("criterion")]
    wsum = sum(float(c.get("weight") or 0) for c in crit) or 1
    out = []
    for o in strat.get("options", []):
        sc = o.get("scores", {})
        total = sum(float(c.get("weight") or 0) * float(sc.get(c["criterion"], 0) or 0) for c in crit) / wsum
        out.append({"name": o.get("name"), "score": total, "description": o.get("description", "")})
    out.sort(key=lambda d: d["score"], reverse=True)
    return out


# ----------------------------------------------------------------------------- indicators & benchmarking
def smart_score(ind: dict) -> int:
    return sum(bool(ind.get(k)) for k in ("specific", "measurable", "available", "relevant", "timely"))


def progress(ind: dict) -> float | None:
    b, t, c = ind.get("baseline"), ind.get("target"), ind.get("current")
    try:
        b, t, c = float(b), float(t), float(c)
    except (TypeError, ValueError):
        return None
    if t == b:
        return None
    return (c - b) / (t - b)


def benchmark(ind: dict, peers: list[dict], series: list[dict]) -> dict:
    """Evidence-based target: compare with peers and extrapolate the historical trend."""
    vals = [float(x["value"]) for x in peers if x.get("value") is not None]
    out = {"n_peers": len(vals)}
    b = ind.get("baseline")
    t = ind.get("target")
    higher_better = True
    if t is not None and b is not None:
        try:
            higher_better = float(t) >= float(b)
        except Exception:
            pass
    if vals:
        out["median"] = statistics.median(vals)
        out["top"] = max(vals) if higher_better else min(vals)
        out["top_peer"] = next((x.get("peer") for x in peers if x.get("value") is not None and float(x["value"]) == out["top"]), "")
        out["p75"] = float(np.percentile(vals, 75 if higher_better else 25))
    pts = sorted([(int(x["year"]), float(x["value"])) for x in series if x.get("year") is not None and x.get("value") is not None])
    if len(pts) >= 2:
        xs, ys = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
        slope, intercept = np.polyfit(xs, ys, 1)
        out["trend_slope"] = float(slope)
        ty = ind.get("target_year") or (xs.max() + 3)
        out["trend_at_target_year"] = float(slope * int(ty) + intercept)
        n = xs.max() - xs.min()
        if ys[0] > 0 and ys[-1] > 0 and n > 0:
            out["cagr"] = float((ys[-1] / ys[0]) ** (1 / n) - 1)
    # suggestions
    if b is not None:
        try:
            b = float(b)
            sug = {}
            if "trend_at_target_year" in out:
                sug["trend"] = out["trend_at_target_year"]
            if "median" in out:
                sug["peer_median"] = out["median"]
            if "p75" in out:
                sug["ambitious_p75"] = out["p75"]
            if "top" in out:
                sug["closing_half_gap"] = b + (out["top"] - b) * 0.5
            out["suggestions"] = sug
            if t is not None and "top" in out:
                t = float(t)
                if (higher_better and t > out["top"]) or (not higher_better and t < out["top"]):
                    out["feasibility"] = "above_top"
                elif "trend_at_target_year" in out and ((higher_better and t <= out["trend_at_target_year"]) or (not higher_better and t >= out["trend_at_target_year"])):
                    out["feasibility"] = "below_trend"
                else:
                    out["feasibility"] = "ok"
        except Exception:
            pass
    return out


# ----------------------------------------------------------------------------- quality frame (Project Life Cycle slide)
QUALITY = {
    "Relevance": [
        ("rel1", "Coerência com as políticas públicas / do Governo?", "Consistency with government policies?"),
        ("rel2", "Stakeholders e grupos-alvo claramente identificados?", "Stakeholders & target groups clearly identified?"),
        ("rel3", "Problemas devidamente analisados?", "Problems properly analysed?"),
        ("rel4", "Lições aprendidas incorporadas na estratégia?", "Lessons learned incorporated in strategy?"),
    ],
    "Feasibility": [
        ("fea1", "Objetivos e programa de trabalho claros?", "Objectives and work programme are clear?"),
        ("fea2", "Recursos e implicações de custo claros e viáveis?", "Resources and cost implications clear and feasible?"),
        ("fea3", "Disposições de gestão e financeiras claras?", "Management and financial arrangements are clear?"),
        ("fea4", "Sistemas de M&A claros?", "M&E systems are clear?"),
        ("fea5", "Disposições de gestão de risco estabelecidas?", "Risk management arrangements are in place?"),
        ("fea6", "O projeto é sustentável?", "The project is sustainable?"),
    ],
    "Effectiveness": [
        ("eff1", "O projeto mantém-se relevante e viável?", "Project remains relevant and feasible?"),
        ("eff2", "Os objetivos estão a ser alcançados?", "Objectives are being achieved?"),
        ("eff3", "O projeto está a ser bem gerido?", "Project is being well-managed?"),
        ("eff4", "As questões de sustentabilidade estão a ser tratadas?", "Sustainability issues are being addressed?"),
        ("eff5", "Estão a ser seguidas boas práticas de PCM?", "Good PCM practices are being followed?"),
    ],
}
QUALITY_SCORE = {"Yes": 1.0, "Partial": 0.5, "No": 0.0}


def quality_scores(answers: dict) -> dict:
    out = {}
    for attr, qs in QUALITY.items():
        vals = [QUALITY_SCORE[answers[q[0]]] for q in qs if answers.get(q[0]) in QUALITY_SCORE]
        out[attr] = (sum(vals) / len(vals)) if vals else None
    return out
