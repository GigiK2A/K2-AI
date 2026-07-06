---
name: contabilita-bilancio
description: "BILANCIO E CONTABILITA ITALIANA - Contabilità generale, bilanci d'esercizio, principi OIC/IAS-IFRS, partita doppia, analisi di bilancio, revisione contabile per commercialisti, controller, CFO. Usa SEMPRE per: partita doppia dare avere, libro giornale mastro, CO.GE., IVA liquidazione, ciclo acquisti vendite anticipi resi sconti, busta paga contributi INPS IRPEF, TFR rivalutazione imposta sostitutiva 17%, fondi rischi oneri accantonamento, ammortamento civilistico fiscale, scritture assestamento ratei risconti rimanenze, IRES imposte differite anticipate riversamento, RAI RI variazioni permanenti temporanee, bilancio SP CE rendiconto finanziario nota integrativa, OIC IAS IFRS, clausole generali art. 2423, principi prudenza competenza continuità, schemi civilistici bilancio abbreviato micro, revisione contabile, analisi ROE ROI ROS leverage, bilancio consolidato."
---

# Contabilità e Bilancio Italiano — Manuale Operativo

## Architettura della Skill

Questa skill copre l'intero ciclo contabile e di bilancio italiano, dalla partita doppia alla redazione e analisi del bilancio d'esercizio. I contenuti di dettaglio sono organizzati in **5 reference files tematici**.

## Routing — Quale reference file consultare

| Domanda / Tema | Reference file |
|---|---|
| CO.GE., partita doppia, dare/avere, conti bifase/monofase, ciclo bilancio 6 fasi, tipologie valori (certi/stimati/congetturati), piano dei conti, libro giornale, scritture contabili obbligatorie, costituzione società, efficacia probatoria scritture | `references/sistema-contabile-partita-doppia.md` |
| IVA (meccanismo, aliquote, liquidazione), ciclo acquisti (fatture, anticipi fornitori, resi, abbuoni, sconti incondizionati/condizionati/cassa), ciclo vendite (speculare), costo del lavoro (busta paga, contributi INPS, ritenute IRPEF, TFR scritture), finanziamento corrente (banca c/c, fido, cambiali, sconto cambiario pro-soluto/pro-solvendo), acquisto/cessione immobilizzazioni, plusvalenze/minusvalenze | `references/scritture-esercizio.md` |
| Fondi per rischi e oneri (classificazione 4 criteri, condizioni iscrizione OIC 31), distinzione fondi rischi/fondi oneri/debiti, TFR (calcolo completo: quota capitale, rivalutazione ISTAT, imposta sostitutiva 17%, destinazione post-riforma 2007), scritture di assestamento (ammortamenti, svalutazione crediti, ratei, risconti, rimanenze) | `references/fondi-rischi-oneri-tfr.md` |
| IRES 24%, dal RAI al RI, variazioni fiscali in aumento/diminuzione, differenze permanenti vs temporanee (positive e negative), imposte differite (fondo SP passivo B.2), imposte anticipate (credito SP attivo C.II.5-ter), riversamenti, formula imposte di competenza, plusvalenza rateizzata art. 86 TUIR, ammortamento civilistico vs fiscale coefficienti ministeriali, esercizi completi con scritture | `references/imposte-reddito-fiscalita-differita.md` |
| Tipologie bilancio (5 tipi), fonti diritto contabile (c.c./OIC vs Reg. UE/IFRS), D.Lgs. 38/2005 destinatari, funzioni bilancio, clausole generali nazionali art. 2423 (chiarezza, veridicità, correttezza, deroga obbligatoria, materialità), clausole internazionali IAS 1, principi generali (continuità, prudenza/dissimmetria, competenza, sostanza su forma, costanza criteri), schemi SP/CE civilistici, bilancio abbreviato/micro, nota integrativa art. 2427, rendiconto finanziario OIC 10, approvazione e deposito | `references/bilancio-diritto-contabile.md` |

## Istruzioni Operative

1. **Identifica il tema** dalla domanda dell'utente usando la tabella di routing
2. **Leggi il reference file** appropriato con il tool Read
3. **Per domande trasversali** (es. "fammi il bilancio completo"), consulta più reference file
4. **Per scritture contabili**: usa sempre il formato tabellare Dare/Avere con importi numerici
5. **Per esercizi d'esame**: mostra il calcolo step-by-step, le scritture e la verifica finale
6. **Per confronti OIC/IFRS**: evidenzia le differenze operative e il diverso posizionamento in bilancio

## Risorse Normative di Riferimento

- Codice Civile: artt. 2082-2083 (imprenditore), 2214-2220 (scritture contabili), 2423-2435-ter (bilancio)
- D.Lgs. 38/2005 (adozione IAS/IFRS in Italia)
- D.Lgs. 139/2015 (recepimento Direttiva 34/2013/UE — riforma bilanci)
- D.Lgs. 39/2010 (revisione legale dei conti)
- D.Lgs. 127/1991 (bilancio consolidato nazionale)
- TUIR D.P.R. 917/1986: art. 83 (derivazione rafforzata), art. 86 (plusvalenze), art. 102 (ammortamenti)
- Principi contabili OIC 1-35
- IAS/IFRS (IASB): IAS 1, 2, 12, 16, 36, 37, 38; IFRS 3, 9, 10, 15, 16

## Quick Reference — Analisi di Bilancio

### Redditività
- **ROE** = Utile Netto / Patrimonio Netto (redditività per l'azionista)
- **ROI** = EBIT / Capitale Investito (efficienza operativa)
- **ROS** = EBIT / Ricavi (marginalità sulle vendite)

### Solidità
- **Leverage** = Debiti / Patrimonio Netto (equilibrio finanziario; < 1 prudenziale)
- **Indice di autonomia** = PN / Attivo Totale (> 40% prudenziale)

### Liquidità
- **Current Ratio** = Attivo Circolante / Passivo Circolante (ideale 1,5-2,0)
- **Quick Ratio** = (Attivo Circolante - Rimanenze) / Passivo Circolante (ideale 1,0-1,5)

### Ciclo Monetario
- **GG credito** = (Crediti Clienti / Ricavi) × 365
- **GG magazzino** = (Rimanenze / Costo Venduto) × 365
- **GG debito** = (Debiti Fornitori / Acquisti) × 365
- **Ciclo netto** = GG credito + GG magazzino - GG debito

## Quick Reference — Bilancio Consolidato

### Area di Consolidamento
- **Controllo** (> 50%): metodo integrale — aggregazione linea per linea
- **Influenza significativa** (20-50%): metodo del patrimonio netto
- **Partecipazione passiva** (< 20%): fair value

### Eliminazioni Infragruppo
- Crediti/debiti reciproci
- Utili su vendite infragruppo non realizzati verso terzi
- Dividendi intragruppo
- Goodwill = prezzo pagato - valore netto acquisito

## Quick Reference — Revisione Contabile (D.Lgs. 39/2010)

| Giudizio del revisore | Significato |
|---|---|
| Senza riserve | Bilancio attendibile — caso ideale |
| Con riserve | Attendibile salvo eccezioni circoscritte |
| Negativo | Bilancio non attendibile |
| Impossibilità di esprimere opinione | Dati critici mancanti |

## Checklist Operativa — Chiusura d'Esercizio

1. Verificare competenza economica di tutti i ricavi e costi
2. Completare ammortamenti (tabella beni e scadenze)
3. Svalutare crediti dubbi (fondo svalutazione)
4. Inventario fisico merci e riconciliazione con contabilità
5. Accantonare a fondi rischi per passività probabili
6. Quantificare ratei e risconti
7. Calcolare TFR (quota capitale + rivalutazione - imposta sostitutiva)
8. Determinare imposte correnti, differite e anticipate
9. Verificare consolidamento e eliminazioni infragruppo (se controllate)
10. Calcolare indicatori di bilancio (ROE, ROI, liquidità, leverage)
11. Redigere Nota Integrativa e Rendiconto Finanziario
12. Coordinare con revisore per relazione
