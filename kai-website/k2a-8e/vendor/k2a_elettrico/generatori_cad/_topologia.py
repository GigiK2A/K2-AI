"""Estrattore di topologia condiviso per i generatori CAD (SVG/DXF/XLSX).

Normalizza i dati di Layer 3 (`dimensioni`) + schema arricchito (Layer 2) in una
struttura comune deterministica, riusata dai 3 generatori. Nessun LLM, nessun calcolo
nuovo: solo riorganizzazione dei risultati già prodotti dalla pipeline.

Input tollerante: `dimensioni` può essere un dict (asdict di DimensioniCalcolate) o
l'oggetto stesso; `schema` è lo schema arricchito (dict, sezioni A–E).
"""
from __future__ import annotations

from typing import Any


def _get(obj: Any, key: str, default=None):
    """Accesso uniforme a dict o oggetto/dataclass."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _val(schema: dict, *path, default=None):
    """Naviga lo schema A–E risolvendo i CampoBase {valore: ...}."""
    cur: Any = schema
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    if isinstance(cur, dict) and "valore" in cur:
        v = cur.get("valore")
        return v if v is not None else default
    return cur if cur is not None else default


def estrai_topologia(dimensioni: Any, schema: dict) -> dict:
    """Restituisce {progetto, sorgenti, trafi, quadri, linee, terra, fulmine}."""
    schema = schema or {}
    A = schema.get("A_anagrafica_contesto", {})
    C = schema.get("C_sorgenti_carichi", {})

    progetto = {
        "committente": _val(A, "committente", default="—"),
        "indirizzo": _val(A, "indirizzo", default="—"),
        "tipologia": schema.get("tipologia", "—"),
    }

    # --- Sorgenti (rete DSO sempre; FV/GE da sorgenti_accessorie) ---
    sorgenti: list[dict] = []
    tensione_mt = _val(schema.get("B_allacciamento_sistema", {}), "tensione_MT_kV")
    sorgenti.append({"tipo": "rete_dso", "label": "Rete DSO",
                     "dettaglio": f"MT {tensione_mt} kV" if tensione_mt else "BT 400 V"})
    for s in (C.get("sorgenti_accessorie") or []):
        sv = s.get("valore", s) if isinstance(s, dict) else {}
        tipo = sv.get("tipo")
        if tipo == "fotovoltaico":
            sorgenti.append({"tipo": "fv", "label": "FV",
                             "dettaglio": f"{sv.get('potenza_kVA', '?')} kW"})
        elif tipo in ("gruppo_elettrogeno", "generatore", "ge"):
            sorgenti.append({"tipo": "ge", "label": "GE",
                             "dettaglio": f"{sv.get('potenza_kVA', '?')} kVA"})

    # --- Trasformatori ---
    trafi: list[dict] = []
    trafi_schema = C.get("trasformatori") or []
    dtrafo = _get(dimensioni, "dimensionamento_trafo")
    for i, t in enumerate(trafi_schema):
        tv = t.get("valore", {}) if isinstance(t, dict) else {}
        trafi.append({
            "id": f"TR{i+1}",
            "Sn_kVA": tv.get("Sn_kVA") or (dtrafo or {}).get("Sn_trafo_commerciale_kVA"),
            "V1_kV": tv.get("V1_kV", tensione_mt),
            "V2_V": tv.get("V2_V", 400),
            "gruppo": tv.get("gruppo", "Dyn11"),
        })
    if not trafi and dtrafo:
        trafi.append({"id": "TR1", "Sn_kVA": dtrafo.get("Sn_trafo_commerciale_kVA"),
                      "V1_kV": tensione_mt, "V2_V": 400, "gruppo": "Dyn11"})

    # --- Quadri (QMT se MT, QGBT sempre) ---
    quadri: list[dict] = []
    if tensione_mt:
        quadri.append({"id": "QMT", "label": "Quadro MT", "tensione": f"{tensione_mt} kV"})
    quadri.append({"id": "QGBT", "label": "Quadro Generale BT", "tensione": "400 V"})

    # --- Linee (da dimensionamento_linee) ---
    linee: list[dict] = []
    for ln in (_get(dimensioni, "dimensionamento_linee") or []):
        cavo = _get(ln, "dimensionamento_cavo") or {}
        cdt = _get(ln, "caduta_tensione") or {}
        linee.append({
            "id": _get(ln, "linea_id") or f"L{len(linee)+1}",
            "descrizione": _get(ln, "descrizione") or "linea",
            "sezione_mm2": _get(cavo, "sezione_minima_mm2"),
            "Iz_A": _get(cavo, "Iz_corretta"),
            "In_A": _get(ln, "protezione_In"),
            "dV_pct": _get(cdt, "delta_V_percento") if isinstance(cdt, dict) else None,
        })

    # --- Icc / terra / fulmine ---
    icc = _get(dimensioni, "icc_calculations") or []
    terra = _get(dimensioni, "protezione_terra")
    fulmine = _get(dimensioni, "rischio_fulmine")

    return {
        "progetto": progetto, "sorgenti": sorgenti, "trafi": trafi,
        "quadri": quadri, "linee": linee, "icc": icc,
        "terra": terra, "fulmine": fulmine, "tensione_mt_kV": tensione_mt,
    }
