# Decision theory — strumenti operativi

Questo file si applica quando **c'è un solo decisore** (tu) contro la natura/mercato — cioè quando non ci sono altri attori strategici che reagiscono deliberatamente alle tue mosse. Se invece ci sono avversari razionali che rispondono alla tua scelta, usa `game-theory-core.md`.

## Valore atteso (Expected Value, EV)

Formula: `EV = Σ(probabilità_scenario × payoff_scenario)`

Usalo quando:
- Puoi stimare probabilità (anche soggettive) degli scenari
- Il decisore è risk-neutral o la scommessa è piccola rispetto al patrimonio
- Puoi ripetere la scelta molte volte (la legge dei grandi numeri aiuta)

**Attenzione**: l'EV più alto non è sempre la scelta giusta. Se il worst case ti fa fallire, la varianza conta. Affianca sempre EV con il worst case.

## Utilità attesa (Expected Utility)

Quando il payoff è denaro ma le somme sono grandi rispetto al patrimonio, usa una funzione di utilità concava (es. logaritmica) al posto del payoff lineare. Questo cattura l'avversione al rischio in modo razionale.

Approssimazione pragmatica: penalizza scenari estremi negativi in modo sproporzionato. Se il worst case è "fallimento dell'azienda", trattalo come payoff = −∞ qualunque sia la probabilità, a meno che non ci sia un matching gain altrettanto estremo.

## Criteri decisionali sotto incertezza (senza probabilità affidabili)

Quando non puoi assegnare probabilità ai scenari:

| Criterio | Logica | Quando usarlo |
|---|---|---|
| **Maximax** | Scegli l'opzione con il best case più alto | Decisore aggressivo, rischio limitato, asimmetria al rialzo |
| **Maximin (Wald)** | Scegli l'opzione con il worst case meno peggiore | Decisione one-shot con rischio esistenziale, paranoico ragionato |
| **Minimax regret (Savage)** | Minimizza il "rimpianto massimo" (differenza tra la tua scelta e la scelta ottima ex-post in quello scenario) | Decisioni visibili dove il giudizio altrui conta |
| **Laplace** | Assumi equiprobabilità e calcola EV | Ignoranza totale sulle probabilità, decisioni ripetibili |
| **Hurwicz α** | Mix ponderato di best e worst case: α·best + (1−α)·worst | Quando vuoi esplicitare il grado di ottimismo |

Nella pratica: scegli 2-3 criteri e vedi se concordano. Se concordano, procedi. Se divergono, il disaccordo ti dice qualcosa sul tipo di incertezza che stai affrontando.

## Alberi decisionali

Strumento visivo per decisioni sequenziali con più stadi di scelta e incertezza. Convenzioni:
- Nodi quadrati = decisioni (controlli tu)
- Nodi tondi = eventi casuali (non controlli tu)
- Foglie = payoff finali

**Backward induction**: parti dalle foglie, calcola l'EV di ogni nodo casuale, scegli il ramo con EV più alto in ogni nodo decisionale, risali all'indietro fino alla radice.

Utile per: decisioni di investimento per stadi (MVP → scale), espansioni, negoziazioni multi-round.

## Analisi di sensitività

Dopo aver fatto i conti, **varia gli input** e vedi se la raccomandazione cambia:
- Se una variazione del 10% nella probabilità o nel payoff ribalta la scelta, la raccomandazione è **fragile** → raccogli più informazione prima di decidere.
- Se la raccomandazione regge anche a variazioni del 30-40%, è **robusta** → decidi e vai avanti.

## Value of Information (VoI)

Quanto vale comprare più informazione prima di decidere?

`VoI = EV(decisione con informazione perfetta) − EV(migliore decisione attuale)`

Se VoI > costo di raccogliere l'informazione, **raccogli l'informazione prima di decidere**. È un concetto potentissimo e spesso trascurato: spiega perché fare un test, un sondaggio, un prototipo, un pilot può essere razionale anche se "ritarda" la decisione.

## Cosa NON fare

- **Sunk cost fallacy**: i costi già sostenuti non devono influenzare la decisione forward-looking. L'unica cosa che conta è il payoff atteso delle opzioni disponibili da qui in poi.
- **Confondere probabilità con frequenza**: in decisioni uniche, la probabilità è soggettiva. Sii esplicito su "cosa significa 70%" nella tua testa.
- **Eccesso di quantificazione**: se devi inventare 8 numeri per fare una tabella EV, probabilmente il modello sta aggiungendo rumore invece di segnale. Scendi a livello qualitativo ma esplicito.
