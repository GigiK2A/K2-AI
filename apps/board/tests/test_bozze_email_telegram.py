"""Le bozze email devono essere approvabili da Telegram.

Le bozze vivono in `email_messages`, non nella coda approvazioni: le card Telegram
nascevano solo da kernel.approvals.pending() e quindi le mail non comparivano mai.
Risultato in produzione: 105 bozze in uscita, nessuna mai inviata.
"""
import pytest

from aios.conversation import ConversationManager
from aios.notify import telegram


class _ClientFinto:
    """Supabase REST finto: registra le chiamate invece di farle."""

    def __init__(self, righe=None):
        self.righe = righe or []
        self.update_chiamate = []

    def select(self, tabella, params):
        assert tabella == "email_messages"
        self.ultimi_params = params
        return self.righe

    def update(self, tabella, filtri, patch):
        self.update_chiamate.append((tabella, filtri, patch))
        return [{"id": 1}]


def _manager(righe=None):
    client = _ClientFinto(righe)
    m = ConversationManager.__new__(ConversationManager)   # niente LLM/piattaforma
    m.client = client
    return m, client


# ─── lettura bozze ───────────────────────────────────────────────────────────

def test_bozze_in_attesa_filtra_solo_le_uscite_non_inviate():
    m, client = _manager([{"id": 1, "subject": "ciao"}])
    out = m.bozze_in_attesa()
    assert out == [{"id": 1, "subject": "ciao"}]
    # il filtro deve escludere le mail in ingresso e quelle già inviate
    assert client.ultimi_params["direction"] == "eq.out"
    assert client.ultimi_params["status"] == "eq.bozza"


def test_bozze_in_attesa_limita_le_righe():
    m, client = _manager([])
    m.bozze_in_attesa(limit=999)
    assert int(client.ultimi_params["limit"]) <= 50


def test_bozze_in_attesa_degrada_a_lista_vuota():
    """Un errore di rete non deve fermare il loop di autonomia."""
    m, _ = _manager()
    m.client.select = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("rete giù"))
    assert m.bozze_in_attesa() == []


# ─── dispatch dei callback ───────────────────────────────────────────────────

@pytest.fixture
def telegram_attivo(monkeypatch):
    """Attiva il canale e intercetta le chiamate HTTP."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    inviati = []

    def _post_finto(method, payload, timeout=35):
        inviati.append((method, payload))
        if method == "getUpdates":
            return _post_finto.updates
        return {}

    _post_finto.updates = {"result": []}
    monkeypatch.setattr(telegram, "_post", _post_finto)
    return _post_finto, inviati


def _callback(data, chat_id=42, update_id=1):
    return {"result": [{"update_id": update_id,
                        "callback_query": {"id": "cq1", "data": data,
                                           "message": {"chat": {"id": chat_id}}}}]}


def test_mailok_invia_la_bozza(telegram_attivo):
    post, _ = telegram_attivo
    post.updates = _callback("mailok:7")
    inviate = []
    telegram.poll_decisions(lambda x: None, lambda x: None,
                            on_email_send=lambda d: inviate.append(d) or "📤 Email inviata.",
                            once=True)
    assert inviate == ["7"]


def test_mailno_scarta_la_bozza(telegram_attivo):
    post, _ = telegram_attivo
    post.updates = _callback("mailno:9")
    scartate = []
    telegram.poll_decisions(lambda x: None, lambda x: None,
                            on_email_discard=lambda d: scartate.append(d) or "🗑 Scartata.",
                            once=True)
    assert scartate == ["9"]


def test_esito_del_gestore_finisce_nel_toast(telegram_attivo):
    """Il toast deve dire cosa è successo, non un 'fatto' fisso."""
    post, inviati = telegram_attivo
    post.updates = _callback("approve:3")
    telegram.poll_decisions(lambda x: "⚠️ Approvato ma NON eseguito — n8n giù",
                            lambda x: None, once=True)
    risposte = [p["text"] for m, p in inviati if m == "answerCallbackQuery"]
    assert risposte == ["⚠️ Approvato ma NON eseguito — n8n giù"]


def test_errore_del_gestore_arriva_all_utente(telegram_attivo):
    post, inviati = telegram_attivo
    post.updates = _callback("approve:3")

    def _esplode(_):
        raise RuntimeError("bozza non trovata")

    telegram.poll_decisions(_esplode, lambda x: None, once=True)
    risposte = [p["text"] for m, p in inviati if m == "answerCallbackQuery"]
    assert "bozza non trovata" in risposte[0]


def test_chat_non_autorizzata_non_esegue(telegram_attivo):
    """Fail-closed: un callback da una chat estranea non deve inviare nulla."""
    post, _ = telegram_attivo
    post.updates = _callback("mailok:7", chat_id=999)
    inviate = []
    telegram.poll_decisions(lambda x: None, lambda x: None,
                            on_email_send=lambda d: inviate.append(d), once=True)
    assert inviate == []


def test_card_bozza_mostra_destinatario_e_avverte_che_e_esterna(telegram_attivo):
    _, inviati = telegram_attivo
    telegram.send_email_draft_card(5, "cliente@example.com", "Preventivo", "Buongiorno…")
    testo = inviati[0][1]["text"]
    assert "cliente@example.com" in testo and "Preventivo" in testo
    assert "ESTERNO" in testo          # niente approvazioni cieche
    bottoni = inviati[0][1]["reply_markup"]["inline_keyboard"][0]
    assert [b["callback_data"] for b in bottoni] == ["mailok:5", "mailno:5"]
