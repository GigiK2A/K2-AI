# Integrazione Piattaforma — Tool Custom FinanceBoost

Questo documento descrive i tool custom disponibili quando la skill `flusso-financeboost-pmi` gira in modalita piattaforma SaaS (Agent SDK backend). In modalita consulenziale (Cowork/Claude Code), questi tool non sono disponibili e la skill degrada gracefully.

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

Ogni invocazione e isolata per tenant (azienda cliente). I dati di bilancio non vengono mai condivisi tra tenant.

---

## Tool Custom

### 1. parse_bilancio

**Scopo**: parsare un file PDF o XLSX di bilancio civilistico italiano e restituire un oggetto strutturato.

**Invocazione**:
```json
{
  "tool": "parse_bilancio",
  "input": {
    "file_id": "uuid-del-file-caricato",
    "format": "pdf|xlsx",
    "anni": [2023, 2022, 2021]
  }
}
```

**Output**:
```json
{
  "status": "success",
  "bilancio": {
    "anni": [2023, 2022, 2021],
    "stato_patrimoniale": {
      "2023": {
        "attivo": {
          "immobilizzazioni_immateriali": 50000,
          "immobilizzazioni_materiali": 320000,
          "immobilizzazioni_finanziarie": 15000,
          "rimanenze": 180000,
          "crediti_commerciali": 290000,
          "crediti_altri": 45000,
          "disponibilita_liquide": 35000,
          "ratei_risconti_attivi": 12000,
          "totale_attivo": 947000
        },
        "passivo": {
          "capitale_sociale": 100000,
          "riserve": 85000,
          "utile_esercizio": 62000,
          "totale_patrimonio_netto": 247000,
          "tfr": 95000,
          "debiti_finanziari_mlt": 180000,
          "debiti_finanziari_bt": 120000,
          "debiti_commerciali": 230000,
          "debiti_tributari": 35000,
          "debiti_altri": 28000,
          "ratei_risconti_passivi": 12000,
          "totale_passivo": 947000
        }
      }
    },
    "conto_economico": {
      "2023": {
        "ricavi_vendite": 1850000,
        "altri_ricavi": 25000,
        "valore_produzione": 1875000,
        "costi_materie": 680000,
        "costi_servizi": 420000,
        "godimento_beni_terzi": 65000,
        "costo_personale": 480000,
        "ammortamenti": 72000,
        "svalutazioni": 8000,
        "variazione_rimanenze": -15000,
        "oneri_diversi": 18000,
        "totale_costi_produzione": 1758000,
        "differenza_ab": 117000,
        "proventi_finanziari": 2000,
        "oneri_finanziari": 28000,
        "saldo_gestione_finanziaria": -26000,
        "risultato_ante_imposte": 91000,
        "imposte": 29000,
        "utile_netto": 62000
      }
    },
    "warnings": ["Nota: voce B.14 non presente nel PDF, assunta pari a 0"]
  }
}
```

**Modalita sincrona**: risposta entro 10 secondi per XLSX, fino a 30 secondi per PDF (OCR).
**Errori comuni**: PDF non leggibile (scan di bassa qualita), formato non standard, bilancio abbreviato vs ordinario.

---

### 2. calcola_indici

**Scopo**: calcolare tutti i KPI finanziari a partire dal bilancio strutturato.

**Invocazione**:
```json
{
  "tool": "calcola_indici",
  "input": {
    "bilancio": { "...output di parse_bilancio..." },
    "settore_ateco": "C25",
    "num_dipendenti": 22
  }
}
```

**Output**:
```json
{
  "status": "success",
  "indici": {
    "redditivita": {
      "roe": { "valore": 25.1, "benchmark_mediana": 9.5, "benchmark_q3": 16.8, "semaforo": "verde" },
      "roi": { "valore": 12.4, "benchmark_mediana": 7.2, "benchmark_q3": 12.1, "semaforo": "verde" },
      "ros": { "valore": 6.3, "benchmark_mediana": 5.8, "benchmark_q3": 9.5, "semaforo": "giallo" },
      "ebitda_margin": { "valore": 10.6, "benchmark_mediana": 10.2, "benchmark_q3": 15.0, "semaforo": "giallo" },
      "utile_fatturato": { "valore": 3.4, "benchmark_mediana": 3.0, "benchmark_q3": 5.5, "semaforo": "giallo" }
    },
    "liquidita": {
      "current_ratio": { "valore": 1.28, "benchmark_mediana": 1.35, "semaforo": "giallo" },
      "quick_ratio": { "valore": 0.85, "benchmark_mediana": 0.95, "semaforo": "giallo" },
      "ccn": { "valore": 120000, "semaforo": "verde" },
      "dso": { "valore": 57, "benchmark_mediana": 72, "semaforo": "verde" },
      "dpo": { "valore": 48, "benchmark_mediana": 65, "semaforo": "giallo" },
      "dio": { "valore": 42, "benchmark_mediana": 55, "semaforo": "verde" },
      "ccc": { "valore": 51, "benchmark_mediana": 62, "semaforo": "verde" }
    },
    "solidita": { "..." },
    "efficienza": { "..." },
    "crescita": { "..." }
  },
  "du_pont": {
    "ros": 6.3,
    "rotazione": 1.96,
    "leverage": 3.83,
    "roe_calcolato": 47.3,
    "roe_effettivo": 25.1,
    "erosione_finanziaria_fiscale": 22.2
  }
}
```

**Modalita sincrona**: risposta entro 2 secondi.

---

### 3. benchmark_settore

**Scopo**: restituire i benchmark di settore per un dato codice ATECO.

**Invocazione**:
```json
{
  "tool": "benchmark_settore",
  "input": {
    "ateco": "C25",
    "fascia_dipendenti": "11-50",
    "area_geografica": "nord-ovest"
  }
}
```

**Output**:
```json
{
  "status": "success",
  "settore": "Fabbricazione di prodotti in metallo",
  "macro_settore": "manifatturiero",
  "fonte": "AIDA Bureau van Dijk - ultimo aggiornamento 2024-Q2",
  "campione": 4250,
  "benchmark": {
    "roe": { "mediana": 9.8, "q1": 4.5, "q3": 17.2 },
    "roi": { "mediana": 7.5, "q1": 3.8, "q3": 12.5 },
    "ros": { "mediana": 6.1, "q1": 3.0, "q3": 10.0 },
    "ebitda_margin": { "mediana": 10.5, "q1": 6.8, "q3": 15.5 },
    "de_ratio": { "mediana": 1.7, "q1": 0.7, "q3": 3.0 },
    "current_ratio": { "mediana": 1.38, "q1": 1.08, "q3": 1.80 },
    "dso": { "mediana": 70, "q1": 46, "q3": 92 },
    "dpo": { "mediana": 62, "q1": 38, "q3": 82 },
    "dio": { "mediana": 52, "q1": 28, "q3": 80 }
  }
}
```

**Modalita sincrona**: risposta entro 1 secondo (lookup da database).

---

### 4. genera_budget

**Scopo**: generare un budget previsionale a 12 mesi con 3 scenari.

**Invocazione**:
```json
{
  "tool": "genera_budget",
  "input": {
    "bilancio": { "...output di parse_bilancio..." },
    "indici": { "...output di calcola_indici..." },
    "ipotesi": {
      "crescita_ricavi_base": 0.03,
      "crescita_ricavi_ottimistico": 0.08,
      "crescita_ricavi_pessimistico": -0.05,
      "variazione_costi_personale": 0.04,
      "investimenti_previsti": 50000,
      "note": "Possibile perdita cliente X (15% fatturato) nello scenario pessimistico"
    }
  }
}
```

**Output**:
```json
{
  "status": "success",
  "budget": {
    "scenario_base": {
      "mesi": [
        { "mese": 1, "ricavi": 158000, "costi_variabili": 95000, "costi_fissi": 42000, "ebitda": 21000, "utile_netto": 8500 }
      ],
      "totale_anno": { "ricavi": 1905000, "ebitda": 198000, "utile_netto": 72000 },
      "bep_mese": 4
    },
    "scenario_ottimistico": { "..." },
    "scenario_pessimistico": { "..." }
  }
}
```

**Modalita asincrona**: puo richiedere fino a 15 secondi per calcoli complessi. Usa `update_job_progress` per aggiornare il frontend.

---

### 5. save_to_tenant_storage

**Scopo**: salvare i file generati (DOCX, XLSX, HTML, JSON) nello storage del tenant.

**Invocazione**:
```json
{
  "tool": "save_to_tenant_storage",
  "input": {
    "tenant_id": "auto",
    "job_id": "uuid-del-job",
    "files": [
      { "name": "report-finanziario.docx", "content_base64": "...", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document" },
      { "name": "cruscotto-kpi.xlsx", "content_base64": "...", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
      { "name": "dashboard.html", "content_base64": "...", "mime": "text/html" },
      { "name": "output.json", "content_base64": "...", "mime": "application/json" }
    ]
  }
}
```

**Output**:
```json
{
  "status": "success",
  "files": [
    { "name": "report-finanziario.docx", "url": "https://storage.example.com/tenant/xxx/job/yyy/report-finanziario.docx", "size_bytes": 245000 }
  ]
}
```

**Tenant isolation**: il `tenant_id: "auto"` viene risolto dal middleware di autenticazione. Un tenant non puo mai accedere ai file di un altro tenant.

---

### 6. update_job_progress

**Scopo**: aggiornare la barra di avanzamento nel frontend durante l'elaborazione.

**Invocazione**:
```json
{
  "tool": "update_job_progress",
  "input": {
    "job_id": "uuid-del-job",
    "progress": 45,
    "step": "Analisi indici e benchmark",
    "message": "Calcolo KPI di redditivita completato, avvio analisi liquidita..."
  }
}
```

**Mapping step/progress consigliato**:

| Step | Progress | Descrizione |
|---|---|---|
| 1 | 5-15% | Acquisizione e parsing bilancio |
| 2 | 15-25% | Riclassificazione |
| 3 | 25-45% | Analisi indici e benchmark |
| 4 | 45-55% | Analisi marginalita |
| 5 | 55-65% | Valutazione performance |
| 6 | 65-80% | Proiezioni e scenari |
| 7 | 80-100% | Generazione deliverable |

---

## Endpoint

| Tipo | Endpoint | Metodo | Uso |
|---|---|---|---|
| Sincrono | `/api/v1/tools/{tool_name}` | POST | parse_bilancio, calcola_indici, benchmark_settore |
| Asincrono | `/api/v1/jobs` | POST | genera_budget (job lungo) |
| Polling | `/api/v1/jobs/{job_id}` | GET | Stato del job asincrono |
| WebSocket | `/ws/jobs/{job_id}` | WS | Aggiornamenti real-time progress |
| Storage | `/api/v1/storage/files` | POST | save_to_tenant_storage |

## Autenticazione e Tenant Isolation

- Ogni richiesta porta un JWT con `tenant_id` e `user_id`
- Il middleware inietta automaticamente `tenant_id` in ogni query al database
- Row-Level Security (RLS) su PostgreSQL garantisce isolamento anche in caso di bug applicativo
- I file in S3 sono organizzati per `tenant_id/job_id/` con policy IAM per tenant
- Log di audit per ogni operazione su dati sensibili (bilanci)

## Graceful Degradation

Quando un tool non e disponibile (modalita consulenziale), la skill deve:

1. **Non fallire**: procedere con calcolo manuale o stima ragionata
2. **Annotare**: segnalare nel report che il dato e stimato e non calcolato da strumento dedicato
3. **Suggerire**: indicare che in modalita piattaforma il dato sarebbe piu preciso
4. **Mantenere la struttura**: l'output JSON deve avere la stessa struttura, con campo `source: "manual_estimate"` invece di `source: "tool"`
