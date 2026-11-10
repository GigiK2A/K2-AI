"""Artefatti nei testi e nei PDF esportati (collaudo del 10/11/2026): CSS visibile in cima al documento, entità come &#x27; / &nbsp; / &egrave;
mostrate alla lettera. Cause verificate in `_html_to_pdf_bytes` (toglieva solo i tag <html>/<head>/<title> ma non il CONTENUTO di <style> né
di <title>; le entità diverse da amp/lt/gt/quot/#n restavano «&amp;egrave;» e una entità già «escapata» si vedeva doppia). Si ripara nel
codice, senza istruzioni al modello e senza toccare i caratteri legittimi."""
import io

import pytest

from app.lib import testo_pulito as T

pdfminer = pytest.importorskip("pdfminer.high_level")


def _pdf(html):
    from app.lib.pdf_renderer import _html_to_pdf_bytes
    return " ".join(pdfminer.extract_text(io.BytesIO(_html_to_pdf_bytes(html))).split())


def _doc(corpo, titolo="T"):
    return f"<html><head><meta charset='utf-8'><title>{titolo}</title><style>p {{ color: red; }} @page {{ size: A4 }}</style></head><body>{corpo}</body></html>"


# ── PDF: niente CSS, niente titolo ripetuto, entità decodificate ───────────────────────────────────────
def test_il_pdf_non_contiene_il_css():
    t = _pdf(_doc("<h1>Titolo</h1><p>Testo del documento.</p>"))
    assert "@page" not in t and "color" not in t and "size: A4" not in t and "Testo del documento." in t


def test_il_titolo_del_tag_title_non_si_stampa_nel_corpo():
    t = _pdf(_doc("<p>Corpo</p>", titolo="TITOLO-NASCOSTO"))
    assert "TITOLO-NASCOSTO" not in t and "Corpo" in t


@pytest.mark.parametrize("html,atteso", [
    ("l&#x27;art. 113", "l'art. 113"),
    ("l&amp;#x27;art. 113", "l'art. 113"),            # già «escapata» una volta
    ("&quot;citato&quot;", '"citato"'),
    ("&egrave; &euro; 5 &rsquo;", "è € 5 ’"),
    ("5 &amp; 6", "5 & 6"),
    ("a&nbsp;b", "a b"),
])
def test_le_entita_si_vedono_decodificate_nel_pdf(html, atteso):
    assert atteso in _pdf(_doc(f"<p>{html}</p>"))


def test_il_pdf_esportato_da_un_messaggio_non_ha_css_ne_entita():
    from app.api import export as E
    md = "# Oggetto: l'art. 113\n\nL'azienda ha pagato 1.700 € e \"più\" di 5 & 6; è < 7.\n\n- primo\n- secondo **grassetto** &nbsp; fine &egrave;"
    t = _pdf(E._wrap_html_documento(md, "Documento d'esempio"))
    for brutto in ("@page", "&#x27;", "&nbsp;", "&egrave;", "&amp;", "color:"):
        assert brutto not in t, (brutto, t[:300])
    assert "1.700 €" in t and "è < 7" in t and "l'art. 113" in t


# ── testo: chat, documento, docx ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("sporco,pulito", [
    ("l&#x27;azienda &nbsp;paga &egrave; &euro; 5", "l'azienda paga è € 5"),
    ("l&amp;#x27;azienda", "l'azienda"),
    ("<style>p{color:red}</style>Testo<br>riga due<div>blocco</div>", "Testo\nriga due\nblocco"),
    ("<span class=\"x\">dentro</span> il testo", "dentro il testo"),
    ("perchÃ© â‚¬ 5", "perché € 5"),                    # codifica doppia (UTF-8 letto come Latin-1)
    ("caff\\u00e8 e perch\\u00e9", "caffè e perché"),                         # escape unicode non interpretati
    ("a​b﻿c d", "abc d"),                                    # invisibili e nbsp
    ("testo�rotto", "testorotto"),
])
def test_pulisci_toglie_gli_artefatti(sporco, pulito):
    assert T.pulisci(sporco) == pulito


@pytest.mark.parametrize("ok", [
    "Lettere accentate: è é à ò ù ì, perché, più, già.",
    "Apostrofi e virgolette: l'azienda, “virgolette” ‘apici’ «caporali» \"dritte\".",
    "Valute e segni: € 1.700,50 · 5 % · ≥ 3 · ≤ 4 · ± 2 · × · ÷ · — – … ° §",
    "Confronti: se x < 7 e y > 3, oppure 5 < 6 > 4 e a<b",
    "Riferimenti: art. 113, comma 2, D.Lgs. 81/2008; L. 198/2025; c.c. art. 2087 ¶ 3",
    "Elenco:\n1. primo\n2. secondo\n- punto\n* punto\n\n| a | b |\n|---|---|\n| 1 | 2 |",
    "Marcatori del documento: <<<DOCUMENTO: Lettera>>> testo <<<FINE DOCUMENTO>>>",
    "AT&T e Johnson & Johnson non sono entità",
])
def test_i_caratteri_legittimi_restano_intatti(ok):
    assert T.pulisci(ok) == ok


def test_il_codice_non_si_tocca():
    t = "Esempio:\n```html\n<div>&nbsp;&#x27;</div>\n```\nfine &nbsp;testo"
    assert "<div>&nbsp;&#x27;</div>" in T.pulisci(t) and T.pulisci(t).endswith("fine  testo".replace("  ", " "))


def test_idempotente():
    s = "l&amp;#x27;azienda <b>paga</b> &egrave; Ã¨"
    assert T.pulisci(T.pulisci(s)) == T.pulisci(s)


def test_esportazione_docx_usa_testo_pulito():
    from docx import Document
    from app.api import export as E
    d = Document()
    E._markdown_to_docx(d, "# L&#x27;oggetto\n\nL&amp;#x27;azienda &nbsp;&egrave; qui\n\n- punto &euro; 5")
    testo = "\n".join(p.text for p in d.paragraphs)
    assert "&" not in testo and "L'oggetto" in testo and "è qui" in testo and "€ 5" in testo
