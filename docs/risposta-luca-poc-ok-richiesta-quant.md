# Risposta a Luca — verdetto recepito, i due fix fatti, e cosa ci serve da te (per intero)

Ciao Luca,

verdetto recepito, e grazie per aver **rifatto la verifica di tracciabilità in modo indipendente** invece di fidarti del mio audit — è esattamente il livello di rigore che serve su un deliverable venduto. I tuoi tre criteri sono giusti e li ho già messi in pratica dove posso senza il quant.

## Cosa ho già fatto sul PoC (non dipende dal tuo quant)

**Criterio #2 — provenienza esplicita: FATTO.** Ho abbandonato il match per valore. Ora ogni tool quant ritorna un `call_id` univoco; il deliverable, nella sezione `enterprise_value.provenance`, deve **citare il call_id** che ha prodotto ogni numero; e il gate Stop verifica che il valore nel campo sia davvero un output **di quella specifica chiamata**. Testato: un numero inventato che cita una chiamata sbagliata ora viene **rifiutato** ("NON è un output della chiamata citata"). Il buco che avevi trovato è chiuso.

**Criterio #3 — fail-closed: FATTO.** Esaurito il numero di blocchi del gate, il run è marcato FAILED e il file viene messo in **quarantena** (`deliverable.REJECTED.json` + `ALERT.txt`): non esiste percorso per cui un run fallito diventi un deliverable consegnato. In prod questa diventa la regola del backend (niente documento → alert/retry/escalation), l'exit code è già non-zero.

**Run ripetuti in-target: in corso.** Ho preparato 4 casi PMI reali nel target (studio ingegneria sano, manifatturiero in turnaround, servizi IT che valuta un'acquisizione, hospitality asset-heavy) e li sto girando per misurare **stabilità e varianza dell'orchestrazione**. Come dicevi, questa misura non dipende dallo snapshot — misura se l'agente completa, passa i gate e produce provenienza verificata in modo consistente, **non** la correttezza dei numeri (quella aspetta il tuo quant).

## La precisazione su #1 (il punto migliore che hai fatto)

Sono d'accordo al 100% che **le assunzioni sono il valore**, non le formule, e che vadano nei tool. Una sola linea di confine da fissare insieme, perché cambia il design:

> **Non tutte** le assunzioni sono tool-derivabili. Costo equity (CAPM da beta+ERP snapshot), g (range da snapshot), WACC, matematica DCF/multipli: **sì, deterministiche nel tool.** Ma le **proiezioni FCF forward** dipendono da giudizio di business reale — non c'è una regola universale per ogni azienda. Lì il modello giusto è: l'agente le **dichiara esplicitamente come assunzioni** (scenario base/pessimistico), il deliverable le mostra, l'audit le traccia. Auditabili anche se non tool-derivate.

In sintesi: **tool-derivato dove è derivabile, dichiarato-e-auditato dove è giudizio genuino.** Così il quant non deve fingere di calcolare ciò che è una scelta — la rende solo trasparente e tracciata.

## Cosa ci serve da te, per intero, per sbloccare lo swap quant-lite → quant vero

Hai detto che imposti `k2a-mcp-quant` in stile `k2a-mcp-elettrico` e mi mandi il perimetro dei primi tool. Perfetto — perché sia subito agganciabile, mi servono **queste cose, complete**:

### 1. Spec dei tool (per ognuno: CAPM, WACC, DCF, multipli, patrimoniale, reconcile, indici+CCII)
- **nome** del tool MCP (es. `mcp__quant__capm_cost_of_equity`)
- **input** (nome, tipo, obbligatorio) — e quali input l'agente **non** passa più perché derivati dallo snapshot (es. beta ed ERP per il CAPM)
- **output** (nome, tipo) + un esempio JSON
- **quali assunzioni possiede il tool** (criterio #1): es. CAPM → beta per settore + ERP + risk-free dallo snapshot; DCF → g vincolato a range; dove invece l'assunzione resta dichiarata dall'agente (FCF forward)
- **metodo/formula** e garanzie di determinismo

### 2. Spec dello snapshot (il dato che invecchia)
- contenuto: beta per settore ATECO, ERP, risk-free, g-range per settore, multipli EV/EBITDA ed EV/Ricavi per settore, ecc.
- **fonte** (Damodaran o altro) e **as_of**
- **cadenza di aggiornamento** e **chi la possiede** (manutenzione ricorrente, non check una-tantum)

### 3. Come si invoca l'MCP
- trasporto: **stdio** (comando + args) o **URL/SSE**?
- **env** richieste, eventuale auth
- come lo lancio in locale per il test e come andrà nel container 8e

### 4. Contratto di provenienza (per agganciarsi a quello che ho già costruito)
- conferma che ogni tool ritorni un **identificativo di chiamata** (o un risultato strutturato) che possiamo citare nel deliverable, così il mio gate di provenienza ci si aggancia senza riscritture

### 5. Tier/entitlement lato quant
- c'è qualche limite di tier sui tool quant, o l'entitlement resta **tutto** nel backend e gli hook lo rafforzano? (Per me l'allowlist per tier sta negli hook, ma confermami che dal tuo lato non serve nulla.)

### 6. Ordine e tempi
- da quali tool parti (per Advisor bastano i 7 sopra) e una stima, così pianifichiamo lo swap

## Il punto

Da parte nostra il PoC è pronto a ricevere il quant vero: provenienza e fail-closed dentro, casi in-target in misura. Appena mi mandi i 6 punti, sostituisco `quant-lite` col tuo MCP e rigiriamo i casi con i **numeri veri e le assunzioni nei tool** — ed è lì che misuriamo la correttezza, non solo la robustezza.

Allego il pacchetto aggiornato (codice + artefatti + audit). Quando hai il perimetro dei tool, partiamo.

Luigi
