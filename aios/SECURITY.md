# AIOS — Security posture

Internal K2-AI platform. Cloud stack (Anthropic Claude + Supabase EU). GDPR-aware.

## Controlli attivi
- **Autonomia governata**: ogni azione esterna passa dalla scaletta L0→L3 + coda approvazioni. Proposte e calendario sono **cap L1** (serve approvazione umana). **Kill-switch** globale nel kernel. Ogni azione è in **audit log** immutabile.
- **DB**: tutte le tabelle `aios_*` + `servizi`/`topics` hanno **RLS attiva senza policy** → solo `service_role` (backend) accede; anon/authenticated = zero righe. Verificato dal vivo (anon → `[]`).
- **API**: **bearer auth** env-gated (`AIOS_API_TOKEN`) sulle route che mutano (`run`, `approve`, `reject`). CORS ristretto (`AIOS_ALLOWED_ORIGIN`). Header `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`. `approval_id` validato `>0`. Errori di dominio generici (no echo). `action_key` validato con regex prima dell'uso.
- **Segreti**: tutti in `aios/.env` (ignorato da git via `*.env`). **Nessun segreto nei file tracciati** (verificato con grep su `sk-ant`, `eyJhbGci`, `EAA*`, `service_role`).
- **Iniezione**: accesso DB via PostgREST con parametri url-encoded e psycopg parametrico. Nessuna interpolazione SQL diretta.

## Audit sicurezza completo (giugno 2026) — findings risolti
Audit su tutto il codice + Supabase advisors. Esito:
- **API auth (HIGH)** → tutti i GET con dati/PII (`approvals`, `activity`, `insights`, `deliverables`, `integrations`, `domain`) ora richiedono bearer (env-gated come le mutazioni). Test in `test_security.py`.
- **Token in prod (HIGH)** → `serve_cockpit.py` solleva se `AIOS_HOST` non-locale e manca `AIOS_API_TOKEN`.
- **Telegram (HIGH)** → fail-closed: senza chat allowlist valida il canale non ascolta; controllo chat sempre attivo.
- **SSRF competitor_web (MED)** → solo `http/https` (no `file://`/metadata).
- **upsert on_conflict (MED)** → url-encoded.
- **Policy tampering (MED)** → al load `level` viene clampato a `capped_at` (un DB manomesso non alza l'autonomia oltre il cap L1).
- **Header (LOW)** → middleware aggiunge `X-Content-Type-Options/X-Frame-Options/Referrer-Policy/Cache-Control` su TUTTE le risposte.
- **Prompt-injection (LOW)** → dati sensori racchiusi in `<dati_non_fidati>` + istruzione esplicita; l'attuatore (allowlist+no-delete+no-money+approvazione umana) resta il backstop reale.
- Supabase advisors: `set_updated_at` search_path fissato; `handle_new_kbot_user` non più eseguibile via RPC (revoke da PUBLIC). RLS attiva su TUTTE le tabelle (nessuna pubblica).

### Residui noti (basso rischio / azione manuale)
- `pg_trgm` nello schema `public` (spostarlo può rompere indici trigram — rimandato).
- Auth "leaked password protection" (HaveIBeenPwned): abilitare dal dashboard Supabase (1 click).
- Report generati `kai-website/kbot/data/reports/*.html` versionati (possibili PII): aggiungere a `.gitignore` e rimuovere dal tracking (scope sito).

## Attuatore L1 (Approva → scrittura reale, `actuator.py`)
- Esegue scritture su Supabase **solo dopo approvazione umana** (la coda L1 = consenso per-azione).
- Perimetro stretto: **solo insert/update** su tabelle operative in **allowlist** (`ALLOWLIST`); **mai delete**;
  **mai denaro** (`board_revenue_events`/`kbot_conversions`/Stripe in `BLOCKED`); mai auth/permessi; mai dati utente kbot.
- `update` richiede sempre un `match` (niente update di massa). Azione non valida → errore tracciato, l'approvazione non crasha.
- Verificato dal vivo: insert reale su `board_tasks` ok, `delete` rifiutato (`ActuatorError`).

## Chat a istruzioni (CommandRouter — `command.py`)
- Canali: cockpit (bearer auth) e Telegram (chat id in allowlist, fail-closed). Un'istruzione vale solo dal canale autenticato dell'owner.
- Flusso: l'istruzione viene valutata dall'LLM sui dati reali; poi ogni azione è classificata e:
  - **interna sicura** (tabella allowlist reversibile) → eseguita SUBITO (l'istruzione dell'owner È l'autorizzazione, come da regola "le scritture da me possono essere fatte");
  - **interna sensibile** (denaro/persone/legale/dati personali: `invoices`, `finance_journal`, `employees`, `candidates`, `legal_documents`, ...) → messa in **conferma**;
  - **esterna** (n8n/pubblicazioni) → messa in **conferma**;
  - **fuori perimetro** (non-allowlist, delete, tabelle denaro `BLOCKED`) → **rifiutata**.
- Backstop reale: ogni scrittura passa comunque da `actuator.validate` (allowlist + no delete + no denaro). Qualunque cosa proponga l'LLM fuori perimetro viene bloccata. Ogni esecuzione è tracciata in audit. Test: `test_command.py`.
- n8n (`sources/n8n.py`): azione esterna `integrazioni.n8n.esegui`, **cap L1** (mai autonoma), env-gated `N8N_WEBHOOK_URL` (solo http/https, header firma opzionale `N8N_WEBHOOK_TOKEN`). Senza URL degrada a "non configurato" (nessun side-effect).
- **Gestione workflow n8n** (Public API, `N8N_API_URL`+`N8N_API_KEY`): lettura workflow = sensore readonly; modifica (`create/update/activate/deactivate`) = **sempre in conferma** dalla chat (mai automatica). **DELETE non esposta** (nessuna cancellazione di workflow). Senza API degrada a "non configurato".

## Connettori esterni (env-gated, privilegi minimi)
- Tutti i connettori (`sources/connectors.py`) sono **readonly** (`action_type=None`) e degradano a `[]` senza credenziali: nessuna azione che muove denaro/stato.
- Chiavi con **least-privilege**: Stripe = *restricted key read-only* (charges/balance/subscriptions read, **mai** scrittura); IMAP = *app-password* dedicata; Google (GSC/Calendar) = service account scope `*.readonly`; Telegram = bot con `callback_data` opaco (solo id approvazione) e **allowlist chat id**.
- Nuove tabelle (`board_cost_items`, `employees`, `candidates`, `legal_documents`, `privacy_registro_trattamenti`, `vendors`): **RLS attiva senza policy** → solo `service_role`.
- Telegram bidirezionale: accetta decisioni solo da `TELEGRAM_CHAT_ID`/`TELEGRAM_ALLOWED_CHAT_IDS`; l'azione resta `resolve_approval` sul kernel (stessa del cockpit), nessun bypass dell'autonomia L1.

## DA FARE prima del deploy in produzione (HARD requirements)
1. **Ruotare i segreti** esposti in chat durante lo sviluppo:
   - `AIOS_SUPABASE_SERVICE_KEY` → Supabase → Settings → API → rigenera
   - `ANTHROPIC_API_KEY` → console.anthropic.com → API Keys
   - `AIOS_IG_TOKEN` (Meta long-lived) → rigenera/revoca
   - **Meta App Secret** → Meta for Developers → App Settings → Basic → rigenera
2. **Impostare `AIOS_API_TOKEN`** (un valore forte) — senza, l'auth è disabilitata (ok solo in locale).
3. **HTTPS + reverse proxy** (nginx/caddy) davanti a uvicorn; non esporre :8800 in chiaro.
4. Tenere il bind su `127.0.0.1` se non dietro proxy.

## Note GDPR
- Dati con **PII** finiscono nei prompt verso **Anthropic (cloud)**: nomi lead (`pipeline_leads`), e-mail iscritti newsletter (`newsletter_subscribers`) e consensi (`kbot_profiles`) letti dagli agenti Vendite/Legal. È un trattamento da registrare nel Registro dei Trattamenti. Mitigazione: pseudonimizzare (iniziali + id) prima dell'invio, o LLM on-premise per i dati sensibili. L'agente **Legal** legge i consensi solo per audit e **propone** (non scrive/cancella).
- L'agente Legal in verifica live ha segnalato anomalie reali (iscritto non confermato, `is_active` incoerente con `unsubscribed_at`, timestamp consenso mancanti): da sanare a parte, non automaticamente.

## Avvisi pre-esistenti Supabase (non da questo codice — fixare a parte)
- `function_search_path_mutable` su `set_updated_at`
- `pg_trgm` installata nello schema `public`
- `handle_new_kbot_user` SECURITY DEFINER eseguibile da anon (legacy kbot)
- protezione password compromesse (HaveIBeenPwned) disattivata in Auth
