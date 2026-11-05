"""Home: project management (database), demos, import/export, project settings and dashboard."""
import json
from datetime import date

import pandas as pd
import streamlit as st

from core import db, ui
from core import finance as F
from core import interpret as I
from core import schedule as S
from core.analysis import exposure, smart_score
from core.demos import DEMOS, build_demo
from core.fmt import d, money, num, pct, unit_label
from core.i18n import opt_codes, opt_label, tr, trd
from core.model import new_project, normalize


def render():
    p = ui.P()
    st.title(tr("🧭 PM Studio — Gestão do Ciclo de Projeto", "🧭 PM Studio — Project Cycle Management"))
    st.caption(tr("Logic Models · Ferramentas analíticas · Planeamento (PERT/CPM, Gantt, custos, riscos) · Finanças (VAL, TIR, MIRR, WACC) · M&A (SMART, EVM) · Agente IA",
                  "Logic Models · Analytical tools · Planning (PERT/CPM, Gantt, costs, risks) · Finance (NPV, IRR, MIRR, WACC) · M&E (SMART, EVM) · AI agent"))
    ui.help_panel("home")

    t1, t2, t3, t4 = st.tabs([tr("📊 Painel do projeto", "📊 Project dashboard"), tr("📂 Projetos", "📂 Projects"),
                              tr("⚙️ Dados do projeto", "⚙️ Project settings"), tr("⬆️⬇️ Importar / exportar", "⬆️⬇️ Import / export")])
    with t1:
        dashboard(p)
    with t2:
        projects_tab()
    with t3:
        settings(p)
    with t4:
        import_export(p)


def dashboard(p):
    m = p["meta"]
    cur = m.get("currency", "EUR")
    sched = S.compute(p)
    st.subheader(m.get("name", ""))
    if m.get("description"):
        st.write(m["description"])
    c = st.columns(6)
    if sched.get("ok"):
        c[0].metric(tr("Duração (CPM/PERT)", "Duration (CPM/PERT)"), f"{num(sched['cpm']['duration'], 1)} {unit_label(sched['unit'])}")
        c[1].metric(tr("Fim previsto", "Planned finish"), d(sched["finish"]))
        c[2].metric(tr("Orçamento (BAC)", "Budget (BAC)"), money(sched["bac"], cur))
        e = S.evm(p, sched)
        c[3].metric("CPI / SPI", f"{num(e['CPI'], 2)} / {num(e['SPI'], 2)}")
    else:
        c[0].metric(tr("Duração", "Duration"), "—")
    fa = F.analyse(p.get("cashflows", []), p["finance"], float(p["finance"].get("residual_value") or 0))
    c[4].metric(tr("VAL (NPV)", "NPV"), money(fa["npv"], cur) if fa else "—", help=tr("Ver 'VAL, TIR, MIRR e WACC'", "See 'NPV, IRR, MIRR & WACC'"))
    crit = sum(1 for r in p["risks"] if exposure(r) >= 12)
    c[5].metric(tr("Riscos críticos", "Critical risks"), crit)
    c = st.columns(6)
    c[0].metric("Stakeholders", len(p["stakeholders"]))
    c[1].metric(tr("Objetivos (logframe)", "Objectives (logframe)"), len(p["objectives"]))
    c[2].metric(tr("Atividades", "Activities"), len(p["activities"]))
    c[3].metric(tr("Indicadores SMART", "SMART indicators"), f"{sum(1 for i in p['indicators'] if smart_score(i) == 5)}/{len(p['indicators'])}")
    c[4].metric(tr("Pressupostos", "Assumptions"), len(p["assumptions"]))
    c[5].metric(tr("TIR / MIRR", "IRR / MIRR"), f"{pct(fa['irr']) if fa and fa['irr'] is not None else '—'} / {pct(fa['mirr']) if fa and fa['mirr'] is not None else '—'}")

    if sched.get("ok"):
        txt = I.cpm_text(sched) + "\n\n" + I.evm_text(S.evm(p, sched), cur)
        if fa:
            txt += "\n\n" + I.finance_text(fa, cur)
        ui.interpret(txt, tr("Síntese interpretativa", "Interpretive summary"))

    st.markdown(tr("#### 🔍 Verificação de coerência entre módulos", "#### 🔍 Cross-module consistency check"))
    ch = I.checks(p, sched)
    if not ch:
        st.success(tr("Sem problemas detetados. 👏", "No issues found. 👏"))
    else:
        icon = {"error": "🔴", "warn": "🟠", "info": "🔵"}
        n = {k: sum(1 for x in ch if x["sev"] == k) for k in icon}
        st.caption(f"🔴 {n['error']} {tr('erros', 'errors')} · 🟠 {n['warn']} {tr('avisos', 'warnings')} · 🔵 {n['info']} {tr('sugestões', 'suggestions')}")
        df = pd.DataFrame([{"": icon[x["sev"]], tr("Módulo", "Module"): x["module"], tr("Mensagem", "Message"): x["msg"]}
                           for x in sorted(ch, key=lambda x: ["error", "warn", "info"].index(x["sev"]))])
        st.dataframe(df, hide_index=True, width="stretch", height=min(420, 38 + 35 * len(df)))

    st.markdown(tr("#### 🗺️ Percurso sugerido", "#### 🗺️ Suggested path"))
    st.markdown(tr(
        "1. **Identificação** — políticas → stakeholders → padrões comportamentais → árvore de problemas → objetivos e estratégia\n"
        "2. **Formulação** — logframe (lógicas vertical, horizontal e diagonal) → modelo lógico → teoria da mudança → pressupostos\n"
        "3. **Planeamento** — atividades → PERT/CPM → Gantt e custos → RACI → riscos → orçamento → contingências → procurement\n"
        "4. **Finanças** — WACC → VAL, TIR, MIRR, payback → sensibilidade\n"
        "5. **M&A** — indicadores SMART → baselines, metas e benchmarking → EVM → qualidade e avaliação\n"
        "6. **Relatórios e IA** — relatório interpretativo, modelos Excel do professor, modelo alargado e agente IA",
        "1. **Identification** — policy → stakeholders → behavioural patterns → problem tree → objectives & strategy\n"
        "2. **Formulation** — logframe (vertical, horizontal and diagonal logic) → logic model → theory of change → assumptions\n"
        "3. **Planning** — activities → PERT/CPM → Gantt & costs → RACI → risks → budget → contingencies → procurement\n"
        "4. **Finance** — WACC → NPV, IRR, MIRR, payback → sensitivity\n"
        "5. **M&E** — SMART indicators → baselines, targets & benchmarking → EVM → quality & evaluation\n"
        "6. **Reports & AI** — interpretive report, professor's Excel templates, extended template and AI agent"))


def projects_tab():
    st.markdown(tr("#### Projetos de exemplo (6 setores)", "#### Example projects (6 industries)"))
    st.caption(tr("Carregar um exemplo cria uma cópia de trabalho; guarde-a para a manter na base de dados.",
                  "Loading an example creates a working copy; save it to keep it in the database."))
    cols = st.columns(3)
    for i, (k, lab) in enumerate(DEMOS.items()):
        if cols[i % 3].button(trd(lab), key=f"demo_{k}", width="stretch"):
            ui.set_project(build_demo(k), None)
            st.toast(tr("Exemplo carregado", "Example loaded"))
            st.rerun()

    st.markdown(tr("#### Novo projeto", "#### New project"))
    with st.form("new_proj"):
        c1, c2 = st.columns(2)
        name = c1.text_input(tr("Nome do projeto", "Project name"))
        ind = c2.text_input(tr("Setor / indústria", "Industry / sector"))
        if st.form_submit_button(tr("➕ Criar projeto vazio", "➕ Create empty project"), type="primary"):
            p = new_project(name or tr("Novo projeto", "New project"), ind)
            ui.set_project(p, None)
            ui.save()
            st.rerun()

    st.markdown(tr("#### Projetos guardados", "#### Saved projects"))
    try:
        rows = db.list_projects()
    except Exception as e:
        st.error(tr(f"Não foi possível ligar à base de dados: {e}", f"Could not connect to the database: {e}"))
        rows = []
    if not rows:
        st.info(tr("Ainda não há projetos guardados.", "No saved projects yet."))
    for r in rows:
        c1, c2, c3, c4 = st.columns([5, 2, 1, 1])
        cur = " 🟢" if r["id"] == st.session_state.get("pid") else ""
        c1.markdown(f"**{r['name']}**{cur}  \n<small>{r['industry'] or ''} · {str(r['updated_at'])[:16]}</small>", unsafe_allow_html=True)
        if c3.button("📂", key=f"open_{r['id']}", help=tr("Abrir", "Open")):
            ui.set_project(db.load_project(r["id"]), r["id"])
            st.rerun()
        if c4.button("🗑️", key=f"del_{r['id']}", help=tr("Apagar", "Delete")):
            st.session_state[f"confirm_del_{r['id']}"] = True
        if st.session_state.get(f"confirm_del_{r['id']}"):
            st.warning(tr(f"Apagar definitivamente '{r['name']}'?", f"Permanently delete '{r['name']}'?"))
            b1, b2 = st.columns(2)
            if b1.button(tr("Sim, apagar", "Yes, delete"), key=f"y_{r['id']}"):
                db.delete_project(r["id"])
                if st.session_state.get("pid") == r["id"]:
                    st.session_state.pid = None
                st.session_state.pop(f"confirm_del_{r['id']}")
                st.rerun()
            if b2.button(tr("Cancelar", "Cancel"), key=f"n_{r['id']}"):
                st.session_state.pop(f"confirm_del_{r['id']}")
                st.rerun()

    pid = st.session_state.get("pid")
    if pid:
        st.markdown(tr("#### Versões (snapshots) deste projeto", "#### Versions (snapshots) of this project"))
        with st.form("snap"):
            lab = st.text_input(tr("Nome da versão", "Version label"), value=tr(f"Versão {date.today().isoformat()}", f"Version {date.today().isoformat()}"))
            if st.form_submit_button(tr("📸 Guardar versão", "📸 Save version")):
                db.add_snapshot(pid, lab, ui.P())
                st.toast(tr("Versão guardada", "Version saved"))
        for s in db.list_snapshots(pid):
            c1, c2 = st.columns([6, 1])
            c1.write(f"📸 {s['label']} · {str(s['created_at'])[:16]}")
            if c2.button(tr("Repor", "Restore"), key=f"snap_{s['id']}"):
                ui.set_project(db.load_snapshot(s["id"]), pid)
                ui.mark_dirty()
                st.rerun()


def settings(p):
    m = p["meta"]
    with st.form("meta_form"):
        c1, c2 = st.columns(2)
        m["name"] = c1.text_input(tr("Nome do projeto", "Project name"), m.get("name", ""))
        m["industry"] = c2.text_input(tr("Setor / indústria", "Industry"), m.get("industry", ""))
        m["organisation"] = c1.text_input(tr("Organização promotora", "Implementing organisation"), m.get("organisation", ""))
        m["sponsor"] = c2.text_input(tr("Patrocinador / financiador", "Sponsor / donor"), m.get("sponsor", ""))
        m["country"] = c1.text_input(tr("País / região", "Country / region"), m.get("country", ""))
        m["manager"] = c2.text_input(tr("Gestor de projeto", "Project manager"), m.get("manager", ""))
        m["description"] = st.text_area(tr("Descrição", "Description"), m.get("description", ""))
        c1, c2, c3, c4 = st.columns(4)
        m["start_date"] = c1.date_input(tr("Data de início", "Start date"), S.to_date(m.get("start_date"))).isoformat()
        m["time_unit"] = c2.selectbox(tr("Unidade de tempo (PERT/CPM)", "Time unit (PERT/CPM)"), opt_codes("time_unit"),
                                      index=opt_codes("time_unit").index(m.get("time_unit", "weeks")), format_func=lambda c: opt_label("time_unit", c))
        m["duration_mode"] = c3.selectbox(tr("Duração usada no CPM", "Duration used in CPM"), ["pert", "ml"],
                                          index=0 if m.get("duration_mode", "pert") == "pert" else 1,
                                          format_func=lambda x: tr("PERT tₑ=(a+4m+b)/6", "PERT tₑ=(a+4m+b)/6") if x == "pert" else tr("Mais provável (m)", "Most likely (m)"))
        m["currency"] = c4.selectbox(tr("Moeda", "Currency"), ["EUR", "USD", "GBP", "BRL", "AOA", "MZN", "CVE", "CHF"],
                                     index=["EUR", "USD", "GBP", "BRL", "AOA", "MZN", "CVE", "CHF"].index(m.get("currency", "EUR")))
        c1, c2, c3 = st.columns(3)
        m["status_date"] = c1.date_input(tr("Data de controlo (EVM)", "Status date (EVM)"), S.to_date(m.get("status_date"))).isoformat()
        m["period"] = c2.selectbox(tr("Período dos custos", "Cost period"), ["week", "month", "quarter", "year"],
                                   index=["week", "month", "quarter", "year"].index(m.get("period", "month")),
                                   format_func=lambda x: {"week": tr("Semana", "Week"), "month": tr("Mês", "Month"), "quarter": tr("Trimestre", "Quarter"), "year": tr("Ano", "Year")}[x])
        td = c3.number_input(tr("Prazo-alvo (unidades de tempo)", "Target duration (time units)"), value=float(m.get("target_duration") or 0), min_value=0.0)
        m["target_duration"] = td or None
        if st.form_submit_button(tr("Aplicar", "Apply"), type="primary"):
            ui.mark_dirty()
            st.rerun()


def import_export(p):
    st.markdown(tr("#### Exportar", "#### Export"))
    ui.download_json_button()
    st.caption(tr("Excel (modelos do professor e modelo alargado) e relatório HTML: página 'Relatório e exportações'.",
                  "Excel (professor's templates and extended template) and HTML report: 'Report & exports' page."))
    st.markdown(tr("#### Importar", "#### Import"))
    f = st.file_uploader(tr("Projeto completo (JSON exportado pela app)", "Full project (JSON exported by the app)"), type=["json"])
    if f is not None and st.button(tr("Importar JSON como novo projeto", "Import JSON as new project"), type="primary"):
        try:
            data = json.load(f)
            ui.set_project(normalize(data), None)
            st.success(tr("Projeto importado. Guarde-o para o manter na base de dados.", "Project imported. Save it to keep it in the database."))
            st.rerun()
        except Exception as e:
            st.error(str(e))
    from core import excel_io
    st.markdown(tr("##### Modelos Excel (do professor ou modelo alargado)", "##### Excel templates (professor's or extended)"))
    st.caption(tr("Descarregue um modelo em branco, preencha-o no Excel e carregue-o abaixo.", "Download a blank template, fill it in Excel and upload it below."))
    xl = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    b1, b2, b3 = st.columns(3)
    b1.download_button(tr("⬇️ StakeholderRegister (professor)", "⬇️ StakeholderRegister (professor)"), excel_io.professor_blank("stakeholders"),
                       "StakeholderRegister_template.xlsx", xl, help=tr("Modelo original do professor, em branco", "Professor's original template, blank"))
    b2.download_button(tr("⬇️ RiskRegister (professor)", "⬇️ RiskRegister (professor)"), excel_io.professor_blank("risks"),
                       "RiskRegister_Template.xlsx", xl, help=tr("Modelo original do professor (a linha de exemplo não é importada)", "Professor's original template (the example row is not imported)"))
    b3.download_button(tr("⬇️ Modelo alargado em branco", "⬇️ Blank extended template"), excel_io.blank_template(),
                       tr("Modelo_alargado_em_branco.xlsx", "Extended_template_blank.xlsx"), xl, type="primary",
                       help=tr("17 folhas (todos os módulos) com listas pendentes, exemplo e instruções", "17 sheets (every module) with drop-downs, example and instructions"))
    x = st.file_uploader(tr("StakeholderRegister, RiskRegister ou modelo alargado (.xlsx)", "StakeholderRegister, RiskRegister or extended template (.xlsx)"), type=["xlsx"])
    mode = st.radio(tr("Modo", "Mode"), ["append", "replace"], horizontal=True,
                    format_func=lambda v: tr("Acrescentar às tabelas atuais", "Append to current tables") if v == "append" else tr("Substituir as tabelas importadas", "Replace imported tables"))
    if x is not None and st.button(tr("Importar Excel", "Import Excel")):
        try:
            msg = excel_io.import_workbook(p, x, mode)
            ui.bump()
            st.success(msg)
        except Exception as e:
            st.error(str(e))
    st.markdown(tr("##### Atividades (CSV/Excel com colunas id, name, predecessors, optimistic, most_likely, pessimistic, cost…)",
                   "##### Activities (CSV/Excel with columns id, name, predecessors, optimistic, most_likely, pessimistic, cost…)"))
    c1, c2 = st.columns(2)
    c1.download_button(tr("⬇️ Modelo de atividades (.xlsx)", "⬇️ Activities template (.xlsx)"), excel_io.activities_template("xlsx"),
                       tr("Atividades_template.xlsx", "Activities_template.xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    c2.download_button(tr("⬇️ Modelo de atividades (.csv)", "⬇️ Activities template (.csv)"), excel_io.activities_template("csv"),
                       tr("Atividades_template.csv", "Activities_template.csv"), "text/csv")
    a = st.file_uploader(tr("Ficheiro de atividades", "Activities file"), type=["csv", "xlsx"], key="acts_up")
    if a is not None and st.button(tr("Importar atividades", "Import activities")):
        try:
            n = excel_io.import_activities(p, a, mode)
            ui.bump()
            st.success(tr(f"{n} atividades importadas.", f"{n} activities imported."))
        except Exception as e:
            st.error(str(e))
    st.caption(tr("Para extrair informação de documentos Word ou de texto livre, use o 'Agente IA'.",
                  "To extract information from Word documents or free text, use the 'AI agent'."))
