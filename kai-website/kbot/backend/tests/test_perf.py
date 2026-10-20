"""Cronometro per fase e conteggio delle chiamate al modello."""
import time
from types import SimpleNamespace

from app.lib.perf import ClientContato, Cronometro


class _Fake:
    def __init__(self):
        self.messages = SimpleNamespace(create=self._create, stream=self._stream, altro=lambda: "x")

    def _create(self, **k):
        return SimpleNamespace(content=[], usage=SimpleNamespace(input_tokens=100, output_tokens=20))

    def _stream(self, **k):
        return "flusso"


def test_conta_chiamate_e_token():
    c = Cronometro()
    cl = ClientContato(_Fake(), c)
    cl.messages.create(model="m", max_tokens=60)
    cl.messages.create(model="m", max_tokens=800)
    assert cl.messages.stream(model="m", max_tokens=16000) == "flusso"
    assert cl.messages.altro() == "x"                     # il resto passa invariato
    assert c.chiamate == 3 and c.token_in == 200 and c.token_out == 40


def test_riepilogo_per_fase():
    c = Cronometro()
    for nome in ("preparato", "fonti", "primo_token", "ultimo_token", "verificato", "salvato"):
        time.sleep(0.01)
        c.segna(nome)
    r = c.riepilogo()
    for k in ("preparazione_s", "fonti_s", "primo_token_s", "generazione_s", "verifica_s", "salvataggio_s", "totale_s"):
        assert r[k] is not None and r[k] >= 0
    assert r["totale_s"] >= r["primo_token_s"] >= r["preparazione_s"]
    assert "chiamate_llm=0" in c.riga()


def test_una_marca_si_registra_una_volta():
    c = Cronometro()
    a = c.segna("x"); time.sleep(0.01); c.segna("x")
    assert c.marche["x"] == a
