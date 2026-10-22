"""Test 10 (22/10/2026): la ricerca web citava un sito di noleggio (cs-noleggi.it, «?utm_source=openai») al posto delle fonti
ufficiali. Priorità alle fonti ufficiali: prima ricerca ristretta ai domini istituzionali, ripiego senza filtro, fonti ordinate
e marcate, URL ripulito dal tracciamento."""
from types import SimpleNamespace

import pytest

from app.lib import web_search as W


@pytest.mark.parametrize("url,atteso", [
    ("https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legislativo:2008-04-09;81", True),
    ("https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32024R0886", True),
    ("https://www.agenziaentrate.gov.it/portale/documents/x.pdf", True),
    ("https://www.inail.it/cs/internet/home.html", True),
    ("https://servizi.lavoro.gov.it/x", True),
    ("https://www.arbitrobancariofinanziario.it/", True),
    ("https://cs-noleggi.it/blog/parapetti-anticaduta-normativa?utm_source=openai", False),
    ("https://www.money.it/bonifici", False),
    ("https://www.normattiva.it.evil.example/x", False),
    ("https://evil.example/?u=normattiva.it", False),
])
def test_e_ufficiale(url, atteso):
    assert W.e_ufficiale(url) is atteso


def test_ordina_e_marca_le_fonti():
    cites = [{"url": "https://cs-noleggi.it/blog/x?utm_source=openai", "title": "Noleggio"},
             {"url": "https://www.normattiva.it/x?utm_source=openai", "title": "D.Lgs. 81/2008"}]
    out = W.ordina_fonti(cites)
    assert [c["url"] for c in out] == ["https://www.normattiva.it/x", "https://cs-noleggi.it/blog/x"]
    assert out[0]["ufficiale"] is True and out[1]["ufficiale"] is False


def _risposta(urls):
    ann = [SimpleNamespace(type="url_citation", url=u, title=u) for u in urls]
    return SimpleNamespace(output_text="testo", output=[SimpleNamespace(content=[SimpleNamespace(annotations=ann)])])


class _Client:
    def __init__(self, risposte):
        self.risposte, self.chiamate = list(risposte), []
        self.responses = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.chiamate.append(kw)
        r = self.risposte.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def _patch(monkeypatch, client):
    import sys, types
    mod = types.ModuleType("openai"); mod.OpenAI = lambda **k: client
    monkeypatch.setitem(sys.modules, "openai", mod)
    monkeypatch.setattr(W, "OPENAI_API_KEY", "k")


def test_prima_ricerca_ristretta_ai_domini_ufficiali(monkeypatch):
    c = _Client([_risposta(["https://www.normattiva.it/a"])])
    _patch(monkeypatch, c)
    W.inizia_turno()
    out = W.run_openai_search("art. 115 d.lgs 81/2008 vigente")
    assert len(c.chiamate) == 1
    assert "normattiva.it" in c.chiamate[0]["tools"][0]["filters"]["allowed_domains"]
    assert "[ufficiale]" in out.lower()


def test_senza_risultati_ufficiali_si_ripiega_e_lo_dice(monkeypatch):
    c = _Client([_risposta([]), _risposta(["https://cs-noleggi.it/blog/x?utm_source=openai"])])
    _patch(monkeypatch, c)
    W.inizia_turno()
    out = W.run_openai_search("parapetti anticaduta")
    assert len(c.chiamate) == 2 and "filters" not in c.chiamate[1]["tools"][0]
    assert "non ufficiale" in out.lower() and "utm_source" not in out


def test_errore_del_filtro_ripiega_senza_filtro(monkeypatch):
    c = _Client([RuntimeError("filters non supportato"), _risposta(["https://www.inail.it/x"])])
    _patch(monkeypatch, c)
    W.inizia_turno()
    out = W.run_openai_search("inail")
    assert len(c.chiamate) == 2 and "inail.it" in out


def test_le_fonti_in_coda_sono_ordinate_e_marcate(monkeypatch):
    W.inizia_turno()
    W._registra([{"url": "https://cs-noleggi.it/x", "title": "Noleggio"}, {"url": "https://www.normattiva.it/y", "title": "Norma"}])
    testo = W.aggiungi_fonti_web("Risposta.")
    assert testo.index("normattiva.it") < testo.index("cs-noleggi.it")
    assert "non ufficiale" in testo.lower()
