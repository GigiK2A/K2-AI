# Messaggio per Luca — PoC Agent SDK su AdvisorBoost (2 domande + contesto)

> Da inviare via WhatsApp/email. Le 2 domande in fondo sono le uniche cose che bloccano.

---

Ciao Luca, due cose da decidere insieme prima che parta con un esperimento sul motore. Contesto rapido e poi le domande.

## Contesto

Il K-BOT ora genera i Boost via 8e (pipeline deterministica: route → snapshot → prosa → validazione → PDF). Funziona bene per i boost "compilativi" (Legal, Fisco, Finance). **AdvisorBoost invece fallisce spesso la validazione**: ha lo schema più stringente (12 sezioni, EV con multipli/DCF/patrimoniale, campi numerici obbligatori) e una pipeline a passi fissi non riesce ad adattarsi ai dati disponibili caso per caso.

Voglio fare un **PoC isolato** (fuori dal K-BOT live, nessun impatto su ciò che gira): AdvisorBoost orchestrato da un **agente a guinzaglio corto** (Claude Agent SDK) che:
- legge la tua skill `flusso-advisorboost-pmi` come istruzioni operative,
- decide caso per caso quali metodi di valutazione applicare in base ai dati che ha,
- prende i **numeri SOLO da MCP deterministici** (mai dal modello),
- con **hook deterministici** che bloccano: PreToolUse = entitlement/allowlist tool per tier, Stop = anti-omissione (non consegna se manca una sezione obbligatoria o un numero non tracciato a un tool).

Misuro costo token e latenza contro la pipeline attuale, e decidiamo coi numeri se promuoverlo a ramo del motore per i boost "che ragionano". I boost compilativi restano in pipeline com'è.

## Domanda 1 — k2a-mcp-quant

Per i numeri della valutazione (DCF, WACC, multipli Damodaran, EV) mi serve il tuo **k2a-mcp-quant** (i 27 tool quant). Senza, il PoC non dimostra nulla perché i numeri li farebbe il modello — esattamente ciò che vogliamo evitare.

- Mi dai accesso al repo / build? Come lo lancio (stdio? porta? env richieste)?
- Gli snapshot dati (multipli, tassi) sono abbastanza freschi o vanno rigenerati prima?

## Domanda 2 — chi orchestra L2 (la decisione di architettura)

Questa è la vera scelta di piattaforma, e la possiedi tu. Per il livello L2 (l'orchestrazione di un boost), due strade:

**A. La skill è ESEGUIBILE**: un agente legge `flusso-*boost` e la esegue passo passo. La tua skill è l'orchestratore — *single source of truth*. Tu aggiorni la skill → il comportamento cambia subito, senza che io tocchi codice. Costo: token e latenza più alti, serve guinzaglio (hook, max_turns, allowlist).

**B. La skill è una SPEC**: il codice del 8e la ri-implementa come pipeline fissa (com'è oggi). Più economico, deterministico, veloce. Costo: la logica vive in **due posti** (la tua skill + il mio codice) e va tenuta in sync a mano, come facciamo col catalog.json — rischio drift silenzioso quando aggiorni una skill.

La mia proposta: **B resta per i boost compilativi, A si sperimenta col PoC per i boost che ragionano** (Advisor, e in futuro le verifiche tecniche/ingegneria). Ma voglio saperlo da te: **nella tua testa le skill `flusso-*` sono nate per essere eseguite da un agente, o sono spec di riferimento?** La risposta decide quanto investire nel PoC.

## Cosa NON cambia

- K-BOT live: intatto (API + pipeline 8e).
- Interfaccia 8e (API + catalog.json): intatta.
- Entitlement/paywall: restano nel backend, mai delegati all'agente (gli hook li *rafforzano*, non li sostituiscono).

Appena mi rispondi su quant e su A/B, parto col PoC e ti porto numeri (qualità output, token, latenza) per decidere.
