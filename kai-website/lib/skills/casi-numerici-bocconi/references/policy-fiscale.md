# Casi Numerici — Policy Fiscale e PNRR

## Caso 1: Analisi Costo-Benefici (ACB) Progetto PNRR

**Contesto:** Comune italiano (Basilicata) valuta investimento in impianto solare su scuola pubblica. Finanziamento PNRR per €200k (grant 100%).

**Dati progetto:**
- Investimento iniziale: €200k
- Vita utile: 15 anni
- Generazione energetica annua: 50 MWh
- Prezzo energia (medio): €80/MWh (valore di mercato)
- Costi manutenzione annui: €3k
- Discount rate (sociale): 3.5%
- Benefici non-monetari: riduzione CO2 (1,500 ton CO2/anno equiv. a €80/ton = €120k/anno valore ambientale)

**Calcolo ACB:**

**Benefici (15 anni):**

| Anno | Benefici Energetici | Benefici Ambientali | Totale Benefici | PV@3.5% |
|------|---|---|---|---|
| 1 | €4,000 | €120,000 | €124,000 | €119,807 |
| 2-15 | €4,000 | €120,000 | €124,000 | €1,537,814 |
| **NPV Benefici** | | | | **€1,657,621** |

Cálculo: PV anno 1 = €124k / 1.035 = €119.8k; anni 2-15 annuità = €124k × [(1 − 1.035^(−14)) / 0.035] / 1.035 = €1.538M

**Costi (15 anni):**

| Voce | Valore |
|------|--------|
| Investimento iniziale (t=0) | €200,000 |
| Manutenzione annuale (PV) | €38,400 |
| **NPV Costi** | **€238,400** |

Manutenzione PV: €3k × [(1 − 1.035^(−15)) / 0.035] = €38.4k

**Analisi ACB:**

| Metrica | Valore |
|---|---|
| **NPV** | €1,657,621 − €238,400 = **€1,419,221** |
| **Benefit-Cost Ratio** | €1,657,621 / €238,400 = **6.95** |
| **Payback Period (semplice)** | €200,000 / €124,000 = **1.6 anni** |
| **IRR** | ~31% (ca. tasso interno) |

**Interpretazione:** 
- NPV fortemente positivo: VAN €1.42M su investimento €200k (leverage 7x)
- BCR 6.95 > 1: ogni euro speso produce €6.95 di benefici
- Payback < 2 anni: investimento recuperato rapidamente
- **Decisione: Approvare progetto PNRR (criterio costo-efficacia soddisfatto)**

---

## Caso 2: Calcolo IRPEF/IRES con Detrazioni (PMI a Regime Ordinario)

**Contesto:** Impresa individuale "Consulting Rossi" (regime ordinario), anno d'imposta 2024.

**Ricavi e costi:**

| Voce | Importo |
|---|---|
| **Ricavi da prestazioni professionali** | €80,000 |
| **Costi manuali e consulenti** | −€12,000 |
| **Affitto studio professionale** | −€6,000 |
| **Utensili/attrezzature (ammort.)** | −€2,500 |
| **Assicurazioni professionali** | −€1,200 |
| **IVA indetraibile (2%)** | −€1,600 |
| **EBITDA lordo** | €56,700 |
| **Contributi INPS volontari (stimato 20% su reddito netto)** | −€11,000 |
| **Reddito netto commerciale** | €45,700 |

**Calcolo imposta:**

**Metodo 1: Imposta lorda IRPEF**

1. **Reddito imponibile (base):** €45,700

2. **Imposta lorda scaglioni (2024):**
   - Scaglione 1 (0-15,000): 15,000 × 23% = €3,450
   - Scaglione 2 (15,000-28,000): 13,000 × 35% = €4,550
   - Scaglione 3 (28,000-45,700): 17,700 × 43% = €7,611
   - **Imposta lorda = €15,611**

3. **Detrazioni applicabili:**
   - Detrazione base lavoro autonomo (fino a 5,000): −€1,910 (su 45.7k)
   - Detrazione per redditi da lavoro autonomo: −€500 (base)
   - **Totale detrazioni = −€2,410**

4. **Imposta netta IRPEF:**
   - Imposta netta = €15,611 − €2,410 = **€13,201**

**Aliquota effettiva:**
- IRPEF % = €13,201 / €45,700 = **28.9%**

**Aggiunta: Addizionali regionali/comunali:**
- Addizionale regionale Lombardia: 1.73% × €45,700 = €791
- Addizionale municipale Milano: 0.80% × €45,700 = €366
- **Total addizionali = €1,157**

**Imposta totale lorda:**
- IRPEF + Addizionali = €13,201 + €1,157 = **€14,358**

**Aliquota effettiva complessiva:**
- €14,358 / €45,700 = **31.4%**

**Flusso di cassa (anno d'imposta 2024):**

| Voce | € |
|---|---|
| Ricavi netti IVA | €80,000 |
| − Costi deducibili | −€23,300 |
| − Contributi INPS | −€11,000 |
| − Imposte IRPEF + addiz. | −€14,358 |
| = **Reddito disponibile** | **€31,342** |

**Nota:** Se PMI avesse fruito di incentivi (credito imposta R&D, bonus ordinanza fiscale per autonomi, etc.), imposta si ridurrebbe.

---

## Caso 3: Transfer Pricing Arm's Length (Multinazionale TLC)

**Contesto:** Holding italiana "Global TLC SpA" fornisce servizi tech a filiale francese "Global TLC SARL". Necessario documentare arm's length price per transfer pricing.

**Servizi forniti (anno 2024):**
- Servizi di supporto tecnico (helpdesk, infrastructure management)
- Costi diretti sostenuti da Global TLC Italia: €300k
- Indirect costs allocation (R&D, management): €150k
- **Total cost base: €450k**

**Analisi comparable:**
- Commissioni ricarico per servizi tech cross-border (market benchmarks OECD):
  - Cost-plus method: markup 15-25% su costi full-loaded
  - Comparable service providers: markup medio 20%

**Determinazione transfer price arm's length:**

**Metodo Cost-Plus:**
- Cost base: €450k
- Markup (20%): €450k × 20% = €90k
- **Transfer price = €450k + €90k = €540k**

**Documentazione:**
- Analisi economica di 5 comparabili indipendenti
- Giustificazione della percentuale (complessità servizi, margine industry)
- Range arm's length: €450k − €565k (15-25% markup)
- **Prezzo negoziato: €540k (dentro range)**

**Impatto fiscale:**

| | Italia | Francia |
|---|---|---|
| **Ricavi** | €540k | — |
| **Costi** | −€450k | €540k |
| **Utile lordo** | €90k | — |
| **Imposte 24% (ITA) / 25.83% (FRA)** | €21.6k | — |

**Se non documentato / contestato:**
- Fisco italiano potrebbe contestare la transfer price
- Richiesta di correzione: es. se Agenzia ritiene arm's length €500k
- Maggiore tassazione: (€500k − €450k) × 24% = €12k di imposte aggiuntive
- Rischio doppia imposizione se Francia non accetta rettifica

**Strategie mitigazione:**
- Mantenere documentazione comparabile aggiornata
- Uso di metodi OECD accreditati (TNMM, CUP, cost-plus)
- Accordi APA (Advance Pricing Agreement) con Agenzia Entrate
- Assicurazione transfer pricing (se valore significativo)

---

## Caso 4: Calcolo Detrazioni Fiscali Strutturali (Efficientamento Energetico)

**Contesto:** Azienda manifatturiera "Prod Italia Srl" installa caldaia a condensazione (art. 16-bis TUIR, Ecobonus 65%).

**Investimento:** €30,000 (incl. manodopera)

**Calcolo detrazione 65% (quinquennale):**

1. **Importo detraibile:**
   - Spesa complessiva: €30,000
   - Detrazione 65%: €30,000 × 65% = €19,500

2. **Ripartizione quinquennale:**
   - Detrazione annuale: €19,500 / 5 = **€3,900/anno per 5 anni**

3. **Simulazione cassa (cash flow benefit):**

| Anno | Imposte lordo | Detrazione | Imposte netto | Risparmio |
|------|---|---|---|---|
| 2024 | €35,000 | €3,900 | €31,100 | €3,900 |
| 2025 | €40,000 | €3,900 | €36,100 | €3,900 |
| 2026 | €38,000 | €3,900 | €34,100 | €3,900 |
| 2027 | €42,000 | €3,900 | €38,100 | €3,900 |
| 2028 | €45,000 | €3,900 | €41,100 | €3,900 |

**PV del beneficio fiscale (WACC 5%):**
- PV = €3,900 × [(1 − 1.05^(−5)) / 0.05] = €3,900 × 4.329 = **€16,883**

**Impatto ROI investimento:**
- Costo netto (post-detrazione): €30,000 − €16,883 = €13,117
- Risparmi energetici annui (stimato): €2,500/anno
- Payback period: €13,117 / €2,500 = **5.2 anni**
- IRR (interno): ~8% (confrontare con WACC 5% → VAN positivo)

**Interpretazione:** Detrazione fiscale riduce effettivamente il costo dell'investimento di €16.9k. Unitamente ai risparmi energetici, il payback è sostenibile. Opportunità: estendere ecobonus a impianti fotovoltaici (bonus ulteriore) o rifacimento facciate (110%).

