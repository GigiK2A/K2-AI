"""Instradamento delle skill PER TEMA (app/data/skill_temi.json).

Il problema (misurato il 20/10/2026): l'instradamento storico passa da 20 «pillar» del vecchio prodotto di soluzioni AI
(agenti email, RAG, ERP…). Per le domande di un pre-consulente non funziona: «posso installare telecamere?», «devo
rinnovare il DVR?», «ho ricevuto un avviso di accertamento», «voglio cedere le quote» → NESSUN pillar, quindi solo la
skill di metodo; «come funziona il periodo di prova?» → recruiting-pipeline, interview-prep, onboarding; «un cliente
non mi paga» → contabilità e budget forecast. Le skill giuste esistono (diritto-italiano, fiscale-tributario-italiano,
sicurezza-lavoro, diritto-societario-italiano, analisi-bilancio-pmi…) ma non venivano caricate.

Qui: i temi si riconoscono dai messaggi dell'utente (gli ultimi tre, i più recenti pesano di più), si prendono al
massimo due temi e quattro skill. KBOT_SKILL_TEMI=0 spegne e torna all'instradamento storico.
"""
from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import List

log = logging.getLogger(__name__)

_PERCORSO = Path(__file__).resolve().parent.parent / "data" / "skill_temi.json"
MAX_TEMI = 2
MAX_SKILL = 4


@lru_cache(maxsize=1)
def _temi() -> list:
    try:
        voci = json.load(open(_PERCORSO, encoding="utf-8")).get("temi", [])
        return [{"id": v["id"], "trigger": [re.compile(t, re.I) for t in v["trigger"]], "skill": list(v["skill"])}
                for v in voci if v.get("trigger") and v.get("skill")]
    except Exception:
        log.warning("skill_router: mappa dei temi non leggibile", exc_info=True)
        return []


def punteggi(messaggi_utente: List[str]) -> dict:
    """{tema: punteggio} sugli ultimi tre messaggi dell'utente (peso 3 per l'ultimo, 2 il penultimo, 1 l'altro)."""
    recenti = [m for m in (messaggi_utente or []) if isinstance(m, str)][-3:]
    pesi = [1, 2, 3][-len(recenti):] if recenti else []
    out: dict = {}
    for t in _temi():
        p = 0
        for testo, peso in zip(recenti, pesi):
            p += peso * sum(1 for rx in t["trigger"] if rx.search(testo))
        if p:
            out[t["id"]] = p
    return out


def skill_per_tema(messaggi_utente: List[str]) -> List[str]:
    """Le skill dei temi riconosciuti (ordinate per punteggio), senza doppioni, al massimo MAX_SKILL. [] se nessun tema."""
    if os.getenv("KBOT_SKILL_TEMI", "1") == "0":
        return []
    pt = punteggi(messaggi_utente)
    if not pt:
        return []
    per_id = {t["id"]: t for t in _temi()}
    skills: List[str] = []
    for tid, _ in sorted(pt.items(), key=lambda kv: -kv[1])[:MAX_TEMI]:
        for s in per_id[tid]["skill"]:
            if s not in skills:
                skills.append(s)
    return skills[:MAX_SKILL]
