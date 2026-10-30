"""PM Studio — Project Cycle Management (Logic Models, Analytical & Planning Tools, PERT/CPM, Gantt, EVM, Finance).

Run locally:   streamlit run app.py
"""
import streamlit as st

try:  # local development: read .env (ANTHROPIC_API_KEY, DATABASE_URL)
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

st.set_page_config(page_title="PM Studio — Project Cycle Management", page_icon="🧭", layout="wide",
                   initial_sidebar_state="expanded")

from core import db, ui  # noqa: E402
from core.i18n import tr  # noqa: E402
from views import formulation, finance_view, home, identification, me, planning, reports  # noqa: E402

ui.init_state()

st.markdown("""
<style>
[data-testid="stSidebarNav"] span {font-size: 0.92rem;}
div[data-testid="stMetricValue"] {font-size: 1.45rem;}
.block-container {padding-top: 2.2rem;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧭 PM Studio")
    lang = st.segmented_control("Idioma / Language", ["pt", "en"], default=st.session_state.lang,
                                format_func=lambda x: "🇵🇹 Português" if x == "pt" else "🇬🇧 English", key="lang_sel")
    if lang and lang != st.session_state.lang:
        st.session_state.lang = lang
        st.rerun()

def page(fn, pt, en, icon, path, default=False):
    return st.Page(fn, title=tr(pt, en), icon=icon, url_path=path, default=default)


pages = {
    tr("Projeto", "Project"): [
        page(home.render, "Início e projetos", "Home & projects", "🏠", "home", default=True),
    ],
    tr("1 · Identificação", "1 · Identification"): [
        page(identification.policy, "Políticas e estratégia", "Policy & strategy", "🏛️", "policy"),
        page(identification.stakeholders, "Stakeholders", "Stakeholders", "👥", "stakeholders"),
        page(identification.behaviour, "Padrões comportamentais", "Behavioural patterns", "🔺", "behaviour"),
        page(identification.problems, "Árvore de problemas", "Problem tree", "🌳", "problems"),
        page(identification.objectives, "Objetivos e estratégias", "Objectives & strategies", "🎯", "objectives"),
    ],
    tr("2 · Formulação (Logic Models)", "2 · Formulation (Logic Models)"): [
        page(formulation.logframe, "Logframe (matriz)", "Logframe matrix", "🧩", "logframe"),
        page(formulation.logic_model, "Modelo lógico", "Logic model", "🔗", "logic-model"),
        page(formulation.toc, "Teoria da Mudança", "Theory of Change", "🔄", "toc"),
        page(formulation.assumptions, "Pressupostos", "Assumptions", "🧱", "assumptions"),
    ],
    tr("3 · Planeamento", "3 · Planning"): [
        page(planning.activities, "Atividades e WBS", "Activities & WBS", "📋", "activities"),
        page(planning.pert, "PERT / CPM", "PERT / CPM", "🕸️", "pert"),
        page(planning.gantt, "Gantt e custos no tempo", "Gantt & time-phased cost", "📅", "gantt"),
        page(planning.raci, "Matriz RACI / RASCI", "RACI / RASCI matrix", "🧑‍🤝‍🧑", "raci"),
        page(planning.risks, "Riscos", "Risks", "⚠️", "risks"),
        page(planning.budget, "Orçamento e cash flow", "Budget & cash flow", "💶", "budget"),
        page(planning.contingency, "Contingências", "Contingencies", "🛟", "contingency"),
        page(planning.procurement, "Procurement", "Procurement", "🛒", "procurement"),
    ],
    tr("4 · Análise financeira", "4 · Financial appraisal"): [
        page(finance_view.render, "VAL, TIR, MIRR e WACC", "NPV, IRR, MIRR & WACC", "📈", "finance"),
    ],
    tr("5 · Monitorização e Avaliação", "5 · Monitoring & Evaluation"): [
        page(me.indicators, "Indicadores SMART", "SMART indicators", "📏", "indicators"),
        page(me.benchmark, "Baselines, metas e benchmarking", "Baselines, targets & benchmarking", "🏁", "benchmark"),
        page(me.evm, "Earned Value (EVM)", "Earned Value (EVM)", "📊", "evm"),
        page(me.quality, "Qualidade e avaliação", "Quality & evaluation", "✅", "quality"),
    ],
    tr("6 · Relatórios e IA", "6 · Reports & AI"): [
        page(reports.report, "Relatório e exportações", "Report & exports", "📑", "report"),
        page(reports.agent, "Agente IA", "AI agent", "🤖", "agent"),
    ],
}

nav = st.navigation(pages, expanded=True)

with st.sidebar:
    st.divider()
    m = st.session_state.project["meta"]
    st.markdown(f"**📁 {m.get('name', '')}**")
    pid = st.session_state.get("pid")
    st.caption((tr("Guardado na BD · id ", "Saved in DB · id ") + str(pid)) if pid else tr("⚠️ Ainda não guardado", "⚠️ Not saved yet"))
    c1, c2 = st.columns(2)
    if c1.button(tr("💾 Guardar", "💾 Save"), width="stretch", type="primary"):
        ui.save()
        st.rerun()
    st.session_state.autosave = c2.toggle(tr("Auto", "Auto"), value=st.session_state.get("autosave", True),
                                          help=tr("Guardar automaticamente cada alteração (depois da 1.ª gravação)",
                                                  "Automatically save every change (after the first save)"))
    if st.session_state.get("dirty"):
        st.caption(tr("✏️ Alterações por guardar", "✏️ Unsaved changes"))
    st.caption(f"🗄️ {db.backend_name()}")

nav.run()
ui.autosave()
ui.sync_query()
