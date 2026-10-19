"""Se si chiede una bozza e la risposta non la contiene, seconda chiamata esplicita (19/10/2026)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from app.lib import verifica_bozze as V

LETTERA = ("Oggetto: diffida ad adempiere – fattura n. 2026/0417\n\nSpett.le Gamma Servizi S.r.l.,\n[indirizzo PEC del destinatario]\n\n"
           "Con la presente Vi intimiamo il pagamento di euro 2.013,00 entro [termine in giorni] giorni, oltre agli interessi di mora.\n\n"
           "Distinti saluti,\n[tuo nome e ruolo]")
DOMANDA = "Per scrivere una diffida efficace, mi serve una cosa: chi sei? Sei un'impresa o un privato?"
RICHIESTA = "Scrivimi una lettera di diffida per un cliente che non paga la fattura 2026/0417 di 2.013 euro."


class _Blocco:
    type = "text"

    def __init__(self, t):
        self.text = t


class _Client:
    def __init__(self, risposte, errore=None):
        self.risposte, self.errore, self.chiamate = list(risposte), errore, []
        self.messages = self

    def create(self, **kw):
        self.chiamate.append(kw)
        if self.errore:
            raise self.errore
        return type("R", (), {"content": [_Blocco(self.risposte.pop(0))]})()


@pytest.mark.parametrize("t", ["Scrivimi una lettera di diffida", "Prepara una mail di sollecito al cliente", "Redigi una disdetta del contratto",
                               "Stendimi una PEC di contestazione", "fammi una bozza di risposta al reclamo"])
def test_riconosce_la_richiesta_di_una_bozza(t):
    assert V.richiesta_bozza(t)


@pytest.mark.parametrize("t", ["Come funziona una lettera di diffida?", "Cos'è una PEC?", "Quanto costa un avvocato?"])
def test_non_scambia_una_domanda_per_una_richiesta(t):
    assert not V.richiesta_bozza(t)


def test_contiene_bozza():
    assert V.contiene_bozza(LETTERA)
    assert V.contiene_bozza("Buongiorno [nome],\nti scrivo per sollecitare il pagamento della fattura.\nCordiali saluti,\n[firma]")
    assert not V.contiene_bozza(DOMANDA)
    assert not V.contiene_bozza("Prima di scrivere serve capire se Gamma ha già contestato la fattura. Me lo dici?")
    assert not V.contiene_bozza("")


def test_domanda_al_posto_della_bozza_seconda_chiamata():
    c = _Client([LETTERA])
    out = V.assicura(c, "m", "SISTEMA", [{"role": "user", "content": RICHIESTA}], DOMANDA, RICHIESTA)
    assert out == LETTERA and len(c.chiamate) == 1
    ch = c.chiamate[0]
    assert "BOZZA DI DOCUMENTO RICHIESTA" in ch["system"] and ch["system"].startswith("SISTEMA")
    assert ch["messages"][-1]["content"] == V.ISTRUZIONE and ch["messages"][-2] == {"role": "assistant", "content": DOMANDA}
    assert ch["messages"][0]["content"] == RICHIESTA


def test_se_la_bozza_c_e_gia_nessuna_chiamata():
    c = _Client([])
    assert V.assicura(c, "m", "S", [], LETTERA, RICHIESTA) == LETTERA and c.chiamate == []


def test_se_non_era_richiesta_nessuna_chiamata():
    c = _Client([])
    assert V.assicura(c, "m", "S", [], DOMANDA, "Come funziona la diffida?") == DOMANDA and c.chiamate == []


def test_se_anche_la_seconda_manca_resta_la_prima():
    c = _Client(["Ho bisogno di un altro dato prima di scrivere."])
    assert V.assicura(c, "m", "S", [], DOMANDA, RICHIESTA) == DOMANDA and len(c.chiamate) == 1


def test_errore_della_seconda_chiamata_fail_open():
    c = _Client([], errore=RuntimeError("giù"))
    assert V.assicura(c, "m", "S", [], DOMANDA, RICHIESTA) == DOMANDA


def test_interruttore(monkeypatch):
    monkeypatch.setenv("KBOT_VERIFICA_BOZZE", "0")
    c = _Client([LETTERA])
    assert V.assicura(c, "m", "S", [], DOMANDA, RICHIESTA) == DOMANDA and c.chiamate == []


def test_end_to_end_dalla_chat_la_domanda_diventa_la_bozza(monkeypatch):
    from test_e2e_scenarios import FakeAnthropic, _FakeMessages, _FakeResp, _make_session, _chiamate_chat  # noqa
    from fastapi.testclient import TestClient
    from app.lib.limiter import limiter
    import test_e2e_scenarios as E

    seq = [DOMANDA, LETTERA]                         # prima risposta: domanda; seconda chiamata: la lettera

    def create(self, **kw):
        self.capture.append(kw)
        sistema = str(kw.get("system", ""))
        if sistema.startswith(("Estrai dal MESSAGGIO", "Sei un indicizzatore")):      # scheda del cliente, proposta fonti
            return _FakeResp("{}")
        return _FakeResp(seq.pop(0) if seq else LETTERA)

    monkeypatch.setattr(_FakeMessages, "create", create)
    # fixture a mano (non si possono usare le fixture di un altro modulo dentro un test che le modifica)
    from test_e2e_scenarios import FakeSupabase
    fake = FakeSupabase()
    for modulo in ("app.lib.supabase_admin", "app.lib.sessions", "app.api.upload", "app.lib.storage"):
        monkeypatch.setattr(f"{modulo}.get_admin_client", lambda: fake)
    import anthropic
    FakeAnthropic.captured_calls = []
    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    monkeypatch.setattr("app.api.message.anthropic.Anthropic", FakeAnthropic)
    from app.main import app
    limiter.reset()
    client = TestClient(app)
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid, "message": RICHIESTA})
    m = r.json()["message"]
    assert "Spett.le Gamma Servizi" in m and "Distinti saluti" in m and "chi sei?" not in m
    ultimi = [str(c["messages"][-1]["content"])[:60] for c in FakeAnthropic.captured_calls]
    assert any(V.ISTRUZIONE == (c["messages"][-1]["content"]) for c in FakeAnthropic.captured_calls), ultimi


# ── quality gate: la lettera chiesta dall'utente non viene sostituita da consigli di cautela ─────────────────
def _gate_client(verdetto: dict):
    import json as _json

    class _C:
        def __init__(self):
            self.chiamate = []
            self.messages = self

        def create(self, **kw):
            self.chiamate.append(kw)
            return type("R", (), {"content": [_Blocco(_json.dumps(verdetto))]})()
    return _C()


LETTERA_DIFFIDA = LETTERA + "\nIn mancanza procederemo in sede giudiziale. Invio via PEC."
VERDETTO = {"premature_summary": False, "assertive_diagnosis": False, "drastic_actions": True,
            "depth_mismatch": False, "rewrite": "Ti consiglio di non inviare nulla prima di aver verificato i fatti."}


def test_il_gate_non_sostituisce_la_bozza_richiesta():
    from app.lib import quality_gate as qg
    msgs = [{"role": "user", "content": RICHIESTA}]
    c = _gate_client(VERDETTO)
    assert qg.review(c, "m", msgs, LETTERA_DIFFIDA, bozza_richiesta=True) == LETTERA_DIFFIDA
    # senza la richiesta di una bozza il gate funziona come prima
    c2 = _gate_client(VERDETTO)
    assert qg.review(c2, "m", msgs, LETTERA_DIFFIDA, bozza_richiesta=False).startswith("Ti consiglio di non inviare nulla")


def test_il_gate_continua_a_fermare_le_altre_violazioni_anche_con_la_bozza():
    from app.lib import quality_gate as qg
    v = dict(VERDETTO, drastic_actions=False, assertive_diagnosis=True, rewrite="Versione prudente senza diagnosi.")
    out = qg.review(_gate_client(v), "m", [{"role": "user", "content": RICHIESTA}], LETTERA_DIFFIDA, bozza_richiesta=True)
    assert out.startswith("Versione prudente")


def test_interruttore_del_gate_per_le_bozze(monkeypatch):
    from app.lib import quality_gate as qg
    monkeypatch.setenv("KBOT_GATE_BOZZE", "0")
    out = qg.review(_gate_client(VERDETTO), "m", [{"role": "user", "content": RICHIESTA}], LETTERA_DIFFIDA, bozza_richiesta=True)
    assert out.startswith("Ti consiglio di non inviare nulla")
