# Audit 8 — fascicoli: versioni, deduplicazione, documenti nel visualizzatore (10 nov 2026)

## Problemi confermati (sul fascicolo fittizio UM-26-041, in sola lettura)
| Problema | Evidenza | Stato |
|---|---|---|
| Append-only, nessuno stato del record | 31 voci, tutte `non_verificato`, nessun modo di marcare «superata» | **risolto** (codice + migrazione 008, da applicare) |
| Duplicati | 15.250 ×2, 15.650 ×2, acconto 6.400 ×2 (+1 nota), protocollate ×2, «8 incluse» ×2, maturato ×2, residuo 7.890 ×2, anomalia 1.360 ×2 = **8 gruppi** | **risolto per i nuovi salvataggi; i 8 gruppi esistenti si consolidano con conferma** (non toccati) |
| `chiave` sempre nulla | il controllo delle contraddizioni dell'audit 7 non poteva scattare mai | **risolto**: la chiave è ora richiesta dallo strumento e, se manca, il confronto usa numeri + parole |
| Origine sbagliata | voci «CALCOLATO…» con `fonte.origine = documento` | **risolto** per i nuovi record (origine esplicita); il backfill della 008 corregge i vecchi da testo |
| Documento del fascicolo non apribile | il modello vedeva solo `doc f9561058b1fc pag. 1` | **risolto** (due vie: strumento `fascicolo_documento` + visualizzatore che trova il documento anche se non è della conversazione) |

## Cosa cambia
**Modello dati** (migrazione 008, additiva, con `008_rollback.sql`): su ogni record tre assi separati — `stato_record` (attuale · da_verificare · superata · contestata · archiviata), `verifica` (non_verificato · verificato · confermato) e `origine` (letto da documento · dichiarato dall'utente · calcolato · verificato esterno · confermato da autorizzato) — più unità, periodo, contesto, versione del documento, data di efficacia, `valido_dal/fino`, record sostituito/sostituente, motivo, autore, fonti multiple. Tabella `kbot_fascicolo_eventi` (prima/dopo/motivo/attore per ogni modifica). Documenti: versione, serie, hash del contenuto, stato (caricato/verificato/approvato).
**Regole** (`lib/fascicoli_versioni.py`): stesso dato → nessun duplicato (se la fonte è nuova, si aggiunge al record); valore diverso → **proposta** `da_verificare`, mai sovrascrittura; la sostituzione richiede la conferma dell'utente (verificata dal codice sul suo messaggio): il vecchio valore diventa «superata» e resta nello storico; una revisione solo dichiarata resta `da_verificare` e non sostituisce l'ultimo valore documentato. Stesso valore ma periodo/contesto diverso = record distinti. Storico e «cosa era valido alla data X».
**Duplicati esistenti**: rilevatore (stesso tipo, stessi numeri, parole simili; soglia più bassa se il valore è scritto identico) → gruppi con record di riferimento (attuale > confermato > origine > numero di fonti > più vecchio), fonti e differenze; consolidamento = archivia i duplicati unendo le fonti, **non cancella**, scrive un evento con lo stato precedente e si **annulla**.
**Documenti**: nuovo upload nella stessa serie (anche `_v2`, «rev», date nel nome) = versione successiva; stesso contenuto = non duplicato. «Ultima ricevuta / verificata / approvata» mostrate separate, il valore «in uso» è il record attuale. `fascicolo_documento` recupera metadati, versioni e passaggi pertinenti (con pagina se esistono i chunk della sessione di origine) e rende il file citabile/apribile; `collega` non carica più tutti i documenti (prestazioni). Il visualizzatore (`/session/{id}/documents/{doc}/view`) risolve il documento anche fra quelli dei fascicoli dello stesso utente; stesso codice su `/fascicoli/{id}/documents/{doc}/view`.
**Strumenti del modello** (8): cerca, apri (anche `alla_data`), collega, salva, voce (storico · sostituisci · contesta · archivia · conferma · verifica esterna), confronta (sola lettura), duplicati (elenca · consolida), documento. Ogni scrittura è rifiutata dal codice senza conferma dell'utente («NON ESEGUITO»).
**API utente**: storico, duplicati, consolida, annulla consolidamento, apertura documento.

## Test
- Backend: suite completa verde; nuovi: `test_fascicoli_versioni` (10: fasi 1-6 del collaudo, revisione dichiarata, storico a una data, dedup con periodi diversi, consolidamento + rollback, versioni di documento, apertura dal visualizzatore da un'altra conversazione, 410 se il file manca, isolamento tra tenant, **rilevatore sui 31 record reali fittizi** → 8 gruppi attesi, 0 falsi accorpamenti), `test_fascicoli` (9) e `test_fascicoli_chat`.
- Migrazione 008 provata **su copie temporanee** delle tabelle di produzione (sessione SQL, nessuna tabella reale toccata): backfill corretto su 31 record (21 letti da documento, 6 calcolati, 1 dichiarato, 3 «da_verificare»).
- Non rifatti nel browser (frontend invariato): scroll, Markdown, visualizzatore, citazioni — coperti dalle prove dell'audit 7, la suite backend resta verde.

## Non completato / rischi
- **Migrazione 008 non applicata in produzione** (decisione tua): finché non lo è, il codice nuovo non deve andare in linea (le colonne mancano).
- Nessuna interfaccia utente per proposte/storico/consolidamento: solo chat e API.
- L'estrazione dei valori dalla nuova versione del PDF la fa il modello (`fascicolo_confronta` confronta in codice, ma i valori sono quelli che il modello legge): va misurata con Haiku 5.5.
- Il rilevatore dei duplicati è euristico (conservativo: meglio un duplicato non visto che due dati diversi fusi); il consolidamento si propone sempre prima.
- Le pagine dei passaggi di un documento recuperato da un fascicolo richiedono i chunk della sessione di origine (`kbot_file_chunks`, esistenti dal 10/11); per documenti più vecchi i passaggi sono «parti» senza pagina.
- Costi: +8 definizioni di strumento ≈ 1,5–2k token a turno solo per gli utenti loggati; nessuna chiamata LLM aggiuntiva; nessun documento caricato nel contesto a ogni messaggio.
