"""Un filtro scritto male non deve costare l'intera lettura.

Il 20 ago 2026 Vendite doveva leggere i prospect «dal 2026-08-20» e ha passato quella
frase come filtro: PostgREST ha risposto 400 (PGRST100) e l'agente non ha letto NIENTE
— ha detto all'owner «sembra che ci sia stato un errore» e si è fermato.

La prosa non si indovina: interpretarla a naso porterebbe a leggere righe sbagliate e a
riportare numeri falsi. Si restituisce un errore che spiega la sintassi, così l'agente
corregge nello stesso giro di tool.
"""
import pytest

from aios.platform import _filtro_postgrest


# ---- quello che passa ----
@pytest.mark.parametrize("valore,atteso", [
    ("eq.nuovo", "eq.nuovo"),
    ("gte.2026-08-20", "gte.2026-08-20"),
    ("in.(nuovo,contattato)", "in.(nuovo,contattato)"),
    ("is.null", "is.null"),
    ("not.eq.chiuso", "not.eq.chiuso"),
    ("ilike.*srl*", "ilike.*srl*"),
])
def test_sintassi_giusta_passa_intatta(valore, atteso):
    ok, out = _filtro_postgrest(valore)
    assert ok and out == atteso


@pytest.mark.parametrize("valore,atteso", [
    ("nuovo", "eq.nuovo"),          # il caso ovvio si completa
    ("42", "eq.42"),
    ("2026-08-20", "eq.2026-08-20"),
])
def test_un_valore_secco_diventa_eq(valore, atteso):
    ok, out = _filtro_postgrest(valore)
    assert ok and out == atteso


# ---- quello che viene fermato ----
@pytest.mark.parametrize("valore", [
    "dal 2026-08-20",               # il caso reale
    "ultimi 7 giorni",
    "maggiore di 80",
    "tutti i nuovi",
    "",
])
def test_la_prosa_e_un_errore_non_un_indovinello(valore):
    ok, _out = _filtro_postgrest(valore)
    assert not ok


def test_un_operatore_inventato_non_passa():
    """«dopo.2026-08-20» non è PostgREST. Completarlo a `eq.dopo.2026-08-20` cercherebbe
    un valore letterale inesistente: zero righe, e l'agente riferisce «nessun prospect».
    Un numero falso è peggio di un errore."""
    for finto in ("dopo.2026-08-20", "prima.100", "maggiore.80"):
        ok, _ = _filtro_postgrest(finto)
        assert not ok, finto


@pytest.mark.parametrize("valore", ["info@laintegra.com", "3.14", "80"])
def test_un_valore_riconoscibile_passa(valore):
    """Non si rifiuta tutto quello che ha un punto: un'email non somiglia a un operatore."""
    ok, out = _filtro_postgrest(valore)
    assert ok and out == f"eq.{valore}"


@pytest.mark.parametrize("valore", ["www.modulonet.com", "K2-AI s.r.l.s."])
def test_gli_ambigui_si_fermano_ma_con_le_istruzioni(valore):
    """`www.modulonet.com` è indistinguibile da un operatore sbagliato. Fra i due errori
    si scarta quello che non si recupera: dedurre `eq.` a caso può dare zero righe e far
    riferire «nessun risultato». Rifiutare costa un giro di tool e si corregge."""
    from aios.platform import leggi_tabella
    ok, _ = _filtro_postgrest(valore)
    assert not ok
    out = leggi_tabella(ClientFinto(), tabella="marketing_prospects",
                        filtri={"website": valore})
    assert f"eq.{valore}" in out["error"]          # gli dice esattamente cosa scrivere


class ClientFinto:
    def __init__(self):
        self.chiamate = []

    def select(self, tabella, params):
        self.chiamate.append((tabella, params))
        return [{"company": "Alfa"}]


def test_il_messaggio_insegna_la_sintassi():
    """L'errore deve bastare all'agente per correggersi da solo, e il DB non va
    nemmeno interrogato: un 400 costerebbe la lettura intera."""
    from aios.platform import leggi_tabella
    c = ClientFinto()
    out = leggi_tabella(c, tabella="marketing_prospects",
                        filtri={"created_at": "dal 2026-08-20"})
    assert "error" in out
    assert "operatore.valore" in out["error"] and "gte.2026-08-20" in out["error"]
    assert c.chiamate == []


def test_con_la_sintassi_giusta_legge():
    from aios.platform import leggi_tabella
    c = ClientFinto()
    assert leggi_tabella(c, tabella="marketing_prospects",
                         filtri={"created_at": "gte.2026-08-20"}) == [{"company": "Alfa"}]
    _tab, params = c.chiamate[0]
    assert params["created_at"] == "gte.2026-08-20"


def test_il_valore_secco_arriva_come_eq():
    from aios.platform import leggi_tabella
    c = ClientFinto()
    leggi_tabella(c, tabella="pipeline_leads", filtri={"status": "nuovo"})
    assert c.chiamate[0][1]["status"] == "eq.nuovo"


def test_limite_righe_e_tabella_obbligatoria():
    from aios.platform import leggi_tabella
    c = ClientFinto()
    assert "error" in leggi_tabella(c, tabella=None)
    leggi_tabella(c, tabella="invoices", limit=5000)
    assert c.chiamate[0][1]["limit"] == "200"


def test_un_errore_del_db_non_esplode():
    from aios.platform import leggi_tabella

    class Rotto:
        def select(self, *a, **kw):
            raise RuntimeError("connessione persa")

    assert "connessione persa" in leggi_tabella(Rotto(), tabella="invoices")["error"]
