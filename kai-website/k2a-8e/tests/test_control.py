"""ControlBoost — KPI Balanced Scorecard deterministici dai dati operativi."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jsonschema import Draft202012Validator  # noqa: E402

from app import control  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


def approx(a, b, tol=0.5):
    return a is not None and abs(float(a) - float(b)) <= tol


_FORM = {"mese": "giugno", "anno": 2024, "azienda": "Direzionale", "fatturato": 145000,
         "costi_operativi": 118000, "incassi": 130000, "pagamenti": 125000, "nuovi_clienti": 4,
         "clienti_persi": 1, "clienti_attivi": 45, "ore_lavorate": 2800, "ore_fatturabili": 2100,
         "posizione_cassa": 85000, "crediti": 210000, "concentrazione_top5_pct": 38,
         "target_budget": 150000}


def _kpis(out):
    d = {}
    for p in ("kpi_finanziaria", "kpi_cliente", "kpi_processi", "kpi_crescita"):
        for k in out.get(p, []):
            d[k["nome"]] = k
    return d


print("── apply_controlboost: 4 prospettive BSC calcolate dai dati operativi (no LLM) ──")
base = {"kpi_finanziaria": [], "alert": [], "trend_12_mesi": {"mesi": [], "fatturato": []}}
out, meta = control.apply_controlboost(base, _FORM)
K = _kpis(out)
check("Margine operativo = 27.000 (fatturato-costi)", approx(K["Margine operativo"]["valore"], 27000))
check("Margine % = 18,62", approx(K["Margine operativo %"]["valore"], 18.62, tol=0.1))
check("Cash flow = 5.000 (incassi-pagamenti) semaforo verde", approx(K["Cash flow del mese"]["valore"], 5000) and K["Cash flow del mese"]["semaforo"] == "verde")
check("Churn = 2,22% (persi/attivi) verde", approx(K["Churn rate"]["valore"], 2.22, tol=0.1) and K["Churn rate"]["semaforo"] == "verde")
check("DSO = 43,45 gg (crediti/fatt×30) verde", approx(K["DSO (giorni incasso)"]["valore"], 43.45, tol=0.1))
check("Utilizzo = 75% (ore_fat/ore_lav) giallo <80", approx(K["Utilizzo (billability)"]["valore"], 75) and K["Utilizzo (billability)"]["semaforo"] == "giallo")
check("Concentrazione top-5 = 38% ROSSO (>30, lower better)", K["Concentrazione top-5"]["semaforo"] == "rosso")
check("Raggiungimento budget = 96,67%", approx(K["Raggiungimento budget"]["valore"], 96.67, tol=0.1))

print("── alert generati per i KPI rosso/giallo (cause=array, scostamento=number) ──")
check("alert non vuoti", len(out["alert"]) >= 2)
check("alert su Concentrazione (rosso)", any(a["kpi"] == "Concentrazione top-5" for a in out["alert"]))
check("cause è una LISTA (schema)", all(isinstance(a["cause"], list) for a in out["alert"]))
check("scostamento_percentuale è un NUMBER (mai None)", all(isinstance(a["scostamento_percentuale"], (int, float)) for a in out["alert"]))

print("── schema-valido (i pezzi del binder) ──")
sch = json.load(open(str(Path(__file__).resolve().parent.parent / "blueprints/cruscotto-direzionale/output-schema.json")))
errs = [e for e in Draft202012Validator(sch).iter_errors(out)
        if e.path and str(e.path[0]) in ("kpi_finanziaria", "kpi_cliente", "kpi_processi", "kpi_crescita", "alert", "trend_12_mesi")]
check("0 errori schema sui campi calcolati", not errs)

print("── senza fatturato/costi → non tocca (il gate deciderà) ──")
out2, meta2 = control.apply_controlboost(base, {"mese": "x", "anno": 2024})
check("no dati minimi → nessun binder (meta None)", meta2 is None)

print("\nTEST CONTROL " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
