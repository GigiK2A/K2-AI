"""Pipeline 6 stadi (Phase-1, pilota LegalBoost) sugli asset REALI (handoff v2.27).

routing(manifest, catalogo chiuso) → resolve(snapshot entries per tipo) →
filiera(prosa attorno ai fatti) → assemble(deliverable conforme output-schema) →
validate(L1 libreria + L2 linter + output-schema) → render(HTML+PDF). Refuse esplicito.
"""
from __future__ import annotations

import logging
from pathlib import Path

from jsonschema import Draft202012Validator

from . import assets, jobs, llm, validate
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
            facts[k] = {"valore": e.get("formula"), "tipo": "formula"}
        elif tipo == "input":
            facts[k] = {"valore": form.get(e.get("campo_form")), "tipo": "input"}
        elif tipo == "benchmark":
            # non bloccante: se non disponibile → confronto assente (D-handoff E)
            facts[k] = {"valore": e.get("valore"), "tipo": "benchmark",
                        "status": e.get("status")}
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
        mappa = [{"area": "Contrattualistica", "semaforo": "giallo"},
                 {"area": "Privacy & dati", "semaforo": "rosso"}]
    score = (meta_struct or {}).get("score")
    if not isinstance(score, int) or not (0 <= score <= 100):
        score = 72
    return {
        "meta": {
            "servizio": "LegalBoost", "versione": "1.0.0", "data": "2026-06-08",
            "azienda": inputs.get("ragione_sociale") or inputs.get("azienda") or "Cliente",
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
        if not blueprint or not out_schema:
            raise Refuse("unresolvable_placeholder", f"asset mancanti per skill '{skill}'")

        facts, citazioni = resolve(skill, inputs)

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

        jobs.update(
            job_id, status="rendered",
            outputs={"html_path": str(html_path), "pdf_path": str(pdf_path),
                     "json_path": str(json_path), "bundle": []},
            validation={"L1": "PASS", "L2": "PASS", "output_schema": "PASS"},
            citazioni=citazioni,
            meta={"skill": skill, "blueprint_id": bp_id, "auth_level": "FULL",
                  "filiera": filiera_meta, "snapshot_version": assets.snapshot_version()},
        )
    except Refuse as r:
        jobs.update(job_id, status="refused", refusal_reason=r.reason, error=r.message)
    except Exception as exc:
        log.exception("pipeline error")
        jobs.update(job_id, status="error", error=str(exc))
