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
    "mendelow": "Mendelow, A. (1991). Stakeholder mapping. *Proceedings of the 2nd International Conference on Information Systems*.",
}

H = {
"home": {
 "pt": ("Este estúdio acompanha todo o **ciclo de gestão de projetos (PCM)**: Programação → Identificação → Formulação → Implementação → Avaliação. "
        "Os módulos estão ligados: problemas → objetivos → logframe → atividades → PERT/CPM → Gantt e custos → riscos → indicadores → EVM.",
        "Siga o menu de cima para baixo. Cada página tem uma legenda (o que é, como se lê, fonte) e uma interpretação automática dos resultados.",
        ["pcm", "pm2", "course"]),
 "en": ("This studio covers the whole **Project Cycle Management (PCM)**: Programming → Identification → Formulation → Implementation → Evaluation. "
        "Modules are linked: problems → objectives → logframe → activities → PERT/CPM → Gantt & costs → risks → indicators → EVM.",
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
        "Em cada caixa: em cima ES | ID | EF; em baixo LS | D | LF. Vermelho = crítico. Probabilidade de cumprir T: P(Z ≤ (T − μ)/σ). Folga livre (FF) = quanto a atividade pode atrasar sem atrasar a sucessora.",
        ["course", "pmbok", "pm2"]),
 "en": ("**CPM**: forward pass (early start/finish, ES/EF) and backward pass (late start/finish, LS/LF); **total float** TF = LS − ES and the **critical path** is the sequence of zero-float activities. "
        "**PERT**: three estimates (optimistic *a*, most likely *m*, pessimistic *b*); expected duration tₑ = (a + 4m + b)/6, variance σ² = ((b − a)/6)². **Monte Carlo simulation** (Beta-PERT) gives deadline probabilities and criticality indices. **Crashing** shortens the project at minimum cost (linear programming).",
        "In each box: top ES | ID | EF; bottom LS | D | LF. Red = critical. Probability of meeting T: P(Z ≤ (T − μ)/σ). Free float (FF) = how long an activity can slip without delaying its successor.",
        ["course", "pmbok", "pm2"])},
"gantt": {
 "pt": ("O **diagrama de Gantt** mostra as atividades no calendário, calculado a partir do PERT/CPM. Com o **orçamento distribuído no tempo** obtém-se o custo por período e o acumulado (**curva S**), base do mapa de fluxos de caixa (cash flow).",
        "Barras vermelhas = caminho crítico; extensão cinzenta = folga total; losangos = marcos. A linha de base (baseline) permite comparar o planeado inicial com o atual.",
        ["course", "pcm", "pm2"]),
 "en": ("The **Gantt chart** shows activities on the calendar, computed from PERT/CPM. The **time-phased budget** gives cost per period and cumulative cost (**S-curve**), the basis for the project cash-flow map.",
        "Red bars = critical path; grey extension = total float; diamonds = milestones. The baseline lets you compare the original plan with the current one.",
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
}
