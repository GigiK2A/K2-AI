"""Resolver Normattiva — il ROUTE dei fatti C2 normativi (handoff Luca §3).

Interroga il corpus FTS5 di Luca (`normattiva.db`: 62.491 articoli + 41.696 norme
integrali) per dare al motore 8e le CITAZIONI VERBATIM che il Grounding Contract
pretende sui Boost normativi (Safety/Build/TLC/Agevolazioni/Legal/Fisco). Senza
questo, il ROUTE di quei fatti degrada a "da verificare" (onesto ma vuoto) e il CAGE
C2 (`norma_non_citata`, §2) non ha una fonte contro cui grounddare.

Deterministico, read-only, no LLM. Il path del DB viene da env `NORMATTIVA_DB_PATH`;
se l'env manca o il file non c'è → `available()` è False e il motore degrada come
prima (nessun crash, nessuna invenzione). Lo schema è quello del server MCP di Luca:
  chunks(id, file, testo, source) + chunks_fts(file, testo)  [FTS5]
Il nome-file codifica gli estremi: `decreto_legislativo_2001_231_art_25-septies.md`.
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

_DB_ENV = "NORMATTIVA_DB_PATH"

# tipo (dal nome-file) → label di citazione. Il corpus usa sia forme estese sia
# abbreviate (es. 'decreto_presidente_repubblica' e 'dpr'): mappate entrambe. I tipi
# non mappati si umanizzano (la label è cosmetica; gli estremi restano corretti).
_TIPO_LABEL = {
    "legge": "L.", "l": "L.",
    "decreto_legislativo": "D.Lgs", "dlgs": "D.Lgs", "d_lgs": "D.Lgs",
    "decreto_legge": "D.L.", "dl": "D.L.",
    "decreto_ministeriale": "D.M.", "dm": "D.M.",
    "decreto_presidente_repubblica": "D.P.R.", "dpr": "D.P.R.",
    "decreto_presidente_consiglio_ministri": "D.P.C.M.", "dpcm": "D.P.C.M.",
    "regio_decreto": "R.D.", "rd": "R.D.",
    "regio_decreto_legge": "R.D.L.", "rdl": "R.D.L.",
    "codice": "Codice", "costituzione": "Cost.",
}

# nome-file → estremi: <tipo>_<anno>_<numero>_art_<articolo>.md
_FN_RE = re.compile(
    r"^(?P<tipo>[a-z_]+?)_(?P<anno>\d{4})_(?P<numero>[0-9A-Za-z-]+?)_art_(?P<articolo>[0-9A-Za-z._-]+)\.md$"
)


def _db_path() -> Optional[Path]:
    p = os.environ.get(_DB_ENV)
    if not p:
        return None
    path = Path(p)
    return path if path.is_file() else None


def available() -> bool:
    """True solo se il corpus è raggiungibile: altrimenti il motore degrada onesto."""
    return _db_path() is not None


def _estremi(filename: str) -> dict:
    name = os.path.basename(str(filename))
    m = _FN_RE.match(name)
    if not m:
        return {"file": name}
    d = m.groupdict()
    return {"tipo": d["tipo"], "anno": int(d["anno"]), "numero": d["numero"],
            "articolo": d["articolo"], "file": name}


def citazione(estremi: dict) -> str:
    """Estremi → stringa di citazione leggibile (es. 'D.Lgs 231/2001, art. 25-septies')."""
    tipo = estremi.get("tipo")
    if not tipo:
        return str(estremi.get("file", "")).removesuffix(".md").replace("_", " ")
    label = _TIPO_LABEL.get(tipo, tipo.replace("_", " ").capitalize())
    numero, anno = estremi.get("numero"), estremi.get("anno")
    base = f"{label} {numero}/{anno}".strip() if numero and anno else label
    art = estremi.get("articolo")
    return f"{base}, art. {art}" if art else base


def _fts_query(query: str) -> str:
    """Senza operatori espliciti, unisce le parole in AND (come il server di Luca)."""
    q = (query or "").strip()
    if not q:
        return q
    if not re.search(r'["*^]|\bAND\b|\bOR\b|\bNOT\b|NEAR\(', q):
        tokens = [t for t in re.split(r"\s+", q) if t]
        q = " AND ".join(tokens) if tokens else q
    return q


def search(query: str, limit: int = 5) -> list[dict]:
    """FTS5 sul corpus → lista di articoli con testo VERBATIM + estremi + citazione.

    Ritorna [] se il corpus non è disponibile o la query FTS è invalida (degrado
    onesto: nessun crash, nessun fatto inventato). Ogni voce:
    {tipo, anno, numero, articolo, file, citazione, snippet, testo, rank}.
    """
    db = _db_path()
    if not db or not query or not query.strip():
        return []
    q = _fts_query(query)
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=20)
    except sqlite3.Error:
        return []
    try:
        con.execute("PRAGMA busy_timeout=20000")
        rows = con.execute(
            "SELECT file, testo, snippet(chunks_fts, 1, '«', '»', '…', 16), rank "
            "FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?",
            (q, max(1, int(limit))),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()

    out: list[dict] = []
    for file, testo, snippet, rank in rows:
        e = _estremi(file)
        out.append({**e, "citazione": citazione(e), "snippet": snippet,
                    "testo": testo, "rank": round(rank, 4) if rank is not None else None})
    return out
