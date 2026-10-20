"""Stream: fasi reali, tempi per fase, documento separato, fonti in parallelo (audit del 20/10/2026)."""
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from test_e2e_scenarios import (FakeAnthropic, _chiamate_chat, _make_session, client, fake_anthropic, fake_db)  # noqa: F401
from app.lib import documento as D


def _sse(r):
    return [json.loads(riga[5:].strip()) for riga in r.text.splitlines() if riga.startswith("data:")]


PEC = ("Ecco la PEC.\n\n<<<DOCUMENTO: PEC di contestazione>>>\nOggetto: contestazione fattura n. [numero]\n\n"
       "Spett.le DemoSoft S.r.l., contestiamo le difformità del gestionale rispetto al contratto firmato il [data].\n\n"
       "Distinti saluti\n<<<FINE DOCUMENTO>>>\n\nVerifica: numero e data della fattura.")


def test_le_fasi_arrivano_nell_ordine_reale_e_il_done_porta_i_tempi(client, fake_anthropic):
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Come funziona il TFR?"}))
    fasi = [e["fase"] for e in ev if "fase" in e]
    assert fasi == ["fonti", "generazione", "verifica"]
    done = ev[-1]
    assert done["done"] and done["timing"]["chiamate_llm"] >= 1
    for k in ("preparazione_s", "fonti_s", "primo_token_s", "generazione_s", "verifica_s", "salvataggio_s", "totale_s"):
        assert done["timing"][k] is not None and done["timing"][k] >= 0, k
    # l'ordine dei delta rispetto alle fasi: «generazione» prima del primo testo, «verifica» dopo l'ultimo
    idx = {json.dumps(e, sort_keys=True): i for i, e in enumerate(ev)}
    primo_delta = next(i for i, e in enumerate(ev) if "delta" in e)
    ultimo_delta = max(i for i, e in enumerate(ev) if "delta" in e)
    assert ev.index({"fase": "generazione"}) < primo_delta and ev.index({"fase": "verifica"}) > ultimo_delta


def test_il_documento_resta_separato_nello_stream_e_nel_messaggio_salvato(client, fake_anthropic):
    FakeAnthropic.canned_text = PEC
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Scrivimi una PEC per contestare il software difettoso"}))
    mostrato = "".join(e.get("delta", "") for e in ev)
    finale = ev[-1]["message"]
    for t in (mostrato, finale):
        b = D.estrai(t)
        assert len(b) == 1 and b[0]["completo"] and "Spett.le DemoSoft" in b[0]["testo"]
    assert "Verifica: numero e data" in D.fuori_dal_documento(finale)
    assert ev[-1]["summary"] is None and ev[-1]["nextAction"] == "continue"       # nessun generatore di report


def test_fonti_e_norme_partono_in_parallelo(client, fake_anthropic, monkeypatch):
    from app.api import message as M
    ritardo = 0.4

    def lenta_ricerca(*_a, **_k):
        time.sleep(ritardo)
        return ""

    async def lenta_norme(*_a, **_k):
        await asyncio.sleep(ritardo)
        return None

    monkeypatch.setattr(M.fact_grounding, "ground_block", lenta_ricerca)
    monkeypatch.setattr(M, "_pacchetto_norme", lenta_norme)
    sid = _make_session(client)
    ev = _sse(client.post("/api/kbot/message/stream", json={"session_id": sid, "message": "Come funziona il TFR?"}))
    fonti_s = ev[-1]["timing"]["fonti_s"]
    assert fonti_s < ritardo * 1.6, f"fonti_s={fonti_s}: in sequenza sarebbero ≥ {2 * ritardo}"
    assert fonti_s >= ritardo * 0.9
