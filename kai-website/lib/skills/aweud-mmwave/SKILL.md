---
name: aweud-mmwave
description: >
  Skill per l'installazione degli apparati AWEUD mmWave 5G nei siti iliad: specifiche tecniche,
  modalità di montaggio, distanze di sicurezza, cablaggio e configurazioni a 24GHz e 26GHz.
  Usa SEMPRE questa skill quando l'utente dice "AWEUD iliad", "mmWave iliad", "5G millimetrico",
  "24GHz iliad", "26GHz iliad", "ASMR Nokia iliad", "AirScale mmWave", "installazione AWEUD",
  "distanza antenne AWEUD", "cablaggio AWEUD", "AMTA staffa AWEUD", "OCTIS cavo AWEUD",
  "banda n258", "banda n257", "frequenze millimetriche iliad", "5G mmWave antenna attiva",
  "linee guida installative AWEUD".
metadata:
  version: "0.1.0"
  author: "Luca Rossi"
  riferimento: "Linee guida installative AWEUD iliad v.1.1; Linee guida installative 26GHz AWEUD iliad v.1.1"
---

# AWEUD mmWave 5G — Installazione iliad

Questa skill guida l'installazione degli apparati AWEUD (AirScale mmWave Radio) nei siti iliad per il 5G millimetrico, coprendo le bande a 24 GHz e 26 GHz.

---

## Cos'è l'AWEUD

**AWEUD** = AirScale mmWave Radio (ASMR) — unità radio di quinta generazione che opera nello spettro delle onde millimetriche (da 24 GHz a 300 GHz).

L'AWEUD è un'**antenna attiva integrata** (beamforming): antenna e unità radio sono in un unico dispositivo compatto, con beamforming analogico.

---

## Specifiche Tecniche — AWEUD 24 GHz (banda n258)

| Proprietà | Valore |
|-----------|--------|
| Codice prodotto | 475169A |
| Frequenza | 24.25 – 27.50 GHz, 3GPP band **n258** |
| Duplex | TDD, 3GPP |
| Modulazione | Up to 64 QAM (DL e UL) |
| TXRX | 2T2R |
| Antenna elements | 192 AE, dual polarized (12 × 8 array) |
| Beamforming | Analogico integrato |
| Occupied BW (oBW) | 800 MHz |
| Instantaneous BW (iBW) | 1400 MHz |
| Carrier BW supportata | 100 MHz (fino a 8 × 100 MHz nei limiti oBW) |
| EIRP massimo | 55 dBm |
| Potenza consumo max | 250 W (senza moduli estensione) / 430 W (con 2 moduli estensione) |
| Altezza | 325 mm |
| Larghezza | 270 mm |
| Profondità | 115 mm |
| Peso | 10 kg (con antenna integrata) |
| IP rating | IP65 |
| Temperatura operativa | -40°C ÷ +55°C |
| Raffreddamento | Convezione naturale |

---

## Interfacce AWEUD

| Interfaccia | Label | N° | Connettore | Note |
|-------------|-------|:--:|-----------|------|
| Alimentazione DC | DC IN | 1 | OCTIS Plug Kit DC Power | -40.5 a -57 V DC |
| Ottica fronthaul | OPT 0, OPT 1 | 2 | OCTIS Plug Kit SFP/SFP+ | 2× SFP28 25 Gbps per eCPRI |
| Moduli estensione | EXT MOD 1, EXT MOD 2 | 2 | OCTIS Wide Multi-Channel Hybrid Cable | Per moduli estensione mmWave |
| Messa a terra | — | 1 | Ground lug 6 AWG M5 2 hole straight | Crimpare secondo istruzioni produttore |
| LED stato | LED | 1 | — | Indicazione stato operativo |

---

## Configurazione Standard a 2 Settori (Main Stream)

Una configurazione a 2 settori richiede:
- N.2 × AWEUD AirScale mmWave 24 GHz
- N.2 AMTA (ASMR Wall/Pole mount kit — kit di staffa)
- N.2 link OM3 MM (1 link per AWEUD) + N.2 OCTIS NOKIA SFP
- N.2 cavi DC FG16OH2R16 2×4 mmq + N.2 OCTIS NOKIA Power
- N.4 AOMC SFP28 70m MM I-temp RS (fibra ottica fronthaul)
- N.1 BBU Capacity Board ABIO (+ ASIB se swap ASIK)
- GPS antenna (se 5G non già presente sul sito)

---

## Regole di Posizionamento (OBBLIGATORIE)

L'AWEUD è un'**antenna attiva** (radiante attivo integrato). Le distanze di sicurezza sono tassative:

### Distanze minime da altri radianti

| Tipo radiante adiacente | Distanza minima dal bordo AWEUD |
|------------------------|--------------------------------|
| Antenna passiva (legacy 4G/5G sub-6GHz) | ≥ **30 cm** (bordo antenna passiva) |
| Antenna attiva (altro radiante attivo) | ≥ **50 cm** (bordo antenna attiva) |

> **ATTENZIONE**: Le distanze minime sono vincolanti per evitare interferenze e garantire la sicurezza CEM.

### Allineamento rispetto alle antenne legacy

- Il posizionamento degli AWEUD deve **mantenere l'allineamento dei piani verticali** degli altri radianti (stessa direzione azimutale del settore)
- Posizione: **on top** (sopra) o **affiancata** alla legacy
- Allineamento: i **top-antenna** devono essere allineati

### Compatibilità tecnologica

- Configurazione bi-settoriale compatibile con **4G legacy** e **700 MHz** (se presente)
- **Non supportata** la configurazione con 5G 3700 MHz (n78)

---

## Modalità di Montaggio (Staffa AMTA)

La staffa **AMTA (475128A)** — ASMR Wall/Pole Vertical/Horizontal Mounting Bracket — è il kit standard di montaggio.

### Montaggio a palina

- Fissaggio su palina con collari (2x morsetti a nastro in acciaio inox per palo)
- Bulloni M8 con rondelle (inclusi nella delivery)
- Posizionamento verticale o orizzontale (staffa regolabile)
- Verificare capacità portante della palina (peso AWEUD = 10 kg, vento su area 270×325 mm)

### Montaggio a parete

- Fissaggio diretto a parete con tasselli (sito RT)
- Staffa AMTA in configurazione wall mount

---

## Cablaggio AWEUD

### 1. Alimentazione DC

- Cavo: FG16OH2R16 2×4 mm² (resistente agli UV, outdoor)
- Connettore: OCTIS Plug Kit DC Power (crimpare secondo istruzioni)
- Tensione: da FPRB/FPBC (-48V DC nominale, range -40.5 / -57V)
- Percorso: dal quadro FPRB → lungo la struttura → all'AWEUD in quota
- Fissaggio: con fascette ogni 30-40 cm, proteggi da usura nei punti di curvatura

### 2. Fibra Ottica Fronthaul (eCPRI)

- Cavo: OM3 MM 50/125 µm (per distanze fino a 70-100m)
- Connettori: OCTIS NOKIA SFP+ sul lato BBU; OCTIS Plug Kit SFP sul lato AWEUD
- Interfaccia: SFP28 25 Gbps (OPT 0 o OPT 1)
- Percorso: dal BBU/NodeBox → lungo la struttura → all'AWEUD
- Raggio di curvatura minimo cavo OM3: rispettare indicazioni produttore (tipicamente ≥ 10× diametro)

### 3. Messa a terra

- Connettore: Ground lug 6 AWG M5 2 hole straight (incluso nella delivery)
- **Crimpare il connettore secondo le istruzioni del produttore** (non serrare manualmente)
- Collegare al sistema di terra del palo/struttura
- Sezione conduttore di terra: min. 6 AWG ≈ 16 mm²

---

## AWEUD 26 GHz (banda n257/n258 26GHz)

La variante a 26 GHz (da "Linee guida installative 26ghz AWEUD v.1.1") ha caratteristiche analoghe all'AWEUD 24 GHz con le seguenti differenze:

| Proprietà | AWEUD 24 GHz | AWEUD 26 GHz |
|-----------|:---:|:---:|
| Banda 3GPP | n258 (24.25-27.50 GHz) | n257/n258 (24.25-29.50 GHz) |
| Frequenza centrale | ~26 GHz | ~26.5 GHz |
| Standard | TDD, 3GPP | TDD, 3GPP |
| Cablaggio | Identico | Identico |
| Staffa | AMTA | AMTA |

Le regole di posizionamento, distanze minime e procedure di cablaggio sono identiche alle linee guida AWEUD 24 GHz.

---

## Checklist Installazione AWEUD

Prima dell'installazione:
- [ ] TSSR completato e approvato
- [ ] Scheda Radio di progetto disponibile in cantiere
- [ ] Distanze dagli altri radianti verificate (≥30cm passivi, ≥50cm attivi)
- [ ] Struttura portante idonea al peso aggiuntivo (verificare VS)
- [ ] Cavi DC e fibra ottica pre-posati lungo la struttura

Durante l'installazione:
- [ ] Staffa AMTA installata e serrata a coppia prescritta
- [ ] AWEUD fissato alla staffa (viti M5xL10 con rondelle, 2 pezzi)
- [ ] Connettore di terra crimpato e collegato
- [ ] Cavo DC collegato con OCTIS Plug Kit Power
- [ ] Fibra ottica fronthaul collegata con OCTIS Plug Kit SFP
- [ ] Allineamento verticale con antenne legacy verificato
- [ ] LED di stato acceso (verde = operativo)

Dopo l'installazione:
- [ ] Tutte le connessioni impermeabilizzate (outdoor IP65 raggiunto)
- [ ] Cavi fissati lungo la struttura
- [ ] Documentazione fotografica eseguita
- [ ] Checklist consegnata all'ufficio tecnico

---

## Attivare Skill Complementari

- **installazione-apparati** — per il contesto generale di installazione sito (FPRB, BBU, configurazioni T1/T3)
- **relazioni-strutturali** — per la verifica strutturale del palo/struttura con i nuovi carichi AWEUD
- **elaborati-impianti** — per il cablaggio elettrico (DC feed dall'FPRB all'AWEUD)
