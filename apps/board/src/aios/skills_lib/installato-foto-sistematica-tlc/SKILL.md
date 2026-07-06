---
name: installato-foto-sistematica-tlc
description: Sub-skill di VerifyBoost TLC. Analisi sistematica delle foto cantiere di un sito TLC. Categorizza per fase temporale (carpenteria/baggioli/palina/apparati/cablaggio/MAT) usando timestamp EXIF e geolocalizzazione, e per tipologia di evidenza (struttura/RF/MAT/architettonico/sicurezza). Si attiva quando l'orchestratore richiede analisi foto, oppure quando l'utente dice "analizza le foto del sito {codice}", "verifica visiva foto cantiere", "foto sistematica". Output: lista foto categorizzate + esiti visivi per ogni elemento del telaio TLC.
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


# Analisi sistematica foto cantiere TLC

Analizza in modo esaustivo (non a campione) le foto di un sito TLC per produrre evidenze visive di conformità.

## Trigger di attivazione

- Chiamata da `verifyboost-tlc-orchestrator` (Step 2 della pipeline)
- "Analizza le foto del sito {codice}"
- "Foto sistematica {codice}"
- "Verifica visiva foto cantiere"

## Regola anti-campionamento

I siti TLC tipici hanno **50-100 foto cantiere**. Mai limitarsi a 5-10 a campione. Se la dimensione totale supera la capacità di lettura sequenziale, invece di campionare:
1. Categorizza tutte le foto per fase + tipologia (senza aprire)
2. Apri 2-4 foto per categoria (le più rappresentative)
3. Documenta lo skip categorico, mai casuale

## Pipeline operativa

### 1. Inventario completo foto

```bash
find <cartella_sito> -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) ! -iname "Thumbs.db" | sort
```

Estrai anche dalle eventuali foto in archivi (zip/rar). Verifica md5 per scartare duplicati - tipicamente 30-50% delle foto sono duplicate (zip multipli con stesse foto).

### 2. Estrazione metadati EXIF

Per ogni foto leggi:
- **Timestamp** (data + ora di scatto)
- **Geolocalizzazione GPS** (lat/lon - foto di siti TLC moderni hanno tipicamente GPS)
- **Modello dispositivo**

Le foto WhatsApp (`IMG-YYYYMMDD-WA####`) **non hanno EXIF GPS** - usare timestamp dal nome file.

### 3. Clustering per fase temporale

Raggruppa le foto per fase costruttiva basandoti sui timestamp:

| Fase | Timestamp tipico | Contenuto atteso |
|---|---|---|
| Pre-cantiere (sopralluogo) | settimana -2 a -4 | Stato attuale torrino/lastrico/copertura, parabole esistenti |
| Carpenteria/baggioli | 1°-3° settimana cantiere | Realizzazione baggioli c.a., guaina catramata, ancoraggi chimici Fischer M20 |
| Posa carpenteria metallica | 2°-4° settimana | Travi HEA accoppiate, UPN diagonale, bullonature giunti |
| Posa palina+puntoni | 3°-5° settimana | Palina installata, puntoni Ø114 fissati, tirafondi Ø24, mascheramento finto camino |
| Installazione apparati | 4°-7° settimana | RFM, quadri CFE-ILIAD, MiniTD, FCOB, antenna GPS |
| Cablaggio jumper RF + MAT | 5°-7° settimana | Cavi tracciati ed etichettati, collettore terra, SPD |
| Foto fine lavori | settimana finale | Vista d'insieme, foto a corredo verbali |

### 4. Tagging tipologia evidenza

Per ogni cluster temporale, applica i tag di tipologia:

| Tag | Descrizione |
|---|---|
| `STR_baggiolo_palina` | Baggiolo centrale 840x840 |
| `STR_baggiolo_puntone` | Baggioli esterni 840x500 |
| `STR_grigliato_HEA` | Travi HEA180 accoppiate |
| `STR_UPN_diagonale_ipotenusa` | Trave UPN180 l=3.91m diagonale - **VERIFICA SEMPRE** la presenza |
| `STR_palina` | Palina Ø219 + giunto a 2.7m |
| `STR_puntoni_ipotenusa_triangoli_verticali` | 2 puntoni Ø114 + ancoraggi |
| `STR_flangia_base` | 8 bulloni Ø24 visibili |
| `RF_antenne_NOKIA_AEQE` | Etichetta CE Nokia visibile |
| `RF_parabole_MW` | Parabole Huawei Ø30 cm |
| `RF_RFM_apparati` | 7 moduli RFM impilati |
| `RF_GPS_antenna` | Cupola bianca GPS su mensola |
| `MAT_collettore` | Collettore principale terra con cavi G/V etichettati |
| `MAT_pozzetto` | Pozzetto MAT |
| `IMP_quadri_CFE` | Quadri CFE-ILIAD-ICA + Mini-TD aperti con SPD |
| `IMP_finto_pluviale` | Tubo nero verticale per cavi facciata retrostante |
| `ARC_finto_camino_completo` | Mascheramento bianco vetroresina installato |
| `ARC_parabola_condominiale_riposizionata` | Parabola condominio (TRIAX/ecc.) riposizionata di lato |
| `ARC_torrino_panorama` | Vista d'insieme torrino integrato architettonicamente |
| `SIC_scala_GlideLoc_SOLL` | Scala di sicurezza rimovibile |
| `SIC_paletti_amovibili_catena` | Delimitazione area apparati |
| `SIC_dispositivi_anticaduta` | Imbragature, fermacaduta |

### 5. Verifica esaustività

Per ogni elemento del telaio TLC del PE, verifica che ci sia ALMENO 1 foto che lo documenta. Se manca, segnala come `evidenza_visiva_mancante`:

- Baggiolo palina: ALMENO 1 foto
- Baggioli puntoni: ALMENO 2 foto (uno per baggiolo)
- UPN180 diagonale: ALMENO 1 foto - **questa è la più frequente "mancante"**
- Grigliato HEA180: ALMENO 1 foto giunzione
- Flangia base palina: ALMENO 1 foto con 8 bulloni Ø24 visibili
- Puntoni: ALMENO 2 foto (uno per puntone, anche dal mascheramento installato)
- Antenne: ALMENO 1 foto etichetta CE per modello
- Parabole MW: ALMENO 1 foto retro con connettori
- RFM: ALMENO 1 foto rack 7 moduli
- Quadri: ALMENO 1 foto interno con SPD
- MAT collettore: ALMENO 1 foto cavi G/V etichettati

### 6. Output strutturato

```json
{
  "analisi_foto_sistematica": {
    "totale_foto_trovate": 87,
    "totale_foto_uniche": 59,
    "duplicati_scartati": 28,
    "fasi_documentate": ["pre-cantiere", "baggioli", "carpenteria", "palina", "apparati", "MAT", "fine-lavori"],
    "tipologie_documentate": ["STR_*", "RF_*", "MAT_*", "IMP_*", "ARC_*", "SIC_*"],
    "evidenze_visive_chiave": [
      {"foto": "IMG-20221222-WA0007.jpg", "tag": "STR_baggiolo_palina + STR_palina + STR_flangia_base", "esito": "OK"},
      {"foto": "IMG_20230116_102345_447.jpg", "tag": "STR_puntoni + STR_flangia_base 8xØ24", "esito": "OK"}
    ],
    "evidenze_mancanti": [
      "STR_UPN_diagonale_ipotenusa - nessuna foto chiaramente identificabile - prescrivere sopralluogo del DL"
    ],
    "warning": [
      "Anomalia geolocalizzazione: 1 foto con GPS Viale Belfiore 34 invece di 36 - GPS-drift accettabile"
    ]
  }
}
```

## Lessons learned

- **La UPN180 diagonale è quasi sempre nascosta** dal mascheramento finto camino o dalla pavimentazione galleggiante - prescrivere sempre conferma DL
- **Le foto WhatsApp** sono affidabili nei timestamp ma compresse - per dettagli (es. etichette CE, codici modelli) preferire foto IMG_yyyymmdd_hhmmss
- **GPS-drift** entro 30-50m è normale - non ribaltare conformità per coordinate GPS leggermente diverse dall'indirizzo
- **Etichetta CE antenne** è un'evidenza forte: foto del retro antenna con etichetta NOKIA Solutions / Huawei / Ericsson conferma il modello dichiarato in PE
