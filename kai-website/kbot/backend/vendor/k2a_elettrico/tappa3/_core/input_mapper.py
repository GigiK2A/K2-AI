"""Mapping schema A–E → input dei tool MCP reali (Layer 3).

Deriva i parametri elettrotecnici richiesti da ciascun tool a partire dallo schema
arricchito (sezioni A–E). Le derivazioni sono semplici e difendibili (In = Sn/√3·V,
Ib = P/√3·V·cosφ, ...): producono numeri reali, non placeholder.

Dove lo schema non contiene un dato e non c'è una derivazione plausibile, si usano
default tipologici ragionevoli; se nemmeno quelli bastano, il tool a valle fallirà la
validazione Pydantic e l'executor marcherà lo step `failed_input` (pipeline continua).
"""
from __future__ import annotations

import math
from typing import Any

SQRT3 = math.sqrt(3.0)
_STD_IN = [16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400,
           500, 630, 800, 1000, 1250, 1600, 2000, 2500]


def _node(schema: dict, path: str) -> Any:
    node: Any = schema
    for p in path.split("."):
        if not isinstance(node, dict) or p not in node:
            return None
        node = node[p]
    return node


def _val(schema: dict, path: str, default=None):
    n = _node(schema, path)
    if isinstance(n, dict) and "valore" in n:
        v = n.get("valore")
        return v if v is not None else default
    return n if n is not None else default


def _next_std(corrente: float) -> float:
    for s in _STD_IN:
        if s >= corrente:
            return float(s)
    return float(math.ceil(corrente / 100.0) * 100)


def _derivati(schema: dict) -> dict:
    trafi = _val(schema, "C_sorgenti_carichi.trasformatori", []) or []
    t0 = trafi[0].get("valore", {}) if trafi and isinstance(trafi[0], dict) else {}
    Sn = float(t0.get("Sn_kVA", 1000))
    V1 = float(t0.get("V1_kV", _val(schema, "B_allacciamento_sistema.tensione_MT_kV", 15)))
    V2 = float(t0.get("V2_V", 400))
    vcc = float(t0.get("vcc_pct", 6.0))
    P = float(_val(schema, "C_sorgenti_carichi.carico.P_kW", 0) or 0)
    cosphi = float(_val(schema, "C_sorgenti_carichi.carico.cosphi", 0.9) or 0.9)
    Icc_MT = float(_val(schema, "B_allacciamento_sistema.Icc_MT_kA", 12.5) or 12.5)
    area = float(_val(schema, "A_anagrafica_contesto.edificio.superficie_m2", 100) or 100)
    h = float(_val(schema, "A_anagrafica_contesto.edificio.altezza_interna_m", 6) or 6)
    Ng = float(_val(schema, "A_anagrafica_contesto.Ng_fulmini_km2_anno", 2.5) or 2.5)
    rho = float(_val(schema, "D_impianti_protezioni.impianto_terra.resistivita_terreno_ohm_m", 100) or 100)
    lato = math.sqrt(area)

    In_BT = Sn * 1000.0 / (SQRT3 * V2)            # corrente nominale secondario trafo
    Ib_load = (P * 1000.0 / (SQRT3 * V2 * cosphi)) if P else In_BT
    return {"Sn": Sn, "V1": V1, "V2": V2, "vcc": vcc, "P": P, "cosphi": cosphi,
            "Icc_MT": Icc_MT, "area": area, "h": h, "Ng": Ng, "rho": rho,
            "L": round(lato, 1), "W": round(lato, 1), "In_BT": round(In_BT, 1),
            "Ib_load": round(Ib_load, 1)}


def _sorgenti(schema: dict):
    acc = _val(schema, "C_sorgenti_carichi.sorgenti_accessorie", []) or []
    fv = next((s["valore"] for s in acc if isinstance(s, dict)
               and s.get("valore", {}).get("tipo") == "fotovoltaico"), None)
    return fv


def _trafi_specs(schema: dict, default_Sn: float, default_vcc: float) -> list[dict]:
    """Tutti i trasformatori dello schema → spec per icc_bt_multisorgente.
    Cabine multi-trafo: l'Icc BT in parallelo dipende da TUTTI i trafi (non solo dal primo)."""
    trafi = _val(schema, "C_sorgenti_carichi.trasformatori", []) or []
    specs = []
    for t in trafi:
        tv = t.get("valore", {}) if isinstance(t, dict) else {}
        specs.append({"Sn_kVA": float(tv.get("Sn_kVA", default_Sn)),
                      "vcc_pct": float(tv.get("vcc_pct", default_vcc))})
    return specs or [{"Sn_kVA": default_Sn, "vcc_pct": default_vcc}]


def mappa_input(tool: str, schema: dict, iterazione: str | None = None) -> dict:
    """Costruisce il dict di input (senza i flag pilastro) per un tool MCP."""
    d = _derivati(schema)
    if tool == "dimensiona_trafo":
        return {"Pn_carico_kW": d["P"] or 100, "cosfi": d["cosphi"],
                "fattore_contemporaneita": float(
                    _val(schema, "C_sorgenti_carichi.carico.contemporaneita", 0.8) or 0.8)}
    if tool == "calcola_icc_cabina":
        # Vn_MT e Vn_BT in kV (la norma/tool: Vn_BT 0.4 = 400 V).
        return {"Sn_trafo_kVA": d["Sn"], "Ucc_percento": d["vcc"],
                "Vn_MT": d["V1"], "Vn_BT": d["V2"] / 1000.0}
    if tool == "icc_bt_multisorgente":
        return {"Icc_MT_kA": d["Icc_MT"], "Vn_BT": d["V2"], "Vn_MT": d["V1"] * 1000.0,
                "trafi": _trafi_specs(schema, d["Sn"], d["vcc"])}
    if tool == "dimensiona_cavo":
        # I montanti di cabina ad alta corrente si realizzano con conduttori in
        # parallelo: si dimensiona il singolo conduttore (Ib per polo / n paralleli).
        if iterazione == "arrivo_bt":
            n_par = max(1, math.ceil(d["In_BT"] / 400.0))
            Ib = round(d["In_BT"] / n_par, 1)
        else:
            n_par = max(1, math.ceil(d["Ib_load"] / 400.0))
            Ib = round(d["Ib_load"] / n_par, 1)
        return {"Ib": Ib, "posa": "F", "isolante": "EPR_XLPE"}
    if tool == "caduta_tensione":
        if iterazione == "arrivo_bt":
            return {"I": d["In_BT"], "L": 10.0, "sezione_mm2": 300.0}
        return {"I": d["Ib_load"], "L": 30.0, "sezione_mm2": 240.0}
    if tool == "verifica_protezione":
        Ib = d["In_BT"] if iterazione == "arrivo_bt" else d["Ib_load"]
        In = _next_std(Ib)
        return {"Ib": Ib, "In": In, "Iz": round(In * 1.10, 1),
                "sezione_mm2": 300.0 if iterazione == "arrivo_bt" else 240.0,
                "Icc_max_kA": 30.0}
    if tool == "coordinamento_atrs_fv_generatore":
        return {"P_utenza_kW": d["P"] or 100, "Un_BT_V": d["V2"], "Un_MT_kV": d["V1"]}
    if tool == "verifica_spi_cei_021":
        fv = _sorgenti(schema)
        pgen = float(fv.get("potenza_kVA", 100)) if fv else 100.0
        return {"P_generazione_kW": pgen, "Vn": d["V2"]}
    if tool == "corrente_guasto_terra_mt":
        tm = _val(schema, "terra_mt", {}) or {}
        if not isinstance(tm, dict):
            tm = {}
        kv = d["V1"] if d["V1"] >= 1 else 20.0
        modalita = tm.get("modalita_calcolo_ig", "dati_dso_dichiarati")
        out = {"tensione_nominale_kV": 20 if kv >= 17.5 else 15, "modalita_calcolo": modalita}
        if modalita == "dati_dso_dichiarati":
            # default tipico 20 kV neutro compensato Italia (validato CEI 0-16 §8.5.12.3.2)
            out["ig_dso_dichiarata_A"] = tm.get("ig_dso_dichiarata_A") or (50.0 if kv >= 17.5 else 40.0)
            out["stato_neutro_dso"] = tm.get("stato_neutro_dso") or "compensato"
        else:
            out["lunghezza_cavi_mt_utente_km"] = tm.get("lunghezza_cavi_mt_utente_km", 0.5)
            out["lunghezza_linee_aeree_utente_km"] = tm.get("lunghezza_linee_aeree_utente_km", 0.0)
            out["tipo_zona_dso"] = tm.get("tipo_zona_dso", "suburbana")
        # catena Ig→U_E se disponibile R_terra (target/obiettivo dell'impianto di terra)
        rt = tm.get("r_terra_ohm") or _val(schema, "D_impianti_protezioni.impianto_terra.Re_target_ohm")
        if rt:
            out["R_terra_ohm"] = float(rt)
        return out
    if tool == "verifica_protezione_generale_mt":
        # Corrente nominale impianto al primario MT (da potenza FV o carico).
        fv = _sorgenti(schema)
        p_kw = float(fv.get("potenza_kVA", d["P"] or 100)) if fv else (d["P"] or 100)
        kv = d["V1"] if d["V1"] >= 1 else 20.0
        In_mt = (p_kw * 1000.0) / (SQRT3 * kv * 1000.0)
        neutro = str(_val(schema, "B_allacciamento_sistema.stato_neutro_MT", "isolato") or "isolato")
        neutro = "compensato_impedenza" if "impeden" in neutro or "terra" in neutro else "isolato"
        l_cavo = float(_val(schema, "B_allacciamento_sistema.lunghezza_rete_cavo_MT_m", 0) or 0)
        return {"tensione_nominale_kV": 20 if kv >= 17.5 else 15,
                "corrente_nominale_A": round(In_mt, 1), "icc_mt_trifase_kA": d["Icc_MT"],
                "neutro": neutro, "lunghezza_rete_cavo_utente_m": l_cavo}
    if tool == "verifica_protezione_interfaccia_mt":
        fv = _sorgenti(schema)
        pgen = float(fv.get("potenza_kVA", 100)) if fv else 100.0
        kv = d["V1"] if d["V1"] >= 1 else 20.0
        return {"potenza_generazione_kW": pgen,
                "tensione_nominale_kV": 20 if kv >= 17.5 else 15,
                "apparecchiatura_ddi": "MT"}
    if tool == "verifica_selettivita_catena":
        return {"Icc_max_BT_kA": 30.0, "catena": [
            {"nome": "DSO MT", "tipo": "DSO", "t_intervento_s": 0.5},
            {"nome": "Protezione MT", "tipo": "MT_protezione", "t_intervento_s": 0.3},
            {"nome": "Generale BT", "tipo": "ACB_BT", "t_intervento_s": 0.1}]}
    if tool == "dispersore_terra":
        return {"lunghezza_m": round(4 * d["L"], 1), "resistivita_ohm_m": d["rho"]}
    if tool == "verifica_terra":
        sistema = _val(schema, "B_allacciamento_sistema.sistema_distribuzione_BT", "TN-S") or "TN-S"
        if sistema not in ("TT", "TN-S", "TN-C", "TN-C-S"):
            sistema = "TN-S"
        if sistema == "TT":
            ra = _val(schema, "D_impianti_protezioni.impianto_terra.Re_target_ohm", 20.0) or 20.0
            return {"sistema": "TT", "RA_ohm": float(ra), "Idn_RCD_mA": 30.0, "U_limite_V": 50.0}
        return {"sistema": sistema, "Zs_ohm": 0.8, "Ia_A": 1250.0, "U0_V": 230.0}
    if tool == "valuta_rischio_fulmine":
        return {"modalita": "completo_62305", "Nt_fulmini_km2_anno": d["Ng"],
                "L_m": d["L"], "W_m": d["W"], "H_m": d["h"],
                "destinazione": "industriale_commerciale",
                "pavimento_tipo": "agricola_calcestruzzo"}
    if tool == "dimensiona_ups":
        # Carico IT da proteggere (kW); altri parametri ai default del tool.
        return {"P_carico_kW": d["P"] or 50.0, "cosfi_carico": d["cosphi"],
                "autonomia_richiesta_min": 15.0}
    if tool == "parallelo_trafi_circolazione":
        specs = _trafi_specs(schema, d["Sn"], d["vcc"])
        a = specs[0]
        b = specs[1] if len(specs) > 1 else dict(specs[0])  # 1 trafo → parallelo identico
        return {"Vn_BT_V": d["V2"],
                "trafo_a": {"Sn_kVA": a["Sn_kVA"], "vcc_pct": a["vcc_pct"]},
                "trafo_b": {"Sn_kVA": b["Sn_kVA"], "vcc_pct": b["vcc_pct"]},
                "S_carico_kVA": (d["P"] / d["cosphi"]) if d["P"] else d["Sn"]}
    if tool == "verifica_spd_coordinato":
        return {"L_cavi_da_SPD2_apparato_m": 10.0, "tipo_struttura": "LPS_esterno",
                "LPL": "II", "Up_spd_tipo2_kV": 1.5, "tensione_tenuta_apparato_Uw_kV": 2.5}
    return {}
