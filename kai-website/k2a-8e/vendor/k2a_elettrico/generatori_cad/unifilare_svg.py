"""Tool: genera schema unifilare SVG da topologia (Layer 3 → SVG).

Deterministico (nessun LLM): layout verticale automatico sorgenti→trafo→quadri→linee,
simboli IEC 60617 *semplificati* (rettangoli/cerchi/linee), etichette con grandezze
calcolate. Dipendenza opzionale `svgwrite` ([cad]); se assente ritorna warning e nessun file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ._topologia import estrai_topologia


class GeneraUnifilareInput(BaseModel):
    dimensioni: dict = Field(..., description="Dimensioni Layer 3 (asdict di DimensioniCalcolate)")
    schema_arricchito: dict = Field(..., description="Schema arricchito Layer 2 (sezioni A–E)")
    output_dir: str = Field("output", description="Cartella di output")
    slug: str = Field("progetto", description="Slug progetto per il nome file")
    include_grandezze_calcolate: bool = True
    with_kb_references: bool = False


class GeneraUnifilareOutput(BaseModel):
    file_path: str | None
    elementi_disegnati: list[dict]
    dimensioni_canvas_mm: tuple[float, float]
    norma_riferimento: str = "CEI 0-16 / CEI 64-8 (schema unifilare); simboli IEC 60617 semplificati"
    kb_references: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# Geometria layout (unità: px ~ mm su canvas).
_COL_X = 300.0       # colonna centrale
_Y0 = 60.0           # y prima riga (sorgenti)
_DY = 110.0          # passo verticale tra livelli
_BOX_W, _BOX_H = 120.0, 50.0


def _svg_disponibile() -> bool:
    try:
        import svgwrite  # noqa: F401
        return True
    except ImportError:
        return False


def genera_unifilare_svg(inp: GeneraUnifilareInput) -> GeneraUnifilareOutput:
    warnings: list[str] = []
    topo = estrai_topologia(inp.dimensioni, inp.schema_arricchito)
    elementi: list[dict] = []

    if not _svg_disponibile():
        return GeneraUnifilareOutput(
            file_path=None, elementi_disegnati=[], dimensioni_canvas_mm=(0.0, 0.0),
            warnings=["svgwrite non installato ([cad]): SVG non generato (degradazione controllata)."])

    import svgwrite

    # Costruisci la sequenza verticale dei livelli.
    livelli: list[dict] = []
    for s in topo["sorgenti"]:
        livelli.append({"tipo": s["tipo"], "label": s["label"], "sub": s["dettaglio"]})
    for t in topo["trafi"]:
        sn = f"{t['Sn_kVA']} kVA" if t.get("Sn_kVA") else ""
        livelli.append({"tipo": "trafo", "label": f"{t['id']} {t.get('gruppo','')}".strip(),
                        "sub": f"{sn} {t.get('V1_kV','?')}kV/{t.get('V2_V','?')}V".strip()})
    for q in topo["quadri"]:
        livelli.append({"tipo": "quadro", "label": q["label"], "sub": q.get("tensione", "")})

    h_canvas = _Y0 + _DY * (len(livelli) + max(1, len(topo["linee"]))) + 120
    w_canvas = max(640.0, _COL_X + 60 + 60 * len(topo["linee"]))
    dwg = svgwrite.Drawing(size=(f"{w_canvas}px", f"{h_canvas}px"))

    def _box(x, y, label, sub, fill):
        dwg.add(dwg.rect(insert=(x - _BOX_W / 2, y), size=(_BOX_W, _BOX_H),
                         fill=fill, stroke="black", stroke_width=1.5, rx=4))
        dwg.add(dwg.text(label, insert=(x, y + 20), text_anchor="middle",
                         font_size="13px", font_weight="bold", font_family="Helvetica"))
        if sub and inp.include_grandezze_calcolate:
            dwg.add(dwg.text(sub, insert=(x, y + 38), text_anchor="middle",
                             font_size="10px", font_family="Helvetica"))

    _COLORI = {"rete_dso": "#cfe2ff", "fv": "#fff3cd", "ge": "#f8d7da",
               "trafo": "#d1e7dd", "quadro": "#e2e3e5"}

    prev_y = None
    for i, lv in enumerate(livelli):
        y = _Y0 + _DY * i
        # connessione verticale col livello precedente
        if prev_y is not None:
            dwg.add(dwg.line(start=(_COL_X, prev_y + _BOX_H), end=(_COL_X, y),
                             stroke="black", stroke_width=1.5))
        _box(_COL_X, y, lv["label"], lv["sub"], _COLORI.get(lv["tipo"], "#ffffff"))
        elementi.append({"tipo": lv["tipo"], "label": lv["label"],
                         "position": {"x": _COL_X, "y": y}})
        prev_y = y

    # Linee in partenza dal quadro generale (ventaglio sotto l'ultimo livello).
    if topo["linee"]:
        y_bus = (prev_y or _Y0) + _BOX_H + 30
        x0 = _COL_X - 30 * (len(topo["linee"]) - 1)
        dwg.add(dwg.line(start=(_COL_X, prev_y + _BOX_H), end=(_COL_X, y_bus),
                         stroke="black", stroke_width=1.5))
        dwg.add(dwg.line(start=(min(x0, _COL_X), y_bus),
                         end=(max(x0 + 60 * (len(topo["linee"]) - 1), _COL_X), y_bus),
                         stroke="black", stroke_width=2))  # sbarra
        for j, ln in enumerate(topo["linee"]):
            x = x0 + 60 * j
            yl = y_bus + 60
            dwg.add(dwg.line(start=(x, y_bus), end=(x, yl), stroke="black", stroke_width=1.2))
            # interruttore (rettangolino)
            dwg.add(dwg.rect(insert=(x - 7, y_bus + 12), size=(14, 18),
                             fill="white", stroke="black", stroke_width=1.2))
            et = ln.get("descrizione", ln["id"])[:14]
            dwg.add(dwg.text(et, insert=(x, yl + 14), text_anchor="middle",
                             font_size="9px", font_family="Helvetica"))
            if inp.include_grandezze_calcolate and ln.get("sezione_mm2"):
                dwg.add(dwg.text(f"{ln['sezione_mm2']}mm² {ln.get('In_A','?')}A",
                                 insert=(x, yl + 26), text_anchor="middle",
                                 font_size="8px", fill="#333", font_family="Helvetica"))
            elementi.append({"tipo": "linea", "label": ln["id"], "position": {"x": x, "y": yl}})

    # Title block
    p = topo["progetto"]
    dwg.add(dwg.line(start=(10, h_canvas - 60), end=(w_canvas - 10, h_canvas - 60),
                     stroke="black", stroke_width=1))
    dwg.add(dwg.text(f"Schema unifilare — {p['committente']}", insert=(15, h_canvas - 40),
                     font_size="12px", font_weight="bold", font_family="Helvetica"))
    dwg.add(dwg.text(f"{p['indirizzo']} · tipologia: {p['tipologia']}",
                     insert=(15, h_canvas - 22), font_size="10px", font_family="Helvetica"))

    dest = Path(inp.output_dir) / inp.slug
    dest.mkdir(parents=True, exist_ok=True)
    file_path = dest / "unifilare.svg"
    dwg.saveas(str(file_path))

    if len(topo["trafi"]) == 0 and topo["tensione_mt_kV"]:
        warnings.append("Topologia MT senza trasformatori espliciti nello schema.")

    return GeneraUnifilareOutput(
        file_path=str(file_path),
        elementi_disegnati=elementi,
        dimensioni_canvas_mm=(round(w_canvas, 1), round(h_canvas, 1)),
        warnings=warnings,
    )
