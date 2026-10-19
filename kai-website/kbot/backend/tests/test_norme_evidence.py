"""Evidence pack normativo: il testo di legge entra nel contesto prima della risposta e le guardie lo
riconoscono. Corpus finto (SQLite con lo stesso schema, testi reali accorciati): la CI non ha il corpus da
1,9 GB. I casi sono quelli che hanno fatto sbagliare durante lo sviluppo (15/10/2026)."""
import json
import sqlite3
from types import SimpleNamespace as NS

import pytest

from app.lib import deadline_guard, norme_evidence as E, norme_guard

# ── articoli di prova (testo reale accorciato, struttura del corpus) ─────────────────────────
ART_2473 = (
    "# Art. 2473 Codice Civile Art. 2473. (Recesso del socio). L'atto costitutivo determina quando il socio puo' "
    "recedere dalla societa' e le relative modalita'. In ogni caso il diritto di recesso compete ai soci che non hanno "
    "consentito al cambiamento dell'oggetto o del tipo di societa'. Nel caso di societa' contratta a tempo "
    "indeterminato il diritto di recesso compete al socio in ogni momento e puo' essere esercitato con un preavviso di "
    "almeno centottanta giorni. I soci che recedono hanno diritto di ottenere il rimborso della propria partecipazione "
    "in proporzione del patrimonio sociale, determinato tenendo conto del suo valore di mercato. Il rimborso delle "
    "partecipazioni deve essere eseguito entro centottanta giorni dalla comunicazione del recesso. "
    + "Il recesso non puo' essere esercitato e, se gia' esercitato, e' privo di efficacia se la societa' revoca la "
      "delibera. " * 12)

ART_2099 = ("# Art. 2099 Codice Civile Art. 2099. (Retribuzione). La retribuzione del prestatore di lavoro puo' essere "
            "stabilita a tempo o a cottimo e deve essere corrisposta con le modalita' e nei termini in uso nel luogo "
            "in cui il lavoro viene eseguito.")

ART_49 = (
    "# Art. 49 — Decreto Legislativo Limitazioni all'uso del contante e dei titoli al portatore\n\n"
    "**1.** E' vietato il trasferimento di denaro contante tra soggetti diversi quando il valore e' complessivamente "
    "pari o superiore a 3.000 euro. " + "Il trasferimento superiore al predetto limite e' vietato anche se frazionato. " * 18
    + "**2.** Per il servizio di rimessa di denaro la soglia e' di 1.000 euro. "
    "**3.** Per la negoziazione a pronti di mezzi di pagamento in valuta la soglia e' di 3.000 euro. "
    "**3-bis.** A decorrere dal 1° luglio 2020 e fino al 31 dicembre 2022, il divieto di cui al comma 1 e' riferito alla "
    "cifra di 2.000 euro. A decorrere dal 1° gennaio 2023, il predetto divieto di cui al comma 1 e' riferito alla cifra "
    "di ((5.000 euro)). "
    "**4.** I moduli di assegni bancari e postali sono rilasciati dalle banche e da Poste Italiane. "
    + "**5.** Gli assegni emessi per importi pari o superiori a 1.000 euro devono recare il nome del beneficiario. " * 1
    + "\n\n------------- AGGIORNAMENTO (7)\nIl D.L. 31 maggio 2010, n. 78 ha disposto che le soglie sono adeguate "
      "all'importo di euro cinquemila. NOTA-DA-TOGLIERE")

ART_ABROGATO = "# Art. 9999\n\n((ARTICOLO ABROGATO DAL D.LGS. 10 AGOSTO 2018, N. 101))"

ART_FERIE = ("# Art. 10 — Decreto Legislativo (Ferie annuali) **1.** Il prestatore di lavoro ha diritto ad un periodo "
             "annuale di ferie retribuite non inferiore a quattro settimane. **2.** Il predetto periodo minimo di "
             "quattro settimane non puo' essere sostituito dalla relativa indennita' per ferie non godute, salvo il "
             "caso di risoluzione del rapporto di lavoro.")



ART_25_DPR600 = (
    "# Art. 25 Art. 25. ((Ritenuta sui redditi di lavoro autonomo)). I soggetti indicati nel primo comma dell'art. 23, che "
    "corrispondono a soggetti residenti compensi per prestazioni di lavoro autonomo, devono operare all'atto del pagamento "
    "una ritenuta del 15 per cento a titolo di acconto dell'imposta sul reddito delle persone fisiche, con l'obbligo di rivalsa."
    "\n\n--------------- AGGIORNAMENTO (30)\nIl D.L. 2 marzo 1989, n.69, ha disposto che \"La ritenuta del 18 per cento di cui al "
    "primo comma dell'articolo 25 e' elevata al 19 per cento.\"\n\n--------------- AGGIORNAMENTO (54)\nLa L. 27 dicembre 1997, "
    "n.449 ha disposto (con l'art. 21 comma 11) che \"nell'articolo 25: 1) al primo comma le parole: \"19 per cento\" sono "
    "sostituite dalle seguenti: \"20 per cento\";\"\n\n--------------- AGGIORNAMENTO (60)\nIl D.Lgs. 1 gennaio 2000 ha disposto "
    "altre cose che non riguardano le cifre e sono abrogate norme precedenti.")

ART_276_29 = ("# Art. 29 — Decreto Legislativo (Appalto) **1.** Ai fini della applicazione delle norme contenute nel presente titolo, "
              "il contratto di appalto si distingue dalla somministrazione. **2.** In caso di appalto di opere o di servizi, il "
              "committente imprenditore o datore di lavoro e' obbligato in solido con l'appaltatore, entro il limite di due anni "
              "dalla cessazione dell'appalto, a corrispondere ai lavoratori i trattamenti retributivi e i contributi previdenziali.")
ART_276_32 = ("# Art. 32 — Decreto Legislativo (Modifiche al decreto sul lavoro) 1. Sono modificate le definizioni di orario di "
              "lavoro e di mansioni dei dipendenti in materia di organizzazione.")
ART_2479 = ("# Art. 2479 Codice Civile Art. 2479. (Decisioni dei soci). I soci decidono sulle materie riservate alla loro competenza "
            "dall'atto costitutivo, nonche' sugli argomenti che uno o piu' amministratori o tanti soci che rappresentano almeno un "
            "terzo del capitale sociale sottopongono alla loro approvazione.")
ART_2479_TER = ("# Art. 2479-ter Codice Civile Art. 2479-ter. (Invalidita' delle decisioni dei soci). Le decisioni dei soci che non "
                "sono prese in conformita' della legge o dell'atto costitutivo possono essere impugnate dai soci che non vi hanno "
                "consentito entro novanta giorni dalla loro trascrizione nel libro delle decisioni dei soci.")


def _riga(tipo, anno, num, art, testo):
    return (f"normattiva_markdown_api_parsed/{tipo}_{anno}_{num}/{tipo}_{anno}_{num}_art_{art}.md", testo)


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    db = tmp_path / "normattiva.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY AUTOINCREMENT, file TEXT, testo TEXT, source TEXT)")
    con.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(file, testo)")
    for f, t in (_riga("regio_decreto", 1942, 262, "2473", ART_2473), _riga("regio_decreto", 1942, 262, "2099", ART_2099),
                 _riga("decreto_legislativo", 2007, 231, "49", ART_49),
                 _riga("regio_decreto", 1942, 262, "9999", ART_ABROGATO),
                 _riga("decreto_legislativo", 2003, 66, "10", ART_FERIE),
                 _riga("decreto_presidente_repubblica", 1973, 600, "25", ART_25_DPR600),
                 _riga("decreto_legislativo", 2003, 276, "29", ART_276_29),
                 _riga("decreto_legislativo", 2003, 276, "32", ART_276_32),
                 _riga("regio_decreto", 1942, 262, "2479", ART_2479),
                 _riga("regio_decreto", 1942, 262, "2479-ter", ART_2479_TER)):
        con.execute("INSERT INTO chunks(file, testo, source) VALUES (?,?,?)", (f, t, "akn_bulk_xml"))
        con.execute("INSERT INTO chunks_fts(file, testo) VALUES (?,?)", (f, t))
    con.commit()
    con.close()
    monkeypatch.setenv("NORMATTIVA_DB_PATH", str(db))
    monkeypatch.delenv("KBOT_NORME_EVIDENCE", raising=False)
    E._CACHE_ARTICOLI.clear()
    E.imposta(None)
    yield db
    E.imposta(None)
    E._CACHE_ARTICOLI.clear()


def _client(norme, parole=None):
    class _M:
        def create(self, **_kw):
            return NS(content=[NS(type="text", text=json.dumps({"norme": norme, "parole": parole or []}))])
    return NS(messages=_M())


# ── numeri in cifre e in parole ──────────────────────────────────────────────────────────────
def test_numeri_in_parole_e_cifre():
    assert [E.valore(w) for w in ("quaranta", "venticinque", "centottanta", "cinquemila", "ventotto", "5.000", "40")] \
        == [40, 25, 180, 5000, 28, 5000, 40]
    assert E.numeri_nel_testo("entro quaranta giorni e 5.000 euro") == {40, 5000}
    assert (180, "gio") in E.coppie_nel_testo("entro centottanta giorni")


# ── riferimenti ──────────────────────────────────────────────────────────────────────────────
def test_riferimenti_con_articolo_si_leggono_quelli_senza_si_scartano(corpus):
    r = E.riferimenti_da_testo("art. 2473 c.c.; D.Lgs. 231/2007 art. 49; D.Lgs. 81/2008")
    assert {(x["numero"], x["anno"], x["articolo"]) for x in r} == {("262", 1942, "2473"), ("231", 2007, "49")}


# ── recupero e lettura ───────────────────────────────────────────────────────────────────────
def test_recupera_art_2473_con_i_due_termini_di_180_giorni(corpus):
    r = E.riferimenti_da_testo("art. 2473 c.c.")[0]
    f = E.recupera(r, ["recesso", "socio"], "utente", 2400, "quanto tempo per liquidare la quota")
    assert f is not None and f.rubrica == "Recesso del socio" and f.sigla == "art. 2473 c.c."
    assert f.testo.lower().count("centottanta giorni") == 2
    assert "valore di mercato" in f.testo


def test_art_49_il_comma_3bis_con_5000_euro_non_si_perde_e_le_note_si_tolgono(corpus):
    r = E.riferimenti_da_testo("D.Lgs. 231/2007 art. 49")[0]
    f = E.recupera(r, ["contanti", "fornitore"], "utente", 1100, "posso pagare in contanti 1.500 euro?")
    assert "comma 3-bis" in f.testo and "5.000 euro" in f.testo and "1° gennaio 2023" in f.testo
    assert "NOTA-DA-TOGLIERE" not in f.testo and "AGGIORNAMENTO" not in f.testo
    assert "((" not in f.testo and "**" not in f.testo
    assert "[…]" in f.testo                       # il comma 1, lunghissimo, è stato tagliato


def test_il_grassetto_dei_numeri_di_comma_non_impedisce_la_divisione(corpus):
    corpo, _ = E._ripulisci(ART_FERIE)
    assert [et for et, _ in E.dividi_commi(corpo)] == ["", "1", "2"]


def test_articolo_abrogato_non_entra(corpus):
    assert E.recupera({"tipo": "regio_decreto", "anno": 1942, "numero": "262", "articolo": "9999"}, [], "utente", 2400) is None


def test_articolo_inesistente_ritorna_none_senza_errore(corpus):
    assert E.recupera({"tipo": "regio_decreto", "anno": 1942, "numero": "262", "articolo": "77777"}, [], "utente", 2400) is None


def test_i_commi_si_riconoscono_solo_in_sequenza():
    # «n. 196. L'articolo…» non è un comma 196
    corpo = "1. Primo comma. Vedi il decreto n. 196. L'articolo 4 resta. 2. Secondo comma. 3-bis. Terzo bis."
    assert [et for et, _ in E.dividi_commi(corpo)] == ["1", "2"] or [et for et, _ in E.dividi_commi(corpo)][:2] == ["1", "2"]


# ── costruisci: il pacchetto del turno ───────────────────────────────────────────────────────
def test_costruisci_con_riferimenti_proposti_dal_modello(corpus):
    p = E.costruisci("Il socio della srl vuole uscire: quanto tempo abbiamo per liquidargli la quota?", "",
                     _client(["art. 2473 c.c."], ["recesso", "socio", "quota"]), "m")
    assert p is not None and [f.sigla for f in p.fonti] == ["art. 2473 c.c."]
    assert "FONTI NORMATIVE PER QUESTO TURNO" in p.testo and "centottanta giorni" in p.testo
    assert 180 in p.numeri and (180, "gio") in p.coppie


def test_riferimento_proposto_esistente_ma_non_pertinente_e_scartato(corpus):
    # il caso 2099 vs 2096: l'articolo esiste ma parla di retribuzione, non di recesso del socio
    p = E.costruisci("Il socio della srl vuole recedere, quanto tempo per la liquidazione?", "",
                     _client(["art. 2099 c.c.", "art. 2473 c.c."], ["recesso", "socio", "liquidazione"]), "m")
    assert [f.sigla for f in p.fonti] == ["art. 2473 c.c."]


def test_il_riferimento_scritto_dall_utente_non_passa_dal_filtro_di_pertinenza(corpus):
    p = E.costruisci("Cosa dice l'art. 2099 c.c. sulla retribuzione dei dipendenti?", "",
                     _client([], ["recesso"]), "m")
    assert p is not None and p.fonti[0].sigla == "art. 2099 c.c." and p.fonti[0].origine == "utente"


def test_senza_ambito_normativo_nessuna_chiamata(corpus):
    class _Boom:
        class messages:
            @staticmethod
            def create(**_k):
                raise AssertionError("il modello non va chiamato per una chiacchiera")
    assert E.costruisci("ciao, come stai oggi? tutto bene da te", "", _Boom, "m") is None
    assert E.costruisci("grazie mille", "", _Boom, "m") is None
    assert E.costruisci("ok va bene", "", _Boom, "m") is None


def test_il_gate_non_dipende_da_un_elenco_di_parole(corpus):
    """Due domande mai viste durante lo sviluppo («macchinario», «capannone», «difetto») non contenevano nessuna
    delle parole dell'elenco e il pacchetto non partiva."""
    for q in ("Abbiamo comprato un macchinario da un'impresa e dopo un mese ha un difetto. Entro quanto dobbiamo contestarlo?",
              "Il capannone che ci ha costruito un'impresa ha dei difetti gravi comparsi dopo cinque anni. Possiamo pretendere qualcosa?"):
        assert E.serve_evidenza(q)
    assert not E.serve_evidenza("ciao")
    assert not E.serve_evidenza("ok grazie ci sentiamo")


def test_se_il_modello_non_trova_norme_il_pacchetto_e_vuoto(corpus):
    assert E.costruisci("Come imposto una campagna di email marketing per i nostri clienti storici?", "",
                        _client([], []), "m") is None


def test_fail_open_se_il_modello_va_in_errore(corpus):
    class _Err:
        class messages:
            @staticmethod
            def create(**_k):
                raise RuntimeError("timeout")
    assert E.costruisci("il socio della srl vuole uscire, art. 2473 c.c.", "", _Err, "m") is not None  # i riferimenti dell'utente bastano
    assert E.costruisci("il socio della srl vuole uscire dalla societa", "", _Err, "m") is None


def test_flag_spento_e_corpus_assente(corpus, monkeypatch):
    monkeypatch.setenv("KBOT_NORME_EVIDENCE", "0")
    assert E.costruisci("il socio vuole recedere art. 2473 c.c.", "", _client(["art. 2473 c.c."]), "m") is None
    monkeypatch.delenv("KBOT_NORME_EVIDENCE")
    monkeypatch.setenv("NORMATTIVA_DB_PATH", "/non/esiste.db")
    assert E.costruisci("il socio vuole recedere art. 2473 c.c.", "", _client(["art. 2473 c.c."]), "m") is None


# ── guardie: le citazioni e i numeri del pacchetto restano, il resto no ──────────────────────
def _pacchetto(corpus):
    E.imposta(E.costruisci("socio srl recesso quanto tempo", "", _client(["art. 2473 c.c."], ["recesso", "socio"]), "m"))


def test_norme_guard_tiene_le_citazioni_del_pacchetto_e_toglie_le_altre(corpus):
    _pacchetto(corpus)
    t = "Il recesso è regolato dall'art. 2473 c.c., non dall'art. 2099 c.c.: lì si parla di retribuzione."
    out = norme_guard.sanitize(t)
    assert "art. 2473 c.c." in out and "art. 2099" not in out and "non dal codice civile" in out


def test_norme_guard_senza_pacchetto_toglie_tutto_come_prima(corpus):
    out = norme_guard.sanitize("Vale l'art. 2473 c.c. sul recesso.")
    assert "2473" not in out and "il codice civile" in out


def test_deadline_guard_non_cancella_un_termine_che_sta_nella_fonte(corpus):
    _pacchetto(corpus)
    t = "Il rimborso va eseguito entro 180 giorni dalla comunicazione del recesso (normativa sul recesso del socio)."
    assert deadline_guard.sanitize(t) == t
    # un termine che NON sta nella fonte si rende ancora descrittivo
    out = deadline_guard.sanitize("Il rimborso va eseguito entro 45 giorni dalla comunicazione del recesso del socio.")
    assert "45 giorni" not in out and "entro il termine previsto dalla normativa" in out


def test_deadline_guard_senza_pacchetto_non_cambia_comportamento(corpus):
    out = deadline_guard.sanitize("Il rimborso va eseguito entro 180 giorni dalla comunicazione del recesso del socio.")
    assert "180 giorni" not in out


def test_deadline_guard_importi_fondati(corpus):
    E.imposta(E.costruisci("pagamento in contanti limite importo 1.500 euro", "",
                           _client(["D.Lgs. 231/2007 art. 49"], ["contanti", "importo", "limite"]), "m"))
    t = "Dal 2023 il limite per i pagamenti in contanti è di 5.000 euro, quindi 1.500 euro vanno bene (art. 49 D.Lgs. 231/2007)."
    assert "5.000 euro" in deadline_guard.sanitize(t)


# ── elenco delle fonti in coda ───────────────────────────────────────────────────────────────
def test_aggiungi_fonti_solo_quelle_citate(corpus):
    _pacchetto(corpus)
    out = E.aggiungi_fonti("Il rimborso entro centottanta giorni (art. 2473 c.c.).")
    assert out.endswith("Fonti: art. 2473 c.c.")
    assert E.aggiungi_fonti("Il rimborso entro centottanta giorni.") == "Il rimborso entro centottanta giorni."
    assert E.aggiungi_fonti(out) == out                        # nessun doppione


def test_aggiungi_fonti_senza_pacchetto_non_tocca_nulla(corpus):
    assert E.aggiungi_fonti("testo (art. 2473 c.c.)") == "testo (art. 2473 c.c.)"


def test_il_punto_unico_del_testo_visibile_applica_guardie_e_fonti(corpus):
    from app.api import message as M
    _pacchetto(corpus)
    raw = "Il recesso: rimborso entro 180 giorni (art. 2473 c.c.). Non vale l'art. 2099 c.c."
    visible, _, _ = M._extract_gated_summary(raw, [], {})
    assert "180 giorni" in visible and "art. 2473 c.c." in visible and "2099" not in visible
    assert visible.rstrip().endswith("Fonti: art. 2473 c.c.")


# ── elisioni rotte quando si toglie «art. N c.c.» (difetto vecchio, visto anche nell'audit) ─────
def test_elisioni_riparate_dopo_la_rimozione_dell_articolo():
    from app.lib import prompts
    assert prompts.sanitize_unverified_legal_citations("Vale l'art. 2099 c.c. sulla retribuzione.") \
        == "Vale il codice civile sulla retribuzione."
    assert prompts.sanitize_unverified_legal_citations("Lo dice nell'art. 2096 c.c. e dall'art. 2119 c.c.") \
        == "Lo dice nel codice civile e dal codice civile"
    assert prompts.ripara_elisioni("come dell'la normativa") == "come della normativa"
    # l'italiano corretto non si tocca
    for ok in ("l'impresa", "dell'azienda", "all'inizio", "nell'ambito", "sull'importo"):
        assert prompts.ripara_elisioni(ok) == ok


# ── vigenza: le note che modificano cifre ───────────────────────────────────────────────────
def test_la_nota_che_cambia_l_aliquota_entra_nel_pacchetto(corpus):
    """Il corpo dell'art. 25 D.P.R. 600/1973 dice 15%; la nota (54) dice che la L. 449/1997 ha messo 20%."""
    r = E.riferimenti_da_testo("art. 25 D.P.R. 600/1973")[0]
    f = E.recupera(r, ["ritenuta", "consulente"], "utente", 2400, "ritenuta d'acconto su un consulente")
    assert "15 per cento" in f.testo
    assert "20 per cento" in f.note and "(54)" in f.note
    assert "(60)" not in f.note                        # la nota senza cifre non entra
    blocco = E.costruisci_blocco([f])
    assert "Modifiche successive al testo" in blocco and "20 per cento" in blocco
    # e i numeri delle note sono «fondati» per le guardie
    p = E.Pacchetto(testo=blocco, fonti=[f], numeri=E.numeri_nel_testo(f.testo + " " + f.note))
    assert 20 in p.numeri


def test_note_spente_dal_flag(corpus, monkeypatch):
    monkeypatch.setenv("KBOT_NORME_NOTE", "0")
    r = E.riferimenti_da_testo("art. 25 D.P.R. 600/1973")[0]
    assert E.recupera(r, ["ritenuta"], "utente", 2400).note == ""


def test_note_rilevanti_ordina_per_anno_e_taglia():
    grezzo = ("corpo ------------- AGGIORNAMENTO (1)\nLa L. 10 marzo 1990, n. 1 ha disposto che \"le parole: \"10 per cento\" sono "
              "sostituite dalle seguenti: \"12 per cento\"\"\n------------- AGGIORNAMENTO (2)\nLa L. 5 maggio 2015, n. 9 ha "
              "disposto che \"le parole: \"12 per cento\" sono sostituite dalle seguenti: \"15 per cento\"\"")
    out = E.note_rilevanti(grezzo)
    assert out.index("(2)") < out.index("(1)")         # la più recente per prima


# ── richiamo: la norma è nota, l'articolo no; gli articoli gemelli ───────────────────────────
def test_cerca_dentro_la_norma_trova_l_articolo_giusto(corpus):
    rif = E.riferimenti_da_testo("D.Lgs. 276/2003", solo_con_articolo=False)[0]
    assert rif["articolo"] is None
    fs = E.cerca_in_norma(rif, ["appalto", "committente", "solidale", "lavoratori", "retribuzione"], 2400, "")
    assert [f.articolo for f in fs][:1] == ["29"] and fs[0].origine == "norma"
    # l'articolo che non parla dell'argomento non entra (servono almeno due parole)
    assert all(f.articolo != "32" for f in fs)


def test_articoli_affini_trovano_il_ter(corpus):
    rif = E.riferimenti_da_testo("art. 2479 c.c.")[0]
    fs = E.articoli_affini(rif, ["impugnare", "decisioni", "soci", "novanta", "trascrizione"], 2400, "")
    assert [f.articolo for f in fs] == ["2479-ter"]


def test_costruisci_con_norma_senza_articolo_e_affini(corpus):
    # il modello propone «D.Lgs. 276/2003» (senza articolo) e «art. 2479 c.c.»: il sistema trova 29 e 2479-ter
    p = E.costruisci("Un operaio dell'appaltatore chiede a noi gli stipendi; e possiamo impugnare la decisione dei soci della srl?",
                     "", _client(["D.Lgs. 276/2003", "art. 2479 c.c."],
                                 ["appalto", "committente", "solidale", "impugnare", "decisioni", "soci", "novanta"]), "m")
    sigle = [f.articolo for f in p.fonti]
    assert "29" in sigle and "2479-ter" in sigle


def test_affini_e_ricerca_norma_spegnibili(corpus, monkeypatch):
    monkeypatch.setenv("KBOT_NORME_AFFINI", "0")
    monkeypatch.setenv("KBOT_NORME_RICERCA_NORMA", "0")
    p = E.costruisci("impugnare la decisione dei soci e gli stipendi dell'appalto", "",
                     _client(["D.Lgs. 276/2003", "art. 2479 c.c."], ["appalto", "solidale", "impugnare", "decisioni", "soci"]), "m")
    assert p is None or all(f.articolo not in ("29", "2479-ter") for f in p.fonti)


# ── mappa temi: punto di estensione (vuota di proposito, da validare con un professionista) ───────
def test_la_mappa_distribuita_non_ha_voci_attive_e_ben_formata(monkeypatch):
    """Le voci distribuite sono BOZZE (nessun professionista le ha validate): in produzione, senza
    KBOT_MAPPA_BOZZE=1, la mappa attiva è vuota. Quando una voce viene validata, questo test va aggiornato."""
    import json
    d = json.load(open(E._MAPPA_PATH, encoding="utf-8"))
    assert "validato_da" in d["schema"]
    assert all(not (t.get("validato_da") or "").strip() for t in d["temi"]), "una voce validata: aggiorna il test"
    monkeypatch.delenv("KBOT_MAPPA_BOZZE", raising=False)
    E._mappa.cache_clear()
    try:
        assert E._mappa() == []
    finally:
        E._mappa.cache_clear()


def test_una_voce_della_mappa_porta_i_riferimenti_senza_il_modello(corpus, monkeypatch, tmp_path):
    mappa = tmp_path / "mappa.json"
    mappa.write_text(json.dumps({"temi": [{"id": "recesso-socio-srl", "trigger": ["socio .{0,40}(esce|uscire|recedere)"],
                                           "riferimenti": ["art. 2473 c.c."], "validato_da": "test"}]}), encoding="utf-8")
    monkeypatch.setattr(E, "_MAPPA_PATH", mappa)
    E._mappa.cache_clear()
    try:
        class _Boom:
            class messages:
                @staticmethod
                def create(**_k):
                    raise RuntimeError("il modello non risponde")
        p = E.costruisci("Il mio socio vuole uscire dalla srl, cosa dobbiamo fare adesso?", "", _Boom, "m")
        assert p is not None and p.fonti[0].sigla == "art. 2473 c.c." and p.fonti[0].origine == "mappa"
        assert E.riferimenti_da_mappa("parliamo di marketing") == []
    finally:
        E._mappa.cache_clear()


def _sdk_severo(rifiuta_temperatura=False, visti=None):
    """Client finto con la STESSA firma dell'SDK Anthropic reale: nessun `temperature`, c'è `extra_body`. Un
    argomento sconosciuto fa fallire il test (un client che accetta qualunque cosa nascondeva il difetto)."""
    class _M:
        def create(self, *, model, max_tokens, messages, system=None, timeout=None, extra_body=None):
            if visti is not None:
                visti.append(extra_body)
            if rifiuta_temperatura and extra_body and "temperature" in extra_body:
                err = RuntimeError("temperature not supported")
                err.status_code = 400
                raise err
            return NS(content=[NS(type="text", text=json.dumps({"norme": ["art. 2473 c.c."], "parole": ["recesso"]}))])
    return NS(messages=_M())


def test_la_proposta_passa_la_temperatura_zero_da_extra_body_con_la_firma_vera_dell_sdk(corpus):
    visti = []
    rif, parole = E.proponi(_sdk_severo(visti=visti), "m", "il socio vuole recedere dalla srl", "")
    assert visti == [{"temperature": 0.0}] and [r["articolo"] for r in rif] == ["2473"]


def test_se_l_api_rifiuta_la_temperatura_si_riprova_senza(corpus):
    visti = []
    rif, _ = E.proponi(_sdk_severo(rifiuta_temperatura=True, visti=visti), "m", "il socio vuole recedere dalla srl", "")
    assert visti == [{"temperature": 0.0}, None] and [r["articolo"] for r in rif] == ["2473"]


def test_tutti_i_client_finti_dei_test_usano_la_firma_dell_sdk(corpus):
    # il pacchetto completo, con il client severo, deve produrre fonti: se la firma sbagliasse, sarebbe vuoto
    p = E.costruisci("Il socio della srl vuole recedere: quanto tempo per liquidare la quota?", "", _sdk_severo(), "m")
    assert p is not None and p.fonti[0].sigla == "art. 2473 c.c."


# ── avviso di vigenza: la cifra sostituita da una nota che il corpo non ha incorporato ──────────────
def test_avviso_di_vigenza_dice_quale_cifra_e_vigente_e_quale_e_superata(corpus):
    r = E.riferimenti_da_testo("art. 25 D.P.R. 600/1973")[0]
    f = E.recupera(r, ["ritenuta"], "utente", 2400, "ritenuta d'acconto su un consulente")
    assert "20 per cento" in f.avviso and "15 per cento" in f.avviso and "SUPERATE" in f.avviso
    blocco = E.costruisci_blocco([f])
    assert blocco.index("ATTENZIONE VIGENZA") < blocco.index("ritenuta del 15 per cento")      # prima del testo


def test_nessun_avviso_se_il_testo_contiene_gia_la_cifra_nuova_o_non_ci_sono_note(corpus):
    for rif in ("art. 2473 c.c.", "D.Lgs. 231/2007 art. 49"):
        r = E.riferimenti_da_testo(rif)[0]
        assert E.recupera(r, ["recesso", "contanti"], "utente", 2400, "x").avviso == ""


def test_avviso_spento_dal_flag(corpus, monkeypatch):
    monkeypatch.setenv("KBOT_NORME_AVVISO", "0")
    r = E.riferimenti_da_testo("art. 25 D.P.R. 600/1973")[0]
    assert E.recupera(r, ["ritenuta"], "utente", 2400).avviso == ""


def test_avviso_solo_sulle_cifre_del_comma_nominato_dalla_nota():
    grezzo = ("# Art. 9 1. La ritenuta e' del 15 per cento. 2. L'interesse e' dell'1 per cento. "
              "------------- AGGIORNAMENTO (3)\nLa L. 5 maggio 2015, n. 9 ha disposto che \"al primo comma le parole: \"15 per cento\" "
              "sono sostituite dalle seguenti: \"20 per cento\"\"")
    corpo, _ = E._ripulisci(grezzo)
    avv = E.vigenza_avviso(grezzo, corpo)
    assert "«20 per cento»" in avv and "«15 per cento»" in avv and "1 per cento" not in avv.replace("15 per cento", "").replace("20 per cento", "")


def test_la_rubrica_si_legge_anche_nel_formato_con_il_titolo_della_norma():
    # formato AKN moderno e supplemento: «# Art. 7 — Legge\n\n(Sanzioni disciplinari)» (prima la rubrica restava vuota)
    assert E._RUBRICA.search("# Art. 7 — Legge\n\n(Sanzioni disciplinari)\n\nLe norme...").group(1) == "Sanzioni disciplinari"
    assert E._RUBRICA.search("# Art. 2118 Codice Civile Art. 2118. (Recesso dal contratto a tempo indeterminato). Ciascuno")
    assert E._RUBRICA.search("# Art. 3 — Decreto Legislativo\n\n(Licenziamento per giustificato motivo)\n\n1.").group(1).startswith("Licenziamento")
