"""Glossario degli indici e regola delle bozze: si accendono solo quando servono (19/10/2026)."""
import pytest

from app.lib import indici_e_bozze as IB
from app.lib.prompts import build_system_prompt_v2


@pytest.mark.parametrize("t", [
    "Dal bilancio allegato calcolami PFN/EBITDA e il DSO", "Com'è la posizione finanziaria netta della mia azienda?",
    "Ti do i numeri del bilancio 2025: ricavi 4 milioni, EBITDA 380.000", "La banca guarda la leva finanziaria?",
    "Ho debiti verso banche per 1,9 milioni, sono sostenibili?", "Quali indici di bilancio dovrei guardare?"])
def test_il_glossario_si_accende(t):
    assert "GLOSSARIO DEGLI INDICI" in IB.blocchi(t) and "NON è il capitale circolante netto" in IB.blocchi(t)


@pytest.mark.parametrize("t", ["Posso licenziare un dipendente in prova?", "Come funziona il TFR?", "Quando scade l'IVA trimestrale?",
                               "Scrivimi una poesia sul mare", "Un cliente non mi paga: cosa faccio?"])
def test_il_glossario_non_si_accende_fuori_tema(t):
    assert "GLOSSARIO DEGLI INDICI" not in IB.blocchi(t)


@pytest.mark.parametrize("t", [
    "Scrivimi una lettera di diffida per un cliente che non paga la fattura", "Prepara una mail di sollecito al cliente",
    "Redigi una disdetta del contratto di affitto", "Stendimi una PEC di contestazione per il fornitore", "fammi una bozza di risposta al reclamo"])
def test_la_regola_delle_bozze_si_accende(t):
    b = IB.blocchi(t)
    assert "BOZZA DI DOCUMENTO RICHIESTA" in b and "SEGNAPOSTO" in b and "231/2002" in b


@pytest.mark.parametrize("t", ["Come funziona una lettera di diffida?", "Cos'è una PEC?", "Devo preparare il bilancio, da dove parto?",
                               "Un cliente non paga, che interessi chiedo?"])
def test_la_regola_delle_bozze_non_si_accende_se_non_chiedi_un_testo(t):
    assert "BOZZA DI DOCUMENTO RICHIESTA" not in IB.blocchi(t)


def test_interruttori(monkeypatch):
    monkeypatch.setenv("KBOT_GLOSSARIO_INDICI", "0")
    monkeypatch.setenv("KBOT_REGOLA_BOZZE", "0")
    assert IB.blocchi("scrivimi una lettera di diffida, calcola la PFN") == ""


def test_i_blocchi_entrano_nel_system_prompt():
    sess = {"collected_data": {}, "messages": [{"role": "user", "content": "Scrivimi una diffida e calcolami la PFN dal bilancio"}]}
    p = build_system_prompt_v2([], sess)
    assert "GLOSSARIO DEGLI INDICI" in p and "BOZZA DI DOCUMENTO RICHIESTA" in p
    sess2 = {"collected_data": {}, "messages": [{"role": "user", "content": "Come funziona il TFR?"}]}
    p2 = build_system_prompt_v2([], sess2)
    assert "GLOSSARIO DEGLI INDICI" not in p2 and "BOZZA DI DOCUMENTO RICHIESTA" not in p2


def test_la_pfn_del_glossario_non_e_il_capitale_circolante():
    # la formula di riferimento col bilancio dello scenario E2: debiti finanziari 480.000 + 1.650.000, liquidità 140.000
    pfn = 480_000 + 1_650_000 - 140_000
    ebitda = 380_000 + 330_000
    assert pfn == 1_990_000 and round(pfn / ebitda, 1) == 2.8
    assert round(1_870_000 / 6_200_000 * 365) == 110
