"""Grounding dei CODICI citati per abbreviazione (c.p./c.c./c.p.c.) + verbatim pulito.

Bug: i pareri legali citano 'art. 595 c.p.', '2043 c.c.', '700 c.p.c.' ma il motore
NON li agganciava al corpus normattiva (1.8GB, che i Codici li HA come
regio_decreto_1930_1398_art_595 ecc.) perché:
  1. extract_norm_refs riconosceva solo 'L. NNN/AAAA', non le abbreviazioni dei Codici;
  2. _query_estremi non metteva l'articolo nella MATCH → sui Codici (750-3000 artt.)
     pescava 8 chunk a caso, mai quello giusto;
  3. i chunk del corpus hanno un frontmatter YAML che finiva stampato come 'legge'.
Risultato: norme citate a memoria, senza verbatim, e appendice coi 3 placeholder fissi.

Le parti dipendenti dal corpus 1.8GB (grounding reale) sono verificate a mano/in prod;
qui i pezzi puri (estrazione, pulizia frontmatter, filtro placeholder) — offline.

Standalone: python tests/test_codici_abbrev.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import normattiva as N  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


print("── extract_norm_refs: Codici per abbreviazione → estremi del corpus ──")
refs = {(r["tipo"], r["numero"], r.get("articolo")): r["label"]
        for r in N.extract_norm_refs(
            "diffamazione art. 595 c.p. comma 3; exceptio veritatis art. 596 c.p.; "
            "illecito ex art. 2043 c.c.; inibitoria art. 700 c.p.c.; querela art. 124 c.p.; "
            "clausole vessatorie artt. 1341-1342 c.c.; ricorso al c.p.a. e c.p.i.")}
check("595 c.p. → regio_decreto 1398 art 595", ("regio_decreto", "1398", "595") in refs)
check("2043 c.c. → regio_decreto 262 art 2043", ("regio_decreto", "262", "2043") in refs)
check("700 c.p.c. → regio_decreto 1443 art 700", ("regio_decreto", "1443", "700") in refs)
check("124 c.p. → regio_decreto 1398 art 124", ("regio_decreto", "1398", "124") in refs)
check("range 'artt. 1341-1342 c.c.' → primo art 1341", ("regio_decreto", "262", "1341") in refs)
# c.p.a. (Cod. Proc. Amm.) e c.p.i. (Cod. Prop. Ind.) NON devono mappare su c.p.
labels = " ".join(refs.values()).lower()
check("c.p.a. NON confuso con c.p.", "c.p.a" not in labels)
check("c.p.i. NON confuso con c.p.", "c.p.i" not in labels)
check("nessun match spurio su 262 diverso da 2043/1341", all(
    a in ("2043", "1341") for (t, n, a) in refs if n == "262"))

print("── _clean_testo: rimuove il frontmatter YAML dei chunk 'Codici' ──")
raw = ("---\ntipo: regio_decreto\nanno: 1930\nnumero: '1398'\ntitolo_norma: Codice Penale\n"
       "fonte: Normattiva\n---\n\n# Art. 595 — Codice Penale\n\nArt. 595.\n(Diffamazione)\nChiunque...")
cleaned = N._clean_testo(raw)
check("frontmatter rimosso (inizia con '# Art.')", cleaned.startswith("# Art. 595"))
check("il testo di legge è conservato", "Diffamazione" in cleaned and "Chiunque" in cleaned)
check("no-op su testo senza frontmatter",
      N._clean_testo("# Art. 1\n\nSono protette…") == "# Art. 1\n\nSono protette…")

print("── _cit_referenced: filtra i placeholder fissi non pertinenti ──")
try:
    from app import pipeline as P
    full = "il caso discute clausole vessatorie art. 1341 c.c. e diffamazione art. 595 c.p."
    def cit(campo, rif):
        return {"campo": campo, "riferimento": rif}
    check("cc_1341 CITATO nel testo → tenuto",
          P._cit_referenced(cit("cc_1341", "Art. 1341 Codice Civile"), full) is True)
    check("cc_1342 NON citato → scartato",
          P._cit_referenced(cit("cc_1342", "Art. 1342 Codice Civile"), full) is False)
    check("dlgs231_25septies (sicurezza lavoro) fuori tema → scartato",
          P._cit_referenced(cit("dlgs231_25septies", "Art. 25-septies Responsabilità enti"), full) is False)
    check("citazione senza articolo → conservativa (tenuta)",
          P._cit_referenced(cit("gdpr", "Reg. UE 2016/679"), full) is True)
except ImportError as exc:
    print(f"  SKIP _cit_referenced (pipeline non importabile senza deps: {exc})")

print("\n" + ("TEST CODICI-ABBREV PASS ✅" if ok else "TEST CODICI-ABBREV FAIL ❌"))
sys.exit(0 if ok else 1)
