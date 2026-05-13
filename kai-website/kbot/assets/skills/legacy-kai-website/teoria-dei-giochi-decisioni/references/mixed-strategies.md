# Strategie miste

Usa questo file quando un gioco **non ha equilibrio di Nash in strategie pure**, o quando la prevedibilità ti penalizza. In business succede più spesso di quanto sembri.

## Quando servono davvero

Una strategia pura significa "faccio sempre la stessa mossa". Una strategia mista significa "randomizzo tra più mosse con probabilità specifiche". Serve quando:

- **Nessuna combinazione di strategie pure è stabile** (classico: sasso-carta-forbice, servizio a tennis, attaccante/difensore).
- **Essere prevedibili ti costa**: controllo antifrode, audit, pricing dinamico contro un competitor che osserva, timing del lancio, scelta del canale di vendita se il competitor presidia quelli che usi sempre.
- **Hai risorse limitate e più target**: quale cliente visiti oggi, quale segmento attacchi prima, dove allocare il team commerciale quando non puoi coprire tutto.
- **Vuoi mantenere opzionalità**: non perché sei indeciso, ma perché vincolarti aiuta il competitor a prepararsi.

Il teorema di Nash garantisce che **ogni gioco finito ha almeno un equilibrio in strategie miste**, anche quando non ce l'ha in strategie pure.

## Il test "cella per cella" per capire se serve la strategia mista

Prendi la matrice 2×2 e segna con un asterisco le best response:

1. Per ogni colonna (mossa avversario), metti `*` sul payoff più alto per te.
2. Per ogni riga (tua mossa), metti `*` sul payoff più alto dell'avversario.
3. Celle con due `*` = equilibrio in strategie pure.

**Se nessuna cella ha due asterischi**, non c'è equilibrio puro → serve strategia mista.

Esempio — Tennis (attaccante sceglie dove tirare, difensore dove coprire):

| Paolo \\ Mario | (LL) | (IN) |
|---|---|---|
| **(LL)** | 50, 50 | 80, 20 |
| **(IN)** | 90, 10 | 20, 80 |

Nessuna cella ha doppio `*` → devi randomizzare.

## Il principio: rendere l'avversario indifferente

La logica della strategia mista ottima è controintuitiva ma fondamentale:

> **Tu scegli le tue probabilità in modo che l'avversario sia indifferente tra le sue mosse.**

Perché? Se l'avversario fosse contento di giocare una mossa specifica contro di te, la giocherebbe sempre e tu saresti sfruttato. Rendendolo indifferente, lo costringi a randomizzare a sua volta, e l'equilibrio regge.

## Calcolo pratico (2 mosse × 2 mosse)

Chiamiamo `p` la probabilità che tu giochi la prima mossa (1-p la seconda). Calcola il payoff atteso dell'**avversario** nei due casi in cui sceglie (A) o (B):

```
EV_avversario(A) = p × payoff_A_tu1 + (1-p) × payoff_A_tu2
EV_avversario(B) = p × payoff_B_tu1 + (1-p) × payoff_B_tu2
```

Imposta `EV_avversario(A) = EV_avversario(B)` e risolvi per `p`.

**Esempio tennis** (dal caso sopra, payoff di Mario):
- Mario gioca LL contro p-mix di Paolo: `50p + 10(1-p)`
- Mario gioca IN contro p-mix di Paolo: `20p + 80(1-p)`
- Uguagliando: `50p + 10 − 10p = 20p + 80 − 80p` → `40p + 10 = 80 − 60p` → `100p = 70` → `p = 0.7`

Paolo deve scegliere LL con probabilità 70% e IN con 30%. Stessa procedura simmetrica per Mario → `q = 0.6`.

## Traduzione business delle strategie miste

Nel business raramente calcoli `p = 0.7` con tre decimali. Ma il principio guida è potentissimo:

**1. Controllo e audit.** Se i dipendenti sanno che controlli il martedì, il martedì saranno perfetti e il resto della settimana no. Randomizza la scansione → massimizza la copertura effettiva a parità di costo.

**2. Pricing dinamico.** Se il competitor sa che reagisci sempre agli sconti, diventa un gioco ripetuto degenere. Rispondere a volte e ignorare altre (randomizzazione) rompe la sua capacità predittiva.

**3. Allocazione commerciale.** Con budget insufficiente per presidiare tutti i segmenti, presidiarne sempre lo stesso è subottimo — il competitor entra negli altri. Rotazione (deterministica o randomizzata) copre meglio.

**4. Timing di lancio.** Se il competitor prepara una contro-mossa basata sul tuo timing storico, randomizzare il timing di annunci e lanci riduce la sua capacità di anticiparti.

**5. Selezione target.** Nell'enforcement (compliance, controlli fiscali, cybersecurity red teaming) randomizzare i target è sempre meglio di pattern prevedibili.

## Strategie miste vs "fare a caso"

Attenzione: strategia mista ≠ scelta a caso senza pensarci.

- Le **probabilità devono essere calcolate** per bilanciare i payoff. Una randomizzazione uniforme 50/50 è quasi sempre subottima.
- La strategia mista **assume razionalità dell'avversario**. Se l'avversario è prevedibile/emotivo/boundedly rational, meglio sfruttarlo con strategia pura.
- **La credibilità del commitment a randomizzare** è essenziale. Se l'avversario pensa che in realtà tu abbia un pattern, tornerà a sfruttarti.

## Limite pratico: quando non vale la pena

- Giochi con equilibrio puro chiaro (dominanza) → usa quello, la strategia mista è solo rumore.
- Giochi dove l'avversario è poco razionale → la strategia mista premia un avversario che non saprebbe comunque sfruttarti.
- Decisioni one-shot con grande reversibilità: non ha senso randomizzare la scelta di un cloud provider.

## Collegamento con Bayes

Quando non sai con certezza il tipo di avversario (aggressivo vs prudente, informato vs disinformato), non usare una strategia mista pura: usa il tuo modello bayesiano delle probabilità di tipo, e aggiorna al margine con le informazioni disponibili. La strategia mista "pura" è il caso estremo di incertezza completa — nella vita reale quasi sempre hai qualche informazione su chi è l'avversario.
