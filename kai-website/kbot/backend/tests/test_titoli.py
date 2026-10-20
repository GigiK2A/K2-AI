"""Titoli brevi delle conversazioni."""
from types import SimpleNamespace

import pytest

from app.lib import titoli as T


class _C:
    def __init__(self, testo=None, errore=None):
        self.testo, self.errore, self.chiamate = testo, errore, 0
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.chiamate += 1
        if self.errore:
            raise self.errore
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.testo)])


@pytest.mark.parametrize("grezzo,atteso", [
    ('"Ammortamento computer."', "Ammortamento computer"),
    ("Titolo: Ritardi dipendente", "Ritardi dipendente"),
    ("«server aziendale lento»", "Server aziendale lento"),
    ("Una frase davvero molto lunga che supera di parecchio le cinque parole", "Una frase davvero molto lunga"),
    ("Nuova conversazione", None), ("Richiesta assistenza", None), ("Domanda aziendale", None), ("", None), ("   ", None),
])
def test_pulisci(grezzo, atteso):
    assert T.pulisci(grezzo) == atteso


def test_pulisci_non_supera_48_caratteri():
    assert len(T.pulisci("Interpretazione straordinariamente complicata dell'ammortamento")) <= T.MAX_CARATTERI


@pytest.mark.parametrize("testo", [
    "Abbiamo comprato un computer da 2.500 euro per l'azienda. Conviene scaricarlo tutto subito oppure ammortizzarlo?",
    "Un nostro dipendente arriva spesso in ritardo, anche di 20-30 minuti, e nonostante glielo abbiamo già fatto presente continua.",
    "Da qualche giorno il nostro server aziendale è molto lento, soprattutto quando più dipendenti lavorano.",
])
def test_la_riserva_e_breve_e_non_e_la_frase_tagliata(testo):
    t = T.titolo_di_riserva(testo)
    assert 1 <= len(t.split()) <= 5 and len(t) <= T.MAX_CARATTERI
    assert not testo.startswith(t) or len(t.split()) <= 4          # non è «Abbiamo comprato un computer da 2.500 euro per l»
    assert t.lower() not in ("abbiamo", "un", "da qualche")


def test_riserva_su_testo_vuoto():
    assert T.titolo_di_riserva("") == "Nuova pratica"


def test_genera_usa_il_modello_una_sola_volta():
    c = _C("Ammortamento computer")
    assert T.genera(c, "m", "Abbiamo comprato un computer da 2.500 euro, conviene ammortizzarlo?") == "Ammortamento computer"
    assert c.chiamate == 1


@pytest.mark.parametrize("risposta", ["Nuova conversazione", "", "Richiesta assistenza"])
def test_genera_scarta_i_titoli_generici_e_usa_la_riserva(risposta):
    t = T.genera(_C(risposta), "m", "Un nostro dipendente arriva spesso in ritardo e non cambia")
    assert t and not T.GENERICI.match(t)


def test_genera_fail_open_sull_errore():
    t = T.genera(_C(errore=RuntimeError("timeout")), "m", "Il server aziendale è molto lento oggi")
    assert t == T.titolo_di_riserva("Il server aziendale è molto lento oggi")


def test_genera_spento_con_la_variabile(monkeypatch):
    monkeypatch.setenv("KBOT_TITOLI_LLM", "0")
    c = _C("Qualcosa")
    T.genera(c, "m", "Il server aziendale è molto lento oggi")
    assert c.chiamate == 0
