"""2 · Formulation: logframe, logic model, theory of change, assumptions."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import analysis as AN
from core import ui
from core.i18n import opt_label, tr
from core.matrix import logframe_html
from core.model import expected_assumption_type, objective_level


def _obj_options(p, levels=("Impact", "Outcome", "Output")):
    return [str(o["code"]) for o in p["objectives"] if o.get("level") in levels]


def logframe():
    p = ui.P()
    ui.header("Matriz de Enquadramento Lógico (Logframe)", "Logical Framework Matrix (Logframe)", "logframe", "🧩")
    t1, t2, t3 = st.tabs([tr("🧩 Matriz", "🧩 Matrix"), tr("✏️ Lógica de intervenção (vertical)", "✏️ Intervention logic (vertical)"),
                          tr("📏 Indicadores e pressupostos", "📏 Indicators & assumptions")])
    with t1:
        st.markdown(logframe_html(p), unsafe_allow_html=True)
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
    ov = {"objective_code": st.column_config.SelectboxColumn(tr("Condiciona o objetivo", "Conditions objective"), options=_obj_options(p))}
    rows = ui.edit_table("assumptions", overrides=ov, key="full")
    if not rows:
        return
    st.markdown(tr("##### Avaliação pelo fluxograma PCM", "##### Assessment with the PCM flowchart"))
    out = []
    for h in rows:
        code, why = AN.assumption_decision(h)
        exp = expected_assumption_type(objective_level(p, h.get("objective_code")))
        risk = next((r["id"] for r in p["risks"] if str(r.get("assumption_id")) == str(h["id"])), "")
        out.append({"ID": h["id"], tr("Tipo", "Type"): opt_label("assumption_type", h["type"]),
                    tr("Tipo esperado", "Expected type"): opt_label("assumption_type", exp) if exp else "—",
                    tr("Decisão", "Decision"): {"drop": "⚪", "include": "🟡", "redesign": "🟠", "killer": "🔴"}[code] + " " + why,
                    tr("Prob. do risco (1-4)", "Risk likelihood (1-4)"): AN.assumption_risk_probability(h),
                    tr("Risco associado", "Linked risk"): risk or "—"})
    st.dataframe(pd.DataFrame(out), hide_index=True, width="stretch")
    st.caption(tr("A probabilidade do risco deriva da qualidade da evidência: quanto menor a evidência, maior a probabilidade (5 − qualidade).",
                  "Risk likelihood derives from evidence quality: the weaker the evidence, the higher the likelihood (5 − quality)."))
    c1, c2 = st.columns([2, 3])
    with c1:
        st.markdown(tr("##### Fluxograma (PCM, Fig. 30)", "##### Flowchart (PCM, Fig. 30)"))
        ui.graph(_flow_dot())
    with c2:
        st.markdown(tr("##### Converter pressupostos em riscos", "##### Turn assumptions into risks"))
        st.caption(tr("Cria no registo de riscos um risco (formulação negativa) por cada pressuposto a incluir que ainda não tenha risco associado.",
                      "Creates in the risk register one (negatively phrased) risk for each included assumption that has no linked risk yet."))
        if st.button(tr("⚙️ Gerar riscos a partir dos pressupostos", "⚙️ Generate risks from assumptions")):
            n = 0
            from core.model import empty_row, next_id
            for h in rows:
                code, _ = AN.assumption_decision(h)
                if code not in ("include", "redesign", "killer") or any(str(r.get("assumption_id")) == str(h["id"]) for r in p["risks"]):
                    continue
                r = empty_row("risks")
                r.update({"id": next_id(p["risks"], "R"), "type": {"Political": "Political", "Behavioural": "Project/programme delivery", "Operational": "Project/programme delivery"}[h["type"]],
                          "description": tr("Não se verifica: ", "Does not hold: ") + h["text"], "likelihood": AN.assumption_risk_probability(h),
                          "impact": {"Impact": 4, "Outcome": 4, "Output": 2}.get(objective_level(p, h.get("objective_code")), 3),
                          "assumption_id": h["id"], "level_affected": objective_level(p, h.get("objective_code")) or "Output",
                          "target_exposure": 4, "review": tr("Gerado a partir do pressuposto ", "Generated from assumption ") + h["id"]})
                p["risks"].append(r)
                n += 1
            ui.bump()
            st.success(tr(f"{n} risco(s) criados. Veja a página 'Riscos'.", f"{n} risk(s) created. See the 'Risks' page."))
        # evidence quality chart
        fig = go.Figure(go.Bar(x=[h["id"] for h in rows], y=[h.get("evidence_quality") or 0 for h in rows],
                               marker_color=["#27AE60" if (h.get("evidence_quality") or 0) >= 3 else "#E67E22" if (h.get("evidence_quality") or 0) == 2 else "#C0392B" for h in rows]))
        fig.update_layout(height=260, yaxis=dict(range=[0, 4.2], title=tr("Qualidade da evidência", "Evidence quality")), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")


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
