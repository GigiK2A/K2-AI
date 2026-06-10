---
name: produzione-deliverable-tlc
description: Sub-skill di VerifyBoost TLC. Genera i 5 deliverable formali della verifica conformità: Report DOCX 15-25 pp, Verbale PDF firmabile, Tracker XLSX 5 fogli, Dashboard HTML self-contained, JSON master. Si attiva quando l'orchestratore richiede produzione output (Step 7). Usa gli script Python pre-confezionati in references/template-deliverable/. Tutti i deliverable includono nota legale standard "documento AI-assisted, richiede firma di tecnico abilitato".
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --limit 5
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

Knowledge pack norme: (skill generalista — nessun pack)

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Produzione deliverable VerifyBoost TLC

## Trigger di attivazione

- Chiamata da `verifyboost-tlc-orchestrator` (Step 7)
- "Genera deliverable conformità sito {codice}"
- "Produci report"

## Struttura output

I deliverable vanno salvati in `outputs/VRF_{codice_sito}_{YYYYMMDD}/`:

```
outputs/VRF_FI50144_002_20260504/
├── Report_Conformita_FI50144_002_VIALE_BELFIORE.docx     (15-25 pp)
├── Verbale_Sopralluogo_FI50144_002_VIALE_BELFIORE.pdf    (3-5 pp firmabile)
├── Tracker_Scostamenti_FI50144_002_VIALE_BELFIORE.xlsx   (5 fogli)
├── Dashboard_Conformita_FI50144_002_VIALE_BELFIORE.html  (self-contained)
└── verifyboost_output.json                                (master strutturato)
```

## Pipeline operativa

### 1. Verifica prerequisiti

Devi avere già pronto:
- JSON aggregato da `matrice-scostamenti-tlc` con tutti i campi compilati
- Outputs delle 4 sub-skill di confronto
- Esiti deposito GC
- Checklist documentale

### 2. Installazione librerie

```bash
pip install python-docx openpyxl reportlab --break-system-packages --quiet
```

### 3. Salva JSON master

Salva il JSON aggregato come `verifyboost_output.json` nella cartella outputs.

### 4. Genera ogni deliverable

Usa i 4 script in `references/template-deliverable/`:

**XLSX Tracker (5 fogli):**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/references/template-deliverable/gen_xlsx.py \
    --json verifyboost_output.json \
    --out Tracker_Scostamenti_{codice}.xlsx
```

5 fogli:
1. Anagrafica sito (con dati committente, progettisti, DL)
2. Matrice scostamenti completa (filtrabile per esito)
3. Checklist documentale (24 voci standard)
4. KPI conformità (con formule LIVE per ricalcolo automatico)
5. Cronoprogramma remediation (con barre Gantt simboliche)

**DOCX Report (15-25 pp):**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/references/template-deliverable/gen_docx.py \
    --json verifyboost_output.json \
    --out Report_Conformita_{codice}.docx
```

10 sezioni:
1. Sintesi esecutiva (1 pp) per il committente
2. Inquadramento sito e intervento
3. Baseline progettato (PE + atti + GC)
4. Ricostruzione dell'installato
5. Matrice scostamenti
6. Verifica documentale
7. Indice di conformità + verdetto
8. Piano di remediation con cronoprogramma
9. Limiti della verifica e nota legale
10. Allegati e fonti documentali

**PDF Verbale (3-5 pp firmabile):**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/references/template-deliverable/gen_pdf.py \
    --json verifyboost_output.json \
    --out Verbale_Sopralluogo_{codice}.pdf
```

Sezioni:
- Anagrafica + esiti sintetici
- Lista NC rilevate con codici
- Foto chiave (campione)
- Modalità di verifica
- Nota legale
- Firme (placeholder per tecnico abilitato + DL + committente)

**HTML Dashboard:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/references/template-deliverable/gen_html.py \
    --json verifyboost_output.json \
    --out Dashboard_Conformita_{codice}.html
```

Componenti:
- Gauge SVG conformità 0-100
- Distribuzione esiti (6 KPI cards colorate)
- Semafori per macro-area
- Top 3 criticità (rivelate)
- Anagrafica sito
- Matrice scostamenti completa (con badge colorati)
- Checklist documentale (espandibile)
- Nota legale

### 5. Nota legale standard

Tutti i deliverable devono includere in chiusura:

> **Documento tecnico AI-assisted prodotto da VerifyBoost TLC** (orchestratore K2-AI). Costituisce **bozza tecnica** di due diligence che richiede:
>
> - firma di tecnico abilitato (ingegnere) per acquisire valore probatorio formale
> - verifica in loco da parte di Luca Rossi (K2A) o suo delegato
> - eventuale asseverazione se richiesta dal contratto con il Committente
>
> NON sostituisce sopralluogo fisico, asseverazione strutturale, denuncia DPR 462/2001 INAIL/ASL, né collaudi obbligatori previsti dal contratto operatore. Le valutazioni di costo e tempo della remediation sono indicative basate su prassi di mercato e vanno tarate sulle condizioni contrattuali specifiche.

### 6. QA finale obbligatorio

Prima di restituire i file all'utente, verifica:

```python
# Verifico coerenza calcolo indice
calcolo_corretto = max(0, 100 - (NC_DOC*2 + NC_SAN*5 + NC_GR*15 + NC_CR*40))
assert calcolo_corretto == indice_dichiarato

# Verifico ogni NC ha campi richiesti
for m in matrice_scostamenti:
    if m['esito'].startswith('NC'):
        assert m['norma_violata']
        assert m['azione_raccomandata']
        assert m['responsabile']

# Verifico nota legale
assert 'AI-assisted' in nota_legale
assert 'firma di tecnico abilitato' in nota_legale
```

### 7. Presentazione all'utente

Restituisci 5 link `computer://` ai file finali, in questo ordine:
1. Report DOCX (deliverable principale)
2. Verbale PDF (firmabile)
3. Tracker XLSX (per ulteriori analisi)
4. Dashboard HTML (per presentazioni)
5. JSON master (per integrazione tracker multi-sito)

Aggiungi una sintesi di 5-7 righe con:
- Indice conformità + verdetto
- Distribuzione esiti
- Top 3 criticità
- Piano remediation (tempo + costo stimato)
- Avvertenza sulla bozza
