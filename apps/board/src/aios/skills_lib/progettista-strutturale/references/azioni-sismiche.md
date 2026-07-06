# Azioni sismiche — NTC 2018 §§ 3.2, 7 + Circ. 7/2019

Riferimento completo per la determinazione dell'azione sismica di progetto, la scelta del fattore di struttura q e la progettazione in capacity design.

---

## 1. Pericolosità sismica di base (NTC 2018 § 3.2)

### 1.1 Stati limite sismici e periodi di ritorno

Il periodo di riferimento è VR = VN × Cu. Per ciascuno stato limite si valuta ag e lo spettro in funzione della probabilità di superamento PVR nel periodo di riferimento.

| Stato limite | Sigla | PVR (%) | Descrizione |
|--------------|-------|---------|-------------|
| Operatività | SLO | 81 | Nessun danno a elementi strutturali e non strutturali |
| Danno | SLD | 63 | Danni limitati tali da non compromettere funzionalità |
| Salvaguardia vita | SLV | 10 | Rotture significative ma capacità residua per carichi verticali |
| Prevenzione collasso | SLC | 5 | Rotture gravi ma edificio ancora in piedi |

Periodo di ritorno: TR = − VR / ln(1 − PVR). Per VR = 50 anni:
- SLO → TR ≈ 30 anni
- SLD → TR ≈ 50 anni
- SLV → TR ≈ 475 anni
- SLC → TR ≈ 975 anni

Per VR ≠ 50 anni i TR cambiano proporzionalmente (formula NTC 3.2.1).

### 1.2 Parametri di base del sito

Per ciascun TR si estraggono da tabella NTC (reticolo 0.05° × 0.05°) o webservice CSLP tre parametri:

| Parametro | Significato |
|-----------|-------------|
| ag | Accelerazione orizzontale massima su suolo rigido (Cat. A) in [g] |
| F0 | Valore massimo dell'amplificazione spettrale |
| TC* | Periodo di inizio del tratto a velocità costante dello spettro su Cat. A (s) |

Procedura operativa: identificare latitudine/longitudine del sito → interrogare il reticolo NTC → interpolare se il punto non coincide con un nodo.

---

## 2. Effetti di sito — coefficienti di amplificazione (NTC 2018 § 3.2.3)

### 2.1 Categoria di sottosuolo (Tab. 3.2.II)

| Cat. | Descrizione | Vs,eq (m/s) | NSPT,30 | cu,30 (kPa) |
|------|-------------|-------------|---------|------------|
| A | Roccia o terreno rigido | > 800 | — | — |
| B | Rocce tenere e depositi molto addensati | 360–800 | > 50 | > 250 |
| C | Depositi molto addensati o consistenti | 180–360 | 15–50 | 70–250 |
| D | Depositi scarsamente addensati o coerenti | < 180 | < 15 | < 70 |
| E | Strati A-C/D su substrato (spessore ≤ 20 m) | variabile | variabile | variabile |

Vs,eq = velocità media di propagazione equivalente delle onde di taglio nei primi 30 m (o H se inferiore).

**Categorie speciali S1/S2** (valutazioni specifiche):
- S1: terreni coesivi molto deformabili (cu < 10 kPa) o torbe
- S2: terreni liquefacibili o argille sensitive

### 2.2 Coefficiente stratigrafico SS (Tab. 3.2.IV)

| Cat. | SS |
|------|----|
| A | 1.00 |
| B | 1.00 ≤ 1.40 − 0.40·F0·ag/g ≤ 1.20 |
| C | 1.00 ≤ 1.70 − 0.60·F0·ag/g ≤ 1.50 |
| D | 0.90 ≤ 2.40 − 1.50·F0·ag/g ≤ 1.80 |
| E | 1.00 ≤ 2.00 − 1.10·F0·ag/g ≤ 1.60 |

### 2.3 Coefficiente CC per calcolo TC (Tab. 3.2.IV)

| Cat. | CC |
|------|----|
| A | 1.00 |
| B | 1.10·(TC*)^(−0.20) |
| C | 1.05·(TC*)^(−0.33) |
| D | 1.25·(TC*)^(−0.50) |
| E | 1.15·(TC*)^(−0.40) |

### 2.4 Categoria topografica (Tab. 3.2.III)

| Cat. | Descrizione | ST |
|------|-------------|----|
| T1 | Superficie pianeggiante, pendii, rilievi isolati con inclinazione media ≤ 15° | 1.0 |
| T2 | Pendii con inclinazione media > 15° | 1.2 |
| T3 | Rilievi con larghezza in cresta molto minore della base e inclinazione 15°–30° | 1.2 |
| T4 | Rilievi con larghezza in cresta molto minore della base e inclinazione > 30° | 1.4 |

ST si applica solo alla sommità del rilievo e decade linearmente fino alla base.

---

## 3. Spettri di risposta (NTC 2018 § 3.2.3.2)

### 3.1 Parametri dello spettro

```
S = SS · ST
TB = TC / 3
TC = CC · TC*
TD = 4.0·ag/g + 1.6    [s]
```

### 3.2 Spettro elastico orizzontale Se(T)

```
0 ≤ T < TB:    Se(T) = ag·S·η·F0·[T/TB + 1/(η·F0)·(1 − T/TB)]
TB ≤ T ≤ TC:   Se(T) = ag·S·η·F0
TC < T ≤ TD:   Se(T) = ag·S·η·F0·(TC/T)
T > TD:        Se(T) = ag·S·η·F0·(TC·TD/T²)
```

Dove:
- η = √(10/(5 + ξ)) ≥ 0.55 (ξ = smorzamento viscoso in %, per c.a./acciaio ξ = 5% → η = 1)
- Per spettro di progetto SLV: Sd(T) = Se(T)/q, con il limite Sd(T) ≥ 0.2·ag per T ≤ TC

### 3.3 Spettro elastico verticale Sve(T)

```
0 ≤ T < TB:    Sve(T) = ag·S·η·FV·[T/TB + 1/(η·FV)·(1 − T/TB)]
TB ≤ T ≤ TC:   Sve(T) = ag·S·η·FV
TC < T ≤ TD:   Sve(T) = ag·S·η·FV·(TC/T)
T > TD:        Sve(T) = ag·S·η·FV·(TC·TD/T²)
```

Parametri verticali (Tab. 3.2.VIII): TB = 0.05 s, TC = 0.15 s, TD = 1.0 s; FV = 1.35·F0·(ag/g)^0.5.

La componente verticale si considera obbligatoriamente solo per:
- Edifici con piani sospesi a mensole > 4 m
- Pilastri in falso
- Strutture di grande luce (> 20 m)
- Travi principali con luce > 20 m

---

## 4. Fattore di struttura q (NTC 2018 § 7.3.1)

### 4.1 Formula generale

```
q = q0 · KR
```

- q0 = fattore legato alla tipologia strutturale (Tab. 7.3.II)
- KR = 1.0 per strutture regolari in altezza, 0.8 altrimenti

### 4.2 Edifici in c.a. (Tab. 7.3.II)

| Tipologia | CD"A" | CD"B" |
|-----------|-------|-------|
| Telai | 4.5·αu/α1 | 3.0·αu/α1 |
| Pareti (accoppiate o non) | 4.0·αu/α1 | 3.0 |
| Telaio-pareti equivalente | 4.5·αu/α1 | 3.0·αu/α1 |
| Pareti grandi non armate | 3.0·αu/α1 | 3.0 |
| A nucleo | 3.0·αu/α1 | 2.0 |

Valori αu/α1 di default (se non determinati da analisi pushover):
- Telai 1 piano: 1.1
- Telai pluripiano 1 campata: 1.2
- Telai pluripiano più campate: 1.3
- Pareti accoppiate: 1.2
- Telaio-pareti: 1.2

### 4.3 Edifici in acciaio (Tab. 7.3.II)

| Tipologia | CD"A" | CD"B" |
|-----------|-------|-------|
| Telai MRF | 5.0·αu/α1 | 4.0 |
| Controventi concentrici | 4.0 | 4.0 |
| Controventi eccentrici | 5.0·αu/α1 | 4.0 |
| Pendolo invertito | 2.0 | 2.0 |

### 4.4 Edifici in muratura (Tab. 7.8.I/II)

| Tipologia | q0 nuove | q0 esistenti |
|-----------|----------|--------------|
| Muratura ordinaria regolare | 2.0·αu/α1 | 1.5·αu/α1 |
| Muratura armata | 2.5·αu/α1 | — |
| Muratura armata con progetto capacità | 3.0·αu/α1 | — |

### 4.5 Riduzioni per irregolarità

- Edificio NON regolare in altezza → KR = 0.8
- Edificio NON regolare in pianta → riduzione ulteriore solo se analisi semplificata: utilizzo di analisi dinamica modale con due componenti orizzontali

### 4.6 Limiti assoluti

- q ≥ 1.5 per strutture non dissipative
- Per edifici esistenti in muratura non sismo-resistente: q = 1.5 ÷ 2.0 massimo

---

## 5. Classe di duttilità e requisiti di progettazione

### 5.1 Classe di duttilità Alta "CD"A"" (NTC § 7.4.6, 7.5.5)

**C.a. — requisiti principali:**
- Gerarchia delle resistenze trave-pilastro: ΣMC,Rd ≥ γRd · ΣMB,Rd (γRd = 1.3)
- Zone critiche trave: Lcr = 1.5 · h (H = altezza trave)
- Zone critiche pilastro: Lcr = max(h; L/6; 45 cm)
- Staffe zone critiche: s ≤ min(6·φL; h/4; 10 cm)
- Acciaio barre: B450C obbligatorio (duttilità)

**Acciaio — requisiti principali:**
- Rapporto larghezza/spessore per zone dissipative (classe 1 sempre)
- Collegamenti saldati in zone dissipative: verifica overstrength con γov·fy
- Travi: sezione a doppio T con alette larghe per duttilità flessionale

### 5.2 Classe di duttilità Bassa "CD"B"" (NTC § 7.4.7)

- Gerarchia delle resistenze non obbligatoria
- Dettagli costruttivi semplificati
- q0 ridotto (da 3.0 a 3.0 senza moltiplicatore αu/α1 per c.a. telai)
- Acciaio barre B450A/B450C (B450A ammesso)

---

## 6. Regolarità strutturale (NTC 2018 § 7.2.2)

### 6.1 Regolarità in pianta

Tutti i criteri devono essere soddisfatti:
1. Configurazione in pianta compatta e approssimativamente simmetrica rispetto a due direzioni ortogonali (rapporto lati L/B ≤ 4)
2. Rientri o sporgenze ≤ 25% della dimensione totale in quella direzione
3. Solai infinitamente rigidi nel piano
4. Eccentricità massima e0 ≤ 0.30 · r (r = raggio giratore inerzia di piano)
5. Raggio di torsione r ≥ ls (ls = raggio inerzia masse)

### 6.2 Regolarità in altezza

Tutti i criteri devono essere soddisfatti:
1. Tutti i sistemi resistenti verticali si estendono per tutta l'altezza
2. Massa e rigidezza variano in modo graduale (variazione ≤ 25% tra piani adiacenti)
3. Nessun piano debole (rapporto resistenza/resistenza del piano sovrastante ≥ 0.80)
4. Restringimenti graduali: nessuna riduzione delle dimensioni > 30% dal piano sotto; nessun ampliamento al piano superiore (salvo coperture)

Edifici NON regolari in altezza: KR = 0.8 → q ridotto del 20%.

---

## 7. Metodi di analisi (NTC 2018 § 7.3)

### 7.1 Analisi lineare statica (§ 7.3.3)

**Applicabilità:**
- T1 ≤ 2.5 · TC o T1 ≤ TD
- Struttura regolare in altezza

**Periodo fondamentale approssimato:**
- T1 = C1 · H^(3/4)
  - C1 = 0.085 per telai in acciaio
  - C1 = 0.075 per telai in c.a.
  - C1 = 0.050 per altre strutture

**Forza sismica di base:**
```
Fb = Sd(T1) · W · λ / g
```
- W = peso sismico totale (G + ψ2j·Q)
- λ = 0.85 se T1 ≤ 2·TC e N ≥ 3 piani; altrimenti λ = 1.0

**Distribuzione forze ai piani:**
```
Fi = Fb · (zi · Wi) / Σ(zj · Wj)
```
- zi = quota del piano i dal piano di fondazione
- Wi = peso sismico del piano i

**Eccentricità accidentale:** ±5% della dimensione in direzione ortogonale alla componente sismica considerata (momento torcente Mi = Fi · 0.05·Li).

### 7.2 Analisi dinamica modale con spettro di risposta (§ 7.3.4)

Sempre applicabile. Obbligatoria per edifici NON regolari in altezza o T1 > 2.5·TC.

**Procedura:**
1. Analisi modale: estrazione dei modi propri con masse partecipanti
2. Considerare tutti i modi con massa partecipante ≥ 5% fino a somma massa ≥ 85%
3. Per ogni modo calcolare le risposte Ei (spostamenti, forze, sollecitazioni)
4. Combinare i modi con SRSS (se periodi ben distanziati) o CQC (se modi ravvicinati)

**Combinazione CQC:**
```
E = √(Σ Σ ρij · Ei · Ej)
```
Coefficiente di correlazione ρij funzione del rapporto periodi βij = Ti/Tj e smorzamento.

**Combinazione direzionale** (azione sismica a 2 componenti orizzontali):
- E = 1.00·Ex + 0.30·Ey (e permutazioni)
- Oppure SRSS: E = √(Ex² + Ey²)

### 7.3 Analisi non lineare statica — Pushover (§ 7.3.4.1)

Usata per edifici esistenti e verifiche di vulnerabilità.

**Procedura:**
1. Definire un pattern di forze laterali (proporzionale ai modi o uniforme)
2. Incrementare progressivamente le forze fino al collasso di un meccanismo
3. Costruire la curva di capacità: taglio alla base V vs spostamento in sommità d
4. Bilinearizzare la curva per ottenere un SDOF equivalente
5. Confrontare con la domanda sismica in formato ADRS
6. Punto di prestazione (performance point) = intersezione

**Verifica:** PGA,capacità ≥ PGA,domanda per lo stato limite considerato (αU ≥ 1.0 per SLV).

### 7.4 Analisi non lineare dinamica (§ 7.3.4.2)

Richiede almeno 7 accelerogrammi spettro-compatibili per direzione.
- Si usa la media delle risposte (non il massimo)
- Accelerogrammi: naturali, artificiali (SIMQKE, REXEL), ibridi
- Validazione spettro-compatibilità in banda [0.2·T1; 2·T1]

---

## 8. Gerarchia delle resistenze (Capacity Design)

### 8.1 Principio

L'obiettivo è indirizzare le plasticizzazioni verso elementi duttili (travi) evitando meccanismi fragili (pilastri, taglio, fondazioni). Non è una verifica aggiuntiva: è un principio che vincola il dimensionamento degli elementi "sovra-resistenti".

### 8.2 C.a. — Travi → Pilastri (NTC § 7.4.4.2)

Per ogni nodo interno:
```
ΣMC,Rd ≥ γRd · ΣMB,Rd
```
- ΣMC,Rd = somma momenti resistenti dei pilastri convergenti al nodo
- ΣMB,Rd = somma momenti resistenti delle travi convergenti al nodo
- γRd = 1.3 per CD"A", 1.1 per CD"B" (edifici esistenti)

Eccezioni:
- Non si applica all'ultimo piano (tetti/attici)
- Non si applica se il pilastro è già dimensionato per NEd < 0.1·Ac·fcd (basso sforzo normale)

### 8.3 C.a. — Momento flettente → Taglio (NTC § 7.4.4.1.1)

Il taglio di progetto per travi e pilastri in CD"A" si calcola con i momenti resistenti alle estremità e non con l'analisi elastica:
```
VEd,CD = (MRd,i + MRd,j) / L + VEd,gravitazionale
```
- MRd,i, MRd,j = momenti resistenti alle due estremità (con segni opposti)
- L = luce netta trave/pilastro
- VEd,gravitazionale = taglio da carichi verticali (G + ψ2·Q)

### 8.4 C.a. — Nodo trave-pilastro (NTC § 7.4.4.3)

Taglio di progetto del nodo:
```
VjhEd = γRd · (As1 + As2) · fyd − VC
```
- As1, As2 = armatura tesa superiore/inferiore della trave nel nodo
- VC = taglio del pilastro sopra il nodo
- γRd = 1.2 per CD"A", 1.0 per CD"B"

Verifica: VjhRd (calcolato con puntoni compressi di cls) ≥ VjhEd.

### 8.5 Acciaio — Capacity design

- Collegamenti più resistenti degli elementi collegati: MRd,conn ≥ γov · γsh · MRd,beam
  - γov = 1.25 (acciaio strutturale)
  - γsh = 1.2 (incrudimento)
- Controventi: diagonali teso-compresse dissipative; montanti e correnti sovra-resistenti con N*Rd ≥ 1.1 · γov · Npl,Rd,diag

### 8.6 Fondazioni

Le azioni trasferite alle fondazioni sono quelle equilibrate dalle resistenze degli elementi dissipativi in elevazione, non quelle dell'analisi elastica:
```
EF,d = EF,G + γRd · Ω · EF,E
```
- Ω = MRd,elemento / MEd,elemento (≤ q)
- γRd = 1.0 (fondazioni progettate in CD"B" di default)

Razionale: le fondazioni devono restare in campo elastico anche se la sovrastruttura plasticizza.

---

## 9. Verifiche SLE sismiche

### 9.1 SLD — Spostamento d'interpiano (NTC § 7.3.7.2)

```
dr/h ≤ limite
```

| Tipologia | Limite dr/h |
|-----------|-------------|
| Tamponature rigide collegate | 0.005 |
| Tamponature rigide disaccoppiate | 0.0075 |
| Edifici a pareti in c.a. con tamponature rigide | 0.005 |
| Edifici in muratura (SLV pseudo-SLD) | 0.003 |

dr = spostamento relativo d'interpiano calcolato con spettro SLD (TR=50 anni, non ridotto da q).

### 9.2 SLO — Spostamento d'interpiano (NTC § 7.3.7.2, per classi III-IV)

```
dr/h ≤ 2/3 · limite SLD
```

Controllo obbligatorio solo per Classe d'uso III e IV.

---

## 10. Elementi non strutturali (NTC 2018 § 7.2.3)

### 10.1 Azione sismica su elementi non strutturali

Per parapetti, tramezze alte > 4 m, apparecchiature, serbatoi:
```
Fa = (Sa · Wa) / qa
```
- Sa = accelerazione al piano di ancoraggio (spettro pseudoaccelerazione al piano)
- Wa = peso elemento
- qa = fattore di struttura elemento (1.0 ÷ 2.0 tipicamente)

### 10.2 Verifica piano rigido

Tamponature o tramezze: verifica che non si ribaltino fuori piano né danneggino la struttura principale.

---

## 11. Combinazione sismica (NTC 2018 § 3.2.4, 7.3.5)

### 11.1 Combinazione di carico sismica

```
E + G1 + G2 + Σ ψ2j · Qkj
```

Dove:
- E = azione sismica (SLU: con q; SLE SLD: senza q)
- ψ2j = coefficiente quasi-permanente (vedi normativa-strutturale.md)

### 11.2 Masse sismiche

Le masse da considerare:
```
W = G1 + G2 + Σ ψ2j · Qkj
```

Per edifici residenziali (Cat. A): ψ2 = 0.30 → si considera il 30% dei carichi variabili.

### 11.3 Combinazione delle componenti sismiche

Secondo NTC § 7.3.5:
- Orizzontale prevalente + 30% componente ortogonale
- Per edifici regolari di Classe I-II: possibile trascurare componente verticale salvo casi specifici (vedi § 3.3 sopra)

---

## 12. Checklist operativa — progettazione nuova in zona sismica

### Fase 1 — Input sismico
- [ ] Coordinate sito (lat/long), Comune
- [ ] Classe d'uso (I/II/III/IV) e VN → VR
- [ ] ag, F0, TC* per SLO, SLD, SLV, SLC (interrogazione reticolo NTC)
- [ ] Categoria sottosuolo (A/B/C/D/E) da relazione geotecnica
- [ ] Categoria topografica (T1/T2/T3/T4)
- [ ] Calcolo SS, CC, ST, TB, TC, TD

### Fase 2 — Scelta tipologia e q
- [ ] Tipologia strutturale (telai/pareti/misto)
- [ ] Classe duttilità (CD"A" o CD"B")
- [ ] Verifica regolarità in pianta e altezza
- [ ] Calcolo q0, KR, q finale
- [ ] Spettro di progetto Sd(T) orizzontale (e verticale se rilevante)

### Fase 3 — Analisi
- [ ] Scelta metodo (statica lineare o dinamica modale)
- [ ] Modello strutturale con masse sismiche
- [ ] Eccentricità accidentale ±5%
- [ ] Combinazione direzionale (1.0 + 0.3)
- [ ] Estrazione sollecitazioni di progetto

### Fase 4 — Verifiche
- [ ] SLV: verifica resistenze elementi con combinazione sismica
- [ ] Capacity design: ΣMC,Rd ≥ γRd·ΣMB,Rd, taglio da MRd, nodi
- [ ] SLD: verifica drift d'interpiano
- [ ] Verifica fondazioni con azioni da sovrastruttura sovra-resistente
- [ ] Dettagli costruttivi CD"A"/"B" (zone critiche, staffe, ancoraggi)

---

## 13. Formule riassuntive per script e calcolo rapido

```python
# Spettro di progetto orizzontale SLV
def Sd(T, ag, F0, TC, TB, TD, S, q, eta=1.0):
    if T < TB:
        return max(ag*S*eta*F0*(T/TB + 1/(eta*F0)*(1 - T/TB))/q, 0.2*ag)
    elif T <= TC:
        return max(ag*S*eta*F0/q, 0.2*ag)
    elif T <= TD:
        return ag*S*eta*F0*(TC/T)/q
    else:
        return ag*S*eta*F0*(TC*TD/T**2)/q

# Periodo fondamentale approssimato
def T1_approx(H, C1=0.075):
    return C1 * H**0.75

# Forza sismica di base
def Fb(SdT1, W, lambda_=0.85, g=9.81):
    return SdT1 * W * lambda_ / g

# Distribuzione forze al piano
def Fi(Fb, Wi, zi, Wz_sum):
    return Fb * (Wi * zi) / Wz_sum
```

Vedi anche: `scripts/calcolo_spettro.py` (calcolo completo dello spettro con SS/CC/ST) e `scripts/analisi_sismica_statica.py` (analisi lineare statica completa).
