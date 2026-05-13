---
name: sentiment-analysis
description: >-
  Analisi sentiment e triage intelligente ticket customer service per PMI
  italiane. Classifica urgenza, identifica segnali di escalation, suggerisce
  routing e template di risposta per tipo di richiesta.
---

# Sentiment Analysis e Triage Ticket Customer Service

## Classificazione sentiment

| Livello | Segnali linguistici | Azione |
|---------|--------------------|---------
| 🔴 Critico | "inaccettabile", "avvocato", "denuncia", "vergogna", "scandaloso", caps lock | Risposta entro 1h, supervisore |
| 🟠 Negativo urgente | "ancora nessuna risposta", "terza volta", "non funziona da X giorni" | Risposta entro 2h, priorità P1 |
| 🟡 Insoddisfatto | "deluso", "non sono soddisfatto", tono seccato | Risposta entro 4h, P2 |
| 🟢 Neutro | Richiesta informazioni, tono neutro | Risposta entro 24h, P3 |
| 💙 Positivo | Ringraziamento, apprezzamento | Risposta cortese, P4 |

## Triage per tipo di richiesta

| Categoria | Segnali | Team/skill |
|-----------|---------|------------|
| Guasto tecnico | "non funziona", "errore", "bloccato", "non si apre" | Tecnico |
| Fatturazione | "fattura", "addebito", "rimborso", "pagamento" | Amministrativo |
| Reclamo formale | "reclamo", "lamentela", "voglio essere risarcito" | Responsabile CS |
| Informazioni | "come si fa", "vorrei sapere", "è possibile" | Self-service / FAQ |
| Richiesta commerciale | "preventivo", "listino", "voglio acquistare" | Commerciale |
| Urgenza operativa | "bloccato", "fermo produzione", "scadenza oggi" | Escalation immediata |

## Template risposte per categoria

**Guasto tecnico (primo contatto)**:
> Gentile [Nome], ho ricevuto la segnalazione relativa a [problema]. Ho già aperto ticket #[ID] con priorità [P1/P2]. Il nostro tecnico la ricontatterà entro [X ore] per risolvere. Nel frattempo, può provare [workaround se disponibile]. Rimango a disposizione.

**Reclamo formale**:
> Gentile [Nome], la ringrazio per aver segnalato il problema. Comprendo la sua insoddisfazione riguardo a [oggetto reclamo] e me ne scuso. Ho escalato la situazione a [responsabile] che la contatterà entro [X ore] con una soluzione. Il numero del suo reclamo è #[ID].

**Fatturazione**:
> Gentile [Nome], ho verificato il suo account. [Situazione trovata]. Procederò con [azione: rimborso/correzione/spiegazione] entro [X giorni lavorativi]. Riceverà conferma via email a [indirizzo].

## KPI customer service — target PMI

| Metrica | Acronimo | Target B2B | Target B2C |
|---------|----------|------------|------------|
| Tempo prima risposta | FRT | < 2h | < 4h |
| Tempo risoluzione | AHT | < 24h | < 48h |
| Risoluzione primo contatto | FCR | > 70% | > 65% |
| Soddisfazione cliente | CSAT | > 4/5 | > 4/5 |
| Net Promoter Score | NPS | > 40 | > 35 |
| Riapertura ticket | Reopen rate | < 10% | < 15% |

## Escalation triggers — condizioni automatiche

Escalate immediatamente se:
- Cliente menziona azione legale o diffida
- Stesso problema segnalato 3+ volte in 30 giorni
- Impatto su > 5 clienti (problema sistemico)
- Perdita economica dichiarata dal cliente > 500€
- Media/stampa citata nella segnalazione
- Utente VIP / contratto premium

## Analisi batch ticket

Per analisi di molti ticket contemporaneamente:
1. Raggruppa per categoria (tecnico/fatturazione/reclamo/info)
2. Identifica pattern ricorrenti → possibili bug o gap di prodotto
3. Calcola distribuzione sentiment (% critici, negativi, neutri, positivi)
4. Segnala top 3 problemi per volume
5. Suggerisci FAQ o articoli KB per ridurre volume richieste

## Regole operative

- Non promettere tempistiche che non puoi garantire
- Usa sempre il nome del cliente nella risposta
- Non usare linguaggio burocratico ("in merito alla sua del giorno")
- Chiudi sempre con un'azione concreta + owner + scadenza
- Aggiungi sempre numero ticket per tracciabilità
