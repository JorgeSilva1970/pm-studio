# Guia de teste — templates preenchidos (Retalho)

Projeto de exemplo: **Transformação omnicanal — Supermercados Vale Verde** (42 lojas, loja online, click & collect, cartão de fidelização digital, stock unificado, 14 meses, BAC 1 665 000 €).
É o mesmo projeto do exemplo **🛒 Retalho** da app (Início → Exemplos), por isso podes comparar o resultado de cada upload com o exemplo.

Todos os ficheiros importam-se em **Início → Importar/exportar**:

- **Excel (.xlsx):** caixa *StakeholderRegister, RiskRegister, modelo alargado ou modelo temático*, depois **Importar Excel**.
- **Atividades (.xlsx/.csv):** caixa *Ficheiro de atividades*, depois **Importar atividades**.
- **Projeto completo (.json):** caixa *Projeto completo (JSON)*.

Antes de começares, cria um projeto novo e vazio (Início → Novo projeto) e escolhe o modo **Substituir as tabelas importadas**.

---

## Caminho A — um só ficheiro (o mais rápido)

| Passo | Ficheiro | O que deves ver |
|---|---|---|
| 1 | `11_Modelo_alargado_Retalho_preenchido.xlsx` | Mensagem com as contagens por folha (Stakeholders: 8 · Logframe: 8 · Indicadores: 10 · Atividades: 12 · WBS-EAP: 11 · Riscos: 8 …). Todas as páginas ficam preenchidas, exceto os dados que não são tabelas (ver nota no fim). |

## Caminho B — ficheiro a ficheiro (testa cada modelo)

| Passo | Ficheiro | Página onde verificar | O que deves ver |
|---|---|---|---|
| 1 | `01_StakeholderRegister_Retalho.xlsx` (formato do professor) | 1 · Stakeholders | 8 stakeholders |
| 2 | `02_RiskRegister_Retalho.xlsx` (formato do professor) | 3 · Riscos e 6 · Revisão de riscos | 8 riscos, mais uma revisão datada de 31/10/2027 |
| 3 | `03_Atividades_Retalho.xlsx` (ou `.csv`) | 3 · Atividades e PERT/CPM | 12 atividades, duração de cerca de 13,8 meses |
| 4 | `04_Modelo_7_WBS_EAP_dicionario_Retalho.xlsx` | 3 · WBS / EAP | 11 elementos, 8 pacotes, 12/12 atividades ligadas, regra dos 100% ✅ |
| 5 | `05_Modelo_1_Monitorizacao_indicadores_marcos_Retalho.xlsx` | 6 · Indicadores e marcos | 9 medições e 5 marcos |
| 6 | `06_Modelo_2_Alteracoes_revisoes_contingencia_Retalho.xlsx` | 6 · Alterações e 6 · Revisão de riscos | 2 alterações, 16 revisões de riscos, 6 revisões de pressupostos, 1 movimento de contingência |
| 7 | `07_Modelo_3_Envolvimento_feedback_Retalho.xlsx` | 6 · Envolvimento e feedback | 5 ações e 4 registos de feedback |
| 8 | `08_Modelo_4_Plano_comunicacao_Retalho.xlsx` | 6 · Plano de comunicação | 3 ações (círculos 1, 2 e 3) |
| 9 | `09_Modelo_5_Concursos_contratos_financiamento_Retalho.xlsx` | 6 · Concursos e contratos e 6 · Tesouraria | 4 aquisições, 12 propostas, 12 passos de encerramento, 3 tranches |
| 10 | `10_Modelo_6_Avaliacao_licoes_Retalho.xlsx` | 7 · Avaliação e encerramento | Matriz com 6 perguntas, 10 itens de qualidade M&A, 5 pilares, 1 auditoria, 1 registo de propriedade, 3 lições, 1 boa prática, 3 ações de disseminação |

**Ordem recomendada:** primeiro as atividades (passo 3) e só depois os modelos 1, 5 e 7. Esses modelos referem IDs de atividades, indicadores e riscos (A1, I3, R2…), que já têm de existir no projeto.

**StakeholderRegister do professor:** o formato original não tem colunas de influência, interesse e atitude.
- Se o stakeholder já existir no projeto (o nome tem de coincidir), a app mantém esses valores.
- Num projeto vazio, preenche-os na página Stakeholders ou usa a folha *2 Stakeholders* do modelo alargado.

## Caminho C — projeto completo

| Passo | Ficheiro | O que deves ver |
|---|---|---|
| 1 | `12_Projeto_Retalho_completo.json` | Projeto completo, incluindo também o que não está nos Excel: dados gerais, estratégias, ToC, parâmetros financeiros, RACI, qualidade PCM e desenho da avaliação. |

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

Testado automaticamente: os caminhos A e B reproduzem 100% das tabelas do exemplo (37 tabelas no caminho A, 23 no B). Duração e BAC após o upload são iguais aos do exemplo (13,8 meses; 1 665 000 €).
