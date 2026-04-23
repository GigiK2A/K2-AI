# C.a.p. e Strutture composte acciaio-calcestruzzo

## PARTE 1 — Calcestruzzo armato precompresso (c.a.p.) — NTC 2018 § 4.1.8

### Tipologie di precompressione

| Tipo | Descrizione | Uso tipico |
|------|-------------|-----------|
| **Pretensione (pre-tesatura)** | Cavi tesi prima del getto del cls; rilascio dopo maturazione → aderenza diretta | Travi prefabbricate, pannelli alveolari, solai |
| **Post-tensione con cavi aderenti** | Cavi in guaine iniettate dopo tesatura (getto cls → tesatura → iniezione) | Ponti, travi lunghe, serbatoi |
| **Post-tensione con cavi non aderenti** | Cavi in guaine con grasso anti-corrosivo (no iniezione) | Solai piani con post-tensione, cisterne |
| **Precompressione esterna** | Cavi esterni alla sezione, deviati da selle | Ponti, rinforzi esistenti |

### Materiali

#### Calcestruzzo per c.a.p.
- Classe minima: **C28/35** (fck ≥ 28 MPa)
- Valori tipici: C35/45, C40/50, C45/55
- Maturazione prima della tesatura: fcm(t) ≥ 25 MPa (pretensione) o ≥ 30 MPa (post-tensione)
- γc = 1.5 (SLU) — stesso del c.a. ordinario

#### Acciai da precompressione (NTC § 11.3.3)
| Tipo | Designazione | fp0,1k (MPa) | fptk (MPa) |
|------|-------------|-------------|-----------|
| Filo | Y1860/1770 | 1670 | 1860 |
| Trefolo 7 fili | Y1860 | 1670 | 1860 |
| Barra | Y1230 | 1080 | 1230 |

γs,p = 1.15 per SLU.
Tensione ammissibile in tesatura: σp,max = min(0.80 fptk ; 0.90 fp0,1k)
Tensione dopo ancoraggio (tempo 0): σp,0 = min(0.75 fptk ; 0.85 fp0,1k)

### Stati limite di esercizio (SLE) — NTC Tab. 4.1.IV

Le tensioni ammissibili al cls e all'acciaio dipendono dalle condizioni di esposizione ambientale e dalla durabilità richiesta.

#### Tensioni in compressione del calcestruzzo
| Condizione | Combinazione | Limite |
|------------|-------------|--------|
| Stato iniziale (rilascio, trasferimento precompressione) | Quasi-permanente | σc ≤ 0.60 fck(t) |
| Esercizio, ambienti aggressivi XD/XS | Caratteristica | σc ≤ 0.60 fck |
| Esercizio, ambiente ordinario XC | Caratteristica | σc ≤ 0.60 fck |
| Esercizio | Quasi-permanente | σc ≤ 0.45 fck |

#### Tensioni in trazione del calcestruzzo
| Condizione | Limite |
|------------|--------|
| XC ordinario, caratteristica | σct ≤ fctm (evitare fessurazione) |
| XD/XS aggressivo, frequente | σct ≤ 0 (sezione completamente compressa) |

#### Fessurazione (NTC § 4.1.2.2.4)
Limiti di apertura fessure **wk** in esercizio:

| Classe esposizione | Comb. frequente | Comb. quasi-permanente |
|--------------------|----------------|----------------------|
| XC1, XC2 | wk ≤ 0.2 mm | wk ≤ 0.2 mm |
| XC3, XC4 | wk ≤ 0.3 mm | wk ≤ 0.2 mm |
| XD/XS (precompresso) | decompressione | wk ≤ 0.2 mm |

### Perdite di precompressione

Le perdite istantanee e differite riducono la forza di precompressione nel tempo.

#### Perdite istantanee (al momento dell'ancoraggio)
- **Attrito lungo il cavo** (post-tensione): Δσp,μ = σp,0 · (1 - e^(-μ·(θ + k·x)))
  - μ = coeff. attrito (0.17–0.25 tipico)
  - θ = angolo totale di deviazione [rad]
  - k = coeff. deviazione involontaria (0.004–0.010 m⁻¹)
  - x = lunghezza del cavo [m]
- **Rientro dell'ancoraggio**: Δσp,sl = Δl · Ep / L (tipico Δl = 2-6 mm)
- **Accorciamento elastico del cls**: Δσp,el = Ep · σcp / Ecm

#### Perdite differite (nel tempo)
- **Ritiro del cls**: Δσp,cs = Ep · εcs,∞ (tipicamente εcs,∞ ≈ 0.30–0.45 ‰)
- **Viscosità (creep)**: Δσp,cr = Ep · (σcp / Ecm) · φ(t,t0)
  - φ(t,t0) = coeff. di viscosità (1.5–3.5 per t=∞)
- **Rilassamento dell'acciaio**: Δσp,rel ≈ 2–8% di σp,0 (classe 2 dei trefoli)

**Perdita totale tipica: 15–25% della forza iniziale.**

### Dominio di rottura N-M

La sezione in c.a.p. va verificata includendo la **forza di precompressione** come azione interna combinata con le azioni esterne (G, Q, sisma).

Verifica SLU a flessione:
```
MEd ≤ MRd = MRd(NEd,p + NEd,ext)
```

### Verifica a taglio (NTC § 4.1.6.1)

Per travi precompresse in assenza di armatura trasversale:
```
VRd,c = [0.18·k·(100·ρ1·fck)^(1/3) + 0.15·σcp] · bw·d
```
con σcp = NEd,p / Ac (tensione di compressione media dovuta alla precompressione).

La precompressione **aumenta** VRd,c perché σcp è in compressione.

### Zone di ancoraggio e diffusione

Verifica delle zone terminali sotto l'ancoraggio (post-tensione):
- Pressione sotto la piastra di ancoraggio ≤ fccd = α·fcd (confinamento)
- Armatura di spinta (split) calcolata per tensioni trasversali da diffusione

### Deposito e verifiche specifiche

Per opere in c.a.p. si applicano **certificazioni specifiche dei sistemi di precompressione** (ETA del sistema), oltre alla certificazione standard dei materiali:
- Sistema di tesatura certificato CE (ETAG 013)
- Certificato di benestare tecnico (CBT) per il sistema
- Registrazione delle operazioni di tesatura (libro di tesatura)

---

## PARTE 2 — Strutture composte acciaio-calcestruzzo (NTC § 4.3 + EC4)

### Campo di applicazione
- Travi miste acciaio-cls con connettori a taglio
- Solette collaboranti su lamiera grecata
- Colonne miste (acciaio + cls riempito o rivestito)
- Orizzontamenti misti
- Ponti misti acciaio-cls

### Riferimenti normativi
- **NTC 2018 § 4.3** — Progettazione strutture composte acciaio-cls
- **EN 1994-1-1 (Eurocodice 4)** — progettazione generale
- **EN 1994-1-2** — progettazione al fuoco
- **EN 1994-2** — ponti misti

### Principi di progettazione composita

La resistenza della sezione composta è determinata dalla **collaborazione** tra acciaio e cls tramite connettori a taglio. Si distinguono:
- **Connessione totale**: numero di connettori sufficiente a sviluppare la resistenza plastica completa della sezione
- **Connessione parziale**: numero ridotto di connettori → resistenza ridotta Mpl,Rd,part < Mpl,Rd,totale

### Trave composta su lamiera grecata

#### Larghezza efficace della soletta (EC4 § 5.4.1.2)
```
beff = b0 + Σ bei
```
dove:
- b0 = distanza tra assi connettori (tipicamente 0 se 1 fila)
- bei = min(Le/8 ; bi/2) con Le = lunghezza di continuità

Per travi semplicemente appoggiate: Le = L (luce)
Per travi continue: Le ≈ 0.7·L nelle campate, 0.25·(L1+L2) agli appoggi

#### Resistenza plastica a flessione (asse neutro nella soletta)
```
Nc = beff · xpl · 0.85·fcd       (compressione cls)
Na = As · fyd                     (trazione acciaio)
```
Se Na ≤ Nc,max (= beff·hc·0.85·fcd): asse neutro nella soletta
```
xpl = Na / (beff · 0.85·fcd)
Mpl,Rd = Na · (ha/2 + hp + hc - xpl/2)
```
dove ha = altezza profilo acciaio, hp = altezza costole lamiera, hc = altezza soletta piena.

#### Se asse neutro nell'acciaio (Na > Nc,max)
Analisi plastica con redistribuzione di zona compressa nell'anima del profilo.

### Connettori a taglio — Piolo Nelson

**Resistenza di progetto del singolo piolo (EC4 § 6.6.3.1):**

Rottura dell'acciaio:
```
PRd,1 = 0.8 · fu · π·d²/4 / γV        con γV = 1.25
```

Rottura del cls:
```
PRd,2 = 0.29 · α · d² · √(fck·Ecm) / γV
```
con α = 1 per hsc/d ≥ 4 ; α = 0.2·(hsc/d + 1) per 3 ≤ hsc/d ≤ 4

Resistenza adottata: **PRd = min(PRd,1, PRd,2)**

**Riduzione per lamiera grecata:**
- Lamiera trasversale: kt = 0.85 · b0/(hp·√n) (per n=1 piolo)
- Lamiera longitudinale: kl = 0.6 · b0/hp · (hsc/hp - 1) ≤ 1.0

### Numero di connettori (connessione totale)
```
n = Nc,f / PRd
```
Nc,f = min(Nc,max , Na) = forza longitudinale da trasferire nella luce a momento positivo.

**Connessione parziale**: possibile se n/nf ≥ 0.4 (ma genera riduzione di Mpl,Rd e freccia aumentata).

### Verifiche SLE

1. **Fessurazione** della soletta (agli appoggi in travi continue)
   - Armatura longitudinale minima 0.2% della sezione soletta piena in zona di momento negativo
   - wk ≤ 0.3 mm (XC3/XC4)

2. **Freccia** a breve e lungo termine
   - A breve: Ec,eff = Ecm  → sezione trasformata con n = Ea/Ec,eff
   - A lungo: considerare viscosità con coeff. ψL (ψL = 1.1·φ per carichi permanenti EC4 § 5.4.2.2)

3. **Vibrazioni** (uffici, commerciali): frequenza propria f1 ≥ 3 Hz

### Colonne miste (cls riempito in profilo scatolare)

Verifica semplificata SLU (EC4 § 6.7.3):
```
NRd = Aa · fyd + 0.85 · Ac · fcd + As · fsd
```
con:
- Aa = area acciaio profilo
- Ac = area cls riempito
- As = area armature longitudinali
- 0.85 → per profili rivestiti; **sostituire con 1.0** per profili tubolari riempiti di cls (confinamento)

Verifica instabilità con curve χ-λ come per colonne in acciaio (EC3) ma con modulo equivalente EI_eff.

### Solette con lamiera grecata

#### Fase di getto
- Lamiera sottoposta al peso del cls fresco + carichi di montaggio
- Verifica freccia δ ≤ L/180 (con L = luce di montaggio)

#### Fase di esercizio
- Azione composta: cls portante flessione + lamiera come armatura in trazione
- Resistenza da rottura lamiera/cls o scorrimento interfaccia
- Carico ammissibile da tabelle di progetto del produttore (es. A55/P600, HI-BOND A75)

---

## Confronto c.a. ordinario / c.a.p. / strutture composte

| Caratteristica | C.a. ordinario | C.a.p. | Composte acc-cls |
|----------------|---------------|--------|-----------------|
| Luce tipica (travi solai) | 5–8 m | 10–20 m | 8–15 m |
| Snellezza (h/L) | 1/10–1/15 | 1/20–1/30 | 1/20–1/25 |
| Peso proprio | Alto (25 kN/m³) | Medio-alto | Medio-basso |
| Velocità di costruzione | Lenta (getti + maturazione) | Media (prefabbricati) | Veloce (montaggio) |
| Costo | Basso | Medio-alto | Alto |
| Durabilità | Buona | Ottima con protezione | Buona con protezione anti-corrosione |
| Resistenza fuoco | Ottima | Ottima | Richiede protezione (intumescente/rivestimento) |

---

## Checklist operativa — c.a.p.

### Progettazione
- [ ] Definire forza di precompressione iniziale P0
- [ ] Determinare il tracciato dei cavi (posizione cdg cavo lungo la trave)
- [ ] Calcolare perdite istantanee e differite → Pt=∞ (valore di progetto)
- [ ] Verifiche SLU: momento resistente, taglio, torsione (se presente)
- [ ] Verifiche SLE: tensioni cls e acciaio, fessurazione, frecce
- [ ] Zone terminali di ancoraggio e diffusione
- [ ] Verifica a fatica (se ciclica rilevante — ponti)

### Esecuzione
- [ ] Certificati materiali (cls, acciai, sistema precompressione)
- [ ] Libro di tesatura con valori di allungamento/forza per cavo
- [ ] Controllo del ritiro (cls maturato a ≥ 25 MPa prima del rilascio)
- [ ] Iniezione boiacca (post-tensione aderente) con prove di intasamento

---

## Checklist operativa — Strutture composte

### Progettazione
- [ ] Definire beff della soletta
- [ ] Verifica Mpl,Rd e connessione richiesta
- [ ] Progettare i connettori (piolo + passo)
- [ ] Verifiche trasversali della soletta (armatura trasversale)
- [ ] Verifiche SLE (freccia, fessurazione soletta, vibrazioni)
- [ ] Dettagli di continuità (travi continue → armatura sup. per M-)
- [ ] Protezione al fuoco (vernici intumescenti / rivestimento)

### Esecuzione
- [ ] Certificati pioli Nelson (saldatura a percussione)
- [ ] Test di saldatura in opera (prova a martello, prova piegatura 30°)
- [ ] Controllo armatura trasversale soletta prima del getto
- [ ] Stabilità temporanea in fase di getto (puntellazione o lamiera auto-portante)
