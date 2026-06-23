"""Test binder BuildBoost (app/build.py): totale_eur = Σ voci deterministico;
oneri/lavori/tempi flaggati (nessuna tabella/prezzario).

Standalone: python tests/test_build.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import build  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


DELIV = {
    "costi": {"lavori_eur": 100000.0, "professionisti_eur": 12000.0,
              "oneri_eur": 8000.0, "contingency_eur": 5000.0, "totale_eur": 999999.0},
    "iter": {"oneri_comunali_eur": 8000.0, "tempo_totale_mesi": 6.0},
}

out, meta = build.apply_build(DELIV, {})

print("── costi.totale_eur = Σ voci (sovrascrive 999999) ──")
# 100000+12000+8000+5000 = 125000
check("totale_eur = 125000", out["costi"]["totale_eur"] == 125000.0)
check("meta riporta le 4 voci sommate", len(meta["costi_totale"]["voci_sommate"]) == 4)

print("── onestà: oneri/lavori/tempi flaggati (no tabelle) ──")
check("flag oneri_eur (per-comune)", any("oneri_eur" in f for f in meta["voci_non_validate"]))
check("flag lavori_eur (prezzario)", any("lavori_eur" in f for f in meta["voci_non_validate"]))
check("flag iter tempi/oneri comunali", any("iter" in f for f in meta["voci_non_validate"]))

print("── senza voci: nessuna fabbricazione del totale ──")
out2, meta2 = build.apply_build({"costi": {}}, {})
check("totale non calcolato senza voci", meta2["costi_totale"]["ricalcolato"] is False)

print("\nTEST BUILD " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
