"""10/11/2026, test C: dopo il contenuto principale il K-BOT aggiungeva «Se nella tua visualizzazione manca qualcosa, dimmi l'ultima
frase che vedi e riprendo da lì». Causa: `taglio_guard` scambiava per interrotta una risposta COMPLETA (finale senza punto), chiedeva una
«continuazione» e appendeva la risposta meta del modello. Con l'API vera lo `stop_reason` dice se il modello ha finito (end_turn) o è stato
tagliato (max_tokens): la guardia agisce solo sul secondo caso, sull'ellissi, o se lo stop_reason manca."""
from types import SimpleNamespace

import pytest

from app.lib import taglio_guard as T

BASE = ("Per correggere la fattura conviene emettere una nota di credito di 500 euro più IVA, collegata alla fattura originale, "
        "così il documento resta tracciabile e non si crea una doppia fatturazione. ")
COMPLETA_SENZA_PUNTO = BASE + "Prima di investire, verifica quante delle tue aziende accetterebbero davvero l'offerta e a quale condizione"


class _C:
    def __init__(self, testo="x"):
        self.testo, self.chiamate, self.visto = testo, 0, None
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.chiamate += 1
        self.visto = kw
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.testo)])


def test_end_turn_la_risposta_e_finita_non_si_chiama_il_modello():
    c = _C("Se nella tua visualizzazione manca qualcosa, dimmi l'ultima frase che vedi e riprendo da lì.")
    assert T.completa(c, "m", "s", [], COMPLETA_SENZA_PUNTO, stop_reason="end_turn") == COMPLETA_SENZA_PUNTO
    assert c.chiamate == 0


def test_max_tokens_si_chiede_la_continuazione_anche_se_il_testo_sembra_finito():
    c = _C("e così il costo resta sotto controllo.")
    out = T.completa(c, "m", "s", [], BASE + "Ti conviene farlo subito.", stop_reason="max_tokens")
    assert c.chiamate == 1 and out.endswith("sotto controllo.")


def test_l_ellissi_finale_si_completa_anche_con_end_turn():
    c = _C("e così il costo resta sotto controllo.")
    out = T.completa(c, "m", "s", [], BASE + "Qui invece la detrazione dell'IVA…", stop_reason="end_turn")
    assert c.chiamate == 1 and out.endswith("sotto controllo.")


def test_senza_stop_reason_resta_l_euristica_di_prima():
    c = _C("rettifica va fatta con la nota di credito.")
    out = T.completa(c, "m", "s", [], BASE + "Qui invece la rettific", stop_reason=None)
    assert c.chiamate == 1 and out.endswith("nota di credito.")


@pytest.mark.parametrize("meta", [
    "Se nella tua visualizzazione manca qualcosa, dimmi l'ultima frase che vedi e riprendo da lì.",
    "La mia risposta non era interrotta: era già completa.",
    "OK_COMPLETA",
    "Mi scuso, il messaggio precedente sembrava troncato; ecco la parte mancante.",
])
def test_la_risposta_meta_del_modello_non_si_appende(meta):
    c = _C(meta)
    t = BASE + "Qui invece la rettific"
    assert T.completa(c, "m", "s", [], t, stop_reason="max_tokens") == t


def test_il_prompt_di_continuazione_prevede_l_uscita_se_la_risposta_e_completa():
    c = _C("e basta.")
    T.completa(c, "m", "s", [], BASE + "Qui invece la rettific", stop_reason="max_tokens")
    assert "OK_COMPLETA" in c.visto["messages"][-1]["content"]


# ── dall'endpoint, come in produzione ─────────────────────────────────────────────────────────────────
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_e2e_scenarios import (FakeAnthropic, _chiamate_chat, _make_session, client, fake_anthropic, fake_db)  # noqa: E402,F401


def _continuazioni():
    return [c for c in FakeAnthropic.captured_calls
            if any("OK_COMPLETA" in str(m.get("content")) for m in (c.get("messages") or []))]


def _turno(client, sid, testo):
    r = client.post("/api/kbot/message/stream", json={"session_id": sid, "message": testo})
    return [json.loads(x[5:]) for x in r.text.splitlines() if x.startswith("data:")][-1]


def test_endpoint_end_turn_senza_punto_finale_non_aggiunge_nulla(client, fake_anthropic):
    fake_anthropic.canned_text = ("Parto da una distinzione: l'idea è una proposta da validare, non ancora un problema risolto. " * 3
                                  + "Il dato più utile da raccogliere è quante delle tue aziende accetterebbero davvero l'offerta")
    sid = _make_session(client)
    fin = _turno(client, sid, "Che ne pensi della mia idea di investimento da 100.000 euro?")
    assert fin["message"].rstrip().endswith("l'offerta") and not _continuazioni()


def test_endpoint_max_tokens_chiede_la_continuazione(client, fake_anthropic, monkeypatch):
    from types import SimpleNamespace as NS
    import test_e2e_scenarios as E
    monkeypatch.setattr(E._FakeStream, "get_final_message",
                        lambda self: NS(stop_reason="max_tokens", usage=NS(input_tokens=1, output_tokens=1), content=[]))
    fake_anthropic.canned_text = "Parto da una distinzione: l'idea è una proposta da validare, non ancora un problema risolto. " * 3 + "Il dato più utile"
    sid = _make_session(client)
    _turno(client, sid, "Che ne pensi della mia idea di investimento da 100.000 euro?")
    assert _continuazioni()          # la chiamata di continuazione è partita
