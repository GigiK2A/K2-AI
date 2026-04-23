---
name: impianti-termici-hvac
description: >
  Esperto termotecnico HVAC per edifici italiani. Invoca per: caldaie condensazione, pompe di
  calore (aria/acqua/geotermica/sonde verticali), pannelli radianti, solare termico ACS, VAV,
  split/VRF/chiller, free cooling, VMC/UTA, psicrometria, deumidificazione, portate d'aria
  (ristoranti, uffici, palestre), APE/SIAPE/classi A4-G, NZEB, dispersioni termiche, reti
  idrauliche, bilanciamento, vasi espansione, ACS/Legionella/accumuli, BMS/regolazione
  climatica/KNX/BACnet, acustica impianti/NC/LWA, collaudo/TAB/DdC/F-Gas, Conto Termico 3.0,
  EPBD 2024, Ecodesign UE. Attiva per: UNI TS 11300, UNI EN ISO 12831, UNI 10339, UNI 11466,
  EN 15232, DM 26/06/2015, D.Lgs. 192/2005, D.M. 37/2008, D.P.R. 74/2013, zone climatiche,
  gradi giorno, EPH, COP/SEER/SCOP, geotermia — residenziale, uffici, ospedali, industriale.
---

## Come usare questa skill

1. **Identifica la categoria** della domanda: carichi/dispersioni, riscaldamento, raffrescamento, ventilazione, normativa, APE, calcoli idraulici, selezione componenti
2. **Consulta il file di riferimento** corrispondente nella cartella `references/`
3. **Cita le fonti** con norma e articolo pertinenti
4. **Distingui** tra norme cogenti (D.Lgs., D.M., D.P.R.) e norme tecniche UNI/EN (presunzione di conformità)
5. **Avvisa** quando la risposta richiede un progettista abilitato, collaudo o dichiarazione di conformità

---

## Struttura delle risorse

| File | Contenuto |
|------|-----------|
| `references/carichi-termici.md` | Calcolo dispersioni invernali (UNI EN ISO 12831), carichi estivi (UNI 10339), metodo semplificato e dettagliato |
| `references/riscaldamento.md` | Caldaie (condensazione, biomassa), pompe di calore aria/acqua e geotermiche, pannelli radianti a pavimento/parete/soffitto, radiatori, ventilconvettori (fancoil) |
| `references/raffrescamento.md` | Chiller, gruppi frigo, VRF/VRV, split e multisplit, free cooling, torri evaporative, fancoil, raffreddamento adibatico |
| `references/ventilazione.md` | UTA, VMC, recuperatori di calore, portate d'aria (UNI 10339), qualità aria interna (IAQ), filtrazione, classificazione filtri EN ISO 16890 |
| `references/reti-idrauliche.md` | Perdite di carico (Darcy-Weisbach, Moody), dimensionamento tubazioni, bilanciamento, pompe di circolazione (curva, punto di lavoro), vasi di espansione, valvole sicurezza |
| `references/normativa.md` | D.Lgs. 192/2005, D.P.R. 74/2013, D.M. 37/2008, D.Lgs. 102/2014, direttiva F-Gas, requisiti minimi NZEB |
| `references/ape-certificazione.md` | APE, classi energetiche A4-G, EPH/EPC/EPw/EPe, metodo di calcolo (UNI TS 11300), attestazione e registrazione |
| `references/ambienti-speciali.md` | Data center e shelter TLC, sale operatorie e ospedali, ambienti industriali e clean room, piscine, grandi cucine |
| `references/solare-termico-cogenerazione.md` | Solare termico (collettori, dimensionamento ACS/riscaldamento), cogenerazione CHP, trigenerazione, teleriscaldamento, deumidificatori, comfort termico PMV/PPD |
| `references/incentivi-fiscali.md` | **Conto Termico 3.0** (DM 07/08/2025, in vigore dal 25/12/2025), Ecobonus, TEE, requisiti tecnici PdC/solare/biomassa, aliquote, massimali, modalità accesso GSE |
| `references/acs-dimensionamento.md` | Fabbisogno ACS per destinazione d'uso (UNI EN 15316), dimensionamento serbatoi accumulo, Legionella (temperature, igienizzazione, D.Lgs. 81/2008), reti di ricircolo, coibentazione, VMT, PdC per ACS |
| `references/bms-regolazione.md` | BMS/BACS classi EN 15232 (A–D), regolazione climatica, sonde e valvole, protocolli BACnet/Modbus/KNX, algoritmi PID, DCV, free cooling, night setback, contabilizzazione calore D.Lgs. 102/2014 |
| `references/acustica-impianti.md` | Limiti DPCM 05/12/1997, classificazione acustica UNI 11367, potenza sonora UE split/VRF/chiller, NC per ambienti, velocità aria in canali, silenziatori, antivibranti, isolamento locali tecnici |
| `references/psicrometria-vav.md` | Diagramma psicrometrico, formule aria umida (x, h, T_rugiada), cicli UTA (estivo/invernale), raffreddamento con deumidificazione, ADP, umidificazione adiabatica/vapore, sistemi VAV (terminali, dimensionamento, bilanciamento, inverter), IAQ e CO₂ |
| `references/geotermia.md` | Sonde geotermiche verticali (UNI 11466/11467/11468), calcolo lunghezza sonde, potenza specifica per terreno, TRT, grouting, loop orizzontali, acqua di falda (GWHP), energy pile, free cooling passivo, COP/SCOP PdC geotermiche, autorizzazioni |
| `references/collaudo-commissioning.md` | DdC D.M. 37/2008, libretto impianto D.P.R. 74/2013, prova di tenuta idraulica, TAB aeraulico e idronico (UNI EN 12599), prima accensione caldaia/PdC/VRF, commissioning BMS (FPT), collaudo F-Gas, verbale tipo |
| `references/errori-comuni.md` | Errori tipici di progettazione e installazione con cause, conseguenze e soluzioni |



### Aggiornamenti normativi 2025-2026 (febbraio 2026)

**DM Requisiti Minimi 28 ottobre 2025** (vigente dal 3 giugno 2026)
- Aggiorna le norme sulle prestazioni energetiche minime degli edifici
- Impatto su NZEB, requisiti EPH/EPC, categorie edifici
- Verificare conformità progetti nuovi e ristrutturazioni importanti

**EPBD IV (Dir. 2024/1275) — Recepimento in ritardo**
- Scadenza recepimento: 29 maggio 2026
- Italia non ha avviato formalmente il recepimento a febbraio 2026
- Impatto atteso: nuove definizioni NZEB, obblighi heat pump rate, smart readiness
- **Monitorare decreti attuativi e aggiornamenti SIAPE** per conformità futura

**Conto Termico 3.0**
- In fase di attuazione (DM 07/08/2025, vigente dal 25/12/2025)
- Monitorare decreti attuativi per modalità accesso, massimali aggiornati e tempistiche riconoscimento
---

## Principi tecnici fondamentali

### Gerarchia normativa italiana (impianti termici)
1. **D.Lgs. / D.M. / D.P.R.** → obbligatori per legge (es. D.Lgs. 192/2005, D.P.R. 74/2013)
2. **Norme UNI / EN / ISO** → tecnicamente volontarie, ma danno presunzione di conformità alla regola dell'arte
3. **Guide UNI / Linee guida CTI** → supporto interpretativo

### Approccio alla progettazione termica
La progettazione segue sempre questo ordine logico:
1. **Fabbisogno** → calcolo carichi termici invernali ed estivi (UNI EN ISO 12831 / UNI 10339)
2. **Soluzione impiantistica** → scelta della tecnologia in base a vincoli (edificio, zona climatica, combustibile, budget)
3. **Dimensionamento** → potenza generatore, superficie emittenti, portate fluidi
4. **Distribuzione** → rete tubazioni, perdite di carico, bilanciamento, pompe
5. **Regolazione** → controllo climatico, valvole termostatiche, cronotermostati, BMS
6. **Verifiche normative** → conformità D.Lgs. 192, requisiti minimi, EPH

### Zone climatiche italiane
| Zona | GG (Gradi Giorno) | Esempi |
|------|-------------------|--------|
| A | ≤ 600 | Lampedusa |
| B | 601–900 | Reggio Calabria, Palermo |
| C | 901–1400 | Napoli, Bari, Roma (costa) |
| D | 1401–2100 | Roma, Firenze, Bologna |
| E | 2101–3000 | Milano, Torino, Venezia |
| F | > 3000 | Bolzano, zone alpine |

### Temperature di progetto invernali (UNI EN ISO 12831)
Temperature esterne di progetto θe per le principali città:
- Milano: -5°C | Torino: -8°C | Venezia: -5°C | Bologna: -5°C
- Firenze: -2°C | Roma: 0°C | Napoli: +2°C | Palermo: +5°C
- Bolzano: -12°C | Trieste: -3°C | Genova: +1°C

---

## Formule di riferimento rapido

### Potenza termica dispersa (metodo semplificato)
```
Q = U · A · (θi - θe)   [W]
```
- U = trasmittanza termica [W/m²K]
- A = superficie elemento [m²]
- θi = temperatura interna (generalmente 20°C)
- θe = temperatura esterna di progetto

### Fabbisogno energetico annuo riscaldamento (semplificato)
```
QH = Q · DD · 24 / (θi - θe)   [Wh]
```
- DD = gradi giorno della zona climatica
- 24 = ore/giorno

### Portata d'acqua in un circuito idronico
```
G = Q / (c · ρ · ΔT)   [kg/s]
```
- Q = potenza termica [W]
- c = calore specifico acqua ≈ 4186 J/kgK
- ρ = densità acqua ≈ 1000 kg/m³
- ΔT = salto termico mandata/ritorno [K] (tipico: 10 K riscaldamento, 5 K raffrescamento)

### Portata volumetrica
```
Q_vol = G / ρ = G / 1000   [m³/s] → × 3600 per avere m³/h
```
Regola pratica: **1 kW ≈ 86 l/h** (con ΔT = 10 K)

### COP e EER
- **COP** (riscaldamento): energia termica prodotta / energia elettrica assorbita
- **EER** (raffrescamento): energia frigorifera prodotta / energia elettrica assorbita
- **SCOP / SEER**: valori stagionali, usati per classificazione energetica UE

### Perdita di carico lineare (Darcy-Weisbach)
```
ΔP_lin = λ · (L/D) · (ρ·v²/2)   [Pa]
```
Oppure in forma pratica con la velocità specifica:
- Impianti idrici: velocità consigliata **0.5–1.5 m/s** (max 2 m/s per tubi > DN 50)
- Regola pratica: perdita di carico unitaria **100–200 Pa/m**

---

## Linee guida per le risposte

### Formato e struttura

Per **domande di calcolo**, struttura sempre la risposta così:
1. Dati di ingresso (con le ipotesi adottate, se mancano)
2. Formula con variabili spiegate
3. Calcolo numerico passo per passo
4. Risultato con unità di misura e norma di riferimento
5. Tabella di riepilogo finale (quando ci sono più risultati)
6. Margine di sicurezza consigliato e motivazione

Per **domande di scelta tecnologica**, usa sempre:
- Tabella comparativa con almeno 5 criteri (efficienza, investimento, manutenzione, rumore, flessibilità)
- Raccomandazione motivata in funzione del caso specifico
- Avvisi normativi pertinenti

Per **domande su relazioni tecniche**, fornisci:
- Indice completo della relazione con tutti i capitoli
- Per ogni capitolo: contenuto richiesto, metodo di calcolo, norma di riferimento
- Checklist finale di verifica pre-consegna

### Tabella riepilogo calcoli
Dopo ogni serie di calcoli, riepiloga con una tabella:

```
| Parametro | Valore | Unità | Norma |
|-----------|--------|-------|-------|
| Dispersioni totali | X | W/K | UNI EN ISO 12831 |
| Potenza termica richiesta | X | kW | — |
| Potenza generatore scelto | X | kW | — |
| Margine | X | % | — |
```

### Checklist di fine progetto
Per ogni progetto termotecnico, includi alla fine una checklist:
- [ ] Calcolo carichi termici eseguito con metodo normativo
- [ ] Generatore dimensionato con margine 15–25%
- [ ] Bilanciamento idraulico verificato
- [ ] Vaso di espansione e valvola di sicurezza dimensionati
- [ ] Conformità D.Lgs. 192/2005 verificata
- [ ] Dichiarazione di conformità D.M. 37/2008 prevista
- [ ] APE redatto se obbligatorio
- [ ] Registro F-Gas previsto se impianto con refrigeranti

### Avvisi obbligatori
Includi sempre un avviso nei seguenti casi:
- **Progettazione obbligatoria** (D.M. 37/2008 art. 5): potenza > 35 kW, edifici pubblici, condomini, industriale → progetto firmato da professionista abilitato
- **Dichiarazione di conformità** (D.M. 37/2008): obbligatoria al termine di ogni installazione/modifica
- **F-Gas**: interventi su impianti con refrigeranti fluorurati → operatori certificati F-Gas, registro perdite
- **Collaudo e messa in servizio**: verifica tenuta, bilanciamento, regolazione
- **APE obbligatorio**: compravendita, locazione, ristrutturazioni importanti

### Quando la domanda è ambigua
Se mancano dati essenziali (zona climatica, tipo edificio, superficie, trasmittanze), chiedi prima i dati necessari o fornisci la risposta con ipotesi esplicite chiaramente indicate e invita a verificare con i dati reali.

---

## Tecnologie a confronto

### Riscaldamento: confronto rapido

| Tecnologia | η / COP | Combustibile | Investimento | Note |
|------------|---------|--------------|--------------|------|
| Caldaia condensazione gas | 103–109% | Gas metano/GPL | Basso | Ancora dominante, incentivabile |
| Pompa di calore aria/acqua | COP 2.5–4.5 | Elettricità | Medio | Ottima con FV, incentivi Conto Termico |
| Pompa di calore geotermica | COP 3.5–5.5 | Elettricità | Alto | Massima efficienza, sonde/collettori |
| Caldaia biomassa (pellet) | 85–95% | Pellet/legna | Medio | Incentivabile, CO2 neutro |
| Solare termico + integratore | COP eq. > 5 | Solare | Medio | Obbligatorio quota NZEB |
| Cogenerazione (CHP) | η_tot 80–90% | Gas/biogas | Alto | Ottimo per H > 4.000 h/anno |
| Teleriscaldamento | — | Vario | Basso (allaccio) | Dove disponibile |

### Raffrescamento: confronto rapido

| Tecnologia | EER/SEER | Applicazione | Note |
|------------|----------|--------------|------|
| Split/Multisplit | 3–5 | Residenziale, piccoli uffici | Semplice, installazione rapida |
| VRF/VRV | 3.5–5 | Terziario, alberghi | Flessibile, refrigerante diretto |
| Chiller + fancoil | 2.5–4 | Grandi uffici, industria | Massima flessibilità, circuito acqua |
| Free cooling | — (integrato) | Climi continentali, data center | Gratuitamente quando Text < Tset |
| Raffr. adiabatico | — | Industria, climi secchi | Efficace, basso consumo |

---

## Dati tecnici di riferimento

### Trasmittanze limite D.Lgs. 192/2005 (zona E – nuova costruzione 2021+)
| Componente | U limite [W/m²K] |
|------------|-----------------|
| Pareti esterne opache | 0.26 |
| Copertura | 0.22 |
| Pavimento su terreno/pilotis | 0.28 |
| Finestre (telaio+vetro) | 1.40 |
| Vetro (solo) | 1.10 |

> Valori variano per zona climatica: consultare Allegato B D.Lgs. 192/2005 e DM 26/06/2015.

### Portate d'aria minime (UNI 10339)

| Destinazione d'uso | Portata rinnovo [l/s per persona] | Portata rinnovo [m³/h per persona] |
|--------------------|------------------------------------|-------------------------------------|
| Uffici aperti | 11 | 40 |
| Sale riunioni | 11 | 40 |
| Residenza | 0.5 vol/h o 11 l/s per persona | — |
| Ristoranti | 20 | 72 |
| Palestre | 20 | 72 |
| Ospedali (degenze) | 36 | 130 |

### Potenze termiche specifiche indicative

| Tipo edificio | Riscaldamento [W/m²] | Raffrescamento [W/m²] |
|---------------|---------------------|----------------------|
| Residenziale ben isolato (zona E) | 30–50 | 40–60 |
| Residenziale anni '80 (zona E) | 70–100 | 50–80 |
| Uffici (zona E) | 40–60 | 60–100 |
| Industriale (capannone) | 50–120 | 30–80 |
| Data center / Shelter | trascurabile | 800–2000 W/rack |
