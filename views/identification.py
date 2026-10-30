"""1 · Identification: policy & strategy, stakeholders, behavioural patterns, problem tree, objectives & strategies."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import analysis as AN
from core import interpret as I
from core import ui
from core.i18n import opt_label, tr

PAL = ["#1F77B4", "#D9822B", "#2CA02C", "#9467BD", "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF", "#B03A2E"]


# ----------------------------------------------------------------------------- policy
def policy():
    p = ui.P()
    ui.header("Análise de políticas e estratégia", "Policy & strategy analysis", "policy", "🏛️")
    pol = p["policy"]
    c1, c2, c3 = st.columns(3)
    for col, key, pt, en, hpt, hen in (
            (c1, "context", "Contexto", "Context", "Ambiente social, económico, político, cultural; quadros institucionais e legais; opinião pública; dinâmica de stakeholders.", "Social, economic, political, cultural environment; institutional & legal frameworks; public opinion; stakeholder dynamics."),
            (c2, "content", "Conteúdo", "Content", "Objetivos, estratégias e instrumentos da política; racional das escolhas; coerência com leis e regulamentos.", "Policy goals, strategies and instruments; rationale of choices; coherence with laws and regulations."),
            (c3, "consequences", "Consequências", "Consequences", "Eficácia, efeitos não pretendidos, impactos distributivos por grupos e regiões.", "Effectiveness, unintended effects, distributional impacts across groups and regions.")):
        v = col.text_area(tr(pt, en), pol.get(key, ""), height=200, help=tr(hpt, hen), key=f"pol_{key}_{st.session_state.dv}")
        if v != pol.get(key, ""):
            pol[key] = v
            ui.mark_dirty()
    st.markdown(tr("#### Objetivos estratégicos do Governo / patrocinador e indicadores de impacto",
                   "#### Strategic goals of Government / sponsor and impact indicators"))
    st.caption(tr("O impacto do projeto é formulado como contribuição para um destes objetivos; os indicadores e fontes de verificação são os da estratégia.",
                  "The project impact is phrased as a contribution to one of these goals; indicators and sources of verification are those of the strategy."))
    ui.edit_table("policy_goals")
    imp = [o for o in p["objectives"] if o.get("level") == "Impact"]
    if imp and p["policy_goals"]:
        ui.interpret(tr(f"Impacto do projeto no logframe: **{imp[0]['text']}** — verifique se está formulado como contribuição para: "
                        + "; ".join(f"*{g['strategic_goal']}*" for g in p["policy_goals"]) + ".",
                        f"Project impact in the logframe: **{imp[0]['text']}** — check it is phrased as a contribution to: "
                        + "; ".join(f"*{g['strategic_goal']}*" for g in p["policy_goals"]) + "."))


# ----------------------------------------------------------------------------- stakeholders
def stakeholders():
    p = ui.P()
    ui.header("Análise de stakeholders", "Stakeholder analysis", "stakeholders", "👥")
    view = st.segmented_control(tr("Vista", "View"), ["full", "prof", "pcm"], default="full",
                                format_func=lambda v: {"full": tr("Completa (alargada)", "Full (extended)"),
                                                       "prof": tr("Modelo do professor (StakeholderRegister)", "Professor's template (StakeholderRegister)"),
                                                       "pcm": tr("Matriz PCM (4 camadas)", "PCM matrix (4 layers)")}[v], key="sh_view")
    cols = {"prof": ["id", "name", "type", "benefits_to_project", "benefits_of_project", "engagement"],
            "pcm": ["id", "name", "type", "characteristics", "interests", "capacity_motivation", "possible_actions"],
            "full": None}[view or "full"]
    rows = ui.edit_table("stakeholders", columns=cols, key=view or "full")
    if not rows:
        return
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(tr("##### Matriz influência × interesse (Mendelow)", "##### Influence × interest grid (Mendelow)"))
        fig = go.Figure()
        for x0, y0, lab in ((0.5, 3, tr("Manter satisfeito", "Keep satisfied")), (3, 3, tr("Gerir de perto", "Manage closely")),
                            (0.5, 0.5, tr("Monitorizar", "Monitor")), (3, 0.5, tr("Manter informado", "Keep informed"))):
            fig.add_shape(type="rect", x0=x0, x1=x0 + 2.5, y0=y0, y1=y0 + 2.5, line=dict(width=0),
                          fillcolor="#FDECE7" if lab in (tr("Gerir de perto", "Manage closely"),) else "#F3F6F8", layer="below")
            fig.add_annotation(x=x0 + 1.25, y=y0 + 0.15, text=f"<b>{lab}</b>", showarrow=False, font=dict(size=11, color="#555"))
        col = {"Supporter": "#2E8B57", "Neutral": "#7F8C8D", "Opponent": "#C0392B"}
        for att in ("Supporter", "Neutral", "Opponent"):
            sub = [r for r in rows if r.get("attitude") == att]
            if not sub:
                continue
            jit = [((i % 3) - 1) * 0.12 for i in range(len(sub))]
            fig.add_trace(go.Scatter(x=[r["interest"] + j for r, j in zip(sub, jit)], y=[r["influence"] + j for r, j in zip(sub, jit)],
                                     mode="markers+text", text=[r["name"][:28] for r in sub], textposition="top center",
                                     marker=dict(size=16, color=col[att], line=dict(width=1, color="white")),
                                     name=opt_label("attitude", att), hovertext=[AN.mendelow(r["influence"], r["interest"]) for r in sub]))
        fig.update_layout(height=470, xaxis=dict(title=tr("Interesse", "Interest"), range=[0.5, 5.5], dtick=1),
                          yaxis=dict(title=tr("Influência", "Influence"), range=[0.5, 5.6], dtick=1),
                          margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.markdown(tr("##### Grupo-alvo ⊂ Beneficiários ⊂ Stakeholders", "##### Target group ⊂ Beneficiaries ⊂ Stakeholders"))
        fig = go.Figure()
        for r_, colr, lab in ((3, "#F3E5E5", "Stakeholders"), (2.1, "#FBE9D7", tr("Beneficiários", "Beneficiaries")), (1.2, "#DCEFF6", tr("Grupo-alvo", "Target group"))):
            fig.add_shape(type="circle", x0=-r_, y0=-r_, x1=r_, y1=r_, fillcolor=colr, line=dict(color="#BBBBBB"))
            fig.add_annotation(x=0, y=r_ - 0.25, text=f"<b>{lab}</b>", showarrow=False, font=dict(size=11))
        groups = {"Target group": [], "Beneficiaries": [], "Stakeholders": []}
        for r in rows:
            groups[AN.circle_of(r.get("type"))].append(r["name"])
        import math
        for g, rad in (("Target group", 0.55), ("Beneficiaries", 1.65), ("Stakeholders", 2.55)):
            names = groups[g]
            for i, n in enumerate(names):
                ang = math.pi * (0.15 + 0.7 * (i + 0.5) / max(1, len(names))) + (math.pi if g == "Stakeholders" and i % 2 else 0)
                fig.add_annotation(x=rad * math.cos(ang) * (0.0 if g == "Target group" and len(names) == 1 else 1), y=rad * math.sin(ang) * (0.3 if g == "Target group" else 1) - (0.2 if g == "Target group" else 0),
                                   text=n[:24], showarrow=False, font=dict(size=9))
        fig.update_layout(height=470, xaxis=dict(visible=False, range=[-3.2, 3.2]), yaxis=dict(visible=False, range=[-3.2, 3.2], scaleanchor="x"),
                          margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
        st.plotly_chart(fig, width="stretch")
    st.markdown(tr("##### Estratégia recomendada por stakeholder", "##### Recommended strategy per stakeholder"))
    st.dataframe(pd.DataFrame([{ui.label("name"): r["name"], ui.label("type"): opt_label("stakeholder_type", r["type"]),
                                tr("Quadrante", "Quadrant"): AN.mendelow(r["influence"], r["interest"]),
                                ui.label("engagement"): opt_label("engagement", r["engagement"]), ui.label("attitude"): opt_label("attitude", r["attitude"])}
                               for r in rows]), hide_index=True, width="stretch")
    ui.interpret(I.stakeholder_text(rows))


# ----------------------------------------------------------------------------- behaviour
def behaviour():
    p = ui.P()
    ui.header("Padrões comportamentais do grupo-alvo", "Target-group behavioural patterns", "behaviour", "🔺")
    tgs = [s["name"] for s in p["stakeholders"] if s.get("type") in ("Target group", "Beneficiary")]
    if tgs:
        st.caption(tr("Grupos-alvo/beneficiários registados: ", "Registered target groups/beneficiaries: ") + ", ".join(tgs))
    rows = ui.edit_table("behaviour")
    c1, c2 = st.columns([2, 3])
    with c1:
        st.markdown(tr("##### Pirâmide", "##### Pyramid"))
        layers = [("OUTCOMES", "#2C6E91"), (tr("MOTIVAÇÃO", "MOTIVATION"), "#D9822B"), (tr("CAPACIDADE", "ABILITY"), "#D9822B"),
                  (tr("OPORTUNIDADE", "OPPORTUNITY"), "#D9822B"), (tr("PERCEÇÃO", "PERCEPTION"), "#D9822B"), ("OUTPUTS", "#2C6E91")]
        fig = go.Figure()
        n = len(layers)
        for i, (lab, colr) in enumerate(layers):
            y0, y1 = n - i - 1, n - i
            w0, w1 = (i + 1) / n, i / n
            fig.add_shape(type="path", path=f"M {-w0} {y0} L {w0} {y0} L {w1} {y1} L {-w1} {y1} Z", fillcolor=colr, line=dict(color="white", width=2))
            fig.add_annotation(x=0, y=y0 + 0.5, text=f"<b>{lab}</b>", showarrow=False, font=dict(color="white", size=12))
        fig.update_layout(height=360, xaxis=dict(visible=False, range=[-1.05, 1.05]), yaxis=dict(visible=False, range=[0, n]),
                          margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, width="stretch")
    with c2:
        if rows:
            st.markdown(tr("##### Perfil por grupo (1 = desfavorável, 5 = favorável)", "##### Profile per group (1 = unfavourable, 5 = favourable)"))
            cats = [tr("Perceção", "Perception"), tr("Oportunidade", "Opportunity"), tr("Capacidade", "Ability"), tr("Motivação", "Motivation")]
            fig = go.Figure()
            for i, r in enumerate(rows):
                v = [r["perception"], r["opportunity"], r["ability"], r["motivation"]]
                fig.add_trace(go.Scatterpolar(r=v + v[:1], theta=cats + cats[:1], fill="toself", name=r["target_group"][:30], line=dict(color=PAL[i % 10]), opacity=0.7))
            fig.add_trace(go.Scatterpolar(r=[2] * 5, theta=cats + cats[:1], mode="lines", line=dict(dash="dot", color="#C0392B"), name=tr("Limiar de risco", "Risk threshold")))
            fig.update_layout(height=360, polar=dict(radialaxis=dict(range=[0, 5], dtick=1)), margin=dict(l=30, r=30, t=20, b=20), legend=dict(orientation="h"))
            st.plotly_chart(fig, width="stretch")
    ui.interpret(I.behaviour_text(rows))


# ----------------------------------------------------------------------------- problem tree
def problems():
    p = ui.P()
    ui.header("Análise de problemas (árvore de problemas)", "Problem analysis (problem tree)", "problems", "🌳")
    st.caption(tr("Níveis: Efeito (topo) · Problema central · Causa (raízes). 'Leva a' = ID(s) do nível superior, separados por vírgulas.",
                  "Levels: Effect (top) · Core problem · Cause (roots). 'Leads to' = upper-level ID(s), comma-separated."))
    rows = ui.edit_table("problems", columns=["id", "level", "text", "parent"], key="pt")
    if rows:
        ui.graph(AN.tree_dot(rows, objective=False))
        cores = [r for r in rows if r.get("level") == "Core problem"]
        causes = [r for r in rows if r.get("level") == "Cause"]
        effects = [r for r in rows if r.get("level") == "Effect"]
        ui.interpret(tr(f"A árvore tem **{len(cores)} problema(s) central(is)**, **{len(causes)} causas** e **{len(effects)} efeitos**. "
                        "As causas são o alvo da intervenção (transformam-se em outputs); se um 'problema central' parecer consequência de outro, provavelmente é um efeito.",
                        f"The tree has **{len(cores)} core problem(s)**, **{len(causes)} causes** and **{len(effects)} effects**. "
                        "Causes are the intervention targets (they become outputs); if a 'core problem' looks like a consequence of another, it is probably an effect."))


# ----------------------------------------------------------------------------- objectives & strategy
def objectives():
    p = ui.P()
    ui.header("Árvore de objetivos e análise de estratégias", "Objective tree & strategy analysis", "objectives", "🎯")
    t1, t2 = st.tabs([tr("🎯 Árvore de objetivos", "🎯 Objective tree"), tr("⚖️ Seleção da estratégia (multicritério)", "⚖️ Strategy selection (multi-criteria)")])
    with t1:
        st.caption(tr("Reformule cada problema pela positiva. Desmarque 'No âmbito?' para os meios que ficam fora da estratégia escolhida (aparecem a cinzento).",
                      "Rephrase each problem positively. Untick 'In scope?' for means outside the chosen strategy (shown in grey)."))
        rows = ui.edit_table("problems", columns=["id", "level", "text", "objective", "in_scope"], key="ot", disabled=["id", "level", "text"], num_rows="fixed")
        if rows:
            ui.graph(AN.tree_dot(rows, objective=True))
        st.markdown(tr("##### Gerar a lógica de intervenção (logframe) a partir da árvore", "##### Generate the intervention logic (logframe) from the tree"))
        st.caption(tr("Fins → Impacto; problema(s) resolvido(s) → Outcome(s); meios no âmbito → Outputs. Substitui a coluna de objetivos do logframe.",
                      "Ends → Impact; problem(s) solved → Outcome(s); in-scope means → Outputs. Replaces the logframe objectives."))
        if st.button(tr("⚙️ Gerar logframe a partir da árvore de objetivos", "⚙️ Generate logframe from the objective tree")):
            generate_logframe(p)
            ui.bump()
            st.success(tr("Logframe gerado. Veja a página 'Logframe (matriz)'.", "Logframe generated. See the 'Logframe matrix' page."))
    with t2:
        strategy(p)


def generate_logframe(p):
    probs = [x for x in p["problems"] if x.get("in_scope", True)]
    effects = [x for x in probs if x["level"] == "Effect"]
    cores = [x for x in probs if x["level"] == "Core problem"]
    causes = [x for x in probs if x["level"] == "Cause"]
    objs = []
    imp_text = "; ".join(e.get("objective") or e["text"] for e in effects) or tr("Impacto", "Impact")
    objs.append({"code": "IMP", "level": "Impact", "text": tr("Contribuir para: ", "Contribute to: ") + imp_text, "parent": "", "source_problem": ",".join(e["id"] for e in effects)})
    core_code = {}
    for i, c in enumerate(cores, 1):
        code = f"OC{i}"
        core_code[c["id"]] = (code, i)
        objs.append({"code": code, "level": "Outcome", "text": c.get("objective") or c["text"], "parent": "IMP", "source_problem": c["id"]})
    count = {}
    for c in causes:
        parents = [x.strip() for x in str(c.get("parent") or "").split(",") if x.strip() in core_code]
        if not parents:
            continue
        oc, n = core_code[parents[0]]
        count[n] = count.get(n, 0) + 1
        objs.append({"code": f"{n}.{count[n]}", "level": "Output", "text": c.get("objective") or c["text"], "parent": oc, "source_problem": c["id"]})
    p["objectives"] = objs


def strategy(p):
    stg = p["strategies"]
    st.markdown(tr("##### 1. Critérios e pesos", "##### 1. Criteria and weights"))
    import copy
    base_key = f"crit_{st.session_state.dv}"
    if base_key not in st.session_state:
        st.session_state[base_key] = pd.DataFrame(stg.get("criteria", []), columns=["criterion", "weight"])
    cdf = st.data_editor(st.session_state[base_key], num_rows="dynamic", hide_index=True, key=f"ed_{base_key}", width="stretch",
                         column_config={"criterion": st.column_config.TextColumn(ui.label("criterion"), width="large"),
                                        "weight": st.column_config.NumberColumn(ui.label("weight"), min_value=0.0, step=0.5)})
    crit = [{"criterion": str(r["criterion"]), "weight": float(r["weight"] or 0)} for r in cdf.to_dict("records") if r.get("criterion")]
    if crit != stg.get("criteria"):
        stg["criteria"] = crit
        ui.mark_dirty()
    st.markdown(tr("##### 2. Opções estratégicas e pontuação (1–5)", "##### 2. Strategic options and scores (1–5)"))
    names = [c["criterion"] for c in crit]
    okey = f"opt_{st.session_state.dv}_{len(names)}_{hash(tuple(names))}"
    if okey not in st.session_state:
        st.session_state[okey] = pd.DataFrame([{"name": o["name"], "description": o.get("description", ""), **{n: o.get("scores", {}).get(n, 3) for n in names}}
                                               for o in stg.get("options", [])], columns=["name", "description", *names])
    cfg = {"name": st.column_config.TextColumn(tr("Estratégia", "Strategy")), "description": st.column_config.TextColumn(tr("Descrição", "Description"), width="large")}
    cfg.update({n: st.column_config.NumberColumn(n[:40], min_value=1, max_value=5, step=1) for n in names})
    odf = st.data_editor(st.session_state[okey], num_rows="dynamic", hide_index=True, key=f"ed_{okey}", column_config=cfg, width="stretch")
    opts = [{"name": str(r["name"]), "description": str(r.get("description") or ""), "scores": {n: float(r.get(n) or 0) for n in names}}
            for r in odf.to_dict("records") if r.get("name") and str(r["name"]) != "nan"]
    if opts != stg.get("options"):
        stg["options"] = opts
        ui.mark_dirty()
    sc = AN.strategy_scores(stg)
    if sc:
        c1, c2 = st.columns([3, 2])
        fig = go.Figure(go.Bar(x=[s["score"] for s in sc][::-1], y=[s["name"] for s in sc][::-1], orientation="h",
                               marker_color=["#2E8B57" if s is sc[0] else "#7FA7C9" for s in sc][::-1],
                               text=[f"{s['score']:.2f}" for s in sc][::-1], textposition="outside"))
        fig.update_layout(height=80 + 50 * len(sc), xaxis=dict(range=[0, 5.5], title=tr("Pontuação ponderada", "Weighted score")), margin=dict(l=10, r=10, t=10, b=10))
        c1.plotly_chart(fig, width="stretch")
        sel = c2.selectbox(tr("Estratégia selecionada", "Selected strategy"), [s["name"] for s in sc],
                           index=[s["name"] for s in sc].index(stg["selected"]) if stg.get("selected") in [s["name"] for s in sc] else 0)
        if sel != stg.get("selected"):
            stg["selected"] = sel
            ui.mark_dirty()
        ui.interpret(I.strategy_text(sc, stg.get("selected")))
