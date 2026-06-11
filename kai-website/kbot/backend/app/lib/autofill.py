"""Auto-compilazione degli input del motore 8e dalla conversazione.

Design "ufficiale" (giu 2026): l'utente NON riempie form. Il bot raccoglie i dati
chiacchierando (domande + file/bilanci caricati); al momento di generare, qui un
LLM economico (Haiku) estrae i valori dei campi richiesti dal boost a partire dal
contesto della sessione. Niente invenzioni: se un dato non c'è, il campo si omette.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from ..settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

log = logging.getLogger(__name__)


def _parse_json_object(text: str) -> dict:
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e <= s:
        return {}
    try:
        return json.loads(text[s : e + 1])
    except json.JSONDecodeError:
        return {}


def _coerce(value: Any, tipo: Optional[str]) -> Any:
    if tipo == "integer":
        return int(float(value))
    if tipo == "number":
        return float(value)
    if tipo == "boolean":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "si", "sì", "yes", "1")
    return value


def extract_inputs(session: dict, campi: list[dict]) -> dict:
    """Conversazione + file caricati → dict di input conformi ai campi del boost.

    Best-effort: ritorna {} se la chiave API manca o l'estrazione fallisce (il
    motore 8e proverà comunque, eventualmente in modalità degradata)."""
    if not ANTHROPIC_API_KEY or not campi:
        return {}
    try:
        import anthropic
        from .analysis import _build_context_block
    except Exception as exc:  # pragma: no cover
        log.warning("autofill: import fallito (%s)", exc)
        return {}

    context = _build_context_block(session)
    msgs = session.get("messages") or []
    convo = "\n".join(
        f"{m.get('role')}: {str(m.get('content', ''))[:600]}"
        for m in (msgs[-14:] if isinstance(msgs, list) else [])
        if isinstance(m, dict)
    )

    spec_lines = []
    for c in campi:
        cid = c.get("id")
        if not cid:
            continue
        t = c.get("tipo")
        req = " (OBBLIGATORIO)" if c.get("obbligatorio") else ""
        desc = c.get("label") or c.get("descrizione") or ""
        line = f"- {cid}: tipo={t}{req} — {desc}"
        if c.get("enum"):
            line += f" [valori ammessi: {c['enum']}]"
        spec_lines.append(line)
    spec = "\n".join(spec_lines)

    system = (
        "Sei un estrattore di dati. Dal CONTESTO (conversazione + eventuali bilanci/"
        "file caricati) compili i campi necessari a generare un documento professionale.\n"
        "REGOLE:\n"
        "- Usa SOLO informazioni presenti nel contesto. Se un campo non è deducibile, "
        "OMETTI la chiave (non inventare, non mettere placeholder).\n"
        "- Numeri SEMPRE in cifre intere, senza separatori di migliaia né valuta "
        "(es. 394600000, non '394,6M').\n"
        "- Per i campi con valori ammessi (enum) usa ESATTAMENTE uno di quelli.\n"
        "- Per i campi 'array' (es. bilanci, competitor) restituisci una lista.\n"
        "- Rispondi SOLO con un oggetto JSON {campo: valore}, niente altro testo."
    )
    user = (
        f"CONTESTO:\n{context}\n\nCONVERSAZIONE RECENTE:\n{convo}\n\n"
        f"CAMPI DA COMPILARE:\n{spec}\n\nJSON:"
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2500,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        data = _parse_json_object(text)
    except Exception as exc:
        log.warning("autofill: estrazione LLM fallita: %s", exc)
        return {}

    by_id = {c.get("id"): c for c in campi}
    out: dict[str, Any] = {}
    for k, v in data.items():
        c = by_id.get(k)
        if not c or v in (None, "", [], {}):
            continue
        try:
            out[k] = _coerce(v, c.get("tipo"))
        except Exception:
            continue  # tipo non coercibile → salta il campo
    return out
