"""Calcoli economici del K-BOT (assunzioni, investimenti, margini): regole nel prompt solo quando serve + controllo dell'aritmetica scritta.

Test B del 10/11/2026: per due assunzioni da 1.700 € netti il modello ha calcolato il netto annuo su 12 mensilità senza dirlo, ha introdotto un
costo aziendale di 55.000 € e un margine di contribuzione del 35% come se fossero dati e solo dopo li ha ritirati come «ipotetici». Non si
costruisce un motore fiscale (netto→costo azienda dipende da livello, CCNL, contributi, INAIL, TFR): si impone il metodo e si verifica
in codice l'aritmetica dei passaggi scritti («a × b = c»). KBOT_CALCOLI=0 spegne.
"""
from __future__ import annotations

import os
import re
from typing import Optional

_ECONOMICA = re.compile(
    r"\bassun\w+|\bcosto\s+(?:del\s+personale|azienda\w*|aziendale|di\s+un\s+dipendente|per\s+l.azienda)|\bnett[oi]\b|\blord[oi]\b|\bRAL\b|"
    r"\binvest\w+|\bmargin\w+|\bbreak.?even\b|\bpayback\b|\bROI\b|\bsostenibil\w+\s+economic\w+|\bfatturato\b.{0,80}\b(?:assun|invest)|"
    r"\bquanto\s+(?:devo|dovrei|devono)\s+(?:incassare|fatturare|vendere)\b|\bpunto\s+di\s+pareggio\b|\bricavi\b.{0,60}\bcost[io]\b", re.I)

BLOCCO = (
    "\nCALCOLI ECONOMICI (assunzioni, investimenti, margini, sostenibilità): il metodo conta più del numero.\n"
    "1) PRIMA dei numeri scrivi le IPOTESI: mensilità (12, 13 o 14), se la cifra dell'utente è netto, lordo o costo azienda, ruolo, livello o CCNL, "
    "periodo. Un «1.700 € netti al mese» è un NETTO: dillo subito, e dì che il costo per l'azienda è più alto e dipende da contributi, INAIL, "
    "TFR, ferie e malattia: non stimarlo con percentuali tue.\n"
    "2) Mai importi o percentuali standard (costo azienda, margine, tassi) presentati come dati. O li chiedi, o li usi come SCENARI chiaramente "
    "etichettati «ipotesi», con un intervallo, dopo aver detto quali dati reali li sostituirebbero. Non confezionare un risultato preciso "
    "da ipotesi: se un valore non lo conosci, il risultato è un ordine di grandezza e lo dici.\n"
    "3) Mostra il conto passo per passo con i numeri dell'utente e ricontrolla l'aritmetica prima di scriverla.\n"
    "4) Distingui ricavi, margine di contribuzione e utile; il recupero dell'investimento (payback) dal ritorno; ciò che entra una tantum "
    "da ciò che è ricorrente.\n"
    "5) Chiudi con i 3-4 dati che servono per affinare il calcolo (es. livello e CCNL, costo azienda dal consulente del lavoro, margine "
    "reale per prodotto) e chi può fornirli. Una risposta chiara e corta vale più di tre scenari.\n"
)


_IDEA = re.compile(
    r"\b(?:idea|progetto|piattaforma|prodotto|servizio|startup)\b[^\n]{0,300}\b(?:invest\w+|lancia\w*|svilupp\w+|vender\w+|abbonament\w+)|"
    r"\b(?:invest\w+|svilupp\w+)\b[^\n]{0,300}\b(?:idea|piattaforma|prodotto|abbonament\w+)|\bvalidar\w+\b[^\n]{0,80}\b(?:idea|mercato|prodotto)\b|"
    r"\bbusiness\s+(?:plan|concreto)\b|\bmercato\s+enorme\b", re.I)

BLOCCO_IDEA = (
    "\nVALIDAZIONE DI UN'IDEA O DI UN INVESTIMENTO NUOVO: non dare il verdetto sull'investimento prima di aver messo alla prova l'idea. "
    "Proponi un PIANO DI VALIDAZIONE a basso costo (poche conversazioni o un'offerta di prova prima di sviluppare), con per ognuna "
    "METRICA, SOGLIA e DECISIONE («se almeno X dei Y interpellati… vai avanti, altrimenti ferma o cambia»); le soglie sono proposte da "
    "discutere, non dati. Con le cifre dell'utente separa ricavo ricorrente, margine, costo di acquisizione di un cliente, abbandoni e "
    "recupero dell'investimento; i numeri che non ha dato sono IPOTESI etichettate e richieste (canale di vendita, tasso di chiusura, "
    "costi di gestione). Metti in discussione le ipotesi dell'imprenditore e, se esiste, un posizionamento più prudente (es. un assistente "
    "che prepara l'utente al professionista invece di sostituirlo) con i suoi limiti. Resta breve: priorità e prossimo passo concreto.\n"
)


def serve(testo: str) -> bool:
    return os.getenv("KBOT_CALCOLI", "1") != "0" and bool(_ECONOMICA.search(testo or ""))


def blocco(messaggi_utente: list[str]) -> str:
    """BLOCCO se l'ultimo messaggio dell'utente (o i due precedenti) parla di calcoli economici; BLOCCO_IDEA se propone un'idea da validare."""
    if os.getenv("KBOT_CALCOLI", "1") == "0":
        return ""
    recenti = (messaggi_utente or [])[-2:]
    out = BLOCCO if any(serve(m) for m in recenti) else ""
    if any(_IDEA.search(m or "") for m in recenti):
        out += BLOCCO_IDEA
    return out


# ── controllo dell'aritmetica scritta: «a × b (× c) = d» ──────────────────────────────────────────────────
_N = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"
_PROD = re.compile(rf"(?<![\d.,])({_N})\s*(?:€|euro)?\s*[×x*]\s*({_N})(?:\s*(?:€|euro)?\s*[×x*]\s*({_N}))?\s*(?:€|euro)?\s*=\s*(?:circa\s+)?({_N})(?![\d,]|\.\d)", re.I)


def _v(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 0.005:
        return f"{int(round(x)):,}".replace(",", ".")
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def nota_aritmetica(testo: str) -> str:
    """'' se i prodotti scritti tornano; altrimenti una nota breve con il valore giusto (non riscrive la risposta)."""
    if os.getenv("KBOT_CALCOLI", "1") == "0":
        return ""
    errori = []
    for m in _PROD.finditer(testo or ""):
        a, b, c, scritto = m.group(1), m.group(2), m.group(3), m.group(4)
        giusto = _v(a) * _v(b) * (_v(c) if c else 1.0)
        if abs(giusto - _v(scritto)) > max(0.5, abs(giusto) * 0.005):
            espressione = " × ".join(x for x in (a, b, c) if x)
            errori.append(f"{espressione} = {_fmt(giusto)} (nel testo: {scritto})")
    if not errori:
        return ""
    return "\n\nControllo dei calcoli: " + "; ".join(errori[:3]) + ". Fai riferimento ai valori corretti."


# ── cifre calcolate dal codice ────────────────────────────────────────────────────────────────────────────
_NUM_P = {"un": 1, "una": 1, "uno": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7, "otto": 8, "nove": 9, "dieci": 10}
_PERSONE = re.compile(r"\b(un|una|due|tre|quattro|cinque|sei|sette|otto|nove|dieci|\d{1,3})\s+(?:altr[ei]\s+)?(?:person\w+|dipendent\w+|collaborator\w+|risors\w+)", re.I)
_NETTO = re.compile(rf"(?:netto|netti)\s+(?:di\s+)?(?:circa\s+)?({_N})\s*(?:€|euro)|({_N})\s*(?:€|euro)\s+netti", re.I)
_PREZZO_MESE = re.compile(rf"({_N})\s*(?:€|euro)\s*(?:al\s+mese|/\s*mese|mensil\w+)", re.I)
_CLIENTI = re.compile(rf"({_N})\s+(?:aziende|clienti|imprese|abbonati|utenti|pmi)\b", re.I)
_INVEST = re.compile(rf"invest\w+\s+(?:circa\s+|almeno\s+|oltre\s+)?({_N})\s*(?:€|euro)", re.I)


def fatti_calcolati(messaggi_utente: list[str]) -> str:
    """Cifre DERIVATE dai numeri dell'utente e calcolate qui, così il modello le usa invece di rifarle a mente (collaudo del 10/11/2026: per
    1.000 clienti × 99 €/mese scriveva 118.800 € o 990.000 € invece di 1.188.000 €). Solo aritmetica; il costo azienda non si deduce dal netto."""
    if os.getenv("KBOT_CALCOLI", "1") == "0":
        return ""
    testo = "\n".join((messaggi_utente or [])[-2:])
    righe = []
    pers, nett = _PERSONE.search(testo), _NETTO.search(testo)
    if pers and nett:
        n = _NUM_P.get(pers.group(1).lower()) or int(pers.group(1))
        netto = _v(nett.group(1) or nett.group(2))
        righe.append(f"Netto annuo per {n} persone con {_fmt(netto)} € netti al mese ciascuna: {_fmt(netto * 12 * n)} € su 12 mensilità, "
                     f"{_fmt(netto * 13 * n)} € su 13, {_fmt(netto * 14 * n)} € su 14. È un NETTO: il COSTO per l'azienda è maggiore e dipende da "
                     "livello, CCNL, contributi, INAIL, TFR: NON si calcola dal netto con una percentuale tua; chiedilo al consulente del lavoro.")
    prezzo, clienti = _PREZZO_MESE.search(testo), _CLIENTI.search(testo)
    if prezzo and clienti:
        p, c = _v(prezzo.group(1)), _v(clienti.group(1))
        arr = p * c * 12
        riga = (f"{_fmt(c)} clienti × {_fmt(p)} €/mese × 12 = {_fmt(arr)} € di ricavo annuo RICORRENTE a regime (lordo, prima di costi, IVA e abbandoni); "
                f"non è il ricavo del primo anno, che dipende dal ritmo di acquisizione (se i clienti arrivassero in modo uniforme durante l'anno, "
                f"circa metà: ipotesi).")
        inv = _INVEST.search(testo)
        if inv:
            i = _v(inv.group(1))
            riga += (f" Con un investimento di {_fmt(i)} €, il recupero richiede almeno {_fmt(i / (arr / 12))} mesi di RICAVI a regime; con un margine "
                     "di contribuzione m (dato da ottenere: non assumerlo) i mesi diventano investimento ÷ (ricavo mensile × m).")
        righe.append(riga)
    if not righe:
        return ""
    return ("\nCALCOLI VERIFICATI DAL SISTEMA (aritmetica sui numeri dell'utente: usa queste cifre, non rifare i conti a mente):\n- "
            + "\n- ".join(righe) + "\n")
