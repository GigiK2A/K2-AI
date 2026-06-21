"""Test del motore fiscale DETERMINISTICO (app/tax.py) — Fix #4.

Aliquote/imposte da `grounding/tax-tables-fiscale.json` (consolidato verificato Luca,
as_of 2026-06-21), NON dall'LLM. Ogni risultato porta provenance (norma/articolo/as_of).
Voci locality/lista-dependent (addizionali, IRAP regionale, ATECO Tab.1) → PARAMETRIZZATE:
se non fornite, escluse con nota esplicita, mai inventate.

Standalone: python tests/test_tax.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import tax  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


def approx(a, b, tol=0.5):
    return a is not None and abs(a - b) <= tol


print("── IRPEF progressiva (23/33/43, L.199/2025) ──")
r = tax.irpef_lorda(40000)
# 28000*0,23 + 12000*0,33 = 6440 + 3960 = 10400
check("IRPEF su 40.000 = 10.400", approx(r["imposta_eur"], 10400))
check("IRPEF aliquota media ~26%", approx(r["aliquota_media_pct"], 26.0, tol=0.2))
check("IRPEF ha provenance (norma+articolo+as_of)", bool(r["fonte"]) and bool(r.get("as_of")))
r80 = tax.irpef_lorda(80000)
# 6440 + 33%*22000(7260) + 43%*30000(12900) = 26600
check("IRPEF su 80.000 = 26.600", approx(r80["imposta_eur"], 26600))
check("IRPEF su 0 = 0", tax.irpef_lorda(0)["imposta_eur"] == 0)

print("── IRES / IRAP / IVA (verified) ──")
ires = tax.ires(100000)
check("IRES 24% su 100.000 = 24.000", approx(ires["imposta_eur"], 24000) and approx(ires["aliquota_pct"], 24))
ir = tax.irap(200000)  # ordinario 3,9%
check("IRAP ordinaria 3,9% su 200.000 = 7.800", approx(ir["imposta_eur"], 7800) and approx(ir["aliquota_pct"], 3.9, 0.01))
irb = tax.irap(200000, tipo="banche", anno=2026)  # 6,65% effettiva 2026-2028
check("IRAP banche 2026 = 6,65% (maggiorazione L.199/2025)", approx(irb["aliquota_pct"], 6.65, 0.01))
irb25 = tax.irap(200000, tipo="banche", anno=2025)  # base 4,65% fuori periodo maggiorazione
check("IRAP banche 2025 = 4,65% base (no maggiorazione)", approx(irb25["aliquota_pct"], 4.65, 0.01))
check("IVA ordinaria = 22%", approx(tax.iva_aliquota()["aliquota_pct"], 22))
check("IVA ridotta 10%", approx(tax.iva_aliquota("ridotta_10")["aliquota_pct"], 10))

print("── locality-dependent: parametrizzato, non inventato ──")
ir_no_reg = tax.irap(200000)
check("IRAP senza aliquota regionale → nota esplicita (non inventata)",
      any("regional" in n.lower() for n in ir_no_reg.get("note", [])))
ir_reg = tax.irap(200000, aliquota_regionale_pct=0.92)
check("IRAP con variazione regionale fornita → applicata (3,9+0,92=4,82%)",
      approx(ir_reg["aliquota_pct"], 4.82, 0.01))

print("── carico fiscale stimato (società) ──")
c = tax.carico_fiscale_stimato(forma_giuridica="SRL", imponibile_eur=100000, valore_produzione_irap_eur=200000)
check("carico = IRES 24.000 + IRAP 7.800 = 31.800", approx(c["totale_eur"], 31800))
check("carico: dettaglio per imposta con provenance", all(d.get("fonte") for d in c["dettaglio"]))
check("carico: nota addizionali locality non incluse", any("addizional" in n.lower() or "regional" in n.lower() for n in c.get("note", [])))
# persona fisica → IRPEF invece di IRES
cpf = tax.carico_fiscale_stimato(forma_giuridica="ditta_individuale", imponibile_eur=40000, valore_produzione_irap_eur=50000)
check("ditta individuale → usa IRPEF (10.400 + IRAP)", approx(cpf["dettaglio"][0]["imposta_eur"], 10400))

print("\nTEST TAX " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
