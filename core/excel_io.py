"""Excel import/export.

1. Professor's templates, filled in their ORIGINAL format (StakeholderRegister, RiskRegister).
2. Extended workbook ("modelo alargado") with every module, live Excel formulas and re-importable headers.
"""
from __future__ import annotations

import io
import json
import os
import re

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

from . import analysis as AN
from . import schedule as S
from .i18n import OPTIONS, opt_codes, tr
from .model import TABLES, _coerce_row, activity_cost, empty_row, ensure_ids, indicator_dimension

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


def _risk_mgmt_sheet(wb, p: dict, f9: list) -> None:
    """Professor's risk management matrix (slide 10) + risk threshold check (cost of risk ÷ BAC vs 5/10/15%)."""
    from . import riskmgmt as RM
    ws = wb.create_sheet(tr("Matriz gestão riscos", "Risk mgmt matrix"))
    _title(ws, tr("Matriz de gestão de riscos e limiar de risco", "Risk management matrix and risk threshold"), tr(*RM.MATRIX_HELP)[:250])
    sched = S.compute(p)
    bac = float(sched.get("bac") or 0)
    cc = L(f9.index("contingency") + 1)
    rows_ = [(tr("Orçamento das atividades (BAC)", "Activity budget (BAC)"), round(bac, 2), EUR),
             (tr("Custo do risco = Σ contingência por risco", "Cost of risk = Σ per-risk contingency"), f"=SUM(Riscos!{cc}5:{cc}500)", EUR),
             (tr("Rácio = custo do risco ÷ BAC", "Ratio = cost of risk ÷ BAC"), "=IF(B4=0,0,B5/B4)", PCT),
             (tr("Limiar de risco da organização (5%, 10% ou 15%)", "Organisation's risk threshold (5%, 10% or 15%)"), float(p["meta"].get("risk_threshold") or 0.10), PCT),
             (tr("Situação", "Status"), '=IF(B6>B7,"' + tr("❌ Acima do limiar: o projeto pode não ser viável", "❌ Above threshold: the project may not be feasible")
              + '",IF(B6>=0.8*B7,"' + tr("⚠️ Perto do limiar (≥ 80%)", "⚠️ Close to the threshold (≥ 80%)") + '","' + tr("✅ Abaixo do limiar", "✅ Below threshold") + '"))', None)]
    for i, (lab, v, fmt_) in enumerate(rows_, 4):
        ws.cell(i, 1, lab)
        _font(ws.cell(i, 1), bold=True)
        c = ws.cell(i, 2, v)
        if fmt_:
            c.number_format = fmt_
        _font(c, color="000000" if isinstance(v, str) and v.startswith("=") else "0000FF", bold=i == 8)
        if i == 7:
            c.fill = YEL
    ws["B7"].comment = Comment(tr(*RM.THRESHOLD_HELP), "PM Studio")
    hdr = [tr("ID", "ID"), tr("Risco", "Risk"), tr("Tipo de pressuposto", "Assumption type"), tr("Impacto adverso potencial", "Potential adverse impact"),
           "P", "I", tr("Nível (P×I)", "Level (L×I)"), tr("Estratégia", "Strategy"), tr("Preventiva", "Preventive"), tr("Corretiva (se e quando…)", "Corrective (if and when…)"),
           tr("Custo (contingência)", "Cost (contingency)"), tr("Responsável", "Responsible"), tr("Responsável sugerido", "Suggested responsible"), tr("Âmbito", "Scope"),
           tr("Lógica Se… e… então…", "If… and… then… logic")]
    kind = {"Political": tr("Político", "Political"), "Behavioural": tr("Comportamental", "Behavioural"), "Operational": tr("Operacional", "Operational")}
    from .i18n import opt_label
    data = [[x["id"], x["risk"], kind[x["kind"]], opt_label("level", x["adverse"]), x["L"], x["I"], f"=E{11 + k}*F{11 + k}", x["strategy"], x["preventive"],
             x["corrective"], x["cost"], x["owner"], x["responsible_sugg"], x["scope"], x["if_then"].replace("**", "")] for k, x in enumerate(RM.matrix_rows(p))]
    last = _table(ws, 10, [(h, "") for h in hdr], data, {1: 8, 2: 40, 4: 18, 8: 18, 9: 34, 10: 34, 11: 14, 12: 22, 13: 30, 14: 10, 15: 50}, wrap_cols=(2, 9, 10, 13, 15))
    ws.column_dimensions["A"].width = 48
    for k in range(len(data)):
        ws.cell(11 + k, 11).number_format = EUR
    if data:
        ws.conditional_formatting.add(f"G11:G{last}", ColorScaleRule(start_type="num", start_value=1, start_color="63BE7B", mid_type="num", mid_value=8, mid_color="FFEB84",
                                                                      end_type="num", end_value=16, end_color="F8696B"))


def extended_workbook(p: dict) -> bytes:
    from .i18n import set_terminology
    set_terminology((p.get("logframe") or {}).get("terminology", "pcm"))
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
             (tr("Folhas: Projeto · Stakeholders · Comportamento · Problemas-Objetivos · Logframe · Indicadores · Benchmarking · Pressupostos · Atividades-PERT · Gantt-Custos · EVM · RACI · Riscos · Matriz de risco · Orçamento · Procurement · Finanças · Avaliação · (implementação, monitorização, avaliação e encerramento: Medições, Marcos, Alterações, Revisões, Contingência, Envolvimento, Feedback, Comunicação, Propostas, Financiamento, Sustentabilidade, Qualidade M&A, Auditorias, Propriedade, Lições, Boas práticas, Disseminação — quando preenchidas)",
                 "Sheets: Project · Stakeholders · Behaviour · Problems-Objectives · Logframe · Indicators · Benchmarking · Assumptions · Activities-PERT · Gantt-Costs · EVM · RACI · Risks · Risk matrix · Budget · Procurement · Finance · Evaluation · (implementation, monitoring, evaluation & closure: Measurements, Milestones, Changes, Reviews, Contingency, Engagement, Feedback, Communication, Bids, Funding, Sustainability, M&E quality, Audits, Ownership, Lessons, Best practices, Dissemination — when filled in)"), False),
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

    # classic 4x4 logframe (PCM)
    from .matrix import TERMS, means_and_costs
    from .model import MATRIX_ROW_OF_ASSUMPTION
    terms = (p.get("logframe") or {}).get("terminology", "pcm")
    ws = wb.create_sheet(tr("Quadro lógico 4x4", "Logframe 4x4"))
    _title(ws, tr("Matriz do Quadro Lógico — formato clássico 4×4 (PCM)", "Logical Framework Matrix — classic 4×4 format (PCM)"))
    from .matrix import term as _term
    heads = ["", _term("col_logic", terms), _term("col_ind", terms), _term("col_src", terms), tr("Pressupostos", "Assumptions")]
    for j, h in enumerate(heads, 1):
        c = ws.cell(4, j, h)
        _font(c, bold=True, color="FFFFFF")
        c.fill = HDR
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BD
    lvl_of = {str(o["code"]): o["level"] for o in p["objectives"]}
    row_asm = {}
    for h in p["assumptions"]:
        rl = MATRIX_ROW_OF_ASSUMPTION.get(lvl_of.get(str(h.get("objective_code") or "")))
        row_asm.setdefault(rl, []).append(f"{h['id']}: {h['text']}")
    fills = {"Impact": "B03A2E", "Outcome": "D9822B", "Output": "C9A227", "Activity": "3C8DBC"}
    r = 5
    for lvl in ("Impact", "Outcome", "Output"):
        items = [o for o in p["objectives"] if o["level"] == lvl]
        il = [i for o in items for i in p["indicators"] if str(i.get("objective_code")) == str(o["code"])]
        vals = [TERMS[terms][lvl][0 if _pt() else 1], "\n".join(f"{o['code']} {o['text']}" for o in items),
                "\n".join(f"{i['id']} {i['indicator']}: {i.get('baseline')} ({i.get('baseline_year') or '—'}) → {i.get('target')} ({i.get('target_year') or '—'})" for i in il),
                "\n".join(f"{i['id']} {i.get('source') or ''}" for i in il),
                tr("(não aplicável)", "(not applicable)") if lvl == "Impact" else "\n".join(row_asm.get(lvl, []))]
        for j, v in enumerate(vals, 1):
            c = ws.cell(r, j, v)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = BD
            _font(c, bold=(j == 1), color="FFFFFF" if j == 1 else None)
        ws.cell(r, 1).fill = PatternFill("solid", fgColor=fills[lvl])
        r += 1
    cats, total = means_and_costs(p)
    acts_txt = "\n".join(f"{a['id']} {a.get('name')}" + (f" [{a.get('output_code')}]" if a.get("output_code") else "") for a in p["activities"])
    vals = [TERMS[terms]["Activity"][0 if _pt() else 1], acts_txt, tr("Meios:", "Means:") + "\n" + "\n".join(f"• {k}" for k, _v in cats),
            tr("Custos:", "Costs:") + "\n" + "\n".join(f"{k}: {v:,.0f}" for k, v in cats) + f"\nTotal: {total:,.0f}", "\n".join(row_asm.get("Activity", []))]
    for j, v in enumerate(vals, 1):
        c = ws.cell(r, j, v)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.border = BD
        _font(c, bold=(j == 1), color="FFFFFF" if j == 1 else None)
    ws.cell(r, 1).fill = PatternFill("solid", fgColor=fills["Activity"])
    r += 1
    c = ws.cell(r, 5, tr("Pré-condições:", "Pre-conditions:") + "\n" + str((p.get("logframe") or {}).get("preconditions", "")))
    c.alignment = Alignment(wrap_text=True, vertical="top")
    c.border = BD
    c.fill = PatternFill("solid", fgColor="FFF8DC")
    for j, w in enumerate([18, 48, 52, 36, 44], 1):
        ws.column_dimensions[L(j)].width = w

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
    hdr = [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f8] + [("tₑ=(a+4m+b)/6", ""), ("σ²", ""), ("ES", ""), ("EF", ""), ("LS", ""), ("LF", ""), ("TF", ""), ("FF", ""), (tr("Crítica", "Critical"), ""), ("BAC", ""), (LABELS["loe"][0 if _pt() else 1], "loe")]
    rows = []
    tab = sched["cpm"]["table"] if sched.get("ok") else {}
    for k, a in enumerate(p["activities"]):
        r = 5 + k
        t = tab.get(a["id"], {})
        rows.append([a.get(f) for f in f8] + [f"=(F{r}+4*G{r}+H{r})/6", f"=((H{r}-F{r})/6)^2", t.get("ES"), t.get("EF"), t.get("LS"), t.get("LF"), t.get("TF"), t.get("FF"),
                                              ("SIM" if _pt() else "YES") if t.get("critical") else ("LOE" if t.get("loe") else ""), activity_cost(p, a),
                                              (("Sim" if _pt() else "Yes") if a.get("loe") else ("Não" if _pt() else "No"))])
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
        ws.cell(r + 4, 1, tr("Margem do projeto = T − duração (negativa = folga negativa)", "Project margin = T − duration (negative = negative float)"))
        ws.cell(r + 4, 3, f'=IF(C{r + 2}="","",C{r + 2}-C{r})')
        ws.cell(r + 4, 3).number_format = "0.00;[Red]-0.00"
        ws.cell(r + 5, 1, tr("Situação face ao prazo", "Status against the target"))
        ws.cell(r + 5, 3, f'=IF(C{r + 2}="","",IF(C{r + 4}<0,"{tr("❌ Não cabe no prazo: recuperar com compressão, sobreposição, âmbito ou renegociar", "❌ Misses the target: recover via crashing, fast-tracking, scope or renegotiate")}",'
                          f'IF(C{r + 3}<0.8,"{tr("⚠️ Cabe, mas probabilidade < 80%", "⚠️ Fits, but probability < 80%")}","{tr("✅ Cabe no prazo", "✅ Fits the target")}")))')
        ws.cell(r + 6, 1, tr("A duração resulta da rede e não é limitada; o prazo-alvo só é comparado com ela.", "The duration comes from the network and is not capped; the target is only compared with it."))
        _font(ws.cell(r + 6, 1), color="666666")
        for i in range(6):
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
                    c.fill = PatternFill("solid", fgColor="F4B6B0" if r["critical"] else "D9D2E9" if r.get("loe") else "BDD7EE")
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
    hdr = [(LABELS.get(f, (f, f))[0 if _pt() else 1], f) for f in f9] + [(tr("Exposição", "Exposure"), ""), (tr("Acima do alvo?", "Above target?"), ""),
                                                                         (tr("Ação exigida (zona)", "Required action (zone)"), "")]
    zt = [tr(*z[3]) for z in AN.RISK_ZONES]
    XC = L(len(f9) + 1)  # exposure column (after every field, so it follows new fields automatically)
    rows = [[x.get(f) for f in f9] + [f"=D{5 + k}*E{5 + k}", f'=IF({XC}{5 + k}>F{5 + k},"⚠","")',
                                      f'=IF({XC}{5 + k}>=12,"{zt[0]}",IF({XC}{5 + k}>=8,"{zt[1]}",IF({XC}{5 + k}>=4,"{zt[2]}","{zt[3]}")))'] for k, x in enumerate(p["risks"])]
    wcols = (3, 7, 8, 12, f9.index("corrective_action") + 1, f9.index("trigger") + 1)
    last = _table(ws, 4, hdr, rows, {3: 40, 7: 30, 8: 30, 12: 30, wcols[4]: 34, wcols[5]: 30}, wrap_cols=wcols)
    if rows:
        ws.conditional_formatting.add(f"{XC}5:{XC}{last}", ColorScaleRule(start_type="num", start_value=1, start_color="63BE7B", mid_type="num", mid_value=8, mid_color="FFEB84", end_type="num", end_value=16, end_color="F8696B"))
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
    _risk_mgmt_sheet(wb, p, f9)

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
        res = "+$B$13" if k == len(cfs) - 1 else ""
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
    _wbs_sheets(wb, p)
    _mon_sheets(wb, p)
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


WBS_FIELD_GLOSSARY = {"code": "level", "type": "work_package", "weight": "weight", "wbs_code": "work_package"}
WBS_COL_GLOSSARY = {"Nível": "level", "Level": "level", "BAC": "bac", "% do BAC": "pct_bac", "% of BAC": "pct_bac", "PV": "pv", "EV": "ev", "AC": "ac",
                    "CPI": "cpi", "SPI": "spi"}


def _gl_comment(cell, key: str) -> None:
    """Excel comment with the glossary formula (single source: help_texts.WBS_GLOSSARY)."""
    from .help_texts import wbs_term
    name, formula, meaning = wbs_term(key)
    cm = Comment(f"{name}\n{tr('Fórmula', 'Formula')}: {formula}\n{meaning}", "PM Studio")
    cm.width, cm.height = 420, 190
    cell.comment = cm


def _wbs_glossary_sheet(wb) -> None:
    from .help_texts import WBS_GLOSSARY, wbs_term
    ws = wb.create_sheet(tr("Glossário WBS", "WBS glossary"))
    ws["A1"] = tr("Glossário da WBS / EAP — fórmulas usadas nas folhas WBS-EAP e WBS-Atividades (fonte única: a mesma da app e do relatório)",
                  "WBS glossary — formulas used in the WBS and WBS-Activities sheets (single source: the same as the app and the report)")
    _font(ws["A1"], bold=True, size=13)
    hdr = [tr("Termo", "Term"), tr("Fórmula", "Formula"), tr("Significado", "Meaning"), tr("Fonte", "Source")]
    for j, h in enumerate(hdr, 1):
        c = ws.cell(3, j, h)
        _font(c, bold=True, color="FFFFFF")
        c.fill = HDR
        c.border = BD
    for i, (k, g) in enumerate(WBS_GLOSSARY.items(), 4):
        n, f, m = wbs_term(k)
        for j, v in enumerate((n, f, m, ", ".join(g["src"])), 1):
            c = ws.cell(i, j, v)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = BD
        _font(ws.cell(i, 1), bold=True)
    for j, w in enumerate((26, 60, 60, 14), 1):
        ws.column_dimensions[L(j)].width = w


def _wbs_sheets(wb, p: dict) -> None:
    """WBS / EAP (re-importable) with roll-up formulas linked to the activities sheet, plus the activity → package sheet."""
    from . import wbs as W
    from .ui import label as _lab
    els = W.elements(p)
    if not els:
        return
    sched = S.compute(p)
    ev = S.evm(p, sched) if sched.get("ok") else None
    ro = W.rollup(p, sched if sched.get("ok") else None, ev)
    acts = p["activities"]
    # --- activity → work package (formulas pull BAC, % and AC from 'Atividades-PERT')
    wa = wb.create_sheet(WBS_SHEETS["wbs_assign"][0 if _pt() else 1])
    wa["A1"] = f"{WBS_SHEETS['wbs_assign'][2 if _pt() else 3]}   [table:wbs_assign]"
    _font(wa["A1"], bold=True, size=13)
    hdr = [(_lab("id"), "id"), (_lab("name"), "name"), (_lab("wbs_code"), "wbs_code"), ("BAC", ""), ("EV", ""), ("AC", "")]
    rows = []
    n = len(acts)
    for k, a in enumerate(acts):
        r = 5 + k
        m_ = f"MATCH($A{r},'Atividades-PERT'!$A$5:$A${4 + n},0)"
        rows.append([a["id"], a.get("name", ""), a.get("wbs_code", ""), f"=INDEX('Atividades-PERT'!$Z$5:$Z${4 + n},{m_})",
                     f"=D{r}*INDEX('Atividades-PERT'!$O$5:$O${4 + n},{m_})", f"=INDEX('Atividades-PERT'!$P$5:$P${4 + n},{m_})"])
    last_a = _table(wa, 4, hdr, rows, {1: 9, 2: 44, 3: 12, 4: 14, 5: 14, 6: 14})
    for k in range(n):
        wa.cell(5 + k, 3).number_format = "@"
        for col in (4, 5, 6):
            wa.cell(5 + k, col).number_format = EUR
    sh = WBS_SHEETS["wbs_assign"][0 if _pt() else 1]
    # --- WBS elements + dictionary + roll-ups
    ws = wb.create_sheet(WBS_SHEETS["wbs"][0 if _pt() else 1])
    ws["A1"] = f"{WBS_SHEETS['wbs'][2 if _pt() else 3]}   [table:wbs]"
    _font(ws["A1"], bold=True, size=13)
    ws["A2"] = tr("BAC, EV e AC são fórmulas SUMPRODUCT sobre a folha WBS-Atividades (soma de todas as atividades do ramo); PV vem da app (depende da data de controlo).",
                  "BAC, EV and AC are SUMPRODUCT formulas over the WBS-Activities sheet (sum of every activity in the branch); PV comes from the app (depends on the status date).")
    _font(ws["A2"], italic=True, color="595959")
    fields = [f for f, _, _ in TABLES["wbs"]]
    hdr = [(_lab(f, "wbs"), f) for f in fields] + [(tr("Nível", "Level"), ""), ("BAC", ""), (tr("% do BAC", "% of BAC"), ""), ("PV", ""), ("EV", ""), ("AC", ""), ("CPI", ""), ("SPI", "")]
    rows = []
    nf = len(fields)
    cL, cB, cS, cP, cE, cA, cC, cSp = (L(nf + i) for i in range(1, 9))
    rng = lambda col: f"'{sh}'!${col}$5:${col}${max(5, last_a)}"  # noqa: E731
    tot_row = 5 + len(els) + 1
    for k, e in enumerate(els):
        r = 5 + k
        cond = f'--(LEFT({rng("C")}&".",LEN($A{r})+1)=$A{r}&".")'
        rr = ro.get(e["code"], {})
        rows.append([e.get(f) for f in fields] + [f'=LEN($A{r})-LEN(SUBSTITUTE($A{r},".",""))+1', f"=SUMPRODUCT({cond},{rng('D')})",
                                                   f"=IF(${cB}${tot_row}=0,0,{cB}{r}/${cB}${tot_row})", round(rr["PV"], 2) if rr.get("PV") is not None else None,
                                                   f"=SUMPRODUCT({cond},{rng('E')})", f"=SUMPRODUCT({cond},{rng('F')})",
                                                   f'=IF({cA}{r}=0,"",{cE}{r}/{cA}{r})', f'=IF(OR({cP}{r}="",{cP}{r}=0),"",{cE}{r}/{cP}{r})'])
    last = _table(ws, 4, hdr, rows, {1: 9, 2: 40, 3: 18, 4: 10, 5: 40, 6: 30, 7: 34, 8: 18, 9: 10}, wrap_cols=(2, 5, 6, 7))
    for k in range(len(els)):
        r = 5 + k
        ws.cell(r, 1).number_format = "@"
        for col in (nf + 2, nf + 4, nf + 5, nf + 6):
            ws.cell(r, col).number_format = EUR
        ws.cell(r, nf + 3).number_format = PCT
        for col in (nf + 7, nf + 8):
            ws.cell(r, col).number_format = "0.00"
        ws.cell(r, 2).alignment = Alignment(indent=2 * (W.level(els[k]["code"]) - 1), wrap_text=True, vertical="top")
        if not ro.get(els[k]["code"], {}).get("leaf"):
            for col in range(1, nf + 9):
                _font(ws.cell(r, col), bold=True)
    ws.cell(tot_row, nf + 1, tr("Total do projeto (= soma do nível 1)", "Project total (= sum of level 1)"))
    _font(ws.cell(tot_row, nf + 1), bold=True)
    ws.cell(tot_row, nf + 2, f'=SUMIF({cL}5:{cL}{last},1,{cB}5:{cB}{last})')
    ws.cell(tot_row, nf + 2).number_format = EUR
    ws.cell(tot_row + 1, nf + 1, tr("Controlo regra dos 100% (BAC das atividades − total)", "100% rule check (activities' BAC − total)"))
    ws.cell(tot_row + 1, nf + 2, f"=SUM({rng('D')})-{cB}{tot_row}")
    ws.cell(tot_row + 1, nf + 2).number_format = EUR
    for c_ in (ws.cell(tot_row, nf + 2), ws.cell(tot_row + 1, nf + 2)):
        _font(c_, bold=True)
    ws.conditional_formatting.add(f"{cC}5:{cSp}{last}", CellIsRule(operator="lessThan", formula=["0.95"], font=Font(color="C00000", bold=True)))
    # glossary comments on the headers (hover in Excel to see the formula)
    for wsx in (ws, wa):
        for c_ in wsx[4]:
            v = str(c_.value or "")
            fld = re.search(r"\[(\w+)\]$", v)
            key_ = WBS_FIELD_GLOSSARY.get(fld.group(1)) if fld else WBS_COL_GLOSSARY.get(v)
            if key_:
                _gl_comment(c_, key_)
    _wbs_glossary_sheet(wb)
    # put both sheets right after the activities sheet
    idx = wb.sheetnames.index("Atividades-PERT") + 1 if "Atividades-PERT" in wb.sheetnames else len(wb.sheetnames)
    wb.move_sheet(ws, offset=idx - wb.sheetnames.index(ws.title))
    wb.move_sheet(wa, offset=idx + 1 - wb.sheetnames.index(wa.title))


def _mon_sheets(wb, p: dict) -> None:
    """Implementation, monitoring, evaluation & closure tables (re-importable: [table:x] marker + 'label [field]' headers)."""
    from .ui import label as _lab
    for t, (spt, sen, dpt, den) in MON_SHEETS.items():
        if t in ("evaluation", "procurement") or not p.get(t):
            continue
        ws = wb.create_sheet((spt if _pt() else sen)[:31])
        ws["A1"] = f"{dpt if _pt() else den}   [table:{t}]"
        _font(ws["A1"], bold=True, size=13)
        fields = [f for f, _, _ in TABLES[t]]
        kinds = {f: k for f, k, _ in TABLES[t]}
        rows = []
        for r in p[t]:
            row = []
            for f in fields:
                v = r.get(f)
                if kinds[f] == "bool":
                    v = (tr("Sim", "Yes") if v else tr("Não", "No"))
                row.append(v)
            rows.append(row)
        _table(ws, 4, [(_lab(f, t), f) for f in fields], rows, {j + 1: (40 if kinds[f] == "long" else 16) for j, f in enumerate(fields)},
               wrap_cols=tuple(j + 1 for j, f in enumerate(fields) if kinds[f] == "long"))
        for j, f in enumerate(fields, 1):
            if f in ("amount", "price", "budget", "cost_impact", "impact_cost", "contract_value"):
                for i in range(len(rows)):
                    ws.cell(5 + i, j).number_format = EUR


def _crit_rule(last):
    from openpyxl.formatting.rule import FormulaRule
    return FormulaRule(formula=[f'$Y5="{("SIM" if _pt() else "YES")}"'], fill=PatternFill("solid", fgColor="FDECE7"))


def _dv(ws, rng, options, allow_sheet: bool = True):
    """Drop-down list. Inline lists cannot hold items with commas (e.g. 'Safety, security and logistics') nor exceed
    255 characters: those go to a hidden '_listas_dv' sheet (or, in the professor's files, get no drop-down)."""
    options = [str(o) for o in options]
    s = ",".join(options)
    if len(s) <= 250 and not any("," in o for o in options):
        formula = f'"{s}"'
    elif allow_sheet:
        wb = ws.parent
        hs = wb["_listas_dv"] if "_listas_dv" in wb.sheetnames else wb.create_sheet("_listas_dv")
        hs.sheet_state = "hidden"
        col = (hs.max_column + 1) if hs.max_row > 1 or hs["A1"].value is not None else 1
        for i, o in enumerate(options, 1):
            hs.cell(i, col, o)
        formula = f"'_listas_dv'!${L(col)}$1:${L(col)}${len(options)}"
    else:
        return
    dv = DataValidation(type="list", formula1=formula, allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(rng)


def _pt():
    from .i18n import get_lang
    return get_lang() == "pt"


# =============================================================================== import
SHEET_TABLE = {"stakeholders": "stakeholders", "comportamento": "behaviour", "behaviour": "behaviour", "problemas-objetivos": "problems",
               "indicadores": "indicators", "indicators": "indicators", "pressupostos": "assumptions", "assumptions": "assumptions",
               "atividades-pert": "activities", "wbs-eap": "wbs", "wbs": "wbs", "riscos": "risks", "risks": "risks", "orçamento": "budget", "budget": "budget",
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
        # the professor's format has no influence/interest/attitude columns: keep them for stakeholders already in the project (matched by name)
        known = {str(s_.get("name", "")).strip().lower(): s_ for s_ in p.get("stakeholders", [])}
        kept = 0
        for r_ in rows:
            ex_ = known.get(str(r_["name"]).strip().lower())
            if ex_:
                kept += 1
                for k_ in ("id", "influence", "interest", "attitude", "characteristics", "interests", "capacity_motivation", "possible_actions"):
                    if ex_.get(k_) not in (None, ""):
                        r_[k_] = ex_[k_]
        if mode == "replace":
            p["stakeholders"] = ensure_ids(rows, "stakeholders")
        else:
            names_ = {str(r_["name"]).strip().lower() for r_ in rows}
            p["stakeholders"] = ensure_ids([s_ for s_ in p["stakeholders"] if str(s_.get("name", "")).strip().lower() not in names_] + rows, "stakeholders")
        msgs.append(tr(f"{len(rows)} stakeholders importados do StakeholderRegister" + (f" ({kept} já existentes: influência, interesse e atitude mantidos)." if kept else
                                                                                         " (influência, interesse e atitude não existem neste formato: preencha-os na app ou no modelo alargado)."),
                       f"{len(rows)} stakeholders imported from StakeholderRegister" + (f" ({kept} already existing: influence, interest and attitude kept)." if kept else
                                                                                         " (influence, interest and attitude are not in this format: fill them in the app or the extended template).")))
    if "riskregister" in names:
        ws = wb[wb.sheetnames[names.index("riskregister")]]
        rows = []
        inv_l = {v: k for k, v in LIK.items()}
        inv_i = {v: k for k, v in IMP.items()}
        r = 11
        while r < 263:
            desc = ws[f"C{r}"].value
            if desc and str(desc).strip() == "Political distortion of the project's findings" and str(ws[f"Q{r}"].value or "").startswith("May 2023"):
                desc = None  # the template's own illustrative example row
            if desc:
                x = empty_row("risks")
                x.update({"type": ws[f"B{r}"].value or "Other (rare)", "description": str(desc), "likelihood": inv_l.get(ws[f"D{r}"].value, 2),
                          "impact": inv_i.get(ws[f"G{r}"].value, 2), "target_exposure": ws[f"K{r}"].value or 4,
                          "existing_mitigation": ws[f"L{r}"].value or "", "proposed_mitigation": ws[f"M{r}"].value or "", "risk_manager": ws[f"N{r}"].value or "",
                          "risk_owner": ws[f"O{r}"].value or "", "review_by": ws[f"P{r}"].value or "", "review": ws[f"Q{r}"].value or ""})
                rows.append(_coerce_row("risks", x))
            r += 1
        # match risks already in the project by description, so ids (and review history) are kept across monthly uploads
        known = {str(x.get("description", "")).strip().lower(): x for x in p.get("risks", [])}
        upd = []
        for r_ in rows:
            ex = known.get(str(r_["description"]).strip().lower())
            if ex:
                keep = {k: ex.get(k) for k in ("id", "assumption_id", "level_affected", "strategy", "contingency", "preventive_activity", "wbs_code", "corrective_action", "trigger")}
                r_.update({k: v for k, v in keep.items() if v not in (None, "")})
                upd.append(r_)
        if mode == "replace":
            for r_ in rows:
                if r_ not in upd:
                    r_["id"] = ""
            p["risks"] = ensure_ids(rows, "risks")
        else:
            ids = {str(r_["id"]) for r_ in upd}
            p["risks"] = ensure_ids([r_ if str(r_.get("id")) not in ids else next(u for u in upd if str(u["id"]) == str(r_["id"])) for r_ in p["risks"]]
                                    + [r_ for r_ in rows if r_ not in upd], "risks")
        # each upload of the (living) RiskRegister also records a dated review → risk history for monitoring
        when = str(p["meta"].get("status_date") or "")
        ids = {str(r["id"]) for r in rows}
        p["risk_reviews"] = [x for x in p.get("risk_reviews", []) if not (str(x.get("risk_id")) in ids and str(x.get("date")) == when)]
        for r_ in rows:
            p["risk_reviews"].append(_coerce_row("risk_reviews", {**empty_row("risk_reviews"), "risk_id": r_["id"], "date": when, "likelihood": r_["likelihood"],
                                                                   "impact": r_["impact"], "status": "Open", "note": str(r_.get("review") or "")}))
        msgs.append(tr(f"{len(rows)} riscos importados do RiskRegister (e registados como revisão de {when}).", f"{len(rows)} risks imported from RiskRegister (and recorded as a review on {when})."))
    wbs_in = False
    for sn in wb.sheetnames:
        ws = wb[sn]
        marker = None
        for coord in ("A1", "A2"):
            mm = re.search(r"\[table:([a-z_]+)\]", str(ws[coord].value or ""))
            if mm and (mm.group(1) in TABLES or mm.group(1) in PSEUDO):
                marker = mm.group(1)
        t = marker or SHEET_TABLE.get(sn.lower())
        if not t:
            continue
        hdr_row = None
        for r in range(1, 12):
            vals = [str(c.value or "") for c in ws[r]]
            if sum(1 for v in vals if re.search(r"\[[a-z_]+\]$", v)) >= (1 if marker else 2):
                hdr_row = r
                break
        if not hdr_row:
            continue
        fields = {}
        for c in ws[hdr_row]:
            mm = re.search(r"\[([a-z_]+)\]$", str(c.value or ""))
            if mm and mm.group(1) in {f for f, _, _ in (TABLES.get(t) or PSEUDO[t])}:
                fields[c.column] = mm.group(1)
        rows = []
        empties = 0
        for r in range(hdr_row + 1, ws.max_row + 1):
            rec = {f: ws.cell(r, col).value for col, f in fields.items()}
            if not any(v not in (None, "") for v in rec.values()):
                if not marker:
                    break  # exported workbook: a blank row ends the table
                empties += 1
                if empties > 50:
                    break
                continue
            empties = 0
            if t in PSEUDO:
                rows.append({k: _code(v) for k, v in rec.items()})
                continue
            x = empty_row(t)
            x.update({k: v for k, v in rec.items() if v is not None})
            rows.append(_coerce_row(t, x))
        if not rows:
            continue
        if t == "risk_params":
            from .model import to_number
            v = to_number(rows[0].get("risk_threshold"))
            if v:
                v = v / 100 if v > 1 else v
                p["meta"]["risk_threshold"] = float(v)
                msgs.append(tr(f"{sn}: limiar de risco {v:.0%}", f"{sn}: risk threshold {v:.0%}"))
            continue
        if t == "wbs_assign":
            by = {str(r.get("id")): r.get("wbs_code") for r in rows if r.get("id")}
            n = 0
            for a in p["activities"]:
                if a["id"] in by:
                    a["wbs_code"] = by[a["id"]] or ""
                    n += 1
            msgs.append(f"{sn}: {n}")
            continue
        if t == "wbs":
            _merge_wbs(p, rows, mode)
            wbs_in = True
        else:
            _merge(p, t, rows, mode)
        msgs.append(f"{sn}: {len(rows)}")
    if wbs_in:
        from .wbs import auto_assign
        auto_assign(p)        # activities still without a package are linked by output
    if not msgs and any(re.search(r"\[table:", str(wb[sn]["A1"].value or "")) for sn in wb.sheetnames):
        raise ValueError(tr("O modelo foi reconhecido, mas não tem dados a partir da linha 5 (a linha 3 é só um exemplo).",
                            "The template was recognised but has no data from row 5 onwards (row 3 is only an example)."))
    if not msgs:
        raise ValueError(tr("Não reconheci o ficheiro: use o StakeholderRegister, o RiskRegister ou o modelo alargado exportado pela app.",
                            "File not recognised: use StakeholderRegister, RiskRegister or the extended template exported by the app."))
    return " · ".join(msgs)


def _code(v):
    """Excel may turn a code such as 2 into 2.0 — keep codes as clean text."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return "" if v is None else str(v).strip()


def _merge_wbs(p, rows, mode):
    for r in rows:
        r["code"] = _code(r.get("code"))
    rows = [r for r in rows if r["code"]]
    if mode == "replace":
        p["wbs"] = rows
        return
    by = {e["code"]: e for e in p.get("wbs", [])}
    for r in rows:
        if r["code"] in by:
            by[r["code"]].update({k: v for k, v in r.items() if v not in (None, "")})
        else:
            p["wbs"].append(r)


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
           "type": ["type", "tipo"], "distribution": ["distribution", "distribuição", "distribuicao"],
           "wbs_code": ["wbs_code", "wbs", "código wbs", "codigo wbs", "wbs code", "eap", "código eap", "edt", "outline number", "número de estrutura de tópicos"]}


def import_activities(p: dict, file, mode: str = "append") -> int:
    name = getattr(file, "name", "")
    # CSV read as text (keeps codes such as 1.10 and accepts PT decimals "1,5"); numbers are converted by the model
    df = pd.read_csv(file, sep=None, engine="python", dtype=str, keep_default_na=False) if name.lower().endswith(".csv") else pd.read_excel(file)
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
        if "wbs_code" in x:
            x["wbs_code"] = _code(x["wbs_code"])
        rows.append(_coerce_row("activities", x))
    _merge(p, "activities", rows, mode)
    if p.get("wbs"):
        from .wbs import auto_assign
        auto_assign(p)
    return len(rows)


# =============================================================================== blank templates for upload
EXAMPLES = {
    "policy_goals": {"id": "G1", "document": "Estratégia Nacional 2026-2030", "strategic_goal": "Aumentar as exportações em 25% até 2030", "impact_indicator": "Valor das exportações (M€)", "baseline": "1200 (2025)", "target": "1500 (2030)", "source": "INE / Banco Central"},
    "stakeholders": {"id": "S1", "name": "Ministério X", "type": "Beneficiary", "characteristics": "Decisor político", "interests": "Precisa de dados fiáveis", "capacity_motivation": "Elevada influência", "possible_actions": "Briefings trimestrais", "benefits_to_project": "Apoio político", "benefits_of_project": "Melhores decisões", "engagement": "Consult", "influence": 5, "interest": 4, "attitude": "Supporter"},
    "behaviour": {"id": "B1", "target_group": "Técnicos do serviço", "perception": 4, "opportunity": 3, "ability": 2, "motivation": 3, "evidence": "Inquérito a 45 técnicos", "implication": "Plano de formação"},
    "problems": {"id": "C1", "text": "Plataformas de TI inadequadas", "level": "Cause", "parent": "P1", "objective": "Plataformas de TI adequadas", "in_scope": "Sim"},
    "objectives": {"code": "1.1", "level": "Output", "text": "Plataformas de TI instaladas e operacionais", "parent": "OC1", "source_problem": "C1"},
    "indicators": {"id": "I1", "objective_code": "OC1", "indicator": "Taxa de discrepância entre fontes de dados", "unit": "%", "baseline": 18, "baseline_year": 2026, "target": 6, "target_year": 2028, "current": 14, "source": "Relatório de qualidade", "frequency": "Semestral", "responsible": "Gestor", "specific": "Sim", "measurable": "Sim", "available": "Sim", "relevant": "Sim", "timely": "Sim"},
    "benchmarks": {"indicator_id": "I1", "peer": "País vizinho A", "value": 4, "year": 2025, "note": ""},
    "timeseries": {"indicator_id": "I1", "year": 2024, "value": 19.6},
    "assumptions": {"id": "H1", "type": "Operational", "objective_code": "1.1", "text": "Os fornecedores entregam o equipamento a tempo", "important": "Sim", "holds": "Possibly", "evidence": "Lições de projetos anteriores", "evidence_quality": 3, "redesign_possible": "Não"},
    "preconditions": {"id": "C1", "text": "Liderança comprometida com a reforma", "leads_to": "OC1", "assumption": "Direção mantém-se estável"},
    "activities": {"id": "A1", "name": "Diagnóstico e requisitos", "output_code": "1.1", "type": "Production", "predecessors": "", "optimistic": 1.5, "most_likely": 2, "pessimistic": 3, "cost": 40000, "distribution": "Uniform", "responsible": "Consultor TI", "crash_duration": 1.5, "crash_cost": 47000, "milestone": "Não", "loe": "Não", "pct_complete": 0, "actual_cost": 0, "wbs_code": "1.1"},
    "budget": {"id": "L1", "activity_id": "A1", "category": "Fees & Direct Expenses", "item": "Consultor sénior", "unit": "dia", "quantity": 40, "unit_cost": 600, "phase": "Inception"},
    "risks": {"id": "R1", "type": "Human resources", "description": "Rotação elevada dos técnicos formados", "likelihood": 3, "impact": 3, "target_exposure": 4, "existing_mitigation": "Pacto de permanência", "proposed_mitigation": "Plano de retenção", "risk_manager": "Direção", "risk_owner": "Gestor", "review_by": "Trimestral", "review": "", "assumption_id": "H2", "level_affected": "Activity", "strategy": "Reduce", "contingency": 15000, "preventive_activity": "A11", "corrective_action": "Contratar técnicos temporários", "trigger": "Rotação > 15% num trimestre"},
    "procurement": {"id": "Q1", "item": "Servidores e licenças", "category": "Goods", "activity_id": "A2", "estimated_cost": 180000, "method": "Competitive Bidding", "planned_date": "2027-03-01", "responsible": "Consultor TI", "selection_criteria": "Preço 40%, técnica 40%, assistência 20%", "risk": "Atrasos de entrega"},
    "cashflows": {"year": 1, "investment": 120000, "operating_costs": 30000, "benefits": 120000, "note": "Ano 0 = início do projeto"},
    "tracking": {"date": "2027-06-30", "ev": 300000, "ac": 320000, "note": "Fim do 2.º trimestre"},
    "evaluation": {"id": "E1", "criterion": "Effectiveness", "q_type": "Normative", "question": "Os resultados foram alcançados?", "judgement_criteria": "Metas de I2 e I3 atingidas", "indicator": "I2, I3", "source": "Relatórios", "data_tools": "Análise documental; entrevistas", "data_type": "Mixed", "method": "Análise de séries"},
    "wbs": {"code": "1.1", "name": "Plataformas de TI instaladas e operacionais", "type": "Work package", "output_code": "1.1",
            "description": "Inclui A1 e A2 (requisitos, aquisição e instalação); exclui a manutenção após o projeto", "deliverable": "Servidores e software estatístico operacionais",
            "acceptance": "Testes de aceitação aprovados; I5 = 45 dias", "owner": "Consultor TI", "weight": 60},
    "wbs_assign": {"id": "A1", "name": "Diagnóstico e requisitos", "wbs_code": "1.1"},
    "risk_params": {"risk_threshold": 0.10},
    "ind_reviews": {"indicator_id": "I2", "date": "2027-06-30", "value": 14.5, "source": "Relatório de qualidade T2", "review": "Abaixo da trajetória: atraso na plataforma", "reviewer": "Técnico M&A"},
    "milestones": {"id": "M1", "name": "Plataforma de TI operacional", "activity_id": "A2", "planned_date": "2027-06-30", "forecast_date": "2027-07-15", "actual_date": "", "accepted": "Não", "accepted_by": "", "deviation_cause": "Atraso do fornecedor", "corrective_action": "Penalização contratual e reforço da equipa"},
    "changes": {"id": "CR1", "date": "2027-05-10", "element_type": "Schedule", "element_ref": "A4", "description": "Prolongar a formação em 2 semanas", "justification": "Rotação de técnicos", "old_value": "6 semanas", "new_value": "8 semanas", "impact_time": 14, "impact_cost": 5000, "impact_quality": "Sem impacto", "requested_by": "Gestor do projeto", "approval_authority": "Comité de acompanhamento", "status": "Approved", "decision_date": "2027-05-20"},
    "risk_reviews": {"risk_id": "R1", "date": "2027-06-30", "likelihood": 2, "impact": 3, "status": "Open", "incident": "", "delay": 0, "cost_impact": 0, "note": "Plano de retenção eficaz"},
    "assumption_reviews": {"assumption_id": "H1", "date": "2027-06-30", "status": "At risk", "evidence": "Fornecedor anunciou atrasos", "affects_relevance": "Não", "affects_feasibility": "Sim", "affects_sustainability": "Não", "action": "Ativar fornecedor alternativo"},
    "contingency_log": {"date": "2027-06-30", "risk_id": "R3", "reserve": "Contingency reserve", "movement": "Use", "amount": 8000, "approved_by": "Gestor do projeto", "note": "Custo do atraso de entrega"},
    "funding": {"date": "2027-01-15", "source": "União Europeia", "amount": 300000, "status": "Received", "note": "1.ª tranche"},
    "engagement": {"id": "EN1", "stakeholder": "Ministério X", "tool": "Repeated interaction", "objective": "Manter o apoio político", "frequency": "Trimestral", "responsible": "Diretor", "next_date": "2027-09-30", "status": "Ongoing"},
    "feedback": {"id": "F1", "date": "2027-06-15", "stakeholder_group": "Técnicos formados", "channel": "Survey", "about": "A4", "feedback": "Pedem mais exercícios práticos", "satisfaction": 3, "anonymous": "Sim", "action_taken": "Sessões práticas adicionadas", "status": "Closed"},
    "bids": {"procurement_id": "Q1", "bidder": "Empresa A", "compliant": "Sim", "technical_score": 82, "price": 171000, "note": ""},
    "closure": {"procurement_id": "Q1", "step": "cs02", "done": "Sim", "date": "2027-09-10", "note": "Entregáveis verificados"},
    "comm_plan": {"id": "K1", "circle": "1", "audience": "Utilizadores das estatísticas", "objective": "Promover o uso dos novos dados", "key_message": "Dados mais fiáveis e mais rápidos", "tool": "Workshops", "activity_id": "A10", "frequency": "Semestral", "budget": 4000, "indicator": "N.º de participantes", "target": 60, "actual": 45},
    "sustainability": {"pillar": "Institutional", "score": 4, "indicator": "Orçamento próprio para manutenção", "evidence": "Plano de atividades 2029", "sdg": "ODS 17"},
    "me_quality": {"item": "me01", "answer": "Yes", "evidence": "Plano de M&A aprovado"},
    "audits": {"id": "AU1", "type": "Financial", "date": "2027-12-15", "auditor": "Auditor externo", "scope": "Despesas do 1.º ano", "findings": "Faltam 2 comprovativos", "recommendations": "Reforçar o arquivo", "corrective_action": "Comprovativos recuperados", "status": "Done"},
    "ownership": {"id": "O1", "result": "Manual de procedimentos", "contributors": "INE, Alfândegas", "ip_type": "Copyright", "regime": "Shared", "publication_rights": "CC BY com menção do financiador", "agreement_ref": "Acordo de parceria, art. 12"},
    "lessons": {"id": "LL1", "category": "Monitoring", "lesson": "Indicadores sem responsável ficam sem dados", "evidence": "2 indicadores sem medições no 1.º ano", "recommendation": "Atribuir responsável e frequência a cada indicador"},
    "best_practices": {"id": "BP1", "practice": "Revisão mensal de riscos com o comité", "criteria": "Eficaz, replicável, baixo custo", "evidence": "Exposição total reduzida", "replicability": 4, "validated_by": "Comité de acompanhamento"},
    "dissemination": {"id": "D1", "channel": "Policy briefs", "audience": "Decisores políticos", "product": "Policy brief com recomendações", "date": "2028-06-30", "responsible": "Gestor", "reach_target": 50, "reach_actual": ""},
}
EXAMPLES["procurement"].update({"scope_certainty": "High", "contract_type": "Lump sum / Fixed price", "stage": "ts11", "tech_weight": 0.4, "awarded_to": "", "contract_value": ""})

BLANK_SHEETS = [
    ("policy_goals", "1 Políticas", "1 Policy", "Objetivos estratégicos e indicadores de impacto", "Strategic goals & impact indicators"),
    ("stakeholders", "2 Stakeholders", "2 Stakeholders", "Stakeholders (colunas do professor + 4 camadas PCM)", "Stakeholders (professor's columns + 4 PCM layers)"),
    ("behaviour", "3 Comportamento", "3 Behaviour", "Padrões comportamentais do grupo-alvo (1–5)", "Target-group behavioural patterns (1–5)"),
    ("problems", "4 Problemas", "4 Problems", "Árvore de problemas e de objetivos (Effect / Core problem / Cause)", "Problem & objective tree (Effect / Core problem / Cause)"),
    ("objectives", "5 Logframe", "5 Logframe", "Lógica de intervenção: IMP (Impact), OC1 (Outcome), 1.1 (Output)", "Intervention logic: IMP (Impact), OC1 (Outcome), 1.1 (Output)"),
    ("indicators", "6 Indicadores", "6 Indicators", "Indicadores SMART (baseline, meta, fonte de verificação)", "SMART indicators (baseline, target, source of verification)"),
    ("benchmarks", "7 Benchmarking", "7 Benchmarking", "Valores de pares por indicador", "Peer values per indicator"),
    ("timeseries", "8 Séries", "8 Time series", "Série histórica por indicador", "Historical series per indicator"),
    ("assumptions", "9 Pressupostos", "9 Assumptions", "Pressupostos (objective_code = objetivo que condicionam)", "Assumptions (objective_code = objective they condition)"),
    ("preconditions", "10 ToC", "10 ToC", "Pré-condições da Teoria da Mudança", "Theory of Change preconditions"),
    ("activities", "11 Atividades", "11 Activities", "Atividades e variáveis PERT/CPM (a ≤ m ≤ b; predecessoras separadas por vírgulas; wbs_code = pacote de trabalho)", "Activities & PERT/CPM variables (a ≤ m ≤ b; comma-separated predecessors; wbs_code = work package)"),
    ("wbs", "11b WBS-EAP", "11b WBS", "WBS / EAP: elementos e dicionário (o código define a hierarquia: 1 → 1.1 → 1.1.1; custos vêm das atividades)", "WBS: elements and dictionary (the code defines the hierarchy: 1 → 1.1 → 1.1.1; costs come from the activities)"),
    ("budget", "12 Orçamento", "12 Budget", "Linhas de orçamento: quantidade × custo unitário", "Budget lines: quantity × unit cost"),
    ("risks", "13 Riscos", "13 Risks", "Registo de riscos alargado e matriz de gestão (P e I 1–4; impacto adverso = linha do logframe do pressuposto; corretiva + gatilho «se e quando…»)",
     "Extended risk register & management matrix (L and I 1–4; adverse impact = logframe row of the assumption; corrective + trigger 'if and when…')"),
    ("risk_params", "13b Limiar de risco", "13b Risk threshold", "Limiar de risco da organização (% do orçamento: 5%, 10% ou 15%) — escreva 0,10 ou 10%",
     "Organisation's risk threshold (% of the budget: 5%, 10% or 15%) — write 0.10 or 10%"),
    ("procurement", "14 Procurement", "14 Procurement", "Plano de procurement", "Procurement plan"),
    ("cashflows", "15 Fluxos", "15 Cash flows", "Fluxos de caixa anuais para VAL/TIR/MIRR (ano 0 = início)", "Annual cash flows for NPV/IRR/MIRR (year 0 = start)"),
    ("tracking", "16 Controlo EVM", "16 EVM tracking", "Histórico de EV e AC acumulados por data de controlo", "History of cumulative EV and AC per status date"),
    ("evaluation", "17 Avaliação", "17 Evaluation", "Matriz de avaliação OCDE-CAD (perguntas tipificadas)", "OECD-DAC evaluation matrix (typed questions)"),
]

# implementation, monitoring, evaluation & closure sheets
MON_SHEETS = {
    "ind_reviews": ("Medições indicadores", "Indicator measurements", "Medições dos indicadores (uma linha por medição; indicator_id = ID do indicador)", "Indicator measurements (one row per measurement; indicator_id = indicator ID)"),
    "milestones": ("Marcos", "Milestones", "Marcos e entregáveis (data prevista vazia = fim da atividade no CPM)", "Milestones & deliverables (empty planned date = activity finish in CPM)"),
    "changes": ("Alterações", "Changes", "Registo de pedidos de alteração (outcome/impacto = alteração estratégica)", "Change request log (outcome/impact = strategic change)"),
    "risk_reviews": ("Revisões riscos", "Risk reviews", "Revisões periódicas dos riscos (risk_id = ID do risco; P e I de 1 a 4)", "Periodic risk reviews (risk_id = risk ID; L and I from 1 to 4)"),
    "assumption_reviews": ("Revisões pressupostos", "Assumption reviews", "Revisões dos pressupostos (assumption_id = ID do pressuposto)", "Assumption reviews (assumption_id = assumption ID)"),
    "contingency_log": ("Contingência", "Contingency", "Movimentos das reservas de contingência e de gestão", "Contingency & management reserve movements"),
    "engagement": ("Envolvimento", "Engagement", "Plano de envolvimento dos stakeholders", "Stakeholder engagement plan"),
    "feedback": ("Feedback", "Feedback", "Registo de feedback dos stakeholders (satisfação 1–5)", "Stakeholder feedback log (satisfaction 1–5)"),
    "comm_plan": ("Plano comunicação", "Communication plan", "Plano de comunicação (círculos 1, 2, 3)", "Communication plan (circles 1, 2, 3)"),
    "procurement": ("Procurement e contratos", "Procurement & contracts", "Plano de procurement com tipo de contrato e etapa do concurso", "Procurement plan with contract type and tender stage"),
    "bids": ("Propostas", "Bids", "Propostas recebidas (procurement_id = ID da aquisição; pontuação técnica 0–100)", "Bids received (procurement_id = purchase ID; technical score 0–100)"),
    "closure": ("Encerramento contratos", "Contract closure", "Encerramento dos contratos (15 passos, ver 'Listas' → closure_step)", "Contract closure (15 steps, see 'Lists' → closure_step)"),
    "funding": ("Financiamento", "Funding", "Tranches de financiamento previstas e recebidas", "Planned and received funding tranches"),
    "evaluation": ("Matriz avaliação", "Evaluation matrix", "Matriz de avaliação OCDE-CAD (perguntas tipificadas)", "OECD-DAC evaluation matrix (typed questions)"),
    "me_quality": ("Qualidade M&A", "M&E quality", "Lista de verificação da qualidade do M&A (10 elementos: me01–me10)", "M&E quality checklist (10 items: me01–me10)"),
    "sustainability": ("Sustentabilidade", "Sustainability", "Sustentabilidade por pilar (1–5) e ODS", "Sustainability per pillar (1–5) and SDGs"),
    "audits": ("Auditorias", "Audits", "Auditorias e ações corretivas", "Audits and corrective actions"),
    "ownership": ("Propriedade", "Ownership", "Propriedade dos resultados e direitos de publicação", "Ownership of results and publication rights"),
    "lessons": ("Lições", "Lessons", "Lições aprendidas (8 categorias)", "Lessons learned (8 categories)"),
    "best_practices": ("Boas práticas", "Best practices", "Boas práticas validadas", "Validated best practices"),
    "dissemination": ("Disseminação", "Dissemination", "Plano e resultados da disseminação", "Dissemination plan and results"),
}

# WBS / EAP sheets ("wbs_assign" is a pseudo-table: it only updates activities.wbs_code)
PSEUDO = {"wbs_assign": [("id", "text", ""), ("name", "text", ""), ("wbs_code", "text", "")],
          # risk threshold (meta.risk_threshold): one row; 0.10, 10 or "10%" are all read as 10%
          "risk_params": [("risk_threshold", "num", 0.10)]}
WBS_SHEETS = {
    "wbs": ("WBS-EAP", "WBS", "WBS / EAP: elementos e dicionário (o código define a hierarquia: 1 → 1.1 → 1.1.1; custos vêm das atividades)",
            "WBS: elements and dictionary (the code defines the hierarchy: 1 → 1.1 → 1.1.1; costs come from the activities)"),
    "wbs_assign": ("WBS-Atividades", "WBS-Activities", "Ligação de cada atividade a um pacote de trabalho (wbs_code = código de um pacote da folha WBS)",
                   "Link of each activity to a work package (wbs_code = code of a package in the WBS sheet)"),
}
RISK_SHEETS = {
    "risks": ("Riscos", "Risks", "Matriz de gestão de riscos: impacto adverso = linha do logframe do pressuposto (Operacional → Activity; Comportamental → Output; "
              "Político → Outcome); preventiva baixa a probabilidade, corretiva + gatilho «se e quando…» baixa a consequência; contingency = custo da estratégia",
              "Risk management matrix: adverse impact = logframe row of the assumption (Operational → Activity; Behavioural → Output; Political → Outcome); "
              "preventive lowers likelihood, corrective + trigger 'if and when…' lowers consequence; contingency = cost of the strategy"),
    "risk_params": ("Limiar de risco", "Risk threshold", "Limiar de risco da organização = % do orçamento tolerado como custo do risco (5%, 10% ou 15%): escreva 0,10 ou 10%",
                    "Organisation's risk threshold = % of the budget tolerated as cost of risk (5%, 10% or 15%): write 0.10 or 10%"),
}
SHEET_INFO = {**WBS_SHEETS, **RISK_SHEETS}


# thematic templates (key → (file name pt, file name en, title pt, title en, tables))
THEMATIC = {
    "monitoring": ("Modelo_1_Monitorizacao_indicadores_marcos", "Template_1_Indicator_milestone_monitoring",
                   "Monitorização de indicadores e marcos", "Indicator & milestone monitoring", ["ind_reviews", "milestones"]),
    "changes": ("Modelo_2_Alteracoes_revisoes_contingencia", "Template_2_Changes_reviews_contingency",
                "Registo de alterações, revisões de riscos/pressupostos e contingência", "Change log, risk/assumption reviews & contingency",
                ["changes", "risk_reviews", "assumption_reviews", "contingency_log"]),
    "engagement": ("Modelo_3_Envolvimento_feedback", "Template_3_Engagement_feedback", "Envolvimento dos stakeholders e feedback", "Stakeholder engagement & feedback", ["engagement", "feedback"]),
    "comm": ("Modelo_4_Plano_comunicacao", "Template_4_Communication_plan", "Plano de comunicação", "Communication plan", ["comm_plan"]),
    "contracts": ("Modelo_5_Concursos_contratos_financiamento", "Template_5_Tenders_contracts_funding", "Concursos, contratos e financiamento", "Tenders, contracts & funding",
                  ["procurement", "bids", "closure", "funding"]),
    "evaluation": ("Modelo_6_Avaliacao_licoes", "Template_6_Evaluation_lessons", "Avaliação, encerramento e lições", "Evaluation, closure & lessons",
                   ["evaluation", "me_quality", "sustainability", "audits", "ownership", "lessons", "best_practices", "dissemination"]),
    "wbs": ("Modelo_7_WBS_EAP_dicionario", "Template_7_WBS_dictionary", "WBS / EAP e dicionário", "WBS & dictionary", ["wbs", "wbs_assign"]),
    "riskmgmt": ("Modelo_8_Matriz_gestao_riscos", "Template_8_Risk_management_matrix", "Matriz de gestão de riscos e limiar de risco", "Risk management matrix & risk threshold",
                 ["risks", "risk_params"]),
}
THEMATIC_ORDER = ["wbs", "riskmgmt", "monitoring", "changes", "engagement", "comm", "contracts", "evaluation"]   # planning before monitoring
SHEET_INFO.update(MON_SHEETS)


def _yesno():
    return ("Sim", "Não") if _pt() else ("Yes", "No")


def blank_template(which: str | None = None, p: dict | None = None) -> bytes:
    """Empty template to fill in Excel and upload into the app (Home → Import).
    which=None → full extended template (every module); which in THEMATIC → thematic template.
    With p, the same template comes FILLED IN with the project's rows (from row 5) — useful to test the upload."""
    from .ui import label as _lab
    if which in THEMATIC:
        _fp, _fe, title_pt, title_en, tabs = THEMATIC[which]
        sheets = [(t, f"{k + 1} {SHEET_INFO[t][0]}"[:31], f"{k + 1} {SHEET_INFO[t][1]}"[:31], SHEET_INFO[t][2], SHEET_INFO[t][3]) for k, t in enumerate(tabs)]
    else:
        title_pt, title_en = "Modelo alargado em branco", "Blank extended template"
        n0 = len(BLANK_SHEETS)
        extra = [t for t in MON_SHEETS if t not in ("evaluation", "procurement")]
        sheets = BLANK_SHEETS + [(t, f"{n0 + k + 1} {MON_SHEETS[t][0]}"[:31], f"{n0 + k + 1} {MON_SHEETS[t][1]}"[:31], MON_SHEETS[t][2], MON_SHEETS[t][3]) for k, t in enumerate(extra)]
    wb = Workbook()
    ws = wb.active
    ws.title = "Leia-me" if _pt() else "Read-me"
    lines = [
        (tr(f"{title_pt} — PM Studio", f"{title_en} — PM Studio"), 14, True),
        ("", 10, False),
        (tr("Como usar", "How to use"), 11, True),
        (tr("1. Preencha as folhas que precisar (não é obrigatório preencher todas). Comece na linha 5, por baixo dos cabeçalhos.", "1. Fill in the sheets you need (not all are required). Start on row 5, below the headers."), 10, False),
        (tr("2. A linha 3 de cada folha (a cinzento) é um EXEMPLO de preenchimento — não é importada.", "2. Row 3 of each sheet (grey) is a filling EXAMPLE — it is not imported."), 10, False),
        (tr("3. Não altere os cabeçalhos da linha 4: o código entre [ ] identifica o campo na app.", "3. Do not change the row-4 headers: the code in [ ] identifies the field in the app."), 10, False),
        (tr("4. Use as listas pendentes; os códigos aceites e a tradução estão na folha 'Listas'.", "4. Use the drop-down lists; accepted codes and translations are in the 'Lists' sheet."), 10, False),
        (tr("5. Na app: Início → Importar/exportar → 'Modelos Excel' → carregar este ficheiro → escolher Acrescentar ou Substituir.", "5. In the app: Home → Import/export → 'Excel templates' → upload this file → choose Append or Replace."), 10, False),
        ("", 10, False),
        (tr("Regras essenciais", "Key rules"), 11, True),
        (tr("• IDs curtos e únicos: S1 (stakeholders), P1/C1/E1 (problemas), I1 (indicadores), H1 (pressupostos), A1 (atividades), R1 (riscos), Q1 (aquisições).", "• Short unique IDs: S1 (stakeholders), P1/C1/E1 (problems), I1 (indicators), H1 (assumptions), A1 (activities), R1 (risks), Q1 (purchases)."), 10, False),
        (tr("• Logframe: códigos IMP (impacto), OC1, OC2 (outcomes), 1.1, 1.2, 2.1 (outputs); 'parent' = código do nível superior.", "• Logframe: codes IMP (impact), OC1, OC2 (outcomes), 1.1, 1.2, 2.1 (outputs); 'parent' = upper-level code."), 10, False),
        (tr("• Pressupostos: Output → Operational; Outcome → Behavioural; Impact → Political (objetivo que o pressuposto condiciona).", "• Assumptions: Output → Operational; Outcome → Behavioural; Impact → Political (objective the assumption conditions)."), 10, False),
        (tr("• Atividades: otimista ≤ mais provável ≤ pessimista, na unidade de tempo do projeto; predecessoras ex.: 'A1, A3'.", "• Activities: optimistic ≤ most likely ≤ pessimistic, in the project time unit; predecessors e.g. 'A1, A3'."), 10, False),
        (tr("• Riscos: probabilidade e impacto de 1 (baixo) a 4 (alto); exposição = P × I (calculada pela app).", "• Risks: likelihood and impact from 1 (low) to 4 (high); exposure = L × I (computed by the app)."), 10, False),
        (tr("• Matriz de gestão de riscos: impacto adverso (level_affected) = linha do logframe onde está o pressuposto (Operacional → Activity; Comportamental → Output; Político → Outcome); "
            "ação corretiva e gatilho «se e quando…»; contingency = custo da estratégia. Limiar de risco (5%, 10% ou 15% do orçamento) na folha 'Limiar de risco'.",
            "• Risk management matrix: adverse impact (level_affected) = logframe row where the assumption sits (Operational → Activity; Behavioural → Output; Political → Outcome); "
            "corrective action and trigger 'if and when…'; contingency = cost of the strategy. Risk threshold (5%, 10% or 15% of the budget) in the 'Risk threshold' sheet."), 10, False),
        (tr("• Percentagens em fração (0,25 = 25%). Datas no formato AAAA-MM-DD.", "• Percentages as fractions (0.25 = 25%). Dates as YYYY-MM-DD."), 10, False),
        ("", 10, False),
        (tr("Os modelos do professor (StakeholderRegister e RiskRegister) continuam a ser os modelos de referência e podem ser carregados tal como estão; este ficheiro complementa-os.",
            "The professor's templates (StakeholderRegister and RiskRegister) remain the reference templates and can be uploaded as they are; this file complements them."), 10, False),
        (tr("• Referências entre folhas: use os IDs do projeto (ex.: indicator_id = I2, risk_id = R1, assumption_id = H1, activity_id = A4, procurement_id = Q1).",
            "• Cross references: use the project's IDs (e.g. indicator_id = I2, risk_id = R1, assumption_id = H1, activity_id = A4, procurement_id = Q1)."), 10, False),
        ("", 10, False),
        (tr("Folhas: ", "Sheets: ") + " · ".join(sp if _pt() else se for _t, sp, se, _a, _b in sheets), 10, False),
    ]
    for i, (t, sz, b) in enumerate(lines, 1):
        c = ws.cell(i, 1, t)
        _font(c, bold=b, size=sz)
        c.alignment = Alignment(wrap_text=True)
    ws.column_dimensions["A"].width = 140

    # Lists sheet
    wl = wb.create_sheet("Listas" if _pt() else "Lists")
    col = 1
    for name, rows in OPTIONS.items():
        if name in ("raci",):
            continue
        wl.cell(1, col, name)
        _font(wl.cell(1, col), bold=True, color="FFFFFF")
        wl.cell(1, col).fill = HDR
        wl.cell(1, col + 1, "PT")
        _font(wl.cell(1, col + 1), bold=True, color="FFFFFF")
        wl.cell(1, col + 1).fill = HDR
        for k, r in enumerate(rows, 2):
            wl.cell(k, col, r[0])
            wl.cell(k, col + 1, r[-1])
        wl.column_dimensions[L(col)].width = 26
        wl.column_dimensions[L(col + 1)].width = 30
        col += 3

    yes, no = _yesno()
    grey = PatternFill("solid", fgColor="EDEDED")
    inp = PatternFill("solid", fgColor="FFFFF0")
    for table, spt, sen, dpt, den in sheets:
        ws = wb.create_sheet(spt if _pt() else sen)
        spec = TABLES.get(table) or PSEUDO[table]
        ws["A1"] = f"{dpt if _pt() else den}   [table:{table}]"
        _font(ws["A1"], bold=True, size=13)
        ws["A2"] = tr("Linha 3 = exemplo (não é importado). Preencha a partir da linha 5. Não altere a linha 4.", "Row 3 = example (not imported). Fill in from row 5. Do not change row 4.")
        _font(ws["A2"], italic=True, color="595959")
        ex = EXAMPLES.get(table, {})
        data = _template_rows(p, table) if p is not None else []
        last_r = max(104, 4 + len(data) + 50)
        for j, (f, kind, _d) in enumerate(spec, 1):
            v = ex.get(f, "")
            c = ws.cell(3, j, v)
            _font(c, italic=True, color="7F7F7F")
            c.fill = grey
            lab = _lab(f, table)
            h = ws.cell(4, j, f"{lab} [{f}]")
            gk = WBS_FIELD_GLOSSARY.get(f) if table in ("wbs", "wbs_assign") or f == "wbs_code" else None
            if gk:
                _gl_comment(h, gk)
            _font(h, bold=True, color="FFFFFF")
            h.fill = HDR
            h.alignment = Alignment(wrap_text=True, vertical="center")
            h.border = BD
            for r in range(5, last_r + 1):
                cc = ws.cell(r, j)
                if r - 5 < len(data):
                    cc.value = _cell_value(data[r - 5].get(f), kind, yes, no)
                cc.border = BD
                cc.fill = inp
                _font(cc, color="0000FF")
                if f in ("code", "wbs_code", "output_code", "objective_code"):
                    cc.number_format = "@"      # keep codes such as 1.10 as text
                if kind == "long":
                    cc.alignment = Alignment(wrap_text=True, vertical="top")
            rng = f"{L(j)}5:{L(j)}{last_r}"
            if kind.startswith("sel:"):
                _dv(ws, rng, [str(o[0]) for o in OPTIONS[kind[4:]]])
            elif kind in ("scale5", "scale4"):
                dv = DataValidation(type="whole", operator="between", formula1="1", formula2="5" if kind == "scale5" else "4", allow_blank=True,
                                    showErrorMessage=True, error=tr("Valor inteiro entre 1 e ", "Whole number between 1 and ") + ("5" if kind == "scale5" else "4"))
                ws.add_data_validation(dv)
                dv.add(rng)
            elif kind == "bool":
                _dv(ws, rng, [yes, no])
            elif kind in ("num", "int"):
                dv = DataValidation(type="decimal", allow_blank=True, operator="greaterThanOrEqual", formula1="-1000000000000",
                                    showErrorMessage=True, error=tr("Introduza um número", "Enter a number"))
                ws.add_data_validation(dv)
                dv.add(rng)
                if f in ("cost", "actual_cost", "crash_cost", "estimated_cost", "unit_cost", "contingency", "investment", "operating_costs", "benefits", "ev", "ac",
                         "amount", "price", "budget", "cost_impact", "impact_cost", "contract_value"):
                    for r in range(5, last_r + 1):
                        ws.cell(r, j).number_format = '#,##0'
                if f == "pct_complete":
                    for r in range(5, last_r + 1):
                        ws.cell(r, j).number_format = "0%"
            w = 42 if kind == "long" else 9 if f in ("id", "code") else 14 if kind in ("num", "int", "scale5", "scale4", "bool") else 22
            ws.column_dimensions[L(j)].width = w
        ws.row_dimensions[4].height = 34
        ws.freeze_panes = "A5"
    if any(t == "wbs" for t, *_r in sheets):
        _wbs_glossary_sheet(wb)          # formulas of the WBS roll-ups, same text as the app
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _template_rows(p: dict, table: str) -> list[dict]:
    if table == "wbs_assign":
        return [{"id": a["id"], "name": a.get("name", ""), "wbs_code": a.get("wbs_code", "")} for a in p.get("activities", [])]
    if table == "risk_params":
        return [{"risk_threshold": float(p["meta"].get("risk_threshold") or 0.10)}]
    return list(p.get(table, []) or [])


def _cell_value(v, kind: str, yes: str, no: str):
    if kind == "bool":
        return yes if v else no
    if v is None or (isinstance(v, float) and v != v):
        return None
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return v


def activities_template(fmt: str = "xlsx", p: dict | None = None) -> bytes:
    """Standalone activities file (for 'Import activities'); 3 example rows to replace."""
    cols = ["id", "name", "output_code", "wbs_code", "type", "predecessors", "optimistic", "most_likely", "pessimistic", "cost", "distribution", "responsible", "crash_duration", "crash_cost", "loe"]
    yes, no = _yesno()
    ex = [["A1", "Diagnóstico e requisitos", "1.1", "1.1", "Production", "", 1.5, 2, 3, 40000, "Uniform", "Consultor", 1.5, 47000, no],
          ["A2", "Aquisição de equipamento", "1.1", "1.1", "Production", "A1", 3, 4, 7, 180000, "Start", "Compras", 3, 200000, no],
          ["A3", "Gestão do projeto", "3.1", "3.1", "Support - Management", "", 1, 1, 1, 60000, "Uniform", "Gestor de projeto", None, None, yes]]
    if p is not None:
        ex = [[(yes if a.get(c) else no) if c == "loe" else a.get(c) for c in cols] for a in p.get("activities", [])]
    df = pd.DataFrame(ex, columns=cols)
    if fmt == "csv":
        # Portuguese Excel expects ';' as separator and ',' as decimal mark; the importer reads both conventions
        if tr("pt", "en") == "pt":
            return df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        return df.to_csv(index=False).encode("utf-8-sig")
    from .ui import LABELS
    wb = Workbook()
    ws = wb.active
    ws.title = "Atividades" if _pt() else "Activities"
    kinds = {f: k for f, k, _ in TABLES["activities"]}
    for j, f in enumerate(cols, 1):
        h = ws.cell(1, j, f"{LABELS.get(f, (f, f))[0 if _pt() else 1]} [{f}]")
        _font(h, bold=True, color="FFFFFF")
        h.fill = HDR
        h.alignment = Alignment(wrap_text=True)
        ws.column_dimensions[L(j)].width = 30 if f == "name" else 14
        for i, row in enumerate(ex, 2):
            c = ws.cell(i, j, row[j - 1])
            _font(c, color="0000FF")
            if f in ("output_code", "wbs_code"):
                c.number_format = "@"
        if kinds[f].startswith("sel:"):
            _dv(ws, f"{L(j)}2:{L(j)}300", [str(o[0]) for o in OPTIONS[kinds[f][4:]]])
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "A2"
    note = wb.create_sheet("Leia-me" if _pt() else "Read-me")
    for i, t in enumerate([tr("As linhas 2–4 da folha de atividades são EXEMPLOS: substitua-as pelas suas atividades.", "Rows 2–4 of the activities sheet are EXAMPLES: replace them with your activities."),
                           tr("Não altere os cabeçalhos (o código entre [ ] identifica o campo).", "Do not change the headers (the code in [ ] identifies the field)."),
                           tr("Predecessoras separadas por vírgulas (ex.: A1, A3). Durações na unidade de tempo do projeto; otimista ≤ mais provável ≤ pessimista.", "Comma-separated predecessors (e.g. A1, A3). Durations in the project time unit; optimistic ≤ most likely ≤ pessimistic."),
                           tr("Código WBS (opcional) = pacote de trabalho da WBS / EAP (ex.: 1.1). Num export do MS Project, a coluna 'WBS' é reconhecida automaticamente; se ficar vazio, a app liga a atividade ao pacote do seu output.",
                              "WBS code (optional) = WBS work package (e.g. 1.1). In an MS Project export the 'WBS' column is recognised automatically; if empty, the app links the activity to its output's package."),
                           tr("Esforço contínuo (LOE) = Sim para a gestão do projeto e a M&A contínua: a duração é derivada (acompanha o trabalho de produção até ao fim) e não define o caminho crítico; a duração escrita é ignorada.",
                              "Level of effort (LOE) = Yes for project management and continuous M&E: the duration is derived (follows the production work to the end) and does not define the critical path; the typed-in duration is ignored."),
                           tr("Importar na app: Início → Importar/exportar → 'Atividades'.", "Import in the app: Home → Import/export → 'Activities'.")], 1):
        note.cell(i, 1, t)
    note.column_dimensions["A"].width = 120
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def professor_blank(which: str) -> bytes:
    path = os.path.join(TPL, "StakeholderRegister_template.xlsx" if which == "stakeholders" else "RiskRegister_Template.xlsx")
    with open(path, "rb") as fh:
        return fh.read()
