"""Filiera — genera la PROSA delle voci attorno ai fatti già fissati.

Principio cardine (8e_Phase0 §1): i FATTI (numeri, citazioni di legge) vengono
dallo snapshot e sono INIETTATI; il modello scrive solo la prosa attorno, non
genera fatti. Se manca la chiave Anthropic → modalità OFFLINE deterministica
(template) così smoke test e CI girano senza rete.

Prompt caching: il system prompt (regole + fatti) è marcato `cache_control` per
abbattere i costi su generazioni ripetute della stessa filiera.
"""
from __future__ import annotations

import logging
from typing import Optional

from .settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

log = logging.getLogger("8e.llm")

_SYSTEM = (
    "Sei il generatore di un deliverable legale per PMI italiane (LegalBoost).\n"
    "REGOLE ASSOLUTE:\n"
    "- NON inventare numeri, articoli di legge o citazioni. I FATTI ti sono forniti già risolti.\n"
    "- Scrivi prosa professionale, in italiano, attorno ai fatti forniti.\n"
    "- Ogni riferimento normativo che usi DEVE essere tra quelli forniti nei FATTI.\n"
    "- Tono pragmatico, diretto. Niente buzzword.\n"
    "- Restituisci SOLO un oggetto JSON {\"<voce_id>\": \"<testo>\", ...}, una chiave per voce richiesta."
)


def _facts_block(facts: dict[str, dict]) -> str:
    lines = ["FATTI DETERMINISTICI (usa SOLO questi per i riferimenti normativi):"]
    for k, v in facts.items():
        lines.append(f"- [{k}] fonte={v.get('fonte')} vigenza={v.get('vigenza')}: {v.get('testo')}")
    return "\n".join(lines)


def _voci_block(voci: list[dict]) -> str:
    lines = ["VOCI DA SCRIVERE (una chiave JSON per id):"]
    for v in voci:
        vid = v.get("id") or v.get("titolo")
        lines.append(f"- id={vid}: {v.get('titolo','')} — {v.get('descrizione','')}")
    return "\n".join(lines)


def generate_sezioni(
    blueprint: dict, facts: dict[str, dict], inputs: dict
) -> tuple[dict[str, str], str]:
    """Ritorna ({voce_id: prosa}, mode). mode ∈ {anthropic, offline}."""
    voci = blueprint.get("voci", [])

    if not ANTHROPIC_API_KEY:
        return _offline(voci, facts, inputs), "offline"

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        user = (
            f"{_facts_block(facts)}\n\n{_voci_block(voci)}\n\n"
            f"DATI CLIENTE (input form): {inputs}\n\n"
            "Genera ora il JSON con la prosa per ogni voce."
        )
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        import json as _json

        # Estrai il primo oggetto JSON dalla risposta.
        start, end = text.find("{"), text.rfind("}")
        data = _json.loads(text[start : end + 1]) if start >= 0 else {}
        # Garantisci una chiave per voce (fallback offline sulle mancanti).
        out = {}
        off = _offline(voci, facts, inputs)
        for v in voci:
            vid = v.get("id") or v.get("titolo")
            out[vid] = str(data.get(vid) or off.get(vid, "")).strip()
        return out, "anthropic"
    except Exception as exc:  # rete/chiave/parse → degrada a offline, non rompere
        log.warning("filiera anthropic fallita, fallback offline: %s", exc)
        return _offline(voci, facts, inputs), "offline"


def _offline(voci: list[dict], facts: dict[str, dict], inputs: dict) -> dict[str, str]:
    """Template deterministico: cita i fatti senza inventarli. Per dev/CI/no-key."""
    fact_refs = "; ".join(
        f"{v.get('fonte')} ({v.get('vigenza')})" for v in facts.values()
    ) or "nessun riferimento deterministico"
    azienda = inputs.get("ragione_sociale") or inputs.get("azienda") or "l'azienda"
    out: dict[str, str] = {}
    for v in voci:
        vid = v.get("id") or v.get("titolo")
        titolo = v.get("titolo", vid)
        out[vid] = (
            f"[BOZZA OFFLINE] {titolo} per {azienda}. "
            f"Analisi basata sui riferimenti normativi forniti: {fact_refs}. "
            f"(Testo segnaposto deterministico — la prosa reale è prodotta da Sonnet "
            f"quando ANTHROPIC_API_KEY è configurata; i FATTI restano invariati.)"
        )
    return out
