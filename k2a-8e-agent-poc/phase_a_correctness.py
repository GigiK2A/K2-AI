"""Phase A — CORRETTEZZA deterministica dei numeri quant sui 4 casi (NO Claude, NO crediti).

Risponde alle domande di Luca senza orchestrazione agentica:
  - il ke è ragionevole per il settore? (capm_cost_of_equity da snapshot reale)
  - gli EV reggono?                       (ev_from_multiples + dcf_guarded)
  - le assunzioni passano il recinto?     (valida_assunzioni: OK/WARN/FAIL)
  - il g-guard rifiuta g fuori range?     (dcf_enterprise_value_guarded)
Più: confronto ke vs lo snapshot vecchio (quant-lite rf 3.85/erp 7.1) per mostrare
l'effetto del nuovo metodo (Bund 2.95 / Damodaran Italia 6.69 anti-doppio-conteggio).

I numeri quant sono deterministici: questo è metà del re-run (la CORRETTEZZA).
La varianza orchestrazione / token / latenza sta nel live run (run_batch, serve API).

Uso:  .venv/bin/python phase_a_correctness.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

POC = Path(__file__).parent
sys.path.insert(0, str(POC))                                   # quant_real (patch copiata)
sys.path.insert(0, str(POC.parent / "kai-website" / "kbot" / "backend" / "vendor"))  # k2a_quant vendored

from quant_real import capm_cost_of_equity, ev_from_multiples, valida_assunzioni  # noqa: E402
from quant_real.dcf_guard import dcf_enterprise_value_guarded                     # noqa: E402
from k2a_quant.dcf import compute_dcf, DcfInput                                   # noqa: E402

SNAP = json.loads((POC / "data" / "snapshot_real.json").read_text())

# Mappa ATECO→settore per i 4 casi (la mappa completa la benedice Luca; qui i 4 in-target).
ATECO_SETTORE = {
    "71.12.10": "engineering_construction",   # studi di ingegneria
    "25.62.00": "machinery",                  # lavorazioni meccaniche conto terzi
    "62.01.00": "software_application",       # produzione software
    "55.10.00": "restaurant_hotel",           # alberghi
}
# Costo del debito dichiarato per caso (assunzione; nel live lo dichiara l'agente).
KD_PCT = {"01": 5.0, "02": 6.0, "03": 5.0, "04": 5.5}


def _series(bilanci, key):
    # serie cronologica crescente (vecchio→nuovo): i bilanci sono nuovo→vecchio
    vals = [b.get(key) for b in reversed(bilanci) if b.get(key) is not None]
    return [float(v) for v in vals]


def _cagr(series):
    if len(series) < 2 or series[0] <= 0:
        return None
    return (series[-1] / series[0]) ** (1 / (len(series) - 1)) - 1


def _wacc(ke_pct, kd_pct, pn, pfn, tax):
    e, d = float(pn), max(float(pfn), 0.0)   # net-cash → D=0 → wacc≈ke
    v = e + d
    ke, kd = ke_pct / 100, kd_pct / 100
    if v <= 0:
        return ke_pct
    return ((e / v) * ke + (d / v) * kd * (1 - tax)) * 100


def _fcf_forward(ebitda_last, tax, cagr_ric):
    """Assunzione FCF conservativa: EBITDA·(1−t)·0.85 (haircut capex/WC), crescita
    = min(CAGR ricavi storico, 8%). È l'assunzione 'ragionevole' che il recinto
    deve far passare; quella aggressiva (sotto) deve fallire."""
    g = min(cagr_ric if cagr_ric is not None else 0.05, 0.08)
    base = ebitda_last * (1 - tax) * 0.85
    return [round(base * (1 + g) ** i) for i in range(3)]


def analizza(case_id, doc):
    b = doc["bilanci"]
    last = b[0]
    ric, eb = float(last["ricavi_eur"]), float(last["ebitda_eur"])
    pn, pfn = float(last["patrimonio_netto_eur"]), float(last["pfn_eur"])
    ateco = doc["settore_ateco"].split(" ")[0].strip()
    settore = ATECO_SETTORE[ateco]
    tax = SNAP["country_data"]["italy"]["tax_rate"]
    ric_series, eb_series = _series(b, "ricavi_eur"), _series(b, "ebitda_eur")
    cagr_ric = _cagr(ric_series)

    # 1) ke (CAPM da snapshot reale)
    capm = capm_cost_of_equity(settore, pfn_eur=pfn, patrimonio_netto_eur=pn,
                               fatturato_eur=ric, snapshot=SNAP)
    ke_pct = capm["outputs"]["ke_pct"]
    wacc_pct = _wacc(ke_pct, KD_PCT[case_id], pn, pfn, tax)

    # 2) EV da multipli
    evm = ev_from_multiples(settore, ebitda_eur=eb, ricavi_eur=ric, snapshot=SNAP)
    ev_mult = evm["outputs"]["ev_eur"]

    # 3) recinto assunzioni (ragionevoli)
    fcf = _fcf_forward(eb, tax, cagr_ric)
    assunzioni = {"fcf_previsti_eur": fcf, "g_perpetuo_pct": 1.5, "costo_debito_pct": KD_PCT[case_id]}
    storici = {"ricavi_eur": ric_series, "ebitda_eur": eb_series}
    vad = valida_assunzioni(storici, assunzioni, settore, SNAP, patrimonio_netto_eur=pn)
    esito = vad["outputs"]["esito_globale"]

    # 4) DCF guarded (g in range)
    dcf = dcf_enterprise_value_guarded(
        {"fcf": fcf, "wacc": round(wacc_pct / 100, 4), "g_perpetual": 0.015, "terminal_method": "gordon"},
        settore, SNAP, compute_dcf, DcfInput)
    ev_dcf = dcf["outputs"].get("enterprise_value") if dcf.get("outputs") else None

    # confronto: ke con lo snapshot VECCHIO (3.85/7.1) per mostrare effetto metodo
    old = json.loads(json.dumps(SNAP))
    old["country_data"]["italy"]["rf_10y"], old["country_data"]["italy"]["erp"] = 0.0385, 0.0710
    ke_old = capm_cost_of_equity(settore, pfn_eur=pfn, patrimonio_netto_eur=pn,
                                 fatturato_eur=ric, snapshot=old)["outputs"]["ke_pct"]

    return {
        "case": case_id, "denom": doc["denominazione"], "settore": settore,
        "ricavi_2024": ric, "ebitda_2024": eb, "margine_ebitda_pct": round(eb / ric * 100, 1),
        "pn": pn, "pfn": pfn, "d_e": round(pfn / pn, 2),
        "ke_pct": ke_pct, "ke_pct_snapshot_vecchio": ke_old, "delta_ke_pp": round(ke_pct - ke_old, 2),
        "beta_levered": capm["outputs"]["beta_levered"], "size_premium_pct": capm["outputs"]["size_premium_pct"],
        "wacc_pct": round(wacc_pct, 2),
        "ev_multipli_eur": ev_mult, "metodo_multiplo": evm["outputs"]["metodo"],
        "fcf_forward": fcf, "valida_esito": esito,
        "ev_dcf_eur": ev_dcf, "peso_tv_warn": dcf["outputs"].get("__warn") if dcf.get("outputs") else None,
        "valida_checks": [f'{c["check"]}={c["esito"]}' for c in vad["outputs"]["checks"]],
        "provenance": {"ke": capm["call_id"], "ev_multipli": evm["call_id"],
                       "valida": vad["call_id"], "ev_dcf": dcf["call_id"]},
    }


def demo_recinto_fail():
    """Mostra che il recinto FAILa su assunzioni incoerenti (caso 02: turnaround a
    margine 5.4% che proietta FCF da margine 14%+) e che il g-guard rifiuta g fuori range."""
    doc = json.loads((POC / "data" / "cases" / "02-manifatturiero-turnaround.json").read_text())
    b = doc["bilanci"]; ric_series, eb_series = _series(b, "ricavi_eur"), _series(b, "ebitda_eur")
    aggressive = {"fcf_previsti_eur": [750000, 950000, 1200000], "g_perpetuo_pct": 1.5, "costo_debito_pct": 6.0}
    va = valida_assunzioni({"ricavi_eur": ric_series, "ebitda_eur": eb_series}, aggressive,
                           "machinery", SNAP, patrimonio_netto_eur=1100000)
    g_fuori = dcf_enterprise_value_guarded(
        {"fcf": [300000, 320000, 340000], "wacc": 0.12, "g_perpetual": 0.05, "terminal_method": "gordon"},
        "machinery", SNAP, compute_dcf, DcfInput)
    return {
        "recinto_su_assunzioni_aggressive": va["outputs"]["esito_globale"],
        "recinto_checks": [f'{c["check"]}={c["esito"]}' for c in va["outputs"]["checks"]],
        "g_5pct_fuori_range": g_fuori.get("errore", {}).get("code") if g_fuori.get("errore") else "ACCETTATO(!)",
        "g_range_ammesso": g_fuori.get("errore", {}).get("range_ammesso_pct"),
    }


def main():
    print(f"Snapshot: as_of={SNAP.get('as_of')}  italy rf={SNAP['country_data']['italy']['rf_10y']*100}%  "
          f"erp={SNAP['country_data']['italy']['erp']*100}%")
    print("=" * 100)
    out = []
    for cid in ("01", "02", "03", "04"):
        f = next(POC.glob(f"data/cases/{cid}-*.json"))
        r = analizza(cid, json.loads(f.read_text()))
        out.append(r)
        print(f"\n[{cid}] {r['denom']}  ({r['settore']})")
        print(f"     ricavi {r['ricavi_2024']/1e6:.2f}M  EBITDA {r['ebitda_2024']/1e3:.0f}k ({r['margine_ebitda_pct']}%)  D/E {r['d_e']}")
        print(f"     ke = {r['ke_pct']}%  (βL {r['beta_levered']}, size +{r['size_premium_pct']}%)   "
              f"[snapshot vecchio: {r['ke_pct_snapshot_vecchio']}% → Δ {r['delta_ke_pp']}pp]")
        print(f"     WACC = {r['wacc_pct']}%")
        print(f"     EV multipli = {r['ev_multipli_eur']/1e6:.2f}M  ({r['metodo_multiplo']})")
        print(f"     EV DCF = {r['ev_dcf_eur']/1e6:.2f}M" if r['ev_dcf_eur'] else "     EV DCF = (rifiutato)")
        print(f"     recinto assunzioni: {r['valida_esito']}   {r['valida_checks']}")
    print("\n" + "=" * 100)
    print("DIMOSTRAZIONE RECINTO (assunzioni incoerenti + g fuori range):")
    print(json.dumps(demo_recinto_fail(), indent=2, ensure_ascii=False))
    (POC / "out").mkdir(exist_ok=True)
    (POC / "out" / "phase_a_correctness.json").write_text(
        json.dumps({"snapshot_as_of": SNAP.get("as_of"), "casi": out, "demo_recinto": demo_recinto_fail()},
                   indent=2, ensure_ascii=False))
    print("\n→ out/phase_a_correctness.json")


if __name__ == "__main__":
    main()
