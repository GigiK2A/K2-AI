"""Guardia NUMERI FINANZIARI INVENTATI della CHAT — presidio 'solo alto rischio'.

Review consolidamento (test M&A/IA): il modello, in una consulenza PRE-decisione, asserisce
con sicurezza inferenze economiche che NON sono ricavabili dai dati disponibili:
  - «500.000 € rappresentano il 10-12% del fatturato» (fatturato non fornito)
  - «il ROI sarà del 25%»
  - «il payback sarà di 3 anni»
Sono i numeri che SEMBRANO giusti e non lo sono. Il prompt da solo non li ferma → serve un
presidio DETERMINISTICO sul testo in uscita, come deadline_guard/norme_guard.

Filosofia (§1 review: PRIORITÀ ASSOLUTA): in chat NON si stimano ROI, payback, quote di
fatturato/margine se i dati base non ci sono. Questi valori sono territorio del REPORT (che ha
provenienza e assunzioni dichiarate), non della chat. La guardia rende DESCRITTIVO il numero:
resta la sostanza («il ROI andrà calcolato»), sparisce la cifra inventata, e si dichiara cosa
serve per stimarla — esattamente ciò che chiede la review.

Deliberatamente CONSERVATIVA (come le altre guardie): colpisce solo i pattern ad altissima
precisione (ROI col %, payback in anni/mesi, incidenza % sul fatturato/margine) tipici della
proiezione inventata. Un valore FORNITO dall'utente non usa queste forme proiettive.

KBOT_FINANCE_GUARD=0 disattiva.
"""
from __future__ import annotations

import os
import re

_DISCLAIMER = ("non è stimabile senza i dati economici (fatturato, margini, costi, "
               "struttura finanziaria)")

# ── ROI / ritorno sull'investimento espresso in percentuale ──────────────────────────────
# «ROI del 25%», «ritorno sull'investimento (atteso) di circa il 30%», «rendimento del 15%».
_ROI = re.compile(
    r"\b(?P<pre>roi|ritorno\s+sull['’\s]*investiment\w*|ritorno\s+dell['’\s]*investiment\w*|"
    r"rendiment\w+\s+(?:dell['’\s]*investiment\w*|atteso|previsto))\b"
    r"(?P<mid>[^.,;:!?\n]{0,35}?)"
    r"(?:\+|del|di|pari\s+al|al|circa\s+(?:il|del)?|intorno\s+al|attorno\s+al|stimat\w+\s+(?:al|in))?\s*"
    r"\d+(?:[.,]\d+)?\s*(?:-\s*\d+(?:[.,]\d+)?\s*)?(?:%|per\s*cento)",
    re.I,
)

# ── Payback / tempo di rientro in anni o mesi ─────────────────────────────────────────────
# «payback di 3 anni», «il tempo di ritorno sarà di 18 mesi», «si ripaga in 2 anni».
_PAYBACK = re.compile(
    r"\b(?P<pre>payback|tempo\s+di\s+(?:ritorno|rientro|recupero)|"
    r"periodo\s+di\s+(?:ritorno|rientro|recupero|payback)|rientr\w+\s+dell['’\s]*investiment\w*|"
    r"si\s+ripagh\w+|si\s+ripaga|si\s+ripagher\w+|si\s+recuper\w+)\b"
    r"(?P<mid>[^.,;:!?\n]{0,30}?)"
    r"(?:in|di|entro|circa|dopo)?\s*\d+(?:[.,]\d+)?\s*(?:-\s*\d+\s*)?(?:ann[oi]|mes[ei])\b",
    re.I,
)

# ── Incidenza percentuale su fatturato / margine / ricavi / EBITDA ────────────────────────
# «rappresentano il 10-12% del fatturato», «pari al 15% dei ricavi», «incide per il 20% sul
# margine». La cifra è sostituita; resta la base («del fatturato») per non perdere la frase.
_SHARE = re.compile(
    r"(?:rappresent\w+|pari\s+a|incid\w+|equival\w+|circa|corrispond\w+|è\s+il|sono\s+il|"
    r"pes\w+\s+(?:per|il))?\s*"
    r"(?:l['’]|il\s+|al\s+|del\s+)?\d+(?:[.,]\d+)?\s*(?:-\s*\d+(?:[.,]\d+)?\s*)?(?:%|per\s*cento)"
    r"\s*(?P<base>(?:del|dei|sul|sui|di|su)\s+(?:fatturat\w+|ricav\w+|margin\w+|ebitda|"
    r"utile\w*|redditivit\w+))\b",
    re.I,
)


def _enabled() -> bool:
    return os.getenv("KBOT_FINANCE_GUARD", "1") != "0"


def _soften_roi(m: "re.Match") -> str:
    # tieni solo la parola-chiave (ROI/ritorno…), scarta i connettivi ('sarà del', 'di circa')
    return f"{m.group('pre')} {_DISCLAIMER}"


def _soften_payback(m: "re.Match") -> str:
    return f"{m.group('pre')} {_DISCLAIMER}"


def _soften_share(m: "re.Match") -> str:
    # spazio iniziale: la % può aver assorbito lo spazio precedente (la pulizia collassa i doppi)
    return f" una quota non determinabile {m.group('base')}"


def sanitize(text: str) -> str:
    """Rende descrittive le inferenze finanziarie inventate (ROI %, payback, incidenza % su
    fatturato/margine). Locale, deterministico, idempotente. Non tocca cifre in altri
    contesti (prezzi, importi forniti). Best-effort: mai solleva."""
    if not text or not _enabled():
        return text
    try:
        out = _ROI.sub(_soften_roi, text)
        out = _PAYBACK.sub(_soften_payback, out)
        out = _SHARE.sub(_soften_share, out)
        out = re.sub(r"[ \t]{2,}", " ", out)
        return out
    except Exception:
        return text
