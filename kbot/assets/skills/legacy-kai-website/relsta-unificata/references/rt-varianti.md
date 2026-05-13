# Varianti Roof Top (RT) — RELSTA palo porta-antenne TLC

I siti Roof Top presentano 4 sotto-tipologie che richiedono **modellazioni e verifiche differenti**. Identificare correttamente la variante è il prerequisito per impostare il modello di calcolo.

---

## RT-1 — Palo ancorato a pilastri in c.a. (o travi di bordo)

**Descrizione:** palo metallico (tubolare o flangiato) vincolato ai **pilastri di testata** dell'edificio, tipicamente tramite piastre bullonate o saldate a collari metallici avvolgenti.

**Vincolo strutturale:**
- Incastro/semi-incastro alla base (su piastra collegata a pilastro)
- Possibili vincoli intermedi aggiuntivi (a metà altezza) per riduzione snellezza
- La **rigidezza del pilastro** va modellata (non è vincolo infinitamente rigido)

**Modellazione FEM:**
- Palo con elementi beam
- Vincolo alla base: molla rotazionale equivalente a rigidezza flessionale pilastro
- Se possibile, modellare ANCHE il pilastro per verifica carichi trasmessi

**Verifiche specifiche:**
1. Sollecitazioni massime sul palo (flessione, taglio, sforzo normale)
2. **Sollecitazioni trasmesse al pilastro esistente** (carichi taglianti, assiali, flettenti alla testa)
3. **Verifica pilastro esistente** con nuovi carichi → se pilastro sottoresistente → rinforzo pilastro
4. Verifica collegamento palo-pilastro (bulloni, saldature, staffe)

**Prescrizioni:**
- Carpenteria: collari metallici S355 abbraccianti, spessore minimo 10 mm
- Bulloni M16-M20 classe 8.8 o 10.9 passanti attraverso pilastro (preferibile) oppure ancoranti chimici
- Zincatura a caldo obbligatoria (anche su carpenteria di collegamento)

**Esempio dataset:** FI50137_802 (simile), contesto tipico centri urbani.

---

## RT-2 — Palo su muratura portante

**Descrizione:** palo vincolato a **muri portanti in muratura ordinaria** (laterizio, tufo, pietra), tipicamente edifici storici o di inizio Novecento.

**Criticità:**
- Muratura ha **bassa resistenza a trazione** (quasi nulla ai nodi)
- **Carichi eccentrici** trasmessi dal palo possono causare fessurazione/espulsione di mattoni
- Difficile garantire vincolo rigido

**Soluzioni tecniche:**
- **Piastra di ripartizione metallica** a cavalcione del muro, con barre passanti attraverso tutta la sezione muraria
- **Collari di acciaio** avvolgenti se mura sufficientemente spesse
- **Cappe in c.a.** sommitali al muro per trasformare la muratura in testa in un sistema rigido

**Modellazione FEM:**
- Vincolo alla base: cerniera o semi-cerniera (rotazione libera) → palo lavora come pendolo/mensola
- Eventualmente modellare il muro come piastra equivalente con modulo elastico E_muratura = 1000-3000 MPa
- Verifica tensione di contatto < f_d,muratura (NTC 2018 § 4.5.6)

**Verifiche specifiche:**
1. Sollecitazioni sul palo
2. **Tensione di contatto sulla muratura** sotto piastra di ripartizione
3. **Pull-out delle barre di ancoraggio** (formula EOTA TR029 adattata per muratura: ancoraggi chimici con bullette di ottone/acciaio inox)
4. Verifica stabilità muro (ribaltamento locale se muro snello)

**Prescrizioni:**
- Iniezioni consolidative del muro (se degradato) con malte compatibili (leganti idraulici naturali — NO cemento su muratura storica)
- Ancoranti chimici specifici per muratura (Fischer FIS VW, Hilti HIT-HY 270)
- Indagini preliminari: saggi muratura, prove sonore, caratterizzazione meccanica

**Esempio dataset:** Non presente in K2A core; tipico per Centri Storici.

---

## RT-3 — Palo su copertura in c.a. (con baggioli o piastra)

**Descrizione:** palo fissato direttamente su **solaio di copertura in c.a.**, tramite:
- **Baggioli metallici** (piedini di ancoraggio saldati al palo, bullonati al solaio)
- **Piastra di base con tirafondi chimici** inghisati nel solaio
- **Zavorramento gravitazionale** (vedi RT-4)

**Criticità:**
- **Copertura c.a. progettata per carichi abitativi/tecnici**, raramente predimensionata per spinte orizzontali da vento su palo
- **Solaio può essere ORDITO IN UNA DIREZIONE** — la distribuzione delle forze dipende dall'orientamento
- Carichi concentrati molto elevati in punti specifici

**Modellazione FEM:**
- Palo con beam elements
- Vincolo alla base: in generale incastro (piastra di base con tirafondi)
- Modellare il solaio c.a. con elementi shell (Straus7/PRO_SAP) per verifica distribuzione dei carichi → individuare zone con sollecitazioni aggiuntive significative

**Verifiche specifiche:**
1. Sollecitazioni sul palo
2. **Verifica solaio c.a. esistente** con carichi aggiuntivi:
   - Flessione travetti (se latero-cemento) o soletta (se piena)
   - Taglio in prossimità della piastra
   - Punzonamento (raro, ma verificare se carico assiale palo > 80-100 kN)
3. **Verifica tirafondi chimici** nel solaio (EOTA TR029, attenzione a distanza dal bordo)
4. **Propagazione fino al piano terra** — carichi trasmessi alle travi portanti e alle pareti sottostanti

**Prescrizioni:**
- Diamantatura e rifacimento impermeabilizzazione attorno ai fori dei tirafondi
- Sistema di fissaggio antifurto/antimanomissione per bulloni piastra
- Manutenzione periodica guaina impermeabile (biennale)

**Esempio dataset:** **SI53014_003** (parzialmente), RM823 (probabile), pratiche ricorrenti.

---

## RT-4 — Palo su shelter metallico zavorrato

**Descrizione:** palo fissato su **shelter (container metallico/prefabbricato)** sul tetto, oppure su **basamento metallico zavorrato** con blocchi di calcestruzzo (tipicamente 4-8 blocchi da 1 tonnellata ciascuno).

**Criticità:**
- **Stabilità al ribaltamento** dipende esclusivamente dalla massa zavorrante
- **Scorrimento** dipende dall'attrito sulla pavimentazione (coefficiente di attrito da prove o da letteratura: μ ≈ 0.4-0.5 per gomma-calcestruzzo)
- **Azione sismica** può essere dimensionante (massa rilevante non vincolata)

**Modellazione FEM:**
- Palo con beam elements
- Vincolo alla base: ancoraggio su piastra di shelter → incastro nominale
- Verifica shelter come **corpo rigido**: ribaltamento + scorrimento

**Verifiche specifiche:**
1. Sollecitazioni sul palo
2. **Verifica ribaltamento shelter** (globale):
   - M_stabilizzante = W_zavorra · b/2
   - M_ribaltante = F_vento · h_palo + F_vento_shelter · h_shelter/2
   - FS_ribaltamento ≥ 1.5 (SLV), ≥ 2.0 (SLE)
3. **Verifica scorrimento** globale:
   - F_stabilizzante = μ · W_tot
   - F_scorrimento = F_vento_tot
   - FS_scorrimento ≥ 1.3
4. **Verifica sollecitazioni sul solaio** da carichi concentrati sotto zavorra
5. **Verifica fissaggio palo a shelter** (bulloni, saldature)

**Prescrizioni:**
- Zavorra obbligatoriamente dimensionata (nessuna tolleranza — se mancano blocchi, lo shelter si ribalta)
- Attrito pavimentazione verificato con prova sul sito (se possibile)
- Sistema antifurto per i blocchi zavorra (saldatura o bulloni tra blocchi)
- Manutenzione: verifica annuale posizione blocchi + fissaggio palo

**Esempio dataset:** RM939 (probabile, da confermare), pratica tipica in periferia industriale.

---

## Matrice decisione RT-variante

| Variante RT | Indicatore | Vincoli calcolabili | Criticità dominante |
|---|---|---|---|
| RT-1 pilastri c.a. | Palo bullonato a pilastro | Rigidezza pilastro | Carichi su pilastro esistente |
| RT-2 muratura | Base ancorata a muro portante | Semi-cerniera | Tensione su muratura |
| RT-3 copertura c.a. | Piastra di base su solaio | Incastro | Punzonamento solaio |
| RT-4 shelter zavorrato | Basamento metallico + pesi | Corpo rigido zavorrato | Ribaltamento/scorrimento |

---

## Classificazione da sopralluogo

Durante il sopralluogo preliminare, verificare:
1. **Posizione del palo**: a ridosso del muro perimetrale? Al centro del tetto? Su torre scala?
2. **Tipo di solaio di copertura**: latero-cemento (travetti + pignatte + soletta), pienamente c.a., struttura metallica con lamiera grecata
3. **Pareti di ancoraggio**: c.a., muratura portante, tamponamento non portante (se tamponamento → NON UTILIZZABILE)
4. **Sistemi esistenti di fissaggio**: baggioli, piastra, stralli, puntoni, zavorra
5. **Documentazione disponibile**: progetto originario palo, progetto edificio, collaudi, prove sul materiale

Da questi dati si classifica definitivamente la variante RT e si imposta la modellazione.

---

## Elaborati grafici minimi per RELSTA RT

1. **Inquadramento sul tetto** (planimetria di copertura con palo e sistema di ancoraggio)
2. **Sezione verticale palo + struttura sottostante** (almeno 1-2 piani a ritroso, per evidenziare carichi trasmessi)
3. **Dettagli costruttivi** dei sistemi di fissaggio (baggioli/piastra/stralli/puntoni/zavorra)
4. **Sezione piano di posa** (vincolo alla base)
5. **Distinta bulloni/ancoranti** utilizzati

---

*Per la classificazione automatica consultare anche la skill `verifica-statica-iliad-cellnex:vs-template-paline-rt` che offre template pre-compilati per le varianti ricorrenti.*
