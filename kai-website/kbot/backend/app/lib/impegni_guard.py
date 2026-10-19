"""Guardia sugli IMPEGNI che il bot non può prendere (rimborsi, risarcimenti).

Misurato il 19/10/2026: davanti a un utente arrabbiato che chiedeva i soldi indietro, il bot ha risposto con calma ma ha
aperto la porta: «ti dico cosa possiamo fare concretamente, incluso il rimborso se è il caso». K-BOT è un servizio
informativo: non può promettere, nemmeno condizionalmente, rimborsi o risarcimenti dell'azienda, né ammettere una
responsabilità. La frase che li promette viene sostituita da una neutra che indica dove segnalare il problema.

Prudente: solo forme in prima persona/promissorie. Un rimborso come argomento giuridico («hai diritto al rimborso dei
costi di recupero», «compreso il rimborso forfettario di 40 euro») non viene toccato. KBOT_IMPEGNI_GUARD=0 spegne.
"""
from __future__ import annotations

import os
import re

_PROMESSA = re.compile(
    r"\bincluso\s+il\s+rimbors\w+\s+se\s+(?:è|e'|e)\s+il\s+caso\b"
    r"|\b(?:ti|vi)\s+(?:rimborsi|rimborsiamo|rimborseremo|risarcisc\w+|risarciamo|risarciremo)\b"
    r"|\b(?:posso|possiamo|potremo|potrò)\s+(?:anche\s+)?(?:valutare\s+|offrire\s+)?(?:un\s+|il\s+)?(?:rimbors\w+|risarcimento)\b"
    r"|\b(?:posso|possiamo)\s+(?:rimborsarti|rimborsarvi|risarcirti|risarcirvi)\b"
    r"|\b(?:avrai|avrete)\s+(?:indietro|il\s+rimborso|un\s+rimborso)\b"
    r"|\bti\s+(?:garantisco|assicuro)\b[^.!?\n]{0,60}\b(?:rimbors|risarc|soldi|indietro)\w*"
    r"|\bci\s+faremo\s+carico\b|\bci\s+assumiamo\s+la\s+responsabilit\w+",
    re.I)

SOSTITUTA = ("Su rimborsi o risarcimenti non posso prendere impegni: per una segnalazione formale scrivi dalla pagina "
             "Contatti di k2-ai.it.")


def sanitize(testo: str) -> str:
    if not testo or os.getenv("KBOT_IMPEGNI_GUARD", "1") == "0" or not _PROMESSA.search(testo):
        return testo
    frasi = re.split(r"(?<=[.!?])\s+", testo)
    out, sostituita = [], False
    for f in frasi:
        if _PROMESSA.search(f):
            if not sostituita:
                out.append(SOSTITUTA)
                sostituita = True
            continue
        out.append(f)
    return " ".join(out)
