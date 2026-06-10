---
name: ai-archive-templates-engineering
description: Skill settoriale per skillizzazione dell'archivio di studi di ingegneria italiani — fornisce template ready-to-use per i 30-50 tipi di documento tipici del settore. Relazioni di sopralluogo, capitolati, computi metrici, calcoli strutturali, PSC, fascicoli, PE TLC iliad e Cellnex, relazioni paesaggistiche, SAL, verbali, schede tecniche. Usa SEMPRE quando ai-knowledge-skillization-studio è attivata per studio di ingegneria, oppure quando il cliente ingegnere dice skill per relazioni sopralluogo, template capitolato MEP, skill PE iliad, template computo metrico, skill relazione strutturale, skill PSC cantiere, knowledge codification ingegneria. Differenziati per 8 sub-specializzazioni — civile, strutturale, MEP, TLC, sicurezza, DL, paesaggistico-monumentale, energetico. Si combina con skill tecniche K2-AI esistenti (progettista-strutturale, impianti-elettrici, psc-coordinamento). NON usare per altri settori, per implementazione tool senza skillization.
---








<!-- LEGAL-EVIDENCE-BLOCK-V7 -->
## Tools Normattiva + Giurisprudenza (CCost + CGUE + CEDU + CdS/TAR + Cassazione) — verifica obbligatoria

Hai 5 toolkit locali + 1 lookup live per consulenza legale evidence-based:
- **Normattiva** — ~42.000 norme italiane (DB FTS5)
- **Corte Costituzionale** — 22.258 pronunce + 46.154 massime (1956→2026)
- **Corte di Giustizia UE + Tribunale UE** — ~38.000 cause (2005→2026)
- **Corte EDU (Strasburgo)** — 10.000 casi contro l'Italia (2001→2026), con traduzioni ufficiali Min. Giustizia
- **Giustizia Amministrativa** — Consiglio di Stato + TAR + CGARS (2024→2025, in espansione)
- **Cassazione (LIVE pubblica)** — SentenzeWeb italgiure, accesso pubblico zero-setup (~188k civ + ~236k pen, testo integrale)

### Workflow obbligatorio

**A. Norme italiane**
```bash
python3 ~/normattiva_ai/tools/cita.py "<es. D.Lgs 81/2008>"
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia lavoro --limit 5
```

**B. Corte Costituzionale**
```bash
python3 ~/giurisprudenza_ai/tools/cross_norma_sentenza.py "art. 32 Cost." --limit 10
python3 ~/giurisprudenza_ai/tools/rag_giurisprudenza.py "<query>" --anno-da 2018
python3 ~/giurisprudenza_ai/tools/cita_sentenza.py "Corte cost. N/AAAA"
```

**C. CGUE (diritto UE / GDPR / appalti / antitrust / privacy / dogana)**
```bash
python3 ~/cgue_ai/tools/cross_norma_cgue.py "art. 101 TFUE" --limit 10
python3 ~/cgue_ai/tools/cross_norma_cgue.py "Reg. UE 679/2016"        # GDPR
python3 ~/cgue_ai/tools/rag_cgue.py "<query>" --anno-da 2018
python3 ~/cgue_ai/tools/cita_cgue.py "C-16/05"
```

**D. CEDU (diritti fondamentali / equo processo art. 6 / detenzione art. 3 / proprietà P1-1 / vita privata art. 8)**
```bash
python3 ~/cedu_ai/tools/cross_articolo_cedu.py "art. 6" --solo-importanti --limit 10
python3 ~/cedu_ai/tools/rag_cedu.py "<query>" --anno-da 2015
python3 ~/cedu_ai/tools/cita_cedu.py "63386/16"      # numero di ricorso
```

**E. Giustizia Amministrativa — CdS/TAR (appalti, edilizia, accesso atti, SCIA, silenzio, espropri, PA)**
```bash
python3 ~/gad_ai/tools/cross_norma_gad.py "D.Lgs 36/2023" --limit 10   # appalti
python3 ~/gad_ai/tools/cross_norma_gad.py "Legge 241/1990"             # procedimento
python3 ~/gad_ai/tools/rag_gad.py "<query>" --sede cds --anno-da 2024
```

**F. Cassazione (LIVE pubblica — civile/penale, legittimità) — zero setup**
```bash
# Verifica/recupera un precedente di Cassazione (SentenzeWeb pubblico, nessun login)
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023"
python3 ~/cassazione_ai/tools/cassazione_lookup.py --q "licenziamento giusta causa" --sezione civ --rows 5
python3 ~/cassazione_ai/tools/cassazione_lookup.py --cit "Cass. civ. 12345/2023" --full   # testo integrale
python3 ~/cassazione_ai/tools/check_cassazione.py --file <output.md>                        # verifica citazioni
```
Copre la finestra pubblica (~ultimi 5 anni + storico parziale). Se una citazione MANCA può essere fuori finestra; dillo, non inventare la massima.

**G. Verifica finale (prima del deliverable, su ogni file MD prodotto)**
```bash
python3 ~/normattiva_ai/tools/check_citazioni.py --file <output.md> --strict
python3 ~/giurisprudenza_ai/tools/check_sentenze.py --file <output.md> --strict
python3 ~/cgue_ai/tools/check_cgue.py --file <output.md> --strict
python3 ~/cedu_ai/tools/check_cedu.py --file <output.md> --strict
python3 ~/gad_ai/tools/check_gad.py --file <output.md> --strict
```

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/lavoro/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# ai-archive-templates-engineering — Template skill settoriali per studi di ingegneria

## 1. Cosa fa questa skill

Questa skill è il **complemento operativo** di `ai-knowledge-skillization-studio` per il settore ingegneria. Mentre quella skill fornisce **metodologia trasversale** di skillizzazione, questa fornisce **template ready-to-use** per le tipologie documentali tipiche di uno studio di ingegneria italiano.

### Il valore concreto

Senza questa skill, ogni progetto di skillizzazione per studio di ingegneria deve partire **da zero** sull'analisi delle tipologie documentali. Con questa skill, K2-AI parte da:
- 50+ template pre-strutturati per i documenti tipici del settore
- Differenziazione per 8 sub-specializzazioni (civile, strutturale, MEP, TLC, sicurezza, DL, paesaggistico, energetico)
- Esempi compilativi
- Knowledge settoriale già codificata

Risultato: tempo di costruzione del primo batch di skill scende del 50-60%, qualità sale del 30-40% (perché i pattern settoriali sono già rodati).

### Come si usa

In una sessione di skillizzazione di uno studio di ingegneria:

1. **Discovery dell'archivio specifico**: mappa archivio del cliente
2. **Matching con template di questa skill**: identifica quali template sono applicabili
3. **Personalizzazione**: ogni template viene adattato sui pattern dello studio specifico (esempi reali, criteri del titolare, riferimenti normativi)
4. **Completamento**: per documenti unici dello studio, costruzione skill custom da zero
5. **Deployment**: skill personalizzate caricate nell'infrastruttura del cliente

---

## 2. Quando attivarsi

### Trigger
- Skillization in corso per studio di ingegneria
- "Template skill ingegneria"
- "Skill relazione sopralluogo civile"
- "Skill capitolato MEP"
- "Skill computo metrico"
- "Skill PSC cantiere"
- "Skill PE TLC iliad/Cellnex"
- "Skill verifica statica"

### Quando NON attivarsi
- Skillization per altri settori (vai a `ai-archive-templates-{settore}`)
- Generica AI assessment senza skillization (vai a `ai-assessment-studio`)
- Implementazione tool senza skillization (vai a `ai-implementazione-pilota`)

---

## 3. Tassonomia dei template per sub-specializzazione

I template sono organizzati in **8 sub-specializzazioni** che rispecchiano la struttura tipica degli studi di ingegneria italiani.

### Sub-specializzazione 1 — Ingegneria Civile (edilizia)

Documenti tipici di studio civile:

**Field Operations** (sopralluoghi):
- skill-relazione-sopralluogo-civile-edilizia
- skill-rilievo-fotografico-classificato
- skill-scheda-rilievo-edificio-esistente
- skill-rilievo-degrado-facciata
- skill-rilievo-strutture-portanti

**Document Production** (progettazione):
- skill-relazione-tecnica-illustrativa
- skill-relazione-paesaggistica-base
- skill-disciplinare-descrittivo
- skill-capitolato-speciale-appalto-civile
- skill-elenco-prezzi-unitari
- skill-computo-metrico-estimativo-civile
- skill-quadro-economico-progetto

**Project Management** (DL e cantiere):
- skill-verbale-consegna-lavori
- skill-verbale-sospensione-ripresa
- skill-ordine-servizio-impresa
- skill-stato-avanzamento-lavori-SAL
- skill-libretto-misure
- skill-registro-contabilita
- skill-certificato-pagamento
- skill-conto-finale-relazione
- skill-CRE-certificato-regolare-esecuzione

### Sub-specializzazione 2 — Ingegneria Strutturale

Documenti tipici di studio strutturale:

**Calcoli e verifiche**:
- skill-relazione-calcolo-CA-armato-NTC
- skill-relazione-calcolo-acciaio-NTC
- skill-relazione-calcolo-legno-NTC
- skill-relazione-calcolo-muratura-NTC
- skill-analisi-modale-strutture
- skill-analisi-pushover
- skill-analisi-tempo-storia
- skill-verifica-statica-edificio-esistente
- skill-verifica-vulnerabilita-sismica
- skill-classificazione-sismica-edificio

**Fondazioni**:
- skill-relazione-geotecnica
- skill-calcolo-fondazione-superficiale
- skill-calcolo-fondazione-pali
- skill-calcolo-paratie-muri
- skill-verifica-cedimenti

**Interventi su esistente**:
- skill-relazione-rinforzo-FRP
- skill-relazione-incamiciatura-CA
- skill-relazione-CAM-cuciture-armate
- skill-piano-interventi-strutturali

**Documentazione di deposito**:
- skill-deposito-strutturale-genio-civile
- skill-collaudo-statico
- skill-fascicolo-strutturale

### Sub-specializzazione 3 — Ingegneria MEP (Mechanical, Electrical, Plumbing)

**Impianti elettrici**:
- skill-progetto-elettrico-civile
- skill-progetto-elettrico-industriale
- skill-progetto-cabina-MT-BT
- skill-progetto-impianto-fotovoltaico
- skill-relazione-tecnica-CEI-37-08
- skill-schemi-elettrici-unifilari
- skill-calcolo-illuminotecnico
- skill-progetto-impianto-terra
- skill-progetto-LPS-protezione-fulmini
- skill-DICO-dichiarazione-conformita

**Impianti termici e HVAC**:
- skill-progetto-impianto-termico-residenziale
- skill-progetto-VRF-uffici
- skill-progetto-VMC-meccanica-controllata
- skill-progetto-pannelli-radianti
- skill-progetto-pompa-calore
- skill-progetto-solare-termico
- skill-relazione-energetica-Legge-10
- skill-relazione-isolamento-acustico
- skill-bilanciamento-impianti-idronici

**Impianti speciali**:
- skill-progetto-rilevazione-incendio
- skill-progetto-spegnimento-automatico
- skill-progetto-EVAC-evacuazione
- skill-progetto-TVCC-videosorveglianza
- skill-progetto-antintrusione

### Sub-specializzazione 4 — Ingegneria TLC (Telecomunicazioni)

Documenti tipici per siti radio base (settore di forte presenza Luca):

**Progettazione siti**:
- skill-PE-progetto-esecutivo-iliad
- skill-PE-progetto-esecutivo-Cellnex
- skill-PE-rooftop-installazione-tetto
- skill-PE-rawland-nuovo-palo
- skill-PE-greenfield-pennone
- skill-PE-colocation-aggiunta-operatori
- skill-PE-transfer-spostamento-sito
- skill-PE-upgrade-incremento-tecnologie
- skill-PE-swap-sostituzione-apparati
- skill-PE-dismissione-sito

**Verifiche tecniche**:
- skill-verifica-statica-palo-TLC
- skill-verifica-statica-rooftop
- skill-verifica-statica-traliccio-esistente
- skill-verifica-fatica-pali-snelli
- skill-analisi-sismica-avanzata-pali
- skill-relazione-azioni-ambientali

**Iter autorizzativo**:
- skill-pratica-DLgs-259-2003
- skill-relazione-tecnica-impatto-elettromagnetico
- skill-relazione-paesaggistica-antenna
- skill-relazione-monumentale-antenna
- skill-CDS-conferenza-servizi
- skill-collaudo-impianti-TLC

**Sicurezza e compliance**:
- skill-PSC-cantiere-TLC
- skill-CSE-coordinamento-cantiere-antenna
- skill-piano-emergenza-cantiere-TLC

### Sub-specializzazione 5 — Sicurezza Cantieri

**Documenti CSP (fase progettuale)**:
- skill-PSC-piano-sicurezza-coordinamento
- skill-fascicolo-tecnico-opera
- skill-stima-costi-sicurezza
- skill-cronoprogramma-sicurezza
- skill-analisi-rischio-cantiere
- skill-procedure-sicurezza-specifiche

**Documenti CSE (fase esecutiva)**:
- skill-verbale-coordinamento-CSE
- skill-verbale-sopralluogo-cantiere
- skill-aggiornamento-PSC
- skill-verifica-POS-impresa
- skill-segnalazione-inadempienze
- skill-relazione-incidente-near-miss
- skill-sospensione-lavori-pericolo

**Sicurezza luoghi di lavoro**:
- skill-DVR-valutazione-rischi
- skill-DUVRI-rischi-interferenziali
- skill-protocollo-sorveglianza-sanitaria
- skill-procedura-emergenza-incendio

### Sub-specializzazione 6 — Direzione Lavori

**Documenti di gestione**:
- skill-giornale-lavori-DL
- skill-libretto-misure-DL
- skill-registro-contabilita-DL
- skill-stato-avanzamento-lavori-SAL-DL
- skill-certificato-pagamento-CP

**Comunicazioni**:
- skill-ordine-servizio-DL
- skill-comunicazione-committente-stato
- skill-richiesta-variante-corso-opera
- skill-segnalazione-inadempienza-impresa
- skill-applicazione-penali

**Conclusione lavori**:
- skill-verbale-fine-lavori
- skill-relazione-fine-lavori-DL
- skill-CRE-certificato-regolare-esecuzione
- skill-conto-finale-DL
- skill-svincolo-cauzione

### Sub-specializzazione 7 — Beni Monumentali e Paesaggistici

**Pratiche su vincolato**:
- skill-relazione-paesaggistica-completa
- skill-relazione-paesaggistica-semplificata-DPR-31-2017
- skill-relazione-monumentale-DLgs-42-2004
- skill-fotosimulazione-impatto-visivo
- skill-cono-visivo-analisi-percettiva
- skill-scheda-degrado-bene-storico

**Interventi su edifici tutelati**:
- skill-progetto-restauro-conservativo
- skill-progetto-consolidamento-storico
- skill-relazione-tecnica-MIC
- skill-progetto-illuminazione-bene-tutelato

**TLC su vincolato** (incrocio con sub-specializzazione 4):
- skill-relazione-compatibilita-antenna-bene-storico
- skill-fotosimulazione-antenna-monumento

### Sub-specializzazione 8 — Energetica e Sostenibilità

**Diagnosi e certificazioni**:
- skill-diagnosi-energetica-edificio
- skill-APE-attestato-prestazione-energetica
- skill-relazione-EGE-certificata
- skill-audit-energetico-industriale
- skill-relazione-Conto-Termico
- skill-relazione-TEE-certificati-bianchi

**Progetti efficientamento**:
- skill-progetto-cappotto-termico
- skill-progetto-sostituzione-caldaia
- skill-progetto-LED-illuminazione
- skill-progetto-fotovoltaico-autoconsumo
- skill-progetto-pompa-calore-sostituzione

---

## 4. Anatomia di un template

Ogni template fornito da questa skill segue una struttura standard, pronta per essere personalizzata sullo studio specifico.

### Esempio template — skill-relazione-sopralluogo-civile-edilizia

```markdown
---
name: skill-relazione-sopralluogo-civile-edilizia
description: Template per la produzione di relazione di sopralluogo per edifici civili residenziali e commerciali. Usa quando devi documentare un sopralluogo tecnico in studio di ingegneria civile per finalità di valutazione stato conservativo, perizia, progetto di intervento, o adeguamento normativo. Format della relazione strutturato secondo prassi consolidata dello studio [NOME STUDIO]. Da personalizzare con criteri specifici del titolare in fase di skillizzazione.
domain: ingegneria-civile
document_type: relazione-sopralluogo
frequency: alta
complexity: media
last_updated: [DATA PERSONALIZZAZIONE]
version: 1.0
based_on_archive_examples: [N esempi reali analizzati]
---

# skill-relazione-sopralluogo-civile-edilizia

## 1. Scope e applicabilità

Questa skill produce una relazione di sopralluogo tecnico per edifici civili.

**Quando usarla**:
- Sopralluogo per valutazione stato conservativo edificio esistente
- Sopralluogo per perizia tecnica (CTU, CTP, parere assicurativo)
- Sopralluogo per progetto di intervento (ristrutturazione, ampliamento)
- Sopralluogo per adeguamento normativo (sicurezza, accessibilità, energetico)
- Sopralluogo per due diligence immobiliare

**Quando NON usarla**:
- Sopralluogo per progetti TLC (vedi skill-PE-progetto-esecutivo-{operatore})
- Sopralluogo strutturale specifico (vedi skill-rilievo-strutture-portanti)
- Sopralluogo per beni vincolati (vedi skill-rilievo-bene-storico)

## 2. Struttura del documento

La relazione di sopralluogo dello studio [NOME STUDIO] segue questa struttura standard:

### Sezione 1 — Dati identificativi
- Cliente / Committente
- Indirizzo dell'intervento
- Data e ora del sopralluogo
- Tecnico/i intervenuti
- Eventuali altre figure presenti
- Numero progressivo sopralluogo (se serie)

### Sezione 2 — Premessa e obiettivi
- Motivo del sopralluogo (incarico, richiesta, finalità)
- Obiettivi specifici del rilievo
- Documentazione preventiva consultata

### Sezione 3 — Inquadramento territoriale e urbanistico
- Localizzazione (indirizzo completo, coordinate, foglio/particella catastale)
- Inquadramento PRG/PUC/PGT comunale
- Eventuali vincoli (paesaggistici, monumentali, idraulici, sismici)
- Caratteristiche del contesto urbano/extraurbano

### Sezione 4 — Caratteristiche generali dell'edificio
- Tipologia edilizia
- Anno di costruzione (se noto)
- Numero piani fuori terra / interrati
- Superficie coperta indicativa
- Volumetria indicativa
- Destinazione d'uso attuale
- Eventuali destinazioni precedenti

### Sezione 5 — Stato di fatto strutturale
- Tipologia struttura portante (CA, muratura, acciaio, mista)
- Tipologia solai
- Tipologia copertura
- Tipologia fondazioni (se evincibile)
- Stato conservativo apparente (Ottimo / Buono / Mediocre / Degradato)

### Sezione 6 — Stato di fatto impiantistico
- Impianto elettrico (presenza, stato, conformità apparente)
- Impianto termico (tipologia, stato)
- Impianto idro-sanitario
- Impianto di climatizzazione (se presente)
- Eventuali impianti speciali

### Sezione 7 — Patologie e degradi rilevati
Per ogni patologia/degrado rilevato:
- Localizzazione precisa
- Tipologia (fessurazione, infiltrazione, distacco intonaco, etc.)
- Estensione/gravità (lieve, media, grave, gravissima)
- Causa probabile (ipotesi)
- Foto identificativa (rimando)
- Rischio strutturale/funzionale associato

### Sezione 8 — Documentazione fotografica
- Riferimenti alla photo gallery allegata
- Numerazione foto e didascalie
- Eventuali planimetrie con punti di scatto

### Sezione 9 — Conclusioni e raccomandazioni
- Sintesi dello stato generale
- Priorità di intervento eventuale
- Raccomandazioni operative
- Indicazione di necessari approfondimenti (es. indagini distruttive, prove, ulteriori sopralluoghi)

### Sezione 10 — Allegati
- Documentazione fotografica
- Eventuali planimetrie/rilievi sketch
- Eventuali documenti del committente

## 3. Criteri di compilazione [DA PERSONALIZZARE PER STUDIO]

I criteri di compilazione del titolare dello studio [NOME STUDIO] sono:

### Tono e stile
- [Es. "Tono tecnico ma accessibile al committente non tecnico, evitando gergo eccessivo"]
- [Es. "Sempre prima persona plurale ('abbiamo rilevato'), mai prima singolare"]
- [Es. "Frasi brevi e chiare, max 25 parole per frase"]

### Approccio metodologico
- [Es. "Sempre cautela nelle conclusioni: 'sembra essere', 'potrebbe indicare', mai certezze assolute senza prove"]
- [Es. "Sempre menzionare i limiti del rilievo: 'con i mezzi disponibili al sopralluogo'"]
- [Es. "Mai fare diagnosi di cause profonde senza indagini distruttive"]

### Standard di documentazione fotografica
- [Es. "Minimo 30 foto per sopralluogo, max 100"]
- [Es. "Foto di insieme + dettagli per ogni patologia"]
- [Es. "Sempre includere foto con riferimento dimensionale (cm, oggetti noti)"]
- [Es. "Sempre geotag attivato"]

### Estensione e dettaglio
- [Es. "Relazione standard 8-15 pagine + allegati fotografici"]
- [Es. "Dettaglio maggiore su patologie identificate, sintesi sul resto"]

## 4. Esempi dall'archivio dello studio [DA PERSONALIZZARE]

### Esempio 1 — Sopralluogo edificio residenziale anni '70 (anonimizzato)
[Estratto reale dall'archivio dello studio, anonimizzato]
[Mostra come il titolare struttura una relazione tipo]

### Esempio 2 — Sopralluogo perizia assicurativa (anonimizzato)
[Estratto reale, mostra approccio per finalità peritale]

### Esempio 3 — Sopralluogo pre-progetto ristrutturazione (anonimizzato)
[Estratto reale, mostra approccio orientato all'intervento]

### Esempio 4 — Sopralluogo edificio in difficoltà (anonimizzato)
[Estratto reale di caso complesso]

### Esempio 5 — Sopralluogo di seconda visita (anonimizzato)
[Per casi che richiedono più visite, format del follow-up]

## 5. Casi limite e varianti

### Variante 1 — Sopralluogo per CTU
- Aggiungere sezione "Quesiti del giudice" e risposte puntuali
- Tono ancora più cauto e formale
- Approfondimento maggiore su questioni controverse

### Variante 2 — Sopralluogo con presenza altri tecnici/CTP
- Documentare presenza terzi
- Annotare eventuali contraddittori
- Evidenziare punti concordi e discordi

### Variante 3 — Sopralluogo edificio molto grande (>2.000 mq)
- Articolare sezione 4-7 per zone/piani
- Cartografia con codici di rilievo
- Sintesi generale + dettaglio per zona

### Variante 4 — Sopralluogo in emergenza (post-evento sismico, allagamento)
- Format ridotto per urgenza
- Focus su agibilità immediata
- Eventuali indicazioni di evacuazione

### Variante 5 — Sopralluogo con limitato accesso (locali chiusi, etc.)
- Documentare i limiti dell'accesso
- Specificare cosa non si è potuto verificare
- Indicare necessità di accesso completo successivo

## 6. Riferimenti normativi e tecnici

- **NTC 2018** (D.M. 17/01/2018) — per riferimenti strutturali
- **DPR 380/2001** — Testo Unico edilizia
- **D.M. 37/2008** — Impianti
- **L. 13/1989** — Barriere architettoniche
- **Norma UNI 11337** — BIM (se rilevante)
- **DPR 462/2001** — Verifiche periodiche impianti
- [Aggiungere riferimenti specifici della zona/regione dello studio]

## 7. Lessons learned [DA PERSONALIZZARE]

Errori tipici da evitare (basati su esperienza dello studio):

- [Es. "Mai dare valutazioni di stabilità strutturale sulla base di sopralluogo visivo. Sempre raccomandare verifiche specifiche se ci sono dubbi"]
- [Es. "Mai dimenticare di datare e firmare ogni pagina"]
- [Es. "Mai usare termini medici impropri ('è malato l'edificio'), il linguaggio tecnico è preciso"]
- [Es. "Sempre conservare copia del rilievo originale (sketch, foto raw) per eventuali contestazioni successive"]

## 8. Checklist operativa pre-sopralluogo

Prima di andare in sopralluogo:
- [ ] Documenti precedenti consultati
- [ ] Inquadramento catastale verificato
- [ ] Vincoli verificati su SITAP / PUC
- [ ] Equipaggiamento controllato (foto, metro, livella, etc.)
- [ ] Eventuali dispositivi di sicurezza
- [ ] Conferma appuntamento committente

Durante il sopralluogo:
- [ ] Foto di insieme (almeno 5)
- [ ] Foto di dettaglio per ogni patologia
- [ ] Misure fondamentali rilevate
- [ ] Eventuali sketch a mano libera
- [ ] Note vocali per dettagli
- [ ] Annotazioni di patologie con riferimento foto

Dopo il sopralluogo (entro 48h):
- [ ] Foto scaricate e organizzate
- [ ] Note vocali trascritte
- [ ] Bozza relazione drafted
- [ ] Review bozza
- [ ] Relazione finalizzata
- [ ] Invio al committente
- [ ] Archiviazione su [SISTEMA STUDIO]

## 9. Output atteso

La skill produce:
- Relazione di sopralluogo .docx (8-15 pp)
- Eventuale archivio fotografico organizzato
- Sintesi executive 1 pagina (se richiesta dal cliente)
```

Questo è solo **uno** dei 50+ template. La skill `ai-archive-templates-engineering` ne contiene di analoghi per ogni tipologia documentale del settore.

---

## 5. Workflow di personalizzazione del template

Quando K2-AI applica questa skill al cliente specifico:

### Step 1 — Pattern matching
Identifica quali template corrispondono a tipi di documento dell'archivio cliente.

### Step 2 — Sample analysis
Per ogni template applicabile, K2-AI analizza 5-10 documenti reali dell'archivio cliente.

### Step 3 — Pattern extraction
Estrae:
- Struttura tipica usata (varia da template generico)
- Stile narrativo specifico del titolare
- Convenzioni di nomenclatura
- Standard ricorrenti
- Casi anomali

### Step 4 — Customization
Personalizza il template:
- **Sezione 3 "Criteri di compilazione"**: criteri reali del titolare
- **Sezione 4 "Esempi"**: estratti reali dall'archivio (anonimizzati)
- **Sezione 7 "Lessons learned"**: errori tipici osservati
- **Sezione 8 "Checklist"**: workflow specifico dello studio

### Step 5 — Validation
- Review da parte del titolare
- Test su 2-3 casi nuovi
- Iterazione fino a v1.0

### Step 6 — Deployment
Skill personalizzata aggiunta a repository del cliente.

---

## 6. Esempio applicato — Studio TLC (incrocio con dominio Luca)

### Skill specifica per dominio Luca

Una skill che K2-AI può costruire **molto facilmente** grazie all'esperienza diretta di Luca:

```markdown
---
name: skill-PE-progetto-esecutivo-iliad-rooftop
description: Template per Progetto Esecutivo iliad rooftop (installazione su edifici esistenti). Codifica struttura completa del PE secondo standard iliad Italia, criteri di scelta tecnica, deliverable richiesti, iter autorizzativo. Da applicare a nuovi siti o transfer rooftop.
domain: ingegneria-TLC
document_type: progetto-esecutivo
client_operator: iliad
site_typology: rooftop
frequency: alta
complexity: alta
last_updated: 2026-01-15
version: 2.3
based_on_archive_examples: 47 PE iliad rooftop completati
---

# skill-PE-progetto-esecutivo-iliad-rooftop

## 1. Scope e applicabilità

Genera Progetto Esecutivo iliad per installazione rooftop su edifici esistenti.

**Quando usarla**:
- Nuovo sito iliad rooftop su edificio esistente
- Transfer iliad da altro sito a nuovo rooftop
- Upgrade tecnologico iliad su rooftop esistente

**Quando NON usarla**:
- Siti rawland o greenfield (skill-PE-progetto-esecutivo-iliad-rawland)
- Siti Cellnex o altri operatori (skill-PE-progetto-esecutivo-Cellnex-*)
- Colocation aggiunta operatori (skill-PE-colocation)

## 2. Struttura completa del PE iliad rooftop

[Struttura specifica iliad: 28 sezioni standard...]

## 3. Criteri tecnici iliad rooftop

[Criteri specifici: distanza minima da ostacoli, vincoli antenne, requisiti elettrici, ecc.]

## 4. Esempi dall'archivio K2A

[5 esempi reali anonimizzati di PE iliad rooftop completati]

## 5. Casi limite

- Edifici con vincolo paesaggistico (rimando a skill-relazione-paesaggistica-antenna)
- Edifici condominiali con dissensi (rimando a skill-PE-condominio-dissenso)
- Rooftop con accesso difficile (procedure speciali)

## 6. Riferimenti normativi

- D.Lgs. 259/2003 (Codice Comunicazioni Elettroniche)
- DM 75/2024
- Linee guida operatore iliad
- CEI 64-8 per impianto elettrico
- NTC 2018 per verifica statica supporti

## 7. Lessons learned (basato su 47 PE completati)

- Sempre verificare sezione strutturale anche per upgrade (errore comune)
- Documentare con precisione punti di accesso per manutenzione
- Foto sempre da 4 prospettive cardinali del rooftop
- Coordinare con condominio prima di sopralluogo

## 8. Checklist completa

[Checklist 35 punti per PE iliad rooftop]

## 9. Output atteso

Pacchetto PE completo:
- Relazione tecnica (40-60 pp)
- Tavole grafiche (12-20)
- Verifiche statiche (skill-verifica-statica-rooftop)
- PSC (skill-PSC-cantiere-TLC)
- Computo (skill-computo-cantiere-TLC)
- Documentazione DLgs 259/2003
```

Questa skill, specifica per il dominio Luca, è **estremamente codificabile** perché Luca ha esperienza diretta su 47+ PE iliad rooftop reali.

---

## 7. Skill K2-AI esistenti rilevanti per ingegneria

L'ecosistema K2-AI ha già molte skill tecniche di settore che si combinano perfettamente con la skillizzazione cliente:

### Skill tecniche K2-AI già esistenti (rilevanti per template clienti)

**Per civile/edilizia**:
- progettazione-architettonica
- agibilita
- direzione-lavori
- consulente-pa-operativa (per pratiche con PA)

**Per strutturale**:
- progettista-strutturale
- progetto-strutturale-gc-tlc
- verifica-statica-iliad-cellnex* (suite completa)

**Per MEP**:
- impianti-elettrici
- impianti-termici-hvac
- diagnosi-energetica-ege
- cci-impianti-produzione

**Per TLC**:
- verifica-pe-terzi
- progetto-strutturale-gc-tlc
- verifica-statica-iliad-cellnexvs-* (3 skill)

**Per sicurezza**:
- psc-coordinamento-sicurezza
- cse-coordinatore-sicurezza
- consulente-sicurezza-lavoro

**Per beni monumentali**:
- architetto-beni-monumentali

**Per energetico**:
- diagnosi-energetica-ege

### Come si combinano

Quando si skillizza uno studio cliente, le skill K2-AI esistenti agiscono come **knowledge base settoriale** che alimenta la costruzione delle skill cliente.

Esempio: per costruire `skill-relazione-calcolo-CA-armato-NTC` per uno studio cliente, K2-AI:
1. Usa template di base da `ai-archive-templates-engineering`
2. Attinge a knowledge da `progettista-strutturale` per riferimenti normativi e formulazioni tecniche
3. Personalizza con esempi reali dell'archivio cliente
4. Risultato: skill cliente di altissima qualità in pochi giorni invece che settimane

---

## 8. Pricing dell'utilizzo di template settoriali

L'uso di questa skill **riduce significativamente l'effort** di costruzione delle skill cliente.

### Risparmio per il cliente

| Approccio | Costo per 50 skill | Tempo |
|-----------|---------------------|-------|
| Skillization da zero (senza template) | ~50.000€ | 12-15 mesi |
| Skillization con template settoriali | ~32.000€ | 7-9 mesi |
| **Risparmio** | **~36%** | **~40%** |

### Pricing K2-AI per servizio

I template settoriali sono **inclusi** nei pacchetti Skillization standard (non add-on a parte). Il valore per K2-AI è:
- Maggiore margine (effort ridotto, prezzo simile)
- Time-to-delivery ridotto (più clienti gestibili in parallelo)
- Qualità più consistente
- Asset proprio K2-AI (i template sono IP K2-AI)

---

## 9. Integrazione con altre skill

### Skill di sistema
- **flusso-ai-studi-professionali**: orchestratore
- **ai-knowledge-skillization-studio**: metodologia trasversale (questa skill è il complemento settoriale)
- **ai-assessment-studio**: discovery iniziale
- **ai-roadmap-progettazione**: design del progetto skillization
- **ai-implementazione-pilota**: implementazione progressiva
- **ai-manutenzione-evoluzione**: manutenzione ongoing

### Skill K2-AI tecniche di settore (knowledge base)
Tutte le skill tecniche K2-AI esistenti citate sopra alimentano la costruzione di skill cliente.

### Skill commerciali
- **lead-qualifier**: qualifica clienti ingegneria
- **pricing-proposal-generator**: proposta commerciale
- **customer-success-manager**: gestione cliente in skillization

---

## 10. Errori comuni da evitare

- **Non usare i template come prodotti finiti**: sono punti di partenza, sempre da personalizzare
- **Non saltare l'analisi dell'archivio cliente**: i template senza pattern reali del cliente sono generici
- **Non promettere "100% template applicabili"**: tipicamente 60-80% dell'archivio si copre con template, il resto richiede skill custom
- **Non confondere template settoriale con template generico**: i template di questa skill sono **specifici** per ingegneria italiana, con riferimenti normativi NTC, EC, deontologia CNI
- **Non sottovalutare le sub-specializzazioni**: studio "civile/strutturale/MEP" è diverso da studio "TLC", template diversi
- **Non saltare l'integrazione con skill K2-AI tecniche esistenti**: sono il valore aggiunto enorme
- **Non considerare i template fissi**: vanno aggiornati periodicamente per evoluzione normativa e tecnica
- **Non personalizzare solo la sezione esempi**: anche criteri, lessons learned, checklist vanno sempre adattati al cliente
- **Non saltare il versioning dei template**: ogni aggiornamento deve essere tracciato
- **Non sottovalutare l'effort di review titolare**: il valore della skill cliente è la voce del titolare, non K2-AI
