---
name: flusso-consulenza-pnrr
description: >
  Orchestratore per consulenza su interventi PNRR e politiche pubbliche.
  Usa quando devi valutare un intervento PNRR, supportare un ente pubblico
  nell'implementazione, o analizzare l'impatto di una misura. Coordina:
  (1) inquadramento di policy con quadro normativo UE e nazionale
  (consulente-policy-ue, consulente-finanza-pubblica), (2) gestione
  procedurale lato PA (consulente-pa-operativa: appalti, RUP, MEPA,
  procedimento amministrativo), (3) valutazione economica dell'intervento
  con analisi costi-benefici, (4) valutazione causale ex-post con metodi
  econometrici (policy-evaluation-bocconi: DiD, RD, IV, RCT). Attiva per
  "PNRR intervento", "valutazione policy pubblica", "consulenza ente PNRR",
  "ACB infrastruttura", "impact evaluation programma".
---

# Flusso Consulenza PNRR

Skill orchestratrice per supportare interventi PNRR end-to-end: dalla progettazione alla valutazione.

## Sequenza operativa

1. **Inquadramento policy**: missione/componente PNRR, ente attuatore, target M&T, scadenze.
2. **Quadro normativo** → `consulente-policy-ue` (governance NGEU, condizionalita, Country-Specific Recommendations) + `consulente-finanza-pubblica` (logica intervento, beni pubblici/esternalita).
3. **Implementazione PA** → `consulente-pa-operativa` (RUP, codice appalti D.Lgs. 36/2023, MEPA/CONSIP, procedimento, DURC, controlli).
4. **Analisi costi-benefici** → `consulente-finanza-pubblica/analisi-costi-benefici` per VAN sociale, prezzi ombra, saggio sociale di sconto.
5. **Valutazione causale ex-post** → `policy-evaluation-bocconi` (RCT se possibile, DiD su comuni trattati vs controllo, RD su soglie, IV per identificare effetti causali).
6. **Sintesi**: cronoprogramma, KPI di monitoraggio, rischi di policy, piano di valutazione.

## Output atteso

Documento strutturato: razionale dell'intervento, quadro normativo, piano implementativo, ACB ex-ante, design valutativo ex-post.

## Quando usarla

Quando l'intervento ha (a) dimensione policy + (b) gestione PA operativa + (c) bisogno di valutazione di impatto. Per pratiche puramente amministrative (es. SCIA singola) usa direttamente `consulente-pa-operativa`.
