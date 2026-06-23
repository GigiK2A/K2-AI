"""Test del resolver quant DETERMINISTICO (app/quant.py) — Fix #0 Fase 1.

I numeri di valutazione (WACC, EV da multipli) di AdvisorBoost devono uscire dal quant
vendorizzato di Luca (k2a_quant @ 1d7d9c2), non dall'LLM. dcf resta parziale (FCF forward
non nel form). Guard onesti: settore finanziario / non coperto → non_disponibile, mai
inventato.

Standalone: python tests/test_quant.py → exit 0 se PASS. (Richiede pydantic — usare il
venv: ../kbot/backend/.venv/bin/python tests/test_quant.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import quant  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


# form AdvisorBoost realistico (numeri K2A riclassificati)
ADV = {
    "settore_ateco": "71.12", "fatturato": 789766.0,
    "bilanci": [{"anno": 2024, "ricavi": 789766.0, "ebitda": 121862.0, "utile_netto": 87688.0,
                 "totale_attivo": 570166.0, "patrimonio_netto": 176127.0, "debiti_finanziari": 92859.0}],
}

print("── multipli_ev (EV da multipli di settore) ──")
f_ev = quant.resolve_quant_fact("multipli_ev", ADV)
check("multipli_ev = valore_calcolato", bool(f_ev) and f_ev["tipo"] == "valore_calcolato")
check("multipli_ev valore > 0", bool(f_ev) and isinstance(f_ev.get("valore"), (int, float)) and f_ev["valore"] > 0)
check("multipli_ev ha call_id (provenance)", bool(f_ev) and bool(f_ev.get("call_id")))
check("multipli_ev ha snapshot_as_of", bool(f_ev) and bool(f_ev.get("snapshot_as_of")))
check("multipli_ev outputs.ev_eur presente", bool(f_ev) and "ev_eur" in (f_ev.get("outputs") or {}))
check("multipli_ev fonte = k2a-quant", bool(f_ev) and f_ev.get("fonte") == "k2a-quant")

print("── wacc (CAPM + ponderazione) ──")
f_w = quant.resolve_quant_fact("wacc", ADV)
check("wacc = valore_calcolato", bool(f_w) and f_w["tipo"] == "valore_calcolato")
check("wacc in range 0-30%", bool(f_w) and 0 < f_w.get("valore", -1) < 30)
check("wacc ha call_id", bool(f_w) and bool(f_w.get("call_id")))
check("wacc outputs.ke_pct presente", bool(f_w) and "ke_pct" in (f_w.get("outputs") or {}))

print("── dcf (parziale: FCF forward non nel form → onesto non_disponibile) ──")
f_d = quant.resolve_quant_fact("dcf", ADV)
check("dcf = non_disponibile", bool(f_d) and f_d["tipo"] == "non_disponibile")
check("dcf motivo cita gli FCF", bool(f_d) and "fcf" in (f_d.get("motivo", "").lower()))

print("── guard onesti (mai numero inventato) ──")
adv_bank = {**ADV, "settore_ateco": "64.19"}  # banking_regional → settore finanziario
f_wb = quant.resolve_quant_fact("wacc", adv_bank)
check("wacc settore finanziario → non_disponibile", bool(f_wb) and f_wb["tipo"] == "non_disponibile")
check("wacc finanziario: nessun valore", bool(f_wb) and f_wb.get("valore") is None)

print("── chiavi non-quant + input mancante ──")
check("chiave non quant (roe) → None (fallback al chiamante)", quant.resolve_quant_fact("roe", ADV) is None)
nd = quant.resolve_quant_fact("multipli_ev", {"settore_ateco": "25"})
check("senza bilanci → non_disponibile (no crash)", bool(nd) and nd["tipo"] == "non_disponibile")
nd_pn = quant.resolve_quant_fact("wacc", {"settore_ateco": "25", "fatturato": 100000.0,
                                          "bilanci": [{"anno": 2024, "patrimonio_netto": 0}]})
check("PN=0 → wacc non_disponibile (no div/0)", bool(nd_pn) and nd_pn["tipo"] == "non_disponibile")

print("── binding strutturale (il numero nel deliverable = quello del tool, non dell'LLM) ──")
facts = {
    "multipli_ev": quant.resolve_quant_fact("multipli_ev", ADV),
    "wacc": quant.resolve_quant_fact("wacc", ADV),
}
ev_val = facts["multipli_ev"]["valore"]
wacc_val = facts["wacc"]["valore"]
# deliverable come lo emette l'LLM: numeri SBAGLIATI negli slot enterprise_value
deliverable = {"enterprise_value": {"multipli_ebitda": {"ev_mediano_eur": 999999.0, "multiplo_mediano": 1.0},
                                    "dcf": {"wacc": 99.0}}}
bound, prov = quant.bind_quant_slots("flusso-advisorboost-pmi", deliverable, facts)
check("ev_mediano_eur SOVRASCRITTO col tool (non 999999)",
      bound["enterprise_value"]["multipli_ebitda"]["ev_mediano_eur"] == ev_val)
check("dcf.wacc SOVRASCRITTO col tool (non 99.0)",
      bound["enterprise_value"]["dcf"]["wacc"] == wacc_val)
check("provenance registrata con call_id", any(p.get("call_id") for p in prov))
check("provenance traccia il valore LLM sovrascritto", any(p.get("valore_llm_sovrascritto") == 999999.0 for p in prov))
check("binding skill non mappata = no-op", quant.bind_quant_slots("flusso-legalboost-pmi", {"x": 1}, facts)[0] == {"x": 1})

print("\nTEST QUANT " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
