"""Test binder MepBoost (app/mep.py).

EEM: payback/VAN/TIR ricalcolati da costo+risparmio col motore quant, non dall'LLM.
Termico/APE: marcato non_validato (tool assente), non fabbricato.

Standalone: python tests/test_mep.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import mep  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


def approx(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


# deliverable come dall'LLM: piano_eem con payback/van/tir FABBRICATI (999) + termico stima
DELIV = {
    "piano_eem": [
        {"intervento": "Relamping LED", "costo_eur": 10000.0, "risparmio_eur": 2000.0,
         "incentivo_eur": 0.0, "payback_anni": 999.0, "van_15y": 999.0, "tir_pct": 999.0},
        {"intervento": "Pompa di calore", "costo_eur": 10000.0, "risparmio_eur": 2000.0,
         "incentivo_eur": 4000.0, "payback_anni": 1.0},
        {"intervento": "Solo kWh, no €", "costo_eur": 5000.0, "risparmio_kwh": 8000.0},
    ],
    "audit_termico": {"generatore_tipo": "caldaia", "rendimento_pct": 91.0},
    "classe_raggiungibile": "B",
}

out, meta = mep.apply_mep(DELIV, {})  # nessun prezzo_kwh

print("── piano_eem: economia ricalcolata (quant), non LLM ──")
led = out["piano_eem"][0]
# VAN @5%/15a: -10000 + 2000·annuity(5%,15=10,3797) = 10759
check("VAN 15y ≈ 10759 (sovrascrive 999)", approx(led["van_15y"], 10759.4, 5.0))
check("payback ≈ 5 anni (sovrascrive 999)", approx(led["payback_anni"], 5.0, 0.6))
check("TIR ≈ 18,4% (sovrascrive 999)", approx(led["tir_pct"], 18.4, 1.5))

print("── incentivo riduce il costo netto → payback più corto ──")
pdc = out["piano_eem"][1]
# costo netto = 10000-4000 = 6000; payback = 6000/2000 = 3
check("payback ≈ 3 anni (incentivo scontato)", approx(pdc["payback_anni"], 3.0, 0.6))

print("── senza €/kWh: intervento solo-kWh saltato onesto (nessuna tariffa inventata) ──")
solo_kwh = out["piano_eem"][2]
check("risparmio_eur NON inventato", solo_kwh.get("risparmio_eur") is None)
check("payback NON calcolato senza risparmio_eur", solo_kwh.get("payback_anni") is None)
check("meta conta gli interventi ricalcolati (2)", meta["eem_economics"]["interventi_ricalcolati"] == 2)

print("── con €/kWh fornito: deriva risparmio_eur dai kWh ──")
out2, meta2 = mep.apply_mep({"piano_eem": [{"intervento": "X", "costo_eur": 5000.0, "risparmio_kwh": 8000.0}]},
                            {"prezzo_energia_eur_kwh": 0.25})
ek = out2["piano_eem"][0]
check("risparmio_eur = 8000·0,25 = 2000", approx(ek.get("risparmio_eur"), 2000.0, 0.1))
check("payback calcolato (5000/2000 ≈ 2,5)", approx(ek.get("payback_anni"), 2.5, 0.6))

print("── termico/APE: marcato non validato (tool assente), non fabbricato ──")
check("flag audit_termico presente", any("audit_termico" in f for f in meta["termico_non_validato"]))
check("flag classe_raggiungibile presente", any("classe_raggiungibile" in f for f in meta["termico_non_validato"]))
check("audit_termico NON mutato con campi non a schema", set(out["audit_termico"].keys()) <= {"generatore_tipo", "generatore_anno", "rendimento_pct", "non_conformita"})

print("\nTEST MEP " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
