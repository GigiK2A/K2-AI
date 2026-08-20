"""Telegram e il cockpit devono essere LA STESSA conversazione.

Prima su Telegram parlavi col CommandRouter — istruzione singola, esegui, dimentica —
mentre nel cockpit c'era il ChatOrchestrator con sessioni persistenti e dibattito fra
reparti. Due chat diverse sugli stessi agenti: quello che chiedevi da telefono non
esisteva per quello che vedevi dal browser.
"""
from aios import telegram_chat
from aios.notify import telegram


class Client:
    """Le tabelle della chat del cockpit, in finto."""

    def __init__(self, sessioni=None, messaggi=None):
        self.sessioni = list(sessioni or [])
        self.messaggi = list(messaggi or [])
        self.insert_sessioni = 0

    def select(self, table, params):
        if table == "aios_chat_sessions":
            titolo = params.get("title", "").replace("eq.", "")
            return [s for s in self.sessioni if s["title"] == titolo]
        if table == "aios_chat_messages":
            sid = params.get("session_id", "").replace("eq.", "")
            return [m for m in self.messaggi if m.get("session_id") == sid]
        return []

    def insert(self, table, row):
        if table == "aios_chat_sessions":
            self.insert_sessioni += 1
            row = {"id": f"s{len(self.sessioni)+1}", **row}
            self.sessioni.append(row)
            return [row]
        self.messaggi.append(dict(row))
        return [row]

    def update(self, table, filters, patch):
        return []


class ChatFinta:
    """Come ChatOrchestrator: eventi di dibattito + azioni del turno."""

    def __init__(self, eventi):
        self.eventi = eventi
        self.chiamate = []

    def stream(self, text, agents=None, history=None, media=None):
        self.chiamate.append({"text": text, "agents": agents,
                              "storico": list(history or [])})
        yield from self.eventi


class Router:
    def __init__(self):
        self.ricevuti = []

    def handle(self, testo, actor="cockpit"):
        self.ricevuti.append((testo, actor))

        class R:
            def to_dict(self):
                return {"risposta": "fatto"}
        return R()


class Kernel:
    def __init__(self, client):
        self._supabase = client


class Platform:
    def __init__(self, chat, client, router=None):
        self.chat = chat
        self.kernel = Kernel(client)
        self.commands = router


def _telegram(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    mandati = []
    monkeypatch.setattr(telegram, "_post",
                        lambda m, p, timeout=35: mandati.append(p) or {})
    return mandati


EVENTI = [
    {"phase": "triage", "modo": "consulta", "agenti": ["finance"]},
    {"phase": "done", "agent": "finance", "text": "Non abbiamo fatture scadute.",
     "azioni": []},
    {"phase": "all_done", "agents": ["finance"]},
]


def test_il_messaggio_passa_dalla_chat_del_board(monkeypatch):
    mandati = _telegram(monkeypatch)
    chat = ChatFinta(EVENTI)
    out = telegram_chat.conversa(Platform(chat, Client()), "quante fatture scadute?")
    assert out["turni"] == 1
    assert chat.chiamate[0]["text"] == "quante fatture scadute?"
    testi = " ".join(str(m.get("text")) for m in mandati)
    assert "Non abbiamo fatture scadute." in testi
    assert "finance" in testi


def test_la_conversazione_vive_nelle_tabelle_del_cockpit(monkeypatch):
    """È questo che rende «la stessa cosa» vera: la sessione si vede dal browser."""
    _telegram(monkeypatch)
    c = Client()
    telegram_chat.conversa(Platform(ChatFinta(EVENTI), c), "ciao")
    assert c.insert_sessioni == 1
    assert c.sessioni[0]["title"].startswith("Telegram")
    ruoli = [m["role"] for m in c.messaggi]
    assert ruoli == ["user", "assistant"]
    assert c.messaggi[1]["agent"] == "finance"


def test_la_sessione_e_la_stessa_al_secondo_messaggio(monkeypatch):
    _telegram(monkeypatch)
    c = Client()
    p = Platform(ChatFinta(EVENTI), c)
    telegram_chat.conversa(p, "primo")
    p.chat = ChatFinta(EVENTI)
    telegram_chat.conversa(p, "secondo")
    assert c.insert_sessioni == 1                     # nessuna sessione nuova
    # e il secondo turno riceve lo storico del primo: c'è memoria
    assert len(p.chat.chiamate[0]["storico"]) >= 2


def test_le_azioni_da_confermare_diventano_bottoni(monkeypatch):
    """La chat mette in coda i casi sensibili col token cmdok: che il poller già gestisce."""
    mandati = _telegram(monkeypatch)
    eventi = [{"phase": "done", "agent": "vendite", "text": "Preparo la mail.", "azioni": [
        {"stato": "da_confermare", "id": 7, "descrizione": "invia email al lead"},
        {"stato": "eseguito", "descrizione": "aggiornato lead", "tabella": "pipeline_leads"},
        {"stato": "rifiutato", "descrizione": "cancella tutto", "motivo": "vietato"}]}]
    telegram_chat.conversa(Platform(ChatFinta(eventi), Client()), "scrivi al lead")
    dati = [b["callback_data"] for m in mandati if m.get("reply_markup")
            for riga in m["reply_markup"]["inline_keyboard"] for b in riga]
    assert "cmdok:7" in dati
    testi = " ".join(str(m.get("text")) for m in mandati)
    assert "aggiornato lead" in testi and "vietato" in testi


def test_il_prefisso_esclamativo_resta_comando_secco(monkeypatch):
    _telegram(monkeypatch)
    r = Router()
    chat = ChatFinta(EVENTI)
    modo = telegram_chat.gestisci_testo(Platform(chat, Client(), r), "!aggiorna il lead 3")
    assert modo == "comando"
    assert r.ricevuti == [("aggiorna il lead 3", "telegram")]
    assert chat.chiamate == []                        # la chat non è stata coinvolta


def test_senza_prefisso_e_conversazione(monkeypatch):
    _telegram(monkeypatch)
    r = Router()
    modo = telegram_chat.gestisci_testo(Platform(ChatFinta(EVENTI), Client(), r), "come va?")
    assert modo == "conversazione"
    assert r.ricevuti == []


def test_una_chat_che_si_rompe_lo_dice(monkeypatch):
    mandati = _telegram(monkeypatch)

    class Rotta:
        def stream(self, *a, **kw):
            raise RuntimeError("modello giù")
            yield  # pragma: no cover

    telegram_chat.conversa(Platform(Rotta(), Client()), "ciao")
    testi = " ".join(str(m.get("text")) for m in mandati)
    assert "interrotta" in testi and "modello giù" in testi


def test_errore_di_un_agente_riportato(monkeypatch):
    mandati = _telegram(monkeypatch)
    eventi = [{"phase": "error", "agent": "hr", "error": "401 chiave invalida"}]
    telegram_chat.conversa(Platform(ChatFinta(eventi), Client()), "ciao")
    testi = " ".join(str(m.get("text")) for m in mandati)
    assert "hr" in testi and "401" in testi


def test_senza_database_la_chat_funziona_comunque(monkeypatch):
    """Storico e sessione sono un extra: se Supabase non c'è, si parla ugualmente."""
    mandati = _telegram(monkeypatch)
    p = Platform(ChatFinta(EVENTI), None)
    out = telegram_chat.conversa(p, "ciao")
    assert out["turni"] == 1 and out["sessione"] is None
    assert any("fatture" in str(m.get("text")) for m in mandati)
