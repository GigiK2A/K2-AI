"""«IVA inclusa»: la risposta che applica l'aliquota al lordo riceve una nota con lo scorporo (20/10/2026)."""
import pytest

from app.lib import iva_guard as G

U = ["Siamo una SRL, abbiamo comprato a ottobre un computer da 2.500 euro IVA inclusa. Come lo ammortizziamo?"]


def test_risposta_che_applica_il_22_al_lordo_riceve_la_nota():
    n = G.nota(U, "L'IVA è 2.500 × 22% = 550 €, quindi il costo da ammortizzare è 2.500 €.")
    assert n and "2.049,18" in n and "450,82" in n and "22%" in n


def test_risposta_gia_corretta_non_riceve_nulla():
    assert G.nota(U, "Scorporando: imponibile 2.049,18 € e IVA 450,82 €. Si ammortizza 2.049,18 €.") is None


def test_senza_iva_inclusa_non_si_tocca():
    assert G.nota(["Computer da 2.500 euro più IVA"], "L'IVA è 550 €.") is None
    assert G.nota(["Computer da 2.500 euro"], "L'IVA è 550 €.") is None


def test_dichiarazioni_in_conflitto_non_si_toccano():
    assert G.nota(["Computer da 2.500 euro IVA inclusa", "anzi no: 2.000 euro + IVA"], "IVA 550 €") is None


def test_la_risposta_non_parla_di_iva_non_riceve_nulla():
    assert G.nota(U, "Si ammortizza in più anni con i coefficienti della tabella ministeriale.") is None


def test_aliquota_diversa_dalla_risposta():
    n = G.nota(["Software da 1.100 euro IVA inclusa"], "L'IVA al 10% è 110 €.")
    assert n and "1.000" in n and "100" in n


def test_forma_inversa_iva_inclusa_importo():
    n = G.nota(["Prezzo IVA inclusa: 1.220 euro"], "IVA 22% = 268,40 €")
    assert n and "1.000" in n


def test_spento(monkeypatch):
    monkeypatch.setenv("KBOT_IVA_GUARD", "0")
    assert G.nota(U, "L'IVA è 550 €.") is None
