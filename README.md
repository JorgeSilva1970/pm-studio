# 🧭 PM Studio — Gestão do Ciclo de Projeto (Project Cycle Management)

Aplicação web em Python (Streamlit) para desenhar, planear, avaliar e acompanhar projetos segundo o **Project Cycle Management (PCM)** e a **abordagem do Quadro Lógico**. Inclui Logic Models, ferramentas analíticas, ferramentas de planeamento (PERT/CPM, Gantt, custos no tempo, riscos, orçamento e procurement), finanças (VAL, TIR, MIRR, WACC), monitorização e avaliação (SMART, benchmarking, EVM) e um agente generativo (Claude, da Anthropic).

Interface **bilingue (PT/EN)**. Persistência em **PostgreSQL** no Render, ou **SQLite** local.

---

## 1. O que a app faz

| Fase | Módulos | Destaques |
|---|---|---|
| **1 · Identificação** | Políticas e estratégia · Stakeholders · Padrões comportamentais · Árvore de problemas · Objetivos e estratégias | Matriz influência × interesse (Mendelow), círculos grupo-alvo ⊂ beneficiários ⊂ stakeholders, pirâmide comportamental, árvores geradas automaticamente, seleção multicritério da estratégia, **geração automática do logframe a partir da árvore** |
| **2 · Formulação (Logic Models)** | Logframe · Modelo lógico · Teoria da Mudança · Pressupostos | Lógicas vertical, horizontal e diagonal; pressupostos operacionais, comportamentais e políticos; fluxograma PCM de avaliação dos pressupostos; conversão de pressupostos em riscos |
| **3 · Planeamento** | Atividades e WBS · PERT/CPM · Gantt e custos · RACI · Riscos · Orçamento · Contingências · Procurement | Assistente para acrescentar atividades; CPM com ES/EF/LS/LF/TF/FF; rede no formato do professor; probabilidade PERT; **Monte Carlo**; **crashing por programação linear**; *what-if*; Gantt com folga, baseline e % concluída; orçamento distribuído no tempo com 6 perfis e curva S; matriz de risco 4×4 |
| **4 · Finanças** | VAL, TIR, MIRR, WACC | WACC (CAPM ou direto), VAL, TIR, MIRR, payback simples e atualizado, índice de rendibilidade, perfil do VAL, *tornado* de sensibilidade, investimento importado do Gantt |
| **5 · M&A** | Indicadores SMART · Baselines/metas/benchmarking · EVM · Qualidade e avaliação | SMART e CREAM, progresso face à meta, metas baseadas em evidência (pares, top performer, tendência), EVM completo (PV, EV, AC, CPI, SPI, EAC, ETC, VAC, TCPI), atributos de qualidade do PCM, matriz de avaliação OCDE-CAD |
| **6 · Relatórios e IA** | Relatório e exportações · Agente IA | Relatório HTML interpretativo; **modelos Excel do professor no formato original**; **modelo alargado** com fórmulas; agente que gera projetos, extrai informação de documentos Word/PDF, revê a coerência e conversa sobre o projeto |

Cada página tem uma **legenda** ("o que é", "como se lê", "fontes") e uma **interpretação automática** dos resultados, baseada em regras, que funciona sem chave de IA. O painel inicial faz uma **verificação de coerência entre módulos**.

**Projetos exemplo:**
- Cooperação para o desenvolvimento: Estatísticas de Comércio, com as árvores do professor
- Educação/TIC
- Saúde
- Tecnologia (ERP)
- Construção
- Indústria aeronáutica (MRO)

A página PERT/CPM tem um interruptor que carrega o **exemplo A–H do professor**: duração 19 e caminho crítico A → B → D → G → H.

---

## 2. Estrutura do projeto

```
pm-studio/
├── app.py                  # entrada: navegação, idioma, guardar
├── core/
│   ├── cpm.py              # CPM, PERT, Monte Carlo, crashing (LP)
│   ├── schedule.py         # calendário, custos no tempo, curva S, EVM, baseline
│   ├── finance.py          # WACC, VAL, TIR, MIRR, payback, sensibilidade
│   ├── analysis.py         # diagramas (Graphviz), pressupostos, stakeholders, riscos, benchmarking
│   ├── interpret.py        # interpretações automáticas + verificação de coerência
│   ├── excel_io.py         # modelos do professor, modelo alargado, importação
│   ├── report.py           # relatório HTML
│   ├── agent.py            # agente IA (Claude API)
│   ├── demos.py            # 6 projetos exemplo
│   ├── db.py               # PostgreSQL / SQLite (SQLAlchemy)
│   ├── model.py            # modelo de dados do projeto
│   ├── help_texts.py       # legendas e bibliografia
│   ├── i18n.py, fmt.py, ui.py, matrix.py
├── views/                  # páginas (identificação, formulação, planeamento, finanças, M&A, relatórios)
├── templates/              # modelos Excel ORIGINAIS do professor (não alterar)
├── tests/test_engines.py   # testes automáticos (pytest)
├── requirements.txt
├── render.yaml             # Blueprint do Render (web service + PostgreSQL)
├── .python-version         # 3.13
├── .streamlit/config.toml
└── .env.example
```

---

## 3. Montagem passo a passo

### Passo 0 — Pré-requisitos (uma vez)
1. **Python 3.12 ou 3.13**: https://www.python.org/downloads/. No Windows, marque *"Add Python to PATH"*.
2. **Git**: https://git-scm.com/downloads.
3. **VS Code** com as extensões *Python* (Microsoft) e *GitHub Pull Requests* (opcional).
4. Contas no **GitHub** (já tem: `JorgeSilva1970`) e no **Render** (https://render.com; pode entrar com a conta GitHub).
5. (Opcional) **Chave da API da Anthropic**, para o agente IA: https://console.anthropic.com → *API Keys*.

### Passo 1 — Abrir no VS Code
1. Descompacte `pm-studio.zip` numa pasta, por exemplo `Documentos/pm-studio`.
2. VS Code → *File → Open Folder…* → escolha a pasta `pm-studio`.
3. Abra o terminal integrado: *Terminal → New Terminal*.

### Passo 2 — Ambiente virtual e dependências
**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
> Se o PowerShell bloquear a ativação, execute uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e repita.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
No VS Code, quando aparecer a pergunta, escolha o interpretador `.venv`. Também pode usar *Ctrl+Shift+P → Python: Select Interpreter*.

### Passo 3 — Configurar a chave da IA (opcional)
Copie `.env.example` para `.env` e preencha:
```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-5-5
```
O ficheiro `.env` está no `.gitignore`, por isso **nunca vai para o GitHub**. Sem chave, a app funciona na mesma; só o agente IA fica desativado.

### Passo 4 — Executar localmente
```bash
streamlit run app.py
```
Abre em http://localhost:8501. Localmente, os projetos ficam em `data/pm_studio.db` (SQLite).

Para correr os testes:
```bash
python -m pytest -q
```
Devem passar 8 testes.

### Passo 5 — Publicar no GitHub
**Opção A (mais simples, no VS Code):**
1. Ícone *Source Control* (barra lateral) → **Publish to GitHub**.
2. Escolha **Public** ou **Private** e o nome `pm-studio`.

**Opção B (terminal):**
1. Crie no GitHub um repositório **vazio** chamado `pm-studio`, sem README.
2. No terminal:
   ```bash
   git init
   git add .
   git commit -m "PM Studio: primeira versão"
   git branch -M main
   git remote add origin https://github.com/JorgeSilva1970/pm-studio.git
   git push -u origin main
   ```

Confirme no GitHub que **não** aparecem as pastas `.venv/` e `data/`, nem o ficheiro `.env`.

### Passo 6 — Render: base de dados PostgreSQL + aplicação

#### Opção A — Blueprint (recomendada: cria tudo de uma vez a partir do `render.yaml`)
1. Render → **New + → Blueprint**.
2. Ligue a conta GitHub, se ainda não estiver ligada, e escolha o repositório `pm-studio`.
3. O Render lê o `render.yaml` e mostra dois recursos:
   - **pm-studio-db**: PostgreSQL free, região Frankfurt
   - **pm-studio**: web service free, região Frankfurt
4. Quando pedir o valor de `ANTHROPIC_API_KEY`, cole a sua chave (ou deixe vazio e acrescente depois).
5. Clique em **Apply**. O Render cria a base de dados e liga-a automaticamente à app através da variável `DATABASE_URL`.
6. Aguarde o build (3–6 minutos) e abra o URL `https://pm-studio-xxxx.onrender.com`.

#### Opção B — Manual (passo a passo no painel)
1. **Criar a base de dados:**
   1. **New + → Postgres**.
   2. Preencha: Name `pm-studio-db`, Database `pm_studio`, User `pm_studio`, Region **Frankfurt (EU Central)**, Plan **Free**.
   3. Clique em **Create Database**.
   4. Quando o estado for *Available*, copie o **Internal Database URL** (secção *Connections*).
2. **Criar o serviço web:**
   1. **New + → Web Service**.
   2. Escolha o repositório `pm-studio`.
   3. Preencha:
      - Name: `pm-studio`
      - Region: **a mesma da base de dados (Frankfurt)**
      - Branch: `main`
      - Runtime: **Python 3**
      - Build Command: `pip install -r requirements.txt`
      - Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
      - Instance Type: **Free**
   4. Em **Environment Variables**, acrescente:

      | Key | Value |
      |---|---|
      | `DATABASE_URL` | *(o Internal Database URL copiado)* |
      | `PYTHON_VERSION` | `3.13.5` |
      | `ANTHROPIC_API_KEY` | *(a sua chave — opcional)* |
      | `ANTHROPIC_MODEL` | `claude-sonnet-5-5` |
   5. Clique em **Create Web Service**.

> A app converte automaticamente o prefixo `postgres://` ou `postgresql://` do Render para o driver `psycopg2`, e cria as tabelas (`projects`, `snapshots`) no primeiro arranque.

### Passo 7 — Verificar
1. Abra a app. Na barra lateral deve aparecer **🗄️ PostgreSQL**; se aparecer *SQLite (local)*, a variável `DATABASE_URL` não está definida.
2. Em **Início → Projetos**, carregue um exemplo e clique em **💾 Guardar**.
3. Recarregue a página: o projeto e o idioma são repostos (o URL contém `?pid=…&lang=…`).
4. Para testar o agente, vá a **Agente IA → Conversar**.

### Passo 8 — Atualizações
Cada `git push` para `main` faz um novo deploy automático no Render:
```bash
git add .
git commit -m "Descrição da alteração"
git push
```

---

## 4. Notas importantes sobre o plano gratuito do Render
- **Web service free:** adormece após 15 minutos sem tráfego; o primeiro acesso seguinte demora cerca de 1 minuto. O disco do serviço é efémero, e é por isso que os projetos ficam no PostgreSQL.
- **PostgreSQL free:**
  - Expira **30 dias após a criação**.
  - Há **14 dias de tolerância** para passar a um plano pago antes de os dados serem apagados.
  - Tem 1 GB, não tem backups e só pode existir uma base de dados gratuita por *workspace*.
- **Para não perder dados**, escolha uma destas opções:
  - Passar a base de dados a um plano pago (ex.: *Basic*), no painel do Render → *pm-studio-db* → *Upgrade*.
  - Exportar regularmente cada projeto em **JSON** (Início → Importar/exportar) e voltar a importá-lo numa nova base de dados.
  - Fazer cópia com `pg_dump`, usando o **External Database URL**: `pg_dump "postgresql://…" > backup.sql`.

---

## 5. Excel — modelos do professor e modelo alargado
- **StakeholderRegister** e **RiskRegister** são exportados a partir dos ficheiros **originais** em `templates/`. A formatação, as listas pendentes, as legendas e as instruções mantêm-se iguais.
  - No RiskRegister, a exposição é uma fórmula que usa as listas do próprio modelo.
  - Ficam respeitados os limites de linhas indicados pelo professor (13 stakeholders e 8 riscos). O excedente segue no modelo alargado.
- O **modelo alargado** tem uma folha por módulo e usa **fórmulas Excel**: tₑ e σ² do PERT, probabilidade NORMDIST, PV acumulado, EVM, exposição ao risco, WACC, VAL, TIR, MIRR e índice de rendibilidade. Inclui ainda gráficos da curva S e da matriz de risco.
- Ambos os formatos podem ser **reimportados** na app (Início → Importar/exportar).

---

## 6. Resolução de problemas

| Sintoma | Causa / solução |
|---|---|
| `ModuleNotFoundError` local | O ambiente virtual não está ativo: ative `.venv` e repita `pip install -r requirements.txt` |
| Build no Render falha numa dependência | Confirme `PYTHON_VERSION=3.13.5` nas variáveis de ambiente |
| Barra lateral mostra *SQLite (local)* no Render | Falta `DATABASE_URL` no serviço web |
| `could not translate host name` | Usou o Internal URL com a app noutra região: ponha os dois serviços na mesma região, ou use o External URL |
| Agente IA desativado | Defina `ANTHROPIC_API_KEY` (Render → *Environment*) e faça *Manual Deploy → Restart* |
| Erro de modelo no agente | Ajuste `ANTHROPIC_MODEL` para um modelo disponível na sua conta (ver https://docs.claude.com) |
| Diagramas não aparecem no relatório HTML | O relatório carrega Plotly e Graphviz (viz.js) por CDN: abra-o com ligação à internet |

---

## 7. Bibliografia
- European Commission – EuropeAid (2004). *Aid Delivery Methods, Vol. 1: Project Cycle Management Guidelines*.
- European Commission – CoEPM² (2016). *The PM² Project Management Methodology Guide – Open Edition*.
- van Es, M., Guijt, I. & Vogel, I. (2015). *Hivos ToC Guidelines – Theory of Change Thinking in Practice*.
- Morra Imas, L. G. & Rist, R. C. (2009). *The Road to Results*. World Bank.
- European Commission – DG INTPA (2025). *Evaluation Handbook – 2025 Edition*.
- PMI (2021). *PMBOK® Guide*, 7.ª ed.
- Materiais da unidade curricular (Policy & Strategy, Stakeholders, Needs Assessment, Time, Risk, Budgeting & Procurement, Data Collection) e Guia de Estudo *Logic Model e Theory of Change*.
