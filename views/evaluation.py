"""7 · Evaluation & Closure: evaluation design & M&E quality, efficiency/effectiveness/sustainability & ex-post risks,
closure (contracts, audits, ownership), lessons learned, best practices & dissemination."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import agent as AG
from core import monitor as M
from core import schedule as S
from core import ui
from core.fmt import money, num, pct
from core.i18n import opt_codes, opt_label, tr
from core.model import DAC_CRITERIA

SEL = st.column_config.SelectboxColumn


def eval_design():
    p = ui.P()
    ui.header("Desenho da avaliação e qualidade do M&A", "Evaluation design & M&E quality", "eval_design", "🔎")
    ed = p["eval_design"]
    t1, t2, t3 = st.tabs([tr("🎯 Finalidade e tipo", "🎯 Purpose & type"), tr("🔎 Matriz de avaliação (OCDE-CAD)", "🔎 Evaluation matrix (OECD-DAC)"),
                          tr("🧪 Qualidade do sistema de M&A", "🧪 M&E system quality")])
    with t1:
        c1, c2, c3, c4 = st.columns(4)
        new = dict(ed)
        new["type"] = c1.selectbox(tr("Tipo", "Type"), opt_codes("eval_type"), index=opt_codes("eval_type").index(ed["type"]) if ed.get("type") in opt_codes("eval_type") else 1,
                                   format_func=lambda c: opt_label("eval_type", c), key=f"ed_t_{st.session_state.dv}")
        new["timing"] = c2.selectbox(tr("Momento", "Timing"), opt_codes("eval_timing"), index=opt_codes("eval_timing").index(ed["timing"]) if ed.get("timing") in opt_codes("eval_timing") else 2,
                                     format_func=lambda c: opt_label("eval_timing", c), key=f"ed_m_{st.session_state.dv}")
        new["who"] = c3.selectbox(tr("Quem avalia", "Who evaluates"), opt_codes("eval_who"), index=opt_codes("eval_who").index(ed["who"]) if ed.get("who") in opt_codes("eval_who") else 1,
                                  format_func=lambda c: opt_label("eval_who", c), key=f"ed_w_{st.session_state.dv}")
        new["evaluator"] = c4.text_input(tr("Avaliador / equipa", "Evaluator / team"), ed.get("evaluator", ""), key=f"ed_e_{st.session_state.dv}")
        new["purposes"] = st.multiselect(tr("Finalidades", "Purposes"), opt_codes("eval_purpose"), default=[x for x in ed.get("purposes", []) if x in opt_codes("eval_purpose")],
                                         format_func=lambda c: opt_label("eval_purpose", c), key=f"ed_p_{st.session_state.dv}")
        new["scope"] = st.text_area(tr("Âmbito e perguntas-chave", "Scope & key questions"), ed.get("scope", ""), key=f"ed_s_{st.session_state.dv}")
        if new != ed:
            p["eval_design"] = new
            ui.mark_dirty()
        tips = {"Formative": tr("**Formativa** — durante a implementação, para melhorar: foco em operações e aprendizagem; usa dados de monitorização.",
                                "**Formative** — during implementation, to improve: focus on operations and learning; uses monitoring data."),
                "Summative": tr("**Sumativa** — no fim, para prestar contas e decidir (continuar, replicar, encerrar): foco em eficácia, impacto e sustentabilidade.",
                                "**Summative** — at the end, for accountability and decisions (continue, scale up, close): focus on effectiveness, impact and sustainability."),
                "Prospective": tr("**Prospetiva** — antes (ex-ante): avalia a probabilidade de sucesso e a avaliabilidade (dados, baseline, lógica).",
                                  "**Prospective** — before (ex-ante): assesses likelihood of success and evaluability (data, baseline, logic).")}
        txt = tips[new["type"]]
        if new["who"] == "Internal" and new["type"] == "Summative":
            txt += tr(" ⚠️ Uma avaliação sumativa interna tem menor credibilidade para prestação de contas — considere avaliação externa ou mista.",
                      " ⚠️ An internal summative evaluation has lower credibility for accountability — consider an external or mixed evaluation.")
        if "Learning" in new["purposes"] and not p["lessons"]:
            txt += tr(" Como a aprendizagem é uma finalidade, preveja o registo de lições (7 · Lições).", " As learning is a purpose, plan the lessons log (7 · Lessons).")
        ui.interpret(txt)
    with t2:
        st.caption(tr("Critérios OCDE-CAD: Relevance, Coherence, Effectiveness, Efficiency, Impact, Sustainability. Tipos de pergunta: descritiva (o quê?), normativa (face a um padrão/meta) e causa-efeito (o projeto causou?).",
                      "OECD-DAC criteria: Relevance, Coherence, Effectiveness, Efficiency, Impact, Sustainability. Question types: descriptive (what?), normative (against a standard/target) and cause-effect (did the project cause it?)."))
        ui.edit_table("evaluation", overrides={"criterion": SEL(ui.label("criterion"), options=DAC_CRITERIA)})
        rows = p["evaluation"]
        if rows:
            fig = go.Figure()
            for qt, col in (("Descriptive", "#9ECAE1"), ("Normative", "#2C7FB8"), ("Cause-effect", "#1F3B57")):
                fig.add_trace(go.Bar(x=DAC_CRITERIA, y=[sum(1 for r in rows if r["criterion"] == c and r.get("q_type") == qt) for c in DAC_CRITERIA], name=opt_label("eval_qtype", qt), marker_color=col))
            fig.update_layout(barmode="stack", height=280, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig, width="stretch")
        ui.interpret(M.evaluation_text(p))
        ui.ai_tables("Propor matriz de avaliação (6 critérios, perguntas tipificadas)", "Propose evaluation matrix (6 criteria, typed questions)", "evalq",
                     lambda: AG.gen_evaluation(p, st.session_state.get("ai_model")))
    with t3:
        if len(p["me_quality"]) < 10 and st.button(tr("➕ Criar a lista de verificação (10 elementos)", "➕ Create the checklist (10 items)")):
            have = {r["item"] for r in p["me_quality"]}
            p["me_quality"] += [{"item": c, "answer": "Partial", "evidence": ""} for c in opt_codes("me_item") if c not in have]
            ui.bump()
            st.rerun()
        ui.edit_table("me_quality", key="meq", num_rows="dynamic")
        q = M.me_quality_score(p)
        sh = M.me_budget_share(p)
        c = st.columns(2)
        c[0].metric(tr("Qualidade do M&A", "M&E quality"), pct(q, 0) if q is not None else "—")
        c[1].metric(tr("Peso do M&A no orçamento", "M&E share of budget"), pct(sh) if sh is not None else "—", help=tr("Atividades do tipo 'Apoio — M&A' / BAC. Referência 5–10%.", "Activities of type 'Support - M&E' / BAC. Reference 5–10%."))
        txt = ""
        if q is not None:
            weak = [opt_label("me_item", r["item"]) for r in p["me_quality"] if r.get("answer") == "No"]
            txt += tr(f"Qualidade do sistema de M&A: **{pct(q, 0)}**. ", f"M&E system quality: **{pct(q, 0)}**. ")
            if weak:
                txt += tr("A corrigir: " + "; ".join(weak) + ". ", "To fix: " + "; ".join(weak) + ". ")
        if sh is not None:
            txt += tr(f"O M&A representa {pct(sh)} do orçamento" + (" — abaixo da referência de 5–10%." if sh < 0.05 else " — dentro/acima da referência de 5–10%."),
                      f"M&E is {pct(sh)} of the budget" + (" — below the 5–10% reference." if sh < 0.05 else " — within/above the 5–10% reference."))
        ui.interpret(txt)


def results():
    p = ui.P()
    ui.header("Eficiência, eficácia, sustentabilidade e riscos ex-post", "Efficiency, effectiveness, sustainability & ex-post risks", "results_eval", "🏆")
    cur = p["meta"].get("currency", "EUR")
    sched = S.compute(p)
    sched = sched if sched.get("ok") else None
    ep = M.efficiency_panel(p, sched)
    t1, t2, t3, t4 = st.tabs([tr("⚙️ Eficiência", "⚙️ Efficiency"), tr("🎯 Eficácia", "🎯 Effectiveness"), tr("🌱 Sustentabilidade e ODS", "🌱 Sustainability & SDGs"),
                              tr("⚠️ Riscos ex-post e realismo", "⚠️ Ex-post risks & realism")])
    with t1:
        c = st.columns(5)
        c[0].metric("CPI", num(ep["CPI"], 2))
        c[1].metric("SPI", num(ep["SPI"], 2))
        c[2].metric(tr("Variação orçamental (EAC/BAC−1)", "Budget variance (EAC/BAC−1)"), pct(ep["budget_var"]) if ep["budget_var"] is not None else "—")
        c[3].metric(tr("Marcos a tempo", "Milestones on time"), pct(ep["ms_on_time"], 0) if ep["ms_on_time"] is not None else "—")
        c[4].metric(tr("Satisfação", "Satisfaction"), f"{ep['satisfaction']:.1f}/5" if ep["satisfaction"] else "—")
        if sched:
            e = S.evm(p, sched)
            tab = e["table"]
            tab = tab[tab["BAC"] > 0]
            fig = go.Figure(go.Scatter(x=tab["SPI"].astype(float), y=tab["CPI"].astype(float), mode="markers+text", text=tab["id"], textposition="top center",
                                       marker=dict(size=(tab["BAC"] / tab["BAC"].max() * 40 + 8), color="#2C7FB8", opacity=0.7)))
            fig.add_hline(y=1, line_dash="dot")
            fig.add_vline(x=1, line_dash="dot")
            fig.update_layout(height=380, xaxis_title="SPI", yaxis_title="CPI", margin=dict(l=10, r=10, t=10, b=10),
                              annotations=[dict(x=1.15, y=1.15, text=tr("adiantado e abaixo do custo", "ahead & under budget"), showarrow=False, font=dict(color="#2E8B57")),
                                           dict(x=0.85, y=0.85, text=tr("atrasado e acima do custo", "behind & over budget"), showarrow=False, font=dict(color="#C0392B"))])
            st.plotly_chart(fig, width="stretch")
        ui.interpret(M.efficiency_text(ep))
    with t2:
        ov = M.indicators_overview(p)
        lv = {"Impact": 0, "Outcome": 1, "Output": 2}
        ov = sorted([o for o in ov if o["achievement"] is not None], key=lambda o: (lv.get(o["level"], 3), o["id"]))
        if ov:
            fig = go.Figure(go.Bar(y=[f"{o['id']} ({opt_label('level', o['level']) if o['level'] else '—'})" for o in ov], x=[o["achievement"] for o in ov], orientation="h",
                                   marker_color=[{"on_track": "#2E8B57", "watch": "#E3B23C", "off_track": "#C0392B"}.get(o["status"], "#999") for o in ov],
                                   text=[pct(o["achievement"], 0) for o in ov], textposition="outside"))
            fig.add_vline(x=1, line_dash="dot", annotation_text=tr("Meta", "Target"))
            fig.update_layout(height=80 + 32 * len(ov), xaxis=dict(tickformat=".0%"), yaxis=dict(autorange="reversed"), margin=dict(l=10, r=40, t=10, b=10))
            st.plotly_chart(fig, width="stretch")
            oc = [o for o in ov if o["level"] == "Outcome"]
            if oc:
                avg = sum(min(o["achievement"], 1.2) for o in oc) / len(oc)
                ui.interpret(tr(f"Eficácia (outcomes): realização média de **{pct(avg, 0)}** da distância baseline→meta em {len(oc)} indicadores de outcome. "
                                "Para atribuir a mudança ao projeto (impacto), use perguntas de causa-efeito e um contrafactual (grupo de comparação, diferenças-em-diferenças, contribuição).",
                                f"Effectiveness (outcomes): average achievement of **{pct(avg, 0)}** of the baseline→target distance across {len(oc)} outcome indicators. "
                                "To attribute change to the project (impact), use cause-effect questions and a counterfactual (comparison group, difference-in-differences, contribution analysis)."))
        else:
            st.info(tr("Registe medições dos indicadores (6 · Monitorização) para avaliar a eficácia.", "Record indicator measurements (6 · Monitoring) to assess effectiveness."))
    with t3:
        ui.edit_table("sustainability", key="sus")
        sc = M.sustainability_scores(p)
        if sc:
            ks = [k for k in opt_codes("pillar") if k in sc]
            fig = go.Figure(go.Scatterpolar(r=[sc[k] for k in ks] + [sc[ks[0]]], theta=[opt_label("pillar", k) for k in ks] + [opt_label("pillar", ks[0])], fill="toself", line=dict(color="#2E8B57")))
            fig.update_layout(height=360, polar=dict(radialaxis=dict(range=[0, 5])), margin=dict(l=40, r=40, t=20, b=20))
            st.plotly_chart(fig, width="stretch")
        ui.interpret(M.sustainability_text(p))
    with t4:
        h = M.risk_history(p)
        if h:
            mat = [x for x in h if x["materialised"]]
            c = st.columns(4)
            c[0].metric(tr("Exposição inicial", "Initial exposure"), sum(x["initial"] for x in h))
            c[1].metric(tr("Exposição final", "Final exposure"), sum(x["latest"] for x in h), sum(x["latest"] for x in h) - sum(x["initial"] for x in h), delta_color="inverse")
            c[2].metric(tr("Riscos materializados", "Materialised risks"), len(mat))
            c[3].metric(tr("Custo dos riscos vs contingência", "Risk cost vs contingency"), money(sum(x["cost_impact"] for x in h), cur), money(-sum(x["contingency"] for x in h), cur), delta_color="off")
            st.dataframe(pd.DataFrame([{"ID": x["id"], tr("Inicial", "Initial"): x["initial"], tr("Final", "Final"): x["latest"], tr("Materializou?", "Materialised?"): "✅" if x["materialised"] else "—",
                                        tr("Custo", "Cost"): x["cost_impact"], tr("Contingência alocada", "Allocated contingency"): x["contingency"],
                                        tr("Mitigação compensou?", "Mitigation paid off?"): ("✅" if x["latest"] < x["initial"] else "—") if not x["materialised"] else ("⚠️" if x["cost_impact"] > x["contingency"] else "✅")}
                                       for x in h]), hide_index=True, width="stretch")
        if sched and p.get("baseline"):
            e = S.evm(p, sched)
            b = p["baseline"]
            bac0 = float(b.get("bac") or e["BAC"])
            dur0 = float(b.get("duration") or sched["cpm"]["duration"])
            spi = e["SPI"] if e["SPI"] == e["SPI"] and e["SPI"] else 1
            dur_fc = sched["cpm"]["duration"] / spi
            st.markdown(tr("##### Realismo do planeamento (ex-post)", "##### Planning realism (ex-post)"))
            c = st.columns(2)
            c[0].metric(tr("Custo: baseline → EAC", "Cost: baseline → EAC"), money(e["EAC"], cur), pct(e["EAC"] / bac0 - 1) if bac0 else None, delta_color="inverse")
            c[1].metric(tr("Duração: baseline → previsão (÷SPI)", "Duration: baseline → forecast (÷SPI)"), f"{num(dur_fc, 1)} {sched['unit']}", pct(dur_fc / dur0 - 1) if dur0 else None, delta_color="inverse")
            ui.interpret(tr(f"O planeamento revelou-se {'realista' if abs(e['EAC'] / bac0 - 1) < 0.05 and abs(dur_fc / dur0 - 1) < 0.05 else 'otimista' if e['EAC'] > bac0 or dur_fc > dur0 else 'conservador'}: "
                            "desvios superiores a 5% devem originar uma lição (categoria 'Desenho e substância' ou 'Financeiro').",
                            f"Planning proved {'realistic' if abs(e['EAC'] / bac0 - 1) < 0.05 and abs(dur_fc / dur0 - 1) < 0.05 else 'optimistic' if e['EAC'] > bac0 or dur_fc > dur0 else 'conservative'}: "
                            "deviations above 5% should give rise to a lesson ('Design and substance' or 'Financial' category)."))


def closure():
    p = ui.P()
    ui.header("Encerramento: contratos, auditorias e propriedade dos resultados", "Closure: contracts, audits & ownership of results", "closure", "🏁")
    t1, t2, t3 = st.tabs([tr("📜 Contratos", "📜 Contracts"), tr("🔍 Auditorias", "🔍 Audits"), tr("©️ Propriedade dos resultados", "©️ Ownership of results")])
    with t1:
        aw = [q for q in p["procurement"] if q.get("awarded_to")]
        if aw:
            st.dataframe(pd.DataFrame([{"ID": q["id"], "Item": q["item"], tr("Adjudicado a", "Awarded to"): q["awarded_to"], tr("Valor", "Value"): q.get("contract_value"),
                                        tr("Encerramento", "Closure"): M.closure_progress(p, q["id"])[0] / 15} for q in aw]), hide_index=True, width="stretch",
                         column_config={tr("Encerramento", "Closure"): st.column_config.ProgressColumn(tr("Encerramento", "Closure"), min_value=0, max_value=1, format="percent")})
            st.caption(tr("Detalhe dos 15 passos em 6 · Concursos e contratos.", "Detail of the 15 steps in 6 · Tenders & contracts."))
        else:
            st.info(tr("Sem contratos adjudicados.", "No contracts awarded."))
    with t2:
        ui.edit_table("audits", key="au")
    with t3:
        ui.edit_table("ownership", key="ow")
    ui.interpret(M.closure_text(p))


def lessons():
    p = ui.P()
    ui.header("Lições aprendidas, boas práticas e disseminação", "Lessons learned, best practices & dissemination", "lessons", "💡")
    t1, t2, t3 = st.tabs([tr("💡 Lições aprendidas", "💡 Lessons learned"), tr("⭐ Boas práticas", "⭐ Best practices"), tr("📢 Disseminação", "📢 Dissemination")])
    with t1:
        ui.edit_table("lessons", key="ll")
        if p["lessons"]:
            cnt = {opt_label("lesson_cat", c): sum(1 for r in p["lessons"] if r.get("category") == c) for c in opt_codes("lesson_cat")}
            fig = go.Figure(go.Barpolar(r=list(cnt.values()), theta=list(cnt), marker_color="#2C7FB8"))
            fig.update_layout(height=360, margin=dict(l=40, r=40, t=20, b=20))
            st.plotly_chart(fig, width="stretch")
        ui.interpret(M.lessons_text(p))
        c1, c2 = st.columns(2)
        with c1:
            ui.ai_tables("Propor lições e boas práticas", "Propose lessons and best practices", "lessons_t", lambda: AG.gen_lessons(p, st.session_state.get("ai_model")))
        with c2:
            ui.ai_text("Síntese de lições (8 categorias)", "Lessons synthesis (8 categories)", "lessons_s", lambda: AG.lessons_synthesis(p, st.session_state.get("ai_model")))
    with t2:
        ui.edit_table("best_practices", key="bp")
        st.caption(tr("Uma boa prática é eficaz (resultados comprovados), eficiente, sustentável, replicável e validada pelos stakeholders.",
                      "A best practice is effective (proven results), efficient, sustainable, replicable and validated by stakeholders."))
    with t3:
        ui.edit_table("dissemination", key="ds")
        rows = [r for r in p["dissemination"] if r.get("reach_target")]
        if rows:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=[r["id"] for r in rows], y=[r["reach_target"] for r in rows], name=tr("Meta", "Target"), marker_color="#BBBBBB"))
            fig.add_trace(go.Bar(x=[r["id"] for r in rows], y=[r.get("reach_actual") or 0 for r in rows], name=tr("Real", "Actual"), marker_color="#2C7FB8"))
            fig.update_layout(barmode="group", height=300, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig, width="stretch")
            done = [r for r in rows if r.get("reach_actual") is not None]
            ui.interpret(tr(f"{len(done)} de {len(rows)} ações de disseminação com alcance medido" + (f"; alcance médio {pct(sum(r['reach_actual'] / r['reach_target'] for r in done) / len(done), 0)} da meta." if done else "."),
                            f"{len(done)} of {len(rows)} dissemination actions with measured reach" + (f"; average reach {pct(sum(r['reach_actual'] / r['reach_target'] for r in done) / len(done), 0)} of target." if done else ".")))
