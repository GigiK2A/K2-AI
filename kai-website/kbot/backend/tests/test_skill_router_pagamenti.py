"""Tema «pagamenti-frodi» (test 09, 22/10/2026). Il set è di un agente che non ha visto il router: alla PRIMA misura 6 domande
su 16 non accendevano la skill (0 falsi positivi su 24); i trigger sono stati poi allargati guardando quei 6 casi, quindi il set
non è più held-out: serve come regressione. Per una prova nuova servono domande nuove."""
import json
from pathlib import Path

from app.lib import skill_router as R

SET = json.load(open(Path(__file__).parent / "data" / "skill_router_pagamenti.json", encoding="utf-8"))
SKILL = "pagamenti-frodi-bancarie"


def test_domande_sui_pagamenti_accendono_la_skill():
    mancati = [x["q"] for x in SET if x["tema"] == "pagamenti" and SKILL not in R.skill_per_tema([x["q"]])]
    assert not mancati, mancati


def test_domande_di_altri_temi_non_la_accendono():
    falsi = [x["q"] for x in SET if x["tema"] == "altro" and SKILL in R.skill_per_tema([x["q"]])]
    assert not falsi, falsi


def test_il_caso_del_test_09():
    q = ("Un nostro dipendente ha ricevuto un'email che sembrava arrivare da un fornitore abituale, con un IBAN diverso per "
         "pagare una fattura. Abbiamo fatto un bonifico di 7.500 euro e solo dopo abbiamo scoperto che l'email era falsa.")
    assert SKILL in R.skill_per_tema([q])


def test_bonifico_ordinario_e_iban_in_fattura_non_bastano():
    assert SKILL not in R.skill_per_tema(["Dobbiamo pagare un fornitore via bonifico entro il 30: come registriamo la fattura?"])
    assert SKILL not in R.skill_per_tema(["Come indichiamo l'IBAN in fattura ai clienti?"])
