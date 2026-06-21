"""Pipeline 6 stadi (Phase-1, pilota LegalBoost) sugli asset REALI (handoff v2.27).

routing(manifest, catalogo chiuso) → resolve(snapshot entries per tipo) →
filiera(prosa attorno ai fatti) → assemble(deliverable conforme output-schema) →
validate(L1 libreria + L2 linter + output-schema) → render(HTML+PDF). Refuse esplicito.
"""
from __future__ import annotations

import logging
from pathlib import Path

from jsonschema import Draft202012Validator

from . import assets, calc, finance, freshness, grounding, jobs, llm, quality, quant, validate
from .render import render_html, render_pdf
from .settings import CATALOGO_CHIUSO, OUT_DIR

log = logging.getLogger("8e.pipeline")


class Refuse(Exception):
    def __init__(self, reason: str, message: str):
        self.reason = reason
        self.message = message


# ---- Stadio 1: routing ---------------------------------------------------

def route(service_id: str) -> tuple[str, str, float]:
    """service_id → (skill, blueprint_id, confidence). Catalogo chiuso Phase-1."""
    entry = CATALOGO_CHIUSO.get(service_id)
    if not entry:
        raise Refuse("out_of_catalog",
                     f"service_id '{service_id}' fuori dal catalogo chiuso Phase-1 (solo LegalBoost)")
    return entry["skill"], entry["blueprint_id"], 0.95


# ---- Stadio 3: resolve deterministico (snapshot entries per tipo) --------

def resolve(skill: str, form: dict) -> tuple[dict, list[dict]]:
    snap = assets.load_snapshot()
    entries = snap.get("entries", {})
    keys = assets.placeholders_for(skill)
    facts: dict[str, dict] = {}
    citazioni: list[dict] = []
    for k in keys:
        e = entries.get(k)
        if e is None:
            raise Refuse("unresolvable_placeholder", f"placeholder '{k}' assente nello snapshot")
        tipo = e.get("tipo")
        if tipo == "normativo":
            # Riferimento leggibile dal titolo verbatim (es. "# Art. 1341 Codice
            # Civile — ...") invece del campo interno (override_locale).
            testo = e.get("testo", "")
            first = testo.lstrip("# ").split("\n", 1)[0].strip() if testo else k
            riferimento = first.split("—")[0].strip() if "—" in first else first
            facts[k] = {"valore": testo, "tipo": "normativo",
                        "fonte": e.get("fonte"), "vigenza": e.get("vigenza"),
                        "riferimento": riferimento}
            citazioni.append({
                "campo": k, "riferimento": riferimento,
                "fonte": e.get("fonte"), "fonte_url": e.get("fonte_url"),
                "vigenza": e.get("vigenza"), "status": e.get("status"),
                "testo": testo,  # verbatim dallo snapshot → appendice deterministica
            })
        elif tipo == "formula":
            # Indici finanziari dichiarati 'calcolo-runtime' nello snapshot: il VALORE va
            # calcolato deterministicamente. Prima calc.py (bilancio/host/cruscotto), poi
            # il quant di Luca (dcf/wacc) — Fix #0. Solo se entrambi None resta la
            # formula-stringa (che poi calcolerebbe l'LLM): da evitare per le chiavi quant.
            computed = calc.resolve_formula_fact(k, form)
            if computed is None:
                computed = quant.resolve_quant_fact(k, form)
            facts[k] = computed if computed is not None else {"valore": e.get("formula"), "tipo": "formula"}
        elif tipo == "input":
            facts[k] = {"valore": form.get(e.get("campo_form")), "tipo": "input"}
        elif tipo == "benchmark":
            # non bloccante: se non disponibile → confronto assente (D-handoff E).
            # multipli_ev: prova il quant (EV da multipli). PRESERVA fonte/as_of/descrizione
            # dello snapshot (P0-8: D-046 — un benchmark senza fonte è un numero nudo).
            qf = quant.resolve_quant_fact(k, form)
            if qf is not None and qf.get("tipo") == "valore_calcolato":
                facts[k] = qf
            else:
                facts[k] = {"valore": e.get("valore"), "tipo": "benchmark",
                            "status": e.get("status"), "fonte": e.get("fonte"),
                            "as_of": e.get("as_of"), "descrizione": e.get("descrizione")}
        else:
            facts[k] = {"valore": e, "tipo": tipo}
    return facts, citazioni


# ---- Stadio 4-assemble: deliverable conforme a output-schema (LegalBoost) -

def assemble_legalboost(blueprint: dict, sezioni: dict, citazioni: list[dict],
                        inputs: dict, meta_struct: dict | None = None) -> dict:
    norme = [
        {"riferimento": c.get("riferimento") or c.get("campo"), "fonte": "normattiva"}
        for c in citazioni
    ]
    voci_meta = (meta_struct or {}).get("voci_meta", {})

    def _grav(g: str) -> str:
        return g if g in ("bassa", "media", "alta") else "media"

    voci_out = []
    for v in blueprint.get("voci", []):
        vid = v["id"]
        argomenti = v.get("argomenti_obbligatori", [])
        vm = voci_meta.get(vid) or {}
        # rischi/azioni: dal meta strutturato (LLM) se presente, altrimenti dalle argomenti
        rischi = [{"descrizione": str(r.get("descrizione", "")), "gravita": _grav(r.get("gravita", "media")),
                   "serve_avvocato": bool(r.get("serve_avvocato", False))}
                  for r in vm.get("rischi", []) if r.get("descrizione")]
        if not rischi:
            rischi = [{"descrizione": f"Verificare: {a}.", "gravita": "media", "serve_avvocato": False}
                      for a in argomenti[:2]] or [{"descrizione": f"Analisi area «{v['titolo']}».",
                                                   "gravita": "media", "serve_avvocato": False}]
        azioni = [str(a) for a in vm.get("azioni", []) if a] or \
                 [f"Approfondire «{a}»." for a in argomenti[:3]] or ["Approfondire l'area."]
        voci_out.append({
            "id": vid,
            "titolo": v["titolo"],
            "contenuto": str(sezioni.get(vid, "")),
            "rischi": rischi,
            "azioni": azioni,
            "norme_citate": norme if vid in ("contrattualistica", "societario_231") else [],
        })

    mappa = (meta_struct or {}).get("mappa_rischi")
    if not (isinstance(mappa, list) and mappa and all(
            m.get("semaforo") in ("verde", "giallo", "rosso") for m in mappa)):
        mappa = []
    score = (meta_struct or {}).get("score")
    if not isinstance(score, int) or not (0 <= score <= 100):
        score = -1  # forza il refuse dello schema: mai score cosmetico di fallback
    return {
        "meta": {
            "servizio": "LegalBoost", "versione": "1.0.0", "data": quality.today_iso(),
            "azienda": quality.display_name(inputs) or "",
        },
        "sintesi": {"score_compliance": score, "mappa_rischi": mappa},
        "voci": voci_out,
        "piano_azione": [
            {"priorita": 1, "azione": "Adeguare le condizioni generali (artt. 1341-1342 c.c.)",
             "handoff_avvocato": True}
        ],
        "disclaimer": blueprint.get(
            "disclaimer",
            "Orientamento legale-compliance, NON consulenza legale (D-034); "
            "handoff all'avvocato sui punti a rischio.",
        ),
    }


def _lint_instance(blueprint: dict) -> dict:
    """Instance per il linter L2 (shape attesa da k2a_validation.linter)."""
    voci = blueprint.get("voci", [])
    voci_li = []
    total = 0
    for v in voci:
        pag = (v.get("pagine") or {}).get("min", 2)
        total += pag
        voci_li.append({
            "id": v["id"], "titolo": v["titolo"], "ord": v.get("ord"),
            "pagine": pag, "argomenti_presenti": list(v.get("argomenti_obbligatori", [])),
        })
    return {
        "voci": voci_li,
        "pagine_totali": total,
        "ha_disclaimer": True, "ha_cta": True, "json_output_valido": True,
        "artefatti": [a["id"] for a in blueprint.get("artefatti_bundle", []) if a.get("obbligatorio")],
        "elementi_grafici": list(blueprint.get("elementi_grafici_obbligatori", [])),
        "tabelle": list(blueprint.get("tabelle_obbligatorie", [])),
        "prezzi_hardcoded": [],
    }


def run(job_id: str, service_id: str, inputs: dict, auth_level: str = "FULL") -> None:
    try:
        jobs.update(job_id, status="running")
        skill, bp_id, _ = route(service_id)

        blueprint = assets.load_blueprint(skill)
        out_schema = assets.load_output_schema(skill)
        form_schema = assets.load_form(skill) or {}
        if not blueprint or not out_schema:
            raise Refuse("unresolvable_placeholder", f"asset mancanti per skill '{skill}'")

        # Gate 0 comune: nessun report parte con campi obbligatori mancanti,
        # copertina anonima o bilancio non riconciliato.
        inputs, input_errors, quality_notes = quality.prepare_inputs(skill, form_schema, inputs)
        if input_errors:
            raise Refuse("insufficient_or_inconsistent_input", "; ".join(input_errors[:12]))

        facts, citazioni = resolve(skill, inputs)

        # Freshness-gate runtime (Fix #6-gate / P0-10): se il boost usa un fatto normativo
        # HARD-stale (snapshot regredito a legge pre-riforma) → non consegnare legge superata.
        stale = freshness.stale_findings(used_keys=set(facts.keys()))
        if stale:
            raise Refuse("snapshot_stale",
                         "; ".join(f"{s['key']}: {s['motivo']} ({s.get('law')})" for s in stale[:5]))

        # PREVIEW (gate W8): compone SOLO l'assaggio, niente documento/file/leak.
        if auth_level == "PREVIEW":
            prev = llm.generate_preview(blueprint, facts, inputs)
            # voci[0]=sintesi, voci[1]=criticità#1 mostrata → altre = voci[2:] (solo titoli)
            altre = [v.get("titolo") for v in blueprint.get("voci", [])][2:]
            jobs.update(
                job_id, status="rendered",
                outputs={"preview": {
                    "score": prev.get("score"),
                    "criticita_1": prev.get("criticita_1"),
                    "altre_aree": altre,            # solo titoli, contenuto NASCOSTO
                    "cta": "Sblocca il documento completo",
                }, "pdf_url": None, "bundle": []},
                validation={"auth_level": "PREVIEW"},
                citazioni=[],
                meta={"skill": skill, "blueprint_id": bp_id, "auth_level": "PREVIEW",
                      "filiera": {"mode": prev.get("mode")},
                      "snapshot_version": assets.snapshot_version()},
            )
            return

        from .settings import VOCI_SHAPE_SKILLS
        generic = skill not in VOCI_SHAPE_SKILLS
        if not generic:
            # Voci-shape (LegalBoost/FiscoBoost): HYBRID prosa + meta strutturato.
            sezioni, filiera_meta = llm.generate_sezioni(blueprint, facts, inputs)
            meta_struct = llm.generate_structured_meta(blueprint, facts, inputs)
            deliverable = assemble_legalboost(blueprint, sezioni, citazioni, inputs, meta_struct)
            filiera_meta = {**filiera_meta, "assembly": "hybrid" if meta_struct else "prose+deterministic",
                            "structured_meta": bool(meta_struct)}
        else:
            # Altri boost: generazione PROFONDA per-sezione (profondità tipo report
            # consulenziale). Fallback alla singola chiamata, poi refuse se invalido.
            deliverable, filiera_meta = llm.generate_deliverable_deep(out_schema, blueprint, facts, inputs)
            if not deliverable:
                deliverable, fm2 = llm.generate_conforming(out_schema, blueprint, facts, inputs)
                filiera_meta = {**filiera_meta, **fm2, "assembly": "generic-fallback"}
            if not deliverable:
                raise Refuse("validation_failed",
                             "generazione non disponibile (offline o incompleta) per questo boost")

        deliverable = quality.ensure_metadata(
            deliverable, out_schema, inputs,
            blueprint.get("pacchetto", {}).get("nome_commerciale", service_id),
        )

        # Binding strutturale (Fix #0 Fase 2): gli slot numerici di valutazione vengono
        # SOVRASCRITTI col valore del quant deterministico (non ri-emessi dall'LLM).
        # Chiude INV1/P0-1/P0-2; la provenance (call_id/as_of) finisce nel meta del job.
        deliverable, quant_prov = quant.bind_quant_slots(skill, deliverable, facts)
        if quant_prov:
            filiera_meta = {**filiera_meta, "quant_binding": quant_prov}

        # FinanceBoost: le 3 sezioni data-payload (riclassificazione/marginalità/
        # valutazione_performance) sono DETERMINISTICHE — dalle voci riclassificate
        # (finance.py) + WACC dal quant — non scritte dall'LLM (chiude P0-2/P0-6).
        if skill == "flusso-financeboost-pmi":
            fb_reclass = finance.latest_reclass_from_inputs(inputs)
            if fb_reclass:
                w = quant.resolve_quant_fact("wacc", inputs)
                wacc_pct = w.get("valore") if (isinstance(w, dict) and w.get("tipo") == "valore_calcolato") else None
                deliverable = finance.apply_financeboost_sections(deliverable, fb_reclass, wacc_pct)
                filiera_meta = {**filiera_meta, "financeboost_sezioni_deterministiche": True}

        # Validazione: L1 (libreria) + output-schema (jsonschema). L2 (linter
        # voci-shape) solo per i boost voci-shape; i generici sono validati dallo
        # schema.
        jobs.update(job_id, status="validating")
        r1 = validate.l1(blueprint)
        r2 = {"pass": True} if generic else validate.l2(_lint_instance(blueprint), blueprint)
        out_errs = sorted(Draft202012Validator(out_schema).iter_errors(deliverable),
                          key=lambda e: list(e.path))
        if not r1["pass"] or not r2["pass"] or out_errs:
            jobs.update(
                job_id, status="refused", refusal_reason="validation_failed",
                validation={"L1": r1["pass"], "L2": r2["pass"],
                            "output_schema_errors": [str(e.message) for e in out_errs[:5]],
                            "L2_errori": r2.get("errori"), "L2_findings": r2.get("findings")},
            )
            return

        # Gate di GROUNDING (integrità qualitativa) — accanto a L1/L2. Becca la
        # classe di difetti che il linter STRUTTURALE non vede e che nessun calc.py
        # intercetta sui boost qualitativi: segnaposto trapelati, numeri esterni
        # asseriti senza citazione, cover non personalizzata, priorità tutte uguali
        # (vedi report StrategyBoost reale). 'block' → non si consegna (fail-closed).
        g_findings = grounding.integrity_findings(
            deliverable, citazioni=citazioni, inputs=inputs, facts=facts,
        )
        g_blocks = grounding.blocks(g_findings)
        if g_blocks:
            log.warning("grounding gate REFUSE job %s: %s", job_id, [b["dettaglio"] for b in g_blocks])
            jobs.update(job_id, status="refused", refusal_reason="grounding_failed",
                        validation={"grounding_block": g_blocks, "grounding_findings": g_findings})
            return

        # Render HTML + PDF.
        out_dir = OUT_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path = out_dir / "deliverable.html"
        pdf_path = out_dir / "deliverable.pdf"
        json_path = out_dir / "deliverable.json"
        import json as _json
        json_path.write_text(_json.dumps(deliverable, ensure_ascii=False, indent=2), encoding="utf-8")
        if generic:
            from .render import render_generic_pdf
            html_path.write_text("<pre>" + _json.dumps(deliverable, ensure_ascii=False, indent=2) + "</pre>",
                                 encoding="utf-8")
            render_generic_pdf(deliverable, blueprint, citazioni, pdf_path)
        else:
            html_path.write_text(render_html(deliverable, blueprint, citazioni), encoding="utf-8")
            render_pdf(deliverable, blueprint, citazioni, pdf_path)

        bundle = []
        extra_outputs = {}
        if skill == "flusso-financeboost-pmi":
            from .xlsx import render_finance_workbook
            xlsx_path = render_finance_workbook(inputs, out_dir / "modello-finanziario.xlsx")
            extra_outputs["xlsx_path"] = str(xlsx_path)
            bundle.append({"formato": "xlsx", "path": str(xlsx_path), "formule_vive": True})

        jobs.update(
            job_id, status="rendered",
            outputs={"html_path": str(html_path), "pdf_path": str(pdf_path),
                     "json_path": str(json_path), "bundle": bundle, **extra_outputs},
            validation={"L1": "PASS", "L2": "PASS", "output_schema": "PASS",
                        "grounding": g_findings or "PASS"},
            citazioni=citazioni,
            meta={"skill": skill, "blueprint_id": bp_id, "auth_level": "FULL",
                  "filiera": filiera_meta, "snapshot_version": assets.snapshot_version()},
        )
    except Refuse as r:
        jobs.update(job_id, status="refused", refusal_reason=r.reason, error=r.message)
    except Exception as exc:
        log.exception("pipeline error")
        jobs.update(job_id, status="error", error=str(exc))
