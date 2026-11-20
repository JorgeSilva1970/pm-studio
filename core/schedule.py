"""Calendar schedule, cost-loaded Gantt (time-phased budget), S-curve and Earned Value Management."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from . import cpm as C
from .model import activity_cost

UNIT_DAYS = {"days": 1.0, "weeks": 7.0, "months": 30.4375}


def to_date(v) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.fromisoformat(str(v)[:10]).date()
    except Exception:
        return date.today().replace(day=1)


def contingency_amount(p: dict, bac: float | None = None) -> float:
    m = p["meta"]
    if bac is None:
        bac = sum(activity_cost(p, a) for a in p["activities"])
    if m.get("contingency_method") == "risk":
        return float(sum(float(r.get("contingency") or 0) for r in p.get("risks", [])))
    return float(bac * float(m.get("contingency_pct") or 0))


def compute(p: dict) -> dict:
    """Run CPM on the project and build every schedule/cost artefact. Returns a dict with
    keys: ok, errors, cpm, dur, unit, factor, start, acts (DataFrame), bac, daily (array), periods (DataFrame)."""
    acts = [a for a in p.get("activities", []) if str(a.get("id", "")).strip()]
    m = p["meta"]
    unit = m.get("time_unit", "weeks")
    factor = UNIT_DAYS.get(unit, 7.0)
    start = to_date(m.get("start_date"))
    out = {"ok": False, "errors": [], "unit": unit, "factor": factor, "start": start}
    if not acts:
        out["errors"] = ["Sem atividades / No activities"]
        return out
    errs = C.validate(acts)
    if errs:
        out["errors"] = errs
        return out
    dur = C.durations(acts, m.get("duration_mode", "pert"))
    res = C.cpm(acts, dur)
    rows = []
    for a in acts:
        t = res["table"][a["id"]]
        es_d, ef_d = t["ES"] * factor, t["EF"] * factor
        rows.append({
            "id": a["id"], "name": a.get("name", ""), "output_code": a.get("output_code", ""),
            "type": a.get("type", ""), "predecessors": a.get("predecessors", ""),
            "D": t["D"], "ES": t["ES"], "EF": t["EF"], "LS": t["LS"], "LF": t["LF"], "TF": t["TF"], "FF": t["FF"],
            "critical": t["critical"], "milestone": bool(a.get("milestone")) or t["D"] == 0,
            "start": start + timedelta(days=es_d), "finish": start + timedelta(days=ef_d),
            "late_finish": start + timedelta(days=t["LF"] * factor),
            "cost": activity_cost(p, a), "distribution": a.get("distribution", "Uniform"),
            "responsible": a.get("responsible", ""), "pct_complete": float(a.get("pct_complete") or 0),
            "actual_cost": float(a.get("actual_cost") or 0),
            "es_days": es_d, "ef_days": ef_d,
        })
    df = pd.DataFrame(rows)
    total_days = max(1, int(np.ceil(res["duration"] * factor)) + 1)
    daily = np.zeros(total_days)
    per_act = {}
    for r in rows:
        v = distribute(r["cost"], r["es_days"], r["ef_days"], r["distribution"], total_days)
        per_act[r["id"]] = v
        daily += v
    out.update({"ok": True, "cpm": res, "dur": dur, "acts": df, "bac": float(df["cost"].sum()),
                "daily": daily, "daily_by_act": per_act, "total_days": total_days,
                "finish": start + timedelta(days=res["duration"] * factor)})
    out["periods"] = periodize(daily, start, m.get("period", "month"), per_act)
    out["contingency"] = contingency_amount(p, out["bac"])
    return out


def _cum(profile: str, u: float) -> float:
    u = min(max(u, 0.0), 1.0)
    if profile == "Front-loaded":
        return 2 * u - u * u
    if profile == "Back-loaded":
        return u * u
    return u


def distribute(cost: float, s: float, e: float, profile: str, ndays: int) -> np.ndarray:
    """Spread `cost` over day bins between s and e (days from project start) using a profile."""
    v = np.zeros(ndays)
    if not cost:
        return v
    def bin_of(x):
        return int(min(max(np.floor(x), 0), ndays - 1))
    length = e - s
    if length <= 1e-9:
        v[bin_of(s)] += cost
        return v
    if profile == "Start":
        v[bin_of(s)] += cost
        return v
    if profile == "End":
        v[bin_of(e - 1e-6)] += cost
        return v
    if profile == "Milestone 50/50":
        v[bin_of(s)] += cost / 2
        v[bin_of(e - 1e-6)] += cost / 2
        return v
    d0, d1 = int(np.floor(s)), int(np.ceil(e))
    for d in range(d0, min(d1, ndays)):
        lo, hi = max(s, d), min(e, d + 1)
        if hi <= lo:
            continue
        v[d] += cost * (_cum(profile, (hi - s) / length) - _cum(profile, (lo - s) / length))
    # any rounding remainder goes to the last bin
    v[bin_of(e - 1e-6)] += cost - v.sum()
    return v


def periodize(daily: np.ndarray, start: date, period: str = "month", per_act: dict | None = None) -> pd.DataFrame:
    days = pd.date_range(start, periods=len(daily), freq="D")
    freq = {"week": "W-MON", "month": "M", "quarter": "Q", "year": "Y"}.get(period, "M")
    s = pd.Series(daily, index=days)
    key = days.to_period(freq)
    g = s.groupby(key).sum()
    df = pd.DataFrame({"period": [str(k) for k in g.index], "period_start": [k.start_time.date() for k in g.index],
                       "period_end": [k.end_time.date() for k in g.index], "pv": g.values})
    df["pv_cum"] = df["pv"].cumsum()
    if per_act:
        for aid, arr in per_act.items():
            df[aid] = pd.Series(arr, index=days).groupby(key).sum().values
    return df


def planned_value_at(sched: dict, when: date) -> float:
    if not sched.get("ok"):
        return 0.0
    k = (to_date(when) - sched["start"]).days + 1
    k = max(0, min(k, len(sched["daily"])))
    return float(sched["daily"][:k].sum())


def planned_value_act(sched: dict, aid: str, when: date) -> float:
    k = (to_date(when) - sched["start"]).days + 1
    arr = sched["daily_by_act"][aid]
    return float(arr[:max(0, min(k, len(arr)))].sum())


def evm(p: dict, sched: dict) -> dict:
    """Earned Value at the status date (meta.status_date)."""
    if not sched.get("ok"):
        return {}
    status = to_date(p["meta"].get("status_date"))
    df = sched["acts"].copy()
    df["BAC"] = df["cost"]
    df["PV"] = [planned_value_act(sched, a, status) for a in df["id"]]
    df["EV"] = df["BAC"] * df["pct_complete"].clip(0, 1)
    df["AC"] = df["actual_cost"]
    df["CV"] = df["EV"] - df["AC"]
    df["SV"] = df["EV"] - df["PV"]
    df["CPI"] = np.where(df["AC"] > 0, df["EV"] / df["AC"].replace(0, np.nan), np.nan)
    df["SPI"] = np.where(df["PV"] > 0, df["EV"] / df["PV"].replace(0, np.nan), np.nan)
    BAC, PV, EV, AC = df["BAC"].sum(), df["PV"].sum(), df["EV"].sum(), df["AC"].sum()
    CPI = EV / AC if AC else float("nan")
    SPI = EV / PV if PV else float("nan")
    EAC = BAC / CPI if AC and CPI else BAC
    cont = sched.get("contingency", 0.0)
    used = float(p["meta"].get("contingency_used") or 0)
    k = {"status": status, "BAC": BAC, "PV": PV, "EV": EV, "AC": AC, "CV": EV - AC, "SV": EV - PV,
         "CPI": CPI, "SPI": SPI, "EAC": EAC, "ETC": EAC - AC, "VAC": BAC - EAC,
         "EAC2": AC + (BAC - EV),  # atypical variance
         "EAC3": AC + (BAC - EV) / (CPI * SPI) if CPI == CPI and SPI == SPI and CPI and SPI else EAC,
         "TCPI": (BAC - EV) / (BAC - AC) if BAC != AC else float("nan"),
         "pct_planned": PV / BAC if BAC else 0, "pct_done": EV / BAC if BAC else 0, "pct_spent": AC / BAC if BAC else 0,
         "contingency": cont, "contingency_used": used, "contingency_left": cont - used}
    # time-based estimate: planned duration / SPI
    T = sched["cpm"]["duration"]
    k["duration_forecast"] = T / SPI if SPI and SPI == SPI else T
    k["finish_forecast"] = sched["start"] + timedelta(days=k["duration_forecast"] * sched["factor"])
    k["table"] = df
    return k


def s_curve(p: dict, sched: dict) -> pd.DataFrame:
    """Per period: PV (cum) from the plan, plus EV/AC history from tracking + current status."""
    per = sched["periods"][["period", "period_start", "period_end", "pv", "pv_cum"]].copy()
    per["ev_cum"] = np.nan
    per["ac_cum"] = np.nan
    hist = list(p.get("tracking", []))
    e = evm(p, sched)
    if e:
        hist.append({"date": e["status"].isoformat(), "ev": e["EV"], "ac": e["AC"]})
    for h in hist:
        d = to_date(h.get("date"))
        mask = (per["period_start"] <= d) & (per["period_end"] >= d)
        if mask.any():
            if h.get("ev") is not None and h.get("ev") == h.get("ev"):
                per.loc[mask, "ev_cum"] = float(h["ev"])
            if h.get("ac") is not None and h.get("ac") == h.get("ac"):
                per.loc[mask, "ac_cum"] = float(h["ac"])
    if p.get("baseline") and p["baseline"].get("pv_curve"):
        b = {r["period"]: r["pv_cum"] for r in p["baseline"]["pv_curve"]}
        per["baseline_pv_cum"] = [b.get(x, np.nan) for x in per["period"]]
    return per


def make_baseline(p: dict, sched: dict) -> dict:
    df = sched["acts"]
    return {"created": date.today().isoformat(),
            "acts": {r["id"]: {"start": str(r["start"]), "finish": str(r["finish"]), "cost": r["cost"]} for _, r in df.iterrows()},
            "duration": sched["cpm"]["duration"], "bac": sched["bac"],
            "pv_curve": sched["periods"][["period", "pv_cum"]].to_dict("records")}


def yearly_investment(sched: dict) -> dict[int, float]:
    """Schedule cost aggregated by project year (year 0 = first 12 months)."""
    if not sched.get("ok"):
        return {}
    out = {}
    for k, v in enumerate(sched["daily"]):
        y = int(k // 365.25)
        out[y] = out.get(y, 0.0) + float(v)
    return out
