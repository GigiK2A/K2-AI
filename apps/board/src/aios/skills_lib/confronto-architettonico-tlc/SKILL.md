---
name: confronto-architettonico-tlc
description: Sub-skill di VerifyBoost TLC. Confronta gli aspetti architettonici e paesaggistici dell'installato con il progetto (A02 deposito GC + Tavole architettoniche PE: planimetria, pianta, prospetti stato attuale/progetto/confronto). Verifica posizione palina/torrino, mascheramento (finto camino), colore RAL, integrazione con edifici limitrofi, riposizionamento elementi esistenti (parabole condominiali), conformità a vincoli SABAP/UNESCO. Si attiva quando l'orchestratore richiede confronto architettonico.
---








<!-- LEGAL-EVIDENCE-BLOCK-V7 -->
## Tools Normattiva + Giurisprudenza (CCost + CGUE + CEDU + CdS/TAR + Cassazione) — verifica obbligatoria

Hai 5 toolkit locali + 1 lookup live per consulenza legale evidence-based:
- **Normattiva** — ~42.000 norme italiane (DB FTS5)
- **Corte Costituzionale** — 22.258 pronunce + 46.154 massime (1956→2026)
- **Corte di Giustizia UE + Tribunale UE** — ~38.000 cause (2005→2026)
- **Corte EDU (Strasburgo)** — 10.000 casi contro l'Italia (2001→2026), con traduzioni ufficiali Min. Giustizia
- **Giustizia Amministrativa** — Consiglio di Stato + TAR + CGARS (2024→2025, in espansione)
- **Cassazione (LIVE pubblica)** — SentenzeWeb italgiure, accesso pubblico zero-setup (~188k civ + ~236k pen, testo integrale)

### Workflow obbligatorio

**A. Norme italiane**
```bash
python3 ~/normattiva_ai/tools/cita.py "<es. D.Lgs 81/2008>"
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia urbanistica_edilizia --limit 5
```

**B. Corte Costituzionale**
```bash
python3 ~/giurisprudenza_ai/tools/cross_norma_sentenza.py "art. 32 Cost." --limit 10
python3 ~/giurisprudenza_ai/tools/rag_giurisprudenza.py "<query>" --anno-da 2018
python3 ~/giurisprudenza_ai/tools/cita_sentenza.py "Corte cost. N/AAAA"
```

**C. CGUE (diritto UE / GDPR / appalti / antitrust / privacy / dogana)**
```bash
python3 ~/cgue_ai/tools/cross_norma_cgue.py "art. 101 TFUE" --limit 10
python3 ~/cgue_ai/tools/cross_norma_cgue.py "Reg. UE 679/2016"        # GDPR
python3 ~/cgue_ai/tools/rag_cgue.py "<query>" --anno-da 2018
python3 ~/cgue_ai/tools/cita_cgue.py "C-16/05"
```

**D. CEDU (diritti fondamentali / equo processo art. 6 / detenzione art. 3 / proprietà P1-1 / vita privata art. 8)**
```bash
python3 ~/cedu_ai/tools/cross_articolo_cedu.py "art. 6" --solo-importanti --limit 10
python3 ~/cedu_ai/tools/rag_cedu.py "<query>" --anno-da 2015
python3 ~/cedu_ai/tools/cita_cedu.py "63386/16"      # numero di ricorso
```

**E. Giustizia Amministrativa — CdS/TAR (appalti, edilizia, accesso atti, SCIA, silenzio, espropri, PA)**
```bash
python3 ~/gad_ai/tools/cross_norma_gad.py "D.Lgs 36/2023" --limit 10   # appalti
python3 ~/gad_ai/tools/cross_norma_gad.py "Legge 241/1990"             # procedimento
python3 ~/gad_ai/tools/rag_gad.py "<query>" --sede cds --anno-da 2024
```

**F. Cassazione (LIVE pubblica — civile/penale, legittimità) — zero setup**
```bash
# Verifica/recupera un precedente di Cassazione (SentenzeWeb pubblico, nessun login)
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023"
python3 ~/cassazione_ai/tools/cassazione_lookup.py --q "licenziamento giusta causa" --sezione civ --rows 5
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023" --full   # testo integrale
python3 ~/cassazione_ai/tools/check_cassazione.py --file <output.md>                        # verifica citazioni
```
Copre la finestra pubblica (~ultimi 5 anni + storico parziale). Se una citazione MANCA può essere fuori finestra; dillo, non inventare la massima.

**G. Verifica finale (prima del deliverable, su ogni file MD prodotto)**
```bash
python3 ~/normattiva_ai/tools/check_citazioni.py --file <output.md> --strict
python3 ~/giurisprudenza_ai/tools/check_sentenze.py --file <output.md> --strict
python3 ~/cgue_ai/tools/check_cgue.py --file <output.md> --strict
python3 ~/cedu_ai/tools/check_cedu.py --file <output.md> --strict
python3 ~/gad_ai/tools/check_gad.py --file <output.md> --strict
```

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/urbanistica_edilizia/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Confronto architettonico TLC

Confronta installato vs progetto architettonico (PE iliad/Cellnex e A02 deposito GC).

## Trigger di attivazione

- Chiamata da `verifyboost-tlc-orchestrator` (Step 3)
- "Verifica architettonico", "controlla mascheramento", "confronto layout sito"

## Pipeline operativa

### 1. Acquisisci tavole di riferimento

Dal PE iliad standard usa le **tavole 16-26**:
- Tav. 16 - Aerofotogrammetrico
- Tav. 17 - Estratto catastale
- Tav. 18 - Planimetria generale stato attuale (1:500)
- Tav. 19 - Pianta stato attuale (1:100) con quote +20.18m lastrico, +23.11m torrino
- Tav. 20 - Prospetto stato attuale
- Tav. 21 - Planimetria stato di progetto
- **Tav. 22 - Pianta stato di progetto (1:100)** ← VISTA CHIAVE con dettagli palina, antenne, parabole, apparati
- **Tav. 23 - Prospetto stato di progetto** ← integrazione finto camino
- Tav. 24-26 - Stato di confronto (demolizioni gialle + costruzioni rosa)

Dal deposito GC usa il fascicolo **A02 - Progetto Architettonico** (tipicamente identico al PE).

### 2. Verifica elemento per elemento

| Elemento | Riferimento progetto | Verifica installato | Esito tipico |
|---|---|---|---|
| Posizione palina sul torrino | Tav. 22 - sopra torrino vano scale/ascensore | Foto file accesso sito + IMG-20221222-WA0010 | OK |
| Quota base antenna | B.A. dichiarata in tav. 22 (es. 26.90m) | Coerente con quota dichiarata | OK |
| Quota centro elettrico parabole | C.E. dichiarata in tav. 22 (es. 26.40m) | Coerente | OK |
| Mascheramento (finto camino / palo poligonale / nessuno) | Tav. 22 + 23 | Foto cantiere | OK / NC_GR se difforme |
| Forma e colore mascheramento | Tav. 22 (cilindro Ø1.6m bianco vetroresina) | Foto cantiere visibili | OK / NC_DOC se RAL non documentato |
| Integrazione architettonica | Art. 66 c.4 NTA RU FI o equivalente | Foto vista panoramica | OK |
| Parabola condominiale (riposizionamento) | Tav. 19 (esistente) → Tav. 23 (riposizionata) | Foto post-intervento | OK |
| Antenna GPS (esterna o interna mascheramento) | Particolare antenne tav. 22 | Foto IMG_20230116_102338 | OK |
| Apparati alla base palina | Tav. 22 - sul lastrico, area delimitata | Foto IMG_20230116_102103 | OK |
| Paletti amovibili catena bianco-rossa | Tav. 22 | Foto fine lavori | OK |
| Scala SOLL/GlideLoc rimovibile | Tav. 22 - "ancoraggi in gronda scala removibile" | Foto + check list SOLL | OK |
| Finto pluviale per cavi | Tav. 22 | Foto IMG-20221222-WA0017 | OK |
| Percorso interrato fibra ottica | Tav. 21 | Pozzetto F.O. visibile | OK / NC_DOC |
| Vincolo paesaggistico - rispetto prescrizioni SABAP | Autorizzazione paesaggistica n. .../yyyy | Da incrociare con .msg autorizzazione | OK / NC_DOC |
| Vincolo UNESCO buffer zone | Comunicazione fine lavori a SABAP | Verifica obbligo | NC_DOC se assente |

### 3. Verifica RAL

Il colore del mascheramento è una prescrizione tipica della SABAP. Cerca nel pacchetto autorizzazione paesaggistica:
- Numero autorizzazione (es. n. 1504/2022)
- Data
- Eventuali prescrizioni grafiche su RAL/colore

Se RAL prescritto MA non visivamente verificabile come compatibile con foto installato → **NC_DOC** con prescrizione "verifica colorimetrica formale in loco".

### 4. Esiti tipici

Per siti TLC iliad standard rooftop con mascheramento finto camino bianco vetroresina:
- Mascheramento installato CONFORME nel 95% dei casi
- Le NC architettoniche sono quasi sempre **NC_DOC** (colore RAL non formalmente prescritto/documentato, comunicazione fine lavori SABAP mancante) - non NC strutturali

### 5. Output strutturato

```json
{
  "confronto_architettonico": {
    "elementi_verificati": [
      {
        "elemento": "posizione_palina",
        "progetto": "Sul torrino vano scale/ascensore",
        "installato_evidenza": "Foto file accesso sito",
        "esito": "OK"
      },
      {
        "elemento": "mascheramento_finto_camino",
        "progetto": "Cilindrico Ø1.6m bianco vetroresina",
        "installato_evidenza": "IMG-20221222-WA0010",
        "esito": "OK"
      }
    ],
    "rispetto_vincoli": {
      "SABAP_paesaggistica": "OK - autorizzazione n.1504/2022 acquisita - RAL non formalmente verificato",
      "UNESCO_buffer_zone": "OK - rispetto previsto in autorizzazione",
      "SOPRINTENDENZA_comunicazione_fine_lavori": "NC_DOC - mancante in cartella documenti"
    }
  }
}
```
