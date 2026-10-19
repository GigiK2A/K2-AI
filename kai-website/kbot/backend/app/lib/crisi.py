"""Messaggi di CRISI PERSONALE: risposta FISSA e verificata, mai generata dal modello.

Il problema (misurato il 19/10/2026): a «a volte penso di farla finita» il modello ha risposto con empatia ma
ha INVENTATO un numero verde («Numero Verde Anticidio 800 808 109»: nessuna fonte lo conferma). A una persona in
crisi un numero falso è peggio di nessun numero. Qui:

  * `rileva(testo)`: riconosce i messaggi di ideazione suicidaria (espressioni dirette, non l'idioma
    «farla finita con questo fornitore») e il turno viene chiuso con RISPOSTA_FISSA, senza chiamare il modello;
  * `sanifica_numeri(testo, testo_utente)`: rete di sicurezza su OGNI risposta: un numero verde (800/803) scritto
    dal modello che non compare nel testo dell'utente viene tolto (non si conosce la fonte).

NUMERI VERIFICATI (ricerca web del 19/10/2026, pagine di risorse di aiuto e comunicati di Telefono Amico):
  112              numero unico di emergenza
  02 2327 2327     Telefono Amico Italia (gli orari sono cambiati nel 2024 e nel 2026: si rimanda al sito)
Non si aggiunge nessun altro numero senza averlo verificato su una fonte ufficiale.

KBOT_CRISI=0 disattiva (solo per prove).
"""
from __future__ import annotations

import os
import re

_FRASI = re.compile(
    r"\bfarla\s+finita\b(?!\s+(?:con|di|coi|col|cogli|colla|con\s+i|con\s+le)\b)"      # «farla finita con X» è un idioma
    r"|\b(?:togliermi|togliere|toglierci)\s+la\s+vita\b"
    r"|\b(?:uccidermi|ammazzarmi|spararmi|impiccarmi|suicidarmi|annegarmi)\b"
    r"|\bmi\s+(?:voglio|vorrei|devo|sto per)\s+(?:uccidere|ammazzare)\b"
    r"|\b(?:pensieri|idee|intenzioni)\s+(?:di\s+)?suicid\w*"
    r"|\b(?:penso|pensato|pensando|voglio|vorrei|tentare|tentato|tenterò|ho\s+deciso\s+di)\b[^.!?\n]{0,40}\bsuicid\w*"
    r"|\b(?:voglio|vorrei|preferirei|meglio)\s+(?:morire|essere\s+morto|essere\s+morta|sparire\s+per\s+sempre)\b"
    r"|\bnon\s+voglio\s+più\s+vivere\b|\bnon\s+ha\s+più\s+senso\s+vivere\b|\bnon\s+vale\s+più\s+la\s+pena\s+(?:di\s+)?vivere\b"
    r"|\bnon\s+ce\s+la\s+faccio\s+più\s+a\s+vivere\b|\bfarmi\s+del\s+male\b",
    re.I)

RISPOSTA_FISSA = (
    "Mi dispiace molto che tu stia vivendo un momento così pesante. Quello che hai scritto è importante e viene "
    "prima di qualsiasi questione di lavoro o di soldi.\n\n"
    "Se in questo momento sei in pericolo o temi di poterti fare del male, chiama subito il 112 (numero unico di "
    "emergenza) oppure vai al pronto soccorso più vicino.\n\n"
    "Se hai bisogno di parlare con qualcuno adesso, puoi chiamare Telefono Amico Italia al 02 2327 2327 "
    "(controlla gli orari su telefonoamico.it). Puoi anche parlarne con una persona di cui ti fidi o con il tuo "
    "medico di base.\n\n"
    "Non devi affrontare tutto da solo e non devi decidere nulla stasera: per i debiti e per i problemi "
    "dell'azienda esistono strumenti legali e professionisti che possono aiutarti, e ne parliamo quando vorrai, "
    "con calma, un passo alla volta.\n\n"
    "Se ti va, dimmi come stai in questo momento."
)

_NUMERO_VERDE = re.compile(r"(?<![\d.])(?:800|803)[\s.\-]?\d{3}[\s.\-]?\d{3}(?!\d)")


def _attivo() -> bool:
    return os.getenv("KBOT_CRISI", "1") != "0"


def rileva(testo: str) -> bool:
    """True se il messaggio dell'utente esprime ideazione suicidaria. Predilige il richiamo: un falso positivo
    costa un messaggio gentile in più, un falso negativo costa molto di più."""
    return bool(testo) and _attivo() and bool(_FRASI.search(testo))


def sanifica_numeri(testo: str, testo_utente: str = "") -> str:
    """Toglie i numeri verdi (800/803) scritti dal modello che l'utente non ha scritto: fonte sconosciuta."""
    if not testo:
        return testo
    cifre_utente = re.sub(r"\D", "", testo_utente or "")

    def _sost(m: "re.Match") -> str:
        if re.sub(r"\D", "", m.group(0)) in cifre_utente:
            return m.group(0)
        return "[numero da verificare sul sito ufficiale]"
    return _NUMERO_VERDE.sub(_sost, testo)
