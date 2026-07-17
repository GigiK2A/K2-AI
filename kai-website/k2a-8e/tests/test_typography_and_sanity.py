"""Regressione eval 'batterie industriali' (17 lug 2026) — numeri corrotti nel PDF.

CAUSA-RADICE (trovata empiricamente confrontando JSON del job reale vs PDF estratto):
gpt-oss emette U+2011 NON-BREAKING HYPHEN nei range ('€10‑12 M'); DMSans/DMMono NON hanno
il glifo → ReportLab lo scarta → in stampa '€1012 M', '048h', '23 anni'. Tutti i bug
storici di 'range corrotti' erano questo. Fix: normalize_typography (pipeline) +
fix_spacing (render belt). In più: bound-check importi implausibili e Role Assignment.
"""
from __future__ import annotations

from app import quality, styling

# stringa REALE dal JSON del job dell'eval (job_3382ae0e8a51): contiene U+2011
REALE = "finanziamento aggiuntivo di €10‑12 M per contenere il picco"


# ── normalizzazione tipografica ────────────────────────────────────────────────────────

def test_normalize_u2011_del_caso_reale():
    out = quality.normalize_typography({"s": REALE})
    assert "€10-12 M" in out["s"] and "‑" not in out["s"]


def test_normalize_tutti_i_trattini_esotici():
    s = "a‐b c‑d e‒f g−h i﹣j k－l"
    out = quality.normalize_typography({"s": s})["s"]
    assert out == "a-b c-d e-f g-h i-j k-l"


def test_normalize_spazi_speciali():
    out = quality.normalize_typography({"s": " x y z"})["s"]
    assert out == " x y z"


def test_normalize_preserva_en_em_dash():
    # – e — hanno il glifo e sono usati dal nostro stesso codice: NON toccarli
    out = quality.normalize_typography({"s": "range 10–12 — nota"})["s"]
    assert out == "range 10–12 — nota"


def test_fix_spacing_belt_del_render():
    assert "€10-12 M" in styling.fix_spacing(REALE)


def test_pdf_end_to_end_range_visibile(tmp_path):
    # con la normalizzazione, il range del caso reale DEVE sopravvivere all'estrazione PDF
    import subprocess, shutil
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    styling.register_fonts() if hasattr(styling, "register_fonts") else None
    S = styling.styles()
    doc = SimpleDocTemplate(str(tmp_path / "t.pdf"))
    doc.build([Paragraph(styling.html_escape(REALE), S["body"])])
    if shutil.which("pdftotext"):
        subprocess.run(["pdftotext", str(tmp_path / "t.pdf"), str(tmp_path / "t.txt")], check=True)
        txt = (tmp_path / "t.txt").read_text()
        assert "10-12" in txt and "1012" not in txt.replace("10-12", "")


# ── bound-check importi implausibili ───────────────────────────────────────────────────

def test_bound_check_taglia_importo_sopra_fatturato():
    d = {"p": "miglioramento liquidità stimato €34 M (ipotesi da confermare)"}
    out, n = quality.bound_check_amounts(d, 42_000_000, known=set())
    assert n == 1 and "€34" not in out["p"] and "N/D" in out["p"]


def test_bound_check_risparmia_grounded_e_plausibili():
    d = {"a": "investimento €18 M a piano", "b": "contratto €20 M/anno",
         "c": "enterprise value €55 M"}
    known = {18.0, 18_000_000.0, 55.0, 55_000_000.0}
    out, n = quality.bound_check_amounts(d, 42_000_000, known)
    assert n == 0 and out == d  # 18/20 sotto fatturato; 55 grounded (EV legittimo)


def test_bound_check_noop_senza_fatturato():
    d = {"p": "beneficio €99 M"}
    out, n = quality.bound_check_amounts(d, None, set())
    assert n == 0 and out == d


# ── Role Assignment Engine ─────────────────────────────────────────────────────────────

def test_role_it_su_scorte_corretto():
    d = {"piano": [{"azione": "Ottimizzazione delle scorte di magazzino", "responsabile": "IT"}]}
    out, n = quality.fix_owner_assignments(d)
    assert n == 1 and out["piano"][0]["responsabile"] == "Operations / Supply Chain"


def test_role_commercialista_su_negoziazione_corretto():
    d = {"x": [{"azione": "Negoziazione termini con i clienti chiave", "responsabile": "Commercialista"}]}
    out, n = quality.fix_owner_assignments(d)
    assert n == 1 and out["x"][0]["responsabile"] == "Direzione Commerciale"


def test_role_avvocato_su_assicurazione_crediti_corretto():
    d = {"x": [{"azione": "Attivare assicurazione crediti commerciali", "responsabile": "Avvocato"}]}
    out, n = quality.fix_owner_assignments(d)
    assert n == 1 and "CFO" in out["x"][0]["responsabile"]


def test_role_plausibile_non_toccato():
    d = {"x": [{"azione": "Negoziazione con i clienti", "responsabile": "Direttore Commerciale"},
               {"azione": "Aggiornare il gestionale ERP", "responsabile": "IT"},
               {"azione": "Rivedere il DVR", "responsabile": "RSPP"}]}
    out, n = quality.fix_owner_assignments(d)
    assert n == 0 and out == d


# ── gusci LLM delle sezioni deterministiche (eval batterie: investment_summary tutto None) ──

def test_strip_deterministic_shells():
    from app import pipeline, assets
    sch = assets.load_output_schema("flusso-financeboost-pmi")
    shell = {"executive_summary": {"testo": "ok"},
             "investment_summary": {"npv": None, "chiavi": "sbagliate"},
             "decision_board": {"verdetto": None}}
    out = pipeline._strip_deterministic_shells(shell, sch)
    assert "investment_summary" not in out and "decision_board" not in out
    assert out["executive_summary"] == {"testo": "ok"}


def test_sezioni_deterministiche_sono_tutte_opzionali():
    # invariante: una sezione [Deterministico] non deve MAI essere required (lo strip
    # e lo skip del deep-gen la rimuovono: se fosse required la validazione fallirebbe)
    from app import assets
    for skill in ("flusso-financeboost-pmi", "flusso-strategyboost-pmi"):
        sch = assets.load_output_schema(skill)
        req = set(sch.get("required", []))
        det = {k for k, v in (sch.get("properties") or {}).items()
               if str((v or {}).get("description", "")).startswith("[Deterministico")}
        assert not (det & req), f"{skill}: sezioni deterministiche required: {det & req}"
