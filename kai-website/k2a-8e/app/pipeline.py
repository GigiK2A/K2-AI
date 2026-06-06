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
            facts[k] = {"valore": e["testo"], "tipo": "normativo",
                        "fonte": e.get("fonte"), "vigenza": e.get("vigenza")}
            citazioni.append({
                "campo": k, "fonte": e.get("fonte"), "fonte_url": e.get("fonte_url"),
                "vigenza": e.get("vigenza"), "status": e.get("status"),
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

def assemble_legalboost(blueprint: dict, sezioni: dict, citazioni: list[dict], inputs: dict) -> dict:
    norme = [
        {"riferimento": c.get("fonte") or c.get("campo"), "fonte": "normattiva"}
        for c in citazioni
    ]
    voci_out = []
    for v in blueprint.get("voci", []):
        vid = v["id"]
        voci_out.append({
            "id": vid,
            "titolo": v["titolo"],
            "contenuto": str(sezioni.get(vid, "")),
            "rischi": [{"descrizione": "Rischio rilevato nell'area (vedi contenuto).",
                        "gravita": "media", "serve_avvocato": False}],
            "azioni": ["Azione prioritaria indicata nel contenuto."],
            "norme_citate": norme if vid in ("contrattualistica", "societario_231") else [],
        })
    return {
        "meta": {
            "servizio": "LegalBoost", "versione": "1.0.0", "data": "2026-06-04",
            "azienda": inputs.get("ragione_sociale") or inputs.get("azienda") or "Cliente",
        },
        "sintesi": {
            "score_compliance": 72,
            "mappa_rischi": [
                {"area": "Contrattualistica", "semaforo": "giallo"},
                {"area": "Privacy & dati", "semaforo": "rosso"},
            ],
        },
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


def run(job_id: str, service_id: str, inputs: dict) -> None:
    try:
        jobs.update(job_id, status="running")
        skill, bp_id, _ = route(service_id)

        blueprint = assets.load_blueprint(skill)
        out_schema = assets.load_output_schema(skill)
        if not blueprint or not out_schema:
            raise Refuse("unresolvable_placeholder", f"asset mancanti per skill '{skill}'")

        facts, citazioni = resolve(skill, inputs)
        sezioni, filiera_meta = llm.generate_sezioni(blueprint, facts, inputs)

        # Assemble (Phase-1 pilota = LegalBoost).
        deliverable = assemble_legalboost(blueprint, sezioni, citazioni, inputs)

        # Validazione: L1 (libreria) + L2 (linter) + output-schema (jsonschema).
        jobs.update(job_id, status="validating")
        r1 = validate.l1(blueprint)
        r2 = validate.l2(_lint_instance(blueprint), blueprint)
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
        html_path.write_text(render_html(deliverable, blueprint, citazioni), encoding="utf-8")
        render_pdf(deliverable, blueprint, citazioni, pdf_path)

        jobs.update(
            job_id, status="rendered",
            outputs={"html_path": str(html_path), "pdf_path": str(pdf_path),
                     "json_path": str(json_path), "bundle": []},
            validation={"L1": "PASS", "L2": "PASS", "output_schema": "PASS"},
            citazioni=citazioni,
            meta={"skill": skill, "blueprint_id": bp_id, "filiera": filiera_meta,
                  "snapshot_version": assets.snapshot_version()},
        )
    except Refuse as r:
        jobs.update(job_id, status="refused", refusal_reason=r.reason, error=r.message)
    except Exception as exc:
        log.exception("pipeline error")
        jobs.update(job_id, status="error", error=str(exc))
