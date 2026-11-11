# Test 31 — audit di sicurezza multi-tenant di K-Bot

Data: 11/11/2026. Metodo: lettura del codice di tutte le 71 rotte, interrogazione **in sola lettura** del catalogo del database di produzione (RLS, policy, grant, bucket, conteggi), sonde HTTP anonime a produzione (4), e una batteria di test automatici con due aziende fittizie. Nessun utente, tenant o dato creato in produzione; nessun dato reale usato.

## 1. Architettura di isolamento effettivamente implementata

**K-Bot isola per ACCOUNT, non per azienda.** Non esiste alcuna entità organizzazione/tenant, alcuna associazione utente↔azienda, alcun ruolo o permesso per fascicolo/documento/operazione (nessun `org_id`, `tenant_id`, `azienda_id`, tabella di membership nelle migrazioni o nel codice). Ogni login Supabase è un silo a sé: `user_id` = `sub` del JWT. Due colleghi della stessa azienda con due account non condividono nulla; una stessa azienda non può avere due utenti con accesso agli stessi fascicoli. **Non va dichiarato multi-tenant.**

Come è garantito l'isolamento (verificato nel codice):
- Il backend usa la **service role** di Supabase (aggira RLS): l'isolamento sta tutto nel codice, non nel database.
- Fascicoli, record, eventi, documenti, versioni: ogni lettura/scrittura passa da `_righe(tabella, user_id, …)` con `eq("user_id", …)`; l'identità viene dal JWT (`require_user`) o dal contesto del turno (`ContextVar` impostata dall'endpoint dopo l'autenticazione). Nessuno strumento `fascicolo_*` accetta un parametro di tenant: l'utente non è mai un argomento.
- Sessioni di chat: `user_id` sulla riga; ogni endpoint che prende `session_id` verifica `owner == chiamante` (403). Le sessioni **anonime** (senza proprietario) sono accessibili da chi ne conosce l'UUID (capability) e si «reclamano» solo con un `link_token` emesso alla creazione.
- Conversazioni (`kbot_conversations`): filtro per `user_id` e controllo proprietario; in più RLS con policy `auth.uid() = user_id`.
- Memoria persistente (`kbot_client_memory`, profilo): chiave `user_id`, mai un parametro.
- Documenti: percorso nello storage deterministico per sessione; l'apertura passa dal backend (`/documents/{id}/view`), che risolve l'id **solo** fra i documenti della sessione dell'utente o dei suoi fascicoli.
- Database (produzione, 11/11/2026): RLS **attiva su tutte le 83 tabelle `public`**; sulle tabelle dei fascicoli (`kbot_fascicoli`, `_voci`, `_documenti`, `_eventi`, `kbot_file_chunks`, `kbot_extraction_cache`) **zero policy** → `anon` e `authenticated` non leggono né scrivono nulla pur avendo i grant standard di Supabase: solo il backend le raggiunge.
- Produzione, sonde anonime: `/fascicoli`, `/conversations` → 401; `/diagnostics` → 401 (INTERNAL_API_KEY impostata); sessione inesistente → 404.

## 2. Vulnerabilità e debolezze

| # | Gravità | Cosa | Stato |
|---|---|---|---|
| V1 | **Alta** | I bucket `kbot-uploads` e `kbot-reports` sono **pubblici** in produzione. Chiunque conosca il percorso (`<uuid sessione>/<ts>-<nome>`, `deliverables/<uuid>/<job>.pdf`) scarica allegati e report **senza autenticazione**: gli URL firmati e i controlli del backend non servono a nulla su un file pubblico. Il codice nuovo crea già bucket privati e firma gli URL («i bucket già esistenti in prod vanno resi privati manualmente»: non è mai stato fatto). 66 sessioni su 92 con `pdf_url` hanno ancora un link pubblico; 43 sessioni hanno URL pubblici di upload. Il percorso contiene un UUID (122 bit) quindi non si indovina: è sfruttabile solo da chi ha ricevuto/intercettato il link (email, log, cronologia, referer). | Codice **corretto** (`rinfresca_url`: i vecchi link pubblici e i firmati scaduti si ri-firmano a ogni lettura, solo dopo i controlli di proprietà). **Bucket NON ancora resi privati**: modifica di infrastruttura in produzione, richiede il tuo OK (rollback: `update storage.buckets set public=true …`). |
| V2 | **Media** | BOLA su `POST /deliverables/save`: accettava la PROPRIA `session_id` con il `job_id` di un ALTRO tenant, scaricava il PDF del report dal motore e lo salvava nello storage della sessione di chi chiamava (restituendone l'URL). Provato dal test prima del fix (HTTP 200 con il PDF dell'altra azienda). Richiede di conoscere un `job_id` (UUID), quindi non enumerabile. | **Corretto**: si salva solo un job che la sessione ha generato (`deliverable_job_id`/`deliverable_saved_job`), altrimenti 403. |
| V3 | **Bassa** | `POST/PATCH /conversations` accettava un `kbotSessionId` qualunque, anche di un altro tenant (riferimento non validato; la sessione restava illeggibile: 403). Il primo test era vacuo (chiave di risposta sbagliata) e l'ho riscritto. | **Corretto**: 403 se la sessione ha un altro proprietario. |
| V4 | **Bassa** | `has_paid` era letto anche da `user_metadata`, scrivibile dall'utente stesso (`auth.updateUser`). Nel backend serve solo a mostrare lo stato dell'account (le porte reali sono `billing_store` e `status=paid`), ma è un diritto dichiarato dal client. Il frontend (`providers.tsx`) lo legge ancora per la sola UI. | **Corretto** nel backend: solo `app_metadata` (scritto dal webhook di pagamento). Frontend non toccato. |
| V5 | Bassa | La riga `kbot_profiles` è modificabile dall'utente (policy UPDATE own) **incluso `has_paid`**. Nel repo la tabella è letta solo da `apps/board`; nessun consumo come diritto d'accesso trovato. | **Non corretto**: da decidere (colonna non scrivibile dal client, o policy a colonne). Non verificabile da qui chi la legga fuori dal repo. |
| V6 | Bassa | Il download dei deliverable (`/deliverables/{job}`, `/pdf`, `/xlsx`) impone il proprietario **solo se il chiamante presenta un token**: senza token basta il `job_id` + sessione pagata (capability opaca; il commento nel codice lo dichiara: i download partono da `<a href>` senza header). Idem `POST /checkout/exchange` (token di successo → `session_id` e `pdf_url`) e le sessioni anonime (UUID). | **Non corretto**, per progetto: è un modello a capability. Richiede URL firmati per-job per essere chiuso. |
| V7 | Informativa | Cache di estrazione (`kbot_extraction_cache`) con chiave SHA-256 dei byte: due tenant che caricano lo stesso file condividono il testo estratto (chi lo carica ha già i byte). Nessuna fuga di contenuto, ma è un oracolo «questo file è già stato caricato». | Non corretto, accettato. |
| V8 | Informativa | Il motore 8e usa `K2A_8E_API_KEY` con valore predefinito noto se non impostata. | Non verificabile da qui (non ho letto i valori dei segreti di produzione): da controllare che la variabile sia impostata. |

Conteggio: **1 alta, 1 media, 2 basse corrette + 2 basse aperte (V5, V6), 2 informative.** Corrette 4 su 8 (V1 solo in parte: il bucket resta pubblico finché non lo rendi privato).

Nessuna fuga di dati fra account è stata riprodotta con i soli identificativi «validi» di un altro tenant sulle rotte e sugli strumenti dei fascicoli: V2 era la sola strada riprodotta (e richiede un `job_id`).

## 3. Verifica per componente

| Componente | Isolamento verificato | Test eseguiti | Esito | Gravità | Correzioni |
|---|---|---|---|---|---|
| Fascicoli (API: elenco, apertura, storico, duplicati, consolida, annulla evento, PATCH/DELETE voce, DELETE fascicolo) | Sì | 11 chiamate × 2 direzioni (A→B, B→A), anche con l'id altrui nel percorso del proprio fascicolo; confronto prima/dopo di tutti i dati della vittima | Superato | — | — |
| Documenti e versioni (viewer di sessione e di fascicolo, v1 e v2, allegati di sessione) | Sì | id di entrambe le versioni e degli allegati altrui da sessione propria, altrui e senza token; controllo positivo sui propri | Superato | — | — |
| Citazioni persistenti `[[fonte|…]]` | Sì | citazione a un documento altrui: non collegato, tolta, nessun testo | Superato | — | — |
| Sessioni/chat (24 chiamate: 21 POST e 3 GET che prendono `session_id`, anche streaming SSE) | Sì | 24 chiamate dall'altro tenant e senza token: 403/404/409 e nessun segreto in risposta | Superato | — | — |
| Conversazioni | Sì (dopo fix) | lista, PATCH, DELETE altrui, collegamento a sessione altrui | Superato | Bassa (V3) | Sì |
| Memoria persistente e profilo | Sì | lettura e cancellazione per `chiave` non scelgono l'utente | Superato | — | — |
| Strumenti `fascicolo_*` (10) | Sì | 19 tentativi sull'altro tenant + parametri `user_id/tenant/owner/azienda` + richieste contemporanee interleaved | Superato | — | — |
| Strumenti dalla chat vera (modello finto che prova ogni strumento) | Sì | il risultato che torna al modello non contiene dati altrui | Superato | — | — |
| Deliverable/report (job) | Parziale | download dell'altro tenant (403); `save` con job altrui | Superato dopo fix | Media (V2) | Sì |
| Storage (bucket, URL) | **No** | catalogo produzione, conteggio dei link pubblici | **Non superato** | **Alta (V1)** | Codice sì, bucket no |
| Database (RLS) | Sì | catalogo produzione | Superato | — | — |
| Autenticazione/diritti | Parziale | `has_paid` | Corretto | Bassa (V4) | Sì |
| Ruoli nella stessa azienda | **Non esistono** | codice e migrazioni | Non implementato | requisito | piano §6 |
| Cache, log, analytics | Sì (lettura) | nessuna cache globale con dati utente; telemetria senza testi | Superato | — | — |
| Backup, indici vettoriali, MCP, job asincroni | Non verificabili | nessun indice vettoriale (BM25 in memoria sui chunk della sessione); MCP senza dati per tenant; backup Supabase fuori portata | — | — | — |

## 4. Test

- `tests/test_isolamento_tenant.py` — **25 test**, rilanciabili con `pytest tests/test_isolamento_tenant.py`: A→B e B→A su fascicoli, documenti/versioni/citazioni, sessioni, conversazioni, memoria, strumenti, job, richieste contemporanee, bucket, `has_paid`; più il controllo che le migrazioni non introducano policy sulle tabelle dei fascicoli.
- **Mutanti** sui controlli di isolamento: 8 su 8 uccisi (job non legato alla sessione, conversazione→sessione altrui, `_righe` senza filtro utente, `documento_dell_utente`, `collega_citati`, viewer senza ownership, GET fascicolo senza filtro, `status` senza ownership). Un primo mutante sopravviveva (viewer: il test non attaccava gli *allegati di sessione*): aggiunto il caso.
- Suite backend completa dopo i fix: **1177 superati, 1 saltato, 0 falliti** (prima dei fix: 1152 superati; la differenza sono i 25 test di isolamento).

## 5. Haiku 5.5

**Non eseguito**: da qui non è raggiungibile (nessuna chiave Anthropic). Non l'ho sostituito con un'altra simulazione dichiarata equivalente. Ho invece provato **il lato server**, che è quello che conta: un modello finto scritto da me chiama dalla chat vera (`/message/stream`) gli strumenti sul fascicolo dell'altra azienda e il test controlla il RISULTATO che torna al modello (nessun dato altrui). Resta da fare, in produzione e con account di prova tuoi, la prova con le frasi del Test (apri il fascicolo dell'altra azienda, conosco l'id…): il backend è fatto per rispondere «non trovato» a prescindere da ciò che il modello chiede.

## 6. Limiti, rischi residui e piano

Rischi residui: V1 finché il bucket è pubblico; V5, V6; nessun log di accesso ai documenti; nessun rate limit specifico per tentativi su id; capability URL non revocabili.

**Piano per un vero multi-tenant (per azienda)** — oggi NON presente:
1. Tabelle `organizzazioni` e `membri(org_id, user_id, ruolo)`; `org_id` NOT NULL su fascicoli, documenti, eventi, conversazioni, memoria.
2. Una funzione unica nel backend che risolve «l'azienda attiva» dal JWT + membership (mai da un parametro) e la usa al posto di `user_id` in `_righe`.
3. Ruoli minimi (amministratore, collaboratore, sola lettura) e permessi per fascicolo; auditing degli accessi.
4. Migrazione additiva: `org_id` popolato dall'account esistente (un'organizzazione per account), poi RLS con policy per `org_id` come seconda linea.
5. Storage: percorsi `org/<id>/…` e URL firmati brevi serviti dal backend.
6. Gli stessi test di questo file, parametrizzati su organizzazioni e ruoli.
Fino ad allora: un'azienda = un account, nessuna collaborazione.

## 7. Valutazione per una beta commerciale

**IDONEO CON LIMITAZIONI**, a queste condizioni indispensabili:
1. Rendere privati `kbot-uploads` e `kbot-reports` (dopo il deploy del codice che ri-firma gli URL; rollback con un UPDATE).
2. Deploy dei fix V2–V4 e della suite di isolamento in CI.
3. Verificare che `K2A_8E_API_KEY` non sia il valore predefinito.
4. Un account per azienda, nessuna promessa di collaborazione multiutente né di ruoli.
5. Decidere V5 (colonna `has_paid` scrivibile).

Senza la condizione 1 il giudizio resterebbe **NON IDONEO** per documenti contrattuali reali: un link noto basta, senza login. Con le 5 condizioni il rischio residuo è quello delle capability (V6).
