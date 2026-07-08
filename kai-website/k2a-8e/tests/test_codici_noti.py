"""Whitelist codici primari italiani (owner-approved 8 lug) + timeout legale.

Bug prod: parere legale (primo_parere_legale) → grounding REFUSE perché il corpus
normattiva non aggancia 8 codici MAJOR (Consumo 206/2005, Privacy 196/2003, diritto
d'autore 633/1941, Proprietà industriale 30/2005, IRAP 446/1997…). I codici noti/stabili
vengono promossi a FONTE NOTA (come i reg. UE) → non bloccano; le norme fuori whitelist
restano strict.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import pipeline, grounding, settings  # noqa: E402

FAILS = []


def check(nome, cond):
    print(("  OK  " if cond else "  FAIL ") + nome)
    if not cond:
        FAILS.append(nome)


_D = {"meta": {"cliente": "Studio Rossi SRL"},
      "voci": [{"id": "v1", "titolo": "Parere",
                "contenuto": "Rilevano il D.Lgs. 206/2005 (Codice del Consumo), il D.Lgs. 196/2003, "
                             "la Legge 633/1941 sul diritto d'autore, il D.Lgs. 30/2005 e l'IRAP "
                             "(D.Lgs. 446/1997). Inoltre il D.L. 145/2013 e il DL 146/21.",
                "fonti": []}]}

enriched = pipeline._enrich_citazioni_normattiva(_D, [])
noti = [c["riferimento"] for c in enriched if c.get("fonte") == "codice_noto"]
check("Codice del Consumo promosso a fonte nota", any("206/2005" in n for n in noti))
check("Codice Privacy promosso", any("196/2003" in n for n in noti))
check("diritto d'autore promosso", any("633/1941" in n for n in noti))
check("IRAP 446/1997 promosso", any("446/1997" in n for n in noti))

# gate legale (strict_norme=True): i codici noti NON bloccano, i DL fuori-lista SÌ
blocks = grounding.blocks(grounding.integrity_findings(
    _D, citazioni=enriched, inputs={}, facts={}, strict=False, strict_norme=True))
det = " ".join(b["dettaglio"] for b in blocks)
check("nessun block sui codici noti (206/196/633/30/446)",
      all(x not in det for x in ("206/2005", "196/2003", "633/1941", "30/2005", "446/1997")))
check("DL fuori whitelist restano strict (145/2013 + 146/21 bloccano)",
      "145/2013" in det and "146/21" in det)

# fonte nota = SENZA testo verbatim (va in Fonti, non tra i testi normativi)
check("codici noti senza 'testo' (no finto verbatim)",
      all("testo" not in c for c in enriched if c.get("fonte") == "codice_noto"))

# timeout legale alzato (240s tagliava i parere ~7-8 min)
check("JOB_TIMEOUT_S >= 600 (copre generazione legale)", settings.JOB_TIMEOUT_S >= 600)

# ── fix mistag corpus: lo scraper salva i D.Lgs come 'legge_YYYY_N' → legge↔dlgs
#    resi reciprocamente compatibili nel filtro tipo; DM/DPR restano DISTINTI (guardia) ──
from app import normattiva as _N  # noqa: E402
check("alias: decreto_legislativo accetta 'legge'", "legge" in _N._TIPO_ALIASES["decreto_legislativo"])
check("alias: legge accetta 'decreto_legislativo'", "decreto_legislativo" in _N._TIPO_ALIASES["legge"])
check("guardia: DM NON accetta 'legge' (niente falso positivo DM↔L)",
      "legge" not in _N._TIPO_ALIASES["decreto_ministeriale"])
check("guardia: DPR resta distinto", "legge" not in _N._TIPO_ALIASES["decreto_presidente_repubblica"])

# relabel canonico: un D.Lgs noto agganciato dal corpus (che lo tiene come 'legge_') esce
# col nome/tipo giusto, non 'L. 206/2005'
from app.pipeline import _canon_riferimento  # noqa: E402
_lab = _canon_riferimento({"tipo": "decreto_legislativo", "numero": "206", "anno": 2005, "articolo": "18"},
                          "L. 206/2005, art. 18")
check("relabel: Codice del Consumo col nome canonico + articolo",
      "Codice del Consumo" in _lab and "D.Lgs" in _lab and "art. 18" in _lab)
check("relabel: norma fuori whitelist resta invariata",
      _canon_riferimento({"tipo": "decreto_legge", "numero": "145", "anno": 2013}, "D.L. 145/2013") == "D.L. 145/2013")

# ── supplemento bundlato: norme aggiunte non ancora nel corpus canonico (633/1941 diritto
#    d'autore + DL) si agganciano col verbatim via il fallback di find_by_estremi ──
if _N._supp_path():
    hh = _N.find_by_estremi(1941, "633", tipo="legge", limit=1)
    check("supplemento: 633/1941 grounded col verbatim reale",
          bool(hh) and "opere dell'ingegno" in (hh[0].get("testo", "").lower()))
    check("supplemento: DL 145/2013 grounded",
          bool(_N.find_by_estremi(2013, "145", tipo="decreto_legge", limit=1)))
    check("available() resta sul corpus principale (supplemento = fallback interno)",
          _N.available() == (_N._db_path() is not None))
else:
    print("  --  supplemento non presente (skip test bundle)")

print()
if FAILS:
    print(f"TEST CODICI-NOTI FAIL ❌ ({len(FAILS)})")
    sys.exit(1)
print("TEST CODICI-NOTI PASS ✅")
sys.exit(0)
