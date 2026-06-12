# Handoff a Luca (+ il suo Claude) — PoC Agent SDK su AdvisorBoost

> **Scopo di questo documento:** dare a te e al tuo runtime engineer tutto il necessario per **valutare** un proof-of-concept che abbiamo costruito ed eseguito oggi (2026-06-12). Niente è in produzione, niente tocca il K-BOT live. Vogliamo una decisione informata su **se e come** promuovere questo approccio per i boost "che ragionano".
>
> Codice in repo: `k2a-8e-agent-poc/` (commit `63b2cb4`). Artefatti del run in `k2a-8e-agent-poc/out/`.

---

## 1. Il contesto / perché l'abbiamo fatto

Il K-BOT oggi genera i Boost via **pipeline 8e deterministica** (route → snapshot → prosa Sonnet per-sezione → validazione L1/L2/schema → render). Funziona bene per i boost **compilativi** (Legal, Fisco, Finance: procedura stabile, "riempi il documento dal catalogo").

**AdvisorBoost fa eccezione: la pipeline lo RIFIUTA spesso.** Ha lo schema più stringente (12 sezioni, enterprise value con 3 metodi, campi numerici obbligatori) e una pipeline a passi fissi non si adatta ai dati disponibili caso per caso — se manca un input per un metodo, la validazione blocca tutto.

Ipotesi da testare: **un boost che richiede giudizio (quale metodo di valutazione applicare in base ai dati) si genera meglio con un agente a guinzaglio corto che esegue la skill, piuttosto che con una pipeline a passi fissi** — *purché* il determinismo sui numeri sia garantito da fuori (tool + gate), non dal modello.

AdvisorBoost è il candidato giusto **proprio perché è quello che fallisce**: testiamo l'ipotesi dove deve contare.

---

## 2. Cosa abbiamo costruito (architettura del PoC)

Tre livelli, esattamente la tua architettura L1→L2→L3, ma con L2 eseguito da un **agente** invece che da codice pipeline:

```
[L2] Agente (Claude Agent SDK 0.2.99, Sonnet 4.6, guinzaglio corto)
      ├─ system_prompt = la TUA skill  flusso-advisorboost-pmi/SKILL.md  (integrale, eseguita)
      ├─ max_turns=60, setting_sources=None (isolamento: nessuna skill/CLAUDE.md esterna)
      ├─ allowed_tools = solo i 6 quant + Read/Write/Edit/TodoWrite
      └─ disallowed = Bash/WebSearch/WebFetch/Task/Glob/Grep
              │
              ├──[L3] quant-lite (MCP in-process, create_sdk_mcp_server)
              │       6 tool DETERMINISTICI (funzioni Python pure):
              │       wacc · dcf_enterprise_value · ev_from_multiples ·
              │       patrimonial_value · reconcile_ev · indici_bilancio (+ alert CCII)
              │       → ⚠ surrogato di k2a-mcp-quant. Snapshot multipli = PLACEHOLDER dichiarato.
              │
              └──[gate] Hook deterministici (codice, non LLM — "sempre", non "quasi sempre")
                      PreToolUse = allowlist per tier (es. tier "light" NON può usare il DCF);
                                   Write solo dentro out/  → altrimenti DENY
                      Stop       = anti-omissione: 10 sezioni obbligatorie presenti +
                                   EV completo (4 campi) + OGNI numero EV tracciato a un
                                   output dei tool quant → altrimenti BLOCK e l'agente rifà
```

**Audit trace** (`out/audit.json`) registra: hash della skill, hash degli input, ogni tool chiamato, gli output integrali dei tool quant, ogni evento di gate. È il requisito pass/fail di riproducibilità per un deliverable venduto e contestabile.

---

## 3. Cosa è successo durante il test (run reale)

**Input:** bilancio **Juventus FC** consolidato 2023/24 + 2022/23 (dati veri: ricavi 394,6M, EBITDA −5,7M, perdita 199,2M, PN 40,2M, PFN 242,8M). File `data/juventus_input.json`.

**Esito: deliverable completo e validato AL PRIMO Stop, nessuna rilavorazione.**

| Misura | Valore |
|---|---|
| Deliverable | **OK** — 10/10 sezioni, passato il gate anti-omissione al primo tentativo |
| Tool call totali | 22 (tutte quant + Read/Write) — 7 risultati quant tracciati |
| Costo | **$0,909** |
| Latenza | 500 s (~8,3 min) |
| Turni | 23 |
| Output tokens | 27.964 (cache read 518K → prompt caching attivo sulla skill) |
| Gate PreToolUse DENY | **1** |
| Gate Stop BLOCK | 0 |

### I gate hanno funzionato dal vivo (non in teoria)
- **PreToolUse → DENY**: l'agente ha provato a chiamare `ToolSearch` (fuori allowlist del tier) → l'hook l'ha negato → l'agente si è adattato e ha proseguito senza.
- **Stop → ALLOW**: l'hook ha verificato che **tutti e 4 i numeri dell'enterprise value combaciassero con un output dei tool quant** (non inventati dal modello). Tutti tracciati → consegna concessa.

### Comportamento "da advisor vero" (l'adattività che la pipeline non ha)
- EBITDA negativo → l'agente **ha scelto** EV/Ricavi sui multipli invece di EV/EBITDA, e l'ha motivato.
- Ha pesato i 3 metodi (multipli 45% / DCF / patrimoniale) **citando transazioni di mercato reali** (Roma/Friedkin ~1,1x; Milan/RedBird ~2,2x) per giustificare il multiplo.
- Ha rilevato **da solo** che la Juventus è fuori target AdvisorBoost (PMI 5-50 dip.) e l'ha dichiarato come "stress-test" in apertura — auto-consapevolezza di perimetro.
- Ha applicato la **regola operativa #5 della tua skill**: allerta CCII attiva (Art. 2446 c.c., DSCR<1, perdite > 1/3 capitale) + raccomandazione composizione negoziata (D.Lgs. 14/2022). Senza che nessuno gliela ricordasse: l'ha letta dalla skill e applicata.

---

## 4. Cosa è stato prodotto

In `k2a-8e-agent-poc/out/`:
- **`deliverable.json`** — l'output strutturato (output #4 della tua skill): 10 sezioni (executive_summary, analisi_bilancio, analisi_settore, posizionamento_vrio, opzioni_strategiche, piano_36_mesi, enterprise_value, azioni_prioritarie, cruscotto_kpi, disclaimer).
- **`audit.json`** — trace di riproducibilità.
- **`metrics.json`** — costi/token/latenza/gate.

**Enterprise value prodotto** (tutti i numeri dai tool quant, tracciati nell'audit):

| Metodo | Valore |
|---|---|
| Multipli (EV/Ricavi 2,4x, perché EBITDA<0) | 947,0 M€ |
| DCF (WACC dai tool, FCF previsti, Gordon) | 861,7 M€ |
| Patrimoniale (PN + rettifiche dichiarate) | 190,2 M€ |
| **EV raccomandato** (media pesata, pesi motivati) | **833,0 M€** |

> ⚠ I valori riflettono lo **snapshot multipli PLACEHOLDER**, non il tuo dataset. Servono a validare l'**architettura** (i numeri escono dai tool e sono tracciati), non a essere una valutazione reale della Juve.

**Non** ancora prodotti dal PoC: il DOCX 30-40 pagine, l'XLSX 7-tab, la dashboard HTML (output #1-3 della skill). Sono rendering a valle, fuori dallo scope del test architetturale. La sostanza (analisi + numeri + struttura) è tutta nel JSON.

---

## 5. Le 2 cose che ci servono da te (sbloccano la promozione)

**Domanda 1 — k2a-mcp-quant.** Per sostituire il mio `quant-lite` (snapshot placeholder) col tuo motore vero:
- I 27 tool quant esistono già come **MCP deterministico reale**, o sono ancora conoscenza/skill da "mcp-ificare"? (È un prerequisito di *build*, non di accesso.)
- Come lo lancio (stdio? URL? env)? E gli **snapshot** (multipli Damodaran ~annuali, tassi mobili) sono freschi o vanno rigenerati? Trattiamolo come manutenzione ricorrente, non check una-tantum.

**Domanda 2 — chi orchestra L2 (la tua decisione di architettura).** Le skill `flusso-*boost` sono nate per essere **eseguite da un agente** (single source of truth, questo PoC) o sono **spec di riferimento** che il codice 8e ri-implementa (pipeline attuale, rischio drift skill↔codice)?
- La nostra proposta è l'**ibrido**: pipeline deterministica per i boost compilativi (Legal/Fisco/Finance), agente a guinzaglio corto per quelli che ragionano (Advisor, e in futuro le verifiche tecniche/ingegneria). Ma la decisione la possiedi tu.

---

## 6. Cosa resta prima di promuovere in produzione (paletti onesti)

1. **Swap quant-lite → k2a-mcp-quant** reale + snapshot freschi (Domanda 1).
2. **Run ripetuti**: 1 run = segnale forte, non statistica. Vanno provati N casi (PMI vere in target, non solo lo stress-test Juve) per misurare stabilità e varianza.
3. **Tier reali**: l'allowlist ora è simulata; in prod deriva dal token entitlement firmato del backend (la business logic resta nel backend, gli hook la *rafforzano*, non la sostituiscono).
4. **Audit obbligatorio in prod**: per un deliverable venduto 1.999-3.999€ contestabile, il trace di riproducibilità (versione skill + tool + inputs_hash + scelta metodo) è condizione di promozione, non opzione.
5. **Rendering DOCX/XLSX/HTML** a valle del JSON.

---

## 7. La domanda secca per te + il tuo Claude

> Guardando l'architettura (sez. 2), il comportamento osservato nei gate e nell'adattività (sez. 3), e l'output (sez. 4): **l'approccio agente-a-guinzaglio-corto + hook è la strada giusta per i boost che ragionano, o vedete un rischio/limite che non abbiamo considerato?** E: **le `flusso-*` skill, nella tua testa, sono eseguibili o spec?**
>
> Tutto il resto (quant vero, run ripetuti, tier, rendering) è lavoro noto. Questa è la sola decisione di architettura che vogliamo prendere con te.
