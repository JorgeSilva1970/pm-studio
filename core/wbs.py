"""WBS / EAP (Work Breakdown Structure / Estrutura Analítica do Projeto).

* The hierarchy is given by the code ("1", "1.2", "1.2.3"); the project itself is the implicit root ("0").
* Activities are attached to the leaves (work packages) through activity.wbs_code.
* Costs, dates, progress and earned value are rolled up **bottom-up from the activities only**: WBS elements hold no
  cost of their own, so nothing is ever counted twice.
* Rule checks (100% rule, 8/80 or reporting-period rule, single-child, dictionary completeness, logframe coherence) are
  quality warnings — they never block the rest of the app.
"""
from __future__ import annotations

import math
import re

from .i18n import opt_label, tr
from .model import activity_cost

CODE_RE = re.compile(r"^\d+(\.\d+)*$")
HOURS_PER_DAY = 8.0


# ============================================================================ code helpers
def key(code: str) -> tuple:
    out = []
    for part in str(code).split("."):
        out.append((0, int(part), "") if part.isdigit() else (1, 0, part))
    return tuple(out)


def parent_of(code: str) -> str:
    code = str(code)
    return code.rsplit(".", 1)[0] if "." in code else "0"


def level(code: str) -> int:
    return str(code).count(".") + 1


def is_under(code: str, anc: str) -> bool:
    code, anc = str(code), str(anc)
    return anc == "0" or code == anc or code.startswith(anc + ".")


def elements(p: dict) -> list[dict]:
    return sorted([e for e in p.get("wbs", []) if str(e.get("code") or "").strip()], key=lambda e: key(e["code"]))


def children(p: dict, code: str) -> list[dict]:
    return [e for e in elements(p) if parent_of(e["code"]) == str(code)]


def leaves(p: dict) -> list[dict]:
    els = elements(p)
    codes = [e["code"] for e in els]
    return [e for e in els if not any(parent_of(c) == e["code"] for c in codes)]


def next_child_code(p: dict, parent: str) -> str:
    kids = [e["code"] for e in elements(p) if parent_of(e["code"]) == str(parent)]
    n = 1 + max([int(k.rsplit(".", 1)[-1]) for k in kids if k.rsplit(".", 1)[-1].isdigit()] or [0])
    return str(n) if str(parent) in ("", "0") else f"{parent}.{n}"


def label(e: dict) -> str:
    return f"{e['code']} {e.get('name', '')}".strip()


def leaf_options(p: dict) -> list[str]:
    return [""] + [e["code"] for e in leaves(p)]


def all_options(p: dict) -> list[str]:
    return [""] + [e["code"] for e in elements(p)]


# ============================================================================ generation from the logframe
def _row(code, name, typ, output_code="", description="", deliverable="", acceptance="", owner=""):
    return {"code": code, "name": name[:120], "type": typ, "output_code": output_code, "description": description, "deliverable": deliverable,
            "acceptance": acceptance, "owner": owner, "weight": None}


SUPPORT_NAMES = {"Support - Management": ("Gestão do projeto", "Project management"), "Support - M&E": ("Monitorização e avaliação", "Monitoring & evaluation"),
                 "Support - Communication": ("Comunicação e visibilidade", "Communication & visibility"), "Support - Events": ("Eventos", "Events"),
                 "Support - Risk prevention": ("Prevenção de riscos", "Risk prevention")}


def generate(p: dict, orientation: str = "deliverables") -> tuple[list[dict], dict]:
    """Return (wbs rows, {activity_id: wbs_code}) built from the logframe and the activity types."""
    objs = p.get("objectives", [])
    outcomes = [o for o in objs if o.get("level") == "Outcome"]
    outputs = [o for o in objs if o.get("level") == "Output"]
    acts = p.get("activities", [])
    out_codes = {str(o["code"]) for o in outputs}
    rows, assign = [], {}

    def attach(code, pred):
        for a in acts:
            if a["id"] not in assign and pred(a):
                assign[a["id"]] = code

    is_support = lambda a: str(a.get("type") or "").startswith("Support")  # noqa: E731
    orphan_prod = [a for a in acts if not is_support(a) and str(a.get("output_code") or "") not in out_codes]
    support_types = [t for t in SUPPORT_NAMES if any(a.get("type") == t for a in acts)] + \
                    sorted({a.get("type") for a in acts if is_support(a) and a.get("type") not in SUPPORT_NAMES})
    sname = lambda t: tr(*SUPPORT_NAMES[t]) if t in SUPPORT_NAMES else opt_label("activity_type", t)  # noqa: E731

    if orientation == "phases":
        k = 0
        if any(a.get("type") == "Support - Management" for a in acts):
            k += 1
            rows.append(_row(str(k), tr("Iniciação e planeamento", "Initiation & planning"), "Phase"))
            rows.append(_row(f"{k}.1", tr("Gestão do projeto", "Project management"), "Work package",
                             deliverable=tr("Plano do projeto aprovado; relatórios de gestão", "Approved project plan; management reports")))
            attach(f"{k}.1", lambda a: a.get("type") == "Support - Management")
        k += 1
        rows.append(_row(str(k), tr("Execução", "Execution"), "Phase"))
        j = 0
        for o in outputs:
            j += 1
            rows.append(_row(f"{k}.{j}", o["text"], "Work package", o["code"], deliverable=o["text"]))
            attach(f"{k}.{j}", lambda a, c=str(o["code"]): not is_support(a) and str(a.get("output_code") or "") == c)
        if orphan_prod:
            j += 1
            rows.append(_row(f"{k}.{j}", tr("Outras atividades de produção", "Other production activities"), "Work package"))
            attach(f"{k}.{j}", lambda a: not is_support(a))
        for t in [t for t in support_types if t not in ("Support - Management", "Support - M&E", "Support - Communication")]:
            j += 1
            rows.append(_row(f"{k}.{j}", sname(t), "Work package"))
            attach(f"{k}.{j}", lambda a, t=t: a.get("type") == t)
        if any(a.get("type") == "Support - M&E" for a in acts):
            k += 1
            rows.append(_row(str(k), tr("Monitorização e controlo", "Monitoring & control"), "Phase"))
            rows.append(_row(f"{k}.1", tr("Monitorização e avaliação", "Monitoring & evaluation"), "Work package",
                             deliverable=tr("Relatórios de progresso e de avaliação", "Progress and evaluation reports")))
            attach(f"{k}.1", lambda a: a.get("type") == "Support - M&E")
        if any(a.get("type") == "Support - Communication" for a in acts):
            k += 1
            rows.append(_row(str(k), tr("Comunicação e encerramento", "Communication & closure"), "Phase"))
            rows.append(_row(f"{k}.1", tr("Comunicação e visibilidade", "Communication & visibility"), "Work package",
                             deliverable=tr("Produtos de comunicação e disseminação", "Communication and dissemination products")))
            attach(f"{k}.1", lambda a: a.get("type") == "Support - Communication")
    else:
        k = 0
        placed = set()
        for oc in outcomes:
            kids = [o for o in outputs if str(o.get("parent")) == str(oc["code"])]
            k += 1
            rows.append(_row(str(k), oc["text"], "Control account", oc["code"], deliverable=oc["text"]))
            for j, o in enumerate(kids, 1):
                rows.append(_row(f"{k}.{j}", o["text"], "Work package", o["code"], deliverable=o["text"]))
                attach(f"{k}.{j}", lambda a, c=str(o["code"]): not is_support(a) and str(a.get("output_code") or "") == c)
                placed.add(str(o["code"]))
        rest = [o for o in outputs if str(o["code"]) not in placed]
        items = [(o["text"], o["code"], o["text"]) for o in rest]
        if orphan_prod:
            items.append((tr("Outras atividades de produção", "Other production activities"), "", ""))
        if items and outcomes:
            k += 1
            rows.append(_row(str(k), tr("Outros resultados", "Other results"), "Control account"))
            codes = [f"{k}.{j}" for j in range(1, len(items) + 1)]
        else:
            codes = [str(k + j) for j in range(1, len(items) + 1)]
            k += len(items)
        for code, (name, oc, dl) in zip(codes, items):
            rows.append(_row(code, name, "Work package", oc, deliverable=dl))
            if oc:
                attach(code, lambda a, c=str(oc): not is_support(a) and str(a.get("output_code") or "") == c)
            else:
                attach(code, lambda a: not is_support(a))
        if support_types:
            k += 1
            rows.append(_row(str(k), tr("Gestão e apoio ao projeto", "Project management & support"), "Control account"))
            for j, t in enumerate(support_types, 1):
                rows.append(_row(f"{k}.{j}", sname(t), "Work package"))
                attach(f"{k}.{j}", lambda a, t=t: a.get("type") == t)
    return rows, assign


def apply_generated(p: dict, orientation: str = "deliverables") -> int:
    from .model import _coerce_row, empty_row
    rows, assign = generate(p, orientation)
    p["wbs"] = [_coerce_row("wbs", {**empty_row("wbs"), **r}) for r in rows]
    for a in p.get("activities", []):
        a["wbs_code"] = assign.get(a["id"], "")
    p["meta"]["wbs_orientation"] = orientation
    return len(rows)


def auto_assign(p: dict) -> int:
    """Attach unassigned activities to a work package: 1) the package whose scope description names the activity id
    (e.g. "Inclui: A1, A2"); 2) the package that carries its output; 3) a support package of the same type."""
    lv = leaves(p)
    valid = {e["code"] for e in lv}
    named = {}
    for e in lv:
        for aid in re.findall(r"\b[A-Z]{1,3}\d+\b", str(e.get("description") or "")):
            named.setdefault(aid, []).append(e["code"])
    by_out = {}
    for e in lv:
        if e.get("output_code"):
            by_out.setdefault(str(e["output_code"]), e["code"])      # first package carrying the output
    n = 0
    for a in p.get("activities", []):
        if a.get("wbs_code") in valid:
            continue
        c = named[a["id"]][0] if len(named.get(a["id"], [])) >= 1 else None
        if not c and not str(a.get("type") or "").startswith("Support"):
            c = by_out.get(str(a.get("output_code") or ""))
        if not c and str(a.get("type") or "").startswith("Support"):
            nm = tr(*SUPPORT_NAMES[a["type"]]) if a["type"] in SUPPORT_NAMES else ""
            c = next((e["code"] for e in lv if nm and nm.lower() in str(e.get("name", "")).lower()), None)
        if c:
            a["wbs_code"] = c
            n += 1
    return n


def renumber(p: dict) -> dict:
    """Make codes sequential (1, 1.1, 1.2, 2…) keeping the tree; updates activities and risks. Returns {old: new}."""
    els = elements(p)
    mp, counters = {"0": "0"}, {}
    for e in els:
        par = parent_of(e["code"])
        npar = mp.get(par, "0")
        counters[npar] = counters.get(npar, 0) + 1
        mp[e["code"]] = str(counters[npar]) if npar == "0" else f"{npar}.{counters[npar]}"
    for e in p["wbs"]:
        if e.get("code") in mp:
            e["code"] = mp[e["code"]]
    for t in ("activities", "risks"):
        for r in p.get(t, []):
            if r.get("wbs_code") in mp:
                r["wbs_code"] = mp[r["wbs_code"]]
    if p.get("raci", {}).get("matrix_wbs"):
        p["raci"]["matrix_wbs"] = {mp.get(k, k): v for k, v in p["raci"]["matrix_wbs"].items()}
    return {k: v for k, v in mp.items() if k != v}


def delete(p: dict, code: str) -> None:
    """Delete an element and its descendants; its activities become unassigned."""
    p["wbs"] = [e for e in p["wbs"] if not is_under(e["code"], code)]
    for t in ("activities", "risks"):
        for r in p.get(t, []):
            if r.get("wbs_code") and is_under(r["wbs_code"], code):
                r["wbs_code"] = ""


# ============================================================================ roll-up (cost, dates, progress, EVM)
def rollup(p: dict, sched: dict | None = None, ev: dict | None = None) -> dict:
    """{code: metrics} for every element plus the root "0". Bottom-up from activities only."""
    acts = p.get("activities", [])
    cost = {a["id"]: activity_cost(p, a) for a in acts}
    tab = None
    if sched and sched.get("ok"):
        tab = sched["acts"].set_index("id")
    evt = ev["table"].set_index("id") if ev and ev.get("table") is not None else None
    els = [{"code": "0", "name": p["meta"].get("name", "")}] + elements(p)
    leaf_codes = {e["code"] for e in leaves(p)}
    out = {}
    for e in els:
        ids = [a["id"] for a in acts if a.get("wbs_code") and is_under(a["wbs_code"], e["code"])] if e["code"] != "0" else [a["id"] for a in acts]
        r = {"code": e["code"], "level": 0 if e["code"] == "0" else level(e["code"]), "leaf": e["code"] in leaf_codes, "acts": ids,
             "BAC": sum(cost.get(i, 0) for i in ids), "start": None, "finish": None, "ES": None, "EF": None, "duration": None,
             "critical": False, "PV": None, "EV": None, "AC": None, "CPI": None, "SPI": None, "pct": None}
        if tab is not None and ids:
            sub = tab.loc[[i for i in ids if i in tab.index]]
            if len(sub):
                r.update(start=sub["start"].min(), finish=sub["finish"].max(), ES=float(sub["ES"].min()), EF=float(sub["EF"].max()),
                         critical=bool(sub["critical"].any()))
                r["duration"] = r["EF"] - r["ES"]
        if evt is not None and ids:
            sub = evt.loc[[i for i in ids if i in evt.index]]
            pv, evv, ac = float(sub["PV"].sum()), float(sub["EV"].sum()), float(sub["AC"].sum())
            r.update(PV=pv, EV=evv, AC=ac, CPI=evv / ac if ac else None, SPI=evv / pv if pv else None, pct=evv / r["BAC"] if r["BAC"] else None)
        out[e["code"]] = r
    return out


# ============================================================================ checks (quality warnings — never blocking)
WORKDAYS_PER_UNIT = {"days": 1.0, "weeks": 5.0, "months": 21.67}      # 8/80 rule counts working time


def duration_limits(p: dict) -> tuple[float, float, str]:
    """(min, max) work-package duration in the project's time unit and the rule used."""
    from .schedule import UNIT_DAYS
    m = p["meta"]
    unit = m.get("time_unit", "weeks")
    rule = m.get("wbs_rule") or "auto"
    if rule == "auto":
        rule = "8/80" if unit == "days" else "reporting"
    if rule == "8/80":
        wpu = WORKDAYS_PER_UNIT.get(unit, 5.0)
        mn, mx = 8 / HOURS_PER_DAY / wpu, 80 / HOURS_PER_DAY / wpu
    else:
        mn, mx = 0.0, 30.4375 / UNIT_DAYS.get(unit, 7.0)      # reporting period = one month (the app's period)
    if m.get("wbs_max"):
        mx = float(m["wbs_max"])
    return mn, mx, rule


def rule_arithmetic(p: dict) -> str:
    """How the work-package size limit was obtained, with the numbers."""
    from .fmt import num, unit_label
    unit = p["meta"].get("time_unit", "weeks")
    u = unit_label(unit)
    mn, mx, rule = duration_limits(p)
    if p["meta"].get("wbs_max"):
        return tr(f"Limite máximo definido manualmente: {num(mx, 2)} {u}.", f"Maximum limit set manually: {num(mx, 2)} {u}.")
    if rule == "8/80":
        wpu = WORKDAYS_PER_UNIT.get(unit, 5.0)
        return tr(f"Regra 8/80: 8 h ÷ 8 h/dia = 1 dia útil; 80 h ÷ 8 h/dia = 10 dias úteis; ÷ {wpu:g} dias úteis por {u[:-1] if u.endswith('s') else u} → mín. {num(mn, 2)} e máx. {num(mx, 2)} {u}.",
                  f"8/80 rule: 8 h ÷ 8 h/day = 1 working day; 80 h ÷ 8 h/day = 10 working days; ÷ {wpu:g} working days per {u[:-1] if u.endswith('s') else u} → min {num(mn, 2)} and max {num(mx, 2)} {u}.")
    return tr(f"Regra do período de reporte: 1 mês = 30,44 dias = {num(mx, 2)} {u} (máximo por pacote).",
              f"Reporting-period rule: 1 month = 30.44 days = {num(mx, 2)} {u} (maximum per package).")


def checks(p: dict, sched: dict | None = None) -> list[dict]:
    out = []

    def add(sev, ref, pt, en):
        out.append({"sev": sev, "ref": ref, "module": "WBS", "msg": tr(pt, en)})
    els = elements(p)
    if not els:
        if p.get("activities"):
            add("warn", "", "Ainda não existe WBS: gere-a a partir do quadro lógico (página WBS / EAP).", "There is no WBS yet: generate it from the logframe (WBS / WBS page).")
        return out
    codes = [e["code"] for e in els]
    cset = set(codes)
    for c in sorted({c for c in codes if codes.count(c) > 1}, key=key):
        add("error", c, f"Código {c} repetido.", f"Code {c} is duplicated.")
    for c in codes:
        if not CODE_RE.match(c):
            add("warn", c, f"Código {c} fora do formato 1.2.3.", f"Code {c} is not in 1.2.3 format.")
        elif parent_of(c) != "0" and parent_of(c) not in cset:
            add("error", c, f"{c} não tem elemento-pai ({parent_of(c)}).", f"{c} has no parent element ({parent_of(c)}).")
    lv = {e["code"] for e in leaves(p)}
    acts = p.get("activities", [])
    # 100% rule
    noc = [a["id"] for a in acts if not a.get("wbs_code")]
    bad = [a["id"] for a in acts if a.get("wbs_code") and a["wbs_code"] not in cset]
    mid = [a["id"] for a in acts if a.get("wbs_code") in cset and a["wbs_code"] not in lv]
    if noc:
        add("warn", "", f"Regra dos 100%: atividades fora da WBS — {', '.join(noc)}.", f"100% rule: activities outside the WBS — {', '.join(noc)}.")
    if bad:
        add("error", "", f"Atividades com código WBS inexistente — {', '.join(bad)}.", f"Activities with a non-existent WBS code — {', '.join(bad)}.")
    if mid:
        add("warn", "", f"Atividades ligadas a um elemento que não é pacote de trabalho (tem filhos) — {', '.join(mid)}.",
            f"Activities linked to an element that is not a work package (it has children) — {', '.join(mid)}.")
    used = {a.get("wbs_code") for a in acts}
    for c in sorted(lv - used, key=key):
        add("warn", c, f"Regra dos 100%: o pacote {c} não tem atividades (trabalho sem plano).", f"100% rule: work package {c} has no activities (work without a plan).")
    for par in ["0"] + codes:
        kids = [e for e in els if parent_of(e["code"]) == par]
        if len(kids) == 1 and par != "0":
            add("info", par, f"{par} tem um só filho ({kids[0]['code']}) — decomposição desnecessária.", f"{par} has a single child ({kids[0]['code']}) — unnecessary decomposition.")
        w = [k.get("weight") for k in kids if k.get("weight") is not None]
        if w and abs(sum(w) - 100) > 0.5:
            add("warn", par, f"Regra dos 100%: os pesos dos filhos de {par if par != '0' else 'projeto'} somam {sum(w):.0f}% (devem somar 100%).",
                f"100% rule: weights of the children of {par if par != '0' else 'project'} add up to {sum(w):.0f}% (must be 100%).")
    # duration rule (one summary line, guidance only)
    if sched and sched.get("ok"):
        ro = rollup(p, sched)
        mn, mx, rule = duration_limits(p)
        from .fmt import num, unit_label
        unit = unit_label(p["meta"].get("time_unit", "weeks"))
        long_ = [f"{c} ({num(ro[c]['duration'], 1)})" for c in sorted(lv, key=key) if ro.get(c, {}).get("duration") is not None and ro[c]["duration"] > mx + 1e-9]
        short = [c for c in sorted(lv, key=key) if ro.get(c, {}).get("duration") and ro[c]["duration"] < mn - 1e-9]
        rn = "8/80" if rule == "8/80" else tr("do período de reporte", "reporting-period")
        if long_:
            ar = rule_arithmetic(p)
            add("info", "", f"Regra {rn}: pacotes com duração acima de {num(mx, 2)} {unit} — {', '.join(long_)}. ({ar} Duração do pacote = EF máx. − ES mín. das suas atividades.) Pacotes longos são mais difíceis de controlar; considere decompô-los ou definir marcos intermédios.",
                f"{rn} rule: work packages longer than {num(mx, 2)} {unit} — {', '.join(long_)}. ({ar} Package duration = max EF − min ES of its activities.) Long packages are harder to control; consider breaking them down or setting interim milestones.")
        if short:
            add("info", "", f"Regra {rn}: pacotes muito pequenos (< {num(mn, 2)} {unit}) — {', '.join(short)}; considere agregá-los.",
                f"{rn} rule: very small packages (< {num(mn, 2)} {unit}) — {', '.join(short)}; consider merging them.")
    # dictionary completeness (summary lines)
    noacc = [e["code"] for e in els if e["code"] in lv and not str(e.get("acceptance") or "").strip()]
    noown = [e["code"] for e in els if e["code"] in lv and not str(e.get("owner") or "").strip()]
    if noacc:
        add("info", "", f"Dicionário da WBS: pacotes sem critérios de aceitação — {', '.join(noacc)}.", f"WBS dictionary: packages without acceptance criteria — {', '.join(noacc)}.")
    if noown:
        add("info", "", f"Dicionário da WBS: pacotes sem responsável — {', '.join(noown)}.", f"WBS dictionary: packages without an owner — {', '.join(noown)}.")
    # coherence with the logframe
    linked = {str(e.get("output_code")) for e in els if e.get("output_code")}
    miss = [o["code"] for o in p.get("objectives", []) if o.get("level") == "Output" and str(o["code"]) not in linked]
    if miss:
        add("warn", "", f"Outputs do quadro lógico sem elemento na WBS: {', '.join(map(str, miss))}.", f"Logframe outputs without a WBS element: {', '.join(map(str, miss))}.")
    for r in p.get("risks", []):
        if r.get("wbs_code") and r["wbs_code"] not in cset:
            add("warn", r["id"], f"Risco {r['id']} ligado a um código WBS inexistente ({r['wbs_code']}).", f"Risk {r['id']} linked to a non-existent WBS code ({r['wbs_code']}).")
    return out


def rule100_ok(p: dict) -> bool:
    return not any(c["msg"].startswith(tr("Regra dos 100%", "100% rule")) or "WBS inexistente" in c["msg"] or "non-existent WBS" in c["msg"]
                   for c in checks(p) if c["sev"] in ("warn", "error"))


def summary_text(p: dict, ro: dict, cur: str = "EUR") -> str:
    from .fmt import money, num, pct
    els = elements(p)
    if not els:
        return ""
    lv = leaves(p)
    depth = max(level(e["code"]) for e in els)
    ch = checks(p)
    n_acts = len(p.get("activities", []))
    assigned = sum(1 for a in p.get("activities", []) if a.get("wbs_code") in {e["code"] for e in lv})
    txt = tr(f"WBS com **{len(els)} elementos** em **{depth} níveis** e **{len(lv)} pacotes de trabalho**; {assigned} de {n_acts} atividades ligadas a pacotes. ",
             f"WBS with **{len(els)} elements** across **{depth} levels** and **{len(lv)} work packages**; {assigned} of {n_acts} activities linked to packages. ")
    txt += (tr("✅ A regra dos 100% está cumprida (todo o trabalho planeado está na WBS e todos os pacotes têm trabalho). ",
               "✅ The 100% rule holds (all planned work is in the WBS and every package has work). ") if assigned == n_acts and not any("100" in c["msg"] for c in ch)
            else tr("⚠️ A regra dos 100% não está cumprida — ver verificações. ", "⚠️ The 100% rule does not hold — see checks. "))
    top = [ro[e["code"]] for e in els if level(e["code"]) == 1 and e["code"] in ro]
    if top and ro["0"]["BAC"]:
        big = max(top, key=lambda r: r["BAC"])
        name = next(e["name"] for e in els if e["code"] == big["code"])
        txt += tr(f"O ramo com maior peso é **{big['code']} {name[:60]}** ({money(big['BAC'], cur)}, {pct(big['BAC'] / ro['0']['BAC'], 0)} do BAC). ",
                  f"The heaviest branch is **{big['code']} {name[:60]}** ({money(big['BAC'], cur)}, {pct(big['BAC'] / ro['0']['BAC'], 0)} of BAC). ")
    bad = [r for c, r in ro.items() if c != "0" and r.get("CPI") is not None and r["CPI"] < 0.95 and r["leaf"]]
    late = [r for c, r in ro.items() if c != "0" and r.get("SPI") is not None and r["SPI"] < 0.95 and r["leaf"]]
    if bad:
        w = min(bad, key=lambda r: r["CPI"])
        txt += tr(f"Derrapagem de custo localizada em {', '.join(r['code'] for r in bad)} (pior: {w['code']}, CPI {num(w['CPI'], 2)}). ",
                  f"Cost overrun located in {', '.join(r['code'] for r in bad)} (worst: {w['code']}, CPI {num(w['CPI'], 2)}). ")
    if late:
        w = min(late, key=lambda r: r["SPI"])
        txt += tr(f"Atraso localizado em {', '.join(r['code'] for r in late)} (pior: {w['code']}, SPI {num(w['SPI'], 2)}).",
                  f"Delay located in {', '.join(r['code'] for r in late)} (worst: {w['code']}, SPI {num(w['SPI'], 2)}).")
    return txt


# ============================================================================ diagram (Graphviz DOT, org-chart style)
TYPE_COLOR = {"Project": "#1F3B57", "Phase": "#2C7FB8", "Deliverable": "#41AB5D", "Control account": "#2C7FB8", "Work package": "#EAF2F8"}


def _wrap(s: str, n: int = 24) -> str:
    words, lines, cur = str(s).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\\n".join(lines[:4]) + ("…" if len(lines) > 4 else "")


def dot(p: dict, ro: dict | None = None, depth: int = 9, rankdir: str = "TB", cur: str = "EUR", show_acts: bool = False) -> str:
    from .fmt import money, num
    els = [e for e in elements(p) if level(e["code"]) <= depth]
    unit = p["meta"].get("time_unit", "weeks")
    esc = lambda s: str(s).replace('"', '\\"')  # noqa: E731  (labels keep their \\n line breaks)
    lines = [f'digraph WBS {{ rankdir={rankdir}; splines=ortho; nodesep=0.25; ranksep=0.45; node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10, margin="0.12,0.06"]; edge [arrowhead=none, color="#7A8A99"];']
    r0 = (ro or {}).get("0", {})
    lines.append(f'"0" [label="{esc(_wrap(p["meta"].get("name") or tr("Projeto", "Project"), 30))}\\n{money(r0.get("BAC", 0), cur)}", fillcolor="#1F3B57", fontcolor="white", fontsize=12];')
    for e in els:
        r = (ro or {}).get(e["code"], {})
        info = []
        if r.get("BAC"):
            info.append(money(r["BAC"], cur))
        if r.get("duration") is not None:
            info.append(f"{num(r['duration'], 1)} {unit[:3]}")
        if r.get("CPI") is not None:
            info.append(f"CPI {num(r['CPI'], 2)}")
        typ = e.get("type") or "Work package"
        fill = TYPE_COLOR.get(typ, "#EAF2F8")
        font = "white" if typ in ("Project", "Phase", "Control account") else "#1F2933"
        pen = ' color="#C0392B", penwidth=2.2' if r.get("CPI") is not None and r["CPI"] < 0.95 else (' color="#C0392B", penwidth=1.5, style="rounded,filled,dashed"' if r.get("critical") and r.get("leaf") else "")
        lab = f"{e['code']}  {_wrap(e.get('name', ''))}" + ("\\n" + " · ".join(info) if info else "")
        lines.append(f'"{esc(e["code"])}" [label="{esc(lab)}", fillcolor="{fill}", fontcolor="{font}"{pen}];')
        lines.append(f'"{esc(parent_of(e["code"]))}" -> "{esc(e["code"])}";')
        if show_acts and r.get("leaf"):
            for aid in r.get("acts", [])[:12]:
                a = next((x for x in p["activities"] if x["id"] == aid), {})
                lines.append(f'"act_{esc(aid)}" [label="{esc(aid)} {esc(_wrap(a.get("name", ""), 20))}", shape=note, fillcolor="white", fontsize=9];')
                lines.append(f'"{esc(e["code"])}" -> "act_{esc(aid)}" [style=dashed];')
    lines.append("}")
    return "\n".join(lines)


def indented(p: dict, ro: dict | None = None) -> list[dict]:
    """Rows for an indented (outline) view, with roll-ups."""
    out = []
    for e in elements(p):
        r = (ro or {}).get(e["code"], {})
        out.append({"code": e["code"], "level": level(e["code"]), "name": e.get("name", ""), "type": e.get("type"), "leaf": r.get("leaf"),
                    "n_acts": len(r.get("acts", [])), "BAC": r.get("BAC"), "start": r.get("start"), "finish": r.get("finish"),
                    "duration": r.get("duration"), "pct": r.get("pct"), "PV": r.get("PV"), "EV": r.get("EV"), "AC": r.get("AC"),
                    "CPI": r.get("CPI"), "SPI": r.get("SPI"), "critical": r.get("critical")})
    return out


def dictionary(p: dict, code: str, ro: dict | None = None) -> dict:
    """Everything known about one WBS element (the WBS dictionary entry)."""
    e = next((x for x in elements(p) if x["code"] == code), None)
    if not e:
        return {}
    r = (ro or {}).get(code, {})
    ids = set(r.get("acts", []))
    acts = [a for a in p.get("activities", []) if a["id"] in ids]
    risks = [x for x in p.get("risks", []) if (x.get("wbs_code") and is_under(x["wbs_code"], code)) or (x.get("preventive_activity") in ids)]
    ms = [m for m in p.get("milestones", []) if m.get("activity_id") in ids]
    bud = [b for b in p.get("budget", []) if b.get("activity_id") in ids]
    proc = [q for q in p.get("procurement", []) if q.get("activity_id") in ids]
    raci = p.get("raci", {}).get("matrix_wbs", {}).get(code, {})
    out_text = next((o["text"] for o in p.get("objectives", []) if str(o["code"]) == str(e.get("output_code"))), "")
    return {"element": e, "rollup": r, "activities": acts, "risks": risks, "milestones": ms, "budget": bud, "procurement": proc,
            "raci": {k: v for k, v in raci.items() if v}, "output_text": out_text,
            "parent": next((x for x in elements(p) if x["code"] == parent_of(code)), None), "children": children(p, code)}


def enrich_dictionary(p: dict, overwrite: bool = False) -> int:
    """Fill empty dictionary fields of work packages from the project data (owner, scope, deliverable, acceptance criteria)."""
    from collections import Counter
    n = 0
    lv = {e["code"] for e in leaves(p)}
    for e in p.get("wbs", []):
        if e.get("code") not in lv:
            continue
        acts = [a for a in p.get("activities", []) if a.get("wbs_code") == e["code"]]
        resp = Counter(a.get("responsible") for a in acts if a.get("responsible")).most_common(1)
        inds = [i for i in p.get("indicators", []) if e.get("output_code") and str(i.get("objective_code")) == str(e["output_code"])]
        upd = {}
        if resp:
            upd["owner"] = resp[0][0]
        if acts:
            upd["description"] = tr("Inclui: ", "Includes: ") + "; ".join(f"{a['id']} {a.get('name', '')}" for a in acts)
        if not e.get("deliverable") and e.get("output_code"):
            upd["deliverable"] = e.get("name", "")
        acc = [f"{i['id']}: {i.get('indicator', '')[:70]} = {i.get('target')}{(' ' + i['unit']) if i.get('unit') else ''}" for i in inds if i.get("target") is not None]
        upd["acceptance"] = (tr("Metas atingidas — ", "Targets met — ") + "; ".join(acc) + ". " if acc else "") +             tr("Entregável verificado e aceite formalmente pelo patrocinador/comité.", "Deliverable verified and formally accepted by the sponsor/committee.")
        for k, v in upd.items():
            if v and (overwrite or not str(e.get(k) or "").strip()):
                e[k] = v
                n += 1
    return n


def explain(p: dict, code: str, ro: dict, ev: dict | None = None, cur: str = "EUR") -> str:
    """Markdown showing how each indicator of one element was obtained, with the real numbers."""
    from .fmt import money, num, pct, unit_label
    from .help_texts import wbs_term
    r = ro.get(code)
    if not r:
        return ""
    u = unit_label(p["meta"].get("time_unit", "weeks"))
    names = {a["id"]: a.get("name", "") for a in p.get("activities", [])}
    evt = ev["table"].set_index("id") if ev and ev.get("table") is not None else None
    kids = [k for k in children(p, code)] if code != "0" else [e for e in elements(p) if level(e["code"]) == 1]
    ids = r["acts"]
    lines = []
    n = lambda k: f"**{wbs_term(k)[0]}**"  # noqa: E731
    # BAC
    if kids:
        parts = " + ".join(f"{k['code']} ({money(ro[k['code']]['BAC'], cur)})" for k in kids)
        lines.append(f"- {n('bac')} = {tr('Σ BAC dos filhos', 'Σ children BAC')} = {parts} = **{money(r['BAC'], cur)}**")
    elif ids:
        from .model import activity_cost
        acts = {a["id"]: a for a in p.get("activities", [])}
        parts = " + ".join(f"{i} ({money(activity_cost(p, acts[i]), cur)})" for i in ids)
        lines.append(f"- {n('bac')} = {tr('Σ custo das atividades', 'Σ activity costs')} = {parts} = **{money(r['BAC'], cur)}**")
    else:
        lines.append(f"- {n('bac')} = 0 — " + tr("pacote sem atividades (viola a regra dos 100%).", "package without activities (breaks the 100% rule)."))
    if code != "0" and ro["0"]["BAC"]:
        lines.append(f"- {n('pct_bac')} = {money(r['BAC'], cur)} ÷ {money(ro['0']['BAC'], cur)} = **{pct(r['BAC'] / ro['0']['BAC'])}**")
    # dates & duration
    if r.get("ES") is not None and ids:
        sched_acts = None
        try:
            from .schedule import compute
            sc = compute(p)
            sched_acts = sc["acts"].set_index("id") if sc.get("ok") else None
        except Exception:
            pass
        if sched_acts is not None:
            sub = sched_acts.loc[[i for i in ids if i in sched_acts.index]]
            i_es, i_ef = sub["ES"].idxmin(), sub["EF"].idxmax()
            lines.append(f"- {n('duration')} = {tr('EF máx.', 'max EF')} ({i_ef}: {num(r['EF'], 1)}) − {tr('ES mín.', 'min ES')} ({i_es}: {num(r['ES'], 1)}) = **{num(r['duration'], 1)} {u}**"
                         + (tr(f" (a soma simples das durações seria {num(float(sub['D'].sum()), 1)} — maior porque há atividades em paralelo)",
                               f" (the simple sum of durations would be {num(float(sub['D'].sum()), 1)} — larger because activities run in parallel)") if float(sub["D"].sum()) > r["duration"] + 0.05 else ""))
            crit = [i for i in sub.index if bool(sub.loc[i, "critical"])]
            lines.append(f"- {n('critical')}: " + (tr(f"sim — atividades críticas (folga total 0): {', '.join(crit)}", f"yes — critical activities (total float 0): {', '.join(crit)}") if crit
                                                     else tr("não — todas as atividades têm folga", "no — every activity has float")))
    # EVM
    if evt is not None and ids and r.get("EV") is not None:
        sub = evt.loc[[i for i in ids if i in evt.index]]
        if len(sub) <= 8:
            parts = " + ".join(f"{i} ({money(float(sub.loc[i, 'BAC']), cur)} × {pct(float(sub.loc[i, 'pct_complete'] or 0), 0)})" for i in sub.index)
            lines.append(f"- {n('ev')} = Σ (BAC × % {tr('concl.', 'done')}) = {parts} = **{money(r['EV'], cur)}**")
        else:
            lines.append(f"- {n('ev')} = Σ (BAC × % {tr('concl.', 'done')}) {tr('de', 'of')} {len(sub)} {tr('atividades', 'activities')} = **{money(r['EV'], cur)}**")
        lines.append(f"- {n('pv')} = Σ PV {tr('das atividades à data de controlo', 'of the activities at the status date')} ({p['meta'].get('status_date')}) = **{money(r['PV'], cur)}**")
        lines.append(f"- {n('ac')} = Σ {tr('custo real', 'actual cost')} = **{money(r['AC'], cur)}**")
        if r["BAC"]:
            avg = float(sub["pct_complete"].fillna(0).mean()) if len(sub) else 0
            lines.append(f"- {n('pct')} = EV ÷ BAC = {money(r['EV'], cur)} ÷ {money(r['BAC'], cur)} = **{pct(r['pct'])}**"
                         + (tr(f" (a média simples das % seria {pct(avg)})", f" (the simple average of % would be {pct(avg)})") if abs(avg - (r["pct"] or 0)) > 0.005 else ""))
        if r.get("CPI") is not None:
            msg = tr("custo acima do orçamentado" if r["CPI"] < 1 else "custo dentro ou abaixo do orçamento", "over budget" if r["CPI"] < 1 else "on or under budget")
            lines.append(f"- {n('cpi')} = Σ EV ÷ Σ AC = {money(r['EV'], cur)} ÷ {money(r['AC'], cur)} = **{num(r['CPI'], 2)}** → {msg}"
                         + tr(f" (cada 1 € gasto produziu {num(r['CPI'], 2)} € de trabalho)", f" (each €1 spent produced €{num(r['CPI'], 2)} of work)"))
        if r.get("SPI") is not None:
            lines.append(f"- {n('spi')} = Σ EV ÷ Σ PV = {money(r['EV'], cur)} ÷ {money(r['PV'], cur)} = **{num(r['SPI'], 2)}** → "
                         + tr("atrasado face ao plano" if r["SPI"] < 1 else "no prazo ou adiantado", "behind plan" if r["SPI"] < 1 else "on or ahead of schedule"))
        if len(sub) > 1:
            cp = [float(x) for x in sub["CPI"] if x == x and x is not None]
            if cp and r.get("CPI") is not None and abs(sum(cp) / len(cp) - r["CPI"]) > 0.005:
                lines.append(tr(f"  - ⚠️ A média simples dos CPI das atividades seria {num(sum(cp) / len(cp), 2)} — errado, porque ignora o peso de cada atividade.",
                                f"  - ⚠️ The simple average of the activities' CPIs would be {num(sum(cp) / len(cp), 2)} — wrong, because it ignores each activity's weight."))
    elif ids:
        lines.append(tr("- EVM (PV, EV, AC, CPI, SPI): disponível quando a rede de atividades estiver completa.", "- EVM (PV, EV, AC, CPI, SPI): available once the activity network is complete."))
    return "\n".join(lines)


def nan_to_none(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else v
