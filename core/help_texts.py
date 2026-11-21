"""Explanatory legends for every module: concept, how to read it, and source (bibliography)."""

SRC = {
    "pcm": "European Commission – EuropeAid (2004). *Aid Delivery Methods, Vol. 1: Project Cycle Management Guidelines*. Brussels.",
    "pm2": "European Commission – CoEPM² (2016). *The PM² Project Management Methodology Guide – Open Edition*. Luxembourg: Publications Office of the EU.",
    "hivos": "van Es, M., Guijt, I. & Vogel, I. (2015). *Hivos ToC Guidelines – Theory of Change Thinking in Practice*. The Hague: Hivos.",
    "r2r": "Morra Imas, L. G. & Rist, R. C. (2009). *The Road to Results: Designing and Conducting Effective Development Evaluations*. Washington DC: World Bank.",
    "eval": "European Commission – DG INTPA (2025). *Evaluation Handbook – 2025 Edition*. Luxembourg: Publications Office of the EU.",
    "pmbok": "Project Management Institute (2021). *A Guide to the Project Management Body of Knowledge (PMBOK® Guide)*, 7th ed.",
    "course": "Materiais da unidade curricular (professor): Policy & Strategy Analysis; Stakeholders Management; Needs Assessment; Time, Risk, Budgeting & Procurement; Data Collection.",
    "guide": "Guia de Estudo: O Modelo Lógico e Teoria da Mudança (vídeos da unidade curricular).",
    "brealey": "Brealey, R., Myers, S. & Allen, F. *Principles of Corporate Finance*. McGraw-Hill.",
    "mon": "Materiais da unidade curricular — Monitorização (módulos 1–16): monitorização de indicadores, marcos e entregáveis, gestão de alterações, revisão de riscos e pressupostos, comunicação com stakeholders, procurement e contratos, plano de comunicação.",
    "evalc": "Materiais da unidade curricular — Avaliação (módulos 1b–19b): finalidades e tipos de avaliação, perguntas e critérios OCDE-CAD, recolha de dados, qualidade do M&A, eficiência e eficácia, sustentabilidade e ODS, auditorias, propriedade dos resultados, lições aprendidas, boas práticas e disseminação.",
    "oecd": "OECD-DAC (2019). *Better Criteria for Better Evaluation: Revised Evaluation Criteria Definitions and Principles for Use*. Paris: OECD.",
    "mendelow": "Mendelow, A. (1991). Stakeholder mapping. *Proceedings of the 2nd International Conference on Information Systems*.",
}

H = {
"home": {
 "pt": ("Este estúdio acompanha todo o **ciclo de gestão de projetos (PCM)**: Programação → Identificação → Formulação → Implementação → Avaliação. "
        "Os módulos estão ligados: problemas → objetivos → logframe → atividades → PERT/CPM → Gantt e custos → riscos → indicadores → EVM → monitorização (marcos, alterações, revisões, tesouraria, contratos, comunicação) → avaliação, encerramento e lições.",
        "Siga o menu de cima para baixo. Cada página tem uma legenda (o que é, como se lê, fonte) e uma interpretação automática dos resultados.",
        ["pcm", "pm2", "course"]),
 "en": ("This studio covers the whole **Project Cycle Management (PCM)**: Programming → Identification → Formulation → Implementation → Evaluation. "
        "Modules are linked: problems → objectives → logframe → activities → PERT/CPM → Gantt & costs → risks → indicators → EVM → monitoring (milestones, changes, reviews, cash, contracts, communication) → evaluation, closure & lessons.",
        "Follow the menu from top to bottom. Every page has a legend (what it is, how to read it, source) and an automatic interpretation of the results.",
        ["pcm", "pm2", "course"])},
"policy": {
 "pt": ("O desenho do projeto é um exercício **top-down**: parte dos objetivos estratégicos do Governo e dos parceiros. O **impacto** do projeto é a sua contribuição para um objetivo estratégico. "
        "Analisa-se o **Contexto** (ambiente social, económico, político, institucional), o **Conteúdo** (objetivos, instrumentos e coerência da política) e as **Consequências** (efeitos pretendidos e não pretendidos, impactos distributivos).",
        "Os indicadores de impacto e as suas metas são os da própria estratégia (o projeto contribui para eles); as fontes de verificação são as dos indicadores estratégicos.",
        ["course", "pcm"]),
 "en": ("Project design is a **top-down** exercise starting from the strategic goals of Government and partners. The project's **impact** is its contribution to one strategic goal. "
        "Analyse the **Context** (social, economic, political, institutional), the **Content** (policy goals, instruments, coherence) and the **Consequences** (intended and unintended effects, distributional impacts).",
        "Impact indicators and targets are those of the strategy itself (the project contributes to them); sources of verification are the same as the strategic indicators'.",
        ["course", "pcm"])},
"stakeholders": {
 "pt": ("A análise de stakeholders combina quatro camadas: **características básicas**; **como os interesses são afetados** (onde há um problema, há quem tire partido dele); **capacidade e motivação para a mudança**; e **ações possíveis** para acomodar interesses e controlar resistências. "
        "Os círculos concêntricos distinguem **grupo-alvo** ⊂ **beneficiários** ⊂ **stakeholders**.",
        "A matriz influência × interesse (Mendelow) indica a estratégia: gerir de perto (alto/alto), manter satisfeito, manter informado ou monitorizar. Os opositores influentes exigem ações específicas.",
        ["course", "pcm", "mendelow"]),
 "en": ("Stakeholder analysis combines four layers: **basic characteristics**; **how interests are affected** (where there is a problem, someone takes advantage of it); **capacity and motivation to change**; and **possible actions** to accommodate interests and control resistance. "
        "Concentric circles distinguish **target group** ⊂ **beneficiaries** ⊂ **stakeholders**.",
        "The influence × interest grid (Mendelow) suggests the strategy: manage closely (high/high), keep satisfied, keep informed or monitor. Influential opponents require specific actions.",
        ["course", "pcm", "mendelow"])},
"behaviour": {
 "pt": ("O comportamento do grupo-alvo perante os outputs determina o sucesso. A pirâmide liga **Outputs → Perceção → Oportunidade → Capacidade → Motivação → Outcomes**: "
        "perceção (positiva/negativa), oportunidade de acesso (género, geografia, estatuto), capacidade para usar os outputs e motivação (religião, crenças, cultura, hábitos).",
        "Pontuações ≤ 2 indicam um **pressuposto comportamental em risco**: acrescente atividades de apoio ou reformule a estratégia. Esta análise é a evidência dos pressupostos comportamentais.",
        ["course"]),
 "en": ("Target-group behaviour towards the outputs drives success. The pyramid links **Outputs → Perception → Opportunity → Ability → Motivation → Outcomes**: "
        "perception (positive/negative), opportunity to access (gender, geography, status), ability to use outputs and motivation (religion, beliefs, culture, habits).",
        "Scores ≤ 2 flag a **behavioural assumption at risk**: add support activities or rethink the strategy. This analysis is the evidence for behavioural assumptions.",
        ["course"])},
"problems": {
 "pt": ("A **árvore de problemas** identifica os aspetos negativos da situação e estabelece relações causa-efeito: o problema central ao centro, as **causas** (raízes) em baixo e os **efeitos** em cima. "
        "Erro comum: confundir um efeito com o problema central. Focar as causas leva a soluções sustentáveis.",
        "Leia de baixo para cima: 'porque existe esta causa, verifica-se o problema, que provoca estes efeitos'. Cada nó liga-se ao nível superior (coluna 'Leva a').",
        ["course", "pcm"]),
 "en": ("The **problem tree** identifies the negative aspects of the situation and establishes cause-effect relations: the core problem in the centre, **causes** (roots) below and **effects** above. "
        "Common mistake: taking an effect for the core problem. Focusing on root causes leads to sustainable solutions.",
        "Read bottom-up: 'because of this cause, the problem occurs, which produces these effects'. Each node links to the level above ('Leads to' column).",
        ["course", "pcm"])},
"objectives": {
 "pt": ("A **árvore de objetivos** descreve a situação futura depois de resolvidos os problemas: as causas transformam-se em **meios** (outputs), o problema central em **outcome** e os efeitos em **fins** (impactos alinhados com a política). "
        "A **análise de estratégias** escolhe que meios ficam dentro do âmbito do projeto, com critérios como relevância, viabilidade técnica, custo-benefício, sustentabilidade e capacidade institucional.",
        "Relações meios-fins: 'se estes meios forem disponibilizados, este fim é alcançado'. A cadeia de resultados que daqui emerge é a espinha dorsal do projeto e o ponto de partida do planeamento.",
        ["course", "pcm"]),
 "en": ("The **objective tree** describes the future situation once problems are solved: causes become **means** (outputs), the core problem becomes the **outcome** and effects become **ends** (impacts aligned with policy). "
        "**Strategy analysis** selects which means fall within the project scope, using criteria such as relevance, technical feasibility, cost-benefit, sustainability and institutional capacity.",
        "Means-ends relations: 'if these means are delivered, this end is achieved'. The resulting results chain is the backbone of the project and the starting point of planning.",
        ["course", "pcm"])},
"logframe": {
 "pt": ("A **Matriz de Enquadramento Lógico (Logframe)** cruza três lógicas: **vertical** (Impacto ← Outcomes ← Outputs ← Atividades ← Recursos), **horizontal** (indicadores, baseline, meta, fontes de verificação) e **diagonal** (pressupostos). "
        "Os outputs estão sob **controlo total** do gestor, os outcomes sob **influência direta** e o impacto sob **influência indireta**.",
        "Leia na diagonal: Atividades + pressupostos operacionais → Outputs; Outputs + pressupostos comportamentais → Outcomes; Outcomes + pressupostos políticos → Impacto. A célula de pressupostos do impacto fica vazia.",
        ["pcm", "guide", "course"]),
 "en": ("The **Logical Framework Matrix (Logframe)** crosses three logics: **vertical** (Impact ← Outcomes ← Outputs ← Activities ← Inputs), **horizontal** (indicators, baseline, target, sources of verification) and **diagonal** (assumptions). "
        "Outputs are under the manager's **full control**, outcomes under **direct influence** and impact under **indirect influence**.",
        "Read diagonally: Activities + operational assumptions → Outputs; Outputs + behavioural assumptions → Outcomes; Outcomes + political assumptions → Impact. The impact-level assumption cell stays empty.",
        ["pcm", "guide", "course"])},
"logic_model": {
 "pt": ("O **Modelo Lógico** representa a cadeia causal: **Inputs (4 Ms: Materiais, Maquinaria, Mão de obra, Money) → Atividades → Outputs → Outcomes → Impacto**. "
        "Atividades de **produção** entregam outputs; atividades de **apoio** (comunicação, M&A, eventos, gestão) garantem a qualidade da gestão.",
        "Avalie cada ligação: Inputs & Outputs → **Eficiência**; Outcomes → **Eficácia**; Impacto → **Sustentabilidade** (mnemónica E-E-S).",
        ["guide", "course"]),
 "en": ("The **Logic Model** shows the causal chain: **Inputs (4 Ms: Materials, Machinery, Manpower, Money) → Activities → Outputs → Outcomes → Impact**. "
        "**Production** activities deliver outputs; **support** activities (communication, M&E, events, management) ensure management quality.",
        "Assess each link: Inputs & Outputs → **Efficiency**; Outcomes → **Effectiveness**; Impact → **Sustainability** (E-E-S).",
        ["guide", "course"])},
"toc": {
 "pt": ("A **Teoria da Mudança (ToC)** explicita *como e porquê* se espera que a mudança aconteça: visão de sucesso, análise de contexto e atores, **caminhos de mudança** (pré-condições), **pressupostos explícitos**, escolhas estratégicas e perguntas de aprendizagem. "
        "Complementa o logframe: é mais flexível e reconhece a complexidade.",
        "Leia os caminhos de baixo para cima; as setas são hipóteses causais e as notas amarelas os pressupostos que as sustentam. Reveja a ToC periodicamente (ciclo de aprendizagem).",
        ["hivos", "guide"]),
 "en": ("The **Theory of Change (ToC)** makes explicit *how and why* change is expected: vision of success, context and actor analysis, **pathways of change** (preconditions), **explicit assumptions**, strategic choices and learning questions. "
        "It complements the logframe: more flexible and complexity-aware.",
        "Read the pathways bottom-up; arrows are causal hypotheses and yellow notes the assumptions behind them. Revisit the ToC periodically (learning loop).",
        ["hivos", "guide"])},
"assumptions": {
 "pt": ("Os **pressupostos** são afirmações **positivas** sobre fatores externos necessários: **OUTPUTS = ATIVIDADES + PRESSUPOSTOS OPERACIONAIS; OUTCOMES = OUTPUTS + COMPORTAMENTAIS; IMPACTOS = OUTCOMES + POLÍTICOS**. "
        "Só são válidos se suportados por **evidência**: políticos ← análise de políticas; comportamentais ← padrões do grupo-alvo; operacionais ← lições de projetos anteriores.",
        "Fluxograma PCM: É importante? → Vai verificar-se? Quase certo → não incluir; Possivelmente → incluir; Improvável → redesenhar o projeto ou, se impossível, é um **pressuposto 'killer'**. Pressupostos não confirmados convertem-se em riscos (formulação negativa).",
        ["course", "pcm", "guide"]),
 "en": ("**Assumptions** are **positive** statements about necessary external factors: **OUTPUTS = ACTIVITIES + OPERATIONAL ASSUMPTIONS; OUTCOMES = OUTPUTS + BEHAVIOURAL; IMPACTS = OUTCOMES + POLITICAL**. "
        "They are only valid if backed by **evidence**: political ← policy analysis; behavioural ← target-group patterns; operational ← lessons from previous projects.",
        "PCM flowchart: Important? → Will it hold? Almost certainly → leave out; Possibly → include; Unlikely → redesign or, if impossible, it is a **killer assumption**. Unconfirmed assumptions become risks (negative phrasing).",
        ["course", "pcm", "guide"])},
"activities": {
 "pt": ("As atividades combinam-se para entregar os outputs. **Atividades de produção** agrupam-se por output; **atividades de apoio** garantem a qualidade da gestão (comunicação, M&A, eventos, gestão geral, prevenção de risco). "
        "Decomponha cada atividade principal em tarefas, defina a sequência e as dependências (predecessoras).",
        "Use IDs curtos (A1, A2…) e indique as predecessoras separadas por vírgulas. O 'Assistente' permite gerar atividades a partir dos outputs do logframe ou acrescentar várias de uma só vez.",
        ["course", "pcm", "pm2"]),
 "en": ("Activities combine to deliver the outputs. **Production activities** are grouped by output; **support activities** ensure management quality (communication, M&E, events, overall management, risk prevention). "
        "Break each main activity into tasks, define sequence and dependencies (predecessors).",
        "Use short IDs (A1, A2…) and list predecessors separated by commas. The 'Assistant' can generate activities from the logframe outputs or add several at once.",
        ["course", "pcm", "pm2"])},
"pert": {
 "pt": ("**CPM**: passagem para a frente (início/fim mais cedo, ES/EF) e para trás (início/fim mais tarde, LS/LF); a **folga total** TF = LS − ES e o **caminho crítico** é a sequência de atividades com folga zero. "
        "**PERT**: três estimativas (otimista *a*, mais provável *m*, pessimista *b*); duração esperada tₑ = (a + 4m + b)/6 e variância σ² = ((b − a)/6)². A **simulação de Monte Carlo** (Beta-PERT) mede a probabilidade de cumprir prazos e o índice de criticidade. O **crashing** reduz a duração ao menor custo (programação linear).",
        "Em cada caixa: em cima ES | ID | EF; em baixo LS | D | LF. Vermelho = crítico. Probabilidade de cumprir T: P(Z ≤ (T − μ)/σ). Folga livre (FF) = quanto a atividade pode atrasar sem atrasar a sucessora. "
        "Roxo = **esforço contínuo (LOE)**: gestão e M&A acompanham o trabalho de produção (duração derivada) e nunca definem o caminho crítico — senão as folgas das atividades de produção seriam fictícias.",
        ["course", "pmbok", "pm2"]),
 "en": ("**CPM**: forward pass (early start/finish, ES/EF) and backward pass (late start/finish, LS/LF); **total float** TF = LS − ES and the **critical path** is the sequence of zero-float activities. "
        "**PERT**: three estimates (optimistic *a*, most likely *m*, pessimistic *b*); expected duration tₑ = (a + 4m + b)/6, variance σ² = ((b − a)/6)². **Monte Carlo simulation** (Beta-PERT) gives deadline probabilities and criticality indices. **Crashing** shortens the project at minimum cost (linear programming).",
        "In each box: top ES | ID | EF; bottom LS | D | LF. Red = critical. Probability of meeting T: P(Z ≤ (T − μ)/σ). Free float (FF) = how long an activity can slip without delaying its successor. "
        "Purple = **level of effort (LOE)**: management and M&E follow the production work (derived duration) and never define the critical path — otherwise production floats would be fictitious.",
        ["course", "pmbok", "pm2"])},
"gantt": {
 "pt": ("O **diagrama de Gantt** mostra as atividades no calendário, calculado a partir do PERT/CPM. Com o **orçamento distribuído no tempo** obtém-se o custo por período e o acumulado (**curva S**), base do mapa de fluxos de caixa (cash flow).",
        "Barras vermelhas = caminho crítico; roxas = esforço contínuo (LOE, gestão e M&A ao longo do projeto); extensão cinzenta = folga total; losangos = marcos. A linha de base (baseline) permite comparar o planeado inicial com o atual.",
        ["course", "pcm", "pm2"]),
 "en": ("The **Gantt chart** shows activities on the calendar, computed from PERT/CPM. The **time-phased budget** gives cost per period and cumulative cost (**S-curve**), the basis for the project cash-flow map.",
        "Red bars = critical path; purple = level of effort (LOE, management and M&E across the project); grey extension = total float; diamonds = milestones. The baseline lets you compare the original plan with the current one.",
        ["course", "pcm", "pm2"])},
"raci": {
 "pt": ("A **matriz de responsabilidades (RAM/RASCI)** do PM² atribui papéis por atividade: **R**esponsável (executa), **A**utoridade/Aprova (presta contas — só um por atividade), **S**uporte, **C**onsultado, **I**nformado.",
        "Cada atividade deve ter exatamente um 'A' e pelo menos um 'R'. Pessoas com demasiados 'R' em atividades simultâneas indicam sobrecarga.",
        ["pm2"]),
 "en": ("PM²'s **responsibility assignment matrix (RAM/RASCI)** assigns roles per activity: **R**esponsible (does the work), **A**ccountable (approves — only one per activity), **S**upport, **C**onsulted, **I**nformed.",
        "Each activity needs exactly one 'A' and at least one 'R'. People with too many concurrent 'R's are overloaded.",
        ["pm2"])},
"risks": {
 "pt": ("Risco é a probabilidade de um evento afetar negativamente os objetivos; formula-se **pela negativa** (o pressuposto pela positiva). A estratégia cobre: natureza do risco, impacto adverso, nível, estratégia de gestão e responsável. "
        "**Exposição = Probabilidade × Impacto** (escala 1–4 → índice 1–16), comparada com a exposição-alvo aceitável.",
        "A probabilidade depende da quantidade e qualidade da evidência que suporta o pressuposto; o impacto depende do nível da lógica vertical afetado (outcomes/impactos = severo). Atividades preventivas entram no plano como atividades de apoio.",
        ["course", "pcm", "pm2"]),
 "en": ("Risk is the probability that an event adversely affects the objectives; it is phrased **negatively** (assumptions positively). The strategy covers: nature of the risk, adverse impact, level, management strategy and who is in charge. "
        "**Exposure = Likelihood × Impact** (1–4 scale → index 1–16), compared with the acceptable target exposure.",
        "Likelihood depends on the quantity/quality of evidence behind the assumption; impact depends on the vertical-logic level affected (outcomes/impacts = severe). Preventive activities enter the plan as support activities.",
        ["course", "pcm", "pm2"])},
"budget": {
 "pt": ("O orçamento por tipo de atividade parte das atividades do logframe: identificam-se os recursos (honorários, despesas diretas, equipamentos, materiais), agregam-se em **categorias de custo**, definem-se custos por **fase** (arranque, implementação, encerramento) e soma-se o custo final. "
        "O **mapa de cash flow** monetiza as quantidades com custos unitários e distribui-as no tempo, evitando atrasos por falta de liquidez.",
        "Se uma atividade tiver linhas de orçamento, o seu custo (BAC) é a soma dessas linhas; caso contrário usa-se o custo indicado na tabela de atividades.",
        ["course", "pcm"]),
 "en": ("The activity-type budget starts from the logframe activities: identify resources (fees, direct costs, equipment, materials), aggregate them into **cost categories**, define costs per **phase** (inception, implementation, completion) and sum up the final cost. "
        "The **cash-flow map** monetises quantities with unit costs and spreads them over time, avoiding delays due to lack of liquidity.",
        "If an activity has budget lines, its cost (BAC) is their sum; otherwise the cost in the activities table is used.",
        ["course", "pcm"])},
"contingency": {
 "pt": ("O orçamento de contingência é uma **reserva** para eventos inesperados: identificar riscos, avaliar o impacto, **quantificar** o montante, **alocá-lo** às áreas mais vulneráveis e **documentá-lo** no cash flow. "
        "Pressupostos não confirmados → riscos → atividades de mitigação → estimativas de custo → contingências.",
        "Dois métodos: percentagem do BAC, ou soma das contingências estimadas por risco. Não substitui a gestão e mitigação de riscos.",
        ["course"]),
 "en": ("The contingency budget is a **buffer** for unexpected events: identify risks, assess impact, **quantify** the amount, **allocate** it to the most vulnerable areas and **document** it in the cash flow. "
        "Unconfirmed assumptions → risks → mitigation activities → cost estimates → contingencies.",
        "Two methods: a percentage of BAC, or the sum of per-risk contingency estimates. It does not replace risk management and mitigation.",
        ["course"])},
"procurement": {
 "pt": ("O **plano de procurement** define como o projeto adquire bens, serviços e empreitadas: âmbito, stakeholders, estudo de mercado, riscos, **estratégia** (concurso, RFP, RFQ, ajuste direto, acordo-quadro), documentos, orçamento, calendário, equipa e critérios de seleção.",
        "Cada aquisição deve estar ligada a uma atividade e ao seu orçamento; o calendário deve anteceder o início da atividade.",
        ["course", "pm2"]),
 "en": ("The **procurement plan** sets how the project acquires goods, services and works: scope, stakeholders, market research, risks, **strategy** (competitive bidding, RFP, RFQ, sole sourcing, framework agreement), documents, budget, schedule, team and selection criteria.",
        "Each purchase should link to an activity and its budget; its date must precede the activity start.",
        ["course", "pm2"])},
"finance": {
 "pt": ("**WACC** = E/V·Ke + D/V·Kd·(1 − t), com Ke pelo CAPM (rf + β·prémio de mercado). **VAL** (NPV) = Σ CFₜ/(1 + r)ᵗ; **TIR** (IRR) é a taxa que anula o VAL; a **TIR modificada** (MIRR) assume reinvestimento dos fluxos positivos a uma taxa realista e financiamento dos negativos à taxa de financiamento. Inclui payback, índice de rendibilidade e análise de sensibilidade.",
        "Regra: VAL > 0 e TIR/MIRR > WACC → o projeto cria valor. Quando há várias mudanças de sinal nos fluxos a TIR pode não ser única: prefira a MIRR. O investimento pode ser importado do cronograma de custos (Gantt).",
        ["brealey", "pcm"]),
 "en": ("**WACC** = E/V·Ke + D/V·Kd·(1 − t), with Ke from CAPM (rf + β·market premium). **NPV** = Σ CFₜ/(1 + r)ᵗ; **IRR** is the rate that makes NPV zero; **MIRR** assumes positive flows are reinvested at a realistic rate and negative ones financed at the finance rate. Includes payback, profitability index and sensitivity analysis.",
        "Rule: NPV > 0 and IRR/MIRR > WACC → the project creates value. With several sign changes the IRR may not be unique: prefer the MIRR. Investment can be imported from the cost schedule (Gantt).",
        ["brealey", "pcm"])},
"indicators": {
 "pt": ("Indicadores quantificam o que a lógica vertical qualifica: **input** (recursos mobilizados), **output** (produtos disponibilizados), **resultado/outcome** (efeitos imediatos e intermédios) e **impacto** (efeitos de longo prazo). "
        "Devem ser **SMART** (Specific, Measurable, Available at reasonable cost, Relevant, Timely) e **CREAM** (Clear, Relevant, Economic, Adequate, Monitorable), formulados de forma neutra.",
        "Eficiência ← indicadores input-output; Eficácia ← outcome; Impacto e Sustentabilidade ← impacto; Relevância ← alinhamento com objetivos estratégicos. Não se definem indicadores para medir atividades.",
        ["course", "guide", "r2r"]),
 "en": ("Indicators quantify what the vertical logic qualifies: **input** (resources mobilised), **output** (products delivered), **result/outcome** (immediate and intermediate effects) and **impact** (long-term effects). "
        "They must be **SMART** (Specific, Measurable, Available at reasonable cost, Relevant, Timely) and **CREAM** (Clear, Relevant, Economic, Adequate, Monitorable), phrased neutrally.",
        "Efficiency ← input-output indicators; Effectiveness ← outcome; Impact & Sustainability ← impact; Relevance ← alignment with strategic goals. Activities are not measured by indicators.",
        ["course", "guide", "r2r"])},
"benchmark": {
 "pt": ("**Baseline** = valor do indicador antes da implementação (atualizar no arranque). **Meta** = valor esperado no fim; a diferença meta − baseline é a mudança que o projeto entrega (value for money). "
        "As metas devem ser **baseadas em evidência**: benchmarking com pares, identificação do melhor desempenho (top performer) e séries temporais para estimar o potencial de crescimento realista.",
        "Meta acima do top performer → pouco realista; meta abaixo da tendência → pouco ambiciosa. Um indicador sem baseline não pode ter meta e não deve integrar o modelo lógico.",
        ["course", "r2r"]),
 "en": ("**Baseline** = indicator value before implementation (update at start). **Target** = expected value at the end; target − baseline is the change the project delivers (value for money). "
        "Targets must be **evidence-based**: peer benchmarking, identifying the top performer and time series to estimate realistic growth potential.",
        "Target above the top performer → unrealistic; target below the trend → unambitious. An indicator without a baseline cannot have a target and should not be in the logic model.",
        ["course", "r2r"])},
"evm": {
 "pt": ("**Earned Value Management**: PV (valor planeado), EV (valor ganho = % concluída × orçamento), AC (custo real). CV = EV − AC; SV = EV − PV; CPI = EV/AC; SPI = EV/PV; EAC = BAC/CPI; ETC = EAC − AC; VAC = BAC − EAC; TCPI = (BAC − EV)/(BAC − AC).",
        "CPI ou SPI < 1 = desempenho desfavorável. As três curvas S (PV, EV, AC) mostram a evolução: EV abaixo de PV = atraso; AC acima de EV = derrapagem de custos.",
        ["pmbok", "pm2"]),
 "en": ("**Earned Value Management**: PV (planned value), EV (earned value = % complete × budget), AC (actual cost). CV = EV − AC; SV = EV − PV; CPI = EV/AC; SPI = EV/PV; EAC = BAC/CPI; ETC = EAC − AC; VAC = BAC − EAC; TCPI = (BAC − EV)/(BAC − AC).",
        "CPI or SPI < 1 = unfavourable performance. The three S-curves (PV, EV, AC) show the trend: EV below PV = delay; AC above EV = cost overrun.",
        ["pmbok", "pm2"])},
"quality": {
 "pt": ("O PCM é um ciclo de decisão (PDCA). As decisões seguem três **atributos de qualidade**: **Relevância** (resposta a necessidades prioritárias e às políticas), **Viabilidade** (soluções exequíveis e sustentáveis) e **Eficácia** (implementação orientada para os outcomes). "
        "A avaliação usa os critérios OCDE-CAD: relevância, coerência, eficácia, eficiência, impacto e sustentabilidade.",
        "Responda Sim / Parcial / Não; a pontuação de cada atributo identifica onde reforçar o desenho. A matriz de avaliação liga critérios → perguntas → critérios de juízo → indicadores → fontes.",
        ["pcm", "eval", "r2r"]),
 "en": ("PCM is a decision cycle (PDCA). Decisions follow three **quality attributes**: **Relevance** (meets priority needs and policies), **Feasibility** (workable, sustainable solutions) and **Effectiveness** (implementation geared to outcomes). "
        "Evaluation uses the OECD-DAC criteria: relevance, coherence, effectiveness, efficiency, impact and sustainability.",
        "Answer Yes / Partial / No; each attribute's score shows where to strengthen the design. The evaluation matrix links criteria → questions → judgement criteria → indicators → sources.",
        ["pcm", "eval", "r2r"])},
"report": {
 "pt": ("O relatório reúne todos os módulos com as interpretações automáticas e, opcionalmente, uma síntese escrita pelo agente IA. As exportações Excel incluem os **modelos do professor** (formato original) e um **modelo alargado**.",
        "Abra o relatório HTML no navegador e use 'Imprimir → Guardar como PDF' para obter um PDF.",
        ["pcm", "pm2"]),
 "en": ("The report gathers every module with the automatic interpretations and, optionally, an AI-written synthesis. Excel exports include the **professor's templates** (original format) and an **extended template**.",
        "Open the HTML report in your browser and use 'Print → Save as PDF' to get a PDF.",
        ["pcm", "pm2"])},
"agent": {
 "pt": ("O **agente generativo** (Claude, da Anthropic) conhece a metodologia PCM/PM²/ToC e o conteúdo do projeto aberto. Pode gerar um rascunho completo a partir de uma descrição, extrair informação de documentos Word, sugerir indicadores SMART, rever a coerência lógica e escrever relatórios interpretativos.",
        "As propostas do agente são sempre rascunhos: reveja-as antes de as aplicar ao projeto. Requer a variável de ambiente ANTHROPIC_API_KEY.",
        ["pcm", "hivos"]),
 "en": ("The **generative agent** (Claude, by Anthropic) knows the PCM/PM²/ToC methodology and the content of the open project. It can draft a whole project from a description, extract information from Word documents, suggest SMART indicators, review logical coherence and write interpretive reports.",
        "Agent proposals are drafts: review them before applying them to the project. Requires the ANTHROPIC_API_KEY environment variable.",
        ["pcm", "hivos"])},
"wbs": {
 "pt": ("A **WBS / EAP** (Work Breakdown Structure, Estrutura Analítica do Projeto ou Estrutura de Decomposição do Trabalho) decompõe hierarquicamente **todo o âmbito** do projeto em entregáveis cada vez mais pequenos até aos **pacotes de trabalho** — o nível onde se estima custo e prazo, se atribui um responsável e se verifica a aceitação. As atividades do cronograma ligam-se aos pacotes; as **contas de controlo** agregam pacotes para medir o desempenho (EVM). O **dicionário da WBS** descreve cada pacote.",
        "Código 1.2.3 = posição na hierarquia. Custos, datas, % concluída e EVM sobem automaticamente das atividades para os pacotes e destes para os níveis superiores (sem dupla contagem). Regra dos 100%: todo o trabalho está na WBS e cada nível soma 100% do pai. Regra 8/80 (8 a 80 horas por pacote) ou, em projetos longos, regra do período de reporte. Por omissão a WBS é **orientada a entregáveis e ligada aos outputs do quadro lógico** (coerência PCM); em alternativa, por **fases do ciclo de vida**. Um CPI/SPI < 0,95 num pacote mostra **onde** está o desvio.",
        ["pmbok", "pm2", "pcm", "course"]),
 "en": ("The **WBS** (Work Breakdown Structure) hierarchically decomposes the **entire scope** of the project into ever smaller deliverables down to **work packages** — the level where cost and duration are estimated, an owner is assigned and acceptance is verified. Schedule activities are linked to packages; **control accounts** group packages to measure performance (EVM). The **WBS dictionary** describes each package.",
        "Code 1.2.3 = position in the hierarchy. Costs, dates, % complete and EVM roll up automatically from activities to packages and on to higher levels (no double counting). 100% rule: all work is in the WBS and each level adds up to 100% of its parent. 8/80 rule (8 to 80 hours per package) or, in long projects, the reporting-period rule. By default the WBS is **deliverable-oriented and linked to the logframe outputs** (PCM coherence); alternatively, by **life-cycle phases**. A CPI/SPI < 0.95 in a package shows **where** the variance is.",
        ["pmbok", "pm2", "pcm", "course"])},
"monitoring": {
 "pt": ("A **monitorização** é a recolha sistemática e contínua de dados para verificar se o projeto está no caminho certo: compara o **valor medido** de cada indicador com a **trajetória** entre a baseline e a meta, e verifica os **marcos** (eventos-chave com entregável aceite).",
        "🟢 no bom caminho (≥95% do esperado), 🟡 atenção (75–95%), 🔴 fora da trajetória (<75%). Um marco só conta quando o entregável foi aceite formalmente; os desvios exigem causa e ação corretiva. As metas não se alteram sem pedido de alteração aprovado.",
        ["mon", "pcm", "r2r"]),
 "en": ("**Monitoring** is the systematic, continuous collection of data to check whether the project is on track: it compares the **measured value** of each indicator with the **trajectory** from baseline to target, and checks **milestones** (key events with an accepted deliverable).",
        "🟢 on track (≥95% of expected), 🟡 watch (75–95%), 🔴 off track (<75%). A milestone only counts once its deliverable is formally accepted; deviations need a cause and a corrective action. Targets are not changed without an approved change request.",
        ["mon", "pcm", "r2r"])},
"changes": {
 "pt": ("O **controlo de alterações** regista todas as mudanças a inputs, atividades, outputs, metas, orçamento e prazo, com justificação (necessidade), impacto em prazo/custo/qualidade e decisão. A monitorização das **necessidades** confirma se o problema continua válido.",
        "Regra de ouro: alterações **táticas** (meios) são decididas pela gestão; alterações ao **outcome ou impacto** mudam o propósito — já não é o mesmo projeto: decidir entre encerrar e formular um novo.",
        ["mon", "pm2", "pcm"]),
 "en": ("**Change control** logs every change to inputs, activities, outputs, targets, budget and schedule, with justification (need), impact on time/cost/quality and decision. **Needs** monitoring confirms whether the problem is still valid.",
        "Golden rule: **tactical** changes (means) are decided by management; changes to the **outcome or impact** change the purpose — it is no longer the same project: decide between closing and formulating a new one.",
        ["mon", "pm2", "pcm"])},
"risk_review": {
 "pt": ("O registo de riscos e os pressupostos são **documentos vivos**: em cada revisão reavalia-se a probabilidade e o impacto, regista-se se o risco se materializou (incidente, atraso, custo) e se os pressupostos se confirmam. A **reserva de contingência** cobre riscos identificados; a **reserva de gestão** cobre os desconhecidos.",
        "Compare a exposição inicial com a atual: se desce, a mitigação é eficaz; se sobe, escale. Compare o consumo da contingência com o progresso físico (EV/BAC). Pressupostos não confirmados que afetam a relevância ou a viabilidade obrigam a rever a lógica de intervenção.",
        ["mon", "course", "pmbok"]),
 "en": ("The risk register and assumptions are **living documents**: each review reassesses likelihood and impact, records whether the risk materialised (incident, delay, cost) and whether assumptions hold. The **contingency reserve** covers identified risks; the **management reserve** covers unknown unknowns.",
        "Compare initial with current exposure: falling means mitigation works; rising means escalate. Compare contingency burn with physical progress (EV/BAC). Unconfirmed assumptions affecting relevance or feasibility require revisiting the intervention logic.",
        ["mon", "course", "pmbok"])},
"engagement": {
 "pt": ("A comunicação com os stakeholders durante a implementação usa ferramentas de envolvimento (intermediários, partilha de informação, interação repetida, representantes, técnicas de nivelamento, eventos separados, capacitação…) e mecanismos de **feedback** (inquéritos, grupos focais, visitas, caixas de sugestões).",
        "Cada stakeholder de alta influência deve ter uma ação de envolvimento. O feedback só é útil se o ciclo fechar: registar a resposta/ação e comunicá-la. Satisfação média < 3 num grupo indica necessidade de rever a estratégia.",
        ["mon", "course", "mendelow"]),
 "en": ("Stakeholder communication during implementation uses engagement tools (intermediaries, information sharing, repeated interaction, representatives, levelling techniques, separate events, capacity building…) and **feedback** mechanisms (surveys, focus groups, visits, suggestion boxes).",
        "Every high-influence stakeholder should have an engagement action. Feedback is only useful if the loop is closed: record the response/action and communicate it. Average satisfaction < 3 in a group signals the strategy needs revisiting.",
        ["mon", "course", "mendelow"])},
"cashflow": {
 "pt": ("A **tesouraria** compara as entradas de financiamento (tranches previstas e recebidas) com as necessidades acumuladas do projeto (PV acumulado da curva S) e com o custo real (AC).",
        "Se o financiamento acumulado ficar abaixo do PV acumulado há um **défice de liquidez** — uma das causas mais frequentes de atraso. Antecipe tranches, negocie adiantamentos ou reprograme atividades com folga.",
        ["mon", "course", "pm2"]),
 "en": ("**Cash management** compares funding inflows (planned and received tranches) with the project's cumulative needs (cumulative PV from the S-curve) and actual cost (AC).",
        "If cumulative funding falls below cumulative PV there is a **liquidity gap** — one of the most frequent causes of delay. Bring tranches forward, negotiate advances or reschedule activities with float.",
        ["mon", "course", "pm2"])},
"tenders": {
 "pt": ("O ciclo de **concurso** tem 17 etapas (da identificação da necessidade ao encerramento e avaliação). O **tipo de contrato** depende da certeza do âmbito: preço fixo quando o âmbito é claro (risco no fornecedor); custos reembolsáveis ou T&M quando é incerto (risco no comprador); preço unitário, FPIF, GMP, IDIQ ou acordo-quadro nos casos intermédios.",
        "A grelha de avaliação combina pontuação técnica e financeira: Total = w × Técnica + (1 − w) × 100 × Preço mínimo / Preço. O encerramento do contrato segue 15 passos (verificação, aceitação, liquidação, libertação de garantias, arquivo, lições…).",
        ["mon", "course", "pmbok"]),
 "en": ("The **tender** cycle has 17 stages (from identifying the need to closure and evaluation). The **contract type** depends on scope certainty: fixed price when scope is clear (risk on the seller); cost reimbursement or T&M when uncertain (risk on the buyer); unit price, FPIF, GMP, IDIQ or framework agreements in between.",
        "The evaluation grid combines technical and financial scores: Total = w × Technical + (1 − w) × 100 × Lowest price / Price. Contract closure follows 15 steps (verification, acceptance, settlement, release of bonds, archiving, lessons…).",
        ["mon", "course", "pmbok"])},
"comm": {
 "pt": ("O **plano de comunicação** define, para cada audiência, o objetivo, a mensagem-chave, a ferramenta, a frequência, o orçamento e o indicador. As audiências organizam-se em **três círculos**: 1.º stakeholders locais e multiplicadores; 2.º interessados sem relação estabelecida; 3.º público em geral.",
        "Comece pelo 1.º círculo (apropriação). Cada ação deve estar ligada a uma atividade de apoio de comunicação (para ter custo no orçamento) e ter indicador e meta de alcance.",
        ["mon", "pcm"]),
 "en": ("The **communication plan** defines, for each audience, the objective, key message, tool, frequency, budget and indicator. Audiences are organised in **three circles**: 1st local stakeholders and multipliers; 2nd interested parties without an established relationship; 3rd the general public.",
        "Start with the 1st circle (ownership). Every action should be linked to a communication support activity (so it is costed in the budget) and have an indicator and reach target.",
        ["mon", "pcm"])},
"progress_report": {
 "pt": ("O **relatório de progresso** junta num só documento o estado dos indicadores, marcos, EVM (custo e prazo), riscos e pressupostos, alterações, tesouraria e feedback, adaptado à audiência (financiador, gestão, comunidade).",
        "Um bom relatório responde a: o que foi feito, o que foi alcançado face às metas, o que correu mal e porquê, o que vamos fazer (ações corretivas) e que decisões são necessárias.",
        ["mon", "pm2", "pcm"]),
 "en": ("The **progress report** brings together indicators, milestones, EVM (cost and time), risks and assumptions, changes, cash and feedback, tailored to the audience (donor, management, community).",
        "A good report answers: what was done, what was achieved against targets, what went wrong and why, what we will do (corrective actions) and which decisions are needed.",
        ["mon", "pm2", "pcm"])},
"eval_design": {
 "pt": ("A **avaliação** julga o valor do projeto. Finalidades: **estratégia** (relevância), **operações** (eficácia, eficiência) e **aprendizagem** (lições). Tipos: **formativa** (durante, para melhorar), **sumativa** (no fim, para prestar contas) e **prospetiva** (ex-ante). As perguntas são **descritivas** (o que aconteceu?), **normativas** (face a um padrão/meta) ou de **causa-efeito** (o projeto causou a mudança?).",
        "Cada pergunta da matriz precisa de critério de juízo, indicador, fonte, ferramentas de recolha (inquérito, entrevista, grupo focal, observação, análise documental…) e tipo de dados. A lista de qualidade do M&A (10 elementos) e o peso do M&A no orçamento (referência 5–10%) avaliam o próprio sistema de M&A.",
        ["evalc", "eval", "r2r", "oecd"]),
 "en": ("**Evaluation** judges the worth of the project. Purposes: **strategy** (relevance), **operations** (effectiveness, efficiency) and **learning** (lessons). Types: **formative** (during, to improve), **summative** (at the end, for accountability) and **prospective** (ex-ante). Questions are **descriptive** (what happened?), **normative** (against a standard/target) or **cause-effect** (did the project cause the change?).",
        "Each matrix question needs a judgement criterion, indicator, source, data collection tools (survey, interview, focus group, observation, document review…) and data type. The 10-item M&E quality checklist and M&E share of budget (reference 5–10%) assess the M&E system itself.",
        ["evalc", "eval", "r2r", "oecd"])},
"results_eval": {
 "pt": ("**Eficiência** = relação entre recursos e resultados (CPI, SPI, marcos a tempo, variação orçamental); **eficácia** = grau de alcance das metas dos outcomes; **sustentabilidade** = continuidade dos benefícios após o projeto, em cinco pilares (económico, social, ambiental, institucional, tecnológico) e contributo para os ODS. A análise **ex-post dos riscos** compara a exposição inicial com a final e o custo dos riscos materializados com a contingência.",
        "Pilares com pontuação < 3 exigem estratégia de saída. Riscos materializados acima da contingência alocada indicam subestimação no planeamento — uma lição a registar.",
        ["evalc", "oecd", "eval"]),
 "en": ("**Efficiency** = relation between resources and results (CPI, SPI, milestones on time, budget variance); **effectiveness** = extent to which outcome targets are achieved; **sustainability** = continuity of benefits after the project, across five pillars (economic, social, environmental, institutional, technological) and contribution to the SDGs. **Ex-post risk** analysis compares initial and final exposure and the cost of materialised risks with contingency.",
        "Pillars scoring < 3 need an exit strategy. Materialised risks above allocated contingency indicate underestimation in planning — a lesson to record.",
        ["evalc", "oecd", "eval"])},
"closure": {
 "pt": ("O **encerramento** inclui o fecho dos contratos (15 passos), as **auditorias** (processo, produto, conformidade, financeira) com constatações, recomendações e ações corretivas, e a **propriedade dos resultados** (tipo de propriedade intelectual, regime exclusivo/partilhado/conjunto, direitos de publicação, acordo).",
        "Não encerre com auditorias por resolver nem com resultados partilhados sem acordo escrito sobre uso e publicação.",
        ["evalc", "pm2", "pmbok"]),
 "en": ("**Closure** includes contract closeout (15 steps), **audits** (process, product, compliance, financial) with findings, recommendations and corrective actions, and **ownership of results** (IP type, exclusive/shared/joint regime, publication rights, agreement).",
        "Do not close with unresolved audit findings or shared results without a written agreement on use and publication.",
        ["evalc", "pm2", "pmbok"])},
"lessons": {
 "pt": ("As **lições aprendidas** classificam-se em 8 categorias (política, técnica, cooperação, desenho e substância, financeira, participação, governação, monitorização). As **boas práticas** são práticas validadas, eficazes e replicáveis. A **disseminação** leva os resultados às audiências certas pelos canais adequados (relatórios, workshops, publicações, policy briefs, redes sociais…).",
        "Uma lição só é útil se for transferível: evidência (o que aconteceu) + recomendação acionável. Compare o alcance real com a meta de cada ação de disseminação.",
        ["evalc", "pcm", "eval"]),
 "en": ("**Lessons learned** are classified in 8 categories (political, technical, cooperation, design and substance, financial, participation, governance, monitoring). **Best practices** are validated, effective, replicable practices. **Dissemination** takes results to the right audiences through suitable channels (reports, workshops, publications, policy briefs, social media…).",
        "A lesson is only useful if it is transferable: evidence (what happened) + an actionable recommendation. Compare actual with target reach for each dissemination action.",
        ["evalc", "pcm", "eval"])},
}


# =============================================================================== WBS / EAP glossary (single source)
# Used by the app (tooltips, "how is it calculated?" panels, glossary tab), the HTML report and the Excel comments.
# key → {"pt": (name, formula, meaning), "en": (...), "src": [...]}
WBS_GLOSSARY = {
    "elements": {"pt": ("Elementos", "N.º de linhas da WBS com código (excluindo o projeto, nível 0)", "Tamanho da estrutura. Cada elemento é um entregável, fase, conta de controlo ou pacote de trabalho."),
                 "en": ("Elements", "No. of WBS rows with a code (excluding the project, level 0)", "Size of the structure. Each element is a deliverable, phase, control account or work package."), "src": ["pmbok"]},
    "level": {"pt": ("Nível", "Nível = n.º de pontos do código + 1 (1 → nível 1; 1.2 → nível 2; 1.2.3 → nível 3)", "Posição na hierarquia. O elemento-pai de 1.2.3 é 1.2; o projeto é o nível 0."),
              "en": ("Level", "Level = no. of dots in the code + 1 (1 → level 1; 1.2 → level 2; 1.2.3 → level 3)", "Position in the hierarchy. The parent of 1.2.3 is 1.2; the project is level 0."), "src": ["pmbok"]},
    "work_package": {"pt": ("Pacote de trabalho", "Elemento sem filhos (folha da árvore)", "Nível mais baixo da WBS: é aqui que se ligam as atividades, se estima custo e prazo, se atribui um responsável e se verifica a aceitação."),
                     "en": ("Work package", "Element without children (leaf of the tree)", "Lowest WBS level: activities are attached here, cost and time are estimated, an owner is assigned and acceptance is verified."), "src": ["pmbok", "pm2"]},
    "linked": {"pt": ("Atividades ligadas", "N.º de atividades cujo código WBS é um pacote de trabalho existente ÷ n.º total de atividades", "Mede a cobertura da WBS sobre o cronograma. Tem de ser n/n para cumprir a regra dos 100%."),
               "en": ("Linked activities", "No. of activities whose WBS code is an existing work package ÷ total no. of activities", "Measures how much of the schedule the WBS covers. Must be n/n to meet the 100% rule."), "src": ["pmbok"]},
    "rule100": {"pt": ("Regra dos 100%", "✅ quando: (1) todas as atividades estão num pacote de trabalho; (2) todos os pacotes têm pelo menos uma atividade; (3) não há códigos inexistentes; (4) se houver pesos, os filhos de cada elemento somam 100%",
                        "Garante que a WBS contém todo o trabalho do projeto e só esse trabalho. Nos custos: BAC do projeto = Σ BAC do nível 1 = Σ custos das atividades."),
                "en": ("100% rule", "✅ when: (1) every activity is in a work package; (2) every package has at least one activity; (3) there are no non-existent codes; (4) if weights are used, the children of each element add up to 100%",
                       "Ensures the WBS contains all of the project's work and nothing else. For costs: project BAC = Σ level-1 BAC = Σ activity costs."), "src": ["pmbok", "pm2"]},
    "bac": {"pt": ("BAC (orçamento)", "BAC do elemento = Σ custo das atividades de todos os pacotes do ramo (custo da atividade = custo direto + linhas de orçamento associadas)",
                   "Os elementos da WBS não têm custo próprio: o valor sobe sempre das atividades (bottom-up), por isso não há dupla contagem. BAC do pai = Σ BAC dos filhos."),
            "en": ("BAC (budget)", "Element BAC = Σ cost of the activities in every package of the branch (activity cost = direct cost + linked budget lines)",
                   "WBS elements hold no cost of their own: the value always rolls up from activities (bottom-up), so nothing is counted twice. Parent BAC = Σ children BAC."), "src": ["pmbok", "pm2"]},
    "pct_bac": {"pt": ("% do BAC", "% do BAC = BAC do elemento ÷ BAC do projeto", "Peso financeiro do ramo; mostra onde está concentrado o orçamento (também visível no treemap)."),
                "en": ("% of BAC", "% of BAC = element BAC ÷ project BAC", "Financial weight of the branch; shows where the budget is concentrated (also visible in the treemap)."), "src": ["pmbok"]},
    "start_finish": {"pt": ("Início e fim", "Início = data mais cedo de início (ES) mínima das atividades do ramo; Fim = data mais cedo de fim (EF) máxima", "Datas do plano CPM (passagem para a frente). São as datas da barra-resumo no Gantt."),
                     "en": ("Start and finish", "Start = minimum early start (ES) of the branch's activities; Finish = maximum early finish (EF)", "CPM plan dates (forward pass). They are the dates of the summary bar in the Gantt."), "src": ["pmbok"]},
    "duration": {"pt": ("Duração", "Duração = EF máx. − ES mín. das atividades do ramo (na unidade de tempo do projeto)",
                        "NÃO é a soma das durações: atividades em paralelo sobrepõem-se. Ex.: A (0→4) e B (2→6) em paralelo → duração 6, não 8."),
                 "en": ("Duration", "Duration = max EF − min ES of the branch's activities (in the project time unit)",
                        "It is NOT the sum of durations: parallel activities overlap. E.g. A (0→4) and B (2→6) in parallel → duration 6, not 8."), "src": ["pmbok"]},
    "critical": {"pt": ("Crítico", "🔴 se pelo menos uma atividade do ramo tem folga total = 0 (caminho crítico)", "Um atraso nesse ramo atrasa o fim do projeto."),
                 "en": ("Critical", "🔴 if at least one activity in the branch has total float = 0 (critical path)", "A delay in this branch delays the end of the project."), "src": ["pmbok"]},
    "pv": {"pt": ("PV (valor planeado)", "PV = Σ PV das atividades do ramo; PV da atividade = BAC × % do trabalho que devia estar feito na data de controlo, segundo o perfil de distribuição",
                  "Quanto devia estar gasto/feito à data de controlo. Muda com a data de controlo."),
           "en": ("PV (planned value)", "PV = Σ PV of the branch's activities; activity PV = BAC × % of work that should be done at the status date, according to the distribution profile",
                  "How much should have been done/spent by the status date. Changes with the status date."), "src": ["pmbok", "pm2"]},
    "ev": {"pt": ("EV (valor ganho)", "EV = Σ (BAC da atividade × % concluída da atividade) no ramo", "Valor do trabalho efetivamente realizado, medido ao preço orçamentado."),
           "en": ("EV (earned value)", "EV = Σ (activity BAC × activity % complete) in the branch", "Value of the work actually done, measured at budgeted cost."), "src": ["pmbok", "pm2"]},
    "ac": {"pt": ("AC (custo real)", "AC = Σ custo real registado das atividades do ramo", "Quanto já foi efetivamente gasto."),
           "en": ("AC (actual cost)", "AC = Σ recorded actual cost of the branch's activities", "How much has actually been spent."), "src": ["pmbok", "pm2"]},
    "pct": {"pt": ("% concluída", "% concluída do elemento = EV ÷ BAC (ponderada pelo custo)",
                   "NÃO é a média simples das % das atividades: uma atividade de 200 000 € pesa 40 vezes mais do que uma de 5 000 €."),
            "en": ("% complete", "Element % complete = EV ÷ BAC (cost-weighted)",
                   "It is NOT the simple average of activity percentages: a €200,000 activity weighs 40 times more than a €5,000 one."), "src": ["pmbok"]},
    "cpi": {"pt": ("CPI (índice de desempenho de custo)", "CPI do elemento = Σ EV ÷ Σ AC do ramo (soma primeiro, divide depois)",
                   "< 1 → custa mais do que o orçamentado (cada € gasto produz CPI € de trabalho); > 1 → abaixo do custo. NÃO é a média dos CPI das atividades. Contorno vermelho no diagrama quando < 0,95."),
            "en": ("CPI (cost performance index)", "Element CPI = Σ EV ÷ Σ AC of the branch (sum first, then divide)",
                   "< 1 → costing more than budgeted (each € spent yields CPI € of work); > 1 → under budget. It is NOT the average of activity CPIs. Red border in the diagram when < 0.95."), "src": ["pmbok", "pm2"]},
    "spi": {"pt": ("SPI (índice de desempenho de prazo)", "SPI do elemento = Σ EV ÷ Σ PV do ramo", "< 1 → atrasado face ao plano; > 1 → adiantado. Vermelho quando < 0,95."),
            "en": ("SPI (schedule performance index)", "Element SPI = Σ EV ÷ Σ PV of the branch", "< 1 → behind plan; > 1 → ahead. Red when < 0.95."), "src": ["pmbok", "pm2"]},
    "weight": {"pt": ("Peso no elemento-pai", "Opcional, em %. Os pesos dos filhos de cada elemento devem somar 100%", "Útil quando se quer medir progresso por marcos ponderados; se vazio, o peso efetivo é o % do BAC."),
               "en": ("Weight in parent", "Optional, in %. The weights of the children of each element must add up to 100%", "Useful to measure progress by weighted milestones; if empty, the effective weight is the % of BAC."), "src": ["pmbok"]},
    "rule_880": {"pt": ("Regra 8/80", "Duração do pacote entre 8 h e 80 h de trabalho; conversão: 8 h = 1 dia útil; 80 h = 10 dias úteis = 2 semanas (5 dias úteis/semana) ≈ 0,46 meses (21,67 dias úteis/mês)",
                        "Pacotes muito grandes são difíceis de controlar; muito pequenos geram burocracia. É uma orientação (aviso), não uma obrigação."),
                 "en": ("8/80 rule", "Package duration between 8 h and 80 h of work; conversion: 8 h = 1 working day; 80 h = 10 working days = 2 weeks (5 working days/week) ≈ 0.46 months (21.67 working days/month)",
                        "Very large packages are hard to control; very small ones create bureaucracy. It is guidance (a warning), not an obligation."), "src": ["pmbok"]},
    "reporting": {"pt": ("Regra do período de reporte", "Duração do pacote ≤ 1 período de reporte (na app: 1 mês ≈ 4,35 semanas); o limite pode ser ajustado em 'Duração máx.'",
                         "Usada em projetos longos (semanas/meses): assim cada pacote começa e acaba entre dois relatórios, o que facilita medir o progresso."),
                  "en": ("Reporting-period rule", "Package duration ≤ 1 reporting period (in the app: 1 month ≈ 4.35 weeks); the limit can be adjusted in 'Max. duration'",
                         "Used in long projects (weeks/months): each package then starts and ends between two reports, which makes progress easier to measure."), "src": ["pmbok", "pm2"]},
    "summary_bar": {"pt": ("Barra-resumo (Gantt)", "Barra preta do Início (ES mín.) ao Fim (EF máx.) do ramo; faixa amarela = % concluída = EV ÷ BAC",
                           "Mostra cada entregável como um bloco, como no MS Project; expandir mostra as atividades por baixo."),
                    "en": ("Summary bar (Gantt)", "Black bar from the branch's Start (min ES) to Finish (max EF); yellow strip = % complete = EV ÷ BAC",
                           "Shows each deliverable as one block, as in MS Project; expanding shows the activities underneath."), "src": ["pmbok"]},
    "raci_wp": {"pt": ("RACI por pacote", "Um papel por célula (R, A, S, C, I) para cada pacote de trabalho; deve haver exatamente um 'A' por pacote",
                       "O 'A' do pacote responde pela sua aceitação (critérios do dicionário) e pela de todas as suas atividades."),
                "en": ("RACI per package", "One role per cell (R, A, S, C, I) for each work package; there should be exactly one 'A' per package",
                       "The package's 'A' is accountable for its acceptance (dictionary criteria) and that of all its activities."), "src": ["pmbok", "pm2"]},
    "change_prop": {"pt": ("Propagação das alterações", "Impacto do elemento = Σ impactos (custo e dias) das alterações aprovadas/implementadas que referem esse elemento, uma das suas atividades ou um dos seus descendentes",
                           "Uma alteração ao pacote 1.2.1 aparece também em 1.2 e em 1, até ao topo. Pedidos propostos ou rejeitados não contam."),
                    "en": ("Change propagation", "Element impact = Σ impacts (cost and days) of approved/implemented changes referring to that element, one of its activities or one of its descendants",
                           "A change to package 1.2.1 also shows in 1.2 and in 1, up to the top. Proposed or rejected requests do not count."), "src": ["pmbok", "pm2"]},
}


def wbs_term(key: str, lang: str | None = None) -> tuple[str, str, str]:
    """(name, formula, meaning) of a WBS glossary term in the current language."""
    from .i18n import get_lang
    g = WBS_GLOSSARY[key]
    return g["pt" if (lang or get_lang()) == "pt" else "en"]


def wbs_tip(key: str) -> str:
    """Tooltip text: formula + meaning."""
    _, f, m = wbs_term(key)
    return f"{f}. {m}"
