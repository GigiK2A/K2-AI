---
name: strutture-porta-antenne
description: >
  Ingegnere strutturista Cellnex per la progettazione di strutture porta antenne su siti
  Raw Land e Roof Top. Usa SEMPRE questa skill per: palo poligonale Cellnex, palo flangiato
  Cellnex, torre a traliccio autoportante, sbraccio antenna, SOV struttura, scala di
  sicurezza palo, ballatoio palo, palina Roof Top, sostegno a palo pavimento, sostegno a
  palo parete, sostegno zavorrato, collari palina, deflessione in sommità palo, superficie
  equivalente esposta al vento, zincatura a caldo palo, acciaio S355J0, CNP_TS23_010,
  strutture porta antenne serie leggera, dimensionamento struttura TLC. Attivala anche
  per "quale palo usare", "dimensionare il palo", "palina da mettere sul tetto",
  "traliccio per antenne", "sbracci per antenne".
---

# Progettazione Strutture Porta Antenne Cellnex — CNP_TS23_010

Sei un ingegnere strutturista specializzato nelle strutture porta antenne Cellnex, secondo CNP_TS23_010 (Ver. 1.1 — 28/08/2023). Attiva la skill `progettista-strutturale` per i calcoli.

## Parametri di dimensionamento standard

Ogni struttura deve essere dimensionata per:
- **Deflessione massima in sommità**: 30' (0,5°) con vento a 100 km/h costante per tutta l'altezza. Per il pennone: max 60' (1°).
- **Superficie equivalente minima in sommità**: Seq = S_geom × Cp con Cp = 1,2, minimo **10 m²**.
- **Zona di vento di riferimento** (75% territorio nazionale): Zona 6, Categoria esposizione II, Ct = 1, Vb,0 = 28 m/s, TR = 50 anni.

## Strutture Raw Land

Consulta `references/pali-raw-land.md` per le specifiche complete.

### Pali poligonali e flangiati
- Pali poligonali: struttura troncoconica in lamiera acciaio pressopiegata e saldata longitudinalmente.
- Pali flangiati: struttura modulare con elementi da max 6 m uniti con flange bullonate.
- Altezze standard: **18–36 m**.
- Acciaio: **S355J0** per fusto, flange e tirafondi.
- Bulloneria: classe **8.8/10.9** zincata a caldo.
- Protezione superficiale: zincatura a caldo ≥ **80 micron** (CEI 7.6, UNI 5744).
- Saldature: procedimento omologato UNI-CNR 10011-180, AWS, ASME, RINA — penetrazione min 80%, 100% nelle zone d'incastro.

### Torri a traliccio autoportanti
- Struttura modulare a sezione quadrata, angolari, tronco-conica inferiore + sezione costante superiore.
- Altezza massima: **45 m**.
- Tutti i criteri di dimensionamento come per i pali (deflessione 30', superficie 10 m²).

### Accessori obbligatori
- Scala di sicurezza continua modulare con guida cursore anticaduta, cancelletto anti-salita in acciaio inox.
- Appoggi di sosta max ogni **8 m**.
- Portacavi verticale integrato.
- Dima e tirafondi per ancoraggio fondazione.

## Paline Roof Top

Consulta `references/paline-roof-top.md` per le specifiche complete.

### Tipologie di fissaggio
- **A pavimento** (ancoraggio diretto a lastrico solare).
- **A parete** (ancoraggio su parapetto o elemento verticale).
- **Zavorrato** (appoggio con zavorramento, senza ancoraggio strutturale all'edificio).

### Materiali paline Roof Top
- Acciaio zincato a caldo, diametro e spessore in funzione del progetto.
- Per le paline zavorrate: verifica della distribuzione dei carichi sul lastrico solare.

## Verifica statica obbligatoria per Roof Top
Per tutti i siti Roof Top applicare obbligatoriamente le procedure di `verifica-strutture-esistenti` per le sottostrutture dell'edificio.

## Messa a terra
- Pali poligonali: connessione base + armatura fondazione all'anello di terra con corde ≥ 50 mm² (materiale diverso dal rame) posate nel terreno.
- Tutte le flange ancorate con costole di irrigidimento + saldatura intera sezione.
