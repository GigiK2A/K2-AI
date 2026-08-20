"""Due scale per la stessa idea non devono costare la riga.

`marketing_prospects.fit_score` va 0-100, `pipeline_leads.score` va 1-10 (vincolo
`pipeline_leads_score_check`, verificato sul DB il 20 ago 2026). Vendite copiava il
primo nel secondo e PostgREST rispondeva 23514 su OGNI lead: dieci opportunità vere
perse perché due colonne che si chiamano quasi uguale misurano su scale diverse.
"""
import pytest

from aios.actuator import _in_scala, _sanitize


@pytest.mark.parametrize("fit,atteso", [
    (85, 9), (90, 9), (88, 9), (91, 9), (100, 10), (80, 8), (65, 7), (11, 1),
])
def test_un_punteggio_su_cento_diventa_su_dieci(fit, atteso):
    out = _sanitize("pipeline_leads", {"name": "Alfa", "score": fit}, "insert")
    assert out["score"] == atteso


def test_l_ordinamento_si_conserva():
    """Serve a ordinare i lead: se 85 e 100 diventassero entrambi 10, il punteggio
    non distinguerebbe più un prospect ottimo da uno mediocre."""
    punteggi = [_in_scala(v, 1, 10) for v in (30, 50, 70, 85, 100)]
    assert punteggi == sorted(punteggi)
    assert len(set(punteggi)) > 1


@pytest.mark.parametrize("dentro", [1, 3, 5, 8, 10])
def test_chi_e_gia_nella_scala_non_si_tocca(dentro):
    assert _in_scala(dentro, 1, 10) == dentro


def test_i_limiti_del_vincolo():
    """0 e 11 sono rifiutati dal DB: nessuno dei due deve arrivarci."""
    assert _in_scala(0, 1, 10) == 1
    assert _in_scala(-5, 1, 10) == 1
    assert _in_scala(150, 1, 10) == 10


def test_un_valore_non_numerico_passa_intatto():
    """Non è compito di questa funzione validare i tipi: se non è un numero, lo
    gestiscono i controlli a valle."""
    assert _in_scala("alto", 1, 10) == "alto"
    assert _in_scala(None, 1, 10) is None


def test_le_altre_tabelle_non_hanno_questo_vincolo():
    out = _sanitize("marketing_prospects", {"company": "Alfa", "fit_score": 85}, "insert")
    assert out["fit_score"] == 85          # 0-100 è la scala giusta qui


def test_la_riga_completa_di_un_lead_passa():
    """La riga esatta che PostgREST rifiutava con 23514."""
    out = _sanitize("pipeline_leads", {
        "company": "Modulo S.r.l.", "email": "info@modulonet.com",
        "sector": "manifatturiero", "score": 85, "status": "nuovo",
        "channel": "email", "pain_point": "controllo qualità manuale"}, "insert")
    assert out["name"] == "Modulo S.r.l."      # NOT NULL dedotto da company
    assert out["score"] == 9                   # scala riportata a 1-10
    assert out["status"] == "nuovo" and out["channel"] == "email"
