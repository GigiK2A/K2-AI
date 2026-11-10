"""10/11/2026: «indicando espressamente il numero dell'articolo» (art. 113 comma 2 D.Lgs. 81/2008) il K-BOT non lo recuperava: il parser dei
riferimenti riconosceva «art. N» solo se subito seguito da «del/di» e dagli estremi: «art. 113 comma 2 del D.Lgs. 81/2008», «articolo 113,
comma 2, del decreto legislativo n. 81 del 2008» e «TUSL» non producevano alcun riferimento."""
import pytest

from app.lib import norme_evidence as N

M = N.lettore()
pytestmark = pytest.mark.skipif(M is None, reason="lettore Normattiva non disponibile")


def _r(testo):
    return [(r.get("tipo"), r.get("numero"), r.get("anno"), r.get("articolo"), r.get("comma")) for r in M.extract_norm_refs(testo)]


ATTESO = ("decreto_legislativo", "81", 2008, "113", "2")


@pytest.mark.parametrize("t", [
    "Cosa prevede esattamente l'art. 113 comma 2 del D.Lgs. 81/2008 sulle scale verticali permanenti?",
    "L'articolo 113, comma 2, del decreto legislativo n. 81 del 2008 dopo il D.L. 159/2025",
    "D.Lgs. 81/2008, art. 113, comma 2",
    "ex art. 113 co. 2 del D.Lgs 81/08",
    "Vale ancora l'art. 113, comma 2 del TUSL per le scale a pioli?",
])
def test_art_113_comma_2_si_riconosce(t):
    assert ATTESO in _r(t), _r(t)


def test_decreto_legge_con_comma_composto():
    assert ("decreto_legge", "159", 2025, "5", "1-bis") in _r("l'art. 5, comma 1-bis, del D.L. 159/2025")


def test_forma_con_la_data():
    r = _r("il decreto legislativo 9 aprile 2008, n. 81, art. 113")
    assert ("decreto_legislativo", "81", 2008, "113", None) in r


def test_i_riferimenti_di_prima_non_cambiano():
    assert ("regio_decreto", "262", 1942, "2087", None) in _r("art. 2087 c.c.")
    assert ("legge", "300", 1970, "7", None) in _r("art. 7 della L. 300/1970")
    assert ("decreto_legislativo", "231", 2001, "25-septies", None) in _r("D.Lgs 231/2001, art. 25-septies")
    assert _r("Abbiamo fatturato 81/2008 euro") == []                     # una frazione non è una norma
