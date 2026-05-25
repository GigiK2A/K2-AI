# Setup Google Sheet per blog autopilot

> Da fare una volta. Tempo stimato: 15 minuti.

## 1. Apri il foglio esistente

Il foglio già in uso da n8n: **K2AI — Spotlight Laboratori & Suite**.
Tab attiva: `Servizi`.

Layout attuale (riga 1 = header):

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| Servizio | Problema | Risultato/KPI | Agevolazione | Stato | Data |

## 2. Aggiungi 5 colonne nuove

Riga 1, dalla colonna G in poi, inserisci queste intestazioni esatte:

| G | H | I | J | K |
|---|---|---|---|---|
| `blog_slug` | `blog_pubblicato` | `blog_url` | `pillar_padre` | `pillar_url` |

Il foglio finale avrà 11 colonne (A-K).

## 3. Compila a mano `pillar_padre` e `pillar_url` per le 12 righe esistenti

Sono dati statici (non cambieranno). Per ogni servizio, scegli il pillar
più vicino e copia il link.

Mapping suggerito (puoi modificare se vuoi un'altra associazione):

| Servizio (col A) | pillar_padre (col J) | pillar_url (col K) |
|---|---|---|
| CheckExpress AI | P12 | `/suite-ai/analisi-strategica-pmi.html` |
| Laboratorio Automazione Processi | P02 | `/suite-ai/automazioni-amministrative.html` |
| Laboratorio AI Customer Care | P06 | `/suite-ai/ai-customer-service-ticket.html` |
| Laboratorio Analisi Dati & BI | P17 | `/suite-ai/ai-data-analytics-bi.html` |
| Laboratorio Content & Marketing AI | P11 | `/suite-ai/ai-marketing-contenuti.html` |
| K2-Suite Core | P10 | `/suite-ai/integrazione-gestionali-erp.html` |
| K2-Suite Sales AI | P01 | `/suite-ai/agenti-email-crm.html` |
| K2-Suite HR & Recruiting AI | P15 | `/suite-ai/ai-hr-recruiting.html` |
| K2-Suite Operations & Logistica | P20 | `/suite-ai/ai-hospitality-revenue.html` |
| K2-Suite Finance AI | P09 | `/suite-ai/ai-controllo-gestione-reporting.html` |
| Formazione AI Aziendale | P12 | `/suite-ai/analisi-strategica-pmi.html` |
| AI Readiness Assessment | P12 | `/suite-ai/analisi-strategica-pmi.html` |

Le altre 3 colonne (`blog_slug`, `blog_pubblicato`, `blog_url`) lascia
vuote. Le compila il bot quando pubblica.

## 4. Crea un Google Service Account per l'accesso programmatico

Lo serve a GitHub Actions per leggere/scrivere il foglio.

1. Vai su https://console.cloud.google.com/
2. Crea un nuovo progetto (es. `k2ai-blog-bot`) — o usa uno esistente
3. APIs & Services → Library → cerca **"Google Sheets API"** → Enable
4. APIs & Services → Credentials → **Create credentials → Service account**
5. Nome: `blog-bot`. Skippa i ruoli IAM. Crea.
6. Sul service account creato → tab **Keys** → Add Key → Create new key →
   tipo **JSON** → scarica il file (es. `blog-bot-credentials.json`)
7. Apri il JSON e copia il valore di `client_email` (è tipo
   `blog-bot@k2ai-blog-bot.iam.gserviceaccount.com`)
8. Torna al foglio Google Sheets → **Condividi** → incolla la email →
   permesso **Editor** → Invia (senza notifica)

## 5. Aggiungi i secret a GitHub

https://github.com/GigiK2A/K2-AI/settings/secrets/actions

Aggiungi questi 5:

| Nome | Valore |
|---|---|
| `ANTHROPIC_API_KEY` | la stessa key di Railway (sk-ant-api03-...) |
| `GOOGLE_SHEETS_CREDENTIALS` | **tutto il contenuto** del file `blog-bot-credentials.json` (multi-line JSON, copia-incolla) |
| `GOOGLE_SHEET_ID` | l'ID del foglio: nella URL del foglio, è la parte tra `/d/` e `/edit`. Es. URL `https://docs.google.com/spreadsheets/d/1A2B3C.../edit` → ID = `1A2B3C...` |
| `TELEGRAM_BOT_TOKEN` | stesso token che usa n8n IG |
| `TELEGRAM_CHAT_ID` | `278384928` (la tua chat) |

## 6. (Opzionale) GH_PAT per push automatici

Se il repo ha branch protection su `main` che richiede review o se vuoi
evitare che il workflow Actions triggeri se stesso ricorsivamente:

1. https://github.com/settings/tokens?type=beta → Generate new token (fine-grained)
2. Repo: `GigiK2A/K2-AI` — solo questo
3. Permissions:
   - **Contents: Read and write**
   - **Workflows: Read and write** (se vuoi che il bot tocchi anche `.github/`)
4. Genera, copia
5. Aggiungi secret: `GH_PAT_BLOG_PUSH` = il token

Se NON aggiungi questo secret, il workflow usa il `GITHUB_TOKEN` automatico
(che ha `contents: write` grazie al `permissions:` nel workflow). Funziona,
ma alcune branch protection lo bloccano. Per ora prova senza, aggiungi
solo se push fallisce.

## 7. Test

Trigger manuale (non aspetta il mercoledì):

```bash
gh workflow run "Blog autopilot" --field dry_run=true
```

Questo genera un articolo SENZA pubblicare, lo salva in
`tools/blog-bot/dry-run-output/`. Vedi log su:
https://github.com/GigiK2A/K2-AI/actions/workflows/blog-autopilot.yml

Se il dry-run riesce, prova quello vero (PUBBLICA):

```bash
gh workflow run "Blog autopilot"
```

Verifica:
1. Telegram alert "✅ Blog bot: articolo pubblicato"
2. Riga del foglio compilata con `blog_slug`, `blog_pubblicato`, `blog_url`
3. https://www.k2-ai.it/blog/<slug> live (dopo deploy Railway ~3 min)
4. Sitemap include la nuova URL

## 8. Schedule attivo

Da quando il workflow è committato e i secret sono settati, parte
automatico ogni **mercoledì alle 06:00 CET** (5:00 UTC).

Stessa data: alle **18:00 CET di mercoledì** il workflow n8n esistente
pubblica il post Instagram, che ora include il link al blog. **Importante**:
l'agente che gestisce n8n deve spostare il cron del Workflow 07 da
giovedì 18:00 a mercoledì 18:00 (vedi `n8n-ig-update-prompt.md`).

Se per qualche motivo blog NON è uscito (validator FAIL o crash), n8n IG
NON deve pubblicare quel mercoledì — vedi `n8n-ig-update-prompt.md` per le
istruzioni da dare all'agente che gestisce il workflow IG.
