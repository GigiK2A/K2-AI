# Gmail OAuth setup per Sprint 9C — email triage

Giuseppina può leggere la casella Gmail di Luigi (read-only) per
classificare le email in `ignora | memo | lead | task`. La connessione è
**opzionale**: senza queste credenziali resta disponibile solo lo
`StubProvider` (tabella `board_inbox_pending`).

## 1. Crea un progetto Google Cloud
1. Vai su <https://console.cloud.google.com/>.
2. Crea un nuovo progetto (es. `k2-board-gmail`).

## 2. Abilita Gmail API
1. APIs & Services → **Library** → cerca *Gmail API* → **Enable**.

## 3. Configura OAuth consent screen
1. APIs & Services → **OAuth consent screen**.
2. Tipo: **External** (perché usi un account personale Gmail).
3. App name: `K2-Board Triage`, email = la tua.
4. Scopes: aggiungi
   * `.../auth/gmail.readonly`
   * `.../auth/gmail.modify` (per applicare label in futuro)
5. Test users: aggiungi la mail Gmail da cui Giuseppina leggerà.

## 4. Crea OAuth Client ID
1. APIs & Services → **Credentials** → Create credentials → **OAuth client ID**.
2. Application type: **Desktop app**.
3. Salva `client_id` e `client_secret`.

## 5. Ottieni refresh_token
Dalla root di `apps/board/backend`:

```bash
.venv/bin/python playground/oauth2.py \
    --client-id <CLIENT_ID> \
    --client-secret <CLIENT_SECRET>
```

Lo script apre il browser, ti fa accedere al tuo Gmail, autorizza
l'app, e poi stampa nel terminale le 3 righe pronte da incollare
nel `.env`:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
```

## 6. Attiva il triage
Aggiungi anche:

```
EMAIL_TRIAGE_ENABLED=true
EMAIL_TRIAGE_CRON=0 */2 * * *   # ogni 2 ore
```

Riavvia il backend (`uvicorn` o `railway up`). Verifica con:

```bash
curl -X POST https://board.k2-ai.it/api/agent/email/triage-now \
    -H "Content-Type: application/json" \
    -H "Cookie: k2board_session=..." \
    -d '{"provider":"gmail","hours":24}'
```

## Fallback: StubProvider (sempre disponibile)
Se non vuoi/puoi configurare Gmail, puoi incollare manualmente le mail
da triage nella tabella `board_inbox_pending` (vedi migration
`003_inbox_pending.sql`). Lo `StubProvider` le legge e le triagia
esattamente come farebbe Gmail.

```sql
insert into board_inbox_pending (from_email, from_name, subject, body)
values ('mario@acme.it', 'Mario', 'Preventivo', 'Vorrei un agente AI...');
```

Poi chiama `POST /api/agent/email/triage-now` con
`{"provider":"stub"}`.

## Sicurezza
- Il `refresh_token` ha potere di leggere la mail finché non viene
  revocato. Conservalo come segreto Railway.
- Lo scope `gmail.readonly` non permette di inviare email da Giuseppina.
- Per inviare risposte usiamo Resend (vedi `RESEND_API_KEY`), non Gmail.
