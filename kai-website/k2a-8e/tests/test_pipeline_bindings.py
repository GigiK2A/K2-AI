"""Integration test: pipeline.apply_deterministic_bindings DISPATCHA all'hook giusto per-skill.

Chiude un buco reale: prima NESSUN test toccava il dispatch dentro pipeline.run() — i binder
erano testati solo in isolamento. Qui verifico che, dato uno skill, la pipeline SCATTI davvero
l'hook giusto e sovrascriva gli slot fabbricati dall'LLM.

Standalone: python tests/test_pipeline_bindings.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import pipeline  # noqa: E402

ok = True
FACTS: dict = {}


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


print("── MepBoost: dispatch → apply_mep + apply_elettrico (2 hook) ──")
deliv = {
    "piano_eem": [{"intervento": "LED", "costo_eur": 10000, "risparmio_eur": 2000,
                   "incentivo_eur": 0, "van_15y": 999, "payback_anni": 999, "tir_pct": 999}],
    "audit_elettrico": {"conforme_dm37": True, "non_conformita": []},
    "audit_termico": {"rendimento_pct": 91}, "classe_raggiungibile": "B",
}
inputs = {"impianto_elettrico_dettaglio": {"circuiti": [
    {"nome": "L1", "corrente_a": 30, "lunghezza_m": 80, "sezione_mm2": 2.5}]}}
out, meta = pipeline.apply_deterministic_bindings("flusso-mepboost-studio", deliv, FACTS, inputs, {})
check("hook mep scattato: van ricalcolato (non 999)", out["piano_eem"][0]["van_15y"] != 999)
check("meta porta 'mep'", "mep" in meta)
check("hook elettrico scattato: audit dal MCP, NC trovata + verificato",
      len(out["audit_elettrico"]["non_conformita"]) >= 1 and meta.get("elettrico", {}).get("verificato") is True)
check("meta porta 'elettrico'", "elettrico" in meta)

print("── SafetyBoost: dispatch → apply_safety (R=P×D + totale) ──")
ds = {"cantiere": {"importo_lavori": 200000}, "rischi": [{"p": 3, "d": 4, "r": 99}],
      "costi_sicurezza": {"apprestamenti": 5000, "dpi": 1500, "totale": 999}}
outs, ms = pipeline.apply_deterministic_bindings("flusso-safetyboost-studio", ds, FACTS, {}, {})
check("hook safety scattato: r=12 e totale=6500", outs["rischi"][0]["r"] == 12 and outs["costi_sicurezza"]["totale"] == 6500.0)
check("meta porta 'safety'", "safety" in ms)

print("── BuildBoost: dispatch → apply_build + apply_norme (2 hook) ──")
db = {"costi": {"lavori_eur": 100000, "professionisti_eur": 12000, "oneri_eur": 8000,
                "contingency_eur": 5000, "totale_eur": 999}}
outb, mb = pipeline.apply_deterministic_bindings("flusso-buildboost-studio", db, FACTS,
                                                 {"tipo_intervento": "ristrutturazione"}, {})
check("hook build scattato: totale=125000", outb["costi"]["totale_eur"] == 125000.0)
check("meta porta 'build' e 'norme_tecniche'", "build" in mb and "norme_tecniche" in mb)

print("── WebBoost: dispatch → apply_web (no rete: onesto, ma l'hook SCATTA) ──")
dw = {"diagnosi": {"seo_onpage": {"valutazione_sintetica": "x", "score": 80, "findings": []}}}
# url senza schema → fetch_html ritorna None subito (niente chiamata di rete nel test)
outw, mw = pipeline.apply_deterministic_bindings("flusso-webboost-pmi", dw, FACTS,
                                                 {"url": "esempio.it", "keywords_seed": ["x"]}, {})
check("meta porta 'web_onpage' (hook scattato)", "web_onpage" in mw)
check("score LLM non toccato senza fetch (onesto)", dw["diagnosi"]["seo_onpage"]["score"] == 80)

print("── Negativo: skill senza hook tecnico non triggera mep/safety/build ──")
_, mn = pipeline.apply_deterministic_bindings("flusso-legalboost-pmi", {"x": 1}, FACTS, {}, {})
check("nessun meta tecnico per legalboost", not any(k in mn for k in ("mep", "elettrico", "safety", "build", "web_onpage")))

print("\nTEST PIPELINE BINDINGS " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
