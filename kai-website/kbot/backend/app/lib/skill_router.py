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
        return [{"id": v["id"], "trigger": [re.compile(t, re.I) for t in v["trigger"]],
                 "debole": [re.compile(t, re.I) for t in v.get("debole", [])], "skill": list(v["skill"])}
                for v in voci if v.get("trigger") and v.get("skill")]
    except Exception:
        log.warning("skill_router: mappa dei temi non leggibile", exc_info=True)
        return []


SOGLIA_DEBOLI = 3     # parole ambigue (dipendenti, fattura, progetto…): da sole non accendono un tema, ne servono tre diverse


def punteggi(messaggi_utente: List[str]) -> dict:
    """{tema: punteggio} sugli ultimi tre messaggi dell'utente (peso 3 per l'ultimo, 2 il penultimo, 1 l'altro).
    Un tema si accende con almeno una parola FORTE, oppure con SOGLIA_DEBOLI parole deboli diverse."""
    recenti = [m for m in (messaggi_utente or []) if isinstance(m, str)][-3:]
    pesi = [1, 2, 3][-len(recenti):] if recenti else []
    out: dict = {}
    for t in _temi():
        forti_distinte = {i for i, rx in enumerate(t["trigger"]) if any(rx.search(m) for m in recenti)}
        deboli_distinte = {i for i, rx in enumerate(t["debole"]) if any(rx.search(m) for m in recenti)}
        if not forti_distinte and len(deboli_distinte) < SOGLIA_DEBOLI:
            continue
        p = 0
        for testo, peso in zip(recenti, pesi):
            p += peso * (2 * sum(1 for rx in t["trigger"] if rx.search(testo))
                         + sum(1 for rx in t["debole"] if rx.search(testo)))
        if p:
            out[t["id"]] = p
    return out


def skill_per_tema(messaggi_utente: List[str], temi_modello: List[str] | None = None) -> List[str]:
    """Le skill dei temi riconosciuti (ordinate per punteggio), senza doppioni, al massimo MAX_SKILL. [] se nessun tema.
    `temi_modello`: i temi scelti dal modello (temi_con_modello) quando le parole non ne hanno trovato nessuno."""
    if os.getenv("KBOT_SKILL_TEMI", "1") == "0":
        return []
    pt = punteggi(messaggi_utente)
    if not pt and temi_modello:
        validi = {t["id"] for t in _temi()}
        pt = {tid: 1 for tid in temi_modello if tid in validi}
    if not pt:
        return []
    per_id = {t["id"]: t for t in _temi()}
    skills: List[str] = []
    for tid, _ in sorted(pt.items(), key=lambda kv: -kv[1])[:MAX_TEMI]:
        for s in per_id[tid]["skill"]:
            if s not in skills:
                skills.append(s)
    return skills[:MAX_SKILL]


# --- Secondo livello: il modello sceglie il tema quando le parole non ne trovano nessuno -------------------------
# Misura (20/10/2026, 40 domande scritte da un agente che non aveva visto l'elenco, lessico colloquiale): le sole
# parole coprono 21/40 («scaricare dalle tasse», «cacciare», «spalmarlo»). Una chiamata breve (≈30 token in uscita,
# temperatura 0) parte SOLO quando le parole non trovano nulla; KBOT_SKILL_TEMI_LLM=0 la spegne.
_SISTEMA_TEMI = (
    "Classifica la domanda di un titolare o dipendente di una PMI italiana in uno o due TEMI, o in nessuno.\n"
    "TEMI:\n{elenco}\n"
    "Scegli un tema solo se la domanda riguarda DAVVERO quella materia (norme, obblighi, diritti, tasse, "
    "contratti). Problemi informatici, organizzazione del lavoro, scrittura di testi, marketing, curiosità e "
    "parole usate in senso non giuridico («fattura» di un servizio web, «contratto» di un calciatore) → nessun tema.\n"
    'Rispondi SOLO con JSON: {{"temi": ["id", ...]}} oppure {{"temi": []}}.'
)


def llm_attivo() -> bool:
    return os.getenv("KBOT_SKILL_TEMI_LLM", "1") != "0" and os.getenv("KBOT_SKILL_TEMI", "1") != "0"


def temi_con_modello(client, modello: str, messaggio: str, timeout: float = 8.0) -> List[str]:
    """Id dei temi (al massimo MAX_TEMI) che il modello riconosce nel messaggio; [] se nessuno o su qualunque errore."""
    from .norme_evidence import _json_tollerante
    try:
        voci = json.load(open(_PERCORSO, encoding="utf-8")).get("temi", [])
        elenco = "\n".join(f"- {v['id']}: {v.get('descrizione', '')}" for v in voci)
        base = dict(model=modello, max_tokens=60, system=_SISTEMA_TEMI.format(elenco=elenco),
                    messages=[{"role": "user", "content": (messaggio or "").strip()[:1500]}], timeout=timeout)
        try:
            r = client.messages.create(**base, extra_body={"temperature": 0})
        except Exception as e:
            if isinstance(e, TypeError) or getattr(e, "status_code", None) in (400, 422):
                r = client.messages.create(**base)
            else:
                raise
        testo = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        validi = {v["id"] for v in voci}
        scelti = [t for t in ((_json_tollerante(testo) or {}).get("temi") or []) if isinstance(t, str) and t in validi]
        return list(dict.fromkeys(scelti))[:MAX_TEMI]
    except Exception:
        log.warning("skill_router: classificazione col modello fallita (fail-open)", exc_info=True)
        return []
