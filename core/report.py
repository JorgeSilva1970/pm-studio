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
from . import schedule as S
from .fmt import d, money, num, pct, unit_label
from .help_texts import SRC
from .i18n import opt_label, tr
from .matrix import logframe_classic_html, logframe_html
from .model import activity_cost, indicator_dimension, objective_level

VIZ = "https://cdn.jsdelivr.net/npm/@viz-js/viz@3.14.0/lib/viz-standalone.js"


def _e(s):
    return html.escape(str(s if s is not None else ""))


def _md(s: str) -> str:
    """Tiny markdown → HTML (bold/italic) for interpretation texts."""
    import re
    s = _e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)
    return s.replace("\n\n", "</p><p>").replace("\n", "<br>")


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
        out.append(f"<h3>Stakeholders</h3>")
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
        out.append(_df(pd.DataFrame([{tr("Estratégia", "Strategy"): s["name"], tr("Pontuação", "Score"): round(s["score"], 2), tr("Descrição", "Description"): s["description"]} for s in sc])))
        out.append(_interp(I.strategy_text(sc, p["strategies"].get("selected"))))

    # ------------------------------------------------------------------ formulation
    H(3, tr("Formulação — Logic Models", "Formulation — Logic Models"))
    out.append(f"<h3>{tr('Matriz do Quadro Lógico — vista clássica 4×4 (PCM)', 'Logical Framework Matrix — classic 4×4 view (PCM)')}</h3>"
               + logframe_classic_html(p, (p.get("logframe") or {}).get("terminology", "pcm")))
    out.append(f"<h3>{tr('Matriz do Quadro Lógico — vista alargada (baseline, meta, critério)', 'Logical Framework Matrix — extended view (baseline, target, criterion)')}</h3>" + logframe_html(p))
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
    if sched.get("ok"):
        df = sched["acts"]
        out.append(f"<h3>PERT / CPM</h3>")
        out.append(_df(df[["id", "name", "predecessors", "D", "ES", "EF", "LS", "LF", "TF", "FF", "critical"]].rename(columns={"name": tr("Atividade", "Activity"), "predecessors": tr("Predecessoras", "Predecessors"), "critical": tr("Crítica", "Critical")}),
                       {k: (lambda v: f"{v:.2f}") for k in ["D", "ES", "EF", "LS", "LF", "TF", "FF"]}))
        out.append(_dot(AN.network_dot(sched)))
        acts = [a for a in p["activities"] if a.get("id")]
        pp = C.pert_project(acts, sched["cpm"])
        T = p["meta"].get("target_duration")
        out.append(_interp(I.pert_text(pp, T, C.prob_by(T, pp["mean"], pp["sd"]) if T else None, sched["unit"])))
        mc = C.monte_carlo(acts, 5000)
        out.append(_interp(I.mc_text(mc, sched["unit"], T, pp["mean"]), "Monte Carlo"))
        out.append(f"<h3>{tr('Diagrama de Gantt', 'Gantt chart')}</h3>")
        gd = df.assign(Start=pd.to_datetime(df["start"]), Finish=pd.to_datetime(df["finish"]) + pd.Timedelta(hours=12),
                       Status=df["critical"].map({True: tr("Crítica", "Critical"), False: tr("Não crítica", "Non-critical")}), Task=df["id"] + " " + df["name"].str.slice(0, 40))
        g = px.timeline(gd, x_start="Start", x_end="Finish", y="Task", color="Status", color_discrete_map={tr("Crítica", "Critical"): "#E4572E", tr("Não crítica", "Non-critical"): "#3C8DBC"})
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
    if p["budget"]:
        out.append(f"<h3>{tr('Orçamento', 'Budget')}</h3>")
        out.append(_df(pd.DataFrame([{tr("Atividade", "Activity"): b["activity_id"], tr("Categoria", "Category"): opt_label("cost_category", b["category"]), "Item": b["item"], tr("Qtd.", "Qty"): b["quantity"],
                                      tr("Custo unitário", "Unit cost"): money(b["unit_cost"], cur), "Total": money((b["quantity"] or 0) * (b["unit_cost"] or 0), cur)} for b in p["budget"]])))
    if p["procurement"]:
        out.append(f"<h3>Procurement</h3>")
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
        out.append(_df(pd.DataFrame(p["evaluation"])[["criterion", "question", "judgement_criteria", "indicator", "source", "method"]]))

    # ------------------------------------------------------------------ checks & references
    H(7, tr("Verificação de coerência", "Consistency check"))
    ch = I.checks(p, sched)
    out.append(_df(pd.DataFrame([{"": {"error": "🔴", "warn": "🟠", "info": "🔵"}[x["sev"]], tr("Módulo", "Module"): x["module"], tr("Mensagem", "Message"): x["msg"]} for x in ch]))
               if ch else f"<p>{tr('Sem problemas detetados.', 'No issues found.')}</p>")
    H(8, tr("Referências", "References"))
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
@media print {{ h2{{page-break-before:always}} .toc{{display:none}} }}
</style></head><body>
<h1>{title}</h1>
<div class="meta">{_e(m.get('industry', ''))} · {_e(m.get('organisation', ''))} · {_e(m.get('sponsor', ''))} · {tr('Relatório gerado em', 'Report generated on')} {d(date.today())}</div>
<p>{_e(m.get('description', ''))}</p>
<div class="toc"><b>{tr('Índice', 'Contents')}</b><ol>{toc}</ol></div>
{body}
<p class="meta" style="margin-top:40px">PM Studio — Project Cycle Management · {tr('As interpretações automáticas baseiam-se em regras e devem ser validadas pelo gestor de projeto.', 'Automatic interpretations are rule-based and should be validated by the project manager.')}</p>
<script src="{VIZ}"></script>
<script>
Viz.instance().then(function(viz){{document.querySelectorAll('.dot').forEach(function(el){{try{{el.appendChild(viz.renderSVGElement(el.dataset.dot));}}catch(e){{el.textContent='Graphviz: '+e;}}}});}});
</script>
</body></html>"""
