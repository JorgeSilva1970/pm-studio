"""3 · WBS / EAP — Work Breakdown Structure (Estrutura Analítica do Projeto / Estrutura de Decomposição do Trabalho)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import agent as AG
from core import schedule as S
from core import ui
from core import wbs as W
from core.fmt import d, money, num, pct, unit_label
from core.i18n import opt_codes, opt_label, tr
from core.model import activity_cost
from core.help_texts import WBS_GLOSSARY, SRC, wbs_term, wbs_tip

SEL = st.column_config.SelectboxColumn


def _outputs(p):
    return [""] + [str(o["code"]) for o in p["objectives"] if o.get("level") in ("Output", "Outcome")]


def page():
    p = ui.P()
    m = p["meta"]
    cur = m.get("currency", "EUR")
    ui.header("WBS / EAP — Estrutura Analítica do Projeto", "WBS — Work Breakdown Structure", "wbs", "🌳")
    sched = S.compute(p)
    sched = sched if sched.get("ok") else None
    ev = S.evm(p, sched) if sched else None
    ro = W.rollup(p, sched, ev)
    els = W.elements(p)

    # ------------------------------------------------------------------ settings & actions
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        ori = c1.selectbox(tr("Orientação da WBS", "WBS orientation"), opt_codes("wbs_orientation"),
                           index=opt_codes("wbs_orientation").index(m.get("wbs_orientation") or "deliverables"), format_func=lambda c: opt_label("wbs_orientation", c),
                           key=f"wbs_ori_{st.session_state.dv}")
        rule = c2.selectbox(tr("Regra de dimensão dos pacotes", "Work-package size rule"), opt_codes("wbs_rule"),
                            index=opt_codes("wbs_rule").index(m.get("wbs_rule") or "auto"), format_func=lambda c: opt_label("wbs_rule", c), key=f"wbs_rule_{st.session_state.dv}",
                            help=wbs_tip("rule_880") + "\n\n" + wbs_tip("reporting"))
        if rule != m.get("wbs_rule"):
            m["wbs_rule"] = rule
            ui.mark_dirty()
        mn, mx, _r = W.duration_limits(p)
        u = unit_label(m.get("time_unit", "weeks"))
        newmx = c3.number_input(tr(f"Duração máx. ({u})", f"Max. duration ({u})"), 0.0, 1000.0, float(round(mx, 2)), 0.25, key=f"wbs_mx_{st.session_state.dv}",
                                help=tr("Limite acima do qual um pacote é sinalizado (aviso, não bloqueia). Por omissão vem da regra escolhida: ",
                                        "Limit above which a package is flagged (warning, never blocking). Defaults to the chosen rule: ") + W.rule_arithmetic(p))
        if abs(newmx - mx) > 1e-6:
            m["wbs_max"] = newmx
            ui.mark_dirty()
        b1, b2, b3, b4 = st.columns(4)
        conf = True
        if els:
            conf = b1.checkbox(tr("Substituir a WBS atual", "Replace the current WBS"), key="wbs_conf")
        if b1.button(tr("🧩 Gerar a partir do quadro lógico", "🧩 Generate from the logframe"), disabled=not conf, width="stretch"):
            n = W.apply_generated(p, ori)
            W.enrich_dictionary(p)
            ui.bump()
            st.toast(tr(f"WBS gerada com {n} elementos", f"WBS generated with {n} elements"))
            st.rerun()
        if ori != m.get("wbs_orientation"):
            b1.caption(tr("A orientação escolhida aplica-se ao gerar.", "The chosen orientation applies when generating."))
        if b2.button(tr("🔗 Ligar atividades em falta", "🔗 Link missing activities"), width="stretch", disabled=not els,
                     help=tr("Liga cada atividade sem pacote ao pacote do seu output (ou ao pacote de apoio do mesmo tipo).",
                             "Links each unassigned activity to its output's package (or the support package of the same type).")):
            n = W.auto_assign(p)
            ui.bump()
            st.toast(tr(f"{n} atividades ligadas", f"{n} activities linked"))
            st.rerun()
        if b3.button(tr("🔢 Renumerar códigos", "🔢 Renumber codes"), width="stretch", disabled=not els):
            W.renumber(p)
            ui.bump()
            st.rerun()
        if b4.button(tr("📖 Preencher dicionário (campos vazios)", "📖 Fill dictionary (empty fields)"), width="stretch", disabled=not els):
            n = W.enrich_dictionary(p)
            ui.bump()
            st.toast(tr(f"{n} campos preenchidos", f"{n} fields filled"))
            st.rerun()

    if not els:
        st.info(tr("Ainda não há WBS. Use **Gerar a partir do quadro lógico** ou acrescente elementos no separador Estrutura.",
                   "There is no WBS yet. Use **Generate from the logframe** or add elements in the Structure tab."))
    lv = W.leaves(p)
    n_acts = len(p["activities"])
    linked = sum(1 for a in p["activities"] if a.get("wbs_code") in {e["code"] for e in lv})
    ch = W.checks(p, sched)
    c = st.columns(5)
    c[0].metric(tr("Elementos", "Elements"), len(els), help=wbs_tip("elements"))
    c[1].metric(tr("Níveis", "Levels"), max([W.level(e["code"]) for e in els] or [0]), help=wbs_tip("level"))
    c[2].metric(tr("Pacotes de trabalho", "Work packages"), len(lv), help=wbs_tip("work_package"))
    c[3].metric(tr("Atividades ligadas", "Linked activities"), f"{linked}/{n_acts}", help=wbs_tip("linked"))
    ok100 = els and linked == n_acts and not any("100" in x["msg"] for x in ch)
    c[4].metric(tr("Regra dos 100%", "100% rule"), "✅" if ok100 else "⚠️", help=wbs_tip("rule100"))
    if els:
        ui.interpret(W.summary_text(p, ro, cur))

    t1, t2, t3, t4, t5, t6 = st.tabs([tr("🌳 Estrutura", "🌳 Structure"), tr("🗺️ Diagrama", "🗺️ Diagram"), tr("📋 Vista indentada e EVM", "📋 Outline & EVM"),
                                      tr("📖 Dicionário da WBS", "📖 WBS dictionary"), tr("✅ Verificações e IA", "✅ Checks & AI"), tr("📘 Glossário e fórmulas", "📘 Glossary & formulas")])
    # ------------------------------------------------------------------ structure editor
    with t1:
        with st.form("wbs_add", clear_on_submit=True):
            st.markdown(tr("**Acrescentar elemento** (o código é atribuído automaticamente)", "**Add element** (the code is assigned automatically)"))
            f1, f2, f3, f4 = st.columns([2, 3, 2, 1])
            par = f1.selectbox(tr("Elemento-pai", "Parent element"), ["0"] + [e["code"] for e in els],
                               format_func=lambda c: tr("0 — Projeto (nível 1)", "0 — Project (level 1)") if c == "0" else W.label(next(e for e in els if e["code"] == c))[:60])
            name = f2.text_input(tr("Nome", "Name"))
            typ = f3.selectbox(tr("Tipo", "Type"), opt_codes("wbs_type"), index=4, format_func=lambda c: opt_label("wbs_type", c))
            oc = f4.selectbox("Output", _outputs(p), format_func=lambda c: c or "—")
            if st.form_submit_button(tr("➕ Acrescentar", "➕ Add"), type="primary") and name.strip():
                from core.model import _coerce_row, empty_row
                p["wbs"].append(_coerce_row("wbs", {**empty_row("wbs"), "code": W.next_child_code(p, par), "name": name.strip(), "type": typ, "output_code": oc}))
                ui.bump()
                st.rerun()
        st.caption(tr("O código define a hierarquia (1 → 1.1 → 1.1.1). Pode editar códigos e nomes diretamente; os pesos (%) são opcionais e, se usados, devem somar 100% em cada nível. "
                      "Os custos **não** se introduzem aqui: são sempre somados a partir das atividades (sem dupla contagem).",
                      "The code defines the hierarchy (1 → 1.1 → 1.1.1). You can edit codes and names directly; weights (%) are optional and, if used, must add up to 100% at each level. "
                      "Costs are **not** entered here: they are always summed from the activities (no double counting)."))
        ui.edit_table("wbs", columns=["code", "name", "type", "output_code", "owner", "weight"], key="wbs_tbl",
                      overrides={"output_code": SEL(ui.label("output_code", "wbs"), options=_outputs(p))})
        if els:
            x1, x2 = st.columns([3, 1])
            dl = x1.selectbox(tr("Eliminar elemento (e descendentes)", "Delete element (and descendants)"), [""] + [e["code"] for e in W.elements(p)],
                              format_func=lambda c: c and W.label(next(e for e in W.elements(p) if e["code"] == c))[:70])
            if x2.button(tr("🗑️ Eliminar", "🗑️ Delete"), disabled=not dl):
                W.delete(p, dl)
                ui.bump()
                st.rerun()
        st.markdown(tr("##### Ligação das atividades aos pacotes de trabalho", "##### Linking activities to work packages"))
        ui.edit_table("activities", columns=["id", "name", "output_code", "type", "wbs_code"], key="wbs_acts", num_rows="fixed",
                      disabled=["id", "name", "output_code", "type"],
                      overrides={"wbs_code": SEL(ui.label("wbs_code"), options=W.leaf_options(p),
                                                 format_func=lambda c: (W.label(next((e for e in W.elements(p) if e["code"] == c), {"code": c}))[:55]) if c else "—")})

    # ------------------------------------------------------------------ diagram
    with t2:
        if els:
            c1, c2, c3 = st.columns(3)
            maxd = max(W.level(e["code"]) for e in els)
            depth = c1.slider(tr("Mostrar até ao nível", "Show down to level"), 1, max(1, maxd), maxd) if maxd > 1 else 1
            rk = c2.segmented_control(tr("Orientação do diagrama", "Diagram layout"), ["TB", "LR"], default="TB" if len(lv) <= 6 else "LR",
                                      format_func=lambda x: {"TB": tr("Vertical (organigrama)", "Vertical (org chart)"), "LR": tr("Horizontal (projetos grandes)", "Horizontal (large projects)")}[x])
            acts_on = c3.toggle(tr("Mostrar atividades", "Show activities"), value=False)
            dotsrc = W.dot(p, ro, depth, rk or "TB", cur, acts_on)
            ui.graph(dotsrc)
            st.caption(tr("Azul-escuro = projeto · azul = fase/conta de controlo · claro = pacote de trabalho · contorno vermelho = CPI < 0,95 · tracejado vermelho = pacote no caminho crítico. "
                          "Em WBS grandes use a vista horizontal ou limite o nível.",
                          "Dark blue = project · blue = phase/control account · light = work package · red border = CPI < 0.95 · red dashed = package on the critical path. "
                          "For large WBS use the horizontal layout or limit the level."))
            st.caption(tr("**Em cada caixa:** código e nome · BAC = Σ custo das atividades do ramo · duração = EF máx. − ES mín. (não é a soma) · CPI = Σ EV ÷ Σ AC. Detalhe das contas no separador *Vista indentada e EVM* e no *Glossário*.",
                          "**In each box:** code and name · BAC = Σ cost of the branch's activities · duration = max EF − min ES (not the sum) · CPI = Σ EV ÷ Σ AC. Calculation details in the *Outline & EVM* tab and the *Glossary*."))
            st.download_button(tr("⬇️ Descarregar diagrama (Graphviz .dot)", "⬇️ Download diagram (Graphviz .dot)"), dotsrc.encode("utf-8"), "wbs.dot", "text/vnd.graphviz")
            st.markdown(tr("##### Peso de cada ramo no orçamento (treemap)", "##### Weight of each branch in the budget (treemap)"))
            st.caption(tr("Área de cada retângulo = BAC do pacote de trabalho (Σ custo das suas atividades); os retângulos agrupam-se pelos elementos-pai. ",
                          "Area of each rectangle = work-package BAC (Σ cost of its activities); rectangles are grouped by parent elements. ") + wbs_tip("pct_bac"))
            recs = []
            for e in lv:
                path = []
                cc = e["code"]
                while cc != "0":
                    path.insert(0, cc)
                    cc = W.parent_of(cc)
                names = [W.label(next((x for x in els if x["code"] == k), {"code": k}))[:45] for k in path]
                recs.append({"root": p["meta"].get("name", "")[:40], **{f"l{i}": names[i] if i < len(names) else names[-1] for i in range(maxd)}, "BAC": max(ro[e["code"]]["BAC"], 1)})
            if recs:
                fig = px.treemap(pd.DataFrame(recs), path=["root"] + [f"l{i}" for i in range(maxd)], values="BAC", color="l0")
                fig.update_traces(texttemplate="%{label}<br>%{value:,.0f}")
                fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, width="stretch")

    # ------------------------------------------------------------------ outline & EVM
    with t3:
        rows = W.indented(p, ro)
        if rows:
            lvmax = st.slider(tr("Nível máximo", "Maximum level"), 1, max(r["level"] for r in rows), max(r["level"] for r in rows), key="wbs_lv") if max(r["level"] for r in rows) > 1 else 1
            df = pd.DataFrame([{tr("Código", "Code"): r["code"], tr("Elemento", "Element"): " " * (r["level"] - 1) + r["name"],
                                tr("Tipo", "Type"): opt_label("wbs_type", r["type"]), tr("Ativ.", "Acts"): r["n_acts"], "BAC": r["BAC"],
                                tr("Início", "Start"): d(r["start"]) if r["start"] else "—", tr("Fim", "Finish"): d(r["finish"]) if r["finish"] else "—",
                                tr("Duração", "Duration"): r["duration"], tr("% concl.", "% done"): r["pct"], "PV": r["PV"], "EV": r["EV"], "AC": r["AC"],
                                "CPI": r["CPI"], "SPI": r["SPI"], tr("Crítico", "Critical"): "🔴" if r["critical"] else ""} for r in rows if r["level"] <= lvmax])

            def _col(v):
                if v is None or v != v:
                    return ""
                return "color:#C0392B;font-weight:600" if v < 0.95 else ("color:#2E8B57" if v >= 1 else "")
            fmt = {"BAC": "{:,.0f}", "PV": "{:,.0f}", "EV": "{:,.0f}", "AC": "{:,.0f}", "CPI": "{:.2f}", "SPI": "{:.2f}", tr("Duração", "Duration"): "{:.1f}", tr("% concl.", "% done"): "{:.0%}"}
            colhelp = {tr("Código", "Code"): "level", tr("Ativ.", "Acts"): "linked", "BAC": "bac", tr("Início", "Start"): "start_finish", tr("Fim", "Finish"): "start_finish",
                       tr("Duração", "Duration"): "duration", tr("% concl.", "% done"): "pct", "PV": "pv", "EV": "ev", "AC": "ac", "CPI": "cpi", "SPI": "spi", tr("Crítico", "Critical"): "critical"}
            ccfg = {c_: st.column_config.Column(c_, help=wbs_tip(k_)) for c_, k_ in colhelp.items()}
            st.dataframe(df.style.format(fmt, na_rep="—").map(_col, subset=["CPI", "SPI"]), hide_index=True, width="stretch", height=min(700, 38 + 35 * len(df)),
                         column_config=ccfg)
            st.caption(tr("ⓘ Passe o rato sobre o título de cada coluna para ver a fórmula.", "ⓘ Hover over each column title to see the formula."))
            with st.expander(tr("🧮 Como se calcula? (contas com os números reais)", "🧮 How is it calculated? (worked out with the real numbers)")):
                ex_code = st.selectbox(tr("Elemento", "Element"), ["0"] + [r["code"] for r in rows],
                                       format_func=lambda c: tr("0 — Projeto (total)", "0 — Project (total)") if c == "0" else W.label(next(e for e in els if e["code"] == c))[:80], key="wbs_explain_sel")
                st.markdown(W.explain(p, ex_code, ro, ev, cur))
            r0 = ro["0"]
            st.caption(tr(f"Total do projeto: BAC {money(r0['BAC'], cur)}" + (f" · PV {money(r0['PV'], cur)} · EV {money(r0['EV'], cur)} · AC {money(r0['AC'], cur)}" if r0.get("PV") is not None else "") +
                          " — a soma dos elementos de nível 1 é sempre igual ao total (regra dos 100% aplicada aos custos).",
                          f"Project total: BAC {money(r0['BAC'], cur)}" + (f" · PV {money(r0['PV'], cur)} · EV {money(r0['EV'], cur)} · AC {money(r0['AC'], cur)}" if r0.get("PV") is not None else "") +
                          " — the sum of level-1 elements always equals the total (100% rule applied to costs)."))
            wp = [ro[e["code"]] for e in lv if ro[e["code"]].get("CPI") is not None and ro[e["code"]].get("SPI") is not None]
            if wp:
                fig = go.Figure(go.Scatter(x=[r["SPI"] for r in wp], y=[r["CPI"] for r in wp], mode="markers+text", text=[r["code"] for r in wp], textposition="top center",
                                           marker=dict(size=[8 + 40 * r["BAC"] / max(x["BAC"] for x in wp) for r in wp], color=["#C0392B" if min(r["CPI"], r["SPI"]) < 0.95 else "#2C7FB8" for r in wp], opacity=0.75)))
                fig.add_hline(y=1, line_dash="dot")
                fig.add_vline(x=1, line_dash="dot")
                fig.update_layout(height=380, xaxis_title=tr("SPI (prazo)", "SPI (schedule)"), yaxis_title=tr("CPI (custo)", "CPI (cost)"), margin=dict(l=10, r=10, t=30, b=10),
                                  title=tr("Onde está o desvio? CPI × SPI por pacote de trabalho (tamanho = BAC)", "Where is the variance? CPI × SPI per work package (size = BAC)"))
                st.plotly_chart(fig, width="stretch")
            elif not sched:
                st.info(tr("Sem cronograma válido: os valores EVM aparecem quando a rede de atividades estiver completa.", "No valid schedule: EVM values appear once the activity network is complete."))

    # ------------------------------------------------------------------ dictionary
    with t4:
        if els:
            code = st.selectbox(tr("Elemento", "Element"), [e["code"] for e in els], index=next((i for i, e in enumerate(els) if e["code"] in {x["code"] for x in lv}), 0),
                                format_func=lambda c: W.label(next(e for e in els if e["code"] == c))[:90], key="wbs_dict_sel")
            dct = W.dictionary(p, code, ro)
            e = dct["element"]
            r = dct["rollup"]
            st.markdown(f"#### {W.label(e)}")
            k = st.columns(5)
            k[0].metric(tr("Tipo", "Type"), opt_label("wbs_type", e.get("type")), help=wbs_tip("work_package"))
            k[1].metric("BAC", money(r.get("BAC", 0), cur), help=wbs_tip("bac"))
            k[2].metric(tr("Duração", "Duration"), f"{num(r['duration'], 1)} {u}" if r.get("duration") is not None else "—", help=wbs_tip("duration"))
            k[3].metric("CPI", num(r.get("CPI"), 2) if r.get("CPI") is not None else "—", help=wbs_tip("cpi"))
            k[4].metric("SPI", num(r.get("SPI"), 2) if r.get("SPI") is not None else "—", help=wbs_tip("spi"))
            with st.expander(tr("🧮 Como chegámos a estes valores?", "🧮 How did we get these values?"), expanded=False):
                st.markdown(W.explain(p, code, ro, ev, cur))
            if r.get("start"):
                st.caption(f"{d(r['start'])} → {d(r['finish'])}" + (" · 🔴 " + tr("no caminho crítico", "on the critical path") if r.get("critical") else ""))
            with st.form(f"wbs_dict_{code}_{st.session_state.dv}"):
                f1, f2 = st.columns(2)
                desc = f1.text_area(tr("Descrição do âmbito (o que inclui / o que exclui)", "Scope description (what is in / out)"), e.get("description", ""), height=110)
                deliv = f2.text_area(tr("Entregável", "Deliverable"), e.get("deliverable", ""), height=110)
                acc = f1.text_area(tr("Critérios de aceitação", "Acceptance criteria"), e.get("acceptance", ""), height=110)
                own = f2.text_input(tr("Responsável", "Owner"), e.get("owner", ""))
                outs = _outputs(p)
                oc2 = f2.selectbox(tr("Output do quadro lógico", "Logframe output"), outs, index=outs.index(str(e.get("output_code") or "")) if str(e.get("output_code") or "") in outs else 0)
                if st.form_submit_button(tr("💾 Guardar ficha", "💾 Save entry"), type="primary"):
                    e.update(description=desc, deliverable=deliv, acceptance=acc, owner=own, output_code=oc2)
                    ui.bump()
                    st.rerun()
            if dct["output_text"]:
                st.caption(tr("Output do quadro lógico: ", "Logframe output: ") + f"{e.get('output_code')} — {dct['output_text']}")
            g1, g2 = st.columns(2)
            with g1:
                st.markdown(tr("**Atividades**", "**Activities**"))
                if dct["activities"]:
                    tab = sched["acts"].set_index("id") if sched else None
                    st.dataframe(pd.DataFrame([{"ID": a["id"], tr("Atividade", "Activity"): a.get("name"), tr("Responsável", "Owner"): a.get("responsible"),
                                                tr("Custo", "Cost"): activity_cost(p, a),
                                                tr("Crítica", "Critical"): ("🔴" if tab is not None and a["id"] in tab.index and tab.loc[a["id"], "critical"] else "")} for a in dct["activities"]])
                                 .style.format({tr("Custo", "Cost"): "{:,.0f}"}), hide_index=True, width="stretch")
                else:
                    st.caption("—")
                st.markdown(tr("**Marcos**", "**Milestones**"))
                st.caption("; ".join(f"{x['id']} {x.get('name', '')}" for x in dct["milestones"]) or "—")
                st.markdown(tr("**Responsabilidades (RACI do pacote)**", "**Responsibilities (package RACI)**"), help=wbs_tip("raci_wp"))
                st.caption(" · ".join(f"{k_}: {v}" for k_, v in dct["raci"].items()) or tr("— (definir em 3 · RACI, vista por pacote de trabalho)", "— (set in 3 · RACI, work-package view)"))
            with g2:
                st.markdown(tr("**Riscos**", "**Risks**"))
                st.caption("; ".join(f"{x['id']} {x.get('description', '')[:80]} (L×I {int(x.get('likelihood') or 0) * int(x.get('impact') or 0)})" for x in dct["risks"]) or "—")
                st.markdown(tr("**Linhas de orçamento**", "**Budget lines**"))
                st.caption("; ".join(f"{x['id']} {x.get('item', '')}" for x in dct["budget"]) or "—")
                st.markdown(tr("**Aquisições**", "**Procurement**"))
                st.caption("; ".join(f"{x['id']} {x.get('item', '')}" for x in dct["procurement"]) or "—")
            md = _dictionary_md(p, ro, cur)
            st.download_button(tr("⬇️ Descarregar dicionário completo (Markdown)", "⬇️ Download full dictionary (Markdown)"), md.encode("utf-8"), "dicionario_wbs.md", "text/markdown")

    # ------------------------------------------------------------------ checks & AI
    with t5:
        if not ch:
            st.success(tr("Sem problemas: a WBS cumpre a regra dos 100%, não tem filhos únicos e o dicionário está completo. ✅",
                          "No issues: the WBS meets the 100% rule, has no single children and the dictionary is complete. ✅"))
        for sev, fn in (("error", st.error), ("warn", st.warning), ("info", st.info)):
            items = [x for x in ch if x["sev"] == sev]
            if items:
                fn("\n".join(f"- {x['msg']}" for x in items))
        st.caption(tr("Todas as verificações são **avisos de qualidade**: não impedem o uso do resto da app.", "All checks are **quality warnings**: they never block the rest of the app."))
        st.caption("🧮 " + W.rule_arithmetic(p) + " " + tr("Duração de um pacote = EF máx. − ES mín. das suas atividades.", "Package duration = max EF − min ES of its activities."))
        with st.expander(tr("📚 Regras de uma boa WBS", "📚 Rules of a good WBS")):
            st.markdown(tr("""- **Regra dos 100%** — a WBS inclui 100% do trabalho do projeto (e nada fora do âmbito); os filhos de cada elemento somam 100% do trabalho do pai.
- **Orientada a entregáveis** — os elementos são *o que* se entrega (substantivos), não *como* (verbos); as atividades ficam no cronograma.
- **Mutuamente exclusiva** — nenhum trabalho aparece em dois ramos (evita dupla contagem de custo e esforço).
- **Pacote de trabalho** — o nível mais baixo: estimável, atribuível a um responsável e verificável (critérios de aceitação).
- **Regra 8/80** — um pacote deve ter entre 8 e 80 horas de trabalho; em projetos longos usa-se a **regra do período de reporte** (um pacote não deve ultrapassar um período de reporte).
- **Conta de controlo** — ponto de gestão onde se integram âmbito, prazo e custo e se mede o desempenho (EVM).
- **Dicionário da WBS** — para cada pacote: âmbito, entregável, critérios de aceitação, responsável, atividades, custo, marcos e riscos.""",
                           """- **100% rule** — the WBS includes 100% of the project's work (and nothing out of scope); the children of each element add up to 100% of the parent's work.
- **Deliverable-oriented** — elements are *what* is delivered (nouns), not *how* (verbs); activities belong to the schedule.
- **Mutually exclusive** — no work appears in two branches (avoids double counting of cost and effort).
- **Work package** — the lowest level: estimable, assignable to an owner and verifiable (acceptance criteria).
- **8/80 rule** — a package should take between 8 and 80 hours of work; in long projects the **reporting-period rule** is used (a package should not exceed one reporting period).
- **Control account** — management point where scope, schedule and cost are integrated and performance is measured (EVM).
- **WBS dictionary** — for each package: scope, deliverable, acceptance criteria, owner, activities, cost, milestones and risks."""))
        c1, c2 = st.columns(2)
        with c1:
            ui.ai_text("Rever a WBS (regras 100% e 8/80, dicionário)", "Review the WBS (100% and 8/80 rules, dictionary)", "wbs_review",
                       lambda: AG.wbs_review(p, st.session_state.get("ai_model")))
        with c2:
            ui.ai_tables("Propor WBS com dicionário", "Propose WBS with dictionary", "wbs_gen", lambda: AG.gen_wbs(p, ori, st.session_state.get("ai_model")), after=_after_ai)
            st.caption(tr("Ao aplicar a proposta do agente, as atividades são ligadas automaticamente aos pacotes pelo output.",
                          "When applying the agent's proposal, activities are linked automatically to packages by output."))

    # ------------------------------------------------------------------ glossary
    with t6:
        _glossary_tab()


def _glossary_tab():
    st.markdown(tr("Todas as fórmulas usadas na WBS / EAP, na app, no relatório e no Excel vêm deste glossário (fonte única).",
                   "Every formula used for the WBS in the app, the report and Excel comes from this glossary (single source)."))
    df = pd.DataFrame([{tr("Termo", "Term"): wbs_term(k)[0], tr("Fórmula", "Formula"): wbs_term(k)[1], tr("O que significa", "What it means"): wbs_term(k)[2],
                        tr("Fonte", "Source"): ", ".join(g["src"])} for k, g in WBS_GLOSSARY.items()])
    st.table(df.set_index(tr("Termo", "Term")))     # st.table wraps long formulas (no truncation)
    st.caption(tr("Fontes: ", "Sources: ") + " · ".join(f"**{k}** — {SRC[k]}" for k in sorted({s_ for g in WBS_GLOSSARY.values() for s_ in g["src"]})))
    md = "\n".join([f"# {tr('Glossário da WBS / EAP', 'WBS glossary')}\n"] + [f"## {wbs_term(k)[0]}\n\n- **{tr('Fórmula', 'Formula')}:** {wbs_term(k)[1]}\n- **{tr('Significado', 'Meaning')}:** {wbs_term(k)[2]}\n" for k in WBS_GLOSSARY])
    st.download_button(tr("⬇️ Descarregar glossário (Markdown)", "⬇️ Download glossary (Markdown)"), md.encode("utf-8"), "glossario_wbs.md", "text/markdown")


def _after_ai(p: dict) -> None:
    valid = {e["code"] for e in W.leaves(p)}
    for a in p["activities"]:
        if a.get("wbs_code") not in valid:
            a["wbs_code"] = ""
    W.auto_assign(p)
    codes = {e["code"] for e in W.elements(p)}
    for r in p["risks"]:
        if r.get("wbs_code") and r["wbs_code"] not in codes:
            r["wbs_code"] = ""


def _dictionary_md(p: dict, ro: dict, cur: str) -> str:
    out = [f"# {tr('Dicionário da WBS', 'WBS dictionary')} — {p['meta'].get('name', '')}\n"]
    for e in W.elements(p):
        r = ro.get(e["code"], {})
        out.append(f"## {W.label(e)}\n")
        out.append(f"- **{tr('Tipo', 'Type')}:** {opt_label('wbs_type', e.get('type'))}")
        out.append(f"- **BAC:** {money(r.get('BAC', 0), cur)}" + (f" · {d(r['start'])} → {d(r['finish'])}" if r.get("start") else ""))
        for f, lab in (("description", tr("Âmbito", "Scope")), ("deliverable", tr("Entregável", "Deliverable")), ("acceptance", tr("Critérios de aceitação", "Acceptance criteria")),
                       ("owner", tr("Responsável", "Owner")), ("output_code", "Output")):
            if e.get(f):
                out.append(f"- **{lab}:** {e[f]}")
        if r.get("leaf"):
            acts = [a for a in p["activities"] if a.get("wbs_code") == e["code"]]
            if acts:
                out.append(f"- **{tr('Atividades', 'Activities')}:** " + "; ".join(f"{a['id']} {a.get('name', '')} ({money(activity_cost(p, a), cur)})" for a in acts))
        out.append("")
    return "\n".join(out)
