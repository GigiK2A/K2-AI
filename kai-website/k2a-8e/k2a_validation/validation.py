"""Funzioni pure L1/L2 — port da k2a-mcp-deliverable/server.py (*_impl), senza MCP.

Dipendenze: jsonschema>=4.20 (solo per L1), stdlib. `linter.py` (puro) per L2.
Nessun percorso assoluto: il meta-schema è incluso nel pacchetto (default_meta_schema)
oppure passato come dict.
"""
from __future__ import annotations

import json
import os
from typing import Any

from jsonschema import Draft202012Validator

from . import linter

_META_PATH = os.path.join(os.path.dirname(__file__), "deliverable-blueprint.schema.json")


def default_meta_schema() -> dict:
    """Carica la copia del meta-schema inclusa nel pacchetto."""
    with open(_META_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate_blueprint(blueprint: dict, meta_schema: dict | None = None) -> dict:
    """LIVELLO 1 — blueprint ben formato rispetto al meta-schema.

    Args:
        blueprint: dict del blueprint (già caricato; nessuna risoluzione da disco).
        meta_schema: dict del meta-schema; se None usa la copia inclusa.
    Returns:
        {"pass": bool, "livello": 1, "skill": ..., "tier": ..., "errors": [{path,messaggio}]}
    """
    meta = meta_schema if meta_schema is not None else default_meta_schema()
    Draft202012Validator.check_schema(meta)
    v = Draft202012Validator(meta)
    errs = sorted(v.iter_errors(blueprint), key=lambda e: list(e.path))
    pkg = blueprint.get("pacchetto", {})
    return {
        "pass": not errs,
        "livello": 1,
        "skill": pkg.get("skill"),
        "tier": pkg.get("tier"),
        "errors": [{"path": list(e.path), "messaggio": e.message} for e in errs],
    }


def lint_deliverable(deliverable: dict, blueprint: dict) -> dict:
    """LIVELLO 2 — deliverable conforme al blueprint (stesso linter del MCP).

    Args:
        deliverable: instance strutturata (voci, pagine, artefatti, flag).
        blueprint: dict del blueprint.
    Returns:
        {"pass": bool, "livello": 2, "errori": n, "warning": n, "findings": [...], ...}
    """
    report = linter.lint(blueprint, deliverable or {})
    report["livello"] = 2
    report["pass"] = report.get("esito") == "PASS"
    return report
