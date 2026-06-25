"""Ricerca web PRE-GATE: riempe i campi OBBLIGATORI *ricercabili* (competitor, dati di
mercato) cercandoli DAVVERO sul web, prima che il gate required-fields blocchi la
generazione.

È la differenza tra "l'agente RICHIEDE all'utente i competitor" (vicolo cieco della
screenshot) e "l'agente VA A CERCARLI" — la lamentela #1 dell'owner.

Confini netti:
- Solo dati PUBBLICI/esterni: competitor, mercato, benchmark, trend. MAI dati interni
  privati del cliente (bilanci, fatturato, obiettivi, descrizione azienda = identità).
- Ogni valore arriva con provenienza (`_fonti` = URL usati), niente invenzioni: se dopo
  la ricerca un campo resta ignoto, viene omesso (il gate lo bloccherà legittimamente).
- Best-effort: se la web search è spenta o l'API non risponde, è un no-op (il flusso
  resta identico a prima → nessuna regressione).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from ..settings import ANTHROPIC_API_KEY, ANTHROPIC_PDF_MODEL
from . import web_search

log = logging.getLogger(__name__)

# Claude struttura il risultato (il cervello resta Anthropic); la RICERCA vera la fa
# OpenAI dietro al client-tool web_search. Modello structurer = Sonnet di default (il
# pre-gate è raro e ad alto valore). Override con KBOT_RESEARCH_MODEL.
_RESEARCH_MODEL = os.environ.get("KBOT_RESEARCH_MODEL") or ANTHROPIC_PDF_MODEL

# Campi cercabili su fonti pubbliche. NON include dati privati del cliente: 'bilanci',
# 'fatturato', 'obiettivo*' e 'descrizione_azienda' (identità) restano all'utente.
_RESEARCHABLE_KW = (
    "competitor", "concorrent", "rivali", "benchmark",
    "mercato", "market", "trend", "quota di mercato",
    "dimensione del mercato", "domanda di mercato",
)


def is_researchable(campo: dict) -> bool:
    """Vero se il campo riguarda informazioni pubbliche cercabili sul web.

    Se il form 8e dichiara un flag esplicito `ricercabile`/`researchable`, vince su tutto
    (così Luca può marcare i campi a mano nei blueprint). Altrimenti euristica keyword."""
    if not isinstance(campo, dict):
        return False
    flag = campo.get("ricercabile", campo.get("researchable"))
    if isinstance(flag, bool):
        return flag
    blob = f"{campo.get('id', '')} {campo.get('label', '')} {campo.get('descrizione', '')}".lower()
    return any(kw in blob for kw in _RESEARCHABLE_KW)


def enabled() -> bool:
    # serve Claude (structurer) + la ricerca web usabile (OpenAI dietro al tool)
    return bool(ANTHROPIC_API_KEY) and web_search.enabled()


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
    return value  # array/object/string passano così come sono


def research_missing_fields(
    session: dict, campi: list[dict], missing: list[dict], inputs: dict
) -> tuple[dict, list[str]]:
    """Per i campi OBBLIGATORI mancanti che sono RICERCABILI, cerca sul web e li riempie.

    Ritorna `(valori_trovati, fonti)`. No-op (`{}, []`) se la web search è spenta, manca
    la chiave API, o nessun campo mancante è ricercabile (→ nessuna chiamata di rete)."""
    targets = [c for c in (missing or []) if is_researchable(c)]
    if not targets or not enabled():
        return {}, []

    try:
        import anthropic
        from .analysis import _build_context_block
    except Exception as exc:  # pragma: no cover - import di sicurezza
        log.warning("research: import fallito (%s)", exc)
        return {}, []

    context = _build_context_block(session)
    msgs = session.get("messages") or []
    convo = "\n".join(
        f"{m.get('role')}: {str(m.get('content', ''))[:500]}"
        for m in (msgs[-12:] if isinstance(msgs, list) else [])
        if isinstance(m, dict)
    )
    azienda = str(inputs.get("ragione_sociale") or inputs.get("descrizione_azienda") or "").strip()

    spec_lines, ids = [], []
    for c in targets:
        cid = c.get("id")
        if not cid:
            continue
        ids.append(cid)
        line = f"- {cid}: tipo={c.get('tipo')} — {c.get('label') or c.get('descrizione') or ''}"
        if c.get("enum"):
            line += f" [valori ammessi: {c['enum']}]"
        spec_lines.append(line)
    if not ids:
        return {}, []
    spec = "\n".join(spec_lines)

    system = (
        "Sei un analista di mercato. Cerca DAVVERO sul web (tool `web_search`) e compila i "
        "campi richiesti su CONCORRENTI e MERCATO dell'azienda in oggetto, nel suo settore "
        "e mercato geografico.\n"
        "REGOLE:\n"
        "- USA il tool web_search per ogni dato. NIENTE invenzioni: se dopo la ricerca un "
        "campo resta ignoto, OMETTI la chiave.\n"
        "- I competitor devono essere aziende REALI dello stesso settore/mercato; per "
        "ciascuna {nome, descrizione breve}.\n"
        "- Numeri di mercato solo se trovati su fonte: cifre pure (es. 1500000), senza "
        "valuta né separatori di migliaia.\n"
        "- Rispondi SOLO con un oggetto JSON: le chiavi richieste + una chiave \"_fonti\" "
        "= lista degli URL usati. Nessun altro testo."
    )
    user = (
        f"AZIENDA: {azienda or '(deducila dal contesto)'}\n\n"
        f"CONTESTO:\n{context}\n\nCONVERSAZIONE RECENTE:\n{convo}\n\n"
        f"CAMPI DA COMPILARE CON RICERCA WEB:\n{spec}\n\n"
        f"Chiavi attese: {ids} + \"_fonti\". JSON:"
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = web_search.create_with_web_search(
            client,
            model=_RESEARCH_MODEL,
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_rounds=6,
            timeout=180.0,
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        data = _parse_json_object(text)
    except Exception as exc:
        log.warning("research: ricerca web fallita: %s", exc)
        return {}, []

    raw_fonti = data.pop("_fonti", None)
    fonti = [f for f in raw_fonti if isinstance(f, str) and f.strip()] if isinstance(raw_fonti, list) else []

    by_id = {c.get("id"): c for c in targets}
    out: dict[str, Any] = {}
    for k, v in data.items():
        c = by_id.get(k)
        if not c or v in (None, "", [], {}):
            continue
        try:
            out[k] = _coerce(v, c.get("tipo"))
        except Exception:
            continue  # tipo non coercibile → salta il campo

    if out:
        log.info("research: riempiti dal web %s (%d fonti)", list(out.keys()), len(fonti))
    return out, fonti
