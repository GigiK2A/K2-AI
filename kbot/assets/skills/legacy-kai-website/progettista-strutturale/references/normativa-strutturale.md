# Normativa strutturale — Riferimento dettagliato

## Norme Tecniche per le Costruzioni (NTC 2018)

### Struttura del D.M. 17/01/2018

| Capitolo | Contenuto |
|----------|-----------|
| Cap. 1 | Oggetto, campo di applicazione, glossario |
| Cap. 2 | Sicurezza e prestazioni attese — SLU, SLE, SLO, SLD, SLV, SLC |
| Cap. 3 | Azioni sulle strutture — carichi, vento, neve, temperatura, sisma |
| Cap. 4 | Costruzioni civili e industriali — c.a., c.a.p., acciaio, legno, muratura, fondazioni |
| Cap. 5 | Ponti |
| Cap. 6 | Progettazione geotecnica |
| Cap. 7 | Progettazione per azioni sismiche |
| Cap. 8 | Costruzioni esistenti |
| Cap. 9 | Collaudo |
| Cap. 10 | Redazione dei progetti e delle relazioni di calcolo |
| Cap. 11 | Materiali e prodotti per uso strutturale |
| Cap. 12 | Riferimenti tecnici |

### Stati Limite (NTC 2018 § 2.2)

**Stati Limite Ultimi (SLU):**
- SLV (Salvaguardia della Vita) → TR = 475 anni (PVR = 10% in 50 anni)
- SLC (Collasso) → TR = 975 anni (PVR = 5% in 50 anni)

**Stati Limite di Esercizio (SLE):**
- SLD (Danno) → TR = 50 anni (PVR = 63% in 50 anni)
- SLO (Operatività) → TR = 30 anni (PVR = 81% in 30 anni)

**Per strutture non sismiche:**
- SLU fondamentale → gestione carichi permanenti e variabili
- SLE rara / frequente / quasi-permanente → deformazioni, fessurazione, vibrazioni

### Classi di conseguenze (NTC 2018 § 2.4.1)

| Classe | Descrizione | Esempi | KFI |
|--------|-------------|--------|-----|
| CC1 | Conseguenze basse | Strutture agricole, depositi | 0.9 |
| CC2 | Conseguenze medie | Edifici residenziali, uffici | 1.0 |
| CC3 | Conseguenze alte | Teatri, stadi, ospedali | 1.1 |

### Vita nominale e classe d'uso (NTC 2018 §§ 2.4.1, 2.4.2)

| Tipo struttura | VN (anni) |
|----------------|-----------|
| Strutture provvisorie | ≥ 10 |
| Strutture ordinarie | ≥ 50 |
| Grandi opere/infrastrutture | ≥ 100 |

| Classe d'uso | Cu | Edifici tipici |
|-------------|-----|----------------|
| I | 0.7 | Agricoli, scarsa presenza umana |
| II | 1.0 | Residenziali, uffici, artigianali |
| III | 1.5 | Affollamento elevato (musei, stadi) |
| IV | 2.0 | Funzioni pubbliche essenziali (ospedali, VV.FF.) |

Periodo di riferimento: VR = VN × Cu (usato per determinare ag e spettro)

---

## Classificazione sismica del territorio italiano

Le zone sismiche sono definite dall'OPCM 3274/2003 e s.m.i., con valori di ag da tabelle NTC:

| Zona | ag/g | Descrizione |
|------|------|-------------|
| 1 | > 0.25 | Alta sismicità |
| 2 | 0.15–0.25 | Media-alta sismicità |
| 3 | 0.05–0.15 | Media-bassa sismicità |
| 4 | < 0.05 | Bassa sismicità |

La classificazione puntuale usa le coordinate geografiche e la griglia NTC (reticolo 0.05°×0.05°).

---

## Categorie del suolo di fondazione (NTC 2018 tab. 3.2.II)

| Cat. | Descrizione | Vs,30 (m/s) | NSPT | cu (kPa) |
|------|-------------|-------------|------|---------|
| A | Roccia o terreno rigido | > 800 | — | — |
| B | Rocce tenere, dep. granulari densi | 360–800 | > 50 | > 250 |
| C | Dep. granulari mediamente addensati | 180–360 | 15–50 | 70–250 |
| D | Dep. coesivi/granulari sciolti | < 180 | < 15 | < 70 |
| E | Strati superficiali su roccia | — | — | — |

Categorie speciali: S1 (torbe/argille sensitive), S2 (terreni potenzialmente liquefacibili).

---

## Coefficienti parziali NTC 2018 — sintesi

### Azioni (SLU fondamentale)
| Azione | γ sfavorevole | γ favorevole |
|--------|--------------|--------------|
| G1 (peso proprio struttura) | 1.3 | 1.0 |
| G2 (permanenti non strutturali) | 1.5 | 0.0 |
| Q (variabili) | 1.5 | 0.0 |
| P (precompressione) | 1.0 o 1.2 | 0.9 |

### Materiali — calcestruzzo e acciaio
| Materiale | γM | fdk → fdd |
|-----------|----|----------|
| Calcestruzzo c.a. (SLU) | 1.5 | fcd = αcc·fck/1.5 (αcc=0.85) |
| Acciaio barre (SLU) | 1.15 | fyd = fyk/1.15 |
| Acciaio strutturale (SLU) | 1.05 | fyd = fyk/1.05 |
| Legno massiccio | 1.3 | fd = kmod·fk/1.3 |
| Legno lamellare | 1.25 | fd = kmod·fk/1.25 |
| Muratura ordinaria | 2.0 | fd = fk/2.0 |
| Muratura armata (sismica) | 3.0 | fd = fk/3.0 |

### Coefficienti ψ per carichi variabili (NTC 2018 tab. 2.5.I) — COMPLETA

| Categoria | Descrizione | ψ0 | ψ1 | ψ2 |
|-----------|-------------|----|----|----|
| A | Ambienti residenziali | 0.7 | 0.5 | 0.3 |
| B1 | Uffici non pubblici | 0.7 | 0.5 | 0.3 |
| B2 | Uffici pubblici | 0.7 | 0.5 | 0.3 |
| C1 | Sale con tavoli (scuole, caffè, ristoranti) | 0.7 | 0.7 | 0.6 |
| C2 | Sale con sedute fisse (teatri, chiese) | 0.7 | 0.7 | 0.6 |
| C3 | Ambienti senza ostacoli (sale riunioni, esposizioni) | 0.7 | 0.7 | 0.6 |
| C4 | Ambienti attività fisica | 0.7 | 0.7 | 0.6 |
| C5 | Ambienti suscettibili di affollamento | 1.0 | 0.9 | 0.8 |
| D1 | Negozi | 0.7 | 0.7 | 0.6 |
| D2 | Centri commerciali | 0.7 | 0.7 | 0.6 |
| E1 | Biblioteche, archivi, magazzini | 1.0 | 0.9 | 0.8 |
| E2 | Magazzini e industriali | 1.0 | 0.9 | 0.8 |
| F | Rimesse/parcheggi ≤ 30 kN | 0.7 | 0.7 | 0.6 |
| G | Rimesse/parcheggi > 30 kN | 0.7 | 0.5 | 0.3 |
| H | Coperture (non accessibili) | 0.0 | 0.0 | 0.0 |
| I | Coperture praticabili | come cat. d'uso | | |
| K | Coperture speciali (eliporti) | — | — | — |
| Neve (quota ≤ 1000m) | | 0.5 | 0.2 | 0.0 |
| Neve (quota > 1000m) | | 0.7 | 0.5 | 0.2 |
| Vento | | 0.6 | 0.2 | 0.0 |
| Temperatura | | 0.6 | 0.5 | 0.0 |

---

## Azione del vento (NTC 2018 § 3.3)

### Zone del vento (Tab. 3.3.I NTC 2018)

| Zona | Descrizione (regioni) | vb,0 (m/s) | a0 (m) | ka (1/s) |
|------|----------------------|-----------|--------|----------|
| 1 | Valle d'Aosta, Piemonte, Lombardia, Trentino-Alto Adige, Veneto, Friuli-Venezia Giulia, Emilia-Romagna | 25 | 1000 | 0.010 |
| 2 | Toscana, Marche, Umbria, Lazio, Abruzzo, Molise, Puglia, Campania, Basilicata | 25 | 750 | 0.015 |
| 3 | Calabria, Sicilia | 27 | 500 | 0.020 |
| 4 | Sardegna (zona E di Cagliari) | 28 | 500 | 0.020 |
| 5 | Sardegna (zona occidentale) | 28 | 750 | 0.015 |
| 6 | Liguria | 28 | 1000 | 0.010 |
| 7 | Trieste | 30 | 1500 | 0.010 |
| 8 | Isole tranne Sicilia/Sardegna e mare aperto | 31 | 500 | 0.020 |
| 9 | Isole minori | 31 | 500 | 0.020 |

### Velocità di riferimento vb
```
vb = vb,0 · ca           se as ≤ a0
vb = vb,0 · ca · (1 + ka · (as - a0))   se as > a0
```
dove `as` = altitudine del sito [m s.l.m.], `ca` = coefficiente di altitudine (1.0 standard).

### Pressione cinetica di riferimento
```
qb = 0.5 · ρ · vb²           con ρ = 1.25 kg/m³
qb [N/m²] = vb²/1.6           (formula pratica)
```

### Coefficiente di esposizione ce(z) — NTC § 3.3.7

Dipende dalla categoria di esposizione del sito (I, II, III, IV, V) e dall'altezza z.
Formule in NTC § 3.3.7 con coefficienti kr, z0, zmin da Tab. 3.3.II:

| Categoria | kr | z0 [m] | zmin [m] |
|-----------|------|-------|---------|
| I (mare) | 0.17 | 0.01 | 2 |
| II (aperta) | 0.19 | 0.05 | 4 |
| III (suburbana) | 0.20 | 0.10 | 5 |
| IV (urbana) | 0.22 | 0.30 | 8 |
| V (centro città) | 0.23 | 0.70 | 12 |

```
ce(z) = kr² · ct · ln(z/z0) · [7 + ct · ln(z/z0)]   per z ≥ zmin
ce(zmin)                                            per z < zmin
```

### Coefficienti di forma cp — edifici chiusi (NTC § 3.3.8)

| Superficie | cp,est |
|-----------|--------|
| Parete sopravento (perpendicolare al vento) | +0.80 |
| Parete sottovento | -0.40 |
| Pareti laterali | -0.50 (tipico) |
| Copertura piana (a < 5°) | -0.80 / +0.20 |
| Copertura a falda 15°-30° | -0.70 / +0.10 |
| Copertura a falda > 30° | -0.50 / +0.40 |

Pressione di progetto: **p = qb · ce · cp · cd** (cd = dinamico, tipicamente 1.0)

---

## Azione della neve (NTC 2018 § 3.4)

### Valore caratteristico al suolo qsk (NTC tab. 3.4.I)

| Zona | Regione | qsk(as=0) | Formula generale |
|------|---------|-----------|------------------|
| **Zona I — Alpina** | Aosta, Belluno, Bergamo, Biella, Bolzano, Brescia, Como, Cuneo, Lecco, Novara, Sondrio, Torino, Trento, Udine, Verbania, Vercelli, Vicenza | 1.50 kN/m² | 1.39·[1 + (as/728)²] per as > 200 m |
| **Zona I — Mediterranea** | Alessandria, Ancona, Asti, Avellino, Benevento, Bologna, Cagliari, Caserta, Chieti, Ferrara, Forlì, Genova, Gorizia, L'Aquila, La Spezia, Lodi, Lucca, Macerata, Mantova, Milano, Modena, Monza, Padova, Parma, Pavia, Pesaro, Piacenza, Pisa, Pistoia, Pordenone, Prato, Ravenna, Reggio Emilia, Rieti, Rimini, Roma, Rovigo, Savona, Teramo, Terni, Treviso, Trieste, Varese, Venezia, Verona | 1.50 kN/m² | 1.39·[1 + (as/728)²] per as > 200 m |
| **Zona II** | Bari, Campobasso, Caltanissetta, Enna, Firenze, Grosseto, Imperia, Isernia, Matera, Napoli, Nuoro, Oristano, Pescara, Potenza, Sassari, Siena, Taranto | 1.00 kN/m² | 0.85·[1 + (as/481)²] per as > 200 m |
| **Zona III** | Agrigento, Brindisi, Cosenza, Catania, Catanzaro, Crotone, Foggia, Lecce, Latina, Messina, Palermo, Ragusa, Reggio Calabria, Salerno, Siracusa, Trapani, Vibo Valentia, Viterbo | 0.60 kN/m² | 0.51·[1 + (as/481)²] per as > 200 m |

### Carico di progetto sulla copertura
```
qs = μi · qsk · CE · Ct
```

| Parametro | Valore |
|-----------|--------|
| μi — coeff. forma copertura piana/debole pendenza (≤ 30°) | 0.80 |
| μi — copertura con pendenza 30°–60° | 0.80·(60-α)/30 |
| μi — copertura α > 60° | 0.00 |
| CE — coeff. esposizione (standard) | 1.00 |
| CE — sito riparato | 1.10 |
| CE — sito molto ventoso | 0.90 |
| Ct — coeff. termico (standard) | 1.00 |

Per coperture adiacenti di altezza diversa valutare **accumuli** e **sporgenze** (NTC § 3.4.5).

---

## Azione della temperatura (NTC 2018 § 3.5)

Per strutture esposte:
- Variazione uniforme ΔT,u (ad es. ±15 °C per strutture in c.a. esterne)
- Gradiente termico ΔTM (tra intradosso/estradosso solaio)

Per edifici coibentati: spesso l'effetto è trascurabile; per strutture ponti e strutture esposte va verificato.

---

## Adempimenti procedurali — deposito strutturale

### Zone sismiche 1 e 2 (autorizzazione preventiva)
1. Presentazione istanza + progetto strutturale allo Sportello Sismico Regionale
2. Attesa autorizzazione (30-60 gg tipicamente)
3. Solo dopo autorizzazione: inizio lavori strutturali
4. Certificazioni materiali durante lavori (§ 11 NTC)
5. Collaudo statico a fine lavori (art. 67 DPR 380/2001)

### Zone sismiche 3 e 4 (denuncia lavori)
1. Deposito progetto strutturale allo Sportello Sismico PRIMA dell'inizio lavori
2. Ricevuta di deposito → inizio lavori autorizzato
3. Certificazioni materiali durante lavori
4. Collaudo statico

### Documentazione obbligatoria (art. 93 DPR 380/2001)
- Relazione illustrativa
- Relazione di calcolo strutturale
- Relazione sui materiali
- Relazione geotecnica e geologica (firmata da geologo abilitato)
- Elaborati grafici (tavole strutturali)
- Piano di manutenzione della struttura
- Fascicolo dell'opera (D.Lgs. 81/2008 All. XVI)

---

## Certificazione materiali (NTC 2018 Cap. 11)

### Calcestruzzo
- Classe di resistenza: CX/Y (es. C25/30 → fck cilindrico/cubico)
- Classi di esposizione (UNI EN 206): XO, XC, XD, XS, XF, XA
- Rapporto a/c e contenuto minimo cemento per classe esposizione
- Prove di accettazione cantiere: ogni 100 m³ o ogni giorno getto → 2 provini per coppia
- Resistenza media rm ≥ fck + 3.5 MPa (§ 11.2.5)

### Acciaio per c.a.
- B450C (corrugato, saldabile) → fyk = 450 MPa, ftk = 540 MPa
- B450A (reti elettrosaldate) → fyk = 450 MPa
- Certificati di prova in stabilimento + certificati di conformità CE
- Identificazione barre: marchiatura del produttore

### Acciaio strutturale
- S235, S275, S355 (UNI EN 10025)
- Certificati di qualità per colata/lotto
- Classi di tenacità J0, J2, K2 (impatto Charpy)

---

## Riferimenti pratici — formule rapide

### Trave semplicemente appoggiata — carichi uniformi
- M_max = q·L²/8 (mezzeria)
- V_max = q·L/2 (appoggi)
- freccia_max = 5·q·L⁴/(384·EI) (SLE)

### Trave a sbalzo — carico uniforme
- M_max = q·L²/2 (all'incastro)
- freccia_max = q·L⁴/(8·EI)

### Pilastro — lunghezza libera di inflessione
- Schema biincernierato: L0 = L
- Schema incastro-libero: L0 = 2L
- Schema incastro-cerniera: L0 = 0.7L
- Schema biincastrato (ideale): L0 = 0.5L

### Momento di inerzia sezioni
- Rettangolo (b×h): I = b·h³/12 ; W = b·h²/6
- Cerchio (∅d): I = π·d⁴/64 ; W = π·d³/32
- Sezioni IPE/HEA: vedere tabelle profili

### Frecce limite (SLE)
| Caso | Limite |
|------|--------|
| Freccia totale | L/250 |
| Freccia diff. (dopo part. non strutt.) | L/500 |
| Freccia orizzontale (spostamento d'interpiano) | H/300 (NTC) |
| Spostamento d'interpiano sismico SLD | 0.005·H (telaio muratura) / 0.010·H (c.a.) |
