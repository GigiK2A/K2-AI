# Contesto operativo K2-AI e domande al lato backend

**Da**: Luigi + Claude operativo (lato `kai-website/kbot` — il "braccio che esegue")
**A**: Luca + Claude backend (lato ecosistema — autore di MASTERPLAN v2.25, 8e_Phase0_design_API, 234 skill, 24 blueprint, MCP catalogo/normattiva)
**Scopo**: chiarire chi è chi, come si lavora davvero, e quali sono i punti aperti per evitare doc-in-vacuum.

---

## 0. Premessa critica — leggere prima di tutto il resto

I documenti scambiati finora (architettura proposta, risposta-verifica, ARCHITETTURA_PRODOTTO_FINALE) sono **utili come visione**, ma sono stati scritti come se chi li produce fosse anche chi li deploya. **Non è così**.

C'è una asimmetria operativa che va riconosciuta:

| Aspetto | Chi lo gestisce |
|---|---|
| Visione prodotto, modello commerciale, decisioni strategiche | Luca |
| 234 skill, 24 blueprint, grounding, MCP, motore 8e | Luca + Claude backend **— oggi locale sul Mac di Luca** |
| Codice del K-BOT (FastAPI + Next.js) in produzione | Luigi + Claude operativo **— deployato su Railway, accessibile dal pubblico** |
| Database Supabase EU produzione | Luigi |
| Stripe production, Resend production | Luigi |
| Monitoring, log, on-call, incident response | Luigi |
| Sito vetrina Vite, blog-bot, SEO | Luigi |

**Conseguenza**: tutto quello che il backend produce passa di qui (Luigi + Claude operativo) per arrivare in produzione. Non c'è "8e gira" finché non c'è un container Railway raggiungibile via HTTPS. Non c'è "MCP normattiva" finché non è un servizio HTTP autenticato. Non c'è "234 skill" se sono in un repo GitHub a cui questo lato non ha accesso.

**Regola operativa**: nessun pezzo del backend è "pronto" finché non rispetta i vincoli di sezione 2 di questo documento.

---

## 1. Identità del lato operativo

### Chi siamo
- **Persone**: Luigi (team operativo) + Claude operativo (questo Claude). Code è l'executor sul Mac di Luigi.
- **Repo principale**: `kai-website/` (monorepo). Include sito Vite + K-BOT (Next.js + FastAPI) + tooling.
- **Owner formale repo**: Luca (`inglucarossi73`); Luigi è team operativo con accesso completo, gestisce produzione e codice live.
- **Owner email progetto**: rluigiluca@gmail.com (CLAUDE.md §12).
- **Repo path locale**: `/Volumes/PARASSITA/K-AI/kai-website/` sul Mac di Luigi.
- **Repo remoto**: `inglucarossi73/kai-website` (proprietà Luca, accesso Luigi).

### Cosa abbiamo costruito e mantenuto finora
- Sito vetrina Vite + 10 pillar hub `/suite-ai/*.html`
- Blog automatico (blog-bot) che pubblica articoli pillar
- K-BOT Premium: Next.js + FastAPI + Supabase + Stripe + Resend + ReportLab. **In produzione**.
- 14 endpoint FastAPI (`session`, `message`, `upload`, `report`, `checkout`, `generate-pdf`, `webhook`, `status`, `skills`, `fetch_url`, `followups`, `diagnostics`, `conversations`, `export`)
- 3 migrazioni Supabase con RLS attive (`kbot_sessions`, `kbot_conversations`, `kbot_file_chunks`, `kbot_extraction_cache`)
- Sistema skill loader Python che legge `kai-website/lib/skills/` (cache LRU, references opzionali)
- Sistema RAG BM25 in-process per file utente
- Security: JWT JWKS, prompt injection mitigation, success_token opaco, link_token sessioni anonime

### Cosa NON gestiamo (è di Luca + Claude backend)
- I 234 skill/24 blueprint dell'ecosistema (sono in `inglucarossi73/k2a-skills`, repo separato, **oggi non accessibile da Luigi**)
- Il motore 8e (è "Phase0 design", non esiste codice deployato)
- Gli MCP catalogo/normattiva (girano localmente sul Mac di Luca, non raggiungibili in produzione)
- Il database/snapshot grounding normativo
- I dataset normattiva, override Cod.Civ., scaglioni fiscali
- La visione strategica e le decisioni commerciali finali

---

## 2. Vincoli operativi non negoziabili

Questi vincoli emergono dal CLAUDE.md di progetto + dalle memorie operative + dalla realtà produzione. Sono **vincoli del lato che deploya**, vanno rispettati a prescindere dalla bellezza dell'architettura proposta.

### 2.1 Stack tecnico fisso
- **Frontend sito**: Vite 5 + HTML/CSS/JS vanilla. Niente framework JS. Lighthouse mobile ≥ 90.
- **Frontend K-BOT**: Next.js 16 + React 19 + TypeScript + Tailwind 4. basePath `/app`, output `standalone`.
- **Backend K-BOT**: FastAPI Python 3.12 + uvicorn.
- **Database**: Supabase EU (Frankfurt). RLS attivo.
- **Pagamenti**: Stripe Checkout one-time. Webhook con firma. No integrazione custom.
- **Email**: Resend, dominio k2-ai.it verificato.
- **LLM**: Anthropic Claude API. No OpenAI. Haiku per chat, Sonnet per generazione.
- **Hosting**: **Railway**. Solo Railway. Non Vercel (memoria `feedback_railway_deploy.md`).

### 2.2 Budget infrastruttura
- **65€/mese hard cap** per tutta l'infra (CLAUDE.md §3). Include Railway, Supabase, Stripe (no fee mensile), Resend (free), Anthropic (variabile).
- Ogni nuovo container Railway = +5-15€/mese, va giustificato esplicitamente.
- **Costo LLM**: separato come variable cost per acquisto Boost. Non incluso nei 65€.

### 2.3 Disciplina dipendenze
- Niente npm package frontend senza motivazione esplicita di peso bundle (CLAUDE.md §3, §10).
- Niente nuova libreria Python senza valutazione.
- Niente SaaS aggiuntivi senza OK di Luca.

### 2.4 Workflow git
- Branch `feat/<area>-<descrizione>` (es. `feat/catalog-v1`).
- Commit semantici: `feat:`, `fix:`, `chore:`, `docs:`, `style:`, `refactor:`.
- PR verso `main` con checklist Lighthouse + screenshot se visivo.
- CI: type-check + lint + build devono passare.
- Default branch = `main` (live). Lavoro su `main` salvo branch redesign esplicito (memoria `feedback_branch_default.md`).
- Agente operativo può mergiare su main + deployare senza chiedere (memoria `feedback_agent_merges_main.md`).

### 2.5 Deploy reale
- **Sempre via Railway** (memoria `feedback_railway_deploy.md`): `railway up --detach` da `kai-website/` per il sito, da `kbot/` per il K-BOT, da `kbot/backend/` per il backend Python.
- Mai Vercel, mai deploy manuale ftp/ssh.
- Webhook Stripe puntano agli URL Railway production.
- Deploy materialmente eseguito da Luigi (con Claude operativo). Luca non tocca produzione direttamente.

### 2.6 Sicurezza e secrets
- Chiavi API solo in env Railway, mai in repo.
- Mai chiave API Claude in frontend/browser.
- Supabase service_role key solo backend.
- Stripe webhook secret per verifica firma.
- CORS lista bianca esplicita, no `*` con credentials.

### 2.7 Produzione = SLA non scritto ma vero
- K-BOT è live. Ha utenti veri. Pagamenti veri (19€/report).
- Rotture sono visibili, refundabili, costose in reputazione.
- Cambio architettura = piano di rollback + smoke test + monitoring.

---

## 3. Cosa significa "produrre qualcosa" su questo lato

Quando il backend dice "il servizio 8e è pronto" o "i 234 skill sono pronti", da questo lato significa che si può fare TUTTO quanto segue, oggi:

| Item | Significato operativo |
|---|---|
| Codice accessibile | Repo pubblico o sub-module nel nostro monorepo, leggibile da questo lato |
| CI/CD | Pipeline che builda, testa, deploya senza intervento manuale del Mac di Luca |
| Deployabile | Container Railway con Dockerfile/Nixpacks, healthcheck, restart policy |
| Documentato | README con env vars, comandi, troubleshooting |
| Versionato | Semver + changelog. Non "ultima versione locale" |
| Monitorabile | Endpoint `/health`, log strutturati, errori catturati |
| Testato | Smoke test contro l'endpoint reale, no "funziona sul mio Mac" |
| Aggiornabile | Procedura per aggiornare in produzione senza downtime |
| On-call definito | Chi sistema se si rompe alle 02:00? |

**Asimmetria attuale**:
- I 234 skill, 24 blueprint, MCP esistono ma **0 dei criteri sopra è soddisfatto** per essere "produzione-ready dal lato Luigi".
- L'8e non esiste come container deployato.
- Gli MCP girano sul laptop di Luca.

Non è una critica al lavoro fatto. È un check operativo: tra "fatto sul Mac di Luca" e "deployato in produzione su Railway" c'è un'enorme distanza. Questa distanza la copre Luigi, e va riconosciuta nei piani.

---

## 4. Stato reale ad oggi (con livello di certezza)

| Componente | Stato | Certezza | Note |
|---|---|---|---|
| K-BOT FastAPI in prod | Live | Alta | Railway, ~14 endpoint, RLS Supabase |
| K-BOT Next.js in prod | Live | Alta | basePath `/app`, Tailwind 4 |
| Sito Vite + 10 pillar | In sviluppo | Alta | Alcuni pillar pubblicati, altri in progress |
| Blog-bot pubblicazione articoli | Attivo | Alta | Continua per scenario C |
| Skill loader Python (esistente) | Live | Alta | `lib/skills/` letto da backend |
| 24 blueprint backend | Esistono | **Media** | Claim "L1+L2 PASS" da verificare con ispezione |
| 234 skill backend | Esistono in repo separato | **Media** | `inglucarossi73/k2a-skills`, non accessibile da qui |
| MCP normattiva/catalogo | Funzionano localmente | **Bassa per prod** | Mac di Luca, non deployati |
| 8e service | Phase0 design | **Bassa** | Nessun codice in produzione |
| Catalog.json fonte unica | Da costruire | Alta | Schema proposto, da congelare e committare |
| Membrana KBot ↔ 8e | Da definire | Alta | API + schema, da scrivere |

---

## 5. Domande critiche al lato backend

Le domande seguenti richiedono risposte **operative e verificabili**, non architetturali.

### 5.1 Accesso ai repository

**5.1.A** Repo `inglucarossi73/k2a-skills` (proprietà Luca): è pubblico, privato collaborativo, o privato chiuso? Come accede Luigi (sub-module nel monorepo, deploy artifact, fork)?

**5.1.B** Se il repo è privato: Luca deve aggiungere Luigi come collaboratore? Come si autentica una CI (GitHub Actions del monorepo `kai-website`) per leggere e sincronizzare?

**5.1.C** Strategia di sync: sub-module, npm package, Python package PyPI, CI artifact, file copy manuale? Trade-off per ognuna nel nostro stack.

**5.1.D** Versioning: come sappiamo quale versione di `k2a-skills` è compatibile con quale versione di 8e e quale versione di catalog.json?

### 5.2 Servizio 8e: realtà produzione

**5.2.A** `8e_Phase0_design_API.md`: dove sta il documento? Mandarlo per ispezione, è il contratto su cui si costruisce tutto.

**5.2.B** Esiste anche solo uno skeleton FastAPI/Express/qualunque che risponde a `POST /v1/deliverables` con un mock? O è 100% disegno?

**5.2.C** Quando il backend si impegna a consegnare 8e Phase-1 skeleton end-to-end su LegalBoost in un container deployabile? Data realistica, non aspirazionale.

**5.2.D** Stack del servizio 8e: Python? Node? Quale framework? Quali dipendenze? Servono per stima container Railway.

**5.2.E** Persistenza: 8e è stateless al 100% per richiesta, o ha bisogno di un suo DB? Se sì, dove sta?

**5.2.F** Autenticazione KBot → 8e: API key in env? mTLS? Bearer JWT? Definire prima di scrivere il client.

**5.2.G** Limiti operativi: rate limit, timeout, max concurrent jobs. Vanno dichiarati per dimensionare il sistema.

**5.2.H** Storage output (PDF generati): dove finiscono? Supabase Storage del lato operativo (il KBot ce l'ha già) o uno storage dedicato a 8e?

### 5.3 MCP: dal Mac alla produzione

**5.3.A** Quali MCP servono **live in produzione** post-Fase 6 (dopo decisione su snapshot statico):
- `k2a-catalogo` → SE genera `catalog.json` via CI, NON serve live
- `k2a-mcp-bandi`/`agevolazioni` → potrebbe servire live se i bandi cambiano spesso
- Tutti gli altri → snapshot statico committato basta

Confermare quale lista finale.

**5.3.B** Per ogni MCP che resta live: stack di esecuzione? Container Docker? Nixpacks? Quale porta? Quale path?

**5.3.C** Snapshot grounding: dove vive il JSON? Quanto è grande? Frequenza di rigenerazione? Da quale macchina (CI in cloud, non il Mac di Luca)?

**5.3.D** Pipeline di rigenerazione snapshot: schedule cron? Triggered manualmente? Come si versiona?

**5.3.E** Failure su MCP live (agevolazioni): cosa vede l'utente? Quanto tempo si aspetta prima di degradare con caveat?

### 5.4 Catalog.json: ownership e processo

**5.4.A** Catalog generato da `k2a-catalogo` MCP: oggi `k2a-catalogo` esiste solo sul Mac di Luca. Come si fa girare in CI per generare `catalog.json` se non c'è un container produttivo?

**5.4.B** Proposta operativa: `catalog.json` editato direttamente nel monorepo (PR review come ogni altro file), poi `k2a-catalogo` lo legge come fonte (inverte la direzione). Va bene per il backend o c'è un motivo strutturale per cui catalog **deve** essere derivato da k2a-catalogo?

**5.4.C** CODEOWNERS: chi può approvare cambi a `catalog.json`? Solo Luca? Anche il backend Claude via PR firmata? Definire policy.

**5.4.D** Validazione: JSON Schema su CI (proposto in piano §1.1). Confermare campi del schema definitivo dopo le 3 aggiunte (`genera_via`, `blueprint_id`, `output_schema_ref`).

### 5.5 Effort, timeline, responsabilità

**5.5.A** Effort stimato per ogni pezzo del backend non ancora in produzione, in giorni-persona di Luca:
- 8e Phase-1 skeleton LegalBoost: ?
- Produttizzazione MCP catalogo (se serve live): ?
- Pipeline generazione snapshot grounding: ?
- Creazione blueprint per i ~10 Boost P01-P20 che non ne hanno: ?
- Adattamento skill esistenti per integrazione con catalog.json: ?
- Documentazione operativa per ogni servizio: ?

**5.5.B** Chi scrive materialmente il codice backend: Luca + Claude backend tramite Code sul Mac di Luca? C'è un altro sviluppatore umano coinvolto?

**5.5.C** Capacità di Luca: quante ore/giorni a settimana dedica a costruire l'ecosistema backend?

**5.5.D** Bottleneck: cosa rallenta di più il lato Luca oggi? (così Luigi sa dove può aiutare o accettare ritardi)

### 5.6 Modello operativo a regime

**5.6.A** Quando un cliente paga un Boost, il flusso in produzione passa attraverso:
- KBot (Railway, gestito da Luigi)
- 8e (Railway dedicato, da deployare — chi lo gestisce in prod?)
- MCP live (Railway dedicato, da deployare se serve — chi lo gestisce in prod?)

Tutti 3 i container devono essere up. Chi è on-call se 8e si rompe alle 22:00 e c'è un cliente che aspetta un report? Luigi non può essere on-call su servizi che non conosce e non ha deployato.

**5.6.B** Aggiornamento blueprint: oggi modifichi un blueprint in `k2a-skills`, come arriva in produzione? PR → review → merge → rebuild 8e → deploy → smoke test → verify. Quanti minuti realistici?

**5.6.C** Versioning end-to-end: cliente acquista Boost X il 01/07 quando catalog v1.3 + 8e v0.5 + blueprint advisorboost v2.1 era attivo. Il 15/08 catalog è v1.4, 8e v0.6, blueprint v2.2. Se vogliamo riprodurre il report del 01/07 in caso di reclamo legale, come si fa? Snapshot delle versioni nel `kbot_purchases`?

**5.6.D** Rollback: se 8e v0.6 introduce bug e va rollbackato a v0.5, come si gestiscono i deliverable in-flight? Quando si applica il rollback?

### 5.7 Costi reali

**5.7.A** Costo per AdvisorBoost completo (token Sonnet su input + output + eventuale peer-review): stima realistica? Su 2.499€ di prezzo, quanto resta dopo costi LLM + Stripe fee?

**5.7.B** Costo Check Express 19€ con 8e: token chat (Haiku) + token generazione (Sonnet su 5 pagine) + Stripe fee 0.50€ = quanto resta?

**5.7.C** Costo container 8e mensile: stima container Railway Standard plan? Se il volume è basso (1-5 Boost/mese), il container fisso costa più dei token risparmiati?

**5.7.D** Costi MCP live (agevolazioni): se è container piccolo che gira sempre, +10€/mese. Su volume basso ha senso?

---

## 6. Cosa proponiamo come modus operandi

### 6.1 La membrana documento
Creare `docs/interfaccia-kbot-8e.md` come contratto vivente. Aggiornato solo quando cambia l'interfaccia (non a ogni iterazione). Owner condiviso.

### 6.2 Repo accessibility
Luca aggiunge Luigi come collaboratore (read-only minimo) su `inglucarossi73/k2a-skills` + ogni altro repo backend. Senza questo, "le skill esistono" è non-verificabile da Luigi.

### 6.3 Definizione di "pronto"
Un componente backend è "production-ready" quando soddisfa la checklist §3 di questo documento. Prima è "WIP utile per design", non "fatto".

### 6.4 Deployment unificato
Tutti i container del sistema vivono in Railway, project K2-AI. Una sola dashboard, una sola fonte di log, un solo billing. No GCP, no AWS, no Cloudflare Workers.

### 6.5 Pipeline di rilascio
Ogni componente backend ha:
- Dockerfile o railway.toml
- README con env vars + comandi locali + comandi deploy
- Healthcheck endpoint
- Smoke test
- Tag semver

Senza, non viene deployato.

### 6.6 Sync cycle
Doc di allineamento (come questo) scritti ogni volta che cambia la membrana o emerge una decisione che impatta entrambi i lati. Non comunicazione asincrona via WhatsApp con file mandati tra Luca e Luigi.

---

## 7. Risk register dal lato operativo

| Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|
| 8e mai prodotto da Luca come container raggiungibile | Media | Critico | Gate: prima di Fase 4, smoke test su 8e deployato in Railway accessibile a Luigi |
| MCP locali sul Mac di Luca = downtime durante ferie/manutenzione | Alta | Alto | Snapshot statico + CI di rigenerazione cloud |
| Skill in repo `k2a-skills` inaccessibile a Luigi = il KBot non può integrare niente | Alta | Critico | Luca aggiunge Luigi come collaboratore prima di scrivere codice integrazione |
| Aspettative di velocità irrealistiche dal lato Luca | Alta | Medio | Stima effort dichiarata da Luca per ogni componente, gate quantitativi |
| Drift tra catalog.json (KBot in repo Luigi) e k2a-catalogo (sul Mac di Luca) | Media | Alto | Un solo file editor di verità + CI validation |
| Cliente paga Boost ma 8e timeout/crash | Media | Critico | Refund automatico + retry + alerting (J.1 risposta) — implementazione lato Luigi, design lato Luca |
| Costi LLM esplodono con peer-review e tool use | Media | Alto | Monitoring + cap per sessione + downgrade modello se possibile |
| Container 8e fisso costa più dei revenue (low volume) | Alta | Medio | Calcolo ROI prima di deployarlo. Su volume 0-5/mese, eseguire 8e on-demand con cold start accettato |
| Luca non disponibile per debug urgente su componenti suoi in produzione | Alta | Alto | Documentazione operativa + runbook + accesso secondario Luigi a infrastruttura backend |

---

## 8. Divisione lavoro chiara

### Cosa fa Luca + Claude backend (NON Luigi)
1. Scrivere blueprint diagnostici (competenza dominio professionale)
2. Mantenere il dataset normattiva + override Cod.Civ.
3. Decidere il pricing dei Boost
4. Decidere la tassonomia P01-P20 vs blueprint (con criterio in §5 del piano)
5. Costruire l'8e e tenerlo aggiornato
6. Mantenere il MCP normattiva e gli MCP di dominio
7. Generare il contenuto deliverable (via 8e + skill)

### Cosa fa Luigi + Claude operativo (NON Luca)
1. Intake agentico (chat KBot, UI, login, sessione)
2. Stripe, billing, ricevute, fatture, abbonamenti
3. Routing al servizio giusto via catalog + tag pillar
4. Chiamata API a 8e (quando esiste)
5. Consegna deliverable al cliente (storage Supabase + email Resend)
6. Monitoring, on-call, incident response su quanto è in produzione su Railway
7. SEO, sito vetrina, blog-bot
8. Pubblicazione blueprint sul sito come offerta commerciale (cosa il cliente compra)
9. Deploy materiale di TUTTI i container Railway, inclusi quelli backend di Luca

### Zona grigia da chiudere
- Chi mantiene il container 8e in produzione: Luca lo scrive, ma Luigi lo deploya. Chi fa il bugfix se rotto in prod?
- Aggiornamento blueprint in prod: Luca commit → Luigi merge/deploy, o Luca ha accesso prod diretto?

---

## 9. In una frase

Il sistema K2-AI in produzione passa interamente per Railway, Supabase EU, Stripe, FastAPI/Next.js che questo lato gestisce; qualsiasi pezzo del backend (8e, MCP, skill, blueprint, grounding) per essere "in produzione" deve diventare deployabile, accessibile, versionato, monitorabile da qui — finché è solo "sul Mac di Luca" o "in un repo non accessibile", è un asset di design, non un asset di produzione, e il piano va dimensionato di conseguenza.

---

*Documento operativo. Risposta richiesta in `docs/risposta-contesto-operativo.md` da committare nel repo. Rispondere alle domande §5 in modo verificabile (path, container name, data realistica, numero esatto). Niente claim non operazionalizzabili.*
