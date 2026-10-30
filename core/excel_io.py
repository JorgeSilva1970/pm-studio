"""Excel import/export.

1. Professor's templates, filled in their ORIGINAL format (StakeholderRegister, RiskRegister).
2. Extended workbook ("modelo alargado") with every module, live Excel formulas and re-importable headers.
"""
from __future__ import annotations

import io
import os
import re
from copy import copy

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

from . import analysis as AN
from . import cpm as C
from . import finance as F
from . import schedule as S
from .i18n import OPTIONS, opt_codes, tr
from .model import TABLES, _coerce_row, activity_cost, empty_row, ensure_ids, indicator_dimension, objective_level

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(HERE, "templates")

FONT = "Arial"
HDR = PatternFill("solid", fgColor="1F3B57")
SUB = PatternFill("solid", fgColor="D9E1F2")
TOT = PatternFill("solid", fgColor="F2F2F2")
YEL = PatternFill("solid", fgColor="FFFF00")
thin = Side(style="thin", color="BFBFBF")
BD = Border(left=thin, right=thin, top=thin, bottom=thin)
EUR = '#,##0;(#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'

LIK = {4: "Almost certain", 3: "Likely", 2: "Possible", 1: "Unlikely"}
IMP = {4: "Severe", 3: "Major", 2: "Moderate", 1: "Minor"}


# =============================================================================== professor's templates
def professor_stakeholders(p: dict) -> tuple[bytes, list[str]]:
    wb = load_workbook(os.path.join(TPL, "StakeholderRegister_template.xlsx"))
    ws = wb["StakeholderRegister"]
    rows = p.get("stakeholders", [])
    warn = []
    first, last = 6, 18  # template rows available above "DO NOT CREATE ANY NEW ROWS BELOW THIS ROW"
    cap = last - first + 1
    if len(rows) > cap:
        warn.append(tr(f"O modelo do professor tem {cap} linhas; {len(rows) - cap} stakeholders seguem apenas no modelo alargado.",
                       f"The professor's template has {cap} rows; {len(rows) - cap} stakeholders go only to the extended template."))
    for r in range(first, last + 1):
        for c in "BCDEF":
            ws[f"{c}{r}"].value = None
    for k, s in enumerate(rows[:cap]):
        r = first + k
        ws[f"B{r}"] = s.get("name")
        ws[f"C{r}"] = s.get("type")
        ws[f"D{r}"] = s.get("benefits_to_project")
        ws[f"E{r}"] = s.get("benefits_of_project")
        ws[f"F{r}"] = s.get("engagement")
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue(), warn


def professor_risks(p: dict) -> tuple[bytes, list[str]]:
    wb = load_workbook(os.path.join(TPL, "RiskRegister_Template.xlsx"))
    ws = wb["RiskRegister"]
    rows = sorted(p.get("risks", []), key=lambda r: -AN.exposure(r))
    warn = []
    first, last = 11, 18
    cap = last - first + 1
    if len(rows) > cap:
        warn.append(tr(f"O modelo do professor tem {cap} linhas; os {len(rows) - cap} riscos menos expostos seguem apenas no modelo alargado.",
                       f"The professor's template has {cap} rows; the {len(rows) - cap} least exposed risks go only to the extended template."))
    for r in range(first, last + 1):
        for c in "BCDGJKLMNOPQ":
            ws[f"{c}{r}"].value = None
    for k, x in enumerate(rows[:cap]):
        r = first + k
        ws[f"B{r}"] = x.get("type")
        ws[f"C{r}"] = x.get("description")
        ws[f"D{r}"] = LIK.get(int(x.get("likelihood") or 0))
        ws[f"G{r}"] = IMP.get(int(x.get("impact") or 0))
        # exposure = likelihood x impact, using the template's own key lists (D264:D267 / G264:G267)
        ws[f"J{r}"] = f'=IFERROR((5-MATCH(D{r},$D$264:$D$267,0))*(5-MATCH(G{r},$G$264:$G$267,0)),"")'
        ws[f"K{r}"] = x.get("target_exposure")
        ws[f"L{r}"] = x.get("existing_mitigation")
        ws[f"M{r}"] = x.get("proposed_mitigation")
        ws[f"N{r}"] = x.get("risk_manager")
        ws[f"O{r}"] = x.get("risk_owner")
        ws[f"P{r}"] = x.get("review_by")
        ws[f"Q{r}"] = x.get("review")
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue(), warn


# =============================================================================== extended workbook
def _font(c, bold=False, color=None, italic=False, size=None):
    c.font = Font(name=FONT, bold=bold, color=color, italic=italic, size=size or 10)


def _title(ws, text, sub=None):
    ws["A1"] = text
    _font(ws["A1"], bold=True, size=14)
    if sub:
        ws["A2"] = sub
        _font(ws["A2"], italic=True, color="595959")


def _table(ws, row0: int, headers: list[tuple[str, str]], rows: list[list], widths: dict | None = None, wrap_cols=()):
    """headers: list of (label, field). Writes 'label [field]' so the sheet can be re-imported."""
    for j, (lab, field) in enumerate(headers, 1):
        c = ws.cell(row0, j, f"{lab} [{field}]" if field else lab)
        _font(c, bold=True, color="FFFFFF")
        c.fill = HDR
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BD
    for i, r in enumerate(rows, 1):
        for j, v in enumerate(r, 1):
            c = ws.cell(row0 + i, j, v)
            is_formula = isinstance(v, str) and v.startswith("=")
            _font(c, color="000000" if is_formula else "0000FF")
            c.border = BD
            if j in wrap_cols:
                c.alignment = Alignment(wrap_text=True, vertical="top")
    for j in range(1, len(headers) + 1):
        ws.column_dimensions[L(j)].width = (widths or {}).get(j, 16)
    ws.freeze_panes = ws.cell(row0 + 1, 1)
    return row0 + len(rows)


def extended_workbook(p: dict) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Leia-me"
    m = p["meta"]
    lines = [(tr("Modelo alargado de gestão de projeto", "Extended project management template"), True),
             (m.get("name", ""), True), ("", False),
             (tr("Este livro complementa os modelos do professor (StakeholderRegister e RiskRegister), que são exportados à parte no formato original.",
                 "This workbook complements the professor's templates (StakeholderRegister and RiskRegister), exported separately in their original format."), False),
             (tr("Cada folha corresponde a um módulo da app. Os cabeçalhos têm o código do campo entre [ ] para permitir voltar a importar o ficheiro na app.",
                 "Each sheet is an app module. Headers carry the field code in [ ] so the file can be re-imported into the app."), False),
             (tr("Legenda: texto azul = valores introduzidos; texto preto = fórmulas Excel; fundo amarelo = pressupostos-chave.",
                 "Legend: blue text = inputs; black text = Excel formulas; yellow fill = key assumptions."), False), ("", False),
             (tr("Folhas: Projeto · Stakeholders · Comportamento · Problemas-Objetivos · Logframe · Indicadores · Benchmarking · Pressupostos · Atividades-PERT · Gantt-Custos · EVM · RACI · Riscos · Matriz de risco · Orçamento · Procurement · Finanças · Avaliação",
                 "Sheets: Project · Stakeholders · Behaviour · Problems-Objectives · Logframe · Indicators · Benchmarking · Assumptions · Activities-PERT · Gantt-Costs · EVM · RACI · Risks · Risk matrix · Budget · Procurement · Finance · Evaluation"), False),
             ("", False), (tr("Fontes: EuropeAid (2004) PCM Guidelines; CE (2016) PM²; Hivos (2015) ToC; Morra Imas & Rist (2009); CE DG INTPA (2025) Evaluation Handbook; materiais da unidade curricular.",
                              "Sources: EuropeAid (2004) PCM Guidelines; EC (2016) PM²; Hivos (2015) ToC; Morra Imas & Rist (2009); EC DG INTPA (2025) Evaluation Handbook; course materials."), False)]
    for i, (t, b) in enumerate(lines, 1):
        ws.cell(i, 1, t)
        _font(ws.cell(i, 1), bold=b, size=14 if i == 1 else 10)
        ws.cell(i, 1).alignment = Alignment(wrap_text=True)
    ws.column_dimensions["A"].width = 130

    # project
    ws = wb.create_sheet("Projeto")
    _title(ws, tr("Dados do projeto", "Project data"))
    meta_rows = [[k, str(v)] for k, v in m.items()]
    _table(ws, 3, [(tr("Campo", "Field"), "key"), (tr("Valor", "Value"), "value")], meta_rows, {1: 26, 2: 80})

    # stakeholders
    ws = wb.create_sheet("Stakeholders")
    _title(ws, "Stakeholder register (alargado / extended)", tr("Colunas do modelo do professor + 4 camadas PCM + influência/interesse", "Professor's columns + 4 PCM layers + influence/interest"))
    fields = ["id", "name", "type", "benefits_to_project", "benefits_of_project", "engagement", "characteristics", "interests", "capacity_motivation", "possible_actions", "influence", "interest", "attitude"]
    from .ui import LABELS
    hdr = [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in fields] + [(tr("Quadrante Mendelow", "Mendelow quadrant"), "")]
    rows = []
    for k, s in enumerate(p["stakeholders"]):
        r = 5 + k
        rows.append([s.get(f) for f in fields] + [f'=IF(AND(K{r}>=3,L{r}>=3),"Gerir de perto / Manage closely",IF(K{r}>=3,"Manter satisfeito / Keep satisfied",IF(L{r}>=3,"Manter informado / Keep informed","Monitorizar / Monitor")))'])
    last = _table(ws, 4, hdr, rows, {1: 6, 2: 30, 3: 18, 4: 34, 5: 34, 6: 16, 7: 30, 8: 30, 9: 30, 10: 30, 14: 30}, wrap_cols=(2, 4, 5, 7, 8, 9, 10))
    _dv(ws, f"C5:C{max(last, 5) + 20}", [c for c in opt_codes("stakeholder_type")])
    _dv(ws, f"F5:F{max(last, 5) + 20}", [c for c in opt_codes("engagement")])
    _dv(ws, f"M5:M{max(last, 5) + 20}", [c for c in opt_codes("attitude")])

    ws = wb.create_sheet("Comportamento")
    _title(ws, tr("Padrões comportamentais do grupo-alvo (1–5)", "Target-group behavioural patterns (1–5)"))
    f2 = ["id", "target_group", "perception", "opportunity", "ability", "motivation", "evidence", "implication"]
    rows = [[b.get(f) for f in f2] + [f"=AVERAGE(C{5 + k}:F{5 + k})", f'=IF(MIN(C{5 + k}:F{5 + k})<=2,"Pressuposto em risco / Assumption at risk","OK")'] for k, b in enumerate(p["behaviour"])]
    _table(ws, 4, [(LABELS[f][0 if _pt() else 1], f) for f in f2] + [(tr("Média", "Average"), ""), (tr("Alerta", "Alert"), "")], rows, {2: 30, 7: 40, 8: 40, 10: 30}, wrap_cols=(2, 7, 8))

    ws = wb.create_sheet("Problemas-Objetivos")
    _title(ws, tr("Árvore de problemas e de objetivos", "Problem and objective trees"))
    f3 = ["id", "level", "text", "parent", "objective", "in_scope"]
    _table(ws, 4, [(LABELS[f][0 if _pt() else 1], f) for f in f3], [[x.get(f) for f in f3] for x in p["problems"]], {3: 45, 5: 45, 2: 14}, wrap_cols=(3, 5))
    r0 = 6 + len(p["problems"])
    ws.cell(r0, 1, tr("Seleção da estratégia (multicritério)", "Strategy selection (multi-criteria)"))
    _font(ws.cell(r0, 1), bold=True)
    crit = p["strategies"].get("criteria", [])
    ws.cell(r0 + 1, 1, tr("Peso", "Weight"))
    for j, c in enumerate(crit, 2):
        ws.cell(r0 + 1, j, c.get("weight"))
        _font(ws.cell(r0 + 1, j), color="0000FF")
        ws.cell(r0 + 2, j, c.get("criterion"))
        _font(ws.cell(r0 + 2, j), bold=True)
    ws.cell(r0 + 2, 1, tr("Estratégia", "Strategy"))
    _font(ws.cell(r0 + 2, 1), bold=True)
    ws.cell(r0 + 2, len(crit) + 2, tr("Pontuação ponderada", "Weighted score"))
    _font(ws.cell(r0 + 2, len(crit) + 2), bold=True)
    for i, o in enumerate(p["strategies"].get("options", []), 1):
        rr = r0 + 2 + i
        ws.cell(rr, 1, o["name"])
        for j, c in enumerate(crit, 2):
            ws.cell(rr, j, o.get("scores", {}).get(c["criterion"]))
            _font(ws.cell(rr, j), color="0000FF")
        a, b = L(2), L(len(crit) + 1)
        ws.cell(rr, len(crit) + 2, f"=SUMPRODUCT({a}{rr}:{b}{rr},${a}${r0 + 1}:${b}${r0 + 1})/SUM(${a}${r0 + 1}:${b}${r0 + 1})")
        ws.cell(rr, len(crit) + 2).number_format = "0.00"

    # logframe
    ws = wb.create_sheet("Logframe")
    _title(ws, tr("Matriz de Enquadramento Lógico", "Logical Framework Matrix"), tr("Lógica vertical · horizontal · diagonal", "Vertical · horizontal · diagonal logic"))
    hdr = [(tr("Nível", "Level"), "level"), (tr("Código", "Code"), "code"), (tr("Lógica de intervenção", "Intervention logic"), "text"), (tr("Leva a", "Leads to"), "parent"),
           (tr("Indicadores", "Indicators"), ""), ("Baseline", ""), (tr("Meta", "Target"), ""), (tr("Fontes de verificação", "Sources of verification"), ""),
           (tr("Pressupostos (que condicionam este nível)", "Assumptions (conditioning this level)"), ""), (tr("Critério", "Criterion"), "")]
    rows = []
    for o in p["objectives"]:
        inds = [i for i in p["indicators"] if str(i.get("objective_code")) == str(o["code"])]
        hs = [h for h in p["assumptions"] if str(h.get("objective_code")) == str(o["code"])]
        rows.append([o["level"], o["code"], o["text"], o.get("parent"), "\n".join(f"{i['id']}: {i['indicator']}" for i in inds),
                     "\n".join(str(i.get("baseline")) for i in inds), "\n".join(str(i.get("target")) for i in inds), "\n".join(str(i.get("source")) for i in inds),
                     "\n".join(f"{h['id']} [{h['type']}]: {h['text']}" for h in hs), indicator_dimension(o["level"])])
    for a in p["activities"]:
        rows.append(["Activity", a["id"], a.get("name"), a.get("output_code"), "", "", "", "", "", "Efficiency"])
    _table(ws, 4, hdr, rows, {1: 10, 2: 8, 3: 45, 4: 8, 5: 40, 6: 12, 7: 12, 8: 30, 9: 45, 10: 18}, wrap_cols=(3, 5, 6, 7, 8, 9))

    # indicators
    ws = wb.create_sheet("Indicadores")
    _title(ws, tr("Indicadores SMART", "SMART indicators"))
    f4 = [f for f, _, _ in TABLES["indicators"]]
    hdr = [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f4] + [("SMART", ""), ("Δ", ""), (tr("Progresso", "Progress"), "")]
    rows = []
    for k, i in enumerate(p["indicators"]):
        r = 5 + k
        rows.append([i.get(f) for f in f4] + [f"=COUNTIF(M{r}:Q{r},TRUE)", f'=IF(OR(E{r}="",G{r}=""),"",G{r}-E{r})', f'=IF(OR(E{r}="",G{r}="",I{r}="",G{r}=E{r}),"",(I{r}-E{r})/(G{r}-E{r}))'])
    last = _table(ws, 4, hdr, rows, {3: 40, 10: 30}, wrap_cols=(3, 10))
    for k in range(len(rows)):
        ws.cell(5 + k, len(f4) + 3).number_format = PCT

    ws = wb.create_sheet("Benchmarking")
    _title(ws, tr("Benchmarking e séries temporais", "Benchmarking and time series"))
    f5 = ["indicator_id", "peer", "value", "year", "note"]
    last = _table(ws, 4, [(LABELS[f][0 if _pt() else 1], f) for f in f5], [[b.get(f) for f in f5] for b in p["benchmarks"]], {2: 26, 5: 30})
    r0 = last + 3
    ws.cell(r0 - 1, 1, tr("Série temporal", "Time series"))
    _font(ws.cell(r0 - 1, 1), bold=True)
    f6 = ["indicator_id", "year", "value"]
    _table(ws, r0, [(LABELS[f][0 if _pt() else 1], f) for f in f6], [[t.get(f) for f in f6] for t in p["timeseries"]])
    ws.freeze_panes = None

    ws = wb.create_sheet("Pressupostos")
    _title(ws, tr("Pressupostos baseados em evidência", "Evidence-based assumptions"), "OUTPUTS = ACTIVITIES + OPERATIONAL · OUTCOMES = OUTPUTS + BEHAVIOURAL · IMPACTS = OUTCOMES + POLITICAL")
    f7 = [f for f, _, _ in TABLES["assumptions"]]
    rows = []
    for h in p["assumptions"]:
        code, why = AN.assumption_decision(h)
        rows.append([h.get(f) for f in f7] + [why, AN.assumption_risk_probability(h)])
    _table(ws, 4, [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f7] + [(tr("Decisão (fluxograma PCM)", "Decision (PCM flowchart)"), ""), (tr("Prob. risco", "Risk likelihood"), "")],
           rows, {4: 45, 7: 40, 10: 45}, wrap_cols=(4, 7, 10))

    # activities / PERT
    sched = S.compute(p)
    ws = wb.create_sheet("Atividades-PERT")
    _title(ws, tr("Atividades, PERT e CPM", "Activities, PERT and CPM"), tr(f"Unidade de tempo: {m.get('time_unit')}. tₑ e σ² são fórmulas; ES/EF/LS/LF/TF calculados pela app.",
                                                                        f"Time unit: {m.get('time_unit')}. tₑ and σ² are formulas; ES/EF/LS/LF/TF computed by the app."))
    f8 = ["id", "name", "output_code", "type", "predecessors", "optimistic", "most_likely", "pessimistic", "cost", "distribution", "responsible", "crash_duration", "crash_cost", "milestone", "pct_complete", "actual_cost"]
    hdr = [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f8] + [("tₑ=(a+4m+b)/6", ""), ("σ²", ""), ("ES", ""), ("EF", ""), ("LS", ""), ("LF", ""), ("TF", ""), ("FF", ""), (tr("Crítica", "Critical"), ""), ("BAC", "")]
    rows = []
    tab = sched["cpm"]["table"] if sched.get("ok") else {}
    for k, a in enumerate(p["activities"]):
        r = 5 + k
        t = tab.get(a["id"], {})
        rows.append([a.get(f) for f in f8] + [f"=(F{r}+4*G{r}+H{r})/6", f"=((H{r}-F{r})/6)^2", t.get("ES"), t.get("EF"), t.get("LS"), t.get("LF"), t.get("TF"), t.get("FF"),
                                              ("SIM" if _pt() else "YES") if t.get("critical") else "", activity_cost(p, a)])
    last = _table(ws, 4, hdr, rows, {2: 38, 4: 18, 5: 12, 10: 16, 11: 18}, wrap_cols=(2,))
    for k in range(len(rows)):
        for col in (17, 18, 19, 20, 21, 22, 23, 24):
            ws.cell(5 + k, col).number_format = "0.00"
        ws.cell(5 + k, 26).number_format = EUR
        ws.cell(5 + k, 9).number_format = EUR
    if rows:
        ws.conditional_formatting.add(f"A5:Z{last}", _crit_rule(last))
        r = last + 2
        ws.cell(r, 1, tr("Duração do projeto", "Project duration"))
        ws.cell(r, 3, f"=MAX(T5:T{last})")
        ws.cell(r + 1, 1, tr("Variância do caminho crítico", "Critical-path variance"))
        ws.cell(r + 1, 3, f'=SUMIF(Y5:Y{last},"{("SIM" if _pt() else "YES")}",R5:R{last})')
        ws.cell(r + 2, 1, tr("Prazo-alvo T", "Target T"))
        ws.cell(r + 2, 3, float(m.get("target_duration") or 0) or None)
        ws.cell(r + 2, 3).fill = YEL
        _font(ws.cell(r + 2, 3), color="0000FF")
        ws.cell(r + 3, 1, tr("P(concluir até T)", "P(finish by T)"))
        ws.cell(r + 3, 3, f'=IF(OR(C{r + 2}="",C{r + 1}=0),"",NORMDIST(C{r + 2},C{r},SQRT(C{r + 1}),TRUE))')
        ws.cell(r + 3, 3).number_format = PCT
        for i in range(4):
            _font(ws.cell(r + i, 1), bold=True)

    # Gantt + costs
    if sched.get("ok"):
        ws = wb.create_sheet("Gantt-Custos")
        _title(ws, tr("Gantt com custos por período e curva S", "Cost-loaded Gantt and S-curve"), tr("Células coloridas = atividade em curso (vermelho = crítica).", "Coloured cells = activity in progress (red = critical)."))
        per = sched["periods"]
        df = sched["acts"]
        base = ["ID", tr("Atividade", "Activity"), tr("Início", "Start"), tr("Fim", "Finish"), "BAC"]
        for j, h in enumerate(base, 1):
            c = ws.cell(4, j, h)
            _font(c, bold=True, color="FFFFFF")
            c.fill = HDR
        for j, pr in enumerate(per["period"], 6):
            c = ws.cell(4, j, str(pr))
            _font(c, bold=True, color="FFFFFF")
            c.fill = HDR
            c.alignment = Alignment(horizontal="center")
        np_ = len(per)
        lastc = L(5 + np_)
        for k, (_, r) in enumerate(df.iterrows()):
            rr = 5 + k
            ws.cell(rr, 1, r["id"])
            ws.cell(rr, 2, r["name"])
            ws.cell(rr, 3, r["start"]).number_format = "dd/mm/yyyy"
            ws.cell(rr, 4, r["finish"]).number_format = "dd/mm/yyyy"
            ws.cell(rr, 5, f"=SUM(F{rr}:{lastc}{rr})").number_format = EUR
            for j, pr in enumerate(per["period"], 6):
                v = float(per.loc[per["period"] == pr, r["id"]].iloc[0])
                c = ws.cell(rr, j, round(v, 2) if v else None)
                c.number_format = '#,##0;(#,##0);""'
                _font(c, color="0000FF")
                if v:
                    c.fill = PatternFill("solid", fgColor="F4B6B0" if r["critical"] else "BDD7EE")
        n = len(df)
        rt = 5 + n + 1
        labels = [tr("Custo do período (PV)", "Period cost (PV)"), tr("PV acumulado", "Cumulative PV"), tr("% do BAC", "% of BAC"), tr("Acumulado + contingência", "Cumulative + contingency")]
        ws.cell(rt + 5, 1, tr("Reserva de contingência", "Contingency reserve"))
        ws.cell(rt + 5, 5, round(sched["contingency"], 2)).number_format = EUR
        ws.cell(rt + 5, 5).fill = YEL
        for i, lab in enumerate(labels):
            ws.cell(rt + i, 2, lab)
            _font(ws.cell(rt + i, 2), bold=True)
            for j in range(6, 6 + np_):
                cl = L(j)
                if i == 0:
                    f = f"=SUM({cl}5:{cl}{4 + n})"
                elif i == 1:
                    f = f"={cl}{rt}" if j == 6 else f"={L(j - 1)}{rt + 1}+{cl}{rt}"
                elif i == 2:
                    f = f"=IFERROR({cl}{rt + 1}/$E${rt},0)"
                else:
                    f = f"={cl}{rt + 1}+{cl}{rt + 2}*$E${rt + 5}"
                c = ws.cell(rt + i, j, f)
                c.number_format = PCT if i == 2 else EUR
                c.fill = SUB
        ws.cell(rt, 5, f"=SUM(E5:E{4 + n})").number_format = EUR
        ws.column_dimensions["B"].width = 38
        for j in range(6, 6 + np_):
            ws.column_dimensions[L(j)].width = 11
        ws.freeze_panes = "F5"
        from openpyxl.chart.series import SeriesLabel
        ch = BarChart()
        ch.title = tr("Custo por período e acumulado (curva S)", "Cost per period and cumulative (S-curve)")
        ch.add_data(Reference(ws, min_col=6, max_col=5 + np_, min_row=rt, max_row=rt), from_rows=True, titles_from_data=False)
        ch.series[0].tx = SeriesLabel(v=labels[0])
        ch.set_categories(Reference(ws, min_col=6, max_col=5 + np_, min_row=4))
        ln = LineChart()
        ln.add_data(Reference(ws, min_col=6, max_col=5 + np_, min_row=rt + 1, max_row=rt + 1), from_rows=True, titles_from_data=False)
        ln.series[0].tx = SeriesLabel(v=labels[1])
        ln.y_axis.axId = 200
        ln.y_axis.crosses = "max"
        ch += ln
        ch.height, ch.width = 9, 24
        ws.add_chart(ch, f"B{rt + 8}")

        # EVM
        ws = wb.create_sheet("EVM")
        e = S.evm(p, sched)
        _title(ws, "Earned Value Management", tr(f"Data de controlo: {e['status']}", f"Status date: {e['status']}"))
        hdr = [("ID", ""), (tr("Atividade", "Activity"), ""), ("BAC", ""), ("PV", ""), (tr("% concluída", "% complete"), ""), ("EV", ""), ("AC", ""), ("CV", ""), ("SV", ""), ("CPI", ""), ("SPI", "")]
        rows = []
        for k, (_, r) in enumerate(e["table"].iterrows()):
            rr = 5 + k
            rows.append([r["id"], r["name"], round(r["BAC"], 2), round(r["PV"], 2), r["pct_complete"], f"=C{rr}*E{rr}", round(r["AC"], 2), f"=F{rr}-G{rr}", f"=F{rr}-D{rr}",
                         f'=IF(G{rr}=0,"",F{rr}/G{rr})', f'=IF(D{rr}=0,"",F{rr}/D{rr})'])
        last = _table(ws, 4, hdr, rows, {2: 38})
        for k in range(len(rows)):
            for col in (3, 4, 6, 7, 8, 9):
                ws.cell(5 + k, col).number_format = EUR
            ws.cell(5 + k, 5).number_format = PCT
            ws.cell(5 + k, 10).number_format = "0.00"
            ws.cell(5 + k, 11).number_format = "0.00"
        t = last + 1
        ws.cell(t, 2, "Total")
        for col in (3, 4, 6, 7, 8, 9):
            ws.cell(t, col, f"=SUM({L(col)}5:{L(col)}{last})").number_format = EUR
        ws.cell(t, 10, f'=IF(G{t}=0,"",F{t}/G{t})').number_format = "0.00"
        ws.cell(t, 11, f'=IF(D{t}=0,"",F{t}/D{t})').number_format = "0.00"
        for col in range(1, 12):
            ws.cell(t, col).fill = TOT
            _font(ws.cell(t, col), bold=True)
        k0 = t + 2
        kp = [("EAC = BAC/CPI", f"=IF(J{t}=\"\",C{t},C{t}/J{t})", EUR), ("ETC = EAC − AC", f"=C{k0}-G{t}", EUR), ("VAC = BAC − EAC", f"=C{t}-C{k0}", EUR),
              ("TCPI = (BAC−EV)/(BAC−AC)", f"=IF(C{t}=G{t},\"\",(C{t}-F{t})/(C{t}-G{t}))", "0.00"),
              (tr("Reserva de contingência", "Contingency reserve"), round(e["contingency"], 2), EUR), (tr("Contingência consumida", "Contingency used"), e["contingency_used"], EUR),
              (tr("Contingência disponível", "Contingency available"), f"=C{k0 + 4}-C{k0 + 5}", EUR)]
        for i, (lab, f, fmt) in enumerate(kp):
            ws.cell(k0 + i, 1, lab)
            _font(ws.cell(k0 + i, 1), bold=True)
            ws.cell(k0 + i, 3, f).number_format = fmt
        # S-curve history
        sc = S.s_curve(p, sched)
        r0 = k0 + len(kp) + 2
        hdr = [(tr("Período", "Period"), ""), (tr("PV acumulado", "Cumulative PV"), ""), (tr("EV acumulado", "Cumulative EV"), ""), (tr("AC acumulado", "Cumulative AC"), "")]
        rows = [[r["period"], round(r["pv_cum"], 0), None if pd.isna(r["ev_cum"]) else round(r["ev_cum"], 0), None if pd.isna(r["ac_cum"]) else round(r["ac_cum"], 0)] for _, r in sc.iterrows()]
        last2 = _table(ws, r0, hdr, rows)
        ws.freeze_panes = "A5"
        ch = LineChart()
        ch.title = tr("Curvas S: PV, EV e AC", "S-curves: PV, EV and AC")
        ch.add_data(Reference(ws, min_col=2, max_col=4, min_row=r0, max_row=last2), titles_from_data=True)
        ch.set_categories(Reference(ws, min_col=1, min_row=r0 + 1, max_row=last2))
        ch.height, ch.width = 9, 22
        ws.add_chart(ch, f"F{r0}")

    # RACI
    ws = wb.create_sheet("RACI")
    roles = p["raci"].get("roles", [])
    _title(ws, tr("Matriz RACI / RASCI (PM²)", "RACI / RASCI matrix (PM²)"), "R = Responsible · A = Accountable · S = Support · C = Consulted · I = Informed")
    rows = [[a["id"], a.get("name")] + [p["raci"]["matrix"].get(a["id"], {}).get(r, "") for r in roles] +
            [f'=COUNTIF(C{5 + k}:{L(2 + len(roles))}{5 + k},"A")'] for k, a in enumerate(p["activities"])]
    _table(ws, 4, [("ID", ""), (tr("Atividade", "Activity"), "")] + [(r, "") for r in roles] + [("N.º A", "")], rows, {2: 38})
    if rows:
        ws.conditional_formatting.add(f"{L(3 + len(roles))}5:{L(3 + len(roles))}{4 + len(rows)}", CellIsRule(operator="notEqual", formula=["1"], fill=PatternFill("solid", fgColor="F4B6B0")))

    # risks
    ws = wb.create_sheet("Riscos")
    _title(ws, tr("Registo de riscos (alargado)", "Risk register (extended)"), tr("Exposição = probabilidade × impacto (1–16)", "Exposure = likelihood × impact (1–16)"))
    f9 = [f for f, _, _ in TABLES["risks"]]
    hdr = [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f9] + [(tr("Exposição", "Exposure"), ""), (tr("Acima do alvo?", "Above target?"), "")]
    rows = [[x.get(f) for f in f9] + [f"=D{5 + k}*E{5 + k}", f'=IF(R{5 + k}>F{5 + k},"⚠","")'] for k, x in enumerate(p["risks"])]
    last = _table(ws, 4, hdr, rows, {3: 40, 7: 30, 8: 30, 12: 30}, wrap_cols=(3, 7, 8, 12))
    if rows:
        ws.conditional_formatting.add(f"R5:R{last}", ColorScaleRule(start_type="num", start_value=1, start_color="63BE7B", mid_type="num", mid_value=8, mid_color="FFEB84", end_type="num", end_value=16, end_color="F8696B"))
    _dv(ws, f"B5:B{last + 20}", opt_codes("risk_type"))
    ws = wb.create_sheet(tr("Matriz de risco", "Risk matrix"))
    _title(ws, tr("Matriz probabilidade × impacto (n.º de riscos)", "Likelihood × impact matrix (number of risks)"))
    for j, i in enumerate(range(1, 5), 2):
        ws.cell(4, j, f"{i} {IMP[i]}")
        _font(ws.cell(4, j), bold=True)
    for k, l in enumerate(range(4, 0, -1), 5):
        ws.cell(k, 1, f"{l} {LIK[l]}")
        _font(ws.cell(k, 1), bold=True)
        for j, i in enumerate(range(1, 5), 2):
            c = ws.cell(k, j, f"=COUNTIFS(Riscos!$D$5:$D$500,{l},Riscos!$E$5:$E$500,{i})")
            e_ = l * i
            c.fill = PatternFill("solid", fgColor="C0392B" if e_ >= 12 else "E67E22" if e_ >= 8 else "F1C40F" if e_ >= 4 else "27AE60")
            c.alignment = Alignment(horizontal="center")
            _font(c, bold=True, color="FFFFFF")
    ws.column_dimensions["A"].width = 20
    for j in range(2, 6):
        ws.column_dimensions[L(j)].width = 16

    # budget
    ws = wb.create_sheet("Orçamento")
    _title(ws, tr("Orçamento por atividade (recursos × custo unitário)", "Budget per activity (resources × unit cost)"))
    f10 = [f for f, _, _ in TABLES["budget"]]
    rows = [[b.get(f) for f in f10] + [f"=F{5 + k}*G{5 + k}"] for k, b in enumerate(p["budget"])]
    last = _table(ws, 4, [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f10] + [("Total", "")], rows, {4: 34, 3: 26})
    for k in range(len(rows)):
        ws.cell(5 + k, 7).number_format = EUR
        ws.cell(5 + k, 9).number_format = EUR
    t = last + 2
    ws.cell(t, 1, tr("Resumo por atividade (BAC)", "Summary per activity (BAC)"))
    _font(ws.cell(t, 1), bold=True)
    rows = []
    for a in p["activities"]:
        rows.append([a["id"], a.get("name"), a.get("cost"), activity_cost(p, a)])
    _table(ws, t + 1, [("ID", ""), (tr("Atividade", "Activity"), ""), (tr("Custo manual", "Manual cost"), ""), ("BAC", "")], rows, {2: 34})
    ws.freeze_panes = "A5"

    # procurement
    ws = wb.create_sheet("Procurement")
    _title(ws, tr("Plano de procurement", "Procurement plan"))
    f11 = [f for f, _, _ in TABLES["procurement"]]
    last = _table(ws, 4, [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f11], [[q.get(f) for f in f11] for q in p["procurement"]], {2: 34, 9: 34, 10: 30}, wrap_cols=(2, 9, 10))
    _dv(ws, f"F5:F{last + 20}", opt_codes("procurement"))

    # finance with live formulas
    ws = wb.create_sheet(tr("Finanças", "Finance"))
    f = p["finance"]
    _title(ws, tr("Análise financeira: WACC, VAL, TIR, MIRR", "Financial appraisal: WACC, NPV, IRR, MIRR"))
    inp = [(tr("Capital próprio E", "Equity E"), f.get("equity"), EUR), (tr("Dívida D", "Debt D"), f.get("debt"), EUR),
           ("rf", f.get("rf"), PCT), ("β", f.get("beta"), "0.00"), (tr("Prémio de mercado", "Market premium"), f.get("mrp"), PCT),
           (tr("Ke direto (se não CAPM)", "Direct Ke (if not CAPM)"), f.get("ke"), PCT), (tr("Usar CAPM? (1/0)", "Use CAPM? (1/0)"), 1 if f.get("ke_method") == "capm" else 0, "0"),
           ("Kd", f.get("kd"), PCT), (tr("Imposto t", "Tax t"), f.get("tax"), PCT), (tr("Valor residual", "Residual value"), f.get("residual_value") or 0, EUR)]
    for i, (lab, v, fmt) in enumerate(inp, 4):
        ws.cell(i, 1, lab)
        c = ws.cell(i, 2, v)
        c.number_format = fmt
        c.fill = YEL
        _font(c, color="0000FF")
    r = 4 + len(inp)
    calc = [("Ke", "=IF(B10=1,B6+B7*B8,B9)", PCT), ("V = E + D", "=B4+B5", EUR), ("WACC", f"=IF(B{r + 1}=0,B{r},B4/B{r + 1}*B{r}+B5/B{r + 1}*B11*(1-B12))", PCT)]
    for i, (lab, fm, fmt) in enumerate(calc, r):
        ws.cell(i, 1, lab)
        _font(ws.cell(i, 1), bold=True)
        ws.cell(i, 2, fm).number_format = fmt
    wacc_cell = f"B{r + 2}"
    if f.get("rate_override"):
        ws.cell(r + 3, 1, tr("Taxa de desconto usada (override)", "Discount rate used (override)"))
        ws.cell(r + 3, 2, f.get("rate_override")).number_format = PCT
        rate_cell = f"B{r + 3}"
    else:
        rate_cell = wacc_cell
    r0 = r + 5
    hdr = [(LABELS["year"][0 if _pt() else 1], "year"), (LABELS["investment"][0 if _pt() else 1], "investment"), (LABELS["operating_costs"][0 if _pt() else 1], "operating_costs"),
           (LABELS["benefits"][0 if _pt() else 1], "benefits"), (tr("Fluxo líquido", "Net flow"), ""), (tr("Fluxo atualizado", "Discounted flow"), ""), (tr("Acumulado atualizado", "Cumulative discounted"), "")]
    cfs = sorted(p["cashflows"], key=lambda x: int(x.get("year") or 0))
    rows = []
    for k, cf in enumerate(cfs):
        rr = r0 + 1 + k
        res = f"+$B$13" if k == len(cfs) - 1 else ""
        rows.append([cf.get("year"), cf.get("investment"), cf.get("operating_costs"), cf.get("benefits"), f"=D{rr}-C{rr}-B{rr}{res}",
                     f"=E{rr}/(1+{rate_cell})^A{rr}", f"=F{rr}" if k == 0 else f"=G{rr - 1}+F{rr}"])
    last = _table(ws, r0, hdr, rows)
    for k in range(len(rows)):
        for col in range(2, 8):
            ws.cell(r0 + 1 + k, col).number_format = EUR
    if rows:
        a, b = r0 + 1, last
        out = [(tr("VAL (NPV)", "NPV"), f"=E{a}+NPV({rate_cell},E{a + 1}:E{b})", EUR), (tr("TIR (IRR)", "IRR"), f"=IFERROR(IRR(E{a}:E{b}),\"\")", PCT),
               ("MIRR", f"=IFERROR(MIRR(E{a}:E{b},{f.get('finance_rate') or rate_cell},{f.get('reinvest_rate') or rate_cell}),\"\")", PCT),
               (tr("Índice de rendibilidade", "Profitability index"), f"=IFERROR((B{last + 3}+SUMPRODUCT(B{a}:B{b}/(1+{rate_cell})^A{a}:A{b}))/SUMPRODUCT(B{a}:B{b}/(1+{rate_cell})^A{a}:A{b}),\"\")", "0.00")]
        for i, (lab, fm, fmt) in enumerate(out, last + 3):
            ws.cell(i, 1, lab)
            _font(ws.cell(i, 1), bold=True)
            c = ws.cell(i, 2, fm)
            c.number_format = fmt
            _font(c, bold=True)
    ws.column_dimensions["A"].width = 34
    for j in range(2, 8):
        ws.column_dimensions[L(j)].width = 16
    ws.freeze_panes = None

    ws = wb.create_sheet(tr("Avaliação", "Evaluation"))
    _title(ws, tr("Matriz de avaliação (OCDE-CAD) e atributos de qualidade (PCM)", "Evaluation matrix (OECD-DAC) and quality attributes (PCM)"))
    f12 = [f for f, _, _ in TABLES["evaluation"]]
    last = _table(ws, 4, [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f12], [[e.get(f) for f in f12] for e in p["evaluation"]], {3: 45, 4: 35, 5: 30, 6: 30}, wrap_cols=(3, 4, 5, 6))
    r = last + 3
    ws.cell(r, 1, tr("Atributos de qualidade", "Quality attributes"))
    _font(ws.cell(r, 1), bold=True)
    for k, (attr, qs) in enumerate(AN.QUALITY.items()):
        for qid, qpt, qen in qs:
            r += 1
            ws.cell(r, 1, attr)
            ws.cell(r, 2, qpt if _pt() else qen)
            ws.cell(r, 3, p["quality"].get(qid, ""))
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _crit_rule(last):
    from openpyxl.formatting.rule import FormulaRule
    return FormulaRule(formula=[f'$Y5="{("SIM" if _pt() else "YES")}"'], fill=PatternFill("solid", fgColor="FDECE7"))


def _dv(ws, rng, options):
    s = ",".join(options)
    if len(s) > 250:
        return
    dv = DataValidation(type="list", formula1=f'"{s}"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(rng)


def _pt():
    from .i18n import get_lang
    return get_lang() == "pt"


# =============================================================================== import
SHEET_TABLE = {"stakeholders": "stakeholders", "comportamento": "behaviour", "behaviour": "behaviour", "problemas-objetivos": "problems",
               "indicadores": "indicators", "indicators": "indicators", "pressupostos": "assumptions", "assumptions": "assumptions",
               "atividades-pert": "activities", "riscos": "risks", "risks": "risks", "orçamento": "budget", "budget": "budget",
               "procurement": "procurement", "avaliação": "evaluation", "evaluation": "evaluation", "benchmarking": "benchmarks"}


def import_workbook(p: dict, file, mode: str = "append") -> str:
    wb = load_workbook(file, data_only=True)
    names = [s.lower() for s in wb.sheetnames]
    msgs = []
    if "stakeholderregister" in names:
        ws = wb[wb.sheetnames[names.index("stakeholderregister")]]
        rows = []
        for r in range(6, 19):
            name = ws[f"B{r}"].value
            if not name:
                continue
            x = empty_row("stakeholders")
            x.update({"name": str(name), "type": ws[f"C{r}"].value or "Other (specify)", "benefits_to_project": ws[f"D{r}"].value or "",
                      "benefits_of_project": ws[f"E{r}"].value or "", "engagement": ws[f"F{r}"].value or "Consult"})
            if x["type"] not in opt_codes("stakeholder_type"):
                x["characteristics"] = f"Tipo original: {x['type']}"
                x["type"] = "Other (specify)"
            if x["engagement"] not in opt_codes("engagement"):
                x["possible_actions"] = str(x["engagement"])
                x["engagement"] = "Consult"
            rows.append(_coerce_row("stakeholders", x))
        _merge(p, "stakeholders", rows, mode)
        msgs.append(tr(f"{len(rows)} stakeholders importados do StakeholderRegister.", f"{len(rows)} stakeholders imported from StakeholderRegister."))
    if "riskregister" in names:
        ws = wb[wb.sheetnames[names.index("riskregister")]]
        rows = []
        inv_l = {v: k for k, v in LIK.items()}
        inv_i = {v: k for k, v in IMP.items()}
        r = 11
        while r < 263:
            desc = ws[f"C{r}"].value
            if desc:
                x = empty_row("risks")
                x.update({"type": ws[f"B{r}"].value or "Other (rare)", "description": str(desc), "likelihood": inv_l.get(ws[f"D{r}"].value, 2),
                          "impact": inv_i.get(ws[f"G{r}"].value, 2), "target_exposure": ws[f"K{r}"].value or 4,
                          "existing_mitigation": ws[f"L{r}"].value or "", "proposed_mitigation": ws[f"M{r}"].value or "", "risk_manager": ws[f"N{r}"].value or "",
                          "risk_owner": ws[f"O{r}"].value or "", "review_by": ws[f"P{r}"].value or "", "review": ws[f"Q{r}"].value or ""})
                rows.append(_coerce_row("risks", x))
            r += 1
        _merge(p, "risks", rows, mode)
        msgs.append(tr(f"{len(rows)} riscos importados do RiskRegister.", f"{len(rows)} risks imported from RiskRegister."))
    for sn in wb.sheetnames:
        t = SHEET_TABLE.get(sn.lower())
        if not t:
            continue
        ws = wb[sn]
        hdr_row = None
        for r in range(1, 12):
            vals = [str(c.value or "") for c in ws[r]]
            if sum(1 for v in vals if re.search(r"\[[a-z_]+\]$", v)) >= 2:
                hdr_row = r
                break
        if not hdr_row:
            continue
        fields = {}
        for c in ws[hdr_row]:
            mm = re.search(r"\[([a-z_]+)\]$", str(c.value or ""))
            if mm and mm.group(1) in {f for f, _, _ in TABLES[t]}:
                fields[c.column] = mm.group(1)
        rows = []
        for r in range(hdr_row + 1, ws.max_row + 1):
            rec = {f: ws.cell(r, col).value for col, f in fields.items()}
            if not any(v not in (None, "") for v in rec.values()):
                break
            x = empty_row(t)
            x.update({k: v for k, v in rec.items() if v is not None})
            rows.append(_coerce_row(t, x))
        _merge(p, t, rows, mode)
        msgs.append(f"{sn}: {len(rows)}")
    if not msgs:
        raise ValueError(tr("Não reconheci o ficheiro: use o StakeholderRegister, o RiskRegister ou o modelo alargado exportado pela app.",
                            "File not recognised: use StakeholderRegister, RiskRegister or the extended template exported by the app."))
    return " · ".join(msgs)


def _merge(p, table, rows, mode):
    if mode == "replace":
        p[table] = ensure_ids(rows, table)
    else:
        for r in rows:
            if r.get("id") and any(str(x.get("id")) == str(r["id"]) for x in p[table]):
                r["id"] = ""
        p[table] = ensure_ids(p[table] + rows, table)


ALIASES = {"id": ["id", "código", "codigo", "code"], "name": ["name", "nome", "atividade", "activity", "tarefa", "task"],
           "predecessors": ["predecessors", "predecessoras", "precedentes", "dependências", "dependencias", "pred"],
           "optimistic": ["optimistic", "otimista", "a", "o"], "most_likely": ["most_likely", "mais provável", "mais provavel", "m", "ml", "duração", "duracao", "duration"],
           "pessimistic": ["pessimistic", "pessimista", "b", "p"], "cost": ["cost", "custo", "orçamento", "orcamento", "budget"],
           "output_code": ["output_code", "output", "resultado"], "responsible": ["responsible", "responsável", "responsavel"],
           "type": ["type", "tipo"], "distribution": ["distribution", "distribuição", "distribuicao"]}


def import_activities(p: dict, file, mode: str = "append") -> int:
    name = getattr(file, "name", "")
    df = pd.read_csv(file, sep=None, engine="python") if name.lower().endswith(".csv") else pd.read_excel(file)
    cols = {}
    for c in df.columns:
        key = re.sub(r"\s*\[.*\]$", "", str(c)).strip().lower()
        mm = re.search(r"\[([a-z_]+)\]$", str(c))
        if mm:
            cols[c] = mm.group(1)
            continue
        for f, al in ALIASES.items():
            if key in al:
                cols[c] = f
                break
    rows = []
    for rec in df.rename(columns=cols).to_dict("records"):
        x = empty_row("activities")
        x.update({k: v for k, v in rec.items() if k in x and not (isinstance(v, float) and v != v)})
        if not x.get("name") and not x.get("id"):
            continue
        if (x.get("optimistic") in (None, 1.0)) and x.get("most_likely") and "optimistic" not in rec:
            x["optimistic"] = x["pessimistic"] = x["most_likely"]
        rows.append(_coerce_row("activities", x))
    _merge(p, "activities", rows, mode)
    return len(rows)
