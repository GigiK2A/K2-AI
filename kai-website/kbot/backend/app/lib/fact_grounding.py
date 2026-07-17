"""Grounding FORZATO sui numeri fattuali (17 lug — risposta a Luca: «essendoci mcp non
dovrebbe esserci questo errore»).

Il problema: gpt-oss locale, sulle domande di NUMERO specifico (scadenze, aliquote, soglie,
durate, termini), risponde a MEMORIA e inventa valori plausibili-ma-sbagliati ('comunicazione
assunzione entro 10 giorni' — è il giorno prima). Il web_search ESISTE ma è discrezionale: il
modello non lo chiama perché 'crede' di sapere. Il corpus normattiva verifica gli ARTICOLI,
non le scadenze.

Soluzione: quando la domanda dell'utente chiede un numero fattuale, il SERVER esegue una
ricerca web (OpenAI, la stessa già usata) PRIMA del turno e inietta i risultati nel prompt
come DATI VERIFICATI — il modello risponde ancorato alla fonte, non alla memoria. Trigger
deterministico (pattern-based), esecuzione best-effort e fail-open (se la ricerca non va, si
prosegue col linguaggio prudente del prompt). KBOT_FACT_GROUNDING=0 disattiva.
"""
from __future__ import annotations

import logging
import os
import re

from . import web_search

log = logging.getLogger(__name__)

# Interrogativi che chiedono un NUMERO/TERMINE con una risposta di fatto (legale/fiscale/HR):
# scadenze, durate, aliquote, soglie, termini. NON i giudizi soggettivi ('quanto dovrei
# spendere in marketing') — quelli non hanno un numero 'giusto' da verificare.
_TRIGGER = re.compile(
    r"\b("
    r"entro\s+quant\w+|entro\s+quando|"
    r"quant[ie]\s+(?:giorni|ore|mesi|settimane|anni)|"
    r"quanto\s+(?:dura|tempo|deve durare)|"
    r"qual[e']?\s+è\s+(?:l'|la\s+|il\s+)?(?:aliquota|soglia|limite|termine|scadenza|durata|percentuale|imposta|tasso)|"
    r"che\s+(?:aliquota|soglia|percentuale|termine)|"
    r"quando\s+(?:scade|devo\s+(?:versare|pagare|comunicare|presentare|inviare))|"
    r"(?:soglia|limite|tetto)\s+(?:di\s+)?(?:ricavi|fatturato|reddito)|"
    r"aliquota\s+iva|scadenz\w+\s+(?:iva|f24|imu|tari|inps|contribut)"
    r")\b", re.I)

# Il tema deve essere NORMATIVO/FISCALE/CONTRATTUALE (dove un numero sbagliato fa danno):
# se la domanda non tocca questi ambiti la ricerca non serve (es. 'quanti clienti ho perso').
_DOMAIN = re.compile(
    r"\b(iva|imposta|tass\w+|fiscal\w+|f24|imu|tari|inps|contribut\w+|forfettari\w+|"
    r"ccnl|preavviso|licenzi\w+|assunzion\w+|dimission\w+|ferie|malattia|prova|apprendist\w+|"
    r"contratto|scadenz\w+|dichiarazion\w+|versament\w+|bilancio|deposit\w+|"
    r"registrazion\w+|termin\w+|sanzion\w+|multa|verbal\w+|adempiment\w+|comunicazion\w+)\b",
    re.I)


def _enabled() -> bool:
    return os.getenv("KBOT_FACT_GROUNDING", "1") != "0" and web_search.enabled()


def needs_grounding(user_text: str) -> bool:
    t = user_text or ""
    return bool(_TRIGGER.search(t)) and bool(_DOMAIN.search(t))


def _query(user_text: str) -> str:
    # ancora la ricerca all'ordinamento italiano e all'anno corrente (le scadenze cambiano)
    return f"{user_text.strip()[:220]} normativa italiana aggiornata"


def ground_block(user_text: str) -> str | None:
    """Blocco di grounding da iniettare nel prompt, o None se non serve / ricerca non
    disponibile. best-effort: qualunque errore → None (fail-open, prosegue col prompt)."""
    if not _enabled() or not needs_grounding(user_text):
        return None
    try:
        res = web_search.run_openai_search(_query(user_text))
    except Exception:
        log.warning("fact_grounding: ricerca fallita (fail-open)", exc_info=True)
        return None
    if not res or res.startswith("[ricerca web"):
        return None  # nessun risultato utile → il prompt prudente gestisce da solo
    return (
        "\nDATI VERIFICATI DA RICERCA WEB (aggiornati) — la domanda dell'utente chiede un "
        "numero/termine specifico: basa la risposta su QUESTI risultati, NON sulla tua "
        "memoria. Cita il valore solo se è QUI; se questi risultati non contengono il dato "
        "preciso, dillo e rimanda alla fonte ufficiale, senza indovinare un numero.\n"
        "<<<RISULTATI RICERCA>>>\n" + res[:2500] + "\n<<<FINE RISULTATI>>>\n"
    )
