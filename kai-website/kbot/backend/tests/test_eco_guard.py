"""La risposta non può essere il messaggio dell'utente ripetuto (20/10/2026)."""
from types import SimpleNamespace

import pytest

from app.lib import eco_guard as E

U = "Ricontrolla i calcoli: l'IVA sul computer da 2.500 euro è 550 euro e la quota di ammortamento del primo anno è 250 euro."


class _C:
    def __init__(self, testo=None, errore=None):
        self.testo, self.errore, self.chiamate = testo, errore, 0
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.chiamate += 1
        if self.errore:
            raise self.errore
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.testo)])


@pytest.mark.parametrize("risposta,atteso", [
    (U, True),
    (U.upper(), True),
    ("  " + U + "  ", True),
    (U.replace("550", "551"), True),                       # copia con una cifra cambiata
    (U + " Fammi sapere.", True),
    ("Hai ragione a farmelo rifare: l'IVA al 22% su 2.500 euro è 550 euro. La quota del primo anno è la metà del coefficiente.", False),
    ("Sì.", False),
    ("", False),
])
def test_e_eco(risposta, atteso):
    assert E.e_eco(risposta, U) is atteso


def test_un_messaggio_breve_non_e_mai_eco():
    assert E.e_eco("Sì, ok grazie", "Sì, ok grazie") is False


def test_una_risposta_che_cita_il_messaggio_ma_risponde_non_e_eco():
    r = U + "\n\nHo ricontrollato: l'IVA è corretta (22% di 2.500 = 550). La quota del primo anno invece va dimezzata per l'anno di acquisto, "\
            "quindi dipende dal coefficiente della tabella ministeriale e dal mese di entrata in funzione."
    assert E.e_eco(r, U) is False


def test_assicura_non_tocca_una_risposta_normale():
    c = _C("x")
    assert E.assicura(c, "m", "sys", [], "Ho ricontrollato: tutto corretto tranne la quota del primo anno.", U).startswith("Ho ricontrollato")
    assert c.chiamate == 0


def test_assicura_rigenera_una_volta():
    c = _C("Rifatti i calcoli: IVA 550 euro corretta; quota del primo anno dimezzata, quindi 125 euro se il coefficiente è 20%.")
    out = E.assicura(c, "m", "sys", [{"role": "user", "content": U}], U, U)
    assert out.startswith("Rifatti i calcoli") and c.chiamate == 1


def test_assicura_se_anche_la_seconda_e_un_eco_invita_a_riformulare():
    out = E.assicura(_C(U), "m", "sys", [], U, U)
    assert out == E.INVITO


def test_assicura_fail_open_sull_errore():
    assert E.assicura(_C(errore=RuntimeError("x")), "m", "sys", [], U, U) == E.INVITO


def test_spento_con_la_variabile(monkeypatch):
    monkeypatch.setenv("KBOT_ECO_GUARD", "0")
    c = _C("x")
    assert E.assicura(c, "m", "sys", [], U, U) == U and c.chiamate == 0
