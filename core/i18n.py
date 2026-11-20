"""Bilingual support (Português / English).

Usage:  tr("Atividades", "Activities")
The current language is stored in st.session_state["lang"] ("pt" or "en").
"""
from __future__ import annotations

try:
    import streamlit as st
except Exception:  # pragma: no cover - allows engines to run without streamlit
    st = None

_FALLBACK = {"lang": "pt"}


def get_lang() -> str:
    if st is not None:
        try:
            from streamlit import runtime
            if runtime.exists():
                return st.session_state.get("lang", "pt")
        except Exception:
            pass
    return _FALLBACK["lang"]


def set_lang(lang: str) -> None:
    _FALLBACK["lang"] = lang
    if st is not None:
        try:
            from streamlit import runtime
            if runtime.exists():
                st.session_state["lang"] = lang
        except Exception:
            pass


def get_terminology() -> str:
    """Logframe terminology of the current project: 'pcm' (overall/specific objective, results) or 'results' (impact/outcome/output)."""
    if st is not None:
        try:
            from streamlit import runtime
            if runtime.exists():
                return st.session_state.get("terminology", "pcm")
        except Exception:
            pass
    return _FALLBACK.get("terminology", "pcm")


def set_terminology(t: str) -> None:
    _FALLBACK["terminology"] = t or "pcm"
    if st is not None:
        try:
            from streamlit import runtime
            if runtime.exists():
                st.session_state["terminology"] = t or "pcm"
        except Exception:
            pass


# level names with the PCM terminology; the results-based equivalent is kept in brackets to avoid the
# classic trap: in PCM "Resultados" = Outputs, while in results-based management "Resultado" = Outcome
PCM_LEVEL = {"Impact": ("Objetivo global (Impacto)", "Overall objective (Impact)"), "Outcome": ("Objetivo específico (Outcome)", "Specific objective (Outcome)"),
             "Output": ("Resultado (Output)", "Result (Output)")}


def tr(pt: str, en: str) -> str:
    """Return the text in the active language."""
    return pt if get_lang() == "pt" else en


def trd(d: dict | str | None) -> str:
    """Translate a dict {'pt':..., 'en':...} (or return a plain string)."""
    if d is None:
        return ""
    if isinstance(d, str):
        return d
    return d.get(get_lang()) or d.get("pt") or d.get("en") or ""


# Canonical option lists (stored values are language-neutral codes; labels are translated)
OPTIONS = {
    "stakeholder_type": [  # professor template (StakeholderRegister)
        ("Resource provider", "Fornecedor de recursos"),
        ("Target group", "Grupo-alvo"),
        ("Beneficiary", "Beneficiário"),
        ("Project partner", "Parceiro do projeto"),
        ("Other (specify)", "Outro (especificar)"),
    ],
    "engagement": [
        ("Inform", "Informar"),
        ("Consult", "Consultar"),
        ("Involve", "Envolver"),
        ("Collaborate", "Colaborar"),
        ("Empower", "Capacitar / delegar"),
        ("Monitor", "Monitorizar"),
    ],
    "attitude": [("Supporter", "Apoiante"), ("Neutral", "Neutro"), ("Opponent", "Opositor")],
    "risk_type": [  # professor template (RiskRegister)
        ("Project/programme delivery", "Execução do projeto/programa"),
        ("Human resources", "Recursos humanos"),
        ("Communication and reputation", "Comunicação e reputação"),
        ("Financial", "Financeiro"),
        ("IT", "TI"),
        ("Safety, security and logistics", "Segurança e logística"),
        ("Political", "Político"),
        ("Other (rare)", "Outro (raro)"),
    ],
    "likelihood": [(4, "Almost certain", "Quase certo"), (3, "Likely", "Provável"),
                   (2, "Possible", "Possível"), (1, "Unlikely", "Improvável")],
    "impact": [(4, "Severe", "Severo"), (3, "Major", "Grave"), (2, "Moderate", "Moderado"), (1, "Minor", "Menor")],
    "risk_strategy": [("Avoid", "Evitar"), ("Reduce", "Reduzir / mitigar"), ("Transfer", "Transferir"),
                      ("Accept", "Aceitar"), ("Exploit", "Explorar (oportunidade)")],
    "assumption_type": [("Operational", "Operacional"), ("Behavioural", "Comportamental"), ("Political", "Político")],
    "activity_type": [("Production", "Produção"), ("Support - Communication", "Apoio - Comunicação"),
                      ("Support - M&E", "Apoio - Monitorização e Avaliação"), ("Support - Events", "Apoio - Eventos"),
                      ("Support - Management", "Apoio - Gestão do projeto"), ("Support - Risk prevention", "Apoio - Prevenção de risco")],
    "distribution": [("Uniform", "Uniforme"), ("Start", "Início"), ("End", "Fim"),
                     ("Front-loaded", "Concentrado no início"), ("Back-loaded", "Concentrado no fim"),
                     ("Milestone 50/50", "Marco 50/50")],
    "cost_category": [("Fees & Direct Expenses", "Honorários e despesas diretas"),
                      ("Reimbursable Expenses", "Despesas reembolsáveis"),
                      ("Equipment", "Equipamento"), ("Materials", "Materiais"),
                      ("Services / Subcontracting", "Serviços / subcontratação"), ("Other", "Outros")],
    "phase": [("Inception", "Arranque (inception)"), ("Implementation", "Implementação"), ("Completion", "Encerramento")],
    "procurement": [("Competitive Bidding", "Concurso público"), ("Request for Proposals (RFP)", "Pedido de propostas (RFP)"),
                    ("Request for Quotations (RFQ)", "Pedido de cotações (RFQ)"), ("Sole Sourcing", "Ajuste direto"),
                    ("Framework Agreement", "Acordo-quadro")],
    "proc_category": [("Goods", "Bens"), ("Services", "Serviços"), ("Works", "Empreitadas")],
    "level": [("Impact", "Impacto"), ("Outcome", "Resultado (Outcome)"), ("Output", "Produto (Output)"),
              ("Activity", "Atividade"), ("Input", "Recurso (Input)")],
    "indicator_level": [("Impact", "Impacto"), ("Outcome", "Resultado (Outcome)"), ("Output", "Produto (Output)"),
                        ("Input", "Recurso (Input)")],
    "problem_level": [("Effect", "Efeito"), ("Core problem", "Problema central"), ("Cause", "Causa")],
    "holds": [("Almost certainly", "Quase de certeza"), ("Possibly", "Possivelmente"), ("Unlikely", "Improvável")],
    "time_unit": [("days", "dias"), ("weeks", "semanas"), ("months", "meses")],
    "raci": [("R", "R"), ("A", "A"), ("S", "S"), ("C", "C"), ("I", "I"), ("", "")],
    "wbs_type": [("Project", "Projeto"), ("Phase", "Fase"), ("Deliverable", "Entregável"), ("Control account", "Conta de controlo"),
                 ("Work package", "Pacote de trabalho")],
    "wbs_orientation": [("deliverables", "Por entregáveis (ligados ao quadro lógico)"), ("phases", "Por fases do ciclo de vida")],
    "wbs_rule": [("auto", "Automática (8/80 em dias; período de reporte em semanas/meses)"), ("8/80", "Regra 8/80 (8 a 80 horas de trabalho)"), ("reporting", "Regra do período de reporte (≤ 1 período)")],
    # ---------------- implementation & monitoring
    "engagement_tool": [("Intermediaries", "Trabalhar com intermediários"), ("Information sharing", "Partilha de informação"),
                        ("Repeated interaction", "Interação repetida"), ("Surrogates", "Representantes indiretos (surrogates)"),
                        ("Levelling techniques", "Técnicas de nivelamento"), ("Separate events", "Eventos separados"),
                        ("Capacity building", "Capacitação"), ("Working with the community", "Trabalho com a comunidade"),
                        ("Representatives", "Representantes legitimados"), ("On-site visits", "Visitas ao terreno"),
                        ("Document review", "Revisão de documentos pelos stakeholders"), ("Start early and broadly", "Começar cedo e de forma ampla"),
                        ("Common ground", "Procurar terreno comum"), ("Dealing with deadlock", "Gerir o impasse")],
    "task_status": [("Planned", "Planeado"), ("Ongoing", "Em curso"), ("Done", "Concluído"), ("Delayed", "Atrasado"), ("Cancelled", "Cancelado")],
    "feedback_channel": [("Survey", "Inquérito"), ("Focus group", "Grupo focal"), ("Site visit", "Visita ao terreno"), ("Interview", "Entrevista"),
                         ("Suggestion box", "Caixa de sugestões"), ("Meeting", "Reunião"), ("Document review", "Revisão de documentos"),
                         ("Online platform", "Plataforma online")],
    "open_closed": [("Open", "Aberto"), ("Closed", "Fechado")],
    "change_element": [("Work package", "Pacote de trabalho (WBS)"), ("Input", "Recursos (inputs)"), ("Activity", "Atividade"), ("Output", "Output"), ("Outcome", "Outcome"),
                       ("Impact", "Impacto"), ("Target", "Meta de indicador"), ("Budget", "Orçamento"), ("Schedule", "Cronograma")],
    "change_status": [("Proposed", "Proposto"), ("Approved", "Aprovado"), ("Rejected", "Rejeitado"), ("Implemented", "Implementado")],
    "risk_status": [("Open", "Aberto"), ("Materialised", "Materializado"), ("Closed", "Fechado")],
    "asm_status": [("Confirmed", "Confirmado"), ("At risk", "Em risco"), ("Not confirmed", "Não confirmado")],
    "reserve": [("Contingency reserve", "Reserva de contingência"), ("Management reserve", "Reserva de gestão")],
    "cont_move": [("Use", "Utilização"), ("Release", "Libertação"), ("Reinforcement", "Reforço")],
    "funding_status": [("Planned", "Previsto"), ("Received", "Recebido")],
    "contract_type": [("Lump sum / Fixed price", "Preço fixo global (lump sum)"), ("Cost reimbursement", "Custos reembolsáveis (CPFF/CPIF/CPAF)"),
                      ("Time and materials", "Tempo e materiais (T&M)"), ("Unit price", "Preço unitário"),
                      ("Fixed price incentive fee", "Preço fixo com incentivo (FPIF)"), ("Guaranteed maximum price", "Preço máximo garantido (GMP)"),
                      ("IDIQ", "Entrega e quantidade indefinidas (IDIQ)"), ("Framework agreement", "Acordo-quadro"),
                      ("Master service agreement", "Contrato-quadro de serviços (MSA)")],
    "tender_stage": [("ts01", "1 Identificação da necessidade"), ("ts02", "2 Planeamento e documentação"), ("ts03", "3 Orçamento e financiamento"),
                     ("ts04", "4 Seleção do procedimento"), ("ts05", "5 Identificação/pré-qualificação"), ("ts06", "6 Publicação do anúncio"),
                     ("ts07", "7 Período de submissão"), ("ts08", "8 Esclarecimentos"), ("ts09", "9 Comissão de avaliação"),
                     ("ts10", "10 Abertura das propostas"), ("ts11", "11 Avaliação das propostas"), ("ts12", "12 Clarificações/negociação"),
                     ("ts13", "13 Adjudicação"), ("ts14", "14 Debriefing"), ("ts15", "15 Gestão do contrato"),
                     ("ts16", "16 Documentação e reporte"), ("ts17", "17 Encerramento e avaliação")],
    "certainty": [("High", "Alta"), ("Medium", "Média"), ("Low", "Baixa")],
    "audience_circle": [("1", "1.º círculo — stakeholders locais e multiplicadores"), ("2", "2.º círculo — interessados sem relação estabelecida"),
                        ("3", "3.º círculo — público em geral")],
    "closure_step": [("cs01", "Revisão do contrato"), ("cs02", "Verificação dos entregáveis"), ("cs03", "Inspeção final e aceitação"),
                     ("cs04", "Resolução de pendências"), ("cs05", "Liquidação financeira"), ("cs06", "Reunião de encerramento"),
                     ("cs07", "Documentação e registos"), ("cs08", "Relatório final"), ("cs09", "Notificação formal de encerramento"),
                     ("cs10", "Libertação de garantias/retenções"), ("cs11", "Plano de transição"), ("cs12", "Arquivo"),
                     ("cs13", "Lições aprendidas"), ("cs14", "Certificado de encerramento"), ("cs15", "Revisão jurídica")],
    # ---------------- evaluation & closure
    "eval_qtype": [("Descriptive", "Descritiva"), ("Normative", "Normativa"), ("Cause-effect", "Causa-efeito")],
    "data_type": [("Quantitative", "Quantitativa"), ("Qualitative", "Qualitativa"), ("Mixed", "Mista")],
    "eval_type": [("Formative", "Formativa"), ("Summative", "Sumativa"), ("Prospective", "Prospetiva")],
    "eval_purpose": [("Strategy", "Estratégia (relevância)"), ("Operations", "Operações (eficácia e eficiência)"), ("Learning", "Aprendizagem (lições)")],
    "eval_timing": [("Ex-ante", "Ex-ante"), ("Mid-term", "Intercalar"), ("Final", "Final"), ("Ex-post", "Ex-post")],
    "eval_who": [("Internal", "Interna"), ("External", "Externa"), ("Mixed", "Mista")],
    "pillar": [("Economic", "Viabilidade económica"), ("Social", "Impacto social"), ("Environmental", "Sustentabilidade ambiental"),
               ("Institutional", "Capacidade institucional"), ("Technological", "Viabilidade tecnológica")],
    "lesson_cat": [("Political", "Político"), ("Technical", "Técnico"), ("Cooperation", "Cooperação"), ("Design and substance", "Desenho e substância"),
                   ("Financial", "Financeiro"), ("Participation", "Participação"), ("Governance", "Governação"), ("Monitoring", "Monitorização")],
    "diss_channel": [("Project reports", "Relatórios de projeto"), ("Presentations and workshops", "Apresentações e workshops"),
                     ("Publications", "Publicações"), ("Websites and blogs", "Sites e blogues"), ("Social media", "Redes sociais"),
                     ("Press releases", "Comunicados de imprensa"), ("Webinars", "Webinars e eventos online"),
                     ("Videos and infographics", "Vídeos e infografias"), ("Conferences", "Conferências"),
                     ("Partnerships and networks", "Parcerias e redes"), ("Knowledge platforms", "Plataformas de conhecimento"),
                     ("Public events", "Eventos públicos"), ("Policy briefs", "Policy briefs"), ("Newsletters", "Newsletters"),
                     ("Targeted outreach", "Contacto direcionado")],
    "audit_type": [("Process", "Processo"), ("Product", "Produto"), ("Compliance", "Conformidade"), ("Financial", "Financeira")],
    "ip_type": [("Copyright", "Direitos de autor"), ("Patent", "Patente"), ("Trademark", "Marca"), ("Data/database", "Dados/base de dados"),
                ("Know-how", "Know-how"), ("None", "Nenhum")],
    "owner_regime": [("Exclusive", "Exclusiva"), ("Shared", "Partilhada"), ("Joint", "Conjunta")],
    "yesno3": [("Yes", "Sim"), ("Partial", "Parcial"), ("No", "Não")],
    "me_item": [("me01", "Plano e quadro de M&A claros (objetivos, indicadores, metas)"), ("me02", "Fontes de dados fiáveis e métodos adequados"),
                ("me03", "Gestão e análise de dados com controlo de qualidade"), ("me04", "Relatórios completos, atempados e usados nas decisões"),
                ("me05", "Envolvimento dos stakeholders no M&A"), ("me06", "Princípios éticos (privacidade, consentimento, confidencialidade)"),
                ("me07", "Aprendizagem e gestão adaptativa"), ("me08", "Custo-eficácia do sistema de M&A"),
                ("me09", "Comparação com padrões nacionais/internacionais"), ("me10", "Feedback dos stakeholders sobre o M&A")],
}


def opt_codes(name: str) -> list:
    rows = OPTIONS[name]
    return [r[0] for r in rows]


def opt_label(name: str, code) -> str:
    if name in ("level", "indicator_level") and code in PCM_LEVEL and get_terminology() == "pcm":
        return PCM_LEVEL[code][0 if get_lang() == "pt" else 1]
    for r in OPTIONS[name]:
        if r[0] == code:
            if len(r) == 3:  # numeric scales
                return f"{r[0]} - {r[1] if get_lang() == 'en' else r[2]}"
            if get_lang() == "en":
                if name in EN_LABELS:
                    return EN_LABELS[name][OPTIONS[name].index(r)]
                return r[0]
            return r[1]
    return "" if code is None else str(code)


def scale_labels(name: str) -> list[str]:
    """For likelihood/impact: labels in English as stored in the professor template."""
    return [r[1] for r in OPTIONS[name]]


def scale_value(name: str, label) -> int:
    for r in OPTIONS[name]:
        if label in (r[1], r[2]) or label == r[0] or str(label) == str(r[0]):
            return int(r[0])
    try:
        return int(label)
    except Exception:
        return 0


# English labels for lists whose stored codes are not readable English words
EN_LABELS = {
    "wbs_orientation": ["By deliverables (linked to the logframe)", "By life-cycle phases"],
    "wbs_rule": ["Automatic (8/80 in days; reporting period in weeks/months)", "8/80 rule (8 to 80 hours of work)", "Reporting-period rule (≤ 1 period)"],
    "tender_stage": ["1 Identification of need", "2 Planning and documentation", "3 Budgeting and funding", "4 Procurement method selection",
                     "5 Supplier identification/prequalification", "6 Tender advertising", "7 Submission period", "8 Bidder queries & clarifications",
                     "9 Bid evaluation committee", "10 Bid opening", "11 Bid evaluation", "12 Clarifications & negotiations", "13 Contract award",
                     "14 Debriefing", "15 Contract management", "16 Documentation & reporting", "17 Closure & evaluation"],
    "audience_circle": ["1st circle — local stakeholders & multipliers", "2nd circle — interested parties without established relationship", "3rd circle — general public"],
    "closure_step": ["Contract review", "Verification of deliverables", "Final inspection and acceptance", "Resolution of outstanding issues",
                     "Financial settlement", "Contract closeout meeting", "Documentation and records", "Final reporting", "Formal notice of contract closure",
                     "Release of performance bonds / retainage", "Transition planning", "Archiving", "Lessons learned", "Contract closure certificate", "Legal review"],
    "me_item": ["Clear M&E plan and framework (objectives, indicators, targets)", "Reliable data sources and appropriate methods",
                "Data management and analysis with quality control", "Complete, timely reports used in decisions", "Stakeholder engagement in M&E",
                "Ethical standards (privacy, consent, confidentiality)", "Learning and adaptive management", "Cost-effectiveness of the M&E system",
                "Comparison with national/international standards", "Stakeholder feedback on M&E"],
}
