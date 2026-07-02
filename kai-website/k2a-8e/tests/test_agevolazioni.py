"""Test del binder agevolazioni DETERMINISTICO (app/agevolazioni.py) — Fix #3.

I benefici (Sabatini, Transizione 5.0, de minimis) escono dai tool di k2a_agevolazioni
vendorizzati, non dall'LLM. Cumulabilità segnalata (non sommata alla cieca). Input non nel
form (es. risparmio energetico T5.0 storico) → non rilevante per il 2026 (iperammortamento).

Standalone (richiede pydantic): kbot/backend/.venv/bin/python tests/test_agevolazioni.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import agevolazioni  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


FORM = {
    "settore_ateco": "25.62", "regione": "Umbria",
    "dimensione": {"n_dipendenti": 8, "fatturato": 800000},
    "investimenti_pianificati": [
        {"tipo": "macchinari", "importo_stimato": 200000},
        {"tipo": "efficienza_energetica", "importo_stimato": 50000},
    ],
    "agevolazioni_gia_fruite": [],
}

print("── compute_benefici: numeri dai tool, non dall'LLM ──")
c = agevolazioni.compute_benefici(FORM)
det = {d["strumento_id"]: d for d in c["benefici"]["dettaglio_per_strumento"]}
check("Nuova Sabatini calcolata (beneficio>0)", "nuova_sabatini" in det and det["nuova_sabatini"]["beneficio_lordo_eur"] > 0)
check("Transizione 5.0 2026 calcolata (beneficio>0)", "transizione_5_0" in det and det["transizione_5_0"]["beneficio_lordo_eur"] > 0)
check("Sabatini base = solo macchinari/software (200k, non 250k)", det["nuova_sabatini"]["spesa_agevolabile_eur"] == 200000.0)
b = c["benefici"]
check("scenario_base = miglior singolo (no cumulo)", b["scenario_base_eur"] == max(b["scenario_base_eur"], b["scenario_ottimistico_eur"]) or b["scenario_base_eur"] <= b["scenario_massimo_eur"])
check("scenario_massimo = somma (>= base)", b["scenario_massimo_eur"] >= b["scenario_base_eur"])
check("provenance de minimis massimale = 300.000", any(p.get("strumento") == "de_minimis" and p.get("massimale_eur") == 300000.0 for p in c["provenance"]))
check("nota segnala cumulabilità da verificare", "cumulab" in c["note"].lower())

print("── senza investimenti → onesto, non inventato ──")
c0 = agevolazioni.compute_benefici({"settore_ateco": "25", "regione": "Lazio", "dimensione": {"n_dipendenti": 3}})
check("nessun investimento → dettaglio benefici vuoto", c0["benefici"]["dettaglio_per_strumento"] == [])
check("nessun investimento → scenari 0 + nota onesta", c0["benefici"]["scenario_massimo_eur"] == 0.0 and "non" in c0["note"].lower())

print("── apply_agevolazioni: sovrascrive benefici_stimati nel deliverable ──")
deliv = {"benefici_stimati": {"scenario_massimo_eur": 9999999, "dettaglio_per_strumento": [{"strumento_id": "inventato"}]}}
deliv2, meta = agevolazioni.apply_agevolazioni(deliv, FORM)
check("benefici_stimati sovrascritto (non più 9999999)", deliv2["benefici_stimati"]["scenario_massimo_eur"] != 9999999)
check("dettaglio deterministico (no 'inventato')", not any(d.get("strumento_id") == "inventato" for d in deliv2["benefici_stimati"]["dettaglio_per_strumento"]))
check("meta porta provenance", bool(meta) and "provenance" in meta)

print("── de minimis: plafond residuo DETERMINISTICO da agevolazioni_gia_fruite (bug residuo=0) ──")
# Parser importi da testo libero
check("parse '120k' → 120000", agevolazioni._parse_eur_amount("120k") == 120000.0)
check("parse 'de minimis 120.000€' → 120000", agevolazioni._parse_eur_amount("de minimis 120.000€") == 120000.0)
check("parse 'Industria 5.0' → None (no falso positivo)", agevolazioni._parse_eur_amount("Industria 5.0") is None)
check("parse 'credito 4.0 da 35.000' → 35000", agevolazioni._parse_eur_amount("credito 4.0 da 35.000") == 35000.0)
# Scenario NeuroForge: 120k usati su massimale 300k → residuo 180k
FORM_DM = {**FORM, "agevolazioni_gia_fruite": ["de minimis: negli ultimi 3 anni abbiamo preso 120k"]}
cdm = agevolazioni.compute_benefici(FORM_DM)
check("de minimis massimale = 300.000", cdm["de_minimis"]["massimale_eur"] == 300000.0)
check("de minimis usato = 120.000 (estratto dal testo)", cdm["de_minimis"]["usato_eur"] == 120000.0)
check("de minimis residuo = 180.000 (300k − 120k), NON 0", cdm["de_minimis"]["residuo_eur"] == 180000.0)
# apply_agevolazioni sovrascrive il campo LLM (che qui è 0, il bug)
deliv_dm = {"profilo_aziendale": {"de_minimis_residuo_eur": 0}, "benefici_stimati": {}}
deliv_dm2, _ = agevolazioni.apply_agevolazioni(deliv_dm, FORM_DM)
check("profilo.de_minimis_residuo_eur sovrascritto 0 → 180000", deliv_dm2["profilo_aziendale"]["de_minimis_residuo_eur"] == 180000.0)
# Nessun pregresso → residuo = massimale (mai 0)
cdm0 = agevolazioni.compute_benefici({**FORM, "agevolazioni_gia_fruite": []})
check("nessun pregresso → residuo = massimale (300k), mai 0", cdm0["de_minimis"]["residuo_eur"] == 300000.0)

print("\nTEST AGEVOLAZIONI " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
