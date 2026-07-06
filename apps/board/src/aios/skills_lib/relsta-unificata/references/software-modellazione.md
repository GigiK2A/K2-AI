# Software di modellazione FEM — RELSTA palo porta-antenne TLC

Nel dataset RELSTA K2A ricorrono 3 famiglie di software strutturali. Questa scheda documenta le specificità di ciascuno per la redazione di una RELSTA replicabile.

---

## Software 1 — Straus7 (HSH-G+D Computing)

**Versione ricorrente dataset:** **Straus7 rel. 2.2.3**

**Produttore:** G+D Computing (Australia) distribuito in Italia da HSH Srl.

**Impiego tipico:**
- Modellazione FEM completa di pali, strutture metalliche, porta-antenne
- Analisi lineare statica + modale + spettrale
- Analisi di buckling (P-Δ)
- Preferito da studi professionali medio-grandi

### Setup consigliato per palo TLC

**Tipo di elementi:**
- Beam elements (elementi trave) per il palo (1D)
- Plate/shell elements (per analisi locali piastre) se richiesto
- Point mass elements per antenne (massa concentrata)

**Modellazione palo tubolare:**
```
Property → Beam → Cross-section: Circular Hollow Section (CHS)
- Diametro esterno: D_ex (tronco per tronco)
- Spessore: t (tronco per tronco)
- Modulo elastico E = 210000 MPa (acciaio S355/S275)
- Densità ρ = 7850 kg/m³
```

**Modellazione flange/giunti:**
- Rigid links (legami cinematici rigidi) per simulare giunzione flangiata
- OPPURE gap element se si vuole simulare apertura flangia (non tipico per RELSTA)

**Vincoli alla base:**
- Incastro (6 gradi di libertà bloccati) per pali RL su plinto
- Molla rotazionale equivalente per pali RT su pilastro c.a.
- Cerniera per pali RT su muratura

**Carichi:**
- Peso proprio → Body Force automatico (g = 9.81 m/s²)
- Antenne → masse concentrate su nodi (F_x, F_y da vento)
- Vento distribuito sul palo → load patch lineare (intensità variabile con z)
- Sisma → spettro di risposta importato (spectral response)

### Vantaggi/limiti

**Vantaggi:**
- Modellazione robusta, validazione rigorosa (software datato ma stabile)
- Interfaccia con CAD (importa IFC, DWG)
- Ottima post-processazione (diagrammi sollecitazioni, tabelle tensioni)

**Limiti:**
- Interfaccia utente datata (anni 2000)
- Report in ASCII (necessita post-elaborazione per PDF)
- Licenza costosa (licenze multi-utente studio)

### Pattern ricorrenti in RELSTA Straus7

- Report ASCII auto-generato include: "Element Forces", "Node Displacements", "Base Reactions"
- I valori dei Δσ per fatica vanno estratti manualmente
- Coordinamento flangia-piastra-tirafondi richiede **post-processing Excel** (non integrato nel solver)

**Esempi dataset K2A:** FI023, FI50137_802, LU55041_002 (probabile)

---

## Software 2 — PRO_SAP (2S.I. Software)

**Produttore:** 2S.I. Software Srl (Italia)

**Versioni ricorrenti:** PRO_SAP 23, PRO_SAP SUPER 24

**Impiego tipico:**
- Progettazione strutturale integrata (c.a., acciaio, muratura, legno)
- Verifiche automatiche NTC 2018 + Circolare 7/2019
- Interfaccia CAD integrata (disegno strutturale)
- Preferito da studi italiani di progettazione architettonica/strutturale

### Setup consigliato per palo TLC

**Moduli richiesti:**
- PRO_SAP Struttura (ossatura palo)
- PRO_SAP Acciaio (verifiche EN 1993)
- PRO_SAP Sisma (analisi spettrale)
- PRO_SAP Geotecnica (verifiche fondazione)

**Modellazione:**
- Aste (beam) per il palo (sezione CHS)
- Nodi cerniere/incastri secondo schema statico
- Antenne: masse puntuali con SEV impostata come input
- Vento: automatico da coordinate geografiche + zona CNR-DT 207
- Sisma: automatico da coordinate + classe d'uso

### Verifiche automatiche integrate

**PRO_SAP esegue automaticamente:**
- Verifica membrature acciaio (EN 1993-1-1) — flessione, compressione, stabilità
- Verifica giunti (flange bullonate, piastra base) — limitato, spesso da completare manualmente
- Verifica fondazione (portanza, ribaltamento, scorrimento)
- Spettro di risposta e analisi modale

**Output automatico:**
- Report in formato ODT/DOCX (esportabile)
- Tabelle tensioni per ogni elemento
- Schemi grafici sollecitazioni

### Vantaggi/limiti

**Vantaggi:**
- Integrazione nativa NTC 2018 + Circ. 7/2019 (no adattamenti manuali)
- Report DOCX quasi pronto da inserire in RELSTA
- Buon rapporto prezzo/prestazioni
- Community italiana attiva (forum, webinar)

**Limiti:**
- Verifiche giunti non sempre esaustive (flangia α-factor da calcolare manualmente)
- Analisi di fatica NON integrata (da fare con calcoli separati)
- P-Δ analysis limitata alle versioni superiori

### Pattern ricorrenti in RELSTA PRO_SAP

- I capitoli sono generati direttamente dal software (layout standard)
- Le verifiche fatica, α-factor flangia e rinforzi sono sempre sezioni MANUALI
- Output grafici ben integrati

**Esempi dataset K2A:** LT032, RM00189_012_Rev1, SI53014_003, RM823 (probabile)

---

## Software 3 — WinStrand (ENEXSYS Srl)

**Produttore:** ENEXSYS Srl (Italia)

**Impiego tipico:**
- Software di nicchia, specializzato in strutture reticolari/pali
- Interfaccia testuale input (file .dat) con post-processing grafico
- Preferito da studi specialistici storicamente dedicati a TLC (produttori di pali)

### Specificità WinStrand

**Modellazione:**
- Input via file testuale (formato .DAT proprietario)
- Sintassi:
```
* NODO x y z
N 1  0.0  0.0  0.0
N 2  0.0  0.0  5.0
...
* ELEMENTO n1 n2 SECT
E 1 2 CHS500x8
...
* CARICO
L 10  0.0 -100.0 0.0
...
```

**Caratteristica unica:**
- **Templete proprietari per strutture porta-antenne** pre-costruiti (WinStrand salva template ricorrenti)
- **Database integrato antenne** (SEV, peso, orientamento automatico)
- **Combinazioni di carico RELSTA-specifiche** (ante/post, co-siting) automatizzate

### Vantaggi/limiti

**Vantaggi:**
- Velocità di modellazione per siti TLC (template pronti)
- Database antenne aggiornato
- Combinazioni di carico "smart" per RELSTA

**Limiti:**
- Interfaccia non moderna
- Community piccola
- Non adatto a strutture miste (solo pali/reticoli)
- **Ereditarietà dei template:** se un template è sbagliato alla fonte (es. bug in bulloni flangia), tutti i report successivi eredidano l'errore → CRITICO

### Pattern ricorrenti in RELSTA WinStrand

- Report include "Template ID" in testa (da cui deriva il modello)
- La sezione α-factor flangia usa formula parametrica embedded (non sempre aggiornata)
- La nota di "Ereditarietà WinStrand" va inclusa obbligatoriamente:

> "La verifica è stata condotta utilizzando WinStrand (ENEXSYS Srl, template standard TLC porta-antenne). Il template è stato verificato e adattato al sito specifico. Eventuali discrepanze fra parametri calcolati e valori di template sono state controllate manualmente."

**Esempi dataset K2A:** RM00189_012_Rev1 (probabile), varie

---

## Confronto operativo fra i 3 software

| Aspetto | Straus7 | PRO_SAP | WinStrand |
|---|---|---|---|
| Velocità modellazione | Media | Alta | Molto alta (template) |
| Integrazione NTC 2018 | Manuale | Automatica | Semi-automatica |
| Verifiche fatica | Manuale esterna | Manuale esterna | Manuale esterna |
| Report DOCX integrato | No | Sì | No |
| Fatturato licenza/anno | Alto | Medio | Medio |
| Adatto a RT complesse | Sì | Sì | Limitato |
| Adatto a rinforzi | Sì | Sì | Limitato |
| Community/support | Internazionale | Italiano | Italiano specialistico |

---

## Scelta del software per il nostro sistema

**Raccomandazione K2A:**
- **Default software di calcolo: PRO_SAP** (integrazione nativa NTC, report DOCX, fatturato medio)
- **Alternativa per casi complessi: Straus7** (modellazione più fine per RT multi-variante o rinforzi)
- **WinStrand SCONSIGLIATO** per nuove RELSTA (ereditarietà template a rischio)

**Nota:** Il nostro sistema Claude può emettere calcoli analitici completi SENZA un solver esterno dedicato, ma i risultati FEM detti "numerici" richiedono comunque verifica con uno dei tre software (tipicamente in studio committente).

**Output atteso dal sistema Claude:**
- Formule, numeri, prescrizioni, ragionamento ingegneristico completo
- Input file pronto per PRO_SAP o Straus7 (da importare nel software del professionista)
- Report RELSTA completo

---

## Prescrizioni in RELSTA sul software usato

**Nota obbligatoria in capitolo "Metodologia di calcolo":**

> "Il modello strutturale è stato realizzato con il software [NOME_SOFTWARE], versione [VERSIONE]. Il software è certificato per l'uso in progettazione strutturale secondo NTC 2018. La validazione del modello è stata condotta attraverso [DESCRIZIONE_VALIDAZIONE: esempio 'confronto fra analisi analitica semplificata e risultati FEM, con scostamento < 5%']."

Questa nota è richiesta per conformità al DM 2018 §2.7 "Verifica e validazione del software".

---

*La scelta del software impatta principalmente sulla velocità di produzione della RELSTA, non sulla validità dei risultati. Tutti e tre i software sono adeguati se usati correttamente. La competenza del professionista resta il fattore dominante.*
