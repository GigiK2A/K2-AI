---
name: flusso-due-diligence-mna
description: >
  Orchestratore per due diligence M&A. Usa quando devi valutare un'operazione
  di acquisizione, fusione, joint venture o cessione. Coordina in sequenza:
  (1) valutazione finanziaria target con DCF/multipli (corporate-finance,
  finanza-quantitativa-bocconi, casi-numerici-bocconi), (2) due diligence
  contabile e analisi bilancio storico (contabilita-bilancio,
  bilancio-consolidato-analisi), (3) due diligence legale societaria
  (diritto-societario-italiano), (4) due diligence fiscale e international
  tax (fiscale-tributario-italiano, fiscale-dogmatico-internazionale),
  (5) screening antitrust soglie comunicazione (antitrust-concorrenza-ue),
  (6) benchmark di settore per multipli (benchmark-italia-business). Attiva
  per "due diligence", "M&A", "fusione", "acquisizione", "valutazione target",
  "screening antitrust merger".
---

# Flusso Due Diligence M&A

Skill orchestratrice per condurre una due diligence completa su operazione M&A. Coordina le skill verticali nell'ordine corretto e produce un dossier integrato.

## Sequenza operativa

1. **Inquadramento operazione**: tipo (acquisto azioni vs azienda vs ramo), parti, controvalore stimato.
2. **Valutazione finanziaria** → richiama `corporate-finance` (DCF, WACC, multipli) + `finanza-quantitativa-bocconi` (matematica finanziaria) + `casi-numerici-bocconi` (esempi worked-out).
3. **Analisi bilancio storico** → `contabilita-bilancio` + `bilancio-consolidato-analisi` (DuPont, riclassificazioni, rendiconto).
4. **DD legale societaria** → `diritto-societario-italiano` (statuto, patti parasociali, contenziosi, governance).
5. **DD fiscale** → `fiscale-tributario-italiano` (carico fiscale, contenzioso) + `fiscale-dogmatico-internazionale` (TP, esterovestizione, CFC se internazionale).
6. **Screening antitrust** → `antitrust-concorrenza-ue` (soglie merger control italiane/UE, notifica AGCM/CE).
7. **Benchmark** → `benchmark-italia-business` (multipli EV/EBITDA settore, ROE, leva).
8. **Sintesi**: red flags, range di valore, deal breakers, raccomandazione.

## Output atteso

Dossier strutturato con sezioni: executive summary, valutazione, bilancio, legale, fiscale, antitrust, raccomandazione finale.

## Quando NON usare

Se l'operazione è interna (riorganizzazione di gruppo senza change of control) → usa solo le skill verticali rilevanti senza orchestrazione.
