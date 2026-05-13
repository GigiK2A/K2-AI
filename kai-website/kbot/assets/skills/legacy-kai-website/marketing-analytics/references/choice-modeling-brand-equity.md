# Consumer Choice Modeling e Brand Equity

## 3. Consumer Choice Modeling

### 3.1 Regressione Logistica
Per modellare scelte binarie (acquista/non acquista, sceglie marca A/marca B):

**P(Y=1) = 1 / (1 + e^(-(β₀ + β₁X₁ + ... + βₖXₖ)))**

**Interpretazione**:
- I coefficienti βᵢ indicano il log-odds ratio
- **Odds Ratio** = e^βᵢ = moltiplicatore della probabilità di scelta per un incremento unitario di Xᵢ
- OR > 1 → la variabile aumenta la probabilità; OR < 1 → la diminuisce

### 3.2 Multinomial Logit (MNL)
Estensione per scelte tra J alternative (es. scelta tra 5 marche):

**P(scelta j) = e^(Vⱼ) / Σₖ e^(Vₖ)**

Dove Vⱼ = β₁Xⱼ₁ + β₂Xⱼ₂ + ... è l'utilità deterministica dell'alternativa j.

**Proprietà IIA** (Independence of Irrelevant Alternatives): il rapporto delle probabilità tra due alternative è indipendente dalle altre alternative presenti. Limitazione: in realtà le marche spesso competono in modo asimmetrico.

### 3.3 Conjoint Analysis
Misura il valore (part-worth utility) di ciascun attributo del prodotto:
1. Definire attributi e livelli (es. marca: A/B/C; prezzo: 5€/8€/12€; dimensione: S/M/L)
2. Generare profili di prodotto (design fattoriale frazionario)
3. I rispondenti valutano/scelgono tra i profili
4. Stimare i part-worth utilities tramite regressione
5. Calcolare l'importanza relativa di ciascun attributo

**Importanza attributo i** = (max utility - min utility)ᵢ / Σⱼ (max utility - min utility)ⱼ

---

## 4. Brand Equity: Misurazione e Valutazione

### 4.1 Brand Asset Valuator (BAV) — Young & Rubicam
Misura il brand su 4 dimensioni (pillar):

1. **Differentiation** (differenziazione): quanto la marca è percepita come diversa
2. **Relevance** (rilevanza): quanto è appropriata/rilevante per il consumatore
3. **Esteem** (stima): quanto è rispettata e considerata di qualità
4. **Knowledge** (conoscenza): quanto è familiare e compresa

**Brand Strength** = Differentiation × Relevance (capacità di crescita futura)
**Brand Stature** = Esteem × Knowledge (forza attuale/passata)

**Power Grid** (matrice 2×2: Strength vs Stature):
- Alta Strength + Alta Stature → Brand leader (crescita + solidità)
- Alta Strength + Bassa Stature → Brand emergente (potenziale alto)
- Bassa Strength + Alta Stature → Brand in declino (erosione)
- Bassa Strength + Bassa Stature → Brand debole o nuovo

### 4.2 Metodo Interbrand (Valutazione Economica del Brand)
Stima il valore finanziario della marca in 3 step:

**Step 1 — Financial Analysis**: proiezione dei ricavi futuri attribuibili alla marca (brand earnings)

**Step 2 — Role of Brand Index**: percentuale dei ricavi attribuibile al brand (vs. altri driver come distribuzione, prezzo, R&D). Determinato tramite analisi dei driver d'acquisto.

**Step 3 — Brand Strength Score**: valutazione su 10 fattori (scala 0-100) che determina il tasso di sconto:
- Fattori interni: chiarezza, commitment, governance, responsiveness
- Fattori esterni: autenticità, rilevanza, differenziazione, consistenza, presenza, engagement

**Brand Value** = Brand Earnings × (Role of Brand %) / discount rate derivato dal Brand Strength

### 4.3 Customer-Based Brand Equity (Keller)
Piramide della brand equity:
1. **Identity** (salienza): awareness e riconoscimento
2. **Meaning** (significato): performance + imagery
3. **Response** (risposta): giudizi + sentimenti
4. **Relationships** (relazione): risonanza e lealtà

### 4.4 Brand Personality via Big Five (Pradeep/Appel/Sthanunathan)
From "AI for Marketing and Product Innovation" (Wiley 2019, Cap 12). Il framework associa ai brand 5 archetipi di personalità basati sul Big Five:

**5 Archetipi di Brand Personality**:
| Archetipo | Tratto Big Five | Brand Scales | Benefit Scales |
|-----------|----------------|--------------|----------------|
| Explorer | Openness | Innovativo, curioso, anticonvenzionale | Scoperta, novità, stimolazione |
| Director | Conscientiousness | Affidabile, efficiente, strutturato | Controllo, ordine, risultati |
| Connector | Extraversion | Energetico, sociale, espressivo | Appartenenza, divertimento, condivisione |
| Caregiver | Agreeableness | Premuroso, generoso, empatico | Sicurezza, comfort, cura |
| Sentinel | Neuroticism (inverse) | Stabile, calmo, rassicurante | Protezione, tranquillità, fiducia |

### 4.5 Brand Tracking AI-Driven (5 Step)
Processo sistematico per misurare la salute del brand nel tempo, integrando fonti tradizionali e AI:

**Step 1 — Define Brand Metrics**: selezione KPI chiave da monitorare:
- **Awareness**: spontanea (unaided) e sollecitata (aided)
- **Consideration**: percentuale del target che considera il brand tra le opzioni di acquisto
- **Preference**: quota di preferenza relativa ai competitor
- **Loyalty**: retention rate, repeat purchase, NPS
- **Advocacy**: % di clienti che raccomandano attivamente il brand (passaparola, referral)

**Step 2 — Continuous Data Collection**: tracking continuo e multi-fonte:
- Survey periodiche (brand tracker tradizionali) per metriche attitudinali
- Social media listening per sentiment e share of voice in tempo reale
- Search data (volume query brand, CPC) per intent e interesse
- Sales data per correlazione tra metriche di brand e performance di business

**Step 3 — AI Pattern Recognition**: algoritmi che identificano:
- Trend emergenti (accelerazione o decelerazione nelle metriche)
- Anomalie (calo improvviso di awareness, spike di sentiment negativo)
- Correlazioni cross-metriche (es. calo consideration → calo vendite con lag di 2 mesi)
- Attribuzione causale tra investimenti marketing e variazioni delle metriche brand

**Step 4 — Competitive Benchmarking**: posizionamento relativo sui 5 archetipi Big Five:
- Mappatura del profilo Big Five del proprio brand vs ogni competitor chiave
- Identificazione dei gap di personalità: dove il brand è più debole rispetto ai competitor
- Tracking dell'evoluzione competitiva nel tempo (chi sta crescendo su Openness? Chi sta perdendo Conscientiousness?)

**Step 5 — Action Triggers**: soglie automatiche che attivano interventi correttivi:
- Calo awareness > 5% → attivare campagna di brand awareness
- Sentiment negativo > 20% del volume social → crisi management protocol
- Gap di Openness vs competitor leader > 1.5 punti → investire in innovazione percepita
- Calo NPS > 10 punti QoQ → diagnosi urgente su customer experience

### 4.6 Brand Leadership Assessment
Correlazione tra tratti Big Five del brand e leadership di mercato. I brand leader tendono a:
- Score alto su Openness (innovazione percepita)
- Score alto su Conscientiousness (affidabilità)
- Bilanciamento tra Extraversion (visibilità) e Agreeableness (trust)

### 4.7 Celebrity Spokesperson Selection
Due metodi AI-driven per selezionare testimonial:
- **Exact Match**: il profilo Big Five della celebrity deve corrispondere esattamente al profilo del brand target
- **Compensatory Match**: la celebrity compensa le dimensioni deboli del brand (es. brand poco "Extravert" sceglie celebrity ad alta Extraversion)

### 4.8 M&A Brand Portfolio e Product Naming

**M&A Brand Portfolio Analysis**:
In operazioni di fusione/acquisizione, l'AI analizza il portafoglio brand combinato su due dimensioni:
- **Depth (profondità)**: numero di marchi nello stesso segmento di mercato — indica sovrapposizione e potenziale cannibalizzazione
- **Breadth (ampiezza)**: numero di marchi in segmenti diversi — indica diversificazione e copertura di mercato
- **Decisione strategica**: mantenere entrambi i brand (house of brands), fondere (branded house), o eliminare (razionalizzazione) — guidata da analisi di overlap nei profili Big Five e nel targeting

**Product Naming AI-Driven (5-Step Process)**:
1. **Define brand personality**: stabilire il profilo Big Five target del prodotto
2. **Generate candidate names**: AI genera centinaia di nomi candidati basati su associazioni semantiche, fonetiche e culturali
3. **Test associations**: ogni nome viene testato per le associazioni spontanee che evoca (positivo/negativo, coerenza con la categoria)
4. **Evaluate phonetic/semantic fit**: analisi della sonorità (suoni duri vs morbidi, vocali aperte vs chiuse), memorabilità, pronunciabilità cross-lingua, e significato in diverse lingue/culture
5. **Select**: selezione finale basata su fit complessivo con personalità brand + proteggibilità legale (trademark)

**30 Categorie di Product Naming**:
| Categoria | Descrizione | Esempio |
|-----------|-------------|---------|
| Descrittivo | Descrive la funzione | General Motors, PayPal |
| Evocativo | Evoca qualità/emozione senza descrivere | Nike (vittoria), Amazon (vastità) |
| Inventato | Parola completamente nuova | Kodak, Xerox, Häagen-Dazs |
| Acronimo | Lettere iniziali | IBM, BMW, IKEA |
| Metaforico | Metafora per qualità del prodotto | Apple (semplicità), Jaguar (velocità) |
| Fondatore/Persona | Nome del creatore | Ford, Dell, Ferrari |
| Geografico | Riferimento a un luogo | Patagonia, Amazon, North Face |
| Mitologico | Riferimento a miti/leggende | Nike, Oracle, Pandora |
| Composto | Fusione di due parole | Facebook, YouTube, Instagram |
| Onomatopeico | Suono che evoca l'esperienza | Zoom, Snap, Crunch |
| Alfanumerico | Mix lettere e numeri | 7-Eleven, 3M, WD-40 |
| Abbreviazione | Versione corta di un nome lungo | FedEx, Cisco |
| Latin/Greco | Radici classiche | Volvo (rotolo), Audi (ascolta) |
| Suffissato | Radice + suffisso tecnologico | Spotify (-ify), Shopify, Hulu |
| Prefissato | Prefisso evocativo + radice | Uber- (sopra), Mega-, Hyper- |
| Portmanteau | Blend di due parole | Pinterest (pin+interest), Groupon (group+coupon) |
| Animale | Nome di animale | Puma, Dove, Jaguar, Red Bull |
| Colore | Riferimento cromatico | Orange, Red Bull, Blackberry |
| Numerico | Solo numeri | 3M, 7UP, Channel No. 5 |
| Verbo/Azione | Verbo che indica azione | Sprint, Dash, Uber (Eat) |
| Aggettivo | Qualità come nome | Supreme, Epic, Absolute |
| Scientifico | Termine tecnico/scientifico | Qualcomm, Genomics |
| Culturale | Riferimento culturale specifico | Alibaba, Hulu (sacro cinese) |
| Sensoriale | Evoca un senso | Soft (Softbank), Smooth |
| Aspirazionale | Promessa di stato superiore | Aspire, Elevate, Ascend |
| Giocoso | Spelling alternativo, umorismo | Flickr, Tumblr, Reddit |
| Controintuitivo | Contrasto con la categoria | Apple per computer, Virgin per compagnia aerea |
| Narrativo | Racconta una micro-storia | StoryCorps, TripAdvisor |
| Minimalista | Ultra-corto, 1-3 lettere | Ox, Up, Go |
| Ibrido | Combinazione di 2+ categorie sopra | PlayStation (gioco+stazione), Snapchat (onomatopea+azione) |

La scelta della categoria di naming deve essere coerente con il profilo Big Five del brand: brand ad alta Openness preferiscono nomi inventati o controintuitivi; brand ad alta Conscientiousness preferiscono nomi descrittivi o scientifici.
