"""Auto-compilazione degli input del motore 8e dalla conversazione.

Design "ufficiale" (giu 2026): l'utente NON riempie form. Il bot raccoglie i dati
chiacchierando (domande + file/bilanci caricati); al momento di generare, qui un
LLM economico (Haiku) estrae i valori dei campi richiesti dal boost a partire dal
contesto della sessione. Niente invenzioni: se un dato non c'è, il campo si omette.
"""
from __future__ import annotations

import json
import logging
import os
import re
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


def _uploaded_full_text(session: dict) -> str:
    """Testo INTEGRALE dei file caricati (non i 600 char del context block): per
    estrarre/trascrivere un bilancio servono TUTTE le righe, non un estratto."""
    collected = session.get("collected_data") or session.get("collected") or {}
    files = collected.get("uploaded_files") or []
    parts = []
    for f in files if isinstance(files, list) else []:
        if not isinstance(f, dict):
            continue
        txt = (f.get("extractedText") or f.get("extractedSummary") or "").strip()
        if txt:
            parts.append(f"### {f.get('name') or 'documento'}\n{txt}")
    return "\n\n".join(parts)[:60000]  # cap di sicurezza


# Istruzioni SPECIFICHE per i boost finanziari: l'LLM TRASCRIVE le righe del bilancio
# (compito affidabile), NON calcola aggregati derivati (PN, EBITDA — sbagliava). La
# riclassificazione + l'aritmetica le fa il motore 8e (app/finance.py), deterministico.
_BILANCIO_INSTRUCTIONS = (
    "\n\nESTRAZIONE BILANCIO (campo 'bilanci'):\n"
    "- Per OGNI esercizio crea un oggetto {anno, ...}.\n"
    "- DUE MODI, scegli in base a COSA ha dato il cliente:\n"
    "  A) Se il cliente ha fornito le RIGHE DETTAGLIATE del bilancio (voci di SP e CE): "
    "trascrivile in 'voci' come {sezione, descrizione, importo} — sezione 'attivo'/'passivo' "
    "per lo Stato Patrimoniale, 'costi'/'ricavi' per il Conto Economico, 'risultato' per "
    "l'utile/perdita. In questo caso NON calcolare aggregati: li deriva il sistema dalle voci.\n"
    "  B) Se il cliente ha fornito solo AGGREGATI già calcolati (es. 'EBITDA 3,36M, EBIT "
    "2,15M, utile 1,15M, PFN 5,5M, liquidità 3,2M, patrimonio netto 12M'): NON inventare "
    "voci di dettaglio e NON mettere gli aggregati dentro 'voci' (li scambieresti per righe "
    "di costo → il sistema calcolerebbe EBITDA sbagliato). Compila invece i CAMPI aggregati "
    "top-level dell'oggetto bilancio: ricavi, ebitda, reddito_operativo (EBIT), utile_netto, "
    "totale_attivo, patrimonio_netto, debiti_finanziari, liquidita, pfn, attivo_corrente, "
    "passivo_corrente, rimanenze. Ometti quelli non forniti. Lascia 'voci' assente o vuoto.\n"
    "- importo/valori: numero puro in EUR (es. 289835.07). Converti '1.234,56' -> 1234.56. "
    "'3,36M'/'3,36 milioni' -> 3360000. Mantieni i valori ESATTI del cliente, non arrotondare.\n"
    "- Includi la riga 'Utile/Perdita del periodo' (sezione 'risultato') SOLO nel modo A.\n"
    "- Modo A: non saltare righe, la quadratura (attivo = passivo + utile) deve tornare.\n"
    "- Aggiungi anche 'ragione_sociale': la denominazione dell'azienda dall'intestazione "
    "del bilancio (es. 'K2A S.r.l.s.')."
)


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


def _as_num(x: Any) -> Optional[float]:
    """Parsing numerico locale-aware. Gestisce sia il formato IT ('1.234.567',
    '1.234,56') sia EN ('1234.56', '40000'). Prima '1.234.567' → None (i punti-migliaia
    italiani venivano interpretati come decimali) → un bilancio VERO veniva scartato e la
    sessione degradava a PARTIAL."""
    if isinstance(x, (int, float)):
        try:
            return float(x)
        except Exception:
            return None
    s = str(x).strip()
    if not s:
        return None
    has_dot, has_comma = "." in s, "," in s
    try:
        if has_dot and has_comma:
            # Il separatore DECIMALE è l'ultimo che compare. Formato IT '1.234,56'
            # (virgola decimale) vs EN '1,234.56' (punto decimale).
            if s.rfind(",") > s.rfind("."):        # IT: punti = migliaia, virgola = decimale
                s = s.replace(".", "").replace(",", ".")
            else:                                    # EN: virgole = migliaia, punto = decimale
                s = s.replace(",", "")
        elif has_comma:
            # Solo virgole: se una sola ed è decimale ('1234,56') → punto decimale;
            # se multiple → migliaia ('1,234,567').
            if s.count(",") == 1:
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        elif has_dot:
            # Solo punti: multipli = migliaia IT ('1.234.567'); singolo con !=3 cifre
            # dopo = decimale ('1234.56'); singolo con esattamente 3 cifre dopo è
            # ambiguo ('1.234') → trattiamo come migliaia (caso reale nei bilanci IT).
            if s.count(".") > 1:
                s = s.replace(".", "")
            else:
                intpart, decpart = s.split(".")
                if len(decpart) == 3 and intpart.lstrip("-+").isdigit():
                    s = s.replace(".", "")           # '1.234' → migliaia
                # altrimenti lascia il punto come decimale ('1234.56', '12.5')
        return float(s)
    except Exception:
        return None


def _bilancio_ha_attivo(b: Any) -> bool:
    """Un bilancio VERO ha un attivo (stato patrimoniale). L'autofill a volte fabbrica un
    bilancio da frammenti di chat (solo utile/debiti, attivo=0): non quadra e l'8e lo
    rifiuta. Meglio scartarlo qui → il campo resta mancante → parte il report preliminare
    (dati parziali + ipotesi) invece di numeri finti (es. utile scambiato per patrimonio netto).
    Conservativo: scarta SOLO se non trova alcun attivo positivo (un SP reale ne ha sempre)."""
    if not isinstance(b, dict):
        return False
    tot = 0.0
    voci = b.get("voci")
    if isinstance(voci, list):
        for v in voci:
            if isinstance(v, dict) and str(v.get("sezione", "")).lower().startswith("attiv"):
                n = _as_num(v.get("valore") or v.get("importo"))
                if n:
                    tot += n
    for k in ("attivo", "totale_attivo", "attivo_totale"):
        n = _as_num(b.get(k))
        if n:
            tot += n
    return tot > 0


# --- Cross-check numerico (bug "EBITDA 720k → 230k"): l'estrazione passa per un LLM,
# che può trascrivere male una cifra. Ogni numero estratto deve ESISTERE nel corpus che
# l'LLM ha visto (contesto + conversazione + documenti); se non c'è, il campo si scarta:
# meglio un report PRELIMINARE con un dato in meno che un report con un numero sbagliato.
# KBOT_AUTOFILL_NUMCHECK=0 disattiva.

_NUM_TOKEN_RE = re.compile(
    r"(\d+(?:[.,]\d+)*)\s*(k\b|mila\b|mln\b|M\b|milion[ei]\b|miliard[oi]\b)?"
)
_SUFFIX_FACTOR = {"k": 1e3, "mila": 1e3, "mln": 1e6, "M": 1e6,
                  "milione": 1e6, "milioni": 1e6, "miliardo": 1e9, "miliardi": 1e9}


def _numcheck_enabled() -> bool:
    return os.getenv("KBOT_AUTOFILL_NUMCHECK", "1") != "0"


def _corpus_numbers(text: str) -> set[float]:
    """Tutti i numeri presenti nel testo, in ogni formato (IT '1.234,56', EN '1234.56',
    abbreviati '720k', '4,5 mln', '2 milioni')."""
    nums: set[float] = set()
    for m in _NUM_TOKEN_RE.finditer(text or ""):
        base = _as_num(m.group(1))
        if base is None:
            continue
        nums.add(base)
        suf = m.group(2)
        if suf:
            factor = _SUFFIX_FACTOR.get(suf) or _SUFFIX_FACTOR.get(suf.lower())
            if factor:
                nums.add(base * factor)
        # '1.234' è ambiguo (migliaia IT vs decimale EN): accetta entrambe le letture
        raw = m.group(1)
        if raw.count(".") == 1 and "," not in raw:
            try:
                nums.add(float(raw))
            except ValueError:
                pass
    return nums


def _number_in_corpus(v: float, nums: set[float]) -> bool:
    tol = max(0.011, abs(v) * 1e-9)  # 0.011 assorbe arrotondamenti al centesimo
    return any(abs(n - v) <= tol for n in nums)


def drop_unverified_numbers(out: dict, by_id: dict, corpus: str) -> tuple[dict, list[str]]:
    """Rimuove i campi numerici il cui valore non compare nel corpus visto dall'LLM.
    Ritorna (out filtrato, lista campi scartati). I campi enum e non numerici non si
    toccano; gli importi dei 'bilanci' si verificano ma NON si scartano (la trascrizione
    da OCR può variare nel formato): un mismatch lì produce solo un log."""
    nums = _corpus_numbers(corpus)
    dropped: list[str] = []
    for k in list(out.keys()):
        c = by_id.get(k) or {}
        if c.get("enum") or c.get("tipo") not in ("integer", "number"):
            continue
        v = out[k]
        if isinstance(v, (int, float)) and not isinstance(v, bool) \
                and not _number_in_corpus(float(v), nums):
            dropped.append(f"{k}={v}")
            out.pop(k)
    bilanci = out.get("bilanci")
    if isinstance(bilanci, list):
        unmatched = 0
        for b in bilanci:
            for voce in (b.get("voci") or []) if isinstance(b, dict) else []:
                imp = _as_num(voce.get("importo")) if isinstance(voce, dict) else None
                if imp is not None and not _number_in_corpus(imp, nums):
                    unmatched += 1
        if unmatched:
            log.warning("autofill: %d importi di bilancio non riscontrati nel corpus "
                        "(possibile errore di trascrizione LLM)", unmatched)
    return out, dropped


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

    is_financial = any(c.get("id") == "bilanci" for c in campi)

    system = (
        "Sei un estrattore di dati. Dal CONTESTO (conversazione + eventuali bilanci/"
        "file caricati) compili i campi necessari a generare un documento professionale.\n"
        "REGOLE:\n"
        "- Usa SOLO informazioni presenti nel contesto. Se un campo non è deducibile, "
        "OMETTI la chiave (non inventare, non mettere placeholder).\n"
        "- Numeri SEMPRE in cifre, senza separatori di migliaia né valuta "
        "(es. 1500000, non '1,5M'); i decimali col punto (1234.56).\n"
        "- Per i campi con valori ammessi (enum) usa ESATTAMENTE uno di quelli.\n"
        "- Per i campi 'array' (es. bilanci, competitor) restituisci una lista.\n"
        "- Rispondi SOLO con un oggetto JSON {campo: valore}, niente altro testo."
        + (_BILANCIO_INSTRUCTIONS if is_financial else "")
    )
    docs = f"\n\nDOCUMENTI CARICATI (testo integrale):\n{_uploaded_full_text(session)}" if is_financial else ""
    user = (
        f"CONTESTO:\n{context}\n\nCONVERSAZIONE RECENTE:\n{convo}{docs}\n\n"
        f"CAMPI DA COMPILARE:\n{spec}\n\nJSON:"
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            # la trascrizione di un bilancio completo (decine di righe) non sta in 2500 token
            max_tokens=8000 if is_financial else 2500,
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
    if _numcheck_enabled():
        out, dropped = drop_unverified_numbers(out, by_id, f"{context}\n{convo}{docs}")
        if dropped:
            log.warning("autofill: numeri non presenti in conversazione/documenti, "
                        "campi scartati: %s", ", ".join(dropped))

    # Bug-F: scarta bilanci fabbricati senza attivo (frammenti di chat, non un SP reale).
    # Se nessun bilancio è valido, ometti il campo → il gate lo vede mancante → report
    # preliminare (dati parziali) invece di alimentare il motore con numeri incoerenti.
    if isinstance(out.get("bilanci"), list):
        good = [b for b in out["bilanci"] if _bilancio_ha_attivo(b)]
        if good:
            out["bilanci"] = good
        else:
            out.pop("bilanci", None)
            log.info("autofill: scartato bilancio senza attivo (fabbricato da frammenti) → preliminare")

    # ragione_sociale è un metadato trasversale (non un campo del form): il motore lo
    # richiede per personalizzare e identificare il report → tienilo se estratto.
    rs = data.get("ragione_sociale")
    if isinstance(rs, str) and rs.strip():
        out["ragione_sociale"] = rs.strip()
    return out
