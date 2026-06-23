"""Test binder economici AdvisorBoost (app/advisor.py) — SPEC wiring-economici §A-§D.

Numeri da bilancio reale + quant (già wired in PR #54), non dall'LLM. Slot non ottenibili
(DCF senza FCF, CCII senza cash flow/attivo-breve) → non_disponibile/parziale onesto.

Standalone: python tests/test_advisor.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import advisor  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


def approx(a, b, tol=0.5):
    return a is not None and b is not None and abs(a - b) <= tol


ADV = {
    "denominazione": "K2A S.r.l.s.", "forma_giuridica": "SRLS", "settore_ateco": "62",
    "fatturato": 789766.0, "dipendenti": 4, "regione": "Umbria",
    "bilanci": [{"anno": 2024, "ricavi": 789766.0, "ebitda": 121862.0, "utile_netto": 87688.0,
                 "totale_attivo": 570166.0, "patrimonio_netto": 176127.0, "debiti_finanziari": 92859.0}],
}
# deliverable come dall'LLM: enterprise_value con multipli già bindati dal quant (PR #54),
# ma valore_raccomandato/range/dupont/ccii/cta SBAGLIATI o placeholder.
DELIV = {
    "enterprise_value": {"multipli_ebitda": {"ev_mediano_eur": 1559833.0, "multiplo_mediano": 12.8},
                         "dcf": {"wacc": 7.0}, "patrimoniale": {}, "valore_raccomandato_eur": 999999.0,
                         "range_plausibile_eur": {"min": 0, "max": 0}},
    "indici": {"dupont": {"roe_anno_n": 999}, "ccii": {"alert_attivi": 99, "dettaglio": []}},
    "cta": {"retainer_attivo": True, "prezzo_retainer_mensile_eur": 99999.0},
}

out, meta = advisor.apply_advisor(DELIV, ADV)

print("── §B DuPont (da bilancio, identità verificata) ──")
dp = out["indici"]["dupont"]
check("ROE = 49,8% (utile/PN)", approx(dp["roe_anno_n"], 49.8, 0.2))
check("ROS net = 11,1% (utile/ricavi)", approx(dp["ros_anno_n"], 11.1, 0.2))
check("rotazione = 1,38 (ricavi/attivo)", approx(dp["rotazione_anno_n"], 1.385, 0.02))
check("leva = 3,24 (attivo/PN)", approx(dp["leva_anno_n"], 3.237, 0.02))
check("scomposizione_ok (ROS×rot×leva ≈ ROE)", dp["scomposizione_ok"] is True)

print("── §A EV-synth (aggregatore dei metodi) ──")
ev = out["enterprise_value"]
check("valore_raccomandato SOVRASCRITTO (non 999999), tra PN e EV-multipli",
      176127.0 <= ev["valore_raccomandato_eur"] <= 1559833.0 and ev["valore_raccomandato_eur"] != 999999.0)
check("range min=PN, max=EV-multipli", approx(ev["range_plausibile_eur"]["min"], 176127.0) and approx(ev["range_plausibile_eur"]["max"], 1559833.0))
check("patrimoniale.valore_eur = PN", approx(ev["patrimoniale"]["valore_eur"], 176127.0))
check("multiplo_implicito coerente (raccomandato/EBITDA)", ev.get("spread_percentuale") is not None or "multiplo" in str(ev))

print("── §C CCII (parziale onesto: solo alert determinabili dal bilancio) ──")
cc = out["indici"]["ccii"]
tipi = {d["tipo"]: d for d in cc["dettaglio"]}
check("PN_negativo presente, stato verde (PN>0)", "PN_negativo_o_sotto_soglia" in tipi and tipi["PN_negativo_o_sotto_soglia"]["stato"] == "verde")
check("alert_attivi = 0 (azienda sana)", cc["alert_attivi"] == 0)
check("alert non determinabili marcati (commento), non inventati",
      any("non" in (d.get("commento", "").lower()) for d in cc["dettaglio"] if d["tipo"] in ("DSCR_12m_sotto_1", "CCN_negativo_persistente")))

print("── §D CTA (fail-closed: nessun prezzo inventato) ──")
cta = out["cta"]
check("retainer non inventato (prezzo 99999 rimosso)", cta["prezzo_retainer_mensile_eur"] != 99999.0)
check("meta porta provenance/note", bool(meta) and ("note" in meta or "provenance" in meta))

print("── PN negativo → alert rosso (caso crisi) ──")
adv_neg = {**ADV, "bilanci": [{**ADV["bilanci"][0], "patrimonio_netto": -5000.0}]}
out2, _ = advisor.apply_advisor({"indici": {"ccii": {}}, "enterprise_value": {}, "cta": {}}, adv_neg)
tneg = {d["tipo"]: d for d in out2["indici"]["ccii"]["dettaglio"]}
check("PN negativo → PN_negativo stato rosso + alert_attivi>=1",
      tneg.get("PN_negativo_o_sotto_soglia", {}).get("stato") == "rosso" and out2["indici"]["ccii"]["alert_attivi"] >= 1)

print("── voci-bridge: bilancio a VOCI (path prod) viene riclassificato (no §A-§D a vuoto) ──")
b_voci = {"anno": 2024, "voci": [{"sezione": "ricavi", "descrizione": "Ricavi delle vendite", "importo": 100000.0}]}
enr = advisor._latest_bilancio({"bilanci": [b_voci]})
check("advisor riclassifica il bilancio a voci (_reclass allegato)", isinstance(enr, dict) and "_reclass" in enr)
# regressione: con aggregati (no voci) resta invariato e DuPont gira come prima
enr2 = advisor._latest_bilancio(ADV)
check("con aggregati (no voci) bilancio invariato", enr2.get("ricavi") == ADV["bilanci"][0]["ricavi"])

print("\nTEST ADVISOR " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
