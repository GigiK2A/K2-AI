"""Test delle pezze quant contro lo SNAPSHOT REALE di Luca (industry_multiples.json).

python tests/test_quant_patch.py → exit 0 se PASS. Carica lo snapshot vendorizzato,
gli aggiunge i 3 campi mancanti (g_range/banda = default spec §2) e verifica
capm / ev_from_multiples / valida_assunzioni / envelope CalcResult.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# La cartella ha un trattino → la carico come package sintetico "qp" e exec i
# moduli in ordine di dipendenza (i relative import "from . import snapshot" /
# "from .calc_result" si risolvono via sys.modules["qp.*"]).
pkg = types.ModuleType("qp")
pkg.__path__ = [str(ROOT)]
sys.modules["qp"] = pkg
for name in ("calc_result", "snapshot", "capm", "ev_multiples", "valida_assunzioni"):
    spec = importlib.util.spec_from_file_location(f"qp.{name}", ROOT / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"qp.{name}"] = m
    spec.loader.exec_module(m)
cr = sys.modules["qp.calc_result"]
capm = sys.modules["qp.capm"]
evm = sys.modules["qp.ev_multiples"]
va = sys.modules["qp.valida_assunzioni"]

SNAP_PATH = ROOT.parent / "kai-website" / "kbot" / "backend" / "vendor" / "k2a_quant" / "data" / "industry_multiples.json"
SNAP = json.loads(SNAP_PATH.read_text())
SNAP["as_of"] = "2026-01-05"
for s in SNAP["sectors"].values():
    s.setdefault("g_range_pct", [0.5, 2.0])
    s.setdefault("banda_cagr_fcf_pct", 8.0)

ok = True
def check(label, cond):
    global ok; ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")

# envelope
r = cr.calc_result("t", {"a": 1}, {"x": 2})
check("envelope ha call_id/inputs_hash/snapshot_as_of/trace/outputs", all(k in r for k in ("call_id", "inputs_hash", "snapshot_as_of", "trace", "outputs")))
check("inputs_hash invariante all'ordine chiavi", cr.inputs_hash({"a": 1, "b": 2}) == cr.inputs_hash({"b": 2, "a": 1}))

# CAPM da snapshot (restaurant_hotel: βU 0.88 ; italy rf 3.85% erp 7.1% tax 27.9%)
c = capm.capm_cost_of_equity("restaurant_hotel", pfn_eur=2_900_000, patrimonio_netto_eur=2_200_000, fatturato_eur=3_600_000, snapshot=SNAP)
check("capm outputs presenti", "outputs" in c and c["outputs"]["ke_pct"] > 0)
o = c["outputs"]
check(f"capm ke ~17.4% (={o['ke_pct']})", abs(o["ke_pct"] - 17.44) < 0.3)
check("capm legge beta/rf/erp dallo snapshot", o["beta_unlevered"] == 0.88 and o["risk_free_pct"] == 3.85 and o["erp_pct"] == 7.1)
check("capm trace presente (Hamada + CAPM)", len(c["trace"]) == 2)
check("capm settore inesistente → errore (no eccezione)", "errore" in capm.capm_cost_of_equity("inesistente", 1, 1, 1, SNAP))

# ev_from_multiples
e1 = evm.ev_from_multiples("restaurant_hotel", ebitda_eur=540_000, ricavi_eur=3_600_000, snapshot=SNAP)
check("ev EBITDA>0 = 540k*12.8 = 6.912M", e1["outputs"]["ev_eur"] == 6912000.0)
e2 = evm.ev_from_multiples("restaurant_hotel", ebitda_eur=-50_000, ricavi_eur=3_600_000, snapshot=SNAP)
check("ev EBITDA<=0 → EV/Ricavi 2.1x = 7.56M", e2["outputs"]["ev_eur"] == 7560000.0)

# valida_assunzioni — il recinto
v_bad = va.valida_assunzioni(
    storici={"ricavi_eur": [400, 420], "ebitda_eur": [-6, -6]},
    assunzioni={"fcf_previsti_eur": [60, 80, 100], "g_perpetuo_pct": 1.5, "costo_debito_pct": 5.0},
    settore="restaurant_hotel", snapshot=SNAP)
check("valida: margine incoerente (-1.4% → FCF 14%) → FAIL", v_bad["outputs"]["esito_globale"] == "FAIL")
v_g = va.valida_assunzioni(storici={"ricavi_eur": [100, 100]}, assunzioni={"g_perpetuo_pct": 5.0}, settore="restaurant_hotel", snapshot=SNAP)
check("valida: g=5% fuori range [0.5,2.0] → FAIL", v_g["outputs"]["esito_globale"] == "FAIL")
v_ok = va.valida_assunzioni(
    storici={"ricavi_eur": [1000, 1050, 1100], "ebitda_eur": [150, 158, 165]},
    assunzioni={"fcf_previsti_eur": [120, 126, 132], "g_perpetuo_pct": 1.5, "costo_debito_pct": 6.0},
    settore="restaurant_hotel", snapshot=SNAP)
check("valida: assunzioni sane → OK", v_ok["outputs"]["esito_globale"] == "OK")

print("\nTEST QUANT-PATCH " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
