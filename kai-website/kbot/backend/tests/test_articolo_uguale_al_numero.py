"""D.Lgs. 11/2010 art. 11 non veniva trovato (test 09, 22/10/2026): quando il numero dell'articolo coincide col numero della
norma la ricerca FTS restituiva 8 chunk qualsiasi e il filtro li scartava tutti."""
import os
from pathlib import Path

import pytest

DB = Path(os.path.expanduser("~/normattiva_ai/normattiva.db"))
pytestmark = pytest.mark.skipif(not DB.is_file(), reason="corpus Normattiva non presente")


def test_art_11_del_dlgs_11_2010_si_trova():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_n8e", Path(__file__).resolve().parents[3] / "k2a-8e" / "app" / "normattiva.py")
    m = importlib.util.module_from_spec(spec)
    os.environ["NORMATTIVA_DB_PATH"] = str(DB)
    spec.loader.exec_module(m)
    r = m.find_by_estremi(2010, "11", "decreto_legislativo", "11", limit=1)
    assert r and str(r[0]["articolo"]) == "11" and "non autorizzate" in r[0]["testo"]
