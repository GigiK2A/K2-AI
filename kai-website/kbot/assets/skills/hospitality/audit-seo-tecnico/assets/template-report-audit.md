# Template Report Audit SEO Tecnico

Struttura del report DOCX da 10-15 pagine. Usare la skill `docx` per generare il file finale.

---

## Stile documento

- **Font titoli**: Calibri Bold
- **Font corpo**: Calibri Regular, 11pt
- **Colore heading**: blu #1E40AF
- **Tabelle**: zebrate (righe alternate grigio chiaro #F3F4F6 / bianco)
- **Badge severita**:
  - Critico: sfondo rosso #DC2626, testo bianco
  - Importante: sfondo arancione #F59E0B, testo nero
  - Minore: sfondo giallo #FDE047, testo nero
- **Score badge**:
  - 0-30: rosso #DC2626
  - 31-50: arancione #F59E0B
  - 51-70: giallo #FDE047
  - 71-85: verde chiaro #22C55E
  - 86-100: verde #16A34A
- **Margini**: 2.5cm tutti i lati
- **Intestazione**: logo placeholder a sinistra, "Audit SEO Tecnico" a destra
- **Pie di pagina**: "Confidenziale — Preparato per [Nome Cliente]" a sinistra, numero pagina a destra

---

## Sezione 1 — Copertina (1 pagina)

```
[LOGO PLACEHOLDER — rettangolo grigio 200x80px]

AUDIT SEO TECNICO

Sito analizzato: {url_sito}
Cliente: {nome_cliente}
Data: {data_audit}
Redatto da: {nome_consulente}

Versione: 1.0
Classificazione: Confidenziale
```

**Note**: pagina senza intestazione e pie di pagina. Sfondo bianco, testo centrato.

---

## Sezione 2 — Executive Summary (1 pagina)

Questa sezione e scritta per il titolare dell'azienda. Linguaggio semplice, zero gergo tecnico.

```
EXECUTIVE SUMMARY

Score globale: {score_globale}/100  [BADGE COLORE]

Il sito {url_sito} presenta {giudizio_sintetico}.

I 5 problemi piu urgenti:

1. {problema_1_titolo_semplice}
   Impatto: {impatto_1_descrizione_semplice}

2. {problema_2_titolo_semplice}
   Impatto: {impatto_2_descrizione_semplice}

3. {problema_3_titolo_semplice}
   Impatto: {impatto_3_descrizione_semplice}

4. {problema_4_titolo_semplice}
   Impatto: {impatto_4_descrizione_semplice}

5. {problema_5_titolo_semplice}
   Impatto: {impatto_5_descrizione_semplice}

Raccomandazione prioritaria:
{raccomandazione_principale_in_linguaggio_semplice}

Stima impatto complessivo:
Risolvendo i problemi critici, il sito potrebbe recuperare circa {stima_traffico_perso}%
di traffico organico, equivalente a circa {stima_visite_mensili} visite mensili aggiuntive.
```

**Fasce di giudizio sintetico**:
- 0-30: "problemi gravi che impediscono la visibilita su Google"
- 31-50: "diverse criticita che limitano significativamente il posizionamento"
- 51-70: "una base accettabile ma con margini di miglioramento importanti"
- 71-85: "un buon livello tecnico con alcuni aspetti da perfezionare"
- 86-100: "un'ottima base tecnica con dettagli minimi da affinare"

---

## Sezione 3 — Metodologia (1/2 pagina)

```
METODOLOGIA

Questo audit e stato condotto analizzando {numero_pagine} pagine del sito {url_sito}
in data {data_audit}.

Aree analizzate:
- Crawlability e indicizzazione
- Velocita e performance (Core Web Vitals)
- Compatibilita mobile
- Sicurezza (HTTPS)
- SEO on-page (title, meta, heading, contenuto)
- Ottimizzazione immagini
- Struttura del sito e linking interno
- Dati strutturati (Schema markup)

Strumenti utilizzati:
- Analisi automatizzata HTML e performance
- Lighthouse / PageSpeed Insights
- Verifica indicizzazione Google

Ogni problema e classificato per severita (critico, importante, minore) e accompagnato
da istruzioni operative specifiche per la risoluzione.
```

---

## Sezione 4 — Diagnosi per area (6-8 pagine)

Ripetere questa struttura per ciascuna delle 8 aree. Ogni area occupa circa 3/4 di pagina a 1 pagina.

### Struttura per singola area

```
{NOME_AREA}                                          Score: {score_area}/100 [BADGE]

[Tabella problemi trovati]

| # | Problema | Severita | Impatto traffico | Pagine coinvolte |
|---|----------|----------|------------------|------------------|
| 1 | {desc}   | [BADGE]  | {stima}%         | {lista_url}      |
| 2 | ...      | ...      | ...              | ...              |

Dettaglio e istruzioni operative:

PROBLEMA 1: {titolo_problema}
Severita: {badge_severita}
Impatto stimato: {percentuale}% del traffico organico

Situazione attuale:
{descrizione_tecnica_del_problema}

Istruzione operativa per il webmaster:
{istruzione_passo_passo_concreta}

Esempio per CMS specifici:
- WordPress: {istruzione_wordpress}
- Shopify: {istruzione_shopify}  (se pertinente)
- Generico: {istruzione_generica}

Verifica:
{come_verificare_che_il_problema_sia_risolto}

---
```

### Aree da coprire (in ordine)

1. **Crawlability e Indicizzazione** — robots.txt, sitemap, noindex, canonical, redirect, 404, indicizzazione
2. **Velocita e Performance** — Core Web Vitals, TTFB, compressione, caching, immagini, JS blocking
3. **Compatibilita Mobile** — responsive, viewport, tap target, font, mobile-first
4. **Sicurezza** — HTTPS, mixed content, HSTS, header sicurezza
5. **SEO On-Page** — title, meta desc, H1-H6, keyword, thin content, duplicate content
6. **Ottimizzazione Immagini** — alt tag, dimensioni, formati, lazy loading
7. **Struttura Sito** — URL, breadcrumb, internal linking, orphan pages, profondita
8. **Schema Markup** — Organization, LocalBusiness, BreadcrumbList, FAQ, Product

---

## Sezione 5 — Matrice Priorita (1 pagina)

Grafico a 4 quadranti (descrizione testuale per generazione DOCX):

```
MATRICE PRIORITA (IMPATTO x SFORZO)

                        ALTO IMPATTO
                            |
    PROGETTI IMPORTANTI     |     QUICK WIN
    (pianificare)           |     (fare subito)
                            |
  BASSO SFORZO ------------|-------------- ALTO SFORZO
                            |
    DEPRIORITIZZARE         |     MIGLIORAMENTI FACILI
    (rimandare)             |     (quando possibile)
                            |
                       BASSO IMPATTO

Quick Win (fare subito):
{lista_azioni_quick_win}

Progetti importanti (pianificare):
{lista_azioni_progetti}

Miglioramenti facili (quando possibile):
{lista_azioni_miglioramenti}

Da rimandare:
{lista_azioni_rimandare}
```

---

## Sezione 6 — Piano d'Azione (1-2 pagine)

Tabella ordinata per priorita (quick win prima, poi progetti importanti, poi miglioramenti facili).

```
PIANO D'AZIONE

| # | Azione | Severita | Area | Istruzioni sintetiche | Tempo stimato |
|---|--------|----------|------|-----------------------|---------------|
| 1 | {azione} | [BADGE] | {area} | {istruzione_breve} | {tempo} |
| 2 | ... | ... | ... | ... | ... |
| ... | | | | | |

Legenda tempi stimati:
- 15 min: intervento rapido, singola modifica
- 30 min: intervento semplice
- 1-2 ore: intervento medio
- 4+ ore: intervento complesso, possibile coinvolgimento sviluppatore
- Progetto: richiede pianificazione e sviluppo dedicato

Nota: i tempi sono stimati per un webmaster con esperienza media sul CMS utilizzato.
```

---

## Sezione 7 — KPI da Monitorare (1/2 pagina)

```
KPI DA MONITORARE POST-INTERVENTO

Verificare questi indicatori a 30, 60 e 90 giorni dall'implementazione delle correzioni.

| KPI | Valore attuale | Obiettivo 30gg | Obiettivo 90gg | Come misurare |
|-----|---------------|----------------|----------------|---------------|
| Score Lighthouse Performance | {val} | {obj30} | {obj90} | PageSpeed Insights |
| LCP | {val} | {obj30} | {obj90} | PageSpeed Insights |
| INP | {val} | {obj30} | {obj90} | PageSpeed Insights |
| CLS | {val} | {obj30} | {obj90} | PageSpeed Insights |
| Pagine indicizzate | {val} | {obj30} | {obj90} | Google Search Console |
| Errori di scansione | {val} | {obj30} | {obj90} | Google Search Console |
| Posizione media keyword target | {val} | {obj30} | {obj90} | Google Search Console |
| Traffico organico mensile | {val} | {obj30} | {obj90} | Google Analytics |
| Click da ricerca organica | {val} | {obj30} | {obj90} | Google Search Console |

Raccomandazione: configurare Google Search Console e Google Analytics se non ancora attivi.
```

---

## Sezione 8 — Appendice Tecnica (1-2 pagine)

```
APPENDICE TECNICA

A. Elenco completo URL analizzate
| URL | Status | Title | Meta desc | H1 | Canonical | Noindex |
|-----|--------|-------|-----------|----|-----------|---------| 
| ... | ... | ... | ... | ... | ... | ... |

B. Dati Core Web Vitals grezzi
| Pagina | LCP | INP | CLS | FCP | TTFB | TBT | Score Lighthouse |
|--------|-----|-----|-----|-----|------|-----|------------------|
| ... | ... | ... | ... | ... | ... | ... | ... |

C. Elenco completo problemi per severita
| ID | Problema | Severita | Area | Pagine | Impatto |
|----|----------|----------|------|--------|---------|
| ... | ... | ... | ... | ... | ... |

D. Configurazione robots.txt attuale
{contenuto_robots_txt}

E. Analisi sitemap.xml
- URL totali in sitemap: {numero}
- URL con status 200: {numero}
- URL con status 301: {numero}
- URL con status 404: {numero}
- URL non in sitemap ma crawlate: {numero}
```

---

## Note per la generazione DOCX

- Usare la skill `docx` passando la struttura completa
- Sostituire tutti i placeholder {variabile} con i dati reali dell'audit
- I badge severita nel DOCX sono celle colorate nella tabella (sfondo colorato, testo centrato bold)
- Le tabelle zebrate si ottengono alternando sfondo righe bianco / #F3F4F6
- Inserire interruzione di pagina prima di ogni sezione principale
- La copertina e una pagina separata con layout centrato
- Executive Summary deve stare in 1 pagina (regolare dimensione testo se necessario)
