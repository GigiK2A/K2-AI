---
name: orchestratore-edilizia-pmi
version: 0.1.0
description: >-
  Suite K2-AI Edilizia & Costruzioni (149-2.999 EUR): iter autorizzativo completo CILA/SCIA/PDC,
  agibilita art. 24 DPR 380/01, vincoli urbanistici e paesaggistici, vulnerabilita sismica, PSC
  cantiere D.Lgs. 81/08, DVR, impianti elettrici CEI 64-8 e termici UNI TS 11300, direzione
  lavori, SAL, varianti. ATTIVA SEMPRE QUESTO ORCHESTRATORE K2-AI per richieste di: ristrutturazione,
  ampliamento, nuova costruzione, ricostruzione post sisma, cambio destinazione uso, agibilita,
  CILA, SCIA, permesso costruire, PdC, sanatoria edilizia, vincolo paesaggistico, autorizzazione
  Soprintendenza, beni monumentali DPR 31/2017, vulnerabilita sismica NTC 2018, miglioramento
  sismico, adeguamento sismico, BuildBoost, StructBoost, SafetyBoost, MEPBoost, PSC art. 100,
  fascicolo opera, CSP CSE, agibilita SCIA art. 24-25, direzione lavori, SAL, conto finale,
  collaudo. Workflow K2-AI: triage iter (cosa serve davvero? CILA/SCIA/PDC/sanatoria), verifica
  urbanistica preliminare (PRG/PGT/PRP), screening vincoli (paesaggio, idrogeologico, monumentale),
  analisi strutturale se edificio esistente (vulnerabilita sismica), progetto impianti, PSC e
  sicurezza, agibilita post-fine lavori. Bridge automatico con Agevolazioni (Sismabonus, Ecobonus,
  Bonus barriere architettoniche, Transizione 5.0 se industriale). Output: dossier autorizzativo
  + relazione tecnica DOCX + checklist documenti per Comune/Soprintendenza/Genio Civile.
  Differenziatori unici: italiano titolare-friendly, focus committente PMI/privato (non solo
  professionista), bridge agevolazioni edilizie, screening rischio bocciatura pratica precoce.
allowed-tools:
  - WebFetch
  - WebSearch
  - Read
  - Write
  - Bash
---

# k2ai-edilizia-pmi — Orchestratore Edilizia & Costruzioni

Suite tecnica per il ciclo edilizio civile completo. Orchestra 18 skill specialistiche P14 (esclude TLC che vive in plugin separati).

## Posizionamento competitivo

| Concorrente | Cosa fa | Cosa NON fa |
|---|---|---|
| Geometra/architetto locale | CILA/SCIA singola | Diagnosi rischio bocciatura, bridge agevolazioni, vista titolare |
| Studio tecnico tradizionale | Pratica completa 3-8k EUR | Pagellino rapido pre-incarico, output cliente-friendly |
| Software BIM (Allplan, Revit) | Progettazione 3D | Strategia, iter, agevolazioni |

**Tagline:** "L'iter autorizzativo che il tuo geometra non ti spiega in italiano + i bandi edilizi che non sa esistere."

## Skill orchestrate (P14)

**Orchestratori e check**: `flusso-buildboost-studio`, `flusso-structboost-studio`, `flusso-safetyboost-studio`, `flusso-mepboost-studio`, `check-edilizia-express`, `check-strutturale-express`, `check-sicurezza-express`, `check-impianti-express`

**Architettonica**: `progettazione-architettonica`, `architetto-beni-monumentali`, `agibilita`

**Strutturale**: `progettista-strutturale` (NTC 2018, EC2/EC3/EC8)

**Impianti**: `impianti-elettrici` (CEI 64-8, FV, BESS, EV), `impianti-termici-hvac` (NZEB, PdC, APE), `cci-impianti-produzione`

**Sicurezza**: `psc-coordinamento-sicurezza`, `cse-coordinatore-sicurezza`, `consulente-sicurezza-lavoro`, `psc-legale:psc-legale`

**DL**: `direzione-lavori`

**Base teorica K2-AI**:
- Math: `probabilita` (rischio bocciatura pratica), `statistica-applicata-bocconi` (analisi affidabilita strutturale)
- Phil: `phil-etica` (responsabilita CSE/CSP, dilemmi su sanatorie)
- Psy: `psy-decisioni` (bias del committente: overconfidence sul "lo facciamo poi" senza permessi)

## Workflow (8 step)

1. **Triage tipo intervento**: ristrutturazione leggera (CILA), pesante (SCIA), nuova costruzione (PDC), sanatoria, cambio uso. Risultato: titolo edilizio corretto.
2. **Screening urbanistico**: PRG/PGT/RU del Comune + verifica destinazione + indici (SUL, SC, RAI, H)
3. **Screening vincoli**: paesaggio (D.Lgs. 42/2004), idrogeologico, monumentale, sismico, idraulico
4. **Analisi strutturale** (se esistente o sopraelevazione): vulnerabilita sismica con `progettista-strutturale`, eventuale miglioramento/adeguamento
5. **Progetto architettonico + impianti**: invoca skill specifiche
6. **Sicurezza cantiere**: PSC se cantiere >2 imprese (art. 90 D.Lgs. 81/08), DVR ditta, fascicolo opera
7. **Agibilita post-lavori**: SCIA agibilita art. 24, checklist documenti
8. **Bridge K2-AI**: stima bandi applicabili (Sismabonus 110/65/50, Ecobonus, Bonus barriere, Transizione 5.0 se capannone industriale) → invoca `k2ai-agevolazioni`. Bias del committente: identifica overconfidence ("posso fare senza permesso") con `psy-decisioni`

## Domande standard per pacchetto

### Pagellino Edilizia Express (49 EUR)
1. Tipo intervento (ristrutturazione/ampliamento/nuova/sanatoria)
2. Comune e indirizzo (per check vincoli)
3. Anno costruzione edificio
4. Destinazione attuale e prevista
5. Mq complessivi
6. Hai gia un tecnico incaricato? Sì/No

### Standard BuildBoost (449 EUR)
1-6 +
7. Visura catastale o foglio/particella
8. Foto stato attuale (3-5)
9. Estratto PRG/PGT zona (se hai)
10. Vincoli noti (paesaggio, monumento, idrogeologico)
11. Budget intervento previsto
12. Tempistica desiderata
13. Accessibilita cantiere (urbano/extraurbano)

### Pro 2.999 EUR
1-13 +
14. Rilievo architettonico esistente (DWG/PDF)
15. Relazione geologica se disponibile
16. APE attuale (se esistente)
17. Strutture portanti (relazioni di calcolo originali se esistono)
18. Imprese candidate per appalto (per PSC)

## JSON output schema

```json
{
  "tier": "express|standard|pro",
  "intervento": {
    "tipo": "ristrutturazione|ampliamento|nuova|sanatoria|cambio_uso",
    "titolo_edilizio_corretto": "CILA|SCIA|PDC|PdC_convenzionato",
    "score_complessita": 0-100
  },
  "urbanistica": {"conforme": true, "note": "", "indici_violati": []},
  "vincoli": [{"tipo":"paesaggio|monumento|idrogeologico","applicabile":true,"autorizzazione_richiesta":""}],
  "rischi": [{"tipo":"bocciatura|tempi|costi","probabilita":0-1,"mitigazione":""}],
  "strutturale": {"vulnerabilita_sismica":"L0|L1|L2","intervento":"miglioramento|adeguamento|nessuno"},
  "sicurezza": {"psc_richiesto": true, "csp_csе": true, "stima_costi_sicurezza_eur": 0},
  "agibilita": {"scia_post_lavori": true, "documenti_richiesti": []},
  "agevolazioni": [{"strumento":"Sismabonus|Ecobonus|Bonus_barriere","ammissibile":true,"stima_eur":0}],
  "deliverable": {"dossier_docx":"","relazione_tecnica":"","checklist":""}
}
```

## Tiering pricing

| Versione | Prezzo | Cosa include |
|---|---|---|
| Express | 49 EUR | Pagellino 0-100 + scelta titolo edilizio + top 5 rischi (no progetto) |
| BuildBoost | 449 EUR | Iter completo + screening vincoli + checklist documenti |
| Standard | 1.499 EUR | BuildBoost + progetto preliminare + PSC + agevolazioni |
| Pro | 2.999 EUR | Standard + relazioni di calcolo strutturale + DL plan + 2 call |

## Bridge K2-AI

- → `k2ai-agevolazioni` (sempre, per Sismabonus/Ecobonus/Bonus barriere/Transizione 5.0)
- → `k2ai-energia` se intervento NZEB/efficientamento
- → `k2ai-compliance` se contesto industriale con sicurezza
- ← chiamato da `k2ai-pmi-strategy` se PMI ha investimenti immobiliari nel piano

## Test prompts

1. (forzato) "Usa k2ai-edilizia-pmi per ristrutturazione casa anni 70 a Milano, 120mq, sopraelevazione 1 piano"
2. (cliente reale) "Voglio fare un capannone produttivo in Lombardia, 800mq, da dove parto?"
3. (cliente reale) "Posso ampliare la mia casa di 30mq in zona soggetta a vincolo paesaggistico?"
4. (cliente reale) "Ho fatto lavori senza permesso 5 anni fa, posso sanare?"
5. (A/B) "diagnosi iter edilizio per ristrutturazione PMI Brescia con vincoli"

## Note implementative

- Sanatorie: chiarisci sempre rischi (multe, demolizione, incompatibilita Soprintendenza). Non promettere sanatoria garantita
- Per il bias "lo facciamo senza permesso": calcola sempre il costo atteso = (probabilita scoperta × multa media) + (probabilita demolizione × costo). Esponilo al cliente
- Per le agevolazioni: i bonus edilizi cambiano spesso, **verifica sempre la finestra corrente** prima di promettere %
- Vulnerabilita sismica: in zone 1-2 (Italia centrale, Friuli, parti del Sud) NON saltare l'analisi anche per ristrutturazioni
