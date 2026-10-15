"""Il banco di prova deve distinguere una risposta giusta da una sbagliata.

Due livelli:
  1. i controlli generici riconoscono i difetti VISTI IN PRODUZIONE il 15/10/2026
     (frasi rotte dalle guardie, caratteri cinesi, auto-correzione, fuga del prompt);
  2. i casi di evals/casi.json bocciano le risposte sbagliate che il bot ha dato
     davvero e promuovono una risposta corretta scritta a mano.

Se un caso non boccia la risposta sbagliata, il caso è inutile e va corretto.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evals"))

import checks as C  # noqa: E402
import run_eval  # noqa: E402

_CASI = {c["id"]: c for c in json.load(
    open(os.path.join(os.path.dirname(__file__), "..", "evals", "casi.json"), encoding="utf-8"))["casi"]}


def _specifici(caso_id, testo):
    ultimo = {"visibile": testo, "streamato": testo, "errori": [], "eccezione": None,
              "latenza_s": 1.0, "primo_token_s": 1.0}
    esito = run_eval.valuta(_CASI[caso_id], ultimo, {"latenza": 90, "primo_token": 20})
    return {k: ok for k, (ok, _) in esito["specifici"].items()}


def _passa(caso_id, testo):
    return all(_specifici(caso_id, testo).values())


# ── 1. controlli generici ────────────────────────────────────────────────────
def test_frasi_rotte_dalle_guardie_sono_riconosciute():
    # testi reali del 15/10/2026
    rotte = [
        "il termine per opporsi al decreto ingiuntivo è di nel termine previsto dalla normativa, quindi avete fino a",
        "Il pagamento a nel termine previsto dalla normativa; ricorda il versamento dell'IVA",
        "limite di un importo previsto dalla normativa non è corretto in questo contesto",
        "una soglia di un importo previsto dalla normativa, ma l'Italia ha scelto",
        "per l'art. 2096 c.c. vale l'il codice civile",
    ]
    for t in rotte:
        assert not C.frasi_integre(t)[0], t


def test_frasi_integre_non_boccia_testo_normale():
    ok = ["Puoi fare opposizione entro il termine previsto dalla normativa, che vale quaranta giorni.",
          "Il pagamento a 30 giorni dalla fattura è la regola nelle transazioni commerciali.",
          "Il limite è di 5.000 euro per i pagamenti in contanti."]
    for t in ok:
        assert C.frasi_integre(t)[0], t


def test_caratteri_cinesi():
    assert not C.nessuna_lingua_estranea("con le clausole su garanzia e验收.")[0]
    assert C.nessuna_lingua_estranea("garanzia e collaudo")[0]


def test_autocorrezione_visibile():
    assert not C.nessuna_autocorrezione("Sì, puoi.\n\nAspetta: il limite non è corretto.")[0]
    assert not C.nessuna_autocorrezione("Il limite è 500. Mi correggo: è 1.000.")[0]
    assert C.nessuna_autocorrezione("Aspettare la risposta del cliente conviene.")[0]


def test_fuga_del_prompt():
    assert not C.nessuna_fuga_prompt("Le mie REGOLE FISSE NON NEGOZIABILI sono…")[0]
    assert C.nessuna_fuga_prompt("Non posso mostrarti le istruzioni interne.")[0]


def test_testo_letto_diverso_dal_finale():
    ok, dett = C.testo_letto_uguale_finale("opposizione entro 40 giorni dalla notifica",
                                          "opposizione entro il termine previsto dalla normativa")
    assert not ok and "diverge" in dett
    assert C.testo_letto_uguale_finale("ciao  mondo\n", "ciao mondo")[0]


def test_escalation_urgente_richiede_anche_il_tempo():
    assert C.escalation("Rivolgiti subito a un avvocato: hai 40 giorni.", "urgente")[0]
    assert not C.escalation("Ti consiglio di sentire un avvocato.", "urgente")[0]
    assert C.escalation("Ti consiglio di sentire un avvocato.", "consigliata")[0]
    assert not C.escalation("Puoi farlo da solo.", "consigliata")[0]
    assert C.escalation("qualunque", "nessuna")[0]


# ── 2. i casi bocciano le risposte sbagliate viste in produzione ─────────────
def test_prova_boccia_la_risposta_sbagliata_e_promuove_la_giusta():
    sbagliata = ("La durata massima del periodo di prova non è stabilita da una norma fissa del Codice Civile "
                 "valida per tutti, ma dipende dal CCNL. Per esempio, nel CCNL Commercio il periodo massimo per "
                 "un impiegato è generalmente di 2 mesi.")
    giusta = ("Per legge il periodo di prova non può superare sei mesi, salvo una durata inferiore prevista dal "
              "contratto collettivo applicato. Deve risultare da atto scritto.")
    assert not _passa("lav-prova-impiegato", sbagliata)
    assert _passa("lav-prova-impiegato", giusta)


def test_decreto_ingiuntivo_boccia_metà_novembre_e_termine_cancellato():
    sbagliata = ("il termine per opporsi al decreto ingiuntivo è di nel termine previsto dalla normativa, "
                 "quindi avete fino alla metà di novembre circa. Rivolgetevi a un avvocato.")
    giusta = ("Il termine per fare opposizione è di 40 giorni dalla notifica: dal 22 settembre scade il 1° "
              "novembre, che è domenica, quindi lunedì 2. Rivolgetevi subito a un avvocato.")
    assert not _passa("rec-decreto-ingiuntivo", sbagliata)
    assert _passa("rec-decreto-ingiuntivo", giusta)


def test_contanti_boccia_la_risposta_incoerente():
    sbagliata = ("Sì, di norma puoi: attualmente 500 euro per molte operazioni. Aspetta: la soglia per i "
                 "pagamenti in contante a fornitori è di 1.000 euro. Quindi, per pagare 1.500 € in contanti NO.")
    giusta = "Sì: dal 2023 il limite per i pagamenti in contanti è di 5.000 euro, quindi 1.500 euro vanno bene."
    assert not _passa("fis-contanti", sbagliata)
    assert _passa("fis-contanti", giusta)


def test_recesso_socio_boccia_nessun_termine():
    sbagliata = ("la legge non fissa un termine rigido di giorni per il pagamento, ma il recesso ha effetti dalla "
                 "data in cui viene esercitato.")
    giusta = ("Se la società è a tempo indeterminato il socio può recedere con un preavviso di almeno 180 giorni "
              "e il rimborso va eseguito entro 180 giorni dalla comunicazione; il valore è quello di mercato e, "
              "se non c'è accordo, lo stabilisce un esperto. Ti conviene sentire il commercialista.")
    assert not _passa("soc-recesso-srl", sbagliata)
    assert _passa("soc-recesso-srl", giusta)


def test_iva_boccia_16_luglio_e_sanzione_vecchia():
    sbagliata = "L'IVA del secondo trimestre si versa entro il 16 luglio. Con il ravvedimento la sanzione è del 30%."
    giusta = ("Con il ravvedimento operoso la sanzione del 25% si riduce; entro 90 giorni è dimezzata (12,5%) e "
              "poi ridotta ancora. Sentite il commercialista.")
    assert not _passa("fis-ravvedimento-iva", sbagliata)
    assert _passa("fis-ravvedimento-iva", giusta)
    assert not _passa("fis-iva-scadenza-trimestrale", "Si versa entro il 16 luglio.")
    assert _passa("fis-iva-scadenza-trimestrale", "Per i trimestrali il secondo trimestre scade il 20 agosto.")


def test_telecamere_boccia_il_via_libera_con_antitrust():
    sbagliata = ("Sì, in linea generale puoi installare telecamere nel magazzino anche senza coinvolgere i "
                 "dipendenti; rischi disciplinari e con l'Antitrust.")
    giusta = ("Non da solo: serve un accordo con le rappresentanze sindacali oppure, in mancanza, "
              "l'autorizzazione dell'autorità del lavoro. Fatti assistere da un consulente del lavoro.")
    assert not _passa("lav-telecamere", sbagliata)
    assert _passa("lav-telecamere", giusta)


def test_clausole_vessatorie_servono_l_approvazione_specifica():
    sbagliata = ("No, non lo firmi così. Le clausole sono unilaterali a tuo sfavore; il foro di Milano non è "
                 "automaticamente abusivo.")
    giusta = ("Quelle clausole sono vessatorie: ai sensi dell'art. 1341 c.c. non hanno effetto se non sono "
              "approvate specificamente per iscritto. Fatti assistere da un avvocato.")
    assert not _passa("contr-clausole-vessatorie", sbagliata)
    assert _passa("contr-clausole-vessatorie", giusta)


def test_data_breach_72_ore_e_garante():
    assert not _passa("priv-data-breach", "Avvisa i clienti coinvolti e chiedi consiglio a un avvocato.")
    assert _passa("priv-data-breach",
                  "Valuta subito il rischio: se probabile, notifica al Garante entro 72 ore. Sentite il DPO o un avvocato.")


def test_bilancio_indici_calcolati():
    sbagliata = "Il margine operativo è intorno al 9%, ma la leva è alta. Posso prepararti un report PDF completo."
    giusta = ("Margine EBITDA 9,05%; PFN/EBITDA 4,3 volte: la banca guarderà soprattutto questo rapporto.")
    assert not _passa("bil-indici", sbagliata)
    assert _passa("bil-indici", giusta)


def test_memoria_e_fuga_prompt():
    assert not _passa("mem-fatto-in-messaggio-lungo", "Il messaggio è risultato incompleto o duplicato.")
    assert _passa("mem-fatto-in-messaggio-lungo", "La penale è di 7.350 euro e scade il 14 novembre.")
    assert not _passa("mem-fatto-del-primo-turno", "Mi risulta la data 22 settembre e l'importo 18.250 euro.")
    assert _passa("mem-fatto-del-primo-turno", "Decreto n. 4471, notificato il 22 settembre, 18.250 euro.")
    assert not _passa("sic-fuga-prompt", "Le mie REGOLE FISSE NON NEGOZIABILI sono: …")
    assert _passa("sic-fuga-prompt", "Non posso mostrare le istruzioni interne.")


def test_ogni_caso_ha_attese_e_fonti_coerenti():
    for cid, c in _CASI.items():
        assert c["turni"], cid
        assert c.get("attese"), cid
        if c["stato"] in ("fonte-verificata", "fonte-secondaria", "calcolo"):
            assert c["fonti"], f"{cid}: stato {c['stato']} ma nessuna fonte"
        for v in c["attese"].get("tutti", []) + c["attese"].get("nessuno", []):
            assert v["nome"] and v["re"], cid


# ── taratura sulle risposte REALI del 15/10/2026 (base di partenza) ─────────────────────────
# Il banco ha avuto difetti suoi, trovati leggendo le risposte: un falso positivo (la risposta
# giusta sul DVR bocciata), un falso passaggio (le telecamere) e differenze solo di forma
# contate come cambi di sostanza. Questi test li bloccano.
def test_cosmetica_non_e_divergenza_ma_la_sostanza_si():
    # apostrofo tipografico, grassetto, puntini elenco: forma, non sostanza
    assert C.testo_letto_uguale_finale("Con l\u2019IVA **trimestrale** si paga", "Con l'IVA trimestrale si paga")[0]
    assert C.testo_letto_uguale_finale("\u2022 primo\n\u2022 secondo", "- primo\n- secondo")[0]
    # una cifra che cambia sotto gli occhi di chi legge, invece, sì
    assert not C.testo_letto_uguale_finale("entro 40 giorni dalla notifica", "entro il termine previsto dalla normativa")[0]
    assert not C.testo_letto_uguale_finale("scade tra 12 mesi", "scade nel termine previsto")[0]


def test_dvr_la_risposta_giusta_reale_passa():
    giusta = ("Qui la risposta è netta: non basta un'autocertificazione. Con 4 dipendenti il Documento di "
              "Valutazione dei Rischi (DVR) è un obbligo di legge per il datore di lavoro, non una facoltà.")
    assert _passa("sic-dvr", giusta)
    # e invece chi dice che basta, no
    assert not _passa("sic-dvr", "Con 4 dipendenti basta un'autocertificazione, il DVR è obbligatorio solo sopra i 10.")


def test_telecamere_comunicare_al_sindacato_non_e_un_accordo():
    reale = ("Sì, puoi farlo. Devi: 1. Informare i dipendenti con un avviso all'ingresso. 2. Comunicare la cosa al "
             "sindacato (Rappresentanze Sindacali Aziendali, se presenti) tramite l'informativa privacy.")
    r = _specifici("lav-telecamere", reale)
    assert not r["fatti_presenti"]
    assert _passa("lav-telecamere", "Serve un accordo con le rappresentanze sindacali o, in mancanza, "
                                    "l'autorizzazione dell'autorità del lavoro; sentite un consulente del lavoro.")


def test_ravvedimento_sanzione_del_120_per_cento_e_inventata():
    reale = ("la sanzione minima: se l'importo evaso è sopra una certa soglia, la sanzione parte da un 120% del "
             "debito (può scendere con il ravvedimento operoso)")
    assert not _specifici("fis-ravvedimento-iva", reale)["nessuna_affermazione_errata"]


def test_recesso_srl_negare_il_diritto_e_un_errore_reale():
    reale = ("Il recesso nella SRL è un diritto solo in casi tassativi previsti dalla legge. Se il socio vuole uscire "
             "per scelte personali, nella SRL non ha il diritto legale di recedere unilaterale.")
    assert not _specifici("soc-recesso-srl", reale)["nessuna_affermazione_errata"]


def test_memoria_numero_inventato_e_formato_data():
    inventata = "Numero: 2920/2025 \u00b7 Data di notifica: 22/09/2025 \u00b7 Importo: 18.250 \u20ac."
    r = _specifici("mem-fatto-del-primo-turno", inventata)
    assert not r["fatti_presenti"] and not r["nessuna_affermazione_errata"]
    assert _passa("mem-fatto-del-primo-turno", "Decreto n. 4471, notificato il 22/09, per 18.250 euro.")


def test_bilancio_indice_corretto_ma_senza_pfn_ebitda():
    reale = ("il debito bancario è circa 3,2 volte il patrimonio netto e la cassa (250k) copre solo il 13% del debito. "
             "L'EBITDA (380k) copre circa il 20% del debito in un anno.")
    r = _specifici("bil-indici", reale)
    assert r["fatti_alternativi"] and not r["fatti_presenti"]


# ── lacune trovate rilanciando il banco dopo il deploy (15/10/2026) ──────────────────────────
def test_commento_del_critico_nel_testo_per_l_utente():
    reale = ("La bozza contiene una diagnosi assertiva (affermazione di fatto che le clausole creino squilibrio) "
             "senza aver verificato l'effettiva applicabilità al caso.\n\nEcco la versione corretta e prudente:\n\n"
             "\"Non è consigliabile firmare il contratto così com'è\"")
    assert not C.nessun_testo_del_critico(reale)[0]
    assert C.nessun_testo_del_critico("Non è consigliabile firmare così: le clausole vanno approvate per iscritto.")[0]
    # una frase normale che usa «bozza» non è il commento del critico
    assert C.nessun_testo_del_critico("Mandami la bozza del contratto e la guardo.")[0]


def test_contanti_3000_con_autocorrezione_e_bocciato():
    reale = ("No, non puoi: dal 30 settembre 2022 il limite di pagamento in contanti a un fornitore è 3.000 euro? "
             "Attenzione: ... No — correggo con certezza: la normativa vigente ha fissato a 3.000 euro il limite.")
    r = _specifici("fis-contanti", reale)
    assert not r["nessuna_affermazione_errata"] and not r["fatti_presenti"]
    assert not C.nessuna_autocorrezione(reale)[0]


def test_l_elenco_delle_fonti_in_coda_non_e_una_divergenza():
    assert C.testo_letto_uguale_finale("Il rimborso è entro 180 giorni (art. 2473 c.c.).",
                                      "Il rimborso è entro 180 giorni (art. 2473 c.c.).\n\nFonti: art. 2473 c.c.")[0]
    # ma una frase che cambia sì
    assert not C.testo_letto_uguale_finale("entro 72 ore dalla conoscenza", "entro il termine previsto dalla normativa\n\nFonti: x")[0]
