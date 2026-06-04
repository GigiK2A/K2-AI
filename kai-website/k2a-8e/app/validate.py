"""Gate L1 (validate_blueprint) + L2 (lint_deliverable) — implementazione locale.

Phase-1: validatori locali (no MCP k2a-mcp-deliverable, che vive sul Mac di Luca).
Stessa SEMANTICA dei gate descritti in 8e_Phase0_design_API.md §7:
  L1 = struttura/voci conformi al blueprint;
  L2 = ogni numero/citazione ha fonte+vigenza, disclaimer presente, niente vuoti.
Quando l'MCP reale sarà raggiungibile, si può sostituire questa logica con la
chiamata MCP senza toccare la pipeline (stessa firma PASS/FAIL + dettagli).
"""
from __future__ import annotations

from typing import Any


def validate_blueprint(instance: dict, blueprint: dict) -> dict:
    """L1: l'istanza ha tutte le voci dichiarate dal blueprint."""
    voci = [v.get("id") or v.get("titolo") for v in blueprint.get("voci", [])]
    sezioni = instance.get("sezioni", {})
    mancanti = [v for v in voci if v and v not in sezioni]
    ok = not mancanti
    return {
        "gate": "L1",
        "result": "PASS" if ok else "FAIL",
        "missing_voci": mancanti,
        "expected": len(voci),
        "present": len([v for v in voci if v in sezioni]),
    }


def lint_deliverable(instance: dict, blueprint: dict) -> dict:
    """L2: regole linter — fonti sui deterministici, disclaimer, niente vuoti."""
    errors: list[str] = []

    # 1) Disclaimer obbligatorio (D-034 legale).
    if not (instance.get("disclaimer") or "").strip():
        errors.append("disclaimer mancante (D-034)")

    # 2) Ogni campo deterministico citato deve avere fonte + vigenza.
    for c in instance.get("citazioni", []):
        if not c.get("fonte"):
            errors.append(f"citazione senza fonte: {c.get('campo')}")
        if not c.get("vigenza"):
            errors.append(f"citazione senza vigenza: {c.get('campo')}")

    # 3) Nessuna sezione vuota.
    for sid, txt in (instance.get("sezioni") or {}).items():
        if not str(txt or "").strip():
            errors.append(f"sezione vuota: {sid}")

    # 4) Almeno una citazione (un Boost legale senza fonti è sospetto).
    if not instance.get("citazioni"):
        errors.append("nessuna citazione presente")

    ok = not errors
    return {
        "gate": "L2",
        "result": "PASS" if ok else "FAIL",
        "errors": errors,
    }
