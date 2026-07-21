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
    ind.append(["Indice", "Valore", "Descrizione", "Stato dati"])
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


# ─────────────────────────────────────────────────────────────────────────────
# ControlBoost: cruscotto commesse operativo (spec §11).
# Il foglio KPI è popolato dalla STESSA estrazione usata dal PDF
# (quality_gate.extract_kpis) → coerenza PDF/Excel per costruzione.
# Dato mancante → "Da rilevare", mai 0. Le strutture (stati, RACI, checklist)
# sono TEMPLATE PROPOSTI, marcati come tali: nessun dato cliente inventato.
# ─────────────────────────────────────────────────────────────────────────────

_HDR_FILL = "0C7A6F"
_INPUT_FILL = "FFF2CC"
DA_RILEVARE = "Da rilevare"

_STATI_STANDARD = [
    ("Aperta", "Commessa registrata, in attesa di pianificazione",
     "Ordine/contratto ricevuto", "Piano e owner assegnati"),
    ("In pianificazione", "Scope, tempi e risorse in definizione",
     "Owner assegnato", "Piano approvato dalla direzione"),
    ("In corso", "Lavorazione attiva",
     "Piano approvato", "Attività tecniche completate"),
    ("In verifica", "Controllo tecnico/qualità della consegna",
     "Attività completate", "Verifica superata"),
    ("Bloccata", "Avanzamento fermo: motivazione e sblocco OBBLIGATORI",
     "Motivazione registrata nel Registro blocchi", "Blocco risolto → torna In corso"),
    ("In consegna", "Consegna/installazione presso il cliente",
     "Verifica superata", "Accettazione del cliente"),
    ("Chiusa", "Consegnata e accettata; pronta per fatturazione",
     "Accettazione cliente", "Fattura emessa"),
    ("Annullata", "Interrotta definitivamente (motivazione obbligatoria)",
     "Decisione della direzione", "—"),
]

_RACI_ATTIVITA = [
    "Apertura commessa", "Pianificazione", "Assegnazione task",
    "Aggiornamento stato", "Verifica tecnica", "Gestione blocchi",
    "Comunicazione cliente", "Approvazione consegna", "Chiusura", "Fatturazione",
]
_RACI_RUOLI = ["Direzione", "Resp. operativo", "Project Manager",
               "Resp. tecnico", "Amministrazione", "Operatore assegnato"]

_CHECKLIST_FASI = [
    ("Apertura", ["Anagrafica commessa completa", "Contratto/ordine archiviato",
                  "Owner unico assegnato", "Priorità assegnata"]),
    ("Pianificazione", ["Scope e deliverable definiti", "Milestone con date",
                        "Risorse e carichi verificati", "Rischi principali annotati"]),
    ("Esecuzione", ["Stato aggiornato (cadenza definita)", "Blocchi registrati con motivazione",
                    "Data prossima azione sempre presente"]),
    ("Verifica", ["Checklist tecnica superata", "Non conformità registrate"]),
    ("Chiusura", ["Accettazione cliente archiviata", "Consuntivo ore/costi compilato",
                  "Fattura emessa", "Lesson learned annotate"]),
]


def _hdr(ws, row_idx: int = 1):
    from openpyxl.styles import Font, PatternFill
    for c in ws[row_idx]:
        if c.value is not None:
            c.fill = PatternFill("solid", fgColor=_HDR_FILL)
            c.font = Font(color="FFFFFF", bold=True)


def _widths(ws, widths):
    from openpyxl.utils import get_column_letter
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def render_control_workbook(deliverable: dict, inputs: dict, path: Path) -> tuple[Path, dict]:
    """Costruisce il cruscotto commesse. Ritorna (path, mapping) dove mapping =
    {reportSectionId: {"sheet": nome_foglio, "range": intervallo}} (spec §11)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    from .quality_gate import extract_kpis

    kpis = extract_kpis(deliverable)
    azienda = str(inputs.get("azienda") or inputs.get("ragione_sociale") or "")
    periodo = f"{inputs.get('mese', '')} {inputs.get('anno', '')}".strip()
    mapping: dict[str, dict] = {}

    wb = Workbook()

    # 1) Registro commesse — template vuoto (mai dati inventati).
    ws = wb.active
    ws.title = "Registro commesse"
    ws.append([f"Registro commesse — {azienda}".strip(" —"), None, None, None,
               "Compilare: una riga per commessa. Nessun dato è precompilato."])
    ws["A1"].font = Font(bold=True, size=13, color="063B36")
    ws.append(["ID", "Nome commessa", "Cliente", "Owner (PM)", "Stato", "Priorità",
               "Data apertura", "Prossima azione", "Data prossima azione", "Note"])
    _hdr(ws, 2)
    for _ in range(12):
        ws.append([None] * 10)
    _widths(ws, (10, 30, 24, 18, 16, 10, 14, 30, 16, 30))
    ws.freeze_panes = "A3"
    mapping["registro_commesse"] = {"sheet": ws.title, "range": "A2:J14"}

    # 2) Dizionario stati — proposta standard (marcata come tale).
    ws = wb.create_sheet("Dizionario stati")
    ws.append(["Stato", "Definizione", "Criterio di ingresso", "Criterio di uscita"])
    _hdr(ws)
    for row in _STATI_STANDARD:
        ws.append(list(row))
    ws.append([])
    ws.append(["Proposta iniziale di stati standard: da validare con la direzione prima dell'adozione."])
    ws.cell(ws.max_row, 1).font = Font(italic=True, color="8A7A55")
    _widths(ws, (18, 44, 34, 34))
    ws.freeze_panes = "A2"
    mapping["stati_commessa"] = {"sheet": ws.title, "range": f"A1:D{len(_STATI_STANDARD) + 1}"}

    # 3) Registro blocchi.
    ws = wb.create_sheet("Registro blocchi")
    ws.append(["ID", "Commessa", "Descrizione blocco", "Motivazione", "Data inizio",
               "Owner sblocco", "Prossima azione", "Data prossima azione", "Stato"])
    _hdr(ws)
    for _ in range(10):
        ws.append([None] * 9)
    _widths(ws, (8, 22, 34, 30, 12, 16, 30, 16, 12))
    ws.freeze_panes = "A2"
    mapping["registro_blocchi"] = {"sheet": ws.title, "range": "A1:I11"}

    # 4) KPI — dalla stessa estrazione del PDF (coerenza per costruzione).
    ws = wb.create_sheet("KPI")
    ws.append(["KPI", "Valore attuale", "Unità", "Target", "Stato", "Scost. %",
               "Formula", "Fonte", "Periodicità", "Owner", "Ultimo aggiornamento"])
    _hdr(ws)
    for k in kpis:
        ws.append([
            k["nome"],
            k["valore"] if k["valore"] is not None else DA_RILEVARE,
            k["unita"] or "",
            k["target"] if k["target"] is not None else DA_RILEVARE,
            (k["semaforo"] or "").capitalize() or DA_RILEVARE,
            None,
            k["formula"] or DA_RILEVARE,
            k["fonte"] or DA_RILEVARE,
            "Mensile",
            DA_RILEVARE,          # owner del KPI: da assegnare, mai inventato
            periodo or DA_RILEVARE,
        ])
        r = ws.max_row
        ws.cell(r, 6).value = (f'=IF(OR(B{r}="{DA_RILEVARE}",D{r}="{DA_RILEVARE}",D{r}=0),"",'
                               f'(B{r}/D{r}-1))')
        ws.cell(r, 6).number_format = "0.0%"
    if not kpis:
        ws.append(["Nessun KPI disponibile nel report", DA_RILEVARE, "", DA_RILEVARE,
                   "", None, "", "", "", "", ""])
    _widths(ws, (28, 14, 8, 12, 10, 10, 34, 30, 12, 14, 18))
    ws.freeze_panes = "A2"
    mapping["kpi"] = {"sheet": ws.title, "range": f"A1:K{ws.max_row}"}

    # 5) Dashboard — formule vive sul foglio KPI (niente valori copiati).
    ws = wb.create_sheet("Dashboard")
    ws.append([f"Dashboard direzionale — {periodo}".strip(" —")])
    ws["A1"].font = Font(bold=True, size=13, color="063B36")
    last = max(len(kpis) + 1, 2)   # ultima riga dati del foglio KPI
    ws.append(["KPI totali", f"=COUNTA(KPI!A2:A{last})"])
    ws.append(["KPI in stato Rosso", f'=COUNTIF(KPI!E2:E{last},"Rosso")'])
    ws.append(["KPI in stato Giallo", f'=COUNTIF(KPI!E2:E{last},"Giallo")'])
    ws.append(["KPI in stato Verde", f'=COUNTIF(KPI!E2:E{last},"Verde")'])
    ws.append(["KPI da rilevare", f'=COUNTIF(KPI!B2:B{last},"{DA_RILEVARE}")'])
    ws.append([])
    ws.append(["Si aggiorna da sola quando compili il foglio KPI. Non inserire valori a mano qui."])
    ws.cell(ws.max_row, 1).font = Font(italic=True, color="8A7A55")
    _widths(ws, (26, 14))
    mapping["dashboard"] = {"sheet": ws.title, "range": "A2:B7"}

    # 6) Piano 30-60-90 — dalle azioni del report se presenti, senza inventare date.
    ws = wb.create_sheet("Piano 30-60-90")
    ws.append(["Orizzonte", "Azione", "Owner", "Scadenza", "Stato", "Note"])
    _hdr(ws)
    azioni = [a for a in (deliverable.get("azioni") or deliverable.get("piano_azione") or [])
              if isinstance(a, (str, dict))]
    horizons = ("0-30 giorni", "31-60 giorni", "61-90 giorni")
    for i, a in enumerate(azioni[:9]):
        testo = a if isinstance(a, str) else str(a.get("azione") or a.get("titolo") or "")
        ws.append([horizons[min(i // 3, 2)], testo, DA_RILEVARE, DA_RILEVARE, "Da avviare", ""])
    if not azioni:
        for h in horizons:
            ws.append([h, None, None, None, None, None])
    _widths(ws, (14, 52, 16, 12, 12, 26))
    ws.freeze_panes = "A2"
    mapping["piano_30_60_90"] = {"sheet": ws.title, "range": f"A1:F{ws.max_row}"}

    # 7) RACI — attività standard x ruoli PROPOSTI (nessun nome di persona).
    ws = wb.create_sheet("RACI")
    ws.append(["Attività \\ Ruolo"] + [f"{r} (proposto)" for r in _RACI_RUOLI])
    _hdr(ws)
    for att in _RACI_ATTIVITA:
        ws.append([att] + [None] * len(_RACI_RUOLI))
    ws.append([])
    ws.append(["Compilare con R (Responsible), A (Accountable), C (Consulted), I (Informed). "
               "Una sola A per riga. I ruoli sono proposti: adattarli all'organigramma reale."])
    ws.cell(ws.max_row, 1).font = Font(italic=True, color="8A7A55")
    _widths(ws, (26,) + (16,) * len(_RACI_RUOLI))
    ws.freeze_panes = "B2"
    mapping["raci"] = {"sheet": ws.title,
                       "range": f"A1:{chr(ord('A') + len(_RACI_RUOLI))}{len(_RACI_ATTIVITA) + 1}"}

    # 8) Checklist per fase.
    ws = wb.create_sheet("Checklist")
    ws.append(["Fase", "Voce di controllo", "Fatto (Sì/No)", "Note"])
    _hdr(ws)
    for fase, voci in _CHECKLIST_FASI:
        for voce in voci:
            ws.append([fase, voce, None, None])
    _widths(ws, (16, 48, 14, 30))
    ws.freeze_panes = "A2"
    mapping["checklist"] = {"sheet": ws.title, "range": f"A1:D{ws.max_row}"}

    # 9) Log aggiornamenti.
    ws = wb.create_sheet("Log aggiornamenti")
    ws.append(["Data", "Chi", "Cosa è cambiato", "Note"])
    _hdr(ws)
    for _ in range(10):
        ws.append([None] * 4)
    _widths(ws, (12, 16, 48, 30))
    ws.freeze_panes = "A2"
    mapping["log_aggiornamenti"] = {"sheet": ws.title, "range": "A1:D11"}

    # 10) Istruzioni.
    ws = wb.create_sheet("Istruzioni")
    istruzioni = [
        ("Registro commesse", "Una riga per commessa. Stato SOLO dal Dizionario stati. "
                              "Owner unico e data prossima azione sempre compilati."),
        ("Dizionario stati", "Stati standard proposti con criteri di ingresso/uscita. "
                             "Validarli con la direzione, poi non modificarli più."),
        ("Registro blocchi", "Ogni commessa Bloccata DEVE avere una riga qui, con motivazione "
                             "e owner dello sblocco."),
        ("KPI", "Valori del report. 'Da rilevare' = dato non ancora disponibile: sostituirlo "
                "col dato reale appena misurato. Mai inserire 0 al posto di un dato mancante."),
        ("Dashboard", "Si aggiorna automaticamente dal foglio KPI. Non scrivere qui."),
        ("Piano 30-60-90", "Azioni del report distribuite sugli orizzonti. Assegnare owner e scadenze."),
        ("RACI", "Compilare R/A/C/I per ogni attività. Una sola A per riga."),
        ("Checklist", "Spuntare le voci a ogni passaggio di fase della commessa."),
        ("Log aggiornamenti", "Traccia di chi modifica cosa: la disciplina del dato parte da qui."),
    ]
    ws.append(["Foglio", "Come usarlo"])
    _hdr(ws)
    for row in istruzioni:
        ws.append(list(row))
        ws.cell(ws.max_row, 2).alignment = Alignment(wrap_text=True)
    _widths(ws, (22, 90))
    ws.freeze_panes = "A2"
    mapping["istruzioni"] = {"sheet": ws.title, "range": f"A1:B{ws.max_row}"}

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                font = copy(cell.font)
                font.name = "Arial"
                cell.font = font

    wb.calculation.fullCalcOnLoad = True
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path, mapping


def excel_guide_section(mapping: dict) -> dict:
    """Sezione 'modello_excel' da iniettare nel deliverable → il PDF spiega i fogli
    (spec §11: quali fogli, come usarli, cosa si aggiorna da solo)."""
    fogli = [f"{m['sheet']}" for m in mapping.values()]
    return {
        "descrizione": ("Il report è accompagnato dal cruscotto Excel operativo: "
                        "è lo strumento di lavoro quotidiano, il PDF è la fotografia."),
        "fogli_inclusi": fogli,
        "come_usarlo": [
            "Registro commesse: una riga per commessa, stato solo dal Dizionario stati.",
            "KPI: i valori del report; le celle 'Da rilevare' vanno sostituite col dato reale.",
            "Dashboard: si aggiorna automaticamente dal foglio KPI, non scrivere a mano.",
            "RACI e Checklist: da compilare e validare con la direzione.",
            "Log aggiornamenti: tracciare ogni modifica.",
        ],
        "nota": "Nessuna cella contiene dati inventati: dove il dato manca trovi 'Da rilevare'.",
    }
