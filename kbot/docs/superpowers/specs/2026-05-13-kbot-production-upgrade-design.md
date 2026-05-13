# KBot Production Upgrade — Design Spec
**Date:** 2026-05-13  
**Status:** Approved  
**Scope:** Auth, Payments, Supabase Memory, Feedback, Analytics, Rate Limiting, UI Refresh  
**Fuori scope (k2-ai.it repo):** Lead widget — va costruito direttamente nel repo k2-ai.it, non qui

---

## 1. Context

KBot è costruito in questa cartella (`/kbot`) e verrà integrato nel repo k2-ai.it come pagina separata. Tutto viene sviluppato e testato qui prima del deploy.

Stack esistente: Next.js (frontend) + FastAPI (backend Python) + Supabase (DB) + Anthropic Claude.

---

## 2. Architettura dei Modi

| Modo | Repo | Accesso | Auth | Pagamento | Memoria |
|------|------|---------|------|-----------|---------|
| Lead widget (`/suite-ai`) | **k2-ai.it** | Pubblico | No | No | No |
| Report chat | **kbot** | Login Clerk | Sì | No | Sì (Supabase) |
| Report download | **kbot** | Login Clerk | Sì | `has_paid = true` | — |

Il kbot (questa cartella) gestisce solo il **report premium**. Il lead widget è responsabilità del repo k2-ai.it.

---

## 3. Auth — Clerk

**Servizio:** `@clerk/nextjs`  
**Social login:** Google, Apple, email/password  

### Flusso report mode
1. Non loggato → componente `<SignInButton>` al posto della chat
2. Loggato, `has_paid = false` → chat attiva, bottoni download mostrano "Paga per scaricare" → POST `/api/stripe/checkout` → redirect Stripe
3. Loggato, `has_paid = true` → chat + download sbloccati

### Middleware Next.js
- `/api/chat` (mode=report) → verifica JWT Clerk (no payment check)
- `/api/reports/*/download` → verifica JWT Clerk + `publicMetadata.has_paid === true`, altrimenti 402
- Lead mode e `/api/chat` (mode=lead) → pubblici

### UI
- `<UserButton>` di Clerk nell'header (avatar, logout)
- Lead mode: nessun riferimento all'account

---

## 4. Pagamenti — Stripe

**Modello:** one-time payment per sbloccare i download (non abbonamento).  
`has_paid` viene settato su Clerk una volta pagato — accesso permanente ai download.

### Nuovi endpoint backend
```
POST /api/stripe/checkout
  → crea Stripe Checkout Session
  → ritorna { url: "https://checkout.stripe.com/..." }

POST /api/stripe/webhook
  → verifica Stripe signature
  → evento checkout.session.completed
  → Clerk API: updateUser(clerk_user_id, { publicMetadata: { has_paid: true } })
```

### Protezione reale download (non solo UI)
`GET /api/reports/{id}/download` e `/html/download` estraggono JWT Clerk dall'header Authorization, verificano `has_paid`. Se assente → 402.

---

## 5. Lead Widget — FUORI SCOPE (repo k2-ai.it)

Il lead widget viene costruito direttamente nel repo k2-ai.it, non nel kbot.  
Documentazione e design del widget vanno nel repo k2-ai.it.

---

## 6. Memoria Supabase — Report Premium

**Sostituisce:** `chat_memory.json` locale per utenti loggati.  
**Utenti anonimi (lead):** nessuna persistenza — comportamento attuale invariato.

### Schema tabella
```sql
CREATE TABLE conversations (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  role         TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content      TEXT NOT NULL,
  ts           TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON conversations (clerk_user_id, conversation_id, ts);
```

### Backend
- `get_conversation_memory()` e `append_conversation_memory()` — se `clerk_user_id` presente → Supabase, altrimenti → file JSON locale (backward compat lead mode)
- `clerk_user_id` passato dal frontend nell'header `X-Clerk-User-Id` (verificato lato backend tramite JWT)

### Nota privacy (visibile in UI)
> "Le tue conversazioni vengono salvate per continuare da dove hai lasciato. I documenti generati non vengono conservati sui nostri server."

---

## 7. Rate Limiting

**Scope:** chat API (`/api/chat`)  
**Limiti:**
- Utenti anonimi (lead): 20 messaggi/ora per IP
- Utenti loggati (report): 30 messaggi/ora per `clerk_user_id`

**Implementazione:** middleware FastAPI con contatori in-memory (Redis se il volume scala, in-memory sufficiente per MVP).  
**Risposta limite:** HTTP 429 con messaggio: "Hai raggiunto il limite di messaggi. Riprova tra X minuti."

---

## 8. Analytics

**Cosa tracciare:**
- Suite consigliata per ogni sessione lead (quale skill → quale suite)
- Report generati per utente (count, tipo hospitality vs generic)
- Download effettuati (PDF vs HTML)
- Conversion: chat → checkout → paid

**Storage:** tabella Supabase `analytics_events`:
```sql
CREATE TABLE analytics_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,  -- 'suite_recommended', 'report_generated', 'download', 'checkout_started', 'checkout_completed'
  clerk_user_id TEXT,        -- null per eventi anonimi
  session_id TEXT,
  payload JSONB,
  ts TIMESTAMPTZ DEFAULT now()
);
```

**Backend:** `track_event(event_type, payload, clerk_user_id=None)` — fire-and-forget, mai blocca la risposta.

---

## 9. Notifiche Email

**Trigger:** report generato con successo (hospitality HTML pipeline o PDF pipeline).  
**Servizio:** Clerk webhooks + Clerk email (o Resend se Clerk non supporta email custom).  
**Contenuto email:** "Il tuo report è pronto. Accedi per scaricarlo." + link diretto.  
**Implementazione:** `POST /api/stripe/webhook` pattern replicato per report-ready event.

---

## 10. Feedback

**Quando:** dopo la generazione di un report (messaggio con link download).  
**UI:** mini-widget sotto il messaggio report pronto:
```
[⭐⭐⭐⭐⭐] "Come valuteresti questo report?"
[Campo testo opzionale] "Cosa miglioreresti?"
[Invia feedback]
```

**Endpoint:** `POST /api/feedback`  
**Storage:** tabella Supabase `feedback`:
```sql
CREATE TABLE feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT,
  report_id TEXT,
  rating INT CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  ts TIMESTAMPTZ DEFAULT now()
);
```

**Utilizzo:** revisione manuale periodica per migliorare prompt e skill pack.

---

## 11. UI Refresh

**Approccio:** miglioramenti incrementali sul design esistente (no redesign totale).  
**Aree:**
- Header: aggiunta `<UserButton>` Clerk, pulizia spaziatura
- MessageBubble: migliore gerarchia visiva per bottoni report (già parzialmente fatto)
- Report mode: badge "Premium" sull'header quando attivo
- Lead widget: stile coerente con k2-ai.it (colori da verificare al momento dell'integrazione)
- Nota privacy: visibile sotto la prima risposta in report mode

---

## 12. Sequenza di Implementazione

1. **Clerk auth** — provider, middleware, UserButton, gate report mode
2. **Stripe** — checkout endpoint, webhook, gate download
3. **Supabase memory** — schema, migrazione backend da JSON a DB
4. **Rate limiting** — middleware FastAPI
5. **Analytics** — tabella + track_event
6. **Feedback** — widget + endpoint + tabella
7. **Email notifiche** — post-report trigger
8. **UI refresh** — polish finale

---

## 13. Variabili d'Ambiente Necessarie

```env
# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
CLERK_WEBHOOK_SECRET=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID=           # price ID del prodotto report premium

# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

# Esistenti
ANTHROPIC_API_KEY=
NEXT_PUBLIC_API_BASE_URL=
```
