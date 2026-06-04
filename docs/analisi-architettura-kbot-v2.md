# Analisi: architettura K2-AI v2 proposta vs K-BOT esistente

**Scopo**: valutare il documento `ARCHITETTURA-sistema-K2AI-frontend.md` (proposta di
"portale SaaS con KBot agentico, MCP catalogo, wallet crediti, skill/orchestratori")
contro lo stato reale del codice in `kai-website/kbot/`.

**Conclusione anticipata**: l'architettura proposta è concettualmente corretta ma
descrive — con vocabolario diverso e in modo più astratto — un sistema che è già
implementato per il 70-80%. Il 20-30% di novità (wallet crediti, multi-prodotto,
MCP remoto, percorsi a tappe) aggiunge complessità reale e va valutato pezzo per
pezzo, non come un blocco unico.

---

## 1. Stato reale del K-BOT esistente (al 2026-05-29)

Quello che CLAUDE.md §8 descrive è una versione semplificata. Il codice reale è
molto più avanzato.

### 1.1 Stack effettivo

| Layer | Implementazione attuale |
|---|---|
| Frontend | Next.js 16 + React 19 + TypeScript + Tailwind 4, basePath `/app`, output `standalone`. Deploy Railway. |
| Backend | FastAPI Python 3.12 + uvicorn. Deploy Railway. |
| LLM chat | `claude-haiku-4-5` (configurabile via env `ANTHROPIC_MODEL`) |
| LLM report PDF | `claude-sonnet-4-5` (env `ANTHROPIC_PDF_MODEL`), opzionale multi-call 3-fase per evitare troncamento |
| Auth | Supabase Auth, JWT validation via JWKS endpoint (ECC P-256). Nessun Clerk. |
| DB | Supabase Postgres con RLS attivo per tutte le tabelle utente |
| Storage | Supabase Storage, bucket `kbot-uploads` e `kbot-reports` |
| Pagamenti | Stripe Checkout one-time 19€ (`REPORT_PRICE_EUR_CENTS=1900`) + webhook FastAPI con verifica firma |
| Email | Resend (dominio `k2-ai.it` verificato), template HTML |
| PDF | ReportLab nativo Python (Flowables + Platypus + BaseDocTemplate), NON HTML/CSS print |
| RAG | BM25 in-process su `kbot_file_chunks`, NO embeddings/pgvector (MVP) |
| URL fetch | Auto-fetch di max 2 URL per messaggio, cache estrazione |

### 1.2 Endpoint backend FastAPI

Già presenti in `kai-website/kbot/backend/app/api/`:

| Endpoint | Funzione |
|---|---|
| `POST /api/kbot/session` | Crea sessione (anonima o linked a user) |
| `GET /api/kbot/session/{id}` | Lettura sessione |
| `POST /api/kbot/session/{id}/link-user` | Lega sessione anonima a utente (claim con token monouso) |
| `GET /api/kbot/sessions` | Storico sessioni utente (dashboard) |
| `POST /api/kbot/message` | Turno chat → Claude Haiku con system prompt v2 modulare |
| `POST /api/kbot/upload` | Upload file → Supabase Storage + extraction + chunking |
| `POST /api/kbot/report` | ReportData deterministico (no LLM) |
| `POST /api/kbot/checkout` | Crea Stripe Checkout session dinamica (success_token opaco H-7) |
| `POST /api/kbot/generate-pdf` | Sonnet → JSON strutturato → ReportLab → upload Storage |
| `GET /api/kbot/status` | Polling stato post-checkout |
| `POST /api/stripe/webhook` | Verifica firma, marca paid, scrive `has_paid` su `app_metadata`, triggera generate-pdf |
| `GET /api/kbot/skills` | Lista skill disponibili (parsing front-matter SKILL.md) |
| `POST /api/kbot/fetch_url` | Estrazione contenuto URL on-demand |
| `POST /api/kbot/followups` | Suggerimenti follow-up per la chat |
| `POST /api/kbot/diagnostics` | Diagnostica sessione |
| `POST /api/kbot/conversations` | CRUD conversazioni sidebar |
| `POST /api/kbot/export` | Export conversazione |

### 1.3 Schema DB Supabase (migrazioni applicate)

`kai-website/kbot/supabase/migrations/`:

**001_init.sql**:
- `conversations` (legacy Clerk, non usata in v2)
- `analytics_events`
- `feedback`
- `kbot_sessions` (definita altrove, principale)
- `kbot_conversions` (logging conversioni Stripe)

**002_kbot_persistence_rag.sql**:
- `kbot_conversations` (sidebar per utente loggato, RLS owner-only)
- `kbot_file_chunks` (chunk testuali per RAG BM25, embedding JSONB opzionale per future migration a pgvector)
- RLS rigorose: SELECT/INSERT/UPDATE/DELETE solo per `auth.uid() = user_id`

**003_kbot_extraction_cache.sql**:
- Cache estrazione testo da PDF (sha256 → text estratto)

**Tabella `kbot_sessions`** (definita prima delle migrazioni numerate, presumibilmente nello schema base):
- `id` UUID
- `user_id` FK su `auth.users` (nullable per sessioni anonime)
- `link_token` per claim anonimo → loggato (security H-6)
- `step`, `status`, `path`, `mode`
- `messages` JSONB array
- `collected_data` JSONB (con `service_id`, `extractedData`, `uploaded_files`, `analyzed_urls`, `mode`)
- `success_token` per redirect Stripe (H-7, no leak in URL)
- `email`, `stripe_session_id`, `paid_at`
- `pdf_url`

### 1.4 Sistema skill: già implementato

In `kai-website/kbot/backend/app/lib/skills.py`:
- Loader che legge `SKILL.md` + opzionalmente `references/*.md` per ogni skill
- Cache LRU (`@lru_cache(maxsize=512)`)
- Function `load_skill_bundle()` che assembla N skill in un singolo testo cappato a `max_total_chars` (default per chat, vedi `CHAT_SYSTEM_MAX_CHARS`)
- Discovery automatica delle skill in `SKILLS_DIR` (env `KBOT_SKILLS_DIR`, default `kai-website/lib/skills/`)

In `kai-website/kbot/backend/app/lib/services.py`:
- Registry hardcoded di 20 servizi `P01`-`P20` con skill associate (mirror manuale di `src/data/suiteAiServices.ts`)
- Esempio: `P01 — Agenti AI Email & CRM` → skill `draft-outreach`, `pipeline-review`, `email-sequence`, `crm-customer-experience`, `sales-strategy`, `lead-qualification`
- Intent detection da keyword: ogni servizio ha 5-15 keyword associate per inferire il servizio quando l'utente non lo seleziona esplicitamente
- Funzione `resolve_skills_for_session()` che decide quali skill caricare nel system prompt

In `kai-website/kbot/backend/app/lib/prompts.py`:
- `build_system_prompt_v2(skill_names, session)` assembla:
  - Override per il modo "premium = solo analisi/report" (vieta esplicitamente di proporre automazioni)
  - Servizio selezionato (o invito a chiederlo se cold start)
  - File caricati + URL analizzati (riferimenti in sessione)
  - Sezione RAG dinamica con BM25 top-K chunk dai file utente, citazioni `[pag.N]`
  - Bundle skill caricato dinamicamente

### 1.5 Sicurezza già in produzione

- RLS Supabase su `kbot_conversations`, `kbot_file_chunks`
- JWT verification via JWKS (no shared secret hardcoded)
- Prompt injection mitigation: file utente avvolti in `<UNTRUSTED_FILE_CONTENT>` con istruzione esplicita al modello di non eseguire istruzioni interne
- Success token opaco per redirect Stripe (no UUID in URL — H-7)
- Link token per claim sessione anonima (no enumeration — H-6)
- CORS lista bianca esplicita, mai `*` con credentials
- Stripe webhook con verifica firma `stripe.Webhook.construct_event`
- Internal API key per generate-pdf server-to-server

### 1.6 Pricing attuale

- 1 prodotto: report PDF premium a 19€
- `STRIPE_TIER0_PAYMENT_LINK` env var = payment link statico per distribuzione esterna (email mkt, social) con supporto `client_reference_id` per agganciarlo alla sessione K-BOT corrente
- Webhook gestisce idempotenza, scrive `has_paid` su `app_metadata`, triggera generate-pdf

### 1.7 Continuità cross-bot

- Widget K-BOT lite su `suite-ai.html` per qualificazione lead (vive nel sito Vite)
- `sessionStorage["kbot.site_session_id"]` trasferito al K-BOT Premium tramite query `?continue=<session_id>` su `/app/`
- K-BOT Premium adotta la sessione esistente invece di crearne una nuova

---

## 2. Cosa propone l'architettura v2

Sintesi dal documento `ARCHITETTURA-sistema-K2AI-frontend.md`:

1. **Portale SaaS B2B2C** con UNA chiave API Claude server-side per tutti i clienti
2. **KBot = loop agentico nel backend** che chiama API Claude con tool use
3. **MCP catalogo K2-AI remoto** (stateless) per prezzi/percorsi/sconti, esposto come MCP server e collegato all'API Claude tramite MCP connector
4. **Skill/orchestratori** che producono i deliverable (modello di invocazione "da verificare")
5. **Wallet crediti nel backend** (saldo, movimenti, decadenza 12 mesi, transazione di addebito prima dell'erogazione)
6. **Multi-prodotto**: Check Express 49€, Boost diretti 1.499-2.499€, Boost-a-percorsi (5 percorsi × 4-5 tappe), abbonamenti Pro 49€/mese e Business 149€/mese
7. **Frontend portale** con chat + UI wallet + deliverable scaricabili

Il doc compagno (`README-integrazione.md`) aggiunge le **4 leve commerciali**:
endowment (crediti pre-pagati), protezione (decadenza 12 mesi), sconto piano (L3),
retainer (L4).

---

## 3. Confronto puntuale: cosa esiste, cosa è nuovo, cosa è confuso

### 3.1 Cose che il doc propone come "da costruire" ma esistono già

| Proposta v2 | Stato reale |
|---|---|
| "Portale web con login, area riservata" | ✅ Implementato: `kbot/src/app/sign-in/page.tsx`, Supabase Auth, `<AuthGate>` |
| "Backend con API key Claude server-side" | ✅ Implementato: `kbot/backend/app/api/message.py` usa `anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)` lato server, key in env, mai esposta al browser |
| "Multi-tenant rigoroso" | ✅ Implementato: ogni sessione ha `user_id` FK, RLS Postgres attive, ownership check su ogni endpoint (`_check_ownership` in `message.py`) |
| "Storico conversazioni nel DB" | ✅ Implementato: `kbot_sessions.messages` JSONB + `kbot_conversations` per sidebar |
| "Loop conversazionale: invii messaggio → Claude risponde → backend esegue → ripassi storico" | ✅ Implementato: `compact_messages` + storico ripassato a ogni turno in `message.py` |
| "Wallet, sessione, deliverable nel DB del backend (MCP stateless)" | ✅ Implementato: sessioni in Supabase, deliverable PDF in Storage, niente stato nel sistema MCP |
| "Chiave API mai nel frontend, mai nel browser" | ✅ Implementato e verificato via CORS guard, internal API key per chiamate server-to-server |
| "Skill K2-AI per produrre deliverable" | ✅ Implementato come loader di SKILL.md da `SKILLS_DIR`, già 20 servizi mappati |

### 3.2 Cose che il doc propone come novità reali

| Proposta v2 | Stato reale | Effort |
|---|---|---|
| Multi-prodotto a catalogo (Check, Boost diretti, percorsi a tappe, abbonamenti) | Solo 1 prodotto (report 19€) | Alto |
| Wallet crediti con saldo/movimenti/decadenza | Non esiste, paga 1 volta per report | Medio (~1 settimana DB+logica) |
| Percorsi a tappe (sequenza ordinata di acquisti con sconto completamento) | Non esiste | Alto (UX + state machine + N skill) |
| Sconto piano L3 (Pro -10%, Business -20%) | Non esiste, prezzo fisso unico | Basso una volta che esiste il wallet |
| MCP catalogo remoto consumato da API Claude | Catalogo è hardcoded in `services.py` (registry Python statico) | Alto (server MCP + integrazione MCP connector + auth) |
| Tool use Claude per classificare bisogno + chiamare `scheda_listino`, `scheda_percorso` | Non esiste come tool use formale — c'è intent detection da keyword in `services.py` (no Claude) | Medio |
| Loop agentico multi-turno con tool calls (Claude → tool → result → Claude → ...) | Oggi c'è 1 turno chat semplice, Claude risponde testo. Nessun ciclo tool-use → exec → rimanda | Alto |

### 3.3 Cose confuse o sbagliate nel doc

**a) Sezione 0 (fraintendimento "ogni cliente ha il suo Claude")**
Strawman. Nessuno qui ha mai pensato che ogni cliente avesse un account Anthropic separato. Sprecando spazio per smentirlo, il doc fa pensare al lettore che ci sia stata davvero questa confusione. Da rimuovere.

**b) "Skill/orchestratori = Agent Skills K2-AI" (sezione 4)**
Ambiguo. Possibili interpretazioni:
- Sono le **SKILL.md** che il backend già carica via `load_skill_bundle()` → in tal caso esistono già, sono già usate, non c'è nulla da "verificare". Il loro contenuto va nel system prompt, non sono "tool" invocabili.
- Sono **Agent Skills nel formato Anthropic** (`anthropic-skills:*` namespace) → questi vivono dentro Claude Code runtime, non sono pensati per essere chiamati da API Messages. Confusione di runtime.
- Sono **pipeline Python custom** che producono deliverable (es. `generate-pdf` endpoint che chiama Sonnet + ReportLab) → in tal caso il pattern esiste già, basta replicarlo per altri tipi di deliverable. Chiamarli "skill" è fuorviante.

Il doc va riscritto per dichiarare ESPLICITAMENTE quale dei tre significati intende. Sospetto: sta mescolando i tre.

**c) "MCP catalogo remoto chiamato da API Claude"**
Tecnicamente possibile (Anthropic supporta MCP connector remoto in API Messages, beta), ma per K2-AI è over-engineering grave. Vedi §5.

**d) `[DA VERIFICARE]` sparsi**
8 punti `[DA VERIFICARE]` in un doc di 180 righe. Tutti i punti critici (firme tool MCP, modalità invocazione skill, MCP connector nell'API) sono incognite. Un'architettura con il 30% di incognite sui pezzi tecnici reali NON è un'architettura: è uno schema concettuale. Va completato leggendo doc Anthropic e MCP server reale prima di consegnarlo a chi deve implementare.

**e) "Frontend es. React/Next"**
Già scelto e implementato (Next.js 16). Il doc non lo sa, perché ignora lo stato esistente.

### 3.4 Cose corrette nel doc (che il K-BOT esistente già rispetta)

- ✅ Architettura a layer client → backend → API Claude → tool
- ✅ Stato del cliente nel backend, non nel sistema di tool
- ✅ Loop agentico con storico ripassato (API stateless)
- ✅ Chiave API solo lato server
- ✅ Multi-tenant rigoroso
- ✅ Lettura prezzi da fonte di verità centralizzata (oggi `services.py`, domani MCP o catalog.json — la logica è uguale)

Queste sono best practice standard. Il doc le formalizza correttamente. Ma non sta proponendo nulla di nuovo a livello architetturale: sta descrivendo il pattern industria-standard di un SaaS+LLM.

---

## 4. Cosa NON torna nella proposta

### 4.1 Identità del K-BOT è incompatibile col nuovo modello

Il system prompt v2 attuale (`prompts.py`, costante `REPORT_TYPES_OVERVIEW`) è
**esplicito**:

```
REGOLE PREMIUM:
- NON proporre mai servizi di automazione, agenti AI, microapp, integrazioni, RAG o
  implementazioni software
- NON suggerire "ti facciamo l'agente che…" o "automatizziamo X"
- Output: SOLO documento di analisi / report scritto
- Se l'utente chiede automazioni o sviluppi → rimanda al sito principale k2-ai.it/suite-ai
```

Il K-BOT attuale è una **macchina da report**. L'architettura v2 vuole farlo
diventare un **agente di vendita di percorsi**. Sono due prodotti diversi con
posizionamento diverso. Decisione necessaria:

- **Opzione A**: K-BOT resta macchina da report (19€ una tantum). Il "portale
  multi-prodotto + wallet + percorsi" è un'app SEPARATA che condivide solo
  backend infra (Supabase, Stripe).
- **Opzione B**: K-BOT viene riposizionato come agente vendita generale, e il
  prodotto "report 19€" diventa una delle N skill/output del nuovo K-BOT.

Il doc non esplicita la scelta. Senza la scelta, qualsiasi implementazione è
random.

### 4.2 Pricing: 19€ vs 49€ non è una sfumatura

L'architettura v2 cita ripetutamente "Check Express 49€" come porta d'ingresso.
Il K-BOT attuale vende a 19€ ed è live, con copy, payment link, Stripe SKU già
configurati. Cambiare prezzo significa:
- Riconfigurare Stripe (nuovo prodotto o nuovo prezzo)
- Aggiornare copy in tutti i punti del sito che citano 19€
- Decidere se 19€ resta come tripwire più aggressivo o sparisce
- Migrare eventuali link/social/firme email che puntano al payment link 19€

Non è hard ma è una decisione che va presa esplicitamente, non per implicito.

### 4.3 LLM economics: passaggio Haiku → Sonnet su chat

Oggi:
- Chat: Haiku 4.5 → ~$0.80 per milione input token, $4 per milione output (stima)
- PDF: Sonnet 4.5 chiamato 1 volta a fine sessione → costo accettabile su 19€

Con KBot agentico multi-turno con tool use:
- Tool use richiede ragionamento, Haiku spesso non basta per scelte di routing affidabili
- Sonnet 4.5: ~$3 input / $15 output per milione token
- Storico ripassato a ogni turno + tool definitions in prompt + skill bundle = prompt size cresce molto
- Stima ordine di grandezza: costo per sessione passa da ~0.01-0.05€ a 0.20-1€

Su 100 sessioni/mese: differenza è 10-100€/mese. Compatibile col budget 65€/mese
(CLAUDE.md §3)? Da verificare numericamente. Il doc non affronta il punto.

### 4.4 Wallet crediti: leva o frizione?

Doc proposta: "1 credito = 1 euro, trasparente, accumulo via abbonamento o
pacchetti, scali per ogni tappa". Razionale: leva endowment (L1) + protezione (L2)
+ sconto piano (L3).

**Funziona per**: clienti che comprano spesso (acquisti ripetuti, retainer).
**Non funziona per**: PMI che fanno 1 acquisto e basta.

Per il mercato K2-AI (PMI 5-50 dipendenti, ICP definito in CLAUDE.md §1), la
frequenza di acquisto è bassa. La PMI italiana media compra un servizio una
volta, riceve fattura, archivia. Introdurre "crediti" come valuta interna:
- aggiunge step mentale ("quanto vale 1 credito? perché non euro?")
- richiede UX wallet aggiuntiva
- abilita comportamenti di leva (L1, L3) che valgono solo SE l'abbonamento esiste
- richiede gestione decadenza 12 mesi (cron job + email reminder + UX)

**Verifica empirica necessaria**: 3-5 clienti reali vogliono comprare "crediti"
e poi spendere a tappe, o preferiscono comprare il Boost intero con fattura
diretta? Senza dati su questo, costruire wallet è scommessa.

### 4.5 MCP catalogo remoto: costo non giustificato

Catalogo K2-AI: ~25 entry (5 percorsi × 5 tappe + Boost diretti + Check + abbonamenti).
Modificato da Luca, consumato dal solo KBot.

**Opzioni di implementazione**:

| Opzione | Effort iniziale | Manutenzione | Latenza | Costi infra |
|---|---|---|---|---|
| Hardcoded in `services.py` (oggi) | 0 | bassa | ms | 0 |
| `catalog.json` in repo + endpoint Vite | 1 ora | bassa | ms | 0 |
| Tabella Supabase + lettura backend | 1 giorno | media | ms | 0 (incluso Supabase) |
| MCP server custom remoto | settimane | alta | +200-500ms per tool call | +container (5-10€/mese) |

MCP server è 100x più costoso delle alternative e fornisce valore SOLO se:
- Più client diversi consumano il catalogo (oggi: solo KBot interno)
- Partner esterni vogliono interrogare K2-AI da loro agenti Claude (oggi: zero)
- Il catalogo è esposto come API pubblica brandizzata

Verdetto: **per oggi non ha senso**. Da riconsiderare quando >1 client esterno
ne avrà bisogno.

### 4.6 Tool use vs intent detection da keyword

K-BOT oggi usa intent detection deterministica:
```python
_INTENT_KEYWORDS = {
    "P11": ["seo", "audit seo", "keyword", "ranking google", ...],
    ...
}
```
→ Trova match → seleziona servizio → carica skill correlate nel system prompt.

L'architettura v2 implica passaggio a tool use:
```
Claude riceve tool definitions → chiama classifica_prodotto → backend esegue →
ritorna a Claude → Claude chiama scheda_listino → ...
```

**Trade-off**:
- Tool use è più potente: gestisce ambiguità, multi-intent, follow-up
- Tool use è più caro: serve Sonnet, prompt più grandi, più round-trip
- Intent detection da keyword è fragile (perde sfumature) ma deterministica e gratuita

Il salto va motivato. Se l'intent detection attuale converte bene, mantenerla.
Se converte male (KBot sbaglia spesso il servizio), allora tool use è giustificato.

### 4.7 Manca completamente: dati attuali di conversione

Il doc v2 non cita un solo numero. Per decidere se costruire il sistema espanso
servono:
- Quante sessioni K-BOT/mese oggi
- Quante pagano i 19€
- Conversion rate sessione → checkout → pagamento riuscito
- Quanti utenti tornano (per stimare valore wallet/abbonamento)
- Quanti messaggi medi per sessione (per stimare costi LLM scalando a Sonnet)

Senza questi numeri, "costruiamo wallet + 5 percorsi + MCP" è un atto di fede.

---

## 5. Cosa ha senso e cosa NO (verdetto pezzo per pezzo)

| Pezzo proposto | Verdetto | Motivazione |
|---|---|---|
| Portale SaaS con login + chat + deliverable | ✅ Ha senso. **Già fatto.** | È quello che il K-BOT esistente è |
| API key Claude server-side, multi-tenant | ✅ Ha senso. **Già fatto.** | Standard SaaS+LLM |
| Loop agentico con storico ripassato | ✅ Ha senso. **Già fatto.** | Pattern standard, già implementato in `message.py` |
| Catalogo centralizzato come fonte di verità prezzi | ✅ Ha senso. **Parzialmente fatto** | Oggi è `services.py` hardcoded. Spostare in JSON/DB è marginale |
| Multi-prodotto (Check + Boost diretti + percorsi) | ⚠️ Ha senso commerciale, ma richiede skill dedicate per ognuno. Effort alto. | Da fare INCREMENTALMENTE, un Boost per volta, non tutti insieme |
| Wallet crediti | ❌ Prematuro | Senza abbonamenti che funzionano, è infrastruttura inutile. Costruire dopo 20+ abbonamenti reali |
| Decadenza 12 mesi crediti | ❌ Dipende da wallet | N/A finché wallet non esiste |
| Sconto piano L3 | ❌ Dipende da abbonamento | N/A finché abbonamento non esiste |
| MCP server remoto catalogo | ❌ Over-engineering | Per ~25 entry consumate da 1 client, JSON in repo basta |
| Skill/orchestratori come "skill K2-AI" | ⚠️ Già implementato come SKILL.md caricate nel prompt | Va chiarito se vuoi qualcosa di diverso (es. pipeline output strutturati come PDF). Se sì, replica pattern `generate-pdf` |
| Tool use Claude per classifica/lookup | ⚠️ Possibile upgrade futuro | Solo se intent detection attuale non basta. Misurare prima |
| Sezione 0 "fraintendimento Claude per cliente" | ❌ Da cancellare | Strawman, sprecato |
| 8x `[DA VERIFICARE]` su firme tecniche | ❌ Da completare prima di consegnare | Architettura con incognite tecniche non è architettura |

---

## 6. Roadmap incrementale proposta

Sequenza che riusa il 100% del K-BOT esistente e costruisce il modello v2 in
modo VALIDATO. Ogni fase ha un gate quantitativo per la successiva.

### Fase 0 — Misurare (1 settimana, zero codice)
- Estrai metriche K-BOT attuale: sessioni/mese, conversion rate report 19€,
  utenti che tornano, costi LLM mensili
- Survey 5 clienti che hanno pagato 19€: cosa farebbero dopo? hanno bisogno di
  un servizio più grande? sarebbero pronti a pagare 49€? 1.499€?
- **Gate per Fase 1**: ≥10 conversioni/mese stabili E ≥3 clienti che esprimono
  interesse a un servizio post-report

### Fase 1 — Upsell statico post-report (1-2 settimane)
- Dopo invio PDF, aggiungi sezione `/k-bot/grazie` o pannello in `dashboard/page.tsx`:
  "Sulla base della tua diagnosi (categoria X), il prossimo passo è il **Boost Y**
  a 1.499€. Prenota una call →"
- Mapping deterministico: `service_id` di sessione → 1 Boost suggerito (regole
  semplici in `lib/services.py`, no Claude)
- CTA: form Airtable per qualificazione + call commerciale (high-touch da 1.499€,
  serve umano)
- **Riuso**: 100% backend esistente. Aggiungi solo 1 mapping + 1 sezione UI
- **Gate per Fase 2**: ≥2 Boost venduti/mese via questo flow

### Fase 2 — Catalogo formalizzato + 1 percorso pilota (3-4 settimane)
- Sposta `services.py` registry → `catalog.json` in repo, letto da endpoint
  FastAPI. Stessa interfaccia, dato fuori dal codice.
- Aggiungi `kbot_purchases` table: log degli acquisti utente (Stripe → Supabase)
- Implementa UN SOLO percorso pilota (es. `advisorboost` per servizi
  professionali): 5 tappe, ognuna con sua skill (riusa pattern `generate-pdf`)
- Tappe vendute singolarmente via Stripe Payment Link, niente wallet ancora
- Sconto completamento applicato come Stripe coupon dinamico se utente ha comprato
  tutte le tappe precedenti
- **Riuso**: backend FastAPI esistente, ReportLab, Supabase auth, RLS
- **Gate per Fase 3**: ≥5 percorsi completi venduti

### Fase 3 — Estensione catalogo (1-2 mesi)
- Replica pattern Fase 2 per altri 2-3 percorsi (BuildBoost, ControlBoost) se la
  domanda esiste
- Aggiungi tool use semplice (1-2 tool: `get_servizio`, `lista_percorsi`) per
  ridurre il lavoro dell'intent detection da keyword
- Costo LLM: monitora e budgetta
- **Gate per Fase 4**: ≥3 utenti ricorrenti che acquistano >1 servizio nell'arco
  di 6 mesi

### Fase 4 — Abbonamenti + wallet (solo se Fase 3 valida) (1-2 mesi)
- Implementa `kbot_credits` (saldo) + `kbot_credit_movements` (eventi)
- Cron job decadenza 12 mesi + email reminder Resend
- Stripe Subscription per Pro/Business
- UI wallet nel portale (`<WalletPanel>` in dashboard)
- Sconto L3 calcolato lato backend, mai hardcoded
- **Gate per Fase 5**: ≥20 abbonati Pro/Business attivi

### Fase 5 — MCP server (solo se nasce un partner) (3-4 settimane)
- Costruisci MCP server K2-AI catalogo come wrapper sopra `catalog.json` + DB
- Documenta API per partner esterni
- Solo dopo che ALMENO 1 partner ha espresso interesse formale

---

## 7. Decisioni che servono PRIMA di scrivere altro codice

Da chiarire con Luca esplicitamente:

1. **K-BOT identity**: macchina da report standalone (opzione A) o agente vendita
   generale (opzione B)? Influenza il system prompt, il pricing, il copy del sito.

2. **Pricing Check**: 19€ resta (tripwire), passa a 49€ (allinea modello v2),
   o coesistono (19€ entry, 49€ premium)?

3. **Abbonamento Pro/Business**: c'è già una proposta di valore concreta da
   testare? Senza, costruire il wallet è cieco.

4. **Boost "professionale" high-touch o self-serve**: 1.499-2.499€ in self-serve
   web è ambizioso per PMI italiana. Più probabile flow: Check 19/49€ → call →
   contratto offline. Va deciso prima.

5. **Costo LLM accettabile per sessione**: budget per sessione che giustifica il
   passaggio a Sonnet con tool use (Fase 3+). Numero esplicito.

6. **Lock-in stack**: confermare che il deploy è (e resta) Railway, Supabase EU,
   no cambi infra durante l'espansione. CLAUDE.md §3 e memoria
   `feedback_railway_deploy.md` lo dicono. Il doc v2 lo ignora.

---

## 8. In una frase

L'architettura proposta è il **pattern industria-standard di un SaaS+LLM**, già
implementato per il 70-80% nel K-BOT esistente; il restante 20-30% (multi-prodotto,
wallet crediti, MCP remoto, percorsi a tappe) è una scommessa commerciale che va
validata empiricamente prima di costruirla, non tutto in blocco come il doc
suggerisce. Estendere incrementalmente il backend FastAPI già funzionante è la
strada; rifare l'architettura "da zero" perché qualcuno ha scritto un doc che
descrive con altre parole quello che esiste sarebbe spreco.

---

*Analisi tecnica basata sull'ispezione del codice in `kai-website/kbot/` al
2026-05-29. I numeri di effort sono stime; vanno raffinati con chi conosce le
priorità commerciali e i target di traffico reali.*
