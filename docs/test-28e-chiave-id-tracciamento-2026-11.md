# Test 28E — chiave e ID esposti, aggiornamento deterministico, dichiarazioni verificate (10 nov 2026)

## Le affermazioni del modello, verificate nel codice
| Affermazione di K-Bot | Verdetto | Evidenza |
|---|---|---|
| `fascicolo_salva` usa una chiave stabile e non consente di indicare l'ID | **Vera** | `salva` crea/propone; non ha un parametro `record`. Nessun errore: era lo strumento sbagliato per modificare. |
| `fascicolo_apri` non restituisce la chiave | **Vera** | `riga()` stampava id, rev, testo, valore, stato, verifica, origine, fonti ma **non `chiave`**, e mostrava il record collegato solo per le proposte. |
| Lo storico non restituisce la chiave | **Vera** | stessa funzione `riga()`. |
| `sostituisci` opera su una proposta già creata | **Vera** | `V.azione("sostituisci")` richiede `stato=da_verificare` + `sostituisce`. |
| Senza la chiave non si può collegare con certezza | **Vera in parte** | l'aggiornamento per ID (`fascicolo_aggiorna`, build e4ef610) non ha bisogno della chiave; ma la chiave doveva comunque essere visibile e usabile. |
| Il modello ha dichiarato di aver consultato il database senza chiamare gli strumenti | **Plausibile e non tracciato** | non esisteva alcuna traccia degli strumenti chiamati nel turno per le operazioni sui fascicoli (esisteva solo per `cerca_norma`). |
Nota: il Test 28E potrebbe aver girato sulla build precedente: `fascicolo_aggiorna` è in linea dalle 16:16 UTC (build e4ef610).

## Correzioni
**Esposizione (backend)** — ogni riga di `fascicolo_apri` e dello storico ora è `id=… chiave=… rev=… [tipo] testo = valore | stato=… verifica=… origine=… fonti=… | sostituisce/sostituito da <id>`; senza chiave scrive `chiave=(nessuna)`.
**Aggiornamento deterministico** — `fascicolo_aggiorna` (per ID, stesso record, storico dei valori, revisione, idempotente, errori strutturati `NON_TROVATO/NON_MODIFICABILE/CONFLITTO/AMBIGUO/MOTIVO_MANCANTE/NON_ESEGUITO`) accetta ora anche la **chiave esatta**: corrispondenza esatta tra i record attivi, mai approssimata; se più record la hanno → `AMBIGUO` con gli id. Nessun ripiego che crei record. La procedura via proposta resta deterministica: `salva` restituisce l'id della proposta e quello del record collegato; `apri` mostra il legame; `sostituisci` conferma.
**Affidabilità delle dichiarazioni** — ogni chiamata a uno strumento `fascicolo_*` è tracciata nel turno (nome, scrittura sì/no, esito); a fine turno, se il testo dice «ho salvato/aggiornato/archiviato/sostituito… (fascicolo/record/dato/importo)» senza una scrittura riuscita, o «ho consultato il fascicolo» senza nessuna chiamata, il sistema **aggiunge una «Nota del sistema»** con l'esito tecnico (es. «ESITO: errore NON_TROVATO»). Non riscrive il testo, lo affianca col fatto. Le istruzioni del modello distinguono fatto (strumento X ha risposto), deduzione e operazione non eseguita.

## File
`app/lib/fascicoli_versioni.py` (riga completa, `trova_per_chiave`, `aggiorna` per chiave), `app/lib/fascicoli.py` (traccia, `verifica_dichiarazioni`, schema/descrizioni, hint), `app/api/message.py` (controllo a fine turno), test `test_fascicoli_chiave_id.py` (+ casi in `test_fascicoli_chat.py`), `evals/server_ui.py` (fascicolo di prova), nessuna migrazione nuova.

## Test
- Backend: id/chiave/rev/legami esposti in apri e storico; aggiornamento per chiave esatta (chiave quasi giusta rifiutata, ambiguità rifiutata); ciclo di 8 passi su fascicolo isolato (crea, id e chiave, aggiorna, verifica, storico 10.000, nessun duplicato, idempotenza, nuova conversazione); dichiarazioni (scrittura fallita, nessuno strumento, lettura ≠ scrittura, frasi non pertinenti o al passato non scattano).
- Chat con modello finto a più giri (apri → legge id e chiave → aggiorna → risponde): due conversazioni nuove, un record, rev 2; e il caso di fallimento: id sbagliato → nessun record creato e nota del sistema alla frase «Ho aggiornato».
- **Modello vero (Qwen locale via LiteLLM, stessa chat e stessi strumenti; Haiku 5.5 non è raggiungibile da qui)**: due conversazioni nuove con la stessa richiesta su un fascicolo fittizio isolato con 10.000 €. Conv. 1: il modello ha aggiornato lo STESSO record (id d563fd59, rev 1→2, 12.500). Conv. 2: ha riconosciuto l'idempotenza, nessun duplicato, e ha riportato il valore precedente 10.000 € dallo storico. Stato finale: un solo record.
- Fascicolo TEST-KBOT-VERSIONI-01: **non modificato** (solo letto il 10/11 per la diagnosi precedente).

## Limiti residui
- **Test con Haiku 5.5 non eseguito** (nessuna chiave Anthropic in questo ambiente): da fare in produzione sul fascicolo isolato, dopo il deploy.
- Il controllo delle dichiarazioni è a pattern: non intercetta ogni formulazione («ho provveduto a…»); segnala per eccesso solo se compaiono verbo di modifica + oggetto del fascicolo senza scrittura riuscita.
- Il `PATCH` utente sui record non incrementa `revisione` né scrive eventi `aggiorna` (priorità bassa, nessuna UI lo usa).
- Il ripristino di TEST-KBOT-VERSIONI-01 (aggiornare f2c16476; archiviare 1ba4bc3a e f1168545) resta in attesa della tua autorizzazione.
