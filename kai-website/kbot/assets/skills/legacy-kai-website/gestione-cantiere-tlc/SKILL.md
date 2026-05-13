---
name: gestione-cantiere-tlc
description: >-
  Gestione operativa cantieri TLC (iliad, Cellnex, WindTre): tracking fasi,
  SAL, report avanzamento, documentazione obbligatoria, fatturazione BEF/CDMS.
  Usa per monitorare stati cantiere, identificare blocchi, aggiornare tracker.
---

# Gestione Cantieri TLC — Operatività Completa

## Fasi standard cantiere TLC

| Fase | Descrizione | Output atteso |
|------|-------------|---------------|
| PE | Progetto Esecutivo firmato | Elaborati + relazione tecnica |
| SCIA/PCIA | Istanza autorizzativa | Protocollo comune |
| PSC | Piano Sicurezza e Coordinamento | Documento firmato CSP |
| Approvvigionamento | Ordini materiali e apparati | Conferme d'ordine |
| Installazione | Lavori civili + apparati | Verbale fine lavori |
| Collaudo | Test RF + verifica strutturale | Report collaudo |
| BEF | Bolla Elettronica Fatturazione | File Excel CDMS |

## Indicatori di stato per fase

- **Vidimata**: fase approvata dall'operatore → traccia data + utente
- **NC**: non conformità rilevata → descrivi NC + azione correttiva + deadline
- **Bloccata**: blocco esterno (Comune, proprietario, rete elettrica) → motivo + escalation
- **In attesa**: in attesa risposta terzi → da chi + scadenza follow-up

## Report avanzamento — struttura

```
REPORT CANTIERI [DATA]
━━━━━━━━━━━━━━━━━━━━━
AVANZAMENTO GLOBALE
- Totale siti: XX
- Completati: XX (XX%)
- In lavorazione: XX
- Bloccati: XX → azione richiesta

SITI CRITICI (blocchi > 30gg)
1. [SITO] — motivo blocco — azione — owner — scadenza

PROSSIME SCADENZE (7gg)
- [SITO] — [FASE] — [DATA]
```

## Fatturazione BEF (Cellnex)

File BEF contiene per ogni sito:
- ID_SITO, CODICE_COMMESSA, DATA_FINE_LAVORI
- TIPO_LAVORO (new site / transfer / upgrade / manutenzione)
- IMPORTO_NETTO, ALIQUOTA_IVA, IMPORTO_LORDO
- NOTE_FATTURAZIONE

Verifica prima di emettere BEF:
1. Collaudo completato e firmato
2. Verbale fine lavori allegato
3. Eventuali NC chiuse
4. Importo allineato al contratto di fornitura

## Blocchi comuni e azioni

| Tipo blocco | Causa frequente | Azione |
|-------------|-----------------|--------|
| Autorizzativo | Comune non risponde / diniego | Diffida + escalation legale |
| Proprietario | Mancato accordo accesso | Rinegoziazione canone o spostamento sito |
| Elettrico | E-Distribuzione ritarda allaccio | Sollecito scritto + contatto commerciale |
| Strutturale | Verdetto NV su palo esistente | Perizia rinforzo o cambio site |
| Materiali | Delivery apparati in ritardo | Alternativa stock / altro fornitore |

## Regole operative

- Non dichiarare fase completata senza evidenza documentale
- Ogni NC deve avere: data rilevazione, descrizione, responsabile, data chiusura prevista
- SAL mensile entro il 5 del mese successivo
- Siti bloccati da > 45gg → segnalare in escalation automatica
- Sempre distinguere responsabilità: K-AI / Operatore / Terzi
