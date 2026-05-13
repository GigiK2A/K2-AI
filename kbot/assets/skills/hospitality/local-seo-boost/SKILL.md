---
name: local-seo-boost
description: >-
  Ottimizzazione Local SEO per attivita con clientela geografica in Italia (ristoranti, studi
  professionali, artigiani, negozi). Report DOCX 8-10 pagine con audit Google Business Profile,
  verifica NAP, citazioni locali, strategia recensioni, ottimizzazione on-page locale. Trigger:
  "local SEO", "Google Maps", "Google Business", "scheda Google", "farsi trovare su Google Maps",
  "SEO locale", "attivita locale", "clienti della zona", "posizionamento locale", "recensioni
  Google", "NAP", "citazioni locali", "maps posizionamento", "non mi trovano su Maps". Input: URL
  sito, nome attivita, indirizzo completo, categoria, keyword locali 2-3. Output: report DOCX,
  checklist operativa, JSON strutturato. Tono pratico: il titolare puo agire da solo stasera.
  Sotto-skill consulenza web PMI 149-249 EUR per clienti nel raggio di 30 km.
allowed-tools:
  - WebFetch
  - WebSearch
  - fetch_page_content
  - gbp_data
---

# local-seo-boost

Ottimizzazione Local SEO per attivita italiane con clientela geografica: report DOCX 8-10 pagine con piano d'azione immediato.

## Panoramica

Questa skill esegue un audit Local SEO completo per PMI italiane che operano su base territoriale (ristoranti, studi professionali, artigiani, negozi). Il focus e su Google Business Profile, coerenza NAP, citazioni locali italiane, gestione recensioni e ottimizzazione on-page per ricerche locali.

Si posiziona nella fascia 149-249 EUR della scala di valore consulenza web PMI, destinata al cliente che dice "i miei clienti sono tutti nel raggio di 30 km".

Il tono e pratico e orientato all'azione immediata: il titolare di un ristorante deve poter fare le prime 3 cose da solo stasera.

## Input

| Parametro | Obbligatorio | Descrizione |
|-----------|:------------:|-------------|
| URL sito | Si | URL della homepage del sito dell'attivita |
| Nome attivita | Si | Ragione sociale o nome commerciale come appare su GBP |
| Indirizzo completo | Si | Via, numero civico, CAP, citta, provincia |
| Categoria attivita | Si | Categoria merceologica (es. "ristorante", "dentista", "idraulico") |
| Keyword locali | Si | 2-3 keyword target (es. "dentista Milano centro", "pizzeria Trastevere") |

## Workflow

### Step 1 — Audit Google Business Profile

Analisi completa della scheda GBP verificando:
- **Completezza informazioni base**: nome (verifica keyword stuffing), indirizzo, telefono, sito web, orari (anche festivi/speciali), descrizione (max 750 caratteri)
- **Categorie**: primaria + secondarie (max 10), coerenza con attivita reale
- **Foto**: quantita (obiettivo minimo 10), tipologie (logo, cover, interni, esterni, team, prodotti), qualita, data aggiornamento
- **Post GBP**: frequenza pubblicazione, tipologie (novita, eventi, offerte), engagement
- **Q&A**: presidio, domande pre-popolate, risposte tempestive
- **Attributi**: accessibilita, servizi offerti, metodi di pagamento
- **Prodotti/Servizi**: catalogo compilato, descrizioni, pricing
- **Calcolo percentuale completezza** con punteggio per ogni sezione

Riferimento: `references/guida-google-business-profile.md`

**Modalita consulenziale**: WebSearch per cercare la scheda GBP pubblica, WebFetch per analizzare il profilo.
**Modalita piattaforma**: `gbp_data` per accesso diretto ai dati del profilo.

### Step 2 — Verifica coerenza NAP

Controllo Name, Address, Phone su tutte le fonti:
- Confronto dati su sito web (header, footer, pagina contatti, schema markup)
- Confronto dati su Google Business Profile
- Confronto dati sulle principali directory (PagineGialle, Virgilio, Yelp, ecc.)
- Identificazione discrepanze: abbreviazioni diverse, CAP errato, prefisso telefonico, formato numero
- Tabella comparativa fonte per fonte con flag coerente si/no

**Modalita consulenziale**: WebFetch per leggere il sito, WebSearch per cercare NAP sulle directory.
**Modalita piattaforma**: `fetch_page_content` per analisi sito.

### Step 3 — Analisi citazioni locali

Verifica presenza e correttezza su directory italiane:
- **Generaliste**: PagineGialle, PagineBianche, Virgilio, Yelp Italia, Cylex, HotFrog
- **Di settore**: TripAdvisor (ristorazione/turismo), MioDottore (medici), Edilportale (edilizia), directory verticali
- **Mappe**: Google Maps, Apple Maps, Bing Places, Waze, TomTom
- **Social local**: Facebook (pagina business), Instagram (location tag)
- Per ogni directory: presente/assente, dati corretti/errati, azioni correttive

Riferimento: `references/citazioni-locali-italia.md`

**Modalita consulenziale**: WebSearch per verificare presenza su ciascuna directory, WebFetch per controllare i dati.

### Step 4 — Strategia recensioni

Analisi e piano d'azione recensioni:
- **Stato attuale**: volume recensioni, rating medio, trend ultimi 6 mesi
- **Gestione risposte**: percentuale risposte, tempo medio di risposta, qualita risposte (personalizzate vs template)
- **Benchmark**: confronto con competitor locali diretti (top 3-5)
- **Tattiche per ottenere recensioni**: QR code in negozio, follow-up post-servizio, link diretto recensione, formazione staff
- **Gestione recensioni negative**: protocollo di risposta, tempi, tono
- **Obiettivo**: target volume e rating a 90 giorni

**Modalita consulenziale**: WebSearch per analizzare recensioni pubbliche e competitor.

### Step 5 — Ottimizzazione on-page locale

Verifica e raccomandazioni per il sito web:
- **Schema markup LocalBusiness**: verifica presenza, completezza, correttezza (JSON-LD)
- **Pagine per area geografica**: se l'attivita serve piu zone, pagine dedicate (es. "Idraulico Milano Nord", "Idraulico Milano Sud")
- **Contenuti locali**: menzioni del territorio, landmark, quartieri, eventi locali
- **Title tag e meta description**: inclusione citta/zona nelle pagine chiave
- **Pagina contatti**: mappa embedded, indicazioni stradali, orari, parcheggio
- **Mobile optimization**: essenziale per ricerche locali (80%+ da mobile)

**Modalita consulenziale**: WebFetch per analizzare il sito, WebSearch per verificare il markup.
**Modalita piattaforma**: `fetch_page_content` per analisi tecnica del sito.

## Skills invocate

- `digital-marketing-performance` — per analisi traffico e conversioni locali
- `marketing:seo-audit` — per audit SEO tecnico di base del sito

## Deliverable

### Report DOCX (8-10 pagine)

Struttura definita in `assets/template-report-local.md`:
1. Copertina con dati attivita
2. Executive Summary con voto sintetico
3. Audit Google Business Profile
4. Coerenza NAP (tabella comparativa)
5. Citazioni locali
6. Strategia recensioni
7. Ottimizzazione on-page locale
8. Piano d'azione 30-60-90 giorni

### Checklist operativa

Lista di azioni prioritizzate che il titolare puo eseguire autonomamente, organizzata in:
- **Stasera** (15 minuti): le 3 azioni piu urgenti e facili
- **Questa settimana**: azioni a medio impatto
- **Questo mese**: azioni strutturali

### JSON strutturato

Output conforme a `schemas/output-schema.json` per integrazione con altri sistemi e tracciamento nel tempo.

## Tono e stile

- Pratico, orientato all'azione immediata
- Niente gergo tecnico non spiegato
- Ogni raccomandazione include: cosa fare, perche, come farlo (passo passo)
- Il titolare di un ristorante deve poter fare le prime 3 cose da solo stasera
- Prioritizzazione chiara: impatto alto + facilita esecuzione = prima cosa da fare

## Case italiani di riferimento

Per estrarre principi trasferibili a una PMI locale italiana, vedere `references/case-italiani-seo.md`: tre schede-studio (GialloZafferano, Aranzulla, Zalando) con la lezione operativa specifica per attivita territoriali — firma autori e schema di settore, long-tail informativa locale, pagine di categoria strutturate.

---

Aggiornato: 2026-04-17 — integrati contenuti SEO 2025 (AI search) + evoluzione algoritmo + case italiani.
