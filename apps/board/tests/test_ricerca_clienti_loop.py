"""La ricerca clienti deve partire da sola, non dal bottone nel cockpit.

Il Prospector esisteva da mesi ma era chiamato SOLO da POST /api/marketing/prospect:
nessun processo lo lanciava mai, e `marketing_prospects` era fermo a 9 righe mentre
un'azienda dovrebbe cercare clienti ogni giorno.
"""
import autonomy_loop


class FakeProspector:
    def __init__(self, trovati):
        self._t = trovati
        self.chiamate = []

    def find(self, n=5):
        self.chiamate.append(n)
        return self._t


class FakeClient:
    def __init__(self):
        self.inserts = []

    def insert(self, table, row):
        self.inserts.append((table, row))
        return [{"id": len(self.inserts), **row}]


class FakeAudit:
    def __init__(self):
        self.righe = []

    def append(self, **kw):
        self.righe.append(kw)


class FakeKernel:
    def __init__(self):
        self._supabase = FakeClient()
        self.audit = FakeAudit()


class FakePlatform:
    def __init__(self, trovati):
        self.kernel = FakeKernel()
        self.prospector = FakeProspector(trovati)


def _prospect(company, fit=80, in_target=True):
    return {"company": company, "website": "https://x.it", "sector": "studi",
            "in_target": in_target, "fit_score": fit, "fit_reason": "processi manuali",
            "contact_email": "info@x.it", "draft_subject": "Ciao", "draft_body": "Testo"}


def test_salva_solo_i_qualificati():
    p = FakePlatform([_prospect("Alfa", fit=80), _prospect("Beta", fit=40),
                      _prospect("Gamma", in_target=False)])
    out = autonomy_loop._cerca_clienti(p)
    assert out["trovati"] == 3
    assert out["salvati"] == 1 and out["scartati"] == 2
    assert out["nomi"] == ["Alfa"]
    tabelle = [t for t, _r in p.kernel._supabase.inserts]
    assert tabelle == ["marketing_prospects"]


def test_la_bozza_viene_salvata_ma_non_inviata():
    """L'invio è esterno: il loop non deve avere nessun canale di uscita qui."""
    p = FakePlatform([_prospect("Alfa")])
    autonomy_loop._cerca_clienti(p)
    _tab, riga = p.kernel._supabase.inserts[0]
    assert riga["draft_body"] == "Testo"
    assert riga["status"] == "nuovo"        # nuovo, non 'inviato'


def test_ogni_salvataggio_lascia_una_traccia_in_audit():
    p = FakePlatform([_prospect("Alfa")])
    autonomy_loop._cerca_clienti(p)
    eventi = [r["event"] for r in p.kernel.audit.righe]
    assert eventi == ["executed"]


def test_una_ricerca_che_fallisce_non_rompe_il_loop():
    class Rotto(FakeProspector):
        def find(self, n=5):
            raise RuntimeError("web search non disponibile")

    p = FakePlatform([])
    p.prospector = Rotto([])
    out = autonomy_loop._cerca_clienti(p)
    assert "errore" in out and "web search" in out["errore"]


def test_senza_prospector_non_fa_niente():
    p = FakePlatform([])
    p.prospector = None
    assert autonomy_loop._cerca_clienti(p) == {}


def test_quanti_per_giro_dall_ambiente(monkeypatch):
    p = FakePlatform([_prospect("Alfa")])
    autonomy_loop._cerca_clienti(p)
    assert p.prospector.chiamate == [autonomy_loop.PROSPECT_PER_GIRO]
