"""Secondo livello dell'instradamento skill: il modello sceglie il tema quando le parole non ne trovano nessuno."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from app.lib import skill_router as R
from app.lib.services import BASE_SKILL, resolve_skills_for_session


class _Client:
    def __init__(self, testo=None, errore=None):
        self.testo, self.errore, self.chiamate = testo, errore, 0
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.chiamate += 1
        if self.errore:
            raise self.errore
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.testo)])


def test_il_modello_sceglie_solo_temi_esistenti_e_al_massimo_due():
    c = _Client('{"temi": ["fisco", "inventato", "lavoro", "contratti"]}')
    assert R.temi_con_modello(c, "m", "se compro un furgone quanto scarico dalle tasse") == ["fisco", "lavoro"]


@pytest.mark.parametrize("risposta", ['{"temi": []}', "boh", "", '{"temi": "fisco"}'])
def test_risposte_vuote_o_storte_non_accendono_nulla(risposta):
    assert R.temi_con_modello(_Client(risposta), "m", "come imposto il wifi") == []


def test_errore_del_modello_fail_open():
    assert R.temi_con_modello(_Client(errore=RuntimeError("timeout")), "m", "una domanda qualunque lunga") == []


def test_i_temi_del_modello_valgono_solo_se_le_parole_non_trovano_nulla():
    assert R.skill_per_tema(["se compro un furgone quanto scarico dalle tasse"], ["lavoro"]) == ["diritto-del-lavoro-italiano", "diritto-italiano"]   # il modello
    assert R.skill_per_tema(["ho un avviso di accertamento"], ["lavoro"]) == ["fiscale-tributario-italiano"]          # le parole vincono
    assert R.skill_per_tema(["mi scrivi una mail di auguri per i clienti?"], []) == []


def test_resolve_usa_il_tema_scelto_dal_modello():
    sess = {"collected_data": {"tema_llm": {"h": "x", "temi": ["fisco"]}},
            "messages": [{"role": "user", "content": "il computer preso a dicembre lo posso mettere nei costi o lo spalmo"}]}
    sk = resolve_skills_for_session(sess)
    assert sk[0] == BASE_SKILL and "fiscale-tributario-italiano" in sk


def _async_helper():
    from app.api import message as M
    return M


def test_tema_modello_non_chiama_se_le_parole_bastano_o_il_messaggio_e_breve(monkeypatch):
    M = _async_helper()
    monkeypatch.setattr(M, "ANTHROPIC_API_KEY", "k")
    chiamate = []
    monkeypatch.setattr(R, "temi_con_modello", lambda *a, **k: chiamate.append(1) or ["fisco"])
    msgs = lambda t: [{"role": "user", "content": t}]
    for testo in ("ho un avviso di accertamento da pagare", "ok grazie"):
        out = asyncio.run(M._tema_modello({}, msgs(testo), testo))
        assert "tema_llm" not in out
    assert not chiamate


def test_tema_modello_chiama_una_volta_per_messaggio_e_conserva_il_risultato(monkeypatch):
    M = _async_helper()
    monkeypatch.setattr(M, "ANTHROPIC_API_KEY", "k")
    chiamate = []
    monkeypatch.setattr(R, "temi_con_modello", lambda *a, **k: chiamate.append(1) or ["fisco"])
    t = "se compro un furgone nuovo per l'azienda quanto posso scaricare dalle tasse"
    out = asyncio.run(M._tema_modello({}, [{"role": "user", "content": t}], t))
    assert out["tema_llm"]["temi"] == ["fisco"] and len(chiamate) == 1
    asyncio.run(M._tema_modello(out, [{"role": "user", "content": t}], t))
    assert len(chiamate) == 1                                  # stesso messaggio: nessuna seconda chiamata


def test_tema_modello_spento_con_la_variabile(monkeypatch):
    M = _async_helper()
    monkeypatch.setenv("KBOT_SKILL_TEMI_LLM", "0")
    monkeypatch.setattr(M, "ANTHROPIC_API_KEY", "k")
    t = "se compro un furgone nuovo per l'azienda quanto posso scaricare dalle tasse"
    assert "tema_llm" not in asyncio.run(M._tema_modello({}, [{"role": "user", "content": t}], t))


def test_tema_modello_non_chiama_il_modello_su_un_messaggio_di_crisi(monkeypatch):
    M = _async_helper()
    monkeypatch.setattr(M, "ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr(R, "temi_con_modello", lambda *a, **k: pytest.fail("chiamata al modello su un messaggio di crisi"))
    t = "Ho 200mila euro di debiti, l'azienda sta chiudendo e non ce la faccio più. A volte penso di farla finita."
    assert "tema_llm" not in asyncio.run(M._tema_modello({}, [{"role": "user", "content": t}], t))
