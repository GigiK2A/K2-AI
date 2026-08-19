"""Una mail non parte due volte allo stesso cliente.

Due strade portavano al doppio invio, entrambe reali:
- due clic sulla card Telegram (o una card riproposta dopo un riavvio del loop, dato che
  l'elenco delle bozze già notificate vive in memoria);
- invio riuscito ma update dello stato fallito: `except: pass` lo ingoiava, la riga
  restava 'bozza' e il tick successivo la rimandava.
"""
import aios.sources.n8n as n8n_mod
from aios.conversation import ConversationManager


class Client:
    def __init__(self, stato="bozza"):
        self.righe = {"d1": {"id": "d1", "direction": "out", "status": stato,
                             "to_email": "cliente@example.it", "subject": "s",
                             "body": "b", "conversation_id": "c1",
                             "reply_to_message_id": None}}
        self.updates = []
        self.fallisci_update = False

    def select(self, table, params):
        return [dict(self.righe["d1"])] if "d1" in params.get("id", "") else []

    def update(self, table, filters, patch):
        self.updates.append((dict(filters), dict(patch)))
        if self.fallisci_update:
            raise RuntimeError("PostgREST giù")
        # rispetta il filtro su status: è la prenotazione atomica
        atteso = filters.get("status")
        if atteso and self.righe["d1"]["status"] != atteso.replace("eq.", ""):
            return []
        self.righe["d1"].update(patch)
        return [dict(self.righe["d1"])]


class Audit:
    def __init__(self):
        self.eventi = []

    def append(self, **kw):
        self.eventi.append(kw)


class Kernel:
    def __init__(self):
        self.audit = Audit()


class Platform:
    def __init__(self):
        self.kernel = Kernel()


def _conv(client):
    c = ConversationManager.__new__(ConversationManager)
    c.client = client
    c.platform = Platform()
    return c


def _n8n(monkeypatch, ok=True):
    partenze = []

    def fake(workflow, payload):
        partenze.append(payload)
        return {"ok": ok}

    monkeypatch.setattr(n8n_mod, "trigger_n8n", fake)
    return partenze


def test_invio_riuscito_segna_inviato(monkeypatch):
    partenze = _n8n(monkeypatch)
    c = Client()
    out = _conv(c).send("d1", actor="telegram")
    assert out["ok"] is True
    assert len(partenze) == 1
    assert c.righe["d1"]["status"] == "inviato"


def test_secondo_clic_non_manda_una_seconda_mail(monkeypatch):
    partenze = _n8n(monkeypatch)
    c = Client()
    conv = _conv(c)
    assert conv.send("d1")["ok"] is True
    out2 = conv.send("d1")
    assert out2["ok"] is False and out2.get("gia_gestita") is True
    assert len(partenze) == 1, "la mail è partita due volte"


def test_bozza_gia_inviata_non_riparte(monkeypatch):
    partenze = _n8n(monkeypatch)
    out = _conv(Client(stato="inviato")).send("d1")
    assert out["ok"] is False and out["gia_gestita"] is True
    assert partenze == []


def test_prenotazione_prima_di_uscire(monkeypatch):
    """L'ordine conta: prima si prenota, poi si esce verso il cliente."""
    ordine = []

    def fake(workflow, payload):
        ordine.append("invio")
        return {"ok": True}

    monkeypatch.setattr(n8n_mod, "trigger_n8n", fake)

    class C(Client):
        def update(self, table, filters, patch):
            if filters.get("status") == "eq.bozza":
                ordine.append("prenotazione")
            return super().update(table, filters, patch)

    _conv(C()).send("d1")
    assert ordine[:2] == ["prenotazione", "invio"]


def test_invio_fallito_rimette_la_bozza_disponibile(monkeypatch):
    _n8n(monkeypatch, ok=False)
    c = Client()
    out = _conv(c).send("d1")
    assert out["ok"] is False
    assert c.righe["d1"]["status"] == "bozza", "la bozza è rimasta bloccata"


def test_se_il_ripristino_fallisce_lo_dice(monkeypatch):
    """Il caso peggiore va detto, non ingoiato: risulta inviata senza essere partita."""
    _n8n(monkeypatch, ok=False)

    class C(Client):
        def update(self, table, filters, patch):
            out = super().update(table, filters, patch)
            if patch.get("status") == "bozza":
                raise RuntimeError("PostgREST giù")
            return out

    out = _conv(C()).send("d1")
    assert out["ok"] is False
    assert "va rimessa a mano" in out["errore"]


def test_ogni_invio_lascia_traccia_in_audit(monkeypatch):
    _n8n(monkeypatch)
    conv = _conv(Client())
    conv.send("d1", actor="telegram")
    eventi = [e["event"] for e in conv.platform.kernel.audit.eventi]
    assert eventi == ["proposed", "executed"]   # prenotazione, poi conferma
