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


# ----------------------------------------------------------------------------- implementation, monitoring & evaluation
def test_indicator_trajectory_and_status():
    from datetime import date
    from core import monitor as M
    ind = {"baseline": 10, "target": 20, "baseline_year": 2026, "target_year": 2028}
    assert abs(M.expected_value(ind, date(2027, 1, 1)) - 15) < 0.05
    assert M.indicator_status(ind, 15, date(2027, 1, 1))[0] == "on_track"
    assert M.indicator_status(ind, 12, date(2027, 1, 1))[0] == "off_track"
    dec = {"baseline": 18, "target": 6, "baseline_year": 2026, "target_year": 2028}   # decreasing indicator
    assert M.indicator_status(dec, 12.2, date(2027, 1, 1))[0] == "on_track"


def test_change_rule_and_bid_scoring():
    from core import monitor as M
    assert M.change_class({"element_type": "Outcome"})[0] == "strategic"
    assert M.change_class({"element_type": "Target"})[0] == "target"
    assert M.change_class({"element_type": "Budget"})[0] == "tactical"
    sc = M.bid_scores([{"bidder": "A", "compliant": True, "technical_score": 80, "price": 90},
                       {"bidder": "B", "compliant": True, "technical_score": 60, "price": 80},
                       {"bidder": "C", "compliant": False, "technical_score": 99, "price": 50}], 0.5)
    assert [r["bidder"] for r in sc] == ["A", "B"]           # C is not compliant
    assert abs(sc[0]["total"] - (0.5 * 80 + 0.5 * 100 * 80 / 90)) < 1e-9
    assert abs(sc[1]["total"] - (0.5 * 60 + 0.5 * 100)) < 1e-9


def test_contingency_drawdown_and_demo_monitoring():
    from core import monitor as M
    from core import schedule as S
    from core.demos import build_demo
    p = build_demo("trade")
    sched = S.compute(p)
    cs = M.contingency_status(p, sched["bac"])
    c = cs["Contingency reserve"]
    assert abs(c["available"] - (c["initial"] + c["reinforced"] - c["used"] - c["released"])) < 1e-6
    assert abs(c["used"] - p["meta"]["contingency_used"]) < 1e-6
    assert p["milestones"] and p["ind_reviews"] and p["comm_plan"] and p["lessons"]
    ep = M.efficiency_panel(p, sched)
    assert ep["CPI"] is not None and 0 <= (ep["ind_on_track"] or 0) <= 1
    assert M.me_quality_score(p) is not None


def test_thematic_templates_roundtrip():
    import io
    from openpyxl import load_workbook
    from core import excel_io as X
    from core.model import new_project, normalize
    for k in X.THEMATIC:
        wb = load_workbook(io.BytesIO(X.blank_template(k)))
        for ws in wb.worksheets:
            if "[table:" in str(ws["A1"].value):
                for c in range(1, ws.max_column + 1):
                    ws.cell(5, c).value = ws.cell(3, c).value
        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)
        p = normalize(new_project())
        X.import_workbook(p, bio, "append")
        for t in X.THEMATIC[k][4]:
            if t in X.PSEUDO:
                continue            # wbs_assign only updates existing activities
            assert len(p[t]) == 1, (k, t)


# ----------------------------------------------------------------------------- WBS / EAP
def test_wbs_generation_rollup_and_100pct_rule():
    from core import schedule as S
    from core import wbs as W
    from core.demos import build_demo
    for key, ori in (("trade", "deliverables"), ("it", "phases"), ("construction", "deliverables")):
        p = build_demo(key)
        W.apply_generated(p, ori)
        sched = S.compute(p)
        ro = W.rollup(p, sched, S.evm(p, sched))
        # every activity in exactly one work package, bottom-up totals without double counting
        leaves = {e["code"] for e in W.leaves(p)}
        assert all(a["wbs_code"] in leaves for a in p["activities"])
        lvl1 = sum(r["BAC"] for c, r in ro.items() if r["level"] == 1)
        assert abs(lvl1 - ro["0"]["BAC"]) < 1e-6 and abs(ro["0"]["BAC"] - sched["bac"]) < 1e-6
        for e in W.elements(p):
            kids = W.children(p, e["code"])
            if kids:
                assert abs(sum(ro[k["code"]]["BAC"] for k in kids) - ro[e["code"]]["BAC"]) < 1e-6
        assert not any(c["sev"] in ("error", "warn") for c in W.checks(p, sched))


def test_wbs_checks_and_renumber():
    from core import wbs as W
    from core.demos import build_demo
    p = build_demo("trade")
    W.apply_generated(p)
    p["activities"][0]["wbs_code"] = ""
    p["wbs"].append({"code": "9.1", "name": "Órfão", "type": "Work package", "output_code": "", "description": "", "deliverable": "", "acceptance": "", "owner": "", "weight": None})
    msgs = " ".join(c["msg"] for c in W.checks(p))
    assert "A1" in msgs and "9.1" in msgs
    p["wbs"] = [e for e in p["wbs"] if e["code"] != "9.1"]
    p["wbs"].append({"code": "7", "name": "Extra", "type": "Deliverable", "output_code": "", "description": "", "deliverable": "", "acceptance": "", "owner": "", "weight": None})
    p["activities"][0]["wbs_code"] = "7"
    W.renumber(p)
    assert p["activities"][0]["wbs_code"] == "4" and any(e["code"] == "4" for e in p["wbs"])
    assert W.next_child_code(p, "1") == "1.4" and W.parent_of("1.2.3") == "1.2" and W.is_under("1.2.3", "1") and not W.is_under("1.10", "1.1")


def test_wbs_excel_roundtrip():
    import io
    from core import excel_io as X
    from core.demos import build_demo
    from core.model import new_project, normalize
    p = build_demo("trade")
    q = normalize(new_project())
    X.import_workbook(q, io.BytesIO(X.extended_workbook(p)), "replace")
    assert [e["code"] for e in q["wbs"]] == [e["code"] for e in p["wbs"]]
    assert [a["wbs_code"] for a in q["activities"]] == [a["wbs_code"] for a in p["activities"]]


def test_wbs_glossary_and_worked_example():
    from core import schedule as S
    from core import wbs as W
    from core.demos import build_demo
    from core.help_texts import WBS_GLOSSARY, SRC
    for k, g in WBS_GLOSSARY.items():
        assert len(g["pt"]) == 3 and len(g["en"]) == 3 and all(g["pt"]) and all(g["en"]), k
        assert all(s in SRC for s in g["src"]), k
    p = build_demo("trade")
    sched = S.compute(p)
    ev = S.evm(p, sched)
    ro = W.rollup(p, sched, ev)
    for code in ["0"] + [e["code"] for e in W.elements(p)]:
        txt = W.explain(p, code, ro, ev)
        assert "BAC" in txt
        r = ro[code]
        if r.get("CPI"):
            assert abs(r["CPI"] - r["EV"] / r["AC"]) < 1e-9          # CPI = ΣEV ÷ ΣAC (not an average)
        if r.get("pct") is not None:
            assert abs(r["pct"] - r["EV"] / r["BAC"]) < 1e-9          # % complete = EV ÷ BAC
    mn, mx, rule = W.duration_limits({"meta": {"time_unit": "weeks", "wbs_rule": "8/80"}})
    assert abs(mx - 2.0) < 1e-9 and abs(mn - 0.2) < 1e-9          # 80 h = 10 working days = 2 weeks


def test_retail_filled_templates_roundtrip():
    """Every filled template (extended + thematic + activities) re-imports to the same tables."""
    import io
    from core import excel_io as X
    from core.demos import build_demo
    from core.model import new_project, normalize
    ref = build_demo("retail")
    p = normalize(new_project())
    X.import_workbook(p, io.BytesIO(X.blank_template(None, ref)), "replace")
    for t in ("stakeholders", "objectives", "indicators", "activities", "wbs", "risks", "budget", "ind_reviews", "milestones", "changes", "comm_plan", "bids", "lessons"):
        assert len(p[t]) == len(ref[t]), t
    q = normalize(new_project())
    f = io.BytesIO(X.activities_template("csv", ref))
    f.name = "a.csv"
    X.import_activities(q, f, "replace")
    for k in X.THEMATIC:
        X.import_workbook(q, io.BytesIO(X.blank_template(k, ref)), "replace")
    assert [a["wbs_code"] for a in q["activities"]] == [a["wbs_code"] for a in ref["activities"]]
    assert len(q["closure"]) == len(ref["closure"]) and len(q["sustainability"]) == len(ref["sustainability"])
    # professor stakeholder register keeps influence/interest/attitude of existing stakeholders
    r = build_demo("retail")
    X.import_workbook(r, io.BytesIO(X.professor_stakeholders(ref)[0]), "replace")
    assert [(s["influence"], s["attitude"]) for s in r["stakeholders"]] == [(s["influence"], s["attitude"]) for s in ref["stakeholders"]]
