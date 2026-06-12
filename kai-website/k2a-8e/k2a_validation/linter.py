"""CORE — motore di lint semi-dichiarativo dei deliverable K2-AI.

Il linter NON legge il file binario del deliverable: lavora su una *descrizione
strutturata* (instance) di ciò che il deliverable contiene. Questo rende il
linter deterministico, testabile e indipendente dal formato (docx/html/pdf).

Le regole vivono nel blueprint (`regole_validazione_linter`). Il motore classifica
ogni regola, via euristica sul testo, in un *tipo di controllo* e applica il check
corrispondente a (blueprint, instance). Ogni finding eredita la severità dichiarata
dalla regola: "errore" blocca, "warning" segnala.

instance (dict) — campi attesi (tutti opzionali, default permissivi):
  formato            : str   (deve combaciare con blueprint.formato_primario)
  voci               : [ {id, pagine:int, contenuti:[str], cta:bool} ]
  artefatti          : [str] (id artefatti_bundle prodotti)
  elementi_grafici   : [str]
  tabelle            : [str]
  elementi           : [str] (elementi_obbligatori per html)
  ha_disclaimer      : bool
  json_output_valido : bool
  prezzi_hardcoded   : bool
  peso_kb            : int|None
  dipendenze_esterne : bool
"""
from __future__ import annotations

import re
import unicodedata


# ---------------------------------------------------------------- utilità testo

def _norm(s: str) -> str:
    """minuscolo, senza accenti, spazi compattati — per match robusti."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def _tokens_voce(voce_inst: dict) -> str:
    """concatena tutto il contenuto rilevabile di una voce-instance in un blob."""
    parts = []
    for k in ("contenuti", "argomenti_presenti", "elementi"):
        v = voce_inst.get(k)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
        elif isinstance(v, str):
            parts.append(v)
    for k in ("testo", "titolo"):
        if voce_inst.get(k):
            parts.append(str(voce_inst[k]))
    return _norm(" || ".join(parts))


def _covered(needle: str, haystack: str) -> bool:
    """un argomento è coperto se almeno 2 parole-chiave (>=4 lettere) compaiono,
    oppure se l'intera stringa normalizzata è contenuta."""
    n = _norm(needle)
    if n and n in haystack:
        return True
    words = [w for w in re.split(r"[^a-z0-9]+", n) if len(w) >= 4]
    if not words:
        # argomenti molto corti: basta una parola
        words = [w for w in re.split(r"[^a-z0-9]+", n) if w]
        return any(w in haystack for w in words)
    hits = sum(1 for w in words if w in haystack)
    return hits >= min(2, len(words))


# ----------------------------------------------------- classificazione regola

def _classify(regola_testo: str) -> str:
    t = _norm(regola_testo)
    # ordine: dal più specifico al più generico
    if "json" in t and ("valida" in t or "contratto" in t):
        return "json_output"
    if "prezzo" in t or "prezzi" in t or "hard-coded" in t or "hardcoded" in t or "hard coded" in t:
        return "prezzi"
    if "disclaimer" in t:
        return "disclaimer"
    if "cta" in t:
        return "cta"
    if "artefatti" in t or "artefatto" in t or "file_generati" in t or "bundle" in t:
        return "artefatti"
    if ("grafic" in t) and "presenti" in t:
        return "elementi_grafici"
    if ("tabell" in t) and "presenti" in t:
        return "tabelle"
    if "glossario" in t:
        return "glossario"
    if "peso" in t or " kb" in t or "dipendenz" in t:
        return "peso_dipendenze"
    if "executive" in t or ("summary" in t):
        return "exec_summary"
    # conteggio card/criticità: trigger per PAROLA-CHIAVE, valore atteso da conteggi_attesi
    # (VIA B, #21b-res). NON dipende dalla cifra nel testo (elimina il bug "N!=6").
    if "critic" in t:
        return "n_criticita"
    if "card" in t or "semafor" in t or "dimension" in t:
        return "n_card"
    if "gauge" in t or ("score" in t and "0-100" in t):
        return "gauge"
    if "ordine" in t or ("capitol" in t and "present" in t) or ("sezion" in t and "present" in t):
        return "voci_ordine"
    if "somma pagine" in t or ("pagine" in t and ("totali" in t or "entro" in t)):
        return "pagine_totali"
    if "pagine per capitolo" in t or "pagine per voce" in t or ("pagine" in t and "range" in t):
        return "pagine_voce"
    if "argoment" in t and ("rilevabile" in t or "present" in t):
        return "argomenti"
    if "tono" in t or "gergal" in t or "lista nera" in t:
        return "tono"
    return "manuale"


# ------------------------------------------------------------------ i check

# Sentinella: un check ritorna SKIP quando l'input che gli serve è None/assente
# nell'instance (modalità document-extraction). NON è errore né warning: la regola
# è "non valutata". Retrocompatibile: le fixture popolano i campi -> nessuno skip.
class _Skip:
    __slots__ = ("motivo",)

    def __init__(self, motivo: str):
        self.motivo = motivo


def _voce_inst_by_id(instance: dict) -> dict:
    out = {}
    for v in instance.get("voci", []) or []:
        if isinstance(v, dict) and v.get("id"):
            out[v["id"]] = v
    return out


def _voci_senza_id(instance: dict) -> bool:
    """True se ci sono voci ma nessuna ha un id (mapping canonico non fornito)."""
    voci = instance.get("voci", []) or []
    return bool(voci) and not any(isinstance(v, dict) and v.get("id") for v in voci)


def _pagine_tutte_none(instance: dict) -> bool:
    """True se ci sono voci ma nessuna espone un numero di pagine."""
    voci = instance.get("voci", []) or []
    return bool(voci) and all(v.get("pagine") is None for v in voci if isinstance(v, dict))


def _check(kind: str, blueprint: dict, instance: dict) -> list[str]:
    """ritorna lista di messaggi-problema (vuota = ok)."""
    voci_bp = blueprint.get("voci", []) or []
    inst_by_id = _voce_inst_by_id(instance)
    msgs: list[str] = []

    # --- guard "input assente -> salta" (D-025) ---------------------------
    if kind in ("voci_ordine", "argomenti") and _voci_senza_id(instance):
        return _Skip("input mancante: voci[].id (mapping canonico non fornito)")
    if kind in ("pagine_totali", "pagine_voce") and _pagine_tutte_none(instance):
        return _Skip("input mancante: voci[].pagine (page-count non disponibile)")
    if kind == "exec_summary" and _pagine_tutte_none(instance):
        return _Skip("input mancante: voci[].pagine (exec_summary page-based)")
    if kind == "json_output" and instance.get("json_output_valido") is None:
        return _Skip("input mancante: json_output_valido (twin non fornito)")
    if kind == "artefatti" and instance.get("artefatti") is None:
        return _Skip("input mancante: artefatti (estrazione mono-file: bundle non attestabile)")
    # ----------------------------------------------------------------------

    if kind == "voci_ordine":
        ordered_bp = [v["id"] for v in sorted(voci_bp, key=lambda x: x.get("ord", 0))]
        present = [v.get("id") for v in instance.get("voci", []) or []]
        missing = [i for i in ordered_bp if i not in present]
        if missing:
            msgs.append(f"voci mancanti: {missing}")
        # ordine relativo
        seq = [i for i in present if i in ordered_bp]
        if seq != [i for i in ordered_bp if i in present]:
            msgs.append(f"ordine voci non canonico: atteso {ordered_bp}, trovato {seq}")

    elif kind == "pagine_totali":
        pt = blueprint.get("pagine_totali")
        if pt and instance.get("voci"):
            tot = sum(int(v.get("pagine", 0) or 0) for v in instance["voci"])
            if not (pt["min"] <= tot <= pt["max"]):
                msgs.append(f"pagine totali {tot} fuori range [{pt['min']},{pt['max']}]")

    elif kind == "pagine_voce":
        for v in voci_bp:
            rng = v.get("pagine")
            inst = inst_by_id.get(v["id"])
            if rng and inst and inst.get("pagine") is not None:
                p = int(inst["pagine"])
                if not (rng["min"] <= p <= rng["max"]):
                    msgs.append(f"voce '{v['id']}': {p} pag. fuori range [{rng['min']},{rng['max']}]")

    elif kind == "argomenti":
        for v in voci_bp:
            inst = inst_by_id.get(v["id"])
            if inst is None:
                continue  # mancanza già segnalata da voci_ordine
            blob = _tokens_voce(inst)
            for arg in v.get("argomenti_obbligatori", []):
                if not _covered(arg, blob):
                    msgs.append(f"voce '{v['id']}': argomento non rilevato → '{arg}'")

    elif kind == "exec_summary":
        # individua la voce executive summary
        es = next((v for v in voci_bp if "summary" in _norm(v.get("id", "")) or "summary" in _norm(v.get("titolo", ""))), None)
        if es:
            inst = inst_by_id.get(es["id"])
            rng = es.get("pagine")
            if inst and rng and inst.get("pagine") is not None:
                if int(inst["pagine"]) > rng["max"]:
                    msgs.append(f"executive summary {inst['pagine']} pag. > max {rng['max']}")

    elif kind == "artefatti":
        req = [a["id"] for a in blueprint.get("artefatti_bundle", []) if a.get("obbligatorio")]
        have = set(instance.get("artefatti", []) or [])
        for a in req:
            if a not in have:
                msgs.append(f"artefatto obbligatorio mancante: '{a}'")

    elif kind == "elementi_grafici":
        for g in blueprint.get("elementi_grafici_obbligatori", []):
            if not any(_covered(g, _norm(x)) for x in instance.get("elementi_grafici", []) or []):
                msgs.append(f"elemento grafico mancante: '{g}'")

    elif kind == "tabelle":
        for tb in blueprint.get("tabelle_obbligatorie", []):
            if not any(_covered(tb, _norm(x)) for x in instance.get("tabelle", []) or []):
                msgs.append(f"tabella mancante: '{tb}'")

    elif kind in ("disclaimer", "glossario"):
        # cerca in ha_disclaimer / nei contenuti di tutte le voci
        if kind == "disclaimer" and instance.get("ha_disclaimer"):
            pass
        else:
            allblob = " ".join(_tokens_voce(v) for v in instance.get("voci", []) or [])
            if kind not in allblob and not (kind == "disclaimer" and instance.get("ha_disclaimer")):
                msgs.append(f"{kind} non rilevato nel deliverable")

    elif kind == "cta":
        has_cta = bool(instance.get("ha_cta")) or any(
            v.get("cta") for v in instance.get("voci", []) or []
        )
        if not has_cta:
            allblob = " ".join(_tokens_voce(v) for v in instance.get("voci", []) or [])
            if "cta" not in allblob and "call gratuita" not in allblob:
                msgs.append("CTA non rilevata nel deliverable")

    elif kind == "json_output":
        if instance.get("json_output_valido") is False:
            msgs.append("json_output NON valida contro contratto_dati")
        elif instance.get("json_output_valido") is None:
            msgs.append("json_output non verificato (campo assente)")

    elif kind == "prezzi":
        if instance.get("prezzi_hardcoded"):
            msgs.append("prezzo hard-coded rilevato: deve essere risolto da catalogo")

    elif kind == "peso_dipendenze":
        vf = blueprint.get("vincoli_formato", {}) or {}
        mx = vf.get("peso_kb_max")
        if mx and instance.get("peso_kb") is not None and instance["peso_kb"] > mx:
            msgs.append(f"peso {instance['peso_kb']}KB > max {mx}KB")
        if instance.get("dipendenze_esterne"):
            msgs.append("dipendenze esterne presenti (atteso: nessuna)")

    elif kind == "n_card":
        exp = (blueprint.get("conteggi_attesi") or {}).get("card_semaforo")
        if exp is None:
            return _Skip("conteggio card_semaforo non dichiarato (conteggi_attesi)")
        n = instance.get("n_card_semaforo")
        if n is not None and n != exp:
            msgs.append(f"card semaforo: {n} (atteso {exp})")

    elif kind == "n_criticita":
        exp = (blueprint.get("conteggi_attesi") or {}).get("criticita")
        if exp is None:
            return _Skip("conteggio criticita non dichiarato (conteggi_attesi)")
        n = instance.get("n_criticita")
        if n is not None and n != exp:
            msgs.append(f"criticità: {n} (atteso {exp})")

    elif kind == "gauge":
        if instance.get("ha_gauge") is False:
            msgs.append("gauge 0-100 assente")

    elif kind in ("tono", "manuale"):
        # non automatizzabile in modo affidabile: nessun finding automatico
        pass

    return msgs


# ------------------------------------------------------------------ API pubblica

def lint(blueprint: dict, instance: dict) -> dict:
    """Applica le regole del blueprint all'instance. Ritorna report strutturato."""
    findings: list[dict] = []
    instance = instance or {}

    # coerenza di formato (pre-check, severità errore)
    fp = blueprint.get("formato_primario")
    fi = instance.get("formato")
    if fi and fp and _norm(fi) != _norm(fp):
        findings.append({
            "regola": "formato",
            "severita": "errore",
            "messaggio": f"formato instance '{fi}' ≠ formato_primario blueprint '{fp}'",
        })

    non_valutate: list[dict] = []
    for regola in blueprint.get("regole_validazione_linter", []) or []:
        kind = _classify(regola.get("regola", ""))
        sev = regola.get("severita", "warning")
        res = _check(kind, blueprint, instance)
        if isinstance(res, _Skip):
            non_valutate.append({
                "regola": regola.get("id", "?"),
                "tipo": kind,
                "severita": "non_valutata",
                "messaggio": res.motivo,
            })
            continue
        for m in res:
            findings.append({
                "regola": regola.get("id", "?"),
                "tipo": kind,
                "severita": sev,
                "messaggio": m,
            })

    errors = sum(1 for f in findings if f["severita"] == "errore")
    warnings = sum(1 for f in findings if f["severita"] == "warning")
    return {
        "skill": blueprint.get("pacchetto", {}).get("skill"),
        "tier": blueprint.get("pacchetto", {}).get("tier"),
        "esito": "PASS" if errors == 0 else "FAIL",
        "errori": errors,
        "warning": warnings,
        "findings": findings,
        "non_valutate": non_valutate,
    }
