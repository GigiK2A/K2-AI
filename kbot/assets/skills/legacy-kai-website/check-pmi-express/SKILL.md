---
name: check-pmi-express
description: Pagellino strategico-finanziario rapido per PMI italiane 5-50 dipendenti. Lead magnet tripwire verticale ADVISOR (gratuito o 49 EUR). Score 0-100 con 6 semafori (redditualita, solidita, liquidita, crescita, posizionamento, dipendenza clienti) e top 3 criticita spiegate. Usa per "check PMI", "pagella azienda", "come sta la mia PMI", "controllo rapido PMI", "salute azienda", "la mia PMI e in salute?", "diagnosi lampo PMI", "score azienda", "quick check azienda", "stiamo andando bene?", "valutazione rapida PMI", "AdvisorExpress". Input: fatturato ultimo anno, utile netto, PFN, dipendenti, settore, anno fondazione, competitor, concentrazione primo cliente %. Output HTML single-page con gauge score, 6 semafori, 3 criticita prioritarie, CTA verso AdvisorBoost completo, piu JSON strutturato. Per titolari PMI italiane primo check prima di diagnosi strategica 1.999-3.999 EUR. Tono senza gergo business school. Primo touchpoint funnel consulenza K2-AI.
---

# Check PMI Express

Lead magnet tripwire del verticale ADVISOR di K2-AI. Il titolare di una PMI italiana (5-50 dipendenti) inserisce 8-10 dati essenziali e riceve in 5 minuti una pagella visiva con score 0-100, 6 semafori strategico-finanziari e le 3 criticita piu urgenti da affrontare.

## Quando attivare

Questa skill si attiva quando:
- L'utente chiede "check PMI", "pagella azienda", "salute azienda"
- Il titolare vuole un primo colpo d'occhio prima di impegnarsi in AdvisorBoost
- E il primo contatto della tripwire funnel ADVISOR (gratuito o 49 EUR)

**Non attivare** per:
- Analisi di bilancio approfondita → usa `analisi-bilancio-pmi`
- Diagnosi strategica completa → usa `flusso-advisorboost-pmi`
- Salute finanziaria pura (5 KPI) → usa `check-salute-finanziaria` (sovrapposizione parziale: check-pmi-express e piu ampio perche copre anche posizionamento, crescita, dipendenza clienti)

## Input richiesti (8-10 dati)

Minimi (obbligatori):
1. Denominazione azienda (o identificativo)
2. Settore (macro-categoria + sotto-settore)
3. Regione di attivita principale
4. Fatturato ultimo anno (EUR)
5. Utile netto ultimo anno (EUR)
6. PFN (Posizione Finanziaria Netta, EUR)
7. Numero dipendenti
8. Anno fondazione

Facoltativi ma raccomandati:
9. Fatturato anno precedente (per calcolo crescita)
10. 2-3 nomi competitor principali
11. Concentrazione primo cliente (% su fatturato)
12. Dipendenza canale principale (es: digital %, distributori %, diretto %)

Se l'utente non ha PFN: stimala come (Debiti finanziari lordi — Cassa). Se non ha fatturato anno precedente: assume crescita 0% con flag "stimato".

## Workflow in 6 step

### Step 1 — Raccolta input e validazione
Chiedi i 8 dati obbligatori. Se mancano, cerca di stimare solo se il titolare ha dichiarato esplicitamente di non averli. Flagga sempre i dati stimati nel JSON output. Non partire con < 6 dati obbligatori.

### Step 2 — Calcolo KPI derivati
Calcola:
- EBITDA margin stimato (se non fornito): `utile netto × 1.6` come proxy rapido (approssima aggiungendo ammortamenti + imposte + OF)
- PFN/EBITDA stimato
- Margine netto %
- Ricavi per dipendente
- CAGR 1 anno (se fornito anno precedente)
- Eta azienda
- Se concentrazione cliente fornita: flag rischio

### Step 3 — Lookup benchmark
Consulta `references/scoring-model-pmi.md` con settore + fascia dimensionale (micro / piccola bassa / piccola alta / media) per ottenere benchmark mediano e soglie verde/giallo/rosso di ciascuna dimensione.

### Step 4 — Scoring 6 dimensioni
Calcola semaforo per ogni dimensione:
1. **Redditualita**: EBITDA margin + margine netto vs mediana settore
2. **Solidita**: PFN/EBITDA + equilibrio patrimoniale stimato
3. **Liquidita**: proxy current ratio (se disponibile) o giorni medi incasso stimati
4. **Crescita**: CAGR vs trend settore
5. **Posizionamento**: ricavi per dipendente + longevita + presenza competitor
6. **Dipendenza clienti**: concentrazione primo cliente (se fornita, altrimenti semaforo neutro)

Ogni semaforo = verde (3 punti) / giallo (1.5 punti) / rosso (0 punti).

### Step 5 — Calcolo score globale
Score = Σ(punti per dimensione × peso) × normalizzazione a 100.

Pesi:
- Redditualita 25%
- Solidita 20%
- Liquidita 15%
- Crescita 15%
- Posizionamento 15%
- Dipendenza clienti 10%

Se concentrazione cliente non fornita: ribilanciare i pesi altri 5 al 90% + 10% neutro.

### Step 6 — Top 3 criticita prioritarie
Identifica le 3 dimensioni con score piu basso. Per ciascuna:
- Titolo secco ("Margini sotto la mediana del settore", "Indebitamento elevato", ...)
- Sintesi 2-3 righe spiegata in italiano semplice
- Impatto potenziale sulla continuita o sulla crescita
- Azione entro 30 giorni concreta (es: "Chiedi al commercialista un piano di rientro con la banca", "Analizza i 5 clienti che assorbono piu del 50% del fatturato")

## Output deliverable

### HTML single-page (`check-pmi-{slug}-{YYYYMMDD}-pagella.html`)
Vedi `assets/template-semaforo-pmi.md`. Pagina autonoma con:
- Header K2-AI
- Hero: gauge score 0-100 + giudizio + 1 riga sintesi
- 6 card semafori 3x2 grid con valore vs benchmark
- Sezione top 3 criticita espandibili
- CTA: "Vuoi la diagnosi strategica completa? Passa ad AdvisorBoost da 1.999 EUR"
- Footer con disclaimer

### JSON strutturato (`check-pmi-{slug}-{YYYYMMDD}.json`)
Vedi `schemas/output-schema.json`. Conforme a JSON Schema Draft 2020-12.

## Pricing e posizionamento

- **Versione gratuita**: accessibile dal sito k2-ai.it come lead magnet. Tutti i risultati, ma call-to-action obbligatoria verso AdvisorBoost a fondo pagina.
- **Versione 49 EUR**: stessa analisi ma con consegna via email personalizzata e firmata K2-AI, piu 30 minuti di call gratuita di commento.

Il valore per K2-AI non sono i 49 EUR: sono i **lead qualificati** che dopo la pagella chiedono approfondimento. Tasso di conversione target: 8-12% check → AdvisorBoost Light (1.999 EUR).

## Tono di scrittura

- Diretto, senza gergo.
- Numeri sempre con contesto ("il 30% in piu rispetto alla mediana del tuo settore").
- Mai allarmismo gratuito. Mai rassicurazioni vuote.
- Se lo score e rosso, si dice chiaro ma con via d'uscita.
- Se lo score e verde, si celebra ma si sottolineano comunque 2-3 aree di miglioramento.

## Disclaimer standard

Inserire a fondo pagella:

> "Il check PMI express e una valutazione rapida basata su pochi dati dichiarati. Non sostituisce un'analisi di bilancio approfondita ne una diagnosi strategica completa (AdvisorBoost). Le raccomandazioni sono orientative. Per decisioni critiche consulta il tuo commercialista o richiedi ad K2-AI un approfondimento."

## Relazione con altre skill K2-AI

**Tripwire precedente nel funnel**: nessuno — check-pmi-express e il primo contatto ADVISOR.

**Tripwire successivo nel funnel**: `flusso-advisorboost-pmi` (core 1.999-3.999 EUR).

**Skill parallele del verticale**:
- `check-salute-finanziaria` (sovrapposizione 60% — piu focalizzata su 5 KPI finanziari; check-pmi-express estende a posizionamento e crescita)
- `check-competitivo-express` (complementare — focus esclusivo competitivo; check-pmi-express da una vista 360 con una dimensione competitiva)

**Skill tecniche invocate in profondita**: `benchmark-italia-business` per i benchmark settoriali.

## Esempio use-case

Studio di ingegneria TLC con 12 dipendenti, fatturato 950k EUR, utile 85k EUR, PFN 40k EUR, 18 anni di eta, settore servizi professionali. Concentrazione primo cliente: 45% (un operatore TLC).

Risultato atteso: score 62/100 (Sufficiente), semafori gialli su redditualita (margine OK ma non top), solidita (OK), liquidita (OK), crescita (stabile), posizionamento (buono), e rosso su dipendenza clienti (45% > soglia 40%). Top 3 criticita: (1) ridurre dipendenza cliente 1, (2) aumentare margini via pricing, (3) diversificare portafoglio servizi. CTA: "passa a AdvisorBoost per un piano di crescita dettagliato 36 mesi".

## File da generare

1. `check-pmi-{slug}-{YYYYMMDD}-pagella.html`
2. `check-pmi-{slug}-{YYYYMMDD}.json`

Nome slug: prima parola della denominazione azienda, lowercase, senza spazi.
