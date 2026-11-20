"""6 · Implementation & Monitoring: indicators & milestones, change control, risk/assumption reviews & contingency,
stakeholder engagement & feedback, cash flow & funding, tenders & contracts, communication plan, progress report."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import agent as AG
from core import analysis as AN
from core import monitor as M
from core import schedule as S
from core import ui
from core.fmt import d, money, num, pct
from core.i18n import OPTIONS, opt_codes, opt_label, tr

SEL = st.column_config.SelectboxColumn


def _acts(p):
    return [""] + [a["id"] for a in p["activities"]]


def _sched(p):
    s = S.compute(p)
    return s if s.get("ok") else None


# ============================================================================= indicators & milestones
def monitoring():
    p = ui.P()
    ui.header("Monitorização de indicadores e marcos", "Indicator & milestone monitoring", "monitoring", "📡")
    t1, t2 = st.tabs([tr("📏 Indicadores", "📏 Indicators"), tr("🚩 Marcos e entregáveis", "🚩 Milestones & deliverables")])
    with t1:
        ov = M.indicators_overview(p)
        if not ov:
            st.info(tr("Defina primeiro os indicadores (5 · Indicadores SMART).", "Define indicators first (5 · SMART indicators)."))
        else:
            df = pd.DataFrame([{"ID": o["id"], ui.label("indicator"): o["indicator"][:70], tr("Nível", "Level"): opt_label("level", o["level"]) if o["level"] else "—",
                                "Baseline": o["baseline"], tr("Meta", "Target"): o["target"], tr("Último valor", "Last value"): o["last_value"],
                                tr("Data", "Date"): d(o["last_date"]) if o["last_date"] else "—", tr("Esperado", "Expected"): o["expected"],
                                tr("Realização", "Achievement"): o["achievement"], tr("Estado", "Status"): f"{M.STATUS_ICON[o['status']]} {M.status_label(o['status'])}",
                                tr("Medições", "Measurements"): o["n"]} for o in ov])
            st.dataframe(df.style.format({"Baseline": "{:,.2f}", tr("Meta", "Target"): "{:,.2f}", tr("Último valor", "Last value"): "{:,.2f}", tr("Esperado", "Expected"): "{:,.2f}"}, na_rep="—"),
                         hide_index=True, width="stretch",
                         column_config={tr("Realização", "Achievement"): st.column_config.ProgressColumn(tr("Realização", "Achievement"), min_value=0, max_value=1, format="percent")})
            ui.interpret(M.indicators_text(p))
            inds = p["indicators"]
            sel = st.selectbox(tr("Registar medições do indicador", "Record measurements for indicator"), [i["id"] for i in inds],
                               format_func=lambda k: f"{k} — {next(i['indicator'] for i in inds if i['id'] == k)[:90]}", key="mon_ind")
            ind = next(i for i in inds if i["id"] == sel)
            c1, c2 = st.columns([1, 1])
            with c1:
                st.caption(tr("Data no formato AAAA-MM-DD. Cada linha é uma medição (valor, fonte, revisão).", "Date as YYYY-MM-DD. Each row is one measurement (value, source, review)."))
                rows = ui.edit_table("ind_reviews", columns=["date", "value", "source", "review", "reviewer"], key=f"ir_{sel}",
                                     filt=lambda r: str(r.get("indicator_id")) == str(sel), fixed={"indicator_id": sel})
                ser = M.indicator_series(p, sel)
                if ser and st.button(tr("↪️ Usar a última medição como 'valor atual' do indicador", "↪️ Use the last measurement as the indicator's 'current value'")):
                    ind["current"] = ser[-1]["value"]
                    ui.bump()
                    st.rerun()
            with c2:
                fig = go.Figure()
                if ind.get("baseline") is not None and ind.get("target") is not None and ind.get("baseline_year") and ind.get("target_year"):
                    fig.add_trace(go.Scatter(x=[date(int(ind["baseline_year"]), 1, 1), date(int(ind["target_year"]), 12, 31)], y=[ind["baseline"], ind["target"]],
                                             mode="lines", name=tr("Trajetória planeada", "Planned trajectory"), line=dict(color="#2E8B57", dash="dash", width=3)))
                if ser:
                    fig.add_trace(go.Scatter(x=[S.to_date(r["date"]) for r in ser], y=[r["value"] for r in ser], mode="lines+markers",
                                             name=tr("Medido", "Measured"), line=dict(color="#1F3B57", width=3), marker=dict(size=9)))
                if ind.get("target") is not None:
                    fig.add_hline(y=ind["target"], line_dash="dot", line_color="#C0392B", annotation_text=tr("Meta", "Target"))
                fig.update_layout(height=340, yaxis_title=ind.get("unit") or "", legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, width="stretch")
            if rows:
                last = M.indicator_series(p, sel)
                if last:
                    code, exp, ach = M.indicator_status(ind, last[-1]["value"], S.to_date(last[-1]["date"]))
                    ui.interpret(tr(f"{M.STATUS_ICON[code]} Última medição {num(last[-1]['value'], 2)} vs esperado {num(exp, 2)} na trajetória ({M.status_label(code)}); realização {pct(ach) if ach is not None else '—'} da distância baseline→meta.",
                                    f"{M.STATUS_ICON[code]} Last measurement {num(last[-1]['value'], 2)} vs {num(exp, 2)} expected on the trajectory ({M.status_label(code)}); achievement {pct(ach) if ach is not None else '—'} of the baseline→target distance."))
    with t2:
        sched = _sched(p)
        st.caption(tr("Se a data prevista ficar vazia, usa-se o fim da atividade associada no cronograma (CPM). Um marco só conta quando o entregável é aceite.",
                      "If the planned date is empty, the finish of the linked activity in the schedule (CPM) is used. A milestone only counts once the deliverable is accepted."))
        ui.edit_table("milestones", overrides={"activity_id": SEL(ui.label("activity_id"), options=_acts(p))}, key="ms")
        rows = M.milestone_rows(p, sched)
        if rows:
            st.dataframe(pd.DataFrame([{"ID": r["id"], ui.label("name", "milestones"): r.get("name"), tr("Previsto", "Planned"): d(r["planned"]) if r["planned"] else "—",
                                        tr("Previsão", "Forecast"): d(r["forecast"]) if r["forecast"] else "—", tr("Real", "Actual"): d(r["actual"]) if r["actual"] else "—",
                                        tr("Desvio (dias)", "Deviation (days)"): r["deviation"], tr("Aceite", "Accepted"): "✅" if r.get("accepted") else "—",
                                        tr("Estado", "Status"): tr(*M.MS_LABEL[r["code"]])} for r in rows]), hide_index=True, width="stretch")
            fig = go.Figure()
            for r in rows:
                if r["planned"]:
                    fig.add_trace(go.Scatter(x=[r["planned"]], y=[r["id"]], mode="markers", marker=dict(symbol="diamond-open", size=14, color="#1F3B57"), showlegend=False, hovertext=tr("Previsto", "Planned")))
                ref = r["actual"] or r["forecast"]
                if ref and r["planned"]:
                    col = "#2E8B57" if (r["deviation"] or 0) <= 0 else "#C0392B"
                    fig.add_trace(go.Scatter(x=[r["planned"], ref], y=[r["id"], r["id"]], mode="lines+markers", line=dict(color=col, width=3),
                                             marker=dict(symbol=["diamond-open", "diamond"], size=14, color=col), showlegend=False))
            fig.add_vline(x=S.to_date(p["meta"]["status_date"]), line_dash="dot", line_color="#D9822B")
            fig.update_layout(height=60 + 40 * len(rows), margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, width="stretch")
            ui.interpret(M.milestones_text(rows))


# ============================================================================= change control
def changes():
    p = ui.P()
    ui.header("Controlo de alterações e reavaliação de necessidades", "Change control & needs reassessment", "changes", "🔀")
    cur = p["meta"].get("currency", "EUR")
    ui.edit_table("changes", key="cr")
    s = M.changes_summary(p)
    c = st.columns(5)
    c[0].metric(tr("Pedidos", "Requests"), s["n"])
    c[1].metric(tr("Aprovados", "Approved"), s["approved"])
    c[2].metric(tr("Pendentes", "Pending"), s["pending"])
    c[3].metric(tr("Impacto prazo", "Time impact"), f"{s['time']:+.0f} " + tr("dias", "days"))
    c[4].metric(tr("Impacto custo", "Cost impact"), money(s["cost"], cur))
    if p["changes"]:
        st.dataframe(pd.DataFrame([{"ID": c_["id"], ui.label("element_type"): opt_label("change_element", c_["element_type"]), ui.label("element_ref"): c_.get("element_ref"),
                                    tr("Classificação", "Classification"): {"strategic": "🔴 " + tr("Estratégica", "Strategic"), "target": "🟡 " + tr("Meta", "Target"),
                                                                             "tactical": "🟢 " + tr("Tática", "Tactical")}[M.change_class(c_)[0]],
                                    tr("Regra", "Rule"): M.change_class(c_)[1], ui.label("status"): opt_label("change_status", c_["status"])} for c_ in p["changes"]]),
                     hide_index=True, width="stretch", column_config={tr("Regra", "Rule"): st.column_config.TextColumn(width="large")})
    ui.interpret(M.changes_text(p, cur))
    cw = M.changes_by_wbs(p)
    if cw:
        st.markdown(tr("##### Propagação das alterações aprovadas na WBS / EAP", "##### Approved changes propagated through the WBS"))
        st.dataframe(pd.DataFrame([{tr("Código WBS", "WBS code"): r["code"], tr("Elemento", "Element"): ("\u2003" * (r["code"].count("."))) + r["name"][:70],
                                    tr("Impacto custo", "Cost impact"): r["cost"], tr("Impacto prazo (dias)", "Time impact (days)"): r["days"],
                                    tr("Pedidos", "Requests"): ", ".join(dict.fromkeys(r["changes"]))} for r in cw]).style.format({tr("Impacto custo", "Cost impact"): "{:,.0f}"}),
                     hide_index=True, width="stretch")
        from core.help_texts import wbs_tip
        st.caption(tr("Indique em 'Referência (ID)' o código WBS (ex.: 1.2) ou o ID da atividade; o impacto sobe automaticamente pelos níveis da WBS. ",
                      "Enter the WBS code (e.g. 1.2) or the activity ID in 'Reference (ID)'; the impact rolls up automatically through the WBS levels. ") + "🧮 " + wbs_tip("change_prop"))
    with st.expander(tr("🔎 Reavaliação das necessidades (problemas e pressupostos)", "🔎 Needs reassessment (problems & assumptions)")):
        st.caption(tr("O problema central ainda existe? Os pressupostos confirmam-se? Se o outcome deixou de ser relevante, a alteração é estratégica.",
                      "Does the core problem still exist? Do assumptions hold? If the outcome is no longer relevant, the change is strategic."))
        core = [x for x in p["problems"] if x.get("level") == "Core problem"]
        for x in core:
            st.markdown(f"**{tr('Problema central', 'Core problem')} {x['id']}:** {x['text']}")
        al = M.assumption_latest(p)
        if al:
            st.dataframe(pd.DataFrame([{"ID": a["id"], tr("Pressuposto", "Assumption"): a["text"][:90], tr("Último estado", "Latest status"): opt_label("asm_status", a["status"]) if a["status"] else "—",
                                        tr("Data", "Date"): a["date"] or "—"} for a in al]), hide_index=True, width="stretch")
    if p["changes"]:
        sel = st.selectbox(tr("Pedido a analisar pelo agente", "Request for the agent to review"), [c_["id"] for c_ in p["changes"]])
        ui.ai_text("Analisar pedido de alteração", "Review change request", f"change_{sel}", lambda: AG.change_review(p, sel, st.session_state.get("ai_model")))


# ============================================================================= risk & assumption reviews, contingency
def reviews():
    p = ui.P()
    ui.header("Revisão de riscos, pressupostos e contingência", "Risk, assumption & contingency reviews", "risk_review", "🔁")
    cur = p["meta"].get("currency", "EUR")
    t1, t2, t3 = st.tabs([tr("⚠️ Riscos", "⚠️ Risks"), tr("🧱 Pressupostos", "🧱 Assumptions"), tr("🛟 Contingência", "🛟 Contingency")])
    with t1:
        if not p["risks"]:
            st.info(tr("Registe primeiro os riscos (3 · Riscos).", "Register risks first (3 · Risks)."))
        else:
            h = M.risk_history(p)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=[x["id"] for x in h], y=[x["initial"] for x in h], name=tr("Exposição inicial", "Initial exposure"), marker_color="#BBBBBB"))
            fig.add_trace(go.Bar(x=[x["id"] for x in h], y=[x["latest"] for x in h], name=tr("Exposição atual", "Current exposure"), marker_color=[AN.risk_color(x["latest"]) for x in h]))
            fig.add_trace(go.Scatter(x=[x["id"] for x in h], y=[x["target"] for x in h], mode="markers", name=tr("Alvo", "Target"), marker=dict(symbol="line-ew-open", size=26, color="#1F3B57", line=dict(width=3))))
            fig.update_layout(barmode="group", height=320, yaxis=dict(range=[0, 16.5], title="L × I"), legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch")
            st.dataframe(pd.DataFrame([{"ID": x["id"], tr("Risco", "Risk"): x["description"][:70], tr("Inicial", "Initial"): x["initial"], tr("Atual", "Current"): x["latest"],
                                        "Δ": x["trend"], ui.label("status"): opt_label("risk_status", x["status"]), tr("Revisões", "Reviews"): x["n"],
                                        tr("Custo incorrido", "Cost incurred"): x["cost_impact"], tr("Atraso (dias)", "Delay (days)"): x["delay"]} for x in h]),
                         hide_index=True, width="stretch")
            ui.interpret(M.risks_review_text(p, cur))
            sel = st.selectbox(tr("Registar revisão do risco", "Record a review for risk"), [r["id"] for r in p["risks"]],
                               format_func=lambda k: f"{k} — {next(r['description'] for r in p['risks'] if r['id'] == k)[:90]}")
            ui.edit_table("risk_reviews", columns=["date", "likelihood", "impact", "status", "incident", "delay", "cost_impact", "note"], key=f"rr_{sel}",
                          filt=lambda r: str(r.get("risk_id")) == str(sel), fixed={"risk_id": sel})
    with t2:
        if not p["assumptions"]:
            st.info(tr("Registe primeiro os pressupostos.", "Register assumptions first."))
        else:
            ov = {"assumption_id": SEL(ui.label("assumption_id"), options=[h["id"] for h in p["assumptions"]])}
            ui.edit_table("assumption_reviews", overrides=ov, key="ar")
            al = M.assumption_latest(p)
            icon = {"Confirmed": "🟢", "At risk": "🟡", "Not confirmed": "🔴", None: "⚪"}
            st.dataframe(pd.DataFrame([{"ID": a["id"], tr("Nível", "Level"): opt_label("level", a["level"]) if a["level"] else "—", tr("Pressuposto", "Assumption"): a["text"][:90],
                                        tr("Estado", "Status"): f"{icon[a['status']]} {opt_label('asm_status', a['status']) if a['status'] else tr('Por rever', 'Not reviewed')}",
                                        tr("Revisões", "Reviews"): a["n"]} for a in al]), hide_index=True, width="stretch")
            ui.interpret(M.assumptions_text(p))
    with t3:
        m = p["meta"]
        sched = _sched(p)
        bac = sched["bac"] if sched else None
        c1, c2 = st.columns(2)
        mr = c1.slider(tr("Reserva de gestão (% do BAC)", "Management reserve (% of BAC)"), 0.0, 0.20, float(m.get("mgmt_reserve_pct") or 0), 0.01, format="%.2f")
        if mr != m.get("mgmt_reserve_pct"):
            m["mgmt_reserve_pct"] = mr
            ui.mark_dirty()
        c2.caption(tr("A reserva de contingência é definida em 3 · Contingências (percentagem ou soma por risco). Registe aqui cada utilização, libertação ou reforço.",
                      "The contingency reserve is set in 3 · Contingencies (percentage or sum per risk). Record here each use, release or reinforcement."))
        ui.edit_table("contingency_log", overrides={"risk_id": SEL(ui.label("risk"), options=[""] + [r["id"] for r in p["risks"]])}, key="cl")
        cs = M.contingency_status(p, bac)
        used = cs["Contingency reserve"]["used"]
        if p["contingency_log"] and abs(used - float(m.get("contingency_used") or 0)) > 0.5:
            m["contingency_used"] = used
            ui.mark_dirty()
        cols = st.columns(4)
        for i, (k, lab) in enumerate((("Contingency reserve", tr("Contingência", "Contingency")), ("Management reserve", tr("Gestão", "Management")))):
            x = cs[k]
            cols[2 * i].metric(f"{lab} — " + tr("inicial + reforço", "initial + reinforcement"), money(x["initial"] + x["reinforced"], cur))
            cols[2 * i + 1].metric(f"{lab} — " + tr("disponível", "available"), money(x["available"], cur), money(-x["used"], cur) if x["used"] else None)
        x = cs["Contingency reserve"]
        fig = go.Figure(go.Waterfall(x=[tr("Inicial", "Initial"), tr("Reforço", "Reinforcement"), tr("Utilizado", "Used"), tr("Libertado", "Released"), tr("Disponível", "Available")],
                                     measure=["absolute", "relative", "relative", "relative", "total"],
                                     y=[x["initial"], x["reinforced"], -x["used"], -x["released"], 0], connector=dict(line=dict(color="#999"))))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), yaxis_title=cur)
        st.plotly_chart(fig, width="stretch")
        prog = None
        if sched:
            e = S.evm(p, sched)
            prog = e["EV"] / e["BAC"] if e["BAC"] else None
        ui.interpret(M.contingency_text(p, cs, prog, cur))


# ============================================================================= engagement & feedback
def engagement():
    p = ui.P()
    ui.header("Envolvimento dos stakeholders e feedback", "Stakeholder engagement & feedback", "engagement", "🤝")
    names = [s["name"] for s in p["stakeholders"] if s.get("name")]
    t1, t2 = st.tabs([tr("🤝 Plano de envolvimento", "🤝 Engagement plan"), tr("💬 Feedback", "💬 Feedback")])
    with t1:
        ui.edit_table("engagement", overrides={"stakeholder": SEL(ui.label("stakeholder"), options=[""] + names)}, key="en")
        ui.interpret(M.engagement_text(p))
        with st.expander(tr("📚 Ferramentas de envolvimento (quando usar)", "📚 Engagement tools (when to use)")):
            st.markdown(tr("""- **Intermediários** — quando a relação direta é difícil (desconfiança, distância cultural).
- **Partilha de informação** — base de qualquer relação; transparência sobre objetivos, prazos e decisões.
- **Interação repetida** — constrói confiança ao longo do tempo (reuniões regulares).
- **Representantes indiretos (surrogates)** — quando o grupo não pode participar diretamente (ex.: ONG que representa crianças).
- **Técnicas de nivelamento** — reduzir assimetrias de poder (facilitação neutra, votação anónima).
- **Eventos separados** — grupos com interesses em conflito ou que não falam à vontade juntos.
- **Capacitação** — dar ao stakeholder a capacidade de participar de forma informada.
- **Começar cedo e de forma ampla**, **procurar terreno comum** e **gerir o impasse** — princípios transversais.""",
                           """- **Intermediaries** — when a direct relationship is difficult (distrust, cultural distance).
- **Information sharing** — the basis of any relationship; transparency about objectives, timing and decisions.
- **Repeated interaction** — builds trust over time (regular meetings).
- **Surrogates** — when the group cannot take part directly (e.g. an NGO representing children).
- **Levelling techniques** — reduce power asymmetries (neutral facilitation, anonymous voting).
- **Separate events** — groups with conflicting interests or who are not at ease together.
- **Capacity building** — enable the stakeholder to take part in an informed way.
- **Start early and broadly**, **seek common ground** and **deal with deadlock** — cross-cutting principles."""))
    with t2:
        ui.edit_table("feedback", overrides={"stakeholder_group": SEL(ui.label("stakeholder_group"), options=[""] + names)}, key="fb")
        s = M.feedback_summary(p)
        if s["n"]:
            c1, c2 = st.columns([1, 2])
            c1.metric(tr("Satisfação média", "Average satisfaction"), f"{s['avg']:.1f}/5" if s["avg"] else "—")
            c1.metric(tr("Em aberto", "Open"), s["open"])
            fig = go.Figure(go.Bar(y=list(s["by_group"]), x=list(s["by_group"].values()), orientation="h",
                                   marker_color=["#2E8B57" if v >= 4 else "#E3B23C" if v >= 3 else "#C0392B" for v in s["by_group"].values()]))
            fig.update_layout(height=60 + 34 * len(s["by_group"]), xaxis=dict(range=[0, 5], title=tr("Satisfação média", "Average satisfaction")), margin=dict(l=10, r=10, t=10, b=10))
            c2.plotly_chart(fig, width="stretch")
        ui.interpret(M.feedback_text(p))
        ui.ai_text("Analisar feedback (temas, mudança mais significativa)", "Analyse feedback (themes, most significant change)", "feedback",
                   lambda: AG.feedback_analysis(p, st.session_state.get("ai_model")))


# ============================================================================= cash flow & funding
def cash():
    p = ui.P()
    ui.header("Tesouraria e financiamento", "Cash flow & funding", "cashflow", "🏦")
    cur = p["meta"].get("currency", "EUR")
    sched = _sched(p)
    if not sched:
        st.info(tr("Defina primeiro as atividades e o cronograma.", "Define activities and the schedule first."))
        return
    ui.edit_table("funding", key="fd")
    df = M.cash_position(p, sched)
    sc = S.s_curve(p, sched)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["period"], y=df["pv_cum"], name=tr("Necessidades (PV acum.)", "Needs (cum. PV)"), line=dict(color="#1F3B57", width=3)))
    if "ac_cum" in sc:
        fig.add_trace(go.Scatter(x=sc["period"], y=sc["ac_cum"], name=tr("Custo real (AC acum.)", "Actual cost (cum. AC)"), line=dict(color="#C0392B", width=3), connectgaps=True))
    fig.add_trace(go.Scatter(x=df["period"], y=df["funds_all_cum"], name=tr("Financiamento previsto + recebido", "Planned + received funding"), line=dict(color="#2E8B57", dash="dash", shape="hv")))
    fig.add_trace(go.Scatter(x=df["period"], y=df["funds_received_cum"], name=tr("Financiamento recebido", "Funding received"), line=dict(color="#2E8B57", width=3, shape="hv")))
    neg = df[df["gap"] < 0]
    if not neg.empty:
        fig.add_trace(go.Bar(x=neg["period"], y=-neg["gap"], name=tr("Défice", "Shortfall"), marker_color="rgba(192,57,43,0.35)"))
    fig.update_layout(height=420, yaxis_title=cur, legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    tot = sum(float(f.get("amount") or 0) for f in p["funding"])
    rec = sum(float(f.get("amount") or 0) for f in p["funding"] if f.get("status") == "Received")
    c = st.columns(4)
    c[0].metric("BAC + " + tr("contingência", "contingency"), money(sched["bac"] + sched["contingency"], cur))
    c[1].metric(tr("Financiamento total", "Total funding"), money(tot, cur))
    c[2].metric(tr("Recebido", "Received"), money(rec, cur))
    c[3].metric(tr("Cobertura", "Coverage"), pct(tot / (sched["bac"] + sched["contingency"])) if sched["bac"] else "—")
    ui.interpret(M.cash_text(df, cur))


# ============================================================================= tenders & contracts
def tenders():
    p = ui.P()
    ui.header("Concursos, contratos e encerramento de contratos", "Tenders, contracts & contract closure", "tenders", "📜")
    cur = p["meta"].get("currency", "EUR")
    if not p["procurement"]:
        st.info(tr("Defina primeiro o plano de procurement (3 · Procurement).", "Define the procurement plan first (3 · Procurement)."))
        return
    st.markdown(tr("##### Tipo de contrato e etapa do concurso", "##### Contract type & tender stage"))
    ui.edit_table("procurement", columns=["id", "item", "estimated_cost", "scope_certainty", "contract_type", "stage", "tech_weight", "awarded_to", "contract_value"],
                  key="tnd", num_rows="fixed", disabled=["id", "item"],
                  overrides={"tech_weight": st.column_config.NumberColumn(ui.label("tech_weight"), min_value=0.0, max_value=1.0, step=0.05, format="%.2f")})
    st.dataframe(pd.DataFrame([{"ID": q["id"], "Item": q["item"], ui.label("scope_certainty"): opt_label("certainty", q["scope_certainty"]),
                                tr("Contrato", "Contract"): opt_label("contract_type", q["contract_type"]),
                                tr("Recomendado", "Recommended"): ", ".join(opt_label("contract_type", c) for c in M.contract_advice(q["scope_certainty"])),
                                tr("Coerente?", "Fits?"): "✅" if q["contract_type"] in M.contract_advice(q["scope_certainty"]) else "⚠️",
                                tr("Etapa", "Stage"): opt_label("tender_stage", q["stage"]),
                                tr("Progresso", "Progress"): opt_codes("tender_stage").index(q["stage"]) / 16 if q["stage"] in opt_codes("tender_stage") else 0}
                               for q in p["procurement"]]), hide_index=True, width="stretch",
                 column_config={tr("Progresso", "Progress"): st.column_config.ProgressColumn(tr("Progresso", "Progress"), min_value=0, max_value=1, format="percent")})
    ui.interpret(M.procurement_text(p, cur))
    with st.expander(tr("📚 Tipos de contrato — quem suporta o risco e quando usar", "📚 Contract types — who bears the risk and when to use")):
        st.dataframe(pd.DataFrame([{tr("Tipo", "Type"): opt_label("contract_type", k), tr("Risco sobretudo do", "Risk mostly on"): {"seller": tr("fornecedor", "seller"), "buyer": tr("comprador", "buyer"), "shared": tr("partilhado", "shared")}[v[0]],
                                    tr("Quando usar", "When to use"): tr(v[1], v[2])} for k, v in M.CONTRACTS.items()]), hide_index=True, width="stretch")
    sel = st.selectbox(tr("Aquisição", "Purchase"), [q["id"] for q in p["procurement"]], format_func=lambda k: f"{k} — {next(q['item'] for q in p['procurement'] if q['id'] == k)}")
    q = next(x for x in p["procurement"] if x["id"] == sel)
    t1, t2 = st.tabs([tr("📊 Propostas e grelha de avaliação", "📊 Bids & evaluation grid"), tr("✅ Encerramento do contrato (15 passos)", "✅ Contract closure (15 steps)")])
    with t1:
        ui.edit_table("bids", columns=["bidder", "compliant", "technical_score", "price", "note"], key=f"bd_{sel}",
                      filt=lambda r: str(r.get("procurement_id")) == str(sel), fixed={"procurement_id": sel})
        sc = M.bid_scores([b for b in p["bids"] if str(b.get("procurement_id")) == str(sel)], q.get("tech_weight"))
        if sc:
            w = float(q.get("tech_weight") if q.get("tech_weight") is not None else 0.7)
            st.dataframe(pd.DataFrame([{"#": r["rank"], tr("Concorrente", "Bidder"): r["bidder"], tr("Técnica", "Technical"): r["technical"], tr("Financeira", "Financial"): r["financial"],
                                        tr("Preço", "Price"): r["price"], "Total": r["total"]} for r in sc])
                         .style.format({tr("Técnica", "Technical"): "{:.1f}", tr("Financeira", "Financial"): "{:.1f}", tr("Preço", "Price"): "{:,.0f}", "Total": "{:.1f}"}),
                         hide_index=True, width="stretch")
            ui.interpret(tr(f"Grelha: Total = {w:.0%} × técnica + {1 - w:.0%} × financeira (100 × preço mínimo / preço). Melhor proposta: **{sc[0]['bidder']}** ({sc[0]['total']:.1f} pontos, {money(sc[0]['price'], cur)}"
                            + (f", {money(sc[0]['price'] - float(q['estimated_cost'] or 0), cur)} face à estimativa" if q.get("estimated_cost") else "") + ").",
                            f"Grid: Total = {w:.0%} × technical + {1 - w:.0%} × financial (100 × lowest price / price). Best bid: **{sc[0]['bidder']}** ({sc[0]['total']:.1f} points, {money(sc[0]['price'], cur)}"
                            + (f", {money(sc[0]['price'] - float(q['estimated_cost'] or 0), cur)} vs estimate" if q.get("estimated_cost") else "") + ")."))
            if not q.get("awarded_to") and st.button(tr(f"🏆 Adjudicar a {sc[0]['bidder']}", f"🏆 Award to {sc[0]['bidder']}")):
                q.update(awarded_to=sc[0]["bidder"], contract_value=sc[0]["price"], stage="ts13")
                ui.bump()
                st.rerun()
    with t2:
        have = {c["step"] for c in p["closure"] if str(c.get("procurement_id")) == str(sel)}
        if len(have) < 15 and st.button(tr("➕ Criar a lista completa de 15 passos", "➕ Create the full 15-step checklist")):
            p["closure"] += [{"procurement_id": sel, "step": c, "done": False, "date": "", "note": ""} for c in opt_codes("closure_step") if c not in have]
            p["closure"].sort(key=lambda r: (str(r["procurement_id"]), r["step"]))
            ui.bump()
            st.rerun()
        ui.edit_table("closure", columns=["step", "done", "date", "note"], key=f"cl_{sel}", filt=lambda r: str(r.get("procurement_id")) == str(sel), fixed={"procurement_id": sel})
        done, tot = M.closure_progress(p, sel)
        st.progress(done / tot, text=tr(f"{done} de {tot} passos concluídos", f"{done} of {tot} steps done"))


# ============================================================================= communication plan
def comm():
    p = ui.P()
    ui.header("Plano de comunicação", "Communication plan", "comm", "📣")
    cur = p["meta"].get("currency", "EUR")
    ui.edit_table("comm_plan", overrides={"activity_id": SEL(ui.label("activity_id"), options=_acts(p))}, key="cp")
    rows = p["comm_plan"]
    if rows:
        c1, c2 = st.columns(2)
        by = {}
        for r in rows:
            by[opt_label("audience_circle", r["circle"])] = by.get(opt_label("audience_circle", r["circle"]), 0) + float(r.get("budget") or 0)
        fig = go.Figure(go.Pie(labels=list(by), values=list(by.values()), hole=0.55, sort=False, marker=dict(colors=["#1F3B57", "#2C7FB8", "#9ECAE1"])))
        fig.update_layout(height=300, title=tr("Orçamento por círculo de audiência", "Budget by audience circle"), margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.1))
        c1.plotly_chart(fig, width="stretch")
        rr = [r for r in rows if r.get("target")]
        if rr:
            fig = go.Figure(go.Bar(x=[r["id"] for r in rr], y=[(r.get("actual") or 0) / r["target"] for r in rr], text=[r.get("indicator") for r in rr],
                                   marker_color=["#2E8B57" if (r.get("actual") or 0) >= r["target"] else "#E3B23C" for r in rr]))
            fig.add_hline(y=1, line_dash="dot")
            fig.update_layout(height=300, title=tr("Alcance real / meta", "Actual / target reach"), yaxis=dict(tickformat=".0%"), margin=dict(l=10, r=10, t=40, b=10))
            c2.plotly_chart(fig, width="stretch")
    ui.interpret(M.comm_text(p, cur))
    ui.ai_tables("Propor plano de comunicação (3 círculos)", "Propose communication plan (3 circles)", "comm", lambda: AG.gen_comm_plan(p, st.session_state.get("ai_model")))


# ============================================================================= progress report
def progress_report():
    p = ui.P()
    ui.header("Relatório de progresso", "Progress report", "progress_report", "🗞️")
    cur = p["meta"].get("currency", "EUR")
    sched = _sched(p)
    ep = M.efficiency_panel(p, sched)
    c = st.columns(6)
    c[0].metric(tr("Progresso físico", "Physical progress"), pct(ep["progress"]) if ep["progress"] is not None else "—")
    c[1].metric("CPI", num(ep["CPI"], 2))
    c[2].metric("SPI", num(ep["SPI"], 2))
    c[3].metric(tr("Indicadores na trajetória", "Indicators on track"), pct(ep["ind_on_track"], 0) if ep["ind_on_track"] is not None else "—")
    c[4].metric(tr("Marcos a tempo", "Milestones on time"), pct(ep["ms_on_time"], 0) if ep["ms_on_time"] is not None else "—")
    c[5].metric(tr("Satisfação", "Satisfaction"), f"{ep['satisfaction']:.1f}/5" if ep["satisfaction"] else "—")
    sections = [(tr("Indicadores", "Indicators"), M.indicators_text(p)), (tr("Marcos", "Milestones"), M.milestones_text(M.milestone_rows(p, sched))),
                (tr("Custo e prazo (EVM)", "Cost and schedule (EVM)"), M.efficiency_text(ep)), (tr("Riscos", "Risks"), M.risks_review_text(p, cur)),
                (tr("Pressupostos", "Assumptions"), M.assumptions_text(p)), (tr("Alterações", "Changes"), M.changes_text(p, cur)),
                (tr("Contingência", "Contingency"), M.contingency_text(p, M.contingency_status(p, sched["bac"] if sched else None), ep["progress"], cur)),
                (tr("Tesouraria", "Cash"), M.cash_text(M.cash_position(p, sched), cur) if sched else ""), (tr("Stakeholders e feedback", "Stakeholders & feedback"), M.feedback_text(p)),
                (tr("Comunicação", "Communication"), M.comm_text(p, cur)), (tr("Concursos e contratos", "Tenders & contracts"), M.procurement_text(p, cur))]
    md = f"# {tr('Relatório de progresso', 'Progress report')} — {p['meta'].get('name', '')}\n\n{tr('Data de controlo', 'Status date')}: {p['meta'].get('status_date')}\n\n"
    for h, t in sections:
        if t:
            ui.interpret(t, h)
            md += f"## {h}\n\n{t}\n\n"
    st.download_button(tr("⬇️ Descarregar relatório automático (Markdown)", "⬇️ Download automatic report (Markdown)"), md.encode("utf-8"), "relatorio_progresso.md", "text/markdown")
    st.divider()
    st.markdown(tr("#### 🤖 Relatório redigido pelo agente IA", "#### 🤖 Report written by the AI agent"))
    c1, c2 = st.columns(2)
    aud = c1.selectbox(tr("Audiência", "Audience"), ["donor", "management", "community"],
                       format_func=lambda a: {"donor": tr("Financiador (prestação de contas)", "Donor (accountability)"), "management": tr("Gestão / comité de acompanhamento", "Management / steering committee"),
                                              "community": tr("Beneficiários e comunidade", "Beneficiaries & community")}[a])
    per = c2.text_input(tr("Período", "Period"), value=f"{p['meta'].get('start_date')} → {p['meta'].get('status_date')}")
    ui.ai_text("Redigir relatório de progresso", "Write progress report", f"progress_{aud}", lambda: AG.progress_report(p, aud, per, st.session_state.get("ai_model")))
