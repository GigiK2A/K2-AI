"""Deliverable readiness — la decisione deterministica "quali campi OBBLIGATORI del
boost mancano ancora?".

Radice del bug ricorrente: la chat (Haiku) decideva "ho tutto" su 4 campi generici,
cieca ai campi `required` del form del boost instradato (es. StrategyBoost esige
`competitor` + `obiettivo_strategico`). L'autofill omette il non-detto (giusto: niente
invenzioni) → il Gate 0 dell'8e fa fail-closed → l'utente vede un vicolo cieco generico.

Questo modulo è la SSOT condivisa da due punti:
- pre-flight di `/deliverables/auto`: se manca un required → 409 `needs_input` che NOMINA
  cosa serve, invece di spendere una generazione e farla rifiutare dall'8e;
- prompt della chat: dice al bot COSA deve ancora raccogliere prima di dichiararsi pronto.

Puro, niente import dell'app: testato standalone come services.py.
"""
from __future__ import annotations

from typing import Any

_EMPTY = (None, "", [], {})


def missing_required(campi: list[dict] | None, inputs: dict | None) -> list[dict]:
    """I campi del form marcati `obbligatorio` il cui valore è assente/vuoto negli input.

    `campi` è la proiezione 8e di `/v1/form` ({id, obbligatorio, label, ...}); `inputs`
    è il dict auto-compilato dalla conversazione. Combacia col Gate 0 dell'8e
    (`validate_required_inputs`): un required assente = report non generabile."""
    inputs = inputs or {}
    out: list[dict] = []
    for c in campi or []:
        if not isinstance(c, dict) or not c.get("obbligatorio"):
            continue
        cid = c.get("id")
        if not cid:
            continue
        if inputs.get(cid) in _EMPTY:
            out.append(c)
    return out


def _label(campo: dict) -> str:
    return str(campo.get("label") or campo.get("descrizione") or campo.get("id") or "").strip()


def format_missing_labels(campi: list[dict] | None) -> str:
    """Etichette leggibili dei campi mancanti, per il messaggio all'utente."""
    return "; ".join(lbl for lbl in (_label(c) for c in (campi or [])) if lbl)


def required_fields_hint(campi: list[dict] | None, boost_label: str | None = None) -> str:
    """Istruzione per il system prompt della chat: i campi che il boost instradato esige,
    così il bot li raccoglie PRIMA di emettere CONSULENZA_SUMMARY. Stringa vuota se il
    boost non ha campi obbligatori (niente da forzare)."""
    obbligatori = [c for c in (campi or []) if isinstance(c, dict) and c.get("obbligatorio") and c.get("id")]
    if not obbligatori:
        return ""
    voci = "; ".join(f"{c['id']} ({_label(c)})" if _label(c) and _label(c) != c["id"] else str(c["id"])
                     for c in obbligatori)
    quale = f" «{boost_label}»" if boost_label else ""
    return (
        f"\nCAMPI OBBLIGATORI DEL DOCUMENTO{quale} — questo tipo di documento richiede questi dati "
        f"specifici, oltre ai campi generici: {voci}.\n"
        "DEVI raccoglierli (chiedendoli in modo naturale, uno alla volta) PRIMA di emettere "
        "CONSULENZA_SUMMARY. Se l'utente forza 'procedi' ma ne manca qualcuno, chiedi ESPLICITAMENTE "
        "quelli mancanti in una frase breve invece di generare un documento incompleto.\n"
    )
