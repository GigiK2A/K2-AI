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
    ("M&A dritto (valutazione acquisizione)", {"reportType": "due diligence M&A", "objective": "acquisizione di azienda target"}, "checkup_ma"),
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

    # --- ESPANSIONE / MARKET-ENTRY: la DECISIONE è strategica, NON legale/finanziaria anche
    #     se il caso è pieno di termini di contratto (deal col distributore) o di investimento
    #     (eval espansione USA 15 lug: generava LegalBoost = report sbagliato) ---
    ("espansione USA integratori (era LegalBoost)", {"reportType": "valutazione ingresso mercato USA", "objective": "un grande distributore USA ci propone un contratto con esclusiva e clausole; conviene entrare nel mercato USA, quanto investire, rischio concentrazione cliente"}, "checkup_marketing"),
    ("distributore estero + contratto (strategy, non legale)", {"reportType": "espansione internazionale", "objective": "distributore estero, contratto di distribuzione, minimi garantiti, entrare nel mercato estero"}, "checkup_marketing"),
    ("internazionalizzazione + investimento (strategy, non finance)", {"reportType": "internazionalizzazione", "objective": "espansione all'estero, quanto investire, ROI, payback, break-even"}, "checkup_marketing"),

    # --- HR / ORGANIZZATIVO: una crisi organizzativa NON deve finire su StrategyBoost solo
    #     perché "crescita" è presente (bug routing 18 lug) → report generico (ControlBoost) ---
    ("crisi organizzativa post-crescita (era StrategyBoost)", {"reportType": "diagnosi", "objective": "l'azienda è cresciuta in fretta e ora c'è una crisi organizzativa", "scope": "turnover alto, perso il responsabile tecnico, leadership in crisi, ruoli e mansioni poco chiari, processi interni inefficaci, carico di lavoro insostenibile"}, "checkup_controllo"),
    ("turnover + riorganizzazione (org, non marketing)", {"reportType": "analisi", "objective": "turnover elevato e riorganizzazione dei ruoli, clima aziendale peggiorato, conflitti interni"}, "checkup_controllo"),
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


def test_user_text_intent_wins_over_site_derived_reporttype():
    """BUG live giu 2026 (studio commercialista): l'LLM mette reportType='analisi bilancio'
    (dal SITO letto) ma l'utente chiede ESPLICITAMENTE un audit SEO. L'intento dell'utente,
    passato come user_text, deve vincere in PASS 1 → checkup_seo, non checkup_finanziario."""
    out = catalog.suggest_boost(
        {"reportType": "analisi bilancio", "notes": "studio associato, consulenza"},
        explicit_only=True,
        user_text="ciao, vorrei un parere seo sul mio sito internet — il sito è https://studio.com",
    )
    assert out is not None and out["id"] == "checkup_seo", out


def test_user_text_none_backward_compatible():
    """Senza user_text il routing è identico a prima (nessuna regressione)."""
    assert catalog.suggest_boost({"reportType": "analisi bilancio"})["id"] == "checkup_finanziario"
    assert catalog.suggest_boost({"reportType": "audit SEO"})["id"] == "checkup_seo"


def test_legit_finance_stays_finance_with_user_text():
    """Se l'utente parla DAVVERO di finanza, resta finanza anche col nuovo user_text."""
    out = catalog.suggest_boost(
        {"reportType": "analisi finanziaria"}, explicit_only=True,
        user_text="voglio capire la bancabilità e i margini, analisi del bilancio",
    )
    assert out is not None and out["id"] == "checkup_finanziario", out


def test_negated_financial_terms_do_not_route_to_finance():
    """QA S9 «senza dati»: l'utente dice che NON ha bilancio/fatturato. I termini NEGATI non
    sono intento → NON deve instradare a FinanceBoost (che poi chiede proprio quei dati)."""
    out = catalog.suggest_boost(
        {}, user_text="consulenza aziendale servizi, non ho numeri né fatturato né bilancio, voglio un report")
    assert out is None or out["id"] != "checkup_finanziario", out
    out2 = catalog.suggest_boost({}, user_text="vorrei un'analisi ma senza bilancio e senza fatturato")
    assert out2 is None or out2["id"] != "checkup_finanziario", out2
    # positivo: la finanza NON negata resta finanza (nessuna regressione)
    out3 = catalog.suggest_boost({}, user_text="analisi del bilancio e cash flow, margini e liquidità")
    assert out3 is not None and out3["id"] == "checkup_finanziario", out3


def test_user_intent_marketing_seo_beats_sector_edilizia():
    """BUG live giu 2026 #2 (studio rinnovabili+edilizia): l'utente chiede marketing+SEO ma
    nomina il SETTORE 'edilizia'/'rinnovabili'. Lo score-based di _match deve far vincere
    l'INTENTO (seo/marketing, più menzionato), NON BuildBoost (checkup_edilizia) per via
    dell'ordine-dominio. Era la regressione del primo tentativo di fix."""
    out = catalog.suggest_boost(
        {"reportType": "analisi marketing", "objective": "posizionamento, keyword, funnel, contenuti"},
        explicit_only=True,
        user_text=("valutazione marketing e seo del sito, strategia keyword e seo, funnel, "
                   "contenuti, settore rinnovabili ed edilizia, clienti privati o aziende"),
    )
    assert out is not None, out
    assert out["id"] != "checkup_edilizia", out
    assert out["id"] in ("checkup_seo", "checkup_marketing"), out


def test_mna_conversation_routes_to_maboost_not_finance():
    """L'M&A instrada su MABoost (analisi DECISIONALE comprare-vs-crescere: EV/EBITDA,
    ROI, confronto alternative), NON su FinanceBoost (che fail-close sulle proiezioni)
    né su LegalBoost DD (compliance, non decisione — bug del test acquisizione lug 2026).
    Una frase M&A esplicita batte le parole finance INCIDENTALI (bilancio/payback/utile)."""
    out = catalog.suggest_boost({}, user_text=(
        "Sto valutando di acquistare una azienda di telecomunicazioni. Fattibilità economica, "
        "utile post-fusione, sinergie, payback, prezzo di acquisizione, bilancio del target. Procediamo"))
    assert out is not None and out["id"] == "checkup_ma", out
    # variante con apostrofo tipografico
    out2 = catalog.suggest_boost({}, user_text=(
        "sto valutando di acquistare un’azienda concorrente, ho il suo bilancio, "
        "voglio capire margini e payback"))
    assert out2 is not None and out2["id"] == "checkup_ma", out2
    # il caso esatto del test K2-AI: la DECISIONE comprare-vs-crescere
    out3 = catalog.suggest_boost({}, user_text=(
        "Sto valutando l'acquisizione di una piccola azienda concorrente della mia zona. "
        "Non so se convenga acquistarla oppure crescere internamente."))
    assert out3 is not None and out3["id"] == "checkup_ma", out3


def test_mna_weight_does_not_hijack_marketing_or_finance():
    """Il peso DD non deve dirottare: 'acquisizione clienti' resta marketing; finance puro
    resta finance."""
    out = catalog.suggest_boost({}, user_text=(
        "strategia di acquisizione clienti, funnel marketing e campagne social"))
    assert out is not None and out["id"] == "checkup_marketing", out
    out2 = catalog.suggest_boost({}, user_text=(
        "analisi del bilancio e cash flow, margini e liquidità, bancabilità"))
    assert out2 is not None and out2["id"] == "checkup_finanziario", out2


if __name__ == "__main__":
    import sys as _s
    _s.exit(1 if run() else 0)
