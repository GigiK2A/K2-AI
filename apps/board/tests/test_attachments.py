"""Allegati chat: estrazione testo (Office/CSV/txt) e blocchi nativi (immagini/PDF)."""
import base64

from aios.attachments import extract_text
from aios.api.app import _process_attachments


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def test_extract_csv_and_txt():
    csv_txt = extract_text("dati.csv", "text/csv", _b64("a,b\n1,2"))
    assert "a,b" in csv_txt and "1,2" in csv_txt
    plain = extract_text("note.txt", "text/plain", _b64("ciao mondo"))
    assert "ciao mondo" in plain


def test_extract_unknown_returns_empty():
    assert extract_text("x.bin", "application/octet-stream", _b64("boh")) == ""


def test_process_image_becomes_native_block():
    atts = [{"name": "foto.png", "media_type": "image/png", "data": "AAAA"}]
    media, doc_text, names = _process_attachments(atts)
    assert len(media) == 1 and media[0]["type"] == "image"
    assert media[0]["source"]["media_type"] == "image/png"
    assert names == ["foto.png"] and doc_text == ""


def test_process_pdf_becomes_document_block():
    media, _dt, _n = _process_attachments(
        [{"name": "bilancio.pdf", "media_type": "application/pdf", "data": "JVBER"}])
    assert media and media[0]["type"] == "document"
    assert media[0]["source"]["media_type"] == "application/pdf"


def test_process_office_becomes_text_not_media():
    media, doc_text, names = _process_attachments(
        [{"name": "dati.csv", "media_type": "text/csv", "data": _b64("x,y\n3,4")}])
    assert media == []                       # niente blocco media
    assert "ALLEGATI" in doc_text and "3,4" in doc_text and names == ["dati.csv"]


def test_process_empty():
    assert _process_attachments(None) == ([], "", [])
