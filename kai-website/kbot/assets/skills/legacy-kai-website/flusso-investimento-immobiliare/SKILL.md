---
name: flusso-investimento-immobiliare
description: >
  Orchestratore per valutazione e strutturazione di investimento immobiliare
  (acquisto, sviluppo, riqualificazione, locazione commerciale). Coordina:
  (1) perizia di stima valore di mercato (perizia-estimo-immobiliare),
  (2) analisi finanziaria DCF investimento e leva (corporate-finance,
  casi-numerici-bocconi), (3) benchmark yield e prezzi al mq per zona
  (benchmark-italia-business), (4) inquadramento fiscale (registro,
  successioni, IMU, plusvalenze, fiscale-tributario-italiano,
  fiscale-dogmatico-internazionale), (5) verifiche urbanistico-edilizie
  (progettazione-architettonica, agibilita) e paesaggistiche se vincolato
  (architetto-beni-monumentali), (6) protezione patrimoniale via
  societa semplice o trust se rilevante (ss-trust-italiano), (7) valutazione
  tokenizzazione se asset frazionabile (tokenizzazione-immobiliare).
  Attiva per "valutare investimento immobile", "acquistare immobile da reddito",
  "sviluppo immobiliare", "passaggio generazionale immobile".
---

# Flusso Investimento Immobiliare

Skill orchestratrice per valutare un investimento immobiliare in tutte le sue dimensioni: tecnica, finanziaria, fiscale, urbanistica, di protezione patrimoniale.

## Sequenza operativa

1. **Inquadramento**: tipologia (residenziale, commerciale, industriale, sviluppo greenfield), location, controvalore, finalita (reddito, sviluppo, residenza).
2. **Stima valore** → `perizia-estimo-immobiliare` (MCA, reddituale, OMI, coefficienti).
3. **Analisi finanziaria** → `corporate-finance` (DCF, IRR, payback) + `casi-numerici-bocconi` (esempi worked-out).
4. **Benchmark yield/prezzi** → `benchmark-italia-business/mercato-immobiliare` (yield per tipologia/citta, prezzo al mq).
5. **Verifiche tecniche**:
   - Conformita urbanistica → `progettazione-architettonica`
   - Agibilita → `agibilita`
   - Vincoli paesaggistici/monumentali → `architetto-beni-monumentali`
6. **Inquadramento fiscale** → `fiscale-tributario-italiano` (registro, IMU, plusvalenza) + `fiscale-dogmatico-internazionale` se proprieta da residente estero.
7. **Strutturazione**:
   - Protezione patrimoniale → `ss-trust-italiano` (SS immobiliare, trust per dopo-di-noi)
   - Frazionamento → `tokenizzazione-immobiliare` se asset adatto
8. **Sintesi**: rendimento atteso netto, rischi (tecnici, fiscali, di mercato), raccomandazione struttura.

## Output atteso

Memo investimento: valutazione, business plan finanziario, fiscalita, struttura societaria/protettiva, rischi, go/no-go.
