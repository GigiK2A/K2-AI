# Test 28C — aggiornare un record senza crearne uno nuovo (10 nov 2026)

## Diagnosi (dati letti dal database, sola lettura)
Nel fascicolo `TEST-KBOT-VERSIONI-01` i tre record erano nati tutti da `fascicolo_salva` (eventi `crea`, attore «modello»), mai da un aggiornamento.

| Domanda | Risposta |
|---|---|
| 1. Esiste un endpoint per aggiornare un record per ID? | **No** (era un buco nel backend). Esistevano `PATCH /fascicoli/{id}/voci/{vid}` (testo/valore/verifica, per l'utente, senza storico né revisioni) e `fascicolo_voce «sostituisci»`, che però conferma solo una *proposta* già creata. Nessun modo, per il modello, di «cambia il valore di f2c16476». |
| 2. Strumenti registrati ed esposti? | Sì, 8 strumenti esposti (verificato da `/capabilities` e da test). Il problema non è l'esposizione. |
| 3. Lo schema distingue creazione/proposta/conferma/archiviazione? | Sì per proposta (`salva` con valore diverso), conferma (`voce sostituisci`) e archiviazione (`voce archivia`); **mancava l'aggiornamento in-place**. |
| 4. Perché il modello ha usato `salva`? | Perché era l'unico strumento che potesse scrivere un valore nuovo. E `salva` ha creato due record «attuali» invece di una proposta per due difetti nostri (sotto). |
| 5. Istruzioni su strumenti inesistenti? | Il prompt diceva «Un valore DIVERSO non sovrascrive: diventa proposta», vero solo quando il sistema riconosceva i due record come lo stesso dato — nel 28C non li riconosceva. Nessuno strumento inesistente, ma un comportamento promesso e non garantito. |
| 6. Protezioni da duplicati e concorrenza? | Duplicati: parziali (difetti sotto). Concorrenza: **assente**. |

**Due difetti del backend che hanno prodotto i duplicati**
1. Il primo record non aveva `chiave`, il secondo sì (`budget_intervento_tecnico`): senza chiave su entrambi il sistema richiedeva *stessi numeri* per considerarli lo stesso dato, quindi 10.000 e 12.500 risultavano record diversi → creato un secondo «attuale» invece di una proposta.
2. Il modello scriveva in `contesto` una frase di provenienza diversa a ogni chiamata («Dato fittizio di test…», «Revisione del budget…»): `contesto` faceva parte dell'identità del dato, quindi anche i due 12.500 identici risultavano diversi → terzo record.

## Correzioni (Backend)
- **Nuovo strumento `fascicolo_aggiorna(record, valore, motivo, revisione_attesa)`**: cambia il valore di un record esistente **mantenendone l'ID**; il valore precedente va nello storico (evento `aggiorna` con prima/dopo/motivo/attore); contatore `revisione` (migrazione 009). **Non crea mai record**: errori strutturati `NON_TROVATO`, `NON_MODIFICABILE`, `CONFLITTO`, `MOTIVO_MANCANTE`, `NON_ESEGUITO` (senza conferma dell'utente). **Idempotente**: stesso valore (anche «12.500,00 €» = «12.500 €») → «nessuna modifica». **Concorrenza**: se `revisione_attesa` non coincide → `CONFLITTO` con la revisione corrente.
- **Risposte strutturate** per tutti gli strumenti di scrittura: riga `ESITO: ok|errore <CODICE>`, id a 8 caratteri, e per l'aggiornamento una riga JSON `{"ok":…,"id":…,"revisione":…,"valore":…}`; `salva` elenca gli id creati/proposti.
- **Identità del dato**: `contesto` conta solo se è un'etichetta breve (≤ 40 caratteri) in entrambi; record senza chiave ma con testo simile (parole di chiave+testo ≥ 0,35) sono lo stesso dato → `salva` con valore diverso crea una **proposta** `da_verificare`, mai un secondo «attuale», e dice di usare `fascicolo_aggiorna`.
- **Storico**: `fascicolo_voce «storico»` mostra «VALORI PRECEDENTI DELLO STESSO RECORD»; `fascicolo_apri alla_data` ricostruisce il valore di quella data dagli aggiornamenti; `fascicolo_apri` mostra `revN`.
- Archiviazione non distruttiva dei duplicati: già esistente (`fascicolo_voce archivia`, `fascicolo_duplicati consolida`); ora riconosce anche questi duplicati.
- **Istruzioni del modello** (nel prompt e nella descrizione degli strumenti): «per cambiare un record esistente usa apri → aggiorna, mai salva; se l'aggiornamento fallisce riferisci l'errore, non creare un record come ripiego».

## Selezione dei tool da parte di Haiku
Non verificabile da qui con Haiku reale: i test usano un modello finto che sceglie lo strumento giusto. Quello che ho reso vero è che (a) lo strumento giusto esista ed esca nell'elenco, (b) quello sbagliato (`salva`) non possa più produrre il danno (niente secondo attuale, proposta con istruzione esplicita). Da misurare in produzione dopo il deploy.

## Test superati
`test_fascicoli_aggiorna` (stesso ID, storico 10.000 → 12.500, ripetizione idempotente, errori senza record nuovi, concorrenza, caso 28C ricostruito, archiviazione non distruttiva dei duplicati con un solo «attuale» finale) e `test_fascicoli_chat` (due conversazioni **nuove** attraverso il percorso chat con il modello: un solo record, rev 2, 10.000 nello storico, la seconda richiesta è idempotente). Migrazione 009 provata su copia temporanea dei dati reali (35 record).

## Piano di ripristino di `TEST-KBOT-VERSIONI-01` — NON applicato
Prerequisiti: migrazione 009 applicata e build nuova in linea (`/capabilities` → `build` e `fascicoliSchema: true`). Poi, in una chat con il tuo consenso esplicito a ogni passo:
1. `fascicolo_aggiorna` su `f2c16476`: valore 12.500 €, motivo «ripristino del test 28C», `revisione_attesa` 1 → stesso ID, 10.000 € nello storico.
2. `fascicolo_voce archivia` su `1ba4bc3a`, motivo «duplicato di f2c16476».
3. `fascicolo_voce archivia` su `f1168545`, motivo «duplicato di f2c16476».
4. Verifica: `fascicolo_apri` mostra un solo record attuale (`f2c16476`, rev 2, 12.500 €); `storico` mostra 10.000 → 12.500; gli altri due risultano archiviati (non cancellati) con il motivo.
In alternativa dopo il punto 1 si può usare `fascicolo_duplicati consolida`, che archivia i due duplicati unendone le fonti ed è annullabile.

## Criticità residue
- La scelta degli strumenti di Haiku 5.5 resta da misurare dopo il deploy.
- Il `PATCH` dell'utente sulle voci non incrementa la revisione né scrive eventi `aggiorna`: da allineare (priorità bassa, nessuna UI lo usa).
- Soglia 0,35 per riconoscere lo «stesso dato» senza chiave: euristica; un falso collegamento produce solo una proposta da confermare.
