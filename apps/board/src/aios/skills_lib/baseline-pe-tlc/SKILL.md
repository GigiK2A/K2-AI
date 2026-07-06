---
name: baseline-pe-tlc
description: Sub-skill di VerifyBoost TLC. Estrae la baseline progettuale dal Progetto Esecutivo (PE) di un sito TLC italiano, supporta operatori iliad / Cellnex / INWIT / WindTre / towerco. Si attiva quando l'orchestratore VerifyBoost richiede la lettura del PE, oppure quando l'utente dice "leggi il PE del sito {codice}", "estrai dati progetto", "baseline progettuale {codice}". Output JSON strutturato con anagrafica sito, vincoli, struttura (palina/puntoni/baggioli/grigliato/UPN180), impianti, RF/TLC (antenne/parabole/azimut/tilt), paesaggio, atti autorizzativi.
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


# Baseline PE TLC

Estrai la baseline progettuale dal Progetto Esecutivo di un sito TLC italiano.

## Trigger di attivazione

- Chiamata dall'orchestratore VerifyBoost TLC (Step 1)
- "Leggi il PE del sito {codice}"
- "Estrai dati progetto sito {codice}"
- "Baseline {codice}"

## Flusso operativo

### 1. Identifica l'operatore

Dal codice sito determina l'operatore:
- `FI*****_***`, `RM*****_***`, `MI*****_***` → iliad (formato `XX#####_###`)
- `RX***`, `IT*****` → Cellnex
- `MS_***` → INWIT
- `S*****` → WindTre

Adatta la lettura del PE al template tipico dell'operatore. Vedi `references/template-pe-per-operatore.md` per schema specifico.

### 2. Lettura PE multi-strato

Il PE iliad standard ha questa struttura:
1. **Frontespizio** (pp 1-2) - codice sito, indirizzo, vincoli, normative
2. **Indice analitico** (pp 3-4)
3. **PM (Progetto presentato P.A.)** (pp 5-25) - relazione tecnica + estratti cartografici + tavole architettoniche stato attuale/progetto/confronto + scheda radio
4. **PE (Progetto Esecutivo)** (pp 26-fine):
   - RC (Relazione tecnica opere civili)
   - Dosaggio materiali
   - Normative
   - Relazione di calcolo strutturale (Calzavara per fornitura palina + IBS Progetti per sottostrutture)
   - Tabulati FEM
   - Verifica statica + Particolari
   - Impianti elettrici (RI + IE) + impianto terra + scariche atmosferiche

Leggi in batch di 20 pagine massimo (limite tool Read PDF). Estrai i dati chiave per ogni macro-area.

### 3. Estrazione strutturata

Compila JSON con questa struttura completa:

```json
{
  "sito": {
    "codice": "FI50144_002",
    "nome": "VIALE BELFIORE",
    "indirizzo": "Viale Belfiore, 36 - Firenze (FI)",
    "operatore": "iliad Italia S.p.A.",
    "tipologia": "rooftop / rawland / colocation / swap / upgrade",
    "intervento": "nuova installazione SRB ...",
    "coordinate": {"lat": "...", "lon": "..."},
    "catastale": "NCEU foglio X particella Y",
    "vincoli": [...],
    "progettista_pe": "...",
    "data_pe": "..."
  },
  "struttura": {
    "tipo_sostegno": "palina flangiata + 2 puntoni + grigliato HEA + UPN diagonale + 3 baggioli",
    "altezza_palina_m": 5.50,
    "sezione_palina": "Ø219 x 8 mm S355",
    "n_tronchi": 2,
    "tronco_lunghezze_mm": [2700, 3000],
    "giunto_quota": "X bulloni Ø Y cl 8.8",
    "flangia_base": "...",
    "tirafondi_base": "...",
    "puntoni": "Ø114 x 8 mm S355 - 2 puntoni a 90°",
    "grigliato": "n travi HEA180 accoppiate S275",
    "UPN_diagonale_ipotenusa": "UPN180 l=3.91m",
    "baggioli": "n.3 c.a.",
    "ancoraggi_chimici": "Fischer FIS EM Plus M20×245 cl 8.8 ETA 12/0006",
    "mascheramento": "finto camino / palo poligonale / palo tubolare / non mascherato"
  },
  "impianti": {
    "fornitura_bt": "...",
    "tensione_nominale": "230V monofase TT",
    "quadri": [...],
    "cavi_alimentazione": "...",
    "terra": {"tipo": "TT", "Re_progetto_ohm": 10},
    "spd": "...",
    "norme": "CEI 64-8, CEI EN 62305"
  },
  "rf_tlc": {
    "operatori_ospitati": ["iliad"],
    "n_settori": 3,
    "modelli_antenne": [...],
    "azimut_progetto": [70, 210, 310],
    "tilt_meccanico": [0, 0, 0],
    "altezza_centro_radiante_m": [26.90, ...],
    "n_parabole_mw": 2,
    "azimut_parabole": [30, 250],
    "centro_parabola_m": 26.40
  },
  "paesaggio_monumentale": {
    "vincolo_paesaggistico": "DM ...",
    "vincolo_unesco": "...",
    "categoria_dpr_31_2017": "...",
    "mimetismo": "..."
  },
  "atti_autorizzativi": {
    "pratica_suap": "...",
    "autorizzazione_paesaggistica": "n. ...",
    "parere_arpat_cem": "...",
    "nulla_osta_enac": "...",
    "deposito_gc": "Progetto n. ..."
  },
  "incongruenze_interne_pe_rilevate": [
    "Tabella RC-X riporta erroneamente azimut Settore Y come ZZZ° (refuso)",
    "Discrepanza altezza palina: PE H=5,50m vs Calzavara H=5,70m"
  ]
}
```

### 4. Segnalazione refusi noti

Confronta i dati estratti con `references/refusi-noti-pe-iliad.md` (e analoghi per altri operatori). Se rilevi pattern noti, segnala automaticamente:

- **PE iliad pattern A:** tabella RC-6 con copia-incolla azimut Settore 3 = Settore 2
- **PE iliad pattern B:** numerazione parabole "Parabola 1+2" (tav.) vs "Parabola 1+3" (testo)
- **PE iliad pattern C:** discrepanza altezza palina relazione tecnica (specifica iliad) vs relazione di calcolo (fornitura Calzavara sovradimensionata)
- **PE Cellnex pattern A:** schema unifilare CNP_TS21 vs verifica statica - controllo livello di conoscenza LC
- **PE WindTre pattern A:** ...

Per ogni refuso, classifica come `NC_DOC` con campo `pattern_riconosciuto: true` e citazione del reference.

## Output finale

Restituisci JSON completo + segnalazione esplicita di:
- Campi `null` con `evidenza_mancante: true`
- Refusi pattern noti rilevati
- Eventuali fonti contraddittorie tra elaborati del PE (es. pianta vs prospetto vs tabella)

Non simulare valori. La regola è: meglio segnalare un buco che riempirlo con assunzioni implicite.
