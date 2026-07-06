# Integrazione Piattaforma SaaS — StructBoost

## Tool custom disponibili in modalita piattaforma

Quando la skill gira nel backend K2-AI con Agent SDK, i seguenti tool sono disponibili:

### `analizza_parametri_sismici(lat, lon)`
Restituisce ag, F0, TC*, categoria sottosuolo presunta, zona sismica dal database INGV/NTC 2018.

### `calcola_spettro_risposta(ag, F0, TC_star, sottosuolo, topografia, VN, CU, stato_limite)`
Restituisce lo spettro di risposta elastico e di progetto per lo stato limite richiesto.

### `database_materiali(tipo, anno_costruzione)`
Restituisce proprieta meccaniche dei materiali in funzione dell'epoca costruttiva (fcm, fym, Ecm).

### `catalogo_interventi(tipologia_struttura, intervento)`
Restituisce scheda intervento con costo parametrico EUR/mq, durata, invasivita, incremento IS-V tipico.

### `prezzario_regionale(regione, voce)`
Accesso al prezzario regionale per voci di computo metrico.

### `save_to_tenant_storage(files)`
Salva i deliverable nello storage del tenant per accesso da dashboard.

### `update_job_progress(percent, status)`
Aggiorna la barra di progresso visibile al cliente sulla piattaforma.

## Degradazione in modalita consulenziale

In assenza di tool custom:
- Parametri sismici: tabelle NTC 2018 Allegato B (approssimazione al comune).
- Materiali: valori da Circolare 2019 Tab. C8.5.I per c.a. e Tab. C8.5.II per muratura.
- Costi: benchmark da `references/benchmark-strutturali-italia.md` e prezzario DEI.
- Output: file salvati in `/sessions/.../mnt/outputs/` con link computer://.
