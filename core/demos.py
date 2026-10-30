"""Example projects in six industries. Every module is populated so the whole pipeline can be explored."""
from __future__ import annotations

import copy
from datetime import timedelta

from .model import new_project, normalize

DEMOS = {
    "trade": {"pt": "🌍 Cooperação para o desenvolvimento — Estatísticas de Comércio (exemplo do professor)",
              "en": "🌍 Development cooperation — Trade Statistics (professor's example)"},
    "education": {"pt": "🎓 Educação / TIC — Escolas Digitais no 1.º e 2.º ciclos", "en": "🎓 Education / ICT — Digital Schools (primary & lower secondary)"},
    "health": {"pt": "🏥 Saúde — Telemonitorização de doentes crónicos", "en": "🏥 Health — Chronic patient telemonitoring"},
    "it": {"pt": "💻 Tecnologia — Implementação de ERP", "en": "💻 Technology — ERP implementation"},
    "construction": {"pt": "🏗️ Construção — Centro comunitário", "en": "🏗️ Construction — Community centre"},
    "aero": {"pt": "✈️ Indústria aeronáutica — Nova linha de manutenção (MRO)", "en": "✈️ Aerospace — New maintenance line (MRO)"},
}

ALL_SMART = dict(specific=True, measurable=True, available=True, relevant=True, timely=True)


def _compile(D: dict) -> dict:
    p = new_project(D["meta"]["name"], D["meta"]["industry"])
    p["meta"].update(D["meta"])
    p["policy"].update(D.get("policy", {}))
    p["policy_goals"] = [dict(zip(["document", "strategic_goal", "impact_indicator", "baseline", "target", "source"], g), id=f"G{i+1}")
                         for i, g in enumerate(D.get("goals", []))]
    p["stakeholders"] = [dict(zip(["name", "type", "influence", "interest", "attitude", "engagement", "characteristics", "interests",
                                   "capacity_motivation", "possible_actions", "benefits_to_project", "benefits_of_project"], s), id=f"S{i+1}")
                         for i, s in enumerate(D.get("stakeholders", []))]
    p["behaviour"] = [dict(zip(["target_group", "perception", "opportunity", "ability", "motivation", "evidence", "implication"], b), id=f"B{i+1}")
                      for i, b in enumerate(D.get("behaviour", []))]
    p["problems"] = [dict(zip(["id", "level", "text", "parent", "objective", "in_scope"], (*x, True) if len(x) == 5 else x)) for x in D.get("problems", [])]
    crit = [c["criterion"] for c in p["strategies"]["criteria"]]
    p["strategies"]["options"] = [{"name": n, "description": d, "scores": dict(zip(crit, sc))} for n, d, sc in D.get("strategies", [])]
    p["strategies"]["selected"] = D.get("selected", "")
    p["objectives"] = [dict(zip(["code", "level", "text", "parent"], o)) for o in D.get("objectives", [])]
    inds = []
    for x in D.get("indicators", []):
        r = dict(zip(["id", "objective_code", "indicator", "unit", "baseline", "baseline_year", "target", "target_year", "current", "source", "frequency", "responsible"], x))
        r.update(ALL_SMART)
        r.update(D.get("smart_override", {}).get(r["id"], {}))
        inds.append(r)
    p["indicators"] = inds
    p["benchmarks"] = [{"indicator_id": k, "peer": pr, "value": v, "year": D["meta"].get("bench_year", 2025)} for k, lst in D.get("benchmarks", {}).items() for pr, v in lst]
    p["timeseries"] = [{"indicator_id": k, "year": y, "value": v} for k, lst in D.get("series", {}).items() for y, v in lst]
    p["assumptions"] = [dict(zip(["id", "type", "objective_code", "text", "holds", "evidence", "evidence_quality"], h), important=True,
                             redesign_possible=False) for h in D.get("assumptions", [])]
    p["toc"].update(D.get("toc", {}))
    p["preconditions"] = [dict(zip(["id", "text", "leads_to", "assumption"], c)) for c in D.get("pre", [])]
    acts = []
    for x in D.get("activities", []):
        a = dict(zip(["id", "name", "output_code", "type", "predecessors", "optimistic", "most_likely", "pessimistic", "cost", "distribution", "responsible"], x))
        a["crash_duration"] = round(a["most_likely"] * 0.75, 1) if a["type"] == "Production" and a["most_likely"] > 1 else None
        a["crash_cost"] = round(a["cost"] * 1.18, 0) if a["crash_duration"] else None
        acts.append(a)
    p["activities"] = acts
    roles = D.get("roles", p["raci"]["roles"])
    p["raci"] = {"roles": roles, "matrix": {}}
    for a in acts:
        row = {r: "I" for r in roles}
        row[roles[0]] = "A"
        resp = a["responsible"] if a["responsible"] in roles else (roles[1] if len(roles) > 1 else roles[0])
        row[resp] = "R" if resp != roles[0] else "A"
        if resp == roles[0] and len(roles) > 1:
            row[roles[1]] = "S"
        if len(roles) > 2 and row.get(roles[2]) == "I":
            row[roles[2]] = "C"
        p["raci"]["matrix"][a["id"]] = row
    p["risks"] = [dict(zip(["id", "type", "description", "likelihood", "impact", "target_exposure", "existing_mitigation", "proposed_mitigation",
                            "risk_manager", "risk_owner", "review_by", "assumption_id", "level_affected", "strategy", "contingency", "preventive_activity"], r))
                  for r in D.get("risks", [])]
    p["budget"] = [dict(zip(["activity_id", "category", "item", "unit", "quantity", "unit_cost", "phase"], b), id=f"L{i+1}") for i, b in enumerate(D.get("budget", []))]
    p["procurement"] = [dict(zip(["id", "item", "category", "activity_id", "estimated_cost", "method", "planned_date", "responsible", "selection_criteria", "risk"], q))
                        for q in D.get("procurement", [])]
    p["finance"].update(D.get("finance", {}))
    p["evaluation"] = [dict(zip(["criterion", "question", "judgement_criteria", "indicator", "source", "method"], e), id=f"E{i+1}") for i, e in enumerate(D.get("evaluation", []))]
    p["quality"] = D.get("quality", {})
    p = normalize(p)
    # derived: cash flows (investment from schedule) and EVM tracking history
    from . import schedule as S
    sched = S.compute(p)
    if sched.get("ok"):
        # demo progress at the status date, consistent with the plan and the demo "story" (drift)
        import math
        fe, fa = D.get("drift", (0.96, 1.05))
        st_date = S.to_date(p["meta"]["status_date"])
        for k, a in enumerate(p["activities"]):
            bac = sched["acts"].set_index("id").loc[a["id"], "cost"]
            pv = S.planned_value_act(sched, a["id"], st_date)
            if bac <= 0 or pv <= 0:
                continue
            v = 1 + 0.08 * math.sin(1.7 * (k + 1))
            pct_ = min(1.0, pv / bac * fe * v)
            a["pct_complete"] = round(pct_, 2)
            a["actual_cost"] = round(a["pct_complete"] * bac * fa * (2 - v) , -2)
        sched = S.compute(p)
        inv = S.yearly_investment(sched)
        cont = sched["contingency"]
        rows = []
        years = sorted(set(inv) | {y for y, _o, _b in D.get("benefits", [])})
        for y in range(0, max(years) + 1):
            o = next((x[1] for x in D.get("benefits", []) if x[0] == y), 0.0)
            b = next((x[2] for x in D.get("benefits", []) if x[0] == y), 0.0)
            i = inv.get(y, 0.0) + (cont * inv.get(y, 0.0) / sched["bac"] if sched["bac"] else 0)
            rows.append({"year": y, "investment": round(i, 0), "operating_costs": o, "benefits": b,
                         "note": "Investimento importado do cronograma (+ contingência)" if inv.get(y) else ""})
        p["cashflows"] = rows
        p["baseline"] = S.make_baseline(p, sched)
        # two PERT scenarios per demo: the initial plan and an accelerated variant (−15% durations on production activities)
        import copy as _c
        fast = _c.deepcopy(p["activities"])
        for a in fast:
            if a.get("type") == "Production":
                for k in ("optimistic", "most_likely", "pessimistic"):
                    a[k] = round(float(a[k]) * 0.85, 2)
                a["cost"] = round(float(a.get("cost") or 0) * 1.08, 0)
        p["pert_scenarios"] = [{"name": "Plano inicial", "created": p["meta"]["start_date"], "time_unit": p["meta"]["time_unit"],
                                "duration_mode": p["meta"]["duration_mode"], "activities": _c.deepcopy(p["activities"])},
                               {"name": "Acelerado (−15% duração, +8% custo)", "created": p["meta"]["start_date"], "time_unit": p["meta"]["time_unit"],
                                "duration_mode": p["meta"]["duration_mode"], "activities": fast}]
        # tracking: monthly history up to the status date (EV and AC drift as in the demo story)
        status = S.to_date(p["meta"]["status_date"])
        e = S.evm(p, sched)
        hist = []
        per = sched["periods"]
        fe, fa = D.get("drift", (0.96, 1.05))
        for _, r in per.iterrows():
            if r["period_end"] < status:
                pv = S.planned_value_at(sched, r["period_end"])
                hist.append({"date": r["period_end"].isoformat(), "ev": round(pv * fe, 0), "ac": round(pv * fe * fa, 0), "note": ""})
        p["tracking"] = hist
    return p


# =============================================================================== 1. TRADE STATISTICS
TRADE = {
    "meta": {"name": "Melhoria das Estatísticas de Comércio Externo", "industry": "Cooperação para o desenvolvimento",
             "organisation": "Instituto Nacional de Estatística (INE)", "sponsor": "União Europeia (DG INTPA)", "country": "País parceiro",
             "manager": "Gestor de projeto", "description": "Projeto de capacitação institucional para melhorar a qualidade e a disseminação das estatísticas de comércio externo, com base no exemplo das árvores de problemas e objetivos do professor.",
             "start_date": "2027-01-01", "time_unit": "months", "duration_mode": "pert", "status_date": "2027-09-30",
             "target_duration": 17, "contingency_method": "percent", "contingency_pct": 0.08, "contingency_used": 12000, "currency": "EUR", "bench_year": 2025},
    "policy": {"context": "Economia pequena e aberta, dependente de exportações agrícolas; adesão recente a um acordo de comércio regional; INE com recursos limitados e sistemas informáticos obsoletos; dados aduaneiros e estatísticos não coincidem.",
               "content": "A Estratégia Nacional de Desenvolvimento 2026-2030 prevê diversificar exportações e basear a política comercial em evidência. O Programa Indicativo UE-país parceiro inclui a 'Governação económica e estatística' como setor prioritário.",
               "consequences": "Sem estatísticas fiáveis, as negociações comerciais e o apoio às PME exportadoras assentam em estimativas; risco de efeitos distributivos negativos para pequenos produtores do interior com menor acesso à informação."},
    "goals": [("Estratégia Nacional de Desenvolvimento 2026-2030", "Diversificar as exportações e aumentar o seu valor em 25% até 2030", "Valor das exportações (M€)", "1 200 (2025)", "1 500 (2030)", "Banco Central / INE"),
              ("Programa Indicativo Plurianual UE 2026-2030", "Melhorar a formulação de políticas baseada em evidência", "N.º de documentos de política que usam estatísticas oficiais", "3 (2026)", "12 (2030)", "Ministério do Comércio")],
    "stakeholders": [
        ("Instituto Nacional de Estatística (INE)", "Project partner", 5, 5, "Supporter", "Collaborate", "Organismo público, 120 técnicos, mandato legal para estatísticas oficiais", "Quer melhorar a credibilidade e cumprir normas internacionais", "Alta motivação; capacidade técnica limitada em TI", "Co-gestão do projeto; comité de pilotagem", "Dados, técnicos, instalações", "Novos sistemas, competências e reputação"),
        ("Autoridade Aduaneira", "Project partner", 4, 3, "Neutral", "Involve", "Fonte primária dos dados de comércio", "Preocupação com a carga de trabalho adicional", "Capacidade técnica razoável; motivação moderada", "Protocolo de partilha de dados; ganhos rápidos para as Alfândegas", "Acesso aos registos aduaneiros", "Dados validados e menos pedidos ad hoc"),
        ("Técnicos do INE e das Alfândegas", "Target group", 2, 5, "Supporter", "Empower", "≈ 60 técnicos que produzem as estatísticas", "Sobrecarga e ferramentas inadequadas", "Motivados, mas com lacunas de competências", "Formação certificada e mentoria", "Execução diária", "Competências e progressão na carreira"),
        ("Ministério do Comércio", "Beneficiary", 5, 4, "Supporter", "Consult", "Decisor da política comercial", "Precisa de dados fiáveis para negociações", "Elevada influência política", "Briefings trimestrais; produtos de dados à medida", "Apoio político", "Melhor formulação de políticas"),
        ("Empresas exportadoras (PME)", "Beneficiary", 2, 4, "Supporter", "Inform", "≈ 1 500 empresas, muitas no interior", "Faltam dados de mercado para decidir", "Interesse elevado; acesso digital desigual", "Portal web, newsletters e sessões regionais", "Feedback sobre necessidades", "Informação de mercado gratuita"),
        ("Universidades e investigadores", "Beneficiary", 1, 3, "Supporter", "Inform", "Centros de investigação económica", "Ausência de microdados", "Capacidade analítica elevada", "Acesso a microdados anonimizados", "Validação e análise independente", "Dados para investigação"),
        ("União Europeia (DG INTPA)", "Resource provider", 5, 3, "Supporter", "Consult", "Doador; financia 100% do projeto", "Resultados e prestação de contas", "Elevada", "Relatórios semestrais e comité de pilotagem", "Financiamento", "Contribuição para os objetivos do Programa Indicativo"),
        ("Intermediários que vendem dados de comércio", "Other (specify)", 3, 4, "Opponent", "Monitor", "Consultoras que hoje vendem estimativas", "Tiram partido da falta de informação pública", "Motivação baixa para a mudança", "Envolver como reutilizadores de dados abertos; comunicação transparente", "—", "Novos serviços de valor acrescentado sobre dados abertos"),
    ],
    "behaviour": [("Técnicos do INE e das Alfândegas", 4, 3, 2, 3, "Inquérito a 45 técnicos (2026): 70% sem formação SH/SITC atualizada", "Plano de formação certificada + mentoria (A4)"),
                  ("Empresas exportadoras (PME)", 3, 2, 3, 4, "Grupos focais em 3 regiões; 40% das PME do interior sem acesso regular à internet", "Sessões regionais e newsletter por SMS (A8)")],
    "problems": [
        ("E1", "Effect", "Ausência de informação para os agentes económicos", "", "Melhor informação para os agentes económicos"),
        ("E2", "Effect", "Fraca formulação da política comercial", "", "Melhor formulação da política comercial"),
        ("E3", "Effect", "Ausência de informação para os investigadores", "", "Informação disponível para os investigadores"),
        ("P1", "Core problem", "Fraca qualidade das estatísticas de comércio", "E1, E2", "Qualidade das estatísticas de comércio melhorada"),
        ("P2", "Core problem", "Fraca disseminação das estatísticas de comércio", "E2, E3", "Estatísticas de comércio amplamente disseminadas"),
        ("C1", "Cause", "Plataformas de TI inadequadas", "P1", "Plataformas de TI adequadas"),
        ("C2", "Cause", "Enquadramento institucional inadequado", "P1", "Enquadramento institucional adequado"),
        ("C3", "Cause", "Falta de competências-chave em estatísticas de comércio", "P1, P2", "Capacidades-chave em estatísticas de comércio desenvolvidas"),
        ("C4", "Cause", "Inexistência de estratégia de disseminação", "P2", "Estratégia de disseminação implementada"),
        ("C5", "Cause", "Inexistência de plataforma web", "P2", "Plataforma web online"),
    ],
    "strategies": [("Estratégia de qualidade", "Foco em TI, enquadramento institucional e competências (Outcome 1)", [5, 4, 3, 3, 4]),
                   ("Estratégia de disseminação", "Foco na estratégia de disseminação e plataforma web (Outcome 2)", [3, 4, 4, 3, 3]),
                   ("Estratégia integrada", "Qualidade + disseminação (Outcomes 1 e 2), como na árvore de objetivos", [5, 4, 4, 4, 3])],
    "selected": "Estratégia integrada",
    "objectives": [("IMP", "Impact", "Contribuir para uma melhor formulação da política comercial e para a informação dos agentes económicos e investigadores", ""),
                   ("OC1", "Outcome", "Qualidade das estatísticas de comércio melhorada", "IMP"),
                   ("OC2", "Outcome", "Estatísticas de comércio amplamente disseminadas", "IMP"),
                   ("1.1", "Output", "Plataformas de TI adequadas instaladas e operacionais", "OC1"),
                   ("1.2", "Output", "Enquadramento institucional INE–Alfândegas estabelecido", "OC1"),
                   ("1.3", "Output", "Capacidades-chave em estatísticas de comércio desenvolvidas", "OC1"),
                   ("2.1", "Output", "Estratégia de disseminação aprovada e implementada", "OC2"),
                   ("2.2", "Output", "Plataforma web de dados de comércio online", "OC2")],
    "indicators": [
        ("I1", "IMP", "N.º de documentos de política comercial que citam estatísticas oficiais", "documentos/ano", 3, 2026, 12, 2030, 4, "Relatórios do Ministério do Comércio", "Anual", "Ministério do Comércio"),
        ("I2", "OC1", "Taxa de discrepância entre dados aduaneiros e estatísticos", "%", 18, 2026, 6, 2028, 14, "Relatório de qualidade do INE", "Semestral", "INE"),
        ("I3", "OC2", "N.º médio de descargas mensais de dados de comércio", "descargas/mês", 500, 2026, 5000, 2028, 900, "Estatísticas do portal", "Mensal", "INE – Disseminação"),
        ("I4", "1.3", "N.º de técnicos certificados em estatísticas de comércio", "técnicos", 0, 2026, 40, 2028, 22, "Registos de certificação", "Trimestral", "Gestor de projeto"),
        ("I5", "1.1", "Prazo de publicação das estatísticas mensais", "dias após fim do mês", 90, 2026, 45, 2028, 75, "Calendário de publicações do INE", "Mensal", "INE"),
        ("I6", "2.2", "Disponibilidade da plataforma web", "% do tempo", 0, 2026, 99, 2028, 0, "Monitorização do servidor", "Mensal", "Consultor TI"),
        ("I7", "1.2", "Protocolo INE–Alfândegas assinado e em vigor", "sim=1 / não=0", 0, 2026, 1, 2027, 1, "Diário da República", "Única", "Gestor de projeto"),
        ("I8", "2.1", "% de publicações divulgadas na data anunciada no calendário", "%", 40, 2026, 95, 2028, 70, "Calendário de difusão do INE", "Trimestral", "INE – Disseminação"),
    ],
    "smart_override": {"I1": {"timely": False}, "I6": {"available": True}},
    "benchmarks": {"I2": [("País vizinho A", 4), ("País vizinho B", 7), ("Média regional", 9), ("País vizinho C", 12)],
                   "I3": [("INE país A", 8000), ("INE país B", 4500), ("INE país C", 3000), ("Média regional", 5200)],
                   "I5": [("Eurostat (UE)", 40), ("País vizinho A", 30), ("País vizinho B", 45), ("País vizinho C", 60)]},
    "series": {"I2": [(2022, 22), (2023, 20.5), (2024, 19.6), (2025, 18.7), (2026, 18)],
               "I3": [(2023, 380), (2024, 420), (2025, 460), (2026, 500)],
               "I5": [(2022, 98), (2023, 95), (2024, 92), (2025, 91), (2026, 90)]},
    "assumptions": [
        ("H1", "Operational", "1.1", "Os fornecedores entregam o equipamento informático dentro dos prazos contratuais", "Possibly", "Projetos anteriores do INE: 2 em 3 entregas a tempo (lições aprendidas)", 3),
        ("H2", "Operational", "1.3", "Os técnicos formados permanecem nos serviços durante o projeto", "Possibly", "Taxa de rotação de 12%/ano nos últimos 3 anos", 2),
        ("H3", "Behavioural", "OC1", "Os técnicos utilizam as novas plataformas e procedimentos no trabalho diário", "Possibly", "Análise de padrões comportamentais: perceção positiva, capacidade baixa", 2),
        ("H4", "Behavioural", "OC2", "Os agentes económicos consultam regularmente a plataforma de dados", "Possibly", "Grupos focais com PME em 3 regiões", 2),
        ("H5", "Political", "IMP", "O Governo mantém a prioridade às políticas comerciais baseadas em evidência", "Possibly", "Estratégia Nacional 2026-2030 e declarações do Ministro", 3),
        ("H6", "Operational", "1.2", "As Alfândegas aceitam partilhar microdados com o INE", "Almost certainly", "Memorando de entendimento já negociado", 4),
    ],
    "toc": {"vision": "Políticas comerciais e decisões empresariais baseadas em estatísticas oficiais fiáveis, atempadas e acessíveis a todos.",
            "context": "Sistema estatístico com recursos escassos, dados aduaneiros dispersos e procura crescente de informação após o acordo comercial regional.",
            "actors": "INE e Alfândegas (produtores), Ministério do Comércio (utilizador político), PME e investigadores (utilizadores), UE (financiador), intermediários de dados (potenciais opositores).",
            "strategic_choices": "Atuar em simultâneo na qualidade (oferta) e na disseminação (procura); não financiar inquéritos novos (outro doador); dados abertos por defeito.",
            "learning": "As PME do interior passam a usar dados oficiais? A redução do prazo de publicação aumenta a utilização? A rotação de técnicos compromete a sustentabilidade?"},
    "pre": [("C1", "Liderança do INE comprometida com a reforma", "OC1", "Direção do INE mantém-se estável"),
            ("C2", "Utilizadores conhecem os novos produtos de dados", "OC2", "Campanha de comunicação chega às regiões")],
    "activities": [
        ("A1", "Diagnóstico das plataformas de TI e levantamento de requisitos", "1.1", "Production", "", 1.5, 2, 3, 40000, "Uniform", "Consultor TI"),
        ("A2", "Aquisição e instalação de servidores e software", "1.1", "Production", "A1", 3, 4, 7, 180000, "Start", "Consultor TI"),
        ("A3", "Revisão do quadro legal e protocolo INE–Alfândegas", "1.2", "Production", "", 2, 3, 5, 35000, "Uniform", "INE – Direção de Estatísticas"),
        ("A4", "Plano de formação e formação certificada em estatísticas de comércio", "1.3", "Production", "A1", 4, 6, 9, 90000, "Uniform", "INE – Direção de Estatísticas"),
        ("A5", "Produção e validação das novas séries de comércio", "1.1", "Production", "A2, A3, A4", 2, 3, 5, 60000, "Uniform", "INE – Direção de Estatísticas"),
        ("A6", "Desenho da estratégia de disseminação", "2.1", "Production", "A3", 1, 2, 3, 25000, "Uniform", "Gestor de projeto"),
        ("A7", "Desenvolvimento da plataforma web de dados", "2.2", "Production", "A2, A6", 4, 6, 10, 120000, "Back-loaded", "Consultor TI"),
        ("A8", "Lançamento e campanha de comunicação nas regiões", "2.1", "Support - Communication", "A5, A7", 1, 1, 2, 30000, "Milestone 50/50", "Gestor de projeto"),
        ("A9", "Gestão do projeto e comité de pilotagem", "", "Support - Management", "", 15, 15, 15, 80000, "Uniform", "Gestor de projeto"),
        ("A10", "Inquérito de baseline e avaliação final", "", "Support - M&E", "A8", 1, 2, 3, 40000, "Milestone 50/50", "Gestor de projeto"),
        ("A11", "Plano de retenção de técnicos (prevenção do risco R2)", "1.3", "Support - Risk prevention", "A4", 1, 2, 2, 15000, "Uniform", "INE – Direção de Estatísticas"),
    ],
    "progress": {"A1": (1.0, 43000), "A2": (1.0, 186000), "A3": (1.0, 33000), "A4": (0.55, 56000), "A6": (1.0, 27000),
                 "A7": (0.15, 22000), "A9": (0.6, 50000)},
    "drift": (0.95, 1.05),
    "roles": ["Gestor de projeto", "INE – Direção de Estatísticas", "Delegação da UE", "Consultor TI", "Autoridade Aduaneira"],
    "risks": [
        ("R1", "Political", "Mudança de prioridades do Governo reduz o apoio às estatísticas de comércio", 2, 4, 4, "Alinhamento com a Estratégia Nacional", "Briefings trimestrais ao Ministro; integrar o projeto no plano de atividades do INE", "Gestor de projeto", "Delegação da UE", "Semestral", "H5", "Impact", "Reduce", 0, ""),
        ("R2", "Human resources", "Rotação elevada dos técnicos formados", 3, 3, 4, "Contratos de formação com período de permanência", "Plano de retenção e formação de formadores (A11)", "INE – Direção de Estatísticas", "Gestor de projeto", "Trimestral", "H2", "Output", "Reduce", 15000, "A11"),
        ("R3", "IT", "Atraso na entrega ou falha dos servidores", 2, 3, 3, "Garantias contratuais", "Cláusulas de penalização; plano B em cloud", "Consultor TI", "Gestor de projeto", "Na entrega (mês 6)", "H1", "Output", "Transfer", 20000, ""),
        ("R4", "Communication and reputation", "Distorção política dos resultados do projeto", 4, 4, 8, "Comunicação transparente", "Ficha do projeto ao comité de pilotagem com revisão dos itens de comunicação", "Gestor de projeto", "Delegação da UE", "Semestral", "", "Outcome", "Reduce", 5000, "A8"),
        ("R5", "Financial", "Variação cambial aumenta o custo do equipamento importado", 2, 2, 4, "Orçamento em EUR", "Compra antecipada / cobertura cambial", "Gestor de projeto", "INE", "Na adjudicação", "", "Activity", "Accept", 10000, ""),
        ("R7", "Human resources", "Os técnicos não aplicam os novos procedimentos e mantêm as rotinas antigas", 2, 4, 4, "—", "Mentoria no posto de trabalho e manuais de procedimentos", "INE – Direção de Estatísticas", "Gestor de projeto", "Trimestral", "H3", "Outcome", "Reduce", 6000, "A11"),
        ("R6", "Project/programme delivery", "PME do interior não utilizam a plataforma por falta de acesso digital", 3, 4, 6, "—", "Newsletter por SMS e sessões presenciais regionais", "Gestor de projeto", "Ministério do Comércio", "Mês 15", "H4", "Outcome", "Reduce", 8000, "A8"),
    ],
    "budget": [("A4", "Fees & Direct Expenses", "Formadores especializados", "dia", 120, 450, "Implementation"),
               ("A4", "Fees & Direct Expenses", "Per diem dos formandos", "pessoa-dia", 300, 80, "Implementation"),
               ("A4", "Materials", "Materiais pedagógicos e certificação", "lote", 1, 12000, "Implementation"),
               ("A9", "Fees & Direct Expenses", "Gestor de projeto", "mês", 15, 4500, "Implementation"),
               ("A9", "Reimbursable Expenses", "Reuniões do comité de pilotagem", "reunião", 5, 2500, "Implementation"),
               ("A2", "Equipment", "Servidores e armazenamento", "unidade", 4, 30000, "Inception"),
               ("A2", "Equipment", "Licenças de software estatístico", "licença", 20, 3000, "Inception")],
    "procurement": [("Q1", "Servidores, armazenamento e licenças", "Goods", "A2", 180000, "Competitive Bidding", "2027-03-01", "Consultor TI", "Preço (40%), conformidade técnica (40%), assistência (20%)", "Atrasos de entrega (R3)"),
                    ("Q2", "Desenvolvimento da plataforma web", "Services", "A7", 115000, "Request for Proposals (RFP)", "2027-05-15", "Gestor de projeto", "Qualidade técnica (70%) / preço (30%)", "Dependência do fornecedor"),
                    ("Q3", "Formadores especializados", "Services", "A4", 54000, "Framework Agreement", "2027-02-15", "INE – Direção de Estatísticas", "Experiência em SH/SITC, referências", "Disponibilidade dos peritos"),
                    ("Q4", "Avaliação final independente", "Services", "A10", 35000, "Request for Quotations (RFQ)", "2028-02-01", "Gestor de projeto", "Independência, metodologia, preço", "—")],
    "finance": {"equity": 1.0, "debt": 0.0, "ke_method": "direct", "ke": 0.05, "tax": 0.0},
    "benefits": [(1, 30000, 120000), (2, 40000, 260000), (3, 40000, 300000), (4, 40000, 320000), (5, 40000, 320000), (6, 40000, 320000)],
    "evaluation": [("Relevance", "Em que medida o projeto responde às prioridades da Estratégia Nacional e às necessidades dos utilizadores?", "Alinhamento explícito; necessidades identificadas na análise de stakeholders", "Grau de alinhamento (1-5)", "Documentos estratégicos; entrevistas", "Análise documental + entrevistas"),
                   ("Effectiveness", "As estatísticas tornaram-se mais fiáveis e mais utilizadas?", "Metas de I2 e I3 atingidas", "I2, I3", "Relatórios de qualidade; portal", "Análise de séries"),
                   ("Efficiency", "Os outputs foram entregues dentro do orçamento e do prazo?", "CPI e SPI ≥ 0,95", "CPI, SPI", "Relatórios financeiros; EVM", "EVM"),
                   ("Impact", "A política comercial passou a basear-se em evidência?", "Documentos de política citam dados oficiais", "I1", "Ministério do Comércio", "Contribution analysis"),
                   ("Sustainability", "O INE mantém as plataformas sem financiamento externo?", "Orçamento do INE prevê custos recorrentes", "% custos recorrentes no OE", "Orçamento de Estado", "Análise financeira")],
    "quality": {"rel1": "Yes", "rel2": "Yes", "rel3": "Yes", "rel4": "Partial", "fea1": "Yes", "fea2": "Yes", "fea3": "Partial", "fea4": "Yes", "fea5": "Yes", "fea6": "Partial"},
}

# =============================================================================== 2. EDUCATION / ICT
EDU = {
    "meta": {"name": "Escolas Digitais — TIC no 1.º e 2.º ciclos", "industry": "Educação / TIC", "organisation": "Agrupamento de Escolas (exemplo)",
             "sponsor": "Município + Fundos europeus (PRR)", "country": "Portugal", "manager": "Coordenador TIC",
             "description": "Integração pedagógica das TIC em 12 escolas do 1.º e 2.º ciclos: equipamentos, formação de professores, recursos digitais e literacia digital dos alunos.",
             "start_date": "2027-09-01", "time_unit": "weeks", "duration_mode": "pert", "status_date": "2028-01-31",
             "target_duration": 38, "contingency_method": "percent", "contingency_pct": 0.07, "contingency_used": 3000, "bench_year": 2025},
    "policy": {"context": "Plano de Ação para a Transição Digital; heterogeneidade de equipamentos entre escolas; professores com diferentes níveis de competência digital (DigCompEdu).",
               "content": "Programa Escola Digital: equipamento, conectividade, capacitação docente e recursos educativos digitais.",
               "consequences": "Risco de aprofundar desigualdades se as famílias sem internet em casa não forem consideradas."},
    "goals": [("Plano de Ação para a Transição Digital", "Desenvolver as competências digitais de alunos e professores", "% de alunos com competências digitais básicas", "55% (2025)", "80% (2030)", "Ministério da Educação / DGEEC")],
    "stakeholders": [("Professores do 1.º e 2.º ciclos", "Target group", 3, 5, "Supporter", "Empower", "180 professores", "Falta de tempo e de formação", "Motivação variável", "Formação em contexto e comunidades de prática", "Implementação em sala de aula", "Competências e recursos"),
                     ("Alunos (6-12 anos)", "Beneficiary", 1, 4, "Supporter", "Inform", "2 400 alunos", "Aprendizagens mais motivadoras", "Elevada motivação", "Atividades lúdicas e projetos", "—", "Literacia digital"),
                     ("Encarregados de educação", "Beneficiary", 2, 3, "Neutral", "Consult", "Famílias heterogéneas", "Receio do tempo de ecrã", "Capacidade digital desigual", "Sessões para pais e regras de utilização", "Apoio em casa", "Acompanhamento escolar"),
                     ("Município", "Resource provider", 5, 4, "Supporter", "Collaborate", "Entidade financiadora", "Visibilidade e equidade territorial", "Elevada", "Comissão de acompanhamento", "Financiamento, conectividade", "Resultados educativos"),
                     ("Direção do Agrupamento", "Project partner", 5, 5, "Supporter", "Collaborate", "Gestão escolar", "Cumprir o Projeto Educativo", "Elevada", "Integração no plano anual", "Liderança", "Melhoria dos resultados")],
    "behaviour": [("Professores do 1.º e 2.º ciclos", 3, 4, 2, 3, "Autoavaliação DigCompEdu: 60% nível A1-A2", "Formação em contexto com mentores digitais"),
                  ("Alunos (6-12 anos)", 5, 3, 3, 5, "Inquérito: 25% sem computador em casa", "Empréstimo de equipamentos")],
    "problems": [("E1", "Effect", "Baixas competências digitais dos alunos", "", "Competências digitais dos alunos melhoradas"),
                 ("E2", "Effect", "Desigualdade digital entre escolas", "", "Equidade digital entre escolas"),
                 ("P1", "Core problem", "Fraca integração pedagógica das TIC", "E1, E2", "TIC integradas na prática pedagógica"),
                 ("C1", "Cause", "Equipamentos obsoletos e conectividade fraca", "P1", "Equipamentos e conectividade adequados"),
                 ("C2", "Cause", "Professores sem formação em pedagogia digital", "P1", "Professores capacitados em pedagogia digital"),
                 ("C3", "Cause", "Falta de recursos educativos digitais adaptados", "P1", "Recursos digitais adaptados disponíveis")],
    "strategies": [("Equipamento primeiro", "Investir sobretudo em hardware", [3, 5, 2, 2, 3]), ("Capacitação + recursos + equipamento", "Abordagem integrada", [5, 4, 4, 4, 4])],
    "selected": "Capacitação + recursos + equipamento",
    "objectives": [("IMP", "Impact", "Contribuir para a melhoria das competências digitais e das aprendizagens dos alunos", ""),
                   ("OC1", "Outcome", "TIC integradas na prática pedagógica das 12 escolas", "IMP"),
                   ("1.1", "Output", "Salas equipadas e com conectividade", "OC1"), ("1.2", "Output", "Professores capacitados em pedagogia digital", "OC1"),
                   ("1.3", "Output", "Repositório de recursos digitais adaptados", "OC1")],
    "indicators": [("I1", "IMP", "% de alunos com competências digitais de nível básico ou superior", "%", 52, 2027, 75, 2029, 58, "Provas de aferição digitais", "Anual", "Direção"),
                   ("I2", "OC1", "% de aulas semanais com utilização pedagógica de TIC", "%", 15, 2027, 50, 2029, 24, "Registos de sumários", "Trimestral", "Coordenador TIC"),
                   ("I3", "1.2", "N.º de professores com certificação DigCompEdu B1+", "professores", 40, 2027, 150, 2029, 88, "Centro de formação", "Semestral", "Coordenador TIC"),
                   ("I4", "1.1", "Rácio alunos por computador", "alunos/PC", 6, 2027, 2, 2028, 3.5, "Inventário", "Anual", "Técnico TIC")],
    "benchmarks": {"I1": [("Média nacional", 60), ("Agrupamento A", 72), ("Agrupamento B", 66), ("Média UE", 70)],
                   "I4": [("Média nacional", 3), ("Agrupamento A", 1.5), ("Agrupamento B", 2)]},
    "series": {"I1": [(2023, 45), (2024, 48), (2025, 50), (2026, 51), (2027, 52)]},
    "assumptions": [("H1", "Operational", "1.1", "A rede de fibra municipal fica concluída até ao início do ano letivo", "Possibly", "Calendário da obra municipal", 3),
                    ("H2", "Behavioural", "OC1", "Os professores aplicam em aula o que aprendem na formação", "Possibly", "Avaliação de impacto de formações anteriores", 2),
                    ("H3", "Political", "IMP", "O Ministério mantém o currículo de TIC no 1.º e 2.º ciclos", "Almost certainly", "Aprendizagens Essenciais em vigor", 4)],
    "toc": {"vision": "Todos os alunos usam as tecnologias de forma crítica, criativa e segura para aprender.", "context": "Transição digital na educação; desigualdades territoriais.",
            "actors": "Professores, alunos, famílias, município, direção, centro de formação.", "strategic_choices": "Formação em contexto, não apenas cursos; recursos abertos.",
            "learning": "A formação em contexto muda práticas? O empréstimo de equipamentos reduz desigualdades?"},
    "activities": [("A1", "Levantamento de necessidades e inventário", "1.1", "Production", "", 2, 3, 4, 8000, "Uniform", "Técnico TIC"),
                   ("A2", "Aquisição de equipamentos (concurso)", "1.1", "Production", "A1", 6, 8, 12, 210000, "End", "Técnico TIC"),
                   ("A3", "Instalação e configuração nas 12 escolas", "1.1", "Production", "A2", 3, 4, 6, 25000, "Uniform", "Técnico TIC"),
                   ("A4", "Diagnóstico DigCompEdu dos professores", "1.2", "Production", "", 1, 2, 3, 3000, "Uniform", "Coordenador TIC"),
                   ("A5", "Formação em contexto (3 vagas)", "1.2", "Production", "A4", 16, 20, 26, 60000, "Uniform", "Centro de formação"),
                   ("A6", "Criação de recursos educativos digitais", "1.3", "Production", "A4", 10, 14, 20, 35000, "Back-loaded", "Coordenador TIC"),
                   ("A7", "Implementação em sala de aula e mentoria", "OC1", "Production", "A3, A5, A6", 8, 10, 14, 20000, "Uniform", "Coordenador TIC"),
                   ("A8", "Sessões para encarregados de educação", "", "Support - Communication", "A3", 2, 3, 4, 4000, "Uniform", "Direção"),
                   ("A9", "Monitorização e avaliação", "", "Support - M&E", "A7", 2, 3, 4, 6000, "Milestone 50/50", "Coordenador TIC"),
                   ("A10", "Coordenação do projeto", "", "Support - Management", "", 34, 34, 34, 30000, "Uniform", "Coordenador TIC")],
    "progress": {"A1": (1.0, 8500), "A2": (1.0, 205000), "A4": (1.0, 2800), "A5": (0.35, 23000), "A6": (0.3, 12000), "A10": (0.45, 14000), "A3": (0.2, 6000)},
    "drift": (0.93, 1.02),
    "roles": ["Coordenador TIC", "Técnico TIC", "Direção", "Centro de formação", "Município"],
    "risks": [("R1", "Project/programme delivery", "Atraso no concurso público de equipamentos", 3, 3, 4, "Planeamento antecipado", "Lotes separados; acordo-quadro", "Técnico TIC", "Direção", "Semana 10", "H1", "Output", "Reduce", 5000, ""),
              ("R2", "Human resources", "Baixa adesão dos professores à formação", 2, 4, 4, "Créditos de formação", "Formação em horário letivo; mentores", "Coordenador TIC", "Direção", "Trimestral", "H2", "Outcome", "Reduce", 3000, ""),
              ("R3", "IT", "Falhas de conectividade nas escolas rurais", 3, 2, 4, "—", "Routers 5G de contingência", "Técnico TIC", "Município", "Mensal", "H1", "Output", "Reduce", 4000, "")],
    "budget": [("A2", "Equipment", "Portáteis para alunos", "unidade", 600, 280, "Implementation"), ("A2", "Equipment", "Ecrãs interativos", "unidade", 36, 1150, "Implementation")],
    "procurement": [("Q1", "Portáteis e ecrãs interativos", "Goods", "A2", 209400, "Competitive Bidding", "2027-10-15", "Técnico TIC", "Preço, garantia, assistência local", "Atraso (R1)"),
                    ("Q2", "Formação acreditada", "Services", "A5", 60000, "Request for Quotations (RFQ)", "2027-10-01", "Coordenador TIC", "Acreditação, experiência", "—")],
    "finance": {"equity": 1.0, "debt": 0.0, "ke_method": "direct", "ke": 0.04, "tax": 0.0},
    "benefits": [(1, 15000, 90000), (2, 20000, 120000), (3, 20000, 130000), (4, 20000, 130000), (5, 20000, 130000)],
    "evaluation": [("Effectiveness", "As práticas pedagógicas mudaram?", "I2 ≥ 50%", "I2", "Sumários; observação de aulas", "Observação"),
                   ("Sustainability", "Os equipamentos são mantidos após o projeto?", "Plano de manutenção financiado", "% equipamentos operacionais", "Inventário", "Análise documental")],
}

# =============================================================================== 3. HEALTH
HEALTH = {
    "meta": {"name": "Telemonitorização de doentes crónicos", "industry": "Saúde", "organisation": "Unidade Local de Saúde (exemplo)",
             "sponsor": "Ministério da Saúde / PRR", "country": "Portugal", "manager": "Diretor clínico do projeto",
             "description": "Telemonitorização domiciliária de 1 000 doentes com insuficiência cardíaca e DPOC para reduzir internamentos evitáveis.",
             "start_date": "2027-03-01", "time_unit": "weeks", "duration_mode": "pert", "status_date": "2027-08-31",
             "target_duration": 52, "contingency_method": "risk", "contingency_pct": 0.1, "contingency_used": 6000, "bench_year": 2025},
    "policy": {"context": "Envelhecimento da população; pressão sobre urgências; SNS24 e centros de contacto em expansão.", "content": "Plano Estratégico Nacional para a Telessaúde.", "consequences": "Benefícios dependem da literacia digital dos doentes mais idosos."},
    "goals": [("Plano Estratégico Nacional para a Telessaúde", "Reduzir internamentos evitáveis em doenças crónicas", "Taxa de reinternamento a 30 dias (%)", "22% (2025)", "15% (2030)", "SNS – Portal da Transparência")],
    "stakeholders": [("Doentes com IC e DPOC", "Target group", 2, 5, "Supporter", "Empower", "1 000 doentes, média 74 anos", "Querem evitar internamentos", "Literacia digital baixa", "Kits simples e linha de apoio", "Adesão", "Menos internamentos"),
                     ("Enfermeiros de família", "Project partner", 4, 4, "Supporter", "Collaborate", "45 enfermeiros", "Carga de trabalho", "Capacidade elevada", "Protocolos e tempo dedicado", "Monitorização", "Melhor gestão"),
                     ("Médicos de medicina interna", "Project partner", 4, 3, "Neutral", "Involve", "Serviço hospitalar", "Responsabilidade clínica", "Céticos quanto a alarmes", "Algoritmos de triagem validados", "Validação clínica", "Menos urgências"),
                     ("Cuidadores informais", "Beneficiary", 1, 4, "Supporter", "Inform", "Familiares", "Sobrecarga", "Variável", "Formação de cuidadores", "Apoio em casa", "Tranquilidade")],
    "behaviour": [("Doentes com IC e DPOC", 4, 3, 2, 4, "Inquérito: 55% nunca usou tablet", "Formação presencial + cuidador")],
    "problems": [("E1", "Effect", "Internamentos e idas à urgência evitáveis", "", "Internamentos evitáveis reduzidos"),
                 ("P1", "Core problem", "Descompensações detetadas tardiamente", "E1", "Descompensações detetadas precocemente"),
                 ("C1", "Cause", "Ausência de monitorização domiciliária", "P1", "Monitorização domiciliária implementada"),
                 ("C2", "Cause", "Falta de protocolos clínicos de resposta", "P1", "Protocolos de resposta definidos"),
                 ("C3", "Cause", "Baixa literacia em autogestão da doença", "P1", "Doentes capacitados para autogestão")],
    "strategies": [("Telemonitorização integrada", "Kits + central + protocolos + capacitação", [5, 4, 4, 4, 3]), ("Só consultas telefónicas", "Contacto telefónico periódico", [3, 5, 3, 3, 4])],
    "selected": "Telemonitorização integrada",
    "objectives": [("IMP", "Impact", "Contribuir para reduzir internamentos evitáveis em doenças crónicas", ""), ("OC1", "Outcome", "Descompensações detetadas e tratadas precocemente", "IMP"),
                   ("1.1", "Output", "Plataforma e kits de telemonitorização operacionais", "OC1"), ("1.2", "Output", "Protocolos clínicos implementados", "OC1"), ("1.3", "Output", "Doentes e cuidadores capacitados", "OC1")],
    "indicators": [("I1", "IMP", "Taxa de reinternamento a 30 dias dos doentes acompanhados", "%", 22, 2026, 15, 2028, 20, "SClínico / BI da ULS", "Trimestral", "Diretor clínico"),
                   ("I2", "OC1", "Tempo médio entre alerta e contacto clínico", "horas", 48, 2026, 4, 2028, 12, "Plataforma", "Mensal", "Enfermagem"),
                   ("I3", "1.3", "% de doentes com adesão ≥ 80% às medições", "%", 0, 2026, 75, 2028, 61, "Plataforma", "Mensal", "Enfermagem")],
    "benchmarks": {"I1": [("Hospital A (telemonitorização)", 13), ("Hospital B", 16), ("Média nacional", 21)]},
    "series": {"I1": [(2022, 24), (2023, 23.5), (2024, 22.8), (2025, 22.3), (2026, 22)]},
    "assumptions": [("H1", "Operational", "1.1", "Fornecedor garante kits certificados (dispositivo médico) a tempo", "Possibly", "Mercado com 3 fornecedores certificados", 3),
                    ("H2", "Behavioural", "OC1", "Os doentes fazem as medições diárias", "Possibly", "Estudos-piloto: 70-80% de adesão", 3),
                    ("H3", "Political", "IMP", "Financiamento por doente telemonitorizado mantém-se no contrato-programa", "Possibly", "Portaria em vigor até 2028", 2)],
    "activities": [("A1", "Desenho dos protocolos clínicos", "1.2", "Production", "", 4, 6, 9, 30000, "Uniform", "Diretor clínico"),
                   ("A2", "Aquisição da plataforma e kits", "1.1", "Production", "", 8, 10, 16, 320000, "Milestone 50/50", "Serviço de compras"),
                   ("A3", "Integração com o processo clínico eletrónico", "1.1", "Production", "A2", 4, 6, 10, 60000, "Uniform", "Serviço de informática"),
                   ("A4", "Formação de enfermeiros e médicos", "1.2", "Production", "A1, A3", 2, 3, 4, 15000, "Uniform", "Enfermeiro gestor"),
                   ("A5", "Recrutamento e capacitação de doentes (vagas)", "1.3", "Production", "A4", 12, 16, 22, 70000, "Uniform", "Enfermeiro gestor"),
                   ("A6", "Operação da central de monitorização", "OC1", "Production", "A5", 20, 24, 26, 180000, "Uniform", "Enfermeiro gestor"),
                   ("A7", "Comunicação a doentes e cuidadores", "", "Support - Communication", "A3", 2, 3, 4, 8000, "Uniform", "Diretor clínico"),
                   ("A8", "Avaliação de resultados clínicos", "", "Support - M&E", "A6", 3, 4, 6, 20000, "End", "Diretor clínico")],
    "progress": {"A1": (1.0, 32000), "A2": (1.0, 318000), "A3": (0.6, 41000)},
    "drift": (0.97, 1.03),
    "roles": ["Diretor clínico", "Enfermeiro gestor", "Conselho de Administração", "Serviço de informática", "Serviço de compras"],
    "risks": [("R1", "Safety, security and logistics", "Violação de dados de saúde", 2, 4, 4, "RGPD, encarregado de proteção de dados", "Avaliação de impacto (AIPD) e testes de intrusão", "Serviço de informática", "Conselho de Administração", "Antes do arranque", "", "Outcome", "Reduce", 15000, ""),
              ("R2", "Project/programme delivery", "Baixa adesão dos doentes idosos às medições", 3, 3, 6, "—", "Envolver cuidadores; chamadas de reforço", "Enfermeiro gestor", "Diretor clínico", "Mensal", "H2", "Outcome", "Reduce", 10000, "A7"),
              ("R3", "IT", "Falhas de integração com o processo clínico", 3, 2, 4, "Testes", "Ambiente de testes e fase piloto", "Serviço de informática", "Diretor clínico", "Semana 20", "H1", "Output", "Reduce", 8000, "")],
    "procurement": [("Q1", "Plataforma e 1 000 kits de telemonitorização", "Goods", "A2", 320000, "Competitive Bidding", "2027-03-15", "Serviço de compras", "Certificação MDR, preço, interoperabilidade", "Atraso")],
    "finance": {"equity": 1.0, "debt": 0.0, "ke_method": "direct", "ke": 0.04, "tax": 0.0},
    "benefits": [(1, 60000, 250000), (2, 90000, 420000), (3, 90000, 450000), (4, 90000, 450000), (5, 90000, 450000)],
    "evaluation": [("Effectiveness", "Os reinternamentos diminuíram?", "I1 ≤ 15%", "I1", "BI da ULS", "Diferenças-em-diferenças"), ("Efficiency", "Custo por internamento evitado?", "< custo médio internamento", "€/internamento evitado", "Contabilidade analítica", "Custo-efetividade")],
}

# =============================================================================== 4. IT / ERP
IT = {
    "meta": {"name": "Implementação de sistema ERP", "industry": "Tecnologia", "organisation": "Empresa industrial (exemplo)", "sponsor": "Administração",
             "country": "Portugal", "manager": "Gestor de projeto ERP", "description": "Substituição de sistemas legados por um ERP integrado (finanças, compras, produção, vendas) em 12 meses.",
             "start_date": "2027-01-01", "time_unit": "months", "duration_mode": "pert", "status_date": "2027-05-31", "target_duration": 13,
             "contingency_method": "percent", "contingency_pct": 0.10, "contingency_used": 15000, "bench_year": 2025},
    "policy": {"context": "Sistemas legados sem suporte; crescimento de 30% em 3 anos.", "content": "Plano estratégico 2027-2029: excelência operacional e decisão baseada em dados.", "consequences": "Mudança organizacional relevante nos processos de compras e produção."},
    "goals": [("Plano estratégico 2027-2029", "Reduzir o ciclo order-to-cash e os custos administrativos", "Ciclo order-to-cash (dias)", "45", "30", "Relatórios de gestão")],
    "stakeholders": [("Administração", "Resource provider", 5, 4, "Supporter", "Consult", "Patrocinador", "Retorno do investimento", "Elevada", "Comité executivo mensal", "Financiamento", "Eficiência"),
                     ("Utilizadores-chave (key users)", "Target group", 3, 5, "Neutral", "Involve", "25 key users", "Receio da mudança", "Conhecem os processos", "Envolvimento no desenho e formação", "Conhecimento", "Menos trabalho manual"),
                     ("Integrador de ERP", "Project partner", 3, 5, "Supporter", "Collaborate", "Consultora externa", "Cumprir contrato", "Elevada", "Gestão contratual", "Know-how", "Receita"),
                     ("Clientes", "Beneficiary", 2, 2, "Neutral", "Inform", "B2B", "Entregas atempadas", "—", "Comunicação no go-live", "—", "Melhor serviço")],
    "behaviour": [("Utilizadores-chave (key users)", 3, 4, 3, 2, "Inquérito de prontidão para a mudança: 40% resistentes", "Plano de gestão da mudança e champions")],
    "problems": [("E1", "Effect", "Custos administrativos elevados", "", "Custos administrativos reduzidos"), ("E2", "Effect", "Decisões com dados atrasados", "", "Decisões com dados em tempo real"),
                 ("P1", "Core problem", "Processos fragmentados entre sistemas legados", "E1, E2", "Processos integrados num único sistema"),
                 ("C1", "Cause", "Sistemas sem integração", "P1", "ERP integrado implementado"), ("C2", "Cause", "Dados mestre inconsistentes", "P1", "Dados mestre limpos e migrados"),
                 ("C3", "Cause", "Utilizadores sem competências no novo modelo", "P1", "Utilizadores formados")],
    "strategies": [("ERP cloud standard", "Adotar boas práticas do ERP com poucas customizações", [4, 4, 5, 4, 3]), ("ERP on-premise customizado", "Customizar o ERP aos processos atuais", [4, 3, 2, 3, 4])],
    "selected": "ERP cloud standard",
    "objectives": [("IMP", "Impact", "Contribuir para a excelência operacional e o crescimento rentável", ""), ("OC1", "Outcome", "Processos integrados e utilizados no ERP", "IMP"),
                   ("1.1", "Output", "ERP configurado e testado", "OC1"), ("1.2", "Output", "Dados migrados", "OC1"), ("1.3", "Output", "Utilizadores formados", "OC1")],
    "indicators": [("I1", "IMP", "Ciclo order-to-cash", "dias", 45, 2026, 30, 2028, 44, "ERP – relatórios", "Mensal", "Diretor financeiro"),
                   ("I2", "OC1", "% de transações processadas no ERP", "%", 0, 2026, 95, 2027, 0, "ERP – logs", "Mensal", "Gestor de projeto ERP"),
                   ("I3", "1.3", "% utilizadores certificados", "%", 0, 2026, 90, 2027, 10, "LMS", "Mensal", "RH")],
    "benchmarks": {"I1": [("Concorrente A", 28), ("Concorrente B", 35), ("Média setor", 38)]},
    "series": {"I1": [(2023, 40), (2024, 42), (2025, 44), (2026, 45)]},
    "assumptions": [("H1", "Operational", "1.2", "Os donos dos dados limpam os dados mestre a tempo", "Possibly", "Auditoria de dados: 18% de duplicados", 2),
                    ("H2", "Behavioural", "OC1", "Os utilizadores abandonam as folhas de Excel paralelas", "Possibly", "Inquérito de prontidão", 2)],
    "activities": [("A1", "Diagnóstico e requisitos", "1.1", "Production", "", 1.5, 2, 3, 60000, "Uniform", "Gestor de projeto ERP"),
                   ("A2", "Desenho da solução (fit-gap)", "1.1", "Production", "A1", 1.5, 2, 3, 90000, "Uniform", "Integrador"),
                   ("A3", "Licenças e infraestrutura cloud", "1.1", "Production", "A2", 0.5, 1, 1.5, 250000, "Start", "Gestor de projeto ERP"),
                   ("A4", "Configuração e desenvolvimento", "1.1", "Production", "A3", 3, 4, 6, 420000, "Uniform", "Integrador"),
                   ("A5", "Limpeza e migração de dados", "1.2", "Production", "A2", 2, 3, 5, 110000, "Back-loaded", "Key users"),
                   ("A6", "Testes integrados e aceitação", "1.1", "Production", "A4, A5", 1.5, 2, 3, 80000, "Front-loaded", "Key users"),
                   ("A7", "Formação de utilizadores", "1.3", "Production", "A6", 1, 2, 2.5, 70000, "Milestone 50/50", "RH"),
                   ("A8", "Go-live e estabilização", "OC1", "Production", "A7", 1.5, 2, 3, 120000, "Uniform", "Integrador"),
                   ("A9", "Gestão do projeto e da mudança", "", "Support - Management", "", 13, 13, 13, 60000, "Uniform", "Gestor de projeto ERP")],
    "progress": {"A1": (1.0, 64000), "A2": (1.0, 97000), "A3": (1.0, 262000), "A4": (0.2, 98000), "A9": (0.4, 26000)},
    "drift": (0.96, 1.07),
    "roles": ["Gestor de projeto ERP", "Integrador", "Administração", "Key users", "RH"],
    "risks": [("R1", "IT", "Customizações excessivas atrasam a configuração", 3, 3, 4, "Princípio 'standard first'", "Comité de desenho aprova cada customização", "Gestor de projeto ERP", "Administração", "Mensal", "", "Output", "Avoid", 30000, ""),
              ("R2", "Human resources", "Resistência dos utilizadores à mudança", 3, 4, 6, "Comunicação interna", "Rede de champions; formação prática", "RH", "Administração", "Mensal", "H2", "Outcome", "Reduce", 20000, ""),
              ("R3", "Project/programme delivery", "Dados mestre com má qualidade comprometem a migração", 3, 3, 4, "—", "Ensaios de migração (3 ciclos)", "Key users", "Gestor de projeto ERP", "Mês 6", "H1", "Output", "Reduce", 25000, "")],
    "procurement": [("Q1", "Integrador ERP", "Services", "A4", 420000, "Request for Proposals (RFP)", "2026-11-01", "Administração", "Qualidade (60%), preço (40%)", "Dependência"),
                    ("Q2", "Licenças cloud (3 anos)", "Goods", "A3", 250000, "Sole Sourcing", "2027-04-01", "Gestor de projeto ERP", "Fabricante único", "Aumento de preços")],
    "finance": {"equity": 600000, "debt": 400000, "ke_method": "capm", "rf": 0.03, "beta": 1.1, "mrp": 0.06, "kd": 0.05, "tax": 0.21},
    "benefits": [(1, 120000, 300000), (2, 120000, 520000), (3, 120000, 600000), (4, 120000, 600000), (5, 120000, 600000)],
    "evaluation": [("Efficiency", "O ERP foi implementado no prazo e orçamento?", "CPI/SPI ≥ 0,95", "CPI, SPI", "EVM", "EVM"), ("Effectiveness", "O ciclo order-to-cash diminuiu?", "≤ 30 dias", "I1", "ERP", "Análise de séries")],
}

# =============================================================================== 5. CONSTRUCTION
CONSTR = {
    "meta": {"name": "Construção de centro comunitário", "industry": "Construção", "organisation": "Município (exemplo)", "sponsor": "Município + Portugal 2030",
             "country": "Portugal", "manager": "Diretor de obra", "description": "Construção de um centro comunitário de 1 800 m² com creche, centro de dia e salas polivalentes.",
             "start_date": "2027-04-01", "time_unit": "weeks", "duration_mode": "pert", "status_date": "2027-12-31", "target_duration": 66,
             "contingency_method": "percent", "contingency_pct": 0.12, "contingency_used": 40000, "bench_year": 2025},
    "policy": {"context": "Freguesia com população envelhecida e falta de respostas sociais.", "content": "Carta social municipal 2026-2030.", "consequences": "Criação de emprego local; custos de funcionamento futuros."},
    "goals": [("Carta social municipal", "Aumentar a cobertura de respostas sociais", "Taxa de cobertura de creche (%)", "45%", "75%", "Carta Social")],
    "stakeholders": [("Moradores da freguesia", "Beneficiary", 2, 4, "Supporter", "Consult", "8 000 habitantes", "Respostas sociais próximas", "—", "Sessões públicas", "Participação", "Serviços"),
                     ("Famílias com crianças e idosos", "Target group", 2, 5, "Supporter", "Involve", "≈ 300 famílias", "Conciliação trabalho-família", "—", "Inscrições e informação", "Utilização", "Creche e centro de dia"),
                     ("Empreiteiro", "Project partner", 4, 5, "Neutral", "Collaborate", "Adjudicatário", "Margem e prazo", "Elevada", "Reuniões semanais de obra", "Execução", "Contrato"),
                     ("Vizinhos da obra", "Other (specify)", 2, 3, "Opponent", "Inform", "Prédios adjacentes", "Ruído e trânsito", "Podem apresentar queixas", "Horários e plano de comunicação", "—", "Valorização do bairro")],
    "behaviour": [("Famílias com crianças e idosos", 4, 3, 4, 4, "Inquérito às famílias", "Política de preços sociais")],
    "problems": [("E1", "Effect", "Famílias sem resposta social de proximidade", "", "Famílias com resposta social de proximidade"),
                 ("P1", "Core problem", "Falta de equipamento social na freguesia", "E1", "Equipamento social disponível na freguesia"),
                 ("C1", "Cause", "Ausência de edifício adequado", "P1", "Edifício construído e licenciado"), ("C2", "Cause", "Falta de equipamento interior", "P1", "Edifício equipado")],
    "strategies": [("Construção nova", "Edifício novo em terreno municipal", [5, 4, 3, 4, 4]), ("Reabilitação de escola desativada", "Reabilitar edifício existente", [4, 3, 4, 3, 4])],
    "selected": "Construção nova",
    "objectives": [("IMP", "Impact", "Contribuir para aumentar a cobertura de respostas sociais no município", ""), ("OC1", "Outcome", "Centro comunitário em funcionamento", "IMP"),
                   ("1.1", "Output", "Edifício construído e licenciado", "OC1"), ("1.2", "Output", "Edifício equipado", "OC1")],
    "indicators": [("I1", "IMP", "Taxa de cobertura de creche na freguesia", "%", 45, 2026, 75, 2029, 45, "Carta Social", "Anual", "Ação social"),
                   ("I2", "1.1", "% de execução física da obra", "%", 0, 2027, 100, 2028, 32, "Autos de medição", "Mensal", "Diretor de obra")],
    "benchmarks": {"I1": [("Freguesia vizinha", 68), ("Média municipal", 58), ("Média nacional", 50)]},
    "assumptions": [("H1", "Operational", "1.1", "Licenciamentos emitidos sem atrasos", "Possibly", "Prazos médios de licenciamento: 60 dias", 2),
                    ("H2", "Behavioural", "OC1", "As famílias inscrevem-se nos serviços", "Almost certainly", "Lista de espera com 180 inscrições", 4)],
    "activities": [("A1", "Projeto de execução e licenciamento", "1.1", "Production", "", 8, 10, 14, 90000, "Uniform", "Diretor de obra"),
                   ("A2", "Concurso e adjudicação da empreitada", "1.1", "Production", "A1", 6, 8, 12, 5000, "Uniform", "Diretor de obra"),
                   ("A3", "Estaleiro, movimentos de terras e fundações", "1.1", "Production", "A2", 6, 8, 11, 280000, "Uniform", "Empreiteiro"),
                   ("A4", "Estrutura em betão armado", "1.1", "Production", "A3", 10, 12, 16, 520000, "Uniform", "Empreiteiro"),
                   ("A5", "Cobertura e fachadas", "1.1", "Production", "A4", 6, 8, 10, 260000, "Uniform", "Empreiteiro"),
                   ("A6", "Instalações especiais (AVAC, elétrica, águas)", "1.1", "Production", "A4", 8, 10, 14, 330000, "Back-loaded", "Empreiteiro"),
                   ("A7", "Acabamentos interiores", "1.1", "Production", "A5, A6", 6, 8, 11, 240000, "Uniform", "Empreiteiro"),
                   ("A8", "Equipamento e mobiliário", "1.2", "Production", "A7", 2, 3, 5, 150000, "End", "Diretor de obra"),
                   ("A9", "Receção provisória e licença de utilização", "OC1", "Production", "A8", 2, 3, 6, 8000, "End", "Diretor de obra"),
                   ("A10", "Fiscalização e coordenação de segurança", "", "Support - Management", "A2", 42, 44, 46, 95000, "Uniform", "Fiscalização")],
    "progress": {"A1": (1.0, 95000), "A2": (1.0, 5000), "A3": (1.0, 305000), "A4": (0.25, 150000), "A10": (0.3, 30000)},
    "drift": (0.92, 1.08),
    "roles": ["Diretor de obra", "Empreiteiro", "Município", "Fiscalização", "Projetista"],
    "risks": [("R1", "Project/programme delivery", "Condições geotécnicas imprevistas", 2, 4, 4, "Estudo geotécnico", "Sondagens adicionais antes das fundações", "Diretor de obra", "Município", "Antes de A3", "", "Output", "Reduce", 60000, ""),
              ("R2", "Financial", "Revisão de preços dos materiais", 3, 3, 6, "Cláusula de revisão de preços", "Encomenda antecipada do aço", "Diretor de obra", "Município", "Mensal", "", "Output", "Transfer", 50000, ""),
              ("R3", "Safety, security and logistics", "Acidente de trabalho em obra", 2, 4, 4, "PSS aprovado", "Inspeções semanais de segurança", "Fiscalização", "Empreiteiro", "Semanal", "", "Output", "Reduce", 10000, "A10")],
    "procurement": [("Q1", "Empreitada de construção (A3–A7)", "Works", "", 1630000, "Competitive Bidding", "2027-07-01", "Município", "Preço (60%), prazo (20%), valia técnica (20%)", "Erros e omissões"),
                    ("Q2", "Mobiliário e equipamento", "Goods", "A8", 150000, "Competitive Bidding", "2028-03-01", "Diretor de obra", "Preço, ergonomia, prazo", "—")],
    "finance": {"equity": 1.0, "debt": 0.0, "ke_method": "direct", "ke": 0.035, "tax": 0.0},
    "benefits": [(2, 180000, 420000), (3, 220000, 520000), (4, 220000, 540000), (5, 220000, 540000), (6, 220000, 540000), (7, 220000, 540000), (8, 220000, 540000), (9, 220000, 540000), (10, 220000, 540000)],
    "evaluation": [("Relevance", "O centro responde às necessidades das famílias?", "Lista de espera absorvida", "Taxa de ocupação", "Registos", "Análise documental")],
}

# =============================================================================== 6. AEROSPACE MRO
AERO = {
    "meta": {"name": "Nova linha de manutenção de motores (MRO)", "industry": "Indústria aeronáutica", "organisation": "Empresa de MRO (exemplo)", "sponsor": "Conselho de Administração",
             "country": "Portugal", "manager": "Gestor de programa", "description": "Criação de uma linha de manutenção para um novo modelo de motor: hangar, ferramentas, certificação EASA Parte 145 e formação de técnicos.",
             "start_date": "2027-02-01", "time_unit": "weeks", "duration_mode": "pert", "status_date": "2027-10-31", "target_duration": 56,
             "contingency_method": "percent", "contingency_pct": 0.10, "contingency_used": 120000, "bench_year": 2025},
    "policy": {"context": "Procura crescente de manutenção do novo motor; concorrência internacional; escassez de técnicos certificados.", "content": "Estratégia industrial da empresa 2027-2031 e Agenda de Inovação Aeronáutica.", "consequences": "Emprego qualificado; dependência do fabricante (OEM)."},
    "goals": [("Estratégia industrial 2027-2031", "Diversificar a carteira de motores e crescer 40% em receitas de MRO", "Receitas de MRO (M€)", "180", "250", "Relatório e contas")],
    "stakeholders": [("Fabricante do motor (OEM)", "Resource provider", 5, 4, "Supporter", "Collaborate", "Licenciador da manutenção", "Rede de MRO autorizada", "Elevada", "Acordo de licença e formação", "Dados técnicos e ferramentas", "Capacidade de rede"),
                     ("EASA / ANAC", "Other (specify)", 5, 3, "Neutral", "Consult", "Autoridade aeronáutica", "Segurança", "Elevada", "Plano de certificação acordado", "Certificação", "Conformidade"),
                     ("Técnicos de manutenção", "Target group", 3, 5, "Supporter", "Empower", "60 técnicos", "Carreira", "Lacuna no novo motor", "Formação tipo B1/B2", "Execução", "Qualificação"),
                     ("Companhias aéreas clientes", "Beneficiary", 4, 4, "Supporter", "Consult", "6 operadores", "TAT curto", "—", "Contratos de manutenção", "Receita", "Menos tempo em terra")],
    "behaviour": [("Técnicos de manutenção", 4, 4, 2, 4, "Matriz de competências: 15% qualificados no novo motor", "Formação OEM + on-job training")],
    "problems": [("E1", "Effect", "Perda de quota de mercado em MRO de motores", "", "Quota de mercado de MRO aumentada"),
                 ("P1", "Core problem", "Ausência de capacidade para o novo modelo de motor", "E1", "Capacidade para o novo motor criada"),
                 ("C1", "Cause", "Hangar e ferramentas inadequados", "P1", "Hangar e ferramentas adequados"), ("C2", "Cause", "Falta de certificação", "P1", "Linha certificada EASA Parte 145"),
                 ("C3", "Cause", "Técnicos sem qualificação no novo motor", "P1", "Técnicos qualificados")],
    "strategies": [("Linha própria completa", "Investimento integral com licença OEM", [5, 4, 4, 4, 4]), ("Parceria com MRO estrangeiro", "Subcontratar módulos", [3, 5, 3, 2, 3])],
    "selected": "Linha própria completa",
    "objectives": [("IMP", "Impact", "Contribuir para o crescimento e diversificação das receitas de MRO", ""), ("OC1", "Outcome", "Motores do novo modelo reparados com TAT competitivo", "IMP"),
                   ("1.1", "Output", "Hangar adaptado e ferramentas instaladas", "OC1"), ("1.2", "Output", "Linha certificada EASA Parte 145", "OC1"), ("1.3", "Output", "Técnicos qualificados", "OC1")],
    "indicators": [("I1", "IMP", "Receitas de MRO", "M€", 180, 2026, 250, 2031, 182, "Relatório e contas", "Anual", "Administração"),
                   ("I2", "OC1", "Turnaround time (TAT) médio", "dias", 0, 2027, 55, 2029, 0, "ERP de manutenção", "Mensal", "Gestor de programa"),
                   ("I3", "1.3", "N.º de técnicos qualificados no novo motor", "técnicos", 9, 2026, 45, 2028, 21, "Registos de formação", "Trimestral", "Formação")],
    "benchmarks": {"I2": [("MRO concorrente A", 50), ("MRO concorrente B", 62), ("Oficina do OEM", 45)]},
    "assumptions": [("H1", "Operational", "1.1", "O OEM entrega as ferramentas especiais no prazo", "Possibly", "Lead time histórico 20-30 semanas", 2),
                    ("H2", "Behavioural", "OC1", "Os clientes enviam os motores para a nova linha", "Possibly", "Cartas de intenção de 4 operadores", 3),
                    ("H3", "Political", "IMP", "Não há restrições de exportação/certificação ao motor", "Almost certainly", "Motor certificado na UE", 4)],
    "activities": [("A1", "Acordo de licença com o OEM", "1.2", "Production", "", 6, 8, 12, 400000, "Start", "Gestor de programa"),
                   ("A2", "Projeto de adaptação do hangar", "1.1", "Production", "", 4, 6, 8, 120000, "Uniform", "Engenharia"),
                   ("A3", "Obras de adaptação do hangar", "1.1", "Production", "A2", 14, 18, 26, 2600000, "Uniform", "Engenharia"),
                   ("A4", "Aquisição de ferramentas especiais e banco de ensaio", "1.1", "Production", "A1", 20, 24, 32, 4200000, "Milestone 50/50", "Compras"),
                   ("A5", "Formação de técnicos (OEM + on-job)", "1.3", "Production", "A1", 16, 20, 26, 900000, "Uniform", "Formação"),
                   ("A6", "Manual da organização e procedimentos (MOE)", "1.2", "Production", "A1", 6, 8, 10, 150000, "Uniform", "Qualidade"),
                   ("A7", "Instalação e calibração das ferramentas", "1.1", "Production", "A3, A4", 4, 6, 9, 350000, "Uniform", "Engenharia"),
                   ("A8", "Auditoria e certificação EASA Parte 145", "1.2", "Production", "A5, A6, A7", 4, 6, 10, 80000, "End", "Qualidade"),
                   ("A9", "Primeiro motor (piloto) e lições aprendidas", "OC1", "Production", "A8", 6, 8, 12, 250000, "Uniform", "Gestor de programa"),
                   ("A10", "Gestão do programa", "", "Support - Management", "", 50, 52, 53, 300000, "Uniform", "Gestor de programa")],
    "progress": {"A1": (1.0, 400000), "A2": (1.0, 128000), "A3": (0.45, 1300000), "A4": (0.5, 2150000), "A5": (0.4, 390000), "A6": (0.7, 120000), "A10": (0.5, 160000)},
    "drift": (0.97, 1.04),
    "roles": ["Gestor de programa", "Engenharia", "Conselho de Administração", "Compras", "Qualidade", "Formação"],
    "risks": [("R1", "Project/programme delivery", "Atraso na entrega das ferramentas especiais pelo OEM", 3, 4, 6, "Encomenda antecipada", "Penalizações contratuais; aluguer temporário", "Compras", "Gestor de programa", "Mensal", "H1", "Output", "Reduce", 300000, ""),
              ("R2", "Human resources", "Saída de técnicos qualificados para a concorrência", 3, 3, 4, "Pacto de permanência", "Plano de carreira e retenção", "Formação", "Conselho de Administração", "Trimestral", "", "Output", "Reduce", 150000, ""),
              ("R3", "Political", "Novos requisitos regulamentares atrasam a certificação", 2, 3, 4, "Contacto com a ANAC", "Pré-auditoria", "Qualidade", "Gestor de programa", "Antes de A8", "", "Output", "Reduce", 50000, "")],
    "procurement": [("Q1", "Ferramentas especiais e banco de ensaio", "Goods", "A4", 4200000, "Sole Sourcing", "2027-04-01", "Compras", "Fornecedor aprovado pelo OEM", "Atraso (R1)"),
                    ("Q2", "Empreitada de adaptação do hangar", "Works", "A3", 2600000, "Competitive Bidding", "2027-04-15", "Engenharia", "Preço, prazo, experiência aeronáutica", "Derrapagem")],
    "finance": {"equity": 6000000, "debt": 4000000, "ke_method": "capm", "rf": 0.03, "beta": 1.25, "mrp": 0.065, "kd": 0.055, "tax": 0.21, "residual_value": 2000000},
    "benefits": [(1, 600000, 1500000), (2, 3500000, 6500000), (3, 4500000, 8000000), (4, 5000000, 9000000), (5, 5000000, 9000000), (6, 5000000, 9000000), (7, 5000000, 9000000)],
    "evaluation": [("Effectiveness", "A linha atinge o TAT competitivo?", "TAT ≤ 55 dias", "I2", "ERP de manutenção", "Análise de séries"), ("Impact", "As receitas de MRO cresceram?", "+40% até 2031", "I1", "Relatório e contas", "Análise financeira")],
}

_DATA = {"trade": TRADE, "education": EDU, "health": HEALTH, "it": IT, "construction": CONSTR, "aero": AERO}


def build_demo(key: str) -> dict:
    return _compile(copy.deepcopy(_DATA[key]))
