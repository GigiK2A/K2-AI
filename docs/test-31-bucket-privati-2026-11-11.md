# Test 31 — bucket `kbot-reports` e `kbot-uploads` resi privati (11/11/2026)

Autorizzazione: «uno alla volta, secondo il piano». Nessun rollback eseguito. `ig-media`, `instagram-slides`, `robot` non toccati.

## Cronologia (UTC)
- 15:47 `kbot-reports` → privato. 15:49 `kbot-uploads` → privato (SQL su `storage.buckets`; rollback: `update storage.buckets set public = true where id = '…'`).

## `kbot-reports`
| Controllo | Esito |
|---|---|
| Link pubblico diretto di un file nuovo | 400 |
| URL firmato | 200, contenuto identico |
| Vecchio link in formato pubblico salvato in sessione | ri-firmato da `/status` e `/session`; download = PDF originale (158.817 byte) |
| Report fittizio nuovo (Haiku, 33 s) salvato con `/deliverables/save` | link firmato 200 (156.942 byte); link pubblico 400 |
| Sessione con proprietario, senza token: status, session, documents, generate-pdf, save, recover, report | 403 su tutte, nessun link/dato |
| Elenco con chiave anon | 0 voci |
| Manifest (140 oggetti, 16.816.339 byte, impronta `ea2b12cc…`) | identico a prima |

## `kbot-uploads`
| Controllo | Esito |
|---|---|
| Upload fittizio con `/upload` vero | `publicUrl` firmato; download identico; link pubblico 400 |
| Visualizzatore + citazione evidenziata | ok (backend con chiave di servizio) |
| Funzioni del visualizzatore di fascicoli/versioni/citazioni contro lo Storage vero privato (in-process) | byte identici, testo per pagina, pagina resa con riquadro, «versione 2 di 2» |
| Sessione con proprietario, senza token: documents, view, upload, context/remove, message | 403 su tutte |
| Elenco con chiave anon | 0 voci |
| Manifest (65 oggetti, 160.378.508 byte, impronta `2ea4a43f…`) | identico a prima |

## Cache di rete (osservata)
Cloudflare `HIT`, `cache-control: public, max-age=3600`: due file fittizi già in cache restavano scaricabili dal link pubblico subito dopo la privatizzazione (200). Dopo la loro cancellazione i 4 URL sorvegliati rispondono 400. **La scadenza naturale per file esistenti non è stata verificata** (nessun file in cache da provare). Per un file reale scaricato pubblicamente prima del cambio (dopo le 14:47 UTC) il link può servire fino alle 16:47 UTC; dopo non c'è più nulla in cache per costruzione.

## Non verificabile da qui
- Account autenticato vero (dashboard, fascicolo con PDF e citazioni, upload): serve un login; provato lo stesso percorso di codice con la chiave di servizio e i test (54).
- Workflow n8n o altre integrazioni esterne che usino link pubblici dei due bucket (ricerca suggerita: `select name from workflow_entity where nodes::text like '%storage/v1/object/public%';` sul database di n8n).

## Pulizia
Cancellati solo oggetti fittizi creati dai test (id verificati) e 6 sessioni di prova; originali intatti (impronte identiche).
