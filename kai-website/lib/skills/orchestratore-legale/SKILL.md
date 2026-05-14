---
name: orchestratore-legale
version: 0.1.0
description: >-
  Suite K2-AI Legale & Contratti per PMI italiane (49-1.499 EUR): revisione contratti vs playbook,
  triage NDA in GREEN/YELLOW/RED, compliance check GDPR/AI Act/NIS2, diritto civile penale
  amministrativo tributario italiano, diritto societario SRL/SPA/SNC/fusioni/M&A, patti
  parasociali, antitrust UE/AGCM, vendor check stato accordi, generazione risposte legali
  standard, signature request per firma elettronica eIDAS, risk assessment legale severita x
  probabilita, briefing legale contestuale. ATTIVA SEMPRE QUESTO ORCHESTRATORE K2-AI per:
  revisione contratto, NDA review, contratto fornitura, MSA Master Service Agreement, DPA, SOW,
  GDPR compliance, AI Act, DSA, DMA, NIS2, eIDAS firma elettronica, costituzione SRL SPA, patti
  parasociali, M&A acquisizione PMI, due diligence legale, cessione quote, fusione scissione,
  antitrust 101 102 TFEU, AGCM, abuso posizione dominante, intesa restrittiva, vendor check
  scadenze MSA, response cliente fornitore standard, risk assessment legale, triage rischi.
  Workflow K2-AI: triage tipo richiesta (contratto/NDA/compliance/societario/M&A), recupero
  playbook K2-AI o cliente, revisione clausole con redline, classificazione rischi, suggerimento
  negoziazione, output documento finale. Differenziatori unici: italiano nativo (non tradotto da
  EN), tono titolare PMI (non legalese), bridge automatico con `k2ai-compliance` per GDPR/AI Act,
  contesto italiano (Codice Civile, OIC, Cassazione recente).
allowed-tools:
  - WebFetch
  - WebSearch
  - Read
  - Write
  - Bash
---

# k2ai-legale — Orchestratore Legale & Contratti

Per PMI italiane 5-50 dipendenti che non hanno legale in-house. Coordina 12 skill legali e produce review contratti, NDA triage, compliance check, supporto M&A.

## Posizionamento competitivo

| Concorrente | Cosa fa | Cosa NON fa |
|---|---|---|
| Avvocato locale | Tutto, ma 2-5k EUR per pratica | Triage rapido NDA, review veloce, prezzo accessibile |
| LegalAI generico (es. Lawgeex) | Review contratti EN | Italiano nativo, contesto Codice Civile |
| LawDepot/template | Modelli base | Negoziazione, redline, contesto azienda |

**Tagline:** "Triage NDA in 3 minuti, review contratto in 1 giorno, compliance GDPR/AI Act PMI italiana. A prezzo PMI."

## Skill orchestrate (P03)

- `legal:review-contract`, `legal:triage-nda`, `legal:compliance-check`
- `legal:legal-response`, `legal:legal-risk-assessment`, `legal:vendor-check`
- `legal:brief`, `legal:signature-request`
- `diritto-italiano` (civile/penale/amministrativo/tributario/GDPR)
- `diritto-societario-italiano` (SRL/SPA/SNC, fusioni, patti parasociali, M&A)
- `it-law-privacy-ai` (GDPR, AI Act, DMA, DSA, eIDAS, NIS2)
- `antitrust-concorrenza-ue` (Art. 101/102 TFEU, merger control, AGCM)
- `diritto-processuale` (processo civile e penale)
- `fiscale-tributario-italiano` (accertamenti, ravvedimento)

**Base teorica K2-AI**:
- Phil: `phil-etica` (dilemmi etici - es. clausole opacita), `phil-logica` (ambiguita contrattuale, claim verificabili)
- Psy: `psy-decisioni` (loss aversion in negoziazione)
- Bocconi: `management-bocconi` (governance, stakeholder theory)

## Workflow (6 step)

1. **Triage richiesta**: contratto / NDA / compliance / societario / M&A / response cliente
2. **Recupero playbook**: K2-AI default playbook OR upload cliente
3. **Review documento**: invoca skill specifica (`legal:review-contract`, `legal:triage-nda`)
4. **Risk assessment**: `legal:legal-risk-assessment` severita × probabilita
5. **Output**: redline + raccomandazioni + classificazione GREEN/YELLOW/RED
6. **Bridge**: se compliance GDPR/AI Act → `k2ai-compliance`. Se M&A → `k2ai-pmi-strategy` Step 7

## Domande standard per pacchetto

### Express NDA Triage (49 EUR)
1. Tipo documento (NDA, MSA, DPA, SOW, altro)
2. Sei firmatario o controparte?
3. Settore + relazione (cliente/fornitore/partner)
4. NDA caricato (PDF/DOCX)
5. Negoziabile? Sì/No
6. Urgenza (24h/48h/standard)

### Standard Contract Review (299 EUR)
1-6 +
7. Documento completo
8. Playbook cliente o usa K2-AI default
9. Importo contratto (range)
10. Durata
11. Cause critiche da segnalare
12. Bozza tua o controparte?

### Pro M&A Legal DD (1.499 EUR)
1-12 +
13. Tipo operazione (acquisizione/fusione/cessione)
14. Controparte (PMI italiana/estera/fondo)
15. Documenti DD (data room link/upload)
16. Timeline closing
17. Vincoli specifici (golden share, lock-up, earn-out)
18. Studio legale controparte

## JSON output schema

```json
{
  "tier": "express|standard|pro_mna",
  "documento": {"tipo":"","parti":[],"importo":0,"durata":""},
  "triage_color": "GREEN|YELLOW|RED",
  "rischi": [{"clausola":"","severita":"alta|media|bassa","probabilita":0-1,"impatto":"","mitigazione":""}],
  "redline": [{"clausola_originale":"","clausola_proposta":"","motivazione":""}],
  "compliance": {"gdpr":"ok|gap","ai_act":"ok|gap|na","altre":[]},
  "raccomandazioni_negoziazione": [],
  "deliverable": {"redline_docx":"","memo_legale":"","riassunto_titolare":""}
}
```

## Tiering pricing

| Versione | Prezzo | Cosa include |
|---|---|---|
| Express NDA | 49 EUR | Triage GREEN/YELLOW/RED + top 3 clausole rischiose |
| Standard | 299 EUR | Review completa contratto + redline + memo legale |
| Pro M&A | 1.499 EUR | DD legale + redline patti parasociali + memo M&A |

## Bridge K2-AI

- → `k2ai-compliance` per GDPR/AI Act/NIS2 implementation
- → `k2ai-pmi-strategy` per M&A advisory + valuation
- → `k2ai-tokenizzazione` per contratti SPV + ECSP

## Test prompts

1. (forzato) "Usa k2ai-legale per triage NDA con multinazionale tedesca per PMI Brescia"
2. (cliente reale) "Mi hanno mandato un MSA di 40 pagine, devo firmare entro venerdi"
3. (cliente reale) "Voglio cedere 30% della mia SRL a un socio investitore, patti parasociali"
4. (cliente reale) "Sono in causa con un fornitore, ricevo la lettera di diffida"
5. (A/B) "review contratto fornitura PMI italiana con clausole rischiose"

## Note implementative

- Disclaimer obbligatorio: "Output K2-AI non sostituisce parere avvocato iscritto all'Ordine. Per cause attive, sempre raccomandare avvocato"
- Per NDA estere in EN: traduci sempre prima in italiano per il titolare PMI
- Antitrust: per PMI <50 dipendenti, raramente applicabile Art. 101/102 — segnala se non rilevante invece di sovra-analizzare
- Cassazione recente: cita sentenze ultimi 24 mesi, evita precedenti pre-2020 obsoleti
- M&A: la due diligence legale richiede MIN 4-6 settimane reali, non promettere 1 settimana
