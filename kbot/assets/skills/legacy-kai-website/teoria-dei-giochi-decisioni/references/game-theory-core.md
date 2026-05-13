# Teoria dei giochi — concetti core

Usa questo file quando la decisione coinvolge **altri attori strategici** che reagiscono alle tue mosse.

## Forma normale (matrice dei payoff)

Rappresentazione standard di un gioco one-shot a N giocatori: per ogni combinazione di strategie, specifichi il payoff di ciascun giocatore.

**Esempio — dilemma del prigioniero aziendale** (due aziende A e B decidono se aggredire il mercato o cooperare implicitamente):

| A \\ B | Cooperare | Aggredire |
|---|---|---|
| **Cooperare** | (3, 3) | (0, 5) |
| **Aggredire** | (5, 0) | (1, 1) |

Lettura: (payoff_A, payoff_B). "Aggredire" è strategia dominante per entrambi → l'equilibrio è (Aggredire, Aggredire) con payoff (1, 1), peggiore del risultato cooperativo (3, 3). Questo è il **dilemma del prigioniero**: la razionalità individuale porta a un esito collettivamente subottimo.

## Dominanza

- **Strategia strettamente dominata**: qualunque cosa facciano gli altri, un'altra strategia dà un payoff strettamente più alto. **Eliminala** — un giocatore razionale non la userà mai.
- **Strategia (strettamente) dominante**: qualunque cosa facciano gli altri, questa strategia dà il payoff più alto. Se ce l'hai, **giocala** (a meno che non stai cercando di segnalare qualcosa di diverso).

### Eliminazione iterata delle strategie dominate

È una procedura operativa, non solo un concetto:

1. Identifica qualsiasi strategia strettamente dominata di uno qualsiasi dei giocatori. Cancellala dalla matrice.
2. Nel gioco ridotto, guarda di nuovo: potrebbero esserci nuove dominanze emerse. Cancella.
3. Itera finché non trovi più dominanze.
4. Se rimane **una sola combinazione di strategie**, è l'equilibrio del gioco (il gioco è "risolvibile per dominanza"). Se ne rimangono di più, ma meno delle iniziali, hai comunque semplificato l'analisi.

**Attenzione all'ordine**: l'eliminazione iterata di strategie **strettamente** dominate è indipendente dall'ordine (arrivi allo stesso risultato). L'eliminazione di strategie **debolmente** dominate (dove "≥" non è "strettamente >") può invece dipendere dall'ordine — usala con cautela.

**Assunzione implicita**: usare questo metodo richiede **common knowledge of rationality**: tu sei razionale, sai che l'altro è razionale, sai che l'altro sa che tu sei razionale, e così via. In pratica, dopo 2-3 livelli di ricorsione, gli umani reali sbagliano. Se l'avversario non è pienamente razionale, l'eliminazione iterata al 5° livello può non funzionare.

## Equilibrio di Nash

Una combinazione di strategie in cui **nessun giocatore ha incentivo a cambiare unilateralmente**. È il concetto di soluzione più importante della teoria dei giochi.

Come trovarlo in una matrice 2×2:
1. Per ogni colonna (mossa di B), segna con * la riga (mossa di A) con payoff di A più alto.
2. Per ogni riga (mossa di A), segna con * la colonna (mossa di B) con payoff di B più alto.
3. Le celle con due stelle sono equilibri di Nash.

**Attenzione**:
- Un gioco può avere **più equilibri di Nash** (problema di coordinazione). Usa focal points, Pareto-dominanza, risk-dominance per scegliere il più plausibile.
- Un gioco può non avere equilibri di Nash in strategie pure. In questo caso esiste sempre un equilibrio in strategie miste (randomizzazione) — ma nella pratica business raramente lo calcoliamo esplicitamente.
- **L'equilibrio di Nash non è necessariamente Pareto-ottimo**. Vedi dilemma del prigioniero.

## Giochi a somma zero vs somma positiva

- **Somma zero**: il guadagno di un giocatore è esattamente la perdita dell'altro. Tipicamente: divisione di una torta di dimensione fissa, gara per lo stesso cliente.
- **Somma positiva**: la collaborazione può creare valore totale maggiore. Tipicamente: partnership, standard di mercato, ecosistemi.
- **Somma negativa**: la competizione distrugge valore (guerra dei prezzi, escalation reputazionale).

**Errore frequente**: trattare come somma zero situazioni che sono somma positiva. "Se do loro condizioni migliori, io perdo". Spesso non è vero — un accordo migliore per entrambi crea torta più grande.

## Minimax / maximin (giochi a somma zero)

Nei giochi a somma zero puri (poker, gara d'appalto head-to-head su un singolo criterio), la strategia razionale è:
- **Maximin**: scegli la strategia che massimizza il payoff minimo garantito (indipendentemente da cosa fa l'avversario).
- In giochi a somma zero a due giocatori, il valore maximin di un giocatore = valore minimax dell'altro = **valore del gioco** (teorema di von Neumann).

## Giochi cooperativi e Shapley value

Quando i giocatori possono fare accordi vincolanti e dividere il surplus:
- **Core**: insieme delle allocazioni stabili (nessuna coalizione preferisce uscire).
- **Shapley value**: ripartizione "equa" basata sul contributo marginale medio di ciascun giocatore a tutte le possibili coalizioni. Utile per giudicare quote di joint venture, split di revenue in partnership, distribuzione di bonus di team.

## Giochi sequenziali e induzione all'indietro

Quando le mosse sono in ordine (prima A, poi B vede la mossa di A e risponde), rappresenta il gioco in **forma estensiva** (albero) e risolvi con **backward induction**.

### Procedura formale

1. **Disegna l'albero**: radice = prima decisione, ogni nodo interno = decisione di un giocatore, ogni foglia = esito con payoff `(A, B, ...)`.
2. **Parti dalle foglie** e risali al **penultimo livello** (l'ultimo nodo decisionale). In ogni nodo del giocatore che muove per ultimo, segna con una freccia il ramo che massimizza il suo payoff. Gli altri rami sono "potati".
3. **Ora quel giocatore ha una risposta fissa** a ogni possibile mossa che lo precede. Sali di un livello: il giocatore precedente deve scegliere sapendo cosa farà chi viene dopo. Di nuovo, segna con una freccia il suo ramo ottimo.
4. **Continua a risalire** fino alla radice. Il cammino di frecce dalla radice alle foglie è l'**equilibrio perfetto nei sottogiochi (SPNE)**.

**Esempio — Entry deterrence**. Un entrante decide se entrare nel mercato (E/N); se entra, l'incumbent decide se combattere (C) o accomodarsi (A). Payoff: (N) = (0, 10); (E, C) = (−3, −2); (E, A) = (5, 5).
- Al nodo dell'incumbent dopo l'entrata: A dà 5, C dà −2 → incumbent sceglie A.
- Sapendo questo, l'entrante: entrare dà 5, non entrare dà 0 → entra.
- SPNE: (Entra, Accomoda). La minaccia "se entri combatto" non è credibile perché, arrivati al momento, combattere è peggio per l'incumbent stesso.

### SPNE vs Nash semplice

La backward induction esclude gli equilibri di Nash basati su **minacce non credibili**. Nash semplice ammette (Non entra, Combatti se entra) come equilibrio (se l'entrante crede alla minaccia, non entra, quindi combattere non si verifica mai). Ma SPNE lo scarta perché, se l'entrante entrasse, combattere non sarebbe ottimo — quindi la minaccia non reggerebbe.

**Per rendere credibile una minaccia non credibile**, serve commitment (vedi `commitment.md`): trasformare il gioco in modo che la mossa "dura" diventi l'unica razionale una volta arrivati lì.

### Applicazioni tipiche

Negoziazioni multi-round, entry deterrence, annunci strategici, decisioni staged (investimento pilota → scale-up), politiche di prezzo reattive, ultimatum e controproposte.

## Minacce credibili e non credibili

In forma estensiva, Nash semplice permette minacce che non sarebbero razionali eseguire. La backward induction le elimina. **Una minaccia è credibile solo se, arrivati al momento di eseguirla, è nell'interesse di chi minaccia eseguirla.**

Esempio: "Se entri nel mio mercato, scatenerò una guerra dei prezzi che ci porterà entrambi in rosso". Non credibile se, all'atto pratico, la guerra dei prezzi peggiora anche la mia posizione → non la eseguirei → il competitor lo sa → entra lo stesso.

Per rendere credibile la minaccia, serve **commitment** (vedi `commitment.md`).

## Mechanism design: disegnare le regole invece di giocare il gioco

Quando ne hai il potere, **cambiare le regole del gioco** è quasi sempre meglio che giocare bene un gioco mal disegnato. Questo è il dominio del **mechanism design** (premi Nobel Hurwicz, Maskin, Myerson; Roth e Shapley per il market design applicato).

**Quando è disponibile**:
- Sei chi fissa le regole di un'asta, di una gara, di un sistema di incentivi interni.
- Gestisci un marketplace o una piattaforma e puoi scegliere come far incontrare domanda e offerta.
- Sei HR/manager e disegni il sistema di compensation, bonus, valutazione.
- Gestisci una community e scegli le regole di moderazione, ranking, reputazione.

**Principi operativi**:
1. **Incentive compatibility**: disegna le regole in modo che essere onesti sia la strategia dominante per chi partecipa (es. asta Vickrey a secondo prezzo: rivelare il proprio valore vero è ottimo).
2. **Individual rationality**: ogni partecipante deve trovare conveniente partecipare (non peggiorare rispetto all'alternativa).
3. **Budget balance**: le somme dei trasferimenti devono chiudere (niente buchi da coprire col proprio capitale).
4. **Efficienza**: l'allocazione finale massimizza il valore totale.

**Applicazioni tipiche in business**:
- **Aste**: vendita di asset, allocazione di slot pubblicitari, spettro radio, procurement. La scelta del meccanismo (inglese, olandese, first-price sealed, Vickrey) cambia enormemente i risultati.
- **Programmi di incentivi vendita**: come strutturare commissioni e quote per incentivare comportamenti reali (non solo "vendere di più" ma segmenti giusti, retention, upsell).
- **Matching markets**: allocazione di studenti alle scuole, medici ai reparti, dipendenti a progetti interni. Algoritmi di deferred acceptance di Gale-Shapley.
- **Referral e reputation systems**: come far emergere il merito senza creare gaming (es. eBay feedback, Stack Overflow reputation).
- **Governance di piattaforma**: chi decide cosa, con che voti, con che veti.

**Errore frequente**: giocare a lungo un gioco mal disegnato quando bastava cambiarne le regole. Se ti trovi a "trovare workaround" a un sistema di incentivi, spesso il vero problema è il sistema, non i comportamenti.

## Quando la teoria dei giochi è il martello giusto

- Ci sono **almeno 2 attori** che prendono decisioni strategiche.
- Le **mosse degli altri influenzano i tuoi payoff** in modo non trascurabile.
- Gli altri sono abbastanza razionali da anticipare le conseguenze (non sempre vero — vedi `behavioral.md`).
- Puoi almeno approssimare le preferenze degli altri.

Se invece sei da solo contro la natura, usa `decision-theory.md`.
