"""Unit tests for the calculation engines.  Run:  python -m pytest -q"""
import math

from core import cpm as C
from core import excel_io as X
from core import finance as F
from core import interpret as I
from core import report as R
from core import schedule as S
from core.demos import DEMOS, build_demo


def test_professor_cpm_example():
    r = C.cpm(C.PROFESSOR_CPM_EXAMPLE, mode="ml")
    assert r["duration"] == 19
    assert r["critical_path"] == ["A", "B", "D", "G", "H"]
    t = r["table"]
    assert (t["C"]["TF"], t["E"]["TF"], t["F"]["TF"]) == (6, 6, 9)  # the figure's "FF" values
    assert (t["C"]["ES"], t["C"]["LS"], t["F"]["LF"]) == (3, 9, 16)


def test_pert_formulas():
    assert C.pert_te(2, 4, 12) == (2 + 16 + 12) / 6
    assert math.isclose(C.pert_var(2, 12), (10 / 6) ** 2)
    assert math.isclose(C.prob_by(10, 10, 2), 0.5)


def test_cycle_detection():
    acts = [{"id": "A", "predecessors": "B", "most_likely": 1}, {"id": "B", "predecessors": "A", "most_likely": 1}]
    assert any("Cycle" in e or "Ciclo" in e for e in C.validate(acts))


def test_crashing_lp():
    acts = [dict(a, crash_duration=a["most_likely"] - 1, crash_cost=1500) for a in C.PROFESSOR_CPM_EXAMPLE]
    dur = C.durations(acts, "ml")
    costs = {a["id"]: 1000 for a in acts}
    r = C.crash_to(acts, dur, costs, 17)
    assert r["feasible"] and r["duration"] <= 17 + 1e-6
    assert math.isclose(r["extra_cost"], 1000)  # two units at 500 each


def test_finance_matches_excel_conventions():
    cf = [{"year": 0, "investment": 1000}, {"year": 1, "benefits": 300}, {"year": 2, "benefits": 400},
          {"year": 3, "benefits": 500}, {"year": 4, "benefits": 200}]
    f = {"equity": 1, "debt": 0, "ke_method": "direct", "ke": 0.09}
    a = F.analyse(cf, f)
    assert math.isclose(a["npv"], 139.6781, rel_tol=1e-5)
    assert math.isclose(a["irr"], 0.153221, rel_tol=1e-4)
    assert math.isclose(a["mirr"], 0.126217, rel_tol=1e-4)


def test_wacc_capm():
    w = F.wacc({"equity": 600, "debt": 400, "ke_method": "capm", "rf": 0.03, "beta": 1.1, "mrp": 0.06, "kd": 0.05, "tax": 0.21})
    assert math.isclose(w["ke"], 0.096)
    assert math.isclose(w["wacc"], 0.6 * 0.096 + 0.4 * 0.05 * 0.79)


def test_cost_distribution_conserves_budget():
    for prof in ["Uniform", "Start", "End", "Front-loaded", "Back-loaded", "Milestone 50/50"]:
        v = S.distribute(1000, 3.4, 40.2, prof, 60)
        assert math.isclose(v.sum(), 1000, rel_tol=1e-9)


def test_all_demos_end_to_end():
    for k in DEMOS:
        p = build_demo(k)
        s = S.compute(p)
        assert s["ok"], (k, s.get("errors"))
        assert math.isclose(s["periods"]["pv"].sum(), s["bac"], rel_tol=1e-6)
        e = S.evm(p, s)
        assert e["BAC"] > 0 and 0.5 < e["CPI"] < 1.5
        assert F.analyse(p["cashflows"], p["finance"])["npv"] is not None
        I.checks(p, s)
        assert "<html" in R.build(p)
        X.extended_workbook(p)
        X.professor_risks(p)
        X.professor_stakeholders(p)
