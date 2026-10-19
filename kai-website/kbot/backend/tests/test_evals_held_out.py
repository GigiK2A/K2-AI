"""I casi held-out devono bocciare la risposta sbagliata e promuovere quella giusta (come i casi di sviluppo):
un caso che non boccia l'errore che dovrebbe cogliere è inutile."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evals"))

import run_eval  # noqa: E402

_DIR = os.path.join(os.path.dirname(__file__), "..", "evals")


def _carica(nome):
    return {c["id"]: c for c in json.load(open(os.path.join(_DIR, nome), encoding="utf-8"))["casi"]}


_CASI = {**_carica("casi_held_out.json"), **_carica("casi_held_out_2.json"), **_carica("casi_held_out_3.json")}


def _ok(cid, testo):
    ultimo = {"visibile": testo, "streamato": testo, "errori": [], "eccezione": None, "latenza_s": 1.0, "primo_token_s": 1.0}
    esito = run_eval.valuta(_CASI[cid], ultimo, {"latenza": 90, "primo_token": 20})
    return all(ok for ok, _ in esito["specifici"].values())


# (id, risposta giusta, risposta sbagliata)
COPPIE = [
    ("h3-contestazione-cinque-giorni",
     "Il termine di 3 giorni è troppo breve: l'art. 7 dello Statuto dei lavoratori impone almeno cinque giorni dalla contestazione scritta prima di applicare qualsiasi sanzione. Fatti assistere da un avvocato giuslavorista o dal sindacato.",
     "Il termine di 3 giorni per le giustificazioni è sufficiente, ma il licenziamento senza preavviso per quattro ore di assenza sembra sproporzionato."),
    ("h3-multa-quattro-ore",
     "No: la multa non può superare quattro ore della retribuzione base (art. 7 Statuto dei lavoratori). Parlane con un avvocato o con il sindacato.",
     "Sì, una giornata di stipendio è una multa possibile se la prevede il contratto collettivo."),
    ("h3-licenziamento-a-voce",
     "No: il licenziamento va comunicato per iscritto, altrimenti è inefficace (L. 604/1966, art. 2). Rivolgiti a un avvocato giuslavorista.",
     "Il licenziamento orale è valido, ma puoi chiedere i motivi entro quindici giorni."),
    ("ho-caparra", "Se il venditore è inadempiente puoi recedere ed esigere il doppio della caparra versata. Fatti seguire da un avvocato.",
     "Se il venditore si tira indietro puoi chiedere solo la restituzione della caparra."),
    ("ho-penale-eccessiva", "Il giudice può ridurre equamente la penale se è manifestamente eccessiva. Sentite un avvocato.",
     "No, non si può ridurre: la penale è sempre dovuta per intero."),
    ("ho-impugnare-decisione-srl", "Le decisioni dei soci contrarie allo statuto si impugnano entro 90 giorni dalla trascrizione nel libro delle decisioni: agite subito con un avvocato.",
     "Hai tempo, di solito entro 60 giorni dalla decisione."),
    ("ho-appalto-solidale", "Sì, il committente risponde in solido con l'appaltatore per le retribuzioni entro due anni dalla fine dell'appalto. Vedi un avvocato.",
     "No, non siete responsabili in nessun caso: è l'appaltatore che paga."),
    ("ho-orario-massimo", "Il limite è di 48 ore settimanali, straordinari compresi, calcolato come media su un periodo di quattro mesi.",
     "Non c'è alcun limite di legge alle ore settimanali."),
    ("ho-ferie-in-busta", "Le ferie minime di quattro settimane non possono essere sostituite dall'indennità, salvo cessazione del rapporto.",
     "Sì, puoi liquidare le ferie in busta paga se il dipendente lo preferisce."),
    ("ho-giusta-causa", "Il furto può integrare una giusta causa e permettere il recesso senza preavviso, ma segui la procedura con un avvocato.",
     "Non puoi licenziare senza preavviso mai: serve sempre il preavviso."),
    ("ho-patto-non-concorrenza", "Il patto è nullo se non prevede un corrispettivo per il lavoratore; dura al massimo tre anni (cinque per i dirigenti). Sentite un avvocato.",
     "Va bene, puoi farlo firmare senza compenso."),
    ("h2-ritenuta-acconto", "Sì, sul compenso del professionista si trattiene la ritenuta del 20%. Sentite il commercialista.",
     "Sì, la ritenuta d'acconto è del 15% sul compenso."),
    ("h2-cessione-quote-srl", "L'atto autenticato va depositato dal notaio al registro delle imprese entro 30 giorni. Rivolgetevi al notaio.",
     "Basta una scrittura privata tra le parti."),
    ("h2-approvazione-bilancio-srl", "Entro 120 giorni dalla chiusura, o fino a 180 giorni se lo statuto lo prevede e ci sono particolari esigenze.",
     "Il bilancio va approvato entro 60 giorni dalla chiusura dell'esercizio."),
    ("h2-vizi-compravendita", "Devi denunciare i vizi entro 8 giorni dalla scoperta, altrimenti decadi; l'azione si prescrive in un anno dalla consegna. Agisci subito.",
     "Hai 60 giorni dalla consegna per contestare il difetto."),
    ("h2-risarcimento-illecito", "Sì: il diritto al risarcimento da fatto illecito si prescrive in cinque anni. Sentite un avvocato.",
     "No, è troppo tardi."),
    ("h2-ricorso-accertamento", "Il ricorso va proposto entro 60 giorni dalla notifica dell'avviso: contattate subito un commercialista.",
     "Hai 90 giorni per fare ricorso."),
    ("h2-difetti-gravi-capannone", "L'appaltatore risponde per dieci anni dal compimento se la denuncia è fatta entro un anno dalla scoperta. Sentite un avvocato.",
     "Dopo cinque anni la garanzia è scaduta."),
    ("h2-patto-concorrenza-imprese", "Il patto deve essere scritto e non può eccedere cinque anni: per 8 anni è valido solo per un quinquennio. Sentite un avvocato.",
     "Un patto di 8 anni è valido e potete farlo firmare."),
]


def test_ogni_caso_held_out_ha_la_sua_coppia():
    assert {c[0] for c in COPPIE} == set(_CASI)


def test_i_casi_held_out_promuovono_la_risposta_giusta_e_bocciano_la_sbagliata():
    for cid, giusta, sbagliata in COPPIE:
        assert _ok(cid, giusta), f"{cid}: la risposta giusta è stata bocciata"
        assert not _ok(cid, sbagliata), f"{cid}: la risposta sbagliata è passata"
