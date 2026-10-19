"""Lo stato diagnostico emesso senza marcatori non deve mai arrivare all'utente (fuga vista in prod il 19/10/2026)."""
import pytest

from app.lib import signals
from app.lib.prompts import extract_diagnosi, strip_diagnosi_block

PROSA = "Sì: 14 dipendenti, sede a Foligno, srl di verniciatura."
JSON_FULL = ('{"fase":"esplorazione","ipotesi":[{"t":"Problema non ancora chiaro","s":"aperta","p":50}],'
             '"manca":"se c\'e\' un problema concreto","confidenza":"bassa"}')
CASI = {
    "nudo": f"{PROSA}\n\n{JSON_FULL}",
    "troncato": f'{PROSA}\n\n{{"fase":"esplorazione","ipotesi":[{{"t":"Problema non ancora chiaro","s":"aperta","p":50}}],"manca":"se c\'e\' un',
    "in_blocco_json": f"{PROSA}\n\n```json\n{JSON_FULL}\n```",
    "spazi": f'{PROSA}\n\n{{ "fase" : "diagnosi", "ipotesi": [] }}',
}


def _stream(testo, passo):
    sc, out = signals.StreamScrubber(), []
    for i in range(0, len(testo), passo):
        out.append(sc.feed(testo[i:i + passo]))
    out.append(sc.flush())
    return "".join(out)


@pytest.mark.parametrize("nome", list(CASI))
@pytest.mark.parametrize("passo", [1, 2, 3, 5, 7, 11, 64])
def test_lo_stream_non_mostra_il_json_nudo_comunque_sia_spezzato(nome, passo):
    visibile = _stream(CASI[nome], passo)
    assert visibile.strip() == PROSA, (nome, passo, visibile)


@pytest.mark.parametrize("nome", list(CASI))
def test_il_testo_finale_non_contiene_il_json(nome):
    pulito = strip_diagnosi_block(CASI[nome])
    assert pulito == PROSA and "fase" not in pulito and "ipotesi" not in pulito


def test_lo_stato_si_recupera_quando_il_json_e_completo():
    d = extract_diagnosi(CASI["nudo"])
    assert d and d["fase"] == "esplorazione" and d["ipotesi"][0]["p"] == 50
    assert extract_diagnosi(CASI["in_blocco_json"])["confidenza"] == "bassa"
    assert extract_diagnosi(CASI["troncato"]) is None              # troncato: niente stato, ma niente fuga


def test_i_marcatori_normali_funzionano_ancora():
    t = f"{PROSA}\nDIAGNOSI_STATO_START {JSON_FULL} DIAGNOSI_STATO_END"
    assert strip_diagnosi_block(t) == PROSA
    assert _stream(t, 4).strip() == PROSA
    assert extract_diagnosi(t)["fase"] == "esplorazione"


def test_nessun_falso_positivo_su_testo_normale():
    for t in ("La fase di prova dura al massimo sei mesi.", 'Nella "fase" iniziale servono tre documenti.',
              "Un oggetto {a: 1} in JavaScript non ha virgolette.", "Il JSON {\"nome\": \"x\"} è valido."):
        assert strip_diagnosi_block(t) == t
        assert _stream(t, 3) == t
        assert extract_diagnosi(t) is None
