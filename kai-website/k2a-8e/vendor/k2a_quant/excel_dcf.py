"""Generatore Excel DCF — modello vivo con formule (non valori) per consulenza PMI."""
from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel, Field
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


class ExcelDcfInput(BaseModel):
    company_name: str = Field(..., description="Ragione sociale per intestazione")
    fcf: list[float] = Field(..., min_length=3, max_length=10)
    wacc: float
    g_perpetual: float = 0.02
    net_debt: float = 0.0
    output_path: str = Field(..., description="Path assoluto file .xlsx di output")


def generate_dcf_excel(inp: ExcelDcfInput) -> dict:
    wb = Workbook()
    ws = wb.active
    ws.title = "DCF"

    bold = Font(bold=True)
    hdr_fill = PatternFill("solid", fgColor="1F4E78")
    hdr_font = Font(bold=True, color="FFFFFF")
    inp_fill = PatternFill("solid", fgColor="FFF2CC")
    out_fill = PatternFill("solid", fgColor="C6EFCE")

    ws["A1"] = f"Modello DCF — {inp.company_name}"
    ws["A1"].font = Font(bold=True, size=14)
    ws.merge_cells("A1:H1")

    ws["A3"] = "INPUT (modificabili)"
    ws["A3"].font = bold
    ws["A4"] = "WACC"
    ws["B4"] = inp.wacc
    ws["B4"].fill = inp_fill
    ws["A5"] = "g perpetua"
    ws["B5"] = inp.g_perpetual
    ws["B5"].fill = inp_fill
    ws["A6"] = "PFN (Net Debt)"
    ws["B6"] = inp.net_debt
    ws["B6"].fill = inp_fill

    N = len(inp.fcf)
    ws["A8"] = "Anno"
    ws["A9"] = "FCF"
    ws["A10"] = "Discount factor"
    ws["A11"] = "PV FCF"
    for cell in ("A8", "A9", "A10", "A11"):
        ws[cell].font = bold

    for i, cf in enumerate(inp.fcf):
        col = chr(ord("B") + i)
        ws[f"{col}8"] = i + 1
        ws[f"{col}8"].fill = hdr_fill
        ws[f"{col}8"].font = hdr_font
        ws[f"{col}8"].alignment = Alignment(horizontal="center")
        ws[f"{col}9"] = cf
        ws[f"{col}9"].fill = inp_fill
        ws[f"{col}10"] = f"=1/(1+$B$4)^{col}8"
        ws[f"{col}11"] = f"={col}9*{col}10"

    last = chr(ord("B") + N - 1)
    ws["A13"] = "PV esplicito"
    ws["B13"] = f"=SUM(B11:{last}11)"
    ws["B13"].fill = out_fill
    ws["B13"].font = bold

    ws["A14"] = "Terminal Value (Gordon)"
    ws["B14"] = f"={last}9*(1+$B$5)/($B$4-$B$5)"
    ws["B14"].fill = out_fill

    ws["A15"] = "PV Terminal"
    ws["B15"] = f"=B14*{last}10"
    ws["B15"].fill = out_fill

    ws["A16"] = "Enterprise Value"
    ws["B16"] = "=B13+B15"
    ws["B16"].fill = out_fill
    ws["B16"].font = bold

    ws["A17"] = "Equity Value"
    ws["B17"] = "=B16-B6"
    ws["B17"].fill = out_fill
    ws["B17"].font = bold

    ws.column_dimensions["A"].width = 26
    for i in range(N + 2):
        ws.column_dimensions[chr(ord("B") + i)].width = 14

    out = Path(inp.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return {"file": str(out), "sheet": "DCF", "formulas_live": True}
