---
name: audit-trail
description: >-
  Audit trail e tracciabilità operazioni per PMI italiane: requisiti GDPR,
  SOX-lite, conservazione log, struttura evento immutabile, strumenti di
  implementazione, compliance per settori regolamentati (finance, sanità, PA).
---

# Audit Trail — Tracciabilità e Compliance

## Cos'è un audit trail

Registro cronologico immutabile di chi ha fatto cosa, quando, su quale dato. Obbligatorio in molti contesti normativi, essenziale per debugging operativo e dispute resolution.

## Requisiti normativi principali

| Norma | Obbligo | Durata conservazione |
|-------|---------|----------------------|
| **GDPR (art. 5, 30)** | Log accessi a dati personali, modifiche, cancellazioni | 5 anni consigliati |
| **D.Lgs. 231/2001** | Tracciabilità processi a rischio reato societario | Durata processo + 5 anni |
| **PCI-DSS** | Log accessi a dati carta di credito | 12 mesi online, 12 mesi archivio |
| **ISO 27001** | Log eventi sicurezza, accessi sistemi | 90 giorni min. (raccomandato 1 anno) |
| **Codice Privacy** | Log amministratori di sistema | 6 mesi |
| **E-invoicing SDI** | Conservazione documenti fiscali | 10 anni |

## Struttura evento audit trail

Ogni evento deve contenere:

```json
{
  "event_id": "uuid-v4-immutabile",
  "timestamp": "2025-05-05T14:32:11.234Z",  // UTC, non locale
  "actor": {
    "user_id": "usr_123",
    "email": "mario.rossi@azienda.it",
    "role": "admin",
    "ip": "192.168.1.45",
    "session_id": "sess_abc"
  },
  "action": "UPDATE",           // CREATE / READ / UPDATE / DELETE / LOGIN / EXPORT
  "resource": {
    "type": "invoice",
    "id": "inv_456",
    "table": "fatture_emesse"
  },
  "changes": {
    "before": { "importo": 1000, "stato": "draft" },
    "after":  { "importo": 1200, "stato": "sent" }
  },
  "result": "success",          // success / failure / partial
  "metadata": {
    "user_agent": "Chrome/120",
    "request_id": "req_789"
  }
}
```

## Regole di immutabilità

1. **No UPDATE/DELETE su audit log** — solo INSERT
2. Timestamp da server (mai dal client)
3. Hash crittografico della riga (sha256) per rilevare tampering
4. Storage separato dal DB applicativo (idealmente write-only per l'app)
5. Backup indipendente con accesso limitato

## Implementazione su Supabase PostgreSQL

```sql
-- Tabella audit immutabile
CREATE TABLE audit_log (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actor_id    TEXT NOT NULL,
  actor_email TEXT,
  actor_ip    INET,
  action      TEXT NOT NULL CHECK (action IN ('CREATE','READ','UPDATE','DELETE','LOGIN','EXPORT','SHARE')),
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  before_data JSONB,
  after_data  JSONB,
  result      TEXT NOT NULL DEFAULT 'success',
  metadata    JSONB
);

-- Blocca UPDATE e DELETE tramite policy RLS
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_insert_only ON audit_log FOR INSERT TO authenticated WITH CHECK (true);
-- Nessuna policy UPDATE/DELETE = proibiti per default
```

## Livelli di logging — cosa tracciare

| Livello | Cosa loggare | Esempio |
|---------|-------------|---------|
| **Critico** | Sempre | Login/logout, cambi password, modifica ruoli, export dati personali |
| **Alto** | Sempre | Creazione/modifica/cancellazione record core (fatture, contratti, ordini) |
| **Medio** | Raccomandato | Lettura di dati sensibili, generazione report, bulk operations |
| **Basso** | Opzionale | Navigazione, ricerche, visualizzazioni ordinarie |

Regola pratica PMI: logga almeno critico + alto su tutti i sistemi che trattano dati cliente o finanziari.

## Monitoraggio e alerting

Configura alert automatici per:
- Login falliti > 5 in 10 minuti dallo stesso IP → sospetto brute force
- Accesso fuori orario lavorativo (es. 02:00-06:00)
- Export > 500 record in una sessione → possibile data exfiltration
- Modifica ruolo admin senza ticket autorizzativo
- Accesso da Paese non previsto (geoblocking)

## Retention e archiviazione

```
0-3 mesi:   storage hot (PostgreSQL/Supabase) — query veloci
3-12 mesi:  storage warm (S3 compresso) — query con latenza
12+ mesi:   archivio cold (S3 Glacier) — solo per compliance
```

Costo indicativo per PMI: ~5€/mese per 1M eventi/anno su Supabase + S3.

## Audit trail per GDPR — casi specifici

**Right to erasure (diritto all'oblio)**: non cancellare i log dell'audit trail stesso, ma anonimizzare il dato personale sostituendo con `[REDACTED]` o UUID pseudonimo. Il log dice "qualcuno ha modificato" ma non più chi era.

**Data breach**: audit trail è la prima fonte per ricostruire cosa è successo, chi ha avuto accesso, quali dati coinvolti — obbligatorio per notifica GDPR entro 72h al Garante.
