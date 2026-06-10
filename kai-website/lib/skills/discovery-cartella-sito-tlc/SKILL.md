---
name: discovery-cartella-sito-tlc
description: Sub-skill di VerifyBoost TLC. Mappa esaustivamente i file di una cartella di sito TLC italiano (iliad/Cellnex/INWIT/WindTre), inclusi archivi compressi annidati (.zip, .rar, .7z) e file firmati digitalmente (.p7m doppi/tripli). Si attiva quando viene avviata una verifica VerifyBoost o quando l'utente dice "mappa cartella sito", "cosa c'è nella cartella di {codice}", "estrai tutti i file dal sito". Output: lista categorizzata per tipologia documentale (PE, autorizzazioni, deposito GC, realizzato, foto) + segnalazione di archivi/firme da estrarre.
---

# Discovery cartella sito TLC

Mappa esaustivamente la cartella di un sito TLC e categorizza i file per tipologia documentale.

## Trigger di attivazione

- Avvio pipeline VerifyBoost TLC (chiamata dall'orchestratore)
- "Mappa cartella sito {codice}"
- "Cosa c'è nella cartella di {codice}"
- "Discovery sito {codice}"

## Quando NON usare

- Se l'utente vuole solo leggere un file specifico già noto
- Se la verifica non è ancora stata richiesta (è una sub-skill di pipeline)

## Pipeline operativa

### Step 1 - Ricerca esaustiva file

Esegui ricerca completa nella cartella sito target con `find`:

```bash
find "<cartella_sito>" -type f 2>/dev/null | sort
```

Cerca **sempre anche file nascosti in archivi**:

```bash
find "<cartella_sito>" -type f \( -iname "*.zip" -o -iname "*.rar" -o -iname "*.7z" -o -iname "*.p7m" \) 2>/dev/null
```

### Step 2 - Estrazione archivi annidati

**Archivi `.zip`:** estrai con Python `zipfile`:
```python
import zipfile
with zipfile.ZipFile(path) as z:
    z.extractall(dest_dir)
```

**Archivi `.7z`:** richiede `py7zr` (NON usare `7z` CLI che spesso non è disponibile):
```bash
pip install py7zr --break-system-packages --quiet
```
```python
import py7zr
with py7zr.SevenZipFile(path, 'r') as z:
    z.extractall(dest_dir)
```

**Archivi `.rar`:** richiede `rarfile` + `unrar`:
```bash
pip install rarfile --break-system-packages --quiet
```

**File `.p7m` (firma digitale CAdES)**: vedi `references/estrazione-p7m-cades.md` per snippet completo. ATTENZIONE: gestire wrapping doppi/tripli (`.p7m.p7m.p7m`) - alcuni file sono firmati più volte.

### Step 3 - Categorizzazione automatica

Classifica ogni file in una delle macro-categorie:

| Categoria | Pattern nomi tipici |
|---|---|
| `PE_progetto_esecutivo` | `PE_*.pdf`, `*Progetto esecutivo*.pdf`, `*Relazione tecnica*.pdf` |
| `PE_calcolo_strutturale` | `*calcolo*.pdf`, `*VS*.pdf`, `Calzavara*.pdf`, `IBS*.pdf` |
| `PE_tavole_grafiche` | `*OC.*pdf`, `*tav*.pdf`, `*planimetria*.pdf`, `*prospetto*.pdf` |
| `PDM_autorizzato` | `*PDM*.p7m`, `*AUTORIZZATO*.pdf` |
| `autorizzazione_paesaggistica` | `*paesaggist*`, `*SABAP*`, `*1504_2022*` |
| `parere_arpat_cem` | `*ARPAT*`, `*CEM*`, `*positivo*.msg` |
| `nulla_osta_enac` | `*ENAC*` |
| `pratica_suap` | `*SUAP*`, `*CdS*`, `*Conferenza Servizi*` |
| `deposito_genio_civile` | `*Deposito GC*.7z`, `*PORTOS*`, `*Sismica*`, `*Vidimazione*` |
| `cil_inizio_lavori` | `*CIL*`, `*INIZIO LAVORI*` |
| `cfl_fine_lavori` | `*CFL*`, `*FINE LAVORI*` |
| `dico_dm37_2008` | `*Conformit*.pdf`, `*DiCo*`, `*conformita*` |
| `mat_misura_terra` | `*MAT*`, `*terra*` |
| `ddt_materiali` | `*DDT*`, `*DOP*`, `*CE.pdf*` |
| `dichiarazione_corretta_installazione` | `*corretta installazione*`, `*regolare esecuzione*` |
| `scala_sicurezza` | `*scala*`, `*SOLL*`, `*GlideLoc*` |
| `sac_xlsm` | `*SAC*.xlsm` |
| `foto_cantiere` | `*.jpg`, `*.jpeg`, `*.png` (in cartelle FOTO* o estratte da zip foto) |
| `file_accesso_sito` | `*Accesso Sito*` |
| `duvri_art_26` | `*ART 26*`, `*DUVRI*`, `*Rischi specifici*` |

### Step 4 - Output strutturato

Produci JSON con questa struttura:

```json
{
  "sito_codice": "FI50144_002",
  "data_discovery": "2026-05-04",
  "totale_file": 87,
  "totale_foto": 70,
  "archivi_estratti": [
    "1.zip", "Doc fine opere.zip", "Foto Belfiore.zip", "Deposito GC.7z"
  ],
  "categorie": {
    "PE_progetto_esecutivo": ["2022.10.10_PE_..."],
    "deposito_genio_civile": ["19_FI144_002_Deposito GC.7z (estratto)"],
    "...": []
  },
  "p7m_estratti": ["PDM AUTORIZZATO.p7m", "Fascicolo_A02.pdf.p7m.p7m"],
  "warning": [
    "Trovati N file p7m con doppio/triplo wrapping",
    "File X non leggibile: corrotto"
  ]
}
```

## Lessons learned

- **Mai assumere che la cartella sia piatta.** I siti TLC hanno tipicamente 3-5 livelli di nesting con archivi compressi multipli.
- **Mai saltare i `.7z`.** Spesso il deposito GC è in `.7z` per dimensioni - se non viene estratto, si salta l'intera verifica strutturale formale.
- **Verifica md5 dei file con stessa dimensione.** A volte fascicoli depositati con etichette diverse sono lo stesso file (es. caso PORTOS A07/A08/A09 nel sito FI50144_002).
- **Le foto sono spesso in 2-3 zip diversi.** Verificare md5 per evitare di duplicare foto identiche.

## Esempio applicato

Sito: `FI50144_002 VIALE BELFIORE` - cartella su Desktop

```bash
find "/path/FI50144_002 VIALE BELFIORE" -type f | wc -l
# 87 file totali

find ... -iname "*.7z"
# trovato: 1/01_Permessi/19_FI144_002_Deposito GC.7z

# estrazione
python3 -c "import py7zr; py7zr.SevenZipFile('19_FI144_002_Deposito GC.7z').extractall('/tmp/GC/')"

# il pacchetto contiene Avviso Vidimazione + 11 fascicoli .p7m (alcuni doppi/tripli) + 3 asseverazioni + 2 ricevute IRIS
```

## Output finale alla skill chiamante

Restituisci:
- **JSON di mappa categorizzata** completa
- **Lista warning** (file corrotti, p7m problematici, archivi non estraibili)
- **Lista priorità lettura** (i 5-10 documenti più rilevanti per la baseline)
