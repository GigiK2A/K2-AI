# Formule chiave — RELSTA palo porta-antenne TLC

Riferimenti normativi: NTC 2018 + Circ. 7/2019 + EN 1993-1-1/5/8/9 + CNR-DT 207/2008 + EN 1997-1.

---

## 1. Azioni del vento (CNR-DT 207/2008)

**Pressione cinetica di riferimento (v_b,0 → v_b → v_r → q_r):**
- v_b = v_b,0 · c_a (altitudine sul s.l.m., c_a = 1 se a_s ≤ a_0)
- v_r = v_b · c_r (T_R=50 anni → c_r=1)
- q_r = ½ · ρ · v_r² (ρ = 1.25 kg/m³ aria standard)

**Pressione del vento sulla struttura:**
- p = q_r · c_e(z) · c_p · c_d
- c_e(z) = k_r² · ln(z/z_0) · [7 + k_r² · ln(z/z_0) · c_t(z)]  (categoria esposizione)
- c_p = 0.7 per palo cilindrico/poligonale (NORMALE)
- **c_p = 1.0 per palo MASCHERATO FINTO ALBERO** (superficie chioma piena)
- c_d = 1.0 (fattore dinamico, da valutare se H_tot > 60 m)

**Azione sulle antenne (forma quadra/parallelepipeda):**
- F_vento = p · A_eff · c_p_antenna · c_d
- c_p = 1.2-1.5 per antenna a pannello (dato costruttore)
- A_eff = larghezza × altezza antenna (SEV cataloghi Huawei/Ericsson/Nokia)

**Verifica di deformabilità (SLE) — vento di esercizio:**
- **v = 100 km/h ≡ p = 482 N/m²** (obbligatorio per iliad/Cellnex)
- Limite rotazione parabole: ±2° → controllo HPBW link
- Limite spostamento in sommità: H/100 (pali snelli)

---

## 2. Azione sismica (NTC 2018 § 3.2)

**Spettri di risposta (T_R funzione di V_R e classe d'uso):**
- V_N = 50 anni (classe ordinaria) → sito TLC in genere CU II (V_R = 50 a.) o CU III se strategico
- Periodi di ritorno: SLO 30a, SLD 50a, SLV 475a, SLC 975a

**Periodi fondamentali del palo:**
- T₁ ≈ 0.0062 · H^0.75 / √(I/m)  (palo a mensola)
- T₁ reale da modello FEM (sempre da modello — MAI stima analitica per palo snello)

**Per siti TLC l'azione sismica è generalmente NON DIMENSIONANTE** (dominante il vento), ma va COMUNQUE esplicitata nei calcoli.

---

## 3. Azioni sulla neve e sul ghiaccio

**Ghiaccio su elementi tubolari** (CEI EN 60826):
- incremento diametro: Δd = 2 · t_ghiaccio (t_ghiaccio = 25-40 mm in zona montana)
- incremento peso: Δp = ρ_ghiaccio · π · (d+t) · t   (ρ = 900 kg/m³)
- Combinazione "G+V+GHIACCIO" è spesso dimensionante in zona 3-7 (Appennino, Alpi)

**Neve non significativa** su elementi verticali snelli (escluso sommità pennone).

---

## 4. Combinazioni di carico (NTC 2018 § 2.5.3)

**SLU STR** (fondamentale):
- E_d = γ_G1·G1 + γ_G2·G2 + γ_Q1·Q_k1 + Σ(γ_Qi·ψ_0i·Q_ki)
- γ_G1 = 1.3 (sfavorevole), γ_G2 = 1.5, γ_Q = 1.5
- Vento/sisma alternati come azione variabile dominante

**SLU GEO** (per fondazioni):
- Approccio 1 Combinazione 2: γ_G1=1.0, γ_G2=1.3, γ_Q=1.3
- Γ_M (terreno): γ_φ'=1.25, γ_c'=1.25, γ_γ=1.0

**SLE** (rari + frequenti):
- E_d = G1 + G2 + Q_k1 + Σ(ψ_0i·Q_ki) — vento 100 km/h per deformabilità

---

## 5. Verifica membrature — EN 1993-1-1

**Flessione + taglio + sforzo normale** (sezione tubolare circolare):
- σ_Ed = N/A + M/W ≤ f_yd/γ_M0   (γ_M0 = 1.05)
- τ_Ed = V · S / (I · t) ≤ f_yd/(√3·γ_M0)
- Combinata Von Mises: σ_VM = √(σ² + 3τ²) ≤ f_yd/γ_M0

**Instabilità membro compresso:**
- N_Ed/χ·N_Rk/γ_M1 ≤ 1    (γ_M1 = 1.05)
- χ da curva di buckling (b o c per tubi saldati)

**Instabilità locale di sezione (Classe sezione):**
- d/t ≤ 50·ε² → Classe 1-2-3 (EN 1993-1-1 Tab 5.2)
- d/t > 90·ε² → Classe 4 → sezione efficace ridotta (EN 1993-1-6 shell buckling)

ε = √(235/f_y)  →  S355 ε = 0.814, S460 ε = 0.715

---

## 6. Giunto flangiato tronco-tronco (α-factor)

**Formula α-factor** (EN 1993-1-8 Allegato nazionale + DIN 18800):

Sia δ il rapporto fra distanza bullone-bordo flangia e distanza bullone-anima tubo:
- δ = (e - d/2) / (d/2 - b) + 1

**Caso δ < 2.45** (flangia spessa/bulloni vicini):
- α = 1.87 · δ⁴ - 4.50 · δ³ + 4.90 · δ² - 2.12 · δ + 1.00   (polinomiale 4° grado)

**Caso δ ≥ 2.45** (flangia sottile):
- α = 0.35 · δ + 0.15  (lineare)

**Tiro sul bullone:**
- F_t,bullone = α · N_Ed_tubo / n_bulloni    (n = 8/12/16/24 tipico)
- con N_Ed_tubo = N_assiale + M_flettente·y_max/W

**Verifica bullone (EN 1993-1-8):**
- F_t,Rd = 0.9 · f_tb · A_res / γ_M2   (γ_M2 = 1.25)
- F_v,Rd = 0.6 · f_tb · A_res / γ_M2
- Combinata: a = F_v,Ed/F_v,Rd + F_t,Ed/(1.4·F_t,Rd) ≤ 1

**Classi bullone tipiche:** 8.8 (f_tb=800 MPa), 10.9 (f_tb=1000 MPa)

---

## 7. Piastra di base non nervata (formula Quatordio)

**Spessore minimo piastra di base non nervata** (solo tirafondi):

- **k_fs = 0.45 + 0.12 · ρ**     con ρ = d_ex/d_in (rapporto diametro esterno/interno corona tirafondi)
- t_min = k_fs · √(M_Ed / (f_yd · b_eff))

Riferimento: Quatordio R., "Piastre di fondazione: calcolo e verifica" (manualistica IS Ingegneria Strutturale).

**Per piastre nervate** (costole saldate radiali) il modello cambia: la piastra lavora come trave su 2 appoggi (costola + tubo) e non per flessione a mensola.

---

## 8. Tirafondi / Ancoranti chimici

**Tirafondi classici (barre filettate + zancaggio in fondazione):**
- T_tf = F_t,bullone · γ_amp    (γ_amp = 1.1-1.3 per forza dinamica)
- Lunghezza ancoraggio: L_anc ≥ 30·φ (fattore aderenza cls C25/30)

**Ancoranti chimici post-installati** (per rinforzi su strutture esistenti):
- EOTA TR029 / ETA
- Resistenza caratteristica N_Rk,p (pullout) + N_Rk,c (cono cls) + N_Rk,sp (splitting)
- Coefficiente γ_Mc = 1.5 (materiale) · γ_Mi (installazione)

---

## 9. Verifica a fatica — Woehler + Miner

**Curva S-N bilineare** (EN 1993-1-9):
- per N ≤ 5·10⁶: log(ΔσR) = log(ΔσC) + (1/m) · log(2·10⁶/N)   m=3
- per N > 5·10⁶: m=5, fino al cut-off N_L = 10⁸

**Categorie di dettaglio (ΔσC a 2·10⁶ cicli):**
- **80 MPa** — piastra di base saldata d'angolo al tubo (EN 1993-1-9 Tab 8.5)
- **90 MPa** — saldatura longitudinale tubo poligonale
- **56-71 MPa** — flangia bullonata (classi alte di bulloni)

**Tensione ammissibile fatica:**
- Δσ_Ed ≤ ΔσC / γ_Mf   (γ_Mf = 1.35 per danno tollerabile classe "safe life")

**Danno cumulativo Palmgren-Miner:**
- D = Σ (n_i / N_i) ≤ 1.0
- n_i = cicli attesi al livello tensionale Δσ_i (distribuzione vento sito)
- N_i = cicli ammissibili a Δσ_i dalla curva S-N

**Fatica obbligatoria per iliad e Cellnex** se H_S > 30 m o zona vento 3-9 o con parabole MW.

---

## 10. Capacità portante fondazione — Brinch-Hansen / Vesic

**Formula generale:**
- q_lim = c'·N_c·s_c·d_c·i_c + q·N_q·s_q·d_q·i_q + 0.5·γ·B·N_γ·s_γ·d_γ·i_γ

**Fattori di capacità portante:**
- N_q = e^(π·tan φ') · tan²(45+φ'/2)
- N_c = (N_q - 1) · cot φ'
- N_γ = 2 · (N_q - 1) · tan φ'   (Brinch-Hansen)
- N_γ = 2 · (N_q + 1) · tan φ'   (Vesic, più conservativo)

**Fattori di inclinazione carico (i_c, i_q, i_γ):**
- H = forza orizzontale alla base; V = forza verticale
- m = f(B/L) — per plinto quadrato m = 2
- i_q = [1 - H/(V + A_f·c'·cot φ')]^m
- i_γ = [1 - H/(V + A_f·c'·cot φ')]^(m+1)
- **CRITICO** per pali TLC dove H/V elevato (vento dominante)

**Verifica:**
- R_v,d = q_lim · A_f' / γ_R     (γ_R = 2.3 per A1C1, 1.8 per A2C2)
- E_v,d ≤ R_v,d

**Ribaltamento:**
- Momento stabilizzante M_S = W_tot · b/2 (b = lato plinto)
- Momento ribaltante M_R = H·h + M_base
- FS = M_S / M_R ≥ 1.5 (DM 2018)

**Scorrimento:**
- R_h,d = (V + W_plinto) · tan δ / γ_R     (δ = 2/3·φ')
- H_Ed ≤ R_h,d

---

## 11. Micropali (rinforzo fondazione tipico RL-POLE)

**Tipico sito TLC:** micropalo Φ220 mm, L = 8 m, armatura HEA100 o tubo Φ139.7 × 10.

**Portata ultima pullout** (Bustamante-Doix):
- Q_u = π · D · L · f_s
- f_s = attrito laterale (kPa): 50-120 kPa per sabbia densa, 20-80 kPa per argilla

**Portata ultima compressione:**
- Q_u = Q_laterale + Q_base (base trascurabile per pali di piccolo diametro)

**Coefficiente di sicurezza:**
- γ_R = 1.35 (resistenza) + γ_γt = 1.8 (modello)

**Tipica portata micropalo Φ220 L=8m:** 250-400 kN in compressione, 150-250 kN a trazione.

---

## 12. Stralli / Tiranti (sistema strallato RT)

**Tiranti spiroidali tipici:** TECI Ø18 o Ø22 mm, φ_s = 1860 MPa (acciaio armonico).

**Pre-tiro con tensiometro:**
- T_0 ≈ 0.35 · T_Rk   (tensione di servizio)
- T_Rk = A_tirante · f_uk   (A Ø18 ≈ 241 mm² → T_Rk ≈ 448 kN)

**Rigidezza equivalente (strallo inclinato):**
- K_eq = E_s · A · cos²α / L    (α = angolo inclinazione strallo)
- E_s = 205 GPa acciaio armonico

**Verifica** (combinazione SLU con vento + pretiro):
- T_max = T_0 + ΔT_vento ≤ 0.5 · T_Rk

**Prescrizione obbligatoria:** utilizzo tensiometro a taratura certificata per messa in opera + verifica annuale pretensione.

---

## 13. Puntoni (sistema strutturato RT)

**Tipico:** tubo Ø139.7 × 7.8 mm, L = 8.5 m, acciaio S235 o S355.

**Verifica instabilità eulerina:**
- N_cr = π²·E·I / (β·L)²  — β = 1.0 (cerniera-cerniera tipico)
- N_b,Rd = χ · A · f_yd    (da curva buckling)

**Esnellezza limite:** λ ≤ 200 (per membri principali compressi)

---

## 14. Protezione anticorrosiva (UNI EN ISO 1461)

**Zincatura a caldo:**
- Spessore minimo rivestimento (EN ISO 1461 Tab 3): 
  - spessore acciaio 1.5-3 mm → ≥ 45 μm
  - spessore acciaio 3-6 mm → ≥ 55 μm
  - spessore acciaio > 6 mm → ≥ 70 μm
- Sovrametallo di calcolo: 0 mm (rivestimento protettivo esterno)

**Vita utile in ambiente C3:** > 30 anni (corrosione 1-2 μm/anno)

---

## 15. Tassi di sfruttamento — Cellnex vs iliad

**Convenzione iliad:** η = E_d / R_d   (η ≤ 1.00 OK)
**Convenzione Cellnex (CNP_TS21_002):** α = R_d / E_d   (α ≥ 1.00 OK → percentuale utilizzo residuo = 1 - 1/α)

**Margini di sicurezza richiesti:**
- iliad: η ≤ 0.95 raccomandato (soglia 0.80 "buono", 0.80-0.95 "accettabile", > 0.95 "critico")
- Cellnex: margine residuo ≥ 15-20% per new loading (co-siting successivi)

---

## 16. Fattori di Confidenza (NTC 2018 § 8.5.4)

**Livello di Conoscenza → Fattore di Confidenza:**
- **LC1** (conoscenza limitata): FC = 1.35 — solo geometria + specifiche progettuali
- **LC2** (conoscenza adeguata): FC = 1.20 — geometria + dettagli + prove limitate
- **LC3** (conoscenza accurata): FC = 1.00 — geometria + dettagli + prove estese + collaudo

**Applicazione:**
- f_cd_effettivo = f_cd / FC
- f_yd_effettivo = f_yd / FC

**Per palo TLC esistente con collaudo disponibile:** LC2 (FC=1.20) tipico.
**Senza collaudo o documentazione lacunosa:** LC1 (FC=1.35).

---

*Tutte le formule vanno applicate con i valori numerici del sito specifico. Questo riferimento è una sintesi operativa — per derivazioni rigorose consultare le norme citate.*
