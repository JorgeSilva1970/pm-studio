"""4 · Financial appraisal: WACC, NPV, IRR, MIRR, payback, sensitivity."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import finance as F
from core import interpret as I
from core import schedule as S
from core import ui
from core.fmt import money, num, pct
from core.i18n import tr


def render():
    p = ui.P()
    ui.header("Análise financeira — VAL, TIR, MIRR e WACC", "Financial appraisal — NPV, IRR, MIRR & WACC", "finance", "📈")
    f = p["finance"]
    cur = p["meta"].get("currency", "EUR")
    st.markdown("#### 1. WACC")
    c1, c2, c3, c4 = st.columns(4)
    f["equity"] = c1.number_input(tr("Capital próprio (E)", "Equity (E)"), 0.0, 1e13, float(f.get("equity") or 0), step=10000.0)
    f["debt"] = c2.number_input(tr("Dívida (D)", "Debt (D)"), 0.0, 1e13, float(f.get("debt") or 0), step=10000.0)
    f["kd"] = c3.number_input(tr("Custo da dívida Kd", "Cost of debt Kd"), 0.0, 1.0, float(f.get("kd") or 0), 0.0025, format="%.4f")
    f["tax"] = c4.number_input(tr("Taxa de imposto t", "Tax rate t"), 0.0, 1.0, float(f.get("tax") or 0), 0.01, format="%.3f")
    c1, c2, c3, c4 = st.columns(4)
    f["ke_method"] = c1.radio(tr("Custo do capital próprio Ke", "Cost of equity Ke"), ["capm", "direct"], index=0 if f.get("ke_method") == "capm" else 1,
                              format_func=lambda v: "CAPM" if v == "capm" else tr("Direto", "Direct"), horizontal=True)
    if f["ke_method"] == "capm":
        f["rf"] = c2.number_input(tr("Taxa sem risco rf", "Risk-free rate rf"), 0.0, 1.0, float(f.get("rf") or 0), 0.0025, format="%.4f")
        f["beta"] = c3.number_input("β", 0.0, 5.0, float(f.get("beta") or 1), 0.05)
        f["mrp"] = c4.number_input(tr("Prémio de risco de mercado", "Market risk premium"), 0.0, 1.0, float(f.get("mrp") or 0), 0.0025, format="%.4f")
    else:
        f["ke"] = c2.number_input("Ke", 0.0, 1.0, float(f.get("ke") or 0), 0.0025, format="%.4f")
    w = F.wacc(f)
    c = st.columns(4)
    c[0].metric("Ke", pct(w["ke"], 2))
    c[1].metric(tr("Kd após imposto", "After-tax Kd"), pct(w["kd_after_tax"], 2))
    c[2].metric("E/V · D/V", f"{pct(w['we'], 0)} · {pct(w['wd'], 0)}")
    c[3].metric("WACC", pct(w["wacc"], 2))
    st.latex(r"WACC=\frac{E}{V}K_e+\frac{D}{V}K_d(1-t)" + (r"\qquad K_e=r_f+\beta\,(E[R_m]-r_f)" if f["ke_method"] == "capm" else ""))
    with st.expander(tr("Taxas alternativas (opcional)", "Alternative rates (optional)")):
        c1, c2, c3, c4 = st.columns(4)
        ov = c1.number_input(tr("Taxa de desconto (vazio = WACC)", "Discount rate (blank = WACC)"), 0.0, 1.0, float(f.get("rate_override") or 0), 0.0025, format="%.4f")
        f["rate_override"] = ov or None
        fr = c2.number_input(tr("Taxa de financiamento (MIRR)", "Finance rate (MIRR)"), 0.0, 1.0, float(f.get("finance_rate") or 0), 0.0025, format="%.4f")
        f["finance_rate"] = fr or None
        rr = c3.number_input(tr("Taxa de reinvestimento (MIRR)", "Reinvestment rate (MIRR)"), 0.0, 1.0, float(f.get("reinvest_rate") or 0), 0.0025, format="%.4f")
        f["reinvest_rate"] = rr or None
        f["residual_value"] = c4.number_input(tr("Valor residual (último ano)", "Residual value (last year)"), 0.0, 1e13, float(f.get("residual_value") or 0), step=10000.0)
    ui.mark_dirty() if st.session_state.get("_fin_prev") != str(f) else None
    st.session_state["_fin_prev"] = str(f)

    st.markdown(tr("#### 2. Fluxos de caixa anuais", "#### 2. Annual cash flows"))
    sched = S.compute(p)
    c1, c2 = st.columns([3, 2])
    inc = c2.checkbox(tr("Incluir contingência no investimento", "Include contingency in investment"), value=bool(f.get("include_contingency", True)))
    f["include_contingency"] = inc
    if c1.button(tr("⬇️ Importar investimento do cronograma (Gantt)", "⬇️ Import investment from the schedule (Gantt)"), disabled=not sched.get("ok"),
                 help=tr("Substitui a coluna Investimento pelo custo das atividades por ano do projeto", "Replaces the Investment column with activity cost per project year")):
        inv = S.yearly_investment(sched)
        k = 1 + (sched["contingency"] / sched["bac"] if inc and sched["bac"] else 0)
        rows = {int(r["year"]): r for r in p["cashflows"]}
        for y in range(0, max(list(inv) + list(rows) + [0]) + 1):
            r = rows.setdefault(y, {"year": y, "investment": 0.0, "operating_costs": 0.0, "benefits": 0.0, "note": ""})
            r["investment"] = round(inv.get(y, 0.0) * k, 0)
        p["cashflows"] = [rows[y] for y in sorted(rows)]
        ui.bump()
        st.rerun()
    cfs = ui.edit_table("cashflows", columns=["year", "investment", "operating_costs", "benefits", "note"])
    st.caption(tr("Ano 0 = início do projeto. Fluxo líquido = benefícios − custos operacionais − investimento.", "Year 0 = project start. Net flow = benefits − operating costs − investment."))
    if not cfs:
        return
    a = F.analyse(cfs, f, float(f.get("residual_value") or 0))
    be = F.breakeven_benefit_factor(cfs, f, float(f.get("residual_value") or 0))
    st.markdown(tr("#### 3. Indicadores de viabilidade", "#### 3. Feasibility indicators"))
    c = st.columns(6)
    c[0].metric(tr("VAL (NPV)", "NPV"), money(a["npv"], cur))
    c[1].metric(tr("TIR (IRR)", "IRR"), pct(a["irr"], 2) if a["irr"] is not None else "—", delta=(pct(a["irr"] - a["rate"], 2) + " vs WACC") if a["irr"] is not None else None)
    c[2].metric("MIRR", pct(a["mirr"], 2) if a["mirr"] is not None else "—")
    c[3].metric("Payback", f"{num(a['payback'], 1)} {tr('anos', 'yrs')}" if a["payback"] is not None else "—")
    c[4].metric(tr("Payback atualizado", "Discounted payback"), f"{num(a['disc_payback'], 1)} {tr('anos', 'yrs')}" if a["disc_payback"] is not None else "—")
    c[5].metric(tr("Índice de rendibilidade", "Profitability index"), num(a["pi"], 2) if a["pi"] else "—")
    tab = pd.DataFrame({tr("Ano", "Year"): range(len(a["flows"])), tr("Investimento", "Investment"): a["investment"], tr("Custos operacionais", "Operating costs"): a["operating_costs"],
                        tr("Benefícios", "Benefits"): a["benefits"], tr("Fluxo líquido", "Net flow"): a["flows"], tr("Fluxo atualizado", "Discounted flow"): a["discounted"],
                        tr("Acumulado atualizado", "Cumulative discounted"): a["cum_disc"]})
    st.dataframe(tab.style.format({c_: "{:,.0f}" for c_ in tab.columns[1:]}), hide_index=True, width="stretch")
    c1, c2 = st.columns(2)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tab.iloc[:, 0], y=a["flows"], name=tr("Fluxo líquido", "Net flow"), marker_color=["#C0392B" if v < 0 else "#2E8B57" for v in a["flows"]]))
    fig.add_trace(go.Scatter(x=tab.iloc[:, 0], y=a["cum_disc"], name=tr("Acumulado atualizado", "Cumulative discounted"), line=dict(color="#1F3B57", width=3)))
    fig.add_hline(y=0, line_color="#999")
    fig.update_layout(height=340, xaxis_title=tr("Ano", "Year"), legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=10, b=10))
    c1.plotly_chart(fig, width="stretch")
    prof = F.npv_profile(a["flows"], rmax=max(0.3, (a["irr"] or 0.1) * 2))
    fig = go.Figure(go.Scatter(x=[r for r, _ in prof], y=[v for _, v in prof], line=dict(color="#1F3B57", width=3), name="VAL(r)"))
    fig.add_hline(y=0, line_color="#999")
    fig.add_vline(x=a["rate"], line_dash="dash", line_color="#D9822B", annotation_text="WACC")
    if a["irr"] is not None:
        fig.add_vline(x=a["irr"], line_dash="dot", line_color="#2E8B57", annotation_text=tr("TIR", "IRR"))
    fig.update_layout(height=340, xaxis_title=tr("Taxa de desconto", "Discount rate"), xaxis_tickformat=".0%", yaxis_title=tr("VAL", "NPV"), margin=dict(l=10, r=10, t=10, b=10))
    c2.plotly_chart(fig, width="stretch")
    ui.interpret(I.finance_text(a, cur, be))

    st.markdown(tr("#### 4. Análise de sensibilidade (tornado ±20%)", "#### 4. Sensitivity analysis (tornado ±20%)"))
    dl = st.slider(tr("Variação", "Variation"), 0.05, 0.5, 0.2, 0.05, format="%.2f")
    sens = F.sensitivity(cfs, f, float(f.get("residual_value") or 0), dl)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=[s["driver"] for s in sens], x=[s["low"] - s["base"] for s in sens], base=[s["base"] for s in sens], orientation="h", name=f"−{int(dl * 100)}%", marker_color="#C0392B"))
    fig.add_trace(go.Bar(y=[s["driver"] for s in sens], x=[s["high"] - s["base"] for s in sens], base=[s["base"] for s in sens], orientation="h", name=f"+{int(dl * 100)}%", marker_color="#2E8B57"))
    fig.add_vline(x=a["npv"], line_color="#1F3B57")
    fig.update_layout(barmode="overlay", height=300, xaxis_title=tr("VAL", "NPV"), yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")
    top = sens[0]
    ui.interpret(tr(f"A variável mais crítica é **{top['driver']}**: com ±{int(dl * 100)}% o VAL varia entre {money(min(top['low'], top['high']), cur)} e {money(max(top['low'], top['high']), cur)}. "
                    + ("O VAL mantém-se positivo em todos os cenários testados." if min(min(s['low'], s['high']) for s in sens) > 0 else "⚠️ Em pelo menos um cenário o VAL fica negativo — o projeto é sensível aos pressupostos financeiros."),
                    f"The most critical driver is **{top['driver']}**: at ±{int(dl * 100)}% the NPV ranges from {money(min(top['low'], top['high']), cur)} to {money(max(top['low'], top['high']), cur)}. "
                    + ("NPV stays positive in every scenario tested." if min(min(s['low'], s['high']) for s in sens) > 0 else "⚠️ NPV turns negative in at least one scenario — the project is sensitive to the financial assumptions.")))
