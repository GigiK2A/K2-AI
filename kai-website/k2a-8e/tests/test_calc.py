"""Test del calcolo deterministico formula-fact (FinanceBoost + HostBoost + Cruscotto).

Standalone: python tests/test_calc.py → exit 0 se PASS. I dati usano la STRUTTURA
REALE dei form.json (kpi_attuali per HostBoost, clienti_attivi per Cruscotto), non i
nomi assunti: è la riconciliazione che evita il fallimento silenzioso sui venduti.
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


def val(key, form):
    f = calc.resolve_formula_fact(key, form)
    return f.get("valore") if f else None


def nd(key, form):
    f = calc.resolve_formula_fact(key, form)
    return bool(f) and f["tipo"] == "non_disponibile"


# ───── bilancio (regressione: comportamento esistente invariato) ─────
b = {"anno": 2024, "ricavi": 1000000, "ebitda": 150000, "reddito_operativo": 120000,
     "utile_netto": 80000, "totale_attivo": 1200000, "patrimonio_netto": 500000,
     "debiti_finanziari": 300000, "attivo_corrente": 400000, "passivo_corrente": 250000,
     "rimanenze": 50000}
ff = {"bilanci": [b]}
check("de=0.6", val("de", ff) == 0.6)
check("roe=16.0", val("roe", ff) == 16.0)
check("ros=12.0", val("ros", ff) == 12.0)
check("roi=10.0", val("roi", ff) == 10.0)
check("ebitda_margin=15.0", val("ebitda_margin", ff) == 15.0)
check("current_ratio=1.6", val("current_ratio", ff) == 1.6)
check("quick_ratio=1.4", val("quick_ratio", ff) == 1.4)
check("ccn=150000", val("ccn", ff) == 150000)
check("ccc → non_disponibile", nd("ccc", ff))
check("de PN=0 → n/d (no crash)", nd("de", {"bilanci": [{"anno": 2024, "debiti_finanziari": 100, "patrimonio_netto": 0}]}))
serie = calc.resolve_formula_fact("de", {"bilanci": [
    {"anno": 2023, "debiti_finanziari": 400, "patrimonio_netto": 100},
    {"anno": 2024, "debiti_finanziari": 300, "patrimonio_netto": 100}]})
check("serie pluriennale + valore=anno recente", serie.get("serie") == {"2023": 4.0, "2024": 3.0} and serie["valore"] == 3.0)

# ───── hospitality (HostBoost) — KPI dichiarati in kpi_attuali ─────
host = {"nome": "Agriturismo X", "camere_totali": 10,
        "kpi_attuali": {"occupancy_pct": 54.8, "adr_eur": 73.0, "revpar_eur": 40.0}}
check("adr=73.0 (passthrough da kpi_attuali)", val("adr", host) == 73.0)
check("revpar=40.0 (passthrough)", val("revpar", host) == 40.0)
check("occupancy=54.8 (passthrough)", val("occupancy", host) == 54.8)
check("goppar → n/d (non nel form HostBoost)", nd("goppar", host))
nd_adr = calc.resolve_formula_fact("adr", {"camere_totali": 10})
check("adr senza kpi → n/d con campo giusto", nd_adr["tipo"] == "non_disponibile" and "adr_eur" in nd_adr["motivo"])

# ───── controllo (Cruscotto) — struttura form reale ─────
cru = {"mese": 6, "anno": 2026, "fatturato": 1000000, "costi_operativi": 820000,
       "incassi": 900000, "pagamenti": 850000, "crediti": 150000, "clienti_attivi": 200,
       "nuovi_clienti": 20, "clienti_persi": 12,
       "target_budget": {"fatturato_target": 950000, "ebitda_target": 200000}}
check("ctrl_ebitda=180000", val("ctrl_ebitda", cru) == 180000)
check("ctrl_cashflow=50000", val("ctrl_cashflow", cru) == 50000)
check("ctrl_churn=6.2 (base inizio periodo ricostruita)", val("ctrl_churn", cru) == 6.2)
check("ctrl_dso=4.5 (crediti/fatturato*30 mensile)", val("ctrl_dso", cru) == 4.5)
scost = val("ctrl_scost", cru)
check("ctrl_scost = lista per-KPI (ricavi +5.3, ebitda -10.0)",
      isinstance(scost, list) and {s["metrica"]: s["scostamento_pct"] for s in scost} == {"ricavi": 5.3, "ebitda": -10.0})
check("ctrl_scost senza target → n/d", nd("ctrl_scost", {"fatturato": 1000000}))

# ───── dcf/wacc restano fuori (quant) + div/0 ─────
check("dcf → None", calc.resolve_formula_fact("dcf", ff) is None)
check("wacc → None", calc.resolve_formula_fact("wacc", ff) is None)
check("ctrl_churn iniziali=0 → n/d", nd("ctrl_churn", {"clienti_attivi": 0, "nuovi_clienti": 0, "clienti_persi": 0}))

print("\nHANDLED:", sorted(calc.HANDLED))
print("\nTEST CALC " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
