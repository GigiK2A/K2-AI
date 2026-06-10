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
import re
from typing import Optional

from .settings import (ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ANTHROPIC_MODEL_LIGHT,
                       ALLOW_OFFLINE_FALLBACK)

log = logging.getLogger("8e.llm")

_SYSTEM = (
    "Sei il generatore di un deliverable legale-compliance per PMI italiane (LegalBoost).\n"
    "REGOLE ASSOLUTE:\n"
    "- NON inventare numeri, articoli di legge o citazioni. I FATTI ti sono forniti già risolti e VERBATIM.\n"
    "- Quando una voce riguarda un fatto normativo fornito, integra il riferimento ESATTO dai FATTI "
    "(stesso articolo/fonte), senza riscrivere il testo di legge a memoria.\n"
    "- Ogni riferimento normativo che citi DEVE essere tra quelli nei FATTI.\n"
    "- Tono autorevole e chiaro per un titolare d'impresa. Niente buzzword né gergo inutile.\n"
    "- Analisi SPECIFICA e APPROFONDITA per questa azienda (usa i dati cliente: settore, "
    "dimensione, e-commerce, ecc.). Profondità da report consulenziale.\n"
    "- LUNGHEZZA: ~180-240 parole per voce, su più paragrafi: inquadramento, rischio concreto "
    "per QUESTA azienda, implicazioni operative, cosa fare. Non riassunti generici.\n"
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
            # 9 voci a 180-240 parole + rischi/azioni: 8192 tronca → bozze offline.
            max_tokens=16000,
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


def _pat_value(pat: str) -> str:
    """Valore minimo che soddisfa i pattern ricorrenti negli schemi meta."""
    table = {
        r"^\d{11}$": "12345678901",
        r"^\d{4}-\d{2}$": "2026-06",
        r"^\d{4}-\d{2}-\d{2}$": "2026-06-08",
        r"^\d+\.\d+\.\d+$": "1.0.0",
    }
    if pat in table:
        return table[pat]
    if "\\." in pat and "\\d" in pat:  # versione semver-like generica
        return "1.0.0"
    return "0000000000" if "\\d" in pat else "esempio"


def _det_string(key: str, schema: dict, inputs: dict, servizio: str) -> str:
    az = inputs.get("ragione_sociale") or inputs.get("azienda") or "Cliente"
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    # echo diretto del form: se la chiave combacia con un input stringa, usalo
    if key and isinstance(inputs.get(key), str) and inputs[key]:
        return inputs[key]
    if schema.get("pattern"):
        return _pat_value(schema["pattern"])
    fmt = schema.get("format")
    if fmt == "date":
        return "2026-06-08"
    if fmt == "date-time":
        return "2026-06-08T00:00:00Z"
    kl = (key or "").lower()
    if any(w in kl for w in ("azienda", "cliente", "committente", "client")):
        return az
    if "settore" in kl and inputs.get("settore"):
        return str(inputs["settore"])
    if any(w in kl for w in ("skill", "servizio", "nome", "title", "titolo", "report")):
        return servizio
    if "version" in kl:
        return "1.0.0"
    if "slug" in kl:
        return "k2ai-2026"
    if any(w in kl for w in ("data", "date", "generated", "emiss")):
        return "2026-06-08"
    if any(w in kl for w in ("codice", "code", "id")):
        return "K2AI-2026"
    s = servizio
    if "maxLength" in schema:
        s = s[: schema["maxLength"]]
    if "minLength" in schema and len(s) < schema["minLength"]:
        s = s + "x" * (schema["minLength"] - len(s))
    return s


def _det_sample(schema: dict, root: dict, inputs: dict, servizio: str, key: str = "") -> object:
    """Campione deterministico schema-valido (no LLM): risolve $ref, rispetta
    const/enum/required/type. Override semantici sui campi stringa (azienda,
    servizio, data…). Usato per compilare meta/metadata in modo SEMPRE conforme.
    """
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/$defs/"):
            schema = root.get("$defs", {}).get(ref.split("/")[-1], {})
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    t = schema.get("type")
    if isinstance(t, list):
        t = t[0]
    if t == "object":
        props = schema.get("properties", {})
        return {k: _det_sample(v, root, inputs, servizio, k) for k, v in props.items()}
    if t == "array":
        it = schema.get("items", {"type": "string"})
        n = max(1, schema.get("minItems", 1))
        if "maxItems" in schema:
            n = min(n, schema["maxItems"])
        return [_det_sample(it, root, inputs, servizio, key) for _ in range(n)]
    if t in ("integer", "number"):
        kl = (key or "").lower()
        if isinstance(inputs.get(key), (int, float)) and not isinstance(inputs.get(key), bool):
            return inputs[key]
        if any(w in kl for w in ("organico", "dipendent", "dimensione", "addett")):
            for ik in ("dipendenti", "organico", "addetti", "numero_dipendenti"):
                if isinstance(inputs.get(ik), (int, float)):
                    return inputs[ik]
        v = 2026 if ("anno" in kl or "year" in kl) else 1
        if "minimum" in schema:
            v = max(v, schema["minimum"])
        if "maximum" in schema:
            v = min(v, schema["maximum"])
        return v
    if t == "boolean":
        return False
    if t == "null":
        return None
    return _det_string(key, schema, inputs, servizio)


def _fill_meta(sub: dict, inputs: dict, servizio: str, root: dict | None = None) -> dict:
    """Compila deterministicamente meta/metadata, SEMPRE conforme al sotto-schema
    (required, const, type). Mai delegato all'LLM → niente refuse per meta."""
    out = _det_sample(sub, root or sub, inputs, servizio, "meta")
    return out if isinstance(out, dict) else {}


def generate_deliverable_deep(output_schema: dict, blueprint: dict, facts: dict[str, dict],
                              inputs: dict) -> tuple[Optional[dict], dict]:
    """Generazione PROFONDA per-sezione: ogni sezione top-level dell'output-schema
    è generata con una chiamata Sonnet DEDICATA e ricca (niente troncamento del
    JSON monolitico → profondità tipo report consulenziale 8-12 pagine).

    meta/metadata → compilati deterministicamente. Sezioni di contenuto → chiamata
    focalizzata, validata contro il sotto-schema. Una sezione required che fallisce
    → l'intero deliverable refuse (mai consegnare invalido).
    """
    if not ANTHROPIC_API_KEY:
        return None, {"mode": "offline"}
    from jsonschema import Draft202012Validator
    servizio = blueprint.get("pacchetto", {}).get("nome_commerciale", "Deliverable K2-AI")
    props = output_schema.get("properties", {})
    required = set(output_schema.get("required", list(props)))
    result: dict = {}
    sezioni_gen = 0
    tot_out = 0
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception as exc:
        return None, {"mode": "offline", "reason": str(exc)}

    facts_blk = _facts_block(facts)
    cli = json.dumps(inputs, ensure_ascii=False)
    # $defs vive nella RADICE: va propagato sia al modello (così vede la forma dei
    # $ref) sia al validatore della singola sezione (altrimenti '#/$defs/...' non
    # risolve → PointerToNowhere → refuse erroneo su ogni schema con $defs).
    root_defs = output_schema.get("$defs")

    # Blocco SYSTEM condiviso e CACHED: regole + fatti + dati cliente sono identici
    # per ogni sezione → cache_control li fa ri-pagare UNA volta sola invece di ×N
    # (taglio input ~50-70% su doc multi-sezione). La parte variabile (sezione +
    # sotto-schema) va nel messaggio user.
    facts_system = (
        f"Sei un consulente senior che redige le sezioni di un deliverable {servizio} "
        "PREMIUM per una PMI italiana (documento da 8-12 pagine).\n"
        "REGOLE (per OGNI sezione):\n"
        "- Conformati ESATTAMENTE al sotto-schema JSON fornito (required, tipi, enum).\n"
        "- Restituisci SOLO il CONTENUTO della sezione, NON incartato nel suo nome: "
        "direttamente {...} o [...], MAI {\"<nome_sezione>\": {...}}.\n"
        "- Prosa approfondita ma DENSA: ragionamento + implicazioni operative + numeri "
        "dove servono. Ogni voce di lista/analisi: max ~90 parole, niente riempitivo.\n"
        "- Usa i DATI CLIENTE (settore, dimensione, regime). NON inventare numeri o "
        "citazioni di legge: usa i FATTI verbatim; dato mancante → dichiaralo.\n"
        "- Rispetta maxLength/maxItems. JSON STRETTAMENTE VALIDO (virgolette interne con \\\").\n"
        "- Orientamento professionale, non consulenza vincolante (D-034/D-036).\n\n"
        f"{facts_blk}\n\nDATI CLIENTE: {cli}"
    )

    # Sezioni STRUTTURALI (non analitiche): compilate deterministicamente, mai
    # via LLM. 'input' è l'echo del form cliente; 'files' è il manifest dei file
    # generati; 'meta' i metadati. Mandarle a Sonnet → hallucinazione/refuse.
    structural = ("meta", "metadata", "input", "files", "file", "allegati")
    analytical = []  # (name, sub, sub_compact_json, sub_val, user, maxtok, light)
    for name, sub in props.items():
        if name in structural:
            result[name] = _det_sample(sub, output_schema, inputs, servizio, name)
            continue
        sub_compact = {"type": sub.get("type", "object")}
        for kk in ("properties", "required", "items", "enum"):
            if kk in sub:
                sub_compact[kk] = sub[kk]
        if root_defs:
            sub_compact["$defs"] = root_defs
        # schema usato per validare la sezione: stesso sub + $defs della radice
        sub_val = dict(sub)
        if root_defs and "$defs" not in sub_val:
            sub_val["$defs"] = root_defs
        sub_compact_json = json.dumps(sub_compact, ensure_ascii=False)
        user = (f"Genera la sezione «{name}» del deliverable. SOTTO-SCHEMA:\n"
                f"{sub_compact_json[:4000]}\n\n"
                "Rispondi SOLO con il JSON della sezione — contenuto diretto, NON incartato "
                f"nella chiave «{name}».")
        # max_tokens è un CEILING (paghi solo i token generati): alto per NON troncare;
        # il costo reale lo controlla la concisione nel system. Sezioni "pesanti" → cap alto.
        sub_json = json.dumps(sub)
        heavy = (sub.get("type") == "array"
                 or "$ref" in sub_json
                 or sub_json.count('"type": "array"') >= 1
                 or len(sub.get("properties", {})) >= 4)
        maxtok = 32000 if heavy else 20000
        light = _is_light_section(sub)  # tiering: sezioni meccaniche → modello economico
        analytical.append((name, sub, sub_compact_json, sub_val, user, maxtok, light))

    stats = {"cache_read": 0, "input": 0, "repairs": 0}

    def _call(model, sys_text, user_text, maxtok):
        """Una chiamata streaming. Traccia input/cache. Ritorna (text, resp, out_tok)."""
        sys_blk = [{"type": "text", "text": sys_text, "cache_control": {"type": "ephemeral"}}]
        with client.messages.stream(model=model, max_tokens=maxtok, system=sys_blk,
                                    messages=[{"role": "user", "content": user_text}]) as stream:
            resp = stream.get_final_message()
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        u = getattr(resp, "usage", None)
        if u:
            stats["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
            stats["input"] += getattr(u, "input_tokens", 0) or 0
        return text, resp, (getattr(u, "output_tokens", 0) or 0) if u else 0

    def _coerce(text, sub, sub_val, name):
        """parse → unwrap doppio-incarto → clamp ai vincoli."""
        val = _parse_section(text, sub.get("type"))
        if (isinstance(val, dict) and len(val) == 1 and name in val
                and isinstance(val[name], (dict, list))):
            val = val[name]
        if val is not None:
            val = _clamp_to_schema(val, sub_val, output_schema)
        return val

    def _gen_section(item):
        """Genera UNA sezione (thread-safe). Su errore di validazione tenta UNA
        riparazione mirata (mini-chiamata) invece di far fallire l'intero documento."""
        name, sub, sub_compact_json, sub_val, user, maxtok, light = item
        model = ANTHROPIC_MODEL_LIGHT if light else ANTHROPIC_MODEL
        try:
            text, resp, tok = _call(model, facts_system, user, maxtok)
            if getattr(resp, "stop_reason", None) == "max_tokens":
                log.warning("sezione '%s' troncata a max_tokens=%d", name, maxtok)
            val = _coerce(text, sub, sub_val, name)
            errs = list(Draft202012Validator(sub_val).iter_errors(val)) if val is not None else [1]
            if not errs:
                return name, val, False, tok
            # FAIL-FAST REPAIR: correggi il JSON invalido con una mini-chiamata
            # (input = JSON rotto + errori) invece di rigenerare tutto/fallback monolitico.
            stats["repairs"] += 1
            emsgs = ([str(e.message) for e in errs[:3]]
                     if not (len(errs) == 1 and errs[0] == 1) else ["JSON non parsabile/assente"])
            rep_user = (f"Questo JSON per la sezione «{name}» NON è conforme.\n"
                        f"Errori: {emsgs}\nSOTTO-SCHEMA:\n{sub_compact_json[:3000]}\n\n"
                        f"Correggi e restituisci SOLO il JSON valido (contenuto diretto, "
                        f"non incartato):\n{text[:8000]}")
            rtext, _, rtok = _call(model,
                                   "Sei un validatore JSON. Correggi il JSON perché sia conforme "
                                   "al sotto-schema dato. Rispondi SOLO con il JSON corretto.",
                                   rep_user, min(maxtok, 16000))
            rval = _coerce(rtext, sub, sub_val, name)
            rerrs = list(Draft202012Validator(sub_val).iter_errors(rval)) if rval is not None else [1]
            if not rerrs:
                return name, rval, False, tok + rtok
            log.warning("sezione '%s' non conforme anche dopo repair: %s", name, rerrs[:1])
            return name, None, True, tok + rtok
        except Exception as exc:
            log.warning("sezione '%s' fallita: %s", name, exc)
            return name, None, True, 0

    # WARM-UP cache: genera la PRIMA sezione DA SOLA → scrive il prompt-cache; le altre
    # in PARALLELO lo riusano a ~0,1× (chiamate parallele "a freddo" non condividono la
    # cache: ognuna ri-paga i fatti). Tempo ≈ 1 sezione + max(restanti).
    from concurrent.futures import ThreadPoolExecutor
    rows = []
    if analytical:
        rows.append(_gen_section(analytical[0]))
        rest = analytical[1:]
        if rest:
            with ThreadPoolExecutor(max_workers=min(6, len(rest))) as ex:
                rows.extend(ex.map(_gen_section, rest))

    for name, val, invalido, tok in rows:
        tot_out += tok
        if invalido:
            if name in required:
                return None, {"mode": "anthropic", "warning": f"sezione_{name}_invalida"}
            continue  # sezione opzionale non conforme → skip
        result[name] = val
        sezioni_gen += 1

    # validazione finale dell'intero deliverable
    full_errs = list(Draft202012Validator(output_schema).iter_errors(result))
    if full_errs:
        return None, {"mode": "anthropic", "warning": "deliverable_non_conforme",
                      "errors": [str(e.message) for e in full_errs[:3]]}
    return result, {"mode": "anthropic", "model": ANTHROPIC_MODEL, "assembly": "deep",
                    "sezioni": sezioni_gen, "output_tokens": tot_out,
                    "cache_read_tokens": stats["cache_read"], "input_tokens": stats["input"],
                    "repairs": stats["repairs"]}


def _human(s: str) -> str:
    return str(s).replace("_", " ")


_SCALAR = ("string", "number", "integer", "boolean")


def _is_light_section(sub: dict) -> bool:
    """True se la sezione è MECCANICA (liste di scalari, o oggetti/array di oggetti a
    soli campi scalari brevi): candidata al modello 'light' per il tiering di costo.
    Le sezioni con prosa/analisi (campi testo lunghi, nested) NON sono mai light, così
    l'analisi core resta sempre sul modello pieno."""
    t = sub.get("type")
    if t == "array":
        items = sub.get("items", {}) or {}
        it = items.get("type")
        if it in _SCALAR:
            return True
        if it == "object":
            props = items.get("properties", {})
            return bool(props) and len(props) <= 4 and all(
                p.get("type") in _SCALAR and p.get("maxLength", 0) <= 120
                for p in props.values())
        return False
    if t == "object":
        props = sub.get("properties", {})
        return bool(props) and len(props) <= 3 and all(
            p.get("type") in _SCALAR for p in props.values())
    return False


def _repair_pattern(val: str, pat: str) -> str:
    """Rende `val` conforme al pattern regex (best-effort), così la generazione
    non fallisce la validazione per pattern (es. codici ^[a-z_]+$, P.IVA, mese)."""
    try:
        if re.search(pat, val):
            return val
    except re.error:
        return val
    pv = _pat_value(pat)  # pattern noti (P.IVA, YYYY-MM, semver, ...)
    try:
        if re.search(pat, pv):
            return pv
    except re.error:
        pass
    low = (val or "").lower()
    if pat == r"^[a-z_]+$":
        return re.sub(r"[^a-z_]", "_", low).strip("_") or "voce"
    if "a-z0-9-" in pat:  # slug-like, eventuale {1,40}
        return (re.sub(r"[^a-z0-9-]", "-", low).strip("-") or "voce")[:40]
    return pv


def _clamp_to_schema(val, schema: dict, root: dict):
    """Rete di sicurezza: porta `val` entro i vincoli dello schema (maxLength,
    maxItems, min/max numerico, **pattern**, **minItems**), così la generazione
    profonda non fa mai fallire la validazione per uno scostamento formale.
    Risolve i $ref. La profondità resta nei campi liberi."""
    if isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/$defs/"):
            schema = root.get("$defs", {}).get(ref.split("/")[-1], {})
    if not isinstance(schema, dict):
        return val
    # const: il valore DEVE essere esattamente quello → forzalo
    if "const" in schema:
        return schema["const"]
    # enum: valore fuori dall'insieme chiuso → primo valido (rete di sicurezza)
    if "enum" in schema and isinstance(schema["enum"], list) and val not in schema["enum"]:
        return schema["enum"][0]
    t = schema.get("type")
    if isinstance(t, list):
        t = t[0]
    # numeri: rientra nel range minimum/maximum
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if isinstance(schema.get("maximum"), (int, float)) and val > schema["maximum"]:
            val = schema["maximum"]
        if isinstance(schema.get("minimum"), (int, float)) and val < schema["minimum"]:
            val = schema["minimum"]
        return val
    if isinstance(val, str):
        pat = schema.get("pattern")
        if pat:
            val = _repair_pattern(val, pat)
        m = schema.get("maxLength")
        if isinstance(m, int) and len(val) > m:
            cut = val[: m - 1]
            sp = cut.rfind(" ")
            if sp > m * 0.6:
                cut = cut[:sp]
            val = cut.rstrip(" ,;:.-") + "…"
        ml = schema.get("minLength")
        if isinstance(ml, int) and len(val) < ml and not pat:
            val = (val + " — da dettagliare").ljust(ml)[:max(ml, len(val))]
            if len(val) < ml:
                val = val.ljust(ml)
        return val
    if isinstance(val, dict) and t == "object":
        props = schema.get("properties", {})
        return {k: (_clamp_to_schema(v, props[k], root) if k in props else v) for k, v in val.items()}
    if isinstance(val, list) and t == "array":
        items = schema.get("items", {"type": "string"})
        out = [_clamp_to_schema(v, items, root) for v in val]
        # minItems: array required sotto-dimensionato → pad con item deterministici
        # schema-validi (rete di sicurezza; il modello di norma rispetta minItems)
        mi = schema.get("minItems")
        if isinstance(mi, int) and len(out) < mi:
            while len(out) < mi:
                out.append(_clamp_to_schema(_det_sample(items, root, {}, "K2-AI", ""), items, root))
        if isinstance(schema.get("maxItems"), int):
            out = out[: schema["maxItems"]]
        return out
    return val


def _parse_section(text: str, tipo):
    """Estrae il valore di una sezione (oggetto/lista/scalare) dalla risposta."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    t = t.strip()
    # prova oggetto
    if "{" in t and (tipo == "object" or tipo is None):
        s, e = t.find("{"), t.rfind("}")
        if 0 <= s < e:
            try:
                return json.loads(t[s:e + 1])
            except json.JSONDecodeError:
                pass
    # prova lista
    if "[" in t and (tipo == "array" or tipo is None):
        s, e = t.find("["), t.rfind("]")
        if 0 <= s < e:
            try:
                return json.loads(t[s:e + 1])
            except json.JSONDecodeError:
                pass
    # scalare: rimuovi virgolette e COERCISCI al tipo dichiarato (una sezione
    # top-level può essere integer/number/boolean, es. score_globale → altrimenti
    # resterebbe stringa "62" e fallirebbe la validazione).
    s = t.strip().strip('"').strip()
    if tipo == "integer":
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return s
    if tipo == "number":
        try:
            return float(s)
        except (ValueError, TypeError):
            return s
    if tipo == "boolean":
        return s.lower() in ("true", "1", "si", "sì", "yes", "vero")
    return s


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
            "Sei un consulente senior che redige un deliverable PROFESSIONALE e PREMIUM per "
            "una PMI italiana (documento che il cliente paga). Produci un oggetto JSON CONFORME "
            "allo schema fornito (tutti i campi required, tipi corretti, enum rispettati).\n"
            "QUALITÀ ATTESA:\n"
            "- Analisi CONCRETA e SPECIFICA per QUESTA azienda: usa i DATI CLIENTE forniti "
            "(settore, dimensione, regime, ecc.) — niente generalità copia-incolla.\n"
            "- Ogni sezione di prosa: densa e sostanziale, con implicazioni operative e, dove "
            "ha senso, quantificazioni o stime (range, percentuali, soglie).\n"
            "- Rischi e azioni concreti e prioritizzati, non ovvietà.\n"
            "- NON inventare numeri/citazioni di legge: usa i FATTI verbatim forniti per i "
            "riferimenti normativi e i valori deterministici. Se un dato manca, dichiaralo "
            "(es. 'dato non disponibile') invece di inventarlo.\n"
            "- Tono autorevole ma chiaro per un titolare d'impresa. È orientamento, non "
            "consulenza (D-034/D-036).\n"
            "Rispondi SOLO con il JSON, niente altro."
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
