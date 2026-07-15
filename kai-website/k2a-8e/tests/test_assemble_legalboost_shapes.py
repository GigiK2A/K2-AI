"""Regressione: assemble_legalboost tollera forme non-canoniche dell'LLM locale.

gpt-oss emette a volte `rischi` come lista di STRINGHE (o `mappa_rischi` con item
stringa) invece di oggetti → `r.get(...)` andava in AttributeError e faceva fallire
l'intero LegalBoost (crash prod M&A due diligence, 15 lug 2026).
"""
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test")

from app.pipeline import assemble_legalboost


_BP = {"voci": [{"id": "v1", "titolo": "Passività nascoste",
                 "argomenti_obbligatori": ["debiti fiscali", "contenziosi"]}]}


def test_rischi_lista_di_stringhe_non_crasha():
    meta = {"voci_meta": {"v1": {
        "rischi": ["Debiti fiscali pregressi non contabilizzati",
                   {"descrizione": "Contenzioso con ex fornitore", "gravita": "alta"}],
        "azioni": ["Richiedere estratto di ruolo"]}}}
    out = assemble_legalboost(_BP, {"v1": "testo"}, [], {"tipo_operazione": "acquisizione"}, meta)
    rischi = out["voci"][0]["rischi"]
    assert len(rischi) == 2
    assert all(isinstance(r, dict) and r["descrizione"] for r in rischi)
    # la stringa è diventata un rischio con default; il dict è preservato
    assert rischi[0]["gravita"] == "media" and rischi[0]["descrizione"].startswith("Debiti")
    assert rischi[1]["gravita"] == "alta"


def test_mappa_rischi_con_item_stringa_non_crasha():
    meta = {"voci_meta": {"v1": {"rischi": [], "azioni": []}},
            "mappa_rischi": ["spuria", {"semaforo": "rosso", "area": "fiscale"}]}
    out = assemble_legalboost(_BP, {"v1": "t"}, [], {}, meta)
    # non solleva; la mappa mista viene scartata (non tutti gli item sono validi)
    assert isinstance(out.get("mappa_rischi", out.get("sintesi_mappa_rischi", [])), list)


def test_rischi_vuoti_generano_fallback_dagli_argomenti():
    meta = {"voci_meta": {"v1": {"rischi": [], "azioni": []}}}
    out = assemble_legalboost(_BP, {"v1": "t"}, [], {}, meta)
    assert out["voci"][0]["rischi"]  # fallback dagli argomenti_obbligatori
