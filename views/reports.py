"""6 · Reports & AI: HTML report, Excel exports (professor's templates + extended), AI agent."""
import json

import streamlit as st

from core import agent as AG
from core import excel_io as X
from core import report as R
from core import ui
from core.i18n import tr


def report():
    p = ui.P()
    ui.header("Relatório interpretativo e exportações", "Interpretive report & exports", "report", "📑")
    name = ui._slug(p["meta"].get("name", "projeto"))
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(tr("#### 📑 Relatório HTML", "#### 📑 HTML report"))
        st.caption(tr("Inclui todos os módulos, gráficos interativos, diagramas e interpretações automáticas. Abra no navegador → Imprimir → Guardar como PDF.",
                      "Includes every module, interactive charts, diagrams and automatic interpretations. Open in a browser → Print → Save as PDF."))
        use_ai = st.checkbox(tr("Incluir síntese escrita pelo agente IA", "Include AI-written synthesis"), value=False, disabled=not AG.available(),
                             help=None if AG.available() else tr("Requer ANTHROPIC_API_KEY", "Requires ANTHROPIC_API_KEY"))
        if st.button(tr("⚙️ Gerar relatório", "⚙️ Build report"), type="primary"):
            ai = None
            if use_ai:
                with st.spinner(tr("O agente está a escrever a síntese…", "The agent is writing the synthesis…")):
                    try:
                        ai = AG.synthesis(p, st.session_state.get("ai_model"))
                    except Exception as e:
                        st.warning(tr(f"Agente indisponível: {e}", f"Agent unavailable: {e}"))
            with st.spinner(tr("A gerar…", "Building…")):
                st.session_state["report_html"] = R.build(p, ai)
        if st.session_state.get("report_html"):
            st.download_button(tr("⬇️ Descarregar relatório (HTML)", "⬇️ Download report (HTML)"), st.session_state["report_html"].encode("utf-8"),
                               f"relatorio_{name}.html", "text/html", type="primary")
            with st.expander(tr("👁️ Pré-visualizar", "👁️ Preview")):
                st.components.v1.html(st.session_state["report_html"], height=900, scrolling=True)
    with c2:
        st.markdown(tr("#### 📗 Excel", "#### 📗 Excel"))
        st.markdown(tr("**Modelos do professor (formato original respeitado):**", "**Professor's templates (original format preserved):**"))
        b, w = X.professor_stakeholders(p)
        for x in w:
            st.caption("⚠️ " + x)
        st.download_button("⬇️ StakeholderRegister.xlsx", b, f"StakeholderRegister_{name}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        b, w = X.professor_risks(p)
        for x in w:
            st.caption("⚠️ " + x)
        st.download_button("⬇️ RiskRegister.xlsx", b, f"RiskRegister_{name}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.markdown(tr("**Modelo alargado (todos os módulos, com fórmulas Excel):**", "**Extended template (every module, with Excel formulas):**"))
        st.caption(tr("Inclui logframe, indicadores, PERT/CPM, Gantt com custos e curva S, EVM, RACI, riscos e matriz, orçamento, procurement, finanças (WACC, VAL, TIR, MIRR em fórmulas) e avaliação. Pode ser reimportado na app.",
                      "Includes logframe, indicators, PERT/CPM, cost-loaded Gantt & S-curve, EVM, RACI, risks & matrix, budget, procurement, finance (WACC, NPV, IRR, MIRR as formulas) and evaluation. Can be re-imported into the app."))
        if st.button(tr("⚙️ Gerar modelo alargado", "⚙️ Build extended template")):
            st.session_state["ext_xlsx"] = X.extended_workbook(p)
        if st.session_state.get("ext_xlsx"):
            st.download_button(tr("⬇️ Modelo alargado (.xlsx)", "⬇️ Extended template (.xlsx)"), st.session_state["ext_xlsx"], f"Modelo_alargado_{name}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        st.markdown("#### 🗂️ JSON")
        ui.download_json_button()


def agent():
    p = ui.P()
    ui.header("Agente IA de gestão de projetos", "Project management AI agent", "agent", "🤖")
    if not AG.available():
        st.warning(tr("O agente precisa de uma chave da API da Anthropic. No Render: *Environment → Add Environment Variable* → `ANTHROPIC_API_KEY`. "
                      "Localmente: crie um ficheiro `.env` (ver `.env.example`) ou exporte a variável antes de `streamlit run app.py`. "
                      "Todas as outras funcionalidades (cálculos e interpretações automáticas) funcionam sem chave.",
                      "The agent needs an Anthropic API key. On Render: *Environment → Add Environment Variable* → `ANTHROPIC_API_KEY`. "
                      "Locally: create a `.env` file (see `.env.example`) or export the variable before `streamlit run app.py`. "
                      "Every other feature (calculations and automatic interpretations) works without a key."))
        return
    st.session_state.setdefault("ai_model", AG.DEFAULT_MODEL)
    opts = list(dict.fromkeys([AG.DEFAULT_MODEL] + AG.MODELS))
    st.session_state.ai_model = st.selectbox(tr("Modelo", "Model"), opts, index=opts.index(st.session_state.ai_model) if st.session_state.ai_model in opts else 0)
    t1, t2, t3, t4 = st.tabs([tr("💬 Conversar", "💬 Chat"), tr("🏗️ Gerar projeto", "🏗️ Generate project"), tr("📄 Extrair de documento", "📄 Extract from document"),
                              tr("🔎 Rever coerência", "🔎 Review coherence")])
    with t1:
        st.caption(tr("O agente conhece a metodologia e o projeto aberto (incluindo resultados calculados). Exemplos: 'Que pressupostos comportamentais faltam?', "
                      "'Como reduzir o prazo em 2 semanas?', 'Propõe indicadores para o OC2'.",
                      "The agent knows the methodology and the open project (including computed results). Examples: 'Which behavioural assumptions are missing?', "
                      "'How can we cut 2 weeks?', 'Propose indicators for OC2'."))
        hist = st.session_state.setdefault("chat", [])
        for msg in hist:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        q = st.chat_input(tr("Escreva a sua pergunta…", "Type your question…"))
        if q:
            hist.append({"role": "user", "content": q})
            with st.chat_message("user"):
                st.markdown(q)
            with st.chat_message("assistant"):
                try:
                    ans = st.write_stream(AG.chat_stream(hist[-12:], p, st.session_state.ai_model))
                except Exception as e:
                    ans = tr(f"Erro do agente: {e}", f"Agent error: {e}")
                    st.error(ans)
            hist.append({"role": "assistant", "content": ans if isinstance(ans, str) else str(ans)})
        if hist and st.button(tr("🧹 Limpar conversa", "🧹 Clear chat")):
            st.session_state.chat = []
            st.rerun()
    with t2:
        st.caption(tr("Descreva o projeto (setor, problema, público-alvo, orçamento aproximado, duração). O agente propõe um rascunho completo e coerente que pode rever antes de aplicar.",
                      "Describe the project (sector, problem, target group, approximate budget, duration). The agent drafts a complete, coherent proposal you can review before applying."))
        desc = st.text_area(tr("Descrição do projeto", "Project description"), height=160, key="gen_desc")
        mods = st.multiselect(tr("Módulos a gerar", "Modules to generate"), AG.GEN_TABLES, default=AG.GEN_TABLES)
        inc_meta = st.checkbox(tr("Incluir dados gerais, políticas e ToC", "Include general data, policy and ToC"), value=True)
        if st.button(tr("🏗️ Gerar rascunho", "🏗️ Generate draft"), type="primary", disabled=not desc.strip()):
            with st.spinner(tr("O agente está a desenhar o projeto (pode demorar 1–2 minutos)…", "The agent is designing the project (may take 1–2 minutes)…")):
                try:
                    st.session_state["ai_draft"] = AG.generate(desc + ("" if inc_meta else "\n(Do not return meta/policy/toc.)"), p, mods, st.session_state.ai_model)
                except Exception as e:
                    st.error(tr(f"Erro: {e}", f"Error: {e}"))
        _draft_apply("ai_draft")
    with t3:
        st.caption(tr("Carregue um documento (Word, PDF ou texto) — por exemplo, um termo de referência, uma candidatura ou notas de reunião — e o agente extrai a informação estruturada.",
                      "Upload a document (Word, PDF or text) — e.g. terms of reference, a proposal or meeting notes — and the agent extracts structured information."))
        f = st.file_uploader(tr("Documento", "Document"), type=["docx", "pdf", "txt", "md"])
        txt = st.text_area(tr("…ou cole o texto aqui", "…or paste the text here"), height=120)
        mods = st.multiselect(tr("Módulos a extrair", "Modules to extract"), AG.GEN_TABLES, default=["stakeholders", "problems", "objectives", "indicators", "assumptions", "activities", "risks"], key="ext_mods")
        if st.button(tr("📄 Extrair", "📄 Extract"), type="primary", disabled=not (f or txt.strip())):
            source = txt
            if f is not None:
                n = f.name.lower()
                source = AG.docx_text(f) if n.endswith(".docx") else AG.pdf_text(f) if n.endswith(".pdf") else f.read().decode("utf-8", "ignore")
            with st.spinner(tr("A extrair…", "Extracting…")):
                try:
                    st.session_state["ai_extract"] = AG.generate(tr("Extrair do documento a informação do projeto.", "Extract the project information from the document."), p, mods,
                                                                 st.session_state.ai_model, source_text=source)
                except Exception as e:
                    st.error(tr(f"Erro: {e}", f"Error: {e}"))
        _draft_apply("ai_extract")
    with t4:
        st.caption(tr("O agente avalia as lógicas vertical, diagonal e horizontal, o planeamento e a viabilidade, e propõe melhorias prioritárias.",
                      "The agent assesses vertical, diagonal and horizontal logic, planning and feasibility, and proposes prioritised improvements."))
        c1, c2 = st.columns(2)
        if c1.button(tr("🔎 Rever o projeto", "🔎 Review the project"), type="primary"):
            with st.spinner(tr("A rever…", "Reviewing…")):
                try:
                    st.session_state["ai_review"] = AG.review(p, st.session_state.ai_model)
                except Exception as e:
                    st.error(str(e))
        if c2.button(tr("📏 Sugerir indicadores SMART em falta", "📏 Suggest missing SMART indicators")):
            with st.spinner("…"):
                try:
                    st.session_state["ai_ind"] = AG.suggest_indicators(p, st.session_state.ai_model)
                except Exception as e:
                    st.error(str(e))
        if st.session_state.get("ai_review"):
            st.markdown(st.session_state["ai_review"])
        _draft_apply("ai_ind", default_mode="append")


def _draft_apply(key: str, default_mode: str = "replace"):
    d = st.session_state.get(key)
    if not d:
        return
    st.markdown(tr("##### Proposta do agente (rever antes de aplicar)", "##### Agent proposal (review before applying)"))
    for k, v in d.items():
        with st.expander(f"{k} ({len(v) if isinstance(v, list) else '…'})"):
            st.json(v, expanded=False)
    c1, c2, c3 = st.columns(3)
    mode = c1.radio(tr("Aplicar como", "Apply as"), ["replace", "append"], index=0 if default_mode == "replace" else 1, horizontal=True, key=f"mode_{key}",
                    format_func=lambda v: tr("Substituir tabelas", "Replace tables") if v == "replace" else tr("Acrescentar", "Append"))
    if c2.button(tr("✅ Aplicar ao projeto", "✅ Apply to project"), key=f"apply_{key}", type="primary"):
        done = AG.apply(ui.P(), d, mode)
        ui.bump()
        st.session_state.pop(key, None)
        st.success(tr("Aplicado: ", "Applied: ") + ", ".join(done))
        st.rerun()
    if c3.button(tr("🗑️ Descartar", "🗑️ Discard"), key=f"disc_{key}"):
        st.session_state.pop(key, None)
        st.rerun()
    c1.download_button("⬇️ JSON", json.dumps(d, ensure_ascii=False, indent=2), f"{key}.json", "application/json", key=f"dl_{key}")
