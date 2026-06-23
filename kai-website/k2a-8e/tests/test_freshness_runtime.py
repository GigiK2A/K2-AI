"""Test del freshness-gate a RUNTIME (Fix #6-gate / P0-10).

Standalone: ../kbot/backend/.venv/bin/python tests/test_freshness_runtime.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import freshness  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


# evaluate puro — entry stale (marker superato) → finding
rules = [
    {"key": "tuir_11", "severity": "hard", "law": "IRPEF 3 scaglioni",
     "stale_markers": ["quattro scaglioni"], "evidence_any": ["tre scaglioni", "23/33/43"]},
    {"key": "altra", "severity": "soft", "law": "X", "evidence_any": ["ok"], "stale_markers": []},
]
entries_stale = {"tuir_11": {"testo": "imposta a quattro scaglioni"}, "altra": {"testo": "tutto ok qui"}}
f = freshness.evaluate(rules, entries_stale)
check("stale rilevato per tuir_11", any(x["key"] == "tuir_11" for x in f))
check("entry fresca (altra) non flaggata", not any(x["key"] == "altra" for x in f))

entries_fresh = {"tuir_11": {"testo": "tre scaglioni 23/33/43"}, "altra": {"testo": "ok"}}
check("snapshot fresco → nessun finding", freshness.evaluate(rules, entries_fresh) == [])

entries_missing = {}
fm = freshness.evaluate(rules, entries_missing)
check("entry assente → finding 'entry assente'", any("assente" in x["motivo"] for x in fm))

# stale_findings sullo snapshot REALE: oggi 0 hard (8/10 fresche, 2 soft) → lista vuota hard
real_hard = freshness.stale_findings(hard_only=True)
check("snapshot reale: 0 hard-stale oggi (gate non blocca nulla a torto)", real_hard == [])

# filtro per chiavi usate dal boost: chiave non normativa → nessun blocco
check("filtro used_keys non-normative → vuoto", freshness.stale_findings(used_keys={"de", "roe"}) == [])

print("\nTEST FRESHNESS-RUNTIME " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
