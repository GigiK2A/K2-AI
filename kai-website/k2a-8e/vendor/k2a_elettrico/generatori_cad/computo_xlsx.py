"""Tool: genera computo metrico XLSX (lista materiali) da topologia (Layer 3 → XLSX).

Deterministico: estrae voci da `dimensioni` (cavi, protezioni, trafo, quadri, terra,
SPD) e le raggruppa per categoria o per linea. SENZA prezzi (richiederebbe catalogo
prezzi non disponibile: `include_prezzi` lasciato False). openpyxl è in dependencies.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ._topologia import estrai_topologia


class GeneraComputoMetricoInput(BaseModel):
    dimensioni: dict = Field(..., description="Dimensioni Layer 3 (asdict)")
    schema_arricchito: dict = Field(..., description="Schema arricchito Layer 2")
    output_dir: str = "output"
    slug: str = "progetto"
    include_prezzi: bool = Field(False, description="Richiede catalogo prezzi (non disponibile)")
    raggruppa_per: str = Field("categoria", description="categoria | linea")
    include_riferimenti_calcolo: bool = True


class GeneraComputoMetricoOutput(BaseModel):
    file_path: str | None
    num_voci: int
    num_categorie: int
    totale_metratura_cavi_m: float
    totale_protezioni_n: int
    norma_riferimento: str = "Computo da pipeline Layer 3 (senza prezzi)"
    warnings: list[str] = Field(default_factory=list)


def genera_computo_metrico_xlsx(inp: GeneraComputoMetricoInput) -> GeneraComputoMetricoOutput:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    warnings: list[str] = []
    if inp.include_prezzi:
        warnings.append("include_prezzi ignorato: nessun catalogo prezzi disponibile.")

    topo = estrai_topologia(inp.dimensioni, inp.schema_arricchito)
    voci: list[dict] = []

    # Cavi (da linee). Lunghezza: usa quella nota se presente, altrimenti stima 20 m + nota.
    tot_m = 0.0
    for ln in topo["linee"]:
        sez = ln.get("sezione_mm2")
        if sez is None:
            continue
        lung = float(ln.get("lunghezza_m") or 20.0)
        if not ln.get("lunghezza_m"):
            warnings.append(f"Lunghezza linea {ln['id']} stimata (20 m): non nello schema A–E.")
        tot_m += lung
        voci.append({"categoria": "Cavi BT", "descrizione": f"Cavo {sez} mm² — {ln['descrizione']}",
                     "um": "m", "qta": lung, "rif": ln["id"]})

    # Protezioni (da linee con In).
    n_prot = 0
    for ln in topo["linee"]:
        if ln.get("In_A"):
            n_prot += 1
            voci.append({"categoria": "Protezioni", "descrizione": f"Interruttore In {ln['In_A']} A",
                         "um": "n", "qta": 1, "rif": ln["id"]})

    # Trafo.
    for t in topo["trafi"]:
        voci.append({"categoria": "Trasformatori",
                     "descrizione": f"Trafo {t['id']} {t.get('Sn_kVA','?')} kVA {t.get('gruppo','')}",
                     "um": "n", "qta": 1, "rif": t["id"]})
    # Quadri.
    for q in topo["quadri"]:
        voci.append({"categoria": "Quadri", "descrizione": q["label"], "um": "n", "qta": 1, "rif": q["id"]})
    # Terra.
    if topo["terra"]:
        voci.append({"categoria": "Impianto di terra", "descrizione": "Dispersore + collegamenti",
                     "um": "a corpo", "qta": 1, "rif": "terra"})
    # SPD / fulmine.
    if topo["fulmine"]:
        voci.append({"categoria": "Protezione fulmini", "descrizione": "SPD coordinato / LPS (se previsto)",
                     "um": "a corpo", "qta": 1, "rif": "fulmine"})

    # Costruzione XLSX.
    wb = Workbook()
    cats = sorted({v["categoria"] for v in voci})
    bold = Font(bold=True)

    # Foglio riepilogo.
    ws0 = wb.active
    ws0.title = "Riepilogo"
    p = topo["progetto"]
    ws0["A1"] = f"Computo metrico — {p['committente']}"; ws0["A1"].font = bold
    ws0["A2"] = f"{p['indirizzo']} · {p['tipologia']}"
    ws0.append([])
    ws0.append(["Categoria", "N. voci"]);
    for c in ws0[4]: c.font = bold
    for c in cats:
        ws0.append([c, sum(1 for v in voci if v["categoria"] == c)])
    ws0.append(["TOTALE voci", len(voci)])
    ws0.append(["Metratura cavi (m)", round(tot_m, 1)])
    ws0.append(["Protezioni (n)", n_prot])

    # Un foglio per categoria (o per linea).
    if inp.raggruppa_per == "linea":
        gruppi = {}
        for v in voci:
            gruppi.setdefault(v["rif"], []).append(v)
    else:
        gruppi = {c: [v for v in voci if v["categoria"] == c] for c in cats}

    header = ["Codice", "Categoria", "Descrizione", "U.M.", "Quantità"]
    if inp.include_riferimenti_calcolo:
        header.append("Rif. calcolo")
    for nome, items in gruppi.items():
        title = str(nome)[:31] or "Voci"
        ws = wb.create_sheet(title=title)
        ws.append(header)
        for c in ws[1]:
            c.font = bold
        for i, v in enumerate(items, 1):
            row = [f"{title[:3].upper()}{i:02d}", v["categoria"], v["descrizione"], v["um"], v["qta"]]
            if inp.include_riferimenti_calcolo:
                row.append(v["rif"])
            ws.append(row)

    dest = Path(inp.output_dir) / inp.slug
    dest.mkdir(parents=True, exist_ok=True)
    file_path = dest / "computo_metrico.xlsx"
    wb.save(str(file_path))

    return GeneraComputoMetricoOutput(
        file_path=str(file_path), num_voci=len(voci), num_categorie=len(cats),
        totale_metratura_cavi_m=round(tot_m, 1), totale_protezioni_n=n_prot, warnings=warnings)
