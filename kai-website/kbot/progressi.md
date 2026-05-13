# Progressi — K-bot

Registro cronologico di tutti i cambiamenti al progetto. Aggiornato ad ogni modifica.

---

## 2026-05-13 (sessione 11)

### Auth pages — pagine dedicate /sign-in e /sign-up

**Obiettivo:** rendere visibile e accessibile il flusso auth a tutti gli utenti.

**Nuovi file:**
- `src/app/sign-in/[[...sign-in]]/page.tsx` — pagina login Clerk (catch-all route)
- `src/app/sign-up/[[...sign-up]]/page.tsx` — pagina registrazione Clerk (catch-all route)

**File modificati:**
- `src/middleware.ts` — aggiunti `/sign-in(.*)` e `/sign-up(.*)` alle route pubbliche
- `src/components/auth/AuthGate.tsx` — modal `SignInButton` sostituito con `Link href="/sign-in"` (link diretto, no button-in-anchor)
- `src/components/layout/ChatLayout.tsx` — `UserButton` sempre visibile su tutti i device (rimosso `hidden md:flex`)
- `src/app/page.tsx` — nav mobile Account: `<Link href="/sign-in">` se non loggato, `<UserButton />` inline se loggato; importato `isSignedIn` da `useAuth()`
- `.env.local` — aggiunti `NEXT_PUBLIC_CLERK_SIGN_IN_URL`, `NEXT_PUBLIC_CLERK_SIGN_UP_URL`, `NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/`, `NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/` (naming Clerk v7)

**Fix qualità:**
- Nomi env var corretti da `AFTER_SIGN_IN_URL` (v4/v5) a `SIGN_IN_FALLBACK_REDIRECT_URL` (v7)
- Eliminato button annidato dentro Link in AuthGate (HTML invalido)

---

## 2026-05-13 (sessione 10)

### Production Upgrade — Clerk, Stripe, Supabase, rate limiting, analytics, feedback, email

**Obiettivo:** rendere kbot production-ready con auth, pagamento one-time, memoria persistente e notifiche.

**Architettura adottata:**
- Clerk gestisce identità (Google/Apple/email) e porta `has_paid` nel JWT publicMetadata
- Stripe one-time payment sblocca i download (chat rimane gratuita)
- Supabase sostituisce `chat_memory.json` per utenti loggati in report mode
- Rate limiting in-memory: 20 msg/h per IP (lead), 30 msg/h per utente (report)
- Analytics fire-and-forget su tabella Supabase `analytics_events`
- Feedback widget post-report (stelle + commento testo)
- Email notifiche post-report via Resend

**Nuovi file backend:**
- `backend/app/auth.py` — verifica JWT Clerk RS256 via JWKS, estrae `clerk_user_id` + `has_paid`
- `backend/app/rate_limit.py` — sliding window in-memory, `anon_limiter` (20/h) + `user_limiter` (30/h)
- `backend/app/supabase_client.py` — client Supabase singleton, get/append conversation memory
- `backend/app/analytics.py` — `track_event()` fire-and-forget asyncio
- `backend/app/stripe_routes.py` — `POST /api/stripe/checkout` + `POST /api/stripe/webhook`
- `supabase/migrations/001_init.sql` — tabelle `conversations`, `analytics_events`, `feedback`

**Nuovi file frontend:**
- `src/middleware.ts` — Clerk middleware Next.js 16, protegge route non-pubbliche
- `src/components/auth/AuthGate.tsx` — gate: non loggato → modal SignIn, loggato → children
- `src/components/report/FeedbackWidget.tsx` — stelle 1-5 + campo testo + submit

**File modificati:**
- `backend/app/main.py` — auth + rate limiting nel `chat()`, Supabase memory, analytics, `POST /api/feedback`, `has_paid` gate sui download, `send_report_ready_email()` via Resend
- `backend/requirements.txt` — aggiunti: PyJWT[crypto], stripe, supabase, cryptography, httpx, resend
- `src/app/layout.tsx` — wrappato con `<ClerkProvider>`
- `src/app/page.tsx` — Clerk hooks (`useAuth`, `useUser`, `hasPaid`), `AuthGate`, `startCheckout`, `submitFeedback`, rimossa `PremiumLock`
- `src/lib/api.ts` — `authToken` in `sendChat`, nuove funzioni `startCheckout`, `submitFeedback`
- `src/types/chat.ts` — `hasPaid?: boolean` in `ChatMessage`, tipo `FeedbackPayload`
- `src/components/chat/MessageBubble.tsx` — payment gate sui download (paga/scarica), `FeedbackWidget` post-report
- `src/components/layout/ChatLayout.tsx` — `UserButton` Clerk, badge Premium aggiornato, prop `isReportMode`
- `package.json` — aggiunti: `@clerk/nextjs`, `@stripe/stripe-js`

**Test backend:** 29/29 pass (auth, rate_limit, supabase_client, stripe_routes, feedback, skill_loader)
**TypeScript:** zero errori

**Azioni manuali richieste:**
1. Eseguire `supabase/migrations/001_init.sql` in Supabase Dashboard → SQL Editor
2. Compilare variabili in `backend/.env`: `CLERK_SECRET_KEY`, `CLERK_JWKS_URL`, `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `RESEND_API_KEY`, `FRONTEND_URL`
3. Compilare variabili in `.env.local`: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`

---

## 2026-05-12 (sessione 9)

### Architettura corretta: pipeline hospitality SOLO in report premium

**Errore architetturale corretto:** il workflow hospitality (raccolta dati skill → HTML report) era stato erroneamente inserito nel lead mode. Lead mode è solo chat per lead generation.

**Lead mode ora:** `build_prompt("lead")` → `ask_claude()` → risposta conversazionale. Mai report, mai pipeline hospitality, mai `hospitality_inputs_complete`.

**Report premium ora:** workflow completo —
- `report_already_done` → chat follow-up
- `_user_explicitly_requests_report` + `len >= 2` → generate con benchmark per campi mancanti
- altrimenti → `hospitality_inputs_complete` → se ok genera report, se no `_make_collection_answer`

**Debug verificato:**
- Lead mode: 4 turni incluso "genera il report" → mai report ✅
- Report mode: T1 (dati parziali) → domanda ✅ | T2 (tutti 6 campi) → report generato ✅

---

## 2026-05-12 (sessione 8)

### Ripristino workflow skill: raccolta dati → report (non report immediato)

**Regressione introdotta in sessione 6:** rimozione del gate `hospitality_inputs_complete` faceva generare il report al primo messaggio senza raccogliere nessun dato

**Fix:** ripristinato il flusso originale per lead mode esistenti:
- `hospitality_inputs_complete` → se incompleto → `_make_collection_answer` (domanda seguendo skill)
- `hospitality_inputs_complete` → se completo → `_run_hospitality_html_pipeline`
- Unica eccezione: `explicit_report` ("genera il report") bypassa il gate e usa benchmark per campi mancanti

**Fix aggiuntivi frontend:**
- Rimossa `matchSkills` call prima di `sendChat` (aggiungeva 2-3s di latenza extra)
- Aggiunto AbortController con timeout 120s su `sendChat` (preveniva risposte vuote su richieste lunghe)

**Verificato:**
- T1-T3 nuova struttura airbnb → risposta conversazionale, no report ✅
- T1-T3 agriturismo esistente → domande skill workflow ✅
- T4 (dati completi) → report auto-generato ✅
- T5 post-report → follow-up conversazionale ✅
- T6 "genera il report" → report con benchmark ✅

---

## 2026-05-12 (sessione 7)

### Fix routing report: threshold history + vecchio processo in background

**Bug 1:** `_user_explicitly_requests_report` richiedeva `len(history) >= 6` → con 4 messaggi (2 turni) il trigger "genera il report" non scattava
- Fix: soglia abbassata a `len(history) >= 2`

**Bug 2:** `new_property=True` dai turni precedenti faceva bypassare il pipeline HTML anche quando l'utente diceva esplicitamente "genera il report"
- Fix: `explicit_report` check è il primo ramo, ha priorità su `new_property`

**Bug 3:** vecchio processo uvicorn sulla porta 8000 non veniva ucciso dai restart → codice aggiornato non caricava mai
- Fix: ora usiamo `lsof -ti:8000 | xargs kill -9` prima di ogni avvio

**Verificato:**
- T1: primo messaggio nuova struttura → risposta conversazionale ✅
- T2: follow-up location → risposta conversazionale ✅  
- T3: "genera il report" → report generato con benchmark ✅ (reportPdfUrl + reportHtmlUrl presenti)

---

## 2026-05-12 (sessione 6)

### Benchmark di mercato come fallback per dati numerici mancanti

**Comportamento precedente:** se il cliente non forniva notti vendute / ricavi / ADR → bot chiedeva ripetutamente quei numeri bloccando il report

**Nuovo comportamento:** dati numerici non forniti → usa benchmark dal web (DuckDuckGo) + scoring model → report generato con "(benchmark mercato)" accanto ai valori stimati

**Modifiche:**
- `_run_hospitality_html_pipeline()`: accetta `missing_fields` e inietta nota esplicita "usa benchmark web per questi campi, NON scrivere REPORT_NOT_READY"
- Prompt HTML: rimosso `REPORT_NOT_READY` per dati stimabili; REPORT_NOT_READY solo se mancano TIPO struttura E regione (impossibile cercare benchmark)
- `_make_collection_answer()`: NON chiede più dati numerici, solo info qualitative (tipo struttura, regione, obiettivo)
- Routing lead mode: se `len(history) >= 3` → genera sempre il report con benchmark; sotto soglia → UNA domanda qualitativa
- Routing report mode: rimosse due righe di check `inputs_ok`; sempre genera con `missing_fields` passato al pipeline

**Verificato:**
- 3 turni, zero dati numerici → report generato con benchmark ✅
- `reportPdfUrl` e `reportHtmlUrl` restituiti correttamente ✅
- 13/13 unit test da verificare al prossimo restart

---

## 2026-05-12 (sessione 5)

### Fix session memory in raccolta dati + new property detection allargata + cleanup frontend

**Fix root cause: memory non iniettata in `_make_collection_answer()`:**
- Aggiunto parametro `session_summary: str = ""` a `_make_collection_answer()`
- Iniettato come blocco "CONCETTI CHIAVE SESSIONE — NON ri-chiedere questi dati già stabiliti" nel collection prompt
- Aggiornati entrambi i call site in `/api/chat` per passare `session_summary`
- Fix: bot non ri-chiede più dati già forniti (camere, notti, budget, ecc.) durante il flusso raccolta check-host

**Allargamento segnali `_is_new_property_planning()`:**
- Aggiunti: "investimento per un", "investimento immobiliare", "investimento airbnb", "piano marketing", "capire l'investimento", "valutare l'investimento", "analisi investimento", "studio di fattibilità", "rendimento atteso", "potenziale di reddito", "quanto posso guadagnare", "conviene comprare", "comprare per affittare", "mettere a reddito"
- Fix: "aiutami a capire l'investimento per un airbnb" → risposta corta consulenziale invece di raccolta dati storici

**Cleanup frontend:**
- Rimosso `generatingReport` state da `page.tsx` (non più necessario con LoadingState time-based)
- Rimosso `isReportRequest` logic da `handleSubmit`
- `<LoadingState />` senza props — si auto-gestisce con timer 8s interno

**Verificato:**
- New property detection ✅ (3 turni consulenziali, no richiesta notti/ricavi)
- Session summary creata con 11 fatti corretti ✅
- Backend restart OK ✅
- Test T7+ interrotto per crediti API esauriti

---

## 2026-05-12 (sessione 4)

### Session memory + report trigger esplicito + loading indicator

**Session memory (ispirato al pattern Agno SessionSummary):**
- `get_or_update_session_summary()`: estrae concetti chiave dalla conversazione ogni 4 turni
- Formato bullet list (max 14 punti: tipo progetto, budget, location, obiettivi, decisioni prese, ecc.)
- Salvato in `chat_memory.json` come `session_summaries[conv_id]`
- Iniettato in ogni prompt come "CONCETTI CHIAVE SESSIONE — non ri-chiedere questi dati"
- Fix: bot non ri-chiede più dati già forniti nelle conversazioni lunghe

**Report trigger esplicito in lead mode:**
- `_user_explicitly_requests_report()`: rileva "genera il report", "crea il report", ecc.
- Se trigger + storia ≥ 6 turni → usa HTML pipeline (gestisce dati mancanti con stime)
- Inietta session_summary nel contesto → report ricco anche per pianificazione strategica
- Fix: risolve il loop infinito di domande quando l'utente dice "genera il report"

**Loading indicator con progress bar (frontend):**
- `LoadingState` componente rinnovato: due modalità
  - Chat normale: tre pallini animati (invariato)
  - Generazione report: barra progresso con % simulata (0→92%) + step label rotante
- Rilevamento automatico in `page.tsx`: mode=report OR messaggio contiene "genera.*report"
- `generatingReport` state separato da `loading`

**Verificato:**
- 8 turni pianificazione + "genera il report" → HTML report generato ✅
- Session summary corretta (budget, location, target, concept) ✅
- 13/13 unit tests ✅

---

## 2026-05-12 (sessione 3)

### Fix lead mode — nuova proprietà vs check esistente

**Bug:** richieste su *nuove* proprietà (acquisto bilocale, business plan) attivavano il pipeline check-host-express → `_make_collection_answer()` chiedeva dati storici inesistenti → Claude ignorava il vincolo e generava un piano markdown da 5000 parole

**Root cause 1 — Nessuna distinzione tra nuova e esistente:**
- `_is_new_property_planning()` aggiunta: rileva segnali "ho comprato", "nuovo investimento", "rientro economico", ecc. nei primi 6 turni
- In lead mode, se `new_property=True` → regular lead chat (4-8 righe) invece del workflow check-host

**Root cause 2 — `_make_collection_answer()` senza limite token:**
- Claude poteva scrivere quanto voleva → generava report completi
- Fix: `max_tokens=350` + prompt rafforzato ("MASSIMO 4 RIGHE. UNA domanda.")

**Risultato verificato:**
- Nuova proprietà → risposta 4 righe conversazionale ✅
- Proprietà esistente → raccolta dati + HTML report in 5 turni ✅
- 13/13 unit test ✅

---

## 2026-05-12 (sessione 2)

### Fix pipeline HTML hospitality — report da lead mode

**Root cause 1 — Report mai generato in lead mode**
- Causa: il blocco HTML era dentro `if body.mode == "report"` → in lead mode Claude rispondeva sempre in chat
- Fix: aggiunto blocco hospitality anche in lead mode — quando tutti i 6 campi sono presenti, genera HTML automaticamente

**Root cause 2 — `report_sources_are_ready()` bloccava hospitality anche in report mode**
- Causa: gate veniva valutato PRIMA di `detect_hospitality_template()` — conversazione corta → gate falliva → niente report
- Fix: in report mode, hospitality bypassa `report_sources_are_ready()` e va diretto a `hospitality_inputs_complete()`

**Root cause 3 — Doppio report su follow-up**
- Causa: `report_already_done` controllava solo l'ultimo messaggio assistant → dopo un turn di chat il check falliva
- Fix: controlla tutti i messaggi assistant della conversazione per "Il report è pronto"

**Refactoring**
- Estratte due helper functions: `_run_hospitality_html_pipeline()` e `_make_collection_answer()` — eliminata duplicazione di codice tra lead/report mode
- `/api/chat` endpoint completamente riorganizzato: `detect_hospitality_template()` prima di ogni altra cosa

**Test e2e verificato**
- Flusso completo: 5 turni raccolta dati → report HTML 1.4MB generato automaticamente al completamento
- Follow-up post-report: risposta chat, nessun report duplicato
- `pytest tests/` 13/13 pass

---

## 2026-05-12

### Integrazione skill hospitality (29 skill)
- Estratte 29 skill da `k-bot-hospitality-skills` nella cartella `assets/skills/hospitality/`
- Backend aggiornato con `SKILLS_ROOTS` (lista di 2 root invece di 1)
- `get_skill_packs()` ora scansiona entrambe le root, accetta sia `skills.md` che `SKILL.md`
- Totale skill caricate: **49** (20 generali + 29 hospitality)
- Le skill hospitality si attivano automaticamente per query su RevPAR, agriturismo, OTA, ecc.

### Fix pipeline Report Premium

**Bug 1 — Lead mode si comportava come report mode**
- Causa: `SKILL.md` dei file hospitality iniettava 3000 char di istruzioni di workflow nel contesto lead
- Fix: `skill_limit = 600 if mode == "lead" else 3000`

**Bug 2 — Report non si generava mai (messaggio "dati insufficienti")**
- Causa: soglia `report_sources_are_ready()` troppo alta (300 char)
- Fix: soglia abbassata a `len(combined) > 100 OR len(re.findall(r"\d+[.,]?\d*\s*[€%]?", combined)) >= 3`

**Bug 3 — `get_skill_packs()` chiamata due volte per ogni request**
- Fix: `find_relevant_skills()` accetta parametro `packs` opzionale per evitare doppio I/O

### Pipeline HTML report con WeasyPrint
- Aggiunto `weasyprint==68.1` alle dipendenze
- Funzione `detect_hospitality_template()`: rileva quale template HTML usare in base alle skill attive
  - `check-host-express` → `template-semaforo-host.md` (pagella con semafori)
  - `flusso-hostboost-ricettive` / `orchestratore-hospitality` → `template-dashboard-html.md` (dashboard completa)
- `build_html_report_prompt()`: prompt dedicato che inietta template + scoring model → Claude genera HTML completo
- `save_html_and_pdf()`: salva `.html` + converte in `.pdf` via WeasyPrint, restituisce entrambi gli URL
- Endpoint `GET /api/reports/{report_id}/html` per servire il file HTML
- Frontend aggiornato: pulsante "Apri report" (HTML) + "Scarica PDF" nel MessageBubble

### Test suite
- `backend/tests/test_skill_loader.py`: 13 test su skill loader, report gate, error messages

---

### Ricerca web benchmark (DuckDuckGo)
- Aggiunto `ddgs>=9.0.0` alle dipendenze (gratuito, nessuna API key)
- Funzione `search_web_benchmarks(property_type, region)`: ricerca DDG per benchmark aggiornati
- Integrata nel flusso report hospitality: cerca benchmark per tipo struttura + regione rilevati dall'input
- Risultati iniettati nel prompt come "BENCHMARK AGGIORNATI DAL WEB (priorità alta rispetto ai valori statici)"
- Fallback silenzioso: se DDG fallisce, usa benchmark statici da `scoring-model-host.md`

### Report HTML dinamico — niente più template fissi
- Creato `assets/report-design-system.md`: sistema di design completo con palette, tipografia, componenti CSS (cards, tabelle, badge semaforo, accordion, gauge SVG, barre progress, footer)
- Logo K2-AI (`LOGOK2-AI.png`) caricato in base64 una volta all'avvio (`_LOGO_B64`)
- `build_html_report_prompt()` completamente riscritto: niente template_spec, Claude riceve design system + skill content e costruisce il documento adattandosi alla richiesta
- Claude usa `{{K2AI_LOGO}}` come placeholder, sostituito con base64 reale in post-processing
- `detect_hospitality_template()` ora riconosce tutte le 12 skill hospitality (non solo 2) e non restituisce più template_file — restituisce solo `(is_hosp, skill_name)`
- Qualsiasi richiesta hospitality in report mode → HTML pipeline, indipendentemente dal tipo di report richiesto

### Fix troncatura e qualità PDF
- **Troncatura:** `max_tokens` per generazione HTML aumentato da 8.000 a 16.000 — il report non viene più tagliato a metà
- **PDF quality:** sostituito WeasyPrint con Playwright+Chromium — Playwright renderizza l'HTML in un browser headless reale, quindi Chart.js viene eseguito, CSS variables funzionano, grafici e layout sono identici al browser
- `save_html_and_pdf()`: salva l'HTML su disco, poi Playwright lo carica via `file://`, aspetta `networkidle` (tutti i JS eseguiti), genera PDF A4 con margini 12mm e `print_background=True`
- Aggiunto `playwright>=1.40.0` a `requirements.txt`

### Fix report HTML — doppio bug su generazione
- **Bug 1:** prompt HTML generation non abbastanza imperativo → Claude ignorava le istruzioni e rispondeva con testo conversazionale. Fix: intestazione prompt riscritta con "FORMATO OUTPUT — ASSOLUTO E NON NEGOZIABILE", esplicita che ZERO testo è ammesso prima di `<!DOCTYPE html>` e NON fare domande
- **Bug 2:** quando la risposta non conteneva `<!DOCTYPE html>`, il sistema salvava il testo conversazionale come HTML → PDF corrotto. Fix: se `html_start == -1` dopo entrambi i tentativi, blocca con messaggio di errore invece di salvare spazzatura

### Fix raccolta dati hospitality — prompt conversazionale dedicato
- **Root cause:** `build_prompt()` in modalità report conteneva "Se mancano dati, crea sezione 'Dati richiesti per versione finale'" → Claude generava report parziale invece di fare domande
- Fix 1: rimossa quella istruzione, sostituita con "NON generare mai un report parziale"
- Fix 2: quando `inputs_ok=False`, ora si usa un `collection_prompt` dedicato che istruisce Claude a fare UNA domanda alla volta, seguire il workflow della skill, spiegare perché serve il dato, non generare alcun report
- Il prompt di raccolta inietta le skill complete (3000 char) per seguire il workflow definito nella skill

### Workflow skill hospitality rispettato — raccolta dati obbligatoria
- Aggiunta funzione `hospitality_inputs_complete(user_input, history)`: chiede a Claude di verificare se i 6 campi obbligatori del check-host-express sono presenti nella conversazione
- Se mancano campi → Claude segue il workflow della skill e fa le domande in modo contestuale (non un form fisso)
- Solo quando tutti i 6 campi obbligatori sono presenti → genera il report HTML
- Le skill vengono ora seguite come definito (raccolta input prima della generazione)
- Costante `HOSPITALITY_REQUIRED_FIELDS` con la lista dei 6 campi obbligatori e 3 opzionali
- Fallback "fail open": se il check fallisce per errore tecnico, procede alla generazione per non bloccare

### Upgrade template report

**`template-semaforo-host.md` (pagella check-host-express) — riscritta**
- Design language premium (palette `--primary: #0F2544`, ombre, hover effects)
- Executive Summary card scura con gauge, 3 insight auto, percentile
- Gap Analysis: calcolo in €/anno di quanto si perde vs mediana e vs top 25%
- Ogni KPI mostra impatto economico stimato
- Sezione "Punti di forza" (non solo diagnosi negativa)
- Azioni con step operativi concreti, tool nominata, timing, KPI di misura
- Gauge SVG semicircolare con gradiente rosso→verde

**`template-dashboard-html.md` (HostBoost full) — riscritta**
- 10 sezioni (da 8): aggiunto Booking Window, Cancellation Rate, Compset Pricing
- Radar chart per posizionamento visuale (tu vs mediana vs top 25%)
- Heatmap settimanale stagionalità
- Forecast 3 scenari con ROI esplicito del piano HostBoost
- Architettura dati JSON strutturata per Claude
- Ogni azione con step operativi, budget, rischi, come misurare
