---
name: matrice-scostamenti-tlc
description: Sub-skill di VerifyBoost TLC. Costruisce la matrice degli scostamenti, calcola l'indice di conformità globale 0-100 e assegna il verdetto su 5 fasce. Aggrega gli output delle 4 sub-skill di confronto (strutturale, architettonico, RF, impianti) + checklist documentale + esiti deposito GC. Si attiva quando l'orchestratore richiede aggregazione finale degli esiti.
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


# Matrice scostamenti + indice conformità + verdetto

## Trigger di attivazione

- Chiamata da `verifyboost-tlc-orchestrator` (Step 5-6)
- "Calcola indice conformità sito {codice}"
- "Costruisci matrice scostamenti"

## Pipeline operativa

### 1. Aggregazione

Aggrega gli output di:
- `confronto-strutturale-tlc`
- `confronto-architettonico-tlc`
- `confronto-rf-tlc`
- `confronto-impianti-tlc`
- `baseline-deposito-gc-tlc` (anomalie formali GC se presenti)
- Checklist documentale (24 voci standard)

### 2. Classificazione voci

Ogni voce deve avere uno dei 6 esiti:

| Esito | Significato | Punti penalità |
|---|---|---|
| OK | Conforme nei dati nominali | 0 |
| OK_TOL | Fuori dato nominale ma dentro tolleranza | 0 |
| NC_DOC | Non conformità solo documentale (recupero possibile) | -2 |
| NC_SAN | Non conformità sanabile (variante in opera, art. 6-bis DPR 380) | -5 |
| NC_GR | Non conformità grave (difformità sostanziale - struttura/sicurezza/vincolo) | -15 |
| NC_CR | Non conformità critica (rischio agibilità, sicurezza pubblica) | -40 |

### 3. Per ogni voce raccogli

- ID univoco (es. NC001, OK002, OK_TOL01)
- Macro-area (struttura, impianti, paesaggio, RF, documentale)
- Voce (descrizione sintetica)
- Esito (uno dei 6)
- **Norma puntuale violata** (per le NC) - es. NTC 2018 §X.Y.Z, CEI 64-8 art., DPR 31/2017
- Impatto sulla sicurezza (NULLO / BASSO / MEDIO / ALTO)
- Azione raccomandata
- Responsabile (Impresa, DL, Operatore, Committente)
- Tempo remediation (giorni)
- Costo remediation (€)
- Rischio se non sanata

### 4. Calcolo indice di conformità globale

```
Indice = max(0, 100 - (NC_DOC × 2 + NC_SAN × 5 + NC_GR × 15 + NC_CR × 40))
```

### 5. Assegnazione verdetto

| Indice | Verdetto |
|---|---|
| 90-100 | IDONEO ALL'ESERCIZIO |
| 70-89 | IDONEO CON PRESCRIZIONI DOCUMENTALI |
| 50-69 | IDONEO CON ADEGUAMENTI MINORI |
| 30-49 | NON IDONEO - ADEGUAMENTI OBBLIGATORI |
| <30 | NON IDONEO - RIPROGETTAZIONE O DEMOLIZIONE PARZIALE |

### 6. Top 3 criticità

Estrai le 3 voci con maggiore impatto sostanziale (priorità: NC_CR > NC_GR > NC_SAN > NC_DOC con maggior rischio_se_non_sanata) per il riassunto esecutivo.

### 7. Piano remediation strutturato

Articola in fasi (tipico 3-4 fasi):
- Fase 1 (prima settimana): NC_DOC con errata corrige rapide
- Fase 2 (settimane 2-3): recupero documentale (verbali TX/RF, PSP-CEM)
- Fase 3 (settimana 4): comunicazioni a enti (SABAP, INAIL/ASL)
- Fase 4 (eventuale): sopralluogo DL per conferme visive

Stima tempo (giorni) e costo (€) per ogni fase.

### 8. Output JSON

```json
{
  "indice_conformita": {
    "calcolo": {
      "OK": 12, "OK_TOL": 3,
      "NC_DOC": 9, "NC_SAN": 0, "NC_GR": 0, "NC_CR": 0,
      "totale_voci_valutate": 24
    },
    "formula": "100 - (9×2 + 0×5 + 0×15 + 0×40)",
    "calcolo_dettagliato": "100 - 18 = 82",
    "indice_globale": 82,
    "verdetto": "IDONEO CON PRESCRIZIONI DOCUMENTALI",
    "fascia": "70-89",
    "interpretazione": "..."
  },
  "matrice_scostamenti": [...],
  "top_3_criticita": [...],
  "piano_remediation": {
    "tempo_complessivo_giorni": 35,
    "costo_complessivo_stimato_eur": "300-2700",
    "fasi": [...]
  }
}
```

## Lessons learned

- **L'indice non è un voto.** È uno strumento di prioritizzazione - 9 NC_DOC non significa "sito a rischio", significa "9 errata corrige da fare". Comunicarlo correttamente al committente.
- **Le NC strutturali (NC_GR e NC_CR) sono rare** quando il sito è stato regolarmente progettato e depositato al GC. La maggior parte delle NC sono documentali (NC_DOC).
- **Mai chiudere a 100/100.** Il pragmatismo richiede sempre 1-2 OK_TOL (sequenze temporali, sovradimensionamenti positivi, ecc.) - un sito reale non è mai un PE perfetto.
