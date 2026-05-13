# Mascheramento: finto albero e camuffamento — RELSTA

Il mascheramento di un palo TLC (tipicamente richiesto da vincolo paesaggistico, richiesta del Comune o dell'Ordinario diocesano) modifica significativamente i **parametri aerodinamici** del calcolo statico. Questa scheda documenta le scelte da operare.

---

## Tipologie di mascheramento

### 1. Finto albero (fake tree)

**Descrizione:**
- Palo rivestito da **corteccia sintetica** (polietilene strutturato, vetroresina)
- **Chioma sintetica** in sommità con foglie in plastica → superficie esposta al vento molto maggiore del palo nudo
- Tipiche altezze chioma: 3-5 m (diametro chioma 4-6 m)

**Fornitori principali:**
- Natural Telecom, Larson Electronics, MobileLandscape
- Tipologie: pino, cipresso, palma — dipende dal contesto paesaggistico

### 2. Finto camino

**Descrizione:**
- Palo rivestito da **canna fumaria finta** (acciaio/alluminio sagomato)
- Posizionato sulla copertura di edificio, mimetizzato con camini esistenti
- Sezione tipicamente quadrata o rettangolare (1.0-1.5 m di lato)

### 3. Finta torretta in muratura

**Descrizione:**
- Palo racchiuso in una **struttura in muratura alleggerita** (pareti in cartongesso o prefabbricati)
- Contesto: centri storici, edifici monumentali
- Sezione tipicamente ottagonale o esagonale (2-3 m di lato)

### 4. Rivestimento cromatico

**Descrizione:**
- Solo **verniciatura camouflage** (colori mimetici) senza rivestimento fisico
- Non modifica i parametri aerodinamici
- Soluzione minimale quando richiesto solo adeguamento cromatico

---

## Impatti sul calcolo statico

### Impatto 1 — Coefficiente di forma c_p

**Senza mascheramento (palo cilindrico/poligonale):**
- c_p = 0.7 (valore standard CNR-DT 207/2008 per palo cilindrico snello)

**Con mascheramento finto albero:**
- **c_p = 1.0** (superficie piena, chioma = corpo tozzo)
- Incremento del 43% sulla pressione del vento

**Con finto camino quadro/rettangolare:**
- c_p = 1.2-1.4 (forma con spigoli vivi)
- Incremento del 71-100%

**Con torretta ottagonale/esagonale:**
- c_p = 0.9-1.0 (forma con spigoli smussati)

### Impatto 2 — Area esposta al vento

**Chioma finto albero:**
- A_chioma = superficie proiettata della corona fogliare
- **Valore forfait tipico:** 24 m² (per chioma H=4 m, diametro 5 m)
- Peso chioma: **200 kg/m² forfait** (copertura fogliare + struttura di sostegno)

**Camino finto:**
- A = lato × altezza camino (tipicamente 1.2 × 3 m = 3.6 m²)

**Torretta:**
- A = perimetro · altezza

### Impatto 3 — Peso proprio aggiuntivo

| Mascheramento | Peso forfait |
|---|---|
| Corteccia sintetica palo | 40-60 kg/m di altezza |
| Chioma finto albero | 200 kg/m² di proiezione chioma |
| Finto camino | 80-120 kg/m di altezza |
| Torretta in muratura | 500-800 kg/m² di parete |
| Torretta in cartongesso | 100-150 kg/m² di parete |

### Impatto 4 — Baricentro spostato in alto

La chioma del finto albero concentra peso alla sommità → **incremento del momento di base** anche in assenza di vento (per sisma e gravity).

**Verifica da fare:**
- Periodo fondamentale ridotto (massa concentrata in testa)
- Spettro sismico ricalcolato sul nuovo T₁

---

## Applicazione CNR-DT 207/2008 per mascheramento

**Caso 1 — Finto albero (esempio tipico)**

Sia H_palo = 25 m, Z_0 = 0.3 (categoria esposizione III), c_t = 1.0:
- q_r = 481 N/m² (Firenze, zona vento 2)
- c_e(25) = 2.21

**Palo nudo (c_p = 0.7):**
- p_palo = 481 · 2.21 · 0.7 = 745 N/m²

**Chioma finto albero (c_p = 1.0):**
- p_chioma = 481 · 2.21 · 1.0 = 1063 N/m²
- F_chioma = p_chioma · A_chioma = 1063 · 24 = 25.5 kN applicato a H_chioma

**Contributo al momento di base:**
- M_chioma = F_chioma · H_chioma ≈ 25.5 · 23 = 587 kN·m
- (questo è il **contributo dominante** per pali < 30 m con finto albero)

---

## Chek-list verifiche da fare in presenza di mascheramento

- [ ] Adottato c_p corretto per tipo di mascheramento (1.0 se finto albero, 1.2-1.4 se camino spigoli vivi)
- [ ] Calcolata A_chioma secondo geometria effettiva + forfait se dato mancante
- [ ] Aggiunto peso proprio mascheramento al modello FEM
- [ ] Verificato periodo fondamentale ricalcolato (nuovo T₁)
- [ ] Ricalcolata azione sismica su nuovo spettro
- [ ] Verificato baricentro massa spostato in alto
- [ ] Modellato ancoraggio chioma al palo (tipicamente staffe bullonate)
- [ ] Verificato finto camino/torretta NON trasmette carichi aggiuntivi al palo (struttura indipendente con giunti elastici) — altrimenti sì
- [ ] Previste ispezioni periodiche stato chioma (degrado materiale sintetico, rischio distacco)

---

## Parametri tipici finto albero (dataset K2A)

| Parametro | Valore tipico | Fonte |
|---|---|---|
| c_p chioma | **1.0** | CNR-DT 207 + prassi |
| A chioma | **24 m²** (forfait) | Cataloghi Natural Telecom |
| Peso chioma | **200 kg/m²** | Forfait di progetto |
| Altezza chioma | 3-5 m | Catalogo |
| Diametro chioma | 4-6 m | Catalogo |
| Altezza sopra ultimo ripiano tecnico | +2-3 m | Per coprire antenne |

---

## Prescrizione costruttiva mascheramento

**Da inserire in RELSTA:**
> "Il mascheramento a finto albero va montato successivamente alla verifica statica del palo con le antenne. La struttura di sostegno del fogliame deve essere staffata al palo con morsetti regolabili. Ispezione biennale obbligatoria con particolare attenzione a: stato cromatico (deterioramento UV), integrità fogliame (rottura strappi), stabilità ancoraggi staffe."

---

## Casi particolari

### Palo dissimulato in monumento/torre campanaria

Caso raro ma presente in Italia (vincolo monumentale + 5G su chiesa).
- Il palo è integrato nella muratura esistente → il calcolo statico include ANCHE la muratura come struttura portante
- Richiede skill `architetto-beni-monumentali` + relazione specialistica
- c_p non dominante (la muratura assorbe il vento)

### Palo a bandiera (wall mounted)

Caso RT in cui il palo è ancorato lateralmente al muro dell'edificio, sporgente a sbalzo di 1.5-3 m.
- Non è propriamente "mascheramento" ma altera la classificazione di palo
- c_p = 0.7 normale ma braccio di leva del momento maggiore
- Tipicamente verificato con modello FEM completo (palo + ancoraggi + muro).

---

*Il mascheramento a finto albero è il caso più ricorrente di camuffamento in siti TLC italiani (regola urbanistica dominante in contesti rurali). La corretta assunzione di c_p = 1.0 (invece di 0.7) è una delle scelte di progetto più critiche per il dimensionamento del palo.*
