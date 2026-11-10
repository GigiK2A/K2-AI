"""10/11/2026, test B: stima del costo di due assunzioni da 1.700 € netti: netto annuo su 12 mensilità senza dirlo, «costo aziendale 55.000 €» e
«margine di contribuzione 35%» introdotti come se fossero dati, poi ritirati come «numeri ipotetici». Qui: un blocco di regole per i calcoli
economici che entra nel prompt solo quando serve, e un controllo deterministico dell'aritmetica scritta («a × b = c»)."""
import pytest

from app.lib import calcoli
from app.lib.prompts import build_system_prompt_v2


@pytest.mark.parametrize("t,atteso", [
    ("Vorrei assumere due persone con 1.700 euro netti al mese: me lo posso permettere?", True),
    ("Voglio investire 100.000 euro in una piattaforma: quanto devo incassare per rientrare?", True),
    ("Qual è il margine di contribuzione e il payback?", True),
    ("Quanto costa un dipendente all'azienda, oltre al netto?", True),
    ("Posso fare un richiamo disciplinare al dipendente?", False),
    ("ciao", False),
])
def test_serve(t, atteso):
    assert calcoli.serve(t) is atteso


def _prompt(ultimo):
    s = {"id": "s", "user_id": "u", "messages": [{"role": "user", "content": ultimo}], "collected_data": {}}
    return build_system_prompt_v2(["diagnosi-ai-operativa-pmi"], s)


def test_il_blocco_entra_nel_prompt_solo_per_le_domande_economiche():
    assert "CALCOLI ECONOMICI" in _prompt("Voglio assumere due persone da 1.700 euro netti al mese")
    assert "CALCOLI ECONOMICI" not in _prompt("Il dipendente è arrivato in ritardo tre volte")


def test_il_blocco_chiede_ipotesi_esplicite_e_vieta_percentuali_standard():
    b = calcoli.BLOCCO.lower()
    assert "ipotesi" in b and "netto" in b and "mensilit" in b and "costo" in b and "standard" in b


@pytest.mark.parametrize("t", [
    "Il netto annuo è 1.700 × 12 × 2 = 40.800 euro.",
    "12 x 1.700 = 20.400",
    "1.500,50 × 2 = 3.001",
    "2 * 3 = 6 e poi 4 × 5 = 20",
    "Nessun calcolo qui.",
])
def test_aritmetica_corretta_nessuna_nota(t):
    assert calcoli.nota_aritmetica(t) == ""


def test_aritmetica_sbagliata_nota_con_il_valore_giusto():
    n = calcoli.nota_aritmetica("Il netto annuo è 1.700 × 12 × 2 = 38.000 euro.")
    assert "40.800" in n and "38.000" in n


def test_piu_errori_una_sola_nota_breve():
    n = calcoli.nota_aritmetica("1.000 × 3 = 3.500 e 200 × 5 = 1.200")
    assert n.count("\n") <= 3 and "3.000" in n and "1.000" in n


def test_l_idea_da_validare_porta_il_piano_di_validazione():
    p = _prompt("Sto pensando di investire 100.000 euro per sviluppare una piattaforma AI da vendere con un abbonamento da 99 euro al mese: "
                "pensi che sia un investimento intelligente?")
    assert "VALIDAZIONE DI UN'IDEA" in p and "CALCOLI ECONOMICI" in p
    assert "VALIDAZIONE DI UN'IDEA" not in _prompt("Voglio assumere due persone da 1.700 euro netti al mese")
    assert "VALIDAZIONE DI UN'IDEA" not in _prompt("Il dipendente è arrivato in ritardo tre volte")
