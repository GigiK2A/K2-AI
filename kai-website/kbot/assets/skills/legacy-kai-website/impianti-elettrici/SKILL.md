---
name: impianti-elettrici
description: >
  Skill specializzata su impianti elettrici italiani. Usa sempre questa skill per:
    normativa (D.M. 37/2008, DPR 462/2001, D.Lgs. 81/2008), norme CEI (64-8, 11-27, 0-21,
    EN 61439), protezioni (differenziali AC/A/F/B, magnetotermici, SPD, AFDD), impianti di
    terra (TT/TN, dispersori, CEI 64-12), fotovoltaico e BESS (CEI 0-21, dimensionamento
    stringa), quadri BT/MT (CEI EN 61439, selettività, forme), verifiche (Zs, isolamento,
    terra, CEI 64-8/6), ATEX (zone, modi Ex, CEI EN 60079), motori e avviamento (DOL, Y-Δ,
    VFD, classi IE), cabine MT/BT (trasformatori, relè 50/51/51N, Icc), scariche atmosferiche
    (LPS, CEI EN 62305, captatori, calate), illuminazione (LED, lux, emergenza CEI EN 50172,
    DALI), ricarica EV (wallbox, EVSE, CEI 64-8 sez.722), ambienti speciali (ospedali IT-M,
    piscine, cantieri CEE), domotica (KNX, BTicino MyHome), efficienza energetica (cosφ,
    armoniche, THD, audit), dimensionamento cavi, caduta di tensione, DdC, errori comuni.
---

## Come usare questa skill

1. **Identifica la categoria** della domanda (normativa, CEI, fotovoltaico, terra, protezioni, quadri, verifiche, ATEX, calcoli)
2. **Consulta il file di riferimento** corrispondente nella cartella `references/`
3. **Cita le fonti** pertinenti con norma e URL quando disponibili
4. **Distingui** tra norme cogenti (leggi, DM, DPR) e norme tecniche volontarie (CEI) ma di fatto obbligatorie per presunzione di conformità
5. **Avvisa** sempre quando la risposta richiede un professionista abilitato o lavori sotto tensione

---

## Struttura delle risorse

| File | Contenuto |
|------|-----------|
| `references/normativa.md` | D.M. 37/2008, DPR 462/2001 e leggi italiane |
| `references/norme-cei.md` | CEI 64-8, CEI 11-27, CEI 0-21 e altre norme tecniche |
| `references/impianti-terra.md` | Messa a terra, sistemi TT/TN, formule dispersori, sezioni PE, bagni |
| `references/protezioni.md` | Differenziali (AC/A/F/B), magnetotermici, CEI EN 61008/61009 |
| `references/fotovoltaico.md` | CEI 0-21, dimensionamento stringa, BESS, iter allaccio, GSE |
| `references/didattica.md` | Portate cavi, caduta di tensione, dimensionamento protezioni, fattori di potenza |
| `references/quadri-elettrici.md` | CEI EN 61439, forme di separazione, IP, selettività, quadri civili |
| `references/verifiche-misure.md` | CEI 64-8 Parte 6, misura Zs, isolamento, terra, differenziali, strumenti |
| `references/atex.md` | Zone ATEX, modi di protezione Ex, categorie, DPCE, CEI EN 60079 |
| `references/motori-avviamento.md` | Motori asincroni, DOL/Y-Δ/soft starter/VFD, dimensionamento protezioni, classi IE |
| `references/cabine-mt.md` | Cabine MT/BT, trasformatori, celle MT, protezioni (relè 50/51/51N), terra MT, CEI 11-1 |
| `references/scariche-atmosferiche.md` | LPS esterno/interno, calcolo rischio CEI EN 62305, LPL, captatori, calate, SPD T1/T2/T3 |
| `references/illuminazione.md` | LED, grandezze fotometriche, calcolo lux, emergenza CEI EN 50172, DALI, efficienza LENI |
| `references/evse-wallbox.md` | Modi ricarica 1–4, Tipo 2/CCS, CEI 64-8 Sez. 722, dimensionamento, condominio, V2G |
| `references/ambienti-speciali.md` | CEI 64-8 Parte 7: ospedali (IT-M, IMD), piscine (zone), cantieri (CEE), agricolo |
| `references/domotica-bus.md` | KNX, BTicino MyHome/SCS, DALI, Zigbee, integrazione FV/EVSE/illuminazione |
| `references/efficienza-energetica.md` | Rifasamento, armoniche, THD, audit D.Lgs. 102/2014, monitoraggio energetico |
| `references/errori-comuni.md` | 20+ errori tipici di progettazione/installazione con cause, conseguenze e soluzioni |

---

## Principi tecnici fondamentali

### Gerarchia normativa italiana (impianti elettrici)
1. **Legge / DPR / D.M.** → obbligatori per legge
2. **Norme CEI** → volontarie, ma creano presunzione di conformità alla regola dell'arte
3. **Guide CEI / Guide applicative** → supporto all'interpretazione

### Regola dell'arte (art. 6 D.M. 37/2008)
Gli impianti devono essere realizzati a regola d'arte. Presunzione di conformità se realizzati
secondo le norme CEI vigenti.

### Aggiornamento CEI 64-8 — Edizione IX (novembre 2024)
La norma fondamentale sugli impianti elettrici BT è stata sostanzialmente rivista:
- **Cap. 37**: livelli residenziali aggiornati (1-2-3)
- **Parte 6**: nuove prescrizioni per verifiche iniziali e periodiche
- **Parte 8.1**: efficienza energetica degli impianti BT
- **Parte 8.2**: utenti attivi BT (prosumer, accumuli, V2G)
- **Armonizzazione** con il Codice di Prevenzione Incendi VV.F.

> ⚠️ Per progetti iniziati dopo il 1/11/2024, applicare obbligatoriamente la IX edizione.

### Soggetti abilitati (D.M. 37/2008, art. 3)
- Installatori: imprese iscritte alla CCIAA con requisiti tecnico-professionali
- Progettisti obbligatori: impianti oltre le soglie (es. >6 kW, ambienti speciali, ecc.)
- Dichiarazione di conformità (DdC): obbligatoria al termine dei lavori

---

## Linee guida per le risposte

### Formato
- Usa **tabelle** per confronti tra valori, tipi di dispositivi, sezioni cavi
- Usa **formule** con descrizione delle variabili ed esempi numerici quando si chiede un calcolo
- Cita sempre la **norma di riferimento** (es. "CEI 64-8 art. 5.2") quando fornisci un valore normativo
- Per domande complesse, struttura la risposta con: principio → norma → formula/tabella → esempio → avviso

### Avvisi obbligatori
Includi sempre un avviso nei seguenti casi:
- **Lavori sotto tensione**: ricordare che sono vietati ai non abilitati PES/PAV (CEI 11-27)
- **Impianti ATEX**: la progettazione richiede competenze certificate
- **Ambienti medici**: normativa specifica CEI 64-8 V7-710, verifiche annuali
- **Soglie progetto**: ricordare quando è obbligatorio un professionista (D.M. 37/2008 art. 5)
- **DPR 462/2001**: nei luoghi di lavoro la verifica periodica è un obbligo di legge

### Tono
- Rispondi con precisione tecnica ma linguaggio chiaro
- Se l'utente usa terminologia da elettricista/installatore → rispondi con linguaggio tecnico diretto
- Se l'utente sembra un privato/non tecnico → spiega i concetti prima delle formule
- Non avere paura di dire "questo calcolo dipende da variabili che vanno verificate in situ"

---

## Risposte rapide per domande frequenti

**"Quando serve il progetto?"**
→ Leggi `references/normativa.md`, sezione soglie progetto D.M. 37/2008

**"Come si verifica l'impianto di terra?"**
→ Leggi `references/impianti-terra.md` (formule RE, dispersori) + `references/verifiche-misure.md` (misura telluometro)

**"Quale differenziale usare con un inverter fotovoltaico?"**
→ Leggi `references/protezioni.md` (tipo B o A con filtro) + `references/fotovoltaico.md`

**"Cos'è la CEI 64-8?"**
→ Leggi `references/norme-cei.md`, sezione CEI 64-8

**"Dimensionamento cavi / caduta di tensione"**
→ Leggi `references/didattica.md` (tabelle portate, formule ΔU monofase/trifase, fattori correzione)

**"Come verifico un impianto elettrico? Quali misure devo fare?"**
→ Leggi `references/verifiche-misure.md` (sequenza CEI 64-8 Parte 6, Zs, isolamento, terra, differenziali)

**"Che quadro uso? Forma di separazione, IP, selettività"**
→ Leggi `references/quadri-elettrici.md` (CEI EN 61439, tabelle IP, forme, selettività)

**"Impianto in zona ATEX / atmosfera esplosiva"**
→ Leggi `references/atex.md` (classificazione zone, modi Ex, categorie, DPCE, CEI EN 60079)

**"Avviamento motore, soft starter, VFD, stella-triangolo"**
→ Leggi `references/motori-avviamento.md` (confronto sistemi, dimensionamento protezioni, classi IE, risparmio energetico)

**"Cabina MT/BT, trasformatore, celle MT, protezioni MT, relè 51N"**
→ Leggi `references/cabine-mt.md` (schema cabina, tipologie celle, trasformatori, Icc BT, sistemi neutro MT, terra CEI EN 50522)

**"Protezione fulmini, LPS, calcolo rischio fulmine, captatori, calate"**
→ Leggi `references/scariche-atmosferiche.md` (CEI EN 62305, calcolo Nd, LPL I-IV, metodi captatori, distanza separazione, SPD T1/T2/T3, DPR 462/2001)

**"Illuminazione, LED, calcolo lux, emergenza, DALI"**
→ Leggi `references/illuminazione.md` (grandezze fotometriche, tabelle Em CEI EN 12464-1, metodo del flusso, L70B50, emergenza CEI EN 50172, DALI, LENI)

**"Wallbox, colonnina, ricarica EV, EVSE, Tipo 2, CEI 64-8 sez. 722"**
→ Leggi `references/evse-wallbox.md` (modi 1–4, connettori, sezione cavi, differenziale tipo B, load management, condominio, V2G)

**"Ospedale, sala operatoria, sistema IT-M, IMD, LIM, piscina, cantiere"**
→ Leggi `references/ambienti-speciali.md` (CEI 64-8 Parte 7: gruppi 0/1/2, IT medicale, zone piscina, prese CEE, IP cantiere)

**"KNX, domotica, BTicino MyHome, bus SCS, automazione edificio"**
→ Leggi `references/domotica-bus.md` (struttura KNX, ETS, SCS/MyHome, OpenWebNet, integrazione FV/EVSE/DALI)

**"Rifasamento, cosφ, armoniche, THD, penale reattiva, audit energetico"**
→ Leggi `references/efficienza-energetica.md` (calcolo kvar, condensatori, filtri armoniche, D.Lgs. 102/2014, monitoraggio Modbus)

**"Errori comuni, cosa sbaglio, come non fare, checklist installazione"**
→ Leggi `references/errori-comuni.md` (20+ errori tipici su protezioni, cavi, terra, FV, quadri, ATEX, MT, documentazione)

**"Dimensionamento impianto fotovoltaico / stringa / BESS"**
→ Leggi `references/fotovoltaico.md` (formule Voc, MPPT, stima produzione, accumulo)
