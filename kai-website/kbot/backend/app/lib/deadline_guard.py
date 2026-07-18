"""Guardia SCADENZE / TERMINI / SOGLIE di legge della CHAT — presidio 'solo alto rischio'
(scelta di Luca, 17 lug).

Il problema (dimostrato live, caso #6): il modello locale — anche COL grounding — asserisce
scadenze legali/fiscali/amministrative SBAGLIATE. Es.: «la comunicazione di assunzione va
fatta entro 5 giorni» — è un errore diffuso sul web (va fatta PRIMA dell'inizio del rapporto),
che il modello ripete con sicurezza. Il prompt da solo non lo ferma: serve un presidio
DETERMINISTICO, come norme_guard fa con i numeri di articolo.

Regola (stessa filosofia della chat descriptive-only): in un CONTESTO NORMATIVO
(adempimenti, fisco, lavoro, obblighi di comunicazione…), una scadenza/termine espresso con
un NUMERO preciso o una soglia di legge in euro viene reso DESCRITTIVO — resta la sostanza
(«c'è un termine preciso», «c'è una soglia»), sparisce la cifra non verificata, e si rimanda
alla fonte ufficiale / al report (che ha il grounding sul testo di legge).

NON tocca i numeri di BUSINESS: benchmark di marketing, prezzi, quote di mercato, importi
forniti dall'utente, scadenze commerciali («pagamento a 30 giorni», «consegna in 3 giorni»).
Il gate di contesto (serve un marcatore legale/fiscale/amministrativo vicino) li protegge.

KBOT_DEADLINE_GUARD=0 disattiva.
"""
from __future__ import annotations

import os
import re

# ── Contesto NORMATIVO: senza uno di questi marcatori vicino, non si tocca nulla ──────────
# (protegge i numeri di business: marketing %, prezzi, fatturato dato dall'utente, ecc.)
_LEGAL_CTX = re.compile(
    r"\b(comunicaz\w+|assunzion\w+|unilav|collocament\w+|centro per l'impiego|"
    r"inps|inail|agenzia delle entrate|adempiment\w+|versament\w+|dichiarazion\w+|"
    r"ravvediment\w+|denunc\w+|deposit\w+ del bilancio|bilancio d'esercizio|"
    r"scadenz\w+ fiscal\w+|contribut\w+|f24|imposta|imposte|iva|irpef|ires|irap|"
    r"ritenut\w+|licenziament\w+|dimission\w+|recess\w+|preavviso|diffid\w+|"
    r"prescrizion\w+|decadenz\w+|ricorso|impugnazion\w+|termine di legge|per legge|"
    r"normativ\w+|decreto|obblig\w+|sanzion\w+|multa|ammenda|forfettari\w+|"
    r"registrazion\w+|protocoll\w+|raccomandat\w+|\bpec\b|camera di commercio|"
    r"registro imprese|\bdurc\b|libro unico|cedolino|buste? paga|\btfr\b|"
    r"ferie|permessi rol|apprendistat\w+|cassa integrazione|naspi|congedo)\b",
    re.I,
)

# ── Espressioni di SCADENZA/TERMINE con numero preciso ────────────────────────────────────
# Tre forme: 'entro [le/il] N [unità] [coda]'; 'termine di N unità'; 'N unità dalla/prima/
# successivi…'. La coda (lavorativi, dalla data, del giorno antecedente…) è catturata PER
# INTERO fino alla punteggiatura, così la sostituzione resta grammaticale.
_UNIT = r"(?:giorn[oi]|giornat[ae]|ore|mes[ei]|settiman[ae]|ann[oi])"
# Numeri anche A LETTERE (il modello scrive 'entro otto giorni', non solo '8'): li copriamo.
_NUMWORD = (r"(?:uno|una|un|due|tre|quattro|cinque|sei|sette|otto|nove|dieci|undici|dodici|"
            r"tredici|quattordici|quindici|sedici|diciassette|diciotto|diciannove|venti|"
            r"trenta|quaranta|cinquanta|sessanta|settanta|ottanta|novanta|cento)")
_NUM = r"(?:\d+|" + _NUMWORD + r")"
_TAILKW = (r"(?:lavorativ\w+|solari?|calendari\w+|di calendario|antecedent\w+|precedent\w+|"
           r"success\w+|effettiv\w+|dall['’a]|dal|del|dello|della|dei|degli|delle|nel|nella|"
           r"prima|a partire)")
# coda catturata fino a punteggiatura O parentesi (così non scavalca '(in pratica…')
_CODA = r"[^.,;:!?\n()]{0,45}"
_TAIL = r"(?:\s+" + _TAILKW + r"\b" + _CODA + r")?"
_DEADLINE = re.compile(
    # ── 'entro [le/l'/il/il giorno] N [°] …' : dopo N serve un'unità OPPURE una coda ──
    r"\bentro\s+(?:le\s+|l['’]\s*|(?:ore|il|lo|la)\s+)?(?:giorno\s+)?" + _NUM + r"(?:\s*°)?"
    + r"(?:\s*" + _UNIT + _TAIL
    + r"|\s+" + _TAILKW + r"\b" + _CODA + r")"
    # ── 'termine (di/dei/del/è di) N unità' ──
    + r"|\btermine\s+(?:massimo\s+)?(?:di|dei|del|è\s+di)\s+" + _NUM + r"\s*" + _UNIT + r"\b"
    # ── 'N unità dalla/prima/successivi…' ──
    + r"|\b" + _NUM + r"\s*" + _UNIT + r"\s+" + _TAILKW + r"\b" + _CODA,
    re.I,
)

# ── Soglie / limiti / sanzioni di legge in euro (numero preciso) ───────────────────────────
# Solo quando il numero è introdotto da una parola-soglia: evita di toccare il fatturato che
# l'utente ha dichiarato ('fatturo 500k') o un prezzo di business. Si sostituisce SOLO la
# cifra (gruppo 'pre' conservato) per non perdere il contesto ('del regime forfettario').
# L'importo NON assorbe lo spazio finale (finisce su cifra) → niente 'normatival'anno'.
_THRESHOLD = re.compile(
    r"(?P<pre>\b(?:soglia|limite|tetto|plafond|massimale|franchigia|sanzion\w+|multa|ammenda)\b"
    r"[^.,;:!?\n]{0,40}?(?:di|da|fino a|pari a|è(?: di)?|:)\s*)"
    r"€?\s*\d[\d.]*(?:[.\s]\d{3})*(?:,\d+)?(?:\s*(?:mila|mln|milion\w+|k))?(?:\s*(?:€|euro|eur\b))?",
    re.I,
)

# ── Tassi/interessi/more/penali in % o "punti" (misura di legge citata a memoria) ─────────
# Es. 'tasso legale + 8 punti', 'interessi di mora del 10%'. SOLO in contesto interesse/mora/
# penale: NON tocca le aliquote fiscali (IVA 22%, ecc.), che restano. Sostituisce la misura.
# trigger UNIVOCAMENTE legali (no 'interessi' nudo: escluderebbe i tassi bancari di business)
_RATE = re.compile(
    r"(?P<pre>\b(?:tasso\s+legale|tasso\s+di\s+mora|"
    r"interess\w+\s+(?:di\s+mora|moratori\w+|legal\w+)|mora|penale)\b"
    r"[^.,;:!?\n]{0,20}?)"
    r"(?:\s*(?:\+|maggiorat\w+\s+di|aumentat\w+\s+di|del|della|pari\s+al|al|di))?\s*"
    r"\d+(?:[.,]\d+)?\s*(?:punt\w+(?:\s+percentual\w+)?|%|per\s*cento)",
    re.I,
)

_VERIFY = " (verifica la scadenza/soglia esatta sulla fonte ufficiale o nel report)"


def _enabled() -> bool:
    return os.getenv("KBOT_DEADLINE_GUARD", "1") != "0"


def _soften_deadline(m: "re.Match") -> str:
    low = m.group(0).lower()
    if low.startswith("entro"):
        return "entro il termine previsto dalla normativa"
    if low.startswith("termine"):
        return "termine preciso previsto dalla normativa"  # NB: senza articolo (lo precede già)
    return "nel termine previsto dalla normativa"


def _soften_threshold(m: "re.Match") -> str:
    # conserva 'pre' (parola-soglia + eventuale contesto), sostituisce solo la cifra
    return m.group("pre") + "un importo previsto dalla normativa"


def _soften_rate(m: "re.Match") -> str:
    # conserva il contesto ('tasso legale', 'interessi di mora'), toglie la misura numerica
    return m.group("pre").rstrip() + " nella misura prevista dalla normativa"


def sanitize(text: str) -> str:
    """Rende descrittive scadenze/termini/soglie di legge quando il testo è in contesto
    normativo. Fuori da quel contesto (business), non tocca nulla. Idempotente e senza
    latenza di rete: è tutto locale e deterministico."""
    if not text or not _enabled():
        return text
    has_ctx = bool(_LEGAL_CTX.search(text))       # gate per scadenze/soglie (forme ambigue)
    has_rate = bool(_RATE.search(text))            # tassi/more/penali: già di per sé legali
    if not has_rate and not (has_ctx and (_DEADLINE.search(text) or _THRESHOLD.search(text))):
        return text  # niente da fare → numeri di business intatti

    out = text
    if has_ctx:
        out = _DEADLINE.sub(_soften_deadline, out)     # 'entro 3 giorni' va disambiguato dal contesto
        out = _THRESHOLD.sub(_soften_threshold, out)
    out = _RATE.sub(_soften_rate, out)                 # 'tasso legale + 8 punti' è auto-contestualizzato
    # de-duplica le ripetizioni della stessa frase soft-ata (dalla 2ª in poi → variante leggera)
    _seen = {"n": 0}
    def _dedup(mm: "re.Match") -> str:
        _seen["n"] += 1
        return mm.group(0) if _seen["n"] == 1 else "nei termini di legge"
    out = re.sub(r"entro il termine previsto dalla normativa", _dedup, out, flags=re.I)
    # pulizia leggera: la sostituzione può incollare la frase a una '(' o lasciare doppi spazi
    out = out.replace("normativa(", "normativa (")
    out = re.sub(r"[ \t]{2,}", " ", out).replace(" )", ")").replace("( ", "(")
    if out != text and "verific" not in out.lower():
        out = out.rstrip()
        out = (out[:-1] if out.endswith(".") else out) + _VERIFY + "."
    return out
