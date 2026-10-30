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
}


def label(field: str) -> str:
    pt, en = LABELS.get(field, (field, field))
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
def _colcfg(field: str, kind: str, overrides: dict | None = None):
    cc = st.column_config
    lab = label(field)
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
        return cc.NumberColumn(lab, format="%.2f" if field not in ("cost", "actual_cost", "crash_cost", "estimated_cost", "unit_cost", "contingency", "investment", "operating_costs", "benefits", "ev", "ac") else "%.0f")
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
    cfg = {c: _colcfg(c, kinds.get(c, "text"), overrides) for c in cols}
    edited = st.data_editor(st.session_state[base_key], key=f"ed_{base_key}", num_rows=num_rows, hide_index=True,
                            column_config=cfg, height=height or "auto", width="stretch", disabled=disabled or False)
    rows = []
    for rec in edited.to_dict("records"):
        rec = {k: _clean_val(v) for k, v in rec.items()}
        if not any(v not in (None, "", False) for k, v in rec.items()):
            continue
        # keep hidden columns of existing rows
        orig = next((r for r in sub if rec.get("id") and str(r.get("id")) == str(rec.get("id"))), None)
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


def graph(dot: str, height: int | None = None):
    try:
        st.graphviz_chart(dot, width="stretch")
    except Exception as e:  # pragma: no cover
        st.warning(f"Graphviz: {e}")
        st.code(dot)


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
