---
name: orchestratore-tokenizzazione
version: 0.1.0
description: >-
  Suite K2-AI Real Estate Tokenization (1.999-19.999 EUR + setup SPV): TGC Token-Gated Club,
  tokenizzazione asset immobiliari italiani via SPV, ECSP Reg. UE 2020/1503, smart contract
  ERC-3643 T-REX (compliance on-chain), MiCAR, DLT Pilot Regime, due diligence immobiliare,
  business plan 14 anni con waterfall distribuzioni, KYC/AML investitori, governance assemblee
  on-chain, secondary market MTF/OTC, Notti Club token (utility ricettiva). ATTIVA SEMPRE QUESTO
  ORCHESTRATORE K2-AI per: tokenizzazione immobiliare, real estate token, ECSP crowdfunding,
  ERC-3643 T-REX, MiCAR compliance, DLT Pilot, SPV tokenization, fractional ownership immobiliare,
  TGC Token-Gated Club, founding members onboarding, waterfall distribuzioni token holder, Notti
  Club token ricettivo, secondary market token immobiliare, smart contract audit, KYC/AML
  whitelist on-chain, governance assemblee, NAV calcolo, lifecycle SlotCo SPV, multiasset
  tokenization. Workflow K2-AI: scoring immobile (yield/localizzazione/tokenizzabilita), DD
  completa, business plan 14y, scelta ECSP optimal, smart contract design + audit, KYC/AML setup,
  tokenomics dual token, founding members + pitch personalizzati profilo investitore (HNW/family
  office/tech), prelancio + governance + NAV + secondary. Differenziatori unici: prima soluzione
  PMI italiana per tokenization end-to-end con compliance MiCAR + DLT Pilot, integrazione SPV
  italiano + smart contract Ethereum, focus ricettivo (Notti Club token).
allowed-tools:
  - WebFetch
  - WebSearch
  - Read
  - Write
  - Bash
---

# k2ai-tokenizzazione — Orchestratore Real Estate Tokenization

Coordina la suite TGC (21 skill) per tokenizzazione immobiliare end-to-end conforme MiCAR + DLT Pilot Regime.

## Posizionamento competitivo

Mercato emergente (2024-2026 in espansione). Concorrenti: piattaforme estere (RealT US, Tangany DE), advisor blockchain generici. K2-AI vince perche: PMI italiana, compliance italiana (SPV + ECSP italiano), focus ricettivo (asset turistico = Notti Club model unico).

**Tagline:** "Tokenizzi un immobile italiano in modo legale (MiCAR + DLT Pilot) e vendibile (ECSP) — dal scoring asset all'assemblea on-chain."

## Skill orchestrate (P16, 21 skill TGC)

**Selezione + DD**: `tgc-selezione-immobili`, `tgc-due-diligence`, `flusso-investimento-immobiliare`, `perizia-estimo-immobiliare`

**Business plan + governance**: `tgc-business-plan` (14y), `tgc-governance`, `tgc-slotco-lifecycle`, `tgc-waterfall-distribuzioni`

**Token + smart contract**: `smart-contract-tokenomics`, `tgc-audit-smartcontract`, `tokenizzazione-immobiliare`

**Investitori**: `tgc-founding-members`, `tgc-pitch-designer`, `tgc-kyc-aml`, `tgc-prelancio`, `investor-relations-spv`, `tgc-csp-selector`

**Mercato e contratti**: `tgc-secondary-market`, `tgc-multiasset`, `tgc-notti-club`, `ecsp-regolamento-offerta`, `contratti-investimento-token`, `ss-trust-italiano`

**Master**: `tgc-orchestratore` (gia presente, K2-AI lo wrappa con brand)

**Base teorica K2-AI**:
- Bocconi: `corporate-finance` (DCF immobiliare, IRR/MOIC), `finanza-quantitativa-bocconi`
- Math: `probabilita` (rischio scenari NAV), `statistica-applicata-bocconi`
- Phil: `phil-etica` (trasparenza investitori retail vs accreditati), `phil-logica` (verifica claim ROI)
- Psy: `psy-decisioni` (FOMO investitore retail crypto/RE), `psy-personalita` (matching pitch a profilo HNW vs tech-savvy)

## Workflow (10 step)

1. **Scoring asset**: `tgc-selezione-immobili` (0-100 su yield, location, tokenizzabilita)
2. **DD**: `tgc-due-diligence` + `perizia-estimo-immobiliare` (catastale, urbanistica, tecnica, ambientale)
3. **Business plan 14y**: `tgc-business-plan` con scenari + waterfall ricavi
4. **Tokenomics**: `smart-contract-tokenomics` dual-token (Quota Club + Notti Club se ricettivo)
5. **ECSP scelta**: `tgc-csp-selector` (CrowdFundMe, MamaCrowd, ecc.)
6. **Smart contract audit**: `tgc-audit-smartcontract` pre-deploy mainnet
7. **KYC/AML setup**: `tgc-kyc-aml` whitelist on-chain ERC-3643
8. **Founding Members**: `tgc-founding-members` + `tgc-pitch-designer` profilo (HNW/family office/tech)
9. **Prelancio + governance**: `tgc-prelancio` + `tgc-governance`
10. **Lifecycle**: `tgc-slotco-lifecycle` (NAV, assemblee, distribuzioni `tgc-waterfall-distribuzioni`, secondary `tgc-secondary-market`, multi-asset `tgc-multiasset`)

## Domande standard per pacchetto

### TGC Express (199 EUR — pre-feasibility)
1. Tipo asset (residenziale/ricettivo/commerciale/misto)
2. Comune + indirizzo
3. Valore stimato/perizia
4. Yield atteso annuo %
5. Capitale da raccogliere via tokenization (target)
6. Profilo investitori target (retail/accreditati/misto)

### Standard 4.999 EUR (full feasibility + DD)
1-6 +
7. Visure catastali + urbanistiche
8. Storico ricavi se gia operativo (es. ricettivo)
9. Vincoli paesaggio/monumento
10. Forma giuridica attuale (SPV gia esistente?)
11. Esperienza team (track record real estate?)
12. Timeline desiderata (quando vuoi raccogliere?)
13. ECSP gia identificato? Sì/No

### Pro 19.999 EUR (end-to-end fino al lancio)
1-13 +
14. Documentazione legale completa (atto, regolamento condominiale)
15. Business plan attuale (se gia esiste)
16. Founding members candidati (lista contatti)
17. Budget marketing prelancio
18. Audit firm preferita per smart contract
19. Studio legale tokenization preferito (o lo selezioniamo)

## JSON output schema

```json
{
  "tier": "express|standard|pro",
  "asset": {"tipo":"","localizzazione":"","valore_eur":0,"yield_atteso":0},
  "tokenizability_score": 0-100,
  "feasibility": {"micar_compliance":true,"dlt_pilot_applicable":false,"ecsp_required":true},
  "business_plan_14y": {"capex":0,"opex_y1":0,"irr":0,"moic":0,"distribuzione_y1":0},
  "tokenomics": {"struttura":"dual_token","quota_club":{"supply":0,"price":0},"notti_club":{"supply":0}},
  "ecsp_consigliato": {"piattaforma":"","fee":0},
  "founding_members": {"target_n":0,"profilo_dominante":""},
  "smart_contract": {"standard":"ERC-3643","audit_firm":""},
  "roadmap_lancio": [{"fase":"","mese":0,"deliverable":""}],
  "rischi_top5": [],
  "deliverable": {"feasibility_docx":"","bp_xlsx":"","whitepaper":"","sc_repo":""}
}
```

## Tiering pricing

| Versione | Prezzo | Cosa include |
|---|---|---|
| Express | 199 EUR | Pre-feasibility 0-100 + verdetto MiCAR ammissibile sì/no |
| Standard | 4.999 EUR | Feasibility full + DD + BP 14y + tokenomics + scelta ECSP |
| Pro end-to-end | 19.999 EUR + revenue share | Tutto fino al lancio: smart contract audited + KYC/AML setup + founding members onboarding + prelancio |

## Bridge K2-AI

- → `k2ai-edilizia-pmi` se asset richiede ristrutturazione/cambio uso
- → `k2ai-hospitality` se asset ricettivo (uso Notti Club token)
- → `k2ai-legale` per contratti SPV + investimento + GDPR
- → `k2ai-compliance` per AML obbligo
- → `k2ai-agevolazioni` se asset ammissibile a Sismabonus/Ecobonus pre-tokenization
- ← chiamato da `k2ai-pmi-strategy` se exit via tokenization è opzione strategica

## Test prompts

1. (forzato) "Usa k2ai-tokenizzazione per villa di lusso 12 stanze in Toscana, valore 4M, vogliamo raccogliere 1.5M tramite token"
2. (cliente reale) "Posso tokenizzare il mio agriturismo per attirare investitori internazionali?"
3. (cliente reale) "Differenza tra ECSP e DLT Pilot Regime per la mia operazione?"
4. (cliente reale) "Voglio fare TGC con immobile boutique hotel Roma, da dove parto?"
5. (A/B) "tokenizzazione asset immobiliare italiano MiCAR compliance"

## Note implementative

- MiCAR (Reg. UE 2023/1114): in vigore dal 2024 per crypto-asset, **ATTENZIONE** alla classificazione token (asset-referenced vs e-money vs other)
- DLT Pilot Regime (Reg. UE 2022/858): permette uso DLT per strumenti finanziari, ma poche istituzioni partecipano — NON promettere DLT Pilot se non sai
- ECSP: la piattaforma DEVE avere licenza CONSOB. Senza, è abusivismo finanziario
- KYC/AML obbligatorio: ERC-3643 T-REX permette compliance on-chain (whitelist)
- Conflitti: se il cliente fa proposta non in linea con MiCAR, bloccalo. Tokenization non legale = rovina del committente
- Notti Club token (utility ricettiva): NO security se ben strutturato — verifica con `phil-logica` che il token NON dia diritto a profitto futuro (=> sarebbe security)
