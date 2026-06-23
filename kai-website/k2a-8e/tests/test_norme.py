"""Test cablaggio k2a_norme_tecniche (app/norme.py).

search() invocato dal MCP; KB VUOTA → 0 riferimenti onesti (no crash, no fabbricazione).

Standalone: python tests/test_norme.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import norme  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


print("── search norme invocata: KB vuota → 0 riferimenti onesti ──")
out, meta = norme.apply_norme({}, {"tipo_intervento": "ristrutturazione", "comune": "Perugia"})
check("MCP invocato (disponibile True)", meta["disponibile"] is True)
check("query costruita dall'intervento", "ristrutturazione" in meta["query"])
check("0 riferimenti (KB vuota), nessuna fabbricazione", meta["n_riferimenti"] == 0)
check("nota dichiara KB vuota onesta", "VUOTA" in meta["note"] or "vuot" in meta["note"].lower())
check("provenance dichiara il tool", "norme" in meta["provenance"].lower())

print("── senza intervento → onesto ──")
_, m2 = norme.apply_norme({}, {})
check("disponibile False senza intervento", m2["disponibile"] is False)

print("\nTEST NORME " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
