"""Project data model.

A project is a single JSON-serialisable dict. Every tabular module is a list of row dicts whose
columns are declared in TABLES (used by the editors, Excel import/export and the AI agent).
"""
from __future__ import annotations

import copy
import re
from datetime import date

SCHEMA_VERSION = 1

# column spec: (field, kind, default)   kind: text | long | num | int | bool | sel:<option> | scale5 | scale4
TABLES: dict[str, list[tuple]] = {
    "policy_goals": [("id", "text", ""), ("document", "text", ""), ("strategic_goal", "long", ""),
                     ("impact_indicator", "text", ""), ("baseline", "text", ""), ("target", "text", ""),
                     ("source", "text", "")],
    "stakeholders": [("id", "text", ""), ("name", "text", ""), ("type", "sel:stakeholder_type", "Beneficiary"),
                     ("characteristics", "long", ""), ("interests", "long", ""),
                     ("capacity_motivation", "long", ""), ("possible_actions", "long", ""),
                     ("benefits_to_project", "long", ""), ("benefits_of_project", "long", ""),
                     ("engagement", "sel:engagement", "Consult"), ("influence", "scale5", 3),
                     ("interest", "scale5", 3), ("attitude", "sel:attitude", "Neutral")],
    "behaviour": [("id", "text", ""), ("target_group", "text", ""), ("perception", "scale5", 3),
                  ("opportunity", "scale5", 3), ("ability", "scale5", 3), ("motivation", "scale5", 3),
                  ("evidence", "long", ""), ("implication", "long", "")],
    "problems": [("id", "text", ""), ("text", "long", ""), ("level", "sel:problem_level", "Cause"),
                 ("parent", "text", ""), ("objective", "long", ""), ("in_scope", "bool", True)],
    "objectives": [("code", "text", ""), ("level", "sel:level", "Output"), ("text", "long", ""),
                   ("parent", "text", ""), ("source_problem", "text", "")],
    "indicators": [("id", "text", ""), ("objective_code", "text", ""), ("indicator", "long", ""),
                   ("unit", "text", ""), ("baseline", "num", None), ("baseline_year", "int", None),
                   ("target", "num", None), ("target_year", "int", None), ("current", "num", None),
                   ("source", "long", ""), ("frequency", "text", ""), ("responsible", "text", ""),
                   ("specific", "bool", False), ("measurable", "bool", False), ("available", "bool", False),
                   ("relevant", "bool", False), ("timely", "bool", False)],
    "benchmarks": [("indicator_id", "text", ""), ("peer", "text", ""), ("value", "num", None),
                   ("year", "int", None), ("note", "text", "")],
    "timeseries": [("indicator_id", "text", ""), ("year", "int", None), ("value", "num", None)],
    "assumptions": [("id", "text", ""), ("type", "sel:assumption_type", "Operational"),
                    ("objective_code", "text", ""), ("text", "long", ""), ("important", "bool", True),
                    ("holds", "sel:holds", "Possibly"), ("evidence", "long", ""),
                    ("evidence_quality", "scale4", 2), ("redesign_possible", "bool", False)],
    "risks": [("id", "text", ""), ("type", "sel:risk_type", "Project/programme delivery"),
              ("description", "long", ""), ("likelihood", "scale4", 2), ("impact", "scale4", 2),
              ("target_exposure", "int", 4), ("existing_mitigation", "long", ""),
              ("proposed_mitigation", "long", ""), ("risk_manager", "text", ""), ("risk_owner", "text", ""),
              ("review_by", "text", ""), ("review", "long", ""), ("assumption_id", "text", ""),
              ("level_affected", "sel:level", "Output"), ("strategy", "sel:risk_strategy", "Reduce"),
              ("contingency", "num", 0.0), ("preventive_activity", "text", "")],
    "activities": [("id", "text", ""), ("name", "text", ""), ("output_code", "text", ""),
                   ("type", "sel:activity_type", "Production"), ("predecessors", "text", ""),
                   ("optimistic", "num", 1.0), ("most_likely", "num", 1.0), ("pessimistic", "num", 1.0),
                   ("cost", "num", 0.0), ("distribution", "sel:distribution", "Uniform"),
                   ("responsible", "text", ""), ("crash_duration", "num", None), ("crash_cost", "num", None),
                   ("milestone", "bool", False), ("pct_complete", "num", 0.0), ("actual_cost", "num", 0.0)],
    "budget": [("id", "text", ""), ("activity_id", "text", ""), ("category", "sel:cost_category", "Fees & Direct Expenses"),
               ("item", "text", ""), ("unit", "text", ""), ("quantity", "num", 1.0), ("unit_cost", "num", 0.0),
               ("phase", "sel:phase", "Implementation")],
    "procurement": [("id", "text", ""), ("item", "text", ""), ("category", "sel:proc_category", "Services"),
                    ("activity_id", "text", ""), ("estimated_cost", "num", 0.0),
                    ("method", "sel:procurement", "Request for Quotations (RFQ)"), ("planned_date", "text", ""),
                    ("responsible", "text", ""), ("selection_criteria", "long", ""), ("risk", "long", "")],
    "cashflows": [("year", "int", 0), ("investment", "num", 0.0), ("operating_costs", "num", 0.0),
                  ("benefits", "num", 0.0), ("note", "text", "")],
    "tracking": [("date", "text", ""), ("ev", "num", None), ("ac", "num", None), ("note", "text", "")],
    "evaluation": [("id", "text", ""), ("criterion", "text", "Relevance"), ("question", "long", ""),
                   ("judgement_criteria", "long", ""), ("indicator", "long", ""), ("source", "long", ""),
                   ("method", "text", "")],
    "preconditions": [("id", "text", ""), ("text", "long", ""), ("leads_to", "text", ""), ("assumption", "long", "")],
    "strategy_criteria": [("criterion", "text", ""), ("weight", "num", 1.0)],
}

ID_PREFIX = {"policy_goals": "G", "stakeholders": "S", "behaviour": "B", "problems": "P", "indicators": "I",
             "assumptions": "H", "risks": "R", "activities": "A", "budget": "L", "procurement": "Q",
             "evaluation": "E", "preconditions": "C"}

DEFAULT_QUALITY = {}

DAC_CRITERIA = ["Relevance", "Coherence", "Effectiveness", "Efficiency", "Impact", "Sustainability"]


def empty_row(table: str) -> dict:
    return {f: copy.deepcopy(d) for f, _k, d in TABLES[table]}


def new_project(name: str = "Novo projeto", industry: str = "") -> dict:
    today = date.today().replace(day=1).isoformat()
    return {
        "schema": SCHEMA_VERSION,
        "meta": {"name": name, "industry": industry, "organisation": "", "sponsor": "", "country": "",
                 "description": "", "manager": "", "start_date": today, "currency": "EUR", "time_unit": "weeks",
                 "duration_mode": "pert", "status_date": today, "target_duration": None,
                 "contingency_method": "percent", "contingency_pct": 0.10, "contingency_used": 0.0,
                 "period": "month"},
        "policy": {"context": "", "content": "", "consequences": ""},
        "policy_goals": [], "stakeholders": [], "behaviour": [], "problems": [],
        "strategies": {"criteria": [{"criterion": "Relevância / Relevance", "weight": 3},
                                    {"criterion": "Viabilidade técnica / Technical feasibility", "weight": 2},
                                    {"criterion": "Custo-benefício / Cost-benefit", "weight": 2},
                                    {"criterion": "Sustentabilidade / Sustainability", "weight": 2},
                                    {"criterion": "Capacidade institucional / Institutional capacity", "weight": 1}],
                       "options": [], "selected": ""},
        "objectives": [], "indicators": [], "benchmarks": [], "timeseries": [], "assumptions": [],
        "toc": {"vision": "", "context": "", "actors": "", "strategic_choices": "", "learning": ""},
        "preconditions": [], "risks": [], "activities": [], "raci": {"roles": ["Gestor de projeto", "Equipa técnica", "Patrocinador", "Parceiro"], "matrix": {}},
        "budget": [], "procurement": [],
        "finance": {"equity": 600000.0, "debt": 400000.0, "ke_method": "capm", "ke": 0.10, "rf": 0.03,
                    "beta": 1.1, "mrp": 0.06, "kd": 0.05, "tax": 0.21, "residual_value": 0.0,
                    "reinvest_rate": None, "finance_rate": None, "rate_override": None,
                    "include_contingency": True},
        "logframe": {"preconditions": "", "terminology": "pcm"}, "cashflows": [], "pert_scenarios": [], "tracking": [], "evaluation": [], "quality": {}, "baseline": None,
    }


def normalize(p: dict) -> dict:
    """Fill in any missing keys / columns so older or AI-generated projects never break the app."""
    base = new_project()
    out = copy.deepcopy(p) if p else base
    for k, v in base.items():
        if k not in out or out[k] is None and v is not None:
            out[k] = copy.deepcopy(v)
        elif isinstance(v, dict) and isinstance(out.get(k), dict) and k not in ("quality",):
            for kk, vv in v.items():
                out[k].setdefault(kk, copy.deepcopy(vv))
    for t, cols in TABLES.items():
        if t == "strategy_criteria":
            continue
        rows = out.get(t) or []
        clean = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            row = empty_row(t)
            row.update({k: v for k, v in r.items() if k in row})
            clean.append(_coerce_row(t, row))
        out[t] = clean
    out["raci"].setdefault("roles", [])
    out["raci"].setdefault("matrix", {})
    out["strategies"].setdefault("options", [])
    return out


def _coerce_row(table: str, row: dict) -> dict:
    for f, kind, d in TABLES[table]:
        v = row.get(f)
        if v is None or (isinstance(v, float) and v != v):  # None or NaN
            row[f] = copy.deepcopy(d)
            continue
        try:
            if kind == "num":
                row[f] = float(v) if v != "" else d
            elif kind in ("int", "scale5", "scale4"):
                row[f] = int(float(v)) if v != "" else d
            elif kind.startswith("sel:"):
                from .i18n import OPTIONS
                opts = OPTIONS[kind[4:]]
                sv = str(v).strip()
                match = next((o[0] for o in opts if sv.lower() in (str(o[0]).lower(), str(o[-1]).lower())), None)
                row[f] = match if match is not None else d
            elif kind == "bool":
                row[f] = bool(v) if not isinstance(v, str) else v.strip().lower() in ("1", "true", "yes", "sim", "x")
            else:
                row[f] = str(v)
        except Exception:
            row[f] = copy.deepcopy(d)
    return row


def next_id(rows: list[dict], prefix: str, field: str = "id") -> str:
    n = 0
    for r in rows:
        m = re.match(rf"^{re.escape(prefix)}(\d+)$", str(r.get(field, "")))
        if m:
            n = max(n, int(m.group(1)))
    return f"{prefix}{n + 1}"


def ensure_ids(rows: list[dict], table: str) -> list[dict]:
    prefix = ID_PREFIX.get(table)
    if not prefix:
        return rows
    seen = set()
    for r in rows:
        rid = str(r.get("id") or "").strip()
        if not rid or rid in seen:
            r["id"] = next_id(rows, prefix)
            rid = r["id"]
        seen.add(rid)
    return rows


def activity_cost(p: dict, act: dict) -> float:
    """BAC of an activity: sum of its budget lines if any, else its manual cost."""
    lines = [b for b in p.get("budget", []) if str(b.get("activity_id")) == str(act.get("id"))]
    if lines:
        return float(sum((b.get("quantity") or 0) * (b.get("unit_cost") or 0) for b in lines))
    return float(act.get("cost") or 0)


def objective_level(p: dict, code: str) -> str:
    for o in p.get("objectives", []):
        if str(o.get("code")) == str(code):
            return o.get("level", "")
    return ""


def expected_assumption_type(level: str) -> str:
    """Professor's equations: Outputs = Activities + Operational; Outcomes = Outputs + Behavioural;
    Impacts = Outcomes + Political. An assumption is linked to the level it CONDITIONS (the result it
    leads to); in the logframe matrix it is shown on the row immediately below (PCM convention)."""
    return {"Output": "Operational", "Outcome": "Behavioural", "Impact": "Political"}.get(level, "")


MATRIX_ROW_OF_ASSUMPTION = {"Output": "Activity", "Outcome": "Output", "Impact": "Outcome"}


def indicator_dimension(level: str) -> str:
    return {"Input": "Efficiency", "Output": "Efficiency", "Outcome": "Effectiveness",
            "Impact": "Impact & Sustainability"}.get(level, "")
