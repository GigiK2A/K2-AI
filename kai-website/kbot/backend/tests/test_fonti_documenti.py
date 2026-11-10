import io
import pytest
import pytest
from app.lib import fonti_documenti as fd


def _pdf(righe_per_pagina):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=A4)
    for righe in righe_per_pagina:
        y = 780
        for r in righe:
            c.drawString(60, y, r); y -= 20
        c.showPage()
    c.save(); return b.getvalue()


COLL = {"uploaded_files": [{"name": "Riepilogo economico.pdf", "path": "s1/1-Riepilogo.pdf", "extractedText": "x"}]}
D = fd.doc_id(COLL["uploaded_files"][0])
CH = [{"file_name": "Riepilogo economico.pdf", "page_number": 1, "chunk_index": 0, "content": "Pratiche autorizzative 8 x 680 euro totale 5.040 euro"},
      {"file_name": "Riepilogo economico.pdf", "page_number": 2, "chunk_index": 1, "content": "Residuo da liquidare 7.890 euro"}]


def test_verifica_ok_e_pagina_corretta_dal_testo():
    t = f"Errato [[fonte|{D}|1|totale 5.040 euro]] e residuo [[fonte|Riepilogo economico.pdf|1|Residuo da liquidare 7.890 euro]]."
    out = fd.verifica(t, COLL, "s1", CH)
    assert f"[[fonte|{D}|1|totale 5.040 euro|ok]]" in out
    assert f"[[fonte|{D}|2|Residuo da liquidare 7.890 euro|ok]]" in out   # pagina sbagliata del modello → quella vera


def test_testo_inventato_degrada_a_sola_pagina_e_doc_falso_sparisce():
    out = fd.verifica(f"a [[fonte|{D}|1|importo di 9.999 euro]] b [[fonte|ffffffffffff|1|x]] c", COLL, "s1", CH)
    assert f"[[fonte|{D}|1||pag]]" in out and "ffffffffffff" not in out
    assert fd.verifica(f"[[fonte|{D}|9|qualsiasi]]", COLL, "s1", CH) == ""   # pagina inesistente


def test_localizza_riquadro_solo_se_trovato():
    pdf = _pdf([["Riepilogo", "Pratiche autorizzative 8 x 680 euro  5.040"], ["Pagina due", "Residuo 7.890"]])
    r = fd.localizza(pdf, 1, "Pratiche autorizzative 8 x 680")
    assert r["ok"] and r["localizzato"] and 0 < r["riquadri"][0]["x"] < 0.3 and r["immagine"]
    r2 = fd.localizza(pdf, 1, "testo che non esiste")
    assert r2["ok"] and not r2["localizzato"] and r2["riquadri"] == []
    assert fd.localizza(pdf, 7, "x")["ok"] is False
    r3 = fd.localizza(pdf, 2, "Residuo 7.890")
    assert r3["localizzato"]


def test_endpoint_view_isolamento_e_file_mancante(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import upload
    from app.lib.auth import AuthUser, optional_user
    sess = {"id": "s1", "user_id": "u1", "collected_data": COLL}
    monkeypatch.setattr(upload.sessions, "get_session", lambda sid: sess if sid == "s1" else None)
    pdf = _pdf([["Riepilogo", "Totale 5.040 euro"]])
    monkeypatch.setattr(upload, "_bytes_documento", lambda p: pdf if p == "s1/1-Riepilogo.pdf" else None)
    cl = TestClient(app)
    try:
        app.dependency_overrides[optional_user] = lambda: AuthUser(id="u2", email="a@b.it", has_paid=False, raw={})
        assert cl.get(f"/api/kbot/session/s1/documents/{D}/view?pag=1").status_code == 403
        app.dependency_overrides[optional_user] = lambda: AuthUser(id="u1", email="a@b.it", has_paid=False, raw={})
        r = cl.get(f"/api/kbot/session/s1/documents/{D}/view?pag=1&quote=Totale 5.040 euro")
        assert r.status_code == 200 and r.json()["localizzato"] and r.headers["cache-control"] == "no-store"
        assert cl.get("/api/kbot/session/s1/documents/../../etc/passwd/view").status_code in (404, 422)
        assert cl.get("/api/kbot/session/s1/documents/000000000000/view").status_code == 404
        monkeypatch.setattr(upload, "_bytes_documento", lambda p: None)
        assert cl.get(f"/api/kbot/session/s1/documents/{D}/view?pag=1").status_code == 410
    finally:
        app.dependency_overrides.pop(optional_user, None)


def test_pag_semplice_diventa_citazione_solo_se_il_dato_e_nella_pagina():
    t = "Le pratiche costano 5.040 euro pag. 1, il residuo è 7.890 euro (pag. 2), un dato inventato 123.456 euro (pag. 2)."
    out = fd.verifica(t, COLL, "s1", CH)
    assert f"[[fonte|{D}|1|5.040|ok]]" in out
    assert f"[[fonte|{D}|2|7.890|ok]]" in out
    assert f"[[fonte|{D}|2||pag]]" in out and "123.456 euro [[fonte|" in out    # numero assente dalla pagina: nessun evidenziato inventato


def test_nessun_collegamento_senza_pagine_note_o_senza_allegati():
    assert fd.verifica("costa 5 euro (pag. 3)", {}, "s1", CH) == "costa 5 euro (pag. 3)"
    assert fd.verifica("costa 5.040 euro (pag. 9)", COLL, "s1", CH) == "costa 5.040 euro (pag. 9)"


def test_pagine_dal_pdf_originale_quando_non_ci_sono_chunk(monkeypatch):
    """Documento aperto da un fascicolo, senza chunk con pagine: la citazione prende la pagina vera dal PDF."""
    from app.api import upload
    pdf = _pdf([["Intestazione commessa"], ["Residuo da liquidare 7.890,00 euro"]])
    monkeypatch.setattr(upload, "_bytes_documento", lambda p: pdf if p == "old/r.pdf" else None)
    fd._PDF_PAGINE.clear()
    col = {"uploaded_files": [{"name": "Riepilogo.pdf", "path": "old/r.pdf", "extractedText": "x", "dalFascicolo": "f1"}]}
    d = fd.doc_id(col["uploaded_files"][0])
    out = fd.verifica(f"Residuo [[fonte|{d}|1|Residuo da liquidare 7.890,00 euro]].", col, "s9", [])
    assert f"[[fonte|{d}|2|Residuo da liquidare 7.890,00 euro|ok]]" in out


# ── Test 27D: «Evidenziazione esatta non disponibile» sul residuo di 8.850 € ───────────────────────────────
RIGHE_REALI = [
    "RIEPILOGO ECONOMICO DI COMMESSA", "Commessa UM-26-041 | Adeguamento siti tecnici", "TOTALE IMPONIBILE € 15.250,00",
    "• Delle 8 pratiche autorizzative valorizzate, 6 risultano protocollate; per le altre 2 è indicato lo stato «in attesa di",
    "protocollo».",
    "• Accordo commerciale, estratto: «Il corrispettivo relativo alle pratiche autorizzative matura alla data di deposito e",
    "acquisizione del numero di protocollo».",
    "• Acconto ricevuto il 15/10/2026: € 6.400,00.",
    "• Residuo da incassare riportato nel documento: € 8.850,00.",
    "• Valori esposti al netto dell’IVA. L’IVA non è compresa in questo riepilogo.",
]


@pytest.mark.parametrize("quote", [
    "Residuo da incassare riportato nel documento: € 8.850,00",          # il marcatore salvato dal Test 27D (senza il punto finale)
    "Residuo da incassare riportato nel documento: € 8.850,00.",         # con il punto
    "8.850,00",
    "Acconto ricevuto il 15/10/2026: € 6.400,00",
    "Il corrispettivo relativo alle pratiche autorizzative matura alla data di deposito e acquisizione del numero di protocollo",   # su due righe
    "in attesa di protocollo",                                            # a cavallo di due righe, con la «»
])
def test_passaggi_del_riepilogo_si_verificano_e_si_evidenziano_con_la_stessa_regola(quote):
    pdf = _pdf([RIGHE_REALI])
    testo = "\n".join(RIGHE_REALI)
    assert fd.contiene(testo, quote)                                       # la verifica dice «ok»…
    r = fd.localizza(pdf, 1, quote)
    assert r["ok"] and r["localizzato"] and r["riquadri"], quote           # …e quindi il visualizzatore DEVE poter evidenziare
    assert all(0 <= q["x"] <= 1 and 0 < q["w"] <= 1 and 0 <= q["y"] <= 1 for q in r["riquadri"])


def test_il_testo_non_presente_non_viene_ne_verificato_ne_evidenziato():
    pdf = _pdf([RIGHE_REALI])
    assert not fd.contiene("\n".join(RIGHE_REALI), "Residuo da incassare 9.250,00")
    assert not fd.localizza(pdf, 1, "Residuo da incassare riportato nel documento: € 9.250,00")["localizzato"]


def test_verifica_e_localizza_non_possono_discordare_su_punteggiatura_e_simboli():
    """Proprietà: tutto ciò che `verifica` marca ok su un PDF si evidenzia (stesso confronto a token)."""
    pdf = _pdf([RIGHE_REALI])
    testo = "\n".join(RIGHE_REALI)
    for quote in ["€ 8.850,00", "euro 8.850,00", "“Residuo da incassare”", "(8.850,00)", "6.400,00.", "L’IVA non è compresa"]:
        if fd.contiene(testo, quote):
            assert fd.localizza(pdf, 1, quote)["localizzato"], quote


def test_riquadro_allineato_alla_pagina_disegnata_anche_con_glifi_a_larghezza_nulla():
    """Replica del collaudo: pdfminer misura «€» con larghezza 0 e sfasa le parole di ~5 pt; il riquadro deve seguire il motore di resa (pdfium)."""
    import pypdfium2 as pdfium
    pdf = _pdf([RIGHE_REALI])
    r = fd.localizza(pdf, 1, "Residuo da incassare riportato nel documento: € 8.850,00")
    box = r["riquadri"][0]
    doc = pdfium.PdfDocument(pdf); pag = doc[0]; tp = pag.get_textpage(); n = tp.count_chars(); t = tp.get_text_range(0, n)
    a = t.index("Residuo"); b = t.index("8.850,00") + 8
    l = tp.get_charbox(a, loose=False)[0]; rr = tp.get_charbox(b - 1, loose=False)[2]; W = pag.get_width()
    assert abs(box["x"] * W - l) <= 2.5 and abs((box["x"] + box["w"]) * W - rr) <= 5.5     # +punto finale della parola; prima: sfasato di 5-8 pt e tagliato
    tp.close(); pag.close(); doc.close()
