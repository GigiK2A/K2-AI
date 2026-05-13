# Integrazione Piattaforma — Tool Custom StrategyBoost

Questo documento descrive i tool custom disponibili quando la skill `flusso-strategyboost-pmi` gira in modalita piattaforma SaaS (Agent SDK backend). In modalita consulenziale (Cowork/Claude Code), questi tool non sono disponibili e la skill degrada gracefully.

---

## Architettura

```
Client (Frontend React)
  |
  v
API Gateway (autenticazione, tenant isolation)
  |
  v
Agent SDK (orchestratore Claude + skill)
  |
  v
Tool Layer (tool custom sotto)
  |
  v
Database (PostgreSQL multi-tenant) + Storage (S3 per file)
```

Ogni invocazione e isolata per tenant (azienda cliente). I dati strategici non vengono mai condivisi tra tenant.

---

## Tool Custom

### 1. analizza_settore

**Scopo**: recuperare dati strutturati su un settore economico italiano (dimensione mercato, crescita, concentrazione, trend).

**Invocazione**:
```json
{
  "tool": "analizza_settore",
  "input": {
    "settore_ateco": "C25.1",
    "descrizione_settore": "fabbricazione di elementi da costruzione in metallo",
    "area_geografica": "nord-est",
    "anno_riferimento": 2024
  }
}
```

**Output**:
```json
{
  "status": "success",
  "settore": {
    "codice_ateco": "C25.1",
    "descrizione": "Fabbricazione di elementi da costruzione in metallo",
    "dimensione_mercato_mln_eur": 8500,
    "crescita_annua_pct": 2.3,
    "num_imprese_italia": 12500,
    "num_imprese_area": 3200,
    "concentrazione": "bassa",
    "indice_herfindahl": 0.04,
    "margine_ebitda_mediano": 10.2,
    "trend_principali": [
      "Domanda trainata da PNRR e infrastrutture",
      "Pressione costi materie prime (acciaio +15% YoY)",
      "Crescente richiesta certificazioni (EN 1090, SOA)"
    ],
    "fase_ciclo": "maturita_con_picchi",
    "export_quota_pct": 28.5
  }
}
```

**Timeout**: 15s (sync)

---

### 2. analizza_competitor

**Scopo**: recuperare informazioni strutturate sui competitor indicati dall'utente (dati pubblici: bilanci, prodotti, posizionamento).

**Invocazione**:
```json
{
  "tool": "analizza_competitor",
  "input": {
    "competitors": [
      {
        "nome": "MetalSud Srl",
        "partita_iva": "01234567890",
        "sito_web": "https://www.metalsud.it"
      },
      {
        "nome": "Carpenteria Rossi SpA",
        "sito_web": "https://www.carpenteriarossi.it"
      }
    ],
    "settore_ateco": "C25.1",
    "metriche_richieste": ["fatturato", "dipendenti", "margini", "prodotti", "posizionamento"]
  }
}
```

**Output**:
```json
{
  "status": "success",
  "competitors": [
    {
      "nome": "MetalSud Srl",
      "fatturato_eur": 4200000,
      "dipendenti": 28,
      "ebitda_margin_pct": 12.5,
      "prodotti_principali": ["carpenteria pesante", "strutture prefabbricate", "lavorazioni conto terzi"],
      "posizionamento": "generalista medio-basso prezzo",
      "punti_forza": ["capacita produttiva", "prezzo competitivo", "consegne rapide"],
      "punti_debolezza": ["no certificazioni speciali", "nessun export", "dipendenza da edilizia locale"],
      "trend_fatturato_3y": "+8% CAGR",
      "fonte": "bilancio_depositato_2023"
    }
  ]
}
```

**Timeout**: 30s (sync, include scraping siti competitor)

---

### 3. benchmark_strategico

**Scopo**: fornire benchmark strategici di settore per contestualizzare il posizionamento dell'azienda.

**Invocazione**:
```json
{
  "tool": "benchmark_strategico",
  "input": {
    "settore_ateco": "C25.1",
    "area_geografica": "nord-est",
    "dimensione": "5-50_dipendenti",
    "metriche": [
      "intensita_competitiva",
      "fattori_critici_successo",
      "strategie_prevalenti",
      "barriere_entrata",
      "margini_settore",
      "quota_export"
    ]
  }
}
```

**Output**:
```json
{
  "status": "success",
  "benchmark": {
    "intensita_competitiva": "alta",
    "score_5_forze": {
      "rivalita": 3.8,
      "nuovi_entranti": 2.5,
      "potere_fornitori": 3.2,
      "potere_clienti": 3.5,
      "sostituti": 2.0,
      "media": 3.0
    },
    "fattori_critici_successo": [
      {"fattore": "Qualita e certificazioni", "importanza": 5},
      {"fattore": "Flessibilita produttiva", "importanza": 4},
      {"fattore": "Relazione col cliente", "importanza": 4}
    ],
    "strategie_prevalenti": [
      "Focalizzazione su nicchia tecnica (45% imprese top quartile)",
      "Leadership di costo locale (30%)",
      "Diversificazione correlata (25%)"
    ],
    "margini_settore": {
      "ebitda_mediana": 10.2,
      "ebitda_q1": 6.5,
      "ebitda_q3": 15.0,
      "ros_mediana": 5.8
    },
    "barriere_entrata": {
      "capitale_minimo_eur": 250000,
      "certificazioni_richieste": ["EN 1090", "SOA"],
      "tempo_costruzione_reputazione_anni": 3
    }
  }
}
```

**Timeout**: 10s (sync)

---

### 4. save_to_tenant_storage

**Scopo**: salvare i file deliverable (DOCX, XLSX, HTML, JSON) nello storage del tenant.

**Invocazione**:
```json
{
  "tool": "save_to_tenant_storage",
  "input": {
    "tenant_id": "uuid-tenant",
    "job_id": "uuid-job",
    "files": [
      {
        "filename": "report-strategico-acme-srl.docx",
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "content_base64": "UEsDBBQ...",
        "category": "report_strategico"
      },
      {
        "filename": "mappa-strategica-acme-srl.xlsx",
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "content_base64": "UEsDBBQ...",
        "category": "mappa_strategica"
      },
      {
        "filename": "dashboard-strategica-acme-srl.html",
        "content_type": "text/html",
        "content_base64": "PCFET0NUW...",
        "category": "dashboard"
      },
      {
        "filename": "output-strategico-acme-srl.json",
        "content_type": "application/json",
        "content_base64": "eyJtZXRh...",
        "category": "output_json"
      }
    ]
  }
}
```

**Output**:
```json
{
  "status": "success",
  "files_saved": 4,
  "urls": {
    "report_strategico": "https://storage.example.com/tenant-uuid/job-uuid/report-strategico-acme-srl.docx",
    "mappa_strategica": "https://storage.example.com/tenant-uuid/job-uuid/mappa-strategica-acme-srl.xlsx",
    "dashboard": "https://storage.example.com/tenant-uuid/job-uuid/dashboard-strategica-acme-srl.html",
    "output_json": "https://storage.example.com/tenant-uuid/job-uuid/output-strategico-acme-srl.json"
  },
  "expires_at": "2025-07-16T00:00:00Z"
}
```

**Timeout**: 30s (async per upload, sync per conferma)

---

### 5. update_job_progress

**Scopo**: aggiornare la progress bar del job nella UI del frontend.

**Invocazione**:
```json
{
  "tool": "update_job_progress",
  "input": {
    "job_id": "uuid-job",
    "progress_pct": 45,
    "step_current": 3,
    "step_total": 7,
    "step_name": "Analisi risorse e competenze",
    "message": "Valutazione VRIO delle risorse aziendali in corso..."
  }
}
```

**Output**:
```json
{
  "status": "success",
  "acknowledged": true
}
```

**Timeout**: 2s (sync, fire-and-forget OK)

---

## Mapping Step → Tool

| Step | Tool custom | Fallback consulenziale |
|---|---|---|
| 1 - Discovery | `analizza_settore` | WebSearch + ragionamento strutturato |
| 2 - Analisi settore | `analizza_competitor`, `benchmark_strategico` | WebSearch, WebFetch + framework references |
| 3 - Risorse/competenze | — (input utente) | Domande guidate al cliente |
| 4 - Posizionamento | `benchmark_strategico` | References + analisi qualitativa |
| 5 - Opzioni strategiche | — (ragionamento) | Framework Ansoff + teoria dei giochi |
| 6 - Piano strategico | — (ragionamento) | Skill marketing-strategico |
| 7 - Deliverable | `save_to_tenant_storage` | Generazione diretta file (docx, xlsx skill) |
| Tutti | `update_job_progress` | Output progressivo in chat |

---

## Note di integrazione

- **Tenant isolation**: ogni chiamata tool include `tenant_id` implicito (iniettato dall'API Gateway). La skill non deve mai gestire tenant_id direttamente.
- **Rate limiting**: max 50 chiamate tool per job. La skill ne usa tipicamente 8-12.
- **Error handling**: se un tool fallisce, la skill deve:
  1. Loggare l'errore nell'output JSON (`warnings` array)
  2. Procedere con fallback (dati di reference o ragionamento)
  3. Segnalare nel report la limitazione
- **Idempotenza**: il job puo essere rieseguito. I file vengono sovrascritti nello storage.
