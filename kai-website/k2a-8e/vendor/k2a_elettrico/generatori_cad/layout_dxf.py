"""Tool: genera planimetria DXF SCHEMATICA da topologia (Layer 3 → DXF).

LIMITE NOTO (ADR-026, case study §13): lo schema A–E NON contiene coordinate fisiche
degli elementi (planimetria architettonica). Questo tool genera una planimetria
**schematica auto-derivata dalla topologia**, NON una planimetria architettonica vera.
Per la planimetria reale serve estendere lo schema A–E con coordinate (modalità
`planimetria_vera`, non implementata: ritorna errore esplicito).

Dipendenza opzionale `ezdxf` ([cad]); se assente ritorna warning e nessun file.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ._topologia import estrai_topologia


class GeneraLayoutDxfInput(BaseModel):
    dimensioni: dict = Field(..., description="Dimensioni Layer 3 (asdict)")
    schema_arricchito: dict = Field(..., description="Schema arricchito Layer 2")
    output_dir: str = "output"
    slug: str = "progetto"
    modalita: str = Field("schematica_auto",
                          description="schematica_auto (default) | planimetria_vera (non impl.)")
    include_quote: bool = True
    include_legenda: bool = True


class GeneraLayoutDxfOutput(BaseModel):
    file_path: str | None
    modalita_usata: str
    elementi_posizionati: list[dict]
    norma_riferimento: str = "CEI 99-2 (locali tecnici) — planimetria schematica, non architettonica"
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


def _ezdxf_disponibile() -> bool:
    try:
        import ezdxf  # noqa: F401
        return True
    except ImportError:
        return False


def genera_layout_dxf(inp: GeneraLayoutDxfInput) -> GeneraLayoutDxfOutput:
    if inp.modalita == "planimetria_vera":
        return GeneraLayoutDxfOutput(
            file_path=None, modalita_usata="planimetria_vera", elementi_posizionati=[],
            error="Modalità 'planimetria_vera' non implementata: lo schema A–E è privo di "
                  "coordinate fisiche. Serve estensione schema con planimetria architettonica.")

    warnings = ["Planimetria SCHEMATICA auto-derivata dalla topologia, NON architettonica "
                "(schema A–E privo di coordinate fisiche)."]
    if not _ezdxf_disponibile():
        return GeneraLayoutDxfOutput(
            file_path=None, modalita_usata="schematica_auto", elementi_posizionati=[],
            warnings=warnings + ["ezdxf non installato ([cad]): DXF non generato."])

    import ezdxf

    topo = estrai_topologia(inp.dimensioni, inp.schema_arricchito)
    doc = ezdxf.new("R2010")
    for layer, color in (("MURI", 7), ("ELEMENTI", 5), ("QUOTE", 3),
                         ("TESTO", 2), ("LEGENDA", 8)):
        doc.layers.add(layer, color=color)
    msp = doc.modelspace()
    elementi: list[dict] = []

    # Involucro locale tecnico schematico (mm). Default 6000×4000.
    W, H = 6000.0, 4000.0
    msp.add_lwpolyline([(0, 0), (W, 0), (W, H), (0, H), (0, 0)],
                       dxfattribs={"layer": "MURI"})

    # Posizionamento schematico: trafo a sinistra, quadri a destra, spazi tecnici.
    x = 600.0
    def _rect(x, y, w, h, label):
        msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],
                           dxfattribs={"layer": "ELEMENTI"})
        msp.add_text(label, dxfattribs={"layer": "TESTO", "height": 150}
                     ).set_placement((x + 60, y + h / 2))
        elementi.append({"label": label, "x": x, "y": y, "w": w, "h": h})

    for t in topo["trafi"]:
        _rect(x, 800, 1200, 1200, f"{t['id']} {t.get('Sn_kVA','')}kVA")
        x += 1600
    qx = W - 2400
    for q in topo["quadri"]:
        _rect(qx, 800, 800, 2000, q["label"])
        qx += 1100

    if inp.include_quote:
        # quote ingombro (linee con testo quota)
        msp.add_text(f"{W/1000:.1f} m", dxfattribs={"layer": "QUOTE", "height": 200}
                     ).set_placement((W / 2 - 300, -400))
        msp.add_text(f"{H/1000:.1f} m", dxfattribs={"layer": "QUOTE", "height": 200}
                     ).set_placement((-700, H / 2))

    if inp.include_legenda:
        p = topo["progetto"]
        msp.add_text(f"PLANIMETRIA SCHEMATICA — {p['committente']} ({p['tipologia']})",
                     dxfattribs={"layer": "LEGENDA", "height": 220}).set_placement((0, H + 400))
        msp.add_text("NB: schematica auto, non architettonica (CEI 99-2)",
                     dxfattribs={"layer": "LEGENDA", "height": 150}).set_placement((0, H + 700))

    dest = Path(inp.output_dir) / inp.slug
    dest.mkdir(parents=True, exist_ok=True)
    file_path = dest / "layout_schematico.dxf"
    doc.saveas(str(file_path))

    return GeneraLayoutDxfOutput(
        file_path=str(file_path), modalita_usata="schematica_auto",
        elementi_posizionati=elementi, warnings=warnings)
