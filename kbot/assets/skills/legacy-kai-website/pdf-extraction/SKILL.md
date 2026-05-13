---
name: pdf-extraction
description: >-
  Estrazione, strutturazione e normalizzazione di dati da documenti PDF per PMI italiane. Gestisce sia PDF digitali (testo selezionabile) che PDF scansionati (immagine), identificando sezioni rilevanti come intestazioni, tabelle, firme, date, KPI finanziari, clausole contrattuali e metadati documento. Usa questa skill ogni volta che l'utente fornisce un PDF da cui estrarre dati strutturati, informazioni specifiche o contenuti da rielaborare in report, analisi o template.
---

# Estrazione e Strutturazione Dati da PDF

Skill operativa per l'analisi e l'estrazione intelligente di contenuto da documenti PDF, con particolare focus su documenti aziendali, tecnici, finanziari e legali tipici delle PMI italiane.

## Distinzione Fondamentale: PDF Digitale vs Scansionato

### PDF Digitale (testo selezionabile)
- Il testo è estratto direttamente e con alta fedeltà
- Le tabelle mantengono la struttura originale se ben formate
- I metadati (autore, data creazione, titolo) sono accessibili
- Velocità di elaborazione: alta
- Affidabilità: 95%+

### PDF Scansionato (immagine)
- Richiede OCR (Optical Character Recognition) per estrarre il testo
- Qualità dipende da risoluzione scansione (minimo 200 DPI, ottimale 300 DPI)
- Tabelle spesso non riconoscibili come struttura — necessaria ricostruzione manuale
- Firma e timbri: riconoscibili come immagini, non come testo
- Affidabilità: 70-90% in base alla qualità
- **Azione**: segnalare all'utente se si tratta di scansione e il livello di confidenza

## Workflow di Estrazione

### Step 1: Analisi Preliminare del Documento

Prima di estrarre, identificare:
1. **Tipo documento**: bilancio, contratto, relazione tecnica, fattura, perizia, offerta, verbale, certificato
2. **Lingua**: italiano (prevalente), inglese, misto
3. **Struttura**: ha indice? sezioni numerate? tabelle? allegati?
4. **Qualità**: PDF nativo o scansione? qualità immagini?
5. **Lunghezza**: numero pagine, densità informativa

Comunicare all'utente il tipo rilevato e chiedere conferma dell'obiettivo di estrazione se non è esplicito.

### Step 2: Identificazione Sezioni Rilevanti

#### Elementi Strutturali da Riconoscere
- **Intestazione documento**: titolo, numero protocollo, data, versione/revisione
- **Intestazione pagina (header)**: logo, ragione sociale, codice documento
- **Piè di pagina (footer)**: numerazione pagine, data, versione
- **Indice/Sommario**: struttura gerarchica capitoli
- **Firme e timbri**: posizione, nome firmatario, data
- **Note a piè di pagina**: numerazione, testo

#### Pattern di Riconoscimento per Tipo Documento

**Bilancio / Documento Finanziario**:
- Cercare: "Stato Patrimoniale", "Conto Economico", "Nota Integrativa", "Rendiconto Finanziario"
- Voci tipiche attivo: immobilizzazioni, crediti, disponibilità
- Voci tipiche passivo: patrimonio netto, TFR, debiti
- Anni di confronto in colonne parallele
- Totali e subtotali da verificare aritmeticamente

**Contratto / Accordo Legale**:
- Cercare: "Parti", "Premesse/Whereas", "Oggetto", "Durata", "Corrispettivo/Prezzo", "Penali", "Risoluzione", "Foro competente"
- Date: data firma, data decorrenza, date scadenza
- Importi: con e senza IVA, modalità pagamento
- Clausole di riservatezza (NDA), esclusiva, non concorrenza

**Relazione Tecnica / Perizia**:
- Cercare: "Premessa", "Oggetto", "Metodologia", "Risultati", "Conclusioni"
- Dati tecnici nelle tabelle: numeri con unità di misura
- Normative citate: DM, UNI, EN, ISO con anno
- Valori di calcolo, misure, verifiche

**Fattura / Documento Fiscale**:
- Cedente e cessionario (P.IVA, CF, indirizzo)
- Numero e data fattura
- Descrizione beni/servizi, quantità, prezzo unitario
- Imponibile, aliquota IVA, importo IVA, totale
- Codice destinatario SDI / PEC (fattura elettronica)

### Step 3: Estrazione Tabelle

Le tabelle sono l'elemento più critico. Seguire questo approccio:

1. **Identifica i confini**: dove inizia e finisce la tabella?
2. **Intestazione**: la prima riga è intestazione? è su più righe?
3. **Righe aggregate / subtotali**: identificare e marcare
4. **Celle unite (merge)**: ricostruire la struttura originale
5. **Tabelle multi-pagina**: verificare se la tabella continua nella pagina successiva
6. **Unità di misura**: sono nell'intestazione colonna o nelle celle?

**Output formato tabella**:
```
| Voce | Anno 2023 | Anno 2022 | Variazione % |
|------|-----------|-----------|--------------|
| Ricavi | 1.250.000 | 1.100.000 | +13,6% |
| EBITDA | 187.500 | 154.000 | +21,8% |
```

### Step 4: Normalizzazione Dati Estratti

#### Numeri e Valori
- Rimuovere separatori di migliaia ambigui (punto/spazio) e standardizzare
- Formato output: usare la virgola come separatore decimale italiano
- Valori tra parentesi = negativi: "(125.000)" → -125.000
- Valori con asterisco o nota: preservare il riferimento alla nota
- Percentuali: verificare che sommino correttamente (es. quote di mercato)

#### Date
- Normalizzare al formato ISO esteso italiano: "15 marzo 2024" o "15/03/2024"
- Attenzione a formati ambigui: "04/05/24" → chiedere conferma mese/giorno
- Date in testo narrativo: estrarre e strutturare separatamente

#### Entità Nominali
- Ragioni sociali: preservare la forma esatta inclusa la forma giuridica (S.r.l., S.p.A., S.a.s.)
- P.IVA e CF: validare il formato (P.IVA: 11 cifre; CF: 16 caratteri alfanumerici)
- IBAN: formato IT + 2 cifre check + 1 lettera + 22 caratteri
- Codici normativi: preservare esattamente (DM 17/01/2018 ≠ DM 17/1/18)

### Step 5: Estrazione KPI Finanziari da Bilanci

Per bilanci PMI, estrarre sistematicamente:

**Conto Economico**:
- Ricavi delle vendite (A1)
- Valore della produzione (A totale)
- Costi della produzione (B totale)
- EBITDA (A - B + ammortamenti)
- EBIT (A - B)
- Proventi/oneri finanziari (C)
- Risultato prima delle imposte
- Imposte
- Utile/perdita netto

**Stato Patrimoniale**:
- Immobilizzazioni (materiali, immateriali, finanziarie)
- Attivo circolante (magazzino, crediti, liquidità)
- Patrimonio netto
- Fondi rischi e TFR
- Debiti finanziari (a breve e lungo)
- Debiti commerciali

**Calcolare e riportare**:
- Totale attivo (= totale passivo + PN)
- CCN (Capitale Circolante Netto) = Attivo corrente - Passivo corrente
- PFN (Posizione Finanziaria Netta) = Debiti finanziari - Liquidità

### Step 6: Output Strutturato

L'output dell'estrazione deve essere sempre strutturato in JSON o tabella markdown, mai solo testo narrativo:

```json
{
  "tipo_documento": "bilancio_civilistico",
  "societa": "Rossi S.r.l.",
  "partita_iva": "01234567890",
  "anno_riferimento": 2023,
  "data_approvazione": "2024-04-30",
  "conto_economico": {
    "ricavi": 1250000,
    "ebitda": 187500,
    "ebit": 125000,
    "utile_netto": 78000
  },
  "stato_patrimoniale": {
    "totale_attivo": 890000,
    "patrimonio_netto": 320000,
    "pfn": 210000
  },
  "confidenza_estrazione": "alta",
  "note": ["Bilancio PDF nativo", "Anno comparativo 2022 presente"]
}
```

## Gestione Errori e Incertezze

### Segnalare Sempre
- Testo illeggibile o di bassa qualità OCR → indicare la sezione e il livello di confidenza
- Valori che non tornano aritmeticamente → segnalare la discrepanza
- Tabelle troncate o tagliate → chiedere la pagina mancante
- Contraddizioni interne al documento → evidenziare entrambi i valori

### Mai Inventare
- Non completare valori mancanti con stime senza dichiararlo esplicitamente
- Non assumere un anno se non è dichiarato nel documento
- Non tradurre termini giuridici o tecnici se ambigui — preservare l'originale

## Skill Correlate

| Skill | Quando invocarla |
|-------|-----------------|
| `technical-writing` | Per rielaborare il contenuto estratto in un documento strutturato |
| `template-generation` | Per compilare un template con i dati estratti |
| `analisi-bilancio-pmi` | Per analizzare i dati finanziari estratti |
| `review-contract` | Per analizzare clausole estratte da contratti |
| `docx` | Per produrre il documento finale rielaborato |
