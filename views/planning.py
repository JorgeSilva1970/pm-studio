"""3 · Planning: activities/WBS, PERT/CPM (+Monte Carlo, crashing, what-if), Gantt & time-phased cost,
RACI, risks, budget & cash flow, contingencies, procurement."""
import copy
import math
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import analysis as AN
from core import cpm as C
from core import interpret as I
from core import schedule as S
from core import ui
from core.fmt import d, money, num, pct, unit_label
from core.i18n import opt_codes, opt_label, tr
from core.model import activity_cost, empty_row, next_id

CRIT = "#E4572E"
NONC = "#3C8DBC"


def _outputs(p):
    return [""] + [str(o["code"]) for o in p["objectives"]]


# ============================================================================= activities
def activities():
    p = ui.P()
    ui.header("Atividades de produção e de apoio (WBS)", "Production & support activities (WBS)", "activities", "📋")
    u = unit_label(p["meta"].get("time_unit", "weeks"))
    st.caption(tr(f"Durações em **{u}** (alterar em Início → Dados do projeto). Predecessoras separadas por vírgulas (ex.: A1, A3).",
                  f"Durations in **{u}** (change in Home → Project settings). Predecessors comma-separated (e.g. A1, A3)."))
    ov = {"output_code": st.column_config.SelectboxColumn(ui.label("output_code"), options=_outputs(p))}
    rows = ui.edit_table("activities", columns=["id", "name", "output_code", "type", "predecessors", "optimistic", "most_likely", "pessimistic",
                                                "cost", "distribution", "responsible", "milestone"], overrides=ov, height=420)
    errs = C.validate([a for a in rows if a.get("id")]) if rows else []
    if errs:
        st.error(tr("Problemas na rede de atividades:", "Activity network issues:") + "\n\n" + "\n".join(f"- {e}" for e in errs))
    elif rows:
        sched = S.compute(p)
        st.success(tr(f"Rede válida · duração {num(sched['cpm']['duration'], 1)} {u} · caminho crítico {' → '.join(sched['cpm']['critical_path'])}",
                      f"Valid network · duration {num(sched['cpm']['duration'], 1)} {u} · critical path {' → '.join(sched['cpm']['critical_path'])}"))

    with st.expander(tr("🪄 Assistente: acrescentar e gerar atividades de forma inteligente", "🪄 Assistant: add and generate activities smartly"), expanded=not rows):
        t1, t2, t3 = st.tabs([tr("➕ Acrescentar várias", "➕ Add several"), tr("🧩 Gerar a partir do logframe", "🧩 Generate from logframe"),
                              tr("📐 Completar estimativas PERT", "📐 Complete PERT estimates")])
        with t1:
            with st.form("add_many"):
                c1, c2, c3 = st.columns(3)
                n = c1.number_input(tr("N.º de atividades", "Number of activities"), 1, 50, 3)
                base = c2.text_input(tr("Nome base", "Base name"), tr("Tarefa", "Task"))
                out = c3.selectbox(ui.label("output_code"), _outputs(p))
                c1, c2, c3, c4 = st.columns(4)
                m = c1.number_input(tr("Duração mais provável", "Most likely duration"), 0.0, 1000.0, 2.0)
                unc = c2.slider(tr("Incerteza (pessimista = m × (1+x))", "Uncertainty (pessimistic = m × (1+x))"), 0.0, 2.0, 0.5)
                cost = c3.number_input(tr("Custo por atividade", "Cost per activity"), 0.0, 1e9, 0.0, step=1000.0)
                link = c4.selectbox(tr("Encadeamento", "Linking"), ["chain", "parallel", "after_last"],
                                    format_func=lambda v: {"chain": tr("Em série (cada uma após a anterior)", "In series (each after the previous)"),
                                                           "parallel": tr("Em paralelo", "In parallel"), "after_last": tr("Todas após a última existente", "All after the last existing")}[v])
                after = st.text_input(tr("Predecessora inicial (opcional)", "Initial predecessor (optional)"))
                if st.form_submit_button(tr("Acrescentar", "Add"), type="primary"):
                    last = p["activities"][-1]["id"] if p["activities"] else ""
                    prev = after.strip() or (last if link == "after_last" else "")
                    for k in range(int(n)):
                        a = empty_row("activities")
                        a.update({"id": next_id(p["activities"], "A"), "name": f"{base} {k + 1}", "output_code": out, "most_likely": m,
                                  "optimistic": round(m * max(0.0, 1 - unc / 2), 2), "pessimistic": round(m * (1 + unc), 2), "cost": cost,
                                  "predecessors": prev})
                        p["activities"].append(a)
                        if link == "chain":
                            prev = a["id"]
                    ui.bump()
                    st.rerun()
        with t2:
            st.caption(tr("Cria uma atividade de produção para cada output sem atividades e as atividades de apoio em falta (comunicação, M&A, gestão).",
                          "Creates one production activity per output without activities and the missing support activities (communication, M&E, management)."))
            if st.button(tr("⚙️ Gerar", "⚙️ Generate")):
                n = generate_from_logframe(p)
                ui.bump()
                st.success(tr(f"{n} atividades criadas.", f"{n} activities created."))
        with t3:
            st.caption(tr("Para atividades em que otimista = pessimista, propõe a = m × (1 − x) e b = m × (1 + y). Útil quando só existe a estimativa 'mais provável'.",
                          "For activities where optimistic = pessimistic, sets a = m × (1 − x) and b = m × (1 + y). Useful when only the 'most likely' estimate exists."))
            c1, c2 = st.columns(2)
            x = c1.slider(tr("Redução otimista x", "Optimistic reduction x"), 0.0, 0.9, 0.2)
            y = c2.slider(tr("Acréscimo pessimista y", "Pessimistic increase y"), 0.0, 3.0, 0.5)
            if st.button(tr("Aplicar estimativas", "Apply estimates")):
                k = 0
                for a in p["activities"]:
                    if (a.get("optimistic") or 0) == (a.get("pessimistic") or 0) and not a.get("milestone"):
                        m_ = float(a.get("most_likely") or 0)
                        a["optimistic"], a["pessimistic"] = round(m_ * (1 - x), 2), round(m_ * (1 + y), 2)
                        k += 1
                ui.bump()
                st.success(tr(f"{k} atividades atualizadas.", f"{k} activities updated."))

    if rows:
        st.markdown(tr("##### Estrutura de decomposição do trabalho (WBS) — área proporcional ao custo", "##### Work breakdown structure (WBS) — area proportional to cost"))
        objs = {str(o["code"]): o for o in p["objectives"]}
        recs = []
        for a in p["activities"]:
            oc = str(a.get("output_code") or "")
            o = objs.get(oc)
            parent = objs.get(str(o.get("parent"))) if o else None
            grp = f"{oc} {o['text'][:40]}" if o else tr("Apoio / gestão", "Support / management")
            top = f"{parent['code']} {parent['text'][:40]}" if parent else (tr("Apoio / gestão", "Support / management") if not o else grp)
            recs.append({"project": p["meta"]["name"][:40], "level1": top, "level2": grp, "activity": f"{a['id']} {a.get('name', '')[:40]}", "cost": max(activity_cost(p, a), 1)})
        df = pd.DataFrame(recs)
        fig = px.treemap(df, path=["project", "level1", "level2", "activity"], values="cost", color="level1")
        fig.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width="stretch")


def generate_from_logframe(p) -> int:
    n = 0
    for o in [o for o in p["objectives"] if o["level"] == "Output"]:
        if not any(str(a.get("output_code")) == str(o["code"]) for a in p["activities"]):
            a = empty_row("activities")
            a.update({"id": next_id(p["activities"], "A"), "name": tr("Produzir: ", "Deliver: ") + o["text"][:60], "output_code": o["code"],
                      "optimistic": 2, "most_likely": 3, "pessimistic": 5})
            p["activities"].append(a)
            n += 1
    types = {a.get("type") for a in p["activities"]}
    for t, pt, en in (("Support - Communication", "Comunicação e visibilidade", "Communication & visibility"),
                      ("Support - M&E", "Monitorização e avaliação", "Monitoring & evaluation"),
                      ("Support - Management", "Gestão do projeto", "Project management")):
        if t not in types:
            a = empty_row("activities")
            a.update({"id": next_id(p["activities"], "A"), "name": tr(pt, en), "type": t, "optimistic": 1, "most_likely": 1, "pessimistic": 1})
            p["activities"].append(a)
            n += 1
    return n


# ============================================================================= PERT / CPM
def pert():
    p = ui.P()
    ui.header("PERT / CPM — caminho crítico, probabilidades e compressão", "PERT / CPM — critical path, probabilities & crashing", "pert", "🕸️")
    scen = p.setdefault("pert_scenarios", [])
    m = p["meta"]
    opts = ["project"] + [f"scen:{k}" for k in range(len(scen))] + ["prof"]
    if st.session_state.pop("_pert_reset", False) or st.session_state.get("pert_src") not in opts:
        st.session_state["pert_src"] = "project"
    src = st.selectbox(tr("Rede a analisar", "Network to analyse"), opts,
                       format_func=lambda o: tr("📁 Atividades deste projeto (editáveis)", "📁 This project's activities (editable)") if o == "project"
                       else tr("🎓 Exemplo do professor A–H (apenas referência)", "🎓 Professor's example A–H (reference only)") if o == "prof"
                       else tr("💾 Cenário: ", "💾 Scenario: ") + scen[int(o[5:])]["name"], key="pert_src")
    example = src == "prof"
    if src == "project":
        acts, unit, mode = _pert_variables(p)
        costs = {a["id"]: activity_cost(p, a) for a in acts}
    elif example:
        acts = copy.deepcopy(C.PROFESSOR_CPM_EXAMPLE)
        unit, mode, costs = "days", "ml", {a["id"]: 1000.0 for a in acts}
        for a in acts:
            a["crash_duration"], a["crash_cost"] = max(1, a["most_likely"] - 1), 1500.0
        st.info(tr("Exemplo do material 'Determine Duration with CPM or PERT' (A → B → D → G → H, duração 19), apenas para comparação. Os seus projetos usam as próprias atividades e variáveis.",
                   "Example from 'Determine Duration with CPM or PERT' (A → B → D → G → H, duration 19), for comparison only. Your projects use their own activities and variables."))
    else:
        sc = scen[int(src[5:])]
        acts = [a for a in copy.deepcopy(sc["activities"]) if a.get("id")]
        unit, mode = sc.get("time_unit", m.get("time_unit", "weeks")), sc.get("duration_mode", m.get("duration_mode", "pert"))
        costs = {a["id"]: float(a.get("cost") or 0) for a in acts}
        c1, c2 = st.columns([3, 1])
        c1.info(tr(f"Cenário guardado em {sc.get('created', '')} com {len(acts)} atividades (só leitura). Para o alterar, reponha-o no projeto.",
                   f"Scenario saved on {sc.get('created', '')} with {len(acts)} activities (read only). To change it, restore it into the project."))
        if c2.button(tr("↩️ Repor no projeto", "↩️ Restore into project"), help=tr("Substitui as atividades do projeto por este cenário", "Replaces the project's activities with this scenario")):
            p["activities"] = copy.deepcopy(sc["activities"])
            m["time_unit"], m["duration_mode"] = unit, mode
            ui.bump()
            st.session_state["_pert_reset"] = True
            st.rerun()
    _pert_scenarios(p, src)
    if not acts:
        st.warning(tr("Este projeto ainda não tem atividades: acrescente-as acima (variáveis do modelo).", "This project has no activities yet: add them above (model variables)."))
        return
    errs = C.validate(acts)
    if errs:
        st.error(tr("Corrija a rede para calcular o caminho crítico:", "Fix the network to compute the critical path:") + "\n\n" + "\n".join(f"- {e}" for e in errs))
        return
    u = unit_label(unit)
    dur = C.durations(acts, mode)
    res = C.cpm(acts, dur)
    by = {a["id"]: a for a in acts}
    c = st.columns(4)
    c[0].metric(tr("Duração do projeto", "Project duration"), f"{num(res['duration'], 2)} {u}")
    c[1].metric(tr("Atividades críticas", "Critical activities"), f"{sum(v['critical'] for v in res['table'].values())}/{len(acts)}")
    pp = C.pert_project(acts, res)
    c[2].metric(tr("Desvio-padrão (PERT)", "Std. deviation (PERT)"), f"{num(pp['sd'], 2)} {u}")
    c[3].metric(tr("Fim previsto", "Planned finish"), d(S.to_date(p["meta"]["start_date"]) + timedelta(days=res["duration"] * S.UNIT_DAYS.get(unit, 7))) if not example else f"{num(res['duration'], 0)} {u}")
    st.markdown(tr("**🔴 Caminho crítico:** ", "**🔴 Critical path:** ") + " → ".join(res["critical_path"]))
    if len(res.get("paths", [])) > 1:
        st.caption(tr("Caminhos críticos alternativos: ", "Alternative critical paths: ") + " · ".join(" → ".join(x) for x in res["paths"][1:]))

    t1, t2, t3, t4, t5, t6 = st.tabs([tr("📋 Tabela CPM", "📋 CPM table"), tr("🕸️ Diagrama de rede", "🕸️ Network diagram"),
                                      tr("🎲 Probabilidade PERT", "🎲 PERT probability"), tr("🎰 Monte Carlo", "🎰 Monte Carlo"),
                                      tr("⏩ Compressão (crashing)", "⏩ Crashing"), tr("🔧 What-if", "🔧 What-if")])
    with t1:
        rows = []
        for i in res["order"]:
            t = res["table"][i]
            a = by[i]
            rows.append({"ID": i, tr("Atividade", "Activity"): a.get("name", ""), tr("Predecessoras", "Predecessors"): a.get("predecessors", ""),
                         "a": a.get("optimistic"), "m": a.get("most_likely"), "b": a.get("pessimistic"),
                         "tₑ / D": round(t["D"], 2), "σ²": round(C.pert_var(a.get("optimistic"), a.get("pessimistic")), 3),
                         "ES": round(t["ES"], 2), "EF": round(t["EF"], 2), "LS": round(t["LS"], 2), "LF": round(t["LF"], 2),
                         "TF": round(t["TF"], 2), "FF": round(t["FF"], 2), tr("Crítica", "Critical"): "🔴" if t["critical"] else ""})
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, width="stretch", height=min(600, 40 + 35 * len(df)))
        st.download_button("⬇️ CSV", df.to_csv(index=False).encode("utf-8"), "cpm.csv", "text/csv")
        sched = {"ok": True, "cpm": res, "acts": pd.DataFrame([{"id": i, "name": by[i].get("name", ""), "predecessors": by[i].get("predecessors", ""), **res["table"][i]} for i in res["order"]]),
                 "unit": unit, "start": S.to_date(p["meta"]["start_date"]), "finish": S.to_date(p["meta"]["start_date"]) + timedelta(days=res["duration"] * S.UNIT_DAYS.get(unit, 7))}
        ui.interpret(I.cpm_text(sched))
    with t2:
        ui.graph(AN.network_dot(sched))
        st.caption(tr("Caixa: ES | ID | EF (em cima) e LS | D | LF (em baixo); TF = folga total. Setas vermelhas = caminho crítico.",
                      "Box: ES | ID | EF (top) and LS | D | LF (bottom); TF = total float. Red arrows = critical path."))
    with t3:
        tgt_default = float(p["meta"].get("target_duration") or round(pp["mean"] * 1.05, 1)) if not example else 20.0
        T = st.slider(tr(f"Prazo-alvo ({u})", f"Target deadline ({u})"), float(max(0.0, pp["mean"] - 4 * pp["sd"] - 1)), float(pp["mean"] + 4 * pp["sd"] + 2),
                      float(min(max(tgt_default, pp["mean"] - 4 * pp["sd"] - 1), pp["mean"] + 4 * pp["sd"] + 2)), step=0.5)
        prob = C.prob_by(T, pp["mean"], pp["sd"])
        c1, c2, c3 = st.columns(3)
        c1.metric(tr("P(concluir até T)", "P(finish by T)"), pct(prob))
        c2.metric(tr("Duração com 90% de confiança", "Duration at 90% confidence"), f"{num(C.duration_for_prob(0.9, pp['mean'], pp['sd']), 1)} {u}")
        c3.metric("Z", num((T - pp["mean"]) / pp["sd"], 2) if pp["sd"] else "—")
        if pp["sd"] > 0:
            xs = np.linspace(pp["mean"] - 4 * pp["sd"], pp["mean"] + 4 * pp["sd"], 200)
            from scipy import stats
            ys = stats.norm.pdf(xs, pp["mean"], pp["sd"])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#1F3B57"), name="N(μ, σ)"))
            m = xs <= T
            fig.add_trace(go.Scatter(x=xs[m], y=ys[m], fill="tozeroy", mode="none", fillcolor="rgba(46,139,87,0.35)", name=f"P = {pct(prob)}"))
            fig.add_vline(x=T, line_dash="dash", line_color=CRIT)
            fig.update_layout(height=320, xaxis_title=u, yaxis_title=tr("Densidade", "Density"), margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info(tr("Sem incerteza: otimista = mais provável = pessimista em todas as atividades do caminho crítico.",
                       "No uncertainty: optimistic = most likely = pessimistic for every critical activity."))
        ui.interpret(I.pert_text(pp, T, prob, unit))
    with t4:
        c1, c2 = st.columns(2)
        n = c1.select_slider(tr("N.º de simulações", "Number of simulations"), [1000, 2000, 5000, 10000, 20000], value=5000)
        dist = c2.radio(tr("Distribuição", "Distribution"), ["betapert", "triangular"], horizontal=True, format_func=lambda v: "Beta-PERT" if v == "betapert" else tr("Triangular", "Triangular"))
        mc = C.monte_carlo(acts, n=int(n), dist=dist)
        c = st.columns(4)
        c[0].metric(tr("Média", "Mean"), f"{num(mc['mean'], 1)} {u}")
        c[1].metric("P50", num(mc["percentiles"]["P50"], 1))
        c[2].metric("P80", num(mc["percentiles"]["P80"], 1))
        c[3].metric("P90", num(mc["percentiles"]["P90"], 1))
        c1, c2 = st.columns(2)
        fig = go.Figure(go.Histogram(x=mc["samples"], nbinsx=50, marker_color="#7FA7C9", name=tr("Frequência", "Frequency")))
        for q, colr in (("P50", "#1F3B57"), ("P80", "#D9822B"), ("P90", CRIT)):
            fig.add_vline(x=mc["percentiles"][q], line_dash="dot", line_color=colr, annotation_text=q)
        fig.update_layout(height=320, xaxis_title=u, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        c1.plotly_chart(fig, width="stretch")
        xs = np.sort(mc["samples"])
        fig = go.Figure(go.Scatter(x=xs, y=np.arange(1, len(xs) + 1) / len(xs), mode="lines", line=dict(color="#1F3B57")))
        fig.update_layout(height=320, xaxis_title=u, yaxis_title=tr("Probabilidade acumulada", "Cumulative probability"), yaxis_tickformat=".0%", margin=dict(l=10, r=10, t=10, b=10))
        c2.plotly_chart(fig, width="stretch")
        ci = pd.DataFrame([{"ID": k, tr("Índice de criticidade", "Criticality index"): v} for k, v in sorted(mc["criticality"].items(), key=lambda kv: -kv[1])])
        fig = go.Figure(go.Bar(x=ci["ID"], y=ci.iloc[:, 1], marker_color=[CRIT if v >= 0.95 else "#D9822B" if v >= 0.2 else NONC for v in ci.iloc[:, 1]]))
        fig.update_layout(height=260, yaxis_tickformat=".0%", yaxis_title=tr("% das simulações em que é crítica", "% of runs where critical"), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        ui.interpret(I.mc_text(mc, unit, p["meta"].get("target_duration") if not example else 20, pp["mean"]))
    with t5:
        st.caption(tr("Para cada atividade indique a duração mínima (crash) e o custo total nessa duração na página 'Atividades' (colunas 'Duração crash' e 'Custo crash'). "
                      "A otimização (programação linear) escolhe as reduções de menor custo.",
                      "For each activity set the minimum (crash) duration and the total cost at that duration on the 'Activities' page ('Crash duration' and 'Crash cost'). "
                      "The optimisation (linear programming) picks the cheapest reductions."))
        cd = C.crash_data(acts, dur, costs)
        tab = pd.DataFrame([{"ID": k, tr("Normal", "Normal"): round(v["normal"], 2), "Crash": round(v["crash"], 2), tr("Redução máx.", "Max. reduction"): round(v["max_red"], 2),
                             tr("Custo/unidade (declive)", "Cost per unit (slope)"): (round(v["slope"], 0) if math.isfinite(v["slope"]) else "—")} for k, v in cd.items()])
        with st.expander(tr("Dados de compressão por atividade", "Crashing data per activity")):
            st.dataframe(tab, hide_index=True, width="stretch")
        curve = C.crash_curve(acts, dur, costs, steps=10)
        if len(curve) > 1:
            dmin = min(c_["duration"] for c_ in curve)
            T2 = st.slider(tr(f"Novo prazo pretendido ({u})", f"Desired new deadline ({u})"), float(dmin), float(res["duration"]), float(res["duration"]), step=0.5)
            r = C.crash_to(acts, dur, costs, T2)
            c1, c2 = st.columns([2, 3])
            if r.get("feasible"):
                c1.metric(tr("Custo adicional", "Extra cost"), money(r["extra_cost"], p["meta"].get("currency", "EUR")))
                c1.dataframe(pd.DataFrame([{"ID": k, tr("Redução", "Reduction"): round(v, 2), tr("Nova duração", "New duration"): round(r["durations"][k], 2)}
                                           for k, v in r["reductions"].items() if v > 1e-6]), hide_index=True)
            fig = go.Figure(go.Scatter(x=[c_["duration"] for c_ in curve], y=[c_["total_cost"] for c_ in curve], mode="lines+markers", line=dict(color="#1F3B57")))
            fig.add_vline(x=T2, line_dash="dash", line_color=CRIT)
            fig.update_layout(height=320, xaxis_title=tr(f"Duração ({u})", f"Duration ({u})"), yaxis_title=tr("Custo total", "Total cost"),
                              title=tr("Curva tempo-custo", "Time-cost curve"), margin=dict(l=10, r=10, t=40, b=10))
            c2.plotly_chart(fig, width="stretch")
            ui.interpret(I.crash_text(r, res["duration"], unit, p["meta"].get("currency", "EUR")))
        else:
            st.info(tr("Nenhuma atividade crítica tem dados de compressão — preencha 'Duração crash' e 'Custo crash'.",
                       "No critical activity has crashing data — fill in 'Crash duration' and 'Crash cost'."))
    with t6:
        st.caption(tr("Simule alterações sem mexer no plano: atrasar uma atividade ou aplicar um fator a todas as durações.",
                      "Simulate changes without touching the plan: delay one activity or apply a factor to every duration."))
        c1, c2, c3 = st.columns(3)
        aid = c1.selectbox(tr("Atividade a atrasar", "Activity to delay"), [a["id"] for a in acts])
        delay = c2.number_input(tr(f"Atraso ({u})", f"Delay ({u})"), 0.0, 1000.0, 1.0)
        fac = c3.slider(tr("Fator global nas durações", "Global duration factor"), 0.5, 2.0, 1.0, 0.05)
        d2 = {k: v * fac for k, v in dur.items()}
        d2[aid] += delay
        r2 = C.cpm(acts, d2)
        delta = r2["duration"] - res["duration"]
        st.metric(tr("Nova duração", "New duration"), f"{num(r2['duration'], 2)} {u}", delta=f"{num(delta, 2)}", delta_color="inverse")
        tf = res["table"][aid]["TF"]
        ui.interpret(tr(f"A atividade **{aid}** tem folga total de **{num(tf, 2)} {u}**: um atraso de {num(delay, 2)} "
                        + ("é absorvido pela folga." if delay <= tf + 1e-9 and fac == 1 else f"aumenta a duração do projeto em **{num(delta, 2)} {u}**.")
                        + f" Novo caminho crítico: {' → '.join(r2['critical_path'])}.",
                        f"Activity **{aid}** has **{num(tf, 2)} {u}** of total float: a delay of {num(delay, 2)} "
                        + ("is absorbed by the float." if delay <= tf + 1e-9 and fac == 1 else f"extends the project by **{num(delta, 2)} {u}**.")
                        + f" New critical path: {' → '.join(r2['critical_path'])}."))


def _pert_variables(p):
    """Editable model variables for this project: activities, precedences, a/m/b durations, costs, crash data."""
    m = p["meta"]
    with st.expander(tr("✏️ Variáveis do modelo deste projeto — atividades, precedências e durações", "✏️ This project's model variables — activities, precedences and durations"), expanded=True):
        c1, c2, c3 = st.columns(3)
        tu = c1.selectbox(tr("Unidade de tempo", "Time unit"), opt_codes("time_unit"), index=opt_codes("time_unit").index(m.get("time_unit", "weeks")),
                          format_func=lambda c: opt_label("time_unit", c), key=f"pu_{st.session_state.dv}")
        dm = c2.selectbox(tr("Duração usada no CPM", "Duration used in CPM"), ["pert", "ml"], index=0 if m.get("duration_mode", "pert") == "pert" else 1,
                          format_func=lambda x: "PERT tₑ = (a + 4m + b)/6" if x == "pert" else tr("Mais provável (m)", "Most likely (m)"), key=f"pm_{st.session_state.dv}")
        td = c3.number_input(tr("Prazo-alvo (para probabilidades)", "Target deadline (for probabilities)"), 0.0, 1e5, float(m.get("target_duration") or 0), 0.5, key=f"pt_{st.session_state.dv}")
        if (tu, dm, td or None) != (m.get("time_unit"), m.get("duration_mode"), m.get("target_duration")):
            m["time_unit"], m["duration_mode"], m["target_duration"] = tu, dm, td or None
            ui.mark_dirty()
        st.caption(tr("Edite, acrescente (linha vazia no fim da tabela) ou apague linhas: o caminho crítico, o diagrama e as probabilidades recalculam-se automaticamente.",
                      "Edit, add (empty row at the bottom) or delete rows: the critical path, diagram and probabilities recompute automatically."))
        ov = {"output_code": st.column_config.SelectboxColumn(ui.label("output_code"), options=_outputs(p))}
        ui.edit_table("activities", columns=["id", "name", "output_code", "predecessors", "optimistic", "most_likely", "pessimistic", "cost",
                                             "crash_duration", "crash_cost", "milestone"], key="pert", overrides=ov, height=360)
        ids = [a["id"] for a in p["activities"] if a.get("id")]
        a1, a2 = st.columns(2)
        with a1.form("pert_add", clear_on_submit=True):
            st.markdown(tr("**➕ Nova atividade**", "**➕ New activity**"))
            nm = st.text_input(tr("Nome", "Name"))
            pr = st.multiselect(tr("Predecessoras", "Predecessors"), ids)
            x1, x2, x3, x4 = st.columns(4)
            a_ = x1.number_input("a", 0.0, 1e5, 1.0)
            m_ = x2.number_input("m", 0.0, 1e5, 2.0)
            b_ = x3.number_input("b", 0.0, 1e5, 4.0)
            cs = x4.number_input(tr("Custo", "Cost"), 0.0, 1e12, 0.0, step=1000.0)
            if st.form_submit_button(tr("Acrescentar", "Add"), type="primary"):
                if not (a_ <= m_ <= b_):
                    st.error(tr("Tem de ser a ≤ m ≤ b.", "Must be a ≤ m ≤ b."))
                else:
                    a = empty_row("activities")
                    a.update({"id": next_id(p["activities"], "A"), "name": nm or tr("Nova atividade", "New activity"), "predecessors": ", ".join(pr),
                              "optimistic": a_, "most_likely": m_, "pessimistic": b_, "cost": cs})
                    p["activities"].append(a)
                    ui.bump()
                    st.rerun()
        with a2.form("pert_del"):
            st.markdown(tr("**🗑️ Remover atividade** (limpa também as precedências que a referem)", "**🗑️ Remove activity** (also cleans precedences referring to it)"))
            rid = st.selectbox(tr("Atividade", "Activity"), ids) if ids else None
            if st.form_submit_button(tr("Remover", "Remove")) and rid:
                p["activities"] = [a for a in p["activities"] if a.get("id") != rid]
                for a in p["activities"]:
                    a["predecessors"] = ", ".join(x for x in C.parse_preds(a.get("predecessors")) if x != rid)
                ui.bump()
                st.rerun()
    acts = [a for a in p["activities"] if a.get("id")]
    return acts, m.get("time_unit", "weeks"), m.get("duration_mode", "pert")


def _pert_scenarios(p, src):
    """Save the project's network as named scenarios and compare them."""
    scen = p["pert_scenarios"]
    m = p["meta"]
    with st.expander(tr(f"💾 Cenários deste projeto ({len(scen)}) — guardar e comparar variantes da rede", f"💾 Scenarios of this project ({len(scen)}) — save and compare network variants")):
        c1, c2 = st.columns([3, 1])
        name = c1.text_input(tr("Nome do cenário", "Scenario name"), value=tr(f"Cenário {len(scen) + 1}", f"Scenario {len(scen) + 1}"), key=f"scn_{len(scen)}")
        if c2.button(tr("💾 Guardar rede atual", "💾 Save current network"), disabled=not p["activities"]):
            from datetime import date as _d
            scen.append({"name": name, "created": _d.today().isoformat(), "time_unit": m.get("time_unit"), "duration_mode": m.get("duration_mode"),
                         "activities": copy.deepcopy(p["activities"])})
            ui.mark_dirty()
            st.rerun()
        rows = []
        T = m.get("target_duration")
        cands = [(tr("Projeto (atual)", "Project (current)"), p["activities"], m.get("time_unit"), m.get("duration_mode"))] + \
                [(s["name"], s["activities"], s.get("time_unit"), s.get("duration_mode")) for s in scen]
        for nm, al, tu, dm in cands:
            al = [a for a in al if a.get("id")]
            if not al or C.validate(al):
                rows.append({tr("Cenário", "Scenario"): nm, tr("Atividades", "Activities"): len(al), tr("Duração", "Duration"): None, "σ": None,
                             tr("Caminho crítico", "Critical path"): tr("rede inválida", "invalid network"), "P(T)": None, tr("Custo", "Cost"): None})
                continue
            r = C.cpm(al, C.durations(al, dm or "pert"))
            pp_ = C.pert_project(al, r)
            rows.append({tr("Cenário", "Scenario"): nm, tr("Atividades", "Activities"): len(al), tr("Duração", "Duration"): f"{num(r['duration'], 2)} {unit_label(tu or 'weeks')}",
                         "σ": round(pp_["sd"], 2), tr("Caminho crítico", "Critical path"): " → ".join(r["critical_path"]),
                         "P(T)": pct(C.prob_by(T, pp_["mean"], pp_["sd"])) if T else "—", tr("Custo", "Cost"): sum(float(a.get("cost") or 0) for a in al)})
        st.dataframe(pd.DataFrame(rows).style.format({tr("Custo", "Cost"): "{:,.0f}"}, na_rep="—"), hide_index=True, width="stretch")
        if scen:
            d1, d2 = st.columns([3, 1])
            k = d1.selectbox(tr("Apagar cenário", "Delete scenario"), range(len(scen)), format_func=lambda i: scen[i]["name"], key="scn_del")
            if d2.button(tr("🗑️ Apagar", "🗑️ Delete")):
                scen.pop(k)
                st.session_state["_pert_reset"] = True
                ui.mark_dirty()
                st.rerun()


# ============================================================================= Gantt & time-phased cost
def gantt():
    p = ui.P()
    ui.header("Diagrama de Gantt e custos no tempo", "Gantt chart & time-phased cost", "gantt", "📅")
    sched = S.compute(p)
    if not sched.get("ok"):
        st.error("\n".join(sched.get("errors", [])))
        return
    cur = p["meta"].get("currency", "EUR")
    df = sched["acts"].copy()
    c1, c2, c3, c4 = st.columns(4)
    group = c1.toggle(tr("Agrupar por output", "Group by output"), value=True)
    show_float = c2.toggle(tr("Mostrar folga", "Show float"), value=True)
    show_base = c3.toggle(tr("Mostrar baseline", "Show baseline"), value=bool(p.get("baseline")))
    if c4.button(tr("📌 Guardar baseline", "📌 Save baseline"), help=tr("Fixa o plano atual (datas, custos e curva PV) como referência", "Freezes the current plan (dates, costs, PV curve) as reference")):
        p["baseline"] = S.make_baseline(p, sched)
        ui.mark_dirty()
        st.toast(tr("Baseline guardada", "Baseline saved"))
    df["label"] = df["id"] + " · " + df["name"].str.slice(0, 45)
    objs = {str(o["code"]): o["text"] for o in p["objectives"]}
    df["group"] = df["output_code"].map(lambda c: f"{c} {objs.get(str(c), '')[:30]}" if c else tr("Apoio", "Support"))
    df = df.sort_values(["group", "ES"] if group else ["ES"])
    order = list(df["label"])
    fig = go.Figure()
    status = S.to_date(p["meta"].get("status_date"))
    for _, r in df.iterrows():
        dur_days = (r["finish"] - r["start"]).days or 0.5
        colr = CRIT if r["critical"] else NONC
        if r["milestone"]:
            fig.add_trace(go.Scatter(x=[r["finish"]], y=[r["label"]], mode="markers", marker=dict(symbol="diamond", size=14, color=colr), showlegend=False,
                                     hovertext=f"{r['id']} · {d(r['finish'])}"))
            continue
        fig.add_trace(go.Bar(base=[pd.Timestamp(r["start"])], x=[dur_days * 86400000], y=[r["label"]], orientation="h", marker_color=colr, opacity=0.9,
                             showlegend=False, hovertext=f"{r['id']} · {d(r['start'])} → {d(r['finish'])} · TF {num(r['TF'], 1)} · {money(r['cost'], cur)} · {pct(r['pct_complete'], 0)}",
                             text=f"{pct(r['pct_complete'], 0)}" if r["pct_complete"] else "", textposition="inside"))
        if r["pct_complete"]:
            fig.add_trace(go.Bar(base=[pd.Timestamp(r["start"])], x=[dur_days * r["pct_complete"] * 86400000], y=[r["label"]], orientation="h",
                                 marker_color="rgba(0,0,0,0.35)", width=0.25, showlegend=False, hoverinfo="skip"))
        if show_float and r["TF"] > 1e-6:
            fl = (r["late_finish"] - r["finish"]).days
            fig.add_trace(go.Bar(base=[pd.Timestamp(r["finish"])], x=[fl * 86400000], y=[r["label"]], orientation="h", marker=dict(color="rgba(150,150,150,0.25)", line=dict(color="#999", width=1)),
                                 showlegend=False, hovertext=tr(f"Folga total {num(r['TF'], 1)}", f"Total float {num(r['TF'], 1)}")))
        if show_base and p.get("baseline") and r["id"] in p["baseline"]["acts"]:
            b = p["baseline"]["acts"][r["id"]]
            bs, bf = S.to_date(b["start"]), S.to_date(b["finish"])
            fig.add_trace(go.Bar(base=[pd.Timestamp(bs)], x=[max(1, (bf - bs).days) * 86400000], y=[r["label"]], orientation="h", marker_color="rgba(31,59,87,0.85)",
                                 width=0.18, offset=0.28, showlegend=False, hovertext=f"Baseline {d(bs)} → {d(bf)}"))
    fig.add_vline(x=pd.Timestamp(status).timestamp() * 1000, line_dash="dash", line_color="#2E8B57")
    fig.add_annotation(x=pd.Timestamp(status), y=1.02, yref="paper", text=tr("Data de controlo", "Status date"), showarrow=False, font=dict(color="#2E8B57"))
    fig.update_layout(barmode="overlay", height=max(320, 34 * len(df) + 80), xaxis=dict(type="date"), yaxis=dict(categoryorder="array", categoryarray=order[::-1]),
                      margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption(tr("🔴 crítica · 🔵 não crítica · ▭ cinzento = folga · faixa escura = baseline · ◆ marco · faixa preta interior = % concluída",
                  "🔴 critical · 🔵 non-critical · grey ▭ = float · dark strip = baseline · ◆ milestone · inner black strip = % complete"))
    ui.interpret(I.cpm_text(sched))

    st.markdown(tr("### 💶 Orçamento distribuído no tempo (cash flow das atividades)", "### 💶 Time-phased budget (activity cash flow)"))
    per = sched["periods"]
    cont = sched["contingency"]
    bac = sched["bac"]
    tab = pd.DataFrame({"ID": df["id"], tr("Atividade", "Activity"): df["name"], tr("Distribuição", "Distribution"): df["distribution"].map(lambda c: opt_label("distribution", c)),
                        "BAC": df["cost"]})
    for _, r in per.iterrows():
        tab[r["period"]] = [float(per.loc[per["period"] == r["period"], a].iloc[0]) for a in df["id"]]
    tot = {"ID": "", tr("Atividade", "Activity"): tr("Custo do período (PV)", "Period cost (PV)"), tr("Distribuição", "Distribution"): "", "BAC": bac}
    cum = {"ID": "", tr("Atividade", "Activity"): tr("Acumulado", "Cumulative"), tr("Distribuição", "Distribution"): "", "BAC": None}
    cpc = {"ID": "", tr("Atividade", "Activity"): tr("% acumulado do BAC", "% cumulative of BAC"), tr("Distribuição", "Distribution"): "", "BAC": None}
    ccont = {"ID": "", tr("Atividade", "Activity"): tr("Acumulado + contingência", "Cumulative + contingency"), tr("Distribuição", "Distribution"): "", "BAC": bac + cont}
    for _, r in per.iterrows():
        tot[r["period"]] = r["pv"]
        cum[r["period"]] = r["pv_cum"]
        cpc[r["period"]] = r["pv_cum"] / bac * 100 if bac else 0
        ccont[r["period"]] = r["pv_cum"] * (1 + cont / bac) if bac else r["pv_cum"]
    tab = pd.concat([tab, pd.DataFrame([tot, cum, cpc, ccont])], ignore_index=True)
    fmt = {c: "{:,.0f}" for c in tab.columns if c not in ("ID", tr("Atividade", "Activity"), tr("Distribuição", "Distribution"))}
    st.dataframe(tab.style.format(fmt, na_rep=""), hide_index=True, width="stretch")
    st.caption(tr("Linha '% acumulado' em percentagem. A contingência distribui-se proporcionalmente ao avanço planeado.",
                  "'% cumulative' row in percent. Contingency is spread in proportion to planned progress."))
    sc = S.s_curve(p, sched)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sc["period"], y=sc["pv"], name=tr("Custo do período (PV)", "Period cost (PV)"), marker_color="#9DB9D3"))
    fig.add_trace(go.Scatter(x=sc["period"], y=sc["pv_cum"], name=tr("PV acumulado (curva S)", "Cumulative PV (S-curve)"), yaxis="y2", line=dict(color="#1F3B57", width=3)))
    fig.add_trace(go.Scatter(x=sc["period"], y=sc["pv_cum"] * (1 + cont / bac if bac else 1), name=tr("Com contingência", "With contingency"), yaxis="y2", line=dict(color="#1F3B57", dash="dot")))
    if "baseline_pv_cum" in sc:
        fig.add_trace(go.Scatter(x=sc["period"], y=sc["baseline_pv_cum"], name="Baseline", yaxis="y2", line=dict(color="#999", dash="dash")))
    fig.update_layout(height=380, yaxis=dict(title=tr("€ por período", "€ per period")), yaxis2=dict(title=tr("€ acumulado", "€ cumulative"), overlaying="y", side="right", rangemode="tozero"),
                      legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    ui.interpret(I.cost_text(sched, cur))
    st.caption(tr("O acompanhamento planeado vs. real (EV, AC, CPI, SPI) está na página 'Earned Value (EVM)'.", "Planned vs actual tracking (EV, AC, CPI, SPI) is on the 'Earned Value (EVM)' page."))


# ============================================================================= RACI
def raci():
    p = ui.P()
    ui.header("Matriz de responsabilidades (RACI / RASCI)", "Responsibility matrix (RACI / RASCI)", "raci", "🧑‍🤝‍🧑")
    rc = p["raci"]
    roles_txt = st.text_input(tr("Papéis / pessoas (separados por ';')", "Roles / people (separated by ';')"), "; ".join(rc.get("roles", [])), key=f"roles_{st.session_state.dv}")
    roles = [r.strip() for r in roles_txt.split(";") if r.strip()]
    if roles != rc.get("roles"):
        rc["roles"] = roles
        ui.mark_dirty()
    acts = p["activities"]
    if not acts or not roles:
        st.info(tr("Defina atividades e papéis.", "Define activities and roles."))
        return
    key = f"raci_{st.session_state.dv}_{hash(tuple(roles))}_{len(acts)}"
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame([{"ID": a["id"], tr("Atividade", "Activity"): a.get("name", ""), **{r: rc["matrix"].get(a["id"], {}).get(r, "") for r in roles}} for a in acts])
    cfg = {r: st.column_config.SelectboxColumn(r[:28], options=["", "R", "A", "S", "C", "I"]) for r in roles}
    ed = st.data_editor(st.session_state[key], hide_index=True, column_config=cfg, disabled=["ID", tr("Atividade", "Activity")], key=f"ed_{key}", width="stretch")
    new = {row["ID"]: {r: (row.get(r) or "") for r in roles} for row in ed.to_dict("records")}
    if new != {k: {r: v.get(r, "") for r in roles} for k, v in rc["matrix"].items() if k in new}:
        rc["matrix"] = new
        ui.mark_dirty()
    st.caption("R = " + tr("Responsável (executa)", "Responsible (does)") + " · A = " + tr("Autoridade / aprova (só 1)", "Accountable / approves (only 1)") +
               " · S = " + tr("Suporte", "Support") + " · C = " + tr("Consultado", "Consulted") + " · I = " + tr("Informado", "Informed"))
    issues = []
    for aid, row in new.items():
        a_n = sum(1 for v in row.values() if v == "A")
        r_n = sum(1 for v in row.values() if v == "R")
        if a_n != 1:
            issues.append(tr(f"{aid}: deve ter exatamente 1 'A' (tem {a_n}).", f"{aid}: must have exactly 1 'A' (has {a_n})."))
        if r_n == 0:
            issues.append(tr(f"{aid}: sem 'R'.", f"{aid}: no 'R'."))
    c1, c2 = st.columns([3, 2])
    load = pd.DataFrame([{tr("Papel", "Role"): r, **{k: sum(1 for row in new.values() if row.get(r) == k) for k in "RASCI"}} for r in roles])
    fig = go.Figure()
    for k, colr in zip("RASCI", ["#E4572E", "#1F3B57", "#7FA7C9", "#D9822B", "#BBBBBB"]):
        fig.add_trace(go.Bar(x=load[tr("Papel", "Role")], y=load[k], name=k, marker_color=colr))
    fig.update_layout(barmode="stack", height=320, margin=dict(l=10, r=10, t=10, b=10), yaxis_title=tr("N.º de atividades", "No. of activities"))
    c1.plotly_chart(fig, width="stretch")
    with c2:
        if issues:
            st.warning("\n".join(f"- {x}" for x in issues))
        else:
            st.success(tr("Todas as atividades têm 1 'A' e pelo menos 1 'R'. ✅", "Every activity has 1 'A' and at least 1 'R'. ✅"))
        top = load.sort_values("R", ascending=False).iloc[0]
        ui.interpret(tr(f"**{top[tr('Papel', 'Role')]}** é responsável ('R') por {int(top['R'])} atividades — verifique a sobrecarga se forem simultâneas no Gantt.",
                        f"**{top[tr('Papel', 'Role')]}** is responsible ('R') for {int(top['R'])} activities — check overload if they overlap in the Gantt."))


# ============================================================================= risks
def risks():
    p = ui.P()
    ui.header("Gestão de riscos", "Risk management", "risks", "⚠️")
    view = st.segmented_control(tr("Vista", "View"), ["prof", "strategy", "full"], default="prof", key="risk_view",
                                format_func=lambda v: {"prof": tr("Modelo do professor (RiskRegister)", "Professor's template (RiskRegister)"),
                                                       "strategy": tr("Estratégia de gestão (5 colunas)", "Management strategy (5 columns)"),
                                                       "full": tr("Completa (alargada)", "Full (extended)")}[v])
    cols = {"prof": ["id", "type", "description", "likelihood", "impact", "target_exposure", "existing_mitigation", "proposed_mitigation", "risk_manager", "risk_owner", "review_by", "review"],
            "strategy": ["id", "description", "level_affected", "likelihood", "impact", "strategy", "proposed_mitigation", "risk_owner"],
            "full": None}[view or "prof"]
    ov = {"assumption_id": st.column_config.SelectboxColumn(ui.label("assumption_id"), options=[""] + [h["id"] for h in p["assumptions"]]),
          "preventive_activity": st.column_config.SelectboxColumn(ui.label("preventive_activity"), options=[""] + [a["id"] for a in p["activities"]]),
          "target_exposure": st.column_config.NumberColumn(ui.label("target_exposure"), min_value=1, max_value=16, step=1)}
    rows = ui.edit_table("risks", columns=cols, key=view or "prof", overrides=ov)
    st.caption(tr("Probabilidade: 4 Quase certo · 3 Provável · 2 Possível · 1 Improvável. Impacto: 4 Severo · 3 Grave · 2 Moderado · 1 Menor. Exposição = P × I (1–16).",
                  "Likelihood: 4 Almost certain · 3 Likely · 2 Possible · 1 Unlikely. Impact: 4 Severe · 3 Major · 2 Moderate · 1 Minor. Exposure = L × I (1–16)."))
    if not rows:
        return
    c1, c2 = st.columns([3, 2])
    with c1:
        z = [[i * l for i in range(1, 5)] for l in range(1, 5)]
        fig = go.Figure(go.Heatmap(z=z, x=[opt_label("impact", i) for i in range(1, 5)], y=[opt_label("likelihood", l) for l in range(1, 5)],
                                   colorscale=[[0, "#27AE60"], [0.25, "#F1C40F"], [0.55, "#E67E22"], [1, "#C0392B"]], showscale=False, opacity=0.85))
        cells = {}
        for r in rows:
            cells.setdefault((int(r["impact"] or 1), int(r["likelihood"] or 1)), []).append(r["id"])
        for (i, l), ids in cells.items():
            fig.add_annotation(x=opt_label("impact", i), y=opt_label("likelihood", l), text="<b>" + ", ".join(ids) + "</b>", showarrow=False, font=dict(color="white", size=13))
        fig.update_layout(height=380, xaxis_title=tr("Impacto", "Impact"), yaxis_title=tr("Probabilidade", "Likelihood"), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        legend = "".join(f"<div style='display:flex;gap:8px;align-items:flex-start;margin:3px 0'><span style='min-width:16px;height:16px;border-radius:3px;background:{z[1]};display:inline-block;margin-top:3px'></span>"
                         f"<span><b>{tr(*z[2])}</b> ({rng}): {tr(*z[3])}</span></div>"
                         for z, rng in zip(AN.RISK_ZONES, ["12–16", "8–11", "4–7", "1–3"]))
        st.markdown(f"<div style='font-size:0.85rem'>{legend}</div>", unsafe_allow_html=True)
    with c2:
        df = pd.DataFrame([{"ID": r["id"], tr("Exposição", "Exposure"): AN.exposure(r), tr("Alvo", "Target"): r.get("target_exposure"),
                            tr("Nível", "Level"): AN.risk_level(AN.exposure(r))} for r in sorted(rows, key=lambda r: -AN.exposure(r))])
        st.dataframe(df, hide_index=True, width="stretch")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["ID"], y=df[tr("Exposição", "Exposure")], name=tr("Atual", "Current"), marker_color=[AN.risk_color(e) for e in df[tr("Exposição", "Exposure")]]))
        fig.add_trace(go.Scatter(x=df["ID"], y=df[tr("Alvo", "Target")], mode="markers", marker=dict(symbol="line-ew-open", size=26, color="#1F3B57", line=dict(width=3)), name=tr("Alvo", "Target")))
        fig.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(range=[0, 17]), legend=dict(orientation="h"))
        st.plotly_chart(fig, width="stretch")
    st.markdown(tr("##### Ação exigida por risco (segundo a zona da matriz)", "##### Required action per risk (by matrix zone)"))
    st.dataframe(pd.DataFrame([{"": "🔴" if AN.exposure(r) >= 12 else "🟠" if AN.exposure(r) >= 8 else "🟡" if AN.exposure(r) >= 4 else "🟢",
                                "ID": r["id"], tr("Risco", "Risk"): r.get("description", ""), tr("Exposição", "Exposure"): AN.exposure(r),
                                tr("Ação exigida", "Required action"): AN.risk_action(AN.exposure(r)),
                                tr("Estratégia escolhida", "Chosen strategy"): opt_label("risk_strategy", r.get("strategy")),
                                tr("Responsável", "Owner"): r.get("risk_owner") or r.get("risk_manager") or "—"}
                               for r in sorted(rows, key=lambda r: (-AN.exposure(r), -int(r.get("impact") or 0)))]),
                 hide_index=True, width="stretch",
                 column_config={tr("Risco", "Risk"): st.column_config.TextColumn(width="large"), tr("Ação exigida", "Required action"): st.column_config.TextColumn(width="large")})
    ui.interpret(I.risk_text(rows))
    st.markdown(tr("##### Atividades preventivas", "##### Preventive activities"))
    st.caption(tr("As estratégias preventivas reduzem a probabilidade e entram no plano como atividades de apoio.", "Preventive strategies lower likelihood and enter the plan as support activities."))
    if st.button(tr("⚙️ Criar atividades preventivas para riscos com exposição ≥ 8", "⚙️ Create preventive activities for risks with exposure ≥ 8")):
        n = 0
        for r in p["risks"]:
            if AN.exposure(r) >= 8 and not r.get("preventive_activity"):
                a = empty_row("activities")
                a.update({"id": next_id(p["activities"], "A"), "name": tr("Prevenção: ", "Prevention: ") + (r.get("proposed_mitigation") or r.get("description", ""))[:60],
                          "type": "Support - Risk prevention", "optimistic": 1, "most_likely": 1, "pessimistic": 2, "cost": float(r.get("contingency") or 0) * 0.3,
                          "responsible": r.get("risk_manager", "")})
                p["activities"].append(a)
                r["preventive_activity"] = a["id"]
                n += 1
        ui.bump()
        st.success(tr(f"{n} atividades preventivas criadas.", f"{n} preventive activities created."))


# ============================================================================= budget
def budget():
    p = ui.P()
    ui.header("Orçamento por tipo de atividade e cash flow", "Activity-type budget & cash flow", "budget", "💶")
    cur = p["meta"].get("currency", "EUR")
    ov = {"activity_id": st.column_config.SelectboxColumn(ui.label("activity_id"), options=[a["id"] for a in p["activities"]])}
    st.markdown(tr("##### Linhas de orçamento (recursos × custo unitário)", "##### Budget lines (resources × unit cost)"))
    lines = ui.edit_table("budget", overrides=ov)
    if lines:
        st.caption(tr(f"Total das linhas: **{money(sum((l['quantity'] or 0) * (l['unit_cost'] or 0) for l in lines), cur)}**",
                      f"Lines total: **{money(sum((l['quantity'] or 0) * (l['unit_cost'] or 0) for l in lines), cur)}**"))
    rows = []
    for a in p["activities"]:
        al = [l for l in p["budget"] if str(l.get("activity_id")) == str(a["id"])]
        rows.append({"ID": a["id"], tr("Atividade", "Activity"): a.get("name", ""), tr("Custo manual", "Manual cost"): a.get("cost") or 0,
                     tr("Soma das linhas", "Lines total"): sum((l["quantity"] or 0) * (l["unit_cost"] or 0) for l in al) if al else None,
                     "BAC": activity_cost(p, a), tr("Origem", "Source"): tr("linhas", "lines") if al else tr("manual", "manual")})
    st.markdown(tr("##### Custo por atividade (BAC)", "##### Cost per activity (BAC)"))
    st.dataframe(pd.DataFrame(rows).style.format({c: "{:,.0f}" for c in [tr("Custo manual", "Manual cost"), tr("Soma das linhas", "Lines total"), "BAC"]}, na_rep="—"),
                 hide_index=True, width="stretch")
    sched = S.compute(p)
    if not sched.get("ok"):
        return
    bac = sched["bac"]
    # categories: budget lines by category; activities without lines -> 'Other' (manual)
    cat = {}
    phase = {}
    for a in p["activities"]:
        al = [l for l in p["budget"] if str(l.get("activity_id")) == str(a["id"])]
        if al:
            for l in al:
                v = (l["quantity"] or 0) * (l["unit_cost"] or 0)
                cat[opt_label("cost_category", l["category"])] = cat.get(opt_label("cost_category", l["category"]), 0) + v
                phase[opt_label("phase", l["phase"])] = phase.get(opt_label("phase", l["phase"]), 0) + v
        else:
            k = tr("Sem detalhe (custo manual)", "No detail (manual cost)")
            cat[k] = cat.get(k, 0) + (a.get("cost") or 0)
    c1, c2, c3 = st.columns(3)
    fig = go.Figure(go.Pie(labels=list(cat), values=list(cat.values()), hole=0.5))
    fig.update_layout(height=320, title=tr("Por categoria de custo", "By cost category"), margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h"))
    c1.plotly_chart(fig, width="stretch")
    # cost per phase from schedule thirds when no lines: inception (first 15%), implementation, completion (last 15%) of time
    days = len(sched["daily"])
    ph = {tr("Arranque", "Inception"): float(sched["daily"][: int(days * 0.15)].sum()),
          tr("Implementação", "Implementation"): float(sched["daily"][int(days * 0.15): int(days * 0.85)].sum()),
          tr("Encerramento", "Completion"): float(sched["daily"][int(days * 0.85):].sum())}
    fig = go.Figure(go.Bar(x=list(ph), y=list(ph.values()), marker_color=["#7FA7C9", "#1F3B57", "#D9822B"], text=[money(v, cur) for v in ph.values()], textposition="outside"))
    fig.update_layout(height=320, title=tr("Por fase (calendário)", "By phase (calendar)"), margin=dict(l=10, r=10, t=40, b=10))
    c2.plotly_chart(fig, width="stretch")
    types = {}
    for a in p["activities"]:
        k = opt_label("activity_type", a.get("type"))
        types[k] = types.get(k, 0) + activity_cost(p, a)
    fig = go.Figure(go.Pie(labels=list(types), values=list(types.values()), hole=0.5))
    fig.update_layout(height=320, title=tr("Produção vs. apoio", "Production vs support"), margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h"))
    c3.plotly_chart(fig, width="stretch")
    st.markdown(tr("##### Mapa de cash flow por categoria e período", "##### Cash-flow map by category and period"))
    per = sched["periods"]
    cf = {}
    for a in p["activities"]:
        aid = a["id"]
        if aid not in per.columns:
            continue
        al = [l for l in p["budget"] if str(l.get("activity_id")) == str(aid)]
        tot = activity_cost(p, a) or 1
        parts = [(opt_label("cost_category", l["category"]), (l["quantity"] or 0) * (l["unit_cost"] or 0) / tot) for l in al] or [(tr("Sem detalhe (custo manual)", "No detail (manual cost)"), 1.0)]
        for k, share in parts:
            cf[k] = cf.get(k, np.zeros(len(per))) + per[aid].values * share
    cfm = pd.DataFrame(cf, index=per["period"]).T
    cfm.loc[tr("Total", "Total")] = cfm.sum()
    cfm.loc[tr("Acumulado", "Cumulative")] = cfm.loc[tr("Total", "Total")].cumsum()
    st.dataframe(cfm.style.format("{:,.0f}"), width="stretch")
    peak = per.loc[per["pv"].idxmax()]
    ui.interpret(tr(f"Orçamento das atividades: **{money(bac, cur)}** (+ contingência {money(sched['contingency'], cur)}). "
                    f"A maior necessidade de liquidez ocorre em **{peak['period']}** ({money(peak['pv'], cur)}) — planeie as tranches de financiamento para evitar atrasos por falta de liquidez.",
                    f"Activity budget: **{money(bac, cur)}** (+ contingency {money(sched['contingency'], cur)}). "
                    f"Peak liquidity need is in **{peak['period']}** ({money(peak['pv'], cur)}) — plan funding tranches to avoid delays due to lack of liquidity."))


# ============================================================================= contingency
def contingency():
    p = ui.P()
    ui.header("Orçamento de contingências", "Contingency budget", "contingency", "🛟")
    m = p["meta"]
    cur = m.get("currency", "EUR")
    sched = S.compute(p)
    bac = sched.get("bac", 0)
    c1, c2, c3 = st.columns(3)
    meth = c1.radio(tr("Método", "Method"), ["percent", "risk"], index=0 if m.get("contingency_method") != "risk" else 1,
                    format_func=lambda v: tr("% do orçamento (BAC)", "% of budget (BAC)") if v == "percent" else tr("Soma das contingências por risco", "Sum of per-risk contingencies"))
    pc = c2.slider(tr("Percentagem", "Percentage"), 0.0, 0.30, float(m.get("contingency_pct") or 0), 0.01, format="%.2f", disabled=meth != "percent")
    used = c3.number_input(tr("Contingência já consumida", "Contingency already used"), 0.0, 1e12, float(m.get("contingency_used") or 0), step=1000.0)
    if (meth, pc, used) != (m.get("contingency_method"), m.get("contingency_pct"), m.get("contingency_used")):
        m["contingency_method"], m["contingency_pct"], m["contingency_used"] = meth, pc, used
        ui.mark_dirty()
    cont = S.contingency_amount(p, bac)
    risk_sum = sum(float(r.get("contingency") or 0) for r in p["risks"])
    ev = sum(float(r.get("contingency") or 0) * (int(r.get("likelihood") or 0) / 4) for r in p["risks"])
    c = st.columns(4)
    c[0].metric("BAC", money(bac, cur))
    c[1].metric(tr("Reserva de contingência", "Contingency reserve"), money(cont, cur), f"{pct(cont / bac if bac else 0)} BAC")
    c[2].metric(tr("Disponível", "Available"), money(cont - used, cur))
    c[3].metric(tr("Valor esperado dos riscos", "Expected value of risks"), money(ev, cur), help=tr("Σ contingência × probabilidade (P/4)", "Σ contingency × likelihood (L/4)"))
    st.markdown(tr("##### Alocação por risco", "##### Allocation per risk"))
    ui.edit_table("risks", columns=["id", "description", "likelihood", "impact", "contingency", "strategy"], key="cont", num_rows="fixed", disabled=["id", "description"])
    st.markdown(tr("##### Pressupostos → riscos → mitigação → custos → contingências", "##### Assumptions → risks → mitigation → costs → contingencies"))
    ui.graph(_cont_dot(p))
    txt = tr(f"A reserva de **{money(cont, cur)}** representa {pct(cont / bac if bac else 0)} do orçamento. ",
             f"The **{money(cont, cur)}** reserve is {pct(cont / bac if bac else 0)} of the budget. ")
    if meth == "percent" and risk_sum:
        txt += tr(f"A soma das estimativas por risco é {money(risk_sum, cur)} e o valor esperado {money(ev, cur)}: a percentagem escolhida {'cobre' if cont >= ev else '**não cobre**'} o valor esperado dos riscos.",
                  f"The sum of per-risk estimates is {money(risk_sum, cur)} and the expected value {money(ev, cur)}: the chosen percentage {'covers' if cont >= ev else '**does not cover**'} the expected value of risks.")
    if used > cont:
        txt += tr(" ⚠️ A contingência consumida já excede a reserva.", " ⚠️ Contingency used already exceeds the reserve.")
    ui.interpret(txt)


def _cont_dot(p):
    lines = ['digraph G { rankdir=LR; node [fontname="Helvetica", fontsize=10, style="rounded,filled", shape=box, fontcolor="white", penwidth=0]; edge [color="#13A3B5"];',
             f'CONT [label="{tr("Contingências", "Contingencies")}", fillcolor="#13A3B5", shape=cds];']
    for h in p["assumptions"]:
        code, _ = AN.assumption_decision(h)
        colr = "#0E6E73" if code == "drop" else "#13A3B5"
        lines.append(f'"H{h["id"]}" [label="{h["id"]}\\n{tr("Confirmado", "Confirmed") if code == "drop" else tr("Não confirmado", "Not confirmed")}", fillcolor="{colr}"];')
    for r in p["risks"]:
        if not (r.get("assumption_id") or r.get("contingency")):
            continue
        lines.append(f'"R{r["id"]}" [label="{r["id"]}", fillcolor="#E67E22"];')
        if r.get("assumption_id"):
            lines.append(f'"H{r["assumption_id"]}" -> "R{r["id"]}";')
        if r.get("preventive_activity"):
            lines.append(f'"M{r["id"]}" [label="{tr("Mitigação", "Mitigation")} {r["preventive_activity"]}", fillcolor="#5B8E7D"]; "R{r["id"]}" -> "M{r["id"]}";')
            src = f'"M{r["id"]}"'
        else:
            src = f'"R{r["id"]}"'
        if r.get("contingency"):
            lines.append(f'"K{r["id"]}" [label="{tr("Custo", "Cost")} {num(r["contingency"], 0)}", fillcolor="#1F3B57"]; {src} -> "K{r["id"]}" -> CONT;')
    lines.append("}")
    return "\n".join(lines)


# ============================================================================= procurement
def procurement():
    p = ui.P()
    ui.header("Plano de procurement", "Procurement plan", "procurement", "🛒")
    cur = p["meta"].get("currency", "EUR")
    ov = {"activity_id": st.column_config.SelectboxColumn(ui.label("activity_id"), options=[""] + [a["id"] for a in p["activities"]])}
    rows = ui.edit_table("procurement", overrides=ov)
    if not rows:
        return
    sched = S.compute(p)
    out = []
    for q in rows:
        start = None
        if sched.get("ok") and q.get("activity_id") in set(sched["acts"]["id"]):
            start = sched["acts"].set_index("id").loc[q["activity_id"], "start"]
        pdate = S.to_date(q["planned_date"]) if q.get("planned_date") else None
        ok = (pdate is None or start is None or pdate <= start)
        out.append({"ID": q["id"], "Item": q["item"], tr("Método", "Method"): opt_label("procurement", q["method"]), tr("Custo", "Cost"): q["estimated_cost"],
                    tr("Data prevista", "Planned date"): d(pdate) if pdate else "—", tr("Início da atividade", "Activity start"): d(start) if start else "—",
                    tr("A tempo?", "On time?"): "✅" if ok else "⚠️"})
    df = pd.DataFrame(out)
    st.dataframe(df.style.format({tr("Custo", "Cost"): "{:,.0f}"}), hide_index=True, width="stretch")
    c1, c2 = st.columns(2)
    by = df.groupby(tr("Método", "Method"))[tr("Custo", "Cost")].sum()
    fig = go.Figure(go.Pie(labels=by.index, values=by.values, hole=0.5))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
    c1.plotly_chart(fig, width="stretch")
    late = [o["ID"] for o in out if o[tr("A tempo?", "On time?")] == "⚠️"]
    sole = sum(q["estimated_cost"] for q in rows if q["method"] == "Sole Sourcing")
    tot = sum(q["estimated_cost"] for q in rows) or 1
    with c2:
        ui.interpret(tr(f"Plano com **{len(rows)} aquisições** ({money(tot, cur)}). " + (f"⚠️ Datas posteriores ao início da atividade: {', '.join(late)} — antecipar o lançamento. " if late else "Todas as aquisições antecedem o início das atividades. ")
                        + (f"Ajuste direto representa {pct(sole / tot)} do valor — justificar a exceção à concorrência." if sole else ""),
                        f"Plan with **{len(rows)} purchases** ({money(tot, cur)}). " + (f"⚠️ Dates after the activity start: {', '.join(late)} — launch earlier. " if late else "All purchases precede activity start. ")
                        + (f"Sole sourcing is {pct(sole / tot)} of the value — justify the exception to competition." if sole else "")))
