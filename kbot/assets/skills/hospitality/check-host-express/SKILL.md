---
name: check-host-express
description: Genera un pagellino ricettivo rapido 0-100 per strutture italiane (agriturismi, B&B, piccoli hotel, case vacanza 5-30 camere) partendo da 6-8 numeri essenziali. Trigger "check ricettivo", "check agriturismo", "pagella hotel", "come va il mio agriturismo", "RevPAR rapido", "quanto rende la mia struttura", "check B&B", "diagnosi rapida ricettivo", "score ricettivo", "semaforo hotel", "il mio agriturismo e messo male?", "HostCheck". Input minimi camere, giorni apertura, notti vendute anno, ricavi camera anno, rating Booking, quota Booking.com, zona/regione, tipologia. Calcola 6 KPI (RevPAR vs zona, Occupancy, ADR, Dipendenza OTA, Rating reputation, Quota diretto) con semaforo verde/giallo/rosso, soglie per tipologia e regione. Output pagella HTML single-page con score globale 0-100, 6 semafori, 3 priorita, CTA verso flusso-hostboost-ricettive. Lead magnet gratuito o 49 EUR per PMI ricettive italiane. Primo touchpoint HostBoost.
---

# check-host-express

Pagellino ricettivo rapido 0-100 per PMI italiane del comparto ospitalita (5-30 camere). Il titolare inserisce 6-8 numeri, riceve un semaforo visivo che gli dice in 3 minuti come sta messo vs la sua zona.

## Panoramica

Tripwire / lead magnet del funnel HostBoost. Non fa diagnosi completa (quella e in `flusso-hostboost-ricettive`), fa un primo screening che produce uno score sintetico e i 3 problemi piu urgenti. Il titolare capisce se ha bisogno di approfondire e viene indirizzato all'analisi completa.

Pensato come:
- **Gratuito**: lead magnet su LinkedIn / newsletter K2-AI, in cambio di email.
- **A pagamento 49 EUR**: per chi arriva organico e vuole subito un output.

## Input

### Obbligatori (6)
- **Tipologia** (agriturismo / B&B / hotel 3 stelle / boutique 4 stelle / casa vacanza / affittacamere)
- **Regione** (delle 20 italiane)
- **Camere totali** (numero)
- **Giorni apertura annui** (giorni effettivi)
- **Notti vendute ultimo anno** (somma)
- **Ricavi camera ultimo anno** (EUR, solo alloggio, netto IVA)

### Opzionali (3) — migliorano precisione
- **Rating Booking.com** (scala 1-10)
- **Quota ricavi Booking.com** (% sul totale)
- **Quota ricavi canale diretto** (% sul totale)

Se opzionali mancanti, usare default mediani da `references/scoring-model-host.md` e segnalare "dato stimato" nel report.

## Workflow

1. **Raccolta input** con domande semplici, esempi e default ragionevoli. Se il titolare non sa un dato, guida con domanda alternativa ("quante notti hai venduto? se non sai, quante prenotazioni x durata media?").
2. **Calcolo 3 KPI core**: Occupancy, ADR, RevPAR dalle formule standard del revenue management.
3. **Lookup benchmark**: da `references/scoring-model-host.md` per tipologia + regione.
4. **Calcolo 3 KPI distribuzione/reputation**: Dipendenza OTA, Rating, Quota diretto (con default se mancanti).
5. **Assegnazione semafori**: verde/giallo/rosso per ognuno dei 6 KPI secondo soglie tipologia-specifiche.
6. **Score globale 0-100**: media ponderata (RevPAR e Occupancy pesano di piu).
7. **Top 3 priorita**: seleziona i 3 KPI con semaforo peggiore e genera suggerimenti in italiano semplice, senza jargon.
8. **Generazione pagella HTML**: template in `assets/template-semaforo-host.md`, self-contained, visivo, stampabile.
9. **CTA**: "Se vuoi capire come migliorare concretamente, HostBoost analizza i tuoi dati reali di 12 mesi e ti da un piano operativo. 899 EUR una tantum o pianifichiamo una call."

## I 6 KPI analizzati

| # | KPI | Formula | Cosa dice al titolare |
|---|-----|---------|-----------------------|
| 1 | RevPAR vs zona | `Ricavi / (Camere × Giorni aperto)` confrontato con mediana regione+tipologia | Se stai facendo piu o meno degli altri della tua zona |
| 2 | Occupancy | `Notti vendute / (Camere × Giorni aperto)` | Quanto piene tieni le camere quando sei aperto |
| 3 | ADR | `Ricavi / Notti vendute` | Prezzo medio reale di vendita della camera |
| 4 | Dipendenza OTA | Quota Booking.com + Expedia sui ricavi | Quanto dipendi dalle piattaforme (rischio commissioni e sospensioni) |
| 5 | Rating Booking | Valore assoluto su scala 10 | Reputation online: impatta direttamente la conversione |
| 6 | Quota diretto | % ricavi da canale diretto (sito + WhatsApp + telefono) | Quanto controllo hai sulla clientela |

## Semafori (soglie tipiche)

Le soglie esatte variano per tipologia e regione (tabelle in `references/scoring-model-host.md`). Soglie indicative medie:

| KPI | Verde | Giallo | Rosso |
|---|---|---|---|
| RevPAR vs mediana zona | >= mediana | 70-100% mediana | < 70% mediana |
| Occupancy | >= 55% | 40-55% | < 40% |
| ADR vs mediana zona | 85-115% mediana | 70-85% o 115-130% | < 70% o > 130% |
| Dipendenza OTA | < 50% | 50-65% | > 65% |
| Rating Booking | >= 8.7 | 8.0-8.7 | < 8.0 |
| Quota diretto | > 25% | 15-25% | < 15% |

## Score globale

Media ponderata normalizzata 0-100:
- RevPAR: peso 30%
- Occupancy: peso 20%
- ADR: peso 15%
- Dipendenza OTA: peso 10%
- Rating: peso 15%
- Quota diretto: peso 10%

Verde = 3 punti, Giallo = 1.5 punti, Rosso = 0 punti. Somma ponderata × 33.33 per normalizzare 0-100.

Fascia di giudizio:
- **85-100**: Eccellente. Continua cosi, piccoli tuning.
- **65-84**: Buono. Qualche area da migliorare, niente urgenze.
- **45-64**: Sufficiente. Serve un piano d'azione concreto.
- **25-44**: Preoccupante. Problemi strutturali da affrontare.
- **0-24**: Critico. Rischio economico reale.

## Tono di comunicazione

**Diretto ma empatico**. Il titolare di agriturismo non vuole essere giudicato, vuole capire.
- Non "la tua performance e sotto-media". Scrivi "gli altri agriturismi come il tuo nella tua regione fanno 62 EUR di RevPAR, tu 41. Si puo migliorare."
- Mai jargon: "tariffa media di vendita" prima di introdurre ADR.
- Sempre numeri di zona per contesto.
- Top 3 priorita con verbo all'imperativo: "Ribilancia i canali", "Alza il rating rispondendo alle recensioni", "Taglia il minimum stay infrasettimanale".

## Output

1. **Pagella HTML single-page**: template in `assets/template-semaforo-host.md`. Responsive, stampabile, shareable via link.
2. **JSON strutturato**: schema in `schemas/output-schema.json`.

File salvati in `/mnt/outputs/` e presentati via `mcp__cowork__present_files`. Naming: `check-host-{slug_struttura}-{YYYYMMDD}.html` e `.json`.

## Errori comuni da evitare

- **Non trattare la struttura come hotel di catena**: un agriturismo con 40% di occupancy puo essere sano se e chiuso 4 mesi e fa margini alti sulla ristorazione.
- **Non imporre logica stagionalita standard**: un glamping aperto giu-set con 60% occupancy su quei 120 giorni e top quartile, non sottoperformante.
- **Non chiudere con pressione commerciale**: CTA verso HostBoost esplicita "solo se vuoi approfondire", non aggressivo.
- **Non far mancare il disclaimer**: "questo score e indicativo, serve solo a decidere se approfondire. La diagnosi vera richiede dati di 12 mesi reali."

## Collegamenti con altre skill

- Invoca `benchmark-italia-business` per valori regionali se disponibili.
- Usa i benchmark hardcoded in `references/scoring-model-host.md` come fallback.
- CTA verso `flusso-hostboost-ricettive` per approfondimento.
- Se il titolare dice "voglio migliorare il sito / SEO" → rimanda a `check-seo-express` del verticale WEB.
