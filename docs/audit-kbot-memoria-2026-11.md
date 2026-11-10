# Audit K-BOT del 10/11/2026 — memoria, troncamenti, calcoli, conflitti sul lavoro

Collaudo: 3 scenari (A conflitto interno, B assunzioni, C idea da 100.000 €), modello in produzione Claude Haiku 5.5 (`ANTHROPIC_MODEL=claude-haiku-5-5`).

## Mappa dell'architettura (verificata nel codice)
- **Frontend**: Next.js in `kai-website/kbot/` (basePath `/app`). **Backend**: FastAPI in `kai-website/kbot/backend/app` (`api/message.py` = turno di chat, streaming SSE).
- **Modello**: Anthropic SDK; `settings.py` → `ANTHROPIC_MODEL`, chiave `ANTHROPIC_API_KEY` (devono essere legate a un workspace). Tutte le chiamate ausiliarie (scheda, titoli, temi, norme) usano lo stesso modello.
- **Prompt di sistema**: `lib/prompts.py::build_system_prompt_v2` (skill da `kai-website/lib/skills/*/SKILL.md` scelte da `lib/skill_router.py` + `data/skill_temi.json`; blocchi: profilo/memoria, scheda del cliente, calcoli, norme).
- **Memoria**: due livelli. (1) **scheda del cliente** per conversazione (`lib/scheda_cliente.py`): fatti detti dall'utente, ognuno con citazione verificata in codice. (2) **profilo cross-conversazione** (`lib/profile.py`, tabella `kbot_client_memory`, UNA riga per `user_id`).
- **Isolamento**: il recupero è per `user_id` del proprietario della sessione (`_check_ownership` → 403 se l'utente non è il proprietario; test `test_message_on_other_users_session_403`). Non esiste un'architettura multi-tenant né un identificativo aziendale: tenant = utente = account.
- **RAG/vettori**: nessuno per la memoria. Il recupero normativo usa il corpus Normattiva (SQLite FTS) e `norme_ue/`.
- **Streaming/retry**: SSE con eventi `fase`/`timing`; la guardia `taglio_guard` può chiedere UNA continuazione.

## Criticità → causa → evidenza → esito
| Criticità | Causa | Evidenza | Esito |
|---|---|---|---|
| B: memoria con fatti mai detti e scheda con 7,5 mln, DemoTech, data breach, P.IVA cessata | UNA riga per account accumula TUTTE le conversazioni (anche di prova) con «l'ultimo vince», senza provenienza, iniettata come verità («USALA, non richiedere MAI»); in più `contesto.problemi` era un RIASSUNTO scritto dal modello | Riga reale in `kbot_client_memory` (1 utente): anagrafica DemoTech/7.500.000, 25 fatti, 10 problemi; contiene breach e P.IVA cessata | **Confermata.** Non è un'esposizione fra utenti (una sola riga, recupero per `user_id`): è contaminazione fra conversazioni dello STESSO account |
| C: testo sul «presunto troncamento» in coda | `taglio_guard` scambiava per interrotta una risposta completa senza punto finale, chiedeva una continuazione, il modello rispondeva con un commento meta che veniva appeso | Messaggio reale (sessione `ff4f57be`): «Se nella tua visualizzazione manca qualcosa, dimmi l'ultima frase che vedi…» dopo l'analisi | **Confermata e corretta** (usa `stop_reason`; scarta le risposte meta) |
| B: calcoli (12 mensilità non dichiarate, costo 55.000 €, margine 35% come dati) | il modello scrive cifre di sua iniziativa; nessun metodo imposto né calcolo verificato | risposte del collaudo; 1.000×99×12 scritto 118.800/990.000 invece di 1.188.000 anche nel replay locale | **Confermata.** Mitigata (blocco di metodo + cifre calcolate dal codice + controllo aritmetico); efficacia su Haiku 5.5 NON misurata |
| A: fatti riferiti trattati come accertati; procedura disciplinare semplificata; tutele immediate poco sviluppate; esclusione dei colleghi | skill lavoro senza sezione sul conflitto; art. 2087 c.c. non nel pacchetto normativo | replay locale: senza la sezione nessuna citazione di art. 7 / 2087 | **Parzialmente corretta** (skill + voce di mappa + pacchetto normativo); in 1 replay su 2 il modello cita art. 7 e 2087 |
| C: nessun piano di validazione; economia superficiale | nessuna istruzione specifica per idee/investimenti nuovi | replay locale | **Blocco aggiunto, effetto NON dimostrato** su Qwen locale |
| «Domande ripetitive», «acquiescenza» | non riproducibili con un controllo oggettivo | — | **Non confermate**: nessuna modifica speculativa |

## Modifiche (file)
- `lib/profile.py`, `api/profile.py`, `lib/prompts.py`, `api/deliverables.py`, `api/message.py`: memoria con provenienza, dati confermati vs appresi, conversazione in corso prevale, riassunti del modello esclusi, API `GET/DELETE /profile/memoria`, conteggi (non valori) nel `done` come `memoria`, blocco «da dove l'hai preso» con fatti verificabili.
- `lib/taglio_guard.py` (+ `api/message.py`): `stop_reason`.
- `lib/calcoli.py`: blocco di metodo, validazione idee, cifre calcolate, controllo `a × b = c`.
- `data/skill_temi.json`, `data/mappa_temi.json`, `lib/skills/diritto-del-lavoro-italiano/SKILL.md`: conflitti/vessazioni.
- Test: `test_memoria_provenienza.py`, `test_taglio_stop_reason.py`, `test_calcoli_economici.py` (+4 file aggiornati).

## Non implementato
- Interfaccia per vedere/correggere la memoria (esistono solo le API); azione «segnala memoria errata» nel frontend.
- Motore deterministico netto→costo azienda (dipende da CCNL/contributi: serve il consulente del lavoro).
- Togliere `temperature` dalle chiamate ausiliarie (Haiku 5.5 risponde 400 e il codice ripiega).
