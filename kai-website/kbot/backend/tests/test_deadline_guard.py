"""deadline_guard — presidio deterministico 'solo alto rischio' (scelta Luca 17 lug):
scadenze/termini/soglie di LEGGE resi descrittivi in chat; numeri di BUSINESS intatti.
Il valore del guard sta tutto nel non fare falsi positivi: la batteria NON_TOCCARE è la
parte critica."""
import importlib

from app.lib import deadline_guard as dg


# ── scadenze/termini/soglie in contesto normativo → la cifra sparisce ─────────────────────
DA_TOCCARE = [
    ("Devi comunicare l'assunzione al Centro per l'Impiego entro 5 giorni lavorativi dalla data di assunzione.", "5 giorni"),
    ("La comunicazione obbligatoria va inviata entro le 24 del giorno antecedente.", "24 del giorno"),
    ("Il versamento IVA va fatto entro il 16 del mese successivo.", "16 del mese"),
    ("Per il ravvedimento operoso hai un termine di 30 giorni.", "30 giorni"),
    ("La dichiarazione va presentata 90 giorni dalla chiusura dell'esercizio.", "90 giorni"),
    ("Il licenziamento va impugnato entro 60 giorni dalla comunicazione.", "60 giorni"),
    ("La soglia del regime forfettario è di 85.000 euro.", "85.000"),
    ("La sanzione per omessa comunicazione è di 500 euro.", "500 euro"),
]

# ── numeri di business / dati utente / scadenze commerciali → INVARIATI ───────────────────
NON_TOCCARE = [
    "Con un fatturato di 500k, in marketing si spende tipicamente il 2-5%.",
    "Il CPC medio su Google Ads è tra 0,30 e 1,20 euro.",
    "Concordate col cliente il pagamento a 30 giorni dalla fattura.",
    "Il fornitore consegna in 3 giorni lavorativi.",
    "Il mercato del food delivery vale circa 5 miliardi di euro.",
    "Ho 5 dipendenti e fatturo 800.000 euro.",
    "Ti conviene un budget di 20.000 euro per il sito.",
    "Per una campagna social servono almeno 2-3 mesi di test.",
]


def test_softening_scadenze_e_soglie_di_legge():
    for testo, cifra in DA_TOCCARE:
        out = dg.sanitize(testo)
        assert cifra not in out, f"la cifra doveva sparire: {out!r}"
        assert out != testo
        assert "normativa" in out.lower()


def test_numeri_a_lettere_e_articolo_eliso():
    """Casi LIVE che sfuggivano: numero a lettere ('otto giorni'), articolo eliso ('l'8°'),
    'termine dei N', 'giorno N'. La regex \\d+ da sola non bastava."""
    reply = ("Devi trasmettere la comunicazione di assunzione al Centro per l'Impiego entro "
             "otto giorni dal primo giorno di lavoro (in pratica, entro l'8° giorno calendario "
             "successivo alla data di inizio rapporto). Se avviene dopo il termine dei 8 giorni "
             "ci sono sanzioni.")
    out = dg.sanitize(reply)
    assert "otto giorni" not in out and "8°" not in out and "8 giorni" not in out
    assert "normativa(" not in out            # spaziatura pulita attorno alla parentesi
    assert "normativao" not in out and "normativaa" not in out  # niente parola tagliata
    for t in ("Il versamento IVA va fatto entro il giorno 16 del mese successivo.",
              "Va comunicato entro quindici giorni lavorativi dalla registrazione."):
        assert not __import__("re").search(r"\b(?:otto|quindici|\d+)\s*giorn", dg.sanitize(t).lower())


def test_zero_falsi_positivi_su_numeri_di_business():
    for testo in NON_TOCCARE:
        assert dg.sanitize(testo) == testo, f"NON doveva toccare: {testo!r}"


def test_gate_di_contesto_senza_marcatori_legali_non_tocca():
    # stessa forma 'entro N giorni' ma SENZA contesto normativo → intatto
    t = "Ti mando il preventivo entro 3 giorni, poi decidiamo insieme."
    assert dg.sanitize(t) == t


def test_grammatica_pulita_no_doppi_articoli_o_spazi():
    out = dg.sanitize("La comunicazione va inviata entro le 24 del giorno antecedente.")
    assert "normativadel" not in out            # niente spazio mangiato
    assert "un un" not in out and "La la" not in out
    out2 = dg.sanitize("Per il ravvedimento hai un termine di 30 giorni.")
    assert "un un" not in out2


def test_env_disable(monkeypatch):
    monkeypatch.setenv("KBOT_DEADLINE_GUARD", "0")
    importlib.reload(dg)
    t = "Devi comunicare l'assunzione entro 5 giorni dalla data."
    try:
        assert dg.sanitize(t) == t  # disattivato → passthrough
    finally:
        monkeypatch.delenv("KBOT_DEADLINE_GUARD", raising=False)
        importlib.reload(dg)


def test_idempotente():
    t = "Il versamento IVA va fatto entro il 16 del mese successivo."
    once = dg.sanitize(t)
    assert dg.sanitize(once) == once  # già ripulito → non ri-modifica


def test_tassi_interessi_penali_di_legge():
    """Leak visto live: 'interessi di mora (tasso legale + 8 punti)'. Le misure di
    interesse/mora/penale di legge citate a memoria vanno rese descrittive."""
    for testo, cifra in [
        ("Gli interessi di mora sono pari al tasso legale + 8 punti.", "8 punti"),
        ("Applica interessi di mora del 10% annuo sulla fattura non pagata.", "10%"),
        ("La penale è del 5% per ogni giorno di ritardo.", "5%"),
    ]:
        out = dg.sanitize(testo)
        assert cifra not in out and "normativa" in out.lower(), out


def test_aliquote_e_tassi_bancari_non_toccati():
    """Le aliquote fiscali (IVA) e i tassi bancari/di business NON sono figure 'di legge'
    da softare: restano intatti (zero falsi positivi)."""
    for testo in ["L'IVA sugli alimentari è del 4%.",
                  "L'aliquota ordinaria IVA è il 22%.",
                  "La banca applica interessi del 3% sul conto.",
                  "Il mutuo ha un tasso del 4,5%.",
                  "In marketing si spende il 2-5% del fatturato."]:
        assert dg.sanitize(testo) == testo, testo


def test_dedup_ripetizione_frase_softata():
    """Se la stessa frase soft-ata compare più volte, dalla 2ª in poi diventa una variante
    leggera (niente 'entro il termine previsto dalla normativa' ripetuto 3 volte)."""
    t = ("Invia la comunicazione al Centro per l'Impiego entro 5 giorni; poi il versamento "
         "entro 10 giorni; infine la dichiarazione entro 30 giorni.")
    out = dg.sanitize(t)
    assert out.lower().count("entro il termine previsto dalla normativa") == 1
    assert "nei termini di legge" in out.lower()
