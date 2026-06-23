"""Test binder §E (app/budget.py) — piano_economico_finanziario dal MCP k2a_budget.

Golden K2A 2024 (stessi numeri del motore) + VALIDITÀ SCHEMA del piano prodotto
(36 mesi, scenari, sensitivity) contro l'output-schema reale di AdvisorBoost.

Standalone: python tests/test_budget.py → exit 0 se PASS.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import budget  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


def approx(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


# bilancio reale K2A 2024 (come nel golden del motore) + multiplo EV dal quant
INPUTS = {"bilanci": [{
    "anno": 2024, "ricavi": 789766.17, "ebitda": 121861.50,
    "ammortamenti": 12470.37, "oneri_finanziari": 13181.28, "pfn": -197149.54,
}]}
DELIV = {"enterprise_value": {"multipli_ebitda": {"multiplo_mediano": 12.8}},
         "piano_economico_finanziario": {"budget_mensile_36m": [], "scenari": {}, "sensitivity": [], "ipotesi_base": []}}

out, meta = budget.apply_budget(DELIV, INPUTS)
pef = out["piano_economico_finanziario"]

print("── budget 36m dal motore (golden K2A) ──")
check("disponibile", meta["disponibile"] is True)
check("36 mesi", len(pef["budget_mensile_36m"]) == 36)
anno1_ricavi = sum(m["ricavi"] for m in pef["budget_mensile_36m"][:12])
check("anno-1 ricavi ≈ 805.561 (base×1,02)", approx(anno1_ricavi, 805561.5, 50))
check("warning motore propagati (aliquota/no-carryforward)", "aliquota_effettiva_approssimata" in (meta.get("warnings_motore") or []))

print("── scenari (ricavi/EBITDA dal motore, EV = EBITDA_anno3 × 12,8) ──")
check("scenari sovrascritti (scenari_bound)", meta["scenari_bound"] is True)
sc = pef["scenari"]
check("base/ottimistico/pessimistico presenti", all(k in sc for k in ("base", "ottimistico", "pessimistico")))
check("ottimistico ricavi3 > base > pessimistico",
      sc["ottimistico"]["ricavi_anno3_eur"] > sc["base"]["ricavi_anno3_eur"] > sc["pessimistico"]["ricavi_anno3_eur"])
check("EV base = EBITDA_anno3 × 12,8", approx(sc["base"]["enterprise_value_eur"], sc["base"]["ebitda_anno3_eur"] * 12.8, 1.0))
check("delta_ev base = 0", approx(sc["base"]["delta_ev_vs_base_eur"], 0.0, 0.1))

print("── sensitivity (matrice 3 leve × ±Δ) ──")
variabili = {s["variabile"] for s in pef["sensitivity"]}
check("3 leve presenti (ricavi/margine/costi_fissi)", {"ricavi", "margine_variabile", "costi_fissi"} <= variabili)
check("ogni voce ha impatto_ebitda_eur", all("impatto_ebitda_eur" in s for s in pef["sensitivity"]))

print("── VALIDITÀ SCHEMA: pef conforme all'output-schema reale di AdvisorBoost ──")
schema = json.load(open(ROOT / "blueprints/flusso-advisorboost-pmi/output-schema.json"))
pef_schema = {**schema["properties"]["piano_economico_finanziario"], "$defs": schema.get("$defs", {})}
try:
    from jsonschema import Draft202012Validator
    errs = sorted(Draft202012Validator(pef_schema).iter_errors(pef), key=lambda e: list(e.path))
    check("piano_economico_finanziario VALIDO a schema", not errs)
    if errs:
        print("     primo errore:", errs[0].message[:120])
except ImportError:
    print("     (jsonschema non disponibile, skip validazione)")

print("── senza multiplo EV: 36m+sensitivity ok, scenari NON sovrascritti (onesto) ──")
out2, meta2 = budget.apply_budget({"piano_economico_finanziario": {"budget_mensile_36m": [], "scenari": {}, "sensitivity": []}}, INPUTS)
check("budget_mensile comunque bound", len(out2["piano_economico_finanziario"]["budget_mensile_36m"]) == 36)
check("scenari_bound False senza multiplo + nota", meta2["scenari_bound"] is False and "multiplo" in (meta2.get("note") or ""))

print("── input FORM-CONFORME (solo anno/ricavi/ebitda/debiti, no D&A/OF/PFN) → default + flag onesto ──")
# path produzione reale: l'intake porta solo gli aggregati base, NON ammortamenti/oneri/pfn
form_inputs = {"bilanci": [{"anno": 2024, "ricavi": 789766.17, "ebitda": 121861.5,
                            "debiti_finanziari": 92859.0}]}
df = {"enterprise_value": {"multipli_ebitda": {"multiplo_mediano": 12.8}},
      "piano_economico_finanziario": {"budget_mensile_36m": [], "scenari": {}, "sensitivity": []}}
outf, mf = budget.apply_budget(df, form_inputs)
peff = outf["piano_economico_finanziario"]
check("budget gira comunque (36 mesi)", len(peff["budget_mensile_36m"]) == 36)
check("flag onesto: D&A/OF assenti segnalato in meta", mf.get("da_of_assenti") is True)
check("ipotesi_base avverte di utile/FCF sovrastimati", any("sovrastima" in i.lower() for i in peff["ipotesi_base"]))
check("PFN derivata da debiti_finanziari (no pfn esplicito)", approx(mf.get("pfn_iniziale"), 92859.0, 0.1))
errs_f = sorted(Draft202012Validator(pef_schema).iter_errors(peff), key=lambda e: list(e.path))
check("pef form-conforme comunque VALIDO a schema", not errs_f)

print("── bilancio VOCI-based (path produzione): D&A/oneri/PFN dalla riclassificazione, non 0 ──")
# enrich_bilancio allega _reclass quando il bilancio arriva come voci (lo simulo qui):
# il binder deve leggere D&A/oneri/PFN dal _reclass, NON defaultare a 0
b_reclass = {"anno": 2024, "_reclass": {
    "ce": {"ricavi": 789766.17, "ebitda": 121861.5, "ammortamenti": 12470.37, "oneri_finanziari": 13181.28},
    "indici": {"pfn": -197149.54}, "sp": {}}}
dv = {"enterprise_value": {"multipli_ebitda": {"multiplo_mediano": 12.8}},
      "piano_economico_finanziario": {"budget_mensile_36m": [], "scenari": {}, "sensitivity": []}}
outr, mr = budget.apply_budget(dv, {"bilanci": [b_reclass]})
check("budget gira da voci-reclass (36 mesi)", len(outr["piano_economico_finanziario"]["budget_mensile_36m"]) == 36)
check("D&A/oneri NON azzerati (presi dal reclass) → da_of_assenti False", mr.get("da_of_assenti") is False)
check("PFN dal reclass (−197.149)", approx(mr.get("pfn_iniziale"), -197149.54, 1.0))

print("── senza bilancio → onesto ──")
_, meta3 = budget.apply_budget({}, {})
check("disponibile False senza bilancio", meta3["disponibile"] is False)

print("\nTEST BUDGET " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
