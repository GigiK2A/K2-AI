"""Lo stato del loop deve sopravvivere al riavvio.

Il 19 ago 2026 il servizio è ripartito tre volte e tre volte sono tornate le stesse otto
card: `seen` e `seen_mail` erano variabili Python. Uno stato che non sopravvive al
riavvio non è stato, è una cache.
"""
import autonomy_loop
from aios.notify import telegram
from aios.stato_loop import CATEGORIA, LIMITE_ID, StatoLoop


class Client:
    """shared_memory finta, con lo stesso contratto di SupabaseREST."""

    def __init__(self):
        self.righe: dict[str, dict] = {}
        self.scritture = 0

    def select(self, table, params):
        assert table == "shared_memory"
        chiave = params.get("key", "").replace("eq.", "")
        r = self.righe.get(chiave)
        return [r] if r else []

    def insert(self, table, row):
        self.scritture += 1
        self.righe[row["key"]] = dict(row)
        return [dict(row)]

    def update(self, table, filters, patch):
        self.scritture += 1
        chiave = filters.get("key", "").replace("eq.", "")
        if chiave not in self.righe:
            return []
        self.righe[chiave].update(patch)
        return [dict(self.righe[chiave])]


def test_gli_id_visti_sopravvivono_al_riavvio():
    c = Client()
    StatoLoop(c).segna_visto("decisioni", [11, 12, 13])
    # nuovo processo, stesso database
    assert StatoLoop(c).visti("decisioni") == {11, 12, 13}


def test_gli_id_si_accumulano_senza_perdere_i_vecchi():
    c = Client()
    s = StatoLoop(c)
    s.segna_visto("decisioni", [1])
    s.segna_visto("decisioni", [2])
    assert StatoLoop(c).visti("decisioni") == {1, 2}


def test_i_marcatori_di_giornata_sopravvivono():
    c = Client()
    StatoLoop(c).segna_giorno("prospect", 231)
    assert StatoLoop(c).giorno("prospect") == 231
    assert StatoLoop(c).giorno("mai_scritto") is None


def test_categoria_scritta_per_ritrovarli():
    c = Client()
    StatoLoop(c).segna_visto("bozze_email", ["d1"])
    assert list(c.righe.values())[0]["category"] == CATEGORIA


def test_insieme_non_cresce_all_infinito():
    c = Client()
    StatoLoop(c).segna_visto("decisioni", list(range(LIMITE_ID + 50)))
    assert len(StatoLoop(c).visti("decisioni")) == LIMITE_ID


def test_senza_database_il_loop_continua_in_memoria():
    s = StatoLoop(None)
    s.segna_visto("decisioni", [1, 2])
    assert s.visti("decisioni") == {1, 2}      # in RAM, ma non solleva


def test_database_rotto_non_ferma_il_loop():
    class Rotto:
        def select(self, *a, **k):
            raise RuntimeError("giù")

        def insert(self, *a, **k):
            raise RuntimeError("giù")

        def update(self, *a, **k):
            raise RuntimeError("giù")

    s = StatoLoop(Rotto())
    s.segna_visto("decisioni", [1])            # non solleva
    assert s.visti("decisioni") == {1}


# ---- integrazione col loop ----
class Conv:
    def bozze_in_attesa(self, limit=20):
        return [{"id": "d1", "to_email": "a@b.it", "subject": "s", "body": "b"}]


class Platform:
    def __init__(self):
        self.conversations = Conv()


def test_le_bozze_notificate_finiscono_nello_stato(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(telegram, "_post", lambda m, p, timeout=35: {})
    c = Client()
    stato = StatoLoop(c)
    assert autonomy_loop._notify_new_email_drafts(Platform(), set(), stato) == 1
    # nuovo processo: la bozza non torna
    assert autonomy_loop._notify_new_email_drafts(
        Platform(), StatoLoop(c).visti("bozze_email"), StatoLoop(c)) == 0
