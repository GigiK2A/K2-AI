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
_GENERIC_NAMES = {"", "cliente", "azienda", "la tua azienda", "n/d", "-", "—"}


def has_identity(inputs: dict | None) -> bool:
    """Vero se gli input contengono un nome-cliente USABILE. Mirror di 8e
    quality.display_name: il Gate 0 dell'8e lo esige per personalizzare il report, ma il
    pre-flight non lo controllava → un'identità mancante cadeva nel Gate 0 (errore generico)
    invece di essere nominata. Qui la riconosciamo per dirla tra i dati mancanti."""
    inputs = inputs or {}
    for k in ("ragione_sociale", "denominazione", "azienda", "nome", "client_name"):
        v = str(inputs.get(k) or "").strip()
        if v and v.lower() not in _GENERIC_NAMES:
            return True
    # StrategyBoost usa una descrizione libera: vale come identità solo se breve/nominale
    # (come 8e: una descrizione lunga NON è un nome).
    desc = str(inputs.get("descrizione_azienda") or "").strip()
    return bool(desc) and len(desc) <= 100


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


def _is_url(x: Any) -> bool:
    return isinstance(x, str) and x.strip().lower().startswith(("http://", "https://"))


def _value_plausible(prop: dict, v: Any) -> bool:
    """Lenient: vero salvo violazioni PALESI. Oggi copre i campi che vogliono URL
    (`format: uri`) ma ricevono testo libero — il caso reale: WebBoost `competitor`
    esige URL, ma la chat trova NOMI. Tutto il resto passa (non si scarta a caso)."""
    if not isinstance(prop, dict):
        return True
    types = prop.get("type")
    types = types if isinstance(types, list) else [types]
    if "array" in types and isinstance(v, list):
        items = prop.get("items") or {}
        if isinstance(items, dict) and items.get("format") == "uri":
            return all(_is_url(x) for x in v)
    if "string" in types and prop.get("format") == "uri":
        return _is_url(v)
    return True


def drop_invalid_optional(form_schema: dict | None, inputs: dict | None) -> tuple[dict, list[str]]:
    """Scarta dagli input i campi OPZIONALI il cui valore viola palesemente lo schema,
    così un dato auto-estratto sbagliato (es. competitor=nomi vs campo che vuole URL) non
    fa rifiutare la generazione dall'8e. I REQUIRED non si toccano MAI (li gestisce
    `missing_required`, che blocca con un messaggio leggibile). Ritorna (inputs, scartati).

    Self-adjusting: se l'8e allenta lo schema (competitor non più 'uri'), `_value_plausible`
    ritorna vero → il campo NON viene scartato → i valori fluiscono."""
    inputs = dict(inputs or {})
    if not isinstance(form_schema, dict):
        return inputs, []
    props = form_schema.get("properties") or {}
    required = set(form_schema.get("required") or [])
    dropped: list[str] = []
    for k, v in list(inputs.items()):
        if k in required or k not in props:
            continue
        if not _value_plausible(props[k], v):
            inputs.pop(k, None)
            dropped.append(k)
    return inputs, dropped


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
