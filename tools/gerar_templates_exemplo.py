"""Generate a set of PRE-FILLED upload templates (professor's registers, activities, thematic templates 1-7, extended
template and full JSON) for one of the sample projects, plus a test guide with the expected counts.

The sample projects are NOT offered in the app's example menu: the point is to upload them manually and check that
filling in and uploading the templates works.

Usage:  python tools/gerar_templates_exemplo.py imaging  saida/templates_saude_imagiologia
        python tools/gerar_templates_exemplo.py retail   saida/templates_retalho
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import excel_io as X  # noqa: E402
from core import schedule as S  # noqa: E402
from core import wbs as W  # noqa: E402
from core.demos import DEMOS, SAMPLES, UPLOAD_ONLY, build_demo  # noqa: E402
from core.fmt import money, num  # noqa: E402
from core.i18n import set_lang  # noqa: E402

ORDER = ["monitoring", "changes", "engagement", "comm", "contracts", "evaluation"]


def generate(key: str, out: str, suffix: str) -> dict:
    set_lang("pt")
    p = build_demo(key)
    os.makedirs(out, exist_ok=True)
    files = {
        f"01_StakeholderRegister_{suffix}.xlsx": X.professor_stakeholders(p)[0],
        f"02_RiskRegister_{suffix}.xlsx": X.professor_risks(p)[0],
        f"03_Atividades_{suffix}.xlsx": X.activities_template("xlsx", p),
        f"03_Atividades_{suffix}.csv": X.activities_template("csv", p),
        f"04_Modelo_7_WBS_EAP_dicionario_{suffix}.xlsx": X.blank_template("wbs", p),
    }
    for i, k in enumerate(ORDER, 5):
        files[f"{i:02d}_{X.THEMATIC[k][0]}_{suffix}.xlsx"] = X.blank_template(k, p)
    files[f"11_Modelo_alargado_{suffix}_preenchido.xlsx"] = X.blank_template(None, p)
    files[f"12_Projeto_{suffix}_completo.json"] = json.dumps(p, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    for n, b in files.items():
        with open(os.path.join(out, n), "wb") as fh:
            fh.write(b)
    with open(os.path.join(out, "00_GUIA_DE_TESTE.md"), "w", encoding="utf-8") as fh:
        fh.write(guide(p, key, suffix))
    return p


def guide(p: dict, key: str, suffix: str) -> str:
    sc = S.compute(p)
    n = {t: len(p.get(t, [])) for t in p if isinstance(p.get(t), list)}
    m = p["meta"]
    lv = len(W.leaves(p))
    cur = m.get("currency", "EUR")
    return f"""# Guia de teste — templates preenchidos ({suffix.replace('_', ' ')})

**Projeto:** {m['name']}
**Organização:** {m.get('organisation', '')} · **Pedido por:** {m.get('sponsor', '')}

{m.get('description', '')}

{"Este projeto **não existe nos exemplos da app**: entra só pelos uploads, para testares o preenchimento e o carregamento dos modelos." if key in UPLOAD_ONLY else
 "Este projeto existe também nos exemplos da app (Início → 📂 Projetos → " + DEMOS[key]["pt"] + "): depois de carregares os ficheiros num projeto vazio, podes compará-lo com o exemplo."}

Todos os ficheiros importam-se em **Início → separador ⬆️⬇️ Importar / exportar**:
- **Excel (.xlsx):** caixa *StakeholderRegister, RiskRegister, modelo alargado ou modelo temático*, depois **Importar Excel**.
- **Atividades (.xlsx/.csv):** caixa *Ficheiro de atividades*, depois **Importar atividades**.
- **Projeto completo (.json):** caixa *Projeto completo (JSON)*.

**Antes de começar:**
1. Cria um projeto novo e vazio: Início → separador **📂 Projetos** → *Novo projeto*.
2. No separador **⚙️ Dados do projeto**, define:
   - **Data de início:** {m['start_date']}
   - **Unidade de tempo (PERT/CPM):** meses
   - **Data de controlo (EVM):** {m['status_date']}

   Sem isto, as durações seriam lidas em semanas e o EVM noutra data.
3. No separador **⬆️⬇️ Importar / exportar**, escolhe o modo **Substituir as tabelas importadas**.

---

## Caminho A — um só ficheiro (o mais rápido)

| Passo | Ficheiro | O que deves ver |
|---|---|---|
| 1 | `11_Modelo_alargado_{suffix}_preenchido.xlsx` | Contagens por folha: Stakeholders {n['stakeholders']} · Problemas {n['problems']} · Logframe {n['objectives']} · Indicadores {n['indicators']} · Pressupostos {n['assumptions']} · Atividades {n['activities']} · WBS-EAP {n['wbs']} · Orçamento {n['budget']} · Riscos {n['risks']} · Procurement {n['procurement']} … |

## Caminho B — ficheiro a ficheiro (testa cada modelo)

| Passo | Ficheiro | Página onde verificar | O que deves ver |
|---|---|---|---|
| 1 | `01_StakeholderRegister_{suffix}.xlsx` (formato do professor) | 1 · Stakeholders | {n['stakeholders']} stakeholders |
| 2 | `02_RiskRegister_{suffix}.xlsx` (formato do professor) | 3 · Riscos e 6 · Revisão de riscos | {n['risks']} riscos, mais uma revisão datada da data de controlo |
| 3 | `03_Atividades_{suffix}.xlsx` (ou `.csv`) | 3 · Atividades e PERT/CPM | {n['activities']} atividades; duração ≈ {num(sc['cpm']['duration'], 1)} meses; BAC {money(sc['bac'], cur)} |
| 4 | `04_Modelo_7_WBS_EAP_dicionario_{suffix}.xlsx` | 3 · WBS / EAP | {n['wbs']} elementos, {lv} pacotes de trabalho, {n['activities']}/{n['activities']} atividades ligadas, regra dos 100% ✅ |
| 5 | `05_Modelo_1_Monitorizacao_indicadores_marcos_{suffix}.xlsx` | 6 · Indicadores e marcos | {n['ind_reviews']} medições e {n['milestones']} marcos |
| 6 | `06_Modelo_2_Alteracoes_revisoes_contingencia_{suffix}.xlsx` | 6 · Alterações e 6 · Revisão de riscos | {n['changes']} alterações, {n['risk_reviews']} revisões de riscos, {n['assumption_reviews']} revisões de pressupostos, {n['contingency_log']} movimento(s) de contingência |
| 7 | `07_Modelo_3_Envolvimento_feedback_{suffix}.xlsx` | 6 · Envolvimento e feedback | {n['engagement']} ações e {n['feedback']} registos de feedback |
| 8 | `08_Modelo_4_Plano_comunicacao_{suffix}.xlsx` | 6 · Plano de comunicação | {n['comm_plan']} ações (círculos 1, 2 e 3) |
| 9 | `09_Modelo_5_Concursos_contratos_financiamento_{suffix}.xlsx` | 6 · Concursos e contratos e 6 · Tesouraria | {n['procurement']} aquisições, {n['bids']} propostas, {n['closure']} passos de encerramento, {n['funding']} tranches |
| 10 | `10_Modelo_6_Avaliacao_licoes_{suffix}.xlsx` | 7 · Avaliação e encerramento | {n['evaluation']} perguntas, {n['me_quality']} itens de qualidade M&A, {n['sustainability']} pilares, {n['audits']} auditoria(s), {n['lessons']} lições, {n['dissemination']} ações de disseminação |

**Ordem recomendada:** primeiro as atividades (passo 3) e só depois os modelos 1, 5 e 7. Esses modelos referem IDs de atividades, indicadores e riscos (A1, I3, R2…), que já têm de existir no projeto. Os indicadores, pressupostos e objetivos vêm do modelo alargado (caminho A) ou do JSON.

**StakeholderRegister do professor:** o formato original não tem colunas de influência, interesse e atitude.
- Se o stakeholder já existir no projeto (o nome tem de coincidir), a app mantém esses valores.
- Num projeto vazio, preenche-os na página Stakeholders ou usa a folha *2 Stakeholders* do modelo alargado.

## Caminho C — projeto completo

| Passo | Ficheiro | O que deves ver |
|---|---|---|
| 1 | `12_Projeto_{suffix}_completo.json` | Projeto completo, incluindo também o que não está nos Excel: dados gerais, estratégias, ToC, parâmetros financeiros, RACI, qualidade PCM e desenho da avaliação. |

---

## Como testar o preenchimento

1. Abre um dos modelos no Excel e altera ou acrescenta uma linha a partir da linha 5. Usa as listas pendentes; os códigos estão na folha *Listas*.
2. Grava e volta a carregar o ficheiro na app, no modo **Acrescentar** ou **Substituir**.
3. Confirma a alteração na página correspondente da tabela acima.

**Regras dos modelos:**
- A linha 3 é um exemplo e não é importada.
- Não alteres os cabeçalhos da linha 4: o código entre [ ] identifica o campo.
- As datas podem ser escritas como 2027-06-30 ou como data do Excel.

**Nota:** os Excel transportam as **tabelas** do projeto. Os dados gerais, as estratégias, os parâmetros financeiros e a matriz RACI vão no **JSON** (caminho C) ou introduzem-se diretamente na app.
"""


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "imaging"
    out = sys.argv[2] if len(sys.argv) > 2 else f"templates_{key}"
    suffix = {"imaging": "Imagiologia", "retail": "Retalho"}.get(key, key)
    if key not in SAMPLES:
        raise SystemExit(f"Projeto desconhecido: {key}. Disponíveis: {', '.join(SAMPLES)}")
    generate(key, out, suffix)
    print(f"Modelos preenchidos gerados em {out}")
