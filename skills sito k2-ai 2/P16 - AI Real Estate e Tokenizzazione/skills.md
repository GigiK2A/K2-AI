# P16 — AI Real Estate & Tokenizzazione
## Servizio K2-AI
Agenti AI per investimenti immobiliari, tokenizzazione di asset reali, strutturazione SPV, crowdfunding ECSP e gestione del ciclo di vita degli investitori.

## Skill Claude disponibili

### Token-Gated Club (TGC) — Orchestratore e Fasi
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:tgc-orchestratore` | Orchestratore master TGC: coordina tutte le skill specialistiche |
| `anthropic-skills:tgc-selezione-immobili` | Scoring 0-100 immobili: localizzazione, yield, idoneità tokenizzazione |
| `anthropic-skills:tgc-due-diligence` | Due diligence immobiliare: catastale, urbanistica, tecnica, ambientale |
| `anthropic-skills:tgc-business-plan` | Business plan finanziario 14 anni: CAPEX, OPEX, IRR, MOIC, scenari |
| `anthropic-skills:tgc-founding-members` | Identificazione, approccio e onboarding dei Founding Members |
| `anthropic-skills:tgc-pitch-designer` | Pitch personalizzati per profilo investitore (HNW, family office, tech…) |
| `anthropic-skills:tgc-prelancio` | Strategia pre-lancio: lista d'attesa, teaser, drip campaign |
| `anthropic-skills:tgc-kyc-aml` | KYC/AML investitori, whitelist on-chain ERC-3643, screening PEP |
| `anthropic-skills:tgc-governance` | Assemblee token holder, voto on-chain/off-chain, quorum, verbali |
| `anthropic-skills:tgc-notti-club` | Gestione Notti Club token: allocazione, prenotazioni, redemption |
| `anthropic-skills:tgc-waterfall-distribuzioni` | Calcolo distribuzioni ai token holder con waterfall ricavi → costi → fee |
| `anthropic-skills:tgc-slotco-lifecycle` | Ciclo di vita SlotCo: scadenze legali, NAV, assemblee, exit |
| `anthropic-skills:tgc-secondary-market` | Liquidità secondaria: MTF, OTC, buyback, lock-up management |
| `anthropic-skills:tgc-multiasset` | Replicazione modello TGC: Slot 2/3/4+, portfolio multi-asset |
| `anthropic-skills:tgc-csp-selector` | Selezione piattaforma ECSP ottimale per raccolta crowdfunding |
| `anthropic-skills:tgc-audit-smartcontract` | Security audit smart contract ERC-3643 pre-deployment mainnet |

### Normativa e Contratti
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:tokenizzazione-immobiliare` | Tokenizzazione RE: blockchain, ERC-3643, MiCAR, DLT Pilot, SPV, ECSP |
| `anthropic-skills:smart-contract-tokenomics` | Tokenomics ERC-3643 T-REX, dual-token model, governance on-chain |
| `anthropic-skills:ecsp-regolamento-offerta` | Regolamento di Offerta ECSP, KID, risk factors, obblighi informativi |
| `anthropic-skills:contratti-investimento-token` | Subscription agreement, patti parasociali SPV, lock-up, side letter |
| `anthropic-skills:investor-relations-spv` | Comunicazioni periodiche investitori: report NAV, assemblee, newsletter |

### Investimento Immobiliare Tradizionale
| Skill | Descrizione |
|-------|-------------|
| `anthropic-skills:flusso-investimento-immobiliare` | Orchestratore: perizia + DCF + fiscalità + urbanistica + tokenizzazione |
| `anthropic-skills:perizia-estimo-immobiliare` | Perizia immobiliare: MCA, capitalizzazione, DCF, OMI, superficie commerciale |
| `anthropic-skills:property-management-revenue` | Revenue management ricettivo: RevPAR, ADR, pricing, OTA, P&L hospitality |
| `anthropic-skills:ss-trust-italiano` | Società semplice e trust: protezione patrimoniale, passaggio generazionale |

## Come usarle
Es: "voglio tokenizzare un immobile, da dove parto?" → `anthropic-skills:tgc-orchestratore`
Es: "fai la due diligence di questo immobile" → `anthropic-skills:tgc-due-diligence`
Es: "calcola la distribuzione ai token holder di questo trimestre" → `anthropic-skills:tgc-waterfall-distribuzioni`
