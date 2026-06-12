"""build_catalog.py — genera catalog.json del K-BOT.

Fonde:
  1. catalog di Luca (k2a-catalogo, D-040) = fonte di verità prezzi/blueprint
  2. catalog.overlay.json (Luigi) = strato SEO scenario C (tag_pillar, mapping, percorsi)

Output: catalog.json nella shape che il loader (lib/catalog.py) consuma:
  service_id→id, strato→tipo, + tag_pillar_sito sui servizi mappati,
  + mapping_tag_to_servizi / percorsi / abbonamenti / tipi_listino dall'overlay.

Uso:
  python app/data/build_catalog.py --source <path-catalog-luca> [--out catalog.json]
Default source: ../../../k2a-8e/catalog/catalog.json (vendorizzato nel repo).
Re-run a ogni nuovo catalog di Luca → catalog.json rigenerato + commit (membrana §2).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent.parent.parent.parent / "k2a-8e" / "catalog" / "catalog.json"
OVERLAY = HERE / "catalog.overlay.json"
DEFAULT_OUT = HERE / "catalog.json"


def build(source: Path, overlay_path: Path, out: Path) -> dict:
    src = json.loads(source.read_text(encoding="utf-8"))
    ov = json.loads(overlay_path.read_text(encoding="utf-8"))

    # tag inverso: service_id → [pillar...]
    svc_to_tags: dict[str, list[str]] = {}
    for tag, m in ov.get("mapping_tag_to_servizi", {}).items():
        sid = m.get("boost_primario")
        if sid:
            svc_to_tags.setdefault(sid, []).append(tag)

    servizi = []
    for s in src.get("services", []):
        sid = s["service_id"]
        servizi.append({
            "id": sid,
            "tipo": s.get("strato"),
            "label": s.get("label"),
            "prodotto_commerciale": s.get("prodotto_commerciale"),
            "ambito": s.get("ambito"),
            "livello": s.get("livello"),
            "prezzo_eur": s.get("prezzo_eur"),
            "genera_via": s.get("genera_via"),
            "blueprint_id": s.get("blueprint_id"),
            "output_schema_ref": s.get("output_schema_ref"),
            "tag_pillar_sito": svc_to_tags.get(sid, []),
        })

    catalog = {
        "version": src.get("catalog_version", "unknown"),
        "generated_from": str(source.name),
        "fonte": src.get("fonte", "k2a-catalogo"),
        "n_services": len(servizi),
        "n_generabili_8e": sum(1 for s in servizi if s["genera_via"] == "8e"),
        "tipi_listino": ov.get("tipi_listino", {}),
        "servizi": servizi,
        "percorsi": ov.get("percorsi", []),
        "abbonamenti": ov.get("abbonamenti", []),
        "mapping_tag_to_servizi": ov.get("mapping_tag_to_servizi", {}),
    }
    out.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return catalog


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(DEFAULT_SOURCE))
    ap.add_argument("--overlay", default=str(OVERLAY))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args()
    cat = build(Path(a.source), Path(a.overlay), Path(a.out))
    gen = [s["id"] for s in cat["servizi"] if s["genera_via"] == "8e"]
    print(f"catalog.json scritto: {a.out}")
    print(f"  servizi: {cat['n_services']} · generabili 8e: {cat['n_generabili_8e']}")
    print(f"  tag mappati: {list(cat['mapping_tag_to_servizi'].keys())}")
    print(f"  generabili: {gen}")
