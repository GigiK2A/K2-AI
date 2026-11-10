# Test 26 — diagnosi: «il modello vede solo 4 strumenti» (10 nov 2026)

## Causa
**Il Test 26 ha girato sulla build vecchia.** Cronologia (Railway, UTC): il commit 3117fcc (4 strumenti `fascicolo_*`) è andato in linea alle 14:10; il commit 825adbd (8 strumenti, versioni, duplicati, documenti) è partito alle 14:45 e ha finito alle 14:52 (`uptime_s` 23). Il modello ne vedeva 4 perché in produzione c'erano ancora 4. Nessun riavvio o configurazione mancante: era solo il deploy in corso. La migrazione 008 era già applicata prima del deploy.
Per non ripeterlo: `GET /api/kbot/capabilities` ora riporta `build` (SHA del commit in esecuzione), `fascicoliTools` (gli strumenti che il modello vedrà) e `fascicoliSchema` (true se la migrazione 008 è applicata).

## Troncamento di `fascicolo_apri` (confermato, corretto)
La versione 3117fcc mostrava solo gli ultimi 30 record e tagliava a 6000 caratteri a metà riga, senza dirlo: con i 31 record di UM-26-041 ne perdeva almeno uno. Ora l'output è paginato e dichiara sempre `[PARZIALE: mostrati i record N–M di T … richiama con da=M]` oppure `[COMPLETO …]`, con filtri `tipo`/`cerca_testo`; ogni pagina ≤ 12.000 caratteri.

## Tabella funzionalità
Legenda: ✅ sì · ⚠️ parziale · ❌ no. «Prod» = in linea dopo il deploy delle 14:52 (SHA 825adbd); la correzione di questa sessione non è ancora pubblicata.

| Funzionalità | Codice | Backend | Tool al modello | Frontend | Verificata e2e | Note |
|---|---|---|---|---|---|---|
| Record con ID univoco | ✅ | ✅ `GET /fascicoli/{id}` | ✅ `fascicolo_apri` (id a 8 caratteri in ogni riga) | — (solo chat) | ✅ test su 230 record | prima del 825adbd gli ID non c'erano |
| Fascicolo grande, recupero completo | ✅ (**corretto oggi**) | ✅ | ✅ `fascicolo_apri` con `da`, `tipo`, `cerca_testo` | — | ✅ 230 record in 6 pagine, browser: «PARZIALE» al modello | era la causa del troncamento |
| Aggiornamento controllato | ✅ | ✅ (`/fascicoli/{id}/voci/{vid}`) | ✅ `fascicolo_voce` (sostituisci/contesta/archivia/conferma/verifica esterna), solo con conferma dell'utente | ❌ nessuna UI | ✅ test (rifiuta senza conferma, esegue con conferma) | |
| Storico e valore a una data | ✅ | ✅ `/fascicoli/{id}/storico` | ✅ `fascicolo_voce` «storico», `fascicolo_apri` `alla_data` | ❌ | ✅ test | |
| Stati attuale / da verificare / superata / contestata / archiviata | ✅ | ✅ (migrazione 008 applicata) | ✅ (mostrati in ogni riga) | ❌ | ✅ test | stato ≠ verifica ≠ origine |
| Deduplicazione al salvataggio | ✅ | — | ✅ `fascicolo_salva` | — | ✅ test (5+5 voci → 5; altra fonte aggiunta; periodo diverso = record distinto) | |
| Consolidamento duplicati | ✅ | ✅ `/fascicoli/{id}/duplicati`, `/consolida`, `/eventi/{id}/annulla` | ✅ `fascicolo_duplicati` (consolida solo con conferma) | ❌ | ✅ test su 31 record reali fittizi → 8 gruppi attesi, 0 falsi accorpamenti, rollback | UM-26-041 non toccata |
| Aprire il PDF dal fascicolo (modello) | ✅ | ✅ | ✅ `fascicolo_documento` | — | ✅ chat vera con modello finto | passaggi con pagina |
| Aprire il PDF dal fascicolo (utente) | ✅ | ✅ `/session/{id}/documents/{doc}/view` (anche per documenti dei fascicoli dello stesso utente) e `/fascicoli/{id}/documents/{doc}/view` | — | ✅ stesso visualizzatore delle chat | ✅ browser: citazione → PDF alla **pagina 2** con la riga evidenziata → ritorno alla chat | |
| Citazioni persistenti cliccabili | ✅ (**corretto oggi**) | ✅ verifica pagina+testo | ✅ marcatori `[[fonte\|…]]` | ✅ chip cliccabile | ✅ browser | difetto trovato: senza chunk della sessione d'origine la pagina non si ricavava; ora si legge dal PDF originale |
| Autorizzazioni tra aziende | ✅ | ✅ | ✅ | — | ✅ test (404/403 su fascicoli, record, documenti e viewer altrui) | |
| 8e solo su richiesta | ✅ | ✅ `/deliverables/auto` rifiuta (409) l'avvio automatico | — | ✅ niente auto-avvio | ✅ test | richiesta separata dell'utente |

## Ancora aperto
- Nessuna interfaccia utente per proposte, storico e consolidamento (solo chat/API).
- L'estrazione dei valori da una nuova versione del PDF resta del modello (Haiku 5.5): da misurare in produzione dopo questo deploy.
- Il modello finto prova strumenti, marcatori e interfaccia, non la scelta degli strumenti di Haiku: serve un test reale su UM-26-041 dopo il deploy (in sola lettura: `fascicolo_apri`, storico, `fascicolo_documento`, citazione).

## Test 27D — «Evidenziazione esatta non disponibile» sul residuo di 8.850 € (corretto)
**Causa (riprodotta con il marcatore reale salvato nella sessione di collaudo):** la citazione era `[[fonte|f9561058b1fc|1|Residuo da incassare riportato nel documento: € 8.850,00|ok]]`. Nel PDF la riga finisce con un punto («€ 8.850,00.»). La verifica della citazione confrontava stringhe (sottostringa) e diceva «ok»; il visualizzatore confrontava parola per parola e vedeva «8.850,00.» ≠ «8.850,00»: nessun riquadro. Due controlli diversi sulla stessa cosa. Non mancavano coordinate né collegamenti: il testo estratto e il PDF erano agganciati correttamente (pagina 1 giusta).
**Correzione (un solo sistema, quello già usato per i PDF della chat):** verifica ed evidenziazione ora usano lo stesso confronto a token (`contiene` / `trova_in_parole`, punteggiatura ai bordi ignorata, «€» = euro, parole del PDF che valgono più token); ciò che la verifica accetta, il visualizzatore lo evidenzia — proprietà coperta da test. Inoltre i riquadri ora vengono dalla geometria di pdfium (il motore che disegna la pagina) e non da pdfplumber: con font senza metriche per «€» i riquadri risultavano sfasati di 5-8 pt (visto nella replica del documento); il ripiego su pdfplumber resta per i casi in cui pdfium non trova il testo.
**Verifica:** replica fittizia di `KBot_Test_04_Riepilogo_Commessa.pdf` (stesse righe, «€», punti finali, frasi su due righe; l'originale non è accessibile da qui): 6 passaggi (residuo, acconto, clausola su due righe, «in attesa di protocollo» a cavallo di righe…) verificati ed evidenziati; e2e nel browser partendo dal fascicolo (DEMO-001, finto): citazione → PDF alla pagina 1 → riga «Residuo … € 8.850,00.» evidenziata con il riquadro allineato al testo. Dati del fascicolo reale non toccati.
**Da rifare tu in produzione dopo il deploy:** stessa domanda sul residuo e clic sulla citazione sul PDF originale (la replica prova il meccanismo, non il tuo file).
