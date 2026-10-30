"""HTML rendering of the Logframe matrix (vertical, horizontal and diagonal logic)."""
from __future__ import annotations

import html

from .fmt import money, num
from .i18n import opt_label, tr
from .model import MATRIX_ROW_OF_ASSUMPTION, activity_cost, indicator_dimension

CSS = """
<style>
.lf {border-collapse:collapse;width:100%;font-size:0.86rem}
.lf th{background:#1F3B57;color:#fff;padding:6px 8px;text-align:left;vertical-align:bottom}
.lf td{border:1px solid #D5DDE5;padding:6px 8px;vertical-align:top}
.lf td.lvl{font-weight:700;color:#fff;width:9%}
.lf .Impact{background:#B03A2E}.lf .Outcome{background:#D9822B}.lf .Output{background:#C9A227}.lf .Activity{background:#3C8DBC}.lf .Input{background:#2E4A7D}
.lf .code{font-weight:700;color:#1F3B57}
.lf .asm{background:#FFF8DC}
.lf small{color:#666}
</style>"""


def _e(s):
    return html.escape(str(s if s is not None else ""))


def _n(v):
    try:
        f = float(v)
        return num(f, 0 if f == int(f) else 2)
    except Exception:
        return "—"


def _ind_cell(inds):
    if not inds:
        return "<small>—</small>", "", "", ""
    i_txt = "<br>".join(f"<b>{_e(i['id'])}</b> {_e(i['indicator'])} <small>({_e(i.get('unit'))})</small>" for i in inds)
    b = "<br>".join(f"{_e(_n(i.get('baseline')) if i.get('baseline') is not None else '—')} <small>{_e(i.get('baseline_year') or '')}</small>" for i in inds)
    t = "<br>".join(f"{_e(_n(i.get('target')) if i.get('target') is not None else '—')} <small>{_e(i.get('target_year') or '')}</small>" for i in inds)
    s = "<br>".join(_e(i.get("source")) for i in inds)
    return i_txt, b, t, s


def logframe_html(p: dict, include_activities: bool = True) -> str:
    objs = p.get("objectives", [])
    inds = p.get("indicators", [])
    asm = p.get("assumptions", [])
    cur = p["meta"].get("currency", "EUR")
    by_obj = {}
    for i in inds:
        by_obj.setdefault(str(i.get("objective_code")), []).append(i)
    lvl_of = {str(o["code"]): o["level"] for o in objs}
    # assumptions shown on the row below the level they condition
    asm_row = {}
    for h in asm:
        oc = str(h.get("objective_code") or "")
        lvl = lvl_of.get(oc)
        if not lvl:
            continue
        row_lvl = MATRIX_ROW_OF_ASSUMPTION.get(lvl)
        if row_lvl == "Activity":
            key = ("Activity", oc)  # activities of that output
        else:
            # find children of oc at row_lvl -> show on each child? show once on first child
            children = [o for o in objs if str(o.get("parent")) == oc and o["level"] == row_lvl]
            key = (row_lvl, str(children[0]["code"])) if children else (row_lvl, None)
        asm_row.setdefault(key, []).append(h)

    def asm_cell(key):
        hs = asm_row.get(key, [])
        if not hs:
            return ""
        return "<br>".join(f"<b>{_e(h['id'])}</b> <small>[{_e(opt_label('assumption_type', h.get('type')))}]</small> {_e(h.get('text'))}" for h in hs)

    head = (f"<table class='lf'><tr><th></th><th>{tr('Lógica de intervenção', 'Intervention logic')}</th>"
            f"<th>{tr('Indicadores', 'Indicators')}</th><th>Baseline</th><th>{tr('Meta', 'Target')}</th>"
            f"<th>{tr('Fontes de verificação', 'Sources of verification')}</th><th>{tr('Pressupostos', 'Assumptions')}</th>"
            f"<th>{tr('Critério', 'Criterion')}</th></tr>")
    rows = []
    lvl_name = {"Impact": tr("Impacto", "Impact"), "Outcome": "Outcome", "Output": "Output", "Activity": tr("Atividades", "Activities"), "Input": tr("Recursos", "Inputs")}
    crit_name = {"Impact": tr("Impacto e Sustentabilidade", "Impact & Sustainability"), "Outcome": tr("Eficácia", "Effectiveness"),
                 "Output": tr("Eficiência", "Efficiency"), "Activity": tr("Eficiência", "Efficiency"), "Input": tr("Eficiência / custos", "Efficiency / costs")}
    for lvl in ("Impact", "Outcome", "Output"):
        for o in [o for o in objs if o["level"] == lvl]:
            it, b, t, s = _ind_cell(by_obj.get(str(o["code"]), []))
            a = "<small>" + tr("(não aplicável ao impacto)", "(not applicable at impact level)") + "</small>" if lvl == "Impact" else asm_cell((lvl, str(o["code"])))
            rows.append(f"<tr><td class='lvl {lvl}'>{lvl_name[lvl]}</td><td><span class='code'>{_e(o['code'])}</span> {_e(o['text'])}</td>"
                        f"<td>{it}</td><td>{b}</td><td>{t}</td><td>{s}</td><td class='asm'>{a}</td><td><small>{crit_name[lvl]}</small></td></tr>")
    if include_activities:
        acts = p.get("activities", [])
        outs = [o for o in objs if o["level"] == "Output"]
        for o in outs:
            al = [a for a in acts if str(a.get("output_code")) == str(o["code"])]
            if not al and not asm_row.get(("Activity", str(o["code"]))):
                continue
            txt = "<br>".join(f"<b>{_e(a['id'])}</b> {_e(a.get('name'))}" for a in al) or "—"
            cost = sum(activity_cost(p, a) for a in al)
            rows.append(f"<tr><td class='lvl Activity'>{lvl_name['Activity']} {_e(o['code'])}</td><td>{txt}</td>"
                        f"<td colspan='4'><small>{tr('Meios', 'Means')}: {tr('ver orçamento', 'see budget')} · {tr('Custo', 'Cost')}: <b>{money(cost, cur)}</b></small></td>"
                        f"<td class='asm'>{asm_cell(('Activity', str(o['code'])))}</td><td><small>{crit_name['Activity']}</small></td></tr>")
        other = [a for a in acts if str(a.get("output_code")) not in {str(o['code']) for o in outs}]
        if other:
            txt = "<br>".join(f"<b>{_e(a['id'])}</b> {_e(a.get('name'))} <small>({_e(opt_label('activity_type', a.get('type')))})</small>" for a in other)
            cost = sum(activity_cost(p, a) for a in other)
            rows.append(f"<tr><td class='lvl Activity'>{tr('Atividades de apoio', 'Support activities')}</td><td>{txt}</td>"
                        f"<td colspan='4'><small>{tr('Custo', 'Cost')}: <b>{money(cost, cur)}</b></small></td><td class='asm'></td><td></td></tr>")
        total = sum(activity_cost(p, a) for a in acts)
        rows.append(f"<tr><td class='lvl Input'>{lvl_name['Input']}</td><td>{tr('Materiais · Maquinaria · Mão de obra · Money (4 Ms)', 'Materials · Machinery · Manpower · Money (4 Ms)')}</td>"
                    f"<td colspan='4'>{tr('Orçamento total das atividades (BAC)', 'Total activity budget (BAC)')}: <b>{money(total, cur)}</b></td><td></td><td><small>{crit_name['Input']}</small></td></tr>")
    return CSS + head + "".join(rows) + "</table>"
