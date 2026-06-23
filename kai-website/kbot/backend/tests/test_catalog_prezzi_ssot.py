"""§6 (handoff Luca) — il CATALOGO è l'unica fonte dei prezzi Boost (claim C2).

Il prezzo che paga il cliente esce SEMPRE da `catalog.prezzo_eur`, mai scritto a mano
nel codice o nelle skill. Questi test pinnano il caso di deriva noto (HostBoost = 690,
non 899) e bloccano il ritorno di un prezzo Boost hardcoded nel checkout.
Deterministici, no rete/DB/Stripe."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.lib import billing, catalog  # noqa: E402

_BACKEND = Path(__file__).resolve().parent.parent


def test_hostboost_e_690_non_899():
    # La deriva citata nell'handoff: il catalogo dice 690; la skill diceva 899.
    assert catalog.prezzo_eur("checkup_hospitality") == 690


def test_accessor_ritorna_il_campo_del_catalogo():
    """prezzo_eur() NON applica override: ritorna esattamente il campo del catalogo,
    e ogni Boost vendibile+8e-generabile ha un prezzo valido."""
    boosts = catalog.lista_servizi(tipo="servizio")
    assert boosts, "nessun Boost a catalogo?"
    for s in boosts:
        sid = s["id"]
        assert catalog.prezzo_eur(sid) == int(s.get("prezzo_eur") or 0)
        if catalog.is_vendibile(sid) and catalog.is_8e_generabile(sid):
            assert catalog.prezzo_eur(sid) > 0, f"{sid} vendibile ma senza prezzo"


def test_sconto_boost_si_applica_sul_prezzo_del_catalogo():
    """Il path che usa davvero il checkout: prezzo base DAL CATALOGO → sconto abbonato
    via billing.prezzo_boost_scontato (-10% Pro / -20% Business). È quello che addebita
    Stripe (checkout.py): l'UNICO path corretto per lo sconto Boost."""
    base = catalog.prezzo_eur("checkup_hospitality")  # 690
    assert base == 690
    assert billing.prezzo_boost_scontato(base, "pro") == 621       # -10%
    assert billing.prezzo_boost_scontato(base, "business") == 552  # -20%
    assert billing.prezzo_boost_scontato(base, None) == base


def test_suggest_boost_explicit_only_intento_vince():
    """Routing chat: un intento ESPLICITO (es. bilancio/finanza) deve poter vincere sul
    contesto-pagina (tag_pillar). explicit_only=True ritorna il match o None (niente
    default), così il chiamante sovrascrive il boost solo quando l'utente è chiaro."""
    fin = {"notes": "vorrei valutassi il bilancio: salute finanziaria, redditività, investimento"}
    assert catalog.suggest_boost(fin, explicit_only=True)["id"] == "checkup_finanziario"
    assert catalog.suggest_boost({}, explicit_only=True) is None         # vuoto → tiene il corrente
    assert catalog.suggest_boost({}) is not None                          # non-explicit → default


def test_percorso_controllo_di_gestione():
    """La scala finanza di Luca (P1→P7) modellata come PERCORSO: tappe reali del
    catalogo, prezzi dal catalogo (SSOT). Guard contro reference morte — scheda_percorso
    droppa in silenzio gli id inesistenti, quindi un typo sparirebbe senza errore."""
    sch = catalog.scheda_percorso("controllo_di_gestione")
    assert sch is not None, "percorso non trovato (overlay non rigenerato in catalog.json?)"
    assert [t["id"] for t in sch["tappe"]] == \
        ["tappa_bilancio_pmi", "tappa_budget_forecast_pmi", "tappa_cruscotto_direzionale"], \
        "una tappa non risolve (id sbagliato → droppata in silenzio)"
    assert sch["prezzo_tappe_totale"] == 299 + 399 + 452            # prezzi dal catalogo
    assert sch["destinazione"]["id"] == "checkup_controllo"
    for cid in sch["entry_checks_id"]:                              # i lead magnet esistono
        assert catalog.get_servizio(cid) is not None, f"entry check '{cid}' non a catalogo"


def test_percorso_advisor_strategico():
    """Percorso AdvisorBoost: tappe reali del catalogo (settore→bilancio→posizionamento
    →sintesi) → destinazione checkup_advisor. Prezzi dal catalogo (SSOT)."""
    sch = catalog.scheda_percorso("advisor_strategico")
    assert sch is not None
    assert [t["id"] for t in sch["tappe"]] == \
        ["tappa_settore_pmi", "tappa_bilancio_pmi", "tappa_posizionamento_pmi", "tappa_advisor_sintesi"], \
        "una tappa non risolve (id sbagliato → droppata in silenzio)"
    assert sch["prezzo_tappe_totale"] == 349 + 299 + 449 + 753
    assert sch["destinazione"]["id"] == "checkup_advisor"


def test_prezzo_per_piano_rimosso():
    """Regression: catalog.prezzo_per_piano era dead code che ritornava SEMPRE il prezzo
    pieno (leggeva `abbonamenti` vuoti + `sconto_tappa_pct` invece di sconto_boost_pct).
    Rimosso: lo sconto Boost passa SOLO da billing.prezzo_boost_scontato. Questo blocca
    la sua resurrezione come mina silenziosa sul prezzo."""
    assert not hasattr(catalog, "prezzo_per_piano"), \
        "catalog.prezzo_per_piano è tornato: usa billing.prezzo_boost_scontato per lo sconto Boost"


def test_checkout_non_hardcoda_prezzi_boost():
    """Guard strutturale: l'amount Stripe del Boost si calcola da `prezzo_eur` del
    catalogo, mai da un numero a mano. Nessun prezzo di listino (≥600, soglia che
    evita le collisioni con i codici HTTP) deve comparire come letterale in checkout.py.
    L'unico prezzo letterale ammesso è il report legacy (REPORT_PRICE_EUR_CENTS=1900)."""
    src = (_BACKEND / "app" / "api" / "checkout.py").read_text(encoding="utf-8")
    prezzi_listino = {int(s["prezzo_eur"]) for s in catalog.lista_servizi(tipo="servizio")
                      if s.get("prezzo_eur") and int(s["prezzo_eur"]) >= 600}
    letterali = {int(n) for n in re.findall(r"(?<![\w.])(\d{3,5})(?![\w.])", src)}
    sovrapposti = prezzi_listino & letterali
    assert not sovrapposti, (f"prezzo Boost hardcoded in checkout.py: {sorted(sovrapposti)} "
                             f"— usa catalog.prezzo_eur(servizio_id)")


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
