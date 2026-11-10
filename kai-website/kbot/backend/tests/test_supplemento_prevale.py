"""Il supplemento (articoli riscaricati dall'API ufficiale, con vigenza e note) prevale sul corpus principale (consolidato più vecchio)."""
import importlib.util
import sqlite3
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[3] / "k2a-8e" / "app" / "normattiva.py"


def _db(path, righe):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY AUTOINCREMENT, file TEXT, testo TEXT, source TEXT DEFAULT 'x')")
    con.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(file, testo)")
    for f, t in righe:
        cur = con.execute("INSERT INTO chunks(file, testo) VALUES (?,?)", (f, t))
        con.execute("INSERT INTO chunks_fts(rowid, file, testo) VALUES (?,?,?)", (cur.lastrowid, f, t))
    con.commit(); con.close()


@pytest.fixture()
def modulo(tmp_path, monkeypatch):
    f = "decreto_legislativo_2008_81_art_113.md"
    _db(tmp_path / "main.db", [("corpus/" + f, "# Art. 113 — Scale\n\n**2.** testo VECCHIO del corpus"),
                               ("corpus/decreto_legislativo_2008_81_art_114.md", "# Art. 114\n\ntesto 114 del corpus")])
    _db(tmp_path / "supp.db", [("chunks/" + f, "# Art. 113 — Scale\n\n**2.** testo NUOVO aggiornato\nAGGIORNAMENTO (65) D.L. 159/2025")])
    monkeypatch.setenv("NORMATTIVA_DB_PATH", str(tmp_path / "main.db"))
    monkeypatch.setenv("NORMATTIVA_SUPPLEMENT_PATH", str(tmp_path / "supp.db"))
    spec = importlib.util.spec_from_file_location("_n8e_test", SRC)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_l_articolo_aggiornato_batte_quello_del_corpus(modulo):
    r = modulo.find_by_estremi(2008, "81", "decreto_legislativo", "113", limit=1)
    assert r and "NUOVO" in r[0]["testo"] and "159/2025" in r[0]["testo"]


def test_gli_altri_articoli_restano_quelli_del_corpus(modulo):
    r = modulo.find_by_estremi(2008, "81", "decreto_legislativo", "114", limit=1)
    assert r and "del corpus" in r[0]["testo"]


def test_nessun_doppione_dello_stesso_articolo(modulo):
    r = modulo.find_by_estremi(2008, "81", "decreto_legislativo", None, limit=10)
    assert sorted(x["articolo"] for x in r).count("113") == 1
