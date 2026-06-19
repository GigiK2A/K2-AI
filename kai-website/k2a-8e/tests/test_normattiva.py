"""Resolver Normattiva (§3a) — testato su un DB FTS5 fixture minuscolo (no dipendenza
dal corpus reale da 1.8GB). Verifica: available() segue l'env, search() ritorna testo
verbatim + estremi + citazione, parsing degli estremi dal nome-file, degrado onesto."""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import normattiva as N  # noqa: E402

_ROWS = [
    ("chunks/decreto_legislativo_2008_81_art_28.md",
     "Art. 28 - La valutazione dei rischi per la salute e sicurezza dei lavoratori "
     "deve riguardare tutti i rischi presenti nei luoghi di lavoro."),
    ("chunks/dpr_2001_380_art_10.md",
     "Art. 10 - Interventi subordinati a permesso di costruire. Costituiscono "
     "trasformazione urbanistica ed edilizia del territorio."),
    ("chunks/legge_1990_241_art_1.md",
     "Art. 1 - L'attivita' amministrativa persegue i fini determinati dalla legge."),
]


def _fixture_db() -> Path:
    db = Path(tempfile.mktemp(suffix=".db"))
    con = sqlite3.connect(str(db))
    con.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(file, testo)")
    con.executemany("INSERT INTO chunks_fts(file, testo) VALUES (?, ?)", _ROWS)
    con.commit()
    con.close()
    return db


def _set_db(path) -> None:
    if path is None:
        os.environ.pop("NORMATTIVA_DB_PATH", None)
    else:
        os.environ["NORMATTIVA_DB_PATH"] = str(path)


def _fts5_ok() -> bool:
    try:
        c = sqlite3.connect(":memory:")
        c.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        c.close()
        return True
    except sqlite3.OperationalError:
        return False


def test_available_segue_l_env():
    _set_db(None)
    assert N.available() is False                       # niente env → non disponibile
    if not _fts5_ok():
        return
    db = _fixture_db()
    try:
        _set_db(db)
        assert N.available() is True
        _set_db(Path(tempfile.gettempdir()) / "non_esiste_normattiva.db")
        assert N.available() is False                   # path inesistente → non disponibile
    finally:
        _set_db(None)
        db.unlink(missing_ok=True)


def test_search_ritorna_verbatim_estremi_e_citazione():
    if not _fts5_ok():
        return
    db = _fixture_db()
    try:
        _set_db(db)
        res = N.search("valutazione dei rischi", limit=3)
        assert res, "FTS dovrebbe trovare l'art. 28 D.Lgs 81/2008"
        top = res[0]
        assert top["tipo"] == "decreto_legislativo" and top["anno"] == 2008
        assert top["numero"] == "81" and top["articolo"] == "28"
        assert top["citazione"] == "D.Lgs 81/2008, art. 28"
        assert "valutazione dei rischi" in top["testo"]   # testo VERBATIM, non snippet
        assert "«" in top["snippet"]                       # match evidenziato
    finally:
        _set_db(None)
        db.unlink(missing_ok=True)


def test_citazione_formatta_i_tipi():
    assert N.citazione({"tipo": "dpr", "anno": 2001, "numero": "380", "articolo": "10"}) == "D.P.R. 380/2001, art. 10"
    assert N.citazione({"tipo": "legge", "anno": 1990, "numero": "241", "articolo": "1"}) == "L. 241/1990, art. 1"
    # tipo non mappato → umanizzato, mai crash
    assert "2020" in N.citazione({"tipo": "delibera_autorita", "anno": 2020, "numero": "5", "articolo": "2"})


def test_degrado_onesto_senza_corpus():
    _set_db(None)
    assert N.search("qualsiasi cosa") == []              # no corpus → [], niente invenzioni
    if not _fts5_ok():
        return
    db = _fixture_db()
    try:
        _set_db(db)
        assert N.search("") == []                        # query vuota → []
        assert N.search("   ") == []
    finally:
        _set_db(None)
        db.unlink(missing_ok=True)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
