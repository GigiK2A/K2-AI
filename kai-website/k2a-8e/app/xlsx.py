"""Workbook vivo per FinanceBoost, costruito solo da input riconciliati."""
from __future__ import annotations

from copy import copy
from pathlib import Path
from typing import Any


def render_finance_workbook(inputs: dict, path: Path) -> Path:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    rows = [r for r in (inputs.get("bilanci") or []) if isinstance(r, dict)]
    if not rows:
        raise ValueError("bilanci mancanti")
    latest = max(rows, key=lambda r: int(r.get("anno") or 0))

    wb = Workbook()
    ws = wb.active
    ws.title = "Input bilancio"
    ws.append(["FinanceBoost - input riconciliati", None, "Fonte"])
    ws["A1"].font = Font(bold=True, size=14, color="063B36")
    ws.append(["Voce", "Valore", "Nota"])
    labels = [
        ("Ricavi", "ricavi"), ("EBITDA", "ebitda"), ("EBIT", "reddito_operativo"),
        ("Utile netto", "utile_netto"), ("Totale attivo", "totale_attivo"),
        ("Attivo corrente", "attivo_corrente"), ("Passivo corrente", "passivo_corrente"),
        ("Rimanenze", "rimanenze"), ("Patrimonio netto", "patrimonio_netto"),
        ("Debiti finanziari", "debiti_finanziari"),
    ]
    input_rows: dict[str, int] = {}
    for label, key in labels:
        ws.append([label, latest.get(key), f"Esercizio {latest.get('anno', '')}"])
        input_rows[key] = ws.max_row
    for cell in ws[2]:
        cell.fill = PatternFill("solid", fgColor="0C7A6F"); cell.font = Font(color="FFFFFF", bold=True)
    for row in range(3, ws.max_row + 1):
        ws.cell(row, 2).number_format = '#,##0.00;[Red](#,##0.00);-'
        ws.cell(row, 2).font = Font(name="Arial", color="0000FF")
    ws.column_dimensions["A"].width = 24; ws.column_dimensions["B"].width = 18; ws.column_dimensions["C"].width = 28
    ws.freeze_panes = "A3"

    ind = wb.create_sheet("Indici")
    ind.append(["Indice", "Valore", "Formula", "Stato dati"])
    for c in ind[1]:
        c.fill = PatternFill("solid", fgColor="0C7A6F"); c.font = Font(color="FFFFFF", bold=True)
    ref = lambda key: f"'Input bilancio'!B{input_rows[key]}"
    formulas = [
        ("Debt / Equity", f'=IFERROR({ref("debiti_finanziari")}/{ref("patrimonio_netto")},"")', "Debiti finanziari / PN"),
        ("ROE", f'=IFERROR({ref("utile_netto")}/{ref("patrimonio_netto")},"")', "Utile netto / PN"),
        ("ROS", f'=IFERROR({ref("reddito_operativo")}/{ref("ricavi")},"")', "EBIT / Ricavi"),
        ("ROI proxy", f'=IFERROR({ref("reddito_operativo")}/{ref("totale_attivo")},"")', "EBIT / Totale attivo"),
        ("EBITDA margin", f'=IFERROR({ref("ebitda")}/{ref("ricavi")},"")', "EBITDA / Ricavi"),
        ("Current ratio", f'=IFERROR({ref("attivo_corrente")}/{ref("passivo_corrente")},"")', "Attivo corrente / Passivo corrente"),
        ("Quick ratio", f'=IFERROR(({ref("attivo_corrente")}-{ref("rimanenze")})/{ref("passivo_corrente")},"")', "(AC - rimanenze) / PC"),
        ("CCN", f'=IF(OR({ref("attivo_corrente")}="",{ref("passivo_corrente")}=""),"",{ref("attivo_corrente")}-{ref("passivo_corrente")})', "Attivo corrente - Passivo corrente"),
    ]
    for name, formula, description in formulas:
        ind.append([name, formula, description, "formula viva; vuoto se input mancanti"])
        ind.cell(ind.max_row, 2).number_format = "0.00%" if name in {"ROE", "ROS", "ROI proxy", "EBITDA margin"} else "0.00"
    ind.column_dimensions["A"].width = 24; ind.column_dimensions["B"].width = 16
    ind.column_dimensions["C"].width = 36; ind.column_dimensions["D"].width = 16
    ind.freeze_panes = "A2"

    sc = wb.create_sheet("Scenari")
    sc.append(["Scenario", "Crescita ricavi (input)", "Variazione margine EBITDA (input)", "Ricavi proiettati", "EBITDA proiettato"])
    for c in sc[1]:
        c.fill = PatternFill("solid", fgColor="0C7A6F"); c.font = Font(color="FFFFFF", bold=True)
    for scenario in ("Base", "Ottimistico", "Pessimistico"):
        sc.append([scenario, None, None, f'=IF(B{sc.max_row+1}="","",{ref("ricavi")}*(1+B{sc.max_row+1}))',
                   f'=IF(OR(B{sc.max_row+1}="",C{sc.max_row+1}=""),"",D{sc.max_row+1}*({ref("ebitda")}/{ref("ricavi")}+C{sc.max_row+1}))'])
    for row in range(2, 5):
        sc.cell(row, 2).font = Font(color="0000FF"); sc.cell(row, 3).font = Font(color="0000FF")
        sc.cell(row, 2).fill = PatternFill("solid", fgColor="FFF2CC"); sc.cell(row, 3).fill = PatternFill("solid", fgColor="FFF2CC")
        sc.cell(row, 2).number_format = "0.0%"; sc.cell(row, 3).number_format = "0.0%"
        sc.cell(row, 4).number_format = '#,##0.00'; sc.cell(row, 5).number_format = '#,##0.00'
    for col, width in zip("ABCDE", (18, 24, 34, 22, 22)):
        sc.column_dimensions[col].width = width
    sc.freeze_panes = "A2"
    sc["A6"] = "Le celle gialle/blu sono assunzioni utente: nessuno scenario viene inventato dal sistema."
    sc.merge_cells("A6:E6"); sc["A6"].alignment = Alignment(wrap_text=True)

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                font = copy(cell.font)
                font.name = "Arial"
                cell.font = font

    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
