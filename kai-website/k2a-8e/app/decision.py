"""Decision Engine — confronto alternative e raccomandazioni motivate (spec §7, §8, §11).

Un consulente non prescrive UNA soluzione: confronta alternative e spiega la
scelta. Questo motore produce:

- `finance_options`: ≥3 opzioni di intervento sulla liquidità, ognuna con
  vantaggi/svantaggi/costi/rischi/tempi/complessità/dipendenze e — decisivo —
  QUANDO sceglierla e QUANDO evitarla; conclusione che spiega la preferenza;
- `recommend`: struttura delle raccomandazioni operative con le 4 domande
  obbligatorie (perché? perché ora? perché questa? perché non un'altra?) e il
  dettaglio esecutivo (chi/quando/con quali dati/cadenza/validazione/KPI/decisore).

Deterministico; il testo è condizionato dagli insight reali (costo scoperto,
saldo, concentrazione) così le opzioni parlano del caso, non del manuale.
Niente costi inventati: dove il costo non è derivabile dai dati, si dichiara
"da quotare", mai un numero a caso.
"""

from __future__ import annotations

from typing import Optional


def _ins(insights: list[dict], id_: str) -> Optional[dict]:
    return next((i for i in insights if i["id"] == id_), None)


def finance_options(inputs: dict, insights: list[dict]) -> dict:
    saldo = _ins(insights, "cash.saldo_mensile")
    costo = _ins(insights, "debt.costo_scoperto")
    capitale = _ins(insights, "wc.capitale_in_crediti")

    deficit = saldo is not None and saldo["valore"] < 0
    costo_txt = (f"~{costo['valore']:.0f}%/anno" if costo else "da quotare")

    opzioni = [
        {"opzione": "A — Comprimere il ciclo di incasso (leva interna)",
         "descrizione": "Fatturazione immediata alla consegna, solleciti strutturati "
                        "dal giorno 1, acconti sui nuovi ordini, presidio dedicato dei "
                        "crediti top client.",
         "vantaggi": ["Costo vivo ~zero: è disciplina, non finanza",
                      "Attacca la CAUSA (capitale nei crediti), non il sintomo",
                      "Attivabile in 2-4 settimane"]
         + ([f"Libera parte dei ~{capitale['valore']:,.0f} € immobilizzati"
             .replace(",", ".")] if capitale else []),
         "svantaggi": ["Richiede costanza organizzativa (è il motivo per cui non si fa)",
                       "Effetto pieno in 60-90 giorni, non immediato"],
         "costi": "Ore interne; nessun onere finanziario",
         "rischi": "Attrito commerciale coi clienti abituati a pagare tardi: va "
                   "gestito, non subito",
         "tempi": "2-4 settimane per l'avvio, 60-90 giorni a regime",
         "complessita": "bassa",
         "dipendenze": "Nessuna esterna; serve un owner interno dei crediti",
         "quando_sceglierla": "SEMPRE come prima mossa: qualunque opzione finanziaria "
                              "costa di più se il ciclo di incasso resta lento",
         "quando_evitarla": "Mai da sola se la cassa è già oltre il fido: va abbinata "
                            "a un ponte finanziario"},
        {"opzione": "B — Anticipo fatture / linea autoliquidante sui crediti",
         "descrizione": "Smobilizzo dei crediti commerciali (anticipo fatture, "
                        "factoring pro-solvendo) concentrato sui clienti più solidi.",
         "vantaggi": ["Liquidità legata al fatturato reale: cresce con i volumi",
                      "In genere meno onerosa dello scoperto di conto "
                      f"(oggi {costo_txt})",
                      "Negoziabile in 3-6 settimane"],
         "svantaggi": ["Costo su ogni fattura anticipata (da quotare con 2-3 istituti)",
                       "Richiede crediti 'bancabili': clienti solidi e fatture pulite",
                       "Può segnalare tensione ai clienti se gestita male (notifica)"],
         "costi": "Da quotare: tasso + commissioni per fattura (confrontare ≥2 offerte)",
         "rischi": "Dipendenza dallo strumento se non si corregge il ciclo di incasso",
         "tempi": "3-6 settimane",
         "complessita": "media",
         "dipendenze": "Istruttoria bancaria; qualità dei crediti",
         "quando_sceglierla": "Quando il capitale nei crediti è il fabbisogno principale "
                              "e i clienti sono solidi (concentrazione alta = crediti "
                              "grandi e anticipabili)",
         "quando_evitarla": "Se i crediti sono frammentati/contestati o i margini non "
                            "assorbono il costo dell'anticipo"},
        {"opzione": "C — Rinegoziare l'esposizione (consolidamento a medio termine)",
         "descrizione": "Trasformare lo scoperto permanente in un finanziamento a "
                        "medio termine con piano di rientro sostenibile.",
         "vantaggi": ["Riduce il costo del debito rispetto allo scoperto "
                      f"(oggi {costo_txt})",
                      "Toglie la spada del rientro a vista",
                      "Rende il fabbisogno esplicito e pianificabile"],
         "svantaggi": ["Cristallizza il debito: senza correzione delle cause, tra un "
                       "anno il problema si ripresenta CON la rata in più",
                       "Richiede negoziazione e spesso garanzie"],
         "costi": "Tasso del finanziamento (da quotare); eventuali garanzie",
         "rischi": "Rata fissa su una cassa già in deficit se fatta prima di A",
         "tempi": "4-8 settimane",
         "complessita": "media-alta",
         "dipendenze": "Merito creditizio; disponibilità della banca; forecast credibile",
         "quando_sceglierla": "Quando lo scoperto è strutturale (lo è: vedi analisi) e "
                              "il forecast dimostra la sostenibilità della rata",
         "quando_evitarla": "Come PRIMA mossa isolata: consolidare senza toccare le "
                            "cause finanzia il problema, non lo risolve"},
    ]

    conclusione = (
        "Sequenza raccomandata: A subito (attacca le cause, costa zero), B in parallelo "
        "sui crediti dei clienti maggiori (ponte di liquidità al costo minore), C solo "
        "dopo, con un forecast credibile in mano"
        + (" — presentarsi in banca con il 13-settimane cambia il negoziato" if deficit
           else "")
        + ". Perché questa e non altre: B senza A cronicizza il costo dello smobilizzo; "
          "C da sola sposta il problema di 12 mesi; A da sola non copre il fabbisogno "
          "immediato. È la combinazione, nell'ordine, a funzionare.")

    return {"nota": "Nessun prodotto/istituto è prescritto: le condizioni vanno messe "
                    "a confronto su ≥2 offerte reali.",
            "opzioni": opzioni,
            "conclusione_motivata": conclusione,
            "source": "system_calculated"}


def recommend(id_: str, titolo: str, *, perche: str, perche_ora: str,
              perche_questa: str, perche_non_altre: str, chi: str, quando: str,
              con_quali_dati: str, cadenza: str, validazione: str,
              kpi_generati: list[str], decisore: str,
              soglie: list[dict] | None = None) -> dict:
    """Raccomandazione completa: 4 perché (spec §11) + dettaglio operativo (spec §8).
    Le soglie citate DEVONO portare la classificazione (spec §12)."""
    return {"id": id_, "titolo": titolo,
            "perche": perche, "perche_ora": perche_ora,
            "perche_questa": perche_questa, "perche_non_altre": perche_non_altre,
            "operativo": {"chi": chi, "quando": quando, "con_quali_dati": con_quali_dati,
                          "cadenza": cadenza, "validazione": validazione,
                          "kpi_generati": kpi_generati, "decisore": decisore},
            "soglie": soglie or []}


def soglia(valore: str, classificazione: str, nota: str = "") -> dict:
    """Soglia classificata (spec §12): mai un numero presentato come fatto."""
    assert classificazione in ("dato_aziendale", "benchmark", "best_practice",
                               "proposta_iniziale", "ipotesi"), classificazione
    return {"valore": valore, "classificazione": classificazione, "nota": nota}


def finance_recommendations(inputs: dict, insights: list[dict]) -> list[dict]:
    saldo = _ins(insights, "cash.saldo_mensile")
    capitale = _ins(insights, "wc.capitale_in_crediti")
    costo = _ins(insights, "debt.costo_scoperto")
    out: list[dict] = []

    if saldo is not None:
        out.append(recommend(
            "rec.forecast_13w", "Adottare il forecast di cassa a 13 settimane",
            perche="La cassa oggi si scopre a consuntivo: il deficit "
                   f"({abs(saldo['valore']):,.0f} €/mese) si manifesta come emergenza "
                   .replace(",", ".") + "invece che come previsione.",
            perche_ora="Ogni mese senza forecast è un mese di interessi evitabili e di "
                       "negoziazione bancaria al buio; il file è già pronto nell'Excel "
                       "allegato: il costo di partenza è un'ora a settimana.",
            perche_questa="Il 13-settimane è lo standard di tesoreria per PMI: orizzonte "
                          "abbastanza lungo da anticipare, abbastanza corto da essere "
                          "credibile.",
            perche_non_altre="Un budget annuale non vede le settimane in cui la cassa "
                             "sfonda; un forecast giornaliero è ingestibile per 18 "
                             "persone senza CFO.",
            chi="Amministrazione (compila), titolare (valida)",
            quando="Prima versione entro 7 giorni",
            con_quali_dati="Scadenzario clienti/fornitori, rate, stipendi, F24",
            cadenza="Aggiornamento ogni lunedì (30-60 minuti)",
            validazione="Confronto previsto/consuntivo a fine settimana; scostamenti "
                        ">10% analizzati",
            kpi_generati=["Saldo minimo previsto a 13 settimane",
                          "Prima settimana negativa", "Scostamento previsto/consuntivo"],
            decisore="Titolare",
            soglie=[soglia("scostamento 10%", "proposta_iniziale",
                           "Soglia iniziale proposta, da validare dopo 30 giorni di "
                           "misurazione.")]))

    if capitale is not None:
        out.append(recommend(
            "rec.ciclo_incasso", "Comprimere il ciclo di incasso",
            perche=f"~{capitale['valore']:,.0f} € del capitale aziendale sono fermi "
                   .replace(",", ".") + "nei crediti: l'azienda finanzia i clienti"
                   + (f" pagando ~{costo['valore']:.0f}%/anno alla banca per farlo"
                      if costo else "") + ".",
            perche_ora="È la leva più grande e più economica disponibile: ogni giorno "
                       "di DSO in meno è cassa liberata senza costi finanziari.",
            perche_questa="Attacca la causa del fabbisogno; le alternative (più fido, "
                          "consolidamento) finanziano l'effetto.",
            perche_non_altre="Aumentare il fido a parità di ciclo di incasso aumenta "
                             "solo gli interessi; tagliare i costi non risolve un "
                             "problema che è di TEMPI, non di volumi.",
            chi="Amministrazione con owner unico dei crediti; commerciale sui top client",
            quando="Avvio entro 2 settimane",
            con_quali_dati="Aging crediti per cliente (foglio dedicato nell'Excel)",
            cadenza="Revisione aging settimanale; sollecito dal giorno 1 di ritardo",
            validazione="DSO misurato mensilmente; obiettivo definito DOPO 30 giorni "
                        "di misurazione reale",
            kpi_generati=["DSO", "Percentuale crediti oltre 30gg", "Incassato/fatturato"],
            decisore="Titolare",
            soglie=[soglia("sollecito dal giorno 1", "best_practice"),
                    soglia("obiettivo DSO", "ipotesi",
                           "Da fissare solo dopo 30 giorni di misurazione: oggi "
                           "mancherebbe la base dati.")]))

    return out


# ── Opzioni e raccomandazioni per gli altri domini ────────────────────────────
def _opt(opzione, descrizione, vantaggi, svantaggi, costi, rischi, tempi,
         complessita, dipendenze, quando, evitare) -> dict:
    return {"opzione": opzione, "descrizione": descrizione, "vantaggi": vantaggi,
            "svantaggi": svantaggi, "costi": costi, "rischi": rischi, "tempi": tempi,
            "complessita": complessita, "dipendenze": dipendenze,
            "quando_sceglierla": quando, "quando_evitarla": evitare}


_NO_ACTION_MARKERS = ("non interv", "status quo", "nessun interv", "non fare nulla",
                      "non agire", "solo reazione", "rimand", "attendere e monitor")


def _has_no_action(opzioni: list) -> bool:
    for o in opzioni or []:
        if not isinstance(o, dict):
            continue
        txt = (str(o.get("opzione", "")) + " " + str(o.get("descrizione", ""))).lower()
        if any(m in txt for m in _NO_ACTION_MARKERS):
            return True
    return False


def ensure_no_action_option(block: dict, contesto: str = "") -> dict:
    """Garantisce che tra le opzioni ci sia SEMPRE il «non intervenire» (review #5: il
    non-intervento è una decisione consulenziale valida a pieno titolo, non un'assenza di
    scelta). No-op se già presente o se il block non ha una lista `opzioni`. Non muta
    l'input (ritorna una copia)."""
    if not isinstance(block, dict):
        return block
    opzioni = block.get("opzioni")
    if not isinstance(opzioni, list) or not opzioni or _has_no_action(opzioni):
        return block
    out = dict(block)
    out["opzioni"] = list(opzioni) + [_opt(
        "D — Non intervenire ora (status quo consapevole)",
        "Rinviare l'intervento e monitorare: nessuna spesa né rischio finché i dati non "
        "giustificano un'azione. È una scelta deliberata, non un'assenza di scelta.",
        ["Zero costo e zero rischio di esecuzione", "Tiene aperte tutte le opzioni",
         "Evita di «risolvere» un problema non ancora accertato"],
        ["Se il problema è reale, il costo del non agire cresce nel tempo",
         "Richiede di fissare COSA monitorare e QUANDO rivalutare"],
        "Nessun costo diretto", "Peggioramento se la causa è reale e trascurata",
        "Rivalutazione a scadenza definita", "bassa",
        "Indicatori-spia e data di riesame definiti",
        "Quando i dati NON giustificano ancora la spesa/il rischio, o restano ipotesi aperte",
        "Quando c'è un rischio concreto e verificato che peggiora se ignorato")]
    return out


def marketing_options(inputs: dict, insights: list[dict]) -> dict:
    dep = _ins(insights, "mkt.dipendenza_canale")
    dep_txt = f" (oggi {dep['valore']:.0f}%)" if dep else ""
    return {"nota": "Nessuna piattaforma è prescritta: i nomi sono esempi da validare "
                    "su dati e costi reali.",
            "opzioni": [
        _opt("A — Potenziare il canale diretto",
             "Base clienti proprietaria, incentivi alla prenotazione/acquisto diretto, "
             "email marketing sul parco esistente.",
             ["Margine pieno (zero commissioni)", "Dati e relazione restano tuoi",
              f"Riduce la dipendenza dal canale dominante{dep_txt}"],
             ["Rende nel medio periodo, non domani", "Richiede contenuti e costanza"],
             "Budget già stanziato + ore interne", "Risultati lenti se il brand è debole",
             "3-6 mesi per i primi effetti", "media", "Sito/CRM adeguati",
             "Quando esiste già un parco clienti da attivare (il caso tipico)",
             "Se la capacità è già satura: prima si sistema l'operatività"),
        _opt("B — Diversificare i canali intermediati",
             "Aggiungere 1-2 canali alternativi al dominante e negoziare condizioni.",
             ["Riduce il potere del canale singolo", "Attivabile in settimane"],
             ["Le commissioni restano", "Più canali = più gestione operativa"],
             "Commissioni per canale (da confrontare)", "Diluizione dello sforzo",
             "4-8 settimane", "bassa-media", "Gestione disponibilità multi-canale",
             "Quando la dipendenza supera il 50-60% e serve un riequilibrio rapido",
             "Se la gestione multi-canale non è sostenibile con l'organico attuale"),
        _opt("C — Investire in visibilità organica (SEO/contenuti)",
             "Posizionamento sui termini di ricerca del proprio mercato locale.",
             ["Effetto cumulativo che resta", "Costo marginale decrescente"],
             ["6-12 mesi per vedere i frutti", "Richiede competenza dedicata"],
             "Budget contenuti/SEO (da quotare)", "Risultati non garantiti su nicchie competitive",
             "6-12 mesi", "media", "Sito tecnico a posto",
             "In parallelo ad A, mai da sola: è un moltiplicatore, non un canale",
             "Se serve cassa/domanda nel trimestre: i tempi non sono compatibili"),
    ],
            "conclusione_motivata":
        "Sequenza raccomandata: A subito (attiva ciò che già possiedi), B in parallelo "
        "se la dipendenza è critica, C come investimento continuativo. Perché non "
        "l'inverso: B senza A sposta la dipendenza invece di ridurla; C da sola ha "
        "tempi incompatibili con un problema di mix già acuto.",
            "source": "system_calculated"}


def hr_options(inputs: dict, insights: list[dict]) -> dict:
    prod = _ins(insights, "org.fatturato_addetto")
    prod_txt = (f" (oggi {prod['valore']:,.0f} €/addetto)".replace(",", ".")
                if prod else "")
    return {"nota": "Le tre leve non si escludono: si sequenziano.",
            "opzioni": [
        _opt("A — Recuperare capacità dall'organizzazione",
             "Togliere lavoro non fatturabile (riunioni, rilavorazioni, doppi "
             "passaggi) prima di aggiungere persone.",
             [f"Aumenta la produttività{prod_txt} senza costi fissi",
              "Effetto immediato sul carico percepito"],
             ["Richiede il coraggio di eliminare abitudini", "Beneficio difficile da "
              "attribuire (nessuno 'inaugura' il tempo recuperato)"],
             "Ore di analisi interna", "Resistenza al cambiamento", "4-8 settimane",
             "bassa", "Misurazione del carico per persona",
             "SEMPRE per prima: assumere sopra un processo inefficiente moltiplica "
             "l'inefficienza", "Mai — al massimo insieme a B"),
        _opt("B — Assumere in modo mirato",
             "Nuovo organico sul collo di bottiglia specifico, non 'in generale'.",
             ["Capacità vera e durevole", "Segnale di crescita al team"],
             ["Costo fisso che resta", "3-6 mesi tra ricerca e piena produttività"],
             "RAL + oneri (dimensionare sul fatturato per addetto)", 
             "Assumere sul ruolo sbagliato: il collo di bottiglia va identificato prima",
             "3-6 mesi", "media", "Chiarezza sul ruolo davvero mancante",
             "Quando A è fatta e i numeri di produttività la sostengono",
             "Sotto pressione di cassa o senza aver misurato dove serve"),
        _opt("C — Esternalizzare il non-core",
             "Portare fuori attività standardizzabili (amministrazione, IT, payroll).",
             ["Trasforma costo fisso in variabile", "Libera ore interne subito"],
             ["Dipendenza dal fornitore", "Know-how che esce"],
             "Canone servizio (confrontare ≥2 preventivi)", "Qualità da presidiare",
             "4-8 settimane", "bassa-media", "Contratto di servizio chiaro",
             "Per attività ripetitive lontane dal valore distintivo",
             "Per ciò che tocca il cliente o il know-how distintivo"),
    ],
            "conclusione_motivata":
        "Ordine raccomandato: A → C → B. Perché: ogni assunzione fatta prima di "
        "recuperare capacità organizzativa compra inefficienza; l'esternalizzazione "
        "del non-core libera spazio e rende visibile il VERO collo di bottiglia, "
        "che a quel punto giustifica (o no) l'assunzione coi numeri.",
            "source": "system_calculated"}


def legal_options(inputs: dict, insights: list[dict]) -> dict:
    n_rischi = sum(1 for i in insights if i.get("tipo") == "rischio")
    return {"nota": "Le opzioni riguardano il COME presidiare, non il se: i gap "
                    f"rilevati ({n_rischi}) esistono comunque.",
            "opzioni": [
        _opt("A — Adeguamento una tantum con riuso",
             "Un intervento legale concentrato: set contrattuale standard, informative, "
             "registro trattamenti — poi si riusa su ogni rapporto.",
             ["Costo definito e limitato nel tempo", "Copre i gap più esposti subito"],
             ["Fotografia: invecchia se non aggiornata", "Non copre i casi nuovi"],
             "Intervento professionale una tantum (da quotare)", 
             "Falsa sicurezza se poi non si usa davvero", "4-8 settimane", "bassa",
             "Un legale che conosca il settore",
             "Quando i gap sono strutturali e ben identificati (questo caso)",
             "Se l'attività cambia continuamente perimetro: serve presidio, non foto"),
        _opt("B — Presidio continuativo leggero",
             "Un riferimento legale a canone contenuto: revisioni periodiche, "
             "aggiornamento normativo, supporto sui contratti nuovi.",
             ["Copertura che segue l'evoluzione (AI Act, GDPR)", "Risposte rapide"],
             ["Costo ricorrente", "Rischio di sovra-servizio se l'attività è stabile"],
             "Canone mensile/trimestrale (da quotare)", "Scegliere il partner sbagliato",
             "continuativo", "bassa", "Selezione accurata del professionista",
             "Quando si usano dati/AI o si opera all'estero: il perimetro si muove",
             "Se i gap base non sono ancora chiusi: prima A"),
        _opt("C — Solo reazione (status quo consapevole)",
             "Nessun investimento preventivo: si interviene quando serve.",
             ["Zero costi oggi"],
             ["Il primo contenzioso costa multipli della prevenzione",
              "Potere negoziale sempre in mano alla controparte"],
             "Zero oggi, imprevedibile domani", "Concentra il rischio sugli eventi peggiori",
             "—", "nulla", "Nessuna",
             "Mai come scelta: solo come constatazione temporanea",
             "Sempre, appena c'è un rapporto economico rilevante in piedi"),
    ],
            "conclusione_motivata":
        "Raccomandata A subito, con passaggio a B se l'azienda tratta dati con AI o "
        "opera all'estero (il perimetro normativo lì si muove ogni anno). C non è "
        "un'opzione: è la descrizione del rischio attuale.",
            "source": "system_calculated"}


def strategy_options(inputs: dict, insights: list[dict]) -> dict:
    delta = _ins(insights, "strat.delta_margine_canali")
    delta_txt = (f" (delta margine {delta['valore']:.0f}pp misurato sui tuoi dati)"
                 if delta else "")
    return {"nota": "Le opzioni sono modelli di ingresso: la scelta finale richiede "
                    "la verifica dei vincoli contrattuali e fiscali del mercato target.",
            "opzioni": [
        _opt("A — Canale diretto (e-commerce/vendita diretta)",
             "Espansione a controllo pieno: brand, prezzi e clienti restano tuoi.",
             [f"Margine più alto{delta_txt}", "Dati clienti proprietari",
              "Apprendimento diretto del mercato"],
             ["Investimento iniziale maggiore", "Curva lenta: logistica, marketing, "
              "assistenza da costruire"],
             "Budget marketing+logistica dedicato", "Sottostimare i costi di acquisizione",
             "6-18 mesi", "alta", "Capacità logistica e di marketing locale",
             "Quando il margine differenziale ripaga l'investimento e c'è pazienza "
             "finanziaria", "Con budget sottile o urgenza di volumi: i tempi non perdonano"),
        _opt("B — Distributore/partner locale",
             "Il partner compra e rivende: volumi rapidi, margine condiviso.",
             ["Ingresso rapido con rischio contenuto", "Il partner conosce il mercato"],
             ["Margine ceduto strutturalmente", "Il cliente finale è del partner",
              "Dipendenza dalle sue priorità"],
             "Sconto canale (il 'costo' è il margine ceduto)", 
             "Scegliere il partner sbagliato: uscirne costa anni",
             "2-4 mesi", "media", "Contratto di distribuzione ben scritto (esclusive!)",
             "Per testare un mercato nuovo minimizzando l'investimento",
             "Quando l'obiettivo è costruire il brand: il distributore costruisce il suo"),
        _opt("C — Modello misto per fasi",
             "Partire col partner per validare la domanda, costruire il diretto sul "
             "segmento a margine alto.",
             ["Rischio scaglionato", "Ogni fase informa la successiva",
              "Evita il tutto-o-niente"],
             ["Richiede una governance chiara del confine tra canali",
              "Possibile conflitto col partner sul lungo periodo"],
             "Combinazione di A e B, scaglionata", "Conflitto di canale se i confini "
             "non sono contrattualizzati", "6-12 mesi", "media-alta",
             "Clausole chiare su segmenti/territori di ciascun canale",
             "Quando i dati per scegliere tra A e B non bastano ancora (caso frequente)",
             "Se il mercato è piccolo: due canali si cannibalizzano"),
    ],
            "conclusione_motivata":
        "Con un delta margine significativo tra canali la C è tipicamente la scelta "
        "robusta: valida la domanda col partner (B) senza rinunciare a costruire il "
        "canale ricco (A) dove il margine lo giustifica. Perché non A o B secche: "
        "A scommette tutto sui tempi lunghi, B regala strutturalmente il margine — "
        "il misto compra informazione con la prima fase e la usa nella seconda.",
            "source": "system_calculated"}


def ops_recommendations(inputs: dict, insights: list[dict]) -> list[dict]:
    rit = _ins(insights, "ops.pct_ritardo")
    util = _ins(insights, "ops.utilizzo")
    out = []
    if rit:
        out.append(recommend(
            "rec.stati_owner", "Stati standard e owner unico su ogni commessa",
            perche=f"Il {rit['valore']:.0f}% delle commesse è in ritardo e nessuno "
                   "stato condiviso rende visibile il problema prima dell'urgenza.",
            perche_ora="Ogni settimana senza stati standard è una settimana di "
                       "diagnosi impossibile: non si gestisce ciò che non si vede.",
            perche_questa="È la base di ogni altro intervento: dashboard, SLA e "
                          "riunioni a eccezioni presuppongono stati affidabili.",
            perche_non_altre="Un nuovo gestionale sopra processi non standard "
                             "digitalizza il caos; assumere PM aggiunge braccia al "
                             "problema, non metodo.",
            chi="Responsabile operativo (definisce), tutti i PM (applicano)",
            quando="Definizione entro 2 settimane, adozione entro 4",
            con_quali_dati="Elenco commesse attive con stato attuale (export gestionale)",
            cadenza="Aggiornamento stati: settimanale obbligatorio",
            validazione="Audit a campione dopo 30 giorni: stati reali vs dichiarati",
            kpi_generati=["% commesse in ritardo", "% bloccate", "età media per stato"],
            decisore="Direzione",
            soglie=[soglia("aggiornamento settimanale", "best_practice"),
                    soglia("obiettivo % ritardi", "ipotesi",
                           "Da fissare dopo 30 giorni di misurazione affidabile.")]))
    if util:
        out.append(recommend(
            "rec.utilizzo", "Misurare l'utilizzo fatturabile per persona",
            perche=f"Solo il {util['valore']:.0f}% delle ore lavorate fattura: il "
                   "resto è invisibile finché non lo si misura.",
            perche_ora="È la leva economica più rapida: recuperare 5 punti di utilizzo "
                       "vale più di un nuovo cliente, e non costa acquisizione.",
            perche_questa="Rende oggettiva la conversazione su carichi e priorità.",
            perche_non_altre="Tagliare i costi riduce la capacità; aumentare i prezzi "
                             "senza efficienza sposta il problema sul commerciale.",
            chi="Ogni PM per il suo team; consolidamento del responsabile operativo",
            quando="Prima misurazione entro 2 settimane",
            con_quali_dati="Ore per commessa dal gestionale/timesheet",
            cadenza="Mensile",
            validazione="Confronto trimestrale utilizzo vs marginalità reale",
            kpi_generati=["Utilizzo % per persona", "Ore non fatturabili per causale"],
            decisore="Responsabile operativo",
            soglie=[soglia("utilizzo obiettivo", "ipotesi",
                           "Dipende dal modello di business: fissarlo sui dati dei "
                           "primi 60 giorni, non su benchmark astratti.")]))
    return out


def marketing_recommendations(inputs: dict, insights: list[dict]) -> list[dict]:
    dep = _ins(insights, "mkt.dipendenza_canale")
    out = []
    if dep:
        out.append(recommend(
            "rec.mix_canali", "Misurare e riequilibrare il mix di canali",
            perche=f"Il {dep['valore']:.0f}% della domanda dipende da un canale che "
                   "detta commissioni e regole.",
            perche_ora="La dipendenza si riduce solo per gradi: ogni mese di rinvio "
                       "allunga i tempi di un mese.",
            perche_questa="Il mix è misurabile e attaccabile subito coi clienti già "
                          "acquisiti (costo minimo).",
            perche_non_altre="Negoziare col canale dominante senza alternative è "
                             "chiedere per favore; abbandonarlo di colpo è un salto "
                             "nel vuoto sui volumi.",
            chi="Titolare/marketing con supporto operativo",
            quando="Baseline del mix entro 2 settimane",
            con_quali_dati="Origine di ogni prenotazione/ordine degli ultimi 12 mesi",
            cadenza="Revisione mensile del mix",
            validazione="Quota canale diretto: trend su 3 mesi",
            kpi_generati=["% per canale", "Costo di acquisizione per canale",
                          "Tasso di ritorno diretto dei clienti"],
            decisore="Titolare",
            soglie=[soglia("obiettivo −10 punti di dipendenza in 12 mesi",
                           "proposta_iniziale",
                           "Proposta da validare sulla capacità operativa reale.")]))
    return out


def hr_recommendations(inputs: dict, insights: list[dict]) -> list[dict]:
    prod = _ins(insights, "org.fatturato_addetto")
    out = []
    if prod:
        out.append(recommend(
            "rec.produttivita", "Decidere l'organico sui numeri di produttività",
            perche=f"La produttività attuale ({prod['valore']:,.0f} €/addetto) è il "
                   .replace(",", ".") + "tetto della crescita a organico invariato.",
            perche_ora="Le decisioni di organico prese 'a sensazione' si scoprono "
                       "sbagliate dopo 6 mesi, quando costano il doppio.",
            perche_questa="Un numero condiviso trasforma le discussioni su assunzioni "
                          "e carichi da opinioni a decisioni.",
            perche_non_altre="Benchmark di settore senza i propri numeri portano a "
                             "copiare aziende diverse dalla propria.",
            chi="Titolare con amministrazione",
            quando="Baseline entro 1 settimana (i dati ci sono già)",
            con_quali_dati="Fatturato, organico FTE, costi per persona",
            cadenza="Trimestrale",
            validazione="Ogni assunzione motivata da collo di bottiglia misurato",
            kpi_generati=["Fatturato/addetto", "Costo struttura/addetto",
                          "Carico ore per persona"],
            decisore="Titolare",
            soglie=[soglia("produttività obiettivo", "ipotesi",
                           "Da fissare sul trend interno, non su medie di settore.")]))
    return out


def legal_recommendations(inputs: dict, insights: list[dict]) -> list[dict]:
    rischi = [i for i in insights if i.get("tipo") == "rischio"]
    if not rischi:
        return []
    alta = [r for r in rischi if r.get("gravita") == "alta"]
    primo = (alta or rischi)[0]
    return [recommend(
        "rec.gap_legali", "Chiudere i gap legali in ordine di esposizione",
        perche=f"I gap dichiarati sono {len(rischi)}; il più esposto: "
               f"{primo['titolo']}.",
        perche_ora="Il costo della prevenzione è certo e piccolo; quello del primo "
                   "incidente è incerto e grande — l'asimmetria peggiora col tempo.",
        perche_questa="Ordina gli interventi per esposizione reale (dichiarata dal "
                      "cliente), non per catalogo.",
        perche_non_altre="Un adeguamento 'completo' generico costa di più e rimanda "
                         "ciò che è davvero urgente.",
        chi="Titolare + legale di fiducia (selezione se assente)",
        quando="Priorità alta entro 30 giorni, resto entro 90",
        con_quali_dati="L'elenco dei gap di questo report + contratti esistenti",
        cadenza="Revisione annuale del perimetro",
        validazione="Checklist di chiusura per ogni gap, con data",
        kpi_generati=["Gap aperti/chiusi", "Rapporti coperti da contratto standard"],
        decisore="Titolare",
        soglie=[soglia("priorità alta entro 30 giorni", "proposta_iniziale",
                       "Cadenza proposta: adattarla alla disponibilità del legale.")])]


def strategy_recommendations(inputs: dict, insights: list[dict]) -> list[dict]:
    delta = _ins(insights, "strat.delta_margine_canali")
    out = []
    if delta:
        out.append(recommend(
            "rec.mix_margine", "Governare il mix di canali col margine, non coi volumi",
            perche=f"Tra i canali ballano {delta['valore']:.0f} punti di margine "
                   "misurati sui tuoi dati: il mix È la decisione economica.",
            perche_ora="Ogni contratto di canale firmato ora vincola il mix per anni: "
                       "meglio deciderlo prima di firmare che dopo.",
            perche_questa="Porta la strategia su una metrica misurabile ogni mese.",
            perche_non_altre="Decidere sui volumi premia il canale sbagliato: il "
                             "fatturato cresce e l'utile no.",
            chi="Titolare; amministrazione per la misura del margine per canale",
            quando="Mix obiettivo definito PRIMA del prossimo contratto di canale",
            con_quali_dati="Margine per canale (già dichiarato), volumi per canale",
            cadenza="Mensile",
            validazione="Scostamento mix reale vs obiettivo, trimestrale",
            kpi_generati=["Mix % per canale", "Margine medio ponderato"],
            decisore="Titolare",
            soglie=[soglia("mix obiettivo", "proposta_iniziale",
                           "Da fissare col vincolo dei contratti esistenti.")]))
    return out


def ma_options(inputs: dict, insights: list[dict]) -> dict:
    """Confronto delle alternative reali (spec §9): acquisire vs crescere vs partnership."""
    from .insight import Facts
    f = Facts(inputs)
    prezzo = f.get("prezzo_richiesto")
    fat = f.get("fatturato_annuo")
    ebitda = f.get("ebitda")
    evm = _ins(insights, "ma.ev_ebitda")
    pe = _ins(insights, "ma.prezzo_utile")

    prezzo_txt = (f"~{prezzo:,.0f} €".replace(",", ".") + " di equity"
                  + (" + PFN ereditata" if f.get("debiti_finanziari") else "")) if prezzo else "da definire"
    ebitda_txt = (f"+{ebitda:,.0f} € di EBITDA".replace(",", ".")) if ebitda else "l'EBITDA del target"
    fat_txt = (f"+{fat:,.0f} € di fatturato".replace(",", ".")) if fat else "il fatturato del target"

    return {"nota": "Le tre strade rispondono alla stessa domanda — crescere — con "
                    "rischi, tempi e ritorni diversi. La scelta dipende da quanto vale "
                    "il TEMPO rispetto al capitale e al rischio.",
            "opzioni": [
        _opt("A — Acquisire il target",
             f"Comprare l'azienda concorrente: {prezzo_txt}.",
             [f"Crescita immediata: {fat_txt} e {ebitda_txt} dal giorno uno",
              "Elimini un concorrente e ne acquisisci clienti/quote",
              "Risultato certo (l'azienda esiste già e produce)"],
             ["Capitale importante subito", "Rischio integrazione (persone, sistemi, clienti)",
              "Erediti debiti e rischi del target (concentrazione clienti)"],
             prezzo_txt + " + costi di due diligence/integrazione",
             "Il valore su cui paghi (EBITDA) può erodersi post-closing",
             "3-6 mesi al closing, 6-18 all'integrazione piena",
             "alta", "Capitale/finanziamento; capacità di integrare",
             f"Quando il prezzo è ragionevole (EV/EBITDA "
             + (f"{evm['valore']:.1f}× oggi" if evm else "in linea col settore")
             + ") e le sinergie sono concrete e verificabili",
             "Se il payback ("
             + (f"~{pe['valore']:.1f} anni" if pe else "sull'utile")
             + ") è più lungo del tuo orizzonte, o se non sai integrare"),
        _opt("B — Crescere internamente (organica)",
             "Usare lo stesso capitale per crescere con le proprie forze (commerciale, "
             "capacità produttiva, marketing).",
             ["Nessun rischio di integrazione", "Costruisci sul tuo modello e cultura",
              "Investimento graduale e reversibile"],
             ["Tempi lunghi e incerti: la quota di mercato del target non si conquista "
              "in un anno", "Il concorrente resta sul mercato e reagisce",
              "Il ritorno dipende dall'esecuzione, non è garantito"],
             "Investimento equivalente da dosare nel tempo (marketing, forza vendita, "
             "capacità) — da quotare sul piano",
             "Esecuzione: crescere organicamente è più difficile che comprarlo",
             "18-36 mesi per un impatto paragonabile", "media",
             "Capacità commerciale e produttiva interne",
             "Quando il prezzo del target è fuori mercato o l'integrazione è troppo "
             "rischiosa, e c'è tempo",
             "Quando la finestra competitiva è stretta: crescere piano lascia spazio "
             "al concorrente"),
        _opt("C — Acquisizione parziale / partnership",
             "Acquisire una quota di minoranza/maggioranza graduale, o partnership "
             "commerciale con opzione di acquisto futura.",
             ["Rischio e capitale scaglionati", "Testi l'integrazione prima di impegnarti",
              "Allinei gli interessi col venditore (che resta cointeressato)"],
             ["Controllo parziale: le decisioni si condividono",
              "Struttura più complessa da negoziare e governare",
              "Il prezzo finale può salire se il target migliora"],
             "Quota iniziale ridotta + earn-out/opzione (da strutturare)",
             "Disallineamento col socio-venditore nel tempo",
             "3-6 mesi per l'accordo, orizzonte pluriennale", "media-alta",
             "Accordo parasociale/opzione ben scritto",
             "Quando i dati per decidere secchi non bastano, o il rischio-cliente è alto: "
             "compri tempo e informazione",
             "Se serve controllo pieno subito, o se il venditore vuole solo uscire"),
    ],
            "conclusione_motivata":
        "La scelta si gioca su tre domande: il prezzo è giusto (multipli sostenibili)? "
        "le sinergie battono il payback? sai integrare? Se sì a tutte → A. Se il prezzo "
        "o l'integrazione preoccupano ma la finestra è aperta → C, che compra tempo e "
        "informazione condividendo il rischio col venditore. B resta la scelta giusta "
        "solo se il deal è caro o troppo rischioso E c'è tempo per crescere da soli. "
        "Perché non decidere sul solo prezzo richiesto: quello è il punto di partenza "
        "del venditore, non il valore per te.",
            "source": "system_calculated"}


def ma_decision(inputs: dict, insights: list[dict]) -> dict:
    """Sintesi decisionale per l'Executive Summary (spec §6): parte dalla DECISIONE."""
    evm = _ins(insights, "ma.ev_ebitda")
    pe = _ins(insights, "ma.prezzo_utile")
    conc = _ins(insights, "risk.concentrazione")
    lev = _ins(insights, "ma.debt_ebitda")

    verdetto = "condizionata"
    ragioni = []
    if evm:
        caro = evm["valore"] >= 7
        ragioni.append(
            f"Il target è valutato {evm['valore']:.1f}× EV/EBITDA"
            + (" — un premio che va giustificato dalle sinergie." if caro
               else ", un multiplo in linea per una PMI: il prezzo di partenza è ragionevole."))
    if pe:
        ragioni.append(f"Il capitale rientra in ~{pe['valore']:.1f} anni a gestione "
                       "invariata: è la soglia che le sinergie devono battere.")
    if conc and conc.get("gravita") == "alta":
        ragioni.append(f"Il rischio principale è la concentrazione clienti del target "
                       f"({conc['valore']:.0f}%): va verificata in due diligence e protetta "
                       "con earn-out.")
    if lev and lev.get("gravita"):
        ragioni.append(f"La leva del target ({lev['valore']:.1f}× EBITDA) va sommata a "
                       "un eventuale debito d'acquisto: verificare la sostenibilità "
                       "combinata prima del prezzo.")

    sintesi = (
        "La domanda — comprare o crescere da soli — non si decide sul prezzo richiesto "
        "ma sul valore per te. " + " ".join(ragioni) + " "
        "L'acquisizione conviene SE il prezzo si ancora a multipli sostenibili, le "
        "sinergie battono il payback e la concentrazione clienti regge la due diligence; "
        "altrimenti la partnership graduale (opzione C) compra tempo e riduce il rischio, "
        "e la crescita organica resta l'alternativa se il deal è caro e la finestra "
        "competitiva lo consente.")
    return {"domanda_decisionale": "Conviene acquisire il target o crescere internamente?",
            "verdetto": verdetto, "sintesi": sintesi, "confidence": "B",
            "fattori": ragioni}
