"""Reasoning Engine — catene causa-effetto (spec §1-§2).

Un consulente non elenca azioni: spiega PERCHÉ succede, quali cause, come sono
collegate, quali effetti producono, come risolverle. Questo motore costruisce
catene causali strutturate a 6 fasi:

    OSSERVAZIONE → CAUSE → CONSEGUENZE → PRIORITÀ → INTERVENTO → RISULTATO ATTESO

Le catene nascono a REGOLE dagli insight quantitativi (insight.py): ogni nodo
porta le sue evidenze (id degli insight / campi input) e la catena la sua
confidence. Niente LLM: se i dati per una catena non ci sono, la catena non
esiste — mai narrativa inventata.

Generico: `Chain`/`node` sono riusabili per qualunque dominio; qui le regole
finance/liquidità. Altri domini = nuove funzioni build_*_chains.
"""

from __future__ import annotations

from typing import Optional

FASI = ("osservazione", "cause", "conseguenze", "priorita", "intervento",
        "risultato_atteso")


def node(fase: str, testo: str, evidenze: list[str] | None = None) -> dict:
    assert fase in FASI, fase
    return {"fase": fase, "testo": testo, "evidenze": list(evidenze or [])}


def chain(id_: str, titolo: str, nodi: list[dict], priorita: str = "alta",
          confidence: str = "A") -> dict:
    return {"id": id_, "titolo": titolo, "catena": nodi, "priorita": priorita,
            "confidence": confidence}


def _by_id(insights: list[dict]) -> dict:
    return {i["id"]: i for i in insights}


def _fmt(v: Optional[float], unit: str = "") -> str:
    if v is None:
        return ""
    s = f"{v:,.0f}".replace(",", ".")
    return f"{s} {unit}".strip()


def build_finance_chains(insights: list[dict], inputs: dict) -> list[dict]:
    """Catene causali di tesoreria/liquidità dagli insight calcolati."""
    ins = _by_id(insights)
    chains: list[dict] = []

    saldo = ins.get("cash.saldo_mensile")
    costo = ins.get("debt.costo_scoperto")
    capitale = ins.get("wc.capitale_in_crediti")
    conc = ins.get("risk.concentrazione")
    peso = ins.get("debt.peso_interessi")

    # ── Catena 1: la spirale dello scoperto (il caso-tipo della spec §2) ──────
    if saldo and saldo["valore"] < 0 and (capitale or costo):
        cause_txt, cause_ev = [], []
        if capitale:
            cause_txt.append(f"incassi lenti che immobilizzano ~{_fmt(capitale['valore'], '€')} "
                             "nei crediti")
            cause_ev.append(capitale["id"])
        cause_txt.append(f"uscite mensili superiori agli incassi "
                         f"({_fmt(abs(saldo['valore']), '€/mese')} di deficit)")
        cause_ev.append(saldo["id"])
        cause_txt.append("assenza di un forecast: il fabbisogno si scopre quando è già cassa")

        conseg_txt = ["pressione continua sulla cassa e ricorso permanente allo scoperto"]
        conseg_ev = []
        if costo:
            conseg_txt.append(f"interessi che costano ~{costo['valore']:.0f}%/anno "
                              "sull'esposizione")
            conseg_ev.append(costo["id"])
        if peso:
            conseg_txt.append(f"~{peso['valore']:.1f}% del fatturato assorbito dagli oneri "
                              "finanziari → meno margine, meno capacità di investimento")
            conseg_ev.append(peso["id"])
        conseg_txt.append("dipendenza crescente dalla banca: ogni rinnovo del fido "
                          "diventa una trattativa al ribasso")

        chains.append(chain(
            "finance.spirale_scoperto", "La spirale dello scoperto",
            [node("osservazione",
                  f"La gestione corrente perde {_fmt(abs(saldo['valore']), '€/mese')} e "
                  "l'azienda vive stabilmente dentro il fido.",
                  [saldo["id"]]),
             node("cause", "; ".join(cause_txt), cause_ev),
             node("conseguenze", "; ".join(conseg_txt), conseg_ev),
             node("priorita",
                  "Massima: il costo del problema cresce ogni mese e riduce le opzioni "
                  "disponibili (chi ha cassa negozia, chi non ne ha subisce)."),
             node("intervento",
                  "Agire sulle CAUSE nell'ordine: accorciare il ciclo di incasso "
                  "(fatturazione immediata, solleciti strutturati, acconti), costruire il "
                  "forecast a 13 settimane per anticipare i buchi, e solo dopo negoziare "
                  "la forma di finanziamento giusta al costo giusto."),
             node("risultato_atteso",
                  "Riduzione strutturale del fabbisogno finanziato, oneri in calo e ritorno "
                  "del margine alla sua funzione: remunerare l'azienda, non la banca.")],
            priorita="alta"))

    # ── Catena 2: concentrazione clienti → fragilità di cassa ────────────────
    if conc and (saldo or capitale):
        ev = [conc["id"]] + ([saldo["id"]] if saldo else [])
        chains.append(chain(
            "finance.concentrazione", "Concentrazione clienti e fragilità di cassa",
            [node("osservazione",
                  f"Il {conc['valore']:.0f}% del fatturato dipende da pochissimi clienti.",
                  [conc["id"]]),
             node("cause",
                  "Portafoglio commerciale sbilanciato; potere negoziale dei grandi "
                  "clienti sui termini di pagamento."),
             node("conseguenze",
                  "Basta il ritardo di UN pagamento per spostare la cassa dell'intero "
                  "mese; i termini li detta il cliente, non l'azienda"
                  + (" — su una cassa già in deficit strutturale" if saldo and
                     saldo["valore"] < 0 else "") + ".",
                  ev),
             node("priorita",
                  "Alta: è un moltiplicatore del rischio di liquidità, non un rischio "
                  "a sé."),
             node("intervento",
                  "Nel breve: presidio dedicato dei crediti verso i top client (date "
                  "certe, sollecito al giorno 1). Nel medio: diversificazione commerciale "
                  "mirata e clausole di pagamento negoziate sui nuovi contratti."),
             node("risultato_atteso",
                  "Cassa meno esposta al comportamento di un singolo cliente; potere "
                  "negoziale riequilibrato.")],
            priorita="alta"))

    return chains


def validate_chain(c: dict) -> list[str]:
    """Controlli di struttura: ≥4 fasi, ordine rispettato, evidenze sull'osservazione."""
    problems = []
    fasi = [n.get("fase") for n in c.get("catena", [])]
    if len(fasi) < 4:
        problems.append("catena troppo corta (<4 fasi)")
    order = [f for f in FASI if f in fasi]
    if fasi != order:
        problems.append("fasi fuori ordine")
    oss = next((n for n in c.get("catena", []) if n.get("fase") == "osservazione"), None)
    if oss is not None and not oss.get("evidenze"):
        problems.append("osservazione senza evidenze")
    return problems


def build_ops_chains(insights: list[dict], inputs: dict) -> list[dict]:
    """Catene causali operations/commesse."""
    ins = _by_id(insights)
    chains: list[dict] = []
    rit = ins.get("ops.pct_ritardo")
    util = ins.get("ops.utilizzo")
    churn = ins.get("ops.churn")

    if rit:
        ev = [rit["id"]] + ([util["id"]] if util else [])
        conseq = ("capacità assorbita da urgenze e rilavorazioni"
                  + (f" (solo il {util['valore']:.0f}% delle ore fattura)" if util else "")
                  + "; incassi rimandati insieme alle consegne; clienti che percepiscono "
                    "il ritardo prima che l'azienda lo misuri")
        chains.append(chain(
            "ops.spirale_ritardi", "La spirale dei ritardi",
            [node("osservazione",
                  f"Il {rit['valore']:.0f}% delle commesse è in ritardo.", [rit["id"]]),
             node("cause",
                  "Stati e priorità non standard; nessun owner unico per commessa; "
                  "il carico si vede solo quando esplode (manca una dashboard delle "
                  "eccezioni)."),
             node("conseguenze", conseq, ev),
             node("priorita",
                  "Alta: il ritardo è il punto dove operations e cassa si toccano — "
                  "ogni settimana di consegna slittata è una settimana di incasso slittato."),
             node("intervento",
                  "Stati standard con owner unico e data prossima azione; riunione "
                  "settimanale SOLO sulle eccezioni; registro blocchi con motivazione."),
             node("risultato_atteso",
                  "Ritardi visibili prima che diventino urgenze; capacità liberata "
                  "dalle rilavorazioni; incassi più regolari.")],
            priorita="alta"))

    if churn and churn.get("gravita"):
        chains.append(chain(
            "ops.churn", "Perdita clienti e costo della sostituzione",
            [node("osservazione",
                  f"Ogni periodo si perde il {churn['valore']:.1f}% del parco clienti.",
                  [churn["id"]]),
             node("cause",
                  "Il servizio percepito peggiora con i ritardi; nessun presidio "
                  "sistematico della relazione dopo la consegna."),
             node("conseguenze",
                  "Lo sforzo commerciale serve a RIMPIAZZARE, non a crescere: il "
                  "fatturato corre sul posto."),
             node("priorita", "Media-alta: agisce in silenzio sul lungo periodo."),
             node("intervento",
                  "Analisi delle uscite (perché se ne vanno, dato per dato); presidio "
                  "post-consegna sui clienti principali."),
             node("risultato_atteso",
                  "Il nuovo fatturato si somma invece di sostituire.")],
            priorita="media"))
    return chains


def build_marketing_chains(insights: list[dict], inputs: dict) -> list[dict]:
    ins = _by_id(insights)
    chains: list[dict] = []
    dep = ins.get("mkt.dipendenza_canale")
    if dep:
        chains.append(chain(
            "mkt.dipendenza", "La dipendenza dal canale dominante",
            [node("osservazione",
                  f"Il {dep['valore']:.0f}% della domanda arriva da un solo canale.",
                  [dep["id"]]),
             node("cause",
                  "Il canale dominante è comodo: porta volumi senza sforzo commerciale "
                  "diretto — ed è esattamente così che diventa indispensabile."),
             node("conseguenze",
                  "Commissioni e visibilità le decide il canale; il margine è ostaggio "
                  "di regole altrui; i clienti sono SUOI, non tuoi (niente dati, niente "
                  "relazione diretta)."),
             node("priorita",
                  "Alta: ogni mese di attesa rende la dipendenza più profonda."),
             node("intervento",
                  "Costruire il canale diretto per gradi: base clienti proprietaria, "
                  "incentivi alla prenotazione/ordine diretto, misurare il mix ogni mese."),
             node("risultato_atteso",
                  "Mix riequilibrato nel tempo: il canale dominante torna a essere UNA "
                  "fonte, non LA fonte.")],
            priorita="alta"))
    return chains


def build_hr_chains(insights: list[dict], inputs: dict) -> list[dict]:
    ins = _by_id(insights)
    chains: list[dict] = []
    prod = ins.get("org.fatturato_addetto")
    carico = ins.get("org.carico_medio")
    if prod and carico:
        chains.append(chain(
            "org.saturazione", "Saturazione e produttività",
            [node("osservazione",
                  f"Produttività {prod['valore']:,.0f} €/addetto con carico medio "
                  f"{carico['valore']:,.0f} ore/addetto nel periodo.",
                  [prod["id"], carico["id"]]),
             node("cause",
                  "La crescita è passata dalle persone prima che dal metodo: i processi "
                  "assorbono ore che non fatturano."),
             node("conseguenze",
                  "Chi è saturo non segnala: accumula. Prima cala la qualità, poi la "
                  "disponibilità, poi arriva la lettera di dimissioni — nell'ordine."),
             node("priorita",
                  "Media-alta: il costo vero si vede con 6-12 mesi di ritardo."),
             node("intervento",
                  "Misurare il carico per persona (non per reparto); togliere lavoro non "
                  "fatturabile PRIMA di aggiungere organico; decidere assunzioni sui "
                  "numeri di produttività."),
             node("risultato_atteso",
                  "Capacità recuperata senza nuovi costi fissi; assunzioni fatte quando "
                  "servono davvero, motivate dai dati.")],
            priorita="media"))
    return chains


def build_legal_chains(insights: list[dict], inputs: dict) -> list[dict]:
    ins = _by_id(insights)
    chains: list[dict] = []
    contratti = ins.get("legal.ha_contratti_standard")
    estero = ins.get("legal.estero_no_contratti")
    if contratti or estero:
        base = estero or contratti
        oss = ("Si opera all'estero senza contratti standard."
               if estero else "Si lavora senza una base contrattuale standard.")
        chains.append(chain(
            "legal.contratti", "Dal contratto mancante al contenzioso",
            [node("osservazione", oss, [base["id"]]),
             node("cause",
                  "I contratti sembrano un costo finché tutto va bene: si rimandano "
                  "perché il lavoro 'urgente' vince sempre su quello importante."),
             node("conseguenze",
                  "Ogni incarico nasce su termini improvvisati: tempi, responsabilità e "
                  "pagamenti si discutono DOPO, quando il potere negoziale è già speso"
                  + ("; all'estero il foro lo sceglie la controparte" if estero else "") + "."),
             node("priorita",
                  "Alta: è il rischio a rapporto costo/prevenzione più sbilanciato che "
                  "esista — prevenire costa una frazione del primo contenzioso."),
             node("intervento",
                  "Set di condizioni standard (incarico, fornitura, riservatezza) con "
                  "clausole su pagamenti, proprietà e foro; revisione legale una tantum, "
                  "riuso su ogni rapporto."),
             node("risultato_atteso",
                  "Rapporti che nascono già regolati: il contenzioso si sposta da "
                  "probabile a raro, e comunque su un terreno scelto da te.")],
            priorita="alta"))
    return chains


def build_strategy_chains(insights: list[dict], inputs: dict) -> list[dict]:
    ins = _by_id(insights)
    chains: list[dict] = []
    delta = ins.get("strat.delta_margine_canali")
    conc = ins.get("risk.concentrazione")
    if delta:
        chains.append(chain(
            "strat.mix_canali", "Il mix di canali decide il margine",
            [node("osservazione",
                  f"Tra canale diretto e distributore ballano {delta['valore']:.0f} "
                  "punti di margine.", [delta["id"]]),
             node("cause",
                  "Il canale intermediato compra volumi con margine; quello diretto "
                  "chiede investimento prima di rendere."),
             node("conseguenze",
                  "A parità di fatturato, il mix sposta il risultato: crescere sul "
                  "canale sbagliato può DIMINUIRE l'utile."),
             node("priorita",
                  "Alta in fase di espansione: la scelta si paga per anni."),
             node("intervento",
                  "Fissare il mix obiettivo per mercato PRIMA di investire; misurare il "
                  "margine per canale, non solo i volumi."),
             node("risultato_atteso",
                  "Crescita che porta utile, non solo fatturato.")],
            priorita="alta"))
    if conc:
        chains.append(chain(
            "strat.base_fragile", "Espandersi su una base concentrata",
            [node("osservazione",
                  f"Il {conc['valore']:.0f}% del fatturato dipende da pochi clienti.",
                  [conc["id"]]),
             node("cause",
                  "La concentrazione nasce dal successo: i clienti migliori crescono "
                  "e assorbono capacità."),
             node("conseguenze",
                  "Il piano di espansione poggia su una base che un solo addio può "
                  "incrinare: il rischio del nuovo si somma alla fragilità del vecchio."),
             node("priorita", "Alta: condiziona il ritmo sostenibile dell'espansione."),
             node("intervento",
                  "Diversificare DENTRO il piano di crescita: target commerciali su "
                  "nuovi clienti nel mercato attuale in parallelo all'espansione."),
             node("risultato_atteso",
                  "Base più larga sotto un piano più ambizioso.")],
            priorita="alta"))
    return chains


def build_ma_chains(insights: list[dict], inputs: dict) -> list[dict]:
    """Catene causali della valutazione M&A."""
    ins = _by_id(insights)
    chains: list[dict] = []
    evm = ins.get("ma.ev_ebitda")
    lev = ins.get("ma.debt_ebitda")
    conc = ins.get("risk.concentrazione")
    pe = ins.get("ma.prezzo_utile")

    # Catena 1: prezzo, multipli e ritorno.
    if evm and pe:
        chains.append(chain(
            "ma.prezzo_ritorno", "Dal prezzo richiesto al ritorno reale",
            [node("osservazione",
                  f"Il target è valutato {evm['valore']:.1f}× l'EBITDA e "
                  f"{pe['valore']:.1f}× l'utile.", [evm["id"], pe["id"]]),
             node("cause",
                  "Il prezzo richiesto riflette l'ottica del venditore (il massimo che "
                  "spera), non il valore per te: incorpora avviamento e aspettative, "
                  "non ancora le tue sinergie."),
             node("conseguenze",
                  f"A parità di gestione il capitale rientra in ~{pe['valore']:.1f} anni: "
                  "è la soglia che le sinergie devono battere per giustificare il premio. "
                  "Se non le hai concrete, stai comprando il passato del venditore al suo "
                  "prezzo."),
             node("priorita",
                  "Massima: il prezzo è la leva su cui si vince o si perde il deal — "
                  "tutto il resto viene dopo."),
             node("intervento",
                  "Ancorare la trattativa ai TUOI multipli (EV/EBITDA sostenibile per il "
                  "settore), non al prezzo richiesto; legare parte del prezzo ai risultati "
                  "futuri (earn-out) per condividere il rischio col venditore."),
             node("risultato_atteso",
                  "Prezzo allineato al valore reale per l'acquirente e rischio del "
                  "'passato che non si ripete' spostato in parte sul venditore.")],
            priorita="alta"))

    # Catena 2: la concentrazione clienti è il rischio che si compra.
    if conc and evm:
        chains.append(chain(
            "ma.concentrazione_target", "La concentrazione che ti porti in casa",
            [node("osservazione",
                  f"Il {conc['valore']:.0f}% del fatturato del target dipende da pochi "
                  "clienti.", [conc["id"]]),
             node("cause",
                  "Le PMI crescono spesso appoggiandosi a pochi grandi clienti: è la "
                  "loro forza e, per chi compra, il loro rischio."),
             node("conseguenze",
                  f"Hai pagato {evm['valore']:.1f}× un EBITDA che poggia su quei clienti: "
                  "se uno esce dopo il closing — e un cambio di proprietà è spesso "
                  "l'occasione per rivedere i rapporti — il multiplo che hai pagato si "
                  "gonfia di colpo sull'EBITDA rimasto."),
             node("priorita",
                  "Alta: è il rischio che trasforma un multiplo ragionevole in un cattivo "
                  "affare da un giorno all'altro."),
             node("intervento",
                  "Due diligence commerciale sui top client (contratti, durata, "
                  "soddisfazione); earn-out legato alla loro permanenza; clausole di "
                  "aggiustamento prezzo se il churn supera una soglia."),
             node("risultato_atteso",
                  "Rischio-cliente verificato prima di firmare e in parte trasferito al "
                  "venditore tramite la struttura del deal.")],
            priorita="alta"))

    # Catena 3: leva post-acquisizione (se il deal è a debito).
    if lev:
        chains.append(chain(
            "ma.leva_post_deal", "La leva dopo il deal",
            [node("osservazione",
                  f"Il target ha già {lev['valore']:.1f}× EBITDA di debiti finanziari.",
                  [lev["id"]]),
             node("cause",
                  "Il debito del target si eredita; se poi l'acquisto è finanziato a "
                  "debito, le due leve si sommano."),
             node("conseguenze",
                  "Un'azienda comprata a debito su un target già indebitato nasce fragile: "
                  "il primo anno difficile intacca la capacità di ripagare, e la banca lo "
                  "sa prima di te."),
             node("priorita", "Alta se il finanziamento dell'acquisto è a debito."),
             node("intervento",
                  "Costruire il piano di servizio del debito COMBINATO (target + "
                  "acquisizione) su uno scenario prudente; verificare la sostenibilità "
                  "PRIMA di impegnarsi sul prezzo."),
             node("risultato_atteso",
                  "Struttura finanziaria del dopo-deal sostenibile anche nello scenario "
                  "critico, non solo in quello medio.")],
            priorita="alta"))

    return chains
