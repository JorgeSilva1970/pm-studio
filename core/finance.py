"""Financial appraisal: WACC, NPV (VAL), IRR (TIR), MIRR, payback, profitability index, sensitivity."""
from __future__ import annotations

import math

import numpy as np


def cost_of_equity(f: dict) -> float:
    if f.get("ke_method") == "capm":
        return float(f.get("rf") or 0) + float(f.get("beta") or 0) * float(f.get("mrp") or 0)
    return float(f.get("ke") or 0)


def wacc(f: dict) -> dict:
    E, D = float(f.get("equity") or 0), float(f.get("debt") or 0)
    V = E + D
    ke = cost_of_equity(f)
    kd = float(f.get("kd") or 0)
    t = float(f.get("tax") or 0)
    if V <= 0:
        return {"wacc": ke, "ke": ke, "kd_after_tax": kd * (1 - t), "we": 1.0, "wd": 0.0}
    we, wd = E / V, D / V
    return {"wacc": we * ke + wd * kd * (1 - t), "ke": ke, "kd_after_tax": kd * (1 - t), "we": we, "wd": wd}


def npv(rate: float, flows: list[float]) -> float:
    """Flows indexed from year 0 (undiscounted) – Excel's NPV(rate, CF1..CFn) + CF0."""
    return float(sum(cf / (1 + rate) ** t for t, cf in enumerate(flows)))


def irr(flows: list[float]) -> float | None:
    flows = [float(x) for x in flows]
    if not flows or all(x >= 0 for x in flows) or all(x <= 0 for x in flows):
        return None
    # NPV·(1+r)^n = Σ cf_t·y^(n-t) with y = 1+r  ->  np.roots(cf_0, cf_1, ..., cf_n)
    roots = np.roots(flows)
    cands = []
    for y in roots:
        if abs(y.imag) < 1e-9 and y.real > 0:
            r = y.real - 1
            if r > -0.9999:
                cands.append(r)
    if not cands:
        return None
    # choose the root closest to a "reasonable" rate where NPV crosses zero
    cands.sort(key=lambda r: abs(r - 0.1))
    return float(cands[0])


def mirr(flows: list[float], finance_rate: float, reinvest_rate: float) -> float | None:
    n = len(flows) - 1
    if n <= 0:
        return None
    neg = sum(cf / (1 + finance_rate) ** t for t, cf in enumerate(flows) if cf < 0)
    pos = sum(cf * (1 + reinvest_rate) ** (n - t) for t, cf in enumerate(flows) if cf > 0)
    if neg >= 0 or pos <= 0:
        return None
    return float((pos / -neg) ** (1 / n) - 1)


def payback(flows: list[float], rate: float | None = None) -> float | None:
    cum = 0.0
    for t, cf in enumerate(flows):
        v = cf / (1 + rate) ** t if rate is not None else cf
        prev = cum
        cum += v
        if cum >= 0 and t > 0 and prev < 0:
            return float(t - 1 + (-prev / v if v else 0))
    return None


def analyse(cashflows: list[dict], f: dict, residual: float = 0.0) -> dict:
    rows = sorted(cashflows, key=lambda r: int(r.get("year") or 0))
    if not rows:
        return {}
    w = wacc(f)
    rate = f.get("rate_override")
    rate = float(rate) if rate not in (None, "") else w["wacc"]
    fin = f.get("finance_rate")
    fin = float(fin) if fin not in (None, "") else rate
    rein = f.get("reinvest_rate")
    rein = float(rein) if rein not in (None, "") else rate
    years = [int(r.get("year") or 0) for r in rows]
    n = max(years)
    flows = [0.0] * (n + 1)
    inv = [0.0] * (n + 1)
    opx = [0.0] * (n + 1)
    ben = [0.0] * (n + 1)
    for r in rows:
        y = int(r.get("year") or 0)
        i, o, b = float(r.get("investment") or 0), float(r.get("operating_costs") or 0), float(r.get("benefits") or 0)
        inv[y] += i
        opx[y] += o
        ben[y] += b
    flows = [ben[t] - opx[t] - inv[t] for t in range(n + 1)]
    if residual:
        flows[-1] += residual
    disc = [cf / (1 + rate) ** t for t, cf in enumerate(flows)]
    pv_inv = sum(inv[t] / (1 + rate) ** t for t in range(n + 1))
    v = npv(rate, flows)
    return {"rate": rate, "wacc": w, "flows": flows, "investment": inv, "operating_costs": opx, "benefits": ben,
            "discounted": disc, "cum": list(np.cumsum(flows)), "cum_disc": list(np.cumsum(disc)),
            "npv": v, "irr": irr(flows), "mirr": mirr(flows, fin, rein), "finance_rate": fin, "reinvest_rate": rein,
            "payback": payback(flows), "disc_payback": payback(flows, rate),
            "pi": (v + pv_inv) / pv_inv if pv_inv else None,
            "eaa": v * rate / (1 - (1 + rate) ** -n) if n > 0 and rate > 0 else None}


def sensitivity(cashflows: list[dict], f: dict, residual: float = 0.0, delta: float = 0.2) -> list[dict]:
    """Tornado: NPV when each driver varies ±delta."""
    base = analyse(cashflows, f, residual)["npv"]
    out = []

    def scaled(field, k):
        return [dict(r, **{field: float(r.get(field) or 0) * k}) for r in cashflows]

    for field, label in (("benefits", "Benefícios / Benefits"), ("investment", "Investimento / Investment"),
                         ("operating_costs", "Custos operacionais / Operating costs")):
        lo = analyse(scaled(field, 1 - delta), f, residual)["npv"]
        hi = analyse(scaled(field, 1 + delta), f, residual)["npv"]
        out.append({"driver": label, "low": lo, "high": hi, "base": base})
    r0 = analyse(cashflows, f, residual)["rate"]
    lo = analyse(cashflows, dict(f, rate_override=r0 * (1 - delta)), residual)["npv"]
    hi = analyse(cashflows, dict(f, rate_override=r0 * (1 + delta)), residual)["npv"]
    out.append({"driver": "Taxa de desconto / Discount rate", "low": lo, "high": hi, "base": base})
    out.sort(key=lambda d: abs(d["high"] - d["low"]), reverse=True)
    return out


def npv_profile(flows: list[float], rmax: float = 0.4, steps: int = 41) -> list[tuple[float, float]]:
    return [(r, npv(r, flows)) for r in np.linspace(0, rmax, steps)]


def breakeven_benefit_factor(cashflows: list[dict], f: dict, residual: float = 0.0) -> float | None:
    """Multiplier on benefits that makes NPV = 0 (how much benefits may fall before the project destroys value)."""
    from scipy.optimize import brentq

    def g(k):
        return analyse([dict(r, benefits=float(r.get("benefits") or 0) * k) for r in cashflows], f, residual)["npv"]
    try:
        if g(0) * g(5) > 0:
            return None
        return float(brentq(g, 0, 5))
    except Exception:
        return None
