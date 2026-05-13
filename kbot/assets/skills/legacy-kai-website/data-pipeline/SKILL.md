---
name: data-pipeline
description: >-
  Progettazione pipeline dati per PMI: ETL da gestionali italiani, qualità
  dati, scheduling con n8n/Make, warehouse su Supabase/BigQuery, dashboard
  operativa. Copertura dati commerciali, produzione, finanza.
---

# Data Pipeline — Automazione Dati PMI

## Architettura pipeline PMI standard

```
SORGENTI          INGESTIONE        STORAGE            CONSUMO
─────────         ──────────        ───────            ───────
Gestionale  ──→   ETL (n8n/         Supabase     ──→   Dashboard
ERP         ──→   Make/custom)  ──→ PostgreSQL   ──→   Report PDF
Fogli Google──→                     Data Warehouse──→  Alert email
CRM         ──→                     (BigQuery)    ──→  AI/RAG
Form/webhook──→                                   ──→  Esportazione
```

## ETL — fasi

### Extract
- REST API polling (ogni 15min/1h/24h per volume)
- File drop (CSV/XLSX in cartella → trigger)
- Webhook push (real-time)
- Database replication (Postgres CDC via Supabase realtime)

### Transform — operazioni comuni

| Operazione | Esempio |
|------------|---------|
| Normalizza date | `dd/mm/yyyy` → ISO 8601 `yyyy-mm-dd` |
| Converti importi | Stringa "€ 1.234,56" → float 1234.56 |
| Deduplication | Upsert su chiave `codice_cliente + data` |
| Lookup codici | Codice prodotto → categoria merceologica |
| Calcola metriche | `margine = ricavi - costi_diretti` |
| Enrich | Aggiungi ATECO, CAP → regione, P.IVA → ragione sociale |

### Load
- Upsert su Supabase (PostgreSQL): `ON CONFLICT DO UPDATE`
- Append-only per log/eventi (mai modificare storico)
- Soft delete: `deleted_at` timestamp, non DELETE fisico

## Qualità dati — regole obbligatorie

```
Completezza:  campi obbligatori presenti > 95%
Unicità:      no duplicati su chiave primaria
Validità:     P.IVA 11 cifre, CF 16 car., IBAN IT27+18
Consistenza:  data_fine ≥ data_inizio, importo > 0
Freschezza:   dati core aggiornati entro SLA (es. 1h per vendite)
```

Implementa check con SQL assertion o n8n IF node:
```sql
-- Esempio quality check giornaliero
SELECT COUNT(*) as righe_problematiche
FROM ordini
WHERE cliente_id IS NULL
   OR importo <= 0
   OR data_ordine > CURRENT_DATE
```

## Scheduling — criteri di frequenza

| Tipo dato | Frequenza | Motivo |
|-----------|-----------|--------|
| Vendite/ordini | 15-30 min | Decisioni operative intraday |
| Magazzino/stock | 1h | Bilanciamento scorte |
| Fatturazione | 2h | Riconciliazione pagamenti |
| HR / presenze | Giornaliera (06:00) | Elaborazioni batch notturne |
| Bilancio | Settimanale | Consolidamento dati |
| KPI strategici | Mensile | Reporting management |

## Pattern Supabase PostgreSQL per PMI

```sql
-- Tabella vendite denormalizzata per velocità query
CREATE TABLE vendite_agg (
  id          BIGSERIAL PRIMARY KEY,
  data        DATE NOT NULL,
  cliente_id  TEXT NOT NULL,
  prodotto    TEXT,
  quantita    NUMERIC(12,3),
  importo_netto NUMERIC(12,2),
  margine     NUMERIC(12,2),
  agente      TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  source      TEXT -- 'gestionale', 'ecommerce', 'manuale'
);

CREATE INDEX ON vendite_agg(data, cliente_id);
CREATE INDEX ON vendite_agg(data, agente);
```

## Gestione errori pipeline

- **Dead letter queue**: righe fallite → tabella `etl_errors(ts, source, row_data, error_msg)`
- **Retry policy**: max 3 tentativi con backoff 1min/5min/30min
- **Alert soglia**: se `etl_errors > 10 in 1h` → email alert
- **Idempotenza**: ogni run può girare 2x senza doppi inserimenti (upsert, non insert)

## Stack raccomandato K2-AI per PMI

```
Orchestration:  n8n self-host (Railway, ~15€/mese) o Make (free 1000 ops)
Storage:        Supabase EU Frankfurt (free 500MB, poi 25€/mese)
Trasformazioni: JavaScript inline n8n o Python script su Railway
Dashboard:      Supabase + Metabase (self-host) o Google Looker Studio
Alerting:       Resend email + webhook Slack/Teams
Costo totale:   20-50€/mese per PMI < 50 dipendenti
```

## Anti-pattern da evitare

- **Mai SELECT * in produzione**: specifica sempre le colonne
- **No logica business nel DB**: mantienila nell'ETL, non in trigger SQL
- **Non eliminare raw data**: archivia sempre l'originale prima di trasformare
- **No credenziali hardcoded**: sempre env vars, mai in codice o n8n variabili hardcoded
