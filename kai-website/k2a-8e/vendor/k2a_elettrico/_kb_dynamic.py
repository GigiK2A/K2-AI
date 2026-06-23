"""Recupero dinamico verbatim dalla KB norme-tecniche (Tappa 2 Fase 2).

Sostituisce, su opt-in (`dynamic_kb=True`), lo snapshot statico di `_kb_mapping.py`
con un recupero on-demand. Vantaggio: gli aggiornamenti della KB si propagano senza
ricompilare lo snapshot.

Strategia: import diretto del package `k2a_norme_tecniche` e uso del tool
`get_paragrafo(documento, paragrafo)` — l'API autoritativa della KB. NON query SQL
grezze (lo schema reale non ha colonne `norma`/`testo`: la norma è `documenti.codice`,
il testo è `chunks.contenuto`, e il DB è risolto dal package stesso).

Mappatura necessaria: i nomi-norma usati nei tool ("CEI 64-8:2024") non coincidono
con il `codice` del documento in KB ("CEI_64_8"). NORMA_TO_CODICE colma il divario.

Backward compat: se la KB non è importabile/disponibile, il chiamante resta sullo
snapshot statico (graceful degradation). Cache LRU in-memory per sessione.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

# Sorgente del package norme-tecniche (sibling repo). Override via env.
_DEFAULT_NORME_SRC = "/Users/lucarossi/Code/k2a-mcp/k2a-mcp-norme-tecniche/src"
NORME_SRC = os.environ.get("K2A_NORME_SRC", _DEFAULT_NORME_SRC)

# Nome-norma (come citato dai tool / _kb_mapping) -> codice documento in KB.
NORMA_TO_CODICE: dict[str, str] = {
    "CEI 0-21:2025-04": "CEI_0_21",
    "CEI 0-16:2025-04": "CEI_0_16",
    "CEI 64-8:2024": "CEI_64_8",
    "CEI-UNEL 35024/1:1997-06": "CEI_UNEL_35024_1",
    "CEI EN 62305-2:2013": "CEI_EN_62305_2",
    "IEC 61439-1:2020": "IEC_61439_1",
    "NTC 2018": "NTC2018",
    "Circolare 7/2019": "CIRC2019_NTC",
}


def _ensure_path() -> None:
    if NORME_SRC not in sys.path:
        sys.path.insert(0, NORME_SRC)


def is_kb_available() -> bool:
    """True se il package norme-tecniche è importabile e il DB esiste."""
    _ensure_path()
    try:
        from k2a_norme_tecniche.db import DB_PATH  # type: ignore
    except Exception:  # noqa: BLE001
        return False
    return Path(DB_PATH).exists()


@lru_cache(maxsize=512)
def recupera_verbatim_dinamico(norma: str, paragrafo: str,
                               max_chars: int = 500) -> str | None:
    """Recupera il verbatim di (norma, paragrafo) dalla KB on-demand.

    Ritorna il testo (troncato a max_chars) oppure None se non recuperabile
    (norma non mappata, KB non disponibile, paragrafo inesistente). Cache LRU.
    """
    codice = NORMA_TO_CODICE.get(norma)
    if codice is None:
        return None
    _ensure_path()
    try:
        from k2a_norme_tecniche.schemas import GetParagrafoInput  # type: ignore
        from k2a_norme_tecniche.tools import get_paragrafo  # type: ignore
    except Exception:  # noqa: BLE001 — KB non disponibile
        return None
    try:
        out = get_paragrafo(GetParagrafoInput(documento=codice, paragrafo=paragrafo))
    except Exception:  # noqa: BLE001 — errore runtime KB
        return None
    if not getattr(out, "trovato", False):
        return None
    testo = out.contenuto
    if not testo:
        return None
    testo = " ".join(testo.split())  # normalizza whitespace
    if len(testo) > max_chars:
        testo = testo[: max_chars - 3].rstrip() + "..."
    return testo


def clear_cache() -> None:
    """Invalida la cache (es. dopo aggiornamento KB nella stessa sessione)."""
    recupera_verbatim_dinamico.cache_clear()
