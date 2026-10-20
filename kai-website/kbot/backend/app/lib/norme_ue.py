"""Norme dell'Unione europea che il corpus Normattiva non contiene (test 08 del 20/10/2026: incidente GDPR).

Il corpus del pacchetto normativo è Normattiva, cioè solo diritto italiano: il Regolamento (UE) 2016/679 non c'è. Senza l'art. 33
il bot non aveva il termine di 72 ore e la guardia sulle scadenze (`deadline_guard`), che neutralizza ogni termine non presente
nel pacchetto, lo sostituiva con «nel termine previsto dalla normativa»: da qui «ha omesso il termine di 72 ore».

Qui i testi (data/norme_ue/*.txt) sono COPIATI dalla fonte ufficiale (Ufficio delle pubblicazioni dell'UE), mai scritti a mano; una
voce dell'indice entra nel pacchetto quando il messaggio dell'utente combacia con un trigger. KBOT_NORME_UE=0 spegne.
"""
from __future__ import annotations

import functools
import json
import logging
import os
import re
from pathlib import Path
from typing import List

log = logging.getLogger(__name__)

_DIR = Path(__file__).resolve().parent.parent / "data" / "norme_ue"


@functools.lru_cache(maxsize=1)
def _indice() -> list:
    try:
        voci = json.load(open(_DIR / "indice.json", encoding="utf-8")).get("voci", [])
        out = []
        for v in voci:
            if v.get("trigger") and v.get("fonti"):
                out.append({"id": v.get("id", ""), "trigger": [re.compile(t, re.I) for t in v["trigger"]], "fonti": v["fonti"],
                            "escludi": {(str(e["numero"]), int(e["anno"])) for e in v.get("escludi_proposte", [])}})
        return out
    except FileNotFoundError:
        return []
    except Exception:
        log.warning("norme_ue: indice non leggibile", exc_info=True)
        return []


def fonti_ue(testo: str, Fonte) -> List:
    """Le fonti UE pertinenti al messaggio (oggetti `Fonte` del pacchetto normativo), con il testo copiato dalla fonte ufficiale."""
    if os.getenv("KBOT_NORME_UE", "1") == "0" or not testo:
        return []
    out = []
    for voce in _indice():
        if not any(t.search(testo) for t in voce["trigger"]):
            continue
        for f in voce["fonti"]:
            try:
                corpo = (_DIR / f["file"]).read_text(encoding="utf-8").strip()
            except OSError:
                continue
            righe = [r for r in corpo.splitlines()]
            # la prima riga è «Articolo N» (già nel titolo della fonte) e la seconda è la rubrica: si tengono i commi
            corpo = "\n".join("  " + r for r in righe[2:] if r.strip()) if righe and righe[0].lower().startswith("articolo") and f["articolo"] != "4" else \
                    "\n".join("  " + r for r in righe[1:] if r.strip()) if f["articolo"] == "4" else "\n".join("  " + r for r in righe)
            out.append(Fonte(citazione=f["citazione"], tipo="regolamento_ue", anno=2016, numero="679", articolo=f["articolo"],
                             rubrica=f.get("rubrica", ""), sigla=f["sigla"], origine="norma", testo=corpo))
    return out


def escluse(testo: str) -> set:
    """Coppie (numero, anno) di norme italiane da NON proporre quando una voce UE si applica al messaggio (restano quelle citate
    dall'utente): evita articoli del Codice privacy sulla ricerca medica per un incidente di invio errato di un file."""
    if os.getenv("KBOT_NORME_UE", "1") == "0" or not testo:
        return set()
    out: set = set()
    for voce in _indice():
        if any(t.search(testo) for t in voce["trigger"]):
            out |= voce.get("escludi", set())
    return out
