"""Shared Streamlit UI helpers: project state, editable tables, legends, interpretation boxes."""
from __future__ import annotations

import copy
import json
import math

import pandas as pd
import streamlit as st

from . import db
from .help_texts import H, SRC
from .i18n import OPTIONS, get_lang, opt_codes, opt_label, tr
from .model import TABLES, _coerce_row, empty_row, ensure_ids, normalize

# ----------------------------------------------------------------------------- column labels
LABELS = {
    "id": ("ID", "ID"), "name": ("Nome", "Name"), "type": ("Tipo", "Type"), "text": ("Texto", "Text"),
    "document": ("Documento estratégico", "Strategy document"), "strategic_goal": ("Objetivo estratégico", "Strategic goal"),
    "impact_indicator": ("Indicador de impacto", "Impact indicator"), "baseline": ("Baseline", "Baseline"),
    "target": ("Meta", "Target"), "source": ("Fonte de verificação", "Source of verification"),
    "characteristics": ("Características básicas", "Basic characteristics"),
    "interests": ("Interesses e como é afetado", "Interests & how affected"),
    "capacity_motivation": ("Capacidade e motivação p/ mudança", "Capacity & motivation to change"),
    "possible_actions": ("Ações possíveis", "Possible actions"),
    "benefits_to_project": ("Benefícios para o projeto", "Benefits to the project"),
    "benefits_of_project": ("Benefícios do projeto p/ o stakeholder", "Benefits of the project to the stakeholder"),
    "engagement": ("Atividade/estratégia de envolvimento", "Engagement activity/strategy"),
    "influence": ("Influência (1-5)", "Influence (1-5)"), "interest": ("Interesse (1-5)", "Interest (1-5)"),
    "attitude": ("Atitude", "Attitude"), "target_group": ("Grupo-alvo", "Target group"),
    "perception": ("Perceção (1-5)", "Perception (1-5)"), "opportunity": ("Oportunidade (1-5)", "Opportunity (1-5)"),
    "ability": ("Capacidade (1-5)", "Ability (1-5)"), "motivation": ("Motivação (1-5)", "Motivation (1-5)"),
    "evidence": ("Evidência", "Evidence"), "implication": ("Implicação para o projeto", "Implication for the project"),
    "level": ("Nível", "Level"), "parent": ("Leva a (ID superior)", "Leads to (upper ID)"),
    "objective": ("Objetivo (reformulação positiva)", "Objective (positive statement)"),
    "in_scope": ("No âmbito?", "In scope?"), "code": ("Código", "Code"),
    "source_problem": ("Problema de origem", "Source problem"), "objective_code": ("Objetivo (código)", "Objective (code)"),
    "indicator": ("Indicador", "Indicator"), "unit": ("Unidade", "Unit"), "baseline_year": ("Ano baseline", "Baseline year"),
    "target_year": ("Ano meta", "Target year"), "current": ("Valor atual", "Current value"),
    "frequency": ("Frequência", "Frequency"), "responsible": ("Responsável", "Responsible"),
    "specific": ("S", "S"), "measurable": ("M", "M"), "available": ("A", "A"), "relevant": ("R", "R"), "timely": ("T", "T"),
    "indicator_id": ("Indicador", "Indicator"), "peer": ("Par / referência", "Peer / reference"), "value": ("Valor", "Value"),
    "year": ("Ano", "Year"), "note": ("Nota", "Note"), "important": ("Importante?", "Important?"),
    "holds": ("Vai verificar-se?", "Will it hold?"), "evidence_quality": ("Qualidade da evidência (1-4)", "Evidence quality (1-4)"),
    "redesign_possible": ("Redesenho possível?", "Redesign possible?"), "description": ("Descrição do risco", "Risk description"),
    "likelihood": ("Probabilidade", "Likelihood"), "impact": ("Impacto", "Impact"),
    "target_exposure": ("Exposição-alvo", "Target exposure"), "existing_mitigation": ("Mitigação existente", "Existing mitigation"),
    "proposed_mitigation": ("Mitigação proposta", "Proposed mitigation"), "risk_manager": ("Gestor do risco", "Risk manager"),
    "risk_owner": ("Dono do risco", "Risk owner"), "review_by": ("Rever até (data/evento)", "Review/resolve by"),
    "review": ("Revisão", "Review"), "assumption_id": ("Pressuposto", "Assumption"),
    "level_affected": ("Nível afetado", "Level affected"), "strategy": ("Estratégia", "Strategy"),
    "contingency": ("Contingência (€)", "Contingency (€)"), "preventive_activity": ("Atividade preventiva", "Preventive activity"),
    "output_code": ("Output", "Output"), "predecessors": ("Predecessoras", "Predecessors"),
    "optimistic": ("Otimista (a)", "Optimistic (a)"), "most_likely": ("Mais provável (m)", "Most likely (m)"),
    "pessimistic": ("Pessimista (b)", "Pessimistic (b)"), "cost": ("Custo (€)", "Cost (€)"),
    "distribution": ("Distribuição do custo", "Cost distribution"), "crash_duration": ("Duração crash", "Crash duration"),
    "crash_cost": ("Custo crash (€)", "Crash cost (€)"), "milestone": ("Marco?", "Milestone?"),
    "pct_complete": ("% concluída", "% complete"), "actual_cost": ("Custo real AC (€)", "Actual cost AC (€)"),
    "activity_id": ("Atividade", "Activity"), "category": ("Categoria", "Category"), "item": ("Item", "Item"),
    "quantity": ("Quantidade", "Quantity"), "unit_cost": ("Custo unitário (€)", "Unit cost (€)"), "phase": ("Fase", "Phase"),
    "estimated_cost": ("Custo estimado (€)", "Estimated cost (€)"), "method": ("Método", "Method"),
    "planned_date": ("Data prevista", "Planned date"), "selection_criteria": ("Critérios de seleção", "Selection criteria"),
    "risk": ("Risco", "Risk"), "investment": ("Investimento", "Investment"),
    "operating_costs": ("Custos operacionais", "Operating costs"), "benefits": ("Benefícios / receitas", "Benefits / revenue"),
    "date": ("Data", "Date"), "ev": ("EV acumulado", "Cumulative EV"), "ac": ("AC acumulado", "Cumulative AC"),
    "criterion": ("Critério", "Criterion"), "question": ("Pergunta de avaliação", "Evaluation question"),
    "judgement_criteria": ("Critérios de juízo", "Judgement criteria"), "leads_to": ("Leva a", "Leads to"),
    "assumption": ("Pressuposto (seta)", "Assumption (arrow)"), "weight": ("Peso", "Weight"),
    # implementation & monitoring
    "reviewer": ("Revisto por", "Reviewed by"), "forecast_date": ("Data prevista atualizada", "Forecast date"),
    "actual_date": ("Data real", "Actual date"), "accepted": ("Aceite?", "Accepted?"), "accepted_by": ("Aceite por", "Accepted by"),
    "deviation_cause": ("Causa do desvio", "Cause of deviation"), "corrective_action": ("Ação corretiva", "Corrective action"),
    "element_type": ("Elemento alterado", "Element changed"), "element_ref": ("Referência (ID)", "Reference (ID)"),
    "justification": ("Justificação (necessidade)", "Justification (need)"), "old_value": ("Valor anterior", "Old value"),
    "new_value": ("Novo valor", "New value"), "impact_time": ("Impacto prazo (dias)", "Time impact (days)"),
    "impact_cost": ("Impacto custo (€)", "Cost impact (€)"), "impact_quality": ("Impacto na qualidade/âmbito", "Quality/scope impact"),
    "requested_by": ("Pedido por", "Requested by"), "approval_authority": ("Autoridade de aprovação", "Approval authority"),
    "status": ("Estado", "Status"), "decision_date": ("Data da decisão", "Decision date"), "incident": ("Incidente / ocorrência", "Incident"),
    "delay": ("Atraso (dias)", "Delay (days)"), "cost_impact": ("Impacto no custo (€)", "Cost impact (€)"),
    "affects_relevance": ("Afeta relevância?", "Affects relevance?"), "affects_feasibility": ("Afeta viabilidade?", "Affects feasibility?"),
    "affects_sustainability": ("Afeta sustentabilidade?", "Affects sustainability?"), "action": ("Ação", "Action"),
    "reserve": ("Reserva", "Reserve"), "movement": ("Movimento", "Movement"), "amount": ("Montante (€)", "Amount (€)"),
    "approved_by": ("Aprovado por", "Approved by"), "stakeholder": ("Stakeholder", "Stakeholder"),
    "tool": ("Ferramenta", "Tool"), "next_date": ("Próxima data", "Next date"), "stakeholder_group": ("Grupo de stakeholders", "Stakeholder group"),
    "channel": ("Canal", "Channel"), "about": ("Sobre (atividade/output)", "About (activity/output)"), "feedback": ("Feedback recebido", "Feedback received"),
    "satisfaction": ("Satisfação (1-5)", "Satisfaction (1-5)"), "anonymous": ("Anónimo?", "Anonymous?"),
    "action_taken": ("Resposta / ação tomada", "Response / action taken"), "bidder": ("Concorrente", "Bidder"),
    "compliant": ("Admissível?", "Compliant?"), "technical_score": ("Pontuação técnica (0-100)", "Technical score (0-100)"),
    "price": ("Preço (€)", "Price (€)"), "step": ("Passo", "Step"), "done": ("Feito?", "Done?"),
    "circle": ("Círculo de audiência", "Audience circle"), "audience": ("Audiência", "Audience"),
    "key_message": ("Mensagem-chave", "Key message"), "budget": ("Orçamento (€)", "Budget (€)"), "actual": ("Real", "Actual"),
    "pillar": ("Pilar", "Pillar"), "score": ("Pontuação (1-5)", "Score (1-5)"), "sdg": ("ODS", "SDG"),
    "answer": ("Resposta", "Answer"), "auditor": ("Auditor", "Auditor"), "scope": ("Âmbito", "Scope"),
    "findings": ("Constatações", "Findings"), "recommendations": ("Recomendações", "Recommendations"),
    "result": ("Resultado / produto", "Result / product"), "contributors": ("Contribuidores", "Contributors"),
    "ip_type": ("Tipo de PI", "IP type"), "regime": ("Regime de propriedade", "Ownership regime"),
    "publication_rights": ("Direitos de publicação/uso", "Publication/use rights"), "agreement_ref": ("Acordo (ref.)", "Agreement (ref.)"),
    "lesson": ("Lição aprendida", "Lesson learned"), "recommendation": ("Recomendação", "Recommendation"),
    "practice": ("Boa prática", "Best practice"), "criteria": ("Critérios cumpridos", "Criteria met"),
    "replicability": ("Replicabilidade (1-5)", "Replicability (1-5)"), "validated_by": ("Validada por", "Validated by"),
    "product": ("Produto / conteúdo", "Product / content"), "reach_target": ("Alcance-meta", "Target reach"),
    "reach_actual": ("Alcance real", "Actual reach"), "q_type": ("Tipo de pergunta", "Question type"),
    "data_tools": ("Ferramentas de recolha", "Data collection tools"), "data_type": ("Tipo de dados", "Data type"),
    "scope_certainty": ("Certeza do âmbito", "Scope certainty"), "contract_type": ("Tipo de contrato", "Contract type"),
    "stage": ("Etapa do concurso", "Tender stage"), "tech_weight": ("Peso técnico (0-1)", "Technical weight (0-1)"),
    "awarded_to": ("Adjudicado a", "Awarded to"), "contract_value": ("Valor do contrato (€)", "Contract value (€)"),
    "item_me": ("Item", "Item"),
    "wbs_code": ("Código WBS", "WBS code"), "deliverable": ("Entregável", "Deliverable"),
    "acceptance": ("Critérios de aceitação", "Acceptance criteria"), "owner": ("Responsável", "Owner"),
}

# labels that depend on the table
TABLE_LABELS = {
    ("changes", "description"): ("Descrição da alteração", "Change description"),
    ("funding", "source"): ("Fonte de financiamento", "Funding source"),
    ("ind_reviews", "source"): ("Fonte dos dados", "Data source"),
    ("engagement", "objective"): ("Objetivo", "Objective"), ("comm_plan", "objective"): ("Objetivo de comunicação", "Communication objective"),
    ("comm_plan", "tool"): ("Ferramenta / canal", "Tool / channel"), ("comm_plan", "target"): ("Meta", "Target"),
    ("me_quality", "item"): ("Elemento de qualidade do M&A", "M&E quality element"),
    ("milestones", "name"): ("Marco", "Milestone"), ("wbs", "code"): ("Código WBS", "WBS code"),
    ("wbs", "name"): ("Elemento da WBS", "WBS element"), ("wbs", "type"): ("Tipo de elemento", "Element type"),
    ("wbs", "output_code"): ("Output do quadro lógico", "Logframe output"), ("wbs", "description"): ("Descrição do âmbito", "Scope description"),
    ("wbs", "weight"): ("Peso no elemento-pai (%)", "Weight in parent (%)"), ("audits", "type"): ("Tipo de auditoria", "Audit type"),
    ("lessons", "evidence"): ("Evidência (o que aconteceu)", "Evidence (what happened)"),
    ("funding", "status"): ("Estado", "Status"), ("risk_reviews", "note"): ("Eficácia da mitigação / nota", "Mitigation effectiveness / note"),
    ("sustainability", "indicator"): ("Indicador de sustentabilidade", "Sustainability indicator"),
}


def label(field: str, table: str | None = None) -> str:
    pt, en = TABLE_LABELS.get((table, field)) or LABELS.get(field, (field, field))
    return pt if get_lang() == "pt" else en


# ----------------------------------------------------------------------------- project state
def init_state():
    ss = st.session_state
    ss.setdefault("lang", "pt")
    ss.setdefault("dv", 0)
    ss.setdefault("dirty", False)
    ss.setdefault("autosave", True)
    qp = st.query_params
    if "project" not in ss:
        # restore language and last project after a browser reload (?lang=..&pid=..)
        if qp.get("lang") in ("pt", "en"):
            ss.lang = qp.get("lang")
        loaded = None
        if qp.get("pid"):
            try:
                loaded = db.load_project(int(qp.get("pid")))
            except Exception:
                loaded = None
        if loaded:
            ss.project = normalize(loaded)
            ss.pid = int(qp.get("pid"))
        else:
            from .demos import build_demo
            ss.project = normalize(build_demo("trade"))
            ss.pid = None
    sync_query()


def sync_query():
    try:
        qp = st.query_params
        if qp.get("lang") != st.session_state.lang:
            qp["lang"] = st.session_state.lang
        pid = st.session_state.get("pid")
        if pid and qp.get("pid") != str(pid):
            qp["pid"] = str(pid)
        if not pid and "pid" in qp:
            del qp["pid"]
    except Exception:
        pass


def P() -> dict:
    return st.session_state.project


def set_project(p: dict, pid: int | None = None):
    st.session_state.project = normalize(p)
    st.session_state.pid = pid
    st.session_state.dv += 1
    st.session_state.dirty = False


def bump():
    """Call after an external change to the project (import, AI, generators) so editors reload."""
    st.session_state.dv += 1
    st.session_state.dirty = True


def mark_dirty():
    st.session_state.dirty = True


def save(silent: bool = False):
    try:
        pid = db.save_project(P(), st.session_state.get("pid"))
        st.session_state.pid = pid
        st.session_state.dirty = False
        if not silent:
            st.toast(tr("Projeto guardado na base de dados ✅", "Project saved to the database ✅"))
    except Exception as e:  # pragma: no cover
        st.error(tr(f"Erro ao guardar: {e}", f"Error saving: {e}"))


def autosave():
    ss = st.session_state
    if ss.get("dirty") and ss.get("autosave") and ss.get("pid"):
        save(silent=True)


# ----------------------------------------------------------------------------- editable tables
def _colcfg(field: str, kind: str, overrides: dict | None = None, table: str | None = None):
    cc = st.column_config
    lab = label(field, table)
    ov = (overrides or {}).get(field)
    if ov is not None:
        return ov
    if kind.startswith("sel:"):
        name = kind[4:]
        return cc.SelectboxColumn(lab, options=opt_codes(name), format_func=lambda c, n=name: opt_label(n, c))
    if kind == "scale5":
        return cc.NumberColumn(lab, min_value=1, max_value=5, step=1, format="%d")
    if kind == "scale4":
        if field in ("likelihood", "impact"):
            return cc.SelectboxColumn(lab, options=[4, 3, 2, 1], format_func=lambda c, n=field: opt_label(n, c))
        return cc.NumberColumn(lab, min_value=1, max_value=4, step=1, format="%d")
    if kind == "bool":
        return cc.CheckboxColumn(lab)
    if kind == "num":
        return cc.NumberColumn(lab, format="%.2f" if field not in ("cost", "actual_cost", "crash_cost", "estimated_cost", "unit_cost", "contingency", "investment", "operating_costs", "benefits", "ev", "ac", "amount", "price", "budget", "cost_impact", "impact_cost", "contract_value") else "%.0f")
    if kind == "int":
        return cc.NumberColumn(lab, step=1, format="%d")
    if kind == "long":
        return cc.TextColumn(lab, width="large")
    return cc.TextColumn(lab, width="small" if field in ("id", "code") else "medium")


def _clean_val(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    return v


def edit_table(table: str, *, columns: list[str] | None = None, key: str = "", height: int | None = None,
               filt=None, fixed: dict | None = None, overrides: dict | None = None, num_rows: str = "dynamic",
               disabled: list[str] | None = None, store: str | None = None) -> list[dict]:
    """Editable table bound to project[store or table]. `filt` edits only a subset of rows."""
    p = P()
    store = store or table
    spec = TABLES[table]
    kinds = {f: k for f, k, _ in spec}
    cols = columns or [f for f, _, _ in spec]
    all_rows = p.get(store, [])
    sub = [r for r in all_rows if (filt(r) if filt else True)]
    others = [r for r in all_rows if not (filt(r) if filt else True)]
    # The editor's input frame is rebuilt only when the data changed outside this editor
    # (other page, import, AI, generators); otherwise Streamlit keeps the user's in-progress edits.
    root = f"{store}_{key}"
    reg = st.session_state.setdefault("_editors", {}).setdefault(root, {"ver": 0, "dv": -1, "src": None, "out": None})
    cur = _h(sub)
    if reg["dv"] != st.session_state.dv or (cur != reg["src"] and cur != reg["out"]):
        reg["ver"] += 1
        reg["dv"] = st.session_state.dv
        reg["src"] = cur
        st.session_state.pop(f"base_{root}_{reg['ver'] - 1}", None)
    base_key = f"base_{root}_{reg['ver']}"
    if base_key not in st.session_state:
        df = pd.DataFrame([{c: r.get(c) for c in cols} for r in sub], columns=cols)
        for c in cols:
            k = kinds.get(c, "text")
            if k in ("text", "long") or k.startswith("sel:"):
                df[c] = df[c].astype("object")
            elif k == "bool":
                df[c] = df[c].fillna(False).astype(bool)
            elif k in ("num",):
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
            elif k in ("int", "scale5", "scale4"):
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        st.session_state[base_key] = df
    cfg = {c: _colcfg(c, kinds.get(c, "text"), overrides, table) for c in cols}
    edited = st.data_editor(st.session_state[base_key], key=f"ed_{base_key}", num_rows=num_rows, hide_index=True,
                            column_config=cfg, height=height or "auto", width="stretch", disabled=disabled or False)
    rows = []
    recs = edited.to_dict("records")
    kf = "id" if "id" in kinds else ("code" if "code" in kinds else None)
    for pos, rec in enumerate(recs):
        rec = {k: _clean_val(v) for k, v in rec.items()}
        if not any(v not in (None, "", False) for k, v in rec.items()):
            continue
        # keep hidden columns of existing rows (matched by id/code, else by position when nothing was added or removed)
        orig = next((r for r in sub if kf and rec.get(kf) and str(r.get(kf)) == str(rec.get(kf))), None)
        if orig is None and len(recs) == len(sub) and pos < len(sub):
            orig = sub[pos]
        row = copy.deepcopy(orig) if orig else empty_row(table)
        for k, v in rec.items():
            row[k] = v
        if fixed:
            row.update(fixed)
        rows.append(_coerce_row(table, row))
    if "id" in kinds:
        rows = ensure_ids(others + rows, table)[len(others):]
    new_all = others + rows
    reg["out"] = _h(rows)
    if _h(new_all) != _h(all_rows):
        p[store] = new_all
        mark_dirty()
    return rows


def _h(rows) -> str:
    return json.dumps(rows, default=str, sort_keys=True)


# ----------------------------------------------------------------------------- presentation
def header(pt: str, en: str, help_key: str | None = None, icon: str = ""):
    st.title(f"{icon} {tr(pt, en)}".strip())
    st.session_state["_fig_page"] = tr(pt, en)
    st.session_state["_fig_n"] = 0
    m = P()["meta"]
    st.caption(f"📁 **{m.get('name', '')}** · {m.get('industry', '')}")
    if help_key:
        help_panel(help_key)


def help_panel(key: str, expanded: bool = False):
    h = H.get(key)
    if not h:
        return
    what, how, srcs = h[get_lang()]
    with st.expander(tr("ℹ️ Legenda — o que é, como se lê e fontes", "ℹ️ Legend — what it is, how to read it, sources"), expanded=expanded):
        st.markdown(f"**{tr('O que é', 'What it is')}.** {what}")
        st.markdown(f"**{tr('Como se lê', 'How to read it')}.** {how}")
        st.markdown(f"**{tr('Fontes', 'Sources')}:**\n" + "\n".join(f"- {SRC[s]}" for s in srcs))


def interpret(text: str, title: str | None = None):
    if not text:
        return
    with st.container(border=True):
        st.markdown(f"**🧭 {title or tr('Interpretação automática', 'Automatic interpretation')}**")
        st.markdown(text)


VIZ_JS = "https://cdn.jsdelivr.net/npm/@viz-js/viz@3.14.0/lib/viz-standalone.js"
H2I_JS = "https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.js"


def _fig_name(title: str | None = None) -> str:
    """Meaningful file / tooltip name: '<project> - <page> - <n>'."""
    st.session_state["_fig_n"] = st.session_state.get("_fig_n", 0) + 1
    base = title or st.session_state.get("_fig_page") or "figura"
    n = st.session_state["_fig_n"]
    return f"{base}" + (f" {n}" if not title and n > 1 else "")


def _named_dot(dot: str, name: str) -> str:
    """Give the graph a meaningful name: the browser shows it as the SVG tooltip (instead of a bare 'G')."""
    import re
    safe = name.replace('"', "'")
    return re.sub(r"^\s*(strict\s+)?(di)?graph\s+(\w+|\"[^\"]*\")?\s*\{", lambda m_: f'{m_.group(1) or ""}{m_.group(2) or ""}graph "{safe}" {{', dot, count=1)


def graph(dot: str, height: int | None = None, title: str | None = None):
    """Graphviz diagram + export buttons (PNG 3×, SVG, DOT) rendered in the browser (works on Render without Graphviz installed)."""
    name = _fig_name(title)
    dot = _named_dot(dot, name)
    try:
        st.graphviz_chart(dot, width="stretch")
    except Exception as e:  # pragma: no cover
        st.warning(f"Graphviz: {e}")
        st.code(dot)
        return
    export_buttons_dot(dot, name)


def _file_base(name: str) -> str:
    proj = _slug(P()["meta"].get("name", "projeto"))[:45].strip("_")
    return f"{proj}_{_slug(name)[:45].strip('_')}"


_BTN_CSS = """<style>body{margin:0;font-family:'Source Sans Pro',Helvetica,Arial,sans-serif}
.b{display:inline-block;margin:2px 6px 2px 0;padding:5px 11px;border:1px solid #c9d2db;border-radius:8px;background:#fff;color:#1F2933;font-size:13px;cursor:pointer}
.b:hover{border-color:#1F6FB2;color:#1F6FB2}.m{font-size:12px;color:#7a8794;margin-left:4px}</style>"""


def export_buttons_dot(dot: str, name: str):
    import streamlit.components.v1 as components
    fb = _file_base(name)
    lab = {"png": tr("⬇️ PNG (alta resolução)", "⬇️ PNG (high resolution)"), "svg": tr("⬇️ SVG (vetorial)", "⬇️ SVG (vector)"), "dot": "⬇️ DOT",
           "tip": tr("para PowerPoint/Word", "for PowerPoint/Word"), "wait": tr("a preparar…", "preparing…")}
    html_ = f"""{_BTN_CSS}<div><button class="b" id="png">{lab['png']}</button><button class="b" id="svg">{lab['svg']}</button>
<button class="b" id="dot">{lab['dot']}</button><span class="m" id="msg">{lab['tip']}</span></div>
<script src="{VIZ_JS}"></script><script>
const DOT = {json.dumps(dot)}; const FB = {json.dumps(fb)};
function save(blob, ext){{const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=FB+'.'+ext;document.body.appendChild(a);a.click();setTimeout(()=>{{URL.revokeObjectURL(a.href);a.remove();}},1500);}}
async function svgText(){{const viz=await Viz.instance();const el=viz.renderSVGElement(DOT);el.setAttribute('xmlns','http://www.w3.org/2000/svg');return [new XMLSerializer().serializeToString(el), el];}}
document.getElementById('svg').onclick=async()=>{{const [t]=await svgText();save(new Blob([t],{{type:'image/svg+xml'}}),'svg');}};
document.getElementById('dot').onclick=()=>save(new Blob([DOT],{{type:'text/vnd.graphviz'}}),'dot');
document.getElementById('png').onclick=async()=>{{const msg=document.getElementById('msg');msg.textContent={json.dumps(lab['wait'])};
 const [t,el]=await svgText();const w=parseFloat(el.getAttribute('width'))*96/72, h=parseFloat(el.getAttribute('height'))*96/72, k=3;
 const img=new Image();img.onload=()=>{{const c=document.createElement('canvas');c.width=Math.round(w*k);c.height=Math.round(h*k);const g=c.getContext('2d');
  g.fillStyle='#fff';g.fillRect(0,0,c.width,c.height);g.drawImage(img,0,0,c.width,c.height);c.toBlob(b=>{{save(b,'png');msg.textContent={json.dumps(lab['tip'])};}},'image/png');}};
 img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(t);}};
</script>"""
    components.html(html_, height=70)


def export_buttons_html(html_body: str, title: str | None = None, width: int = 1400):
    """'📷 Export as PNG' for an HTML block (e.g. the logframe matrices): rasterised in the browser at 2×."""
    import streamlit.components.v1 as components
    name = _fig_name(title)
    fb = _file_base(name)
    lab = {"png": tr("📷 Exportar como PNG", "📷 Export as PNG"), "tip": tr("imagem da matriz para apresentações", "image of the matrix for presentations"),
           "wait": tr("a preparar…", "preparing…")}
    html_ = f"""{_BTN_CSS}<div><button class="b" id="png">{lab['png']}</button><span class="m" id="msg">{lab['tip']}</span></div>
<div id="cap" style="position:absolute;left:-20000px;top:0;width:{width}px;background:#fff;padding:16px;font-family:'Source Sans Pro',Helvetica,Arial,sans-serif">{html_body}</div>
<script src="{H2I_JS}"></script><script>
const FB={json.dumps(fb)};
document.getElementById('png').onclick=async()=>{{const msg=document.getElementById('msg');msg.textContent={json.dumps(lab['wait'])};
 const node=document.getElementById('cap');node.style.left='0px';
 try{{const url=await htmlToImage.toPng(node,{{pixelRatio:2,backgroundColor:'#ffffff'}});const a=document.createElement('a');a.href=url;a.download=FB+'.png';document.body.appendChild(a);a.click();a.remove();}}
 finally{{node.style.left='-20000px';msg.textContent={json.dumps(lab['tip'])};}}}};
</script>"""
    components.html(html_, height=44)


def plotly_defaults() -> None:
    """All Plotly charts: camera button downloads a PNG at 3× (≈300 dpi on A4) with a meaningful file name; no Plotly logo."""
    from streamlit.delta_generator import DeltaGenerator
    if getattr(DeltaGenerator.plotly_chart, "_pm_patched", False):
        return
    orig = DeltaGenerator.plotly_chart

    def patched(self, figure_or_data, *args, config=None, **kwargs):
        try:
            t = figure_or_data.layout.title.text if hasattr(figure_or_data, "layout") else None
        except Exception:
            t = None
        name = _fig_name(t or None)
        cfg = {"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 3, "filename": _file_base(name)}}
        cfg.update(config or {})
        return orig(self, figure_or_data, *args, config=cfg, **kwargs)
    patched._pm_patched = True
    DeltaGenerator.plotly_chart = patched
    try:                      # st.plotly_chart is a method bound to the main container at import time
        st.plotly_chart = patched.__get__(st._main, DeltaGenerator)
    except Exception:
        pass


def download_json_button():
    p = P()
    st.download_button(tr("⬇️ Descarregar projeto (JSON)", "⬇️ Download project (JSON)"),
                       data=json.dumps(p, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
                       file_name=f"{_slug(p['meta'].get('name', 'projeto'))}.json", mime="application/json")


def _slug(s: str) -> str:
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:60] or "projeto"


def options_list(name: str):
    return OPTIONS[name]


def code_options(rows: list[dict], field: str = "id", label_field: str | None = None) -> list[str]:
    return [str(r.get(field)) for r in rows if r.get(field)]


# ----------------------------------------------------------------------------- AI helpers used across pages
def ai_text(label_pt: str, label_en: str, key: str, fn, *, help_pt: str = "", help_en: str = ""):
    """Button that runs a text-producing agent function and shows/keeps the result (with download)."""
    from . import agent as AG
    if not AG.available():
        st.caption(tr("🤖 Agente IA indisponível — defina ANTHROPIC_API_KEY.", "🤖 AI agent unavailable — set ANTHROPIC_API_KEY."))
        return
    if st.button(f"🤖 {tr(label_pt, label_en)}", key=f"ai_btn_{key}", help=tr(help_pt, help_en) or None):
        with st.spinner(tr("O agente está a trabalhar… (pode demorar 1–3 min)", "The agent is working… (may take 1–3 min)")):
            try:
                st.session_state[f"ai_{key}"] = fn()
            except Exception as e:
                st.error(tr(f"Erro do agente: {e}", f"Agent error: {e}"))
    txt = st.session_state.get(f"ai_{key}")
    if txt:
        with st.container(border=True):
            st.markdown(txt)
        st.download_button(tr("⬇️ Descarregar (Markdown)", "⬇️ Download (Markdown)"), txt.encode("utf-8"), f"{key}.md", "text/markdown", key=f"ai_dl_{key}")


def ai_tables(label_pt: str, label_en: str, key: str, fn, after=None):
    """Button that runs a table-producing agent function, previews the draft and lets the user apply it."""
    from . import agent as AG
    if not AG.available():
        st.caption(tr("🤖 Agente IA indisponível — defina ANTHROPIC_API_KEY.", "🤖 AI agent unavailable — set ANTHROPIC_API_KEY."))
        return
    if st.button(f"🤖 {tr(label_pt, label_en)}", key=f"ai_btn_{key}"):
        with st.spinner(tr("O agente está a trabalhar… (pode demorar 1–3 min)", "The agent is working… (may take 1–3 min)")):
            try:
                st.session_state[f"ai_{key}"] = fn()
            except Exception as e:
                st.error(tr(f"Erro do agente: {e}", f"Agent error: {e}"))
    data = st.session_state.get(f"ai_{key}")
    if data:
        with st.container(border=True):
            st.markdown(tr("**Rascunho do agente** (reveja antes de aplicar)", "**Agent draft** (review before applying)"))
            for t, rows in data.items():
                if isinstance(rows, list) and rows:
                    st.caption(t)
                    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            c1, c2, c3 = st.columns(3)
            if c1.button(tr("✅ Acrescentar", "✅ Append"), key=f"ai_app_{key}"):
                AG.apply(P(), data, "append")
                if after:
                    after(P())
                st.session_state.pop(f"ai_{key}", None)
                bump()
                st.rerun()
            if c2.button(tr("♻️ Substituir", "♻️ Replace"), key=f"ai_rep_{key}"):
                AG.apply(P(), data, "replace")
                if after:
                    after(P())
                st.session_state.pop(f"ai_{key}", None)
                bump()
                st.rerun()
            if c3.button(tr("🗑️ Descartar", "🗑️ Discard"), key=f"ai_del_{key}"):
                st.session_state.pop(f"ai_{key}", None)
                st.rerun()
