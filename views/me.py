"""5 · Monitoring & Evaluation: SMART indicators, baselines/targets/benchmarking, EVM, quality & evaluation."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import analysis as AN
from core import interpret as I
from core import schedule as S
from core import ui
from core.fmt import d, money, num, pct
from core.i18n import opt_label, tr
from core.model import DAC_CRITERIA, indicator_dimension, objective_level


def indicators():
    p = ui.P()
    ui.header("Indicadores SMART", "SMART indicators", "indicators", "📏")
    st.caption(tr("S = Specific · M = Measurable · A = Available (custo razoável) · R = Relevant · T = Timely. Formule os indicadores de forma neutra (ex.: 'Taxa de…', não 'Aumento de…').",
                  "S = Specific · M = Measurable · A = Available (reasonable cost) · R = Relevant · T = Timely. Phrase indicators neutrally (e.g. 'Rate of…', not 'Increase in…')."))
    ov = {"objective_code": st.column_config.SelectboxColumn(ui.label("objective_code"), options=[str(o["code"]) for o in p["objectives"]])}
    rows = ui.edit_table("indicators", overrides=ov, key="full", height=360)
    if not rows:
        return
    out = []
    for i in rows:
        lvl = objective_level(p, i.get("objective_code"))
        pr = AN.progress(i)
        words = ("aumento", "redução", "melhoria", "increase", "decrease", "improve", "reduce")
        neutral = not any(w in str(i.get("indicator", "")).lower()[:20] for w in words)
        out.append({"ID": i["id"], tr("Nível", "Level"): opt_label("level", lvl) if lvl else "—", tr("Critério", "Criterion"): indicator_dimension(lvl),
                    "SMART": f"{AN.smart_score(i)}/5", "Baseline→Meta": f"{num(i.get('baseline'), 2)} → {num(i.get('target'), 2)}",
                    "Δ": num((i["target"] - i["baseline"]) if i.get("target") is not None and i.get("baseline") is not None else None, 2),
                    tr("Progresso", "Progress"): pr, tr("Neutro?", "Neutral?"): "✅" if neutral else "⚠️"})
    df = pd.DataFrame(out)
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={tr("Progresso", "Progress"): st.column_config.ProgressColumn(tr("Progresso", "Progress"), min_value=0, max_value=1, format="percent")})
    c1, c2 = st.columns(2)
    crit = ["specific", "measurable", "available", "relevant", "timely"]
    fig = go.Figure(go.Bar(x=list("SMART"), y=[sum(1 for i in rows if i.get(k)) / len(rows) for k in crit], marker_color="#2C7FB8"))
    fig.update_layout(height=280, yaxis=dict(tickformat=".0%", range=[0, 1.05]), title=tr("% de indicadores que cumprem cada critério", "% of indicators meeting each criterion"), margin=dict(l=10, r=10, t=40, b=10))
    c1.plotly_chart(fig, width="stretch")
    lv = pd.Series([indicator_dimension(objective_level(p, i.get("objective_code"))) or "—" for i in rows]).value_counts()
    fig = go.Figure(go.Pie(labels=lv.index, values=lv.values, hole=0.5))
    fig.update_layout(height=280, title=tr("Indicadores por critério de avaliação", "Indicators per evaluation criterion"), margin=dict(l=10, r=10, t=40, b=10))
    c2.plotly_chart(fig, width="stretch")
    ui.interpret(I.indicators_text(p))


def benchmark():
    p = ui.P()
    ui.header("Baselines, metas baseadas em evidência e benchmarking", "Baselines, evidence-based targets & benchmarking", "benchmark", "🏁")
    inds = p["indicators"]
    if not inds:
        st.info(tr("Defina primeiro os indicadores.", "Define indicators first."))
        return
    sel = st.selectbox(tr("Indicador", "Indicator"), [i["id"] for i in inds], format_func=lambda k: f"{k} — {next(i['indicator'] for i in inds if i['id'] == k)[:90]}")
    ind = next(i for i in inds if i["id"] == sel)
    c = st.columns(4)
    c[0].metric("Baseline", f"{num(ind.get('baseline'), 2)} ({ind.get('baseline_year') or '—'})")
    c[1].metric(tr("Meta", "Target"), f"{num(ind.get('target'), 2)} ({ind.get('target_year') or '—'})")
    c[2].metric(tr("Valor atual", "Current"), num(ind.get("current"), 2))
    pr = AN.progress(ind)
    c[3].metric(tr("Progresso", "Progress"), pct(pr) if pr is not None else "—")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(tr("##### Pares / referências (benchmarking)", "##### Peers / references (benchmarking)"))
        peers = ui.edit_table("benchmarks", columns=["peer", "value", "year", "note"], key=f"b_{sel}", filt=lambda r: r.get("indicator_id") == sel, fixed={"indicator_id": sel})
    with c2:
        st.markdown(tr("##### Série temporal histórica", "##### Historical time series"))
        series = ui.edit_table("timeseries", columns=["year", "value"], key=f"t_{sel}", filt=lambda r: r.get("indicator_id") == sel, fixed={"indicator_id": sel})
    b = AN.benchmark(ind, peers, series)
    fig = go.Figure()
    pts = sorted([(s["year"], s["value"]) for s in series if s.get("year") and s.get("value") is not None])
    if pts:
        fig.add_trace(go.Scatter(x=[x for x, _ in pts], y=[y for _, y in pts], mode="lines+markers", name=tr("Histórico", "History"), line=dict(color="#1F3B57")))
    if "trend_slope" in b and ind.get("target_year"):
        x0 = pts[-1][0]
        xs = np.arange(x0, int(ind["target_year"]) + 1)
        sl = b["trend_slope"]
        fig.add_trace(go.Scatter(x=xs, y=pts[-1][1] + sl * (xs - x0), mode="lines", line=dict(dash="dot", color="#7F8C8D"), name=tr("Tendência", "Trend")))
    if ind.get("baseline") is not None and ind.get("target") is not None:
        fig.add_trace(go.Scatter(x=[ind.get("baseline_year"), ind.get("target_year")], y=[ind["baseline"], ind["target"]], mode="lines+markers",
                                 line=dict(color="#2E8B57", width=3), marker=dict(size=10), name=tr("Baseline → meta", "Baseline → target")))
    if ind.get("current") is not None:
        fig.add_trace(go.Scatter(x=[S.to_date(p["meta"]["status_date"]).year], y=[ind["current"]], mode="markers", marker=dict(symbol="star", size=16, color="#D9822B"), name=tr("Atual", "Current")))
    for pr_ in peers:
        if pr_.get("value") is not None:
            fig.add_hline(y=pr_["value"], line_dash="dash", line_color="#BBBBBB", annotation_text=str(pr_.get("peer"))[:22], annotation_position="right")
    if "top" in b:
        fig.add_hline(y=b["top"], line_color="#C0392B", annotation_text="Top performer", annotation_position="left")
    fig.update_layout(height=400, xaxis_title=tr("Ano", "Year"), yaxis_title=ind.get("unit") or "", margin=dict(l=10, r=120, t=10, b=10), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
    if b.get("suggestions"):
        st.markdown(tr("##### Metas sugeridas (baseadas em evidência)", "##### Suggested targets (evidence-based)"))
        names = {"trend": tr("Tendência histórica (sem projeto)", "Historical trend (without project)"), "peer_median": tr("Mediana dos pares", "Peer median"),
                 "ambitious_p75": tr("Ambiciosa (percentil 75 dos pares)", "Ambitious (peer 75th percentile)"), "closing_half_gap": tr("Fechar 50% do gap face ao top performer", "Close 50% of the gap to the top performer")}
        st.dataframe(pd.DataFrame([{tr("Critério", "Criterion"): names[k], tr("Meta", "Target"): round(v, 2)} for k, v in b["suggestions"].items()]), hide_index=True, width="stretch")
    ui.interpret(I.benchmark_text(ind, b) or tr("Acrescente pares e/ou uma série temporal para avaliar a viabilidade da meta.", "Add peers and/or a time series to assess the target's feasibility."))
    st.markdown(tr("##### Quadro de baselines e metas", "##### Baselines & targets overview"))
    st.dataframe(pd.DataFrame([{"ID": i["id"], ui.label("indicator"): i["indicator"], "Baseline": i.get("baseline"), tr("Ano", "Year"): i.get("baseline_year"),
                                tr("Meta", "Target"): i.get("target"), tr("Ano meta", "Target year"): i.get("target_year"), "Δ": (i["target"] - i["baseline"]) if i.get("target") is not None and i.get("baseline") is not None else None,
                                tr("Pares", "Peers"): sum(1 for x in p["benchmarks"] if x.get("indicator_id") == i["id"])} for i in inds]), hide_index=True, width="stretch")


def evm():
    p = ui.P()
    ui.header("Earned Value Management (EVM) — planeado vs. real", "Earned Value Management (EVM) — planned vs actual", "evm", "📊")
    sched = S.compute(p)
    if not sched.get("ok"):
        st.error("\n".join(sched.get("errors", [])))
        return
    m = p["meta"]
    cur = m.get("currency", "EUR")
    c1, c2 = st.columns([1, 3])
    sd = c1.date_input(tr("Data de controlo", "Status date"), S.to_date(m.get("status_date")))
    if sd.isoformat() != m.get("status_date"):
        m["status_date"] = sd.isoformat()
        ui.mark_dirty()
        st.rerun()
    c2.caption(tr("Atualize a % concluída e o custo real de cada atividade. O EV = % concluída × orçamento da atividade.",
                  "Update % complete and actual cost of each activity. EV = % complete × activity budget."))
    with st.expander(tr("✏️ Progresso por atividade", "✏️ Progress per activity"), expanded=False):
        ui.edit_table("activities", columns=["id", "name", "pct_complete", "actual_cost"], key="evm", num_rows="fixed", disabled=["id", "name"],
                      overrides={"pct_complete": st.column_config.NumberColumn(ui.label("pct_complete"), min_value=0.0, max_value=1.0, step=0.05, format="%.2f")})
    sched = S.compute(p)
    e = S.evm(p, sched)
    c = st.columns(6)
    c[0].metric("PV", money(e["PV"], cur))
    c[1].metric("EV", money(e["EV"], cur))
    c[2].metric("AC", money(e["AC"], cur))
    c[3].metric("CPI", num(e["CPI"], 2), delta=num(e["CPI"] - 1, 2) if e["CPI"] == e["CPI"] else None)
    c[4].metric("SPI", num(e["SPI"], 2), delta=num(e["SPI"] - 1, 2) if e["SPI"] == e["SPI"] else None)
    c[5].metric("EAC", money(e["EAC"], cur), delta=money(e["EAC"] - e["BAC"], cur), delta_color="inverse")
    c = st.columns(6)
    c[0].metric("BAC", money(e["BAC"], cur))
    c[1].metric("CV", money(e["CV"], cur))
    c[2].metric("SV", money(e["SV"], cur))
    c[3].metric("ETC", money(e["ETC"], cur))
    c[4].metric("VAC", money(e["VAC"], cur))
    c[5].metric("TCPI", num(e["TCPI"], 2))
    sc = S.s_curve(p, sched)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sc["period"], y=sc["pv_cum"], name="PV", line=dict(color="#1F3B57", width=3)))
    fig.add_trace(go.Scatter(x=sc["period"], y=sc["ev_cum"], name="EV", line=dict(color="#2E8B57", width=3), connectgaps=True, mode="lines+markers"))
    fig.add_trace(go.Scatter(x=sc["period"], y=sc["ac_cum"], name="AC", line=dict(color="#C0392B", width=3), connectgaps=True, mode="lines+markers"))
    if "baseline_pv_cum" in sc:
        fig.add_trace(go.Scatter(x=sc["period"], y=sc["baseline_pv_cum"], name="PV baseline", line=dict(color="#999", dash="dash")))
    fig.add_hline(y=e["BAC"], line_dash="dot", line_color="#555", annotation_text="BAC")
    if e["EAC"] > e["BAC"]:
        fig.add_hline(y=e["EAC"], line_dash="dot", line_color="#C0392B", annotation_text="EAC")
    fig.update_layout(height=420, yaxis_title=cur, legend=dict(orientation="h", y=-0.15), margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    ui.interpret(I.evm_text(e, cur))
    t1, t2 = st.tabs([tr("Por atividade", "Per activity"), tr("Histórico de controlo (EV/AC acumulados)", "Control history (cumulative EV/AC)")])
    with t1:
        tab = e["table"][["id", "name", "BAC", "PV", "EV", "AC", "CV", "SV", "CPI", "SPI"]].copy()
        tab[["CPI", "SPI"]] = tab[["CPI", "SPI"]].astype(float)
        tab = tab.rename(columns={"id": "ID", "name": tr("Atividade", "Activity")})
        st.dataframe(tab.style.format({k: "{:,.0f}" for k in ["BAC", "PV", "EV", "AC", "CV", "SV"]} | {"CPI": "{:.2f}", "SPI": "{:.2f}"}, na_rep="—")
                     .map(lambda v: "color:#C0392B" if isinstance(v, (int, float)) and v == v and v < 0 else "", subset=["CV", "SV"]),
                     hide_index=True, width="stretch")
    with t2:
        st.caption(tr("Registe aqui EV e AC acumulados de datas de controlo anteriores (fim de cada mês). O ponto da data de controlo atual é calculado automaticamente.",
                      "Record cumulative EV and AC at previous status dates (end of each month). The current status point is computed automatically."))
        ui.edit_table("tracking")
        if st.button(tr("📌 Registar a situação atual no histórico", "📌 Record current status in history")):
            p["tracking"] = [t for t in p["tracking"] if t.get("date") != e["status"].isoformat()] + [{"date": e["status"].isoformat(), "ev": round(e["EV"], 0), "ac": round(e["AC"], 0), "note": ""}]
            ui.bump()
            st.rerun()


def quality():
    p = ui.P()
    ui.header("Qualidade do projeto e avaliação", "Project quality & evaluation", "quality", "✅")
    t1, t2 = st.tabs([tr("✅ Atributos de qualidade (PCM)", "✅ Quality attributes (PCM)"), tr("🔎 Matriz de avaliação (OCDE-CAD)", "🔎 Evaluation matrix (OECD-DAC)")])
    with t1:
        q = p["quality"]
        names = {"Relevance": tr("Relevância", "Relevance"), "Feasibility": tr("Viabilidade", "Feasibility"), "Effectiveness": tr("Eficácia", "Effectiveness")}
        cols = st.columns(3)
        lab = {"Yes": tr("Sim", "Yes"), "Partial": tr("Parcial", "Partial"), "No": tr("Não", "No")}
        for col, (attr, qs) in zip(cols, AN.QUALITY.items()):
            with col:
                st.markdown(f"**{names[attr]}**")
                for qid, qpt, qen in qs:
                    v = st.radio(tr(qpt, qen), ["Yes", "Partial", "No"], index=["Yes", "Partial", "No"].index(q[qid]) if q.get(qid) in ("Yes", "Partial", "No") else None,
                                 horizontal=True, key=f"q_{qid}_{st.session_state.dv}", format_func=lambda x: lab[x])
                    if v and v != q.get(qid):
                        q[qid] = v
                        ui.mark_dirty()
        sc = AN.quality_scores(q)
        fig = go.Figure(go.Bar(x=[names[k] for k in sc], y=[(v or 0) for v in sc.values()], marker_color=["#2E8B57" if (v or 0) >= 0.75 else "#E67E22" if (v or 0) >= 0.5 else "#C0392B" for v in sc.values()],
                               text=[pct(v, 0) if v is not None else "—" for v in sc.values()], textposition="outside"))
        fig.update_layout(height=300, yaxis=dict(range=[0, 1.15], tickformat=".0%"), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        weak = [names[k] for k, v in sc.items() if v is not None and v < 0.75]
        ui.interpret(tr("Atributos a reforçar: " + ", ".join(weak) + "." if weak else "Os três atributos de qualidade estão bem cobertos.",
                        "Attributes to strengthen: " + ", ".join(weak) + "." if weak else "All three quality attributes are well covered.")
                     + tr(" Lembre-se: o PCM é um ciclo PDCA — as lições aprendidas alimentam o próximo ciclo de programação.", " Remember: PCM is a PDCA cycle — lessons learned feed the next programming cycle."))
    with t2:
        st.caption(tr("Critérios OCDE-CAD: Relevance, Coherence, Effectiveness, Efficiency, Impact, Sustainability.", "OECD-DAC criteria: Relevance, Coherence, Effectiveness, Efficiency, Impact, Sustainability."))
        rows = ui.edit_table("evaluation", overrides={"criterion": st.column_config.SelectboxColumn(ui.label("criterion"), options=DAC_CRITERIA)})
        covered = {r["criterion"] for r in rows}
        miss = [c for c in DAC_CRITERIA if c not in covered]
        ui.interpret(tr(f"A matriz cobre {len(covered)} dos 6 critérios OCDE-CAD" + (f"; faltam: {', '.join(miss)}." if miss else "."),
                        f"The matrix covers {len(covered)} of the 6 OECD-DAC criteria" + (f"; missing: {', '.join(miss)}." if miss else ".")))
