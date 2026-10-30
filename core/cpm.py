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
    order = topo_order(acts)
    preds = {a["id"]: [p for p in parse_preds(a.get("predecessors")) if p in dur] for a in acts}
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
    return {"table": table, "duration": T, "critical_path": cp, "paths": paths, "order": order}


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


def prob_by(target: float, mean: float, sd: float) -> float:
    if sd <= 0:
        return 1.0 if target >= mean else 0.0
    return float(stats.norm.cdf((target - mean) / sd))


def duration_for_prob(p: float, mean: float, sd: float) -> float:
    return float(mean + stats.norm.ppf(p) * sd) if sd > 0 else mean


# ----------------------------------------------------------------------------- Monte Carlo
def monte_carlo(acts: list[dict], n: int = 5000, dist: str = "betapert", seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
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
        cc = _num(cc, costs.get(i, 0)) if cc not in (None, "") else costs.get(i, 0)
        cd = min(cd, d)
        max_red = max(0.0, d - cd)
        slope = (cc - costs.get(i, 0)) / max_red if max_red > 1e-9 else float("inf")
        out[i] = {"normal": d, "crash": cd, "max_red": max_red, "slope": slope,
                  "normal_cost": costs.get(i, 0), "crash_cost": cc}
    return out


def crash_to(acts: list[dict], dur: dict[str, float], costs: dict[str, float], deadline: float) -> dict:
    """Minimum-cost reduction of activity durations so the project finishes by `deadline`."""
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
    new = cpm(acts, new_dur)
    return {"feasible": True, "reductions": red, "durations": new_dur, "extra_cost": extra,
            "duration": new["duration"], "cpm": new}


def crash_curve(acts: list[dict], dur: dict[str, float], costs: dict[str, float], steps: int = 12) -> list[dict]:
    normal = cpm(acts, dur)["duration"]
    cd = crash_data(acts, dur, costs)
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
