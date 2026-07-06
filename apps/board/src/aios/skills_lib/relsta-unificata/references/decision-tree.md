# RELSTA — Decision Tree Unificato

**Versione:** 1.0 — 22/04/2026
**Autore:** K2A Srls — Ing. Luca Rossi
**Fonti:** 9 RELSTA analizzate (Iliad/Cellnex/WindTre/Vodafone) + MASTER VERIFICA-PRT PALO FLANGIATO v10

Questo documento è la **sintesi comparata** di tutte le RELSTA acquisite come standard. Guida la skill unificata nella scelta delle sezioni da generare in funzione della tipologia di sito, palo, sistema strutturale, esito e intervento di rinforzo eventuale.

---

## 1. Architettura del decision tree

La redazione di una nuova RELSTA si articola su **11 rami decisionali indipendenti e combinabili**. Ogni ramo attiva template, formule e capitoli specifici. Il documento finale è il risultato della composizione dei capitoli selezionati dai diversi rami.

| # | Ramo | Domanda chiave | N° varianti | Sezioni impattate |
|---|---|---|---|---|
| 1 | **Tipologia sito** | RL o RT? | 2 + 4 sub-RT | Cap. 2, 6, 11 |
| 2 | **Tipologia palo** | Poligonale o tubolare flangiato? | 2 | Cap. 4, 5, 10 |
| 3 | **Pennone** | Presente / tipo | 3 | Cap. 4.5, 5.3 |
| 4 | **Mascheramento** | Presente / tipo | 3 | Cap. 5.1 (cp, A) |
| 5 | **Sistema strutturale** | Mensola / stralli / puntoni / misto | 5 | Cap. 6, 7 |
| 6 | **Fondazione** | Plinto diretto / con micropali / shelter zavorrato | 4 | Cap. 11 |
| 7 | **Intervento** | New site / upgrade / co-siting / innalzamento / rinforzo | 5 | Cap. 1, 3 |
| 8 | **Esito verifiche** | OK senza rinforzo / NV con rinforzo progettato | 2 | Cap. 10, 11, 12 |
| 9 | **Software** | Straus7 / PRO_SAP / WinStrand | 3 | Cap. 6.1 |
| 10 | **Livello conoscenza** | LC1/LC2/LC3 (FC=1.35/1.20/1.00) | 3 | Cap. 3, 4.3 |
| 11 | **Verifica fatica** | Presente (Woehler) / assente | 2 | Cap. 5.9.4, 10 |

---

## 2. Ramo 1 — Tipologia Sito

### 2.1 Raw Land (RL) — default
Palo fondato al suolo su plinto/platea di fondazione dedicato.
Dataset: 8/9 RELSTA (RM00189, LU55041, RM823, FI023/FI50137_802, SI53014, LI57027, PO008).

### 2.2 Roof Top (RT)
Struttura porta-antenne vincolata a elemento esistente di copertura/edificio.

**Sub-varianti RT (decisione obbligatoria):**
- **RT su pilastri in c.a.**: ancoraggi chimici/meccanici a testa pilastro → verificare bullonatura e pilastro a pressoflessione con nuove azioni orizzontali (Capitolo 12 dedicato).
- **RT su muratura portante**: ancoraggi passanti + piastre di ripartizione → verifica muratura a punzonamento + trazione ancoraggi chimici (HILTI/Fischer) + ribaltamento locale del muro.
- **RT su copertura c.a.**: piastre di base bullonate a soletta esistente → verifica soletta a flessione locale + ancoraggi in trazione.
- **RT su shelter metallico zavorrato** (caso LT032): palo montato su shelter esistente in carpenteria + zavorre c.a. accessorie per stralli → verifica shelter + verifica zavorre a ribaltamento/scorrimento.

**Sistemi di stabilizzazione aggiuntivi RT (decisione indipendente):**
- Con **stralli** (funi spiroidali pretese): LT032 — 4 stralli TECI Ø18mm, pretensione 1000 kg/strallo, verifica tensiometro oleostatico ogni 6 mesi (prescrizione obbligatoria).
- Con **puntoni** (tubolari a compressione): LT032 — 2 puntoni Ø139.7×7.8 L=8.5m ancorati a +11.2m, verifica instabilità euleriana.
- Con **baggioli-zavorra** (blocchi c.a. appesantimento): verifica ribaltamento per singolo baggiolo.
- Combinazioni: stralli+puntoni (LT032), solo stralli, solo puntoni, solo baggioli.

---

## 3. Ramo 2 — Tipologia Palo

### 3.1 Palo poligonale
Lamiera piegata a freddo saldata longitudinalmente di testa, giunti a innesto maschio-femmina (no flange intermedie di montaggio).
- **N. lati**: 16 nel 100% del dataset (7 casi).
- **N. tronchi**: 2–5 in funzione di altezza (24–37 m).
- **Acciaio**: S355JR zincato a caldo UNI EN ISO 1461.
- **Flange**: solo alla base (piastra circolare bullonata a tirafondi) e in sommità per collegare pennone (se presente).
- **Verifiche dedicate**: resistenza sezione tronco-conica, flangia base, tirafondi, **saldatura longitudinale (fatica classe 90)**, saldatura tubo-piastra (fatica classe 80).

### 3.2 Palo tubolare flangiato multi-tronco
Tronchi cilindrici o tronco-conici connessi tramite **flange circolari bullonate a ogni giunto** (non solo alla base).
- **N. tronchi**: 4–5 (LU55041: Ø762/Ø609.6/Ø558.8/Ø355; LT032: Ø159→Ø114.3).
- **Flange intermedie bullonate M27/M42 classe 8.8**.
- **Verifiche dedicate AGGIUNTIVE**: ogni flangia intermedia verificata con formula α-factor (polinomio 4° grado per δ<2.45, lineare per δ>2.45) e formula Quatordio per piastra senza nervature (kfs=0.45+0.12·ρ). **Nervature verificate a pressoflessione** (punto critico di NV frequente — vedi LU55041).

---

## 4. Ramo 3 — Pennone

### 4.1 Pennone dritto circolare (default)
Tubolare S275/S355, diametri tipici Ø193.7, Ø194, Ø219.1, Ø219.8, spessori 8–10 mm, altezza 3–6.5 m.
Flangia sommità palo: Ø600–700 mm, 12–18 bulloni M16 cl. 8.8.
Casi: RM00189, RM823, SI53014, LI57027.
**Verifiche**: sezione pennone a pressoflessione, flangia di connessione, bulloni a trazione+taglio (combinazione a = FV/FV,Rd + Ft/(1.4·Ft,Rd) ≤ 1).

### 4.2 Pennone inclinato portafari
Tipologia atipica su torri-faro di stadi (caso FI023/FI50137_802, ~4 m). **Geometria e caratteristiche spesso NON disponibili** dai documenti originari.
**Convenzione RELSTA**: dichiarare esplicitamente l'esclusione delle verifiche del pennone per mancanza dati, inserire prescrizione al gestore di fornire elaborati costruttivi.

### 4.3 Pennone assente
Il palo termina con la sommità del tronco più alto; antenne e parabole installate direttamente su staffe al tronco.
Casi: LU55041, PO008, LT032 (RT con stralli).
Saltare capitolo 4.5 "Verifica pennone".

---

## 5. Ramo 4 — Mascheramento

### 5.1 Nessun mascheramento (default)
**cp,palo = 0.7** (CNR-DT 207/2008), A proiettata = Ø·L tronco per tronco.
Casi: 8/9 RELSTA.

### 5.2 Finto albero (caso RM00189)
**cp,palo = 1.0** in luogo di 0.7 (Circ. 7/2019 per elementi con sagoma non standard).
**Chioma artificiale**: area esposta forfait 24 m² aggiuntiva al palo, applicata a quota baricentrica pennone/sommità. Peso proprio del mascheramento: ≈ 3–5 kN (da dichiarazione produttore o forfettario 200 kg/m² di chioma).
Verificare capitolo 5.1 "Azioni del vento" con sezione dedicata "Mascheramento a finto albero" e incremento A_vento.

### 5.3 Altro mascheramento (camino, antenna mimetica, ecc.)
Trattare caso per caso. Incremento area esposta e coefficiente cp da giustificare con normativa/documentazione fornitore.

---

## 6. Ramo 5 — Sistema Strutturale

| Schema | Casi | Analisi | Capitoli impattati |
|---|---|---|---|
| **Mensola pura** (default) | 8/9 | FEM beam con incastro alla base | 6.2, 6.3 |
| **Mensola + stralli** | teorico | FEM beam + elementi truss solo trazione, pretensione | 6.2, 6.4, 7.3 |
| **Mensola + puntoni** | teorico | FEM beam + elementi truss compressione, verifica instabilità EC3-1-1 | 6.2, 6.5, 7.4 |
| **Mensola + stralli + puntoni** | LT032 | FEM beam + truss misti, verifiche separate stralli/puntoni | 6.2, 6.4, 6.5, 7.3, 7.4 |
| **Mensola + baggioli-zavorra** | teorico | FEM beam + vincoli addizionali alla base, verifica ribaltamento baggiolo | 6.2, 6.6, 11.2 |

---

## 7. Ramo 6 — Fondazione

### 7.1 Plinto c.a. diretto (senza micropali) — default
Dimensioni tipiche: 4×4×1 m + dado 2×2×2 m (LI57027, FI023, SI53014), oppure soletta 5×6×1 + dado 2.5×2.5×2 (RM00189).
- **Materiali**: C20/25 o C25/30 (Rck 25–30), B450C.
- **Verifiche NTC 2018 § 6.4**: ribaltamento (Approccio 1, Combinazione 2), scorrimento, capacità portante (Brinch-Hansen/Vesic con fattori inclinazione), cedimenti SLE, fessurazione wk.
- **qamm terreno** da Relazione Geologica/Geotecnica di sito.

### 7.2 Plinto c.a. con micropali (caso LU55041)
Fondazione superficiale indiretta con pali di fondazione Ø220 mm L=8 m × 12 pali in acciaio+malta, disposti a corona sotto plinto. **Attivato quando plinto diretto NV** (LU55041 ante: coeff.ribaltamento 0.604 → post con micropali: 0.883).
- **Verifiche dedicate**: portanza laterale micropalo, attrito laterale, sfilamento, cedimenti differenziali del sistema.

### 7.3 Shelter metallico zavorrato (caso LT032, RT)
Shelter esistente in carpenteria metallica + zavorre c.a. per stralli. Palo bullonato a piastra superiore shelter.
- **Verifiche dedicate**: shelter a ribaltamento/scorrimento con peso complessivo + azione vento su palo; zavorre stralli singolarmente.

### 7.4 Ancoraggi chimici/meccanici (RT su c.a./muratura/pilastri)
Tasselli HILTI HIT-HY / Fischer FIS / Spit-Fix con resistenza ETA: trazione Ft,Rd + taglio FV,Rd.
- **Verifiche**: trazione per tirant estrattore, taglio combinato, cono di rottura calcestruzzo (EOTA TR029).

---

## 8. Ramo 7 — Intervento

### 8.1 New site (nessun caso nel dataset)
Palo di nuova installazione su fondazione nuova. RELSTA completa senza sezione "ante-operam".

### 8.2 Upgrade / modifica configurazione (RM00189, FI023, FI50137_802)
Modifica antennale su palo esistente, senza variazioni geometriche strutturali.
Tabella ante/post-operam obbligatoria con confronto sfruttamenti.

### 8.3 Co-siting (RM823, LI57027, SI53014)
Aggiunta di un nuovo gestore su palo esistente, tipicamente con sostituzione pennone o aggiunta antenne/parabole.
Sezione dedicata "Sostituzione pennone" se presente (caso LI57027: da h=3 m a h=6.5 m).

### 8.4 Innalzamento (caso RM823, citato come evento storico)
Aggiunta di un tronco in sommità al palo esistente. Richiede:
- Verifica tronco aggiunto come new install.
- Riverifica tronchi inferiori con incremento azioni.
- Riverifica fondazione con incremento momento ribaltante.
- Spesso innesco di rinforzo (vedi ramo 8).

### 8.5 Rinforzo strutturale (LU55041, PO008)
Vedi Ramo 8 per la tipologia.

---

## 9. Ramo 8 — Esito Verifiche (PIVOT)

Questo è il **ramo pivot** che determina se produrre la sola RELSTA o aggiungere il **Progetto di Rinforzo**.

### 9.1 OK senza rinforzi (8/9 casi)
Tutti gli sfruttamenti η ≤ 1.00 (iliad) o α = Rd/Ed ≥ 1.00 (Cellnex).
Documento finale: RELSTA standard con Cap. 10 "Sfruttamenti" e Cap. 12 "Asseverazione sicurezza statica".

### 9.2 NV → rinforzo progettato
Uno o più sfruttamenti > 1.00. Si aggiunge sezione dedicata "Progetto di rinforzo" con:

**9.2.1 Tipologia rinforzo: raddoppio nervature flangia intermedia (caso LU55041)**
Quando flangia intermedia NV per formula α (LU55041 ante: 132.7% e 121.0%).
- Aggiunta di n° nervature pari al numero esistente in posizione angolare sfasata 360°/(2n).
- Risultato atteso: sfruttamento post-rinforzo ≈ 50-70% (LU55041 post: 68.3% e 68.7%).
- Verifiche: flangia con 2n nervature, saldature nervature-flangia-fusto.

**9.2.2 Tipologia rinforzo: demolizione RL-POLE esistente + nuovo RR-POLE (caso PO008)**
Quando rinforzo preesistente NV + palo NV + fondazione NV (PO008: palo 128%, rinforzo 132%, fond 102%).
- Demolizione rinforzo esistente (RL-POLE) mediante taglio controllato.
- Posa nuovo rinforzo a manicotto tubolare RR-POLE fino a quota H_r (tipico 10 m).
- **Allargamento fondazione** su 2 lati con ampliamento laterale e cucitura armatura.
- Software: PRO_SAP con elementi shell per la camicia.

**9.2.3 Tipologia rinforzo: micropali di fondazione (caso LU55041)**
Quando fondazione NV a ribaltamento/portanza (LU55041 ante senza micropali: 0.604 → NV).
- N° 12 micropali Ø220 L=8 m in acciaio+malta, disposti a corona sotto plinto esistente.
- Cucitura micropali-plinto mediante armatura aggiuntiva.

**9.2.4 Tipologia rinforzo: sostituzione bulloneria (casi teorici)**
Quando piastra base/tirafondi/flange bullonate NV ma corpo strutturale OK.
- Sostituzione M16→M20, M20→M24, M27→M30 con aumento classe 8.8→10.9.

**9.2.5 Tipologia rinforzo: cerchiatura/camicia esterna (casi teorici)**
Quando sezione palo NV a resistenza.
- Camicia in acciaio S355 o FRP (fibre carbonio/vetro) con collegamento perfetto.

**9.2.6 Tipologia rinforzo: aggiunta stralli (caso teorico su RL)**
Quando palo snello NV a deformabilità o pressoflessione.
- Verifica geometrica tiranti + pretensione + ancoraggi a terra.

### 9.3 Matrice decisionale rinforzi

| NV riscontrato | Rinforzo tipico | Prerequisiti | Caso di riferimento |
|---|---|---|---|
| Flangia intermedia (α factor) | Raddoppio nervature | Flangia accessibile | LU55041 |
| Sezione palo | Camicia RR-POLE o FRP | Taglio controllato fattibile | PO008 |
| Rinforzo esistente NV | Demolizione + RR-POLE nuovo | Accessibilità base palo | PO008 |
| Fondazione ribaltamento | Allargamento + micropali | Spazio disponibile su almeno 2 lati | PO008 + LU55041 |
| Fondazione capacità portante | Micropali | Geologia compatibile | LU55041 |
| Piastra base | Sostituzione bulloneria + rinforzo nervature | Tirafondi esistenti recuperabili | teorico |
| Deformabilità eccessiva | Aggiunta stralli o puntoni | Spazio libero per tiranti | teorico |

---

## 10. Ramo 9 — Software di calcolo

| Software | Casi | Caratteristiche | Licenza |
|---|---|---|---|
| **Straus7 rel. 2.2.3** (G+D Computing / HSH Srl) | 5/9 | FEM beam 6 GdL/nodo, elasto-plastico | K2A attiva |
| **PRO_SAP** (2S.I. Software) | PO008 | FEM shell+beam, ideale per camicie/rinforzi | K2A attiva |
| **WinStrand** (ENEXSYS Srl) | RM823 | FEM beam, usato da gestore precedente | Progetto ereditato |

**Regola di scelta**: Straus7 default. PRO_SAP attivato per rinforzi con elementi shell (camicie, piastre rinforzo, raddoppio nervature complesso). WinStrand solo per continuità con progetti esistenti del gestore.

---

## 11. Ramo 10 — Livello di Conoscenza (LC/FC)

| LC | Requisiti documentali | FC | Casi nel dataset |
|---|---|---|---|
| **LC3** (accurata) | Disegni esecutivi originari + Relazione geologica + collaudo | 1.00 | Tutti i casi espliciti |
| **LC2** (adeguata) | Disegni esecutivi incompleti + rilievo strumentale | 1.20 | Da applicare se doc. carente |
| **LC1** (limitata) | Solo rilievo + stima materiali | 1.35 | Da applicare se assenza doc. |

**Impatto FC**: riduce le resistenze di calcolo (fyd,ridotta = fyd/FC). LC3 → nessuna riduzione.
**Tracciabilità**: dichiarare in Cap. 3 "Fonti e livello di documentazione" quali documenti sono stati visionati.

---

## 12. Ramo 11 — Verifica a fatica

### 12.1 Presente (default per pali snelli H > 25m o gestori che richiedono)
Eseguita secondo EN 1993-1-9 con:
- **Curve di Woehler** (S-N bilineari).
- **Dettagli critici**: saldatura longitudinale palo poligonale (**classe 90**), saldatura tubo-piastra base (**classe 80**).
- **Combinazione**: SLE Rara con cicli annuali da distribuzione Weibull del vento.
- **γM,fat = 1.35** (Conseguenze significative).
- **Metodo**: Palmgren-Miner D = Σ(ni/Ni) ≤ 1.00.
- **Output**: percentuali di sfruttamento a fatica + vita residua.

### 12.2 Assente (caso RM823, alcuni gestori)
Omessa quando:
- Palo tozzo H < 25 m.
- Gestore non la richiede esplicitamente (es. Wind Tre su sito RM823).
- Dichiarazione di non ricadenza nei requisiti della norma.

**Decisione automatica**: se H_totale ≥ 25 m **OR** presenti parabole MW ad alta quota **OR** gestore = Iliad/Cellnex **→ eseguire fatica**.

---

## 13. Gestori e peculiarità

| Gestore | Peculiarità normativa/documentale |
|---|---|
| **Iliad Italia** | Richiede Scheda Radio allegata, fatica sempre obbligatoria, template K2A v1.4 |
| **Cellnex Italia** | CNP_TS21_002 (verifica esistenti), capacity check α=Rd/Ed, scheda sintesi A4 |
| **Wind Tre** | Co-siting tipico su palo di altro gestore, fatica facoltativa |
| **Vodafone** | Proprietà palo spesso ereditata (co-siting Iliad su Vodafone) |
| **INWIT/Cellnex TowerCo** | Proprietaria infrastruttura, pre-configurazione standard |

**Regola co-siting**: produrre tabella ante/post-operam con confronto sfruttamenti per ogni gestore aggiunto. Chi firma la RELSTA è il tecnico incaricato dal **nuovo gestore** che entra; i gestori preesistenti sono trattati come configurazione di base.

---

## 14. Struttura finale del documento RELSTA

### 14.1 Sequenza capitoli (ordine fisso)
1. Premessa e oggetto
2. Inquadramento sito (RL/RT + sub-RT)
3. Fonti e livello di documentazione (LC/FC)
4. Descrizione strutturale (palo + pennone + mascheramento)
5. Azioni di calcolo (vento + sisma + ghiaccio + manutenzione + fatica se presente)
6. Modellazione (software + schema statico + vincoli)
7. Combinazioni di carico (SLU + SLE)
8. Risultati sollecitazioni (M, V, N)
9. Verifiche resistenza (palo, pennone, flange, piastra, tirafondi)
10. Verifiche fatica (se Ramo 11 attivo)
11. Verifiche fondazione (ribaltamento, scorrimento, portanza, cedimenti, fessurazione)
12. **Progetto di rinforzo** (solo se Ramo 8 = NV)
13. Tabella sfruttamenti ante/post-operam
14. Asseverazione sicurezza statica
15. Allegato A — Profili carico/reazione
16. Allegato B — Output FEM

### 14.2 Sezioni condizionali (attivate da rami)

| Sezione | Attivata da | Esempio |
|---|---|---|
| 2.2 Sottostruttura RT | Ramo 1 = RT | LT032 § descrizione shelter |
| 4.5 Pennone | Ramo 3 ≠ "assente" | SI53014 § flangia pennone |
| 5.1.bis Mascheramento | Ramo 4 ≠ "nessuno" | RM00189 § finto albero |
| 6.4 Stralli | Ramo 5 contiene stralli | LT032 § verifica funi |
| 6.5 Puntoni | Ramo 5 contiene puntoni | LT032 § instabilità tubolare |
| 10 Fatica | Ramo 11 = presente | Tutti tranne RM823 |
| 11.2 Micropali | Ramo 6 = con micropali | LU55041 § micropali Ø220 |
| 12 Progetto rinforzo | Ramo 8 = NV | LU55041 raddoppio / PO008 RR-POLE |
| 14.bis Prescrizione tensiometro | Ramo 5 contiene stralli | LT032 § manutenzione 6 mesi |

---

## 15. Riepilogo dataset di riferimento

| Codice | Sito | Tipologia | Palo | Pennone | Sistema | Fondazione | Intervento | Esito | Software | LC |
|---|---|---|---|---|---|---|---|---|---|---|
| RM00189 | RL | Poligonale 16L | 5 tronchi 29m | Ø194 dritto | Mensola | Platea+dado | Upgrade finto albero | OK | Straus7 | LC3 |
| LU55041 | RL | Flangiato 4T | 33m | assente | Mensola | Plinto+12 micropali Ø220 | Rinforzo raddoppio nervature | NV→OK post | Straus7 | LC3 |
| LT032 | **RT shelter** | Flangiato 5T | 23.5m | assente | **Stralli+puntoni** | Shelter zavorrato | Co-siting | OK | Straus7 | LC3 |
| PO008 | RL | Poligonale | h n.d. | n.d. | Mensola+RL-POLE→RR-POLE | Plinto allargato | **Rinforzo RR-POLE** | NV→OK post | **PRO_SAP** | LC3 |
| RM823 | RL | Poligonale 16L | 24+6m | Ø219.8 S275 | Mensola | Plinto 5×5×0.75 | Co-siting + innalzamento storico | OK | **WinStrand** | LC3 |
| FI023/FI50137_802 | RL torre-faro | Poligonale 16L | 37m+4m | **Inclinato portafari** | Mensola | Platea+dado | Upgrade co-siting | OK (tirafondi 98%) | Straus7 | LC3 |
| SI53014_003 | RL | Poligonale 16L | 2 tronchi 24m+3m | Ø193.7 S355 | Mensola | Plinto 4×4×2.5 | Prima config Iliad | OK | Straus7 | LC3 |
| LI57027_003 | RL | Poligonale 16L | 3 tronchi 30m | **Ø219.1 sostituito 3→6.5m** | Mensola | Plinto 4.2×4.2×1+dado | Co-siting + sost. pennone | OK | Straus7 | LC3 |

---

## 16. Gap/lacune del dataset da completare con norma

Il dataset copre 8 varianti su ~35 possibili combinazioni. Varianti **non presenti nel dataset** ma teoricamente richieste dall'utente:
- RT su pilastri in c.a. isolati.
- RT su muratura portante.
- RT su copertura c.a. piena.
- RL con solo stralli (senza puntoni).
- RL con solo puntoni.
- RL con baggioli-zavorra.
- Pali tralicciati (a 3 o 4 gambe).

**Per queste varianti**: la skill unificata utilizzerà i template normativi (EC3, EC7, NTC 2018, CNR-DT 207/2008) senza RELSTA di riferimento, segnalando all'utente che il caso non ha precedente nel portfolio K2A.

---

**Prossimo step**: costruzione della skill unificata `relsta-unificata` basata su questo decision tree.
