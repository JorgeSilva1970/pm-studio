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


def test_sample_filled_templates_roundtrip():
    """Every filled template (extended + thematic + activities) re-imports to the same tables (sample projects)."""
    for key in ("retail", "imaging"):
        _roundtrip(key)


def test_upload_only_samples_not_in_example_menu():
    from core.demos import DEMOS, SAMPLES, UPLOAD_ONLY
    assert UPLOAD_ONLY <= set(SAMPLES) and not UPLOAD_ONLY & set(DEMOS)
    assert "retail" in DEMOS


def _roundtrip(key):
    import io
    from core import excel_io as X
    from core.demos import build_demo
    from core.model import new_project, normalize
    ref = build_demo(key)
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
    r = build_demo(key)
    X.import_workbook(r, io.BytesIO(X.professor_stakeholders(ref)[0]), "replace")
    assert [(s["influence"], s["attitude"]) for s in r["stakeholders"]] == [(s["influence"], s["attitude"]) for s in ref["stakeholders"]]


def test_risk_management_matrix_threshold_and_impact():
    """Professor's slides: adverse impact = logframe row of the assumption; threshold 5/10/15% of BAC; impact by level/critical path."""
    import io

    from openpyxl import load_workbook

    from core import riskmgmt as RM
    from core.model import normalize
    p = build_demo("retail")
    asm = {h["id"]: h for h in p["assumptions"]}
    for r in p["risks"]:
        if r.get("assumption_id") in asm:
            want = {"Operational": "Activity", "Behavioural": "Output", "Political": "Outcome"}[asm[r["assumption_id"]]["type"]]
            assert r["level_affected"] == want, (r["id"], r["level_affected"])
    # migration runs once: a later manual choice is kept
    p["risks"][0]["level_affected"] = "Outcome"
    assert normalize(p)["risks"][0]["level_affected"] == "Outcome"
    # scope / responsible by type
    rows = {x["id"]: x for x in RM.matrix_rows(p)}
    r1 = rows["R1"]
    assert r1["kind"] == "Operational" and r1["internal"] and r1["short"] == "PMT" and r1["corrective"]
    # threshold statuses
    bac = S.compute(p)["bac"]
    cost = sum(r["contingency"] for r in p["risks"])
    for thr, status in ((cost / bac * 0.9, "over"), (cost / bac * 1.1, "near"), (cost / bac * 2, "ok")):
        p["meta"]["risk_threshold"] = thr
        assert RM.threshold_check(p, bac)["status"] == status
    # suggested impact: Output 3, Outcome 4, activity on the critical path 2, activity with float 1
    tf = RM.floats(p)
    crit = next(a for a, v in tf.items() if v <= 1e-9)
    loose = next(a for a, v in tf.items() if v > 0)
    W_ = __import__("core.wbs", fromlist=["x"])
    code_c = next(a["wbs_code"] for a in p["activities"] if a["id"] == crit)
    code_l = next(a["wbs_code"] for a in p["activities"] if a["id"] == loose)
    base = {"assumption_id": "", "wbs_code": ""}
    assert RM.suggested_impact(p, base | {"level_affected": "Output"}, tf)[0] == 3
    assert RM.suggested_impact(p, base | {"level_affected": "Outcome"}, tf)[0] == 4
    assert RM.suggested_impact(p, base | {"level_affected": "Activity", "wbs_code": code_c}, tf)[0] == 2
    if not any(tf.get(a["id"], 1) <= 1e-9 for a in p["activities"] if a.get("wbs_code") and W_.is_under(a["wbs_code"], code_l)):
        assert RM.suggested_impact(p, base | {"level_affected": "Activity", "wbs_code": code_l}, tf)[0] == 1
    # if-then sentence and HTML
    assert "então" in RM.if_then(p, p["assumptions"][0]) or "then" in RM.if_then(p, p["assumptions"][0])
    assert "<table" in RM.matrix_html(p)
    # extended workbook: matrix sheet, exposure column after every field, new fields round-trip
    p["meta"]["risk_threshold"] = 0.10
    wb = load_workbook(io.BytesIO(X.extended_workbook(p)))
    assert any(n in wb.sheetnames for n in ("Matriz gestão riscos", "Risk mgmt matrix"))
    ws = wb["Riscos"]
    hdr = [c.value for c in ws[4]]
    xc = next(i for i, h in enumerate(hdr) if h in ("Exposição", "Exposure"))
    assert ws.cell(5, xc + 1).value.startswith("=D5*E5")
    assert ws.cell(5, xc + 2).value.startswith(f"=IF({ws.cell(5, xc + 1).column_letter}5>F5")
    q = build_demo("retail")
    q["risks"] = []
    X.import_workbook(q, io.BytesIO(X.extended_workbook(p)), mode="replace")
    assert q["risks"] and q["risks"][0].get("trigger")


def test_examples_risk_management_and_backfill():
    """Every example has corrective actions, triggers and a threshold; examples saved before the update are back-filled once."""
    import copy
    import io

    from core.demos import DEMOS
    from core.model import new_project, normalize
    for k in list(DEMOS) + ["imaging"]:
        p = build_demo(k)
        assert all(r.get("corrective_action") and r.get("trigger") for r in p["risks"]), k
        assert p["meta"]["risk_threshold"] in (0.05, 0.10, 0.15)
    # an example saved before the update: no flags, no corrective actions, old threshold
    old = build_demo("aero")
    for r in old["risks"]:
        r["corrective_action"] = r["trigger"] = ""
    old["meta"]["risk_threshold"] = 0.10
    old["meta"].pop("risk_demo_v")
    old["risks"][1]["trigger"] = "manual"
    q = normalize(copy.deepcopy(old))
    assert q["meta"]["risk_threshold"] == 0.15 and q["risks"][0]["trigger"] and q["risks"][1]["trigger"] == "manual"
    # a user's own project is never touched
    own = build_demo("aero")
    own["meta"]["name"] = "O meu projeto"
    own["meta"].pop("risk_demo_v")
    own["risks"][0]["trigger"] = ""
    assert normalize(own)["risks"][0]["trigger"] == ""
    # template 8: risks with corrective/trigger + threshold (10, 10% or 0.10)
    ref = build_demo("retail")
    ref["meta"]["risk_threshold"] = 0.15
    z = normalize(new_project())
    X.import_workbook(z, io.BytesIO(X.blank_template("riskmgmt", ref)), "replace")
    assert len(z["risks"]) == len(ref["risks"]) and z["meta"]["risk_threshold"] == 0.15
    assert [r["trigger"] for r in z["risks"]] == [r["trigger"] for r in ref["risks"]]


def test_level_of_effort_activities():
    """LOE (hammock): derived duration, never critical, not crashed nor sampled; flags management that drives the critical path."""
    from core import cpm as C
    acts = [{"id": "A", "predecessors": "", "optimistic": 2, "most_likely": 2, "pessimistic": 2},
            {"id": "B", "predecessors": "A", "optimistic": 3, "most_likely": 3, "pessimistic": 3, "crash_duration": 2, "crash_cost": 150},
            {"id": "C", "predecessors": "A", "optimistic": 1, "most_likely": 1, "pessimistic": 1},
            {"id": "M", "predecessors": "", "optimistic": 9, "most_likely": 9, "pessimistic": 9, "type": "Support - Management"}]
    res = C.cpm(acts)                       # typed-in management duration (9) drives the project: artificial critical path
    assert res["duration"] == 9 and res["critical_path"] == ["M"] and C.loe_candidates(acts, res) == ["M"]
    acts[3]["loe"] = True
    res = C.cpm(acts)
    assert res["duration"] == 5 and res["critical_path"] == ["A", "B"] and res["loe"] == ["M"]
    t = res["table"]["M"]
    assert (t["ES"], t["EF"], t["D"], t["critical"]) == (0, 5, 5, False) and C.loe_candidates(acts, res) == []
    assert C.monte_carlo(acts, 200)["criticality"]["M"] == 0.0
    cr = C.crash_to(acts, C.durations(acts), {"A": 100, "B": 100, "C": 100, "M": 100}, 4)
    assert cr["feasible"] and cr["reductions"]["M"] == 0 and abs(cr["duration"] - 4) < 1e-6 and cr["cpm"]["table"]["M"]["D"] == 4
    # an LOE activity cannot be a predecessor
    acts.append({"id": "D", "predecessors": "M", "optimistic": 1, "most_likely": 1, "pessimistic": 1})
    assert any("LOE" in e for e in C.validate(acts))
    # examples: management / M&E are LOE and production risks can sit on the critical path
    from core import riskmgmt as RM
    p = build_demo("imaging")
    sched = S.compute(p)
    assert sched["cpm"]["loe"] == ["A12", "A13"] and "A5" in sched["cpm"]["critical_path"]
    assert {x["id"]: x["suggested"] for x in RM.suggestions(p)}["R2"] == 2


def test_deadline_is_compared_never_caps_the_network():
    """The target only adds a margin / float against the deadline; the computed duration is never capped."""
    from core import cpm as C
    p = build_demo("imaging")
    acts = [a for a in p["activities"] if a.get("id")]
    res = S.compute(p)["cpm"]
    dc = C.deadline_check(acts, res, 18)
    assert dc["margin"] > 0 and dc["status"] in ("ok", "tight") and dc["tf_deadline"]["A12"] is None
    for a in acts:
        if a["id"] == "A5":
            a["most_likely"], a["pessimistic"] = 12, 18
    res2 = C.cpm(acts)
    assert res2["duration"] > 22                      # no cap at the 18-month target
    dc2 = C.deadline_check(acts, res2, 18)
    assert dc2["status"] == "late" and dc2["margin"] < 0 and "A5" in dc2["behind"]
    crit = res2["critical_path"][0]
    assert abs(dc2["tf_deadline"][crit] - dc2["margin"]) < 1e-9
    assert C.deadline_check(acts, res2, None) is None
