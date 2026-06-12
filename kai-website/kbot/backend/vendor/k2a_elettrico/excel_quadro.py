"""Excel quadro elettrico multi-circuito — genera relazione di calcolo asseverabile (XLSX)."""
from __future__ import annotations
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field


class CircuitoQuadro(BaseModel):
    descrizione: str
    Ib_A: float
    L_m: float
    sezione_mm2: float
    posa: Literal["B1", "B2", "C", "E", "F", "D1"] = "C"
    isolante: Literal["PVC", "EPR_XLPE"] = "PVC"
    In_protezione_A: float
    cosfi: float = 0.9
    sistema: Literal["trifase", "monofase"] = "trifase"


class ExcelQuadroInput(BaseModel):
    progetto: str
    committente: str
    Vn: float = 400.0
    Icc_origine_kA: float = 10.0
    output_path: str
    circuiti: list[CircuitoQuadro]


class ExcelQuadroOutput(BaseModel):
    file: str
    sheet: str
    n_circuiti: int
    n_conformi: int
    n_non_conformi: int


def genera_excel_quadro(inp: ExcelQuadroInput) -> ExcelQuadroOutput:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError as e:
        raise RuntimeError(f"openpyxl mancante: {e}. Esegui: uv sync") from e

    # Importi locali per evitare circolarità all'import del modulo
    from .cavo import DimensionaCavoInput, dimensiona_cavo
    from .cavo import iz_per_sezione
    from .caduta_v import CadutaVInput, caduta_tensione
    from .protezione import VerificaProtezioneInput, verifica_protezione

    wb = Workbook()
    ws = wb.active
    ws.title = "Quadro Elettrico"

    bold = Font(bold=True)
    hdr_fill = PatternFill("solid", fgColor="1F4E78")
    hdr_font = Font(bold=True, color="FFFFFF")
    ok_fill = PatternFill("solid", fgColor="C6EFCE")
    ko_fill = PatternFill("solid", fgColor="FFC7CE")
    border = Border(left=Side(style="thin"), right=Side(style="thin"),
                    top=Side(style="thin"), bottom=Side(style="thin"))

    # Header progetto
    ws["A1"] = f"Relazione di calcolo quadro elettrico — {inp.progetto}"
    ws["A1"].font = Font(bold=True, size=14)
    ws.merge_cells("A1:N1")
    ws["A2"] = f"Committente: {inp.committente}"
    ws["A3"] = f"Vn = {inp.Vn} V — Icc origine = {inp.Icc_origine_kA} kA — Norma: CEI 64-8"

    # Intestazione tabella circuiti
    headers = ["Descrizione", "Ib [A]", "L [m]", "Sez. [mm²]", "Posa", "Isol.",
               "In [A]", "cosφ", "Sistema",
               "Iz [A]", "ΔV [%]", "Coord.433", "I²t 434", "Conforme"]
    row = 5
    for col, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=col, value=h)
        c.font = hdr_font
        c.fill = hdr_fill
        c.alignment = Alignment(horizontal="center")
        c.border = border

    n_ok, n_ko = 0, 0
    row = 6
    for ckt in inp.circuiti:
        # Calcolo dim cavo + ΔV + protezione
        dim = dimensiona_cavo(DimensionaCavoInput(
            Ib=ckt.Ib_A, posa=ckt.posa, isolante=ckt.isolante,
            In_protezione=ckt.In_protezione_A,
        ))
        # ΔV su sezione scelta (quella indicata, non quella min calcolata)
        dV = caduta_tensione(CadutaVInput(
            I=ckt.Ib_A, L=ckt.L_m, sezione_mm2=ckt.sezione_mm2,
            cosfi=ckt.cosfi, sistema=ckt.sistema, Vn=inp.Vn,
        ))
        # Per I²t usiamo l'isolante: "EPR_XLPE" → "EPR"
        isol_kc = "EPR" if ckt.isolante == "EPR_XLPE" else "PVC"
        # Iz effettiva della sezione INSTALLATA (non della sezione minima calcolata)
        # Usa iz_per_sezione() del modulo cavo, che gestisce correttamente
        # chiavi sezione 16.0→"16" e 2.5→"2.5".
        # Derating k1/k2 ereditato dai default di dimensiona_cavo (T=30°C, n=1).
        Iz_eff = iz_per_sezione(
            sezione_mm2=ckt.sezione_mm2,
            materiale="Cu",   # CircuitoQuadro hardcoda Cu; Al sarà in v0.4
            isolante=ckt.isolante,
            posa=ckt.posa,
            k1_temperatura=dim.fattore_temperatura_k1,
            k2_raggruppamento=dim.fattore_raggruppamento_k2,
        )

        prot = verifica_protezione(VerificaProtezioneInput(
            Ib=ckt.Ib_A, In=ckt.In_protezione_A, Iz=Iz_eff,
            sezione_mm2=ckt.sezione_mm2, materiale="Cu", isolante=isol_kc,
            Icc_max_kA=inp.Icc_origine_kA, tempo_intervento_max_s=0.04,
        ))

        conforme = prot.conclusione_finale and dV.verifica_CEI_525
        if conforme: n_ok += 1
        else: n_ko += 1

        vals = [ckt.descrizione, ckt.Ib_A, ckt.L_m, ckt.sezione_mm2, ckt.posa, ckt.isolante,
                ckt.In_protezione_A, ckt.cosfi, ckt.sistema,
                round(Iz_eff, 1), dV.delta_V_percento,
                "OK" if prot.verifica_sovraccarico_433_1 else "KO",
                "OK" if prot.verifica_I2t_434_5_2 else "KO",
                "✓ CONFORME" if conforme else "✗ NON CONFORME"]
        for col, v in enumerate(vals, start=1):
            c = ws.cell(row=row, column=col, value=v)
            c.border = border
            if col == len(vals):
                c.fill = ok_fill if conforme else ko_fill
                c.font = bold
            c.alignment = Alignment(horizontal="center" if col not in (1,) else "left")
        row += 1

    # Summary
    row += 1
    ws.cell(row=row, column=1, value="SOMMARIO").font = bold
    ws.cell(row=row+1, column=1, value=f"Circuiti totali: {len(inp.circuiti)}")
    ws.cell(row=row+2, column=1, value=f"Conformi: {n_ok}").fill = ok_fill
    ws.cell(row=row+3, column=1, value=f"Non conformi: {n_ko}").fill = ko_fill if n_ko else ok_fill

    # Larghezze colonne
    widths = [38, 8, 8, 10, 7, 8, 8, 7, 10, 9, 9, 10, 10, 16]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    out = Path(inp.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return ExcelQuadroOutput(
        file=str(out), sheet="Quadro Elettrico",
        n_circuiti=len(inp.circuiti), n_conformi=n_ok, n_non_conformi=n_ko,
    )
