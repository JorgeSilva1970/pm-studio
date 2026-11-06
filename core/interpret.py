"""Rule-based interpretive reports (work without any AI key) and cross-module consistency checks."""
from __future__ import annotations

import math

from . import analysis as AN
from .cpm import parse_preds
from .fmt import d, money, num, pct, unit_label
from .i18n import opt_label, tr
from .model import activity_cost, expected_assumption_type, objective_level


# ----------------------------------------------------------------------------- schedule
def cpm_text(sched: dict) -> str:
    if not sched.get("ok"):
        return ""
    res, df, u = sched["cpm"], sched["acts"], unit_label(sched["unit"])
    cp = " → ".join(res["critical_path"])
    ncrit = int(df["critical"].sum())
    slack = df[~df["critical"]].sort_values("TF", ascending=False)
    txt = tr(
        f"O projeto tem **{len(df)} atividades** e uma duração mínima de **{num(res['duration'], 1)} {u}** "
        f"(início {d(sched['start'])}, fim previsto {d(sched['finish'])}). O **caminho crítico** é **{cp}** "
        f"({ncrit} atividades com folga total zero): qualquer atraso numa destas atividades atrasa o projeto no mesmo valor.",
        f"The project has **{len(df)} activities** and a minimum duration of **{num(res['duration'], 1)} {u}** "
        f"(start {d(sched['start'])}, planned finish {d(sched['finish'])}). The **critical path** is **{cp}** "
        f"({ncrit} activities with zero total float): any delay in one of them delays the whole project by the same amount.")
    if len(res.get("paths", [])) > 1:
        txt += tr(f" Existem **{len(res['paths'])} caminhos críticos** em paralelo — o risco de prazo é maior.",
                  f" There are **{len(res['paths'])} parallel critical paths** — schedule risk is higher.")
    if len(slack):
        top = slack.iloc[0]
        txt += tr(f" A atividade com mais margem é **{top['id']}** ({num(top['TF'], 1)} {u} de folga total), que pode ser adiada ou ceder recursos às críticas.",
                  f" The activity with most slack is **{top['id']}** ({num(top['TF'], 1)} {u} of total float); it can be delayed or lend resources to critical ones.")
    near = df[(~df["critical"]) & (df["TF"] <= 0.1 * max(res["duration"], 1))]
    if len(near):
        txt += tr(f" Atenção às atividades **quase críticas** ({', '.join(near['id'])}), com folga inferior a 10% da duração do projeto.",
                  f" Watch the **near-critical** activities ({', '.join(near['id'])}), with float below 10% of the project duration.")
    return txt


def pert_text(pp: dict, target: float | None, prob: float | None, unit: str) -> str:
    u = unit_label(unit)
    txt = tr(f"Pelo método PERT, a duração esperada é **{num(pp['mean'], 1)} {u}** com desvio-padrão **{num(pp['sd'], 2)} {u}** "
             f"(soma das variâncias do caminho crítico {' → '.join(pp['path'])}).",
             f"Using PERT, the expected duration is **{num(pp['mean'], 1)} {u}** with standard deviation **{num(pp['sd'], 2)} {u}** "
             f"(sum of the variances along the critical path {' → '.join(pp['path'])}).")
    if target and prob is not None:
        txt += tr(f" A probabilidade de concluir em **{num(target, 1)} {u}** é **{pct(prob)}**",
                  f" The probability of finishing within **{num(target, 1)} {u}** is **{pct(prob)}**")
        txt += tr(" — um prazo confortável." if prob >= 0.85 else " — um prazo razoável, mas convém reforçar margens." if prob >= 0.5 else " — prazo **pouco realista**: rever durações, recursos ou âmbito.",
                  " — a comfortable deadline." if prob >= 0.85 else " — reasonable, but buffers should be reinforced." if prob >= 0.5 else " — an **unrealistic** deadline: review durations, resources or scope.")
    return txt


def mc_text(mc: dict, unit: str, target: float | None, pert_mean: float) -> str:
    u = unit_label(unit)
    p = mc["percentiles"]
    txt = tr(f"Na simulação de Monte Carlo a duração média é **{num(mc['mean'], 1)} {u}**; há 50% de probabilidade de terminar até **{num(p['P50'], 1)}**, "
             f"80% até **{num(p['P80'], 1)}** e 90% até **{num(p['P90'], 1)} {u}**.",
             f"In the Monte Carlo simulation the mean duration is **{num(mc['mean'], 1)} {u}**; there is a 50% chance of finishing by **{num(p['P50'], 1)}**, "
             f"80% by **{num(p['P80'], 1)}** and 90% by **{num(p['P90'], 1)} {u}**.")
    if mc["mean"] > pert_mean * 1.01:
        txt += tr(f" A média simulada é superior à estimativa PERT ({num(pert_mean, 1)}): caminhos não críticos em paralelo também podem tornar-se críticos (efeito de fusão).",
                  f" The simulated mean exceeds the PERT estimate ({num(pert_mean, 1)}): parallel non-critical paths can also become critical (merge bias).")
    crit = sorted(mc["criticality"].items(), key=lambda kv: -kv[1])
    shaky = [k for k, v in crit if 0.2 <= v < 0.95]
    if shaky:
        txt += tr(f" Atividades com criticidade intermédia (podem ou não ser críticas): **{', '.join(shaky[:8])}**.",
                  f" Activities with intermediate criticality (may or may not be critical): **{', '.join(shaky[:8])}**.")
    if target:
        import numpy as np
        pr = float((mc["samples"] <= target).mean())
        txt += tr(f" Probabilidade simulada de cumprir {num(target, 1)} {u}: **{pct(pr)}**.",
                  f" Simulated probability of meeting {num(target, 1)} {u}: **{pct(pr)}**.")
    return txt


def crash_text(r: dict, normal: float, unit: str, cur: str) -> str:
    u = unit_label(unit)
    if not r.get("feasible"):
        return tr("Não é possível atingir esse prazo mesmo comprimindo todas as atividades até à duração mínima (crash).",
                  "That deadline cannot be met even crashing every activity to its minimum duration.")
    red = {k: v for k, v in r["reductions"].items() if v > 1e-6}
    lst = ", ".join(f"{k} (−{num(v, 1)})" for k, v in red.items()) or "—"
    return tr(f"Para reduzir o projeto de {num(normal, 1)} para **{num(r['duration'], 1)} {u}**, a solução de custo mínimo comprime: {lst}. "
              f"Custo adicional: **{money(r['extra_cost'], cur)}**. Comprimem-se primeiro as atividades críticas com menor custo por unidade de tempo (declive).",
              f"To cut the project from {num(normal, 1)} to **{num(r['duration'], 1)} {u}**, the minimum-cost solution crashes: {lst}. "
              f"Extra cost: **{money(r['extra_cost'], cur)}**. Critical activities with the lowest cost slope are crashed first.")


# ----------------------------------------------------------------------------- EVM
def evm_text(e: dict, cur: str) -> str:
    if not e:
        return ""
    cpi, spi = e["CPI"], e["SPI"]
    ok_c = cpi == cpi and cpi >= 1
    ok_s = spi == spi and spi >= 1
    txt = tr(f"Na data de controlo ({d(e['status'])}), foi planeado gastar **{money(e['PV'], cur)}** (PV), o trabalho realizado vale **{money(e['EV'], cur)}** (EV) "
             f"e o custo real é **{money(e['AC'], cur)}** (AC). ",
             f"At the status date ({d(e['status'])}), planned spending was **{money(e['PV'], cur)}** (PV), work performed is worth **{money(e['EV'], cur)}** (EV) "
             f"and actual cost is **{money(e['AC'], cur)}** (AC). ")
    if cpi == cpi:
        txt += tr(f"O projeto está **{'dentro' if ok_c else 'acima'} do orçamento** (CPI = {num(cpi, 2)}: cada € gasto produz {num(cpi, 2)} € de trabalho; CV = {money(e['CV'], cur)}) ",
                  f"The project is **{'within' if ok_c else 'over'} budget** (CPI = {num(cpi, 2)}: each € spent yields {num(cpi, 2)} € of work; CV = {money(e['CV'], cur)}) ")
    if spi == spi:
        txt += tr(f"e **{'em linha ou adiantado' if ok_s else 'atrasado'}** face ao plano (SPI = {num(spi, 2)}; SV = {money(e['SV'], cur)}). ",
                  f"and **{'on or ahead of' if ok_s else 'behind'} schedule** (SPI = {num(spi, 2)}; SV = {money(e['SV'], cur)}). ")
    txt += tr(f"Se a eficiência atual se mantiver, o custo final previsto (EAC) é **{money(e['EAC'], cur)}** face ao orçamento (BAC) de {money(e['BAC'], cur)} "
              f"(VAC = {money(e['VAC'], cur)}). ",
              f"If current efficiency persists, the estimate at completion (EAC) is **{money(e['EAC'], cur)}** against a budget (BAC) of {money(e['BAC'], cur)} "
              f"(VAC = {money(e['VAC'], cur)}). ")
    if e["TCPI"] == e["TCPI"]:
        txt += tr(f"Para cumprir o BAC, o trabalho restante teria de ser executado com eficiência {num(e['TCPI'], 2)} (TCPI)"
                  + (" — **difícil de recuperar**." if e["TCPI"] > 1.1 else "."),
                  f"To meet the BAC, remaining work must be performed at an efficiency of {num(e['TCPI'], 2)} (TCPI)"
                  + (" — **hard to recover**." if e["TCPI"] > 1.1 else "."))
    if e["contingency"]:
        over = e["EAC"] - e["BAC"]
        if over > 0:
            cover = e["contingency_left"] >= over
            txt += tr(f" A derrapagem prevista ({money(over, cur)}) {'é coberta' if cover else '**excede**'} a contingência disponível ({money(e['contingency_left'], cur)}).",
                      f" The forecast overrun ({money(over, cur)}) {'is covered by' if cover else '**exceeds**'} the remaining contingency ({money(e['contingency_left'], cur)}).")
    if spi == spi and spi < 1:
        txt += tr(f" Mantendo o ritmo (SPI), o fim estimado desliza para **{d(e['finish_forecast'])}**.",
                  f" At the current pace (SPI), the estimated finish slips to **{d(e['finish_forecast'])}**.")
    return txt


def cost_text(sched: dict, cur: str) -> str:
    per = sched["periods"]
    if per.empty:
        return ""
    peak = per.loc[per["pv"].idxmax()]
    half = per[per["pv_cum"] >= sched["bac"] / 2]
    txt = tr(f"O orçamento das atividades (BAC) é **{money(sched['bac'], cur)}**, distribuído por {len(per)} períodos. "
             f"O pico de despesa ocorre em **{peak['period']}** ({money(peak['pv'], cur)}).",
             f"The activity budget (BAC) is **{money(sched['bac'], cur)}**, spread over {len(per)} periods. "
             f"Peak spending happens in **{peak['period']}** ({money(peak['pv'], cur)}).")
    if len(half):
        txt += tr(f" Metade do orçamento estará consumida em **{half.iloc[0]['period']}**.",
                  f" Half of the budget will be consumed by **{half.iloc[0]['period']}**.")
    if sched.get("contingency"):
        txt += tr(f" A reserva de contingência é de **{money(sched['contingency'], cur)}** ({pct(sched['contingency'] / sched['bac'] if sched['bac'] else 0)} do BAC), "
                  f"pelo que o orçamento total é {money(sched['bac'] + sched['contingency'], cur)}.",
                  f" The contingency reserve is **{money(sched['contingency'], cur)}** ({pct(sched['contingency'] / sched['bac'] if sched['bac'] else 0)} of BAC), "
                  f"so the total budget is {money(sched['bac'] + sched['contingency'], cur)}.")
    return txt


# ----------------------------------------------------------------------------- finance
def finance_text(a: dict, cur: str, be: float | None = None) -> str:
    if not a:
        return ""
    v, irr, mirr, rate = a["npv"], a["irr"], a["mirr"], a["rate"]
    txt = tr(f"Descontando os fluxos à taxa de **{pct(rate, 2)}** (WACC), o **VAL é {money(v, cur)}**",
             f"Discounting the flows at **{pct(rate, 2)}** (WACC), the **NPV is {money(v, cur)}**")
    txt += tr(" — o projeto **cria valor**." if v > 0 else " — o projeto **destrói valor** nas condições atuais." if v < 0 else " — o projeto está no ponto de indiferença.",
              " — the project **creates value**." if v > 0 else " — the project **destroys value** under current assumptions." if v < 0 else " — the project is at break-even.")
    if irr is not None:
        txt += tr(f" A **TIR é {pct(irr, 2)}**, {'superior' if irr > rate else 'inferior'} ao custo do capital ({pct(rate, 2)}).",
                  f" The **IRR is {pct(irr, 2)}**, {'above' if irr > rate else 'below'} the cost of capital ({pct(rate, 2)}).")
    if mirr is not None:
        txt += tr(f" A **TIR modificada (MIRR) é {pct(mirr, 2)}** — mais realista que a TIR por assumir reinvestimento à taxa de {pct(a['reinvest_rate'], 2)} e financiamento a {pct(a['finance_rate'], 2)}.",
                  f" The **modified IRR (MIRR) is {pct(mirr, 2)}** — more realistic than the IRR as it assumes reinvestment at {pct(a['reinvest_rate'], 2)} and financing at {pct(a['finance_rate'], 2)}.")
    if irr is not None and mirr is not None and abs(irr - mirr) > 0.03:
        txt += tr(" A diferença entre TIR e MIRR é relevante: a TIR sobrestima a rendibilidade.",
                  " The gap between IRR and MIRR is material: the IRR overstates profitability.")
    if a.get("payback") is not None:
        txt += tr(f" O investimento é recuperado em **{num(a['payback'], 1)} anos** (payback simples) e em {num(a['disc_payback'], 1) if a.get('disc_payback') is not None else '—'} anos (payback atualizado).",
                  f" The investment is recovered in **{num(a['payback'], 1)} years** (simple payback) and {num(a['disc_payback'], 1) if a.get('disc_payback') is not None else '—'} years (discounted payback).")
    else:
        txt += tr(" O investimento não é recuperado dentro do horizonte analisado.", " The investment is not recovered within the horizon analysed.")
    if a.get("pi"):
        txt += tr(f" Índice de rendibilidade: {num(a['pi'], 2)}.", f" Profitability index: {num(a['pi'], 2)}.")
    if be is not None and v > 0:
        txt += tr(f" Os benefícios podem cair até **{pct(1 - be)}** antes de o VAL se anular (margem de segurança).",
                  f" Benefits can fall by up to **{pct(1 - be)}** before NPV reaches zero (safety margin).")
    return txt


# ----------------------------------------------------------------------------- analytical tools
def stakeholder_text(rows: list[dict]) -> str:
    if not rows:
        return ""
    close = [r["name"] for r in rows if int(r.get("influence") or 0) >= 3 and int(r.get("interest") or 0) >= 3]
    opp = [r["name"] for r in rows if r.get("attitude") == "Opponent" and int(r.get("influence") or 0) >= 3]
    tg = [r["name"] for r in rows if r.get("type") == "Target group"]
    txt = tr(f"Foram identificados **{len(rows)} stakeholders**, dos quais {len(tg)} grupo(s)-alvo. ", f"**{len(rows)} stakeholders** were identified, {len(tg)} of them target group(s). ")
    if close:
        txt += tr(f"Devem ser **geridos de perto** (alta influência e interesse): {', '.join(close)}. ", f"To be **managed closely** (high influence and interest): {', '.join(close)}. ")
    if opp:
        txt += tr(f"⚠️ Opositores influentes — quem beneficia do problema tem baixa motivação para a mudança: **{', '.join(opp)}**; prever ações para controlar a resistência.",
                  f"⚠️ Influential opponents — those taking advantage of the problem have low motivation to change: **{', '.join(opp)}**; plan actions to contain resistance.")
    if not tg:
        txt += tr(" Não há nenhum grupo-alvo definido.", " No target group has been defined.")
    return txt


def behaviour_text(rows: list[dict]) -> str:
    out = []
    names = {"perception": tr("perceção", "perception"), "opportunity": tr("oportunidade", "opportunity"),
             "ability": tr("capacidade", "ability"), "motivation": tr("motivação", "motivation")}
    for r in rows:
        weak = [names[k] for k in names if int(r.get(k) or 3) <= 2]
        if weak:
            out.append(tr(f"**{r['target_group']}**: fragilidades em {', '.join(weak)} — são pressupostos comportamentais em risco; incluir atividades de apoio (ex.: comunicação, formação, acesso).",
                          f"**{r['target_group']}**: weaknesses in {', '.join(weak)} — behavioural assumptions at risk; add support activities (e.g., communication, training, access)."))
        else:
            out.append(tr(f"**{r['target_group']}**: padrões comportamentais favoráveis à utilização dos outputs.",
                          f"**{r['target_group']}**: behavioural patterns favour the use of the outputs."))
    return " ".join(out)


def risk_text(risks: list[dict]) -> str:
    if not risks:
        return ""
    ex = sorted(risks, key=lambda r: -AN.exposure(r))
    crit = [r for r in risks if AN.exposure(r) >= 12]
    high = [r for r in risks if 8 <= AN.exposure(r) < 12]
    above = [r for r in risks if AN.exposure(r) > int(r.get("target_exposure") or 16)]
    txt = tr(f"Registo com **{len(risks)} riscos**: {len(crit)} críticos (exposição ≥ 12) e {len(high)} altos (8–11). ",
             f"Register with **{len(risks)} risks**: {len(crit)} critical (exposure ≥ 12) and {len(high)} high (8–11). ")
    zc = {}
    for r in risks:
        zc[AN.risk_zone(AN.exposure(r))[2]] = zc.get(AN.risk_zone(AN.exposure(r))[2], 0) + 1
    crit_noown = [r["id"] for r in crit if not (r.get("risk_owner") or r.get("risk_manager"))]
    txt += tr(f"Por zona: {zc.get(('Crítico', 'Critical'), 0)} exigem **ação imediata**, {zc.get(('Alto', 'High'), 0)} **mitigação ativa**, "
              f"{zc.get(('Médio', 'Medium'), 0)} **planeamento de contingência** e {zc.get(('Baixo', 'Low'), 0)} apenas **monitorização**. ",
              f"By zone: {zc.get(('Crítico', 'Critical'), 0)} require **immediate action**, {zc.get(('Alto', 'High'), 0)} **active mitigation**, "
              f"{zc.get(('Médio', 'Medium'), 0)} **contingency planning** and {zc.get(('Baixo', 'Low'), 0)} **monitoring** only. ")
    if crit_noown:
        txt += tr(f"⚠️ Riscos críticos sem responsável: {', '.join(crit_noown)}. ", f"⚠️ Critical risks without owner: {', '.join(crit_noown)}. ")
    accepted_hi = [r["id"] for r in risks if AN.exposure(r) >= 8 and r.get("strategy") == "Accept"]
    if accepted_hi:
        txt += tr(f"⚠️ Riscos altos/críticos com estratégia 'Aceitar': {', '.join(accepted_hi)} — incoerente com a ação exigida pela zona. ",
                  f"⚠️ High/critical risks with an 'Accept' strategy: {', '.join(accepted_hi)} — inconsistent with the action required by their zone. ")
    top = ex[0]
    txt += tr(f"O risco mais exposto é **{top['id']} – {top.get('description', '')[:90]}** (exposição {AN.exposure(top)}). ",
              f"The most exposed risk is **{top['id']} – {top.get('description', '')[:90]}** (exposure {AN.exposure(top)}). ")
    if above:
        txt += tr(f"{len(above)} risco(s) estão acima da exposição-alvo aceitável — exigem medidas adicionais: {', '.join(r['id'] for r in above)}. ",
                  f"{len(above)} risk(s) exceed the acceptable target exposure — additional measures needed: {', '.join(r['id'] for r in above)}. ")
    sev = [r for r in risks if r.get("level_affected") in ("Outcome", "Impact")]
    if sev:
        txt += tr(f"{len(sev)} risco(s) comprometem outcomes/impactos (mais severos e menos controláveis que os que afetam atividades/outputs).",
                  f"{len(sev)} risk(s) compromise outcomes/impacts (more severe and less controllable than those affecting activities/outputs).")
    return txt


def strategy_text(scores: list[dict], selected: str) -> str:
    if not scores:
        return ""
    best = scores[0]
    txt = tr(f"Pela análise multicritério, a estratégia com melhor pontuação é **{best['name']}** ({num(best['score'], 2)} em 5).",
             f"According to the multi-criteria analysis, the best-scoring strategy is **{best['name']}** ({num(best['score'], 2)} out of 5).")
    if len(scores) > 1:
        gap = best["score"] - scores[1]["score"]
        txt += tr(f" A diferença para a segunda ({scores[1]['name']}) é {'pequena — convém testar a sensibilidade aos pesos' if gap < 0.3 else 'clara'} ({num(gap, 2)}).",
                  f" The gap to the runner-up ({scores[1]['name']}) is {'small — test sensitivity to the weights' if gap < 0.3 else 'clear'} ({num(gap, 2)}).")
    if selected and selected != best["name"]:
        txt += tr(f" A estratégia selecionada ({selected}) não é a de maior pontuação — justifique a escolha.",
                  f" The selected strategy ({selected}) is not the top-scoring one — justify the choice.")
    return txt


def indicators_text(p: dict) -> str:
    inds = p.get("indicators", [])
    if not inds:
        return ""
    full = [i for i in inds if AN.smart_score(i) == 5]
    nob = [i["id"] for i in inds if i.get("baseline") is None]
    not_ = [i["id"] for i in inds if i.get("target") is None]
    txt = tr(f"**{len(inds)} indicadores**, {len(full)} cumprem os 5 critérios SMART. ", f"**{len(inds)} indicators**, {len(full)} meet all 5 SMART criteria. ")
    if nob:
        txt += tr(f"Sem baseline: {', '.join(nob)} — um indicador sem baseline não pode ter meta, logo não é SMART. ",
                  f"No baseline: {', '.join(nob)} — an indicator without a baseline cannot have a target and is not SMART. ")
    if not_:
        txt += tr(f"Sem meta: {', '.join(not_)}. ", f"No target: {', '.join(not_)}. ")
    prog = [(i["id"], AN.progress(i)) for i in inds]
    prog = [(k, v) for k, v in prog if v is not None]
    if prog:
        lag = [k for k, v in prog if v < 0.5]
        txt += tr(f"Progresso médio face à meta: {pct(sum(v for _, v in prog) / len(prog))}" + (f"; abaixo de 50%: {', '.join(lag)}." if lag else "."),
                  f"Average progress towards targets: {pct(sum(v for _, v in prog) / len(prog))}" + (f"; below 50%: {', '.join(lag)}." if lag else "."))
    return txt


def benchmark_text(ind: dict, b: dict) -> str:
    if not b:
        return ""
    parts = []
    if "top" in b:
        parts.append(tr(f"Melhor desempenho entre pares: **{num(b['top'], 2)}** ({b.get('top_peer', '')}); mediana {num(b['median'], 2)}.",
                        f"Top performer among peers: **{num(b['top'], 2)}** ({b.get('top_peer', '')}); median {num(b['median'], 2)}."))
    if "trend_at_target_year" in b:
        parts.append(tr(f"A tendência histórica projeta **{num(b['trend_at_target_year'], 2)}** no ano-meta (declive {num(b['trend_slope'], 3)}/ano).",
                        f"The historical trend projects **{num(b['trend_at_target_year'], 2)}** in the target year (slope {num(b['trend_slope'], 3)}/year)."))
    f = b.get("feasibility")
    if f == "above_top":
        parts.append(tr("⚠️ A meta ultrapassa o melhor desempenho observado — **pouco realista** sem evidência adicional.",
                        "⚠️ The target exceeds the best observed performance — **unrealistic** without further evidence."))
    elif f == "below_trend":
        parts.append(tr("A meta fica aquém do que a tendência já garantiria — **pouco ambiciosa**; o projeto acrescentaria pouco valor.",
                        "The target is below what the trend would deliver anyway — **unambitious**; little added value from the project."))
    elif f == "ok":
        parts.append(tr("✅ A meta é ambiciosa mas dentro do intervalo observado — **viável e baseada em evidência**.",
                        "✅ The target is ambitious yet within the observed range — **feasible and evidence-based**."))
    return " ".join(parts)


# ----------------------------------------------------------------------------- consistency checks
def checks(p: dict, sched: dict | None = None) -> list[dict]:
    """Return a list of {'sev': 'error'|'warn'|'info', 'module': str, 'msg': str}."""
    out = []

    def add(sev, module, pt, en):
        out.append({"sev": sev, "module": module, "msg": tr(pt, en)})
    objs = p.get("objectives", [])
    codes = {str(o["code"]) for o in objs}
    acts = p.get("activities", [])
    act_ids = {str(a["id"]) for a in acts}
    # identification
    if not p.get("stakeholders"):
        add("warn", "Stakeholders", "Ainda não há stakeholders registados.", "No stakeholders registered yet.")
    elif not any(s.get("type") == "Target group" for s in p["stakeholders"]):
        add("warn", "Stakeholders", "Nenhum stakeholder do tipo 'Target group'.", "No stakeholder of type 'Target group'.")
    probs = p.get("problems", [])
    if probs and not any(x.get("level") == "Core problem" for x in probs):
        add("error", tr("Árvore de problemas", "Problem tree"), "Falta o problema central.", "The core problem is missing.")
    for x in probs:
        if x.get("level") != "Effect" and not str(x.get("parent") or "").strip():
            add("warn", tr("Árvore de problemas", "Problem tree"), f"{x['id']} não está ligado a nenhum nível superior.", f"{x['id']} is not linked to any higher level.")
        if not str(x.get("objective") or "").strip():
            add("info", tr("Árvore de objetivos", "Objective tree"), f"{x['id']} ainda não foi reformulado como objetivo (pela positiva).", f"{x['id']} has not been rephrased as an objective yet.")
    # logframe
    if objs:
        if not any(o.get("level") == "Impact" for o in objs):
            add("error", "Logframe", "Falta o Impacto (objetivo global).", "The Impact (overall objective) is missing.")
        if not any(o.get("level") == "Outcome" for o in objs):
            add("error", "Logframe", "Falta pelo menos um Outcome (objetivo específico).", "At least one Outcome (purpose) is missing.")
        for o in objs:
            if o.get("level") != "Impact" and str(o.get("parent") or "") not in codes:
                add("warn", "Logframe", f"{o['code']} não está ligado a um nível superior (lógica vertical).", f"{o['code']} is not linked to a higher level (vertical logic).")
        for o in [o for o in objs if o.get("level") == "Output"]:
            if not any(str(a.get("output_code")) == str(o["code"]) for a in acts):
                add("warn", "Logframe", f"O output {o['code']} não tem atividades de produção.", f"Output {o['code']} has no production activities.")
        inds_by = {str(i.get("objective_code")) for i in p.get("indicators", [])}
        for o in objs:
            if str(o["code"]) not in inds_by:
                add("warn", tr("Indicadores", "Indicators"), f"{o['code']} ({o.get('level')}) não tem indicador — o que não se mede não é fiável.",
                    f"{o['code']} ({o.get('level')}) has no indicator — what cannot be measured is not reliable.")
    else:
        add("warn", "Logframe", "A lógica de intervenção (logframe) está vazia.", "The intervention logic (logframe) is empty.")
    for a in acts:
        if a.get("output_code") and str(a["output_code"]) not in codes and str(a.get("type", "")).startswith("Production"):
            add("warn", tr("Atividades", "Activities"), f"{a['id']}: output '{a['output_code']}' não existe no logframe.", f"{a['id']}: output '{a['output_code']}' does not exist in the logframe.")
        if not activity_cost(p, a):
            add("info", tr("Orçamento", "Budget"), f"{a['id']} não tem custo.", f"{a['id']} has no cost.")
        if not a.get("responsible"):
            add("info", "RACI", f"{a['id']} não tem responsável.", f"{a['id']} has no responsible person.")
    types = {str(a.get("type")) for a in acts}
    for need, pt_, en_ in (("Support - Communication", "comunicação", "communication"), ("Support - M&E", "monitorização e avaliação", "monitoring & evaluation"),
                           ("Support - Management", "gestão do projeto", "project management")):
        if acts and need not in types:
            add("info", tr("Atividades", "Activities"), f"Não há atividades de apoio de {pt_}.", f"There are no {en_} support activities.")
    if sched and not sched.get("ok") and acts:
        for e in sched.get("errors", [])[:5]:
            add("error", "PERT/CPM", e, e)
    # indicators
    for i in p.get("indicators", []):
        if i.get("baseline") is None:
            add("warn", tr("Indicadores", "Indicators"), f"{i['id']} sem baseline (não pode ter meta).", f"{i['id']} has no baseline (cannot have a target).")
        if i.get("target") is None:
            add("warn", tr("Indicadores", "Indicators"), f"{i['id']} sem meta.", f"{i['id']} has no target.")
        if AN.smart_score(i) < 5:
            add("info", tr("Indicadores", "Indicators"), f"{i['id']} cumpre {AN.smart_score(i)}/5 critérios SMART.", f"{i['id']} meets {AN.smart_score(i)}/5 SMART criteria.")
        if not str(i.get("source") or "").strip():
            add("warn", tr("Indicadores", "Indicators"), f"{i['id']} sem fonte de verificação.", f"{i['id']} has no source of verification.")
    # assumptions
    for h in p.get("assumptions", []):
        code, _ = AN.assumption_decision(h)
        if code == "killer":
            add("error", tr("Pressupostos", "Assumptions"), f"{h['id']} é um pressuposto 'killer' — o projeto não é viável sem redesenho.", f"{h['id']} is a killer assumption — the project is not feasible without redesign.")
        if code == "redesign":
            add("warn", tr("Pressupostos", "Assumptions"), f"{h['id']}: improvável — redesenhar o projeto.", f"{h['id']}: unlikely — redesign the project.")
        exp = AN.assumption_type_check(p, h)
        if exp:
            add("warn", tr("Pressupostos", "Assumptions"), f"{h['id']}: ao nível de '{h.get('objective_code')}' espera-se um pressuposto {opt_label('assumption_type', exp)}.",
                f"{h['id']}: at the level of '{h.get('objective_code')}' a {exp} assumption is expected.")
        if str(h.get("objective_code") or "") not in codes:
            add("warn", tr("Pressupostos", "Assumptions"), f"{h['id']}: indique o objetivo (output/outcome/impacto) que o pressuposto condiciona.", f"{h['id']}: specify the objective (output/outcome/impact) the assumption conditions.")
        if code == "include" and not str(h.get("evidence") or "").strip():
            add("warn", tr("Pressupostos", "Assumptions"), f"{h['id']} não tem evidência — só é válido se suportado por evidência.", f"{h['id']} has no evidence — only valid if supported by evidence.")
        if code == "include" and not any(str(r.get("assumption_id")) == str(h["id"]) for r in p.get("risks", [])):
            add("info", tr("Riscos", "Risks"), f"O pressuposto {h['id']} não tem risco associado (formulação negativa) no registo de riscos.",
                f"Assumption {h['id']} has no matching (negatively phrased) risk in the risk register.")
    # risks
    for r in p.get("risks", []):
        e = AN.exposure(r)
        if e >= 12 and not str(r.get("proposed_mitigation") or "").strip():
            add("error", tr("Riscos", "Risks"), f"{r['id']} crítico sem medidas de mitigação propostas.", f"{r['id']} is critical with no proposed mitigation.")
        pa = str(r.get("preventive_activity") or "").strip()
        if pa and pa not in act_ids:
            add("warn", tr("Riscos", "Risks"), f"{r['id']}: atividade preventiva '{pa}' não existe.", f"{r['id']}: preventive activity '{pa}' does not exist.")
        if e >= 8 and not pa:
            add("info", tr("Riscos", "Risks"), f"{r['id']}: considere incluir uma atividade preventiva (apoio) no plano.", f"{r['id']}: consider adding a preventive (support) activity to the plan.")
    # budget / procurement
    if acts and float(p["meta"].get("contingency_pct") or 0) == 0 and p["meta"].get("contingency_method") != "risk":
        add("warn", tr("Contingências", "Contingencies"), "Não foi definido orçamento de contingência.", "No contingency budget has been defined.")
    for q in p.get("procurement", []):
        if q.get("activity_id") and str(q["activity_id"]) in act_ids:
            a = next(a for a in acts if str(a["id"]) == str(q["activity_id"]))
            if float(q.get("estimated_cost") or 0) > activity_cost(p, a) * 1.0001:
                add("warn", "Procurement", f"{q['id']}: custo estimado excede o orçamento da atividade {a['id']}.", f"{q['id']}: estimated cost exceeds the budget of activity {a['id']}.")
    if not p.get("cashflows"):
        add("info", tr("Finanças", "Finance"), "Sem fluxos de caixa para a análise VAL/TIR/MIRR.", "No cash flows for the NPV/IRR/MIRR analysis.")
    return out
