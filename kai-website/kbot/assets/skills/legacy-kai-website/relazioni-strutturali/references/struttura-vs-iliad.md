# Struttura Verifica Idoneità Statica iliad — Riferimento Completo

Fonte: **Linee Guida Verifiche di Idoneità Statica — Contenuti Minimi, iliad v1.4** (aggiornamento 06/2024, aggiunto fornitura pali e RL 4 settori)

---

## Normativa Obbligatoria (Cap. 2)

Elencare **tutte** le seguenti normative nel capitolo 2 della relazione:

- DM del 17.01.2018: Nuove norme tecniche per le costruzioni (NTC 2018)
- CNR 10022/84: Profilati d'acciaio formati a freddo – Istruzioni per l'impiego nelle costruzioni
- CNR 10012/85: Istruzioni per la valutazione delle azioni sulle costruzioni
- CNR 10011/88: Costruzioni in acciaio: istruzioni per il calcolo, l'esecuzione, il collaudo e la manutenzione
- Legge n° 1086 del 5.11.1971: Disciplina delle opere in conglomerato cementizio, normale e precompresso, ed a struttura metallica
- UNI EN ISO 1461/99: Rivestimenti di zincatura per immersione a caldo su prodotti finiti ferrosi ed articoli in acciaio
- Legge N° 64 del 02/02/1974: "Provvedimenti per le costruzioni con particolari prescrizioni per le zone sismiche"
- Circolare 11 febbraio 2019, n.7 Istruzioni per l'applicazione delle "Nuove norme tecniche per le costruzioni" di cui al D.M. 17 gennaio 2018
- DM 31/07/2012: Approvazione delle Appendici nazionali recanti i parametri tecnici per l'applicazione degli Eurocodici (G.U. n.73 del 27/03/2013)
- UNI EN 1990: Eurocodice 0 – Criteri Generali di progettazione strutturale
- UNI EN 1090-1: Esecuzione di struttura in acciaio e di alluminio – Parte 1: Requisiti per la valutazione di conformità dei componenti strutturali
- UNI EN 1090-2: Esecuzione di struttura in acciaio e di alluminio – Parte 2: Requisiti tecnici per strutture di acciaio
- UNI EN 1991-1-4: Eurocodice 1 – Azioni sulle strutture – Parte 1-4: Azioni in Generale – Azioni del vento
- UNI EN 1993-1-1: Eurocodice 3 – Progettazione delle strutture di acciaio – Parte 1-1: Regole generali e regole per gli edifici
- UNI EN 1993-1-3: Eurocodice 3 – Progettazione delle strutture in acciaio – Parte 1-3: Regole generali e supplementari per l'impiego dei profilati e delle lamiere sottili piegate a freddo
- UNI EN 1993-1-5: Eurocodice 3 – Progettazione delle strutture in acciaio – Parte 1-5: Elementi strutturali a lastra
- UNI EN 1993-1-6: Eurocodice 3 – Progettazione delle strutture in acciaio – Parte 1-6: Resistenza e stabilità delle strutture a guscio
- UNI EN 1993-1-8: Eurocodice 3 – Progettazione delle strutture in acciaio – Parte 1-8: Progettazione dei collegamenti
- UNI EN 1993-1-9: Eurocodice 3 – Progettazione delle strutture in acciaio – Parte 1-9: Fatica
- UNI EN 1993-3-1: Eurocodice 3 – Progettazione delle strutture per le strutture di acciaio – Parte 3-1: **Torri, pali e ciminiere – Torri e pali** ← fondamentale per pali TLC
- UNI EN 1998-1: Eurocodice 8 – Progettazione delle strutture per la resistenza sismica – Parte 1: Regole generali, azioni sismiche e regole per gli edifici

---

## Cap. 1 — Contenuto Minimo Descrizione Opera

**Per TUTTE le strutture:**
- Tipologia strutturale da specificare tra: palo flangiato, palo poligonale, roof-top, traliccio, strallato
- Proprietario della struttura: privato / Tower Company / pubblico
- Motivo per il quale si rende necessaria la verifica strutturale
- Schema riassuntivo caratteristiche geometriche principali: n. tronchi, n. lati, diametri, spessori, dimensioni bulloni

**Per strutture RoofTop aggiungere:**
- Schema strutturale dell'edificio ospite
- Particolare attenzione agli elementi strutturali dello stesso ai quali è collegata la struttura porta-antenne

**Appendice A — Documentazione fotografica stato di fatto:**
- Stato di conservazione della struttura
- Eventuali inghisaggi
- Stato di conservazione della malta di allettamento (per fondazioni)

---

## Cap. 3 — Documentazione Esistente

Per strutture non di nuova realizzazione indicare:
- Elenco dettagliato dei documenti esistenti della struttura (Verifiche statiche precedenti, RSU, collaudi, rilievi, ecc.)
- Per ogni documento: committente, professionista, data
- Se NON disponibile documentazione: determinare le indagini da eseguire per individuare le caratteristiche geometriche e dei materiali (caratterizzazione strutturale)

---

## Cap. 6 — Analisi dei Carichi

### 6.4 Azione del Vento (Cap. 3.3 NTC 2018)

Calcolare le azioni del vento secondo il Cap. 3.3 delle NTC 2018:

**Parametri da definire:**
- Zona di vento (1÷9 per l'Italia, da Tab. 3.3.I NTC 2018 in base al Comune)
- Velocità base di riferimento Vb,0 [m/s] e Vb [m/s]
- Pressione cinetica di riferimento qb [N/m²] = 0,5 × ρ × Vb² (con ρ = 1.25 kg/m³)
- Classe di rugosità del terreno e categoria di esposizione (da Tab. 3.3.II NTC 2018)
- Coefficienti: ce (esposizione), cd (dinamico), cp (forma/pressione)

**6.4.1 Carichi concentrati e distribuiti:**
- Carichi concentrati (antenne, apparati): Fw = qb × ce × cd × Cf × A
- Carichi distribuiti sul palo: pressione distribuita lungo l'asse del palo

### 6.5 Azione del Sisma

Valutare l'azione sismica per la posizione del sito:
- Zona sismica e parametri sismici (ag, F0, TC*) da spettro NTC 2018
- Categoria di sottosuolo (da relazione geotecnica)
- Per pali TLC: verifica se l'azione sismica è significativa rispetto al vento

---

## Cap. 10 — Tabelle Sintetiche Verifiche di Resistenza

**Formato obbligatorio tabella sfruttamenti:**

| Verifica | Sez./Elemento | Ed (azione) | Rd (resistenza) | Sfruttamento [%] | Esito |
|----------|--------------|:---:|:---:|:---:|:---:|
| Flessione sezione max | Tronco base | | | | OK/NO |
| Taglio | Tronco base | | | | OK/NO |
| Pressoflessione | Tronco base | | | | OK/NO |
| Instabilità (svergolamento) | Tronco | | | | OK/NO |
| Fatica saldature | Giunzioni | | | | OK/NO |
| Flangia di giunzione | Giunzione T1-T2 | | | | OK/NO |
| Bulloni flangia | Giunzione T1-T2 | | | | OK/NO |
| Piastra di base | Base | | | | OK/NO |
| Tirafondi/fondazione | Interfaccia | | | | OK/NO |
| Deformazione sommità | Sommità | | | | OK/NO |

> **REGOLA ILIAD**: Tutti gli sfruttamenti devono essere ≤ 80-85% (marginalità residua ≥ 15-20%).

---

## Cap. 11 — Strutture RawLand: Verifiche Fondazione

Contenuto specifico per fondazioni di strutture a terra:
- Verifica capacità portante (GEO): Nd ≤ Rd
- Verifica a scorrimento (GEO)
- Verifica ribaltamento (EQU)
- Verifica pressoflessione plinto (STR): taglio, flessione, punzonamento
- Verifica tirafondi (a trazione e pressoflessione nel cls)

---

## Cap. 12 — Strutture RoofTop: Verifica Ancoraggi

Contenuto specifico per strutture su copertura:
- Descrizione tipologia di ancoraggio (baggioli in cls, tasselli chimici, resine epossidiche)
- Caratteristiche meccaniche resine/tasselli (produttore, codice ETA, valori caratteristici)
- Verifica dei bulloni di ancoraggio baggiolo-struttura
- Verifica del baggiolo (tensioni nel cls, distanza dal bordo)
- Verifica dell'elemento di connessione baggiolo-copertura esistente
- Verifica resistenza solaio/copertura esistente ai carichi trasmessi

---

## Cap. 13 — Verifiche Elementi Non Strutturali

- Sbracci porta antenne (flessione, fatica)
- Connettori e giunzioni bullonate
- Saldature (verifica tensioni, classe di fatica EN 1993-1-9)
- Sistemi di serraggio antenne (se non certificati dal fornitore)

---

## Cap. 14 — Conclusioni e Giudizio di Idoneità

Il giudizio finale deve essere espresso in forma esplicita e inequivocabile:

**✅ IDONEO**
> "La struttura [descrizione] è idonea a sostenere i nuovi carichi [descrizione carichi iliad] con una marginalità minima del [X]% su tutte le verifiche. Non sono necessari interventi strutturali."

**⚠️ IDONEO CON PRESCRIZIONI**
> "La struttura è idonea alle seguenti condizioni: [prescrizioni]. Prescrizioni operative: [es. non installare ulteriori apparati, controllare bulloni ogni 12 mesi, ecc.]"

**❌ NON IDONEO**
> "La struttura non è idonea. Motivazione: [sfruttamento > 100% a causa di..., stato di conservazione insufficiente, ecc.]. Azioni richieste: [sostituzione / rinforzo / riduzione carichi]."

---

## Cap. 15 — Validazione dei Risultati (Cap. 10 NTC 2018)

Il Cap. 10 delle NTC 2018 richiede la validazione del modello di calcolo attraverso:
- Confronto con modello semplificato o calcolo manuale per almeno una verifica significativa
- Verifica della coerenza dei risultati con l'esperienza ingegneristica
- Per software certificati: indicare certificazione e codice versione

---

## Form VS.xlsm

Il file `Form VS.xlsm` nella cartella `03 - Opere Civili/03 - Verifiche Statiche/` è il formato standardizzato iliad per la presentazione delle verifiche statiche. Compilarlo in parallelo alla relazione testuale per garantire la leggibilità e la confrontabilità tra siti diversi.
