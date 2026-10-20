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
    # 20/10/2026: soglia di costo unitario inventata dal modello su un computer (art. 102 c.5 TUIR dice 516,46)
    ("Per i beni strumentali il cui costo unitario è pari o inferiore a 2.000 euro puoi dedurre tutto subito.", "2.000"),
    ("I beni strumentali con un valore unitario fino a 300 € possono essere dedotti integralmente.", "300"),
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
    "Il prezzo unitario del tuo prodotto è inferiore a 50 euro, quindi il margine è basso.",
    "Il computer costa 2.500 euro: con l'ammortamento in 5 anni sono 500 euro l'anno.",
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


# ── la sostituzione non deve ROMPERE la frase (casi reali, produzione 15/10/2026) ──────────
# Prima: «è di nel termine previsto…», «Il pagamento a nel termine…», «hai nel termine…».
GRAMMATICA = [
    # (testo, frammento che NON deve comparire, frammento atteso)
    ("Il termine per opporsi al decreto ingiuntivo è di 40 giorni dalla notifica.",
     "di nel termine", "è quello previsto dalla normativa"),
    ("Per il versamento dell'IVA il pagamento a 30 giorni dalla fattura non vale.",
     "a nel termine", "pagamento nel termine previsto dalla normativa"),
    ("Dopo la notifica del ricorso hai 60 giorni dalla notifica per costituirti.",
     "hai nel termine", "hai il termine previsto dalla normativa"),
]


def test_la_sostituzione_lascia_frasi_integre():
    for testo, vietato, atteso in GRAMMATICA:
        out = dg.sanitize(testo)
        assert vietato not in out, (testo, out)
        assert atteso in out, (testo, out)
        assert "40 giorni" not in out and "30 giorni" not in out and "60 giorni" not in out, out


def test_la_grammatica_non_cambia_la_politica():
    # le forme già corrette restano com'erano
    out = dg.sanitize("Il licenziamento va impugnato entro 60 giorni dalla comunicazione.")
    assert "entro il termine previsto dalla normativa" in out
    assert "60 giorni" not in out


def test_la_soglia_di_costo_unitario_vera_resta_se_e_nel_testo_di_legge(monkeypatch):
    """Se il numero sta nel pacchetto normativo del turno (516,46 dell'art. 102 c.5) la frase non si tocca."""
    monkeypatch.setattr(dg.norme_evidence, "numero_fondato", lambda span: "516,46" in span)
    giusta = "Per i beni il cui costo unitario non è superiore a 516,46 euro la deduzione è integrale (ammortamento escluso)."
    sbagliata = "Per i beni il cui costo unitario non è superiore a 2.000 euro la deduzione è integrale."
    assert "516,46" in dg.sanitize(giusta)
    assert "2.000" not in dg.sanitize(sbagliata)


def _con_pacchetto(testo_legge, testo_utente=""):
    from app.lib import norme_evidence as N
    N.imposta(N.Pacchetto(testo=testo_legge, numeri=N.numeri_nel_testo(testo_legge), coppie=N.coppie_nel_testo(testo_legge),
                          importi=N.importi_nel_testo(testo_legge)))
    N.imposta_testo_utente(testo_utente or None)


def test_un_importo_si_verifica_come_importo_non_come_numero_nudo():
    """«300 €» non è fondato solo perché «300» compare in un altro punto del pacchetto (20/10/2026)."""
    from app.lib import norme_evidence as N
    try:
        _con_pacchetto("comma 5: per i beni il cui costo unitario non è superiore a 516,46 euro è consentita la deduzione "
                       "integrale. Art. 300 del codice; entro 300 giorni.")
        assert N.numero_fondato("516,46 euro") and N.numero_fondato("€ 516,46")
        assert not N.numero_fondato("300 €") and not N.numero_fondato("2.000 euro")
        san = dg.sanitize("Per ammortamento: la soglia di 300 € è superata, quindi ammortizzi.")
        assert "300" not in san
        assert "516,46" in dg.sanitize("Per l'ammortamento la soglia di 516,46 euro non è superata.")
    finally:
        N.imposta(None)
        N.imposta_testo_utente(None)


def test_un_importo_detto_dall_utente_resta():
    from app.lib import norme_evidence as N
    try:
        N.imposta(None)
        N.imposta_testo_utente("Abbiamo comprato un computer da 2.500 euro")
        assert N.numero_fondato("oltre 2.500 euro") and not N.numero_fondato("oltre 3.000 euro")
    finally:
        N.imposta_testo_utente(None)


def test_importi_normalizzati():
    from app.lib import norme_evidence as N
    assert N.importi_nel_testo("516,46 euro; € 2.500; 2.000,00 €; euro 5.000,50; 300 €") == {"516.46", "2500", "2000", "5000.5", "300"}
