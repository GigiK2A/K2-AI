# Test 30B — registrare una revisione documentale dalla chat (v2 dello stesso documento)

Data: 11/11/2026. Fascicolo UM-26-041 **non toccato** (solo letture del database di produzione: elenco dei documenti, senza testo).

## 1. Diagnosi (verificata nel codice e nel database)

| Cosa | Stato prima |
|---|---|
| Struttura | `kbot_fascicolo_documenti`: una riga per file con `versione`, `serie`, `sha256`, `stato`, `sostituisce_doc` (migrazione 008). |
| «Documento logico» | **non esisteva**: era la `serie`, una stringa ricavata dal NOME del file con una regex (toglie «v2», «rev», date…). Due revisioni con nomi diversi non si legavano; la stessa regex poteva legare documenti diversi. |
| Come entra una versione | solo come effetto collaterale di `fascicolo_salva(allega_documenti=true)`: prende **tutti** gli allegati della conversazione, non uno scelto per id. Nessun modo di dire «questo allegato è la v2 di quel documento». |
| Metadati | data (`created_at`) e stato sì; **autore, fonte e motivo della revisione no**. |
| Idempotenza | per impronta del testo (`sha256`), ma il v1 di produzione (`KBot_Test_04_Riepilogo_Commessa.pdf`) è stato salvato **prima** della 008: `serie` e `sha256` vuoti, quindi il confronto per contenuto con quel documento non funzionava. |
| Recupero/confronto | `fascicolo_documento` apriva UNA versione (l'ultima); nessun elenco con id/data/autore, nessun confronto fra versioni. |
| Marcatori `[[fonte|…]]` grezzi | tre cause: (a) `verifica()` usciva senza toccare il testo se la conversazione non aveva allegati → il marcatore del modello arrivava all'utente com'era; (b) le forme con 2 campi (`[[fonte|id|pag. 2]]`), o con una `]` nel testo, non venivano riconosciute né dal backend né dal frontend; (c) una citazione a una versione precedente non aperta in quella conversazione veniva scartata. |

Il modello del Test 30B si era fermato «correttamente»: non aveva lo strumento.

## 2. Cosa cambia

**Modello dati** — migrazione `010_fascicolo_documenti_versioni.sql` (+ `010_rollback.sql`), solo additiva e idempotente:
`documento_id` (UUID stabile del documento logico, uguale in tutte le versioni), `motivo`, `autore`, `fonte`; due indici univoci parziali (`documento_id, versione` e `documento_id, sha256`) che bloccano il doppione anche con due richieste in contemporanea. I documenti esistenti **non vengono modificati**: con `documento_id` vuoto il loro documento logico è la radice della catena `sostituisce_doc` (il v1 di produzione resta com'è; la v2 si lega a lui con `documento_id = id del v1`).

**Tre identificativi distinti** (`lib/fascicoli_documenti.py`)
- documento logico → sigla `L-xxxxxxxx` (stabile);
- versione → `id` della riga e `doc:<12 hex>` (id delle citazioni: sha1 del percorso del file, diverso per ogni versione);
- record del fascicolo (importi) → invariati.

**Nuovo strumento `fascicolo_registra_versione`** (allegato, documento, motivo, nuovo_documento): registra un allegato come versione N+1 del documento indicato per sigla/id/nome. Regole:
- richiede la conferma dell'utente (verificata nel codice) e il `motivo`;
- stesso file o stesso contenuto già presente (anche con altro nome o percorso, anche contro il v1 senza impronta salvata) → «GIÀ REGISTRATO», nulla viene scritto;
- se non indichi `documento` e il nome somiglia a un documento esistente → errore AMBIGUO (non si crea un documento indipendente per sbaglio); `nuovo_documento=true` lo permette;
- registra data, autore (`utente`: la conferma è sua), fonte (`chat:<sessione>:<file>`), motivo, stato `caricato`; evento `documento` nello storico;
- **non verifica né approva i contenuti, non tocca i record economici**: l'esito lo dice e rimanda ai due passi separati (`fascicolo_documento imposta_stato`, `fascicolo_aggiorna`), ciascuno con la sua conferma;
- rilegge dal database e restituisce l'elenco di tutte le versioni; due richieste concorrenti → la seconda risponde idempotente.

**Recupero e confronto** (`fascicolo_documento`): mostra sempre TUTTE le versioni (numero, `doc:`, stato, data, autore, fonte, motivo); `versione` = ultima / N / «tutte» (passaggi di ogni versione, ognuno con il suo id); `confronta_con` = elenco delle differenze (righe modificate prima→dopo, righe solo in una, numeri spariti/nuovi), in sola lettura. `fascicolo_apri` raggruppa per documento logico con le versioni e i loro id.

**Citazioni alla versione esatta**: ogni versione ha il suo `doc:`; `collega_citati` rende disponibile alla verifica e al visualizzatore una versione (solo dell'utente) citata per id anche se non è stata aperta in quella conversazione; il visualizzatore mostra «versione 1 di 2 (precedente)» e restituisce `versione`, `versioni_totali`, `ultima`, `documento_logico`, `stato_documento`.

**Marcatori**: `_MARC` accetta 1–3 campi e una `]` nel testo; `toglie_residui` elimina ogni forma non risolta (anche non chiusa), mantenendo solo i marcatori già normalizzati; in `message.py` senza allegati i marcatori si tolgono tutti; il frontend toglie qualunque `[[fonte…]]` residuo.

**Compatibilità col deploy**: il codice funziona anche PRIMA della migrazione (lo strumento risponde `MIGRAZIONE_MANCANTE`, `fascicolo_salva` continua a salvare senza le colonne nuove). `/api/kbot/capabilities` espone `fascicoliDocVersioni`.

## 3. Prove

- `tests/test_fascicoli_documenti_versioni.py` (17 test, database finto): v1→v2 stesso documento logico con tutti i metadati; record non toccati e stato `caricato`; idempotenza (stesso file, stesso contenuto con altro nome, anche come «nuovo documento»); ambiguità; errori senza scritture; isolamento fra utenti; richiesta concorrente (vincolo univoco simulato); migrazione assente; documenti di prima della 010 non modificati; recupero di tutte le versioni; confronto; approvazione ≠ registrazione; aggiornamento record come passo separato; citazioni a v1 e v2 (e una citazione alla v1 NON può puntare al testo della v2); nessun marcatore grezzo (8 forme × 3 stati della conversazione, più il percorso vero di `message.py`); chat con modello finto che registra la v2, confronta e cita entrambe, e in una conversazione nuova risponde idempotente.
- **Mutanti** sul codice nuovo: 8 su 8 uccisi (idempotenza spenta, documento logico nuovo a ogni versione, registrazione che approva, legame con la versione precedente perso, doppione accidentale consentito, conferma saltata, marcatori grezzi non tolti dopo la verifica / senza documenti); il controllo senza modifiche passa tutto.
- **Browser** (`e2e/versioni_documenti.mjs`, Chromium, backend vero con modello finto, fascicolo fittizio `TEST-DOC-VERSIONI-01`, PDF veri): v1 nel fascicolo → allego la v2 dalla chat → registrata come v2 dello stesso documento logico (id diverso, stato `caricato`, autore, fonte, motivo) → record invariati → confronto con tre citazioni (v1, v2, sola pagina; quella a un documento inesistente sparisce) → nessun `[[` nella pagina → la citazione alla v1 apre il PDF v1 («versione 1 di 2 (precedente)») con «8.850,00» evidenziato, quella alla v2 apre il PDF v2 con «9.250,00» evidenziato → stesso allegato in una conversazione nuova: «idempotente», nessuna v3. 15/15 controlli.
- **Migrazione 010** provata su una copia temporanea dei dati di produzione (nessuna modifica a `public`): si applica due volte senza errori, la riga esistente resta intatta, i vincoli rifiutano stesso contenuto e stessa versione nello stesso documento e consentono lo stesso contenuto in un altro documento.

## 4. Cosa NON è provato

- **Haiku 5.5**: da qui non è raggiungibile (nessuna chiave Anthropic). Non è misurato se sceglie `fascicolo_registra_versione` (e con quali argomenti: `allegato`, `documento`, `motivo`) né se legge l'id dell'allegato dal prompt. Il test «anche tramite Haiku 5.5» va fatto in produzione, dopo il deploy e la migrazione.
- Modello locale vero (Qwen): non rieseguito in questa sessione.
- Il PDF vero `KBot_Test_04_Riepilogo_Commessa_v2.pdf`: non è su questa macchina; provata una replica fittizia a una pagina.
- Documenti scansionati (OCR): nessuna geometria per l'evidenziazione; il confronto lavora sul testo estratto e non vede differenze di sola impaginazione.
- La **migrazione 010 non è applicata in produzione** (serve il tuo ok). Fino ad allora lo strumento risponde «MIGRAZIONE_MANCANTE».
- Nessuna interfaccia per elencare/confrontare le versioni fuori dalla chat (l'API `GET /fascicoli/{id}` ora le espone con `documento_logico`, `versione`, `autore`, `motivo`, `fonte`, `doc`).

## 5. Rollback
`010_rollback.sql` toglie colonne e indici nuovi; i documenti e i file restano. Il codice senza le colonne continua a funzionare.
