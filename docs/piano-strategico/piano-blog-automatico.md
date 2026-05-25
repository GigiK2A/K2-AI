# Piano blog automatico K2-AI

> Spec completa del sistema di generazione + pubblicazione articoli SEO senza intervento umano. Da approvare prima di qualunque riga di codice.

**Versione**: 1.0 — bozza
**Data**: 2026-05-25
**Owner**: Luigi
**Stato**: in attesa di approvazione

---

## 1. Obiettivo

Generare e pubblicare 60 articoli SEO (6 cluster × 10 pillar) entro 6 mesi, **senza che Luigi debba scriverli, leggerli, o approvarli uno per uno**, mantenendo:

- Qualità sufficiente a rankare su Google (no AI slop generico)
- Voce di brand coerente con CLAUDE.md (no buzzword, italiano diretto, numeri concreti)
- **Strategia "teaser content"**: dimostrare competenza → spingere a K-BOT/contatto. **NON dare la soluzione operativa completa.** Se l'articolo risolve da solo il problema del lettore, K2-AI smette di servire e non vende niente.

Obiettivo traffico realistico: 5.000-8.000 visite organiche/mese a 12 mesi dall'avvio. Da queste, 50-200 sessioni K-BOT/mese aggiuntive.

---

## 2. Principio "teaser content" — la regola d'oro

Ogni articolo segue questa struttura mentale:

| Sezione articolo | Cosa diciamo | Cosa NON diciamo |
|---|---|---|
| **Problema** | Descritto in dettaglio, con esempi reali e numeri (chi soffre, quanto, perché) | — |
| **Perché soluzioni comuni non bastano** | Limiti reali di Zapier, n8n, soluzioni manuali, plugin generici | Quale specifica configurazione fa funzionare X |
| **Cosa serve davvero** | Architettura generale (es. "serve un agente che integra Y con Z"), criteri di scelta | I parametri esatti, le query, lo schema dati, i prompt template |
| **Esempio cliente anonimizzato** | "Studio commercialista 12 dipendenti, Umbria, ha portato triage email da 90min/giorno a 8min con un agente custom" | Codice, configurazione esatta, screenshot completo dashboard |
| **Quando ha senso costruire custom vs no** | Tabella decisionale ("se hai meno di X, basta Zapier; sopra X serve agente") | — |
| **CTA** | "Apri K-BOT per capire il tuo caso" o "scrivici a info@k2-ai.it" | Non vendiamo nel pezzo, suggeriamo passo successivo |

Test mentale per validare articolo: **"Un lettore che legge solo questo articolo, può implementare da solo?"**
- Se SÌ → articolo da riscrivere, dà troppo
- Se NO ma "capisce il problema, capisce che esiste una soluzione, capisce che K2-AI sa farla" → articolo OK

Questo va codificato come istruzione fissa nello skill Claude di generazione, non lasciato al caso.

---

## 3. Cosa significa "totalmente autonomo"

Flusso end-to-end senza Luigi:

```
[CRON ogni Lun/Mer/Ven alle 06:00 CET]
        │
        ▼
[1] SELEZIONA prossimo brief da pubblicare
    → legge keyword_map.json, sceglie il prossimo articolo
       non ancora pubblicato (ordinato per priorità)
        │
        ▼
[2] GENERA brief AI
    → Claude espande la riga della keyword map in un brief
       completo (angle, outline, dati da citare)
        │
        ▼
[3] GENERA draft articolo
    → Claude (skill articolo-blog-k2ai) produce HTML
       con title/meta/H1/body/JSON-LD
        │
        ▼
[4] AUTO-EDIT pass 2
    → Claude rilegge l'articolo con prompt critico:
       "Rimuovi frasi AI-typical, sostituisci esempi
        generici, verifica che non sveli la soluzione
        completa, verifica voce brand"
        │
        ▼
[5] VALIDAZIONE automatica (no AI, hard checks)
    → length, H1 unico, internal links ≥ 2,
       no banned terms (Diagnosi Strategica, advisor PMI,
       AdvisorBoost, StrategyBoost, "trasformazione digitale",
       "rivoluzionario"...),
       Lighthouse SEO score >= 90,
       presenza CTA K-BOT,
       schema.org valido (Article + FAQPage + Breadcrumb)
        │
   ┌────┴────┐
   │ OK      │ FAIL
   ▼         ▼
[6a] PUBLISH      [6b] ALERT a Luigi via email + Telegram
    → commit          → articolo va in cartella
       + push            drafts-pending/, sitemap NON aggiornata
       + sitemap         → Luigi rivede manualmente quando può
       + email
       riassunto
       settimanale
       a Luigi
```

Luigi interviene SOLO se:
- Validazione fallisce (≤ 5% dei casi attesi)
- Riceve report settimanale e nota qualcosa di strano
- Decide di aggiungere/modificare la keyword map

Tempo richiesto a Luigi a regime: ~30 min/mese per supervisione + correzioni occasionali.

---

## 4. Architettura tecnica

### 4.1 Dove vive

```
kai-website/
├── src/
│   ├── blog/                       ← cartella nuova
│   │   ├── _index.html            ← pagina /blog con lista filtrata
│   │   ├── _template.html         ← template articolo (non servito)
│   │   ├── automatizzare-email-hubspot-ai.html
│   │   ├── triage-email-studio-ingegneria.html
│   │   └── ... × 60
│   └── css/
│       └── blog.css               ← stile dedicato (sticky TOC, reading time)
│
├── tools/
│   └── blog-bot/                   ← cartella nuova, scripts Node
│       ├── package.json
│       ├── generate-article.ts    ← orchestrator
│       ├── select-next.ts         ← pesca prossimo brief
│       ├── prompts/
│       │   ├── brief-expand.md
│       │   ├── article-draft.md
│       │   └── article-revise.md
│       ├── validators/
│       │   ├── seo.ts             ← length, schema, links
│       │   ├── voice.ts           ← banned terms, AI-typical phrases
│       │   └── teaser.ts          ← controlla che non sveli soluzione
│       └── publish.ts             ← commit + push + sitemap
│
└── docs/piano-strategico/
    └── keyword-map.yaml           ← fonte di verità contenuti
```

### 4.2 Cron + esecuzione

Opzione A (consigliata): **GitHub Actions cron**
```yaml
# .github/workflows/blog-autopilot.yml
on:
  schedule:
    - cron: "0 5 * * 1,3,5"   # Lun/Mer/Ven 06:00 CET (5 UTC)
  workflow_dispatch:           # trigger manuale on-demand
```
- Vantaggi: zero costo, log centralizzati, secret GitHub
- Esegue `npm run blog:autopilot` → script genera articolo → commit + push direttamente
- Push triggera Railway auto-deploy (già configurato)

Opzione B: cron Railway sullo stesso container backend
- Vantaggi: env vars centralizzate
- Svantaggi: serve scrivere file sul repo dal container, complica setup

**Decisione**: Opzione A (GitHub Actions).

### 4.3 Componenti

| Componente | Tech | File |
|---|---|---|
| Orchestrator | Node + TS | `tools/blog-bot/generate-article.ts` |
| LLM client | `@anthropic-ai/sdk` (già in package.json) | — |
| Brand voice skill | Markdown skill nel prompt | `tools/blog-bot/prompts/article-draft.md` |
| Template HTML | Vite multi-page | `src/blog/_template.html` |
| Validator | Custom TS + cheerio per DOM check | `tools/blog-bot/validators/*` |
| Sitemap updater | Riusa logica esistente | `tools/blog-bot/publish.ts` |
| Notify | Resend email + Telegram (env già presenti) | `tools/blog-bot/notify.ts` |

### 4.4 Modello LLM e budget

- **Draft**: Claude Sonnet 4.6 — €0.20-0.40 per articolo (1500-2000 token output)
- **Revise pass**: Claude Haiku 4.5 — €0.05 per articolo
- **Brief expand**: Claude Haiku — €0.02

Totale: ~€0.30-0.50 per articolo. 60 articoli = ~€20-30 una tantum, poi €0 (articoli generati una volta).

Se generiamo 3/settimana per 6 mesi: 72 articoli × €0.50 = €36 totali. Trascurabile rispetto al budget tech 65€/mese.

---

## 5. Keyword map — la fonte di verità

File `docs/piano-strategico/keyword-map.yaml` (da creare). Esempio struttura:

```yaml
- id: P01-C1
  pillar: P01
  pillar_url: /suite-ai/agenti-email-crm
  slug: automatizzare-follow-up-email-hubspot-pmi
  keyword_primaria: "automatizzare follow-up email HubSpot PMI"
  keyword_secondarie:
    - follow-up email automatici PMI
    - HubSpot email sequenza AI
  volume: 320
  difficulty: 18
  intent: how-to
  target_lettore: "PMI 10-30 dipendenti che già usa HubSpot"
  angle: "differenza tra automation HubSpot nativa e agente AI"
  no_dire:
    - configurazione workflow precisa
    - codice template email
    - prompt esatti agente
  citare:
    - costo HubSpot Pro €450/mese 2026
    - tempo medio scrittura follow-up: 3-5 min/email
  pubblicare: true
  published_at: null
  published_url: null

- id: P01-C2
  pillar: P01
  slug: zapier-vs-agente-ai-quando-uno-quando-altro
  ...
```

Quando un articolo viene pubblicato, lo script aggiorna `published_at` e `published_url`. Lo script seleziona il prossimo articolo con `pubblicare: true` e `published_at: null`, ordinato per `volume DESC`.

60 righe iniziali da generare (10 pillar × 6 angoli). Le creo io una volta, Luigi rivede, poi entrano nel ciclo.

---

## 6. Prompt skill — `article-draft.md`

Punti chiave (estratto):

```markdown
# Skill: articolo-blog-k2ai

## Brand voice (vincolante)
- Italiano diretto, "tu" rivolto al lettore
- Mai: "trasformazione digitale", "rivoluzionario", "innovativo",
  "all'avanguardia", "cutting-edge", "nell'era digitale",
  "in conclusione", "è importante notare", "vale la pena di"
- Mai termini v1: "Diagnosi Strategica", "advisor PMI", "AdvisorBoost",
  "StrategyBoost"
- Numeri sempre quantificati ("3-5 minuti", "€450/mese", "120 lead/settimana")
- Periodi brevi. Max 25 parole per frase media.

## Regola TEASER (vincolante)
Devi descrivere il problema in dettaglio, spiegare perché soluzioni
generiche non bastano, citare un esempio cliente anonimizzato.

Devi ASTENERTI dal fornire:
- configurazioni specifiche pronte da copiare
- prompt template
- query SQL complete
- screenshot di dashboard configurati
- istruzioni step-by-step implementative

Il lettore deve capire CHE serve una soluzione custom, ma NON deve
poterla replicare da solo dopo aver letto. Punto di arrivo dell'articolo
è: "ho capito il problema, ho capito che esiste una soluzione, devo
parlare con qualcuno che la implementi".

## Struttura obbligatoria
1. H1 (max 65 char, contiene keyword primaria)
2. Intro 3-4 righe: descrivi il problema concreto
3. H2 "Perché [soluzione comune] non basta" → 200-300 parole
4. H2 "Cosa serve davvero" → 200-300 parole (architettura generale, NO dettagli)
5. H2 "Esempio reale" → 200-300 parole (cliente anonimo, numeri prima/dopo)
6. H2 "Quando ha senso costruire custom" → tabella decisionale
7. H2 "FAQ" → 3-4 domande/risposte (alimenta schema FAQPage)
8. Box CTA: "Apri K-BOT (gratis, 5 min)" → /app

## Internal linking
- 1 link al pillar padre nel paragrafo intro
- 2-3 link ad altri articoli stesso pillar (forniti dall'orchestrator)
- 1 link a /contatti

## SEO
- Title: "[H1] | K2-AI" (50-60 char)
- Meta description: 140-155 char, include keyword primaria + CTA implicita
- Schema.org Article + FAQPage + BreadcrumbList (auto-iniettati
  dall'orchestrator, tu non li scrivere)
```

---

## 7. Validatori — guardrail automatici

Articolo viene pubblicato solo se passa **tutti** questi check:

### 7.1 SEO hard checks (`validators/seo.ts`)
- [ ] Title tag presente, 50-60 char
- [ ] Meta description presente, 140-155 char
- [ ] Esattamente 1 `<h1>`
- [ ] Almeno 4 `<h2>`
- [ ] Canonical URL presente e corretto
- [ ] Schema.org Article valido (json-ld parsable)
- [ ] Schema.org FAQPage con ≥ 3 Question
- [ ] Schema.org BreadcrumbList
- [ ] ≥ 2 link interni a dominio `/suite-ai/*` o `/blog/*`
- [ ] ≥ 1 link a `/app` o `/contatti`
- [ ] ≥ 1200 parole (corpo principale, esclusi nav/footer)
- [ ] ≤ 2500 parole

### 7.2 Voice checks (`validators/voice.ts`)
- [ ] Zero occorrenze di banned terms (lista CLAUDE.md + extension)
- [ ] Zero occorrenze di "in conclusione", "è importante notare", "vale la pena di", "nel mondo di oggi", "nell'era digitale"
- [ ] Densità keyword primaria: 0.5%-2% (no keyword stuffing)
- [ ] Lunghezza media frase < 28 parole
- [ ] Almeno 1 numero quantificato per ogni H2 section

### 7.3 Teaser check (`validators/teaser.ts`)
- [ ] No code blocks `<pre>` o `<code>` di lunghezza > 30 caratteri
- [ ] No liste step-by-step `<ol>` con > 5 item (suggerisce tutorial)
- [ ] No screenshot di configurazione (path immagini con keyword
      "screenshot", "dashboard", "config" flaggato)
- [ ] Secondo pass Claude: chiede al modello "questo articolo permette
      al lettore di implementare da solo? rispondi YES/NO + motivo".
      Se YES → FAIL.

Validator 7.3 è il più importante e il più difficile. Se Claude
giudica male, qualcosa passa che non dovrebbe. Per i primi 10 articoli,
Luigi rivede manualmente l'output del check teaser per calibrare.

### 7.4 Fact check (`validators/facts.ts`)
- [ ] Numeri citati devono essere o vaghi ("3-5 minuti")
      o presenti in file `docs/piano-strategico/facts-allowed.yaml`
      (lista hardcoded di numeri verificati: costi software,
      benchmark mercato). Numeri arbitrari inventati → FAIL.
- [ ] Nomi clienti citati devono essere generici ("Studio commercialista X")
      o presenti in `docs/piano-strategico/case-studies-anonimi.yaml`

---

## 8. Failure modes e mitigazioni

| Cosa può andare male | Probabilità | Mitigazione |
|---|---|---|
| Articolo dà troppe info, lettore implementa da solo | Media | Validator teaser + revisione manuale primi 10 |
| Voce brand drift dopo 30+ articoli | Media | Skill versionato + Luigi rivede 1 articolo/mese random |
| Google penalty per AI content massivo | Bassa | Throttle 3/settimana max, edit pass riduce AI signal, articoli teaser sono comunque utili al lettore |
| Articoli ripetitivi (cluster overlap) | Media | Validator controlla similarità Levenshtein tra articoli stesso pillar > 0.6 → FAIL |
| Cron non parte | Bassa | GitHub Actions sla, alert email se fallisce |
| Claude API down | Bassa | Retry 3x con backoff, alert email se fallisce |
| Numeri inventati che danneggiano credibilità | Media | facts-allowed.yaml è whitelist, tutto fuori da lì → FAIL |
| Articolo duplica argomento di articolo esistente | Bassa | Check titolo + keyword primaria contro pubblicati |
| Costo Claude esplode | Bassa | Throttle hard 5 articoli/settimana, budget alert se > €5/mese |

---

## 9. Metriche di successo

A 3 mesi dall'avvio:
- 24+ articoli pubblicati senza intervento Luigi
- 0 articoli rifiutati per qualità da Luigi (al di fuori dei validator)
- ≥ 5 articoli ranked nei primi 30 di Google su keyword target
- ≥ 500 visite/mese organic ai /blog/*
- ≥ 5 sessioni K-BOT/mese provenienti da blog (UTM tracking)

A 12 mesi:
- 60+ articoli pubblicati
- ≥ 30 articoli ranked nei primi 10 di Google
- ≥ 5.000 visite/mese organic ai /blog/*
- ≥ 75 sessioni K-BOT/mese da blog
- ≥ 3 lead Tier 1 (49€) attribuibili al blog

Tracking via PostHog (già installato). UTM parameters sui CTA del blog.

---

## 10. Roadmap implementazione

| Fase | Cosa faccio | Tempo | Quando |
|---|---|---|---|
| **0** | Tu approvi questo file | 0 | Adesso |
| **1** | Costruisco `keyword-map.yaml` con 60 righe (10 pillar × 6 angoli) + `facts-allowed.yaml` + `case-studies-anonimi.yaml` | 3h | Settimana 1 |
| **2** | Tu rivedi keyword map, modifichi se vuoi diverso angle | 1h tua | Settimana 1 |
| **3** | Costruisco template HTML `_template.html` + CSS blog | 2h | Settimana 1 |
| **4** | Costruisco prompts (article-draft.md, article-revise.md, brief-expand.md) | 3h | Settimana 1 |
| **5** | Costruisco orchestrator `generate-article.ts` + 4 validatori | 6h | Settimana 2 |
| **6** | Genero MANUALMENTE 3 articoli pilota → tu revisioni → calibriamo skill | 4h mie + 1h tua | Settimana 2 |
| **7** | Setup GitHub Actions cron + secret RAILWAY/ANTHROPIC | 1h | Settimana 2 |
| **8** | Genero altri 3 articoli con cron attivo (manual trigger) → verifica end-to-end | 1h | Settimana 3 |
| **9** | Attivo cron automatico 3x/settimana | 0 | Settimana 3 |
| **10** | Pagina `/blog` indice + nav "Risorse" | 2h | Settimana 3 |
| **11** | Report email settimanale a Luigi (articoli pubblicati, traffico, costo Claude) | 2h | Settimana 4 |

**Totale lavoro mio**: ~22h sviluppo (una tantum) + ~€30 Claude API per i 60 articoli.
**Totale lavoro tuo**: ~6h iniziali (review keyword map + 3 pilota) + ~30min/mese a regime.

---

## 11. Cosa NON faccio (out of scope esplicito)

- Articoli "news" o "trend AI" (vivono male senza editorial team)
- Video / podcast
- Newsletter editoriale (separato da newsletter-iscrizione esistente)
- Traduzioni multilingua (ICP solo IT)
- LinkedIn cross-posting automatico (futuro, fase 2)
- Generazione immagini per articolo (per ora niente immagini, layout solo testo + box CTA)
- Comments / community sul blog
- Personalizzazione per visitatore (no recommendation engine)

---

## 12. Cosa serve da te per partire

1. **Approvazione di questo file** (vai/non vai)
2. **Eventuali correzioni** alla strategia teaser (sezione 2): cosa diciamo, cosa NON diciamo
3. **Lista clienti anonimizzabili**: anche solo 5-10 casi reali tuoi con numeri prima/dopo. Li uso nel `case-studies-anonimi.yaml` per dare carne ai 60 articoli.
4. **Lista costi software competitor verificati**: HubSpot, Zapier, n8n, Make, Salesforce, plug-in vari. Per `facts-allowed.yaml`. Se non li hai, li recupero io ma poi tu verifichi.
5. **Telegram chat ID** (opzionale): se vuoi alert su Telegram quando articolo fallisce validazione.
6. **Conferma budget Claude API**: €30 una tantum + €5/mese a regime. OK?

Quando hai questi 6 punti chiari, parto con Fase 1.

---

## 13. Domande aperte per discussione

- D1: 3 articoli/settimana è ritmo giusto? Più lento (2/sett) = meno rischio di sembrare content farm. Più veloce (5/sett) = traffico cresce prima ma più rischio Google penalty.
- D2: Vogliamo immagini negli articoli o solo testo? Generare immagini = +€0.10/articolo + rischio "AI image obvious". Solo testo = più pulito, più veloce.
- D3: CTA fissa "Apri K-BOT" oppure variabile per pillar (es. su pillar legale CTA va a "Parla con specialista contratti")?
- D4: Apriamo i commenti? Probabilmente NO (no community management).
- D5: Cosa facciamo quando i 60 articoli sono finiti? Si rinnova la keyword map o si passa a fase 2 (es. webinar, case study lunghi, white paper)?

---

**Fine documento. Aspetto la tua approvazione (o correzioni) prima di scrivere una riga di codice.**
