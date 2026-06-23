"""Test binder MepBoost audit_elettrico (app/elettrico.py) — cabla k2a_elettrico.

Caduta tensione + verifica terra dal MCP (CEI 64-8), non dall'LLM. Senza il dettaglio
per-circuito nel form → non valutabile onesto (nessun numero inventato).

Standalone: python tests/test_elettrico.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import elettrico  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


print("── circuito conforme + circuito fuori limite → non_conformita reale ──")
inputs = {"impianto_elettrico_dettaglio": {
    "sistema_terra": "TT", "RA_ohm": 20.0, "Idn_RCD_mA": 30.0,
    "circuiti": [
        {"nome": "Luci ufficio", "corrente_a": 20, "lunghezza_m": 30, "sezione_mm2": 6, "sistema": "trifase"},
        {"nome": "Linea lontana", "corrente_a": 30, "lunghezza_m": 80, "sezione_mm2": 2.5, "sistema": "trifase"},
    ]}}
deliv = {"audit_elettrico": {"conforme_dm37": True, "non_conformita": []}}  # LLM diceva "tutto ok"
out, meta = elettrico.apply_elettrico(deliv, inputs)
check("verificato dal MCP", meta["verificato"] is True)
check("2 circuiti verificati", meta["circuiti_verificati"] == 2)
ae = out["audit_elettrico"]
check("almeno 1 non conformità (linea lontana > 4%)", len(ae["non_conformita"]) >= 1)
check("non conformità cita la norma CEI", any("CEI" in n["norma"] for n in ae["non_conformita"]))
check("conforme_dm37 = False (c'è una NC)", ae["conforme_dm37"] is False)
check("gravita valida (enum schema)", all(n["gravita"] in ("critica", "maggiore", "minore") for n in ae["non_conformita"]))

print("── tutti i circuiti ok → conforme_dm37 True ──")
ok_inputs = {"impianto_elettrico_dettaglio": {"circuiti": [
    {"nome": "Corta", "corrente_a": 16, "lunghezza_m": 10, "sezione_mm2": 6}]}}
out2, meta2 = elettrico.apply_elettrico({"audit_elettrico": {}}, ok_inputs)
check("conforme_dm37 True quando nessuna NC", out2["audit_elettrico"]["conforme_dm37"] is True)

print("── senza dettaglio per-circuito → non valutabile onesto (no fabbricazione) ──")
out3, meta3 = elettrico.apply_elettrico({"audit_elettrico": {"conforme_dm37": True}}, {"impianto_elettrico": "trifase 400V"})
check("verificato=False senza dettaglio", meta3["verificato"] is False)
check("nota FEED chiara", "FEED" in meta3["note"] or "non valutabile" in meta3["note"])

print("\nTEST ELETTRICO " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
