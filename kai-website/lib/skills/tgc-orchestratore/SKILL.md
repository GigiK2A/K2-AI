---
name: tgc-orchestratore
description: >-
  Orchestratore Token-Gated Club (TGC) per tokenizzazione immobiliare in Italia:
  struttura SPV/SlotCo, ERC-3643 T-REX, ECSP crowdfunding, KYC/AML investitori,
  governance on-chain, distribuzione ricavi waterfall, ciclo di vita asset.
---

# TGC — Token-Gated Club Immobiliare

## Cos'è il modello TGC

Struttura per co-investimento in immobili (boutique hotel, resort, ville) tramite tokenizzazione su blockchain. Gli investitori acquistano token che rappresentano quote di una SPV (Special Purpose Vehicle) proprietaria dell'immobile.

**Vantaggi vs crowdfunding tradizionale**:
- Liquidità secondaria programmabile (MTF, OTC)
- Governance on-chain (voto token holder)
- Automazione distribuzioni (smart contract waterfall)
- Compliance KYC/AML via whitelist ERC-3643

## Struttura legale

```
INVESTITORI (token holder)
      │
      ▼
  SlotCo S.r.l. / S.r.l.s.        ← SPV dedicata per ogni immobile
  (quota token = quota SPV)
      │
      ▼
  IMMOBILE                         ← di proprietà della SlotCo
      │
      ▼
  GESTORE                          ← operatore hotel/resort (affitto/gestione)
      │
      ▼
  RICAVI NETTI → distribuzione waterfall → token holder
```

## Fasi del progetto TGC

### Fase 1 — Selezione immobile
Score 0-100 per:
- **Localizzazione** (30%): mercato turistico, accessibilità, concorrenza
- **Asset quality** (25%): stato, certificazioni, vincoli urbanistici
- **Yield potenziale** (25%): RevPAR area, occupancy storica, upside
- **Idoneità token** (20%): valorizzazione brand, esperienza vendibile, community

Target: immobili hospitality (hotel boutique, agriturismi premium, ville) con RevPAR ≥ 120€/notte, occupancy ≥ 55%.

### Fase 2 — Due diligence
- Catastale: visure, planimetrie, rendita, ipoteche
- Urbanistica: titoli edilizi, conformità, PRG, vincoli
- Tecnica: perizia strutturale, impianti, classificazione energetica
- Ambientale: amianto, radon, contaminazione
- Legale: provenienza, controversie, contratti locazione

### Fase 3 — Struttura SPV e tokenomics

```
Esempio modello:
- SPV: SlotCo S.r.l. (1 SPV per immobile)
- Token: 100 token = 100% quote SlotCo
- Prezzo token indicativo: 50.000€/token (per immobile da 5M€)
- Founding Members: 10-20 investitori iniziali
- Raccolta ECSP: fino a 5M€ (limite Reg. UE 2020/1503)
```

### Fase 4 — Token ERC-3643 (T-REX protocol)

Standard ERC-3643 su Ethereum/Polygon per security token:
- **Whitelist on-chain**: solo investitori KYC approvati possono detenere/trasferire
- **Compliance module**: blocco automatico trasferimenti a non-whitelistati
- **Identity registry**: ogni wallet linked a identità verificata

Smart contract deploy: Polygon PoS (costi gas ridotti, eco-friendly).

### Fase 5 — KYC/AML investitori

Per ogni investitore:
- Documento identità (carta/passaporto) + selfie
- Prova indirizzo (utenza < 3 mesi)
- Screening PEP (Politically Exposed Person) + sanzioni internazionali
- Fonte dei fondi (importi > 50.000€)
- FATCA/CRS per residenti esteri

Piattaforme KYC: Sumsub, Onfido, Jumio. Integrazione via API con whitelist on-chain.

### Fase 6 — Raccolta ECSP

Reg. UE 2020/1503 (Regolamento Crowdfunding Europeo):
- Raccolta fino a 5M€/anno per emittente
- KID (Key Investment Document) obbligatorio
- Periodo di riflessione 4 giorni per investitori retail
- Test adeguatezza per investitori non sofisticati
- Piattaforma ECSP autorizzata da regolatore (Banca d'Italia in IT)

### Fase 7 — Governance on-chain

Assemblee token holder con voto ponderato per quota:
- Proposte su chain (Snapshot.org o custom)
- Quorum: > 50% token per delibere ordinarie, > 66% per straordinarie
- Verbali assemblea notarizzati off-chain e hash pubblicato on-chain

### Fase 8 — Distribuzione ricavi (waterfall)

```
RICAVI LORDI immobile (affitti, revenue hospitality)
  − Costi operativi (gestione, manutenzione, PM)
  − Fee gestore (tipico 15-20% ricavi)
  − Riserva manutenzione straordinaria (5%)
  − Imposte SlotCo (IRES 24%, IRAP 3,9%)
  ─────────────────────────────────────────
  = DISTRIBUIBILE AI TOKEN HOLDER
  → Pro-quota su numero token
  → Distribuzione trimestrale/semestrale
  → Pagamento via stablecoin o bonifico SEPA
```

## KPI di progetto

| Metrica | Target | Frequenza |
|---------|--------|-----------|
| IRR investitori | > 8% netto | A scadenza |
| MOIC | > 1.8x | A scadenza |
| Occupancy immobile | > 65% | Mensile |
| NAV token | Aggiornato quarterly | Trimestrale |
| Distribuzione yield | > 4% annuo | Trimestrale |

## Uscita / liquidità

- **Secondario OTC**: token holder vendono su mercato privato regolamentato
- **Buyback SPV**: la SPV riacquista token con riserva liquidità
- **Exit immobiliare**: vendita immobile dopo holding period (tipico 5-10 anni), distribuzione capital gain pro-quota
