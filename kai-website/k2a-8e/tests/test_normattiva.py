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
    # esiste come LEGGE 143/2013 — serve a provare che 'DM 143/2013' (confabulato) NON
    # viene verificato per via del tipo diverso.
    ("chunks/legge_2013_143_art_1.md",
     "Art. 1 - Conversione in legge del decreto in materia di pubblica amministrazione."),
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


def test_extract_norm_refs():
    txt = ("Si applica il DPR 380/2001 e il D.Lgs 81/2008. Le tariffe ex DM 143/2013. "
           "Vedi anche L. 241/1990. Un anno a 2 cifre come DM 37/08 va ignorato.")
    refs = {(r["tipo"], r["numero"], r["anno"]) for r in N.extract_norm_refs(txt)}
    assert ("decreto_presidente_repubblica", "380", 2001) in refs
    assert ("decreto_legislativo", "81", 2008) in refs
    assert ("decreto_ministeriale", "143", 2013) in refs
    assert ("legge", "241", 1990) in refs
    assert not any(r[2] == 8 for r in refs)              # '37/08' (2 cifre) scartato


def test_find_by_estremi_verifica_e_scarta_confabulato():
    if not _fts5_ok():
        return
    db = _fixture_db()
    try:
        _set_db(db)
        # norma reale → verificata, con testo verbatim + citazione
        hit = N.find_by_estremi(2008, "81", tipo="decreto_legislativo")
        assert hit and hit[0]["citazione"] == "D.Lgs 81/2008, art. 28"
        assert "valutazione dei rischi" in hit[0]["testo"]
        # alias di tipo: 'decreto_presidente_repubblica' ≡ prefisso-file 'dpr'
        assert N.find_by_estremi(2001, "380", tipo="decreto_presidente_repubblica")
        # CONFABULATO: 'DM 143/2013' → esiste solo legge_2013_143 → tipo diverso → niente match
        assert N.find_by_estremi(2013, "143", tipo="decreto_ministeriale") == []
        # ma come LEGGE 143/2013 esiste
        assert N.find_by_estremi(2013, "143", tipo="legge")
    finally:
        _set_db(None)
        db.unlink(missing_ok=True)


def test_enrich_citazioni_pipeline():
    """§3b end-to-end (livello pipeline): le norme reali del deliverable diventano
    citazioni grounded; la confabulata no."""
    if not _fts5_ok():
        return
    from app.pipeline import _enrich_citazioni_normattiva
    db = _fixture_db()
    try:
        _set_db(db)
        deliv = {"sez": {"t": "Il permesso di costruire (DPR 380/2001) e la sicurezza "
                              "(D.Lgs 81/2008). Tariffe ex DM 143/2013."}}
        out = _enrich_citazioni_normattiva(deliv, [])
        rif = " | ".join(c.get("riferimento", "") for c in out)
        assert "D.P.R. 380/2001" in rif                   # verificata
        assert "D.Lgs 81/2008" in rif                     # verificata
        assert "143/2013" not in rif                      # confabulata DM → NON aggiunta
        assert all(c.get("fonte") == "normattiva" for c in out)
        # senza corpus → no-op (ritorna le citazioni invariate)
        _set_db(None)
        assert _enrich_citazioni_normattiva(deliv, [{"x": 1}]) == [{"x": 1}]
    finally:
        _set_db(None)
        db.unlink(missing_ok=True)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
