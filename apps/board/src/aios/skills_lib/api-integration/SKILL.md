---
name: api-integration
description: >-
  Integrazione API REST e webhook per PMI italiane: connessione gestionali
  (TeamSystem, Zucchetti, Mago4, Fatture in Cloud), automazione flussi con
  n8n/Make, mappatura endpoint, gestione autenticazione OAuth2/API key.
---

# Integrazione API — Gestionali e Servizi Italiani

## Gestionali italiani più diffusi — stato API

| Gestionale | API | Formato | Note |
|------------|-----|---------|------|
| **Fatture in Cloud** | REST (v2) | JSON | OAuth2, sandbox disponibile |
| **TeamSystem** | REST | JSON/XML | Richiede accordo commerciale |
| **Zucchetti** | SOAP/REST | XML/JSON | Legacy SOAP + nuove API REST |
| **Mago4 / Mago Next** | REST | JSON | Micronauta middleware |
| **Danea Easyfatt** | No API native | CSV export | Solo import/export file |
| **QuiCredit / GestPay** | REST | JSON | Solo pagamenti |
| **Aruba Fatturazione** | REST | JSON | Semplice, buona docs |

## Fatture in Cloud — endpoint principali

```
GET    /v2/companies/{company_id}/issued_documents    → fatture emesse
POST   /v2/companies/{company_id}/issued_documents    → crea fattura
GET    /v2/companies/{company_id}/received_documents  → fatture ricevute
GET    /v2/companies/{company_id}/clients             → anagrafica clienti
POST   /v2/companies/{company_id}/clients             → crea cliente
GET    /v2/companies/{company_id}/products            → listino prodotti
```

Auth: Bearer token OAuth2. Scopes: `issued_documents:r`, `issued_documents:e`, `entities.clients:rw`.

## Pattern integrazione standard

### Webhook → azione
```
Evento esterno (fattura pagata, form compilato)
  → webhook POST a endpoint n8n/Make
  → validazione payload (header HMAC sha256)
  → trasformazione dati
  → scrittura su DB / invio email / update CRM
```

### Polling pianificato
```
Cron ogni 15min
  → GET /issued_documents?filter[payment_date]≥{ieri}
  → diff con stato locale
  → elabora nuovi/modificati
  → aggiorna stato interno
```

### Autenticazione OAuth2 flow per app server-side
```
1. Redirect utente a /oauth/authorize?client_id=...&scope=...
2. Callback riceve code
3. POST /oauth/token con code → access_token + refresh_token
4. Salva refresh_token (scade mai), access_token (scade 1h)
5. Prima di ogni call: se access_token scaduto → refresh
```

## n8n — nodi utili per PMI

| Nodo | Use case |
|------|----------|
| HTTP Request | Chiama qualsiasi REST API |
| Webhook | Riceve eventi push |
| Cron | Scheduling automatico |
| Google Sheets | Leggi/scrivi fogli (CRM leggero) |
| Airtable | Sync database operativo |
| Gmail/Resend | Notifiche email |
| Supabase | Query/insert su DB PostgreSQL |
| Code (JS) | Trasformazioni dati custom |
| Split in Batches | Elabora array grandi |
| Error Trigger | Notifica errori workflow |

## Gestione errori API

| Errore HTTP | Significato | Azione |
|-------------|-------------|--------|
| 400 Bad Request | Payload malformato | Logga body inviato, correggi schema |
| 401 Unauthorized | Token scaduto/errato | Refresh token o reinizializza OAuth |
| 403 Forbidden | Scope insufficiente | Richiedi scope corretto |
| 404 Not Found | Risorsa non esiste | Verifica ID, non propagare errore |
| 429 Too Many Requests | Rate limit | Backoff esponenziale: 1s, 2s, 4s... |
| 500 Server Error | Errore lato API | Retry 3x poi alert |

## Mappatura dati — checklist

Prima di ogni integrazione documentare:
- [ ] Endpoint sorgente + autenticazione
- [ ] Schema campo per campo (fonte → destinazione)
- [ ] Trasformazioni (formati data, codifiche moneta, IVA)
- [ ] Gestione valori null/vuoti
- [ ] ID univoci per deduplication
- [ ] Frequenza sync (real-time/polling/batch)
- [ ] Rollback in caso di errore parziale

## Fatturazione elettronica SDI — integrazione

Per inviare/ricevere fatture SDI senza gestionale:
- **Aruba Sign/FatturAziende**: API REST, 0.025€/fattura
- **Fattura24/Invoicex**: API JSON semplice
- Formato: XML FatturaPA, namespace `http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2`
- Canali: PEC o Codice Destinatario (7 caratteri)
- Conservazione sostitutiva: obbligatoria 10 anni

## Sicurezza API

- Secrets mai in codice: usa env vars o vault (Supabase Vault, Railway env)
- Valida sempre HMAC dei webhook prima di elaborare
- Rate limit su endpoint esposti (max 100 req/min per IP)
- Log tutte le chiamate con timestamp, status, latenza
- Ruota API key ogni 90 giorni per servizi critici
