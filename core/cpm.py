"""Critical Path Method, PERT, Monte Carlo simulation and time-cost trade-off (crashing).

All functions are pure (no Streamlit) so they can be unit-tested.
Activities are dicts with at least: id, predecessors ("A, B"), optimistic, most_likely, pessimistic.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict, deque

import numpy as np
from scipy import stats
from scipy.optimize import linprog


# ----------------------------------------------------------------------------- parsing / validation
def parse_preds(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = re.split(r"[,;\s]+", str(value))
    return [str(i).strip() for i in items if str(i).strip() and str(i).strip().lower() not in ("nan", "none", "-")]


def pert_te(a, m, b) -> float:
    a, m, b = _num(a), _num(m), _num(b)
    return (a + 4 * m + b) / 6.0


def pert_var(a, b) -> float:
    a, b = _num(a), _num(b)
    return ((b - a) / 6.0) ** 2


def _num(v, default=0.0) -> float:
    try:
        f = float(v)
        return default if math.isnan(f) else f
    except Exception:
        return default


def _truthy(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "sim", "yes", "s", "y", "x", "loe")
    return bool(v) and v == v


def loe_ids(acts: list[dict]) -> set:
    """Level-of-effort (LOE / hammock) activities: continuous support work (project management, M&E…) whose duration is
    DERIVED from the discrete work it supports — from the finish of its predecessors (or the project start) to the end of the
    project. They never drive the critical path (PMI PMBOK / Practice Standard for Scheduling; Primavera 'Level of Effort').
    If every activity were LOE there would be nothing to derive from, so they are then treated as normal activities."""
    ids = {a["id"] for a in acts if _truthy(a.get("loe"))}
    return ids if len(ids) < len(acts) else set()


LOE_TYPES = ("Support - Management", "Support - M&E")


def loe_candidates(acts: list[dict], res: dict) -> list[str]:
    """Continuous support activities (management, M&E) treated as discrete work that DRIVE the critical path because their
    typed-in duration is longer than (or as long as) the production chain: they should be LOE, otherwise the critical path is
    artificial and every production activity shows a float it does not really have."""
    T = res.get("duration") or 0
    out = []
    for a in acts:
        t = res["table"].get(a["id"], {})
        if a.get("type") in LOE_TYPES and not _truthy(a.get("loe")) and t.get("critical") and T > 0 and t.get("D", 0) >= 0.6 * T:
            out.append(a["id"])
    return out


LOE_HELP = (
    "Esforço contínuo (LOE, level of effort / hammock): trabalho de apoio que acompanha o projeto (gestão, monitorização e avaliação) e não produz um "
    "entregável próprio. A duração é DERIVADA: vai do fim das predecessoras (ou do início) até ao fim do trabalho discreto, por isso estica e encolhe com ele "
    "e nunca define o caminho crítico. Sem esta marcação, uma atividade de gestão com duração escrita igual ou maior do que a cadeia de produção passa a ser "
    "o caminho crítico e todas as atividades de produção ganham uma folga fictícia (o atraso numa obra deixa de 'atrasar' o projeto). "
    "Não pode ser predecessora de outra atividade, não entra no Monte Carlo nem na compressão (crashing); o custo distribui-se pela duração derivada.",
    "Level of effort (LOE / hammock): support work that accompanies the project (management, monitoring & evaluation) and produces no deliverable of its own. "
    "Its duration is DERIVED: from the finish of its predecessors (or the start) to the end of the discrete work, so it stretches and shrinks with it and "
    "never defines the critical path. Without this flag, a management activity whose typed-in duration is as long as (or longer than) the production chain "
    "becomes the critical path and every production activity gets a fictitious float (a delay in the works no longer 'delays' the project). "
    "It cannot be a predecessor, is not sampled in Monte Carlo nor crashed; its cost is spread over the derived duration.")


def durations(acts: list[dict], mode: str = "pert") -> dict[str, float]:
    out = {}
    for a in acts:
        o, m, p = _num(a.get("optimistic")), _num(a.get("most_likely")), _num(a.get("pessimistic"))
        if mode == "ml":
            out[a["id"]] = m
        else:
            out[a["id"]] = pert_te(o, m, p) if (o or p) else m
    return out


def validate(acts: list[dict]) -> list[str]:
    """Return a list of human-readable problems (empty list = valid network)."""
    errors = []
    ids = [str(a.get("id", "")).strip() for a in acts]
    seen = set()
    for i in ids:
        if not i:
            errors.append("Activity without ID / Atividade sem ID")
        elif i in seen:
            errors.append(f"Duplicated ID / ID duplicado: {i}")
        seen.add(i)
    idset = set(ids)
    for a in acts:
        for p in parse_preds(a.get("predecessors")):
            if p not in idset:
                errors.append(f"{a.get('id')}: unknown predecessor / predecessora desconhecida '{p}'")
            if p == a.get("id"):
                errors.append(f"{a.get('id')}: depends on itself / depende de si própria")
        o, m, pe = _num(a.get("optimistic")), _num(a.get("most_likely")), _num(a.get("pessimistic"))
        if (o or pe) and not (o <= m <= pe):
            errors.append(f"{a.get('id')}: must satisfy optimistic ≤ most likely ≤ pessimistic / deve cumprir otimista ≤ mais provável ≤ pessimista")
        if m < 0 or o < 0:
            errors.append(f"{a.get('id')}: negative duration / duração negativa")
    loe = loe_ids(acts)
    for a in acts:
        for p in parse_preds(a.get("predecessors")):
            if p in loe:
                errors.append(f"{a.get('id')}: LOE activity '{p}' cannot be a predecessor (its duration depends on the others) / "
                              f"a atividade LOE '{p}' não pode ser predecessora (a sua duração depende das outras)")
    if not errors:
        try:
            topo_order(acts)
        except ValueError as e:
            errors.append(str(e))
    return errors


def topo_order(acts: list[dict]) -> list[str]:
    preds = {a["id"]: [p for p in parse_preds(a.get("predecessors"))] for a in acts}
    succ = defaultdict(list)
    indeg = {i: 0 for i in preds}
    for i, ps in preds.items():
        for p in ps:
            if p in indeg:
                succ[p].append(i)
                indeg[i] += 1
    q = deque([i for i, d in indeg.items() if d == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for s in succ[n]:
            indeg[s] -= 1
            if indeg[s] == 0:
                q.append(s)
    if len(order) != len(preds):
        cyc = [i for i, d in indeg.items() if d > 0]
        raise ValueError("Cycle in dependencies / Ciclo nas dependências: " + ", ".join(cyc))
    return order


# ----------------------------------------------------------------------------- CPM
def cpm(acts: list[dict], dur: dict[str, float] | None = None, mode: str = "pert") -> dict:
    """Forward/backward pass. Returns {'table': {id: {...}}, 'duration': T, 'critical_path': [...],
    'paths': [[...]]}. Total float (TF) = LS-ES; free float (FF) = min(ES succ) - EF."""
    if dur is None:
        dur = durations(acts, mode)
    loe = loe_ids(acts)
    allacts = acts
    acts = [a for a in acts if a["id"] not in loe]           # the network is made of the discrete work only
    order = topo_order(acts)
    preds = {a["id"]: [p for p in parse_preds(a.get("predecessors")) if p in dur and p not in loe] for a in acts}
    succ = defaultdict(list)
    for i, ps in preds.items():
        for p in ps:
            succ[p].append(i)
    ES, EF = {}, {}
    for i in order:
        ES[i] = max((EF[p] for p in preds[i]), default=0.0)
        EF[i] = ES[i] + dur[i]
    T = max(EF.values(), default=0.0)
    LS, LF = {}, {}
    for i in reversed(order):
        LF[i] = min((LS[s] for s in succ[i]), default=T)
        LS[i] = LF[i] - dur[i]
    eps = 1e-9
    table = {}
    for i in order:
        tf = LS[i] - ES[i]
        ff = (min((ES[s] for s in succ[i]), default=T) - EF[i])
        table[i] = {"ES": ES[i], "EF": EF[i], "LS": LS[i], "LF": LF[i], "D": dur[i],
                    "TF": max(0.0, tf), "FF": max(0.0, ff), "critical": abs(tf) < 1e-6 + eps}
    paths = critical_paths(order, preds, succ, table)
    cp = paths[0] if paths else []
    # LOE / hammock: from the finish of its predecessors (or the start) to the end of the discrete work; never critical
    for a in allacts:
        i = a["id"]
        if i in loe:
            es = max((EF[p] for p in parse_preds(a.get("predecessors")) if p in EF), default=0.0)
            table[i] = {"ES": es, "EF": T, "LS": es, "LF": T, "D": max(0.0, T - es), "TF": 0.0, "FF": 0.0, "critical": False,
                        "loe": True, "D_input": dur.get(i, 0.0)}
            order.append(i)
    return {"table": table, "duration": T, "critical_path": cp, "paths": paths, "order": order, "loe": sorted(loe, key=lambda x: order.index(x))}


def critical_paths(order, preds, succ, table, limit: int = 10) -> list[list[str]]:
    crit = {i for i in order if table[i]["critical"]}
    starts = [i for i in order if i in crit and not any(p in crit and abs(table[p]["EF"] - table[i]["ES"]) < 1e-6 for p in preds[i])]
    paths = []

    def walk(node, path):
        if len(paths) >= limit:
            return
        nxt = [s for s in succ[node] if s in crit and abs(table[s]["ES"] - table[node]["EF"]) < 1e-6]
        if not nxt:
            paths.append(path)
            return
        for s in nxt:
            walk(s, path + [s])

    for s in starts:
        walk(s, [s])
    T = max((v["EF"] for v in table.values()), default=0)
    return [p for p in paths if abs(table[p[-1]]["EF"] - T) < 1e-6] or paths


# ----------------------------------------------------------------------------- PERT probability
def pert_project(acts: list[dict], res: dict) -> dict:
    """Classic PERT: mean = length of critical path (te); variance = sum of variances on it."""
    by = {a["id"]: a for a in acts}
    cp = res["critical_path"]
    var = sum(pert_var(by[i].get("optimistic"), by[i].get("pessimistic")) for i in cp)
    # use the path with the largest variance among the critical ones (conservative)
    for path in res.get("paths", []):
        v = sum(pert_var(by[i].get("optimistic"), by[i].get("pessimistic")) for i in path)
        if v > var:
            var, cp = v, path
    return {"mean": res["duration"], "var": var, "sd": math.sqrt(var), "path": cp}


DEADLINE_TIGHT = 0.80   # below this probability of meeting the target the schedule is "tight" even with a positive margin


def deadline_check(acts: list[dict], res: dict, target: float | None) -> dict | None:
    """Target (imposed finish) vs the duration computed bottom-up by the network. The CPM result is NEVER capped:
    the target only adds a project margin and the float of every activity measured against the deadline
    (TF_deadline = TF + (target − T), negative = behind the deadline; MS Project / Primavera convention for a finish constraint)."""
    if not target or float(target) <= 0:
        return None
    target = float(target)
    T = float(res["duration"])
    margin = target - T
    pp = pert_project(acts, res)
    prob = prob_by(target, pp["mean"], pp["sd"])
    tf = {i: (None if t.get("loe") else t["TF"] + margin) for i, t in res["table"].items()}
    behind = [i for i in res["order"] if tf.get(i) is not None and tf[i] < -1e-9]
    status = "late" if margin < -1e-9 else "tight" if prob < DEADLINE_TIGHT else "ok"
    return {"target": target, "duration": T, "margin": margin, "prob": prob, "sd": pp["sd"], "tf_deadline": tf, "behind": behind,
            "status": status, "icon": {"ok": "✅", "tight": "⚠️", "late": "❌"}[status]}


def prob_by(target: float, mean: float, sd: float) -> float:
    if sd <= 0:
        return 1.0 if target >= mean else 0.0
    return float(stats.norm.cdf((target - mean) / sd))


def duration_for_prob(p: float, mean: float, sd: float) -> float:
    return float(mean + stats.norm.ppf(p) * sd) if sd > 0 else mean


# ----------------------------------------------------------------------------- Monte Carlo
def monte_carlo(acts: list[dict], n: int = 5000, dist: str = "betapert", seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    loe = loe_ids(acts)
    acts = [a for a in acts if a["id"] not in loe]           # LOE follows the discrete work: not sampled
    order = topo_order(acts)
    by = {a["id"]: a for a in acts}
    idx = {i: k for k, i in enumerate(order)}
    preds = {i: [p for p in parse_preds(by[i].get("predecessors")) if p in idx] for i in order}
    samples = np.zeros((n, len(order)))
    for i in order:
        a, m, b = _num(by[i].get("optimistic")), _num(by[i].get("most_likely")), _num(by[i].get("pessimistic"))
        if not (a or b):
            a = b = m
        a, b = min(a, m), max(b, m)
        k = idx[i]
        if b - a <= 1e-12:
            samples[:, k] = m
        elif dist == "triangular":
            samples[:, k] = rng.triangular(a, m, b, n)
        else:  # Beta-PERT
            al = 1 + 4 * (m - a) / (b - a)
            be = 1 + 4 * (b - m) / (b - a)
            samples[:, k] = a + rng.beta(al, be, n) * (b - a)
    EF = np.zeros_like(samples)
    for i in order:
        k = idx[i]
        es = np.zeros(n)
        for p in preds[i]:
            es = np.maximum(es, EF[:, idx[p]])
        EF[:, k] = es + samples[:, k]
    total = EF.max(axis=1)
    # criticality index: activity lies on the longest path (backward check per sample)
    succ = defaultdict(list)
    for i, ps in preds.items():
        for p in ps:
            succ[p].append(i)
    LF = np.zeros_like(samples)
    for i in reversed(order):
        k = idx[i]
        lf = total.copy()
        for s in succ[i]:
            lf = np.minimum(lf, LF[:, idx[s]] - samples[:, idx[s]])
        LF[:, k] = lf
    crit = {i: float(np.mean(np.abs(LF[:, idx[i]] - EF[:, idx[i]]) < 1e-7)) for i in order}
    crit.update({i: 0.0 for i in loe})
    pct = {f"P{q}": float(np.percentile(total, q)) for q in (10, 50, 80, 90, 95)}
    return {"samples": total, "mean": float(total.mean()), "sd": float(total.std(ddof=1)) if n > 1 else 0.0,
            "percentiles": pct, "criticality": crit, "min": float(total.min()), "max": float(total.max())}


# ----------------------------------------------------------------------------- Crashing (LP)
def crash_data(acts: list[dict], dur: dict[str, float], costs: dict[str, float]) -> dict[str, dict]:
    out = {}
    for a in acts:
        i = a["id"]
        d = dur[i]
        cd = a.get("crash_duration")
        cc = a.get("crash_cost")
        cd = _num(cd, d) if cd not in (None, "") else d
        if cd <= 0 and d > 0:  # 0 / empty means "no crashing data"
            cd = d
        cc = _num(cc, costs.get(i, 0)) if cc not in (None, "") else costs.get(i, 0)
        if cc <= 0:
            cc = costs.get(i, 0)
        cd = min(cd, d)
        max_red = max(0.0, d - cd)
        slope = (cc - costs.get(i, 0)) / max_red if max_red > 1e-9 else float("inf")
        out[i] = {"normal": d, "crash": cd, "max_red": max_red, "slope": slope,
                  "normal_cost": costs.get(i, 0), "crash_cost": cc}
    return out


def crash_to(acts: list[dict], dur: dict[str, float], costs: dict[str, float], deadline: float) -> dict:
    """Minimum-cost reduction of activity durations so the project finishes by `deadline` (LOE activities are not crashed:
    they shrink with the discrete work)."""
    allacts = acts
    loe = loe_ids(acts)
    acts = [a for a in acts if a["id"] not in loe]
    order = topo_order(acts)
    n = len(order)
    idx = {i: k for k, i in enumerate(order)}
    cd = crash_data(acts, dur, costs)
    preds = {a["id"]: [p for p in parse_preds(a.get("predecessors")) if p in idx] for a in acts}
    # variables: S(0..n-1), x(n..2n-1), F(2n)
    nv = 2 * n + 1
    c = np.zeros(nv)
    for i in order:
        s = cd[i]["slope"]
        c[n + idx[i]] = s if math.isfinite(s) else 0.0
    A, b = [], []
    for j in order:
        for i in preds[j]:
            row = np.zeros(nv)
            row[idx[i]] = 1
            row[idx[j]] = -1
            row[n + idx[i]] = -1
            A.append(row)
            b.append(-dur[i])
    for i in order:
        row = np.zeros(nv)
        row[idx[i]] = 1
        row[n + idx[i]] = -1
        row[2 * n] = -1
        A.append(row)
        b.append(-dur[i])
    bounds = [(0, None)] * n + [(0, cd[i]["max_red"] if math.isfinite(cd[i]["slope"]) else 0) for i in order] + [(0, deadline)]
    res = linprog(c, A_ub=np.array(A) if A else None, b_ub=np.array(b) if b else None, bounds=bounds, method="highs")
    if not res.success:
        return {"feasible": False}
    red = {i: float(round(res.x[n + idx[i]], 6)) for i in order}
    new_dur = {i: dur[i] - red[i] for i in order}
    extra = float(sum(red[i] * (cd[i]["slope"] if math.isfinite(cd[i]["slope"]) else 0) for i in order))
    for i in loe:
        red[i] = 0.0
        new_dur[i] = dur[i]
    new = cpm(allacts, new_dur)
    return {"feasible": True, "reductions": red, "durations": new_dur, "extra_cost": extra,
            "duration": new["duration"], "cpm": new}


def crash_curve(acts: list[dict], dur: dict[str, float], costs: dict[str, float], steps: int = 12) -> list[dict]:
    normal = cpm(acts, dur)["duration"]
    loe = loe_ids(acts)
    cd = crash_data(acts, dur, costs)
    for i in loe:
        cd[i]["slope"] = float("inf")
    min_d = cpm(acts, {i: cd[i]["crash"] if math.isfinite(cd[i]["slope"]) else dur[i] for i in dur})["duration"]
    base = sum(costs.values())
    pts = []
    if normal - min_d < 1e-9:
        return [{"duration": normal, "extra_cost": 0.0, "total_cost": base}]
    for k in range(steps + 1):
        T = normal - (normal - min_d) * k / steps
        r = crash_to(acts, dur, costs, T)
        if r.get("feasible"):
            pts.append({"duration": round(T, 4), "extra_cost": r["extra_cost"], "total_cost": base + r["extra_cost"]})
    return pts


# ----------------------------------------------------------------------------- professor example
PROFESSOR_CPM_EXAMPLE = [
    {"id": "A", "name": "Activity A", "predecessors": "", "optimistic": 3, "most_likely": 3, "pessimistic": 3},
    {"id": "B", "name": "Activity B", "predecessors": "A", "optimistic": 4, "most_likely": 4, "pessimistic": 4},
    {"id": "C", "name": "Activity C", "predecessors": "A", "optimistic": 2, "most_likely": 2, "pessimistic": 2},
    {"id": "D", "name": "Activity D", "predecessors": "B", "optimistic": 5, "most_likely": 5, "pessimistic": 5},
    {"id": "E", "name": "Activity E", "predecessors": "C", "optimistic": 1, "most_likely": 1, "pessimistic": 1},
    {"id": "F", "name": "Activity F", "predecessors": "C", "optimistic": 2, "most_likely": 2, "pessimistic": 2},
    {"id": "G", "name": "Activity G", "predecessors": "D, E", "optimistic": 4, "most_likely": 4, "pessimistic": 4},
    {"id": "H", "name": "Activity H", "predecessors": "G, F", "optimistic": 3, "most_likely": 3, "pessimistic": 3},
]
