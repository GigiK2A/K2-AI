---
name: ux-copy-review
description: >-
  Revisione UX e copywriting homepage e landing page per PMI italiane. Report DOCX 10-12 pagine
  con annotazioni prima/dopo e piano azione prioritizzato. Trigger: "revisione UX", "UX review",
  "il sito non converte", "homepage non funziona", "migliorare la homepage", "copy sito web",
  "testi sito", "CTA", "call to action", "proposta di valore", "landing page review",
  "conversion rate", "nessuno mi contatta dal sito", "revisione testi", "UX copy",
  "copywriting sito", "audit conversione". Input: URL sito, pagine da analizzare
  (default homepage + max 4 landing), settore, target cliente ideale, obiettivo conversione.
  Analizza gerarchia visiva, proposta di valore, CTA, copy, accessibilita. Per ogni problema:
  riferimento sezione, diagnosi, riscrittura proposta. Output: report DOCX + JSON strutturato.
  Fascia 349-499 EUR consulenza web PMI. Tono empatico e diretto.
allowed-tools:
  - WebFetch
  - WebSearch
  - fetch_page_content
  - lighthouse_audit
---

# ux-copy-review

Revisione UX e copywriting della homepage e landing page principali per PMI italiane: report DOCX 10-12 pagine con annotazioni "prima/dopo" e piano d'azione prioritizzato.

## Panoramica

Questa skill esegue una revisione completa dell'esperienza utente e del copywriting delle pagine principali di un sito web PMI italiano. Il focus e sulla conversione: il prodotto e pensato per chi ha traffico ma non converte ("arrivano sul sito ma non mi contattano"). Analizza gerarchia visiva, proposta di valore, CTA, tono dei testi, orientamento al cliente e accessibilita di base.

Si posiziona nella fascia 349-499 EUR della scala di valore della consulenza web PMI: il passo successivo per chi ha gia il sito ma non ottiene risultati.

**Filosofia**: "Il tuo sito parla di te, non del tuo cliente -- ecco come girarlo."

## Input

| Parametro | Obbligatorio | Default | Descrizione |
|-----------|:------------:|---------|-------------|
| URL sito | Si | - | URL della homepage del sito da analizzare |
| Pagine da analizzare | No | Homepage + max 4 landing | Lista URL delle pagine specifiche da revisionare |
| Settore | No | Auto-detect | Settore merceologico (servizi professionali, e-commerce, ristorazione, artigiani/edilizia, altro) |
| Target cliente ideale | No | - | Descrizione del cliente tipo (es. "proprietari di casa 35-55 anni zona Milano") |
| Obiettivo conversione | No | Contatto | Tipo di conversione: contatto / preventivo / acquisto / iscrizione |

## Workflow

### Step 1: Analisi gerarchia visiva e struttura pagina

Fetch della homepage e delle landing indicate. Per ogni pagina analizzare:

- **Above the fold**: cosa vede l'utente senza scrollare? C'e una headline chiara? Una CTA visibile? Un'immagine rilevante?
- **Struttura sezioni**: le sezioni seguono un flusso logico? (problema → soluzione → prova → azione)
- **Flusso di lettura**: la pagina guida l'occhio verso la conversione o disperde l'attenzione?
- **Elementi distraenti**: slider, animazioni eccessive, popup immediati, musica autoplay
- **Mobile**: la gerarchia regge su mobile? Il contenuto above the fold e lo stesso?

**Strumenti**: WebFetch per leggere il contenuto della pagina, lighthouse_audit per metriche tecniche, fetch_page_content per il DOM.

### Step 2: Valutazione proposta di valore

Applicare il **5-Second Test**: cosa capisce un utente nei primi 5 secondi?

Checklist:
- [ ] Chi sei? (nome azienda/brand riconoscibile)
- [ ] Cosa fai? (servizio/prodotto chiaro)
- [ ] Perche sceglierti? (elemento differenziante)
- [ ] Cosa devo fare adesso? (CTA evidente)

Valutare la proposta di valore con la formula:
**[Per chi]** + **[che ha questo problema]** + **[noi facciamo X]** + **[cosi ottieni Y]** + **[a differenza di Z]**

La proposta di valore attuale copre tutti gli elementi? E differenziante o generica?

### Step 3: Audit CTA

Per ogni CTA trovata nelle pagine analizzate, valutare:

- **Posizione**: above the fold? Fine sezione? Sticky? Exit intent?
- **Testo**: azione specifica ("Richiedi preventivo gratuito") vs generico ("Clicca qui", "Invia")? Beneficio vs feature?
- **Design**: contrasto col background? Dimensione adeguata? Whitespace sufficiente?
- **Friction**: quanti step per convertire? Il form e troppo lungo? Il telefono ha click-to-call? Serve registrazione?
- **Coerenza**: le CTA sono coerenti tra loro? Portano tutte allo stesso obiettivo?
- **Numero**: troppe CTA in competizione? O nessuna CTA visibile?

### Step 4: Revisione copy

Per ogni sezione della pagina (hero, servizi, chi siamo, testimonianze, contatti):

- **Test "Tu vs Noi"**: contare le occorrenze di "noi siamo/facciamo" vs "tu ottieni/risolvi". Il copy e orientato al cliente o autoreferenziale?
- **Headline**: comunica un beneficio specifico o e generica? ("Benvenuti nel nostro sito" = bocciata)
- **Frasi vuote da eliminare**: "azienda leader nel settore", "a 360 gradi", "qualita e professionalita", "da oltre X anni" -- sostituire con fatti concreti
- **Prova sociale**: ci sono testimonianze con nome/foto? Loghi clienti? Numeri concreti? Certificazioni?
- **Micro-copy**: testi dei bottoni, label dei form, messaggi di errore, thank you page
- **Tono**: coerente col target? Troppo formale? Troppo informale? Linguaggio tecnico non necessario?
- **Persuasione** (Cialdini semplificato): uso di scarsita, prova sociale, autorita, reciprocita

Per ogni problema: testo originale, diagnosi del problema, riscrittura proposta con spiegazione.

### Step 5: Check accessibilita base e riscrittura testi chiave

- **Contrasto colori**: il testo e leggibile sullo sfondo?
- **Font size**: il corpo testo e almeno 16px? I titoli sono gerarchici (H1 → H2 → H3)?
- **Tap target**: i bottoni su mobile sono almeno 44x44px?
- **ARIA label**: i form hanno label accessibili?
- **Alt text**: le immagini hanno alt text descrittivo?

Produrre la riscrittura completa dei testi chiave: headline, sottotitolo, CTA principali, proposta di valore.

## Skills invocate

- `design:ux-copy` -- principi di UX writing
- `design:design-critique` -- valutazione design e gerarchia visiva
- `design:accessibility-review` -- check accessibilita
- `psicologia-marketing` -- principi di persuasione e psicologia del consumatore

## Pattern di conversione per settore

Applicare il pattern corretto in base al settore della PMI:

| Settore | CTA primaria | Elementi chiave |
|---------|-------------|-----------------|
| Servizi professionali | Form contatto breve (nome, email, messaggio) | Numero telefono visibile, testimonianze, portfolio |
| E-commerce | Aggiungi al carrello | Trust badge, spedizione, reso, recensioni prodotto |
| Ristorazione | Prenota tavolo | Menu, foto piatti, indicazioni stradali, orari |
| Artigiani/edilizia | Richiedi preventivo | Portfolio lavori, testimonianze, zona servita |

## Errori UX mortali per PMI

Segnalare con priorita massima se presenti:
- Slider/carousel in homepage (nessuno li guarda dopo il primo)
- Musica o video autoplay
- Popup immediato (prima che l'utente veda il contenuto)
- Menu hamburger su desktop
- Form con 15+ campi
- Nessun numero di telefono visibile
- Pagina "chi siamo" come landing principale
- Homepage che non comunica cosa fa l'azienda

## Deliverable

### Report DOCX (10-12 pagine)

Generare con la skill `docx` seguendo il template in `assets/template-report-ux-copy.md`:

1. Copertina
2. Executive Summary (punteggio UX 0-100, punteggio Copy 0-100, top 5 problemi, impatto stimato)
3. Analisi 5-Second Test
4. Audit gerarchia visiva con annotazioni
5. Audit CTA completo
6. Revisione copy per sezione (prima/dopo)
7. Check accessibilita
8. Piano d'azione prioritizzato (quick wins copy + interventi strutturali UX)
9. Appendice: glossario termini UX

### JSON strutturato

Output conforme allo schema in `schemas/output-schema.json`.

## Modalita operative

### Modalita consulenziale (default)
- **WebFetch**: per leggere il contenuto delle pagine
- **WebSearch**: per benchmark competitivi e best practice settore
- Ragionamento esperto basato sui framework in `references/`

### Modalita piattaforma (se disponibili)
- **fetch_page_content**: per ottenere il DOM completo
- **lighthouse_audit**: per metriche performance e accessibilita

## Tono del report

Empatico ma diretto. Il titolare della PMI deve sentirsi capito, non giudicato. Ogni critica e accompagnata dalla soluzione.

Esempi:
- "Il tuo sito parla di te, non del tuo cliente -- ecco come girarlo."
- "La tua homepage dice 'azienda leader dal 1985' -- ma il cliente vuole sapere come risolvi il SUO problema."
- "Hai una CTA, ma e nascosta dopo 4 scroll. Spostiamola dove serve."
