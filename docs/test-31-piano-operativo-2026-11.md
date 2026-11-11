# Test 31 — chiusura delle criticità residue: verifiche e piano operativo

Data: 11/11/2026. **Nessuna modifica all'infrastruttura**: i bucket sono ancora pubblici, nessuna variabile Railway è stata toccata, nessuna migrazione applicata. Letture in produzione: solo catalogo del database, conteggi, deployment, 4 sonde HTTP anonime e 6 sul motore 8e (una con la chiave predefinita del codice, risultato sotto).

## A. Esito delle verifiche richieste

| # | Verifica | Esito |
|---|---|---|
| 1 | Build `70b7418` distribuita? | **Sì, confermata.** Il primo controllo (10:30 UTC circa) dava ancora `65972a9` con il deployment `70b7418` in `BUILDING`; il controllo successivo su `/api/kbot/capabilities` riporta `build: 70b7418`, 10 strumenti `fascicolo_*`, `fascicoliSchema:true`, `fascicoliDocVersioni:true`. Va comunque ripetuto prima di ogni passo (preflight P1). |
| 2 | Ri-firma dei vecchi link | **Provata in locale, non ancora in produzione.** Il formato dei link salvati in produzione è esattamente quello che la funzione riconosce (`https://uiuvwzrmrdqbfajguuab.supabase.co/storage/v1/object/{public,sign}/kbot-reports/…`: 66 pubblici + 24 firmati). Test: `rinfresca_url` su link pubblici e firmati scaduti → URL firmato nuovo; URL di altri host/bucket invariati; applicata a **tutte** le rotte che restituiscono un URL (status, sessione, lista sessioni, exchange, generate-pdf, save, recover, allegati nei messaggi) e solo dopo i controlli di proprietà; il database non viene modificato. Verifica su Supabase vero: lo script del punto 4, dopo il deploy. |
| 3 | Autorizzazioni dei download (citazioni, versioni PDF) | **Superata** (27 test di isolamento): viewer di sessione e di fascicolo con id di entrambe le versioni e degli allegati altrui, da sessione propria, altrui e senza token; citazioni a documenti altrui non collegate; download dei job (`/deliverables/{job}`, `/pdf`, `/xlsx`) rifiutati all'altro tenant; nuovo test-guardia: **ogni rotta che prende un identificatore** (41 oggi) deve stare nell'elenco dei test, altrimenti la suite fallisce. |
| 4 | Test di accesso prima/dopo la privatizzazione | **Pronto, non eseguito**: `backend/scripts/verifica_bucket.py` (+ 5 test su uno Storage finto). Vedi §C. |
| 5 | Chiave del motore 8e | **Trovato un problema più grave del previsto** (§B-V9). |
| 6 | `has_paid` solo da processi autorizzati | **Migrazione 011 pronta e provata su una copia temporanea, non applicata.** |
| 7 | Download protetti anche se si conosce il `job_id` | **Analisi e piano** (§D). |

### B. Nuovo difetto trovato: V9 — motore 8e raggiungibile da Internet con una chiave scritta nel codice (gravità **media-alta**)
- `k2-ai-8e` ha un **dominio pubblico** Railway (`k2-ai-8e-production.up.railway.app`). Il commento in `k2a-8e/app/auth.py` dice «l'8e non è pubblico»: in produzione non è vero.
- `require_bearer` accetta **sempre** `k2a-8e-internal-loopback` (`_INTERNAL_DEFAULT`), anche se in `K2A_8E_API_KEY` c'è una chiave vera: **ruotare la variabile non basta**.
- Prova (sonde read-only, nessun dato letto): senza chiave → 401; chiave casuale → 403; **chiave predefinita del codice → 200 su `/v1/catalog`** e 404 (cioè «autenticato, job inesistente») su un job fasullo.
- Cosa apre: `/v1/catalog`, `/v1/form`, `/v1/norme/verify`, `/v1/render` (calcolo a spese nostre), e la lettura di un job **conoscendone l'id** senza passare dai controlli del backend K-Bot. La creazione di un deliverable richiede l'entitlement JWT (`/health` dice `entitlement: enforced`), quindi non è gratuita. Il valore della chiave non è stato letto: ho provato solo il valore predefinito, già pubblico nel repository.
- Non ho potuto verificare se `K2A_8E_API_KEY` è impostata in produzione senza leggere i segreti (non l'ho fatto): è irrilevante per l'esito, perché il predefinito è comunque accettato.

## C. Modifiche: già applicate / pronte / ancora da fare

| Stato | Cosa |
|---|---|
| **Applicato in produzione** (commit `65972a9`, migrazione 010) | versionamento documenti; migrazione 010. |
| **Applicato in produzione, build `70b7418` confermata** | fix V2 (BOLA `deliverables/save`), V3 (conversazione→sessione), V4 (`has_paid` solo da `app_metadata`); `rinfresca_url` su status, sessione, lista sessioni, `checkout/exchange`, `generate-pdf`, `save`, `recover`; 25 test di isolamento. |
| **Pronto in questo ramo, NON pubblicato** | ri-firma degli allegati dentro i messaggi vecchi (`sessions.py`); test-guardia delle 41 rotte e test sui link rinfrescati (27 test di isolamento in tutto); `scripts/verifica_bucket.py` + 5 test; 8e: interruttore `K2A_8E_REJECT_DEFAULT` (spento: nessun cambio di comportamento) + 4 test; migrazione `011_kbot_profiles_has_paid_protetto.sql` (+ rollback), provata su copia temporanea. Suite backend: **1184 superati, 1 saltato, 0 falliti**; 8e: 4 test nuovi superati. |
| **Da fare in infrastruttura (serve il tuo OK, uno alla volta)** | (1) rotazione chiave 8e e attivazione dell'interruttore; (2) bucket privati; (3) migrazione 011; (4) token di download per i report (codice + frontend); (5) valutare di togliere il dominio pubblico dell'8e. |

## D. Piano operativo

Ordine consigliato, perché ogni passo è reversibile e non rompe il successivo: **P → 1 → 2 → 3 → 4**. Dopo ogni passo si ripete la prova di accesso.

### P. Preflight (tutti, sempre)
- P1. `curl …/api/kbot/capabilities` → `build` deve essere il commit atteso; `fascicoliDocVersioni:true`. Se è diverso: fermarsi.
- P2. Backup logico del solo necessario: `kbot_sessions` (colonne `id, pdf_url, collected_data->deliverable_pdf_url`), elenco `storage.buckets`, valori attuali delle variabili Railway coinvolte (solo nomi e se sono impostate; i valori restano nel gestore segreti, mai in chat).
- P3. Finestra a basso traffico; avvisare chi sta testando (i report in corso non sono interrompibili se la chiave cambia a metà).
- P4. Suite backend verde e `pytest tests/test_isolamento_tenant.py` verde sul commit che va in produzione.

### 1. Chiave del motore 8e (V9) — rotazione senza interruzione
1. Generare in locale una chiave casuale (≥ 32 byte) e conservarla solo nel gestore segreti; non incollarla in chat né nei log.
2. 8e: impostare `K2A_8E_API_KEY_NEXT=<nuova>` (accetta vecchia + nuova + predefinita). Redeploy 8e. *Verifica:* chiave nuova → 200; chat K-Bot → report ok.
3. Backend K-Bot (`k2-ai-website`): impostare `K2A_8E_API_KEY=<nuova>`. Redeploy. *Verifica:* generazione di un report di prova end-to-end (account di test tuo).
4. 8e: `K2A_8E_API_KEY=<nuova>`, togliere `_NEXT`, impostare `K2A_8E_REJECT_DEFAULT=1`. Redeploy. *Verifica:* chiave predefinita → **403**; chiave nuova → 200; report ok.
5. Revocare la chiave vecchia dove era presente.
**Rollback:** rimettere `K2A_8E_REJECT_DEFAULT=0` (o rimuoverla): il predefinito torna accettato in secondi (redeploy 8e). Non toccare il codice.
**Rischio:** se il backend manda ancora il predefinito al passo 4, la generazione si ferma (502 «motore non disponibile»): per questo il passo 3 viene prima e va verificato con un report vero.
**Passo ulteriore (consigliato, dopo):** togliere il dominio pubblico dell'8e e puntare `K2A_8E_BASE_URL` alla rete privata Railway (`*.railway.internal`): rimuove la superficie, non solo la chiave. Rollback: ricreare il dominio.

### 2. Bucket privati (V1)
1. P1 sul commit `70b7418` (o successivo).
2. **Prova «prima»** (account tuo, file fittizi, ripulisce da sola): `SUPABASE_URL=… SUPABASE_SERVICE_ROLE_KEY=… python scripts/verifica_bucket.py --fase prima --progetto uiuvwzrmrdqbfajguuab --esegui`. Atteso: link pubblico **200** (documenta l'esposizione), firmato 200, vecchio link rinfrescato 200.
3. Rendere privati **uno alla volta**, prima `kbot-reports` poi `kbot-uploads`: `update storage.buckets set public = false where id = 'kbot-reports';` (stessa cosa dal pannello Supabase).
4. **Prova «dopo»**: `--fase dopo`. Atteso: link pubblico **400/404**; firmato 200; vecchio link rinfrescato 200.
5. Prova manuale con un tuo account: dashboard (link ai report vecchi), un report nuovo, un allegato caricato, apertura di un PDF dal visualizzatore (citazione v1 e v2).
**Inventario dell'impatto:** `kbot-reports` 140 oggetti (72 report), `kbot-uploads` 65. Sessioni con link salvati: 66 `pdf_url` pubblici (ri-firmati in uscita), 25 `deliverable_pdf_url` pubblici (idem), 43 sessioni con URL di upload pubblici nei dati interni (non restituiti al client) e 1 con un URL negli allegati di un messaggio (ri-firmato in uscita). Link già **incollati o inviati per email fuori da K-Bot** (le email di report hanno il PDF in allegato) smetteranno di funzionare: è lo scopo.
**Rollback:** `update storage.buckets set public = true where id = '…';` (immediato, nessun dato perso).
**Fuori perimetro ma da sapere:** `ig-media`, `instagram-slides` e `robot` sono pubblici per scelta (Instagram richiede URL pubblici): verificare che non contengano materiale dei clienti.

### 3. `has_paid` (V5)
**Stato verificato:** tabella `kbot_profiles`: policy UPDATE «own» + grant UPDATE su tutte le colonne a `anon` e `authenticated`; nessun trigger. In produzione **nessuna riga ha `has_paid = true`** (0): non si rompe nessun utente.
**Analisi delle opzioni:**
- *Revocare il grant di colonna:* inefficace finché esiste il grant a livello di tabella; servirebbe revocare l'UPDATE di tabella e concedere le colonne ammesse una per una — fragile (ogni nuova colonna va ricordata).
- *Policy `WITH CHECK`:* non può confrontare il valore vecchio col nuovo.
- *Trigger `BEFORE INSERT OR UPDATE` (scelto):* blocca solo il cambio di `has_paid` quando la richiesta arriva con ruolo `anon`/`authenticated`; lascia passare service role (webhook di pagamento), migrazioni e connessioni dirette; non cambia nulla per le altre colonne.
**Prova (copia temporanea, nessuna modifica a `public`):** authenticated e anon `UPDATE has_paid=true` → bloccato; authenticated `INSERT has_paid=true` → bloccato; authenticated `UPDATE company_name` → consentito; service_role → consentito; connessione senza claim → consentito.
**Passi:** applicare `011_kbot_profiles_has_paid_protetto.sql` (additiva); verifica con un account di test: `update … set has_paid=true` via client deve dare errore 42501, `update … set company_name=…` deve riuscire. **Rollback:** `011_rollback.sql`.
**Resta aperto:** le altre colonne di audit (`audit_trail`, `*_accepted_at`, `revoked_*`) sono pure scrivibili dall'utente: se hanno valore probatorio (GDPR) vanno protette allo stesso modo, ma richiedono di sapere quali schermate le scrivono.

### 4. Download dei report anche se si conosce il `job_id` (V6)
**Stato:** `/deliverables/{job}`, `/pdf`, `/xlsx` impongono il proprietario **solo se c'è un token**; senza token bastano `job_id` + sessione pagata (i download partono da `<a href>` senza header). Stesso modello per `POST /checkout/exchange` (token di successo → `session_id` e `pdf_url`) e per le sessioni anonime.
**Opzioni:**
- *A. Obbligare sempre l'autenticazione* (header `Authorization`, download via `fetch` → blob): semplice e forte, ma cambia il frontend (nessun link diretto/«apri in nuova scheda»), problemi su telefono per gli xlsx.
- *B. Token di download a vita breve (scelto):* nuova rotta autenticata `POST /deliverables/{job}/link` → controlla proprietà e pagamento, restituisce `…/pdf?t=<token>` con token HMAC legato a `(job, sessione, utente, formato)` e scadenza 5 minuti; le rotte di download accettano **o** `Authorization`+proprietario **o** `t` valido; senza nessuno dei due → 401. Il `job_id` da solo non serve più. Il frontend chiede il link al clic (una chiamata in più) e apre l'URL.
- *C. Solo URL firmati dello Storage per le copie durevoli:* copre i report già salvati, non quelli in generazione sul motore.
**Rollout sicuro:** interruttore `KBOT_DL_TOKEN_REQUIRED` (spento) + modalità «ombra» che **registra** i download anonimi senza bloccarli per qualche giorno → si vede se il frontend usa ancora il vecchio percorso → poi si accende. Stessa cosa per `checkout/exchange`: token monouso con scadenza breve e risposta senza `pdf_url` (il frontend lo legge dopo con `/status` autenticato).
**Test da scrivere con la modifica:** job altrui con token valido di un altro utente → 403; token scaduto → 401; token di formato diverso → 401; job proprio senza token e senza header → 401 (a interruttore acceso); regressione: i download autenticati restano 200.
**Rischio residuo finché non è fatto:** chi conosce un `job_id` (UUID, non indovinabile) e la sessione è pagata può scaricare il report senza login; in nessun caso un altro utente *autenticato* (403) né chi non ha pagato (402).

## E. Rischi residui dopo tutti i passi
- Capability anonime: sessioni senza proprietario (UUID) e, fino al passo 4, i `job_id`.
- Nessun log di accesso ai documenti e nessun limite ai tentativi su identificatori.
- Cache di estrazione condivisa per hash del contenuto (informativo).
- Senza organizzazioni né ruoli: un account = un'azienda (piano multi-tenant nel report del test 31).
- Backup di Supabase e indici fuori portata: non verificati.

## F. Cosa ti chiedo di decidere
1. OK a pubblicare il ramo (ri-firma estesa, guardia delle rotte, script, interruttore 8e **spento**, migrazione 011 come file): nessun effetto in produzione finché non si attivano i passi.
2. OK, uno per volta, ai passi 1–3 della §D (il deploy di `70b7418` è già attivo: P1 soddisfatto, da ripetere al momento).
3. Se vuoi che implementi il token di download (passo 4): è un cambio che tocca anche il frontend.
