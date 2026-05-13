# Integrazione Piattaforma SaaS — BuildBoost

## Tool custom disponibili in modalita piattaforma

### `verifica_prg(comune, foglio, particella)`
Restituisce zona PRG/PGT, destinazione d'uso, indici urbanistici, vincoli sovraordinati.

### `verifica_catasto(foglio, particella, sub)`
Restituisce planimetria catastale, consistenza, categoria, rendita, conformita.

### `calcola_oneri(comune, tipo_intervento, superficie, destinazione)`
Restituisce contributo di costruzione (oneri urbanizzazione + costo costruzione).

### `prezzario_regionale(regione, voce)`
Accesso al prezzario regionale per CME parametrico.

### `suap_submit(comune, tipo_pratica, allegati)`
Invio telematico pratica edilizia al SUAP.

## Degradazione in modalita consulenziale
- PRG: WebSearch per NTA comunali o indicazione utente.
- Catasto: dati forniti dall'utente.
- Oneri: tabelle comunali o stima parametrica.
- Invio: checklist documenti preparata, invio manuale dall'utente.
