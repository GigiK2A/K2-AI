# Integrazione Piattaforma SaaS — MEPBoost

## Tool custom in modalita piattaforma

### `simulazione_energetica(edificio, impianti, clima)`
Calcolo EPgl,nren secondo UNI TS 11300 parti 1-4.

### `database_componenti(tipo, potenza, brand)`
Schede tecniche e prezzi componenti (caldaie, PdC, FV, LED).

### `calcola_incentivi(intervento, zona_climatica, destinazione)`
Importo Conto Termico 3.0, TEE, Ecobonus con verifica requisiti.

### `bollette_parser(file_pdf)`
Estrazione dati consumi da bollette Enel/Eni/A2A/etc.

## Degradazione in modalita consulenziale
- Simulazione: stime parametriche da UNI TS 11300 semplificato.
- Componenti: specifiche generiche, costi da benchmark.
- Incentivi: calcolo manuale da normativa vigente.
- Bollette: dati inseriti manualmente dall'utente.
