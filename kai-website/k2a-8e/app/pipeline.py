"""Pipeline 6 stadi (Phase-1, solo LegalBoost).

routing → resolve(deterministico da snapshot) → filiera(prosa) → validate(L1+L2)
→ render(HTML+PDF) → output. Ogni rifiuto è esplicito (route-or-refuse).
"""
from __future__ import annotations

import logging
from pathlib import Path

from . import assets, jobs, llm, validate
from .render import render_html, render_pdf
from .settings import CATALOGO_CHIUSO, OUT_DIR

log = logging.getLogger("8e.pipeline")


class Refuse(Exception):
    def __init__(self, reason: str, message: str):
        self.reason = reason
        self.message = message


# ---- Stadio 1: routing ---------------------------------------------------

def route(service_id: str) -> tuple[str, float]:
    """service_id → blueprint_id (catalogo chiuso). Refuse se fuori catalogo."""
    bp = CATALOGO_CHIUSO.get(service_id)
    if not bp:
        raise Refuse("out_of_catalog", f"service_id '{service_id}' non nel catalogo chiuso")
    return bp, 0.95  # UI struttura → confidence alta


# ---- Stadio 3: resolve deterministico -----------------------------------

def resolve_facts(output_schema: dict, snapshot: dict) -> tuple[dict, list[dict]]:
    """Per ogni placeholder deterministico dichiarato → valore dallo snapshot.

    Ritorna (facts {chiave: voce_snapshot}, citazioni[]). Manca → Refuse.
    """
    facts: dict[str, dict] = {}
    citazioni: list[dict] = []
    placeholders = output_schema.get("deterministici", [])
    for ph in placeholders:
        chiave = ph.get("chiave")
        snap = snapshot.get(chiave)
        if not snap:
            raise Refuse("unresolvable_placeholder",
                         f"placeholder '{chiave}' non risolto nello snapshot")
        facts[chiave] = snap
        citazioni.append({
            "campo": ph.get("campo", chiave),
            "fonte": snap.get("fonte"),
            "coordinate": snap.get("coordinate"),
            "vigenza": snap.get("vigenza"),
            "status": snap.get("status"),
        })
    return facts, citazioni


def run(job_id: str, service_id: str, inputs: dict) -> None:
    """Esegue la pipeline e aggiorna lo job store. Tutte le eccezioni → refuse/error."""
    try:
        jobs.update(job_id, status="running")
        blueprint_id, _conf = route(service_id)

        blueprint, bp_src = assets.load_blueprint(blueprint_id)
        if not blueprint:
            raise Refuse("out_of_catalog", f"blueprint '{blueprint_id}' assente")
        output_schema, _ = assets.load_output_schema(service_id)
        if not output_schema:
            raise Refuse("unresolvable_placeholder", "output-schema assente")
        snapshot, snap_src = assets.load_snapshot()

        # Stadio 3: resolve (fatti deterministici).
        facts, citazioni = resolve_facts(output_schema, snapshot)

        # Stadio 2: filiera (prosa attorno ai fatti).
        sezioni, mode = llm.generate_sezioni(blueprint, facts, inputs)

        # Assembla istanza.
        instance = {
            "sezioni": sezioni,
            "citazioni": citazioni,
            "disclaimer": blueprint.get(
                "disclaimer",
                "Documento informativo, non sostituisce parere legale. "
                "Verificare la vigenza delle norme citate.",
            ),
        }

        # Stadio 4: validate L1 + L2.
        jobs.update(job_id, status="validating")
        l1 = validate.validate_blueprint(instance, blueprint)
        l2 = validate.lint_deliverable(instance, blueprint)
        if l1["result"] != "PASS" or l2["result"] != "PASS":
            jobs.update(
                job_id, status="refused", refusal_reason="validation_failed",
                validation={"L1": l1, "L2": l2},
            )
            return

        # Stadio 5: render.
        out_dir = OUT_DIR / job_id
        html_path = out_dir / "deliverable.html"
        pdf_path = out_dir / "deliverable.pdf"
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_html(instance, blueprint), encoding="utf-8")
        render_pdf(instance, blueprint, pdf_path)

        # Stadio 6: output (Phase-1 = path locali; prod = upload K-BOT).
        jobs.update(
            job_id,
            status="rendered",
            outputs={
                "html_path": str(html_path),
                "pdf_path": str(pdf_path),
                "bundle": [],
            },
            validation={"L1": l1["result"], "L2": l2["result"]},
            citazioni=citazioni,
            meta={
                "blueprint_source": bp_src,
                "snapshot_source": snap_src,
                "filiera_mode": mode,
            },
        )
    except Refuse as r:
        jobs.update(job_id, status="refused", refusal_reason=r.reason, error=r.message)
    except Exception as exc:
        log.exception("pipeline error")
        jobs.update(job_id, status="error", error=str(exc))
