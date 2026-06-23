"""§4 prep — l'engine regge `competitor` sia string[] (schema vecchio Advisor) sia
object[] (nuovo, dopo il merge del branch grounding di Luca). Il normalizer FEED
canonicalizza a object[] così il breaking change non rompe la prod."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.pipeline import _normalize_inputs as n  # noqa: E402


def test_competitor_stringhe_diventano_oggetti():
    out = n({"competitor": ["ACME", "Beta Srl"]})
    assert out["competitor"] == [{"nome": "ACME"}, {"nome": "Beta Srl"}]


def test_competitor_oggetti_passano_intatti():
    src = [{"nome": "ACME", "descrizione": "leader"}, {"nome": "Beta"}]
    assert n({"competitor": src})["competitor"] == src


def test_competitor_misto_e_tipi_strani():
    # lista mista str+dict → tutto object[]; valori non str/dict scartati
    assert n({"competitor": ["ACME", {"nome": "Beta"}]})["competitor"] == [{"nome": "ACME"}, {"nome": "Beta"}]
    assert n({"competitor": [1, 2, "ACME"]})["competitor"] == [{"nome": "ACME"}]


def test_non_tocca_altri_campi_e_assenza():
    src = {"settore": "ingegneria", "fatturato": 1400000}
    assert n(src) == src                          # nessun competitor → invariato
    assert "competitor" not in n({"settore": "x"})
    assert n(None) is None                         # robusto su input non-dict


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
