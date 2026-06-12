---
name: confronto-strutturale-tlc
description: Sub-skill di VerifyBoost TLC. Confronta sistematicamente la struttura installata con il progetto strutturale (PE + relazioni di calcolo + tavole + deposito GC). Verifica TUTTI gli elementi del telaio TLC: palina, puntoni (ipotenusa triangoli verticali), grigliato HEA, UPN180 diagonale (ipotenusa telaio orizzontale), 3 baggioli, ancoraggi chimici, flangia base, giunti bullonati. Si attiva quando l'orchestratore richiede confronto strutturale, oppure quando l'utente dice "verifica struttura installata", "controlla telaio", "verifica baggioli", "verifica puntone". Usa il glossario codificato in references/glossario-telaio-tlc.md.
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


# Confronto strutturale TLC

Confronta TUTTI gli elementi della struttura installata con quella progettata.

## Trigger di attivazione

- Chiamata da `verifyboost-tlc-orchestrator` (Step 3 della pipeline)
- "Verifica struttura installata sito {codice}"
- "Controlla telaio strutturale"
- "Verifica baggioli + puntoni + travi vs PE"
- "Confronto strutturale"

## Glossario di riferimento

**Apri sempre `references/glossario-telaio-tlc.md`** per il vocabolario standardizzato del telaio TLC. Mai usare termini arbitrari - usa quelli del glossario per evitare ambiguità con il DL strutturale.

Schema concettuale (sintetico):

```
                         ┌─ palina Ø219x8 S355 ─┐
                         │                        │
        triangolo         puntone Ø114                 puntone Ø114    triangolo
        verticale 1   ─►  (ipotenusa 1)                (ipotenusa 2)  ◄─ verticale 2
                         │  ╱                    ╲  │
                         │ ╱                      ╲ │
                         │╱                        ╲│
        ─────────────────●──────● UPN180 ●──────────●─────────────────
                    bagg.       (ipotenusa            bagg.
                    palina      orizzontale)          puntone
        catetere1: HEA180+HEA180 accoppiate    catetere2: HEA180+HEA180 accoppiate
                    │                                       │
                    └─ telaio orizzontale ad L su 3 baggioli c.a.
```

Quindi 2 livelli di "ipotenusa":
1. **Triangoli VERTICALI** (n.2): cateti = palina + tratto orizzontale al baggiolo, ipotenusa = puntone Ø114
2. **Telaio ORIZZONTALE a L** (n.1): cateti = 2 rami HEA180 accoppiate, ipotenusa = trave UPN180 diagonale

**MAI saltare la UPN180 orizzontale.** È l'errore più frequente nei verificatori che fanno solo controllo verticale.

## Pipeline operativa

### 1. Estrai dati progetto

Da `baseline-pe-tlc` e `baseline-deposito-gc-tlc` raccogli:
- Geometria palina (Ø, h totale, n. tronchi, lunghezze)
- Geometria puntoni (Ø, lunghezza, materiale)
- Schema telaio (n. travi HEA, geometria, eventuale UPN diagonale)
- Schema baggioli (n., dimensioni, ancoraggi chimici)
- Bulloneria chiave (flangia base, giunti, ancoraggi)
- Verifiche strutturali (sfruttamento, esiti)

### 2. Estrai evidenze installato

Da `installato-foto-sistematica-tlc` recupera le foto taggate `STR_*`. Verifica esaustività delle evidenze visive.

### 3. Confronto elemento per elemento

Per ogni elemento del telaio:

| Elemento | Cosa verificare | Tolleranza | Esito tipico |
|---|---|---|---|
| Palina (geometria) | Ø, h, n.tronchi, materiale | nessuna | OK / OK_TOL (sovradimens. fornitore) / NC_GR |
| Palina (verticalità) | Verticalità ≤ 0.5° | NTC §4.2 | OK / NC_DOC se non dichiarata |
| Giunto palina (bulloneria) | n. bulloni × Ø × classe | nessuna | OK / NC_DOC se assente DiCo |
| Flangia base (tirafondi) | n. bulloni × Ø × classe (8×Ø24 cl 8.8 standard iliad) | nessuna | OK / NC_DOC |
| Puntoni (Ø + lunghezza) | Ø114 x 8 mm S355, ~3.26m | nessuna | OK |
| Ancoraggio puntone-baggiolo | piastra 340x420 + bullone M24 cl 8.8 | nessuna | OK |
| Grigliato HEA | n. travi, sezione, materiale, accoppiamento | nessuna | OK |
| **UPN180 diagonale** | **PRESENZA visiva o dichiarata** | nessuna | **OK_TOL se da verificare in loco** |
| Baggiolo palina | 840x840x200 c.a. + piastra 'A' | nessuna | OK / NC_DOC |
| Baggioli puntoni (n.2) | 840x500x200 c.a. + piastra 'B' | nessuna | OK / NC_DOC |
| Ancoraggi chimici | Fischer FIS EM Plus M20×245 cl 8.8 ETA 12/0006 | nessuna | OK / NC_GR se non Fischer/etichettato diversamente |
| Impermeabilizzazione baggioli | guaina catramata risvoltata | CEI/UNI buona prassi | OK / NC_DOC |
| Zincatura carpenteria | a caldo UNI EN ISO 1461 ≥80 micron | nessuna | OK / NC_DOC |
| Giunti bullonati piastre | bulloneria classe 8.8 + Palnut antiallentamento | DM 17/01/2018 §4.2.8.1.1 | OK / NC_DOC |

### 4. Confronto verifiche strutturali

Riassumi gli esiti delle verifiche del PE/deposito GC:
- Sfruttamento massimo palina (tipico 10-20%)
- Sfruttamento massimo puntoni (tipico 20-30%)
- Sfruttamento massimo HEA180 (tipico 20-40%)
- Sfruttamento massimo ancoraggi chimici (tipico 40-60% rottura bordo cls)
- Sfruttamento massimo bulloneria flangia base (tipico 5-10%)

Se uno qualsiasi supera 80%: NC_GR (margine insufficiente). Se supera 100%: NC_CR (struttura non verificata).

### 5. Riconoscimento discrepanze interne

Pattern noti da rilevare (cross-check con `references/refusi-noti-pe-iliad.md` e analoghi):

**Pattern frequenti Calzavara:**
- Schema unifilare cita `n. 16 M16 8.8` flangia base ma relazione di calcolo cita `8 bulloni Ø24 cl 8.8` - segnalare come NC_DOC discrepanza interna fornitore. Verificare con foto installato per disambiguare (tipicamente l'installato è coerente con la relazione di calcolo).
- Altezza palina: relazione tecnica PE H=5,50m vs relazione di calcolo Calzavara H=5,70m - sovradimensionamento positivo del fornitore. NON è una NC sostanziale, classificare come **OK_TOL** con nota.

**Pattern frequenti IBS Progetti:**
- Sommario relazione cita "HEA 200" ma testo verifica "HEA 180" - refuso interno. NC_DOC.

### 6. Output strutturato

```json
{
  "confronto_strutturale": {
    "elementi_verificati": [
      {
        "elemento": "puntone_diagonale_Ø114",
        "progetto": "Ø114x8 S355, l=3.26m",
        "installato_evidenza": "IMG_20230116_102345 + IMG-20221222-WA0010",
        "esito": "OK",
        "verifica_calcolo": "Sfruttamento bulloni 22% - VERIFICATO"
      },
      {
        "elemento": "trave_UPN180_diagonale_ipotenusa_telaio",
        "progetto": "UPN180 l=3.91m Tipo '1' - tav. OC.07",
        "installato_evidenza": "NON CHIARAMENTE VISIBILE in foto disponibili",
        "esito": "OK_TOL",
        "azione_raccomandata": "Sopralluogo DL strutturale per conferma visiva"
      },
      {
        "elemento": "baggioli_3_ca",
        "progetto": "1x 840x840x200 + 2x 840x500x200 + Fischer M20",
        "installato_evidenza": "IMG-20221222-WA0001/0003/0007/0009/0015 - 5 foto",
        "esito": "OK",
        "verifica_calcolo": "IBS V.2/V.3 sfruttamento ancoraggi 53.6% - VERIFICATO"
      }
    ],
    "discrepanze_interne_pe_rilevate": [
      "Calzavara - flangia base: schema unifilare M16 vs calcolo M24 - foto installato confermano M24 (coerente con calcolo)",
      "Altezza palina H=5,50m PE vs H=5,70m Calzavara - OK_TOL sovradimensionamento positivo fornitore"
    ],
    "evidenze_visive_mancanti": [
      "UPN180 diagonale - prescrivere sopralluogo DL"
    ]
  }
}
```

## Lessons learned

- **MAI saltare la UPN180 orizzontale.** È l'errore più frequente perché il telaio strutturale TLC ha sia triangoli verticali (palina+puntoni) che telaio orizzontale (HEA+UPN). Il glossario codifica questa distinzione.
- **Verificare md5 dei file di calcolo.** Spesso fornitori (Calzavara, IBS) hanno discrepanze interne tra tavola unifilare e relazione di calcolo - l'installato segue la relazione di calcolo, la tavola è il refuso.
- **Sovradimensionamento fornitore = OK_TOL.** La palina Calzavara H=5,7m fornita per progetto H=5,5m è prassi industriale, non NC.
- **Ancoraggi chimici Fischer FIS EM Plus M20×245 ETA 12/0006** è lo standard di mercato. Se l'installatore ha usato altri ancoraggi (es. Hilti, Würth) verificare ETA equivalente - non è automaticamente NC ma serve dichiarazione di equivalenza.
