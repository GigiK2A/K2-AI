# Gestione dei Processi, Conoscenza e Decision-Making

**Fonte**: Management-Misani, Economia aziendale Bocconi  
**Settori applicativi**: Ottimizzazione operativa TLC, decisioni strategiche, break-even e pricing

---

## 1. Decisioni Manageriali: Modello dei 6 Step

Manager decide continuamente. Modello razionale:

1. **Riconoscere e definire situazione**: Identificare il problema, raccogliere dati
2. **Sviluppare opzioni**: Brainstorm alternative
3. **Analizzare opzioni**: Pro-contro, simulazioni, analisi costi-benefici
4. **Selezionare**: Scegliere best option
5. **Implementare**: Eseguire decisione, allocare risorse
6. **Monitorare conseguenze**: Verificare results, imparare

### Realtà: Bounded Rationality (Simon)

**Ipotesi** (neoclassica):
- Manager perfettamente razionale
- Massimizza utility/profitto
- Completa informazione
- Decisioni ottime

**Realtà** (comportamentale):
- Razionalità **limitata** (bounded): tempo, cognitione, info limitate
- Soddisfazione non massimizzazione: accetta la soluzione "abbastanza buona" (satisficing)
- Euristiche e bias (errori sistematici: anchoring, overconfidence, sunk cost fallacy)
- Contesto influenza decisione (framing effect)

**Implicazioni**: Manager decide rapidamente, non sempre in modo ottimale.

---

## 2. Gestione della Conoscenza e Apprendimento Organizzativo

### Knowledge Management (KM)

**Conoscenza Esplicita**: codificata, trasferibile (manuali, database, procedure)  
**Conoscenza Tacita**: implicita, difficile da trasmettere (skill, intuizioni, relazioni)

### Processi KM

**Creazione**:
- Learning-by-doing, R&D, acquisizione talenti
- Comunità di pratica (informal groups sharing expertise)

**Codificazione**:
- Manuali, procedure standard, best practices
- Knowledge base, wiki interne

**Condivisione**:
- Mentoring, job shadowing, riunioni
- Intraneti, piattaforme collaborative

**Applicazione**:
- Trasferimento knowledge ai nuovi progetti
- Improvement iterativo

### Apprendimento Organizzativo

**Single-Loop**: correggere azioni entro obiettivi fissi  
Es. "Il processo X costa 10€, come ridurlo a 8€?"

**Double-Loop**: interrogare gli obiettivi stessi  
Es. "Il processo X è ancora rilevante, o dovremmo cambiar modello di business?"

**Triple-Loop**: imparare a imparare, trasformare il modo in cui l'organizzazione apprende

### Ostacoli a KM

- Silos funzionali (R&D non parla con Operations)
- Competizione interna (scoraggia sharing)
- Turnover (knowledge walk out con l'impiegato)
- Mancanza di tempo e risorse formali
- Cultura non-collaborative

**Mitigation**: Incentivi su collaboration, time budget per knowledge transfer, community celebration.

---

## 3. Break-Even Point e Operating Leverage

### Concetti Base

**Revenue** (TR) = Prezzo (P) × Quantità (Q)  
**Total Costs** (TC) = Total Variable Costs (TVC) + Total Fixed Costs (TFC)  
**TVC** = Variable Cost per Unit (VC) × Q  
**Operating Income** (π) = TR - TC = (P × Q) - (VC × Q) - TFC = (P - VC) × Q - TFC

### Break-Even Point (BEP)

Quantità dove **π = 0**, ossia TR = TC.

**Formula**:
```
BEP = TFC / (P - VC)
```

Dove (P - VC) = **Contribution Margin** (margine di contribuzione per unità)

**Interpretazione**: BEP è il volume minimo da vendere per coprire i costi fissi. Al di sotto, perdita; al di sopra, profitto.

### Operating Leverage

**Concetto**: Se azienda ha alta % di costi fissi rispetto a variabili, piccoli cambi in volumi hanno grandi impatti su profitti.

**Operating Elasticity**:
```
Operating Elasticity = (TVC / BEP) / ITFC
```

- **Elevato**: rischio operativo alto ma profitti amplificati (poco volume supplementare = grandi guadagni)
- **Basso**: rischio operativo basso ma profitti piccoli anche con volumi elevati

**Esempio TLC**:
- Infrastruttura 5G: TFC altissimo (datacenter, antenne, spectrum). Poco VC (traffico dati marginale). Elevato leverage.
- MVNO (mobile virtual): bassa TFC (non possiede infra), acquista wholesale. Basso leverage, margini contenuti.

---

## 4. Economie di Scala e Costi

### Economie di Scala (EoS)

**Concetto**: Costo per unità scende al crescere del volume.

**Fonti**:
- **Fixed-cost absorption**: ammortizzare investimenti su più unità (es. impianto produttivo)
- **Specializzazione lavoro**: grandi fabbriche hanno operai più esperti
- **Geometric efficiency**: container cost ∝ surface (x²), capacity ∝ volume (x³)
- **Market power**: acquisti in bulk, prezzi migliori da supplier

**Diseconomie di Scala**: oltre certi volumi, costi salgono (difficoltà coordinamento, diminuzione qualità, crescita overhead)

### Economie di Apprendimento (Learning Curve)

**Concetto**: Costo per unità scende con esperienza cumulativa prodotto.

**Fonte**: skill aumentano, procedure si semplifică, sfridi diminuiscono, coordinamento migliora.

**Curva tipica**: 80% experience curve = ogni raddoppio volumen cumulato → costo scende a 80% del precedente.

**Implicazione strategica**: 
- Penetrazione rapida di prezzo (aggressive pricing) → volumi alti → costi scendono velocemente
- Profitti futuri da learning dominano perdite presenti

---

## 5. Costi Variabili, Fissi, Strutturali

### Costi Variabili (VC)

Cambiano direttamente con volume:
- Materie prime
- Lavoro diretto (piecework)
- Packaging
- Commissioni venditori

**Formula**: TVC = VC per unità × Q

### Costi Fissi (FC)

Indipendenti da volume (entro capacità):
- Depreciation impianti
- Affitti uffici
- Stipendi management
- R&D, marketing generale
- Assicurazioni

**Caratteristica**: Esistono anche con Q=0.

### Costi Strutturali

**Costi semi-fissi**: Saltano a livelli discreti (es. assumi un nuovo shift worker ogni 500 unità).

**Utilizzo della capacità**: EoS dipendono da quanta capacità usi.

---

## 6. Make-or-Buy Decision: Analisi Quantitativa

### Scenario: Produrre Internamente vs Comprare da Fornitore

**Dati Tipici**:
- Q = 10,000 unità/anno
- **Make (interno)**:
  - TFC = €500,000 (impianto, setup)
  - VC per unità = €6/u
  - Total Cost Make = 500k + (6 × 10k) = €560,000
- **Buy (esterno)**:
  - Prezzo per unità = €12/u
  - Total Cost Buy = 12 × 10k = €120,000

**Decisione**: Comprare è più conveniente (€120k < €560k).

**Ma se volume sale a 50,000 u/anno**:
- Make: 500k + (6 × 50k) = €800,000
- Buy: 12 × 50k = €600,000
- Ancora meglio comprare.

**Però se volume sale a 100,000 u/anno**:
- Make: 500k + (6 × 100k) = €1,100,000
- Buy: 12 × 100k = €1,200,000
- **Make diventa conveniente!**

**Punto di indifferenza (BEP make-or-buy)**:
```
500k + 6Q = 12Q
500k = 6Q
Q = 83,333 u/anno
```

**Considerazioni aggiuntive**:
- Asset specificity (impianto usabile solo per questo prodotto? = rischio)
- Qualità (controllo interno vs dipendenza fornitori)
- Flessibilità (se volumi scendono, impianto è sunk cost)
- Strategic fit (conoscenza core vs commoditized)

---

## 7. Vertical Integration e Governance

### Backward Integration
- Acquisire fornitori (es. olio company acquista raffineria)
- ✓ Controllo sulla qualità, riduzione costi (eliminare margine fornitore)
- ✗ Sunk cost, perdita flessibilità, aumento complessità

### Forward Integration
- Acquisire distributori/retailer (es. manufacturer apre outlet)
- ✓ Controllo su prezzo finale, margini distributor
- ✗ Sunk cost, conflitto con retailer indipendenti

### Strategic Alliances
- Compromise tra integrazione totale (high sunk cost) e market arms-length (bassa sinergia)
- Long-term contracts, JV, equity stakes

---

## 8. Applicazioni a TLC: Break-Even, Leverage, Make-or-Buy

### 5G Rollout: Elevato Operating Leverage

**Dati**:
- Investimento spectrum + infrastruttura: €2 miliardi (TFC)
- Costo margine traffico dati 5G: €0.002 per GB
- Prezzo medio data plan: €30/mese

**Break-Even**:
BEP = 2 mld / (30 - 0.002) ≈ 67 milioni clienti attivi/mese

**Implicazioni**:
- Elevato leverage: una volta superato BEP, profitti esplodono
- Rischio: se non raggiungi BEP (es. cannibalizzazione 4G), losses massicce
- Strategia: aggressive marketing, international roaming, B2B enterprise 5G (IoT, manufacturing)

### Network Sharing: Make-or-Buy in Infrastruttura

**Make (Build tower independently, e.g., TIM Towers)**:
- TFC: €50k per site (tower build, land, equipment)
- VC: €1k/anno per site (maintenance, power, rent)
- 10,000 sites totali = €50m + €10m/anno

**Buy (Tower Lease from Cellnex)**:
- Prezzo: €5k/anno per site
- 10,000 sites = €50m/anno

**Make-or-Buy**:
- Year 1: Buy è costoso (€50m vs €60m make)
- Year 5: Make conviene (€60m + €50m = €110m make vs €250m buy)

**Ma**: Asset-specific risk (se esci dal business, tower è sunk cost). Compromesso: network sharing con competitor (es. Vodafone + TIM towers condivise).

### MVNO vs Integrazione Verticale

**MVNO** (es. Iliad initial):
- No TFC infra (affittano rete Vodafone)
- VC: wholesale price €0.20/GB
- Prezzo al consumer: €5/GB
- Margine: elevato %, volume basso

**Vertical Integration** (es. TIM, Vodafone):
- TFC infra: altissimo
- VC: basso (marginal cost data è quasi 0)
- Prezzo al consumer: €5/GB
- Margine: basso %, ma volumi giganteschi

**Decisione**:
- MVNO se: non hai capitale, vuoi test market, mercato piccolo
- Vertically integrato se: committed, grandi volumi attesi, want control

---

## 9. Applicazioni a Negoziazione Contratti

### Analisi Costi TLC Grossista vs Retail

**Scenario**: Cliente B2B ti chiede sconto su connectivity.

**Calcolo**:
- Prezzo standard: €100/Mbps
- TFC customer (setup, provisioning): €5,000
- VC per Mbps: €30
- Volume cliente: 100 Mbps per 12 mesi

**Cost to Serve** = €5,000 + (€30 × 100 × 12) = €5,000 + €36,000 = €41,000/anno

**Margine minimo**: €41,000 / 100 Mbps = €410/Mbps annuale, ossia €34/Mbps mensile

**Implicazione**: Non puoi scendere sotto €34/Mbps (o altro scenario è unprofitable).

### Decision-Making: Quale Investimento Scegliere?

**Scenario**: Investire in 4G o 5G spectrum?

**4G**:
- Investimento: €500m
- Previsto revenue 10 anni: €1.5b
- NPV (Net Present Value) @10%: ≈ €420m

**5G**:
- Investimento: €1.2b
- Previsto revenue 10 anni: €3b (assunzione incerta, tech risk)
- NPV @10%: ≈ €800m

**Decisione**: 5G ha NPV superiore, ma rischio maggiore (technology unproven, demand uncertainty).

**Analisi**:
- Sensitivity: se revenue 5G scende del 20%, NPV = €500m (ancora > 4G)
- Breakeven: quanta revenue hai bisogno? Può il mercato assorbirla?
- Strategic option: 4G è "safe", 5G è "growth" → mix portafoglio

---

## 10. Checklist Decision-Making Manageriale

- [ ] Ho definito chiaramente il problema?
- [ ] Ho generato almeno 3 alternative?
- [ ] Ho analizzato pro-contro oggettivi (costi, rischi)?
- [ ] Ho considerato bounded rationality (tempo, info limitate)?
- [ ] Ho consultato stakeholder rilevanti?
- [ ] Ho quantificato break-even, operating leverage, sunk costs?
- [ ] Ho valutato opzioni strategiche (growth, risk, flexibility)?
- [ ] Ho pianificato monitoraggio e learning dalla decisione?
- [ ] Ho comunicato chiaramente il razionale?

---

## Riferimenti Canonici

- **Simon** (1955, 1972): Bounded Rationality, Administrative Behavior
- **Williamson** (1975, 1985): Transaction Cost Economics, make-or-buy
- **Chandler** (1962): Strategy and Structure
- **BCG** (1968): Experience Curve, Learning Effect
- **Porter** (1980, 1985): Generic Strategies, Value Chain
- **Grant & Nippa** (2006): Strategic Management
- **Kahneman & Tversky** (1979): Prospect Theory, behavioral economics
