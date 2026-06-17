"""Matrice di routing boost su TUTTI i domini + casi AVVERSARI (settore vs intento,
parole ambigue cross-dominio). Risponde a: "come siamo sicuri che il mis-routing
non esca anche con le altre materie?". Ogni caso = un riepilogo conversazione
realistico → boost atteso. Se qualcosa sbaglia, è un bug di routing da fixare.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import os
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_URL", "https://x.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "x")
os.environ.setdefault("ANTHROPIC_API_KEY", "x")

from app.lib import catalog  # noqa: E402

# (nome, summary, boost_atteso)
CASI = [
    # --- dritti per dominio ---
    ("marketing dritto", {"reportType": "analisi marketing", "objective": "brand awareness e lead generation"}, "checkup_marketing"),
    ("seo dritto", {"reportType": "audit SEO", "objective": "posizionamento organico, keyword, traffico"}, "checkup_seo"),
    ("finanziario dritto", {"reportType": "analisi finanziaria", "objective": "bancabilità, margini, cash flow, rating"}, "checkup_finanziario"),
    ("legale_dd dritto", {"reportType": "due diligence M&A", "objective": "acquisizione di azienda target"}, "checkup_legale_dd"),
    ("legale_review dritto", {"reportType": "contract review", "objective": "revisione NDA e clausole del contratto"}, "checkup_legale_review"),
    ("parere legale dritto", {"reportType": "parere legale", "objective": "contenzioso, diffida, causa"}, "primo_parere_legale"),
    ("fiscale dritto", {"reportType": "diagnosi fiscale", "objective": "IVA, imposte, F24, dichiarazione dei redditi"}, "checkup_fiscale"),
    ("agevolazioni dritto", {"reportType": "agevolazioni", "objective": "bando, contributo, Sabatini, credito d'imposta"}, "checkup_agevolazioni"),
    ("edilizia dritto", {"reportType": "iter edilizio", "objective": "permesso di costruire, SCIA, titolo edilizio"}, "checkup_edilizia"),
    ("energia dritto", {"reportType": "diagnosi energetica EGE", "objective": "efficientamento, fotovoltaico, impianti termici"}, "checkup_energia"),
    ("sicurezza dritto", {"reportType": "sicurezza sul lavoro", "objective": "DVR, antincendio, RSPP, 81/08"}, "checkup_sicurezza_safetyboost"),
    ("hospitality dritto", {"reportType": "performance struttura ricettiva", "objective": "hotel, occupazione, RevPAR, ADR"}, "checkup_hospitality"),
    ("controllo dritto", {"reportType": "controllo di gestione", "objective": "cruscotto, KPI, reporting direzionale"}, "checkup_controllo"),

    # --- AVVERSARI: settore del cliente vs intento del report ---
    ("BUG storico: marketing+acquisizione clienti+edilizia", {"reportType": "analisi marketing", "objective": "brand awareness, acquisizione clienti", "scope": "edilizia, rinnovabili, tlc"}, "checkup_marketing"),
    ("energia+marketing (azienda rinnovabili che vuole marketing)", {"reportType": "marketing", "objective": "aumentare la visibilità della nostra azienda di energie rinnovabili e fotovoltaico"}, "checkup_marketing"),
    ("hotel+marketing (albergo che vuole marketing)", {"reportType": "marketing", "objective": "aumentare le prenotazioni del nostro hotel e la brand awareness"}, "checkup_marketing"),
    ("edile+marketing (impresa edile che vuole farsi conoscere)", {"reportType": "marketing", "objective": "far conoscere la nostra impresa edile sul territorio"}, "checkup_marketing"),
    ("studio legale+SEO (avvocati che vogliono SEO)", {"reportType": "audit SEO", "objective": "posizionare il sito del nostro studio legale"}, "checkup_seo"),
    ("fiscale + 'sicurezza sociale' (non safety, non marketing via social)", {"reportType": "diagnosi fiscale", "objective": "contributi previdenziali e sicurezza sociale, IVA"}, "checkup_fiscale"),
    ("finanza dopo 'acquisizione clienti' (non legale_dd)", {"reportType": "analisi finanziaria", "objective": "valutare la bancabilità dopo una forte acquisizione clienti"}, "checkup_finanziario"),
    ("contratto fornitura energia (legale, non energia)", {"reportType": "contract review", "objective": "revisione del contratto di fornitura di energia"}, "checkup_legale_review"),
    ("controllo + 'social' (kpi, non marketing)", {"reportType": "controllo di gestione", "objective": "cruscotto KPI e monitoraggio, anche dei costi social"}, "checkup_controllo"),
    ("hospitality KPI (performance hotel, non marketing)", {"reportType": "performance struttura ricettiva", "objective": "migliorare RevPAR e occupazione dell'hotel"}, "checkup_hospitality"),
    ("agevolazioni per impianto fotovoltaico (bando, non energia)", {"reportType": "agevolazioni e bandi", "objective": "credito d'imposta e bando per impianto fotovoltaico"}, "checkup_agevolazioni"),
]


def run():
    ok, fails = 0, []
    for nome, summ, atteso in CASI:
        r = catalog.suggest_boost(summ)
        got = r["id"] if r else None
        if got == atteso:
            ok += 1
        else:
            fails.append((nome, got, atteso))
    print(f"\nROUTING MATRIX: {ok}/{len(CASI)} corretti")
    for nome, got, atteso in fails:
        print(f"  FAIL  {nome}\n        → {got}  (atteso {atteso})")
    return fails


def test_routing_matrix_no_cross_domain_misroute():
    fails = run()
    assert not fails, f"{len(fails)} mis-route cross-dominio: {[(n, g, a) for n, g, a in fails]}"


if __name__ == "__main__":
    import sys as _s
    _s.exit(1 if run() else 0)
