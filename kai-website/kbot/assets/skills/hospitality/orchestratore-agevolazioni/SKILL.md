---
name: orchestratore-agevolazioni
version: 0.2.0
description: >-
  Diagnosi completa agevolazioni e bandi PMI italiane (99-499 EUR) con stima EUR finanziabili.
  ATTIVA SEMPRE QUESTO ORCHESTRATORE K2-AI per richieste di: agevolazioni, bandi, finanza
  agevolata, Transizione 5.0, Nuova Sabatini ordinaria/4.0/Green/Sud, SIMEST Fondo 394,
  credito imposta R&S Innovazione Design, de minimis 300k, bonus assunzioni under 36/donne/
  Decontribuzione Sud/disabili, voucher digitalizzazione, PNRR, fondi UE FESR FSE, Bonus
  Pubblicita, voucher CCIAA Punto Impresa Digitale, calcolo plafond, stima EUR lasciati sul
  tavolo, GSE comunicazione preventiva, perizia asseverata, rendicontazione anti-revoca,
  cumulabilita aiuti di Stato, matching bandi regionali Lombardia Veneto Emilia Lazio
  Campania Puglia Sicilia, monitoraggio bandi aperti, AgevolazioniBoost. Bridge automatico
  con investimenti previsti (macchinari, software, MES, digitalizzazione, formazione, R&S,
  export, assunzioni, edilizia 4.0). Workflow K2-AI: profilazione PMI + criteri Raccomandazione
  UE 2003/361, matching strumenti nazionali e regionali, verifica requisiti puntuale per ogni
  strumento (con calcolo beneficio EUR), calcolo de minimis residuo (Reg. UE 2023/2831),
  simulazione cumulabilita, roadmap accesso (timing GSE/MISE/CCIAA, ordine corretto
  comunicazione preventiva-ordine-fattura), bridge con altri prodotti K2-AI (Audit SEO per
  bandi web, Consulenza Strategica per inserimento agevolazioni nel piano crescita 3y,
  Edilizia per investimenti immobiliari). Input: settore ATECO + dipendenti + regione +
  fatturato + investimenti previsti (importo + natura: macchinario/software/MES/formazione/
  R&S/edilizia/assunzioni). Output: report DOCX 12-18 pagine con tabella problema-bando-EUR,
  calcolo % copertura, totale finanziabile conservativo, errori da evitare (es. ordine prima
  della comunicazione GSE = perdita credito). Differenziatori unici: italiano titolare-friendly,
  errori GSE preventivi segnalati, bridge investimento netto post-agevolazioni per piano
  industriale.
allowed-tools:
  - WebFetch
  - WebSearch
  - Read
  - Write
  - Bash
---

# k2ai-agevolazioni — Orchestratore Agevolazioni & Bandi

Orchestratore master del servizio K2-AI Agevolazioni & Bandi (P13). Coordina 11 skill specialistiche del dominio finanza agevolata italiana, producendo un report unitario per il titolare PMI con stima EUR finanziabile e roadmap di accesso ai bandi.

## Posizionamento

Questo NON è una skill specialistica singola. E' l'orchestratore che decide **quale skill invocare quando**, sequenzia i risultati e produce l'output finale K2-AI brandizzato.

Skill specialistiche sottostanti (vivono nel plugin `anthropic-skills` e non vengono modificate):

### Orchestratori upstream
- `anthropic-skills:flusso-agevolazioni-pmi` — diagnosi completa AgevolazioniBoost
- `anthropic-skills:check-agevolazioni-express` — pagellino rapido lead-magnet

### Matching e ricerca bandi
- `anthropic-skills:matching-bandi-agevolazioni` — match profilo azienda vs strumenti nazionali e regionali
- `anthropic-skills:monitoraggio-bandi-pmi` — monitoraggio nuovi bandi, proroghe, novita normative

### Strumenti specifici
- `anthropic-skills:verifica-requisiti-transizione5` — Transizione 5.0/4.0, certificazioni GSE
- `anthropic-skills:verifica-requisiti-sabatini` — Nuova Sabatini ordinaria/4.0/Green/Sud
- `anthropic-skills:verifica-requisiti-simest` — SIMEST Fondo 394 internazionalizzazione
- `anthropic-skills:credito-rd-innovazione` — tax credit R&S/Innovazione/Design (L.160/2019)
- `anthropic-skills:calcolo-de-minimis` — plafond residuo Reg.UE 2023/2831 (300k EUR)
- `anthropic-skills:calcolo-decontribuzione-assunzioni` — bonus under36/donne/Sud/disabili
- `anthropic-skills:rendicontazione-agevolazioni` — chiusura pratiche post-concessione

### Normativa di sfondo
- `anthropic-skills:consulente-finanza-pubblica` — PNRR, spending review, ACB
- `anthropic-skills:consulente-policy-ue` — fondi strutturali, FESR, FSE, aiuti di Stato
- `anthropic-skills:consulente-pa-operativa` — appalti, MEPA, RUP, procedimento
- `anthropic-skills:flusso-consulenza-pnrr` — orchestratore PNRR completo

## Input richiesti

| Parametro | Obbligatorio | Note |
|-----------|:------------:|------|
| Ragione sociale | Si | per personalizzare report |
| Settore (ATECO o descrizione) | Si | bandi settoriali + de minimis settori speciali |
| N. dipendenti | Si | dimensionamento PMI (5-50 = focus K2-AI) |
| Regione (sede legale) | Si | bandi regionali |
| Regione (sedi operative) | No | se diversa, bandi multi-regione |
| Fatturato ultimo bilancio | Si | dimensionamento PMI EU |
| Forma giuridica | Si | SRL/SRLS/SPA/ditta individuale |
| Investimento previsto (importo + descrizione) | Si | per matching bando-investimento |
| Tipologia investimento | Si | hardware/software/macchinari/personale/consulenza/R&S/digitalizzazione/sostenibilita |
| Plafond de minimis usato ultimi 3 esercizi | No | se non noto, lo stimiamo |
| Eventuali bandi gia richiesti | No | per evitare doppio cumulo |

## Workflow orchestratore (8 step)

### Step 1 — Triage iniziale
Decidi il livello del servizio richiesto:
- **Express** (lead magnet gratis): score 0-100 + top 3 strumenti applicabili → invoca `anthropic-skills:check-agevolazioni-express`
- **Standard** (99 EUR): audit completo con report — prosegui con tutti gli step
- **Pro** (199 EUR): standard + 30 min call review + follow-up 60gg

### Step 2 — Profilazione PMI
Verifica che l'azienda rientri nei criteri PMI (Raccomandazione UE 2003/361):
- Micro: <10 dipendenti, fatturato/totale bilancio <=2 mln EUR
- Piccola: <50 dipendenti, <=10 mln EUR
- Media: <250 dipendenti, <=50 mln EUR fatturato o <=43 mln EUR totale bilancio

Verifica anche: impresa in difficolta (criteri UE), settore escluso (es. tabacco, armi), assenza obblighi recupero aiuti illegittimi (clausola Deggendorf).

### Step 3 — Matching bandi applicabili
Invoca `anthropic-skills:matching-bandi-agevolazioni` passando:
- Settore + ATECO
- Dimensione PMI
- Regione
- Tipo investimento + importo
- Periodo previsto investimento

Output atteso: lista bandi nazionali + regionali con score di compatibilita.

In parallelo, invoca `anthropic-skills:monitoraggio-bandi-pmi` per intercettare aperture/proroghe della settimana corrente.

### Step 4 — Verifica requisiti per bando target
Per ogni bando con score > 70%, invoca la skill di verifica requisiti corrispondente:
- Investimenti 4.0/5.0 → `anthropic-skills:verifica-requisiti-transizione5`
- Acquisto macchinari/software → `anthropic-skills:verifica-requisiti-sabatini`
- Internazionalizzazione/export → `anthropic-skills:verifica-requisiti-simest`
- Sviluppo R&S/innovazione tecnologica/design → `anthropic-skills:credito-rd-innovazione`
- Bonus assunzioni → `anthropic-skills:calcolo-decontribuzione-assunzioni`

Per ogni bando: % copertura, tetto massimo, finestra apertura, documentazione richiesta.

### Step 5 — Calcolo de minimis residuo
Invoca `anthropic-skills:calcolo-de-minimis` con plafond ultimi 3 esercizi (anche stimati). Verifica che le agevolazioni in regime de minimis sommate non sforino i 300k EUR (Reg.UE 2023/2831, in vigore dal 2024).

### Step 6 — Normativa di sfondo (per bandi PNRR e UE)
Se tra i bandi target c'e' uno strumento PNRR o fondo strutturale UE, invoca:
- `anthropic-skills:flusso-consulenza-pnrr` per inquadramento PNRR
- `anthropic-skills:consulente-policy-ue` per fondi strutturali
- `anthropic-skills:consulente-finanza-pubblica` per ACB se richiesto

### Step 7 — Calcolo stima totale finanziabile
Aggrega:
- Per ogni bando applicabile: stima conservativa EUR finanziabile (= costo intervento × % copertura, capped al tetto)
- Sottrai eventuali aiuti gia ricevuti che riducono il plafond
- Verifica cumulabilita (alcuni bandi non sono cumulabili tra loro)

Output: **TOTALE EUR FINANZIABILE** — la metrica forte per l'executive summary del titolare.

### Step 8 — Generazione report DOCX

Struttura report (12-18 pagine):

1. **Copertina** + dati azienda + data
2. **Executive Summary 1 pagina** per il titolare:
   - Score agevolazioni 0-100
   - **TOTALE EUR finanziabile stimato** (numero forte)
   - Top 3 bandi applicabili
   - Prossima scadenza
3. **Profilo aziendale** (dimensione PMI, settore, regione)
4. **Matrice bandi applicabili** — tabella con: bando | tipo | % copertura | tetto | scadenza | priorita
5. **Approfondimento per i top 5 bandi** (1-2 pagine ciascuno):
   - Requisiti specifici verificati
   - Documentazione necessaria
   - Tempistica realistica (apertura → erogazione)
   - Rischi (revoca, doppio cumulo, ecc.)
6. **Plafond de minimis** — stato attuale + impatto bandi proposti
7. **Roadmap di accesso** ordinata cronologicamente con scadenze
8. **Bridge K2-AI**: come gli altri servizi K2-AI possono supportare la rendicontazione (Audit SEO se digital, Audit Bilancio per requisiti finanziari)
9. **Allegati**: estratti normativi, link ufficiali, FAQ

Invoca la skill `docx` per la generazione del DOCX.

## Tono e linguaggio K2-AI

- **Italiano nativo titolare-friendly**: il titolare PMI deve capire l'executive summary senza commercialista
- **Numero forte in alto**: "Stimiamo 47.000 EUR finanziabili" e' piu efficace di "varie agevolazioni applicabili"
- **Stima sempre conservativa**: usa lower bound, evita over-promising. La fiducia vale piu del numero gonfiato
- **Riferimenti normativi precisi**: cita art. e legge esatti per credibilita (es. "L. 160/2019 art. 1 c. 198-209")
- **Lingua semplice**: "soldi che non hai chiesto" invece di "agevolazioni non utilizzate"

## Tiering output (pricing modulare)

| Versione | Prezzo | Cosa include |
|---|---|---|
| **Express** | Free (lead magnet) | Score 0-100 + top 3 strumenti (no report DOCX) |
| **Standard** | 99 EUR | Audit completo + report DOCX 12-18 pagine + roadmap |
| **Pro** | 199 EUR | Standard + 30 min call review + 1 follow-up dopo 60gg |

## Bridge con altri prodotti K2-AI

- Cliente che chiede `k2ai-marketing-seo:audit-seo-tecnico` → la sezione Bridge Agevolazioni dell'audit SEO chiama questo orchestratore per identificare bandi PNRR Digitalizzazione applicabili
- Cliente con `k2ai-controllo-gestione` (futuro): l'audit agevolazioni usa i KPI finanziari per dimostrare requisiti
- Cliente con `k2ai-edilizia-pmi` (futuro): bandi specifici per investimenti edilizi (Sabatini Green, ecotrasformazione)
- Cliente con `k2ai-hospitality` (futuro): bandi Turismo (Fondo Turismo, Tax Credit Hotel)

## Note implementative

- Quando invochi le skill `anthropic-skills:*`, passa SEMPRE il contesto completo (regione, settore, dimensione PMI) per evitare che la skill chieda di nuovo questi dati
- Se una skill specialistica ha bisogno di dati extra (es. cert. GSE per Transizione 5.0), chiedi al titolare e poi rilancia
- Per il calcolo finanziabile finale, fai due stime: ottimistica (tutti i bandi compatibili al 100%) e conservativa (solo bandi con score>=80%, capped al 70% del tetto). Mostra solo la conservativa nell'executive summary.
- Dichiara sempre i limiti del report: "stima basata su normativa al [data], finestre apertura possono cambiare"

## Differenziazione marketing (per il sito)

> "L'audit agevolazioni che ti dice in EUR quanto stai lasciando sul tavolo. Per PMI italiane 5-50 dipendenti che vogliono sapere se i bandi PNRR, Transizione 5.0, Sabatini, SIMEST sono per loro — senza pagare 1.500 EUR a un commercialista per un'analisi che spesso e' solo un copia-incolla. 99 EUR, 5 minuti di input, DOCX 18 pagine, esempio reale scaricabile."

## File di supporto (da creare per arricchire l'orchestratore)

Stub iniziali (puoi espanderli in seguito):
- `references/normativa-2026.md` — riferimenti normativi aggiornati per ogni strumento
- `references/cumulabilita-bandi.md` — matrice cumulabilita tra strumenti
- `assets/template-report-agevolazioni.md` — template DOCX

---

Creato: 2026-05-05 — v0.1.0 primo orchestratore K2-AI Agevolazioni del marketplace privato.
