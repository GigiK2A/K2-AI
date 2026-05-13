# Giochi di coordinazione (equilibri multipli)

Usa questo file quando il problema **non è conflitto** (quale torta vincere) ma **coordinazione** (come allineare le mosse con altri per arrivare a un risultato comune). Il segnale tipico: **ci sono più equilibri di Nash tutti ragionevoli**, e il problema non è trovarne uno ma scegliere quale.

## "Il somaro di Nash": troppi equilibri

Un gioco può avere molti equilibri di Nash tutti stabili. Senza un criterio di selezione, la razionalità individuale non basta — due giocatori razionali possono finire su equilibri diversi e fallire la coordinazione. Nash stesso segnalò questo come limite importante: la teoria non predice **quale** equilibrio sarà giocato, solo quali sono possibili.

**Esempi classici**:

- **Battle of the Sexes**: due partner devono scegliere se andare all'opera o allo stadio. Entrambi preferiscono stare insieme a stare soli, ma lei preferisce l'opera e lui lo stadio. Due equilibri: (Opera, Opera) e (Stadio, Stadio). Quale si realizza?
- **Lato della strada**: guidare a destra o a sinistra. Entrambe le convenzioni sono equilibri stabili. In Italia destra, in UK sinistra. Niente nella razionalità "pura" prescrive l'una o l'altra.
- **Standard tecnologici**: VHS vs Betamax, QWERTY vs Dvorak, TCP/IP vs OSI. Il mercato deve convergere su uno, ma la scelta non è dettata solo da qualità.
- **Convenzioni linguistiche**: parole, unità di misura, formati di file.

## Focal points (Schelling)

Thomas Schelling introdusse il concetto di **focal point**: un equilibrio che, pur non essendo "meglio" in senso logico, è più saliente perché ha qualcosa di psicologicamente, culturalmente o storicamente prominente.

**Esperimento classico**: "Sei a New York ma non hai telefonato al tuo amico, non sai dove sei attesi. Dove vai e a che ora?" Risposta modale: Grand Central Station, mezzogiorno. Non c'è niente di razionalmente ottimo in quella scelta — è saliente.

**Leve per creare focal points in business**:

1. **Salienza storica**: "abbiamo sempre fatto così", "l'industria usa questo standard". Il default vince.
2. **Autorità**: un attore autorevole (regolatore, leader di mercato, analista Gartner) indica una direzione → diventa focal.
3. **Semplicità**: tra due equilibri complessi e uno semplice, il semplice vince. 50/50 è più focal di 47/53.
4. **Simmetria**: soluzioni equilibrate sono più facili da accettare anche quando non sono quelle individualmente preferite.
5. **Annunci pubblici**: dire per primi "andiamo all'opera" crea coordination senza bisogno di contrattare — se l'altro non ha forte preferenza, si adegua.
6. **Prominenza fisica/visiva**: il prodotto più visibile sullo scaffale, il partner più noto nel settore.

## Pareto-dominanza vs risk-dominance

Quando ci sono più equilibri, due criteri per prevederne la selezione:

- **Pareto-dominanza**: un equilibrio è Pareto-dominante se tutti i giocatori stanno meglio lì che in qualsiasi altro equilibrio. Intuitivamente sembra ovvio scegliere questo.
- **Risk-dominance** (Harsanyi-Selten): un equilibrio è risk-dominant se è la best response quando assumi che l'altro giocatore randomizza 50/50. In pratica: è l'equilibrio più "sicuro" se non sai cosa fa l'altro.

**Paradosso**: nei giochi sperimentali, i giocatori spesso scelgono l'equilibrio risk-dominant anche quando un altro è Pareto-dominante, perché temono il fallimento di coordinazione. Esempio classico: stag hunt (cacciare il cervo richiede collaborazione e dà payoff alto; cacciare la lepre si fa da soli con payoff basso ma sicuro). Molti scelgono la lepre.

**Implicazione business**: anche se la partnership/standard/joint venture "migliore" è chiara a tutti, la coordinazione può fallire per paura del tradimento. Serve un investimento esplicito nella costruzione di fiducia e commitment visibile (vedi `commitment.md`).

## Norme sociali come equilibri di Nash

Molte convenzioni sociali (puntualità, dress code, cortesia negli email, galateo di settore, ora di inizio riunioni) sono equilibri di Nash sostenuti da conoscenza comune: tutti sanno che tutti gli altri si attendono una certa mossa, quindi seguirla è la best response. Deviare unilateralmente costa, anche se la norma non è "razionalmente" ottima.

**Implicazione pratica**: cambiare una norma di settore richiede più di una dimostrazione logica — richiede un'azione coordinata o un attore focal abbastanza grande da spostare l'equilibrio.

## Applicazioni tipiche nel business

**1. Standard di settore.** Quando stai lanciando una tecnologia o un formato, non puoi vincere da solo — serve coordinare una coalizione di early adopters che crei un focal point. Mossa chiave: annunci pubblici coordinati, endorsement di attori autorevoli.

**2. Ecosistemi di partner.** API, SDK, integrazioni: la scelta di aderire al tuo ecosistema dipende da quanti altri aderiscono. Tipico gioco di coordinazione con rischio di equilibrio inferiore (nessuno aderisce). Sblocco: partner di ancoraggio (lighthouse customer), commitment visibili, roadmap pubblica.

**3. Piattaforme a due lati.** Chicken-and-egg: i venditori vengono se ci sono i compratori e viceversa. Serve un subsidio iniziale a uno dei due lati per creare il focal point.

**4. Negoziazioni con soluzioni multiple accettabili.** Spesso la questione non è "quanto" (conflitto) ma "quale delle 5 configurazioni equivalenti" (coordinazione). Il primo a proporre una configurazione semplice e simmetrica spesso vince.

**5. Team e organizzazioni.** Chi fa cosa, orari comuni, linguaggio condiviso: tutto sono equilibri di coordinazione. Cambiarli richiede un atto di leadership che crei un nuovo focal point, non solo una discussione logica.

**6. Adozione di software interno.** Nuovo tool collaborativo: funziona solo se tutti lo usano. Fallisce se la maggioranza non migra. Mossa vincente: mandato dall'alto + deadline credibile + rimozione dell'alternativa (chiudere lo strumento vecchio).

## Come agire quando identifichi un gioco di coordinazione

1. **Riconosci che è coordinazione, non conflitto**: non devi "vincere", devi allineare.
2. **Elenca gli equilibri possibili**: tipicamente 2-4.
3. **Identifica il focal point naturale**: storia, salienza, default.
4. **Se nessun focal point naturale vince il tuo preferito, costruiscine uno**: annuncio pubblico, endorsement, coalizione di ancoraggio, incentivi asimmetrici.
5. **Rendi il commitment visibile**: gli altri devono sapere che ti sei impegnato a un equilibrio, altrimenti il gioco di coordinazione resta aperto.
6. **Accetta che il risultato "giusto" può non vincere**: QWERTY esiste ancora.

## Errore frequente

**Trattare un gioco di coordinazione come conflitto**. "Devo convincerli a fare come dico io" quando in realtà entrambi preferiscono allinearsi su una convenzione qualunque. Il framing competitivo distrugge la coordinazione. Il framing corretto è: "come costruiamo un punto di incontro ovvio?"

L'inverso è altrettanto pericoloso: trattare un conflitto come coordinazione ("siamo tutti d'accordo che serve cooperare") quando in realtà gli obiettivi sono incompatibili. Vedi `game-theory-core.md` per distinguere i due casi.
