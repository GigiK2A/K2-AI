---
name: nda-triage
description: Classificazione rapida NDA in ACCETTABILE / DA MODIFICARE / DA RIFIUTARE con red flag
---

# NDA Triage

## Classificazione

Ogni NDA va classificato in una di tre categorie con reasoning esplicito:

- **ACCETTABILE** — standard, no red flag, firma con nota
- **DA MODIFICARE** — clausole problematiche specifiche, proponi modifiche puntuali
- **DA RIFIUTARE** — rischio inaccettabile, spiega perché e proponi alternativa

## Red flag automatici

Segnala obbligatoriamente se presente:

- Durata confidenzialità >5 anni senza giustificazione
- Definizione di "informazioni riservate" eccessivamente ampia (tutto ciò che viene condiviso)
- Mancanza eccezioni standard: info già pubblica, sviluppata indipendentemente, ricevuta da terzi lecitamente
- Clausole di non-concorrenza embedded nell'NDA (fuori scope)
- Legge applicabile non italiana senza giustificazione commerciale
- Assenza di procedura per violazione accidentale
- Asimmetria unilaterale estrema senza contropartita

## Output strutturato

1. Classificazione (ACCETTABILE / DA MODIFICARE / DA RIFIUTARE)
2. Motivazione (max 3 punti chiave)
3. Red flag trovati (lista)
4. Modifiche suggerite (testo alternativo per ogni clausola problematica)
5. Raccomandazione finale

## Regole

- Triage in <5 minuti per NDA standard (<10 pagine).
- Non rifiutare per eccesso di prudenza — valuta il contesto commerciale.
- Per NDA bilaterale: verifica simmetria obblighi tra le parti.
