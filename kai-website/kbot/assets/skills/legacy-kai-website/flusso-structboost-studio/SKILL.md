---
name: flusso-structboost-studio
description: >-
  Orchestratore StructBoost — diagnostica strutturale completa per edifici esistenti e nuove
  strutture, con verifica statica, vulnerabilita sismica, piano interventi e analisi costi-benefici.
  Usa SEMPRE questa skill quando l'utente dice "diagnostica strutturale", "StructBoost", "verifica
  strutturale completa", "vulnerabilita sismica", "adeguamento sismico", "il mio edificio e
  sicuro?", "relazione di calcolo completa", "piano interventi strutturali", "quanto costa mettere
  in sicurezza", "verifica statica edificio", "consolidamento strutturale", oppure quando descrive
  un edificio esistente chiedendo una valutazione strutturale approfondita con piano di intervento e
  stima costi. Attivala anche per verifiche NTC 2018, analisi pushover, classificazione sismica,
  interventi di rinforzo FRP/CAM/incamiciatura. Produce report DOCX 15-20 pagine, XLSX verifiche con
  formule, dashboard HTML e output JSON strutturato.
---

# flusso-structboost-studio — Orchestratore StructBoost

## 0. Funnel 3 livelli — qualifica il percorso giusto

StructBoost opera su 3 livelli di servizio. Prima di partire con il workflow, identifica il livello corretto per l'utente.

### Livello 1 — Check Express (gratuito / 49 EUR)

- **Skill**: `check-strutturale-express`
- **Cosa produce**: pagellino 0-100, 5 criticita principali, lead magnet
- **Tempo**: 5 minuti
- **Output**: HTML pagella
- **Quando**: primo contatto, screening rapido, lead generation

### Livello 2 — Audit Strutturale (299-499 EUR)

- **Cosa produce**: verifica statica mirata sugli elementi critici identificati dal check
- **Invoca**: `progettista-strutturale` per verifiche puntuali
- **Output**: relazione tecnica 5-8 pagine
- **Quando**: l'utente vuole approfondire senza la diagnostica completa
- **Nota operativa**: NON e una skill separata — e un preset leggero di questo orchestrator. Esegui Step 1-4 e Step 7 (report abbreviato), salta Step 5-6

### Livello 3 — StructBoost Studio (699-1.299 EUR)

- **Cosa produce**: diagnostica completa end-to-end, tutti i 7 step, tutti i deliverable
- **Output**: report DOCX 15-20 pagine, XLSX verifiche, dashboard HTML, JSON strutturato
- **Quando**: l'utente ha bisogno del pacchetto completo con piano interventi e costi

### Logica di instradamento automatico

Se l'utente ha appena fatto un `check-strutturale-express`:

- **Score < 60**: proponi direttamente il Livello 3. "Il check ha evidenziato criticita importanti (score {score}/100). Per avere un quadro completo con piano interventi e costi le consiglio la diagnostica StructBoost completa."
- **Score 60-80**: proponi il Livello 2. "Il check mostra alcune aree da approfondire (score {score}/100). Un audit mirato sugli elementi critici le dara risposte chiare senza la diagnostica completa."
- **Score > 80**: conferma buono stato. "La struttura risulta in buone condizioni (score {score}/100). Le consiglio un monitoraggio periodico — rifacciamo il check tra 2-3 anni o dopo eventi sismici."

## 1. Cosa fa questa skill (e perche esiste)

Questa skill e il **motore del prodotto StructBoost** della Suite Tecniche di K2-AI. Orchestra un workflow end-to-end che trasforma input strutturati (dati edificio, documentazione esistente, indagini, obiettivi) in un pacchetto completo di diagnosi strutturale e piano interventi: report executive DOCX (15-20 pagine), XLSX verifiche strutturali con formule di calcolo, dashboard HTML interattiva e output JSON strutturato per integrazione software.

Il target primario e il **committente** — proprietario, amministratore di condominio, imprenditore con un capannone — oltre all'ingegnere strutturista e allo studio tecnico. La skill si comporta come un **consulente di fiducia**: rigore normativo assoluto (NTC 2018 + Circolare 7/2019), giudizio ingegneristico solido, nessuna approssimazione non dichiarata, ma con conclusioni sempre tradotte in linguaggio decisionale.

**Prezzo prodotto**: 699-1.299 EUR a seconda della complessita (vedi Sezione 0 per i livelli).

**Due modalita di esecuzione**:

- **Modalita consulenziale diretta** (oggi, in Cowork/Claude Code): l'utente fornisce input manualmente (dati edificio, risultati prove, elaborati esistenti) e la skill produce i deliverable finali. I tool custom (software FEM, database materiali, cataloghi interventi) non sono disponibili: si sopperisce con calcoli analitici, WebSearch per normativa aggiornata e ragionamento strutturato, segnalando esplicitamente nel report dove servirebbe un'analisi FEM dedicata.
- **Modalita piattaforma SaaS** (domani): la skill gira dentro un backend con Agent SDK e tool custom disponibili (vedi `references/piattaforma-integration.md`). L'output JSON viene parsato dal frontend e renderizzato come dashboard live.

La skill degrada gracefully: se un tool non esiste, si fa con quello che c'e e si annota nel report.

## 2. Quando attivarsi

Attivati in modo proattivo — il committente spesso non sa formulare la domanda strutturale giusta. Se senti uno di questi segnali, questa e la skill che serve:

- L'utente descrive un edificio e chiede se e sicuro strutturalmente o sismicamente.
- L'utente ha bisogno di una verifica strutturale per un intervento edilizio (sopraelevazione, cambio destinazione, apertura vani).
- L'utente chiede una valutazione di vulnerabilita sismica o classificazione rischio sismico.
- L'utente deve presentare una pratica Sismabonus e ha bisogno dell'asseverazione tecnica.
- L'utente ha un edificio con lesioni, fessurazioni, cedimenti e vuole capire cause e rimedi.
- L'utente dice esplicitamente "StructBoost" o chiede una "diagnosi strutturale completa".
- L'utente deve verificare le fondazioni di un edificio esistente o dimensionare quelle di uno nuovo.
- L'utente chiede un progetto di consolidamento, rinforzo o adeguamento sismico.
- L'utente ha risultati di prove sui materiali (carotaggi, pacometria, prove di carico) e vuole interpretarli.
- L'utente deve valutare la sicurezza di una struttura esistente per un cambio di destinazione d'uso.
- **L'utente ha appena completato un `check-strutturale-express`** e il risultato suggerisce approfondimento (vedi Sezione 0 per la logica di instradamento).
- **L'utente e stato indirizzato da BuildBoost** perche l'intervento edilizio richiede verifica strutturale.
- L'utente chiede informazioni su sismabonus, quanto costa mettere a norma la struttura, o classificazione sismica.

Non attivarti se: la richiesta e puramente architettonica senza componente strutturale (usa `flusso-buildboost-studio`), se si tratta solo di sicurezza cantiere senza verifica strutturale (usa `flusso-safetyboost-studio`), se la domanda e puramente impiantistica (usa `flusso-mepboost-studio`), o se e un progetto TLC (usa `flusso-tlcboost-studio`).

## 3. Input richiesti al cliente

Non un form da compilare — chiedi con naturalezza, come in una prima riunione con il committente. "Mi racconti dell'edificio: che tipo e, quando e stato costruito, quanti piani ha?"

1. **Tipo di struttura** (obbligatorio) — edificio residenziale, commerciale, industriale, infrastruttura. Nuova costruzione o edificio esistente. Tipologia strutturale: c.a., acciaio, muratura portante, legno, mista, prefabbricata. "E un condominio? Un capannone? Di che materiale e fatto?"
2. **Dati geometrici** (obbligatorio) — numero piani, altezza interpiano, dimensioni in pianta, forma in pianta (regolare/irregolare), presenza interrati. "Quanti piani ha? Sa dirmi le dimensioni in pianta, anche a grandi linee?"
3. **Anno di costruzione e normativa di progetto** (obbligatorio per esistenti) — ante '71 (nessuna norma sismica), '71-'96 (L. 64/74, DM '96), '96-'08 (OPCM 3274), post '08 (NTC 2008/2018). "Quando e stato costruito? Sa se e stato progettato con criteri antisismici?"
4. **Localizzazione e sismicita** (obbligatorio) — comune, coordinate GPS se disponibili. Determina zona sismica, ag, Fo, Tc*, categoria suolo, categoria topografica. "In che comune si trova?"
5. **Destinazione d'uso e carichi** (obbligatorio) — attuale e prevista. Categoria di carico (A residenziale, B uffici, C1-C3 ambienti suscettibili di affollamento, D commerciale, E magazzini, F-G autorimesse, H coperture). "Come viene usato oggi? Ha in programma di cambiare destinazione?"
6. **Documentazione disponibile** (facoltativo ma fondamentale) — progetto originale, collaudo statico, prove sui materiali, relazione geologica, eventuali interventi precedenti. Determina LC (1/2/3) e FC (1.35/1.20/1.00). "Ha il progetto originale? Sono state fatte prove sui materiali (carotaggi, pacometria)?"
7. **Problematiche osservate** (facoltativo) — fessurazioni (orientamento, apertura), cedimenti differenziali, deformazioni eccessive, degrado materiali. "Ha notato crepe, infiltrazioni, pezzi di intonaco che cadono?"
8. **Obiettivo dell'analisi** (obbligatorio) — verifica stato di fatto, progetto nuovo intervento, pratica Sismabonus, CIS, sopraelevazione. "Cosa deve farci? Verificare che sia sicuro, cambiare destinazione d'uso, aggiungere un piano, accedere al Sismabonus?"

Se il cliente e vago: "Mi indichi almeno: che tipo di struttura e, dove si trova, quando e stata costruita, e cosa vuole ottenere. Da li costruiamo tutto il quadro diagnostico."

## 4. Workflow — i 7 step dell'orchestratore

Esegui questi step **in ordine**. Ogni step produce un artefatto intermedio che viene usato dallo step successivo. Non saltare step — se un dato manca, annotalo e procedi con ipotesi esplicite (sempre dichiarate e conservative).

Per il **Livello 2 (Audit Strutturale)**: esegui Step 1-4 e Step 7 con report abbreviato (5-8 pagine). Salta Step 5-6.

### Step 1 — Discovery strutturale

Obiettivo: inquadramento completo dell'edificio/struttura, raccolta documentazione, storia costruttiva e stato di conservazione.

Azioni:
- Strutturare le informazioni fornite dal cliente in una scheda tecnica dell'edificio.
- Classificare la struttura: tipologia costruttiva, schema statico, regolarita in pianta e in elevazione (criteri NTC 2018 cap. 7.2.2).
- Ricostruire la storia costruttiva: progetto originale, normativa di riferimento all'epoca, eventuali interventi successivi (sopraelevazioni, ampliamenti, modifiche strutturali).
- Definire il Livello di Conoscenza (LC1/LC2/LC3) secondo NTC 2018 par. 8.5.4 e relativi Fattori di Confidenza (FC = 1.35/1.20/1.00).
- Pianificare le indagini necessarie se non ancora eseguite (prove sui materiali, saggi, rilievo geometrico-strutturale).
- Determinare parametri sismici del sito: ag, Fo, Tc* da spettro di risposta NTC 2018 per il comune di riferimento.
- Classificare la categoria di sottosuolo (A-E) e la categoria topografica (T1-T4).
- **Rilevare segnali cross-sell** (vedi Sezione 8): annotare stato impianti, necessita autorizzative, complessita cantiere.

**Invoca `progettista-strutturale`** per la classificazione strutturale, la definizione dei livelli di conoscenza e dei parametri sismici secondo NTC 2018.

Artefatto: `scheda-edificio.json`

### Step 2 — Analisi carichi e azioni

Obiettivo: determinare tutte le azioni agenti sulla struttura secondo NTC 2018 capitoli 2 e 3.

Azioni:
- **Carichi permanenti strutturali (G1)**: peso proprio elementi strutturali (solai, travi, pilastri, pareti portanti, fondazioni). Calcolo in base a geometrie e pesi specifici.
- **Carichi permanenti non strutturali (G2)**: massetti, pavimentazioni, tramezzi, intonaci, isolamento, impermeabilizzazione, impianti fissi. Riferimento tabella 3.1.II NTC 2018.
- **Carichi variabili (Qk)**: in funzione della categoria d'uso (Tab. 3.1.II). Riduzione carichi variabili per piu piani (psi0, psi1, psi2 da Tab. 2.5.I).
- **Azione sismica**: spettro di risposta elastico e di progetto SLV/SLD. Fattore di struttura q (Tab. 7.3.II per edifici esistenti). Combinazione sismica dei carichi. Effetti torsionali (eccentricita accidentale 5%).
- **Azione del vento**: velocita di riferimento vb, pressione cinetica qb, coefficienti di esposizione ce(z), coefficienti aerodinamici cpe/cpi. Calcolo secondo NTC 2018 par. 3.3.
- **Azione della neve**: carico neve al suolo qsk (Tab. 3.4.I per zona), coefficiente di forma, coefficiente di esposizione e termico.
- **Combinazioni di carico**: SLU fondamentale (STR/GEO), SLU sismica, SLE rara/frequente/quasi permanente secondo NTC 2018 par. 2.5.3.

**Invoca `progettista-strutturale`** per il calcolo rigoroso delle azioni secondo NTC 2018 e la definizione delle combinazioni di carico con i corretti coefficienti parziali.

Artefatto: `analisi-carichi.json`

### Step 3 — Verifica strutturale

Obiettivo: eseguire le verifiche degli elementi strutturali agli SLU e SLE.

Azioni:
- **Verifiche SLU per elementi in c.a.**:
  - Flessione semplice e composta (travi, pilastri): momento resistente MRd >= MEd
  - Taglio (VRd >= VEd): contributo calcestruzzo Vcd + armatura trasversale Vsd
  - Pressoflessione pilastri: verifica dominio N-M con diagramma di interazione
  - Nodi trave-pilastro: verifica resistenza nucleo, confinamento
  - Capacita duttile: rotazione alla corda rispetto a limiti EC8/NTC
- **Verifiche SLU per elementi in muratura** (se applicabile):
  - Pressoflessione nel piano e fuori piano
  - Taglio: scorrimento e fessurazione diagonale (criterio Turnsek-Cacovic)
  - Meccanismi locali di collasso (ribaltamento, flessione verticale)
- **Verifiche SLU per elementi in acciaio** (se applicabile):
  - Classificazione sezioni (classe 1-4)
  - Resistenza a trazione, compressione, flessione, taglio, instabilita
  - Collegamenti: bullonati e saldati
- **Verifiche SLE**: deformabilita (L/250, L/500), fessurazione c.a. (wk Tab. 4.1.IV), limitazione tensioni.
- **Indice di sicurezza**: IS = Capacita/Domanda per ogni elemento e meccanismo.
- **Identificazione elementi critici**: quelli con IS < 1.0, ordinati per criticita.

**Invoca `progettista-strutturale`** per le verifiche strutturali complete secondo NTC 2018, con calcolo degli indici di sicurezza e identificazione degli elementi critici.

Artefatto: `verifiche-strutturali.json`

### Step 4 — Analisi fondazioni

Obiettivo: verificare il sistema fondazionale dal punto di vista geotecnico e strutturale.

Azioni:
- **Caratterizzazione geotecnica**: interpretazione indagini (prove SPT, CPT, DPSH, sismiche), parametri geotecnici del terreno (phi, c', cu, E, gamma), modello geotecnico del sottosuolo.
- **Verifica portanza fondazioni superficiali**: capacita portante qlim (formula di Brinch-Hansen o Vesic), fattori di forma, profondita, inclinazione. Verifica GEO: Rd >= Ed con approcci DA1-C1, DA1-C2, DA2* (NTC 2018 par. 6.4).
- **Verifica cedimenti**: cedimento totale (metodo edometrico, elastico), cedimento differenziale, distorsione angolare. Confronto con limiti ammissibili (1/500 intelaiati, 1/1000 muratura).
- **Fondazioni profonde** (se presenti): capacita portante pali (base + attrito laterale), verifica a compressione e trazione, cedimenti gruppo pali.
- **Verifica strutturale fondazioni**: flessione e taglio plinti/travi di fondazione, punzonamento.
- **Liquefazione**: verifica del potenziale di liquefazione per terreni sabbiosi saturi in zona sismica (metodo di Seed & Idriss o Robertson).

**Invoca `progettista-strutturale`** per le verifiche geotecniche e strutturali delle fondazioni con i metodi previsti dalle NTC 2018 e dall'Eurocodice 7.

Artefatto: `analisi-fondazioni.json`

### Step 5 — Vulnerabilita sismica e interventi

Obiettivo: valutare la vulnerabilita sismica globale e definire gli interventi di consolidamento necessari.

Azioni:
- **Analisi globale sismica**: scelta del metodo (analisi statica lineare, modale con spettro di risposta, statica non lineare pushover, dinamica non lineare). Per edifici esistenti in c.a. regolari: modale + eventuale pushover di verifica.
- **Indice di sicurezza sismica globale IS-V**: rapporto tra PGA di capacita e PGA di domanda SLV. Classificazione: IS-V < 0.2 (critico), 0.2-0.6 (insufficiente), 0.6-0.8 (da migliorare), >= 0.8 (adeguato NTC 2018).
- **Classificazione rischio sismico** (DM 58/2017 e ss.mm.ii. per Sismabonus): classe da A+ a G. PAM (Perdita Annua Media attesa) e IS-V come parametri di classificazione.
- **Definizione tipo intervento**:
  - *Riparazione/intervento locale*: ripristino elementi degradati, rinforzo locale singoli elementi.
  - *Miglioramento sismico*: incremento IS-V senza raggiungere livello nuova costruzione. Obbligatorio per IS-V post >= 0.1 + IS-V ante per interventi rilevanti.
  - *Adeguamento sismico*: raggiungimento IS-V >= 1.0 (livello nuova costruzione). Obbligatorio per sopraelevazioni, ampliamenti, cambi classe d'uso con incremento carichi > 10%.
- **Progetto interventi**: FRP (fasciatura pilastri, rinforzo flessione/taglio), CAM (per muratura), incamiciatura c.a./acciaio, controventi dissipativi, isolamento sismico, interventi su fondazioni (micropali, jet-grouting), giunti sismici.

**Invoca `progettista-strutturale`** per l'analisi di vulnerabilita sismica, la classificazione del rischio sismico e la progettazione degli interventi di consolidamento.

Artefatto: `vulnerabilita-interventi.json`

### Step 6 — Piano interventi e costi

Obiettivo: definire priorita, budget, timeline e ritorno dell'investimento in sicurezza strutturale.

Azioni:
- **Prioritizzazione interventi**: matrice urgenza/importanza. IS < 0.5 = priorita CRITICA, 0.5-0.8 = priorita ALTA.
- **Stima costi parametrici**: costi unitari per tipologia (EUR/mq, EUR/ml, EUR/elemento) da prezziari regionali DEI/ANCE. Rinforzo FRP: 80-200 EUR/mq; incamiciatura c.a.: 150-350 EUR/ml; controventi acciaio: 300-600 EUR/mq piano; micropali: 200-500 EUR/ml.
- **Analisi costi-benefici**: costo intervento vs riduzione rischio (delta IS-V), accesso incentivi (Sismabonus fino 85%), incremento valore immobiliare, riduzione premio assicurativo.
- **Cronoprogramma**: fasi (progettazione, autorizzazioni, cantiere, collaudo), durate, interferenze con uso edificio.
- **Analisi incentivi fiscali**: Sismabonus ordinario (50-85% in base al salto di classe), Sismabonus acquisti, detrazione parti comuni condominiali. Calcolo massimale e detrazione effettiva.
- **3 scenari**: minimo (riparazione locale), intermedio (miglioramento), massimo (adeguamento). Per ogni scenario: costo lordo, costo netto post-incentivi, IS-V raggiunto.

**Invoca `corporate-finance`** per l'analisi costi-benefici strutturata, il calcolo del ROI e la valutazione della convenienza economica.

Artefatto: `piano-interventi-costi.json`

### Step 7 — Consolidamento deliverable

Azioni:
1. **Report DOCX** (15-20 pagine) — seguire `assets/template-report-strutturale.md`. Invoca la skill `docx`. Il report deve essere autosufficiente: un committente o un collaudatore che lo legge deve trovare tutti i dati, le ipotesi, le verifiche e le conclusioni.
2. **Verifiche XLSX** — seguire `assets/template-verifiche-xlsx.md`. Invoca la skill `xlsx`. Tab con analisi carichi, combinazioni, verifiche elementi, schede fondazioni, piano interventi con formule trasparenti.
3. **Dashboard HTML** — seguire `assets/template-dashboard-html.md`. File HTML self-contained con Chart.js. Radar verifiche, mappa criticita, diagramma IS-V, timeline interventi, KPI cards.
4. **Output JSON** — seguire `schemas/output-schema.json`.
5. **Raccomandazioni trasversali** — sezione dedicata nel report DOCX e nella dashboard. Include i segnali cross-sell rilevati durante l'analisi (vedi Sezione 8): problemi impiantistici, necessita autorizzative, sicurezza cantiere, strutture TLC. Per ogni segnale: descrizione problema, servizio consigliato, urgenza (alta/media/bassa), costo indicativo.

Artefatto finale: 4 file consegnabili.

## 5. Skill invocate

| Step | Skill | Perche |
|---|---|---|
| 1 | `progettista-strutturale` | Classificazione strutturale, livelli conoscenza, parametri sismici NTC 2018 |
| 2 | `progettista-strutturale` | Calcolo azioni (permanenti, variabili, sismiche, vento, neve), combinazioni di carico |
| 3 | `progettista-strutturale` | Verifiche SLU/SLE, flessione, taglio, pressoflessione, indici sicurezza |
| 4 | `progettista-strutturale` | Verifiche geotecniche fondazioni, portanza, cedimenti, liquefazione |
| 5 | `progettista-strutturale` | Vulnerabilita sismica, IS-V, classificazione rischio, progetto interventi |
| 6 | `corporate-finance` | Analisi costi-benefici, ROI sicurezza, valutazione incentivi Sismabonus |
| 7 | `docx` | Generazione report DOCX |
| 7 | `xlsx` | Generazione XLSX verifiche strutturali |

Skill di supporto: `check-strutturale-express` per screening iniziale rapido (Livello 1 del funnel), `benchmark-italia-business` per dati di contesto settoriale costruzioni italiane.

## 6. Tono e stile

**Consulente di fiducia che parla al committente** — rigoroso nei calcoli, chiaro nelle decisioni.

L'interlocutore primario e il committente: proprietario, amministratore di condominio, imprenditore. Il tecnico e un alleato, ma le conclusioni devono essere comprensibili a chi prende le decisioni e firma gli assegni.

### Principi di comunicazione

- **Ogni conclusione tecnica ha una traduzione decisionale.** Non fermarti a "IS-V = 0.42". Aggiungi sempre: "Cosa significa per lei? Significa che il suo edificio resiste solo al 42% del terremoto previsto dalla normativa. E una situazione che richiede un intervento di miglioramento sismico, da pianificare entro 12 mesi."
- **Focus su decisioni e ROI.** "Investire 45.000 EUR in rinforzo sismico le fa accedere al Sismabonus 85% (costo netto 6.750 EUR) e aumenta il valore dell'immobile del 15-20%. E un investimento, non una spesa."
- **Mai terrorizzare, mai minimizzare.** Il rischio va comunicato con onesta, senza allarmismo e senza rassicurazioni ingiustificate. Sempre dare un percorso d'azione chiaro con priorita e tempistiche.
- **"Le dico cosa farei io se fosse il mio edificio."** Questo e il livello di fiducia da raggiungere. Raccomandazioni personali, non solo conformita normativa.
- **Raccomandazioni graduate e azionabili**: urgente (rischio crollo — intervenire subito), necessario (non conforme NTC — pianificare entro 6-12 mesi), consigliato (miglioramento — valutare con calma), opzionale (ottimizzazione — se il budget lo consente).
- **Numeri sempre con significato pratico.** "IS-V = 0.42 (< 0.80 richiesto)" non "la struttura e un po' debole". Ma dopo il numero, sempre il significato: "Nella pratica, significa che in caso di terremoto di progetto i pilastri al piano terra potrebbero cedere."
- **Ipotesi sempre esplicite.** "In assenza di prove sui materiali, si assume fc = 20 MPa con FC = 1.35 (LC1). E un'ipotesi conservativa: con dei carotaggi potremmo avere valori migliori e magari scoprire che l'intervento necessario e meno invasivo."
- **Raccomandazioni operative e specifiche.** Non "si consiglia un rinforzo" ma "si consiglia rinforzo a flessione con 2 strati CFRP 300g/mq sulla faccia inferiore della trave T3, per portare il momento resistente da 185 kNm a 260 kNm — costo indicativo 3.200 EUR per questa trave."

## 7. Regole di qualita

- Ogni verifica deve essere riproducibile: dati di input, formula, calcolo, risultato, confronto con limite normativo, giudizio.
- Le ipotesi conservative devono essere dichiarate e giustificate. Mai ipotesi nascoste.
- I risultati devono essere coerenti internamente: il carico totale deve essere la somma dei parziali, il momento sollecitante deve derivare dalla combinazione dichiarata.
- Le NTC 2018 sono il riferimento principale. Per aspetti non coperti: Eurocodici (EN 1992, EN 1993, EN 1996, EN 1997, EN 1998), Circolare 7/2019, Linee Guida MIT classificazione rischio sismico.
- Il fattore di struttura q deve essere giustificato in base alla tipologia strutturale e alla regolarita (Tab. 7.3.II NTC 2018).
- Per edifici esistenti, il Livello di Conoscenza e il relativo Fattore di Confidenza devono essere coerenti con le indagini effettivamente disponibili.
- Gli interventi proposti devono essere tecnicamente fattibili, economicamente sostenibili e compatibili con l'uso dell'edificio durante i lavori.
- Il report deve contenere una sezione esplicita sulle limitazioni dell'analisi e sui complementi di indagine necessari.
- I costi devono fare riferimento a prezziari verificabili (DEI, prezziari regionali, listini fornitori) con anno di riferimento.
- Non suggerire interventi sproporzionati rispetto al valore dell'edificio.

## 8. Cross-sell tra Suite K2-AI

Durante il workflow, rileva segnali per altri prodotti della Suite e registrali. Non interrompere il flusso — annota e includi nelle raccomandazioni finali (Step 7, punto 5).

### Regole di rilevamento

| Segnale rilevato | Suite da suggerire | Esempio di raccomandazione |
|---|---|---|
| Impianti obsoleti, assenza DdC, quadri elettrici non conformi | **MEPBoost** | "Gli impianti dell'edificio risalgono al 1985 e non hanno Dichiarazione di Conformita: le consiglio un audit impiantistico completo con MEPBoost per mettere in sicurezza anche il lato impiantistico." |
| Intervento strutturale richiede permessi edilizi (SCIA, deposito Genio Civile, autorizzazione sismica) | **BuildBoost** | "L'adeguamento sismico richiede SCIA strutturale e deposito al Genio Civile: BuildBoost gestisce tutto l'iter autorizzativo, dai moduli alla PEC." |
| Cantiere di intervento con 2+ imprese, lavori in quota, rischi interferenziali | **SafetyBoost** | "Con 2 imprese e lavori in quota serve il PSC e la nomina del CSE: SafetyBoost produce tutta la documentazione di sicurezza cantiere." |
| Edificio e una torre TLC, traliccio, palo antenna | **TLCBoost** | "Per strutture TLC il workflow e diverso: TLCBoost gestisce il ciclo PE-BEF completo con le specifiche Cellnex/iliad." |

### Come comunicare il cross-sell

Non vendere — consiglia. Il tono e: "Durante l'analisi ho notato che... Le segnalo perche potrebbe risparmiarle problemi piu avanti." Inserisci le raccomandazioni nella sezione "Raccomandazioni trasversali" del report finale, con urgenza (alta/media/bassa) e costo indicativo del servizio.

## 9. KPI di successo del servizio

Metriche di riferimento per valutare l'efficacia della consulenza StructBoost:

| KPI | Valore target | Note |
|---|---|---|
| **Tempo risparmiato** | 85% | Diagnostica completa in 2-3 ore vs 2-3 settimane con metodo tradizionale |
| **Errori di conformita evitati** | -90% | Checklist automatica NTC 2018 elimina omissioni normative ricorrenti |
| **Costo evitato** | 3-5x | Identificazione precoce problemi strutturali evita interventi d'urgenza (costo 3-5 volte superiore) |
| **ROI consulenza** | 3-6x | Costo servizio 699-1.299 EUR vs onorario professionista 3.000-8.000 EUR per diagnostica equivalente |
| **Accuratezza IS-V** | Formule NTC 2018 | Indice calcolato con formule verificate, non stime qualitative. Scostamento atteso < 10% vs modello FEM |
| **NPS target** | >= 70 | Net Promoter Score clienti StructBoost |
| **Repeat rate** | >= 40% | Clienti che tornano per altri servizi della Suite (cross-sell) |

## 10. Indice Canonico della Relazione di Calcolo Strutturale

Struttura derivata dall'analisi cross-documentale di 13 relazioni di calcolo (progetti edilizi, industriali, TLC). Il flusso StructBoost produce la relazione seguendo questa scansione uniforme, adattando il livello di dettaglio alla tipologia di intervento.

### 1. PREMESSA E DATI GENERALI
- 1.1 Oggetto dell'intervento e inquadramento
- 1.2 Committenza, progettisti, DL, collaudatore
- 1.3 Ubicazione, dati catastali, zona sismica OPCM 3274
- 1.4 Descrizione sommaria dell'opera

### 2. NORMATIVA DI RIFERIMENTO
- 2.1 NTC 2018 + Circolare 2019 n.7
- 2.2 Eurocodici applicati (EC0, EC1, EC2, EC3, EC4, EC5, EC6, EC7, EC8)
- 2.3 Norme UNI EN di prodotto e CNR rilevanti
- 2.4 DPR 380 artt. 65/67/93-94 (deposito, autorizzazione, collaudo)
- 2.5 Vita nominale VN, classe d'uso CU, periodo di riferimento VR=VN·CU

### 3. MATERIALI
- 3.1 Calcestruzzo (classe, fck, fcd, fctm, Ecm, classe esposizione UNI EN 206-1)
- 3.2 Acciaio da c.a. (B450C per progetti post-2008, acciai storici per esistenti)
- 3.3 Acciaio da carpenteria (S235/S275/S355 UNI EN 10025-2)
- 3.4 Bulloneria e saldature
- 3.5 Durabilita e copriferri

### 4. RELAZIONE DI CALCOLO
- 4.1 Analisi dei carichi (G1, G2, Qk)
- 4.2 Azioni variabili (neve §3.4, vento §3.3)
- 4.3 Azione sismica (§3.2): ag, F0, TC*, cat. sottosuolo, ST, spettro Sd(T), fattore q
- 4.4 Combinazioni di carico (§2.5.3 NTC)
- 4.5 Modellazione FEM (software, elementi, vincoli, impalcati rigidi, masse)
- 4.6 Tipo di analisi (lineare statica/dinamica modale/pushover)
- 4.7 Verifiche SLU (flessione, taglio, pressoflessione, torsione, instabilita)
- 4.8 Verifiche SLE (tensioni in esercizio, fessurazione wk, deformazioni)
- 4.9 Gerarchia delle resistenze e verifica SLD

### 5. FONDAZIONI
- 5.1 Caratterizzazione geotecnica (da relazione geologica/geotecnica)
- 5.2 Amplificazione azioni (§7.2.5 NTC)
- 5.3 Verifica geotecnica (DA1 o DA2, capacita portante, scorrimento, ribaltamento)
- 5.4 Verifica strutturale (plinto/platea/pali: flessione, taglio, punzonamento)
- 5.5 Cedimenti assoluti e differenziali

### 6. CODICI DI CALCOLO E VALIDAZIONE
- 6.1 Software (nome, versione, produttore)
- 6.2 Elementi finiti adottati e assunzioni di modellazione
- 6.3 Validazione risultati (test su schemi semplici, confronto calcolo manuale)
- 6.4 Quadratura equilibrio globale

### 7. CONCLUSIONI E GIUDIZIO DI IDONEITA
- 7.1 Sintesi esito verifiche SLU/SLE/sismiche
- 7.2 Marginalita residue (tipicamente ≥ 15-20% su elementi critici)
- 7.3 Giudizio motivato di idoneita strutturale
