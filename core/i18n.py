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
}


def opt_codes(name: str) -> list:
    rows = OPTIONS[name]
    return [r[0] for r in rows]


def opt_label(name: str, code) -> str:
    for r in OPTIONS[name]:
        if r[0] == code:
            if len(r) == 3:  # numeric scales
                return f"{r[0]} - {r[1] if get_lang() == 'en' else r[2]}"
            return r[0] if get_lang() == "en" else r[1]
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
