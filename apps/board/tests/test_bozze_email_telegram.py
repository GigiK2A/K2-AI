"""Le bozze email devono essere raggiungibili da Telegram, non solo dal cockpit.

Ad agosto 2026 in `email_messages` c'erano 123 righe `out/bozza`: risposte già scritte
a mail di clienti, ferme perché i bottoni Invia/Scarta esistevano solo nel cockpit web.
L'invio resta un'azione ESTERNA: parte solo su clic dell'owner.
"""
import autonomy_loop
from aios.notify import telegram


class FakeConv:
    def __init__(self, bozze):
        self._b = bozze
        self.inviate, self.scartate = [], []

    def bozze_in_attesa(self, limit=20):
        return self._b

    def send(self, draft_id, actor="cockpit", override=None):
        self.inviate.append((draft_id, actor))
        return {"ok": True}

    def discard(self, draft_id):
        self.scartate.append(draft_id)
        return {"ok": True}


class FakePlatform:
    def __init__(self, conv):
        self.conversations = conv


def _bozza(i):
    return {"id": f"d{i}", "to_email": f"cliente{i}@example.it",
            "subject": f"Risposta {i}", "body": "Buongiorno, ..."}


def test_le_bozze_diventano_card(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    mandate = []
    monkeypatch.setattr(telegram, "_post",
                        lambda m, p, timeout=35: mandate.append(p) or {})
    p = FakePlatform(FakeConv([_bozza(1), _bozza(2)]))
    assert autonomy_loop._notify_new_email_drafts(p, set()) == 2
    testi = " ".join(str(m.get("text")) for m in mandate)
    assert "cliente1@example.it" in testi and "Risposta 2" in testi
    # la card deve dire che l'invio è esterno, per non cliccare alla cieca
    assert "ESTERNO" in testi
    dati = [b["callback_data"] for m in mandate
            for riga in m["reply_markup"]["inline_keyboard"] for b in riga]
    assert "mailok:d1" in dati and "mailno:d1" in dati


def test_una_bozza_non_viene_riproposta_due_volte(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(telegram, "_post", lambda m, p, timeout=35: {})
    p = FakePlatform(FakeConv([_bozza(1)]))
    viste = set()
    assert autonomy_loop._notify_new_email_drafts(p, viste) == 1
    assert autonomy_loop._notify_new_email_drafts(p, viste) == 0


def test_cap_per_tick_anche_sulle_bozze(monkeypatch):
    """123 bozze non possono partire tutte insieme: Telegram le scarterebbe."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(telegram, "_post", lambda m, p, timeout=35: {})
    p = FakePlatform(FakeConv([_bozza(i) for i in range(30)]))
    assert autonomy_loop._notify_new_email_drafts(p, set()) == autonomy_loop.MAX_CARD_PER_TICK


def test_senza_conversazioni_non_fa_niente():
    p = FakePlatform(None)
    assert autonomy_loop._notify_new_email_drafts(p, set()) == 0


def test_il_clic_invia_chiama_il_send(monkeypatch):
    """Il bottone deve arrivare al gestore: prima cadeva in 'Azione sconosciuta'."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    toast, inviate = [], []

    def fake_post(method, payload, timeout=35):
        if method == "getUpdates":
            return {"result": [{"update_id": 1, "callback_query": {
                "id": "cq1", "data": "mailok:d7", "message": {"chat": {"id": 42}}}}]}
        if method == "answerCallbackQuery":
            toast.append(payload["text"])
        return {}

    monkeypatch.setattr(telegram, "_post", fake_post)
    telegram.poll_decisions(lambda a: None, lambda a: None,
                            on_email_send=lambda d: inviate.append(d) or "📤 Email inviata.",
                            once=True)
    assert inviate == ["d7"]
    assert toast == ["📤 Email inviata."]


def test_il_clic_scarta_chiama_il_discard(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    scartate = []

    def fake_post(method, payload, timeout=35):
        if method == "getUpdates":
            return {"result": [{"update_id": 2, "callback_query": {
                "id": "cq2", "data": "mailno:d9", "message": {"chat": {"id": 42}}}}]}
        return {}

    monkeypatch.setattr(telegram, "_post", fake_post)
    telegram.poll_decisions(lambda a: None, lambda a: None,
                            on_email_discard=lambda d: scartate.append(d), once=True)
    assert scartate == ["d9"]


def test_bozze_in_attesa_legge_solo_le_uscenti_mai_inviate():
    from aios.conversation import ConversationManager

    class Client:
        def __init__(self):
            self.params = None

        def select(self, table, params):
            self.params = (table, params)
            return [{"id": "d1"}]

    c = Client()
    conv = ConversationManager.__new__(ConversationManager)
    conv.client = c
    assert conv.bozze_in_attesa() == [{"id": "d1"}]
    tabella, params = c.params
    assert tabella == "email_messages"
    assert params["direction"] == "eq.out" and params["status"] == "eq.bozza"
