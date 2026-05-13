# Progettazione geotecnica — NTC 2018 Cap. 6

## Principi generali (§ 6.1)

La progettazione geotecnica riguarda:
- **Opere di fondazione** (superficiali e profonde)
- **Opere di sostegno** (muri, paratie, tiranti)
- **Fronti di scavo e rilevati**
- **Stabilità dei pendii naturali e artificiali**
- **Consolidamento e miglioramento dei terreni**
- **Gallerie e opere in sotterraneo**

Le verifiche geotecniche riguardano sia gli **SLU** (stabilità globale, capacità portante, scorrimento, ribaltamento, galleggiamento) sia gli **SLE** (cedimenti ammissibili, distorsioni angolari, compatibilità con la sovrastruttura).

---

## Approcci progettuali (§ 2.6.1 e § 6.4)

NTC 2018 prevede due approcci per le verifiche SLU geotecniche (GEO).

### Approccio 1 (Design Approach 1 — DA1)

Due combinazioni distinte, **la più sfavorevole governa**:

**Combinazione 1 (A1 + M1 + R1)** → verifica strutturale con γF massimi sulle azioni; resistenze parziali basse sui parametri; R1 = 1.0.

**Combinazione 2 (A2 + M2 + R2)** → verifica geotecnica con γF ridotti sulle azioni; resistenze parziali alte sui parametri terra.

### Approccio 2 (Design Approach 2 — DA2)

**Combinazione unica (A1 + M1 + R3)** — γF massimi sulle azioni, nessuna riduzione dei parametri del terreno, γR massimi sulle resistenze globali.

### Quale approccio si applica?

| Tipo di verifica | Approccio |
|------------------|-----------|
| Capacità portante fondazioni superficiali | **DA2** (di norma in Italia) |
| Scorrimento fondazioni | DA2 |
| Capacità portante pali | DA1 o DA2 |
| Muri di sostegno | DA1 |
| Stabilità globale pendii | DA1 — Combinazione 2 |
| Fronti di scavo | DA1 — Combinazione 2 |

---

## Coefficienti parziali geotecnici (NTC Tab. 6.2.I e 6.2.II)

### Coefficienti parziali sulle azioni γF (Tab. 6.2.I)

| Azione | Effetto | γF (A1) | γF (A2) |
|--------|---------|---------|---------|
| Permanenti strutturali G1 | Sfavorevoli | 1.3 | 1.0 |
| Permanenti strutturali G1 | Favorevoli | 1.0 | 1.0 |
| Permanenti non strutturali G2 | Sfavorevoli | 1.5 | 1.3 |
| Permanenti non strutturali G2 | Favorevoli | 0.0 | 0.0 |
| Variabili Q | Sfavorevoli | 1.5 | 1.3 |
| Variabili Q | Favorevoli | 0.0 | 0.0 |

### Coefficienti parziali sui parametri del terreno γM (Tab. 6.2.II)

| Parametro | Simbolo | γM (M1) | γM (M2) |
|-----------|---------|---------|---------|
| Tangente dell'angolo di attrito | γtan φ' | 1.00 | 1.25 |
| Coesione efficace | γc' | 1.00 | 1.25 |
| Resistenza non drenata | γcu | 1.00 | 1.40 |
| Peso dell'unità di volume | γγ | 1.00 | 1.00 |

Valori di progetto:
```
tan φ'd = tan φ'k / γtan φ'
c'd     = c'k     / γc'
cu,d    = cu,k    / γcu
```

---

## Coefficienti parziali sulle resistenze γR

### Fondazioni superficiali (NTC Tab. 6.4.I)

| Verifica | γR (R1) | γR (R2) | γR (R3) |
|----------|---------|---------|---------|
| Capacità portante | 1.00 | 1.80 | 2.30 |
| Scorrimento | 1.00 | 1.10 | 1.10 |

### Fondazioni su pali (NTC Tab. 6.4.II)

| Verifica (pali infissi, trivellati, a elica) | γR |
|---------------------------------------------|-----|
| Resistenza di punta (verticali a compressione) | 1.15÷1.35 |
| Resistenza laterale | 1.15÷1.30 |
| Resistenza a trazione | 1.25÷1.40 |
| Resistenza trasversale | 1.30 |

### Muri di sostegno (NTC Tab. 6.5.I)

| Verifica | γR (R1) | γR (R2) | γR (R3) |
|----------|---------|---------|---------|
| Capacità portante fondazione | 1.00 | 1.00 | 1.40 |
| Scorrimento | 1.00 | 1.00 | 1.10 |
| Ribaltamento | 1.00 | 1.00 | 1.15 |
| Resistenza del terreno a valle | 1.00 | 1.00 | 1.40 |

---

## Capacità portante fondazioni superficiali

### Formula generale di Terzaghi-Brinch Hansen (per Approccio 2)

Carico limite di progetto:
```
qlim = c'·Nc·sc·dc·ic + q·Nq·sq·dq·iq + 0.5·γ·B'·Nγ·sγ·dγ·iγ
```
dove:
- c' = coesione efficace (per terreni coesivi)
- q = sovraccarico alla profondità di imposta (γ·D)
- γ = peso unità di volume sotto la fondazione
- B' = larghezza effettiva (ridotta per eccentricità: B' = B - 2·eB)
- Nc, Nq, Nγ = fattori di capacità portante (funzione di φ')
- s_i = fattori di forma (fondazione quadrata/rettangolare/circolare)
- d_i = fattori di profondità
- i_i = fattori di inclinazione del carico

Fattori di capacità portante (Meyerhof):
```
Nq = e^(π·tanφ') · tan²(45 + φ'/2)
Nc = (Nq - 1) · cot(φ')                  [per φ' > 0]
Nγ = (Nq - 1) · tan(1.4·φ')              [formula di Vesic]
```

### Verifica semplificata
```
Rd = qlim · A' / γR  ≥  Ed = NEd
```
dove A' = B'·L' (area effettiva).

---

## Cedimenti ammissibili (§ 6.4.2.2)

I cedimenti di una fondazione devono essere compatibili con:
- la tollerabilità della sovrastruttura (cedimenti assoluti)
- la distorsione angolare ammissibile (cedimenti differenziali)

### Valori indicativi di cedimenti ammissibili

| Tipo edificio | s_amm (cedim. totale) | β_amm (distorsione angolare) |
|---------------|----------------------|------------------------------|
| Edifici residenziali/uffici | 25 mm | 1/500 ÷ 1/300 |
| Edifici industriali | 50 mm | 1/300 ÷ 1/200 |
| Edifici muratura storica | 10-15 mm | 1/1000 ÷ 1/500 |
| Strutture rigide con carroponte | 25 mm | 1/500 |
| Macchinari sensibili | 5-10 mm | 1/1000 |

### Calcolo dei cedimenti elastici (NTC § 6.4.2.2 — metodo edometrico)
```
s = Σ (Δσi · Hi) / Es,i
```
con:
- Δσi = incremento di tensione verticale nello strato i (metodo di Boussinesq / Steinbrenner)
- Hi = spessore dello strato
- Es,i = modulo edometrico strato i (da prove edometriche o correlazioni con NSPT/qc)

---

## Verifica al galleggiamento (UPL — Uplift) — § 6.2.4.2

Per strutture parzialmente o totalmente interrate sotto falda:
```
Vdst,d ≤ Gstb,d + Rd
```
dove:
- Vdst,d = azione destabilizzante (spinta idrostatica dell'acqua) · γF,dst
- Gstb,d = azione stabilizzante (pesi propri strutturali e di terreno) · γF,stb
- Rd = eventuale resistenza addizionale (ancoraggi, attrito laterale)

Coefficienti parziali UPL (Tab. 6.2.III):

| Azione | γF,dst | γF,stb |
|--------|-------|--------|
| Permanente (acqua, peso proprio) | 1.10 | 0.90 |
| Variabile | 1.50 | 0.00 |

### Esempio pratico — piano interrato sotto falda
```
Peso struttura + copertura carico: Gk = 1500 kN
Spinta idrostatica (falda a -3m dal pavimento): U = 1800 kN

Verifica UPL:
  Vdst,d = 1.10 · 1800 = 1980 kN
  Gstb,d = 0.90 · 1500 = 1350 kN

1980 > 1350 → NON VERIFICATO → richiedere pali/ancoraggi o incremento zavorra
```

---

## Verifica HYD — moti di filtrazione — § 6.2.4.3

Per scavi sotto falda con possibilità di sollevamento del fondo:
```
u_dst,d ≤ σ_stb,d
```
u_dst,d = pressione interstiziale destabilizzante (γF,dst = 1.30)
σ_stb,d = tensione totale verticale stabilizzante (γF,stb = 0.90)

---

## Fondazioni su pali

### Resistenza per prove di carico (approccio statico — preferito)
```
Rc,d = Rc,k / γR
```
Rc,k determinata tramite:
1. **Prove di carico su pali in vera grandezza** (load test) → Rc,k = min(Rc,m) / ξ1 o media / ξ2 (tab. 6.4.III)
2. **Correlazioni con prove in sito** (SPT, CPT) → Rc,k da formule dirette
3. **Metodi di calcolo analitici** su base parametri geotecnici

### Formula statica analitica
```
Rc,k = Rb,k + Rs,k
     = qb,k · Ab + Σ (τs,i,k · As,i)
```
- Rb,k: resistenza di punta (base)
- Rs,k: resistenza laterale per attrito
- qb,k: tensione limite di rottura sotto la punta
- τs,i,k: attrito laterale caratteristico nello strato i

Fattori ξ (incertezza da numero di prove): Tab. 6.4.IV NTC.

---

## Opere di sostegno

### Spinta attiva — metodo di Coulomb
```
Ka = cos²(φ'-θ) / [cos²θ · cos(θ+δ) · (1 + √(sen(φ+δ)·sen(φ-β)/(cos(θ+δ)·cos(θ-β))))²]
```
in condizioni geometriche semplificate (parete verticale, δ=0, β=0):
```
Ka = tan²(45 - φ'/2)
Kp = tan²(45 + φ'/2)
```

### Spinta sismica — formula di Mononobe-Okabe
Per muri in zona sismica, spinta attiva incrementata da azione sismica orizzontale/verticale:
```
Ka,E = f(φ', θ, δ, β, kh, kv)
```
con kh = β_m · ag · S/g (coefficiente sismico orizzontale per muro), kv = ±0.5·kh.

Per muri ordinari: β_m = 1.0 (NTC § 7.11.6).

### Verifica muri — combinazioni SLU
1. **Capacità portante fondazione** (DA1 combinazione M2, verifica in A2+M2+R2)
2. **Scorrimento alla base** (R2 per scorrimento)
3. **Ribaltamento** (da intendere come verifica d'equilibrio; in NTC 2018 considerata nelle verifiche GEO)
4. **Stabilità globale** (DA1 combinazione M2 con pendii)

---

## Stabilità dei pendii (§ 6.3)

### Metodi di equilibrio limite (più usati)
- **Bishop semplificato** (superficie circolare, terreni coesivi-attritivi)
- **Janbu semplificato** (superficie non circolare)
- **Morgenstern-Price** (rigoroso, per casi generali)

### Verifica fattore di sicurezza
```
Fd = resistenze / sollecitazioni ≥ 1.0
```
In NTC: uso DA1 Combinazione 2 (parametri del terreno ridotti M2, azioni A2).

### Valori minimi di Fd in condizioni statiche (non sismico)
| Tipo pendio | Fd min |
|-------------|--------|
| Pendii naturali | 1.2 ÷ 1.3 |
| Scarpate di scavo temporanee | 1.1 ÷ 1.2 |
| Scarpate di rilevato stradale | 1.3 |
| Pendii protetti strutture esistenti | 1.5 |

In condizioni sismiche: Fd ≥ 1.0 con kh (coefficiente sismico) applicato.

---

## Liquefazione — § 7.11.3.4

In presenza di terreni granulari saturi (sabbie fini e limose), valutare il rischio di liquefazione.

### Criteri di esclusione (indicativi, una condizione basta)
- Magnitudo Mw < 5
- ag · S < 0.1 g
- Falda profonda (≥ 15 m dal p.c.)
- Terreno ben addensato (NSPT,corretto > 30)
- Granulometria con Cu > 3.5 e frazione fine > 20%

Se nessuna condizione è soddisfatta → verifica con metodo semplificato (Seed & Idriss 1971, aggiornato da Youd et al. 2001):
```
FS,liq = CRR / CSR ≥ 1.25  (soglia di sicurezza)
```
- CRR (Cyclic Resistance Ratio) da NSPT corretti o qc CPT
- CSR (Cyclic Stress Ratio) = 0.65 · (amax/g) · (σv / σ'v) · rd

---

## Documentazione geotecnica

### Relazione geologica (firmata dal geologo abilitato)
- Inquadramento geologico-geomorfologico
- Stratigrafia ricostruita
- Idrogeologia (falde, permeabilità)
- Sismicità e categoria di sottosuolo
- Interpretazione delle indagini

### Relazione geotecnica (ingegnere o geologo)
- Parametri di progetto del terreno (con FC o statistiche)
- Schema di calcolo delle fondazioni
- Verifiche SLU e SLE (capacità portante, cedimenti)
- Compatibilità con la sovrastruttura

### Documentazione indagini
- Piano delle indagini approvato (§ 6.2.1)
- Risultati sondaggi (stratigrafie, SPT, CPT, prove in sito)
- Rapporti di laboratorio (prove di taglio, edometriche, granulometriche)

---

## Checklist operativa progettazione geotecnica

### Fase 1 — Inquadramento
- [ ] Acquisizione relazione geologica del sito
- [ ] Definizione stratigrafia significativa
- [ ] Individuazione falda freatica
- [ ] Categoria di sottosuolo per spettro sismico (A/B/C/D/E)
- [ ] Classificazione topografica (T1/T2/T3/T4)

### Fase 2 — Caratterizzazione parametrica
- [ ] Parametri caratteristici (γ, c', φ', cu, E, Es) per ogni strato
- [ ] Valori di progetto con γM (M1 o M2)
- [ ] Livelli di affidabilità delle prove eseguite

### Fase 3 — Verifiche SLU
- [ ] Capacità portante (DA2: A1+M1+R3)
- [ ] Scorrimento (se applicabile)
- [ ] UPL (galleggiamento) se falda interferisce
- [ ] HYD (moti di filtrazione) se scavi sotto falda
- [ ] Stabilità globale (se pendii prossimi)

### Fase 4 — Verifiche SLE
- [ ] Cedimenti totali ≤ s_amm
- [ ] Cedimenti differenziali / distorsioni ≤ β_amm
- [ ] Cedimenti di consolidazione nel tempo (argille)

### Fase 5 — Verifiche sismiche
- [ ] Amplificazione sismica locale (SS, ST)
- [ ] Rischio liquefazione (se condizioni pertinenti)
- [ ] Interazione terreno-struttura (SSI se rilevante)
- [ ] Spinte incrementate sulle strutture di sostegno (Mononobe-Okabe)

---

## Riferimenti normativi complementari

- **EN 1997-1 (Eurocodice 7 parte 1)**: progettazione geotecnica — principi generali
- **EN 1997-2 (Eurocodice 7 parte 2)**: prove di laboratorio e in sito
- **UNI 11531-1**: classificazione dei terreni ai fini sismici
- **CNR-DT 207/2008**: azione del vento sulle strutture
- **D.M. 11/03/1988**: norme tecniche ancora richiamate per prove storiche (superato da NTC)
