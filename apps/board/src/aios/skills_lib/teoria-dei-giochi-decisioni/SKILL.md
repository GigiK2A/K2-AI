---
name: teoria-dei-giochi-decisioni
description: Framework di decision theory e teoria dei giochi per scegliere la mossa migliore di fronte a più alternative. Usa SEMPRE quando l'utente deve scegliere tra opzioni, valutare trade-off, rispondere a un competitor, decidere pricing o posizionamento, selezionare tecnologia/libreria/fornitore, negoziare, allocare risorse scarse. Attiva anche senza menzione esplicita di "teoria dei giochi" quando c'è un dilemma decisionale — tecnico ("meglio React o Vue?"), strategico ("entriamo in questo mercato?"), marketing ("come rispondere al competitor?"), commerciale ("quanto offrire alla gara?"), organizzativo ("internalizzare o esternalizzare?"). Copre decision theory (valore atteso, alberi decisionali, analisi multicriterio), teoria dei giochi (Nash, strategie dominanti, minimax, segnalazione, giochi ripetuti) e behavioral game theory (bias, razionalità limitata, reputazione). Produce analisi strutturata con raccomandazione operativa motivata.
---

# Teoria dei giochi e decision theory per decisioni migliori

## Scopo della skill

Aiutare l'utente a prendere **la decisione migliore possibile** quando si trova di fronte a più alternative, applicando in modo pragmatico gli strumenti di decision theory e teoria dei giochi. L'output non è un saggio accademico: è un'analisi strutturata che porta a una raccomandazione operativa motivata, utilizzabile subito.

## Quando attivare questa skill

Attivala ogni volta che la conversazione include un **trade-off** — anche se l'utente non usa la parola "decidere". Segnali tipici:

- **Scelta esplicita tra N alternative**: "meglio A o B?", "quale conviene?", "cosa scelgo tra X, Y, Z?"
- **Reazione a una mossa di un terzo**: competitor che abbassa i prezzi, cliente che minaccia di andarsene, regolatore che introduce una nuova norma, fornitore che cambia condizioni.
- **Contesto competitivo**: entrare in un nuovo mercato, lanciare un prodotto, rispondere a una gara, fissare un prezzo.
- **Trade-off tecnico**: scelta tra librerie/framework/architetture/cloud provider, buy vs build, refactoring vs nuovo sviluppo.
- **Negoziazione**: tu fai una proposta, la controparte risponde, tu devi decidere la prossima mossa.
- **Allocazione di risorse scarse**: dove investire tempo/budget/persone.
- **Impegni vincolanti**: firmare un contratto di lungo periodo, dichiarare pubblicamente una posizione, assumere/licenziare.

Se il problema si può inquadrare con una domanda del tipo "cosa faccio adesso?" in presenza di alternative distinte con conseguenze diverse, **questa skill è rilevante**. Meglio attivarla in più che in meno.

## Il framework in 6 passi

Applica questi passi in ordine, adattando la profondità alla complessità del problema. Per decisioni semplici (pochi giocatori, info chiara) puoi comprimere i passi; per decisioni strategiche importanti espandili.

### 1. Inquadra il problema

Prima di calcolare qualsiasi payoff, chiediti:

- **Azione parametrica o strategica?** Se gli altri attori **non reagiscono** alle tue mosse (il mercato è troppo grande, la variabile è esogena, stai scegliendo tra beni inerti) → è un'azione parametrica → usa **decision theory pura**. Se ci sono attori che **osservano, anticipano e reagiscono** alle tue mosse → è un'azione strategica → usa **teoria dei giochi**. Errore frequente: trattare un competitor come "mercato inerte" (e subirne le reazioni) o viceversa trattare una variabile impersonale come un "avversario" (e paranoizzarsi).
- **Qual è la vera domanda?** Spesso l'utente pone la domanda sbagliata. "Meglio React o Vue?" può in realtà essere "come formo il team più velocemente?" oppure "come riduco il time-to-market?". Riformula la domanda in termini di **obiettivo** prima di elencare le opzioni.
- **Orizzonte temporale**: decisione one-shot o ripetuta? Reversibile o irreversibile? Questo cambia completamente la strategia ottima (vedi `references/repeated-games.md`).

### 2. Identifica giocatori, opzioni, informazione

- **Giocatori**: tu, competitor diretti, clienti, fornitori, regolatore, partner. Per ciascuno annota brevemente **quali sono i loro obiettivi** (non solo i tuoi).
- **Opzioni (strategie)**: elenca tutte le alternative realistiche, comprese quelle "scomode" (non fare niente, uscire dal mercato, aspettare). Se ne hai meno di 3, probabilmente ne stai dimenticando qualcuna.
- **Informazione**: cosa sai tu, cosa sanno gli altri, cosa è pubblico, cosa è privato. Distingui tra informazione simmetrica e asimmetrica — cambia profondamente la dinamica (vedi `references/signaling.md`). Distingui anche **informazione completa** (conosci le regole e le funzioni di utilità di tutti) vs **incompleta** (non le conosci), e **informazione perfetta** (sai la storia delle mosse precedenti) vs **imperfetta**. Sono assi diversi e l'incompletezza è la norma in business.
- **Classifica il tipo di gioco** — cambia radicalmente la strategia giusta:
  - **Conflitto puro (zero-sum)**: il mio guadagno = la tua perdita. Gara d'appalto head-to-head, acquisizione di un unico asset. Strumenti: minimax, strategie miste.
  - **Coordinazione pura**: entrambi vogliamo la stessa cosa, basta allinearsi. Standard tecnologici, convenzioni, incontri. Strumenti: focal points, segnali, vedi `references/coordination-games.md`.
  - **Interessi misti (il caso più comune)**: parziale conflitto + parziale cooperazione. Negoziazione prezzo-qualità, partnership, relazioni B2B. Strumenti: tutti quelli della skill.
  - **Somma positiva vs negativa**: la collaborazione può creare valore (partnership, ecosistemi) o distruggerlo (guerre dei prezzi, escalation). Molte situazioni che sembrano zero-sum in realtà non lo sono.

### 3. Costruisci i payoff

Per ogni combinazione (mia-opzione, reazione-altrui) stima le conseguenze sulle dimensioni che contano per l'utente. I payoff **non sono solo soldi**: possono essere quote di mercato, reputazione, tempo risparmiato, rischio, allineamento strategico, debito tecnico.

- Usa **analisi multicriterio** (AHP lite) quando le dimensioni sono eterogenee: elenca i criteri, assegna un peso a ciascuno (somma = 100%), dai un punteggio 1-5 a ogni opzione su ogni criterio, calcola il punteggio pesato. Vedi `references/multicriteria.md`.
- Quando c'è incertezza, stima **valore atteso** = Σ(probabilità × payoff). Ma non fermarti lì: guarda anche **varianza** e **scenario peggiore** (principio minimax).
- Stima sempre almeno 3 scenari: **base case, best case, worst case**. Se il worst case è inaccettabile, quell'opzione probabilmente non va bene neanche se ha il valore atteso più alto (loss aversion razionale).

### 4. Analizza strategicamente

Questo è il cuore della teoria dei giochi. Applica questi strumenti in ordine:

1. **Strategie dominate**: c'è un'opzione che è sempre peggio di un'altra, qualunque cosa facciano gli altri? Eliminala. Poi guarda il gioco ridotto e itera — **eliminazione iterata delle strategie dominate** può risolvere il gioco anche senza trovare un equilibrio di Nash esplicito.
2. **Strategia dominante**: c'è un'opzione che è sempre meglio delle altre, qualunque cosa facciano gli altri? Probabilmente quella è la scelta (a meno di considerazioni di reputazione/lungo periodo).
3. **Equilibrio di Nash**: cerca combinazioni di strategie in cui nessun giocatore ha incentivo a cambiare unilateralmente. Se ce ne sono più di uno, è un **gioco di coordinazione** → scegli con focal point / Pareto-dominanza / risk-dominance (vedi `references/coordination-games.md`). Se invece **non ce ne sono in strategie pure**, il gioco richiede **strategie miste** (randomizzazione con probabilità calcolate per rendere l'avversario indifferente — vedi `references/mixed-strategies.md`). Tipico quando essere prevedibili ti penalizza (audit, timing, pricing reattivo).
4. **Giochi sequenziali → backward induction**: se le mosse sono in ordine, rappresenta il gioco come albero e risolvi dalla foglia alla radice. Identifica minacce e promesse credibili (quelle che l'attore eseguirebbe davvero arrivato al momento) e scarta quelle non credibili. Vedi `references/game-theory-core.md`.
5. **Commitment e credibilità**: puoi migliorare la tua posizione impegnandoti irreversibilmente? Un investimento sunk-cost visibile può essere un vantaggio strategico perché toglie a te stesso l'opzione di ritirarti. Vedi `references/commitment.md`.
6. **Segnalazione**: le tue azioni comunicano informazione al mercato. Un prezzo alto può segnalare qualità; un lancio aggressivo può segnalare volontà di combattere. Scegli l'opzione che manda il segnale giusto.
7. **Gioco ripetuto**: se interagirai di nuovo con gli stessi attori, la cooperazione emerge naturalmente (tit-for-tat, reputation). Non trattare una relazione lunga come un gioco one-shot.
8. **Disegnare le regole invece di giocarle** (mechanism design): quando hai il potere di fissare la struttura del gioco (asta, programma di incentivi, matching, sistema di ranking), questo è quasi sempre meglio che giocare un gioco esistente. Vedi la sezione dedicata in `references/game-theory-core.md`.

### 5. Incorpora la behavioral layer

Gli attori reali non sono perfettamente razionali. Prima di finalizzare la raccomandazione, chiediti:

- **Bias cognitivi dei decisori umani**: loss aversion (le persone temono le perdite ~2x più di quanto amino i guadagni equivalenti), anchoring, sunk cost fallacy, overconfidence, status quo bias. Vedi `references/behavioral.md` per la lista operativa.
- **Razionalità limitata**: gli avversari possono non vedere la mossa ottima. Può convenirti una strategia meno elegante ma più leggibile dall'avversario.
- **Reputazione ed emozioni**: in contesti umani, la vendetta, la fiducia, il senso di giustizia contano. Non umiliare un avversario che incontrerai di nuovo.
- **Framing**: come viene presentata l'opzione influenza la scelta. Se devi fare un'offerta, il framing conta quanto il contenuto.

### 6. Sintetizza la raccomandazione

Chiudi sempre con una **raccomandazione operativa**. Non lasciare l'utente a decidere da solo dopo una lista di pro e contro — quello è un'abdicazione. La raccomandazione deve includere:

- **Mossa consigliata** (una sola, chiara)
- **Perché è la migliore** (il ragionamento in 2-3 frasi)
- **Cosa monitorare** dopo la decisione (segnali che indicano se dobbiamo cambiare rotta)
- **Piano B** (cosa fare se si realizza lo scenario negativo)

## Template di output

Usa sempre questa struttura. Adatta la lunghezza di ogni sezione alla complessità del problema — per una scelta tecnica semplice alcune sezioni possono essere di 2 righe; per una mossa strategica di settore possono essere paragrafi.

```markdown
# Analisi decisionale: [nome sintetico del problema]

## 1. Inquadramento
- **Obiettivo reale**: [la vera domanda dietro la richiesta]
- **Tipo di problema**: [decisione individuale / gioco competitivo / misto]
- **Orizzonte**: [one-shot / ripetuto, reversibile / irreversibile]

## 2. Giocatori e opzioni
- **Attori in gioco**: [elenco con obiettivi di ciascuno]
- **Opzioni realistiche**: [almeno 3, compresi "non fare nulla" e alternative non ovvie]
- **Struttura informativa**: [cosa sai / cosa sanno / asimmetrie]

## 3. Matrice payoff / criteri
[Tabella: opzioni × criteri pesati oppure opzioni × scenari con valore atteso]
[Per ogni opzione: base / best / worst case]

## 4. Analisi strategica
- **Strategie dominate** (da scartare): [...]
- **Equilibrio di Nash** (se applicabile): [...]
- **Commitment / segnalazione**: [come le opzioni influenzano le reazioni altrui]
- **Lettura del gioco ripetuto** (se applicabile): [effetti sulla reputazione di lungo periodo]

## 5. Fattori comportamentali
- **Bias da evitare**: [quelli rilevanti per il caso]
- **Segnale trasmesso** da ciascuna opzione: [...]
- **Reazione psicologica attesa** degli altri attori: [...]

## 6. Raccomandazione
> **Mossa consigliata**: [una frase]
>
> **Motivazione**: [2-3 frasi]
>
> **KPI da monitorare**: [2-4 indicatori con soglia]
>
> **Piano B**: [cosa fare se X accade]
```

## Esempi di applicazione

### Esempio 1 — Decisione tecnica (un solo decisore)

**Domanda utente**: "Meglio usare PostgreSQL o MongoDB per il mio nuovo servizio?"

**Approccio**: È una decisione individuale (non c'è un competitor che reagisce alla tua scelta di DB), quindi usa **decision theory** con analisi multicriterio. I criteri rilevanti saranno tipicamente: idoneità al modello dati, maturità ecosistema, competenze del team, costo operativo, performance attese. Pesa i criteri, assegna punteggi, sintetizza. Non serve tirare in ballo Nash equilibrium.

### Esempio 2 — Mossa strategica (gioco competitivo)

**Domanda utente**: "Il nostro principale competitor ha appena lanciato lo stesso servizio al 30% in meno. Cosa facciamo?"

**Approccio**: Questo è un **gioco ripetuto a due giocatori**. Attenzione: abbassare i prezzi in risposta può innescare una guerra dei prezzi (tit-for-tat distruttivo). Valuta: (a) mantenere il prezzo e differenziarti su qualità/servizio (segnala che non giochi al prezzo), (b) abbassare selettivamente solo sui segmenti contendibili (discriminazione), (c) un commitment credibile (es. "price match") che disincentiva il competitor dal continuare. La scelta dipende da elasticità, posizionamento e solidità finanziaria relativa.

### Esempio 3 — Marketing / posizionamento

**Domanda utente**: "Lancio la campagna ad aprile o aspetto settembre quando c'è l'evento di settore?"

**Approccio**: Gioco di timing con asimmetria informativa. Aprile = mossa anticipatoria (first-mover advantage, rischio di essere ignorati dal rumore settembre). Settembre = mossa contestuale (più attenzione ma più competitor). Considera: posso segnalare ad aprile e rinforzare a settembre? Quanto costa il rischio di "sparire" rispetto a "essere uno dei tanti"?

## Riferimenti aggiuntivi

Per approfondire temi specifici quando il problema lo richiede, consulta:

- `references/decision-theory.md` — Alberi decisionali, valore atteso, utilità attesa, criterio minimax e maximax, sensitività.
- `references/game-theory-core.md` — Forma normale, Nash equilibrium, dominanza, eliminazione iterata, backward induction, giochi a somma zero, giochi cooperativi, Shapley value, mechanism design.
- `references/mixed-strategies.md` — Quando servono, come calcolarle (principio di indifferenza dell'avversario), traduzione business (audit, pricing, allocazione, timing).
- `references/coordination-games.md` — Equilibri multipli, focal points di Schelling, Pareto- vs risk-dominance, norme sociali, standard, ecosistemi a due lati.
- `references/repeated-games.md` — Tit-for-tat, folk theorem, reputation, trigger strategies.
- `references/signaling.md` — Costly signaling, screening, adverse selection, segnali credibili vs cheap talk.
- `references/commitment.md` — Impegni irreversibili, burning bridges, first-mover advantages.
- `references/evolutionary-games.md` — ESS, replicator dynamics, pensiero di popolazione per dinamiche di mercato di lungo periodo.
- `references/multicriteria.md` — AHP lite, pesi, scoring, trattamento di criteri incommensurabili.
- `references/behavioral.md` — Lista operativa di bias cognitivi con impatto tipico sulle decisioni.

Leggi il file di riferimento solo quando il problema lo richiede: per una decisione semplice basta questa SKILL.md.

## Errori da evitare

1. **Produrre un elenco di pro e contro senza sintesi**. L'utente può farlo da solo. Il valore di questa skill è sintetizzare → raccomandare.
2. **Ignorare l'opzione "non fare nulla"**. Quasi sempre va considerata esplicitamente; a volte è la scelta ottima.
3. **Trattare un gioco ripetuto come un gioco one-shot**. Con relazioni durature (partner, dipendenti, clienti ricorrenti) la mossa one-shot ottima è spesso subottima nel lungo periodo.
4. **Nash ≠ Pareto-ottimo**. Un equilibrio di Nash può essere peggio per tutti di un'altra combinazione (dilemma del prigioniero classico). Segnalalo quando capita.
5. **Falsa precisione nei payoff**. Meglio ranghi qualitativi motivati che numeri inventati con due decimali.
6. **Ignorare l'asimmetria informativa**. Se tu sai qualcosa che gli altri non sanno, è una leva enorme — usala.
7. **Non chiedere chiarimenti quando servono**. Se mancano informazioni critiche (obiettivo reale, vincoli, orizzonte), chiedile prima di buttare giù la matrice. Però non chiedere 10 cose — max 2-3 domande mirate.

## Una nota sullo stile

L'utente vuole una **raccomandazione operativa**, non una lezione universitaria. Usa la terminologia tecnica (Nash, dominanza, segnalazione) quando serve, ma spiegala brevemente la prima volta. Il tono è quello di un consulente sveglio che ha letto Schelling e Kahneman ma parla la lingua del business. Concretezza > eleganza formale.
