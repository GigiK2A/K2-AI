"""Generatore relazione di calcolo DOCX asseverabile — auto-genera dossier dai calcoli MCP."""
from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel, Field


class SezioneCalcolo(BaseModel):
    titolo: str
    norma_riferimento: str
    descrizione: str
    parametri: dict
    risultati: dict
    esito_conforme: bool | None = None
    note: str = ""


class RelazioneDocxInput(BaseModel):
    progetto: str
    committente: str
    impianto: str
    progettista: str = ""
    data: str = "2026-05-18"
    sezioni: list[SezioneCalcolo]
    output_path: str


class RelazioneDocxOutput(BaseModel):
    file: str
    n_sezioni: int
    n_conformi: int
    n_non_conformi: int
    n_neutre: int


def genera_relazione_docx(inp: RelazioneDocxInput) -> RelazioneDocxOutput:
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as e:
        raise RuntimeError(f"python-docx mancante: {e}. Esegui: uv sync") from e

    doc = Document()
    # Stile base
    s = doc.styles["Normal"]
    s.font.name = "Calibri"
    s.font.size = Pt(11)

    # Frontespizio
    title = doc.add_heading("Relazione di calcolo impianto elettrico", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    info_tbl = doc.add_table(rows=5, cols=2)
    info_tbl.style = "Light Grid Accent 1"
    info_data = [
        ("Progetto", inp.progetto),
        ("Committente", inp.committente),
        ("Impianto", inp.impianto),
        ("Progettista", inp.progettista or "—"),
        ("Data", inp.data),
    ]
    for i, (k, v) in enumerate(info_data):
        info_tbl.cell(i, 0).text = k
        info_tbl.cell(i, 1).text = v
        info_tbl.cell(i, 0).paragraphs[0].runs[0].bold = True

    doc.add_page_break()

    # Indice (semplificato)
    doc.add_heading("Indice", level=1)
    for i, sez in enumerate(inp.sezioni, 1):
        p = doc.add_paragraph(f"{i}. {sez.titolo}")
        p.paragraph_format.left_indent = Cm(0.5)
    doc.add_page_break()

    # Premessa
    doc.add_heading("1. Premessa normativa", level=1)
    doc.add_paragraph(
        "La presente relazione di calcolo è redatta in conformità alle norme tecniche vigenti:\n"
        "• CEI 64-8 (Impianti utilizzatori a tensione nominale non superiore a 1000 V in c.a.)\n"
        "• CEI-UNEL 35024/1 (Portate dei cavi)\n"
        "• CEI 64-12 (Guida impianti di terra)\n"
        "• CEI 11-27 / IEC 60909 (Calcolo correnti di corto circuito)\n"
        "• CEI EN 62305-2/-3 (Protezione contro i fulmini)\n"
        "• CEI 0-21 (Connessione utenti attivi BT)\n"
        "• DPR 462/2001 (Denuncia impianti di terra e LPS)\n"
        "Tutti i calcoli sono tracciabili via MCP k2a-elettrico v0.3."
    )

    # Sezioni
    n_ok, n_ko, n_neutre = 0, 0, 0
    for idx, sez in enumerate(inp.sezioni, 2):
        doc.add_heading(f"{idx}. {sez.titolo}", level=1)
        doc.add_paragraph(f"Norma di riferimento: {sez.norma_riferimento}").runs[0].italic = True
        if sez.descrizione:
            doc.add_paragraph(sez.descrizione)

        # Tabella parametri
        if sez.parametri:
            doc.add_heading("Dati di ingresso", level=2)
            t = doc.add_table(rows=len(sez.parametri), cols=2)
            t.style = "Light List Accent 1"
            for i, (k, v) in enumerate(sez.parametri.items()):
                t.cell(i, 0).text = str(k)
                t.cell(i, 1).text = str(v)
                t.cell(i, 0).paragraphs[0].runs[0].bold = True

        # Tabella risultati
        if sez.risultati:
            doc.add_heading("Risultati", level=2)
            t = doc.add_table(rows=len(sez.risultati), cols=2)
            t.style = "Light List Accent 1"
            for i, (k, v) in enumerate(sez.risultati.items()):
                t.cell(i, 0).text = str(k)
                t.cell(i, 1).text = str(v)
                t.cell(i, 0).paragraphs[0].runs[0].bold = True

        # Esito
        if sez.esito_conforme is True:
            p = doc.add_paragraph()
            r = p.add_run("✅ CONFORME alla normativa applicabile")
            r.bold = True
            r.font.color.rgb = RGBColor(0x00, 0x80, 0x00)
            n_ok += 1
        elif sez.esito_conforme is False:
            p = doc.add_paragraph()
            r = p.add_run("❌ NON CONFORME — richiesto adeguamento")
            r.bold = True
            r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            n_ko += 1
        else:
            n_neutre += 1

        if sez.note:
            doc.add_paragraph(f"Note: {sez.note}").runs[0].italic = True

    # Conclusioni
    doc.add_page_break()
    doc.add_heading(f"{len(inp.sezioni)+2}. Conclusioni", level=1)
    if n_ko == 0:
        doc.add_paragraph(
            f"L'impianto risulta conforme in tutte le {n_ok} verifiche eseguite.\n"
            f"Si attesta la conformità alle norme tecniche di cui al capitolo 1."
        )
    else:
        doc.add_paragraph(
            f"L'impianto presenta {n_ko} non conformità su {len(inp.sezioni)} verifiche.\n"
            f"È richiesto l'adeguamento dei seguenti aspetti prima della messa in servizio."
        )

    # Firma
    doc.add_paragraph()
    doc.add_paragraph()
    p = doc.add_paragraph(f"Data: {inp.data}")
    p = doc.add_paragraph("Il progettista: " + ("_" * 40))

    out = Path(inp.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    return RelazioneDocxOutput(
        file=str(out), n_sezioni=len(inp.sezioni),
        n_conformi=n_ok, n_non_conformi=n_ko, n_neutre=n_neutre,
    )
