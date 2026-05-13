# Behavioral game theory — lista operativa dei bias

Gli attori reali non sono perfettamente razionali. Ignorare questo fatto porta a strategie eleganti sulla carta ma che falliscono nella realtà. Questa lista è operativa: per ogni bias, l'implicazione strategica.

## Bias del decisore (te stesso)

Prima di consigliare una mossa, controlla se tu o chi decide state cadendo in uno di questi.

### Loss aversion (Kahneman-Tversky)

Le perdite pesano circa 2x più dei guadagni equivalenti. Implicazioni:
- Chi è già "in profitto" tende a vendere troppo presto per bloccare il guadagno.
- Chi è "in perdita" tende a tenere troppo a lungo (rifiuta di "realizzare" la perdita). Sunk cost fallacy rafforzata.
- **Antidoto**: nel framing della decisione, presenta sempre l'opzione come scelta tra flussi futuri, non come "tagliare la perdita".

### Anchoring

La prima cifra/opzione menzionata diventa il punto di riferimento per le successive, anche se arbitraria. Implicazioni:
- Nelle negoziazioni, chi apre condiziona il range finale.
- Nelle stime, la prima ipotesi "ancora" le successive.
- **Antidoto**: quando possibile, apri tu (con un ancoraggio credibile). Quando sei ancorato, rifocalizza esplicitamente su un benchmark esterno.

### Sunk cost fallacy

I costi già sostenuti non sono recuperabili, quindi non dovrebbero influenzare le decisioni future. Ma lo fanno. Implicazioni:
- Progetti falliti vengono protratti "perché abbiamo già investito tanto".
- Prodotti sottoperformanti non vengono killati per paura di ammettere l'errore.
- **Antidoto**: chiedi "se partissi oggi senza aver speso nulla, lo farei?" Se no, ferma subito.

### Overconfidence

La probabilità soggettiva di successo è sistematicamente più alta di quella oggettiva. Implicazioni:
- Piani troppo ottimistici su tempi, budget, adozione.
- Sottovalutazione della risposta dei competitor.
- **Antidoto**: pre-mortem. Chiedi al team "immaginate che tra 1 anno il progetto sia fallito. Perché è successo?". Fa emergere rischi che l'analisi forward-looking nasconde.

### Status quo bias

Preferenza irrazionale per lo stato attuale. Implicazioni:
- "Non cambiare fornitore" anche quando il nuovo è migliore.
- Procrastinazione di decisioni di pivot.
- **Antidoto**: imponi esplicitamente l'opzione "cambiare" come default nel framing della discussione. "Se dovessimo cambiare, come lo faremmo?" prima di "dobbiamo cambiare?".

### Confirmation bias

Cerchi attivamente informazione che conferma la tua ipotesi, ignori quella contraria. Implicazioni:
- Analisi di mercato che trovano sempre "opportunità" là dove vuoi andare.
- Test che confermano sempre le ipotesi di prodotto.
- **Antidoto**: assegna esplicitamente il ruolo di "devil's advocate" a qualcuno nel team. Formalizza la contro-ipotesi.

### Framing effect

La stessa scelta presentata diversamente produce decisioni diverse. Esempio classico: "programma A salva 200 persone su 600" vs "programma B fa morire 400 persone su 600". Stessa matematica, scelte opposte.
- **Antidoto**: riformula sempre in almeno 2 modi diversi (positivo e negativo) e vedi se la preferenza regge.

## Bias degli avversari / controparti

Quando gli attori contro cui giochi non sono perfettamente razionali, la strategia teoricamente ottima potrebbe non funzionare. A volte devi giocare "subottimo ma leggibile".

### Razionalità limitata

Gli altri non vedono tutte le mosse possibili, non fanno backward induction fino in fondo, non conoscono tutti i payoff. Implicazioni:
- Strategie troppo elaborate passano inosservate.
- Segnali sottili non vengono captati — serve essere espliciti.
- **Antidoto**: preferisci strategie semplici e leggibili (tit-for-tat è un esempio di strategia che vince grazie alla sua leggibilità).

### Reciprocità

Le persone reali reagiscono all'equità percepita, non solo al payoff economico. Offerte "troppo basse" vengono rifiutate anche quando accettarle sarebbe razionale (ultimatum game). Implicazioni:
- In negoziazione, mai proposte al limite estremo: è più probabile che la controparte le rifiuti per principio.
- Piccoli gesti di equità costruiscono cooperazione disproporzionata.
- **Antidoto**: lascia sempre "qualcosa" alla controparte, anche quando hai il potere di prendere tutto.

### Desiderio di vendetta / punizione altruistica

Le persone puniscono le ingiustizie anche quando la punizione costa loro (terzo nel gioco dell'ultimatum). Implicazioni:
- Umiliare un avversario in una negoziazione può costargli caro nel round successivo.
- Clienti trattati male diventano attori attivi di danno reputazionale, anche oltre il loro interesse economico.
- **Antidoto**: nelle vittorie, lascia sempre una "via d'uscita dignitosa" all'altro.

### Fiducia e tradimento

La fiducia si costruisce lentamente, si distrugge in un istante. Implicazioni:
- Un singolo tradimento (anche piccolo) in un rapporto di lungo periodo ha un costo molto maggiore del beneficio ottenuto.
- **Antidoto**: non barare sui dettagli. La reputazione di affidabilità è un asset enorme e fragile.

### Effetto IKEA / endowment

Le persone sovrastimano ciò che hanno creato o possiedono. Implicazioni:
- Chi ha lavorato a un'idea la difende al di là della sua effettiva qualità.
- Chi detiene uno status quo lo valuta più di quanto un estraneo pagherebbe per averlo.
- **Antidoto**: chiedi "se questa idea fosse di qualcun altro, la compreresti a questo prezzo?".

## Come integrare la behavioral layer nella raccomandazione

1. **Identifica il bias dominante** nel decisore e nelle controparti per il caso specifico.
2. **Aggiungi un margine di sicurezza**: se sospetti overconfidence, scala i benefici attesi del 20-30%.
3. **Scegli il framing della raccomandazione**: se parli a un decisore con status quo bias, presenta il cambiamento come la scelta "prudente". Se parli a un decisore con loss aversion, non enfatizzare le perdite potenziali dell'inazione.
4. **Prevedi reazioni emotive**, non solo razionali, degli altri attori. Chiediti: "come si sentiranno ricevendo questa mossa?".

## La mossa giusta spesso non è quella matematicamente ottima

Un principio di sintesi: la mossa migliore è quella che **funziona nel mondo reale**, non quella che funzionerebbe in un mondo di agenti perfettamente razionali. Se una strategia elegante richiede che l'avversario faccia 3 passaggi di backward induction, probabilmente non funzionerà. Se richiede che il tuo CEO superi il suo loss aversion, probabilmente verrà modificata al momento dell'esecuzione. Tienine conto nel consigliare.
