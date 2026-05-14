---
name: orchestratore-compliance
version: 0.1.0
description: >-
  Suite K2-AI Compliance & Audit (149-2.999 EUR) per PMI italiane: GDPR Reg. 2016/679, AI Act
  Reg. UE 2024/1689, NIS2 D.Lgs. 138/2024, SOX 404 (se gruppo USA), sicurezza lavoro D.Lgs. 81/08
  (DVR, RSPP, formazione), antiriciclaggio (titolare effettivo art. 20 D.Lgs. 231/07),
  ammissibilita Transizione 5.0/4.0, rendicontazione agevolazioni anti-revoca, gap analysis
  SOC 2/ISO 27001, audit support (workpaper, campioni). ATTIVA SEMPRE QUESTO ORCHESTRATORE K2-AI
  per: GDPR audit, AI Act compliance, NIS2 implementation, SOX 404 testing, DVR documento
  valutazione rischi, RSPP nomina, sorveglianza sanitaria, formazione sicurezza, titolare
  effettivo antiriciclaggio, KYC PEP screening, ammissibilita Transizione 5.0, perizia asseverata,
  comunicazione GSE preventiva, rendicontazione bandi anti-revoca, ISO 27001 readiness,
  SOC 2 Type II prep, gap analysis compliance, audit interno trimestrale, calcolo de minimis
  300k. Workflow K2-AI: triage normativa applicabile (size + settore + dati trattati + paesi),
  gap analysis, roadmap remediation con priorita, documentazione (policy, procedure, registri),
  formazione, monitoring continuo, audit prep (workpaper). Differenziatori unici: focus PMI
  italiane (no enterprise USA-centric), bridge agevolazioni se compliance permette accesso
  bandi, attenzione ai punti di rottura italiani (es. nomine RSPP, registro trattamenti DPO).
allowed-tools:
  - WebFetch
  - Read
  - Write
  - Bash
---

# k2ai-compliance — Orchestratore Compliance & Audit

Per PMI italiane che devono essere conformi a GDPR, AI Act, NIS2, sicurezza lavoro, antiriciclaggio. Coordina 11 skill compliance + audit.

## Posizionamento competitivo

| Concorrente | Cosa fa | Cosa NON fa |
|---|---|---|
| Studio legale specializzato | Compliance completa, ma 5-15k EUR | PMI <50 dipendenti, prezzo accessibile |
| Software GRC enterprise (SAP GRC) | Tracking, reporting | Italian-specific, PMI focus |
| Consulente sicurezza (D.Lgs. 81/08) | DVR, RSPP | GDPR, AI Act, antiriciclaggio integrati |

**Tagline:** "Compliance integrata GDPR + AI Act + 81/08 + antiriciclaggio per PMI italiane, senza dover assumere 4 consulenti."

## Skill orchestrate (P08)

- `finance:audit-support` (SOX 404)
- `finance:sox-testing`
- `legal:compliance-check`
- `operations:compliance-tracking`
- `consulente-sicurezza-lavoro` (D.Lgs. 81/08)
- `it-law-privacy-ai` (GDPR, AI Act, NIS2, Data Act)
- `antitrust-concorrenza-ue`
- `fiscale-tributario-italiano`
- `verifica-requisiti-transizione5`
- `rendicontazione-agevolazioni`
- `calcolo-de-minimis`
- `titolare-effettivo-antiriciclaggio`

**Base teorica K2-AI**:
- Phil: `phil-etica` (dilemmi compliance vs business pragmatismo), `phil-logica` (audit del ragionamento normativo)
- Psy: `psy-decisioni` (bias decision-maker su rischio non-conformita)
- Math: `probabilita` (risk scoring), `statistica-applicata-bocconi` (campionamento audit)

## Workflow (7 step)

1. **Triage normative**: GDPR (sempre), AI Act (se sviluppi/usi AI), NIS2 (settori critici), 81/08 (sempre se >0 dipendenti), antiriciclaggio (settori obbligati), SOX (se gruppo USA), ISO 27001/SOC 2 (se richiesto da clienti)
2. **Gap analysis**: confronto stato attuale vs requisito, score gap 0-100 per area
3. **Roadmap remediation**: top 10 azioni prioritarie con sforzo + impatto + costo + scadenza
4. **Documentazione**: policy + procedure + registri (GDPR ROPA, RSPP nomina, DVR, registro trattamenti)
5. **Formazione**: piano formativo obbligatorio (sicurezza, GDPR, AI Act se applicabile)
6. **Monitoring**: cruscotto compliance trimestrale + alert scadenze
7. **Bridge K2-AI**: se compliance abilita bandi → `k2ai-agevolazioni`. Se rischio penale CSE/CSP → `k2ai-edilizia-pmi:psc-legale`

## Domande standard per pacchetto

### Express Compliance Check (49 EUR)
1. N. dipendenti + settore
2. Tratti dati personali clienti? Sì/No
3. Usi AI nei processi? Sì/No
4. Settore critico NIS2? (energia, banche, sanita, ICT)
5. Hai DVR e RSPP nominato?
6. Hai DPO o referente GDPR?

### Standard 499 EUR
1-6 +
7. Lista trattamenti dati (anche descrittiva)
8. Software AI usati (lista)
9. Modello infortuni 24 mesi
10. Storico audit interni
11. Certificazioni gia ottenute (ISO, SOC)
12. Vendor critici (data processor)
13. Paesi terzi data transfer (extra-UE)

### Pro 2.999 EUR
1-13 +
14. ROPA esistente (registro attivita)
15. DPIA fatte (analisi impatto)
16. AI Act high-risk system identification
17. Piano test SOX se applicabile
18. Documentazione DVR + valutazione rischi specifici

## JSON output schema

```json
{
  "tier": "express|standard|pro",
  "azienda": {"size":0,"settore":"","ai_usage":true,"data_eu":true},
  "normative_applicabili": ["GDPR","AI_Act","NIS2","81-08","Antiriciclaggio","SOX","ISO_27001"],
  "score_gap": {"gdpr":0-100,"ai_act":0-100,"nis2":0-100,"81-08":0-100,"aml":0-100},
  "score_complessivo": 0-100,
  "rischi_top10": [{"normativa":"","clausola":"","gap":"","sanzione_max_eur":0,"probabilita":0-1,"azione":""}],
  "roadmap": [{"priorita":1,"azione":"","scadenza":"","sforzo":"","costo_eur":0}],
  "documenti_da_produrre": ["ROPA","DVR","Registro_trattamenti","Policy_GDPR"],
  "formazione_obbligatoria": [{"corso":"","ore":0,"frequenza":""}],
  "scadenze_compliance": [{"adempimento":"","data":""}],
  "deliverable": {"gap_analysis_docx":"","roadmap_xlsx":"","policy_template_zip":""}
}
```

## Tiering pricing

| Versione | Prezzo | Cosa include |
|---|---|---|
| Express | 49 EUR | Score gap 0-100 + top 5 priorita |
| Standard | 499 EUR | Gap analysis full + roadmap + 5 policy template |
| Pro | 2.999 EUR | Standard + audit interno completo + ROPA + DVR + 2 call |

## Bridge K2-AI

- → `k2ai-legale` per stesura contratti DPA, NDA, AI Act compliance contracts
- → `k2ai-agevolazioni` se compliance ammissibile a Transizione 5.0/Sabatini
- → `k2ai-edilizia-pmi:psc-legale` se sicurezza cantiere
- → `k2ai-data-analytics` se ROPA richiede mappatura sistemi dati

## Test prompts

1. (forzato) "Usa k2ai-compliance per gap analysis GDPR + AI Act PMI 30 dipendenti software house Milano"
2. (cliente reale) "Devo fare il DVR ma non ho RSPP, da dove parto?"
3. (cliente reale) "Sviluppiamo un sistema AI per HR, ricade in AI Act high-risk?"
4. (cliente reale) "Il mio commercialista mi ha detto che devo registrare il titolare effettivo, cosa serve?"
5. (A/B) "compliance check PMI italiana 25 dipendenti settore sanita"

## Note implementative

- AI Act timeline: prohibitions (Feb 2025), GPAI (Aug 2025), high-risk (Aug 2026), full app (Aug 2027) — verifica sempre lo stato attuale nel descrivere obblighi
- Per AI Act high-risk: il vero filtro e' Allegato III (es. recruiting, credit scoring, infrastrutture critiche). Non ogni "AI" e' high-risk — segnala correttamente
- DVR: NON e' un documento generico, deve essere specifico per l'azienda. Diffida da template
- Antiriciclaggio: per PMI non finanziarie, l'obbligo TE e' SEMPRE applicabile (Registro Imprese)
- SOX: applica solo se gruppo USA quotato. Non spaventare PMI italiane indipendenti
