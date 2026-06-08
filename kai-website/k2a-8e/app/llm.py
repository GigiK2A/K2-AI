"""Filiera — genera la PROSA delle voci attorno ai fatti già fissati.

Principio cardine (8e_Phase0 §1, D-029): i FATTI (testi di legge, numeri,
citazioni) vengono dallo snapshot e sono INIETTATI; il modello scrive solo la
prosa attorno, non genera fatti.

Modalità:
- ANTHROPIC_API_KEY presente  → Sonnet reale (prompt caching sul system).
- chiave assente              → OFFLINE deterministico (template) — per dev/CI.
- chiave presente MA chiamata fallisce:
    - ALLOW_OFFLINE_FALLBACK=true  → degrada a offline (dev)
    - ALLOW_OFFLINE_FALLBACK=false → rilancia (PROD: niente deliverable silenziosamente scadente)

Ritorna ({voce_id: prosa}, meta) con meta = {mode, model?, usage?}.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from .settings import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ALLOW_OFFLINE_FALLBACK

log = logging.getLogger("8e.llm")

_SYSTEM = (
    "Sei il generatore di un deliverable legale-compliance per PMI italiane (LegalBoost).\n"
    "REGOLE ASSOLUTE:\n"
    "- NON inventare numeri, articoli di legge o citazioni. I FATTI ti sono forniti già risolti e VERBATIM.\n"
    "- Quando una voce riguarda un fatto normativo fornito, integra il riferimento ESATTO dai FATTI "
    "(stesso articolo/fonte), senza riscrivere il testo di legge a memoria.\n"
    "- Ogni riferimento normativo che citi DEVE essere tra quelli nei FATTI.\n"
    "- Tono pragmatico, diretto, per un titolare d'impresa. Niente buzzword. Niente gergo legale inutile.\n"
    "- LUNGHEZZA: massimo ~110 parole per voce (2 paragrafi brevi). Conciso ma concreto.\n"
    "- È orientamento, NON consulenza legale (D-034).\n"
    "- Restituisci SOLO un oggetto JSON {\"<voce_id>\": \"<testo>\", ...}, una chiave per voce richiesta."
)


def _parse_json_object(text: str) -> dict:
    """Estrae un oggetto JSON da una risposta LLM (gestisce ```json fences).

    Tollerante: rimuove i fence, poi json.loads; se fallisce ritorna {} (il
    chiamante riempie le voci mancanti col fallback offline).
    """
    t = text.strip()
    if t.startswith("```"):
        # rimuove ```json ... ``` o ``` ... ```
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        return json.loads(t[start : end + 1])
    except json.JSONDecodeError:
        return {}


def _facts_block(facts: dict[str, dict]) -> str:
    lines = ["FATTI DETERMINISTICI (usa SOLO questi per i riferimenti normativi):"]
    for k, v in facts.items():
        val = str(v.get("valore", ""))[:1500]
        lines.append(f"- [{k}] tipo={v.get('tipo')} fonte={v.get('fonte')} vigenza={v.get('vigenza')}:\n{val}")
    return "\n".join(lines)


def _voci_block(voci: list[dict]) -> str:
    lines = ["VOCI DA SCRIVERE (una chiave JSON per id):"]
    for v in voci:
        vid = v.get("id") or v.get("titolo")
        argomenti = "; ".join(v.get("argomenti_obbligatori", []))
        lines.append(f"- id={vid}: {v.get('titolo','')} — argomenti obbligatori: {argomenti}")
    return "\n".join(lines)


def generate_sezioni(
    blueprint: dict, facts: dict[str, dict], inputs: dict
) -> tuple[dict[str, str], dict]:
    voci = blueprint.get("voci", [])

    if not ANTHROPIC_API_KEY:
        return _offline(voci, facts, inputs), {"mode": "offline", "reason": "no_api_key"}

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        user = (
            f"{_facts_block(facts)}\n\n{_voci_block(voci)}\n\n"
            f"DATI CLIENTE (input form): {json.dumps(inputs, ensure_ascii=False)}\n\n"
            "Genera ora il JSON con la prosa per ogni voce."
        )
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=8192,  # 9 voci ricche: 4096 tronca il JSON
            system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        data = _parse_json_object(text)
        if getattr(resp, "stop_reason", None) == "max_tokens":
            log.warning("filiera: risposta troncata (max_tokens), JSON parziale")
        off = _offline(voci, facts, inputs)
        out = {}
        for v in voci:
            vid = v.get("id") or v.get("titolo")
            out[vid] = str(data.get(vid) or off.get(vid, "")).strip()
        usage = getattr(resp, "usage", None)
        meta = {
            "mode": "anthropic",
            "model": ANTHROPIC_MODEL,
            "usage": {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", None),
            } if usage else None,
        }
        return out, meta
    except Exception as exc:
        log.warning("filiera anthropic fallita: %s", exc)
        if ALLOW_OFFLINE_FALLBACK:
            return _offline(voci, facts, inputs), {"mode": "offline", "reason": f"anthropic_error: {exc}"}
        raise  # PROD: non consegnare un deliverable degradato in silenzio


_SYSTEM_LEGAL_FULL = (
    "Sei l'estensore di un deliverable legale-compliance per PMI italiane (LegalBoost).\n"
    "Produci un documento COMPLETO e CORPOSO, conforme allo schema JSON richiesto.\n"
    "REGOLE ASSOLUTE:\n"
    "- NON inventare numeri/articoli/citazioni: i FATTI normativi ti sono forniti VERBATIM.\n"
    "- Ogni `norme_citate.riferimento` deve corrispondere a un fatto fornito; `fonte` ∈ {normattiva}.\n"
    "- Per ogni voce: contenuto ricco (≥2 paragrafi), rischi concreti con gravità, azioni operative.\n"
    "- È orientamento, NON consulenza legale (D-034).\n"
    "- Rispondi SOLO con l'oggetto JSON conforme allo schema, niente altro."
)


def generate_deliverable_legal(
    blueprint: dict, out_schema: dict, facts: dict[str, dict], inputs: dict
) -> tuple[Optional[dict], dict]:
    """Genera il deliverable LegalBoost STRUTTURATO conforme a output-schema.

    Ritorna (deliverable|None, meta). Se None → il chiamante usa l'assembly
    deterministico di fallback. Garantisce corposità: rischi/azioni/score reali,
    non placeholder.
    """
    voci = blueprint.get("voci", [])
    if not ANTHROPIC_API_KEY:
        return None, {"mode": "offline"}
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        voci_spec = "\n".join(
            f"- id={v['id']} titolo=«{v['titolo']}» argomenti: {'; '.join(v.get('argomenti_obbligatori', []))}"
            for v in voci
        )
        user = (
            f"{_facts_block(facts)}\n\nVOCI (una per id, in ordine):\n{voci_spec}\n\n"
            f"DATI CLIENTE: {json.dumps(inputs, ensure_ascii=False)}\n\n"
            "Genera il JSON conforme allo schema: meta{servizio,versione,data,azienda}, "
            "sintesi{score_compliance(int 0-100), mappa_rischi[{area,semaforo:verde|giallo|rosso}]}, "
            "voci[{id,titolo,contenuto,rischi[{descrizione,gravita:bassa|media|alta,serve_avvocato:bool}],"
            "azioni[str],norme_citate[{riferimento,fonte:normattiva}]}], "
            "piano_azione[{priorita:int,azione,handoff_avvocato:bool}], disclaimer."
        )
        resp = client.messages.create(
            model=ANTHROPIC_MODEL, max_tokens=16000,  # doc completo 9 voci ricche
            system=[{"type": "text", "text": _SYSTEM_LEGAL_FULL, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        truncated = getattr(resp, "stop_reason", None) == "max_tokens"
        data = _parse_json_object(text)
        if truncated or not data.get("voci"):
            log.warning("deliverable strutturato troncato/incompleto → fallback")
            return None, {"mode": "anthropic", "warning": "json_incompleto_o_troncato"}
        # forza meta.azienda dall'input + disclaimer del blueprint se assente
        data.setdefault("meta", {})["azienda"] = inputs.get("ragione_sociale") or data.get("meta", {}).get("azienda", "Cliente")
        data["meta"].setdefault("servizio", "LegalBoost")
        data["meta"].setdefault("versione", "1.0.0")
        data["meta"].setdefault("data", "2026-06-08")
        data.setdefault("disclaimer", blueprint.get("disclaimer", "Orientamento legale, non consulenza (D-034)."))
        usage = getattr(resp, "usage", None)
        return data, {"mode": "anthropic", "model": ANTHROPIC_MODEL,
                      "output_tokens": getattr(usage, "output_tokens", None)}
    except Exception as exc:
        log.warning("deliverable strutturato fallito: %s", exc)
        return None, {"mode": "offline", "reason": str(exc)}


def generate_conforming(output_schema: dict, blueprint: dict, facts: dict[str, dict],
                        inputs: dict) -> tuple[Optional[dict], dict]:
    """Generatore GENERICO schema-driven: produce un deliverable JSON conforme a
    QUALSIASI output-schema (per i boost senza assembly dedicato). I FATTI
    deterministici (verbatim) vanno iniettati e usati senza inventare. Ritorna
    (deliverable|None, meta). Il chiamante valida contro lo schema; se None o
    invalido → refuse (mai consegnare invalido).
    """
    if not ANTHROPIC_API_KEY:
        return None, {"mode": "offline"}
    import json as _json
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        # schema compatto (solo properties + required, niente $schema/title verbosi)
        compact = {"type": "object",
                   "required": output_schema.get("required", []),
                   "properties": output_schema.get("properties", {})}
        sysmsg = (
            "Sei l'estensore di un deliverable professionale per PMI italiane. Produci un "
            "oggetto JSON CONFORME allo schema fornito (tutti i campi required, tipi corretti, "
            "enum rispettati). REGOLE: non inventare numeri/citazioni di legge — usa i FATTI "
            "verbatim forniti dove servono riferimenti normativi o valori; testo conciso e "
            "concreto, italiano, per un titolare d'impresa; è orientamento, non consulenza "
            "(D-034/D-036). Rispondi SOLO con il JSON, niente altro."
        )
        user = (
            f"SCHEMA (conformati esattamente):\n{_json.dumps(compact, ensure_ascii=False)[:6000]}\n\n"
            f"{_facts_block(facts)}\n\nDATI CLIENTE: {_json.dumps(inputs, ensure_ascii=False)}\n\n"
            "Genera ora il JSON conforme."
        )
        # schemi complessi (es. AdvisorBoost 15 sezioni) richiedono più spazio +
        # istruzione di concisione per non troncare.
        n_props = len(compact["properties"])
        maxtok = 16000 if n_props > 8 else 12000
        sysmsg += "\n- CONCISIONE: testi brevi e densi; per le liste max 5-6 elementi salvo necessità."
        resp = client.messages.create(
            model=ANTHROPIC_MODEL, max_tokens=maxtok,
            system=[{"type": "text", "text": sysmsg, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        truncated = getattr(resp, "stop_reason", None) == "max_tokens"
        data = _parse_json_object(text)
        if truncated or not data:
            return None, {"mode": "anthropic", "warning": "troncato_o_vuoto"}
        usage = getattr(resp, "usage", None)
        return data, {"mode": "anthropic", "model": ANTHROPIC_MODEL,
                      "output_tokens": getattr(usage, "output_tokens", None)}
    except Exception as exc:
        log.warning("generate_conforming fallita: %s", exc)
        return None, {"mode": "offline", "reason": str(exc)}


def generate_structured_meta(blueprint: dict, facts: dict[str, dict], inputs: dict) -> Optional[dict]:
    """Chiamata COMPATTA: score + mappa_rischi + per-voce {rischi,azioni} (NO prosa
    lunga → niente troncamento). La prosa `contenuto` arriva da generate_sezioni.
    Ritorna {score, mappa_rischi, voci_meta:{vid:{rischi,azioni}}} o None.
    """
    if not ANTHROPIC_API_KEY:
        return None
    voci = blueprint.get("voci", [])
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        voci_spec = "\n".join(f"- {v['id']}: {v['titolo']} ({'; '.join(v.get('argomenti_obbligatori', [])[:3])})" for v in voci)
        sysmsg = (
            "Produci SOLO i metadati strutturati di una diagnosi legale-compliance PMI "
            "(NON la prosa). Conciso. Rispondi SOLO JSON: {\"score\": int 0-100, "
            "\"mappa_rischi\": [{\"area\": str, \"semaforo\": \"verde|giallo|rosso\"}], "
            "\"voci_meta\": {\"<id>\": {\"rischi\": [{\"descrizione\": str breve, "
            "\"gravita\": \"bassa|media|alta\", \"serve_avvocato\": bool}], \"azioni\": [str breve]}}}."
        )
        user = f"Voci:\n{voci_spec}\n\nDati: {json.dumps(inputs, ensure_ascii=False)}\nUna entry voci_meta per id."
        resp = client.messages.create(
            model=ANTHROPIC_MODEL, max_tokens=4096,
            system=[{"type": "text", "text": sysmsg, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        data = _parse_json_object(text)
        if data.get("score") is not None and data.get("voci_meta"):
            return data
    except Exception as exc:
        log.warning("structured_meta fallita: %s", exc)
    return None


def generate_preview(blueprint: dict, facts: dict[str, dict], inputs: dict) -> dict:
    """Compone SOLO l'assaggio: score + criticità #1 reale. NON il documento.

    Gate W8: a PREVIEW l'LLM compone solo questo (niente contenuto completo →
    nessun leak). Le altre aree restano titoli senza contenuto (gestite dalla
    pipeline). Ritorna {score:int, criticita_1:{area,descrizione,gravita}, mode}.
    """
    voci = blueprint.get("voci", [])
    prima = voci[1] if len(voci) > 1 else (voci[0] if voci else {})
    area = prima.get("titolo", "Area principale")

    if not ANTHROPIC_API_KEY:
        return {
            "score": 68,
            "criticita_1": {
                "area": area,
                "descrizione": f"[ANTEPRIMA] Rilevata una criticità prioritaria in «{area}». "
                               f"Il documento completo dettaglia rischi, norme e azioni.",
                "gravita": "media",
            },
            "mode": "offline",
        }
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        sysmsg = (
            "Genera l'ASSAGGIO (preview) di una diagnosi PMI: un punteggio di sintesi "
            "0-100 e la criticità #1 reale e azionabile. NON scrivere il documento completo. "
            "Usa SOLO i fatti forniti per eventuali riferimenti. "
            "Rispondi SOLO JSON: {\"score\": <int>, \"criticita_1\": {\"area\": <str>, "
            "\"descrizione\": <str ~2 frasi>, \"gravita\": \"bassa|media|alta\"}}."
        )
        user = f"{_facts_block(facts)}\n\nArea prioritaria: {area}\nDati cliente: {json.dumps(inputs, ensure_ascii=False)}"
        resp = client.messages.create(
            model=ANTHROPIC_MODEL, max_tokens=600,
            system=[{"type": "text", "text": sysmsg, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        data = _parse_json_object(text)
        if data.get("score") is not None and data.get("criticita_1"):
            data["mode"] = "anthropic"
            return data
    except Exception as exc:
        log.warning("preview anthropic fallita: %s", exc)
    return {
        "score": 68,
        "criticita_1": {"area": area,
                        "descrizione": f"Criticità prioritaria rilevata in «{area}».",
                        "gravita": "media"},
        "mode": "offline",
    }


def _offline(voci: list[dict], facts: dict[str, dict], inputs: dict) -> dict[str, str]:
    """Template deterministico: cita i fatti senza inventarli. Per dev/CI/no-key."""
    fact_refs = "; ".join(
        f"{v.get('fonte')} ({v.get('vigenza')})"
        for v in facts.values() if v.get("tipo") == "normativo"
    ) or "nessun riferimento deterministico"
    azienda = inputs.get("ragione_sociale") or inputs.get("azienda") or "l'azienda"
    out: dict[str, str] = {}
    for v in voci:
        vid = v.get("id") or v.get("titolo")
        titolo = v.get("titolo", vid)
        out[vid] = (
            f"[BOZZA OFFLINE] {titolo} per {azienda}. "
            f"Analisi ancorata ai riferimenti normativi forniti: {fact_refs}. "
            f"(Segnaposto deterministico — la prosa reale è prodotta da Sonnet con "
            f"ANTHROPIC_API_KEY; i FATTI restano invariati.)"
        )
    return out
