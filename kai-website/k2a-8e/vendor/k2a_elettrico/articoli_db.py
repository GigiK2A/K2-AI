"""DB articoli del cervello + ingestione (JSON/CSV) + query (MT-E1).

Il "DB del cervello" e' **SQLite**. L'ingestione legge JSON o CSV (export
costruttore o ETIM/BMEcat-piatto), **valida ogni voce con lo schema** e:
- voce valida  -> caricata;
- voce non valida -> **SCARTATA con motivo** (mai completata o inventata).

Sorgente di verita' = i file di seed groundati in `data/articoli/*.json`.
La query del tool costruisce un DB **in-memory** dal seed (deterministico,
nessun binario committato); `scripts/ingest_articoli.py` puo' materializzare
un file `data/articoli.db` se serve.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from .articoli_schema import Articolo, valida_articolo

_SEED_DIR = Path(__file__).parent / "data" / "articoli"

# Mapping colonne CSV piatte -> dati_targa (export costruttore / ETIM-piatto).
_CSV_TARGA = {
    "In_A": float,
    "curva": str,
    "poli": int,
    "potere_int_Icn_kA": float,
    "Ue_V": str,
    "Ui_V": float,
    "Uimp_kV": float,
    "norma": str,
}
_CSV_TOP = ("id", "codice_articolo", "costruttore", "tipo_dispositivo",
            "etim_class", "simbolo_grafico_id", "fonte", "vigenza")


def _record_da_riga_csv(row: dict) -> dict:
    """Una riga CSV piatta -> record nidificato {..., dati_targa:{...}}."""
    targa: dict[str, Any] = {}
    for k, conv in _CSV_TARGA.items():
        if k in row and row[k] not in (None, ""):
            targa[k] = conv(row[k])
    rec = {k: row[k] for k in _CSV_TOP if k in row and row[k] not in (None, "")}
    rec["dati_targa"] = targa
    return rec


def ingest(
    sorgente: Union[str, Path, Iterable[dict]],
    formato: Optional[str] = None,
) -> tuple[list[Articolo], list[dict]]:
    """Carica voci-articolo da JSON/CSV (path) o da una lista di record (dict).

    Ritorna (validi, scartati[{'record','motivo'}]). Il chiamante decide cosa fare
    degli scartati: NON vengono mai 'aggiustati' o inventati.
    """
    record_grezzi: list[dict]
    if isinstance(sorgente, (str, Path)):
        p = Path(sorgente)
        fmt = (formato or p.suffix.lstrip(".")).lower()
        if fmt == "json":
            data = json.loads(p.read_text(encoding="utf-8"))
            record_grezzi = data["articoli"] if isinstance(data, dict) and "articoli" in data else data
        elif fmt == "csv":
            with p.open(encoding="utf-8", newline="") as f:
                record_grezzi = [_record_da_riga_csv(r) for r in csv.DictReader(f)]
        else:
            raise ValueError(f"formato non supportato: {fmt!r} (attesi 'json' o 'csv')")
    else:
        record_grezzi = list(sorgente)

    validi: list[Articolo] = []
    scartati: list[dict] = []
    for rec in record_grezzi:
        try:
            validi.append(valida_articolo(rec))
        except Exception as e:  # ValidationError / ValueError
            scartati.append({"record": rec, "motivo": str(e)})
    return validi, scartati


# --------------------------------------------------------------------------- DB

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articoli (
    id TEXT PRIMARY KEY,
    codice_articolo TEXT NOT NULL,
    costruttore TEXT NOT NULL,
    tipo_dispositivo TEXT NOT NULL,
    In_A REAL,
    curva TEXT,
    poli INTEGER,
    potere_int_Icn_kA REAL,
    etim_class TEXT,
    simbolo_grafico_id TEXT,
    fonte TEXT NOT NULL,
    vigenza TEXT NOT NULL,
    dati_targa TEXT NOT NULL
);
"""

_COLS = ("id", "codice_articolo", "costruttore", "tipo_dispositivo", "In_A", "curva",
         "poli", "potere_int_Icn_kA", "etim_class", "simbolo_grafico_id", "fonte",
         "vigenza", "dati_targa")


def crea_db(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA_SQL)
    return conn


def carica(conn: sqlite3.Connection, articoli: Iterable[Articolo]) -> int:
    n = 0
    for a in articoli:
        t = a.dati_targa
        conn.execute(
            f"INSERT OR REPLACE INTO articoli ({','.join(_COLS)}) VALUES ({','.join(['?'] * len(_COLS))})",
            (a.id, a.codice_articolo, a.costruttore, a.tipo_dispositivo,
             t.get("In_A"), t.get("curva"), t.get("poli"), t.get("potere_int_Icn_kA"),
             a.etim_class, a.simbolo_grafico_id, a.fonte, a.vigenza, json.dumps(t)),
        )
        n += 1
    conn.commit()
    return n


def carica_seed(seed_dir: Union[str, Path] = _SEED_DIR) -> tuple[list[Articolo], list[dict]]:
    validi: list[Articolo] = []
    scartati: list[dict] = []
    for f in sorted(Path(seed_dir).glob("*.json")):
        v, s = ingest(f)
        validi += v
        scartati += s
    return validi, scartati


def db_da_seed(seed_dir: Union[str, Path] = _SEED_DIR) -> sqlite3.Connection:
    """Costruisce un DB in-memory dal seed groundato (per il tool/test)."""
    conn = crea_db(":memory:")
    validi, _ = carica_seed(seed_dir)
    carica(conn, validi)
    return conn


def query(
    conn: sqlite3.Connection,
    *,
    costruttore: Optional[str] = None,
    tipo_dispositivo: Optional[str] = None,
    In_A: Optional[float] = None,
    In_min: Optional[float] = None,
    In_max: Optional[float] = None,
    curva: Optional[str] = None,
    poli: Optional[int] = None,
    potere_min_kA: Optional[float] = None,
) -> list[dict]:
    """Filtra gli articoli per requisito. Restituisce solo cio' che e' nel DB."""
    sql = (f"SELECT {','.join(_COLS)} FROM articoli WHERE 1=1")
    args: list[Any] = []
    if costruttore:
        sql += " AND lower(costruttore)=lower(?)"; args.append(costruttore)
    if tipo_dispositivo:
        sql += " AND tipo_dispositivo=?"; args.append(tipo_dispositivo)
    if In_A is not None:
        sql += " AND In_A=?"; args.append(In_A)
    if In_min is not None:
        sql += " AND In_A>=?"; args.append(In_min)
    if In_max is not None:
        sql += " AND In_A<=?"; args.append(In_max)
    if curva:
        sql += " AND curva=?"; args.append(curva)
    if poli is not None:
        sql += " AND poli=?"; args.append(poli)
    if potere_min_kA is not None:
        sql += " AND potere_int_Icn_kA>=?"; args.append(potere_min_kA)
    sql += " ORDER BY In_A, poli, curva"

    out: list[dict] = []
    for r in conn.execute(sql, args):
        d = dict(zip(_COLS, r))
        d["dati_targa"] = json.loads(d["dati_targa"])
        out.append(d)
    return out
