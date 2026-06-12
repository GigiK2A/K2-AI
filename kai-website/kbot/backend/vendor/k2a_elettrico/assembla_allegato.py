"""Assembla Allegato H — asseverazione indipendente DOCX da N sezioni di verifica.

Generalizzazione del pattern "Allegato H" (asseverazione indipendente di un PE)
come tool MCP universale, applicabile a qualunque progetto elettrico (civile,
industriale, TLC). Riceve N SezioneAsseverativa (output di qualunque tool di
verifica) e produce un DOCX professionale + JSON strutturato.

DEBITO TECNICO v0.6: layout pulito a una colonna, niente header/footer ripetuti
né template DOCX dedicato. Priorità qui = leggibilità e correttezza, non estetica.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field


# ====================================================================
# MODELLI
# ====================================================================

class SezioneAsseverativa(BaseModel):
    numero_progressivo: int
    titolo: str
    norma_riferimento: str
    descrizione_metodologia: str = ""
    parametri_input: dict[str, Any] = Field(default_factory=dict)
    risultati: dict[str, Any] = Field(default_factory=dict)
    esito_conforme: bool
    livello_conformita: Literal[
        "conforme", "conforme_con_note", "conforme_condizionatamente", "non_conforme"
    ] = "conforme"
    note_asseverative: str = ""
    raccomandazioni: list[str] = Field(default_factory=list)


class AssembleAllegatoInput(BaseModel):
    # Metadati progetto
    titolo_progetto: str
    committente: str
    progettista_pe: str = ""
    sito_intervento: str = ""
    data_emissione_pe: str | None = None
    revisione_pe: str | None = None
    # Metadati asseveratore
    asseveratore: str = "K2A S.r.l.s. — ing. Luca Rossi"
    data_asseverazione: str
    versione_mcp: str = "v0.5"
    # Contenuto
    sezioni: list[SezioneAsseverativa] = Field(..., min_length=1)
    # Opzioni
    includi_sintesi_esecutiva: bool = True
    includi_raccomandazioni_aggregate: bool = True
    formato_output: Literal["docx", "json", "entrambi"] = "docx"
    path_output: str | None = None


class AssembleAllegatoOutput(BaseModel):
    path_docx: str | None
    n_sezioni: int
    n_conformi: int
    n_conformi_con_note: int
    n_non_conformi: int
    esito_complessivo: Literal["conforme", "conforme_con_riserve", "non_conforme"]
    raccomandazioni_aggregate: list[str]
    json_strutturato: dict


# ====================================================================
# HELPER
# ====================================================================

_VERDE = (0x00, 0x80, 0x00)
_ROSSO = (0xC0, 0x00, 0x00)
_AMBRA = (0xB8, 0x86, 0x00)

_LABEL_LIVELLO = {
    "conforme": "✅ CONFORME",
    "conforme_con_note": "🟡 CONFORME CON NOTE",
    "conforme_condizionatamente": "🟡 CONFORME CONDIZIONATAMENTE",
    "non_conforme": "❌ NON CONFORME",
}


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[-\s]+", "_", s)[:60] or "progetto"


def _conteggi(sezioni: list[SezioneAsseverativa]) -> tuple[int, int, int]:
    n_conf = sum(1 for s in sezioni if s.livello_conformita == "conforme")
    n_note = sum(1 for s in sezioni if s.livello_conformita in ("conforme_con_note", "conforme_condizionatamente"))
    n_ko = sum(1 for s in sezioni if s.livello_conformita == "non_conforme")
    return n_conf, n_note, n_ko


def _esito_complessivo(n_ko: int, n_note: int) -> str:
    if n_ko > 0:
        return "non_conforme"
    if n_note > 0:
        return "conforme_con_riserve"
    return "conforme"


def _color_per_livello(livello: str) -> tuple[int, int, int]:
    if livello == "non_conforme":
        return _ROSSO
    if livello == "conforme":
        return _VERDE
    return _AMBRA


# ====================================================================
# FUNZIONE PRINCIPALE
# ====================================================================

def assembla_allegato_asseverativo(inp: AssembleAllegatoInput) -> AssembleAllegatoOutput:
    n_conf, n_note, n_ko = _conteggi(inp.sezioni)
    esito = _esito_complessivo(n_ko, n_note)

    raccomandazioni_aggregate: list[str] = []
    for s in inp.sezioni:
        for r in s.raccomandazioni:
            raccomandazioni_aggregate.append(f"[V{s.numero_progressivo}] {r}")

    json_strutturato = {
        "progetto": {
            "titolo": inp.titolo_progetto, "committente": inp.committente,
            "progettista_pe": inp.progettista_pe, "sito": inp.sito_intervento,
            "data_emissione_pe": inp.data_emissione_pe, "revisione_pe": inp.revisione_pe,
        },
        "asseveratore": inp.asseveratore,
        "data_asseverazione": inp.data_asseverazione,
        "versione_mcp": inp.versione_mcp,
        "esito_complessivo": esito,
        "conteggi": {"conformi": n_conf, "con_note": n_note, "non_conformi": n_ko, "totale": len(inp.sezioni)},
        "sezioni": [s.model_dump() for s in inp.sezioni],
        "raccomandazioni_aggregate": raccomandazioni_aggregate,
    }

    path_docx: str | None = None
    if inp.formato_output in ("docx", "entrambi"):
        path_docx = _genera_docx(inp, n_conf, n_note, n_ko, esito, raccomandazioni_aggregate)

    return AssembleAllegatoOutput(
        path_docx=path_docx,
        n_sezioni=len(inp.sezioni),
        n_conformi=n_conf,
        n_conformi_con_note=n_note,
        n_non_conformi=n_ko,
        esito_complessivo=esito,
        raccomandazioni_aggregate=raccomandazioni_aggregate,
        json_strutturato=json_strutturato,
    )


def _genera_docx(inp, n_conf, n_note, n_ko, esito, racc_agg) -> str:
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as e:
        raise RuntimeError(f"python-docx mancante: {e}. Esegui: uv sync") from e

    doc = Document()
    base = doc.styles["Normal"]
    base.font.name = "Calibri"
    base.font.size = Pt(11)

    def _badge(testo: str, rgb: tuple[int, int, int]) -> None:
        p = doc.add_paragraph()
        r = p.add_run(testo)
        r.bold = True
        r.font.color.rgb = RGBColor(*rgb)

    def _tabella_kv(d: dict, evidenzia_delta: bool = False) -> None:
        if not d:
            return
        t = doc.add_table(rows=len(d), cols=2)
        t.style = "Light List Accent 1"
        for i, (k, v) in enumerate(d.items()):
            t.cell(i, 0).text = str(k)
            valore = str(v)
            if evidenzia_delta and "delta" in str(k).lower():
                valore = f"Δ {valore}"
            t.cell(i, 1).text = valore
            if t.cell(i, 0).paragraphs[0].runs:
                t.cell(i, 0).paragraphs[0].runs[0].bold = True

    # ---------- PAGINA 1 — Frontespizio ----------
    h = doc.add_heading("ALLEGATO H — ASSEVERAZIONE INDIPENDENTE", level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph(inp.titolo_progetto)
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].bold = True
    sub.runs[0].font.size = Pt(14)
    doc.add_paragraph()

    info = [
        ("Committente", inp.committente),
        ("Progettista PE", inp.progettista_pe or "—"),
        ("Sito intervento", inp.sito_intervento or "—"),
        ("Data emissione PE", inp.data_emissione_pe or "—"),
        ("Revisione PE", inp.revisione_pe or "—"),
        ("Asseveratore", inp.asseveratore),
        ("Data asseverazione", inp.data_asseverazione),
    ]
    t = doc.add_table(rows=len(info), cols=2)
    t.style = "Light Grid Accent 1"
    for i, (k, v) in enumerate(info):
        t.cell(i, 0).text = k
        t.cell(i, 1).text = str(v)
        t.cell(i, 0).paragraphs[0].runs[0].bold = True

    doc.add_paragraph()
    foot = doc.add_paragraph(
        f"Asseverazione condotta con strumenti di calcolo indipendenti MCP k2a-elettrico "
        f"{inp.versione_mcp}, secondo le norme tecniche CEI/IEC applicabili. "
        f"Il presente allegato attesta la verifica indipendente del Progetto Esecutivo."
    )
    foot.runs[0].italic = True
    foot.runs[0].font.size = Pt(9)

    # ---------- PAGINA 2 — Sintesi esecutiva ----------
    if inp.includi_sintesi_esecutiva:
        doc.add_page_break()
        doc.add_heading("Sintesi esecutiva", level=1)
        badge_map = {
            "conforme": ("ESITO COMPLESSIVO: CONFORME", _VERDE),
            "conforme_con_riserve": ("ESITO COMPLESSIVO: CONFORME CON RISERVE", _AMBRA),
            "non_conforme": ("ESITO COMPLESSIVO: NON CONFORME", _ROSSO),
        }
        testo, rgb = badge_map[esito]
        _badge(testo, rgb)
        doc.add_paragraph(
            f"Verifiche eseguite: {len(inp.sezioni)} — "
            f"conformi: {n_conf}, con note/condizionate: {n_note}, non conformi: {n_ko}."
        )
        tab = doc.add_table(rows=len(inp.sezioni) + 1, cols=3)
        tab.style = "Light Grid Accent 1"
        for j, intest in enumerate(("Verifica", "Norma", "Esito")):
            tab.cell(0, j).text = intest
            tab.cell(0, j).paragraphs[0].runs[0].bold = True
        for i, s in enumerate(inp.sezioni, 1):
            tab.cell(i, 0).text = f"V{s.numero_progressivo} — {s.titolo}"
            tab.cell(i, 1).text = s.norma_riferimento
            tab.cell(i, 2).text = _LABEL_LIVELLO[s.livello_conformita]

    # ---------- PAGINE 3+ — Una sezione per verifica ----------
    for s in inp.sezioni:
        doc.add_page_break()
        doc.add_heading(f"V{s.numero_progressivo} — {s.titolo}", level=1)
        p = doc.add_paragraph(f"Norma di riferimento: {s.norma_riferimento}")
        p.runs[0].italic = True
        if s.descrizione_metodologia:
            doc.add_heading("Metodologia", level=2)
            doc.add_paragraph(s.descrizione_metodologia)
        if s.parametri_input:
            doc.add_heading("Parametri di input", level=2)
            _tabella_kv(s.parametri_input)
        if s.risultati:
            doc.add_heading("Risultati (K2A vs PE)", level=2)
            _tabella_kv(s.risultati, evidenzia_delta=True)
        doc.add_heading("Esito", level=2)
        _badge(_LABEL_LIVELLO[s.livello_conformita], _color_per_livello(s.livello_conformita))
        if s.note_asseverative:
            doc.add_heading("Note asseverative", level=2)
            doc.add_paragraph(s.note_asseverative)
        if s.raccomandazioni:
            doc.add_heading("Raccomandazioni", level=2)
            for r in s.raccomandazioni:
                doc.add_paragraph(r, style="List Bullet")

    # ---------- Raccomandazioni aggregate ----------
    if inp.includi_raccomandazioni_aggregate and racc_agg:
        doc.add_page_break()
        doc.add_heading("Raccomandazioni aggregate", level=1)
        doc.add_paragraph(
            "Elenco unico di tutte le raccomandazioni emerse dalle verifiche, "
            "con riferimento alla sezione di origine."
        )
        for r in racc_agg:
            doc.add_paragraph(r, style="List Bullet")

    # ---------- Firma asseverativa ----------
    doc.add_page_break()
    doc.add_heading("Dichiarazione asseverativa", level=1)
    doc.add_paragraph(
        f"Il sottoscritto {inp.asseveratore}, in qualità di tecnico verificatore indipendente, "
        f"attesta di aver condotto la verifica del Progetto Esecutivo «{inp.titolo_progetto}» "
        f"mediante strumenti di calcolo indipendenti (MCP k2a-elettrico {inp.versione_mcp}), "
        f"secondo le norme tecniche CEI/IEC applicabili indicate nelle singole sezioni. "
        f"L'esito complessivo della verifica è: {esito.replace('_', ' ').upper()}."
    )
    doc.add_paragraph(
        "La presente asseverazione non sostituisce la relazione di calcolo del progettista, "
        "ma ne costituisce verifica indipendente a supporto della validazione."
    )
    doc.add_paragraph()
    doc.add_paragraph(f"Data: {inp.data_asseverazione}")
    doc.add_paragraph()
    doc.add_paragraph("Firma del tecnico verificatore: ______________________________")
    tracc = doc.add_paragraph(
        f"Tracciabilità: documento generato automaticamente da MCP k2a-elettrico {inp.versione_mcp} "
        f"a partire da {len(inp.sezioni)} sezioni di verifica."
    )
    tracc.runs[0].italic = True
    tracc.runs[0].font.size = Pt(8)

    # ---------- Salvataggio ----------
    if inp.path_output:
        out_path = Path(inp.path_output)
    else:
        out_path = Path("output/asseverazioni") / f"Allegato_H_{_slug(inp.titolo_progetto)}.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return str(out_path)
