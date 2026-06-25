"""Tool `lookup_ntc` — ricerca full-text NTC 2018 + Circolare.

Sorgente: `ntc_2018.db` (SQLite + FTS5; path risolto via env NTC_DB_PATH),
generato da `chunk_ntc.py` parsando il PDF ufficiale D.M. 17/01/2018.

Restituisce il testo dei paragrafi NTC che corrispondono alla query, così che
ogni `norm_ref` nei TraceStep delle altre verifiche sia citabile alla lettera.
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash

import os
import sqlite3
from pathlib import Path

from pydantic import BaseModel, Field

from .schemas import CalcResult, TraceStep

NTC_DB_PATH = Path(
    os.environ.get("NTC_DB_PATH", os.path.expanduser("~/normattiva_ai/ntc_2018/ntc_2018.db"))
)


class LookupNtcInput(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Testo da cercare (FTS5). Esempi: '\"3.3.2\"' per paragrafo specifico, "
            "'\"velocità\" \"vento\"' per query semantica, '\"Tab. 3.3.I\"' per tabella."
        ),
    )
    paragrafo: str | None = Field(
        None,
        description="Filtro su paragrafo (es. '3.3' restituisce solo §3.3.x).",
    )
    max_risultati: int = Field(5, ge=1, le=20)
    max_chars_per_risultato: int = Field(1500, ge=100, le=10000)


class NtcResult(BaseModel):
    paragrafo: str
    testo: str
    rilevanza_rank: float | None = None


class LookupNtcOutput(CalcResult):
    db_path: str = ""
    risultati: list[NtcResult] = Field(default_factory=list)
    n_totali: int = 0


def lookup_ntc(inp: LookupNtcInput) -> LookupNtcOutput:
    out = LookupNtcOutput(tool="lookup_ntc", inputs_hash=compute_inputs_hash(inp))
    out.db_path = str(NTC_DB_PATH)

    if not NTC_DB_PATH.exists():
        out.out_of_scope = True
        out.out_of_scope_reason = (
            f"DB NTC non trovato: {NTC_DB_PATH}. Esegui chunk_ntc.py o esporta "
            "NTC_DB_PATH=/percorso/alternativo."
        )
        return out

    conn = sqlite3.connect(NTC_DB_PATH)
    cur = conn.cursor()

    filtro = ""
    params: list = [inp.query]
    if inp.paragrafo:
        filtro = " AND file LIKE ?"
        params.append(f"NTC 2018 §{inp.paragrafo}%")

    try:
        rows = cur.execute(
            f"SELECT file, testo, rank FROM chunks_fts "
            f"WHERE chunks_fts MATCH ?{filtro} "
            f"ORDER BY rank LIMIT ?",
            params + [inp.max_risultati],
        ).fetchall()
    except sqlite3.OperationalError as e:
        out.warnings.append(f"Query FTS non valida: {e}. Suggerimento: usa virgolette per frasi.")
        rows = []

    out.n_totali = len(rows)
    for file, testo, rank in rows:
        # estrai SOLO il riferimento §x.y.z (rimuovi titolo lungo)
        par = file
        if "—" in file:
            par = file.split("—")[0].strip()
        snippet = testo
        if len(snippet) > inp.max_chars_per_risultato:
            snippet = snippet[: inp.max_chars_per_risultato] + "…[troncato]"
        out.risultati.append(NtcResult(paragrafo=par, testo=snippet, rilevanza_rank=rank))

    conn.close()

    out.trace.append(TraceStep(
        label="lookup NTC",
        formula="SELECT FROM chunks_fts WHERE FTS5 MATCH ?",
        substitution=f"query='{inp.query}' filtro_par='{inp.paragrafo}' → {len(rows)} risultati",
        value=len(rows), unit="risultati",
        norm_ref="DB locale: D.M. 17/01/2018 — NTC 2018 (Gazz. Uff. n.42 SO n.8)",
    ))
    out.primary_value = len(rows)
    out.primary_unit = "risultati"
    return out
