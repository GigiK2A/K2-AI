"""Validazione cross-KB dei valori normativi (Tappa 2 Fase 2).

Confronta i valori numerici critici hardcoded nei tool (soglie, costanti,
rapporti convenzionali) con il testo verbatim presente nella KB norme-tecniche.

Obiettivo: rilevare *drift* tra implementazione e norma (es. se un tool usasse
1.50 dove la norma dice 1.45). È un controllo di convergenza, non un calcolo.

Strategia di ricerca: ricerca FTS sul **contenuto completo** dei chunk della norma
(non per `section_code`, che per CEI 64-8 è spesso assente nel chunking DOCX), poi
match regex del pattern del valore. Questo risponde alla domanda operativa: «il
testo della norma in KB contiene davvero questo valore?».

Graceful degradation: se la KB non è disponibile, ogni check ha `convergente=None`
e una nota esplicativa; nessuna eccezione al chiamante.
"""
from __future__ import annotations

import re
from typing import TypedDict

from ._kb_dynamic import NORMA_TO_CODICE, _ensure_path, is_kb_available


class _Check(TypedDict):
    valore_hardcoded: str
    contesto: str
    norma: str
    fts_query: str        # query FTS (senza virgole) per recuperare i chunk pertinenti
    pattern_verbatim: str  # regex del valore atteso nel contenuto


VALORI_DA_VALIDARE: dict[str, list[_Check]] = {
    "verifica_protezione": [
        {
            "valore_hardcoded": "1.45",
            "contesto": "I2 ≤ 1.45·In — rapporto convenzionale di funzionamento (sovraccarico)",
            "norma": "CEI 64-8:2024",
            "fts_query": "sovraccarico coordinamento",
            "pattern_verbatim": r"1[.,]45",
        },
        {
            "valore_hardcoded": "I²t = costante (≤3 s)",
            "contesto": "Icw: relazione tenuta-durata per tempi fino a 3 s (quadri)",
            "norma": "IEC 61439-1:2020",
            "fts_query": "withstand current constant duration",
            "pattern_verbatim": r"I.{0,3}t.{0,18}constant",
        },
    ],
    "caduta_tensione": [
        {
            "valore_hardcoded": "4%",
            "contesto": "Soglia raccomandata di caduta di tensione (origine→apparecchio)",
            "norma": "CEI 64-8:2024",
            "fts_query": "caduta tensione raccomanda",
            "pattern_verbatim": r"4\s*%",
        },
    ],
    "valuta_rischio_fulmine": [
        {
            "valore_hardcoded": "Lf = 1e-2",
            "contesto": "Valore medio tipico della perdita Lf (danno fisico) — Allegato C",
            "norma": "CEI EN 62305-2:2013",
            "fts_query": "valori tipici perdita",
            "pattern_verbatim": r"10.{0,4}-?\s*2|0[.,]01",
        },
    ],
}


class ValidationResult(TypedDict):
    valore_atteso: str
    norma: str
    contesto: str
    convergente: bool | None
    note: str


def _kb_text_for(codice: str, fts_query: str, limit: int = 8) -> str | None:
    """Concatena il contenuto completo dei primi `limit` chunk FTS della norma."""
    _ensure_path()
    try:
        from k2a_norme_tecniche.db import get_connection  # type: ignore
    except Exception:  # noqa: BLE001
        return None
    safe = fts_query.replace(",", " ").replace('"', " ")
    try:
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT c.contenuto FROM chunks c
                   JOIN documenti d ON c.documento_id = d.id
                   JOIN chunks_fts f ON f.rowid = c.id
                   WHERE d.codice = ? AND chunks_fts MATCH ? LIMIT ?""",
                (codice, safe, limit),
            ).fetchall()
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 — query/FTS error
        return None
    if not rows:
        return None
    return " ".join(r[0] for r in rows)


def valida_valori_tool(tool_name: str) -> list[dict]:
    """Valida i valori normativi hardcoded di `tool_name` contro la KB.

    Ritorna una lista di ValidationResult. `convergente`:
      - True  : il pattern del valore è presente nel testo KB della norma
      - False : norma in KB ma valore NON trovato (potenziale drift → da indagare)
      - None  : KB non disponibile / norma non mappata (non valutabile)
    """
    checks = VALORI_DA_VALIDARE.get(tool_name, [])
    if not checks:
        return []
    kb_ok = is_kb_available()
    results: list[dict] = []
    for c in checks:
        res: ValidationResult = {
            "valore_atteso": c["valore_hardcoded"],
            "norma": c["norma"],
            "contesto": c["contesto"],
            "convergente": None,
            "note": "",
        }
        codice = NORMA_TO_CODICE.get(c["norma"])
        if not kb_ok or codice is None:
            res["note"] = "KB non disponibile o norma non mappata: validazione non eseguibile"
            results.append(res)  # type: ignore[arg-type]
            continue
        testo = _kb_text_for(codice, c["fts_query"])
        if not testo:
            res["note"] = f"Nessun chunk KB per la query '{c['fts_query']}' su {c['norma']}"
            results.append(res)  # type: ignore[arg-type]
            continue
        match = re.search(c["pattern_verbatim"], testo, re.IGNORECASE)
        res["convergente"] = match is not None
        res["note"] = (
            f"Valore '{c['valore_hardcoded']}' confermato nel testo KB di {c['norma']}"
            if match else
            f"Valore '{c['valore_hardcoded']}' NON trovato nel testo KB di {c['norma']} "
            f"(pattern: {c['pattern_verbatim']}) — possibile drift, verificare"
        )
        results.append(res)  # type: ignore[arg-type]
    return results
