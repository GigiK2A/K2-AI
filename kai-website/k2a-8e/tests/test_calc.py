"""Test del calcolo deterministico indici (stopgap integrità FinanceBoost).

Standalone (stile repo): python tests/test_calc.py → exit 0 se PASS.
Garantisce: numeri deterministici e corretti, 'non_disponibile' mai inventato,
chiavi di altri boost non toccate.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import calc  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


b_full = {"anno": 2024, "ricavi": 1000000, "ebitda": 150000, "reddito_operativo": 120000,
          "utile_netto": 80000, "totale_attivo": 1200000, "patrimonio_netto": 500000,
          "debiti_finanziari": 300000, "attivo_corrente": 400000, "passivo_corrente": 250000,
          "rimanenze": 50000}
form_full = {"bilanci": [b_full]}

# Valori attesi deterministici
check("de = 0.6", calc.resolve_formula_fact("de", form_full)["valore"] == 0.6)
check("roe = 16.0%", calc.resolve_formula_fact("roe", form_full)["valore"] == 16.0)
check("ebitda_margin = 15.0%", calc.resolve_formula_fact("ebitda_margin", form_full)["valore"] == 15.0)
check("ros = 12.0%", calc.resolve_formula_fact("ros", form_full)["valore"] == 12.0)
check("roi = 10.0%", calc.resolve_formula_fact("roi", form_full)["valore"] == 10.0)
check("current_ratio = 1.6", calc.resolve_formula_fact("current_ratio", form_full)["valore"] == 1.6)
check("quick_ratio = 1.4", calc.resolve_formula_fact("quick_ratio", form_full)["valore"] == 1.4)
check("ccn = 150000", calc.resolve_formula_fact("ccn", form_full)["valore"] == 150000)

# Dato mancante → non_disponibile, MAI inventato
f_ros_missing = calc.resolve_formula_fact("ros", {"bilanci": [{"anno": 2024, "ricavi": 1000000}]})
check("ros senza EBIT → non_disponibile", f_ros_missing["tipo"] == "non_disponibile" and f_ros_missing["valore"] is None)
check("ccc → sempre non_disponibile (form non lo supporta)", calc.resolve_formula_fact("ccc", form_full)["tipo"] == "non_disponibile")

# Divisione per zero / PN nullo → non_disponibile, niente crash
f_de_zero = calc.resolve_formula_fact("de", {"bilanci": [{"anno": 2024, "debiti_finanziari": 100, "patrimonio_netto": 0}]})
check("PN=0 → de non_disponibile (no crash)", f_de_zero["tipo"] == "non_disponibile")

# Chiave non gestita → None (fallback alla formula testuale degli altri boost)
check("revpar → None (fallback)", calc.resolve_formula_fact("revpar", form_full) is None)

# Bilanci assenti → non_disponibile
check("no bilanci → non_disponibile", calc.resolve_formula_fact("de", {})["tipo"] == "non_disponibile")

# Serie pluriennale
f_serie = calc.resolve_formula_fact("de", {"bilanci": [
    {"anno": 2023, "debiti_finanziari": 400, "patrimonio_netto": 100},
    {"anno": 2024, "debiti_finanziari": 300, "patrimonio_netto": 100}]})
check("serie pluriennale presente", f_serie.get("serie") == {"2023": 4.0, "2024": 3.0})
check("valore = anno più recente", f_serie["valore"] == 3.0)

print("\nTEST CALC " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
