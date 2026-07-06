---
name: confronto-rf-tlc
description: Sub-skill di VerifyBoost TLC. Confronta la configurazione radio installata con il progetto RF (scheda radio + tav. 21-22 PE + parere ARPAT CEM + verbali TX/RF post-attivazione). Verifica modelli antenne, azimut (tolleranza ±5°), tilt meccanico (tolleranza ±1°), altezza centro radiante, parabole MW (Ø, azimut, centro elettrico), apparati radio (RFM, MiniTD, FCOB). Si attiva quando l'orchestratore richiede confronto RF/TLC.
---

# Confronto RF/TLC installato vs progetto

## Trigger di attivazione

- Chiamata da `verifyboost-tlc-orchestrator` (Step 3)
- "Verifica configurazione radio sito {codice}"
- "Controlla azimut tilt antenne"
- "Confronto RF"

## Tolleranze normative

Vedi `references/tolleranze-normative-tlc.md`. Sintesi:

| Parametro | Tolleranza | Norma |
|---|---|---|
| Azimut antenne settoriali | ±5° meccanico | Verifica PSP-CEM ARPA |
| Tilt meccanico | ±1° | Verifica PSP-CEM |
| Tilt elettrico | ±0° (è settabile da remoto) | Scheda radio |
| Altezza centro radiante | ±50 cm su pali H≤30m | Linea guida operatori |
| Posizione palo planimetrica | ±50 cm dalla coordinata di progetto | Autorizzazione |

## Pipeline operativa

### 1. Estrai dati progetto RF

Dal PE iliad standard:
- **Scheda Radio principale** (foglio elettronico esportato in PDF) con tutti i settori e bande (700 5G, 900 UMTS, 1800 LTE, 2100 LTE, 2600 LTE, 3700 5G)
- **Scheda Radio MW** con parabole microwave
- **Tav. 21-22** con orientamenti grafici
- **Tabella RC-x** della relazione tecnica (attenzione ai refusi - vedi `references/refusi-noti-pe-iliad.md`)

Se trovi discrepanze tra scheda radio e tabella RC, **la scheda radio è la fonte ufficiale** (è approvata da ARPAT CEM).

### 2. Estrai evidenze installato

- Foto retro antenne con etichette CE (modello + ID seriale)
- Eventuale verbale TX/RF check del NOC operatore
- PSP-CEM aggiornato post-attivazione

### 3. Confronto sistemico

| Elemento | Progetto | Installato | Esito tipico |
|---|---|---|---|
| Modello antenne settoriali | NOKIA CS7801001 + AEQE_v90_#8 (iliad) | Etichetta CE su foto | OK / NC_DOC se etichetta non leggibile |
| N. settori | 3 | Da foto + struttura sbracci | OK |
| Azimut settori | [70°, 210°, 310°] | Misura da verbale TX/RF | OK / OK_TOL se ±5° / NC_GR se >±5° |
| Tilt meccanico | [0°, 0°, 0°] tipico | Misura | OK / OK_TOL se ±1° |
| Altezza centro radiante | 26.90 m tipico | Calcolo da quota base + offset | OK |
| N. parabole MW | 0-3 (tipico iliad: 2) | Foto | OK |
| Modelli parabole | Huawei A32S03EAC Ø30 / RTN320 / similar | Da scheda radio MW | OK |
| Azimut parabole | Da scheda MW (es. 30°/250°) | Da verbale TX o foto orientamento | OK / NC_GR se errato |
| Apparati RFM | n. 7 RFM tipico | Foto rack | OK |
| FCOB / MiniTD / ICA | come da PE | Foto | OK |
| Antenna GPS | esterna / interna mascheramento | Foto | OK |
| Cablaggio jumper RF | Etichette di tracciabilità | Foto cavi etichettati | OK / NC_DOC |

### 4. Verifica conformità CEM (ARPAT)

Se disponibile il PSP-CEM aggiornato post-attivazione, confronta:
- Potenza max simulata vs potenza reale apparati
- Punti di simulazione vs limiti CEM (DM 02/12/2014, DPCM 08/07/2003)

Se PSP-CEM aggiornato MANCA → **NC_DOC** con impatto medio (rischio contestazione ARPAT).

### 5. Output strutturato

```json
{
  "confronto_rf_tlc": {
    "elementi_verificati": [
      {
        "elemento": "modello_antenne_5G_3700",
        "progetto": "NOKIA AEQE_v90_#8",
        "installato_evidenza": "Foto etichetta CE Nokia codice 4753114A.101",
        "esito": "OK"
      },
      {
        "elemento": "azimut_settori",
        "progetto": "[70°, 210°, 310°]",
        "installato_evidenza": "non disponibile - verbale TX/RF assente",
        "esito": "NC_DOC",
        "azione_raccomandata": "Recupero verbale TX/RF check da NOC operatore"
      }
    ],
    "psp_cem_post_installazione": "ASSENTE - prescrivere generazione e invio ARPAT"
  }
}
```
