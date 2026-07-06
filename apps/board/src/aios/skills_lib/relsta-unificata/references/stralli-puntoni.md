# Sistemi strallati e strutturati (stralli / puntoni / baggioli) — RELSTA

Sistemi di rinforzo/vincolo laterale del palo, applicati tipicamente su Roof Top (RT) o su pali snelli in Raw Land (RL) quando la sola mensola non è sufficiente.

---

## Sistema strallato

### Configurazione geometrica

**Tiranti disposti a 120° o 90°:**
- 3 stralli a 120° — configurazione ottima per isotropo
- 4 stralli a 90° — configurazione preferita quando esistono vincoli architettonici

**Punti di ancoraggio strallo:**
- **Alto:** morsetto o attacco saldato al palo, posizionato a **2/3 dell'altezza** tipicamente
- **Basso:** ancoraggio su copertura edificio (RT) o su plinto dedicato (RL)

**Angolo di inclinazione ottimale:**
- α ∈ [30°, 45°] rispetto all'orizzontale
- α > 45° → strallo poco efficace (braccio di leva ridotto)
- α < 30° → lunghezza strallo eccessiva + carichi orizzontali elevati sugli ancoraggi

### Componenti tirante

**Tipicamente TECI o similari (produttori italiani):**

| Diametro | Area [mm²] | Carico rottura T_Rk [kN] | Applicazione |
|---|---|---|---|
| Ø 16 mm | 191 | 355 | Pali piccoli H < 15 m |
| **Ø 18 mm** | **241** | **448** | **Tipico RT H 15-25 m** |
| Ø 22 mm | 358 | 666 | RT H > 25 m o carico alto |
| Ø 27 mm | 544 | 1012 | Pali monumentali o H > 40 m |

**Acciaio armonico** (trefoli di fili): f_uk = 1860 MPa, E = 205 GPa

### Pre-tiro obbligatorio

**Formula pretiro ottimale:**
- T_0 = 0.35 · T_Rk
  - Ø 18 → T_0 ≈ 155 kN
  - Ø 22 → T_0 ≈ 230 kN

**Messa in opera:**
- **Tensiometro elettronico a taratura certificata** (obbligatorio)
- Tensiometri tipici: Strainsert, KMT, Dynatest — precisione ±2%
- Certificato di taratura in corso di validità (max 12 mesi)
- Procedura di messa in opera sequenziale — serraggio a croce per bilanciare le deformazioni

**Prescrizione permanente in RELSTA:**
> "Il pretiro iniziale di T_0 kN deve essere verificato annualmente mediante tensiometro a taratura certificata. Eventuali scostamenti > 15% rispetto al valore nominale vanno riallineati."

### Verifica statica

**Combinazioni:**
- SLU: T_max = T_0 + ΔT_vento ≤ 0.5 · T_Rk (margine ampio obbligatorio)
- SLE (vento 100 km/h): T_max ≤ 0.7 · T_Rk

**ΔT_vento dal modello FEM:**
- Applicare vento SLU al palo con stralli già pretensionati
- Output: incremento di trazione ciascuno strallo
- Solitamente ΔT è 30-50% di T_0

**Verifica al "rilassamento":**
- Il vento da direzione opposta può **ridurre la tensione** dello strallo sottovento fino a 0 kN
- Se T = 0, lo strallo non collabora → palo diventa pura mensola → VERIFICARE ANCHE QUESTA CONFIGURAZIONE

### Ancoraggi strallo lato copertura

**Su copertura c.a.:**
- Tasselli chimici M20-M24 classe 10.9 inghisati nel cordolo perimetrale
- EOTA TR029 — verifica pullout + cono cls + splitting
- Profondità ancoraggio ≥ 15·φ (tipico 250-400 mm)
- Distanza dal bordo ≥ 100 mm (altrimenti ψ_re riduttivo)

**Su plinto cls (RL):**
- Plinto dedicato in c.a. (tipicamente 1.5×1.5×1.0 m)
- Piastra di ripartizione con barre piegate annegate in fase di getto
- Dimensionamento: verifica ribaltamento singolo plinto a trazione strallo

**Su muratura portante:**
- SCONSIGLIATO — muratura NON affidabile per carichi concentrati trazione
- Se obbligatorio, piastra di ripartizione a cavalcione del muro con barre passanti

### Esempio applicativo: LT032

- Palo RT su edificio in c.a.
- **Stralli Ø 18 mm × 3** a 120°
- Angolo inclinazione: 40°
- Pretiro iniziale: 155 kN ciascuno
- Ancoraggi: tasselli Hilti HIT-RE 500 M24 classe 10.9, profondità 300 mm
- Prescrizione: controllo pretiro annuale con tensiometro

---

## Sistema con puntoni

### Configurazione geometrica

**Tubi diagonali in compressione:**
- Collegano il palo a piani rigidi sottostanti (solaio c.a., parete portante)
- Disposti a triangolare → stabilizzazione in 2 piani ortogonali
- Tipicamente 4 puntoni ortogonali (o 3 a 120°)

**Materiali e sezioni:**
- **Ø 139.7 × 7.8 mm** tipico (I = 620 cm⁴, W = 88.7 cm³)
- Alternative: Ø 168.3 × 8.0 per carichi maggiori
- Acciaio S235 o S355 (S355 preferibile per vita utile e marginalità)
- Zincatura a caldo UNI EN ISO 1461

### Collegamenti di estremità

**Fork-bearing (cerniera sferica) alle estremità:**
- Permette il solo sforzo assiale nel puntone
- Evita flessione parassita da imperfezioni geometriche
- Tipico: fork-bearing M24-M36 in acciaio zincato

**Piastra di attacco al palo:**
- Saldata al palo o bullonata con cerchiaggio
- Cerniera sferica integrata

**Piastra di attacco al piano di appoggio:**
- Bullonata con ancoranti chimici (copertura c.a.)
- O saldata a struttura metallica esistente (shelter)

### Verifica statica

**Instabilità eulerina (dominante per puntoni snelli):**
- λ = L_cr / i = L · β / √(I/A)   con β=1.0 (cerniera-cerniera)
- λ̄ = λ / λ_1   con λ_1 = π·√(E/f_y) = 93.9 per S235, 76.4 per S355
- χ da curva buckling a (tubo laminato a caldo) o c (tubo saldato longitudinalmente)
- N_b,Rd = χ · A · f_yd / γ_M1

**Esempio Ø 139.7 × 7.8, L=8.5 m, S355:**
- A = 32.3 cm², I = 620 cm⁴, i = 4.38 cm
- λ = 850 / 4.38 ≈ 194
- λ̄ = 194 / 76.4 ≈ 2.54
- χ ≈ 0.15 (curva c)
- N_b,Rd ≈ 0.15 · 3230 · 355 / 1.05 ≈ 164 kN

### Combinazione stralli + puntoni

**Sistema ibrido (caso LT032):**
- Stralli per sollecitazione orizzontale principale (vento dominante)
- Puntoni per stabilità in direzione secondaria o per vincolo aggiuntivo a metà palo
- Vantaggio: ridondanza strutturale + riduzione snellezza

---

## Baggioli (piedini di ancoraggio RT)

### Descrizione

**Baggioli = elementi di ancoraggio metallici del palo sulla copertura:**
- Saldati al palo in corrispondenza della base
- Bullonati alla copertura con tirafondi chimici
- Funzione: trasferire il momento di base del palo alla copertura

**Geometria tipica:**
- Numero: 4 baggioli disposti a 90° (tipico)
- Lunghezza: 300-500 mm
- Spessore piastra: 15-25 mm
- Ogni baggiolo con 2-4 tirafondi M20-M24

### Verifica

**Verifica tirafondi:**
- Trazione T_tf = M_base / (n_baggioli · braccio) + N_palo / (n_baggioli · 4)
- Taglio V_tf = H_base / (n_baggioli · 4)
- Interazione combinata (EN 1993-1-8)

**Verifica baggiolo saldato al palo:**
- Saldature a cordone d'angolo, a = 6-10 mm
- τ_sald ≤ f_vw,d (EN 1993-1-8 Allegato B)

**Verifica solaio sotto baggiolo:**
- Tensione di contatto sulla soletta
- Eventualmente punzonamento se N concentrato
- Diffusione dei carichi fino alle travi portanti

### Rinforzo baggioli (se esistenti sottoresistenti)

Vedi sezione R6.c del catalogo rinforzi:
- Ringrosso baggiolo con getto integrativo cls + ancoranti
- Piastra di ripartizione saldata al baggiolo e inghisata chimicamente su area estesa
- Carotaggio copertura + collegamento a solaio sottostante

---

## Checklist verifica sistema stralli / puntoni / baggioli

- [ ] Configurazione geometrica (numero, angolo, diametri) documentata
- [ ] Verifica combinazione SLU con massima trazione/compressione strallo/puntone
- [ ] Verifica "scarico" stralli (vento da direzione che rilassa uno strallo) — palo come pura mensola
- [ ] Pretiro iniziale definito + valore numerico esplicito in RELSTA
- [ ] Prescrizione obbligatoria tensiometro certificato (per stralli)
- [ ] Verifica instabilità eulerina puntoni
- [ ] Verifica ancoraggi (ancoranti chimici, EOTA TR029)
- [ ] Controllo interferenza geometrica con impianti/antenne esistenti
- [ ] Programma manutenzione: annuale per stralli, biennale per puntoni

---

*Sistemi strallati/strutturati trasformano la tipologia statica del palo da "mensola pura" a "sistema multi-vincolato". Il modello FEM deve essere aggiornato di conseguenza: passare da calcolo analitico a solver multi-vincolo.*
