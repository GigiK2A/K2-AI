"""Regressioni QA prod 8 lug 2026 (job 83b8bff0f30c, FinanceBoost BU-AI 500k).

Cinque bug in un report pagato:
  1. PN -165k INVENTATO (il cliente aveva fornito PN 500k): voci autofill classificate
     male → quadratura KO → ma i derivati garbage sovrascrivevano gli aggregati utente.
  2. Quadratura KO segnalata ma i calcoli continuavano sui dati rotti.
  3. KPI di scenario presentati come quasi-definitivi (banner render, non testato qui).
  4. 'Impatto: 2024.0' — anno trapelato in campo percent-like.
  5. Tabelle vuote: 'Voce:' senza numeri, card indici senza valore, 'True' raw.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import finance, quality  # noqa: E402

FAILS = []


def check(nome, cond):
    print(("  OK  " if cond else "  FAIL ") + nome)
    if not cond:
        FAILS.append(nome)


# ── scenario prod: aggregati utente BUONI + voci garbage ──────────────────────
B = {"anno": 2024,
     "ricavi": 1800000, "ebitda": 340000, "utile_netto": 165000,
     "patrimonio_netto": 500000, "debiti_finanziari": 430000,
     "voci": [  # classificazione storta simulata (autofill)
        {"descrizione": "patrimonio netto", "importo": 500000},
        {"descrizione": "debiti verso banche", "importo": 430000},
        {"descrizione": "utile netto", "importo": -165000},
     ]}

e = finance.enrich_bilancio(dict(B))
quad = (e.get("_reclass") or {}).get("quadratura") or {}
check("quadratura KO rilevata", quad.get("ok") is False)
check("bilancio marcato untrusted", e.get("_reclass_untrusted") is True)
check("PN utente 500k PRESERVATO (non il derivato garbage)", e.get("patrimonio_netto") == 500000)
check("utile utente preservato", e.get("utile_netto") == 165000)

# quadratura OK → i derivati continuano a vincere (comportamento storico invariato)
B_OK = {"anno": 2024, "patrimonio_netto": 1,  # aggregato LLM sbagliato
        "voci": [
            {"descrizione": "immobilizzazioni nette", "importo": 400000},
            {"descrizione": "disponibilità liquide", "importo": 100000},
            {"descrizione": "capitale sociale", "importo": 300000},
            {"descrizione": "debiti verso fornitori", "importo": 200000},
        ]}
e_ok = finance.enrich_bilancio(dict(B_OK))
if ((e_ok.get("_reclass") or {}).get("quadratura") or {}).get("ok"):
    check("quadratura OK → derivato batte aggregato LLM", e_ok.get("patrimonio_netto") != 1)

# ── fallback aggregati: indici VERI dai numeri del cliente ─────────────────────
agg = finance.reclass_from_aggregates(B)
idx = agg["indici"]
check("D/E dagli aggregati = 0.86", idx["de"] == 0.86)
check("ROE dagli aggregati = 33%", idx["roe"] == 33.0)
check("EBITDA margin = 18.9%", idx["ebitda_margin"] == 18.9)
check("indici build non vuoti", len(finance.build_indici(agg)) >= 3)

# ── sanitizer anno-trapelato ───────────────────────────────────────────────────
D = {"scenari": [{"nome": "pessimistico", "sensitivity": [
        {"variabile": "Pressione competitiva", "impatto": 49.0},
        {"variabile": "Tensione liquidità azienda madre", "impatto": 2024.0},  # bug prod
     ]}],
     "piano": [{"azione": "compra", "impatto_eur": 2024}]}     # € legittimo: intatto
out, n = quality.sanitize_implausible_numbers(D, {"bilanci": [{"anno": 2024}]})
check("voce anno-trapelato rimossa", n == 1 and len(out["scenari"][0]["sensitivity"]) == 1)
check("impatto percent legittimo intatto", out["scenari"][0]["sensitivity"][0]["impatto"] == 49.0)
check("campo monetario mai toccato", out["piano"][0]["impatto_eur"] == 2024)

# ── marginalita: niente flag booleano orfano ───────────────────────────────────
mar = finance.build_marginalita({})
check("marginalita senza flag bool residuo", "stima_da_aggregati" not in mar)

print()
if FAILS:
    print(f"TEST PROD-DATA-VALIDATION FAIL ❌ ({len(FAILS)})")
    sys.exit(1)
print("TEST PROD-DATA-VALIDATION PASS ✅")
sys.exit(0)
