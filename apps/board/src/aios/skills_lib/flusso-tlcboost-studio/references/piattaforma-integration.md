# Integrazione Piattaforma SaaS — TLCBoost

## Tool custom in modalita piattaforma

### `database_siti(operatore, codice_sito)`
Restituisce anagrafica sito, coordinate, configurazione, stato, storia interventi.

### `verifica_vincoli_geo(lat, lon, raggio_m)`
Interroga SIT regionale: vincoli paesaggistici, PAI, Natura 2000, ENAC, demanio.

### `template_pe(operatore, tipo_sito, tipo_intervento)`
Restituisce matrice elaborati richiesti con template pre-compilati.

### `suap_tracker(comune, protocollo)`
Stato pratica SUAP: depositata, in istruttoria, integrazione richiesta, autorizzata.

### `scheda_radio_parser(pdf_file)`
Estrazione automatica configurazione radio da PDF scheda radio operatore.

### `gantt_generator(fasi, durate, vincoli)`
Genera cronoprogramma Gantt con dipendenze e percorso critico.

## Degradazione in modalita consulenziale
- Siti: dati forniti dall'utente o da TSSR/scheda radio.
- Vincoli: WebSearch su SIT regionale o indicazione utente.
- Template PE: matrice da skill iliad/Cellnex.
- SUAP: tracking manuale dall'utente.
- Scheda radio: parsing con `tssr-b40-filler:scheda-radio-reader`.
- Gantt: timeline testuale o XLSX.
