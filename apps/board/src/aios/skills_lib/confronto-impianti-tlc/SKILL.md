---
name: confronto-impianti-tlc
description: Sub-skill di VerifyBoost TLC. Confronta gli impianti elettrici e MAT (messa a terra) installati con il PE (Tav. IE.09 schema unifilare + Tav. IE.16 schema collegamenti terra) e con la DiCo D.M. 37/2008. Verifica quadri (CFE-ILIAD-ICA, MiniTD, QPL), cavi (FG16(o)R/M16, N07V-K), SPD scaricatori, dispersori, conformità CEI 64-8 (sistema TT) e CEI EN 62305 (scariche atmosferiche). Validazione del verbale MAT con Re misurato vs limite progetto. Si attiva quando l'orchestratore richiede confronto impianti.
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia energia --limit 5
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

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/energia/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Confronto impianti elettrici e MAT

## Trigger di attivazione

- Chiamata da `verifyboost-tlc-orchestrator` (Step 3)
- "Verifica impianti sito {codice}"
- "Controlla MAT", "verifica messa a terra"
- "Confronto impianti elettrici"

## Pipeline operativa

### 1. Estrai dati progetto

Dal PE iliad/Cellnex acquisisci:
- **Tav. IE.09** - Schema a blocchi utenze e dimensionamento collegamenti
- **Tav. IE.16** - Schema collegamenti di terra (con sigle T01-T12 cavi)
- Relazione di calcolo impianto elettrico (RI capitolo)
- Relazione impianto di terra
- Relazione scariche atmosferiche (CEI EN 62305)

Dati chiave:
- Tensione nominale (230V monofase / 400V trifase)
- Sistema di collegamento (TT / TN-S)
- Fornitura BT (POD, potenza impegnata)
- Quadri previsti (CFE-ILIAD-QPL, CFE-ILIAD-ICA_5G, CFE-ILIAD-miniTD_5G)
- Sezioni cavi alimentazione (4x16, 4x10, 2x16, ecc.) e materiali (FG16(o)R/M16)
- Limite Re progetto (tipico ≤ 10 Ω per TLC)
- SPD previsti (CEI EN 62305)

### 2. Estrai evidenze installato

- **DiCo D.M. 37/2008** con tabella materiali utilizzati e schema di impianto
- **Verbale MAT** con Ra misurato
- Foto quadri aperti (verifica magnetotermici, differenziali, SPD, riarmatori)
- Foto collettore principale di terra con cavi G/V etichettati

### 3. Confronto elemento per elemento

| Elemento | Progetto (PE) | Installato (DiCo + foto) | Esito tipico |
|---|---|---|---|
| Tensione nominale | 230V TT (single-phase) | DiCo | OK |
| Tipo cavi alimentazione | FG16(o)R/M16 + N07V-K | Tabella materiali DiCo | OK / NC_DOC se materiali non equivalenti |
| Marca cavi | (libera scelta installatore) | BALDASSARRI / COM-CAVI / Prysmian / similar | OK |
| Sezioni cavi | come PE | Tabella DiCo | OK / NC_GR se sottosezione |
| Tubazioni PVC | Ø125/Ø50/Ø40 pesante | Foto cantiere | OK |
| Quadro CFE-ILIAD-ICA | con SPD + magnetotermici + differenziali | Foto interno | OK |
| Quadro Mini-TD | come PE | Foto | OK |
| SPD installati | CEI EN 62305 | Foto interno quadro | OK / NC_GR se mancanti |
| Differenziali | tipo A/AC/F come da PE | Foto interno quadro | OK |
| Riarmatori automatici | continuità servizio TLC | Foto | OK / NC_DOC se non visibili |
| Dispersore terra | picchetto in acciaio | Verbale MAT | OK |
| Re misurato | ≤ Re progetto (tipico 10 Ω) | Verbale MAT | OK / NC_GR se Re > limite |
| Conduttori terra G/V 50mm² | come PE | Tabella DiCo | OK |
| Collettore principale | etichettato | Foto MAT | OK / NC_DOC |
| Etichettatura cavi MAT | sigle T01-T12 secondo tav. IE.16 | Foto | OK / NC_DOC se non etichettati |
| Finto pluviale per cavi | come PE | Foto | OK |

### 4. Verifica MAT (specifica)

Verbale MAT deve contenere:
- Ra misurato (Ω)
- Sistema (TT / TN-S)
- Tensione nominale
- Tipologia dispersore
- Conduttori (sezione e materiale)
- **Data della misura** (spesso mancante - NC_DOC tipica)
- **Modello e n. serie strumento** + **certificato taratura valido** (≤ 12 mesi) - spesso mancanti

Re tipico per sito TLC iliad/Cellnex: **5-10 Ω**. Se Ra > 10 Ω → NC_GR.

Norme CEI 64-8 sistema TT: Rt ≤ 50V/Idn (con Idn=300mA → Rt ≤ 167Ω). Quindi soglia operativa TLC (10Ω) è MOLTO conservativa - quasi sempre rispettata.

### 5. Verifica obblighi DPR 462/2001

Controllare se è presente nel dossier:
- Denuncia di messa in esercizio impianto di terra a INAIL/ASL entro 30 giorni dalla messa in esercizio (DPR 462/2001 art. 2)

Se assente → **NC_DOC** con impatto medio (rischio sanzione amministrativa in caso di controllo).

### 6. Output strutturato

```json
{
  "confronto_impianti": {
    "elementi_verificati": [...],
    "MAT": {
      "Ra_misurato_ohm": 5.4,
      "limite_progetto_ohm": 10,
      "esito_misura": "OK",
      "verbale_completezza": "PARZIALE - manca data misura, strumento, taratura",
      "denuncia_DPR_462_2001": "ASSENTE - prescrivere"
    },
    "SPD_installati": "OK - CEI EN 62305",
    "etichettatura_MAT": "OK - cavi T01-T12 etichettati come da Tav. IE.16"
  }
}
```
