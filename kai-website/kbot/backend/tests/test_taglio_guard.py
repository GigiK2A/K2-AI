"""Una risposta interrotta a metà frase viene completata una volta (20/10/2026: 1 turno su 36, stop_reason=end_turn)."""
from types import SimpleNamespace

import pytest

from app.lib import taglio_guard as T

BASE = ("Per correggere la fattura conviene emettere una nota di credito di 500 euro più IVA, collegata alla fattura originale, "
        "così il documento resta tracciabile e non si crea una doppia fatturazione. ")


class _C:
    def __init__(self, testo=None, errore=None):
        self.testo, self.errore, self.chiamate, self.visto = testo, errore, 0, None
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.chiamate += 1
        self.visto = kw
        if self.errore:
            raise self.errore
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.testo)])


@pytest.mark.parametrize("testo,atteso", [
    (BASE + "Qui invece la rettific", True),
    (BASE + "Il cliente però non deve accettare nulla e la nota di credito va registrata nel periodo in cui", True),
    (BASE + "Ti conviene farlo subito.", False),
    (BASE + "Hai già emesso una nuova fattura?", False),
    (BASE + "\n\n- Verifica la data\n- Controlla l'importo della nota di credito", False),        # elenco puntato
    (BASE + "\n\n1. Emetti la nota\n2. Registrala nello stesso periodo della fattura originale", False),
    (BASE + "\n\n## Fonti", False),
    (BASE + "Fonti: D.P.R. 633/1972, art. 26.", False),
    ("Sì.", False),
    ("", False),
    (BASE + "\n```\ncodice senza chiusura", False),
])
def test_e_troncata(testo, atteso):
    assert T.e_troncata(testo) is atteso


def test_completa_aggiunge_la_continuazione_una_volta():
    c = _C("rettifica va fatta con la nota di credito, non con una nuova fattura.")
    out = T.completa(c, "m", "sys", [{"role": "user", "content": "q"}], BASE + "Qui invece la rettific")
    assert out.endswith("non con una nuova fattura.") and c.chiamate == 1
    assert c.visto["messages"][-2]["role"] == "assistant" and "metà frase" in c.visto["messages"][-1]["content"]


def test_completa_non_chiama_se_la_risposta_e_finita():
    c = _C("x")
    assert T.completa(c, "m", "s", [], BASE + "Ti conviene farlo subito.") == BASE + "Ti conviene farlo subito."
    assert c.chiamate == 0


def test_completa_toglie_la_parola_ripetuta():
    c = _C("rettifica va fatta con la nota di credito.")
    out = T.completa(c, "m", "s", [], BASE + "Qui invece la rettifica")
    assert out.endswith("rettifica va fatta con la nota di credito.") and "rettifica rettifica" not in out


def test_completa_fail_open():
    t = BASE + "Qui invece la rettific"
    assert T.completa(_C(errore=RuntimeError("x")), "m", "s", [], t) == t


def test_completa_spento(monkeypatch):
    monkeypatch.setenv("KBOT_TAGLIO_GUARD", "0")
    c = _C("x")
    t = BASE + "Qui invece la rettific"
    assert T.completa(c, "m", "s", [], t) == t and c.chiamate == 0
