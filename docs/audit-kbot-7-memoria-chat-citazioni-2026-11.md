# Audit 7 — memoria aziendale, interfaccia chat, citazioni documentali (10 nov 2026)

## 1. Architettura trovata
Frontend Next.js 16 (`kbot/`, basePath `/app`), backend FastAPI (`kbot/backend`), Supabase (sessioni in `kbot_sessions.collected_data`, memoria cross-sessione `kbot_client_memory`).
Documenti: upload → Storage privato → estrazione (pdfplumber / OCR) → `collected_data.uploaded_files` + chunk (`kbot_file_chunks`, creata il 10/11).
Nessun concetto di «azienda» separato dall'utente: **tenant = `user_id`** (un account = un'azienda). Nessun MCP di memoria preesistente da riusare.

## 2. Problemi e cause (verificati)
| Problema | Causa |
|---|---|
| Scroll che «combatte» durante lo streaming | `scrollIntoView({behavior:"smooth"})` a ogni token (`page.tsx`) |
| Grassetti/tabelle assenti | (a) il frontend renderizzava solo testo (`whitespace-pre-wrap`, nessun parser Markdown); (b) `normalize_assistant_reply` toglieva `**`, `#`, tabelle, codice; (c) il prompt vietava il Markdown |
| Citazioni non cliccabili | `(pag. N)` era solo un chip grafico; nessun id documento, nessuna geometria |
| Nuova chat senza commessa/documento | nessun archivio oltre alla sessione: profilo testuale generato, niente fascicoli |
| Il server moriva dopo il visualizzatore (solo in prova) | `pdfplumber.to_image` → crash pdfium «double free» (lezione globale scritta) |

## 3. Modifiche
**Scroll** — `lib/useAutoScroll.ts`: stato esplicito (segue / sospeso), ancoraggio con `ResizeObserver` e `scrollTop` diretto (niente animazioni per token), sospensione immediata su rotella/tocco/tastiera/barra, ripresa a <64 px dal fondo o col pulsante «Vai alla risposta in corso». Ref a callback (il contenitore compare dopo la schermata di caricamento: il primo tentativo con `useRef` non agganciava nulla).
**Markdown** — `react-markdown` + `remark-gfm` (+2 dipendenze, motivate: parser consolidato, HTML grezzo non interpretato). Blocchi memoizzati (solo l'ultimo si rifà a ogni token), tabelle scorribili, marcatori parziali nascosti in streaming. Backend: `normalize_assistant_reply` non toglie più il Markdown (restano fuori solo i blocchi ```json); il prompt ora lo consente «con misura».
**Citazioni** — `lib/fonti_documenti.py`: il modello scrive `[[fonte|id|pag|testo copiato]]`; il backend risolve il documento, **verifica il testo sulla pagina vera** (stato `ok`), degrada a «solo pagina» o toglie il marcatore; `(pag. N)` scritto a mano diventa citazione solo se un importo della frase è alla lettera in quella pagina. Geometria (`localizza`) dalle parole reali del PDF, mai inventata; resa pagina con pypdfium2 sotto lucchetto. Endpoint `GET /session/{id}/documents/{doc}/view` (autorizzazione sessione→utente, id ≠ percorso, `Cache-Control: no-store`, nessun link pubblico, 410 se il file non c'è). `VisualizzatoreDocumento`: pannello laterale (schermo intero su telefono), zoom, pagine, citazione precedente/successiva, «Chat» per tornare.
**Memoria aziendale** — migrazione 007: `kbot_fascicoli`, `kbot_fascicolo_voci` (fonte, data, stato di verifica, chiave per le contraddizioni), `kbot_fascicolo_documenti`. Strumenti per il modello `fascicolo_cerca/apri/collega/salva` (`lib/fascicoli.py`). **Scrittura solo con conferma dell'utente verificata dal codice sul suo messaggio** (un documento che dice «salva» non scrive). `collega` rende disponibili in una nuova chat testo, citazioni e visualizzatore dei documenti del fascicolo senza ricaricarli. Correzione/cancellazione solo dall'utente (`/api/kbot/fascicoli…`). Nel prompt entra un sommario limitato, non l'archivio.

## 4. File principali
Backend: `lib/fonti_documenti.py`, `lib/fascicoli.py`, `lib/analisi_documenti.py`, `lib/strumenti.py`, `lib/prompts.py`, `lib/rag.py`, `api/message.py`, `api/upload.py`, `api/fascicoli_api.py`, `main.py`. Frontend: `lib/useAutoScroll.ts`, `lib/citazioni.ts`, `lib/files.ts`, `components/chat/{Markdown,VisualizzatoreDocumento,MessageBubble,Composer}.tsx`, `app/page.tsx`. Migrazioni 006 (applicata il 10/11), 007.

## 5. Test
Backend: 1090+ passati (nuovi: `test_fonti_documenti` 6, `test_fascicoli` 9 + `test_fascicoli_chat` 1, `test_documenti_pratica` 4). Browser (Chromium reale, modello finto deterministico): `scroll_streaming.mjs` 8/8, `citazioni_documenti.mjs` 8/8 (grassetto, tabella, citazione → pagina 1 con la cella «5.040,00» evidenziata → ritorno alla chat), `trascina_file.mjs` 9/9; suite esistenti `documento`, `pratica`, `titoli`, `report_non_richiesto`, `ricerca_web` senza fallimenti.
Isolamento: un utente B non trova, non apre, non collega, non corregge e non cancella fascicoli di A (per id e per codice); stesso codice = fascicolo distinto.

## 6. Non provato / aperto
- **Touch** (scroll su telefono): logica implementata (`touchmove`), non provata su dispositivo.
- **Documenti scansionati**: l'evidenziazione richiede testo PDF; per le scansioni OCR resta «solo pagina» (non c'è geometria dall'OCR). **Word/Excel**: citazione sul testo estratto (nessuna pagina).
- **Haiku 5.5 in produzione**: l'uso dei marcatori `[[fonte|…]]` e dei tool `fascicolo_*` è provato con modelli finti/Qwen; con Haiku va misurato dopo il deploy (se non emette marcatori, resta il collegamento automatico di `(pag. N)`).
- Nessuna interfaccia dedicata ai fascicoli (elenco/modifica): solo API; le proposte di salvataggio passano dalla chat.
- Memoria di livello 1 (profilo con provenienza) e 3 (decisioni) restano quelle dell'audit 5; i fascicoli coprono livelli 2 e 4.
- Costi: +2 dipendenze frontend (~45 kB gz), nessuna chiamata LLM aggiuntiva; le pagine PDF si rendono a richiesta (1–2 s), i byte del file sono in cache (6 file).
