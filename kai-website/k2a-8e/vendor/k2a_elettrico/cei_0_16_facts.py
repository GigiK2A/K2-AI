"""Fact-file groundato dei parametri di protezione CEI 0-16 (gate per MT-B).

Carica `data/cei_0_16_facts.json` (valori VERBATIM dalla norma) e ne VERIFICA la
provenienza contro la KB `k2a-mcp-norme-tecniche`: per ogni parametro, ogni
`ancora` (substring) deve comparire nel chunk del paragrafo citato (documento
codice CEI_0_16). Questo PROVA che i valori vengono dalla fonte e non dal
modello: se un'ancora non è nel testo della norma, la validazione fallisce.

Questo modulo NON contiene logica/verifica di conformità (è MT-B): solo
estrazione/citazione/validazione di provenienza.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

FACTS_PATH = Path(__file__).resolve().parents[2] / "data" / "cei_0_16_facts.json"

# Default portabile: la KB norme-tecniche vendorizzata accanto al motore (stessa
# risoluzione di k2a_norme_tecniche/db.py). Override esplicito via K2A_NORME_TECNICHE_DB.
# Assente (dev/prod senza corpus) -> kb_disponibile()=False -> la verifica di provenienza
# e' SALTATA (degrado onesto), non un crash. Niente path personali hardcoded.
_DEFAULT_KB = str(Path(__file__).resolve().parents[2] / "data" / "norme_tecniche.db")


def kb_path() -> Path:
    return Path(os.environ.get("K2A_NORME_TECNICHE_DB", _DEFAULT_KB))


def carica_facts() -> dict[str, Any]:
    return json.loads(FACTS_PATH.read_text(encoding="utf-8"))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def kb_disponibile() -> bool:
    return kb_path().is_file()


def _doc_id(conn: sqlite3.Connection, codice: str) -> int | None:
    r = conn.execute("SELECT id, vigenza FROM documenti WHERE codice=?", (codice,)).fetchone()
    return r[0] if r else None


def _testo_paragrafo(conn: sqlite3.Connection, doc_id: int, paragrafo: str) -> str:
    rows = conn.execute(
        "SELECT contenuto FROM chunks WHERE documento_id=? AND paragrafo=? ORDER BY id",
        (doc_id, paragrafo),
    ).fetchall()
    return " ".join(_norm(r[0]) for r in rows)


def valida_provenienza(facts: dict[str, Any] | None = None, db: Path | None = None) -> dict[str, Any]:
    """Verifica che ogni ancora di ogni parametro sia presente nel paragrafo citato.

    Ritorna {param_id: {"ok": bool, "mancanti": [...]}}. Solleva FileNotFoundError
    se la KB non è disponibile (il chiamante può saltare la verifica in tal caso).
    """
    facts = facts or carica_facts()
    db = db or kb_path()
    if not db.is_file():
        raise FileNotFoundError(f"KB norme-tecniche non trovata: {db}")

    conn = sqlite3.connect(str(db))
    try:
        codice = facts["documento"]
        doc_id = _doc_id(conn, codice)
        if doc_id is None:
            raise RuntimeError(f"documento '{codice}' assente nella KB")
        report: dict[str, Any] = {}
        for p in facts["parametri"]:
            par = p["fonte"]["paragrafo"]
            testo = _testo_paragrafo(conn, doc_id, par)
            mancanti = [a for a in p["ancore"] if _norm(a) not in testo]
            report[p["id"]] = {"ok": not mancanti, "mancanti": mancanti, "paragrafo": par}
        return report
    finally:
        conn.close()
