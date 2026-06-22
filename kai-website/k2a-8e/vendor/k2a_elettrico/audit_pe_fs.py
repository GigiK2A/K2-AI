"""Audit PE a livello filesystem — estensione multi-formato di audit_coerenza_pe.

Aggiunge ai controlli testuali (R2/R4/R5 di audit_pe) la lettura di docx/xlsx/pdf e
3 regole nuove:
  R6 — coerenza somme computo metrico (xlsx): Σ colonna importi vs cella TOTALE
  R7 — riferimenti incrociati indice ↔ file presenti in cartella
  R8 — nomenclatura standard degli allegati (prefisso NN_, duplicati Rev)

Dipendenze: openpyxl (già in deps), pypdf (extra [audit]); se assenti → skip con warning.
PDF scansionati (nessun testo estraibile) → skip con warning (no OCR, fuori scope).
"""
from __future__ import annotations

import re
from pathlib import Path

from .audit_pe import AuditPEInput, Finding, audit_coerenza_pe


# --------------------------------------------------------------------------- #
# Reader di testo per formato
# --------------------------------------------------------------------------- #
def read_docx_text(path: Path) -> list[str]:
    from docx import Document
    d = Document(str(path))
    par = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                par.append(c.text)
    for sec in d.sections:
        for hf in (sec.header, sec.footer):
            par.extend(p.text for p in hf.paragraphs)
    return par


def read_xlsx(path: Path) -> tuple[list[str], list[dict]]:
    """Ritorna (righe_testo, fogli) dove fogli=[{nome, righe:[[celle]]}]."""
    from openpyxl import load_workbook
    wb = load_workbook(str(path), data_only=True, read_only=True)
    testo: list[str] = []
    fogli: list[dict] = []
    for ws in wb.worksheets:
        righe = []
        for row in ws.iter_rows(values_only=True):
            cells = ["" if v is None else str(v) for v in row]
            if any(cells):
                righe.append(list(row))
                testo.append(" ".join(c for c in cells if c))
        fogli.append({"nome": ws.title, "righe": righe})
    wb.close()
    return testo, fogli


def read_pdf_text(path: Path) -> tuple[list[str], bool]:
    """Ritorna (righe_testo, scansione). scansione=True se nessun testo estraibile."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return [], False
    try:
        reader = PdfReader(str(path))
    except Exception:
        return [], True
    testo: list[str] = []
    for page in reader.pages:
        t = (page.extract_text() or "").strip()
        if t:
            testo.extend(t.splitlines())
    scansione = len("".join(testo).strip()) < 20
    return testo, scansione


# --------------------------------------------------------------------------- #
# R6 — coerenza somme computo metrico (xlsx)
# --------------------------------------------------------------------------- #
def regola_R6_computo(fogli: list[dict], nome_file: str, soglia_pct: float = 0.1) -> list[Finding]:
    findings: list[Finding] = []
    for f in fogli:
        righe = f["righe"]
        if not righe:
            continue
        # individua colonna importi: header con "totale"/"importo"/"prezzo"
        col_imp = None
        for r in righe[:8]:
            for j, c in enumerate(r):
                if isinstance(c, str) and re.search(r"totale|importo|prezzo\s*tot", c, re.I):
                    col_imp = j
                    break
            if col_imp is not None:
                break
        if col_imp is None:
            continue  # header non identificabile → skip (no falso positivo)
        # somma numerici della colonna + cerca cella "TOTALE GENERALE"
        somma = 0.0; tot_dichiarato = None
        for r in righe:
            cella_lbl = " ".join(str(x) for x in r if isinstance(x, str)).lower()
            val = r[col_imp] if col_imp < len(r) else None
            if isinstance(val, (int, float)):
                if re.search(r"totale\s+generale|totale\s+complessiv", cella_lbl):
                    tot_dichiarato = float(val)
                elif not re.search(r"totale|subtotale|riepilog", cella_lbl):
                    somma += float(val)
        if tot_dichiarato is not None and somma > 0:
            delta = abs(somma - tot_dichiarato) / tot_dichiarato * 100
            if delta > soglia_pct:
                findings.append(Finding(
                    regola="R6 computo-somma", severita="media", oggetto=f"{nome_file}:{f['nome']}",
                    riga=f"Σ voci={somma:.2f} vs TOTALE={tot_dichiarato:.2f}",
                    messaggio=f"Somma voci ({somma:.2f}) ≠ totale dichiarato ({tot_dichiarato:.2f}), Δ {delta:.2f}%.",
                    suggerimento="Verificare le formule/righe del computo."))
    return findings


# --------------------------------------------------------------------------- #
# R7 — riferimenti incrociati indice ↔ cartella
# --------------------------------------------------------------------------- #
def regola_R7_indice(testo_indice: list[str], file_presenti: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    full = "\n".join(testo_indice)
    # cita codici tipo "01", "02h", "DOC. 06" → confronta con prefissi file presenti
    prefissi_presenti = set()
    for nome in file_presenti:
        m = re.match(r"(\d{2}[a-z]?)[_\.]", nome)
        if m:
            prefissi_presenti.add(m.group(1))
    citati = set(re.findall(r"\b(?:doc\.?\s*)?(\d{2}[a-z]?)\b", full.lower()))
    mancanti = [c for c in citati if c not in prefissi_presenti and len(c) == 2 and c.isdigit()
                and int(c) <= 30]  # plausibili codici elaborato
    for c in sorted(mancanti)[:10]:
        findings.append(Finding(
            regola="R7 indice-riferimento", severita="bassa", oggetto=f"elaborato {c}",
            riga=f"codice {c} citato nell'indice",
            messaggio=f"L'indice cita l'elaborato {c} ma non è presente un file con prefisso {c}_.",
            suggerimento="Verificare presenza/numerazione dell'elaborato o aggiornare l'indice."))
    return findings


# --------------------------------------------------------------------------- #
# R8 — nomenclatura allegati
# --------------------------------------------------------------------------- #
def regola_R8_nomenclatura(file_presenti: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    # duplicati con Rev diverse dello stesso elaborato (stesso prefisso, suffissi _RevN)
    base_map: dict[str, list[str]] = {}
    for nome in file_presenti:
        stem = re.sub(r"_Rev\d+(\.\d+)?", "", Path(nome).stem, flags=re.I)
        base_map.setdefault(stem, []).append(nome)
    for stem, versioni in base_map.items():
        if len(versioni) > 1 and any(re.search(r"_Rev\d", v, re.I) for v in versioni):
            findings.append(Finding(
                regola="R8 nomenclatura", severita="media", oggetto=stem,
                riga=", ".join(versioni),
                messaggio=f"Presenti più revisioni dello stesso elaborato: {', '.join(versioni)}.",
                suggerimento="Tenere in consegna solo la revisione vigente; archiviare le superate."))
    # prefisso numerico mancante (solo per docx/xlsx/pdf di progetto)
    for nome in file_presenti:
        ext = Path(nome).suffix.lower()
        if ext in (".docx", ".xlsx", ".pdf") and not re.match(r"(\d{2}|DOCUMENTO_UNICO|INDICE)", nome, re.I):
            findings.append(Finding(
                regola="R8 nomenclatura", severita="bassa", oggetto=nome,
                riga=nome, messaggio=f"Il file «{nome}» non segue la nomenclatura NN_TIPO_DESCRIZIONE.",
                suggerimento="Adottare prefisso numerico ordinato per gli allegati di progetto."))
    return findings


# --------------------------------------------------------------------------- #
# Orchestrazione file e cartella
# --------------------------------------------------------------------------- #
def audit_file(path: Path, punto_consegna="MT", token_obsoleti=None,
               limite_UE_V=200.0) -> dict:
    token_obsoleti = token_obsoleti or []
    ext = path.suffix.lower()
    warnings: list[str] = []
    fogli: list[dict] = []
    if ext == ".docx":
        testo = read_docx_text(path)
    elif ext == ".xlsx":
        testo, fogli = read_xlsx(path)
    elif ext == ".pdf":
        testo, scan = read_pdf_text(path)
        if scan:
            warnings.append("PDF senza testo estraibile (probabile scansione): regole testuali saltate.")
    else:
        return {"file": path.name, "tipo": ext, "skip": True, "findings": [], "warnings": []}

    res = audit_coerenza_pe(AuditPEInput(
        paragrafi=testo, punto_consegna=punto_consegna,
        token_obsoleti=token_obsoleti, limite_UE_V=limite_UE_V))
    findings = list(res.findings)
    if ext == ".xlsx":
        findings += regola_R6_computo(fogli, path.name)
    return {"file": path.name, "tipo": ext, "skip": False,
            "findings": [f.model_dump() for f in findings], "warnings": warnings}


def audit_cartella(cartella: str, punto_consegna="MT", token_obsoleti=None,
                   limite_UE_V=200.0) -> dict:
    base = Path(cartella)
    token_obsoleti = token_obsoleti or []
    files = sorted([p for p in base.rglob("*")
                    if p.suffix.lower() in (".docx", ".xlsx", ".pdf") and p.is_file()])
    nomi = [p.name for p in files]
    risultati = []
    errori = 0
    for p in files:
        try:
            risultati.append(audit_file(p, punto_consegna, token_obsoleti, limite_UE_V))
        except Exception as e:  # pragma: no cover
            errori += 1
            risultati.append({"file": p.name, "tipo": p.suffix, "skip": True,
                              "findings": [], "warnings": [f"errore parsing: {e}"]})

    # R7 su file indice
    r7: list[dict] = []
    for p in files:
        if "INDICE" in p.name.upper() and p.suffix.lower() in (".docx", ".pdf"):
            testo = read_docx_text(p) if p.suffix.lower() == ".docx" else read_pdf_text(p)[0]
            r7 += [f.model_dump() for f in regola_R7_indice(testo, nomi)]
    # R8 nomenclatura
    r8 = [f.model_dump() for f in regola_R8_nomenclatura(nomi)]

    n_file_rilievi = sum(1 for r in risultati if r["findings"])
    return {
        "cartella": str(base), "n_file": len(files), "n_errori_parsing": errori,
        "n_file_con_rilievi": n_file_rilievi,
        "risultati": risultati, "R7_indice": r7, "R8_nomenclatura": r8,
    }
