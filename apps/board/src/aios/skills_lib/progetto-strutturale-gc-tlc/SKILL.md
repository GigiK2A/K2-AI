---
name: progetto-strutturale-gc-tlc
description: >
  Ingegnere strutturista specializzato nella redazione del Progetto Strutturale Completo
  per il deposito al Genio Civile di interventi su siti di telecomunicazione (pali
  porta-antenne, pennoni, fondazioni). Usa SEMPRE questa skill per: "deposito Genio
  Civile", "progetto strutturale deposito", "deposito GC sito TLC", "D.P.R. 380/2001
  art.65/93", "progetto strutturale palo antenna", "adeguamento strutturale sito TLC",
  "relazione di calcolo strutturale", "verifica statica per Genio Civile",
  "progressione pennone deposito", "nuovo palo deposito strutturale", "palo da
  rinforzare deposito", "fascicolo strutturale GC". Attivala ogni volta che l'utente
  vuole produrre documenti strutturali per un deposito normativo italiano su
  infrastrutture TLC — anche se non usa esplicitamente "Genio Civile". Il modello
  di riferimento è il progetto RM00040_011 (Lido dei Coralli, palo poligonale 16 lati
  H=36m), verificato e depositato con successo.
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


# Progetto Strutturale – Deposito Genio Civile per Adeguamento Siti TLC

Questo skill guida la produzione del **Fascicolo Strutturale Completo** per il deposito
al Genio Civile di interventi strutturali su pali porta-antenne TLC, ai sensi del
**D.P.R. 380/2001 artt. 65 e 93**.

Il metodo di calcolo è **analitico** (non FEM): formule chiuse da NTC 2018 + EN 1993-1-1/1-8/1-9 + CNR-DT 207/2008. Il modello di riferimento è il progetto **RM00040_011** (rev.01, K2A Srls / Ing. Luca Rossi), che costituisce il template di qualità.

---

## Normativa di riferimento

Leggi sempre `references/normativa.md` per l'elenco completo. Le principali:

- **NTC 2018** (D.M. 17/01/2018) + **Circolare n.7/2019** — Norme Tecniche Costruzioni
- **EN 1993-1-1** — Progettazione strutture in acciaio (fusto palo)
- **EN 1993-1-8** — Connessioni (piastra di base, giunto pennone)
- **EN 1993-1-9** — Fatica
- **CNR-DT 207/2008** — Azioni del vento su strutture per TLC
- **D.P.R. 380/2001 artt. 65, 93** — Obbligo deposito strutturale

---

## Step 1 — Raccolta dati di input

Chiedi all'utente i dati seguenti (o estraili dai file di progetto forniti).

### 1a. Anagrafica sito
```
- Codice sito (es. RM00040_011)
- Operatore / towerco
- Indirizzo, Comune, Provincia
- Committente / Direttore Lavori
- Progettista strutturale (nome, albo, n.iscrizione)
```

### 1b. Geometria palo
```
- Tipo: poligonale N lati / tubolare / traliccio
- Altezza fuori terra H [m]
- N. tronchi (tipicamente 3)
- Per ogni tronco: diametro base De_i [mm], diametro testa Dt_i [mm], spessore t_i [mm], lunghezza L_i [mm]
- Acciaio: grado (tipicamente S355JR) → fy=355 MPa, fu=510 MPa
```

### 1c. Pennone
```
- Sezione: CHS (tubo circolare cavo) o profilo diverso
- Diametro esterno D [mm], spessore t [mm]
- Lunghezza ANTE [mm] e POST [mm]
- Quota attacco al palo [m] (tipicamente H_palo - 0.5m)
- Tipo giunto: flangiato (n. bulloni, diametro flange)
```

### 1d. Piastra di base
```
- Diametro esterno De [mm], spessore t [mm]
- N. tirafondi, diametro d [mm], acciaio (tipicamente S355)
- Diametro bulloni [mm], passo corona [mm]
```

### 1e. Fondazione
```
- Tipo: pali trivellati o plinto diretto
- Se pali: n. pali, diametro φ [mm], lunghezza L [m], interasse, soletta (lxbxh) [m]
- Se plinto: dimensioni in pianta, profondità
- Calcestruzzo: classe (tipicamente C25/30) → fck=25 MPa
- Terreno: γ [kN/m³], φ' [°], c' [kPa], tipo (ghiaia/sabbia/argilla)
```

### 1f. Configurazione antennistica ANTE/POST
```
Per ogni antenna (ripeti per ANTE e POST):
- Tipo (panel, parabolica, RRU, MW link)
- Dimensioni [m × m] o diametro [m]
- Peso [kg]
- Quota [m da terra]
- Azimut
- SEV (superficie equivalente al vento) [m²]
```

### 1g. Parametri sito
```
- Zona vento (1÷9 secondo CNR-DT 207/2008, figura 3.1)
- Classe di rugosità del terreno (A/B/C/D secondo NTC 2018)
- Categoria di esposizione (I÷V → Ce(z))
- Zona sismica (1÷4) e Comune → lat/lon per spettro NTC
- Vs30 [m/s] → categoria sottosuolo (A/B/C/D/E)
- Topografia (T1/T2/T3/T4)
```

---

## Step 2 — Calcolo azioni del vento

Usa lo script `scripts/compute_wind.py`. Fornisci i parametri di Step 1g e la geometria.

Il metodo segue **CNR-DT 207/2008** (pressioni cinetiche caratteristiche per strutture TLC):
- Pressione cinetica di riferimento: `qr = ½ρVr²`
- Velocità di riferimento per zona
- Coefficiente di esposizione Ce(z) = cr²(z)·ct²·(1+7·Iv(z))
- Forza equivalente per tronco: `Fw,i = qr · Ce(zi) · Cd · Af,i`
- `Af,i` = area esposta proiettata (fusto + antenne a quota zi)

Documentare per ogni tronco: zi, Vr, Ve(zi), qe(zi), Fw,i [daN].

---

## Step 3 — Calcolo azioni sismiche

Usa lo script `scripts/compute_spectra.py`. Il sisma è quasi sempre non governante (vento >> sisma per pali snelli), ma va comunque calcolato e documentato.

Output: spettro SLV e SLD, forza di taglio alla base `Fb = Sd(T1)·W/g·λ`.

Verifica che `Fb << Fw,base`. Se il sisma fosse governante (Fb > 0.7·Fw), notare e gestire.

---

## Step 4 — Combinazioni di carico SLU/SLE

Leggi `references/combinazioni.md` per le formule complete. Le combinazioni principali:

| ID | Tipo | Descrizione |
|----|------|-------------|
| C1 | SLU-STR | Fondamentale: 1.3G + 1.5Qw (combinazione dominante) |
| C2 | SLU-STR | Con ghiaccio: 1.3G + 1.5Qw·ψ0 + 1.5Qice |
| C3 | SLU-EQU | Equilibrio: 0.9G + 1.5Qw |
| C4 | SLU-GEO | A2: G + Qw (per fondazione) |
| C5 | SLE-Rara | G + Qw (per rotazioni) |

Calcola per ogni combinazione: M [kNm], V [kN], N [kN] alla base e ai giunti.

---

## Step 5 — Verifiche strutturali fusto

Verifica ogni tronco alle **sollecitazioni massime** (sez. inferiore di ogni tronco).

### 5a. Pressoflessione + instabilità globale (EN 1993-1-1 §6.3.3)

Per sezione poligonale equivalente a tubo:
```
Mc,Rd = Wpl,i · fy / γM0
Nb,Rd = χ · A · fy / γM1   (instabilità globale, χ da curva "b")
NEd/Nb,Rd + My,Ed/Mc,Rd ≤ 1.0
```

### 5b. Instabilità locale di parete (EN 1993-1-1 §5.5 + Tab. 5.2)
```
d/t ≤ 90ε²  (classe 1-2 per flessione)
dove ε = √(235/fy)
```

### 5c. Taglio (EN 1993-1-1 §6.2.6)
```
Vpl,Rd = Av · fy / (√3 · γM0)
VEd / Vpl,Rd ≤ 1.0
```

Documentare sfruttamento η [%] per ogni tronco, ANTE e POST.

---

## Step 6 — Verifica nodo di base (EN 1993-1-8)

### 6a. Piastra di base (flessione)
Modello T-stub o formula diretta per piastra circolare soggetta a momento + compressione eccentrica.

### 6b. Tirafondi (trazione)
```
Ftsd = (M - N·e) / (n_t · r_corona)    [kN per tirafondo]
Ft,Rd = 0.9 · fub · A_s / γM2
Ftsd / Ft,Rd ≤ 1.0
```

### 6c. Verifica pressione di contatto fondazione
```
σ_max = N/A_p + M/W_p ≤ f_cd    (compressione)
σ_min = N/A_p - M/W_p ≥ 0       (trazione → EQU check)
```

---

## Step 7 — Verifica fondazione (pali trivellati)

Usa il metodo **Berezantzev** per portanza pali in compressione e trazione.

```
PL = qb · Ab + Σ(fi · Asi)     [portanza laterale]
PP = qp · Ab                    [portanza punta]
Pc,comp = (PL + PP) / γR        (GEO A2: γR = 1.5 o 2.0)
Pc,traz = PL / γR + W_palo
```

Sfruttamento: `NEd,palo / Pc,comp ≤ 1.0` (sia in compressione che trazione).

Leggi `references/fondazione_berezantzev.md` per le formule complete.

---

## Step 8 — Verifica fatica (EN 1993-1-9)

Il carico di fatica è il vento aleatorio con distribuzione di Weibull.

Metodo Palmgren-Miner: `D = Σ(ni / Ni) ≤ 1.0`

Dettagli strutturali critici:
- **Piastra di base** → categoria 80 (saldatura d'angolo su piastra)
- **Fusto palo** → categoria 90 (tubo longitudinale)
- **Giunto pennone** → categoria 71 (bulloni a fatica)

Leggi `references/fatica.md` per il metodo completo di calcolo dello spettro di carico vento.

---

## Step 9 — Verifica SLE (rotazioni)

Limiti ammissibili per siti TLC:
- Top pennone ≤ **40'** (parabole MW link: limite operativo)
- Top palo ≤ **40'** (raccomandazione gestionale)
- Parabole: rotazione relativa ≤ HPBW/4

Calcola con metodo beam-column (doppia integrazione o Mohr virtuale):
```
θ_top = ∫₀ᴴ [M(z) / EI(z)] dz
```

Usa `scripts/compute_deformed_shape.py` per il calcolo numerico con sezione variabile.

---

## Step 10 — Produzione documenti

### Fascicolo minimo per deposito D.P.R. 380/2001

Leggi `references/schema_documenti.md` per il dettaglio di ogni elaborato.

| N. | Documento | Formato |
|----|-----------|---------|
| 01 | Relazione Tecnica Illustrativa (RTI) | DOCX/PDF |
| 02 | Relazione di Calcolo Strutturale | DOCX/PDF |
| 03 | Relazione sui Materiali | DOCX/PDF |
| 04 | Relazione Geotecnica | DOCX/PDF |
| 05 | Piano di Manutenzione Strutturale | DOCX/PDF |
| 06 | Elaborati Grafici (DWG/PDF) | PDF |
| 07 | Tabulati di calcolo | PDF/XLSX |

### Generazione DOCX

Usa `scripts/generate_relazione.js` come **template Node.js**. Il generatore:
1. Calcola tutte le sezioni dalla struttura dati JSON di input
2. Produce il DOCX con `npm install docx && node generate_relazione.js`
3. Segue la struttura di RM00040_011 come modello di stile e contenuto

Prima di generare, adatta le sezioni variabili (geometria, numeri, intestazioni) al sito specifico.

---

## Comunicazione all'utente

Dopo aver raccolto i dati di Step 1:
1. Mostra un **riepilogo strutturato** dei dati raccolti e chiedi conferma
2. Esegui i calcoli step-by-step, mostrando i risultati intermedi
3. Evidenzia in **grassetto** i valori di sfruttamento e i semafori (✅ / ⚠️ / ❌)
4. Se uno sfruttamento > 90%: avvisa l'utente e proponi alternative (riduzione carico, rinforzo)
5. Produce prima la **Relazione di Calcolo** (documento principale), poi gli altri

## Note di qualità

- Tutti i valori di sfruttamento nel riepilogo finale devono essere ANTE e POST
- La relazione deve esplicitare le combinazioni di carico per ogni verifica
- Le formule devono essere riportate sia in forma simbolica che numerica applicata
- I tabulati di calcolo devono essere allegati (non solo i risultati finali)
- Lo stile DOCX deve seguire il template RM00040_011: font Calibri 11, margini standard A4

## File bundled

| File | Scopo |
|------|-------|
| `references/normativa.md` | Elenco completo norme applicabili |
| `references/combinazioni.md` | Formule combinazioni SLU/SLE |
| `references/fondazione_berezantzev.md` | Metodo Berezantzev pali |
| `references/fatica.md` | Metodo Palmgren-Miner + EN 1993-1-9 |
| `references/schema_documenti.md` | Struttura fascicolo GC + contenuto minim |
| `scripts/compute_wind.py` | Calcolo azioni vento CNR-DT 207/2008 |
| `scripts/compute_spectra.py` | Spettri sismici NTC 2018 |
| `scripts/compute_struttura.py` | Verifiche strutturali fusto + giunti |
| `scripts/compute_fondazione.py` | Portanza pali Berezantzev |
| `scripts/compute_deformed_shape.py` | Deflessioni SLE (sezione variabile) |
| `scripts/generate_relazione.js` | Generatore DOCX (Node.js + docx) |
