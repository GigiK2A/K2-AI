# Matrice Sezioni RELSTA — 9 file analizzati

**Autore**: K2A Srls / Ing. Luca Rossi (Albo Ing. Perugia n. A2212)
**Data analisi**: 2026-04-22
**Obiettivo**: individuare i pattern strutturali ricorrenti per riprodurre ogni tipo di RELSTA che il sistema dovrà generare.

---

## 1. Varianti individuate (4 template)

| Variante | Cap. | File | Committente/Gestore | Note |
|---|---|---|---|---|
| **A** – Wind Tre minimal | 5 | RM823 | Wind Tre / Cellnex | TOC compatta senza "Fonti e LC" |
| **B** – Wind Tre full | 7 | LT032 | Wind Tre / CKH | Include Cap. 1 "Fonti e LC", Cap. 2 "Stato conservazione" |
| **C** – Iliad standard | 6 | FI023, FI50137_802, LU55041_002, RM00189_012 | Iliad / Iliad+Wind+Cellnex / Iliad+Inwit | Cap. 5.1–5.10 senza comb. SLE dedicata |
| **D** – Iliad con SLE | 6 | LI57027_003, SI53014_003 | Iliad+Vodafone / Iliad | Cap. 5.1–5.11 con 5.7 "Comb. SLE" |
| **E** – Esteso con Preesistenze | 8 | PO008 | (struttura ibrida ampia, 158 p) | Cap. 4 "Preesistenze", Cap. 8 "Tabulati" |

---

## 2. Matrice sezione-per-sezione

### Legenda
- ✅ sezione presente
- ⚠️ presente con numerazione diversa (vedi nota)
- — assente
- ▲ sezione estesa/ampliata

### 2.1 Blocco "Preambolo"

| Sezione | A (RM823) | B (LT032) | C (Iliad std) | D (Iliad+SLE) | E (PO008) |
|---|---|---|---|---|---|
| Frontespizio + firma | ✅ | ✅ | ✅ | ✅ | ✅ |
| Indice | ✅ | ✅ | ✅ | ✅ | ✅ |
| Premessa (sintesi sito + scopo) | — | — | — | — | — |
| Fonti e livello di documentazione (LC1/2/3, FC) | — | ✅ (Cap.1) | ✅ (Cap.1) | ✅ (Cap.1) | ✅ (Cap.1) |
| Stato di conservazione | — | ✅ (Cap.2) | — | — | — |
| Preesistenze strutturali | — | — | — | — | ✅ (Cap.4) |

### 2.2 Blocco "Quadro normativo e materiali"

| Sezione | A | B | C | D | E |
|---|---|---|---|---|---|
| Relazione tecnico-illustrativa | ✅ (1) | ✅ (3) | ✅ (2) | ✅ (2) | ✅ (2) |
| Normativa di riferimento | ✅ (2) | ✅ (4) | ✅ (3) | ✅ (3) | ✅ (3) |
| Relazione sui Materiali | ✅ (3) | ✅ (5) | ✅ (4) | ✅ (4) | ✅ (5) |

### 2.3 Blocco "Relazione di calcolo" (cuore tecnico)

| Sotto-sezione | A (Cap.4) | B (Cap.6) | C (Cap.5) | D (Cap.5) | E (Cap.6) |
|---|---|---|---|---|---|
| Analisi dei carichi | ✅ 4.1 | ✅ 6.1 | ✅ 5.1 | ✅ 5.1 | ✅ 6.1 |
| Metodo di calcolo e combinazioni | ✅ 4.2 | ✅ 6.2 | ✅ 5.2 | ✅ 5.2 | ✅ 6.2 |
| Individuazione del codice di calcolo (Straus7) | ✅ 4.3 | ✅ 6.3 | ✅ 5.3 | ✅ 5.3 | ✅ 6.3 |
| Combinazione fondamentale (SLU) | — | ✅ | ✅ 5.4 | ✅ 5.4 | ✅ 6.4 |
| Combinazione rara (SLE) | — | ✅ | ✅ 5.5 | ✅ 5.5 | ✅ 6.5 |
| Combinazione sismica | — | ✅ | ✅ 5.6 | ✅ 5.6 | ✅ 6.6 |
| Combinazione SLE (dedicata) | — | — | — | ✅ 5.7 | ✅ 6.7 |
| Resistenza dei materiali | — | ✅ | ✅ 5.7 | ✅ 5.8 | ✅ 6.8 |
| Carichi permanenti + vento distribuito | — | ✅ | ✅ 5.8 | ✅ 5.9 | ✅ 6.9 |
| Output di calcolo / Analisi risultati | ✅ 4.4 | ✅ 6.4 | ✅ 5.9 | ✅ 5.10 | ✅ 6.10 |
| Verifiche elementi (tronchi palo) | ✅ 4.5 | ✅ 6.5 (tronchi) | ✅ 5.9.1 | ✅ 5.10.1 | ✅ 6.10.1 |
| Verifica piastra base + tirafondi | ✅ (in 4.7) | ✅ 6.8 | ✅ 5.9.2 | ✅ 5.10.2 | ✅ 6.10.2 |
| Verifica unioni flangiate | ✅ 4.7 | ✅ 6.6 | ✅ 5.9.3 | ✅ 5.10.3 | ✅ 6.10.3 |
| Verifica puntoni / controventi | — | ✅ 6.7 | — | — | ✅ (se presenti) |
| Verifica stralli / tiranti | — | ✅ 6.9 | — | — | ✅ (se presenti) |
| Verifica pennone | — | ✅ 6.10 | ✅ (in 5.9.x) | ✅ (in 5.10.x) | ✅ (in 6.10.x) |
| Verifica deformabilità (v=100 km/h) | ✅ 4.6 | ✅ 6.11 (se presente) | ✅ 5.9.4 | ✅ 5.10.4 | ✅ 6.10.4 |
| Verifica a fatica (Palmgren-Miner) | — | — | ✅ 5.9.5 | ✅ 5.10.5 | ✅ 6.10.5 |
| Opere di fondazione | — | — | ✅ 5.10 | ✅ 5.11 | ✅ 6.11 |
| └─ Geometria | — | — | ✅ 5.10.1 | ✅ 5.11.1 | ✅ 6.11.1 |
| └─ Materiali | — | — | ✅ 5.10.2 | ✅ 5.11.2 | ✅ 6.11.2 |
| └─ Capacità portante / micropali | — | — | ✅ 5.10.3 | ✅ 5.11.3 | ✅ 6.11.3 |
| └─ Ribaltamento / scorrimento | — | — | ✅ 5.10.4 | ✅ 5.11.4 | ✅ 6.11.4 |
| └─ Fessurazione cls (wk SLE) | — | — | ✅ (se c'è) | ✅ (se c'è) | ✅ |

### 2.4 Blocco "Chiusura"

| Sezione | A | B | C | D | E |
|---|---|---|---|---|---|
| Conclusioni (tabella sfruttamenti η / α) | ✅ (5) | ✅ (7) | ✅ (6) | ✅ (6) | ✅ (7) |
| Firma ing. | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tabulati di calcolo (allegati) | — | — | — | — | ✅ (8) |

---

## 3. Decisione: quale variante usare come MASTER per il sistema?

**Scelta**: **variante C – Iliad standard (6 capitoli)** come base minima, con:
- sotto-variante C+SLE → variante D (attivabile con flag `combinazione_sle_dedicata = True`)
- sotto-variante C+PRE → aggiungere capitolo "Preesistenze" (variante E, attivabile con flag `ha_preesistenze = True`)
- sotto-variante B (Wind Tre full) → ottenibile da C spostando "Fonti/LC" come Cap.1 + aggiungendo Cap.2 "Stato conservazione"
- sotto-variante A (Wind Tre minimal) → ottenibile da C rimuovendo Cap.1 "Fonti/LC"

**Architettura template**: 1 master + 4 flag boolean/enum per coprire le 5 varianti.

```yaml
relsta_config:
  variante: C        # A | B | C | D | E
  ha_fonti_lc: True
  ha_stato_conservazione: False
  ha_preesistenze: False
  combinazione_sle_dedicata: False
  ha_tabulati_allegati: False
  # Operatori ospitati
  gestori: [iliad, wind_tre, cellnex, inwit, vodafone, fastweb, tim]
  # Elementi strutturali
  ha_puntoni: False
  ha_stralli: False
  ha_pennone: True
  # Opere civili
  tipo_fondazione: micropali  # micropali | plinto | platea | travi_rovesce
```

---

## 4. Sezioni ricorrenti — content boilerplate da riusare

### 4.1 Normativa (identica in tutti i 9 file, salvo edizioni)
- DM 17/01/2018 — "Aggiornamento NTC" (NTC 2018)
- Circolare n. 7 del 21/01/2019 — "Istruzioni per l'applicazione dell'NTC 2018"
- Legge 05/11/1971 n. 1086 — opere in c.a., c.a.p., a struttura metallica
- Legge 02/02/1974 n. 64 — provvedimenti per costruzioni in zone sismiche
- CNR-UNI 10011/88 — "Costruzioni di acciaio. Istruzioni per il calcolo"
- CNR DT 207/2008 — "Istruzioni per la valutazione delle azioni e degli effetti del vento"
- EC3 parte 1-1 (EN 1993-1-1) — "Strutture di acciaio. Regole generali e regole per gli edifici"
- EC3 parte 3-1 (EN 1993-3-1) — "Torri, pali e camini. Torri e pali"
- EC3 parte 1-9 (EN 1993-1-9) — "Fatica" (solo per variante con 5.9.5)

### 4.2 Materiali (identici salvo sezioni del palo)
- Acciaio strutturale palo: **S355J0 / S355J2** (fyk = 355 MPa, ftk = 510 MPa, γM0 = 1.05, γM1 = 1.05, γM2 = 1.25)
- Bulloneria: **classe 8.8** (fyb = 640 MPa, ftb = 800 MPa); dadi **classe 8**
- Zincatura: **UNI EN ISO 1461** (tutti gli elementi esterni)
- Calcestruzzo fondazione: **C25/30 XC2** (fck = 25 MPa, fcd = 14.11 MPa, Ecm = 31476 MPa)
- Acciaio armature: **B450C** (fyk = 450 MPa, fyd = 391.3 MPa)
- Tirafondi: **classe 5.6** o **classe 8.8** a seconda del progetto originale

### 4.3 Combinazioni di carico (identiche in C/D/E)
- SLU fondamentale: γG1=1.3, γG2=1.3, γQ1=1.5 (sfavorevoli); γG1=1.0, γG2=1.0, γQ1=0 (favorevoli)
- SLE rara: γG1=1.0, γG2=1.0, γQ1=1.0
- SLE frequente: γG1=1.0, γG2=1.0, ψ1j·Qk
- Sismica: E + G1 + G2 + ψ2j·Qkj (ψ2 vento = 0 per pali TLC snelli)
- Ribaltamento (EQU): γG1=1.1 (0.9 fav), γG2=1.1 (0.9 fav), γQ1=1.5 (0 fav)

### 4.4 Codice di calcolo (identico in tutti i 9)
- **Straus7 rel. 2.2.3** (G+D Computing, HSH Srl) — validato secondo §10.2 NTC 2018 con test di affidabilità su modello monotronco.
- Output standard: Nx, Ty, Tz, Mx, My, Mz per ogni beam; reazioni vincolari al piede; deformate modali; tensioni Von Mises.

### 4.5 Formule di verifica ricorrenti

#### 4.5.1 Unioni flangiate — α-factor
Calcolo dell'area efficace attorno al bullone:
```
δ = √[(de² − db²)/At]
se δ ≤ 2.45:
    α = 0.0709 − 0.2491·δ + 0.3652·δ² − 0.1372·δ³ + 0.0156·δ⁴
se δ > 2.45:
    α = 0.197 + 0.0815·(δ − 2.45)
```
- `de` = diametro esterno area efficace
- `db` = diametro del bullone
- `At` = area di trazione del bullone

Forza di trazione limite:
```
trif = 1.10 · √α · √{(fEd/fyd) · [(de − dt)/db] · At}
```

#### 4.5.2 Verifica bullone a trazione (EC3 1-8)
```
Ft,Rd = 0.9 · ftb · Ares / γM2
η = Ft,Ed / Ft,Rd ≤ 1
```

#### 4.5.3 Verifica bullone a taglio (EC3 1-8)
```
FV,Rd = 0.6 · ftb · Ares / γM2
η = FV,Ed / FV,Rd ≤ 1
```

#### 4.5.4 Combinazione taglio-trazione (EC3 §3.6.1)
```
a = [FV,Ed / FV,Rd] + [Ft,Ed / (1.4 · Ft,Rd)] ≤ 1
```

#### 4.5.5 Verifica deformabilità (v_SLE = 100 km/h → p = 482 N/m²)
- Rotazione sommità: θ ≤ HPBW/2 (tipicamente 0°60' = 1° per parabole MW a banda stretta)
- Spostamento in sommità: ≤ H/100 (raccomandato EC3 parte 3-1)

#### 4.5.6 Verifica fatica (Palmgren-Miner, EC3 1-9)
```
D = Σ (ni / Ni) ≤ 1.0
```
con ni = numero cicli effettivi, Ni = numero cicli sopportati (curva S-N detail category).
Categorie dettaglio ricorrenti:
- Saldatura testa-testa tronchi palo: **Δσc = 71 MPa**
- Flangia bullonata circolare: **Δσc = 50 MPa** (tensioni secondarie)
- Saldatura d'angolo attacco pennone: **Δσc = 36 MPa**

### 4.6 Conclusioni — formato tabella sfruttamenti

Formato ricorrente (LT032, LU55041_002, RM823):
```
ELEMENTO                   η_max [%]   Verifica
Palo (tronco critico)      29.7        ✓
Stralli                    67.4        ✓
Flange bullonate           31.5        ✓
Puntoni                    34.3        ✓
Piastra base + tirafondi   xx.x        ✓
Deformabilità parabole     0.2946°     ✓ (<1°)
Fatica (se presente)       87.3        ✓
Ribaltamento               85.6        ✓
Fondazione                 xx.x        ✓
```

---

## 5. Cosa estrarre ancora

1. **Testo boilerplate esatto** di ogni sezione ricorrente (Cap. Normativa, Cap. Materiali, Cap. Codice di calcolo) → file `references/boilerplate-sezioni.md`
2. **Formule numeriche complete** con verifica numerica (da testo PO008 che ha 6314 righe, il più ricco) → file `references/formule-verifiche.py`
3. **Template DOCX strutturati** per ogni variante (A/B/C/D/E) → `assets/template_*.docx`
4. **JSON schema** per config RELSTA che guida la generazione → `schema/relsta_config.schema.json`

---

**Fine matrice. Task #27 completato.**
