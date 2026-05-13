# Catalogo rinforzi — RELSTA palo porta-antenne TLC

Quando la verifica SLU/SLE del palo esistente **non è soddisfatta** (η > 1.00 iliad / α < 1.00 Cellnex), è necessario progettare un **rinforzo strutturale** e produrre una RELSTA integrata con il progetto di rinforzo.

Questo catalogo raccoglie le 6 tipologie ricorrenti osservate nel dataset RELSTA K2A e le relative formule/procedure.

---

## Decisione: quale rinforzo scegliere?

| Criticità rilevata | Tipologia rinforzo consigliata |
|---|---|
| Tronco superiore/intermedio sottoresistente a flessione | **R1 Fasciatura in c.a. + tubo di ringrosso** |
| Base piastra non nervata sottoresistente | **R2 Nervature radiali saldate** |
| Tirafondi sottoresistenti / passo ridotto | **R3 Cerchiaggio e tirafondi aggiuntivi chimici** |
| Flange bullonate sottoresistenti | **R4 Sostituzione/integrazione bulloni + piastre di irrigidimento** |
| Portanza fondazione (plinto) insufficiente | **R5 Micropali Φ220 L=8m perimetrali + cordolo cls** |
| Intera struttura fortemente sottoresistente | **R6 Sostituzione palo (demolizione + NS)** |

In casi reali **si combinano più rinforzi** (es. LU55041: R2 + R3; LT032: R5 stralli+puntoni + fondazione maggiorata).

---

## R1 — Fasciatura in c.a. + tubo di ringrosso

**Quando si applica:** tronco del palo (tipicamente inferiore o intermedio) con sfruttamento > 1.00 a flessione o compressione.

**Descrizione:**
- Si affianca al tronco un **tubo coassiale** (diametro superiore di 50-100 mm) o si realizza una **fasciatura in c.a.** armata.
- La sezione composta lavora a flessione con modulo resistente maggiorato.

**Formule chiave — tubo di ringrosso:**
- Sezione composta (palo esistente + tubo nuovo): W_composto ≈ W_esistente + W_nuovo
- Coefficiente di efficacia: 0.85-0.90 (collaborazione non piena)
- Saldature di collegamento: cordoni a_sald = 5-8 mm ogni 300-500 mm

**Formule chiave — fasciatura cls:**
- Incamiciatura spessore t = 100-150 mm, armata Φ14/150 verticali + Φ10/200 staffe
- Rigidezza aggiuntiva dal cls (E_cm = 31-33 GPa per C25/30)
- Attenzione a peso aggiuntivo sulla fondazione → verificare portanza

**Pratica costruttiva:**
- Accesso dal cantiere con ponteggio/cestello
- Saldatura in quota (qualifica WPQR)
- Zincatura cordoni a freddo (spray)

**Esempio dataset:** FI023 — non applicato; riferimento teorico.

---

## R2 — Nervature radiali saldate alla piastra di base

**Quando si applica:** piastra di base non nervata (tipica) con spessore insufficiente → k_fs·√(M/f_yd/b_eff) < t_esistente.

**Descrizione:**
- Saldatura di **costole radiali triangolari** (acciaio S355 tipicamente) fra tubo e bordo piastra.
- Trasforma la piastra in un sistema a schema "trave su 2 appoggi" con luce ridotta.

**Formule chiave:**
- N° nervature tipico: 8-12 (coincidenti con posizione tirafondi)
- Dimensione triangolo: base = (d_ex - d_tubo)/2, altezza = 250-400 mm
- Spessore costola: t = 12-20 mm, saldature cordoni a_sald = 6-8 mm
- **Quatordio non si applica più** — la piastra non flette più a mensola
- Verifica come **schema a piastra rinforzata**:  M_max = q·L²/8 (L = distanza fra nervature consecutive misurata lungo la circonferenza)
- Verifica saldatura costola-tubo: τ_sald ≤ f_vw,d (EN 1993-1-8)

**Pratica costruttiva:**
- Intervento in quota base (1.5-2.0 m da fondazione)
- Saldatura a completa penetrazione costola-piastra + cordoni su tubo
- Zincatura impossibile a posteriori: verniciatura epossidica C4/C5

**Esempio dataset:** **LU55041_002** — applicato (combinato con R3).

---

## R3 — Cerchiaggio e tirafondi aggiuntivi con ancoranti chimici

**Quando si applica:** tirafondi originari sottoresistenti a trazione o taglio; passo tirafondi troppo ampio (α-factor δ troppo alto).

**Descrizione:**
- Si aggiungono **barre filettate inghisate** (tipicamente M24-M36 classe 8.8) intercalate fra i tirafondi esistenti.
- La piastra di base viene **forata in opera** per passaggio nuove barre.
- Ancoraggio nella fondazione esistente con **resina epossidica bicomponente** (tipicamente Hilti HIT-RE 500 o Fischer FIS EM).

**Formule chiave:**
- Resistenza ancorante EOTA TR029:
  - N_Rd,p = N_Rk,p / γ_Mc    (pullout, γ_Mc=1.5)
  - N_Rd,c = k_1 · f_ck^0.5 · h_ef^1.5 / γ_Mc    (cono cls)
  - N_Rd,sp = funzione distanza dal bordo
  - N_Rd = min(N_Rd,p, N_Rd,c, N_Rd,sp)
- Profondità ancoraggio: h_ef ≥ 15·φ_barra (tipico 250-500 mm)
- **Distanza minima dal bordo cls:** c ≥ 100 mm (altrimenti coefficiente riduttivo ψ_re)
- **Interasse nuovi ancoranti:** s ≥ 5·φ (per evitare overlap conico)

**Pratica costruttiva:**
- Carotaggio fondazione con lubrificazione ad acqua
- Pulizia foro con aria compressa + spazzola
- Iniezione resina + inserimento barra
- Tempo di cura 48-72 h a 20°C
- Serraggio con chiave dinamometrica (tipicamente 80% M_dyn_costruttore)

**Esempio dataset:** **LU55041_002, RM00189_012** — applicato.

---

## R4 — Sostituzione/integrazione bulloni flangia + piastre di irrigidimento

**Quando si applica:** verifica α-factor sui bulloni della flangia intermedia (giunzione tronco-tronco) non soddisfatta.

**Descrizione:**
- Si **sostituiscono i bulloni esistenti** con classe superiore (8.8 → 10.9 → 12.9).
- Alternativamente si **aggiungono piastre di irrigidimento sotto-flangia** (anulari saldate) per ridurre δ (distanza bullone-bordo → distanza bullone-irrigidimento).

**Formule chiave:**
- Sostituzione bulloni: T_Rd incrementato del rapporto f_tb_nuovo/f_tb_vecchio (es. 10.9/8.8 = 1250/800 = 1.56)
- Piastra di irrigidimento: riduce la distanza b (definita nell'α-factor) → nuovo δ' = (e - d/2) / (d/2 - b') + 1
- **Attenzione:** sostituzione bulloni richiede scarico completo del tronco superiore (operativamente complesso).

**Pratica costruttiva:**
- Scarico tronco superiore con cestello + imbragatura gru
- Svitamento + sostituzione bullone per bullone (procedura sequenziale a croce)
- Coppia di serraggio con chiave dinamometrica

**Esempio dataset:** **LU55041_002** — applicato (combinato con R2, R3).

---

## R5 — Micropali perimetrali + cordolo collaborante

**Quando si applica:** portanza del terreno insufficiente, oppure plinto esistente sottoresistente a ribaltamento o scorrimento.

**Descrizione:**
- Si realizzano **4-8 micropali Φ220 mm L=8-10 m** perimetralmente al plinto esistente.
- Si collega la testa micropalo al plinto con **cordolo in c.a.** armato, che trasferisce le sollecitazioni al nuovo sistema profondo.

**Formule chiave:**
- Portata singolo micropalo (Bustamante-Doix):
  - Q_u = π · D · L · f_s   (attrito laterale)
  - f_s medio: 60-100 kPa in sabbia/limi consolidati
- Tipica Q_u micropalo Φ220 L=8m: 250-400 kN
- N° micropali: determinato da modello distributivo cordolo → tipicamente 4 angolari o 6-8 perimetrali
- Cordolo sezione tipica: 40×60 cm, armato Φ16/200 + staffe Φ10/150

**Pratica costruttiva:**
- Perforazione a rotopercussione (D = 220 mm)
- Armatura HEA100 o tubo Ø139.7×10
- Getto boiacca cementizia ad alta resistenza (rapporto A/C = 0.40-0.45)
- Cordolo in c.a. con ferri passanti attraverso plinto esistente (carotaggio + inghisaggio chimico)

**Esempio dataset:** **LT032 (combinato con R6-stralli+puntoni), SI53014_003** — pratica ricorrente.

---

## R6 — Rinforzi RT specifici: stralli, puntoni, baggioli rinforzati

**Quando si applica:** palo Roof Top con struttura sottoresistente; vincoli ai piani di calpestio non sufficienti.

### R6.a — Strallamento (sistema strallato)

**Tiranti spiroidali tipicamente:**
- TECI Ø18 mm (A=241 mm², T_Rk≈448 kN) o Ø22 mm (A=358 mm², T_Rk≈666 kN)
- Angolo inclinazione strallo: α = 30-45°
- N° stralli: 3 o 4 disposti a 120° o 90° per stabilizzare il palo in 2 piani

**Pretensione:**
- T_0 = 0.35·T_Rk ≈ 150-230 kN (Ø18) / 230-260 kN (Ø22)
- Messa in opera con **tensiometro elettronico** a taratura certificata
- Verifica annuale pretensione (prescrizione in RELSTA e PSC)

**Ancoraggi strallo su copertura:**
- Tasselli chimici M20-M24 classe 10.9 inghisati nel cordolo perimetrale
- Oppure piastre di ripartizione bullonate passanti

**Formule:**
- T_max,SLU = T_0 + ΔT_vento ≤ 0.5·T_Rk
- Verifica ancoraggio: EOTA TR029 con gruppo di tasselli

### R6.b — Puntoni (sistema strutturato)

**Tubi di puntellamento:**
- Tipicamente Ø139.7×7.8 mm, L = 6-10 m, S235 o S355
- Disposti a triangolare fra palo e piani rigidi inferiori (solaio c.a., parete portante)

**Verifica:**
- Instabilità eulerina: N_b,Rd = χ·A·f_yd/γ_M1
- Esnellezza λ ≤ 200
- Cerniere a sfera o fork-bearing alle estremità (per evitare flessione parassita)

**Esempio dataset:** **LT032** — sistema combinato stralli Ø18 + 4 puntoni Ø139.7.

### R6.c — Rinforzo baggioli (per palo su copertura c.a.)

**Baggioli = piedini di ancoraggio del palo sulla copertura c.a.**

Quando la copertura c.a. non è strutturalmente adeguata, si rinforza con:
- **Ringrosso baggiolo**: tassello chimico + getto integrativo c.a.
- **Piastra di ripartizione saldata al baggiolo** e inghisata chimicamente su area estesa
- **Carotaggio copertura + solaio armato**: trasferimento del carico al solaio sottostante

---

## Workflow operativo per la progettazione di un rinforzo

1. **Identifica la criticità** dalla verifica del palo esistente (STEP D.2 del workflow principale).
2. **Scegli la tipologia di rinforzo** dalla tabella in testa.
3. **Dimensiona il rinforzo** applicando le formule specifiche.
4. **Verifica il sistema composto (esistente + rinforzo)** — la verifica SLU va rifatta con la sezione/sistema rinforzato.
5. **Produci gli elaborati grafici** del rinforzo (viste, sezioni, distinte bulloni/saldature/ancoranti).
6. **Inserisci in RELSTA il capitolo "Progetto di rinforzo"** con:
   - Descrizione dell'intervento
   - Calcoli del rinforzo
   - Verifica del sistema rinforzato
   - Prescrizioni esecutive (coppie di serraggio, tempi di cura resine, pretiri, controlli)
   - Tavole grafiche in allegato

## Prescrizioni esecutive sempre da inserire

- **Coppie di serraggio bulloni** (N·m) per ogni classe utilizzata
- **Tempi di cura resine epossidiche** (tipicamente 48-72 h a 20°C)
- **Pretiri stralli** con tensiometro a taratura certificata
- **Controlli post-intervento**: verifica saldature con controllo visivo + LP (liquidi penetranti) su saldature di testa
- **Controllo spessore zincatura** su nuovi elementi (EN ISO 1461)
- **Verifica periodica** (annuale per stralli, biennale per bulloni) prescritta al proprietario

---

*Questo catalogo è la sintesi dei 9 casi dataset K2A. Per ogni nuovo intervento di rinforzo, verificare l'applicabilità al contesto specifico (vincoli ambientali, accessibilità, disponibilità di materiali).*
