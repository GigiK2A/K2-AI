---
name: lead-qualification
description: >-
  Skill verticale per P01 — Agenti AI Email & CRM. Fornisce framework e criteri
  operativi per qualificare lead nel contesto B2B delle PMI italiane. Usare quando
  il K-BOT deve analizzare il processo di qualificazione, identificare MQL/SQL,
  rilevare segnali di disqualifica, o proporre automazioni per il triage dei lead
  in ingresso. Entra nel bundle settoriale insieme a sales-strategy e
  diagnosi-ai-operativa-pmi.
---

# Qualificazione Lead B2B per PMI Italiane

Sei un esperto di qualificazione commerciale nel mercato B2B italiano. Applica
questi framework per analizzare il processo di triage dei lead di una PMI,
identificare dove si perdono opportunità valide o dove si sprecano ore su lead
non qualificabili.

---

## Perché la qualificazione è critica

Il problema più comune nelle PMI italiane non è la mancanza di lead — è la gestione
indiscriminata: ogni contatto riceve lo stesso trattamento, indipendentemente dal
potenziale. Risultato:

- Il commerciale spende 3 ore su un'azienda che non ha budget
- Un lead caldo con urgenza reale aspetta 4 giorni una risposta
- Il CRM accumula "opportunità" che non verranno mai chiuse

**Costo stimato di una qualificazione assente**: 30-50% del tempo commerciale sprecato
su lead non qualificabili, pari a 8-15 ore/settimana per un commerciale full-time.

---

## Framework BANT adattato al B2B italiano

BANT è il framework standard (Budget / Authority / Need / Timeline). Nel contesto
italiano va applicato con alcune varianti:

### B — Budget

Nel B2B italiano il budget raramente è "approvato" in anticipo per acquisti non
ricorrenti. Le domande giuste non sono "hai un budget?", ma:

- "Avete già affrontato spese simili in passato? Di che ordine di grandezza?"
- "Questo progetto rientra in un investimento già previsto o sarebbe nuovo?"
- "Chi gestisce internamente questo tipo di decisione di spesa?"

**Segnali budget positivi**:
- Budget esplicito menzionato (anche range)
- Spesa storica simile già sostenuta
- Progetto incluso in piano annuale / budget IT / PNRR

**Segnali budget negativi**:
- "Non abbiamo budget per ora" senza orizzonte
- Micro-azienda (< 5 dip.) senza entrate documentabili
- Risposta evasiva a 2+ domande sul costo

### A — Authority (Decisore)

In Italia la cultura aziendale è verticistica: il titolare decide spesso in autonomia
anche nelle PMI a 30 dipendenti. Parlare con il responsabile IT o l'office manager
senza coinvolgere l'imprenditore è un percorso a bassa conversione.

- "Chi partecipa alla valutazione di un acquisto come questo?"
- "C'è qualcuno che dovrebbe essere coinvolto prima che si possa procedere?"
- "Lei ha l'autonomia di approvare questo tipo di spesa?"

**Ruoli chiave da identificare**:

| Ruolo | Probabilità di decisione autonoma |
|---|---|
| Titolare / CEO / Socio fondatore | Alta |
| Direttore Generale | Alta se delegato |
| Resp. Amministrativo / CFO | Media (per spese < 5k) |
| Resp. IT / CTO | Bassa (propone, non decide) |
| Office Manager / Segreteria | Molto bassa |

### N — Need (Bisogno reale)

Il bisogno deve essere **esplicito** e **doloroso**. Un bisogno latente o teorico
non genera urgenza d'acquisto.

Domande per portare in superficie il need:

- "Questo problema quanto tempo vi sta costando ogni settimana?"
- "Se non cambiate nulla entro 6 mesi, cosa succede?"
- "C'è qualcosa che non riuscite a fare adesso per questo motivo?"

**Scala di intensità del bisogno**:
1. **Critico**: il problema blocca o rallenta operatività in modo misurabile
2. **Rilevante**: il problema costa tempo/denaro ma non è urgente
3. **Latente**: "sarebbe utile" ma non c'è dolore attivo
4. **Assente**: il lead non ha un problema reale — disqualify

### T — Timeline (Orizzonte temporale)

La timeline è il predittore più forte della velocità di chiusura.

- "Quando vorreste essere operativi con questa soluzione?"
- "C'è una scadenza esterna che guida questo progetto?"
- "Se trovassimo la soluzione giusta entro fine mese, potreste procedere?"

**Scadenze esterne ad alto valore** (generano urgenza reale):
- Scadenze normative (es. adeguamenti GDPR, D.Lgs. 231, NIS2)
- Fine esercizio fiscale con budget da usare
- Apertura di nuova sede / nuovo mercato
- Contratto con cliente che richiede capacità specifica
- Stagionalità del settore (es. picco ordini, campagna marketing)

---

## ICP — Profilo del cliente ideale

Definire l'ICP è prerequisito per qualsiasi processo di scoring. Se la PMI non ha
un ICP definito, ogni lead viene valutato soggettivamente.

### Template ICP per PMI B2B italiana

| Dimensione | Descrizione |
|---|---|
| Settore | Es. studi professionali, manifatturiero, servizi B2B |
| Dimensione | N. dipendenti, fatturato indicativo |
| Ruolo decisore | Es. titolare, direttore generale |
| Problema primario | Cosa li porta a cercare soluzioni come la nostra |
| Trigger evento | Cosa li spinge ad agire adesso |
| Anti-pattern | Chi NON è nostro cliente (budget minimo, settore escluso, ecc.) |

Un agente AI può qualificare in automatico i lead in ingresso (da form, email,
LinkedIn) confrontandoli con l'ICP definito e assegnando un punteggio.

---

## MQL vs SQL: distinzione operativa

### MQL — Marketing Qualified Lead

Un contatto che ha mostrato interesse ma non è ancora pronto per il commerciale:
- Ha scaricato un contenuto / risposto a una survey
- Ha visitato più volte il sito
- Ha aperto 3+ email della sequenza
- **Non ha ancora avuto un contatto diretto con un umano**

Azione: nurturing automatico (email, contenuti, richiamo a 30-60 gg).

### SQL — Sales Qualified Lead

Un contatto che ha superato la qualificazione BANT e merita attenzione commerciale:
- Budget: presenza di segnali positivi
- Authority: siamo in contatto con il decisore
- Need: bisogno esplicito e doloroso (livello critico o rilevante)
- Timeline: orizzonte entro 90 giorni

Azione: assegnazione immediata al commerciale, chiamata entro 24h.

**Regola operativa**: non spostare mai un MQL a SQL senza aver verificato almeno
N e A del framework BANT. Budget e Timeline possono essere parziali.

---

## Segnali di disqualifica (non sprecare tempo)

Interrompere il processo di qualificazione e chiudere il lead come "non qualificato"
quando si verificano 2+ di questi segnali:

| Segnale | Interpretazione |
|---|---|
| Nessuna risposta dopo 3 follow-up in 21 giorni | Disinteresse o timing sbagliato |
| Interlocutore dichiara di non essere il decisore e non vuole facilitare il contatto | Gatekeeper bloccante |
| Budget esplicitamente assente, senza orizzonte | Caso non maturo |
| Settore / dimensione fuori ICP | Rischio fit basso |
| Richiesta di proposta generica "da mandare in giro" | Procurement comparativo a basso valore |
| Richiesta di sconto prima della discovery | Acquisto guidato solo da prezzo |

Un lead disqualificato ora non è perso per sempre. Va messo in una lista di
riattivazione a 6 mesi, gestita in automatico da un agente AI.

---

## Pattern di domande per la qualificazione telefonica/email

### Discovery call (15-20 minuti) — struttura consigliata

```
1. Rompighiaccio (2 min)
   "Come vi ha trovati? / Chi vi ha segnalati?"

2. Contesto azienda (3 min)
   "Quante persone lavorate su [processo specifico]?
    Come gestite oggi [problema]?"

3. Problema e impatto (5 min)
   "Cosa vi sta costando questa situazione in termini di tempo?
    Cosa succede se non risolvete entro fine anno?"

4. Decisore e processo (3 min)
   "Chi è coinvolto nella valutazione di questo tipo di acquisto?
    Come avete preso decisioni simili in passato?"

5. Timeline e passo successivo (3 min)
   "Entro quando vorreste essere operativi?
    Ha senso che preparo una proposta personalizzata entro [data]?"
```

### Email di qualificazione (per lead da form/inbound)

Modello ad alto tasso di risposta:

```
Oggetto: [Nome azienda] — 3 domande rapide prima di risponderti

Ciao [Nome],

Grazie per averci contattato.

Per prepararti una risposta utile (e non generica), ho bisogno di
capire il tuo contesto in 3 minuti:

1. Quante persone in azienda lavorano su [area di problema]?
2. Qual è il principale problema che vuoi risolvere adesso?
3. Hai già valutato altri strumenti / fornitori per questo?

Rispondo entro [N ore] con una proposta su misura.

[Firma]
```

Un agente AI può gestire questa fase di pre-qualificazione in automatico,
raccogliendo le risposte e aggiornando il CRM prima che il commerciale
intervenga. Risparmio stimato: 1-2 ore/giorno per team da 3+ commerciali.

---

## Scoring lead: modello pratico

### Matrice di scoring a 3 fattori (0-3 per fattore, max 9)

**Fit con ICP**:
- 3: Settore, dimensione e ruolo corrispondono perfettamente all'ICP
- 2: 2 su 3 dimensioni corrispondono
- 1: Solo 1 dimensione corrisponde
- 0: Fuori ICP su tutte le dimensioni

**Intensità del bisogno**:
- 3: Problema critico, misurabile, con impatto operativo attivo
- 2: Problema rilevante, ammesso esplicitamente
- 1: Bisogno latente, non ancora prioritario
- 0: Nessun bisogno dichiarato

**Urgency / Timing**:
- 3: Scadenza esterna entro 60 giorni o decision-maker pronto ora
- 2: Orizzonte 60-120 giorni, disponibilità a procedere
- 1: "Ci pensiamo per il prossimo trimestre"
- 0: Nessun orizzonte temporale o esplicitamente non urgente

**Soglie di azione**:
- Score 7-9 → SQL: commerciale contatta entro 24h
- Score 4-6 → MQL: sequenza nurturing automatica
- Score 0-3 → Disqualifica o lista riattivazione 6 mesi
