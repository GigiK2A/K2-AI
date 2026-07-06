---
name: template-generation
description: >-
  Generazione documenti strutturati da template per PMI italiane: offerte
  commerciali, contratti di fornitura, relazioni tecniche, verbali, perizie,
  report KPI. Usa quando l'utente vuole produrre un documento a partire
  da dati strutturati o da conversazione.
---

# Generazione Documenti da Template

## Template supportati per PMI italiane

| Documento | Campi obbligatori | Usi tipici |
|-----------|------------------|------------|
| Offerta commerciale | Cliente, oggetto, prezzi, validità, condizioni | Preventivi, proposte |
| Contratto fornitura | Parti, oggetto, prezzo, termini, penali | Accordi con fornitori |
| Relazione tecnica | Oggetto, metodologia, risultati, allegati | Ingegneria, consulenza |
| Verbale riunione | Data, partecipanti, ODG, delibere, azioni | Meeting, assemblee |
| Perizia di stima | Oggetto, metodo valutativo, valore | Immobili, attrezzature |
| Report KPI mensile | Periodo, metriche, trend, azioni | Management review |
| Lettera formale | Mittente, destinatario, oggetto, corpo, firma | Comunicazioni ufficiali |
| NDA/Riservatezza | Parti, oggetto, durata, penali | Accordi riservati |

## Variabili standard nei template

Usa questa notazione per i placeholder: `[NOME_CAMPO]`

Esempi:
- `[NOME_CLIENTE]` / `[RAGIONE_SOCIALE]`
- `[DATA_DOCUMENTO]` / `[DATA_VALIDITA]`
- `[IMPORTO]` / `[IMPORTO_IN_LETTERE]`
- `[OGGETTO_FORNITURA]`
- `[NOME_FIRMATARIO]` / `[RUOLO_FIRMATARIO]`
- `[P_IVA]` / `[CF]`
- `[INDIRIZZO_LEGALE]`

## Processo di generazione

1. **Identifica il tipo di documento** richiesto dall'utente
2. **Raccogli i dati mancanti** con UNA domanda per volta — non elenchi
3. **Adatta il template al settore** (un contratto ingegneria ≠ contratto software)
4. **Compila le variabili** con i dati forniti
5. **Verifica coerenza interna** (date, importi, nomi coerenti in tutto il doc)
6. **Aggiungi disclaimer** se documento legale: "Da sottoporre a revisione legale prima dell'uso"

## Logica condizionale nei template

```
SE tipo_cliente = "PA" ALLORA
  aggiungi clausola pagamento 30/60gg art. 4 D.Lgs. 231/2002
  aggiungi obbligo tracciabilità flussi finanziari L. 136/2010

SE importo > 40.000€ ALLORA
  aggiungi garanzia fideiussoria

SE settore = "edilizia" ALLORA
  aggiungi riferimenti NTC 2018 e D.Lgs. 81/2008
```

## Adattamenti per settore

**Studi professionali** (ingegneria, architettura, commercialisti):
- Parcella con riferimento tariffario (D.M. 140/2012 o accordo privato)
- Polizza RC professionale obbligatoria citata
- Riservatezza dati cliente

**PMI manifatturiero**:
- Condizioni Incoterms se export
- Garanzia prodotto (min. 12 mesi per B2B, 24 mesi per B2C)
- Responsabilità prodotto

**Servizi B2B**:
- SLA e livelli di servizio con penali
- Clausola riservatezza / NDA inline
- Proprietà intellettuale dell'output

## Formato output

- Markdown ben strutturato con intestazioni, tabelle, elenchi
- Evidenzia in **grassetto** le sezioni critiche da verificare prima della firma
- Metti `[DA COMPLETARE]` sui campi che l'utente non ha fornito
- Aggiungi nota finale: "Documento generato da AI — verificare prima dell'uso esterno"

## Qualità e verifica automatica

Prima di consegnare il documento controlla:
- Tutti i `[PLACEHOLDER]` sono stati compilati o segnalati
- Date coerenti (data documento ≤ data validità)
- Importi coerenti (subtotale + IVA = totale)
- Parti contraenti complete (nome, CF/PIVA, indirizzo)
- Legge applicabile e foro competente presenti (se contratto)
