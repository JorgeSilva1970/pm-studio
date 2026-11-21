"""Self-contained HTML report with automatic interpretations (and optional AI synthesis)."""
from __future__ import annotations

import html
import json
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import analysis as AN
from . import cpm as C
from . import finance as F
from . import interpret as I
from . import riskmgmt as RM
from . import schedule as S
from .fmt import d, money, num, pct, unit_label
from .help_texts import SRC
from .i18n import opt_label, tr
from .matrix import logframe_classic_html, logframe_html
from .model import indicator_dimension, objective_level

VIZ = "https://cdn.jsdelivr.net/npm/@viz-js/viz@3.14.0/lib/viz-standalone.js"
JSZIP = "https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"


def _slug_r(s: str) -> str:
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:60] or "projeto"


def _e(s):
    return html.escape(str(s if s is not None else ""))


def _md(s: str) -> str:
    """Tiny markdown → HTML (bold/italic) for interpretation texts."""
    import re
    s = _e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)
    return s.replace("\n\n", "</p><p>").replace("\n", "<br>")


def _md_list(md: str) -> str:
    """Tiny markdown → HTML for '- ' bullet lists with **bold** (used by the worked WBS calculations)."""
    import re as _re
    items = []
    for ln in md.splitlines():
        sub = ln.startswith("  - ")
        t = html.escape(ln.strip()[2:] if ln.strip().startswith("- ") else ln.strip())
        t = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        style = ' style="margin-left:1.5em"' if sub else ""
        items.append(f"<li{style}>{t}</li>")
    return "<ul>" + "".join(items) + "</ul>"


def _df(df: pd.DataFrame, fmt: dict | None = None) -> str:
    df = df.copy()
    for c, f in (fmt or {}).items():
        if c in df:
            df[c] = df[c].map(lambda v: f(v) if v is not None and v == v else "—")
    return df.to_html(index=False, escape=True, classes="tbl", border=0, na_rep="—")


class _Figs:
    def __init__(self):
        self.first = True

    def __call__(self, fig) -> str:
        fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10))
        h = fig.to_html(full_html=False, include_plotlyjs="cdn" if self.first else False, config={"displaylogo": False})
        self.first = False
        return f"<div class='fig'>{h}</div>"


def _dot(dot: str) -> str:
    return f"<div class='dot' data-dot='{html.escape(dot, quote=True)}'></div>"


def _interp(text: str, title: str | None = None) -> str:
    if not text:
        return ""
    return f"<div class='interp'><div class='it'>🧭 {_e(title or tr('Interpretação', 'Interpretation'))}</div><p>{_md(text)}</p></div>"


def build(p: dict, ai_summary: str | None = None) -> str:
    from .i18n import set_terminology
    set_terminology((p.get("logframe") or {}).get("terminology", "pcm"))
    m = p["meta"]
    cur = m.get("currency", "EUR")
    fig = _Figs()
    sched = S.compute(p)
    e = S.evm(p, sched) if sched.get("ok") else {}
    fa = F.analyse(p.get("cashflows", []), p["finance"], float(p["finance"].get("residual_value") or 0))
    out = []
    sec = []

    def H(n, title):
        sec.append((n, title))
        out.append(f"<h2 id='s{n}'>{n}. {_e(title)}</h2>")

    # ------------------------------------------------------------------ summary
    H(0 if False else 1, tr("Síntese executiva", "Executive summary"))
    kp = []
    if sched.get("ok"):
        kp += [(tr("Duração", "Duration"), f"{num(sched['cpm']['duration'], 1)} {unit_label(sched['unit'])}"), (tr("Fim previsto", "Planned finish"), d(sched["finish"])),
               ("BAC", money(sched["bac"], cur)), (tr("Contingência", "Contingency"), money(sched["contingency"], cur))]
    if e:
        kp += [("CPI", num(e["CPI"], 2)), ("SPI", num(e["SPI"], 2)), ("EAC", money(e["EAC"], cur))]
    if fa:
        kp += [(tr("VAL", "NPV"), money(fa["npv"], cur)), (tr("TIR", "IRR"), pct(fa["irr"]) if fa["irr"] is not None else "—"), ("MIRR", pct(fa["mirr"]) if fa["mirr"] is not None else "—"),
               ("WACC", pct(fa["rate"], 2))]
    kp += [(tr("Riscos críticos", "Critical risks"), str(sum(1 for r in p["risks"] if AN.exposure(r) >= 12))),
           (tr("Indicadores SMART", "SMART indicators"), f"{sum(1 for i in p['indicators'] if AN.smart_score(i) == 5)}/{len(p['indicators'])}")]
    out.append("<div class='kpis'>" + "".join(f"<div class='kpi'><div class='kv'>{_e(v)}</div><div class='kl'>{_e(k)}</div></div>" for k, v in kp) + "</div>")
    if ai_summary:
        out.append(f"<div class='ai'><div class='it'>🤖 {tr('Síntese do agente IA (rever antes de usar)', 'AI agent synthesis (review before use)')}</div><p>{_md(ai_summary)}</p></div>")
    if sched.get("ok"):
        out.append(_interp(I.cpm_text(sched) + "\n\n" + I.cost_text(sched, cur)))
    if e:
        out.append(_interp(I.evm_text(e, cur), "EVM"))
    if fa:
        out.append(_interp(I.finance_text(fa, cur, F.breakeven_benefit_factor(p["cashflows"], p["finance"], float(p["finance"].get("residual_value") or 0))), tr("Viabilidade financeira", "Financial feasibility")))

    # ------------------------------------------------------------------ identification
    H(2, tr("Identificação", "Identification"))
    out.append(f"<h3>{tr('Análise de políticas', 'Policy analysis')}</h3>")
    for k, lab in (("context", tr("Contexto", "Context")), ("content", tr("Conteúdo", "Content")), ("consequences", tr("Consequências", "Consequences"))):
        if p["policy"].get(k):
            out.append(f"<p><b>{lab}.</b> {_e(p['policy'][k])}</p>")
    if p["policy_goals"]:
        out.append(_df(pd.DataFrame(p["policy_goals"])[["document", "strategic_goal", "impact_indicator", "baseline", "target", "source"]]
                       .rename(columns={"document": tr("Documento", "Document"), "strategic_goal": tr("Objetivo estratégico", "Strategic goal"),
                                        "impact_indicator": tr("Indicador de impacto", "Impact indicator"), "target": tr("Meta", "Target"), "source": tr("Fonte", "Source")})))
    if p["stakeholders"]:
        out.append("<h3>Stakeholders</h3>")
        sh = pd.DataFrame([{tr("Nome", "Name"): s["name"], tr("Tipo", "Type"): opt_label("stakeholder_type", s["type"]), tr("Interesses", "Interests"): s.get("interests"),
                            tr("Capacidade/motivação", "Capacity/motivation"): s.get("capacity_motivation"), tr("Ações", "Actions"): s.get("possible_actions"),
                            tr("Influência", "Influence"): s["influence"], tr("Interesse", "Interest"): s["interest"], tr("Estratégia", "Strategy"): AN.mendelow(s["influence"], s["interest"])}
                           for s in p["stakeholders"]])
        out.append(_df(sh))
        g = go.Figure(go.Scatter(x=[s["interest"] for s in p["stakeholders"]], y=[s["influence"] for s in p["stakeholders"]], mode="markers+text",
                                 text=[s["name"][:25] for s in p["stakeholders"]], textposition="top center",
                                 marker=dict(size=14, color=[{"Supporter": "#2E8B57", "Neutral": "#7F8C8D", "Opponent": "#C0392B"}.get(s["attitude"], "#777") for s in p["stakeholders"]])))
        g.add_hline(y=3, line_dash="dot")
        g.add_vline(x=3, line_dash="dot")
        g.update_layout(height=420, title=tr("Influência × interesse", "Influence × interest"), xaxis=dict(range=[0.5, 5.5], title=tr("Interesse", "Interest")), yaxis=dict(range=[0.5, 5.5], title=tr("Influência", "Influence")))
        out.append(fig(g))
        out.append(_interp(I.stakeholder_text(p["stakeholders"])))
    if p["behaviour"]:
        out.append(f"<h3>{tr('Padrões comportamentais', 'Behavioural patterns')}</h3>")
        out.append(_df(pd.DataFrame(p["behaviour"])[["target_group", "perception", "opportunity", "ability", "motivation", "implication"]]))
        out.append(_interp(I.behaviour_text(p["behaviour"])))
    if p["problems"]:
        out.append(f"<h3>{tr('Árvore de problemas', 'Problem tree')}</h3>" + _dot(AN.tree_dot(p["problems"])))
        out.append(f"<h3>{tr('Árvore de objetivos', 'Objective tree')}</h3>" + _dot(AN.tree_dot(p["problems"], objective=True)))
    sc = AN.strategy_scores(p["strategies"])
    if sc:
        out.append(f"<h3>{tr('Seleção da estratégia', 'Strategy selection')}</h3>")
        sel_ = p["strategies"].get("selected")
        out.append(_df(pd.DataFrame([{tr("Estratégia", "Strategy"): ("✔ " if s["name"] == sel_ else "") + ("★ " if i == 0 else "") + s["name"],
                                      tr("Pontuação", "Score"): round(s["score"], 2), tr("Descrição", "Description"): s["description"]} for i, s in enumerate(sc)])))
        out.append("<p><small>" + tr("✔ = estratégia selecionada · ★ = melhor pontuação · Pontuação = Σ (peso × nota) ÷ Σ pesos",
                                     "✔ = selected strategy · ★ = best score · Score = Σ (weight × score) ÷ Σ weights") + "</small></p>")
        out.append(_interp(I.strategy_text(sc, sel_)))
        if sel_:
            out.append(_md_list(I.strategy_explain(p["strategies"], sel_).replace("**Pontuação", "- **Pontuação").replace("**Weighted", "- **Weighted")))

    # ------------------------------------------------------------------ formulation
    H(3, tr("Formulação — Logic Models", "Formulation — Logic Models"))
    out.append(f"<h3>{tr('Matriz do Quadro Lógico — vista clássica 4×4 (PCM)', 'Logical Framework Matrix — classic 4×4 view (PCM)')}</h3>"
               + logframe_classic_html(p, (p.get("logframe") or {}).get("terminology", "pcm")))
    out.append(f"<h3>{tr('Matriz do Quadro Lógico — vista alargada (baseline, meta, critério)', 'Logical Framework Matrix — extended view (baseline, target, criterion)')}</h3>"
               + logframe_html(p, terminology=(p.get("logframe") or {}).get("terminology", "pcm")))
    out.append(f"<h3>{tr('Modelo lógico', 'Logic model')}</h3>" + _dot(AN.results_chain_dot(p)))
    out.append(f"<h3>{tr('Teoria da Mudança', 'Theory of Change')}</h3>")
    for k, lab in (("vision", tr("Visão", "Vision")), ("context", tr("Contexto", "Context")), ("actors", tr("Atores", "Actors")),
                   ("strategic_choices", tr("Escolhas estratégicas", "Strategic choices")), ("learning", tr("Aprendizagem", "Learning"))):
        if p["toc"].get(k):
            out.append(f"<p><b>{lab}.</b> {_e(p['toc'][k])}</p>")
    out.append(_dot(AN.toc_dot(p)))
    if p["assumptions"]:
        out.append(f"<h3>{tr('Pressupostos', 'Assumptions')}</h3>")
        out.append(_df(pd.DataFrame([{"ID": h["id"], tr("Tipo", "Type"): opt_label("assumption_type", h["type"]), tr("Condiciona", "Conditions"): h["objective_code"], tr("Pressuposto", "Assumption"): h["text"],
                                      tr("Evidência", "Evidence"): h["evidence"], tr("Decisão", "Decision"): AN.assumption_decision(h)[1]} for h in p["assumptions"]])))

    # ------------------------------------------------------------------ planning
    H(4, tr("Planeamento", "Planning"))
    from . import wbs as W
    if W.elements(p):
        ro = W.rollup(p, sched if sched.get("ok") else None, S.evm(p, sched) if sched.get("ok") else None)
        out.append(f"<h3>{tr('WBS / EAP — Estrutura Analítica do Projeto', 'WBS — Work Breakdown Structure')}</h3>")
        out.append(_dot(W.dot(p, ro, rankdir="TB" if len(W.leaves(p)) <= 6 else "LR", cur=cur)))
        rows_ = W.indented(p, ro)
        out.append(_df(pd.DataFrame([{tr("Código", "Code"): r["code"], tr("Elemento", "Element"): ("\u2003" * (r["level"] - 1)) + r["name"],
                                      tr("Tipo", "Type"): opt_label("wbs_type", r["type"]), "BAC": r["BAC"], tr("Duração", "Duration"): r["duration"],
                                      "PV": r["PV"], "EV": r["EV"], "AC": r["AC"], "CPI": r["CPI"], "SPI": r["SPI"]} for r in rows_]),
                       {"BAC": lambda v: money(v, cur), "PV": lambda v: "—" if v is None or v != v else money(v, cur), "EV": lambda v: "—" if v is None or v != v else money(v, cur),
                        "AC": lambda v: "—" if v is None or v != v else money(v, cur), "CPI": lambda v: "—" if v is None or v != v else f"{v:.2f}",
                        "SPI": lambda v: "—" if v is None or v != v else f"{v:.2f}", tr("Duração", "Duration"): lambda v: "—" if v is None or v != v else f"{v:.1f}"}))
        out.append(_interp(W.summary_text(p, ro, cur), "WBS / EAP"))
        from .help_texts import wbs_term
        keys = ["bac", "pct_bac", "duration", "start_finish", "pct", "pv", "ev", "ac", "cpi", "spi", "rule100", "rule_880", "reporting"]
        out.append(f"<h4>{tr('Como ler a tabela da WBS (glossário)', 'How to read the WBS table (glossary)')}</h4>")
        out.append(_df(pd.DataFrame([{tr("Termo", "Term"): wbs_term(k)[0], tr("Fórmula", "Formula"): wbs_term(k)[1], tr("Significado", "Meaning"): wbs_term(k)[2]} for k in keys])))
        top = max((e for e in W.elements(p) if W.level(e["code"]) == 1), key=lambda e: ro[e["code"]]["BAC"], default=None)
        if top:
            ev_ = S.evm(p, sched) if sched.get("ok") else None
            out.append(f"<h4>{tr('Exemplo de cálculo', 'Worked example')} — {_e(W.label(top))}</h4>" + _md_list(W.explain(p, top["code"], ro, ev_, cur)))

        lvs = [e for e in W.leaves(p) if any(e.get(f) for f in ("description", "deliverable", "acceptance", "owner"))]
        if lvs:
            out.append(f"<h3>{tr('Dicionário da WBS (pacotes de trabalho)', 'WBS dictionary (work packages)')}</h3>")
            out.append(_df(pd.DataFrame([{tr("Código", "Code"): e["code"], tr("Pacote", "Package"): e["name"], tr("Âmbito", "Scope"): e.get("description"),
                                          tr("Entregável", "Deliverable"): e.get("deliverable"), tr("Critérios de aceitação", "Acceptance criteria"): e.get("acceptance"),
                                          tr("Responsável", "Owner"): e.get("owner")} for e in lvs])))
        wch = [c for c in W.checks(p, sched if sched.get("ok") else None) if c["sev"] != "info"]
        if wch:
            out.append(_interp(" ".join(c["msg"] for c in wch), tr("Verificações da WBS", "WBS checks")))
    if sched.get("ok"):
        df = sched["acts"]
        out.append("<h3>PERT / CPM</h3>")
        out.append(_df(df[["id", "name", "predecessors", "D", "ES", "EF", "LS", "LF", "TF", "FF", "critical"]].assign(critical=[("LOE" if lo else c) for c, lo in zip(df["critical"], df.get("loe", df["critical"] & False))]).rename(columns={"name": tr("Atividade", "Activity"), "predecessors": tr("Predecessoras", "Predecessors"), "critical": tr("Crítica", "Critical")}),
                       {k: (lambda v: f"{v:.2f}") for k in ["D", "ES", "EF", "LS", "LF", "TF", "FF"]}))
        out.append(_dot(AN.network_dot(sched)))
        acts = [a for a in p["activities"] if a.get("id")]
        pp = C.pert_project(acts, sched["cpm"])
        T = p["meta"].get("target_duration")
        out.append(_interp(I.deadline_text(C.deadline_check(acts, sched["cpm"], T), sched["unit"]) + " " + tr(*I.DEADLINE_HELP), tr("Prazo-alvo e margem do projeto", "Target and project margin")))
        out.append(_interp(I.pert_text(pp, T, C.prob_by(T, pp["mean"], pp["sd"]) if T else None, sched["unit"])))
        mc = C.monte_carlo(acts, 5000)
        out.append(_interp(I.mc_text(mc, sched["unit"], T, pp["mean"]), "Monte Carlo"))
        out.append(f"<h3>{tr('Diagrama de Gantt', 'Gantt chart')}</h3>")
        gd = df.assign(Start=pd.to_datetime(df["start"]), Finish=pd.to_datetime(df["finish"]) + pd.Timedelta(hours=12),
                       Status=[tr("Crítica", "Critical") if c else tr("Esforço contínuo (LOE)", "Level of effort (LOE)") if lo else tr("Não crítica", "Non-critical")
                               for c, lo in zip(df["critical"], df.get("loe", df["critical"] & False))], Task=df["id"] + " " + df["name"].str.slice(0, 40))
        g = px.timeline(gd, x_start="Start", x_end="Finish", y="Task", color="Status", color_discrete_map={tr("Crítica", "Critical"): "#E4572E", tr("Não crítica", "Non-critical"): "#3C8DBC",
                                                                                                           tr("Esforço contínuo (LOE)", "Level of effort (LOE)"): "#8E7CC3"})
        g.update_yaxes(autorange="reversed")
        g.update_layout(height=max(320, 30 * len(gd) + 100), title=tr("Gantt (caminho crítico a vermelho)", "Gantt (critical path in red)"))
        out.append(fig(g))
        per = sched["periods"]
        g = go.Figure()
        g.add_trace(go.Bar(x=per["period"], y=per["pv"], name=tr("Custo do período", "Period cost"), marker_color="#9DB9D3"))
        g.add_trace(go.Scatter(x=per["period"], y=per["pv_cum"], name=tr("Acumulado (curva S)", "Cumulative (S-curve)"), yaxis="y2", line=dict(color="#1F3B57", width=3)))
        g.update_layout(height=380, title=tr("Orçamento distribuído no tempo", "Time-phased budget"), yaxis2=dict(overlaying="y", side="right", rangemode="tozero"))
        out.append(fig(g))
        tab = per[["period", "pv", "pv_cum"]].rename(columns={"period": tr("Período", "Period"), "pv": tr("Custo do período", "Period cost"), "pv_cum": tr("Acumulado", "Cumulative")})
        out.append(_df(tab, {tr("Custo do período", "Period cost"): lambda v: money(v, cur), tr("Acumulado", "Cumulative"): lambda v: money(v, cur)}))
    roles = p["raci"].get("roles", [])
    if roles and p["activities"]:
        out.append(f"<h3>{tr('Matriz RACI', 'RACI matrix')}</h3>")
        out.append(_df(pd.DataFrame([{"ID": a["id"], tr("Atividade", "Activity"): a.get("name"), **{r: p["raci"]["matrix"].get(a["id"], {}).get(r, "") for r in roles}} for a in p["activities"]])))
    if p["risks"]:
        out.append(f"<h3>{tr('Riscos', 'Risks')}</h3>")
        out.append(_df(pd.DataFrame([{"ID": r["id"], tr("Tipo", "Type"): opt_label("risk_type", r["type"]), tr("Risco", "Risk"): r["description"], "P": r["likelihood"], "I": r["impact"],
                                      tr("Exposição", "Exposure"): AN.exposure(r), tr("Alvo", "Target"): r["target_exposure"], tr("Estratégia", "Strategy"): opt_label("risk_strategy", r["strategy"]),
                                      tr("Ação exigida", "Required action"): AN.risk_action(AN.exposure(r)),
                                      tr("Mitigação proposta", "Proposed mitigation"): r["proposed_mitigation"], tr("Responsável", "Owner"): r["risk_owner"]}
                                     for r in sorted(p["risks"], key=lambda r: -AN.exposure(r))])))
        z = [[i * l for i in range(1, 5)] for l in range(1, 5)]
        g = go.Figure(go.Heatmap(z=z, x=[1, 2, 3, 4], y=[1, 2, 3, 4], colorscale=[[0, "#27AE60"], [0.25, "#F1C40F"], [0.55, "#E67E22"], [1, "#C0392B"]], showscale=False))
        cells = {}
        for r in p["risks"]:
            cells.setdefault((r["impact"], r["likelihood"]), []).append(r["id"])
        for (i, l), ids in cells.items():
            g.add_annotation(x=i, y=l, text="<b>" + ", ".join(ids) + "</b>", showarrow=False, font=dict(color="white"))
        g.update_layout(height=380, title=tr("Matriz de risco", "Risk matrix"), xaxis=dict(title=tr("Impacto", "Impact"), dtick=1), yaxis=dict(title=tr("Probabilidade", "Likelihood"), dtick=1))
        out.append(fig(g))
        out.append(_interp(I.risk_text(p["risks"])))
        out.append(f"<h3>{tr('Matriz de gestão de riscos', 'Risk management matrix')}</h3>")
        out.append(f"<p style='font-size:0.85rem;color:#555'>{html.escape(tr(*RM.MATRIX_HELP))}</p>")
        out.append(RM.matrix_html(p))
        th = RM.threshold_check(p, sched.get("bac") if sched.get("ok") else None)
        out.append(_interp(th["text"] + " " + tr(*RM.THRESHOLD_HELP)))
    if p["budget"]:
        out.append(f"<h3>{tr('Orçamento', 'Budget')}</h3>")
        out.append(_df(pd.DataFrame([{tr("Atividade", "Activity"): b["activity_id"], tr("Categoria", "Category"): opt_label("cost_category", b["category"]), "Item": b["item"], tr("Qtd.", "Qty"): b["quantity"],
                                      tr("Custo unitário", "Unit cost"): money(b["unit_cost"], cur), "Total": money((b["quantity"] or 0) * (b["unit_cost"] or 0), cur)} for b in p["budget"]])))
    if p["procurement"]:
        out.append("<h3>Procurement</h3>")
        out.append(_df(pd.DataFrame([{"ID": q["id"], "Item": q["item"], tr("Método", "Method"): opt_label("procurement", q["method"]), tr("Custo", "Cost"): money(q["estimated_cost"], cur),
                                      tr("Data", "Date"): q["planned_date"], tr("Critérios", "Criteria"): q["selection_criteria"]} for q in p["procurement"]])))

    # ------------------------------------------------------------------ finance
    H(5, tr("Análise financeira", "Financial appraisal"))
    if fa:
        w = fa["wacc"]
        out.append(f"<p>Ke = {pct(w['ke'], 2)} · Kd {tr('após imposto', 'after tax')} = {pct(w['kd_after_tax'], 2)} · E/V = {pct(w['we'], 0)} · D/V = {pct(w['wd'], 0)} · <b>WACC = {pct(w['wacc'], 2)}</b></p>")
        tab = pd.DataFrame({tr("Ano", "Year"): range(len(fa["flows"])), tr("Investimento", "Investment"): fa["investment"], tr("Custos operacionais", "Operating costs"): fa["operating_costs"],
                            tr("Benefícios", "Benefits"): fa["benefits"], tr("Fluxo líquido", "Net flow"): fa["flows"], tr("Atualizado", "Discounted"): fa["discounted"]})
        out.append(_df(tab, {c: (lambda v: money(v, cur)) for c in tab.columns[1:]}))
        g = go.Figure()
        g.add_trace(go.Bar(x=tab.iloc[:, 0], y=fa["flows"], marker_color=["#C0392B" if v < 0 else "#2E8B57" for v in fa["flows"]], name=tr("Fluxo líquido", "Net flow")))
        g.add_trace(go.Scatter(x=tab.iloc[:, 0], y=fa["cum_disc"], name=tr("Acumulado atualizado", "Cumulative discounted"), line=dict(color="#1F3B57", width=3)))
        g.update_layout(height=360, title=tr("Fluxos de caixa", "Cash flows"))
        out.append(fig(g))
        out.append(_interp(I.finance_text(fa, cur, F.breakeven_benefit_factor(p["cashflows"], p["finance"], float(p["finance"].get("residual_value") or 0)))))

    # ------------------------------------------------------------------ M&E
    H(6, tr("Monitorização e avaliação", "Monitoring & evaluation"))
    if p["indicators"]:
        out.append(_df(pd.DataFrame([{"ID": i["id"], tr("Objetivo", "Objective"): i["objective_code"], tr("Indicador", "Indicator"): i["indicator"], "Baseline": i["baseline"], tr("Meta", "Target"): i["target"],
                                      tr("Atual", "Current"): i["current"], "SMART": f"{AN.smart_score(i)}/5", tr("Critério", "Criterion"): indicator_dimension(objective_level(p, i["objective_code"])),
                                      tr("Fonte", "Source"): i["source"]} for i in p["indicators"]])))
        out.append(_interp(I.indicators_text(p)))
        for i in p["indicators"]:
            b = AN.benchmark(i, [x for x in p["benchmarks"] if x.get("indicator_id") == i["id"]], [x for x in p["timeseries"] if x.get("indicator_id") == i["id"]])
            t = I.benchmark_text(i, b)
            if t:
                out.append(_interp(t, f"Benchmarking {i['id']}"))
    if e:
        sc_ = S.s_curve(p, sched)
        g = go.Figure()
        g.add_trace(go.Scatter(x=sc_["period"], y=sc_["pv_cum"], name="PV", line=dict(color="#1F3B57", width=3)))
        g.add_trace(go.Scatter(x=sc_["period"], y=sc_["ev_cum"], name="EV", line=dict(color="#2E8B57", width=3), connectgaps=True))
        g.add_trace(go.Scatter(x=sc_["period"], y=sc_["ac_cum"], name="AC", line=dict(color="#C0392B", width=3), connectgaps=True))
        g.update_layout(height=380, title="Earned Value — " + tr("curvas S", "S-curves"))
        out.append(fig(g))
        out.append(_interp(I.evm_text(e, cur), "EVM"))
    q = AN.quality_scores(p["quality"])
    if any(v is not None for v in q.values()):
        out.append(f"<h3>{tr('Atributos de qualidade (PCM)', 'Quality attributes (PCM)')}</h3><p>" + " · ".join(f"{k}: <b>{pct(v, 0) if v is not None else '—'}</b>" for k, v in q.items()) + "</p>")
    if p["evaluation"]:
        out.append(f"<h3>{tr('Matriz de avaliação', 'Evaluation matrix')}</h3>")
        out.append(_df(pd.DataFrame(p["evaluation"])[["criterion", "q_type", "question", "judgement_criteria", "indicator", "source", "data_tools", "method"]]))

    # ------------------------------------------------------------------ implementation & monitoring
    from . import monitor as M
    sch = sched if sched.get("ok") else None
    H(7, tr("Implementação e monitorização", "Implementation & monitoring"))
    ov = M.indicators_overview(p)
    if any(o["n"] for o in ov):
        out.append(f"<h3>{tr('Indicadores face à trajetória', 'Indicators against trajectory')}</h3>")
        out.append(_df(pd.DataFrame([{"ID": o["id"], "Baseline": o["baseline"], tr("Meta", "Target"): o["target"], tr("Último valor", "Last value"): o["last_value"],
                                      tr("Esperado", "Expected"): None if o["expected"] is None else round(o["expected"], 2),
                                      tr("Estado", "Status"): f"{M.STATUS_ICON[o['status']]} {M.status_label(o['status'])}"} for o in ov])))
        out.append(_interp(M.indicators_text(p)))
    ms = M.milestone_rows(p, sch)
    if ms:
        out.append(f"<h3>{tr('Marcos', 'Milestones')}</h3>")
        out.append(_df(pd.DataFrame([{"ID": r["id"], tr("Marco", "Milestone"): r.get("name"), tr("Previsto", "Planned"): d(r["planned"]) if r["planned"] else "—",
                                      tr("Real/previsão", "Actual/forecast"): d(r["actual"] or r["forecast"]) if (r["actual"] or r["forecast"]) else "—",
                                      tr("Desvio (dias)", "Deviation (days)"): r["deviation"], tr("Estado", "Status"): tr(*M.MS_LABEL[r["code"]])} for r in ms])))
        out.append(_interp(M.milestones_text(ms)))
    if p["changes"]:
        out.append(f"<h3>{tr('Alterações', 'Changes')}</h3>")
        out.append(_df(pd.DataFrame([{"ID": c["id"], tr("Elemento", "Element"): c["element_type"], tr("Descrição", "Description"): c["description"],
                                      tr("Classe", "Class"): M.change_class(c)[0], tr("Estado", "Status"): c["status"]} for c in p["changes"]])))
        out.append(_interp(M.changes_text(p, cur)))
    for title, txt in ((tr("Riscos (revisões)", "Risks (reviews)"), M.risks_review_text(p, cur)), (tr("Pressupostos (revisões)", "Assumptions (reviews)"), M.assumptions_text(p) if p["assumption_reviews"] else ""),
                       (tr("Contingência", "Contingency"), M.contingency_text(p, M.contingency_status(p, sched.get("bac")), (e["EV"] / e["BAC"]) if e and e.get("BAC") else None, cur)),
                       (tr("Tesouraria", "Cash"), M.cash_text(M.cash_position(p, sch), cur) if sch and p["funding"] else ""),
                       (tr("Stakeholders e feedback", "Stakeholders & feedback"), (M.engagement_text(p) + " " + M.feedback_text(p)) if (p["engagement"] or p["feedback"]) else ""),
                       (tr("Comunicação", "Communication"), M.comm_text(p, cur)), (tr("Concursos e contratos", "Tenders & contracts"), M.procurement_text(p, cur) if p["procurement"] else "")):
        if txt:
            out.append(_interp(txt, title))
    if sch and p["funding"]:
        cp = M.cash_position(p, sch)
        g = go.Figure()
        g.add_trace(go.Scatter(x=cp["period"], y=cp["pv_cum"], name=tr("Necessidades (PV acum.)", "Needs (cum. PV)"), line=dict(color="#1F3B57", width=3)))
        g.add_trace(go.Scatter(x=cp["period"], y=cp["funds_all_cum"], name=tr("Financiamento", "Funding"), line=dict(color="#2E8B57", width=3, shape="hv")))
        g.update_layout(height=340, title=tr("Tesouraria", "Cash position"))
        out.append(fig(g))

    # ------------------------------------------------------------------ evaluation & closure
    H(8, tr("Avaliação e encerramento", "Evaluation & closure"))
    ed = p["eval_design"]
    out.append(f"<p><b>{tr('Desenho da avaliação', 'Evaluation design')}:</b> {_e(opt_label('eval_type', ed.get('type')))} · {_e(opt_label('eval_timing', ed.get('timing')))} · "
               f"{_e(opt_label('eval_who', ed.get('who')))} · {_e(', '.join(opt_label('eval_purpose', x) for x in ed.get('purposes', [])))}</p>")
    out.append(_interp(M.evaluation_text(p), tr("Matriz de avaliação", "Evaluation matrix")))
    mq, sh = M.me_quality_score(p), M.me_budget_share(p)
    if mq is not None or sh is not None:
        out.append(f"<p>{tr('Qualidade do sistema de M&A', 'M&E system quality')}: <b>{pct(mq, 0) if mq is not None else '—'}</b> · {tr('Peso do M&A no orçamento', 'M&E share of budget')}: <b>{pct(sh) if sh is not None else '—'}</b></p>")
    for title, txt in ((tr("Eficiência e eficácia", "Efficiency & effectiveness"), M.efficiency_text(M.efficiency_panel(p, sch))),
                       (tr("Sustentabilidade", "Sustainability"), M.sustainability_text(p)), (tr("Encerramento", "Closure"), M.closure_text(p) if (p["audits"] or p["ownership"] or p["closure"]) else ""),
                       (tr("Lições aprendidas", "Lessons learned"), M.lessons_text(p))):
        if txt:
            out.append(_interp(txt, title))
    if p["lessons"]:
        out.append(_df(pd.DataFrame([{tr("Categoria", "Category"): opt_label("lesson_cat", x["category"]), tr("Lição", "Lesson"): x["lesson"], tr("Evidência", "Evidence"): x["evidence"],
                                      tr("Recomendação", "Recommendation"): x["recommendation"]} for x in p["lessons"]])))
    if p["dissemination"]:
        out.append(f"<h3>{tr('Disseminação', 'Dissemination')}</h3>")
        out.append(_df(pd.DataFrame([{tr("Canal", "Channel"): opt_label("diss_channel", x["channel"]), tr("Audiência", "Audience"): x["audience"], tr("Produto", "Product"): x["product"],
                                      tr("Data", "Date"): x["date"], tr("Alcance meta/real", "Reach target/actual"): f"{num(x['reach_target'])} / {num(x['reach_actual'])}"} for x in p["dissemination"]])))

    # ------------------------------------------------------------------ checks & references
    H(9, tr("Verificação de coerência", "Consistency check"))
    ch = I.checks(p, sched) + M.checks(p, sch)
    out.append(_df(pd.DataFrame([{"": {"error": "🔴", "warn": "🟠", "info": "🔵"}[x["sev"]], tr("Módulo", "Module"): x["module"], tr("Mensagem", "Message"): x["msg"]} for x in ch]))
               if ch else f"<p>{tr('Sem problemas detetados.', 'No issues found.')}</p>")
    H(10, tr("Referências", "References"))
    out.append("<ul>" + "".join(f"<li>{_md(v)}</li>" for v in SRC.values()) + "</ul>")

    toc = "".join(f"<li><a href='#s{n}'>{_e(t)}</a></li>" for n, t in sec)
    body = "\n".join(out)
    title = _e(m.get("name", "Projeto"))
    return f"""<!doctype html><html lang="{'pt' if tr('a', 'b') == 'a' else 'en'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — {tr('Relatório de projeto', 'Project report')}</title>
<style>
body{{font-family:Helvetica,Arial,sans-serif;color:#1d2733;max-width:1150px;margin:0 auto;padding:24px 18px;background:#fff;line-height:1.45}}
h1{{color:#1F3B57;margin-bottom:4px}} h2{{color:#1F3B57;border-bottom:3px solid #1F3B57;padding-bottom:4px;margin-top:40px}} h3{{color:#2C5F8A;margin-top:26px}}
.meta{{color:#5b6875}} .toc{{background:#F4F7FA;padding:10px 18px;border-radius:8px}} .toc li{{margin:2px 0}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:14px 0}}
.kpi{{background:#F4F7FA;border-radius:8px;padding:10px;text-align:center}} .kv{{font-size:1.25rem;font-weight:700;color:#1F3B57}} .kl{{font-size:.8rem;color:#5b6875}}
.interp{{border-left:5px solid #2C7FB8;background:#F2F8FC;padding:8px 14px;margin:12px 0;border-radius:4px}} .ai{{border-left:5px solid #8E44AD;background:#F7F1FA;padding:8px 14px;margin:12px 0;border-radius:4px}}
.it{{font-weight:700;margin-bottom:4px}} table.tbl{{border-collapse:collapse;width:100%;font-size:.84rem;margin:8px 0}}
.tbl th{{background:#1F3B57;color:#fff;padding:5px 7px;text-align:left}} .tbl td{{border:1px solid #D5DDE5;padding:5px 7px;vertical-align:top}}
.dot svg{{max-width:100%;height:auto}} .dot{{overflow-x:auto;margin:10px 0}} .fig{{margin:8px 0}}
.figbar{{margin:2px 0 10px}} .figbar button,.zipbar button{{font-size:.78rem;padding:3px 9px;margin-right:6px;border:1px solid #c9d2db;border-radius:6px;background:#fff;cursor:pointer;color:#1d2733}}
.figbar button:hover,.zipbar button:hover{{border-color:#1F6FB2;color:#1F6FB2}} .zipbar{{background:#F4F7FA;padding:8px 14px;border-radius:8px;margin:10px 0}} .zipbar span{{color:#5b6875;font-size:.85rem}}
@media print {{ h2{{page-break-before:always}} .toc,.figbar,.zipbar{{display:none}} }}
</style></head><body>
<h1>{title}</h1>
<div class="meta">{_e(m.get('industry', ''))} · {_e(m.get('organisation', ''))} · {_e(m.get('sponsor', ''))} · {tr('Relatório gerado em', 'Report generated on')} {d(date.today())}</div>
<p>{_e(m.get('description', ''))}</p>
<div class="toc"><b>{tr('Índice', 'Contents')}</b><ol>{toc}</ol></div>
<div class="zipbar"><button id="zipall">⬇️ {tr('Descarregar todas as figuras (ZIP, PNG alta resolução + SVG)', 'Download all figures (ZIP, high-resolution PNG + SVG)')}</button><span id="zipmsg">{tr('Cada figura tem também os seus próprios botões PNG/SVG.', 'Each figure also has its own PNG/SVG buttons.')}</span></div>
{body}
<p class="meta" style="margin-top:40px">PM Studio — Project Cycle Management · {tr('As interpretações automáticas baseiam-se em regras e devem ser validadas pelo gestor de projeto.', 'Automatic interpretations are rule-based and should be validated by the project manager.')}</p>
<script src="{VIZ}"></script>
<script src="{JSZIP}"></script>
<script>
const PROJ={json.dumps(_slug_r(m.get('name', 'projeto')))};
function slug(s){{return (s||'figura').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^A-Za-z0-9]+/g,'_').replace(/^_|_$/g,'').slice(0,60)||'figura';}}
function titleOf(el){{let n=el;while(n&&n!==document.body){{let p=n.previousElementSibling;while(p){{if(/^H[2-4]$/.test(p.tagName))return p.textContent;p=p.previousElementSibling;}}n=n.parentElement;}}return 'figura';}}
function save(blob,name){{const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();setTimeout(()=>{{URL.revokeObjectURL(a.href);a.remove();}},1500);}}
function svgPng(svg){{return new Promise(res=>{{const t=new XMLSerializer().serializeToString(svg);const w=svg.viewBox.baseVal&&svg.viewBox.baseVal.width?svg.viewBox.baseVal.width*96/72:svg.getBoundingClientRect().width,h=svg.viewBox.baseVal&&svg.viewBox.baseVal.height?svg.viewBox.baseVal.height*96/72:svg.getBoundingClientRect().height,k=3;
 const img=new Image();img.onload=()=>{{const c=document.createElement('canvas');c.width=Math.round(w*k);c.height=Math.round(h*k);const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);g.drawImage(img,0,0,c.width,c.height);c.toBlob(res,'image/png');}};img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(t);}});}}
async function figs(){{const out=[];let i=0;
 for(const el of document.querySelectorAll('.dot svg, .fig .js-plotly-plot')){{i++;const box=el.closest('.dot,.fig');const base=String(i).padStart(2,'0')+'_'+slug(titleOf(box));
  if(el.tagName.toLowerCase()==='svg'){{el.setAttribute('xmlns','http://www.w3.org/2000/svg');out.push({{base,kind:'dot',el}});}} else out.push({{base,kind:'plotly',el}});}}
 return out;}}
async function asPng(f){{if(f.kind==='dot')return await svgPng(f.el);const url=await Plotly.toImage(f.el,{{format:'png',scale:3}});return await (await fetch(url)).blob();}}
async function asSvg(f){{if(f.kind==='dot')return new Blob([new XMLSerializer().serializeToString(f.el)],{{type:'image/svg+xml'}});const url=await Plotly.toImage(f.el,{{format:'svg'}});return await (await fetch(url)).blob();}}
Viz.instance().then(async function(viz){{document.querySelectorAll('.dot').forEach(function(el){{try{{el.appendChild(viz.renderSVGElement(el.dataset.dot));}}catch(e){{el.textContent='Graphviz: '+e;}}}});
 for(const f of await figs()){{const bar=document.createElement('div');bar.className='figbar';
  const b1=document.createElement('button');b1.textContent='⬇️ PNG';b1.onclick=async()=>save(await asPng(f),PROJ+'_'+f.base+'.png');
  const b2=document.createElement('button');b2.textContent='⬇️ SVG';b2.onclick=async()=>save(await asSvg(f),PROJ+'_'+f.base+'.svg');
  bar.append(b1,b2);f.el.closest('.dot,.fig').after(bar);}}
}});
document.getElementById('zipall').onclick=async function(){{const msg=document.getElementById('zipmsg');const zip=new JSZip();const fs=await figs();let k=0;
 for(const f of fs){{k++;msg.textContent={json.dumps(tr('A preparar figura', 'Preparing figure'))}+' '+k+'/'+fs.length+'…';try{{zip.file(f.base+'.png',await asPng(f));zip.file(f.base+'.svg',await asSvg(f));}}catch(e){{console.log(e);}}}}
 save(await zip.generateAsync({{type:'blob'}}),PROJ+'_figuras.zip');msg.textContent={json.dumps(tr('ZIP pronto', 'ZIP ready'))}+' ('+fs.length+')';}};
</script>
</body></html>"""
