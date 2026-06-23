"""Test cablaggio vs_strutturale (app/strutturale.py).

Verifica lo stato ONESTO: resolver pronto, ma 2 blocchi su Luca (sanity_rules.json mancante
upstream → check crasha; nessun consumer boost). apply_strutturale degrada onesto, non finge.

Standalone: python tests/test_strutturale.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import strutturale  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


print("── senza input verifica_strutturale → onesto (cita StructBoost) ──")
_, meta = strutturale.apply_strutturale({}, {"tipo_intervento": "x"})
check("disponibile False", meta["disponibile"] is False)
check("nota cita lo slot/StructBoost mancante", "StructBoost" in meta["note"])

print("── verifica non mappata → onesto, nessuna fabbricazione ──")
r = strutturale.resolve_check("verifica_inesistente", {})
check("resolve_check ok=False su tipo non mappato", r["ok"] is False)

print("── con input reale: degrada onesto sul bug upstream (sanity_rules.json mancante) ──")
_, m3 = strutturale.apply_strutturale({}, {"verifica_strutturale": {
    "tipo": "resistenza_tubolare", "parametri": {"D_ext_mm": 168.3, "t_mm": 5.0, "fy_MPa": 275}}})
# o disponibile True (se per qualche motivo la sanity è OFF) o False con nota sul bug upstream
check("non finge: disponibile True col risultato OPPURE False con nota bug upstream",
      (m3["disponibile"] is True and m3.get("risultato")) or
      (m3["disponibile"] is False and ("upstream" in m3["note"] or "sanity" in m3["note"].lower())))

print("\nTEST STRUTTURALE " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
