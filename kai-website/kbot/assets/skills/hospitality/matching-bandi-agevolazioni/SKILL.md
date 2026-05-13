---
name: matching-bandi-agevolazioni
description: >-
  Matching preciso tra profilo aziendale PMI e strumenti di finanza agevolata
  italiani — nazionali e regionali. Riceve in input il profilo aziendale
  (codice ATECO, dimensione UE, regione, forma giuridica), la lista degli
  investimenti pianificati (tipo e importo) e le agevolazioni gia usate (per
  calcolo de minimis residuo). Filtra la matrice strumenti nazionali, esegue
  WebSearch per bandi FESR/FSE regionali attivi, verifica requisiti base per
  ogni strumento candidato, assegna uno score priorita 1-5 su tre assi
  (valore economico, accessibilita, urgenza). Produce shortlist ordinata con
  nome strumento, tipo agevolazione, stato apertura, beneficio potenziale
  stimato, urgenza e link fonte. Output duplice — JSON strutturato e tabella
  markdown leggibile. Usabile standalone o come Step 2 di flusso-agevolazioni-pmi.
  Attiva per "quali bandi posso usare", "matching agevolazioni", "incentivi per
  il mio investimento", "bandi regionali aperti", "shortlist agevolazioni PMI".
---

# matching-bandi-agevolazioni — Matching Strumenti di Finanza Agevolata per PMI

Skill foglia di matching tra il profilo aziendale di una PMI italiana e il catalogo degli strumenti di finanza agevolata nazionali e regionali attivi. Produce una shortlist ordinata per priorita, pronta per essere lavorata dall'orchestratore `flusso-agevolazioni-pmi` o restituita direttamente al cliente.

---

## Contesto di utilizzo

Questa skill puo essere invocata in due modalita:

- **Modalita orchestrata**: chiamata dallo Step 2 di `flusso-agevolazioni-pmi`, riceve il `profilo-aziendale-agevolativo.json` prodotto dallo Step 1 e restituisce `shortlist-strumenti.json`.
- **Modalita standalone**: invocata direttamente dall'utente con dati aziendali forniti in forma libera. In questo caso la skill raccoglie autonomamente gli input necessari prima di procedere.

---

## Trigger

Attiva questa skill quando l'utente menziona:
- "quali bandi posso usare", "che agevolazioni ho disponibili", "matching agevolazioni"
- "incentivi per il mio investimento", "quali contributi posso prendere"
- "bandi regionali aperti", "fondi FESR per PMI", "shortlist agevolazioni"
- "fammi una lista di incentivi", "scansiona i bandi disponibili"
- Oppure quando l'orchestratore `flusso-agevolazioni-pmi` invoca questo modulo allo Step 2.

---

## Input richiesti

### Se invocata in modalita standalone

Raccogli dall'utente le seguenti informazioni, in forma conversazionale:

1. **Codice ATECO** — attivita principale dell'azienda (es. 28.41 — Fabbricazione di macchine utensili). Se l'utente non lo conosce, aiutalo a identificarlo dalla descrizione dell'attivita.
2. **Dimensione aziendale** — numero di dipendenti, fatturato annuo, totale attivo. Serve per classificare micro/piccola/media impresa ai sensi della Raccomandazione UE 2003/361/CE.
3. **Regione di localizzazione** — dove ha sede l'azienda (es. Lombardia, Campania). Determina l'accesso a bandi regionali e intensita di aiuto ZES/Mezzogiorno.
4. **Forma giuridica** — SRL, SPA, SNC, SAS, ditta individuale, cooperativa, societa di persone. Alcuni strumenti escludono determinate forme.
5. **Investimenti pianificati** — elenco tipologie di investimento con importo stimato. Esempi: macchinari 4.0 (150.000 EUR), software gestionale (30.000 EUR), assunzione tecnico specializzato, export in Germania, brevettazione invenzione. Piu e specifico, piu preciso e il matching.
6. **Agevolazioni gia usate** — contributi a fondo perduto, crediti d'imposta, garanzie MCC ricevuti negli ultimi 3 esercizi finanziari. Necessari per il calcolo del de minimis residuo (soglia generale 300.000 EUR triennale).

Se l'utente non fornisce tutti i dati: *"Per fare un matching preciso mi servono almeno: regione, numero dipendenti e tipo di investimento pianificato. Con questi tre dati posso gia costruire una shortlist significativa."*

### Se invocata dall'orchestratore

Riceve direttamente il JSON `profilo-aziendale-agevolativo.json` con i campi:
```json
{
  "ateco_codice": "...",
  "ateco_descrizione": "...",
  "dimensione_ue": "micro | piccola | media",
  "dipendenti": 0,
  "fatturato_eur": 0,
  "regione": "...",
  "zona_geografica": "Nord | Centro | Sud | ZES",
  "forma_giuridica": "...",
  "startup_innovativa": false,
  "pmi_innovativa": false,
  "difficolta_finanziaria": false,
  "de_minimis_residuo_eur": 0,
  "investimenti": [
    {"tipo": "...", "importo_eur": 0, "timing_mesi": 0}
  ],
  "agevolazioni_usate": [
    {"strumento": "...", "anno": 0, "importo_eur": 0}
  ]
}
```

---

## Workflow — 4 Step

### Step 1 — Filtro matrice strumenti nazionali

Scansiona la matrice degli strumenti nazionali sotto elencata e applica i filtri di esclusione:

**Filtri di esclusione primari** (escludono definitivamente lo strumento):
- **Settore escluso**: alcuni strumenti escludono i settori agricoltura, pesca, trasporti, carbon fossile, siderurgia (verifica per ciascuno secondo il regolamento di riferimento).
- **Dimensione non compatibile**: es. Contratti di Sviluppo richiedono investimento minimo 1,5M EUR — escludi se gli investimenti dichiarati sono inferiori.
- **Forma giuridica non ammessa**: es. alcune misure UIBM (Brevetti+, Marchi+, Design+) richiedono imprese costituite in forma societaria; verificare se la ditta individuale e ammessa nello specifico bando.
- **Difficolta finanziaria**: se `difficolta_finanziaria = true`, escludere tutti gli strumenti GBER (art. 2 par. 18 Reg. UE 651/2014) e i contributi PNRR.
- **De minimis esaurito**: se `de_minimis_residuo_eur = 0` o insufficiente per lo strumento, escludere gli strumenti de minimis.

**Filtri di rilevanza** (includono solo se il tipo investimento e compatibile):
- **Tipo investimento**: confronta ciascun investimento dichiarato con le spese ammissibili dello strumento. Un macchinario non 4.0 non e ammissibile a Transizione 5.0; una spesa in brevettazione non attiva la Sabatini.
- **Soglia minima investimento**: escludi se l'importo pianificato e inferiore alla soglia minima del bando.
- **Geografico**: ZES Unica Mezzogiorno solo per aziende con sede/investimento nelle regioni del Mezzogiorno (Abruzzo, Molise, Campania, Puglia, Basilicata, Calabria, Sicilia, Sardegna). Sabatini Sud solo per le stesse zone.

Dopo il filtro, ottieni la lista degli **strumenti candidati nazionali**.

---

### Step 2 — WebSearch bandi regionali attivi

Per la regione specificata nel profilo, esegui ricerche mirate per identificare bandi FESR/FSE+ regionali aperti o in prossima apertura.

**Query di ricerca da eseguire** (adatta alla regione e al tipo di investimento):

```
"bando FESR [REGIONE] 2025 PMI investimenti sito:regione.[SLUG].it"
"bando [REGIONE] 2025 contributo fondo perduto imprese"
"POR FESR [REGIONE] 2021-2027 bando aperto [tipo investimento]"
"incentivi regionali [REGIONE] 2025 innovazione digitalizzazione"
```

Per ciascun bando regionale trovato, verifica e annota:
- **Nome bando e asse POR/PR** di riferimento.
- **Stato** — aperto / chiuso / in attesa di pubblicazione (con data prevista se nota).
- **Dotazione e plafond residuo** (se disponibile sul sito della regione o su opencoesione.gov.it).
- **Spese ammissibili** — compatibili con gli investimenti dichiarati?
- **Intensita di aiuto** — percentuale grant/credito applicabile alla dimensione aziendale.
- **Scadenza domanda** — data entro cui presentare.
- **Link fonte** — URL ufficiale del bando o dell'avviso.

Annotare sempre la **data di verifica** accanto a ogni bando regionale. La finanza agevolata regionale e soggetta a chiusure rapide.

---

### Step 3 — Verifica requisiti base e scoring priorita

Per ogni strumento candidato (nazionali filtrati + regionali trovati), esegui una verifica rapida dei requisiti principali e assegna uno **score di priorita da 1 a 5** su tre assi.

#### Verifica requisiti base (flag SI/NO/INCERTO)

| Requisito | Verifica |
|---|---|
| Settore ATECO ammesso | SI / NO / INCERTO (richiedere verifica) |
| Dimensione aziendale nei parametri | SI / NO |
| Tipo investimento nelle spese ammissibili | SI / NO / PARZIALE |
| Finestra temporale aperta o futura | APERTO / CHIUSO / IN ATTESA |
| De minimis capiente (se applicabile) | SI / NO / INCERTO |
| Forma giuridica ammessa | SI / NO |
| Azienda non in difficolta finanziaria (se richiesto) | SI / NO |

Escludi dalla shortlist finale tutti gli strumenti con almeno un flag NO certo. Mantieni gli INCERTO segnalando la condizione da verificare.

#### Scoring priorita (1-5 per asse, poi media ponderata)

**Asse 1 — Valore economico** (peso 40%)
Stima il beneficio lordo atteso in EUR basandoti su:
- Importo investimento dichiarato x aliquota agevolazione applicabile alla dimensione aziendale.
- Per i tax credit: importo compensabile in F24.
- Per i grant: importo a fondo perduto stimato.
- Per le garanzie: risparmio interessi stimato su mutuo equivalente.

Score:
- 5 — beneficio stimato > 100.000 EUR
- 4 — beneficio stimato 50.000-100.000 EUR
- 3 — beneficio stimato 20.000-50.000 EUR
- 2 — beneficio stimato 5.000-20.000 EUR
- 1 — beneficio stimato < 5.000 EUR o non quantificabile

**Asse 2 — Accessibilita** (peso 35%)
Valuta quanto e facile accedere allo strumento per questa specifica azienda:

Score:
- 5 — Automatico, nessuna domanda preventiva, requisiti semplici (es. credito d'imposta formazione 4.0 se attivita formative documentate)
- 4 — Sportello automatico con procedura semplice (es. Nuova Sabatini tramite banca convenzionata)
- 3 — Domanda a sportello con documentazione tecnica media (es. Fondo di Garanzia MCC)
- 2 — Bando competitivo con documentazione articolata o perizia tecnica richiesta (es. Transizione 5.0 con certificazione energetica)
- 1 — Procedura negoziale complessa, soglie alte, tempi lunghi (es. Contratti di Sviluppo)

**Asse 3 — Urgenza** (peso 25%)
Valuta la pressione temporale:

Score:
- 5 — Scadenza entro 30 giorni o dotazione quasi esaurita
- 4 — Scadenza entro 60-90 giorni
- 3 — Scadenza entro 6 mesi o finestra rolling con chiusura imprevedibile
- 2 — Strumento aperto stabilmente, scadenza oltre 6 mesi
- 1 — Strumento in attesa di apertura, nessuna scadenza immediata

**Score finale di priorita** = (Valore x 0,40) + (Accessibilita x 0,35) + (Urgenza x 0,25), arrotondato al primo decimale.

---

### Step 4 — Composizione output

Produci i due output finali: JSON strutturato e tabella markdown.

#### Output 1 — JSON strutturato (`shortlist-strumenti.json`)

```json
{
  "data_verifica": "YYYY-MM-DD",
  "profilo_input": {
    "ateco": "...",
    "dimensione": "...",
    "regione": "...",
    "forma_giuridica": "...",
    "de_minimis_residuo_eur": 0
  },
  "shortlist": [
    {
      "rank": 1,
      "nome": "...",
      "tipo_agevolazione": "tax_credit | grant | finanziamento_agevolato | garanzia | bonus_assunzioni | equity",
      "ambito": "nazionale | regionale",
      "stato": "aperto | chiuso | in_attesa",
      "scadenza": "YYYY-MM-DD o null",
      "investimento_agevolabile_eur": 0,
      "aliquota_pct": 0,
      "beneficio_lordo_stimato_eur": 0,
      "score_valore": 0,
      "score_accessibilita": 0,
      "score_urgenza": 0,
      "score_priorita": 0.0,
      "requisiti_critici_da_verificare": ["..."],
      "azione_immediata": "...",
      "link_fonte": "...",
      "note": "..."
    }
  ],
  "strumenti_esclusi": [
    {
      "nome": "...",
      "motivo_esclusione": "..."
    }
  ],
  "avvertenze": [
    "Dato aggiornato al YYYY-MM-DD. Verificare sempre sul sito ufficiale prima di presentare domanda.",
    "..."
  ]
}
```

#### Output 2 — Tabella markdown leggibile

Presenta la shortlist in formato tabella ordinata per score decrescente, seguita da una sezione di avvertenze operative.

**Formato tabella:**

```
## Shortlist Agevolazioni — [Nome Azienda / Settore] — Verifica del [DATA]

| # | Strumento | Tipo | Stato | Beneficio Stimato | Score | Urgenza | Link |
|---|---|---|---|---|---|---|---|
| 1 | ... | Tax credit | Aperto | ~87.500 EUR | 4.2/5 | Alta (scadenza 30/06) | [Fonte](url) |
| 2 | ... | Grant | Aperto | ~25.000 EUR | 3.8/5 | Media | [Fonte](url) |
...

### Azioni immediate
- **Entro 7 giorni**: [strumento urgente] — [cosa fare]
- **Entro 30 giorni**: [strumento con scadenza] — [cosa fare]

### Strumenti esclusi
- **[Nome]**: escluso per [motivo conciso]

### Avvertenze
> Dati verificati il [DATA]. La finanza agevolata e soggetta a variazioni frequenti — verificare sempre lo stato del bando sul sito ufficiale prima di presentare domanda. I benefici indicati sono stime basate sugli importi di investimento dichiarati e sulle aliquote vigenti alla data di verifica. Il beneficio effettivo dipende dalla corretta predisposizione della documentazione tecnica e dal superamento dell'istruttoria.
```

---

## Matrice strumenti nazionali di riferimento

Questa e la matrice base da scansionare ad ogni esecuzione. Le aliquote si intendono per "piccola impresa" ai sensi UE; per le medie imprese si applicano riduzioni standard (-10 pp per la maggior parte degli strumenti GBER).

| Strumento | Tipo | Spese ammissibili | Aliquota piccola | Soglia min | Regime | Riferimento normativo |
|---|---|---|---|---|---|---|
| Transizione 5.0 | Tax credit | Beni strumentali 4.0 + risparmio energetico >= 3% | 35%-45% (fascia investimento e risparmio energetico) | Nessuna | Non de minimis (GBER art. 38bis) | D.L. 19/2024, D.M. attuativo |
| Credito d'imposta R&S | Tax credit | Ricerca fondamentale, ricerca industriale, sviluppo sperimentale | 20% (costi personale, contratti, materiali) | Nessuna | Non de minimis | L. 160/2019 art. 1 cc. 198-209 |
| Credito d'imposta Innovazione tecnologica | Tax credit | Innovazione di prodotto/processo non R&S | 10% (standard), 15% (transizione digitale/ecologica) | Nessuna | Non de minimis | L. 160/2019 art. 1 cc. 198-209 |
| Credito d'imposta Design e ideazione estetica | Tax credit | Design, ideazione estetica settori moda, calzaturiero, occhialeria, oreficeria, ceramica, arredo | 10% | Nessuna | Non de minimis | L. 160/2019 art. 1 cc. 198-209 |
| Credito d'imposta Formazione 4.0 | Tax credit | Formazione su tecnologie 4.0 (elenco allegato L. 205/2017) | 70% (piccola), 50% (media) | Nessuna | Non de minimis | L. 205/2017 art. 1 cc. 46-56 |
| Nuova Sabatini ordinaria | Contributo su interessi + garanzia MCC | Beni strumentali, software, hardware, impianti | Contributo su interessi (tasso agevolato 2,75%) | 20.000 EUR | De minimis | L. 134/2012 art. 2 |
| Nuova Sabatini Green | Contributo su interessi maggiorato | Beni a ridotto impatto ambientale, efficienza energetica | Tasso agevolato 3,575% | 20.000 EUR | De minimis | L. 134/2012 + D.M. 06/03/2017 |
| Nuova Sabatini Sud | Contributo a fondo perduto | Beni strumentali per aziende Mezzogiorno | Contributo diretto maggiorato | 20.000 EUR | De minimis | L. 134/2012 + misure Sud |
| Fondo di Garanzia MCC | Garanzia pubblica | Qualsiasi investimento produttivo o liquidita | Garanzia fino all'80% del finanziamento | Nessuna | De minimis o GBER a seconda dello strumento | L. 662/1996 art. 2 co. 100 |
| SIMEST Fondo 394 — export | Finanziamento agevolato | Partecipazione fiere, e-commerce, studi di fattibilita, apertura strutture estere | Tasso agevolato (attualmente 0% o vicino) | 25.000 EUR | De minimis | D.Lgs. 143/1998 |
| Contratti di Sviluppo (Invitalia) | Grant + finanziamento agevolato | Investimenti produttivi, ambientali, R&S, tutela occupazionale | Fino al 45% grant | 1.500.000 EUR (minimo progetto) | GBER | D.M. 09/12/2014 |
| Brevetti+ (UIBM) | Grant | Servizi di consulenza per valorizzazione brevetti | 80% costi, max 140.000 EUR | Nessuna | De minimis | D.M. MISE 19/03/2018 |
| Marchi+ (UIBM) | Grant | Registrazione marchi UE e internazionali | 80% costi, max 50.000 EUR | Nessuna | De minimis | D.M. MISE 19/03/2018 |
| Design+ (UIBM) | Grant | Consulenza e protezione design industriale | 80% costi, max 100.000 EUR | Nessuna | De minimis | D.M. MISE 19/03/2018 |
| ZES Unica Mezzogiorno | Tax credit | Acquisto beni strumentali nuovi in ZES | 15%-50% (varia per zona e dimensione) | Nessuna (soglia min 100 EUR) | GBER | Art. 16 D.L. 124/2023 |
| Patent Box | Esenzione IRES/IRPEF | Redditi da sfruttamento IP (brevetti, software, know-how, disegni) | 50% escluso da tassazione | Nessuna | Aiuto di Stato compatibile | Art. 6 D.L. 146/2021 |
| Bonus assunzioni under 36 | Decontribuzione | Assunzioni a tempo indeterminato under 36 primo impiego | Esonero contributivo fino a 3 anni (max 8.000 EUR/anno per dipendente) | Nessuna | De minimis | L. 234/2021 + rinnovi annuali |
| Bonus assunzioni donne | Decontribuzione | Assunzioni donne in condizioni di svantaggio | Esonero contributivo 12 mesi (prorogabile) | Nessuna | De minimis | L. 92/2012 + rinnovi |
| Bonus assunzioni Mezzogiorno | Decontribuzione | Assunzioni in regioni Sud (Decontribuzione Sud) | Riduzione contributi 30% | Nessuna | De minimis | L. 178/2020 (verificare stato proroga) |

> **Nota**: le aliquote e le condizioni indicate sono quelle vigenti al momento della redazione di questa skill. Verificare sempre la normativa aggiornata e i decreti attuativi prima di comunicare i valori al cliente. Per Transizione 5.0 in particolare, le aliquote variano in funzione della fascia di investimento (< 2,5M / 2,5-10M / > 10M EUR) e del risparmio energetico conseguito (3-6% / 6-10% / > 10%).

---

## Regole operative

1. **Data di verifica obbligatoria**: ogni output deve riportare la data in cui e stata eseguita la verifica. I bandi regionali cambiano frequentemente — segnalare sempre che i dati devono essere riconfermati prima di presentare domanda.

2. **Mai promettere importi certi**: i benefici sono sempre "stimati" e "potenziali". Il beneficio effettivo dipende dalla corretta predisposizione della documentazione tecnica, dall'istruttoria dell'ente erogatore, e per i bandi competitivi dalla disponibilita del plafond.

3. **Strumenti esclusi: sempre documentati**: non eliminare silenziosamente uno strumento. Ogni esclusione deve essere tracciata nel campo `strumenti_esclusi` con il motivo. Serve per trasparenza e per riabilitare lo strumento se cambiano le condizioni.

4. **De minimis: calcolare prima di includere**: non includere strumenti de minimis se il residuo e insufficiente. Calcolare: residuo disponibile = 300.000 EUR - somma aiuti de minimis ricevuti negli ultimi 3 esercizi.

5. **Cumulabilita: segnalare, non risolvere**: questa skill non effettua la verifica completa di cumulabilita (e compito dello Step 3 dell'orchestratore). Se due strumenti sulla stessa spesa presentano potenziale incompatibilita (es. Transizione 5.0 + bando regionale stesso investimento), segnalarlo nel campo `note` con flag `VERIFICARE_CUMULABILITA`.

6. **Bandi regionali senza URL: non includere**: se la WebSearch non produce un link ufficiale verificabile, non includere il bando nella shortlist. Meglio una lista piu corta e affidabile.

7. **INCERTO non e NO**: i requisiti segnati come INCERTO non escludono lo strumento, ma richiedono un'avvertenza esplicita nel campo `requisiti_critici_da_verificare`. Il cliente deve sapere cosa deve ancora essere verificato.

---

## Output verso orchestratore

Quando invocata dall'orchestratore `flusso-agevolazioni-pmi`, questa skill restituisce:
- **File**: `shortlist-strumenti.json` — input per lo Step 3 (verifica approfondita requisiti e scoring).
- **Segnale di stato**: numero di strumenti in shortlist, numero di strumenti esclusi, presenza di bandi regionali aperti con scadenza imminente (flag urgenza).

Se la shortlist e vuota (nessuno strumento supera i filtri), restituire messaggio esplicito con i motivi principali di esclusione — es. difficolta finanziaria che blocca tutti gli strumenti GBER, de minimis esaurito, investimenti sotto soglia minima.

---

## Skill correlate

- **`flusso-agevolazioni-pmi`** — orchestratore padre che invoca questa skill allo Step 2. Riceve la shortlist e procede con la verifica approfondita (Step 3) e la stima dei benefici (Step 4).
- **`fiscale-tributario-italiano`** — per il dettaglio fiscale dei crediti d'imposta (modalita di utilizzo in compensazione F24, periodo di utilizzo, UNICO/770).
- **`diritto-italiano`** — per i profili normativi degli strumenti piu complessi (Contratti di Sviluppo, Patent Box, regime de minimis UE).
- **`consulente-pa-operativa`** — per la gestione delle procedure amministrative con gli enti erogatori (Invitalia, MCC, SIMEST, Regioni).

---

## Tono e stile

- **Preciso e verificabile**: ogni affermazione deve poter essere ricondotta a un riferimento normativo o a un link ufficiale. Mai dati senza fonte.
- **Orientato all'azione**: la shortlist non e un catalogo teorico — ogni strumento deve avere un'azione immediata associata ("richiedere preventivo alla banca convenzionata", "contattare lo sportello Invitalia", "avviare perizia tecnica").
- **Onesto sulle incertezze**: se un dato non e verificabile via WebSearch, dirlo esplicitamente. Meglio "non trovato, verificare sul sito regionale" che un'informazione non aggiornata.
- **Numeri sempre**: un beneficio senza EUR stimati non serve al titolare di PMI. Se non e possibile stimare, indicare il range di aliquota e dire al cliente di fornire l'importo esatto dell'investimento per quantificare.
