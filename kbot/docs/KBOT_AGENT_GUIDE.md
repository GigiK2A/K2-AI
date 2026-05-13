# K2-AI Kbot — Guida completa per l'agente AI integratore

> **A chi serve questo file:** Agente AI (o sviluppatore) incaricato di integrare il kbot nel sito k2-ai.it come pagina dedicata e separata. Leggi tutto prima di toccare il codice.

---

## 1. Cos'è il kbot

K2-AI Kbot è un'applicazione web standalone che permette a utenti autenticati di generare **report professionali in PDF e HTML** usando l'AI (Claude di Anthropic). Non è un chatbot generico: è un motore di reportistica premium con workflow verticali per settori specifici (hospitality, PMI, legale, edilizia, ecc.).

**Stack:**
- **Frontend:** Next.js 16 App Router, TypeScript, Tailwind CSS, Clerk (auth), Framer Motion
- **Backend:** FastAPI (Python), Anthropic API, Playwright (PDF via Chromium), Supabase, Stripe
- **Auth:** Clerk — gestisce login, sessioni, `publicMetadata.has_paid` per il gate premium
- **Pagamento:** Stripe checkout → webhook → Clerk metadata update

**Deployment attuale (sviluppo):**
- Frontend: `http://localhost:3000` (o `http://192.168.1.169:3000` in LAN)
- Backend: `http://localhost:8000` (o `http://192.168.1.169:8000` in LAN)

---

## 2. Architettura del frontend

```
/src
  /app
    page.tsx              ← Chat principale (unica pagina operativa)
    layout.tsx            ← Root layout con ClerkProvider
    /sign-in/[[...sign-in]]/page.tsx   ← Login split screen
    /sign-up/[[...sign-up]]/page.tsx   ← Registrazione split screen
    /dashboard/page.tsx   ← Dashboard utente (report, account, stats)
  /components
    /layout
      Sidebar.tsx         ← Barra sinistra: navigazione, lista conversazioni
      ChatLayout.tsx      ← Header con badge Premium e link Dashboard
      ConversationList.tsx
    /chat
      Composer.tsx        ← Input composizione messaggio + upload file
      MessageBubble.tsx   ← Bolla messaggio con link download report
      ModeSwitcher.tsx    ← Switcher modalità (ora solo Report Premium)
      SkillBadge.tsx
    /insights
      InsightPanel.tsx    ← Pannello destro: modalità attiva, skill usate
    /auth
      AuthGate.tsx        ← Wrappa contenuto premium: se non loggato mostra gate
    /report
      ReportCard.tsx
    /ui
      AIStatusIndicator.tsx
  /lib
    api.ts               ← Tutte le chiamate al backend
    utils.ts
  /types
    chat.ts              ← Tipi: Mode, ChatMessage, Conversation, SkillSummary, ecc.
  middleware.ts          ← Clerk middleware: protegge tutto tranne route pubbliche
```

---

## 3. Cosa è stato implementato (cronologia sessioni)

### 3.1 Autenticazione Clerk (sessione precedente)

**Problema di partenza:** L'app non aveva login. C'era solo una schermata statica "K2-AI / Accedi per continuare".

**Soluzione implementata:**
- Installato `@clerk/nextjs` e configurato `ClerkProvider` in `layout.tsx`
- Creato `src/middleware.ts` con route protection: tutto è protetto tranne `/sign-in`, `/sign-up` e le API pubbliche
- Pagine dedicata `/sign-in/[[...sign-in]]/page.tsx` e `/sign-up/[[...sign-up]]/page.tsx` con layout **split screen** (sinistra branding K2-AI, destra form Clerk con tema scuro)
- `AuthGate` componente: blocca l'area chat report se utente non loggato, mostra CTA login
- Header aggiornato: mostra `UserButton` (avatar Clerk) se loggato, altrimenti link "Accedi"

**Variabili d'ambiente Clerk richieste (`.env.local`):**
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/
```

**Variabili Clerk nel backend (`backend/.env`):**
```
CLERK_JWKS_URL=https://<instance>.clerk.accounts.dev/.well-known/jwks.json
CLERK_ISSUER=https://<instance>.clerk.accounts.dev
CLERK_SECRET_KEY=sk_test_...
```

**Attenzione:** Le chiavi frontend e backend DEVONO appartenere alla stessa istanza Clerk (`distinct-mite-64`). Istanze diverse causano loop di redirect infiniti.

**LAN:** Per accedere dal LAN (`192.168.1.169`), l'IP deve essere aggiunto nelle Clerk Dashboard → Configure → Domains. Senza questo il form Clerk non si carica.

### 3.2 Rimozione Lead Generation

**Cambio:** La modalità "Lead Generation" è stata rimossa completamente.
- `ModeSwitcher.tsx`: ora mostra solo "Report Premium" (fisso, non switcher)
- `page.tsx`: modalità default cambiata da `"lead"` a `"report"`
- Rimossi: `LEAD_SUGGESTIONS`, `EMAIL_RE`, `CONTACT_BASE_URL`, `ctaUrl`, `handleLeadSave`, `saveLead` import
- Il rendering non ha più il branch condizionale lead/report — sempre report
- `InsightPanel`: rimosso `LeadCaptureCard`, rimossi i placeholder vuoti (Timeline elaborazione, Analytics conversazione, Fonti e reasoning contestuale)
- Il tipo `Mode = "lead" | "report"` esiste ancora nel codebase per retrocompatibilità con il backend

### 3.3 Fix sidebar scomparsa su Report Premium

**Problema:** Quando l'utente cliccava "Report Premium" nella sidebar, la sidebar spariva anche su desktop.

**Root cause:** L'`onMode` callback in `page.tsx` chiamava `setSidebarOpen(false)`, che rimuoveva la sidebar dall'AnimatePresence anche su `lg:` (desktop statico).

**Fix:** Rimosso `setSidebarOpen(false)` dall'handler `onMode`. La sidebar su desktop rimane sempre aperta; su mobile il close avviene solo con il bottone `PanelLeftClose`.

### 3.4 Dashboard utente (`/dashboard`)

**Implementato da zero:**

**Backend — `GET /api/dashboard`** (in `backend/app/main.py`):
- Richiede autenticazione Clerk (Bearer token)
- Legge tutti i file `*.json` in `data/reports/`
- Filtra per `user_id` (solo report dell'utente autenticato)
- Report vecchi senza `user_id` vengono inclusi (retrocompatibilità)
- Restituisce: lista report (max 20), stats (totale, data ultimo), account info

**Backend — `user_id` nei report:**
- `generate_report_pdf()` e `save_html_and_pdf()` ora accettano `user_id: str = ""`
- Il `clerk_user_id` viene passato durante la generazione in `POST /api/chat`
- Il `user_id` viene salvato nel meta JSON del report (`data/reports/<id>.json`)

**Frontend — `src/app/dashboard/page.tsx`:**
- Route protetta da Clerk middleware (non è route pubblica)
- Mostra 4 sezioni:
  1. **Stato account**: Piano Premium / Gratuito (da `has_paid`)
  2. **Statistiche**: numero report totali, data ultimo report
  3. **Azioni rapide**: bottone Nuovo Report (→ `/`), Apri ultimo report
  4. **Storico report**: lista con bottone Apri HTML e PDF (PDF solo se `hasPaid`)
- Download PDF: fetch autenticata → blob → anchor download (non link diretto, serve Bearer token)

**Frontend — `src/lib/api.ts`:**
- Aggiunta funzione `fetchDashboard(authToken)` e interfacce `DashboardData`, `DashboardReport`

**Navigazione:** Bottone "Dashboard" appare nell'header solo se `isSignedIn === true`.

### 3.5 Fix Apple button login

**Problema:** Logo Apple e testo nel bottone social di Clerk erano neri su sfondo `#111111` — illeggibili.

**Fix in entrambe le pagine sign-in e sign-up:**
```js
socialButtonsBlockButton: { ..., color: "#ffffff" },
socialButtonsBlockButtonText: { color: "#ffffff" },
socialButtonsProviderIcon: { filter: "invert(1)" },
```

---

## 4. Logica report (come funziona il motore)

### 4.1 Skill system

Le skill sono cartelle in `assets/skills/` con file `SKILL.md` o `skills.md`. Il backend le carica tutte all'avvio e le matcha per rilevanza keyword con la query dell'utente.

Directory skill:
```
assets/skills/skills sito k2-ai 2/   ← skill generiche (PMI, legale, ecc.)
assets/skills/hospitality/            ← skill hospitality (29 pack)
assets/skills/legacy-kai-website/     ← skill migrate dal vecchio K-BOT del sito
```

Il backend carica tutte e tre le root, deduplica per `id` normalizzato e mantiene priorità alle skill già presenti nel kbot rispetto alle omonime legacy. In modalità report il catalogo completo viene passato all'orchestratore ordinato per rilevanza; il modello deve selezionare caso per caso le skill migliori, anche combinando domini diversi.

### 4.2 Workflow report hospitality

Rilevato automaticamente se le skill matchate includono `orchestratore-hospitality`, `check-host-express`, ecc.

Flusso:
1. L'AI raccoglie i dati mancanti (max 6 campi obbligatori: tipologia, regione, camere, giorni apertura, notti vendute, ricavi)
2. Quando i dati sono completi (o l'utente chiede esplicitamente il report), genera un report HTML completo con design system K2-AI
3. Playwright converte l'HTML in PDF
4. Il link al report appare nella bolla del messaggio

### 4.3 Workflow report generico

Per settori non-hospitality: l'utente fornisce dati, il backend genera testo strutturato, lo valida, lo converte in PDF con fpdf2. Se il testo non supera la validazione (troppo breve, placeholder visibili, ecc.) ritorna un messaggio di errore.

### 4.4 Gate premium

Il download del PDF è protetto da `has_paid` in Clerk `publicMetadata`. Stripe webhook aggiorna questo flag via Clerk API. Senza pagamento, l'utente può vedere il report HTML ma non scaricare il PDF.

---

## 5. Variabili d'ambiente complete

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/
```

### Backend (`backend/.env`)
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-20250514
CLERK_JWKS_URL=https://distinct-mite-64.clerk.accounts.dev/.well-known/jwks.json
CLERK_ISSUER=https://distinct-mite-64.clerk.accounts.dev
CLERK_SECRET_KEY=sk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
SUPABASE_URL=https://...supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
FRONTEND_URL=http://localhost:3000
RESEND_API_KEY=re_...
REPORT_FROM_EMAIL=report@k2-ai.it
REPORT_PAYMENT_LINK=http://localhost:3000/checkout
```

---

## 6. Come avviare il sistema

```bash
# Backend (dalla root del progetto)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (dalla root del progetto)
npm install
npm run dev -- --hostname 0.0.0.0
```

Per LAN: usare `--hostname 0.0.0.0` su entrambi e impostare `NEXT_PUBLIC_API_BASE_URL=http://<IP_LAN>:8000`.

---

## 7. Integrazione nel sito k2-ai.it — istruzioni per l'agente

### 7.1 Requisito chiave: pagina separata

Il kbot NON deve essere un widget o iframe embedded nella homepage del sito. Deve essere una **pagina dedicata e separata**, ad esempio:

```
https://app.k2-ai.it         ← subdomain dedicato (consigliato)
oppure
https://k2-ai.it/app         ← sottopercorso
```

Motivo: il kbot è una SPA React con autenticazione Clerk, routing App Router e stato globale. Embedderla nel sito principale crea conflitti di routing, autenticazione e bundle.

### 7.2 Cosa collegare dal sito principale

Dal sito k2-ai.it (presumibilmente statico o CMS), collegare al kbot con semplici link:

```html
<!-- CTA principale homepage -->
<a href="https://app.k2-ai.it">Prova K2-AI →</a>

<!-- CTA specifica report -->
<a href="https://app.k2-ai.it/sign-up">Inizia gratis</a>
```

### 7.3 Clerk: domini autorizzati

Nella Clerk Dashboard → Configure → Domains, aggiungere:
- Il dominio di produzione del kbot (es. `app.k2-ai.it`)
- Il dominio del sito principale se serve SSO (es. `k2-ai.it`)

### 7.4 Stripe: webhook

Il webhook Stripe deve puntare a `https://app.k2-ai.it/api/stripe/webhook` (o al backend FastAPI se il backend è separato dal frontend).

### 7.5 CORS

Il backend FastAPI ha `allow_origins=["*"]` per sviluppo. In produzione, restringere a:
```python
allow_origins=["https://app.k2-ai.it", "https://k2-ai.it"]
```

### 7.6 Variabili d'ambiente produzione

Cambiare:
```env
NEXT_PUBLIC_API_BASE_URL=https://api.k2-ai.it   # o URL produzione backend
FRONTEND_URL=https://app.k2-ai.it
REPORT_PAYMENT_LINK=https://app.k2-ai.it/checkout
```

### 7.7 Deploy consigliato

| Componente | Servizio consigliato |
|------------|---------------------|
| Frontend Next.js | Vercel (supporta App Router nativo) |
| Backend FastAPI | Railway, Fly.io, o VPS con Docker |
| Storage report | Migrare da file system a Supabase Storage per deploy scalabile |
| Database memoria conversazioni | Supabase (già integrato parzialmente) |

### 7.8 Nota su Playwright in produzione

Il backend usa Playwright + Chromium per la conversione HTML→PDF. In Docker/VPS serve installare le dipendenze:
```dockerfile
RUN playwright install --with-deps chromium
```
Alternativa: usare WeasyPrint (già in `requirements.txt`) per i report non-hospitality e mantenere Playwright solo per HTML hospitality.

---

## 8. Struttura file dati

```
data/
  reports/
    <timestamp>-<conv_id>.pdf    ← PDF report
    <timestamp>-<conv_id>.html   ← HTML report (solo hospitality)
    <timestamp>-<conv_id>.json   ← Meta: id, title, user_id, created_at, has_html
  uploads/
    <id>.bin                     ← File caricati dall'utente
    <id>.json                    ← Meta file: name, mimeType, preview, readable
  leads.jsonl                    ← Lead (deprecato, non più in uso attivo)
  chat_memory.json               ← Memoria conversazioni (locale, retrocompatibilità)
```

**Importante:** In produzione su server multi-istanza, la memoria chat e i report su file system non funzionano. Completare la migrazione a Supabase (già parzialmente implementata per la memoria conversazioni in `backend/app/supabase_client.py`).

---

## 9. Cosa non è ancora implementato

| Feature | Stato | Note |
|---------|-------|-------|
| Storico report su Supabase | Parziale | Solo file locale, `user_id` ora salvato ma non su DB |
| Pagamento Stripe reale | Configurato ma non testato | `STRIPE_PRICE_ID` placeholder |
| Email report via Resend | Implementato ma non testato | `RESEND_API_KEY` placeholder |
| Report multi-lingua | Non implementato | Solo italiano |
| Cancellazione account | Non implementato | Solo tramite Clerk dashboard |
| Quota report per utente | Non implementato | Solo rate limiting globale |

---

## 10. Contatti e riferimenti

- Istanza Clerk: `distinct-mite-64.clerk.accounts.dev`
- Modello AI: `claude-sonnet-4-20250514` (configurabile via `CLAUDE_MODEL`)
- Design system report: `assets/report-design-system.md`
- Logo: `LOGOK2-AI.png` (root), `public/logo-k2ai.png` (frontend)
