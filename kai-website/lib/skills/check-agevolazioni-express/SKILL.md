---
name: check-agevolazioni-express
description: >-
  Pagellino agevolazioni rapido per PMI italiane — stima in EUR quanto stai lasciando sul tavolo.
  Lead magnet tripwire verticale AGEVOLAZIONI (gratuito o 49 EUR). Score 0-100 con 5 semafori
  (investimenti agevolabili, de minimis residuo, bandi regionali, bonus assunzioni, tax credit
  innovazione) e top 3 opportunita perse stimate in EUR.
  Trigger: "check agevolazioni", "bandi PMI", "contributi a fondo perduto", "agevolazioni disponibili",
  "finanza agevolata", "quanto posso prendere dallo Stato", "incentivi impresa", "check contributi",
  "tax credit disponibili", "de minimis residuo", "bandi regionali PMI", "agevolazioni non usate".
  Input: settore, regione, dipendenti, fatturato, tipo investimento pianificato, agevolazioni gia usate.
  Output HTML single-page con gauge score, 5 semafori, top 3 opportunita perse in EUR, CTA verso
  flusso-agevolazioni-pmi. Tono concreto con cifre — "stai lasciando X EUR sul tavolo".
  Per titolari PMI italiane, primo check prima del percorso agevolazioni completo 499-1299 EUR.
---








<!-- LEGAL-EVIDENCE-BLOCK-V7 -->
## Tools Normattiva + Giurisprudenza (CCost + CGUE + CEDU + CdS/TAR + Cassazione) — verifica obbligatoria

Hai 5 toolkit locali + 1 lookup live per consulenza legale evidence-based:
- **Normattiva** — ~42.000 norme italiane (DB FTS5)
- **Corte Costituzionale** — 22.258 pronunce + 46.154 massime (1956→2026)
- **Corte di Giustizia UE + Tribunale UE** — ~38.000 cause (2005→2026)
- **Corte EDU (Strasburgo)** — 10.000 casi contro l'Italia (2001→2026), con traduzioni ufficiali Min. Giustizia
- **Giustizia Amministrativa** — Consiglio di Stato + TAR + CGARS (2024→2025, in espansione)
- **Cassazione (LIVE pubblica)** — SentenzeWeb italgiure, accesso pubblico zero-setup (~188k civ + ~236k pen, testo integrale)

### Workflow obbligatorio

**A. Norme italiane**
```bash
python3 ~/normattiva_ai/tools/cita.py "<es. D.Lgs 81/2008>"
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia tributario --limit 5
```

**B. Corte Costituzionale**
```bash
python3 ~/giurisprudenza_ai/tools/cross_norma_sentenza.py "art. 32 Cost." --limit 10
python3 ~/giurisprudenza_ai/tools/rag_giurisprudenza.py "<query>" --anno-da 2018
python3 ~/giurisprudenza_ai/tools/cita_sentenza.py "Corte cost. N/AAAA"
```

**C. CGUE (diritto UE / GDPR / appalti / antitrust / privacy / dogana)**
```bash
python3 ~/cgue_ai/tools/cross_norma_cgue.py "art. 101 TFUE" --limit 10
python3 ~/cgue_ai/tools/cross_norma_cgue.py "Reg. UE 679/2016"        # GDPR
python3 ~/cgue_ai/tools/rag_cgue.py "<query>" --anno-da 2018
python3 ~/cgue_ai/tools/cita_cgue.py "C-16/05"
```

**D. CEDU (diritti fondamentali / equo processo art. 6 / detenzione art. 3 / proprietà P1-1 / vita privata art. 8)**
```bash
python3 ~/cedu_ai/tools/cross_articolo_cedu.py "art. 6" --solo-importanti --limit 10
python3 ~/cedu_ai/tools/rag_cedu.py "<query>" --anno-da 2015
python3 ~/cedu_ai/tools/cita_cedu.py "63386/16"      # numero di ricorso
```

**E. Giustizia Amministrativa — CdS/TAR (appalti, edilizia, accesso atti, SCIA, silenzio, espropri, PA)**
```bash
python3 ~/gad_ai/tools/cross_norma_gad.py "D.Lgs 36/2023" --limit 10   # appalti
python3 ~/gad_ai/tools/cross_norma_gad.py "Legge 241/1990"             # procedimento
python3 ~/gad_ai/tools/rag_gad.py "<query>" --sede cds --anno-da 2024
```

**F. Cassazione (LIVE pubblica — civile/penale, legittimità) — zero setup**
```bash
# Verifica/recupera un precedente di Cassazione (SentenzeWeb pubblico, nessun login)
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023"
python3 ~/cassazione_ai/tools/cassazione_lookup.py --q "licenziamento giusta causa" --sezione civ --rows 5
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023" --full   # testo integrale
python3 ~/cassazione_ai/tools/check_cassazione.py --file <output.md>                        # verifica citazioni
```
Copre la finestra pubblica (~ultimi 5 anni + storico parziale). Se una citazione MANCA può essere fuori finestra; dillo, non inventare la massima.

**G. Verifica finale (prima del deliverable, su ogni file MD prodotto)**
```bash
python3 ~/normattiva_ai/tools/check_citazioni.py --file <output.md> --strict
python3 ~/giurisprudenza_ai/tools/check_sentenze.py --file <output.md> --strict
python3 ~/cgue_ai/tools/check_cgue.py --file <output.md> --strict
python3 ~/cedu_ai/tools/check_cedu.py --file <output.md> --strict
python3 ~/gad_ai/tools/check_gad.py --file <output.md> --strict
```

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/tributario/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Check Agevolazioni Express

Lead magnet tripwire del verticale AGEVOLAZIONI di K2-AI. Il titolare di una PMI italiana inserisce 6-8 dati essenziali sul profilo aziendale e sugli investimenti pianificati e riceve in 5 minuti una pagella visiva con score 0-100, 5 semafori sulle aree agevolative e le top 3 opportunita non sfruttate stimate in EUR. Tono: "Stai lasciando X EUR sul tavolo."

## Quando attivare

Questa skill si attiva quando:
- L'utente chiede "check agevolazioni", "bandi PMI", "contributi disponibili", "finanza agevolata"
- Il titolare vuole un primo colpo d'occhio su quante agevolazioni sta perdendo
- E il primo contatto della tripwire funnel AGEVOLAZIONI (gratuito o 49 EUR) prima di flusso-agevolazioni-pmi

**Non attivare** per:
- Percorso completo di accesso alle agevolazioni → usa `flusso-agevolazioni-pmi`
- Analisi di bilancio → usa `analisi-bilancio-pmi`
- Check strategico-finanziario generale → usa `check-pmi-express`
- Check salute finanziaria pura → usa `check-salute-finanziaria`

## Input richiesti (6-8 dati)

### Obbligatori
1. **Settore** (manifatturiero, commercio, servizi, IT/software, edilizia, agricoltura, ristorazione/turismo, trasporti, altro)
2. **Regione** di attivita principale (es. Lombardia, Campania, Sicilia...)
3. **Numero dipendenti** (fascia: 0-9 micro, 10-49 piccola, 50-249 media)
4. **Fatturato ultimo anno** (EUR)
5. **Tipo di investimento pianificato nei prossimi 12 mesi** (macchinari/impianti, software/digitale, assunzioni, R&S/innovazione, ristrutturazione immobile, nessuno / non so)
6. **Agevolazioni gia usate negli ultimi 3 anni** (de minimis si/no, Sabatini si/no, Industria 4.0/transizione 5.0 si/no, nessuna, non so)

### Facoltativi (migliorano la stima)
7. **Anno fondazione** (o eta azienda) — sblocca incentivi per startup o aziende storiche
8. **Quota export** (% fatturato estero) — sblocca agevolazioni all'internazionalizzazione
9. **De minimis residuo dichiarato** (EUR) — se il titolare lo conosce

Se l'utente non conosce il de minimis residuo: stima massimale disponibile a 200.000 EUR su 3 anni meno una riduzione prudenziale del 40% e flagga come "stimato". Se non conosce i tipi di investimento: chiedi solo la macro-categoria piu probabile.

## Workflow in 6 step

### Step 1 — Raccolta input e validazione
Poni le 6 domande obbligatorie in modo colloquiale, una domanda per messaggio oppure in un blocco ordinato. Se mancano dati critici (settore, regione, dipendenti, fatturato) non procedere. Per gli altri, stima con flag "dato stimato". Accetta anche risposte imprecise ("circa 20 persone", "nord Italia") e trasformale nella fascia piu vicina.

### Step 2 — Profilazione agevolativa
Sulla base degli input costruisci il profilo agevolativo dell'azienda:
- Classificazione dimensionale UE (micro / piccola / media — importante per massimali e regimi)
- Regime de minimis: calcola il massimale residuo stimato (200.000 EUR / 3 anni meno quanto gia usato)
- Area geografica: identifica se cade in zona obiettivo UE (Sud Italia = agevolazioni maggiorate, zone montane, aree di crisi)
- Settori esclusi de minimis: pesca, acquacoltura, agricoltura primaria, trasporto merci per conto terzi (limitazione parziale) — segnala se applicabile

### Step 3 — Lookup agevolazioni per profilo
Consulta la knowledge base interna (o ragiona per categoria) per identificare le agevolazioni potenzialmente accessibili per questo profilo. Per ciascuna delle 5 aree del semaforo, valuta:

**Area 1 — Investimenti agevolabili**
- Credito d'imposta Transizione 5.0 (beni strumentali 4.0 + risparmio energetico): aliquote 35-45% per investimenti in beni materiali/immateriali Industria 5.0
- Sabatini ordinaria: contributo in conto interessi su finanziamenti 20k-4M EUR per macchinari
- Nuova Sabatini Green / Digitale: maggiorazione 30% per investimenti green o digitali
- Credito d'imposta R&S (art. 1 L. 160/2019): 10-20% su spese ricerca e sviluppo
- Contratti di sviluppo (MISE/MIMIT): per investimenti > 1,5 M EUR in produzione/innovazione

**Area 2 — De minimis residuo**
- Calcolo del plafond disponibile nei 3 esercizi (anno corrente + 2 precedenti)
- Stima di quante agevolazioni de minimis regionali potrebbe ancora incassare
- Se < 50k EUR residui: semaforo giallo; se esaurito: semaforo rosso

**Area 3 — Bandi regionali**
- Ogni regione ha bandi POR-FESR / bandi regionali propri: stima in base alla regione dichiarata
- Sud: maggiori opportunita (FESR + fondi nazionali complementari + ZES)
- Nord-Ovest (Piemonte, Lombardia): bandi innovazione e internazionalizzazione
- Nord-Est (Veneto, Emilia): bandi manifatturiero avanzato
- Centro: bandi misti
- Se non ha mai usato bandi regionali: flag opportunita alta

**Area 4 — Bonus assunzioni**
- Decontribuzione assunzioni under 36 (se rinnovata): stima risparmio contributivo
- Decontribuzione assunzioni donne (se attive): 100% contributi fino 18 mesi in zona svantaggiata
- Bonus assunzioni Sud (se applicabile): agevolazioni INPS per nuovi contratti a tempo indeterminato al Sud
- Apprendistato: vantaggi contributivi per fasce d'eta specifiche
- Calcola l'impatto solo se l'investimento pianificato include assunzioni

**Area 5 — Tax credit innovazione**
- Credito d'imposta formazione 4.0: 70% del costo del personale dipendente in formazione su tecnologie Industry 4.0, fino a 300k EUR
- Patent Box: regime agevolato per redditi da brevetti e software originale (aliquota effettiva ridotta)
- Credito d'imposta design e ideazione estetica (per settori moda, arredo, design)
- Credito d'imposta investimenti pubblicitari incrementali (70% su incremento rispetto anno precedente)
- Credito d'imposta sanificazione e sicurezza (se ancora attivo per settore)

### Step 4 — Scoring 5 semafori
Per ogni area assegna un semaforo e un punteggio:

| Semaforo | Condizione | Punti |
|----------|-----------|-------|
| VERDE | L'azienda ha gia sfruttato o non ha opportunita significative residue | 20 |
| GIALLO | Opportunita parzialmente sfruttate o da verificare | 10 |
| ROSSO | Opportunita significative NON sfruttate, stima EUR disponibile | 0 |

**Score globale** = Σ punti / 100 × 100. Piu e basso, piu opportunita stai perdendo.

Fasce score:
- 0-20: CRITICO — stai lasciando decine di migliaia di EUR sul tavolo ogni anno
- 21-40: ALTO RISCHIO — perdite significative gia quantificabili
- 41-60: PARZIALE — stai sfruttando qualcosa ma meta opportunita e persa
- 61-80: DISCRETO — qualche buco da chiudere
- 81-100: OTTIMIZZATO — gia presidio buono (raro per PMI senza consulente dedicato)

### Step 5 — Top 3 opportunita perse stimate in EUR
Identifica le 3 aree con score piu basso (semafori rosso / giallo). Per ciascuna:
- **Titolo** breve e diretto ("Tax credit Transizione 5.0 non attivato", "Bandi regionali POR-FESR ignorati", ...)
- **Stima EUR persa** (range conservativo-ottimistico basato su aliquote e massimali di legge)
- **Perche vale** (2-3 righe in italiano semplice, zero gergo)
- **Scadenza o urgenza** (se c'e una finestra temporale o un bando in scadenza)
- **Azione minima** entro 30 giorni ("Verifica il plafond de minimis con il tuo commercialista", "Scarica il bando regionale dal sito di Regione X", ...)

### Step 6 — Generazione output
Produci HTML single-page + JSON strutturato come descritto nella sezione Output.

## Logica di stima EUR (tabella di riferimento rapida)

| Agevolazione | Stima rapida applicabile |
|-------------|-------------------------|
| Credito imposta Transizione 5.0 beni materiali | 35-45% dell'investimento pianificato (cap 2,5M EUR) |
| Sabatini ordinaria | ~4-6% del valore del finanziamento (cap 200k EUR contributo) |
| Credito imposta R&S | 10-20% spese R&S (stima 5-15% del fatturato se settore tech) |
| Bandi POR-FESR regionali | 20-50% investimento ammissibile (range ampio per tipo bando) |
| Decontribuzione assunzioni | 30-100% contributi datoriali per 12-18 mesi (stima: 6-8k EUR/dipendente) |
| Formazione 4.0 | 50-70% costi formazione (stima: 2-5k EUR/dipendente formato) |
| De minimis vari | Fino a 200k EUR su 3 anni (residuo calcolato step 2) |

Usa sempre range e mai cifre puntuali. Esplicita sempre le assunzioni ("assumendo un investimento di X EUR come dichiarato", "stima conservativa al 35%").

## Output deliverable

### HTML single-page (`check-agev-{slug}-{YYYYMMDD}-pagella.html`)
Pagina autonoma, senza dipendenze esterne, con:

**Struttura layout:**
- **Header K2-AI** con logo testuale e claim "Finanza Agevolata per PMI italiane"
- **Hero section**: gauge circolare score 0-100 + giudizio sintetico (es. "Stai lasciando ~38.000 EUR sul tavolo") + sottotitolo 1 riga
- **5 card semafori** in griglia 2-3 colonne (responsive): ogni card mostra area, semaforo colorato (verde/giallo/rosso), importo stimato opportunita, 1 riga descrizione
- **Sezione Top 3 Opportunita Perse**: 3 card espandibili con titolo, stima EUR evidenziata in grassetto, spiegazione, scadenza/urgenza, azione minima
- **Box urgenza**: se ci sono bandi in scadenza nei prossimi 60 giorni, highlight in arancione
- **CTA principale**: "Vuoi recuperare questi EUR? Attiva flusso-agevolazioni-pmi da 499 EUR" — pulsante primario + spiegazione di cosa include
- **Footer**: disclaimer + data elaborazione + "Powered by K2-AI"

**Stile visivo:**
- Palette: verde #2ECC71 (ok), giallo/arancione #F39C12 (attenzione), rosso #E74C3C (opportunita persa), blu scuro #1A3C5E (header/testo)
- Font system sans-serif, leggibile su mobile
- Score gauge: SVG circle o CSS conic-gradient con numero centrale grande
- Card semafori: bordo sinistro colorato per colore semaforo

### JSON strutturato (`check-agev-{slug}-{YYYYMMDD}.json`)
```json
{
  "skill": "check-agevolazioni-express",
  "version": "1.0",
  "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
  "azienda": {
    "slug": "string",
    "settore": "string",
    "regione": "string",
    "fascia_dimensionale": "micro|piccola|media",
    "fatturato_eur": 0,
    "dipendenti": 0,
    "anno_fondazione": null,
    "export_pct": null
  },
  "investimento_pianificato": {
    "tipo": "string",
    "valore_stimato_eur": null
  },
  "agevolazioni_gia_usate": ["string"],
  "score_globale": 0,
  "fascia_score": "CRITICO|ALTO_RISCHIO|PARZIALE|DISCRETO|OTTIMIZZATO",
  "stima_totale_opportunita_persa_eur": {
    "min": 0,
    "max": 0
  },
  "semafori": [
    {
      "area": "string",
      "colore": "verde|giallo|rosso",
      "punti": 0,
      "opportunita_eur_min": 0,
      "opportunita_eur_max": 0,
      "note": "string",
      "dati_stimati": false
    }
  ],
  "top3_opportunita": [
    {
      "rank": 1,
      "titolo": "string",
      "agevolazione": "string",
      "importo_stimato_min_eur": 0,
      "importo_stimato_max_eur": 0,
      "descrizione": "string",
      "urgenza": "string",
      "azione_30gg": "string",
      "dati_stimati": false
    }
  ],
  "disclaimer": "string",
  "next_step": "flusso-agevolazioni-pmi"
}
```

## Naming convention file

- Slug: prima parola della denominazione azienda, lowercase, senza spazi (es. "rossi" per "Rossi Srl")
- Se non fornita la denominazione: usa il settore + regione abbreviata (es. "manifatt-lom")
- Esempio: `check-agev-rossi-20260424-pagella.html` e `check-agev-rossi-20260424.json`

## Pricing e posizionamento

- **Versione gratuita**: accessibile come lead magnet dal sito k2-ai.it. Tutti i risultati inclusi, CTA obbligatoria verso flusso-agevolazioni-pmi a fondo pagina.
- **Versione 49 EUR**: stessa analisi con consegna via email personalizzata e firmata K2-AI, piu 30 minuti di call gratuita di commento con un consulente K2-AI.

Il valore per K2-AI non sono i 49 EUR: sono i **lead qualificati** che dopo la pagella vogliono il percorso completo. Tasso di conversione target: 10-15% check → flusso-agevolazioni-pmi (499-1299 EUR).

## Tono di scrittura

- **Concreto con cifre**: sempre "stai lasciando circa 35.000-60.000 EUR sul tavolo", mai "potresti beneficiare di agevolazioni significative"
- **Urgenza reale**: se ci sono scadenze, citarle. Se un de minimis sta per scadere, dirlo.
- **Zero gergo burocratico**: "credito d'imposta" diventa "lo Stato ti rimborsa X% dell'investimento direttamente sulle tasse", "de minimis" diventa "il massimale di aiuti che puoi ricevere in 3 anni senza notifica UE"
- **Mai promesse impossibili**: i numeri sono stime, non garanzie. Esplicita sempre le ipotesi.
- **Azione concreta**: ogni opportunita persa finisce con qualcosa di fattibile entro 30 giorni.

## Regole critiche di compliance

1. **Non garantire mai l'accesso** a un'agevolazione: le cifre sono stime basate su aliquote di legge, non sull'esito effettivo della domanda.
2. **De minimis**: segnalare sempre che il plafond va verificato nel Registro Nazionale Aiuti (RNA) con il commercialista.
3. **Bandi regionali**: i bandi aprono e chiudono — raccomandare sempre di verificare sul sito ufficiale della Regione o su bandi.governo.it.
4. **Cumulabilita**: alcune agevolazioni sono cumulabili, altre no — non affermare mai che lo siano senza segnalare il limite.
5. **Dati stimati**: flaggare sempre nel JSON e nella pagella ogni dato non dichiarato esplicitamente dall'utente.

## Disclaimer standard

Inserire a fondo pagella:

> "Il Check Agevolazioni Express e una stima rapida basata su dati dichiarati e aliquote di legge aggiornate. Non costituisce consulenza fiscale ne garantisce l'accesso alle agevolazioni indicate. I massimali de minimis vanno verificati nel Registro Nazionale Aiuti. I bandi regionali hanno scadenze variabili: verifica sempre sul sito ufficiale della Regione. Per il percorso completo di accesso alle agevolazioni rivolgiti al tuo commercialista o attiva flusso-agevolazioni-pmi con K2-AI."

## Relazione con altre skill K2-AI

**Tripwire precedente nel funnel**: nessuno — check-agevolazioni-express e il primo contatto AGEVOLAZIONI.

**Tripwire successivo nel funnel**: `flusso-agevolazioni-pmi` (core 499-1299 EUR) — percorso completo di identificazione bandi, predisposizione domande, monitoraggio scadenze.

**Skill parallele del verticale**:
- `check-pmi-express` (complementare — check strategico-finanziario; check-agevolazioni-express si focalizza esclusivamente sulle opportunita di finanza agevolata)
- `check-salute-finanziaria` (complementare — fotografia KPI bilancio; non copre agevolazioni)
- `analisi-bilancio-pmi` (approfondimento downstream — spesso utile prima di attivare bandi che richiedono bilanci certificati)

**Skill tecniche invocate in profondita**:
- `benchmark-italia-business`: per confrontare il profilo dimensionale/settoriale con le soglie di accesso alle agevolazioni
- `flusso-agevolazioni-pmi`: lo step successivo naturale dopo questo check

## Esempio use-case

**Scenario**: Piccola impresa manifatturiera metalmeccanica, Campania, 22 dipendenti, fatturato 1,8M EUR, sta pianificando l'acquisto di un tornio CNC da 180k EUR e 2 nuove assunzioni, mai usato Industria 4.0 ne agevolazioni regionali, de minimis non noto.

**Risultato atteso**:
- Score: 12/100 — fascia CRITICO
- Stima opportunita persa totale: 68.000-105.000 EUR
- Semafori: rosso su investimenti agevolabili (Transizione 5.0 non attivato sul tornio CNC, stima 63.000-81.000 EUR), rosso su bandi regionali (Campania ZES e POR-FESR, stima 20.000-40.000 EUR), giallo su de minimis residuo (presunto pieno, non verificato), giallo su bonus assunzioni (decontribuzione Sud disponibile), verde su tax credit innovazione (non applicabile per mancanza R&S dichiarata)
- Top 3 opportunita perse: (1) Transizione 5.0 sul tornio CNC — credito imposta 35-45% = 63.000-81.000 EUR non richiesti; (2) Bando ZES Campania per investimenti produttivi — contributo a fondo perduto fino 40%; (3) Decontribuzione assunzioni Sud — risparmio ~12.000-14.000 EUR in 18 mesi per 2 assunzioni
- CTA: "Questi 68.000-105.000 EUR sono ancora recuperabili. Attiva flusso-agevolazioni-pmi per predisporre le domande in tempo."

## File da generare

1. `check-agev-{slug}-{YYYYMMDD}-pagella.html`
2. `check-agev-{slug}-{YYYYMMDD}.json`

Nome slug: prima parola della denominazione azienda, lowercase, senza spazi. Se denominazione non fornita: `{settore-abbreviato}-{regione-abbreviata}`.
