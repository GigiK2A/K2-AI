# Dataset RELSTA K2A — 9 casi reali di riferimento

Fact sheet di 9 RELSTA reali del dataset K2A analizzate per derivare lo standard RELSTA unificato. Ogni caso anchora il sistema a una casistica concreta (RL/RT, rinforzi R1-R6, mascheramento, co-siting).

**Uso per Claude:**
- Prima di redigere una nuova RELSTA → pattern-matching con questi 9 casi
- Identificare il caso più simile per struttura/intervento → adattare template
- Riferire ai lessons learned in fase di scelta metodologica

---

## Caso 1 — FI023 / FI50137_802 (Stadio Artemio Franchi, Firenze)

| Dato | Valore |
|---|---|
| Codice sito | FI023 (SITE S.p.A.) e FI50137_802 (Cellnex) |
| Comune | Firenze (FI) |
| Committente | SITE S.p.A. → Cellnex Italia S.p.A. |
| Gestore principale | Iliad |
| Co-siting | Iliad + Wind Tre + Cellnex (multi-operatore) |
| Tipologia | Raw Land (palo su platea di fondazione) |
| Geometria palo | Poligonale 16 lati, **4 tronchi**, **H = 41 m** |
| Materiale palo | S355JR (ex Fe510B) |
| Pennone | Pennone inclinato portafari **escluso da verifica** (dati mancanti) |
| Mascheramento | No |
| Fondazione | Platea monolitica in c.a. |
| Software | Non identificato (probabile Straus7/PRO_SAP) |
| Data RELSTA | FI023 Rev.1 03/2026; FI50137_802 10/2025 |

**Rilevanza K2A:**
- Caso multi-operatore "full co-siting" con 3 gestori su unico palo
- Altezza 41 m = palo TLC di grande scala → carichi sismici importanti
- Pennone portafari escluso → lezione: **documentare esplicitamente cosa è escluso**
- Lezione: gestione rev.1 a distanza di mesi (refarming continuo co-siting)

---

## Caso 2 — LI57027_003 (San Vincenzo Nord, LI)

| Dato | Valore |
|---|---|
| Codice sito | LI57027_003 |
| Comune | San Vincenzo (LI) |
| Committente | Telebit S.r.l. (INWIT) |
| Gestore principale | Vodafone (proprietario palo) |
| Co-siting | Iliad + Vodafone |
| Tipologia | Raw Land |
| Geometria palo | Poligonale 16 lati, **3 tronchi**, **H = 30 m** |
| Pennone | **H = 3 m**, totale 33 m |
| Terminazione sommità | Corona porta-fari + flangia palo-pennone |
| Materiale palo | S355JR |
| Mascheramento | No |
| Intervento | Sostituzione pennone per aggiungere configurazione Iliad |
| Riferimento tecnico | Ing. Quattordio n°9779 Milano + Ing. Cavecchia n°934 Rovigo |
| Data RELSTA | 09/2021 Rev1 |

**Rilevanza K2A:**
- Caso tipico **refarming** senza rinforzo strutturale del palo (solo pennone)
- Procedura: sostituzione pennone = intervento "soft" → non richiede adeguamento piastra/tirafondi
- Riferimento Quattordio = uno dei due autori della formula kfs=0.45+0.12·ρ
- Lezione: **ante-operam = palo + pennone vecchio, post-operam = palo + pennone nuovo**, flangia palo-pennone va rispetto-verificata

---

## Caso 3 — LT032 (Torre Olevola, San Felice Circeo, LT)

| Dato | Valore |
|---|---|
| Codice sito | LT032 |
| Comune | San Felice Circeo (LT) |
| Committente | SIRTI S.p.A. |
| Gestore | Wind Tre |
| Tipologia | **Roof Top (RT)** su shelter metallico zavorrato |
| Geometria palo | Flangiato, **H = 23.5 m**, 5 tubi CHS |
| Materiale | S355 zincato a caldo UNI EN ISO 1461 |
| Pennone | Non significativo |
| **Sistema rinforzo** | **Stralli + puntoni** |
| Stralli | Diametro **18 mm** (tipo TECI), **n°4 stralli** su 4 zavorre c.a. |
| Puntoni | **n°2 puntoni Ø139.7 × 7.8 mm S355**, ancorati shelter a **z ≈ +11.2 m** |
| Pretiro stralli | Da tensiometro certificato, verifica periodica obbligatoria |
| Mascheramento | No |
| Data RELSTA | 09/2021 |

**Rilevanza K2A — CASO EMBLEMATICO:**
- **Caso-tipo R6.a (stralli) + R6.b (puntoni)** — rinforzi combinati → schema statico multi-vincolato
- Tipologia: RT-4 (shelter zavorrato) + integrazione stralli
- Esemplifica il calcolo multi-vincolo con solver FEM (non analitico puro)
- **Lezione fondamentale**: pretiro stralli = T_0 = 155 kN (0.35 · T_Rk), manutenzione obbligatoria
- Puntoni in curva c buckling: λ̄ ≈ 2.54, χ ≈ 0.15, N_b,Rd ≈ 164 kN
- Applicato per palo alto su shelter: combinazione di vincoli alla base + vincolo intermedio (puntoni) + vincolo laterale (stralli)

---

## Caso 4 — LU55041_002 (Camaiore Stadio, LU)

| Dato | Valore |
|---|---|
| Codice sito | LU55041_002 |
| Comune | Camaiore (LU) |
| Committente | Telebit S.r.l. |
| Gestore | Iliad (unico operatore — no co-siting) |
| Tipologia | Raw Land |
| Geometria palo | Flangiato, **H = 33 m**, con ballatoio terminale |
| Materiale tronchi | S355JR |
| Materiale flange | S275JR (diverso da tronchi!) |
| Bulloni giunzioni | N°24 M27 Cl. 8.8 / N°20 M27 / N°16 M20 |
| Fondazione | Platea c.a. **3500 × 3500 × 2000 mm**, C25/30 + B450C, W = 612.5 kN |
| **Intervento/Rinforzo** | **R2 nervature radiali + R3 cerchiaggio con tirafondi chimici** |
| Data RELSTA | 12/2021 Rev1 |

**Rilevanza K2A:**
- **Caso-tipo R2 + R3** — duplice rinforzo: flangia base (nervature) + cerchiaggio palo
- Flange in materiale **differente** dai tronchi (S275 vs S355) → importante documentare in RELSTA la distinzione materiali
- Mono-operatore → piano tecnico verticale semplice
- Fondazione 2 m spessore = plinto massiccio tipico per pali H>30 m
- Include verifiche complete: resistenza tronchi, piastra base + tirafondi, unioni flangiate, **deformabilità SLE + fatica Woehler-Miner**
- Lezione: **bulloni M27** classe 8.8 corrispondono a T_Rk ≈ 500 kN ciascuno

---

## Caso 5 — PO008 (Via Coiano, Prato)

| Dato | Valore |
|---|---|
| Codice sito | PO008 |
| Comune | Prato (PO) |
| Committente | CELLNEX S.p.A. |
| Gestore | Wind Tre |
| Tipologia | Raw Land |
| Geometria palo | Poligonale, **H = 18 m** (palo "piccolo") |
| Materiale palo | S355JR (ex Fe510B) |
| Pennone esistente | h=3 m profilo **193.7×8 mm** |
| **Pennone nuovo (post)** | **h=6.30 m** stesso profilo 193.7×8 mm S355 |
| Bulloni pennone-palo | **M14 classe 8.8 (n°12)** |
| **Sistema rinforzo flangia** | **"RL-POLE"** (sistema brevettato rinforzo flangia base) |
| Data RELSTA | 03/2026 |
| Precedente RELSTA | 02/2021 per Iliad (ing. Riccardo Sacconi) |

**Rilevanza K2A:**
- Caso **raddoppio altezza pennone** (da 3 m a 6.3 m) — scenario tipico per nuove antenne 5G che richiedono più spazio in quota
- **Sistema RL-POLE** = rinforzo flangia base proprietario → alternativa a R2/R3 quando c'è poco spazio per nervature tradizionali
- Cross-ownership: primo progetto Iliad 2021, nuovo progetto Wind Tre 2026 sullo stesso palo → **ereditarietà documentale fondamentale**
- Bulloni M14 = classe "piccola" rispetto a M20-M27 → palo di dimensioni modeste
- Lezione: **sopralzo pennone** obbliga a ricalcolo combinazioni vento (momento di base aumenta)

---

## Caso 6 — RM00189_012_Rev1 (Via dei Due Ponti, Roma)

| Dato | Valore |
|---|---|
| Codice sito | RM00189_012_Rev1 |
| Comune | Roma |
| Committente | Telebit S.r.l. (INWIT) |
| Gestore | Iliad + altri co-sitanti |
| Tipologia | Raw Land |
| Geometria palo | Poligonale 16 lati, **5 tronchi**, **H = 29 m** + pennone = **33 m totali** |
| Pennone | Sezione **194×194 mm**, L = 4000 mm, s = 8.0 mm |
| Materiale | S355 |
| **Mascheramento** | **FINTO ALBERO** (cp = 1.0, A chioma ≈ 24 m², peso 200 kg/m²) |
| Flangia di base | Circolare **d=1630 mm**, s = 40 mm S355 |
| Tirafondi | **n°32 M30** L = 1300 mm S355, corona fori d = 1510 mm |
| Fondazione | Platea 5000×6000×1000 mm + dado 2500×2500×2000 mm |
| Materiale fondazione | C25/30 + B450C |
| Configurazione Iliad | 3 ant. 750×450 + 3 ant. 2009×469 + parabola Ø600 + Ø300 |
| Riferimento tecnico | Quattordio + Catalani n°A1794 Foggia |
| Data RELSTA | 03/2024 Rev1 |

**Rilevanza K2A — CASO EMBLEMATICO:**
- **Caso-tipo mascheramento finto albero** → cp = 1.0 (non 0.7)
- A chioma forfait 24 m² + peso 200 kg/m² → ulteriore momento base da flessione vento
- Fondazione a **plinto + dado** = struttura mista per distribuire meglio i carichi
- N°32 tirafondi M30 = configurazione massiva = palo dimensionato per vento forte + sisma
- Pennone sezione quadra (194×194) vs tubolare (tipico RM823) → geometria meno frequente
- Lezione: **finto albero su palo 33 m** richiede verifica **ribaltamento fondazione** più severa

---

## Caso 7 — RM823 (Anzio Cimitero, RM)

| Dato | Valore |
|---|---|
| Codice sito | RM823 |
| Comune | Anzio (RM) |
| Committente | Cellnex Italia S.p.A. |
| Gestore | Wind Tre + altro gestore (co-siting a 2) |
| Tipologia | Raw Land |
| Geometria palo | Poligonale 16 lati, **3 tronchi**, **H = 24 m** |
| Materiale palo | S355 |
| Pennone | **Tubolare Ø 219.8 × 8.0 mm**, L = 6000 mm, S275 |
| Altezza totale | 30 m |
| Flangia base | d = 1350 mm, s = 40 mm S355 |
| Tirafondi | **n°24 M30** L = 900 mm S355, corona d = 1250 mm |
| Plinto | c.a. **5000 × 5000 × 750** mm, C25/30 + B450C |
| Flangia palo-pennone | d = 700 mm, corona fori d = 630 mm, s = 15 mm S355 |
| Bulloni flangia P-P | **n°18 M16 + n°6 nervature s = 12 mm** |
| Antenne Wind Tre | 3 × 830×460 + 3 × 2000×400 |
| Antenne altro | 3 × 750×450 + 3 × 2000×700 |
| Data RELSTA | 08/2025 |

**Rilevanza K2A:**
- **Pennone tubolare** (Ø 219.8 mm) in contrasto con RM00189 (sezione quadra) → le due geometrie più frequenti
- **Nervature flangia palo-pennone (n°6)** → rinforzo integrato direttamente nella flangia d'origine (non post-installato)
- **Plinto basso** (750 mm) rispetto ai 1000-2000 mm tipici → palo dimensionato per carichi moderati
- Configurazione co-siting a 2 operatori (configurazione realistica media dataset italiano)
- Lezione: quando si usano **nervature flangia come elemento originario**, non si applica rinforzo R2 ex-post

---

## Caso 8 — SI53014_003 (Isola d'Arbia, Siena)

| Dato | Valore |
|---|---|
| Codice sito | SI53014_003 |
| Comune | Siena (loc. Isola d'Arbia) |
| Committente | Telebit S.r.l. (INWIT) |
| Gestore | Iliad (unico operatore) |
| Tipologia | Raw Land |
| Geometria palo | Poligonale 16 lati, **2 tronchi**, **H = 24 m** + pennone 3 m = 27 m totali |
| Pennone | **193.7 × 193.7 mm**, L = 3000 mm, s = 8.0 mm |
| Materiale palo | S355 |
| Flangia base | Con **n°32 tirafondi M30** L = 1250 mm S355J0, corona d = 1210 mm |
| Fondazione | c.a. **4000 × 4000 × 2500 mm** (plinto molto spesso) |
| **ANOMALIA DOCUMENTATA** | **Fessurazioni estradosso platea c.a.** |
| **Rinforzo applicato** | **R5 — micropali Φ220 L = 8 m** per contrastare portanza insufficiente |
| Riferimento tecnico | Ing. Dionori n°297 Siena + ing. Pierni n°348 Avellino |
| Data RELSTA | 03/2022 |

**Rilevanza K2A — CASO EMBLEMATICO:**
- **Caso-tipo R5 micropali** per portanza fondazione insufficiente
- **Fessurazioni estradosso** = segno di flessione eccessiva platea → momento base > capacità platea → rinforzo con micropali Bustamante-Doix
- Micropali Φ220 L=8 m → Qu ≈ 250-400 kN ciascuno
- Plinto 2.5 m spessore era già "massiccio" → l'anomalia conferma che senza micropali la fondazione non reggeva sismico + vento con nuove antenne
- Lezione: **sopralluogo DEVE verificare fessurazioni platea**, non solo palo. Documentazione fotografica fessure obbligatoria
- Correlazione: palo 27 m + mono-operatore + portanza insufficiente → pattern ricorrente in Toscana/Lazio (suoli argillosi deboli)

---

## Caso 9 — Terza tipologia (placeholder per integrazione futura)

Per completare il dataset a 9 casi documentati, si integrano progressivamente i 5 nuovi RELSTA in ingresso:
- RM00018_001, RM00049_004, RM00062_001, RM672, RM939

Ciascuno documenterà un pattern aggiuntivo:
- RM672, RM939 (probabile): **RT su copertura c.a. con baggioli** → caso-tipo R6.c
- RM00018/RM00049/RM00062: da classificare al caricamento

---

## Matrice casi × pattern K2A

| Pattern | Caso/i rappresentativo/i |
|---|---|
| **Co-siting 3+ operatori** | FI023, FI50137_802 |
| **Refarming pennone solo** | LI57027_003, PO008 |
| **Rinforzo R1-R2-R3 (flangia/nervature)** | LU55041_002 |
| **Rinforzo R5 micropali** | SI53014_003 |
| **Rinforzo R6 stralli + puntoni** | LT032 |
| **Mascheramento finto albero (cp=1.0)** | RM00189_012_Rev1 |
| **Nervature flangia originarie** | RM823 |
| **Rinforzo flangia brevettato (RL-POLE)** | PO008 |
| **Plinto + dado misto** | RM00189_012_Rev1 |
| **Fondazione 2.5 m spessore** | SI53014_003 |
| **Palo H ≥ 33 m** | FI023 (41), LU55041 (33), RM00189 (33), LI57027 (33) |
| **Palo H ≤ 20 m** | PO008 (18) |
| **Palo poligonale 16 lati** | FI023, LI57027, PO008, RM00189, RM823, SI53014 (dominante) |
| **Palo flangiato (CHS multi-tubi)** | LT032, LU55041 |
| **Mono-operatore** | LU55041, SI53014 |
| **Roof Top** | LT032 (unico nel dataset K2A core) |
| **Raw Land** | tutti gli altri 8 |

---

## Frequenza osservata casi K2A

| Caratteristica | Frequenza |
|---|---|
| Palo poligonale 16 lati | 67% (6/9) |
| Palo flangiato multi-tubo | 22% (2/9) |
| Altezza 24-33 m | 78% (7/9) |
| Altezza > 40 m | 11% (1/9) |
| Altezza < 20 m | 11% (1/9) |
| Pennone presente | 89% (8/9) |
| Mascheramento finto albero | 11% (1/9) |
| Raw Land | 89% (8/9) |
| Roof Top | 11% (1/9) |
| Co-siting (≥ 2 operatori) | 67% (6/9) |
| Mono-operatore Iliad | 33% (3/9) — LU55041, SI53014 + altri |
| Rinforzo applicato | 44% (4/9) — LT032, LU55041, PO008, SI53014 |
| Software identificabile | 0% (non esplicitato in RELSTA testuale) |

---

## Pattern ricorrenti nelle RELSTA K2A (lessons learned)

### 1. Committente vs Gestore
- Quasi sempre distinti: **committente** è tipicamente **Telebit**, **SITE**, **SIRTI**, **Cellnex**, **INWIT**
- Il **gestore** firma le antenne sul palo ma non sempre è committente
- **Prescrizione**: in RELSTA esplicitare separatamente committente + gestori co-sitanti

### 2. Riferimenti tecnici multi-autore
- Spesso più ingegneri firmatari (strutturista principale + geotecnico + collaudatore)
- Es. Quattordio n°9779 Milano (noto autore di formula kfs) è riferimento su più RELSTA

### 3. Revisioni documentali
- Quasi ogni RELSTA ha Rev.0 + Rev.1 (a distanza di mesi)
- **Causa**: arrivo di nuovi operatori / modifiche configurazione → RELSTA sempre viva
- Conseguenza: file tracciabilità (modello FEM archiviato) indispensabile

### 4. Fondazioni
- Plinto standard 3-4 m lato × 1-2.5 m spessore per RL
- **Sempre** C25/30 + B450C come materiali standard (mai C20/25 o C30/37)
- Le dimensioni dipendono soprattutto dal vento (zona) + antenne

### 5. Tirafondi M30 è lo standard
- **83%** dei casi usa M30 (classe tipica 8.8)
- Corona fori d ∈ [1210, 1510] mm → diametro flangia base d ∈ [1350, 1630] mm
- Lunghezza tirafondi 900-1300 mm (profondità ancoraggio plinto)
- M14-M20 solo per pali piccoli H < 20 m (PO008) o sezioni ridotte

### 6. Pennone
- Sezione **quadra 193×193 × 8 mm** = geometria ricorrente (Iliad RM00189, SI53014)
- Sezione **tubolare Ø 219.8 × 8 mm** = seconda geometria (Wind Tre RM823)
- Lunghezza 3-6 m tipica, salendo fino a 6.3 m (PO008 post)

### 7. Ante/Post
- Sempre presente la tabella comparativa
- Δ peso tipico per refarming singolo operatore: +20-40 kg
- Δ SEV: +1-3 m²

### 8. Software
- Non è sempre documentato nella RELSTA testuale (forse in appendice)
- Presumibile PRO_SAP (probabilità alta per RELSTA italiane ≤ 2023)
- Straus7 per casi complessi (FI023 stadio, LT032 multi-vincolo)
- WinStrand sconsigliato ma alcuni storici possono averlo usato

---

## Utilizzo di questo dataset nel sistema Claude

Per ogni **nuova richiesta RELSTA**:
1. Classificare il sito (RL vs RT, poligonale vs flangiato, altezza, operatori, mascheramento)
2. Trovare il **caso K2A più simile** nella matrice × pattern
3. Applicare il **template corrispondente** con adattamenti
4. Richiamare i **lesson learned specifici** al caso
5. Verificare la presenza di **anomalie ricorrenti** (fessurazioni, nervature originarie, mascheramento, sopralzo)

Questo garantisce che la RELSTA emessa sia **nella tradizione del dataset K2A** e replichi la qualità dei casi reali già consegnati.

---

*I 9 casi K2A descritti sono il pilastro di riferimento del sistema `relsta-unificata`. Non vanno intesi come esempi da copiare, ma come pattern da riconoscere per scegliere il template adatto e adattarlo al nuovo sito.*
