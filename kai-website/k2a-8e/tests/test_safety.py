"""Test binder SafetyBoost (app/safety.py): R=P×D + totale/incidenza deterministici;
singole voci di costo flaggate (nessun prezzario Allegato XV).

Standalone: python tests/test_safety.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import safety  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


DELIV = {
    "cantiere": {"importo_lavori": 200000.0, "durata_gg": 120},
    "rischi": [
        {"voce": "Caduta dall'alto", "p": 3, "d": 4, "r": 99},   # r sbagliato → deve = 12
        {"voce": "Elettrico", "p": 2, "d": 3, "r": 1},           # → 6
    ],
    "costi_sicurezza": {"apprestamenti": 5000.0, "misure_preventive": 3000.0,
                        "dpi": 1500.0, "impianti": 2000.0, "procedure": 500.0,
                        "totale": 99999.0, "incidenza_pct": 0.0},  # totale/incidenza sbagliati
}

out, meta = safety.apply_safety(DELIV, {})

print("── rischi: r = p × d (matrice P×D=R), sovrascrive l'LLM ──")
check("rischio 1: r = 3×4 = 12 (era 99)", out["rischi"][0]["r"] == 12)
check("rischio 2: r = 2×3 = 6 (era 1)", out["rischi"][1]["r"] == 6)
check("meta conta 2 rischi ricalcolati", meta["rischi_ricalcolati_pxd"] == 2)

print("── costi_sicurezza: totale = Σ componenti, incidenza = totale/importo×100 ──")
cs = out["costi_sicurezza"]
# 5000+3000+1500+2000+500 = 12000 ; 12000/200000 = 6%
check("totale = 12000 (somma, non 99999)", cs["totale"] == 12000.0)
check("incidenza_pct = 6,0 (12000/200000×100)", abs(cs["incidenza_pct"] - 6.0) < 0.01)

print("── onestà: singole voci di costo flaggate (no prezzario Allegato XV) ──")
check("flag voci_non_validate presente", any("Allegato XV" in f for f in meta["voci_non_validate"]))
check("note dichiara totale/incidenza deterministici", "deterministic" in meta["note"])

print("── senza p/d: rischio non toccato (no fabbricazione) ──")
out2, _ = safety.apply_safety({"rischi": [{"voce": "x", "r": 5}]}, {})
check("rischio senza p/d resta com'è", out2["rischi"][0].get("r") == 5)

print("\nTEST SAFETY " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
