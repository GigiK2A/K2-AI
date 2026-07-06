# Combinazioni di Carico e Contenuti Minimi — CNP_TS21_002 §4

## Condizioni di Carico

### Condizione C1
Carichi installati **alla data della verifica** (concentrati e distribuiti), valutati in conformità alla norma tecnica vigente e al form di redazione Cellnex allegato alla specifica CNP_TS21_002.

### Condizione C2
Carichi di **futura installazione** riguardanti le nuove antenne o la modifica delle esistenti (concentrati e distribuiti), valutati in conformità alla norma tecnica vigente e al form Cellnex.

## Combinazioni di Carico Obbligatorie

| Combinazione | Condizione | Note |
|---|---|---|
| SLU Iniziale | C1 | Stato attuale |
| SLU Nuova/modifica antenne | C1 + C2 | Con le nuove antenne |
| Sismica SLU | E | Azione sismica |
| SLE | C1 | **Vento costante** (specifica Cellnex) |
| SLE | C1 + C2 | **Vento costante** (specifica Cellnex) |

Le SLE si riferiscono a **vento costante** (non a raffica) come da specifica tecnica Cellnex.

## Velocità del Vento e Periodo di Ritorno

La velocità di riferimento è calcolata con periodo di ritorno **TR = 100 anni**:
- vr(TR) = vr(TR=100) = αr × Vb(Tb=50) = αr × Vb(Tb)
- Amplificata attraverso il relativo coefficiente di ritorno

## Contenuti Minimi della Verifica Statica (§4.3)

La relazione di calcolo deve contenere obbligatoriamente:

### Dati strutturali
- Tutti i dimensionali degli elementi strutturali:
  - Per i pali: diametri, lunghezze, spessori dei tronchi; diametri e spessori flange; dimensione costolature rinforzo flange; numero/diametri/classe bulloni; numero/diametri/classe tirafondi
  - Per i tralicci: geometria (lunghezza, spessore, tipologia) profili per montanti, diagonali, rompi-tratta e travesi; numero/diametri/classe bulloni e tirafondi
- Caratteristiche fisico-meccaniche dei materiali di tutti gli elementi strutturali

### Dati di carico
- Carichi C1 (esistenti) — concentrati e distribuiti
- Carichi C2 (futuri) — concentrati e distribuiti
- Coefficiente di topografia adottato con evidenza
- Coefficiente dinamico CsCd: procedimento 1, Annex B EN1991-1-4:2005

### Verifiche strutturali
- Verifiche SLU per C1 e C1+C2 con **percentuale di sfruttamento** di tutti gli elementi
- Indicazione esplicita dell'**incremento di sfruttamento** conseguente alla condizione C2
- Verifiche di esercizio (deformabilità) per C1 e C1+C2
- Azioni in fondazione per C1 e C1+C2
- Verifiche a fatica delle saldature dei giunti a flangia (metodo ciclico, EN 1991-1-4:2005 per numero cicli; EN 1993-1-9 per resistenza a fatica)
- Verifiche strutturali dei plinti (DM 17.01.2018)
- Verifica stabilità aero-elastica (vortex shedding — risonanza periodo proprio vs periodo distacco vortici)
- Per Roof Top: verifica sottostrutture edificio fino alla fondazione (per gli elementi sovrasollecitati in modo non trascurabile)

### Documentazione accessoria
- Report fotografico del sopralluogo con indicazione degli interventi di ripristino
- Indicazioni sulla manutenzione futura
- Piano di manutenzione

### Coefficienti di pressione
- Cp antenne sistemi radianti: **min 1,2**
- Cp parabole ed RRU: **min 1,3**
- Il progettista adotta valori più penalizzanti ove necessario
- La tabella con i coefficienti adottati deve essere riportata in relazione
