# Imposte Dirette — Tabelle e Aliquote

## IRPEF 2024 — Scaglioni e Aliquote
(Riforma IRPEF introdotta dal D.Lgs. 216/2023)

| Scaglione di reddito | Aliquota |
|----------------------|----------|
| Fino a €28.000 | 23% |
| Da €28.001 a €50.000 | 35% |
| Oltre €50.000 | 43% |

**Esempio calcolo IRPEF lorda su reddito €40.000:**
```
Primo scaglione:  €28.000 × 23% = €6.440
Secondo scaglione: €12.000 × 35% = €4.200
IRPEF lorda totale = €10.640
```

### Addizionali IRPEF
- **Addizionale regionale**: variabile per Regione (0,7% base — fino a ~3,33% per regioni con disavanzo sanitario)
- **Addizionale comunale**: deliberata dal Comune (generalmente 0–0,9%)
- Entrambe calcolate sul reddito imponibile IRPEF

---

## Detrazioni IRPEF per tipo di reddito (2024)

### Lavoro dipendente e assimilati
| Reddito complessivo | Detrazione |
|--------------------|-----------|
| ≤ €15.000 | €1.955 (minimo garantito €690 se imposta >0, oppure €1.380 se a tempo determinato) |
| €15.001 – €28.000 | €1.955 + quota variabile decrescente |
| €28.001 – €50.000 | €700 + quota decrescente |
| > €50.000 | €700 × (€80.000 − reddito) / €30.000 (azzerata a €80.000) |

**Trattamento integrativo (ex bonus Renzi)**: €1.200/anno per redditi ≤ €15.000; parziale tra €15.000–€28.000.

### Lavoro autonomo e impresa minore
| Reddito complessivo | Detrazione |
|--------------------|-----------|
| ≤ €5.500 | €1.265 |
| €5.501 – €28.000 | Decrescente da €1.265 a €500 |
| €28.001 – €55.000 | Decrescente da €500 a €0 |

### Pensione
| Reddito complessivo | Detrazione |
|--------------------|-----------|
| ≤ €8.500 | €1.955 (garantito €713 se imposta>0) |
| €8.501 – €28.000 | Decrescente |
| €28.001 – €55.000 | Da €700 a €0 decrescente |

---

## Carichi di famiglia 2024

**Figli a carico (≥21 anni, reddito ≤ €2.840,51 o €4.000 se < 24 anni):**
- Detrazione: €950 per figlio (da ripartire tra i genitori)
- Maggiorazione: +€200 per figlio con disabilità
- Maggiorazione: +€200 per figli da 21 a 24 anni
- La detrazione si riduce al crescere del reddito (formula: detrazione × (95.000 − reddito) / 95.000)

**Nota importante**: per figli < 21 anni → Assegno Unico Universale INPS (non detrazione fiscale)

**Coniuge a carico (reddito ≤ €2.840,51):**
- ≤ €15.000: €800
- €15.001–€40.000: Da €690 a €690 (con formula decrescente)
- €40.001–€80.000: Decrescente fino a €0

**Altri familiari a carico (genitori, fratelli, nuore/generi conviventi):**
- €750 per ciascuno (decrescente al crescere del reddito)

---

## Regime Forfettario — Coefficienti di Redditività per Categoria ATECO (principali)

| Gruppo di attività | Codice ATECO | Coefficiente |
|--------------------|--------------|-------------|
| Industrie alimentari e bevande | 10–11 | 40% |
| Commercio ambulante alimentari | 47.81 | 40% |
| Commercio ambulante altri prod. | 47.82–47.89 | 54% |
| Commercio al dettaglio | 45–46, 47 (esclusi sopra) | 40% |
| Commercio all'ingrosso | 45, 46 | 40% |
| Costruzioni e att. immobiliari | 41–43, 68 | 86% |
| Intermediari del commercio | 46.1 | 62% |
| Servizi di alloggio e ristorazione | 55–56 | 40% |
| Attività professionali, scientifiche | 64–66, 69–75, 85, 86–88, 90–92, 94–99 | 78% |
| Attività finanziarie e assicurative | 64–66 | 78% |
| Altre attività economiche | tutte le altre | 67% |

**Calcolo imposta sostitutiva forfettario:**
```
Reddito imponibile = Ricavi × Coeff. redditività
Imposta sostitutiva = Reddito imponibile × 15% (ordinario)
                    = Reddito imponibile × 5%  (start-up, primi 5 anni)

Contributi INPS (artigiani/commercianti) con riduzione 35%:
Contributi normali × 65% = Contributi ridotti
```

---

## IRES 2024 — Imposta sul Reddito delle Società

**Aliquota base**: 24%
**IRAP**: 3,9% (variabile per regione e settore)
- Banche e assicurazioni: 4,65% e 5,90%
- Imprese pubbliche: 3,80%

### Deducibilità IRAP ai fini IRES
- Quota IRAP relativa al costo del lavoro: deducibile al 100% (dal 2022 il costo del lavoro non concorre alla base IRAP)
- Quota IRAP relativa agli interessi passivi: deducibile al 10%

### Perdite fiscali IRES
- Riportabili illimitatamente nel tempo
- Limite di utilizzo: 80% del reddito imponibile di ciascun periodo
- Eccedenza non utilizzata riportabile agli anni successivi
- Perdite dei primi 3 anni di attività: riportabili senza limite dell'80%

### Mini-IRES / Aliquota ridotta (se vigente)
Verificare se la legge di bilancio dell'anno ha introdotto aliquote ridotte per utili reinvestiti.

---

## Ritenute alla fonte

### Lavoro dipendente
Il sostituto d'imposta (datore di lavoro) applica le ritenute IRPEF sulle retribuzioni mensili in base alle aliquote per scaglioni, tenendo conto delle detrazioni dichiarate dal dipendente con il modello dipendente.

**Tredicesima**: tassata secondo le aliquote IRPEF ordinarie
**TFR**: tassazione separata con aliquota media degli ultimi 5 anni

### Lavoro autonomo (compensi a professionisti)
- Ritenuta del **20%** sui compensi corrisposti a persone fisiche con partita IVA
- I forfettari non subiscono ritenuta (autocertificazione)
- Ritenuta del **30%** su compensi a non residenti

### Dividendi e utili
- Dividendi da SRL/SPA a persone fisiche non imprenditori: ritenuta secca **26%**
- Dividendi a società di capitali (holding): **esenti al 95%** se partecipazione qualificata detenuta da almeno 12 mesi (participation exemption)
- Dividendi a persone fisiche imprenditori: 58,14% concorre a reddito d'impresa (aliquota IRPEF progressiva)

### Interessi e capital gain
- Interessi bancari, obbligazioni: **26%**
- Capital gain da cessione partecipazioni non qualificate: **26%**
- Capital gain da partecipazioni qualificate (>20% diritti voto o >25% capitale): 26% sulla base imponibile del 100% (dal 2019)
- Plus da cessione immobili (prima dei 5 anni): IRPEF ordinaria o imposta sostitutiva 26% (opzione)
- Plus da cessione immobili ristrutturati con Superbonus: tassazione speciale se ceduti entro 10 anni

---

## Previdenza complementare

**Deduzione IRPEF**: contributi versati a fondi pensione → deducibili fino a **€5.164,57/anno**
**Al pensionamento**: tassazione agevolata sull'erogazione (dal 15% al 9% in funzione degli anni di iscrizione)
**RITA** (Rendita Integrativa Temporanea Anticipata): prelievo del 15% sulla rendita (ridotto del 0,3% per ogni anno oltre il 15° di partecipazione, fino a min 9%)

---

## Contributi INPS 2024 (valori orientativi — verificare circolare annuale INPS)

### Artigiani
- Sul minimale (€18.415): contributo fisso ~€4.427
- Sull'eccedente fino a €55.008: 24%
- Sull'eccedente da €55.008 a €86.983: 25%
- Massimale di reddito: €86.983 (no contributi sulla parte eccedente)

### Commercianti
- Stesse soglie degli artigiani
- Aliquota leggermente più alta (~24,48% per titolari)

### Gestione Separata INPS (lavoratori autonomi senza Cassa)
- Con partita IVA: **26,07%**
- Senza partita IVA (co.co.co.): **35,03%** (di cui 2/3 a carico del committente)
- Massimale contributivo 2024: €119.650

### ISA — Indici Sintetici di Affidabilità Fiscale
Gli ISA sostituiscono gli studi di settore dal 2019.
- Punteggio da 1 a 10 calcolato su dati contabili e strutturali
- Punteggio ≥ 8: accesso ai benefici premiali (preclusione accertamenti sintetici, rimborsi IVA prioritari, ecc.)
- Punteggio < 6: rischio maggiore di accertamento
