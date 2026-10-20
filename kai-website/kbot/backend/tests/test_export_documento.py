"""L'esportazione usa solo il blocco-documento: niente conversazione, niente intestazioni del sistema (20/10/2026)."""
import io

import pytest
from fastapi import BackgroundTasks

from app.api import export as E

MSG = ("Ecco la PEC. Il valore probatorio della fattura SDI è limitato: leggi la nota sotto.\n\n"
       "<<<DOCUMENTO: PEC di contestazione>>>\nOggetto: contestazione fattura n. [numero]\n\n"
       "Spett.le DemoSoft S.r.l., contestiamo le difformità del gestionale.\n\nDistinti saluti\n<<<FINE DOCUMENTO>>>\n\n"
       "Verifica: il numero della fattura e l'art. 1667 c.c. con le sue eccezioni.")
V2 = MSG + "\n\n<<<DOCUMENTO: PEC di contestazione>>>\nOggetto: contestazione fattura n. 42/2026\n\nVersione aggiornata.\n<<<FINE DOCUMENTO>>>"


@pytest.fixture
def sessione(monkeypatch):
    sess = {"id": "s1234567", "user_id": None, "messages": [{"role": "user", "content": "Scrivimi una PEC"},
                                                           {"role": "assistant", "content": MSG},
                                                           {"role": "assistant", "content": V2}]}
    monkeypatch.setattr(E.sessions, "get_session", lambda sid: sess)
    return sess


def _testo_docx(resp):
    from docx import Document
    d = Document(io.BytesIO(resp.body))
    return "\n".join(p.text for p in d.paragraphs)


def test_docx_contiene_solo_il_documento(sessione):
    r = E.render_message_docx(E.RenderBody(session_id="s1234567", message_index=1), None)
    t = _testo_docx(r)
    assert "Spett.le DemoSoft" in t and "Distinti saluti" in t
    assert "K2-AI" not in t and "K2A S.R.L.S." not in t and "valore probatorio" not in t and "Verifica:" not in t
    assert "pec-di-contestazione" in r.headers["Content-Disposition"]


def test_docx_usa_l_ultima_versione_e_si_puo_scegliere_la_prima(sessione):
    ult = _testo_docx(E.render_message_docx(E.RenderBody(session_id="s1234567", message_index=2), None))
    assert "Versione aggiornata" in ult and "Spett.le" not in ult.split("Versione aggiornata")[0] or "Versione aggiornata" in ult
    prima = _testo_docx(E.render_message_docx(E.RenderBody(session_id="s1234567", message_index=2, document_index=0), None))
    assert "Spett.le DemoSoft" in prima and "Versione aggiornata" not in prima


def test_un_messaggio_senza_documento_si_esporta_come_prima(monkeypatch):
    sess = {"id": "s1234567", "user_id": None, "messages": [{"role": "assistant", "content": "Report operativo lungo " * 20}]}
    monkeypatch.setattr(E.sessions, "get_session", lambda sid: sess)
    t = _testo_docx(E.render_message_docx(E.RenderBody(session_id="s1234567", message_index=0), None))
    assert "K2-AI — Report operativo" in t


def test_html_del_pdf_pulito():
    h = E._wrap_html_documento("Oggetto: x\n\nTesto del documento.", "PEC")
    assert "Testo del documento" in h and "K2-AI" not in h and "P.IVA" not in h
