# Integrazione con la piattaforma SaaS — Contratto tecnico

Questo file descrive come la skill `flusso-webboost-pmi` si integra con la piattaforma SaaS in sviluppo. Quando la skill gira in modalità piattaforma (dentro Agent SDK su backend), deve rispettare il contratto qui definito. Quando gira in modalità consulenziale (Cowork/Claude Code), questi tool non esistono e la skill degrada gracefully su WebFetch/WebSearch/ragionamento.

---

## 1. Flow di invocazione in piattaforma

```
Cliente PMI nel frontend
    │
    ▼
POST /api/modules/webboost/run
    {
      tenant_id: "...",
      client_id: "...",
      input: {
        url: "https://cliente.it",
        settore: "studio commercialista",
        area_geografica: "Milano",
        keywords_seed: ["commercialista milano", "consulenza fiscale startup", "partita iva regime forfettario"],
        obiettivo: "lead_generation",
        competitor: ["https://...", "https://..."],
        brand_voice_docs: ["s3://..."],
        budget_mensile: 2000
      }
    }
    │
    ▼
Job Dispatcher (Inngest/BullMQ)
    │ → task asincrono, ritorna job_id
    ▼
Worker Agent SDK
    │
    ├─ carica skill: /skills/flusso-webboost-pmi/
    ├─ carica tenant context (dati cliente)
    ├─ carica tool custom (vedi sez. 2)
    ├─ esegue il workflow a 7 step della skill
    │
    ▼
Output JSON + file (DOCX/XLSX/HTML) → S3
    │
    ▼
Webhook → frontend notifica utente
    │
    ▼
Dashboard renderizza JSON + link ai file
```

---

## 2. Tool custom attesi dalla piattaforma

La skill si aspetta che questi tool siano disponibili nel runtime quando in modalità piattaforma. Quando non lo sono (modalità Cowork), la skill usa fallback con WebFetch/WebSearch.

### 2.1 `fetch_page_content(url, render_js=true)`
Scarica HTML renderizzato di una pagina (con JS eseguito). Fallback: `WebFetch`.
Output: `{ status, html, meta_tags, headings, links, images, text_content, load_time_ms }`

### 2.2 `fetch_sitemap(domain)`
Scarica e parsa `sitemap.xml`. Fallback: tentare `{domain}/sitemap.xml` via WebFetch.
Output: `{ urls: [...], count, last_modified }`

### 2.3 `lighthouse_audit(url)`
Esegue audit Lighthouse (performance, accessibility, SEO, best practices).
Fallback: stima qualitativa, annotare "serve strumento dedicato".
Output: `{ scores: {performance, accessibility, seo, best_practices}, core_web_vitals: {lcp, inp, cls}, opportunities: [...] }`

### 2.4 `keyword_research(seed_keywords, geo, language)`
Espande keyword via API SEMrush/Ahrefs/DataForSEO.
Fallback: espansione basata su ragionamento linguistico + WebSearch per SERP snapshot.
Output: `{ keywords: [{kw, volume, difficulty, intent, cpc, trend}, ...] }`

### 2.5 `serp_data(keyword, geo, language)`
Restituisce top 20 risultati Google per la keyword, con metadati.
Fallback: WebSearch + parsing manuale.
Output: `{ organic: [...], featured_snippet, people_also_ask, related_searches, local_pack }`

### 2.6 `competitor_discovery(domain, topic)`
Identifica 5–10 competitor SEO del dominio sul topic.
Fallback: ragionamento + WebSearch mirata.
Output: `{ competitors: [{domain, overlap_score, strengths}, ...] }`

### 2.7 `backlink_sample(domain)`
Campione di 20–50 backlink del dominio con metriche di qualità.
Fallback: non disponibile in consulenziale. Skippare o nota "serve tool dedicato".
Output: `{ backlinks: [...], domain_rating, referring_domains }`

### 2.8 `gbp_data(business_name, geo)`
Dati Google Business Profile: presenza, rating, recensioni, foto, categorie.
Fallback: WebSearch del nome business + ispezione manuale.
Output: `{ exists, rating, reviews_count, categories, hours, ...}`

### 2.9 `save_to_tenant_storage(path, content)`
Salva file nella storage del tenant (S3/R2 con partitioning per tenant_id).
Fallback: save locale in `/sessions/focused-exciting-feynman/mnt/outputs/`.

### 2.10 `update_job_progress(job_id, step, percent)`
Aggiorna progresso del job nel database per UX real-time.
Fallback: no-op.

---

## 3. Schema JSON output (vincolante)

L'output JSON finale deve rispettare `schemas/output-schema.json`. È il contratto API tra skill e frontend. Cambiarlo implica coordinare dev + skill + UI.

Sezioni principali:
- `meta` — tenant, cliente, run, data, versione skill
- `input` — echo degli input ricevuti
- `diagnosi` — array di findings per area (seo_technical, seo_onpage, ux_copy, brand_voice, content, local)
- `keyword_map` — universo keyword con priorità
- `piano_editoriale` — articoli programmati
- `articoli_pronti` — markdown full dei 2 articoli generati
- `roadmap` — azioni con impact/effort/priority/responsabile/deadline/kpi
- `kpi_dashboard` — metriche da monitorare con baseline
- `files` — riferimenti a DOCX/XLSX/HTML salvati

---

## 4. Versionamento e compatibilità

La skill deve includere nel JSON:
```json
"meta": {
  "skill_name": "flusso-webboost-pmi",
  "skill_version": "1.0.0",
  "schema_version": "1.0"
}
```

Quando cambiamo la skill:
- **Patch** (1.0.0 → 1.0.1): fix di testo, non cambia output → nessuna azione backend.
- **Minor** (1.0.0 → 1.1.0): nuovi campi opzionali nel JSON → backend retrocompatibile.
- **Major** (1.0.0 → 2.0.0): cambia schema in modo breaking → serve migrazione frontend + backend.

Mantenere sempre almeno 2 versioni supportate per cliente in rolling upgrade.

---

## 5. Osservabilità e cost tracking

La skill stessa non logga nulla: è Agent SDK che espone token usage. Il backend deve catturare e salvare per tenant:
- token input + output per chiamata Claude
- numero di chiamate tool custom per run
- durata totale del run
- costo stimato in €

Budget target per singolo run WebBoost completo:
- Token: <800k input, <200k output
- Chiamate tool custom: <30
- Durata: <20 minuti
- Costo Claude (Sonnet): <3–5 € per run

Se un run supera 1,5x il budget → alert al team ops, eventualmente kill.

---

## 6. Sincrono vs asincrono

WebBoost ha **tre endpoint** logici:

- **`/webboost/run-full`** (asincrono, 5–15 min): audit completo mensile. Job in coda, webhook al completamento.
- **`/webboost/chat`** (sincrono, <30 s): chat "chiedi al SEO assistant" su un sito già caricato. Risposta streaming.
- **`/webboost/refresh-keyword`** (sincrono, <60 s): aggiorna solo la keyword map con nuovi dati SERP.

La skill `flusso-webboost-pmi` è il motore del primo endpoint. Per chat e refresh servono skill più piccole derivate (`webboost-chat`, `webboost-keyword-refresh`) che riusano i reference file di questa.

---

## 7. Sicurezza e tenant isolation

- Tutti i file prodotti vanno salvati in path partizionati per tenant: `/tenants/{tenant_id}/clients/{client_id}/webboost/{run_id}/`.
- Nessun dato di un tenant deve mai entrare nel context di un altro tenant. Il worker Agent SDK va istanziato fresh per ogni run o con strict context reset.
- I file dei competitor/brand voice caricati dal cliente vanno validati (no PII terzi, no malware).
- Log devono redactare URL e nomi cliente prima di essere inviati a observability esterna.
