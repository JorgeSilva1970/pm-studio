"""2 · Formulation: logframe, logic model, theory of change, assumptions."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import analysis as AN
from core import ui
from core.i18n import opt_codes, opt_label, tr
from core.matrix import terminology_legend, logframe_classic_html, logframe_html
from core.model import expected_assumption_type, objective_level


def _obj_options(p, levels=("Impact", "Outcome", "Output")):
    return [str(o["code"]) for o in p["objectives"] if o.get("level") in levels]


def logframe():
    p = ui.P()
    ui.header("Matriz de Enquadramento Lógico (Logframe)", "Logical Framework Matrix (Logframe)", "logframe", "🧩")
    t1, t2, t3 = st.tabs([tr("🧩 Matriz", "🧩 Matrix"), tr("✏️ Lógica de intervenção (vertical)", "✏️ Intervention logic (vertical)"),
                          tr("📏 Indicadores e pressupostos", "📏 Indicators & assumptions")])
    with t1:
        lf = p.setdefault("logframe", {"preconditions": "", "terminology": "pcm"})
        c1, c2 = st.columns(2)
        view = c1.segmented_control(tr("Vista", "View"), ["classic", "extended"], default="classic", key="lf_view",
                                    format_func=lambda v: tr("Clássica 4×4 (PCM)", "Classic 4×4 (PCM)") if v == "classic" else tr("Alargada (UE: baseline, meta, critério)", "Extended (EU: baseline, target, criterion)"))
        terms = c2.segmented_control(tr("Terminologia", "Terminology"), ["pcm", "results"], default=lf.get("terminology", "pcm"), key="lf_terms",
                                     format_func=lambda v: tr("Objetivo global / específico / resultados", "Overall / specific objective / results") if v == "pcm" else "Impact / Outcome / Output")
        if terms and terms != lf.get("terminology"):
            lf["terminology"] = terms
            from core.i18n import set_terminology
            set_terminology(terms)
            ui.mark_dirty()
            st.rerun()
        with st.expander(tr("📘 Correspondência entre terminologias (o conteúdo não muda, só os nomes)", "📘 Terminology correspondence (content does not change, only the names)")):
            st.markdown(terminology_legend())
        if (view or "classic") == "classic":
            _lf = logframe_classic_html(p, lf.get("terminology", "pcm"))
            st.markdown(_lf, unsafe_allow_html=True)
            ui.export_buttons_html(_lf, tr("Quadro logico 4x4", "Logframe 4x4"))
            st.caption(tr("Formato clássico do PCM (4 colunas). Na linha das atividades, a 2.ª e a 3.ª colunas mostram os **meios** e os **custos** (do orçamento). "
                          "Os indicadores mostram baseline → meta, mantendo a formulação neutra do indicador.",
                          "Classic PCM format (4 columns). In the activities row, the 2nd and 3rd columns show **means** and **costs** (from the budget). "
                          "Indicators show baseline → target, keeping the indicator wording neutral."))
            pre = st.text_area(tr("Pré-condições (uma por linha) — condições a cumprir antes de as atividades começarem", "Pre-conditions (one per line) — conditions to be met before activities start"),
                               lf.get("preconditions", ""), height=90, key=f"lf_pre_{st.session_state.dv}",
                               placeholder=tr("Ex.: Acordo de financiamento assinado\nEquipa de projeto nomeada", "E.g.: Financing agreement signed\nProject team appointed"))
            if pre != lf.get("preconditions", ""):
                lf["preconditions"] = pre
                ui.mark_dirty()
                st.rerun()
        else:
            _lf = logframe_html(p, terminology=lf.get("terminology", "pcm"))
            st.markdown(_lf, unsafe_allow_html=True)
            ui.export_buttons_html(_lf, tr("Quadro logico alargado", "Logframe extended"), width=1700)
        st.caption(tr("Leitura diagonal: Atividades + pressupostos operacionais → Outputs; Outputs + comportamentais → Outcomes; Outcomes + políticos → Impacto. "
                      "Os pressupostos aparecem na linha imediatamente abaixo do nível que condicionam.",
                      "Diagonal reading: Activities + operational assumptions → Outputs; Outputs + behavioural → Outcomes; Outcomes + political → Impact. "
                      "Assumptions appear on the row immediately below the level they condition."))
    with t2:
        st.caption(tr("Códigos sugeridos: IMP (impacto), OC1, OC2 (outcomes), 1.1, 1.2, 2.1 (outputs). 'Leva a' = código do nível superior.",
                      "Suggested codes: IMP (impact), OC1, OC2 (outcomes), 1.1, 1.2, 2.1 (outputs). 'Leads to' = upper-level code."))
        ov = {"level": st.column_config.SelectboxColumn(ui.label("level"), options=["Impact", "Outcome", "Output"], format_func=lambda c: opt_label("level", c)),
              "parent": st.column_config.SelectboxColumn(ui.label("parent"), options=[""] + _obj_options(p, ("Impact", "Outcome")))}
        ui.edit_table("objectives", columns=["code", "level", "text", "parent", "source_problem"], overrides=ov)
        if p["objectives"]:
            ui.graph(AN.results_chain_dot({**p, "activities": []}, show_assumptions=False))
    with t3:
        st.markdown(tr("##### Indicadores (lógica horizontal)", "##### Indicators (horizontal logic)"))
        ov = {"objective_code": st.column_config.SelectboxColumn(ui.label("objective_code"), options=_obj_options(p, ("Impact", "Outcome", "Output", "Input")))}
        ui.edit_table("indicators", columns=["id", "objective_code", "indicator", "unit", "baseline", "baseline_year", "target", "target_year", "source"], key="lf", overrides=ov)
        st.markdown(tr("##### Pressupostos (lógica diagonal)", "##### Assumptions (diagonal logic)"))
        ov = {"objective_code": st.column_config.SelectboxColumn(tr("Condiciona o objetivo", "Conditions objective"), options=_obj_options(p))}
        ui.edit_table("assumptions", columns=["id", "type", "objective_code", "text", "evidence"], key="lf", overrides=ov)


def logic_model():
    p = ui.P()
    ui.header("Modelo lógico (cadeia de resultados)", "Logic model (results chain)", "logic_model", "🔗")
    show = st.toggle(tr("Mostrar pressupostos", "Show assumptions"), value=True)
    ui.graph(AN.results_chain_dot(p, show_assumptions=show))
    st.markdown(tr("##### Níveis de controlo e critérios de avaliação", "##### Levels of control and evaluation criteria"))
    rows = [(tr("Inputs (4 Ms)", "Inputs (4 Ms)"), tr("Controlo total", "Full control"), tr("Eficiência", "Efficiency"), tr("Indicadores de input", "Input indicators")),
            (tr("Atividades", "Activities"), tr("Controlo total", "Full control"), tr("Eficiência", "Efficiency"), tr("(não se medem por indicadores)", "(not measured by indicators)")),
            ("Outputs", tr("Controlo total", "Full control"), tr("Eficiência", "Efficiency"), tr("Indicadores de output", "Output indicators")),
            ("Outcomes", tr("Influência direta", "Direct influence"), tr("Eficácia", "Effectiveness"), tr("Indicadores de resultado", "Result indicators")),
            (tr("Impacto", "Impact"), tr("Influência indireta", "Indirect influence"), tr("Impacto e Sustentabilidade", "Impact & Sustainability"), tr("Indicadores de impacto", "Impact indicators"))]
    st.dataframe(pd.DataFrame(rows, columns=[tr("Nível", "Level"), tr("Responsabilidade do gestor", "Manager's responsibility"), tr("Critério", "Criterion"), tr("Indicadores", "Indicators")]),
                 hide_index=True, width="stretch")
    acts = p["activities"]
    prod = [a for a in acts if a.get("type") == "Production"]
    sup = [a for a in acts if str(a.get("type", "")).startswith("Support")]
    outs = [o for o in p["objectives"] if o["level"] == "Output"]
    ui.interpret(tr(f"Cadeia com **{len(outs)} outputs**, **{len(prod)} atividades de produção** e **{len(sup)} de apoio**. "
                    "Cada output deve ter pelo menos uma atividade de produção; as atividades de apoio (comunicação, M&A, eventos, gestão) garantem a qualidade da gestão.",
                    f"Chain with **{len(outs)} outputs**, **{len(prod)} production activities** and **{len(sup)} support activities**. "
                    "Each output needs at least one production activity; support activities (communication, M&E, events, management) ensure management quality."))


def toc():
    p = ui.P()
    ui.header("Teoria da Mudança (Theory of Change)", "Theory of Change", "toc", "🔄")
    t = p["toc"]
    c1, c2 = st.columns(2)
    fields = [("vision", "Visão de sucesso (mudança desejada)", "Vision of success (desired change)"),
              ("context", "Contexto e análise de sistema", "Context & system analysis"),
              ("actors", "Atores e relações de poder", "Actors & power relations"),
              ("strategic_choices", "Escolhas estratégicas (o que faremos / não faremos)", "Strategic choices (what we will / won't do)"),
              ("learning", "Perguntas de aprendizagem e evidência a recolher", "Learning questions & evidence to collect")]
    for i, (k, pt, en) in enumerate(fields):
        col = c1 if i % 2 == 0 else c2
        v = col.text_area(tr(pt, en), t.get(k, ""), height=110, key=f"toc_{k}_{st.session_state.dv}")
        if v != t.get(k, ""):
            t[k] = v
            ui.mark_dirty()
    st.markdown(tr("##### Pré-condições adicionais (caminhos de mudança)", "##### Additional preconditions (pathways of change)"))
    st.caption(tr("Os outcomes, outputs e pressupostos do logframe já entram no diagrama; acrescente pré-condições que não são outputs do projeto.",
                  "Logframe outcomes, outputs and assumptions are already in the diagram; add preconditions that are not project outputs."))
    opts = [""] + [str(o["code"]) for o in p["objectives"]] + [str(c["id"]) for c in p["preconditions"]]
    ui.edit_table("preconditions", overrides={"leads_to": st.column_config.SelectboxColumn(ui.label("leads_to"), options=opts)})
    ui.graph(AN.toc_dot(p))
    n_asm = len([h for h in p["assumptions"] if h.get("objective_code")])
    ui.interpret(tr(f"A teoria assenta em **{len(p['objectives'])} resultados encadeados**, **{len(p['preconditions'])} pré-condições externas** e **{n_asm} pressupostos explícitos**. "
                    "Teste cada seta perguntando 'porque é que isto leva àquilo?' e 'que evidência temos?'. Reveja a ToC nos momentos de reporte.",
                    f"The theory rests on **{len(p['objectives'])} linked results**, **{len(p['preconditions'])} external preconditions** and **{n_asm} explicit assumptions**. "
                    "Test every arrow by asking 'why does this lead to that?' and 'what evidence do we have?'. Revisit the ToC at reporting points."))


def assumptions():
    p = ui.P()
    ui.header("Pressupostos baseados em evidência", "Evidence-based assumptions", "assumptions", "🧱")
    st.markdown(tr("**OUTPUTS = ATIVIDADES + PRESSUPOSTOS OPERACIONAIS · OUTCOMES = OUTPUTS + COMPORTAMENTAIS · IMPACTOS = OUTCOMES + POLÍTICOS**",
                   "**OUTPUTS = ACTIVITIES + OPERATIONAL ASSUMPTIONS · OUTCOMES = OUTPUTS + BEHAVIOURAL · IMPACTS = OUTCOMES + POLITICAL**"))
    ov = {"objective_code": st.column_config.SelectboxColumn(tr("Condiciona o objetivo", "Conditions objective"), options=_obj_options(p)),
          "redesign_possible": st.column_config.CheckboxColumn(ui.label("redesign_possible"),
                                                               help=tr("Só conta quando o pressuposto é importante e 'Vai verificar-se?' = Improvável (3.ª pergunta do fluxograma PCM). Nos outros casos é ignorado (n/a).",
                                                                       "Only counts when the assumption is important and 'Will it hold?' = Unlikely (3rd question of the PCM flowchart). Otherwise it is ignored (n/a).")),
          "holds": st.column_config.SelectboxColumn(ui.label("holds"), options=opt_codes("holds"), format_func=lambda c: opt_label("holds", c),
                                                    help=tr("Quase de certeza → não incluir · Possivelmente → incluir e monitorizar · Improvável → redesenhar ou killer.",
                                                            "Almost certainly → do not include · Possibly → include and monitor · Unlikely → redesign or killer.")),
          "evidence_quality": st.column_config.NumberColumn(ui.label("evidence_quality"), min_value=1, max_value=4, step=1, format="%d",
                                                               help=tr("1 = muito fraca … 4 = muito forte. Probabilidade do risco = 5 − qualidade.", "1 = very weak … 4 = very strong. Risk likelihood = 5 − quality."))}
    rows = ui.edit_table("assumptions", overrides=ov, key="full")
    if not rows:
        return
    st.markdown(tr("##### Avaliação pelo fluxograma PCM", "##### Assessment with the PCM flowchart"))
    ICON = {"drop": "⚪", "include": "🟡", "redesign": "🟠", "killer": "🔴"}
    out = []
    for h in rows:
        code, why = AN.assumption_decision(h)
        exp = expected_assumption_type(objective_level(p, h.get("objective_code")))
        risk = next((r["id"] for r in p["risks"] if str(r.get("assumption_id")) == str(h["id"])), "")
        out.append({"ID": h["id"], tr("Tipo", "Type"): opt_label("assumption_type", h["type"]),
                    tr("Tipo esperado", "Expected type"): opt_label("assumption_type", exp) if exp else "—",
                    tr("Decisão", "Decision"): ICON[code] + " " + why,
                    tr("Redesenho?", "Redesign?"): (tr("Sim", "Yes") if h.get("redesign_possible") else tr("Não", "No")) if AN.redesign_applies(h) else "n/a",
                    tr("Prob. do risco (1-4)", "Risk likelihood (1-4)"): AN.assumption_risk_probability(h),
                    tr("Risco associado", "Linked risk"): risk or "—"})
    st.dataframe(pd.DataFrame(out), hide_index=True, width="stretch")
    st.caption(tr("A probabilidade do risco deriva da qualidade da evidência: quanto menor a evidência, maior a probabilidade (5 − qualidade). "
                  "'Redesenho?' = n/a quando o pressuposto não é Improvável (a 3.ª pergunta do fluxograma não se coloca).",
                  "Risk likelihood derives from evidence quality: the weaker the evidence, the higher the likelihood (5 − quality). "
                  "'Redesign?' = n/a when the assumption is not Unlikely (the 3rd flowchart question does not arise)."))
    ignored = [h["id"] for h in rows if h.get("redesign_possible") and not AN.redesign_applies(h)]
    if ignored:
        st.info(tr(f"'Redesenho possível?' marcado em {', '.join(ignored)}, mas não tem efeito: só se aplica quando 'Vai verificar-se?' = Improvável.",
                   f"'Redesign possible?' ticked for {', '.join(ignored)}, but it has no effect: it only applies when 'Will it hold?' = Unlikely."))
    with st.expander(tr("🧮 Como se decide? (caminho no fluxograma para cada pressuposto)", "🧮 How is it decided? (flowchart path for each assumption)")):
        st.markdown("\n".join(f"- **{h['id']}**: {AN.assumption_path(h)}" for h in rows))
    c1, c2 = st.columns([2, 3])
    with c1:
        st.markdown(tr("##### Fluxograma (PCM, Fig. 30)", "##### Flowchart (PCM, Fig. 30)"))
        ui.graph(_flow_dot(), title=tr("Fluxograma de pressupostos PCM", "PCM assumptions flowchart"))
    with c2:
        st.markdown(tr("##### Converter pressupostos em riscos", "##### Turn assumptions into risks"))
        st.caption(tr("Cria no registo de riscos um risco (formulação negativa) por cada pressuposto incluído, a redesenhar ou killer que ainda não tenha risco associado. "
                      "Probabilidade = 5 − qualidade da evidência; impacto adverso = linha do logframe onde está o pressuposto (Operacional → Atividades, "
                      "Comportamental → Outputs, Político → Outcome); impacto sugerido pelo nível e pelo caminho crítico.",
                      "Creates in the risk register one (negatively phrased) risk for each included, redesign or killer assumption that has no linked risk yet. "
                      "Likelihood = 5 − evidence quality; adverse impact = logframe row where the assumption sits (Operational → Activities, "
                      "Behavioural → Outputs, Political → Outcome); impact suggested by the level and the critical path."))
        if st.button(tr("⚙️ Gerar riscos a partir dos pressupostos", "⚙️ Generate risks from assumptions")):
            from core import riskmgmt as RM
            from core.model import adverse_level, empty_row, next_id
            created, skipped = [], []
            tf = RM.floats(p)
            for h in rows:
                code, _ = AN.assumption_decision(h)
                linked = next((r["id"] for r in p["risks"] if str(r.get("assumption_id")) == str(h["id"])), None)
                if code == "drop":
                    skipped.append(tr(f"{h['id']} → não incluído no logframe (sem risco)", f"{h['id']} → not included in the logframe (no risk)"))
                    continue
                if linked:
                    skipped.append(tr(f"{h['id']} → já tem {linked}", f"{h['id']} → already has {linked}"))
                    continue
                r = empty_row("risks")
                r.update({"id": next_id(p["risks"], "R"), "type": {"Political": "Political", "Behavioural": "Project/programme delivery", "Operational": "Project/programme delivery"}[h["type"]],
                          "description": tr("Não se verifica: ", "Does not hold: ") + h["text"], "likelihood": AN.assumption_risk_probability(h),
                          "assumption_id": h["id"], "level_affected": adverse_level(p, h),
                          "target_exposure": 4, "review": tr("Gerado a partir do pressuposto ", "Generated from assumption ") + h["id"]})
                r["impact"] = RM.suggested_impact(p, r, tf)[0]
                p["risks"].append(r)
                created.append(f"{h['id']} → {r['id']} (L {r['likelihood']} × I {r['impact']})")
            ui.bump()
            st.session_state["_asm_msg"] = (created, skipped)
            st.rerun()
        msg = st.session_state.pop("_asm_msg", None)
        if msg:
            created, skipped = msg
            if created:
                st.success(tr(f"{len(created)} risco(s) criado(s): ", f"{len(created)} risk(s) created: ") + "; ".join(created))
            else:
                st.warning(tr("Nenhum risco novo criado.", "No new risk created."))
            if skipped:
                st.caption(tr("Ignorados: ", "Skipped: ") + "; ".join(skipped))
            st.caption(tr("➡️ Os riscos criados estão na página **3 · Riscos** (exposição, estratégia, contingência).", "➡️ The created risks are on the **3 · Risks** page (exposure, strategy, contingency)."))
        # decision chart: height = evidence quality, colour = PCM decision, marker = risk likelihood, label = linked risk
        COL = {"drop": "#BDC3C7", "include": "#F1C40F", "redesign": "#E67E22", "killer": "#C0392B"}
        NAME = {"drop": tr("Não incluir", "Do not include"), "include": tr("Incluir e monitorizar", "Include and monitor"), "redesign": tr("Redesenhar", "Redesign"), "killer": tr("Killer", "Killer")}
        fig = go.Figure()
        for code in ("drop", "include", "redesign", "killer"):
            hs = [h for h in rows if AN.assumption_decision(h)[0] == code]
            if hs:
                fig.add_trace(go.Bar(x=[h["id"] for h in hs], y=[h.get("evidence_quality") or 0 for h in hs], name=NAME[code], marker_color=COL[code],
                                     text=[next((r["id"] for r in p["risks"] if str(r.get("assumption_id")) == str(h["id"])), "") for h in hs], textposition="outside"))
        fig.add_trace(go.Scatter(x=[h["id"] for h in rows], y=[AN.assumption_risk_probability(h) for h in rows], mode="markers+lines", name=tr("Prob. do risco (5 − qualidade)", "Risk likelihood (5 − quality)"),
                                 marker=dict(symbol="diamond", size=11, color="#1F3B57"), line=dict(dash="dot", color="#1F3B57")))
        fig.update_layout(height=330, barmode="group", xaxis=dict(categoryorder="array", categoryarray=[h["id"] for h in rows]),
                          yaxis=dict(range=[0, 4.6], title=tr("Qualidade da evidência / probabilidade (1–4)", "Evidence quality / likelihood (1–4)")),
                          title=tr("Decisão PCM por pressuposto (etiqueta = risco associado)", "PCM decision per assumption (label = linked risk)"),
                          legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, width="stretch")
        st.caption(tr("Altura = qualidade da evidência; cor = decisão do fluxograma; losango = probabilidade do risco; etiqueta = risco associado. "
                      "Mudar 'Vai verificar-se?', 'Redesenho possível?' ou gerar riscos atualiza o gráfico.",
                      "Height = evidence quality; colour = flowchart decision; diamond = risk likelihood; label = linked risk. "
                      "Changing 'Will it hold?', 'Redesign possible?' or generating risks updates the chart."))


def _flow_dot():
    return f"""digraph G {{ rankdir=TB; node [fontname="Helvetica", fontsize=10, style="rounded,filled", shape=box, fillcolor="#EEF3F5"]; edge [fontname="Helvetica", fontsize=9];
 q1 [label="{tr('O pressuposto é importante?', 'Is the assumption important?')}", shape=diamond, fillcolor="#DCEFF6"];
 q2 [label="{tr('Vai verificar-se?', 'Will it hold true?')}", shape=diamond, fillcolor="#DCEFF6"];
 q3 [label="{tr('É possível redesenhar o projeto\\npara influenciar o fator externo?', 'Is it possible to redesign the project\\nto influence the external factor?')}", shape=diamond, fillcolor="#DCEFF6"];
 n1 [label="{tr('Não incluir no logframe', 'Do not include in the logframe')}"]; n2 [label="{tr('Incluir como pressuposto', 'Include as an assumption')}", fillcolor="#FFF4C2"];
 n3 [label="{tr('Redesenhar: acrescentar atividades/\\nresultados ou reformular o objetivo', 'Redesign: add activities/results\\nor reformulate the purpose')}", fillcolor="#FDE3C8"];
 n4 [label="{tr('Pressuposto killer:\\no projeto não é viável', 'Killer assumption:\\nthe project is not feasible')}", fillcolor="#F5B7B1"];
 q1 -> n1 [label="{tr('Não', 'No')}"]; q1 -> q2 [label="{tr('Sim', 'Yes')}"];
 q2 -> n1 [label="{tr('Quase de certeza', 'Almost certainly')}"]; q2 -> n2 [label="{tr('Possivelmente', 'Possibly')}"]; q2 -> q3 [label="{tr('Improvável', 'Unlikely')}"];
 q3 -> n3 [label="{tr('Sim', 'Yes')}"]; q3 -> n4 [label="{tr('Não', 'No')}"]; }}"""
