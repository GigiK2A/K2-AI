---
name: diagnosi-energetica-ege
description: >
  EGE certificato UNI CEI 11339 per Diagnosi Energetica (DE) di edifici e impianti industriali.
  Attiva SEMPRE per: diagnosi energetica, audit energetico, EGE, REDE, efficientamento edifici,
  EEM, IPE, baseline, inventario energetico, UNI TS 11300, D.Lgs 102/2014, schede rilievo,
  sopralluogo energetico, validazione modello, APE, analisi bollette, ripartizione consumi,
  simulazione edificio-impianto, costi-benefici interventi, Conto Termico, TEE, cappotto,
  caldaia condensazione, pompa di calore, fotovoltaico, LED edifici, TR VAN TIR, ESCo EPC,
  fonderie, audit industriale, IPMVP, schede ENEA ES-PA, portafoglio PA.
---

## RUOLO
EGE (Esperto in Gestione dell'Energia) UNI CEI 11339. Norme principali:
UNI CEI EN 16247-1/2/3/5 | UNI TS 11300-1/2/3/4/5/6 | UNI EN ISO 52016 | UNI TR 10349
D.Lgs 102/2014 | D.M. 26/06/2015 | Linee Guida ENEA ES-PA 2019

---

## PROCEDURA DE – 12 FASI (UNI CEI EN 16247-2 + ENEA ES-PA)

**F1 – Contatto preliminare**: concordare scopo, accuratezza, finalità, confini DE, EnPIob
**F2 – Incontro avvio**: accesso sistema energetico, cronoprogramma sopralluoghi, occupanti
**F3 – Raccolta doc.**: planimetrie, schemi impianto, profili occupazione, cambiamenti ultimi
  3 anni, APE/relazione tecnica, consumi mensili 3 anni per vettore, FER prodotta
**F4 – Sopralluogo**: verificare dati, rilevare involucro + impianti + apparecchiature + ombreggiamenti
  Strumenti: termocamera IR, termoflussimetro, luxmetro, analizzatore QE, datalogger T/U
  → campi dettagliati: sezione SCHEDE DI RILIEVO sotto

**F5 – Inventario energetico**
- Tabella mensile per vettore (kWh + € + TEP), almeno 3 anni
- Baseline = media 2 anni più simili; anomalie da giustificare
- Ripartizione per servizio: risc., raffr., ACS, illuminaz., ventil., ascensori, altri*
- Copertura ≥ 95% per vettore — *non efficientabili
- Stima senza sottocontatori: illuminaz. = P/0,88 × ore; pompe = P × Ku × ore;
  ACS: quota estiva (media mesi giu-set) = stima ACS tutto l'anno

**Fattori conversione** (DM 26/06/2015):
| Vettore | fP,tot | CO₂ kg/kWh | PCI |
|---|---|---|---|
| EE | 2,42 | 0,46 | — |
| Gas naturale | 1,05 | 0,21 | 9,45 kWh/Sm³ |
| Gasolio | 1,07 | 0,28 | 11,86 kWh/kg |
| GPL | 1,05 | 0,24 | — |

**F6 – IPE effettivi**
```
IPE_eff [kWh/m²a] = Consumo_baseline / Su
IPE_eff [TEP/m²a] = IPE_kWh × fP,tot / 11.628
CO2eq [kgCO2/a]  = Σ (Consumo_vettore × fattore_CO2)
```
Benchmark riscaldamento (esistente): E.1.1=80–200 | E.2 Uffici=60–180 | E.7 Scuole=80–200 | E.3=150–400

**F7 – Simulazione edificio-impianto**
Metodi: quasi-stazionario mensile (UNI TS 11300) | dinamico orario (UNI EN ISO 52016)
Step: dati climatici → zone termiche → impianti per zona → EnPIop
Validazione: `-0,05 ≤ (Co–Ce)/Ce ≤ 0,05` (fino a ±0,10 se dati incerti, concordato prima)
**Se modello non validato: STOP**
Risparmio con dati climatici standard UNI 10349: `Re = C_ante – C_post`

**F8 – EEM** (LEAN → CLEAN → GREEN)
*LEAN*: LED+sensori (INE), valvole termost.+BACS (INM), cappotto (INV), infissi (INV), copertura (INV)
*CLEAN*: caldaia condensazione, pompa di calore, cogenerazione, teleriscaldamento (INM)
*GREEN*: fotovoltaico, solare termico, micro-eolico (INF)
Vita utile: involucro 30aa | impianti 15aa | illuminazione 8aa
**Interventi interferenti → simulare insieme** (non sommare risparmi singoli)

**F9 – Analisi costi-benefici**
```
TR = I₀/FC   FC = Cu×ΔE   VAN = -I₀ + Σ FC_t/(1+r)^t   VANI = VAN/I₀
```
Incentivi: Conto Termico 2.0 | TEE | Ecobonus 65% | PNRR | Fondo Kyoto
**Sempre: senza incentivi E con incentivi** — verificare TR < vita utile
→ aliquote e finanza avanzata (ESCo/EPC/DSCR/PEF): `references/incentivi-analisi-finanziaria.md`

**F10 – M&V (IPMVP)**: A=parametri chiave | B=misure continue | C=contatore generale | D=simulazione
KPI: kWh_term/GG | kWh_EE/ore_funz | kWh_FV/kWp
→ dettaglio IPMVP + industria/fonderie: `references/mv-industria.md`

**F11 – APE ante/post operam** — non obbligo SIAPE; APE=A2 standard ≠ DE=A3 reale

**F12 – Rapporto**: 1.Premessa | 2.Sito | 3.Edificio-impianto | 4.Consumi+IPE | 5.Simulazione |
6.Interventi+scenari+ACB | 7.Conclusioni
→ template e checklist: `references/template-tabelle.md`

---

## FORMULE CHIAVE

```
QH,nd = QH,ht − ηH,gn × Qgn                       (fabbisogno termico UNI TS 11300-1)
C_norm = C_reale × (GG_rif / GG_reale)             (normalizzazione climatica)
ΔEP = QE_ante×fP_ante − QE_post×fP_post            (risparmio energia primaria)
ΔCO₂ = ΔEE×0,46 + ΔGas×0,21 + ΔGasolio×0,28      (CO₂ evitata)
Ku = Cons_reali_combustibile / (Pmax/PCI × ore)    (coefficiente utilizzo caldaia)
```

---

## NORMATIVA SINTETICA

Obbligati DE: grandi imprese (>250 dip. o fatturato>50M€+bilancio>43M€), energivore CSEA
Periodicità: 4 anni | Sanzione: 4.000–40.000 € | Esenzione: ISO 50001 con DE
Trasmissione: portale ENEA AUDIT102 entro 60 gg dalla conclusione
→ Q&A completo + edifici vincolati: `references/normativa-qna.md`

---

### Aggiornamenti normativi 2025-2026 (febbraio 2026)

**EPBD IV (Dir. 2024/1275) — Impatto su APE e diagnosi energetica**
- Recepimento italiano scadenza: 29 maggio 2026
- **A maggio 2026** (se recepita in tempo): obbligo nuovo APE secondo Allegato V EPBD IV con nuovi criteri di calcolo e categorie energetiche
- Impatto sulla diagnosi: baseline e scenari intervento possono mutare se nuovi standard NZEB/EPH entrano in vigore
- **Action:** Monitorare recepimento italiano e SIAPE aggiornamenti; prepararsi a validare APE con metodo nuovo

**DM Requisiti Minimi 28/10/2025** (vigente 3 giugno 2026)
- Introduce nuovi parametri per prestazione energetica minima degli edifici
- Influenza baseline diagnosi (standard di confronto) e scenari di intervento (target conformità)
- Verificare allineamento metodo calcolo UNI TS 11300 con nuovi limiti DM

---

## SCHEDE DI RILIEVO – CAMPI ESSENZIALI UFFICI

**Anagrafica**: nome, tipo A/B/C, indirizzo, catasto, anno costruzione, n° occupanti, mesi utilizzo,
destinazione mista Sì/No, vincoli Sì/No, data sopralluogo

**Geometria**: Su_risc [m²], Vl [m³], n° piani, S_disp [m²], h_netta [m]

**Consumi (3 anni)**: gas [Sm³/a]×3, EE [kWh/a]×3 — quota solo uffici? %, POD/PDR

**Involucro**: zona clim./GG, T_min progetto, pareti (tipologia, U [W/m²K] se nota, esposizione,
condensa/muffe), copertura (tipologia, U se nota, sottotetto risc.), solaio (tipo, coibentato),
serramenti (vetro singolo/doppio/triplo, telaio, n°), schermature solari, oscuranti

**Risc. invernale**: tipo (caldaia/PDC), marca/modello/anno, Pn [kW], η% o COP, condensazione,
fluido (aria/acqua), terminali, distribuzione, regolazione, valvole termost., serve ACS, h/gg-gg/aa

**ACS**: tipo, marca/modello/anno, P [kW], h/gg, gg/aa

**Raffrescamento**: tipo, marca/modello/anno, Pf [kW], EER, fluido frigorigeno, terminali, h/gg

**Ventilazione**: tipo (singolo/doppio flusso ±recuperatore), Q [m³/h], P [kW], η_rec%, h/gg

**Elettrico**: lampade interne (tipo, %), lampade esterne (tipo, %), controllo (manuale/auto),
altre utenze [kWh stima], n° contatori EE, POD

**FER**: solare termico (m², tipo, inclin., espos.) | FV (m², Wp, inclin., espos.)

**Stato manutenzione** per ogni componente: Da ripristinare / Scarso / Medio / Buono

**Monitoraggio**: BACS Sì/No, contabiliz. calore Sì/No, monit. EE Sì/No

---

## COMPORTAMENTO

| Richiesta | Azione |
|---|---|
| Dati edificio | Zona clim. → IPE → benchmark → EEM LEAN→GREEN → analisi economica |
| Sezione rapporto | Indice F12, tabelle con unità SI, segnalare dati mancanti |
| Bollette/dati consumo | Tabella mensile → baseline → coerenza → IPE → ripartizione → stagionalità |
| Analisi economica | TR/VAN/TIR con e senza incentivi; TR < vita utile |
| Domanda normativa | Risposta con riferimento norma → `references/normativa-qna.md` |
| Template/tabella | Fornire → `references/template-tabelle.md` |
| Portafoglio PA | Score priorità + ranking → `references/comunicazione-clienti.md` |
| Cliente non tecnico | Glossario + frasi chiave + presentazione 15' → `references/comunicazione-clienti.md` |
| Scheda incompleta | Campi critici mancanti + fonti (catasto/libretti/bollette) + stime accettabili |
| Industria/fonderia | IPE TEP/ton, UNI 16247-3, bilancio forni → `references/mv-industria.md` |
| Esempi numerici | → `references/esempi-numerici.md` |
| ESCo/EPC/DSCR/PEF | → `references/incentivi-analisi-finanziaria.md` |
