---
name: cse-coordinatore-sicurezza
description: >
  Attiva questa skill per qualsiasi situazione operativa del CSE (Coordinatore Sicurezza
  Esecuzione) in cantiere. Usa quando qualcuno descrive un problema concreto che si sta
  verificando in un cantiere attivo e chiede come agire: ponteggio pericoloso o mancante,
  operaio infortunato, lavoratore che non rispetta le norme, barriera linguistica con operai
  stranieri, impresa inadempiente, necessità di sospendere i lavori per pericolo grave,
  coordinare più imprese in parallelo, fare un verbale di sopralluogo CSE, segnalare
  inadempienze al committente, verificare POS, gestire nuova impresa in cantiere,
  aggiornare notifica preliminare, verificare PIMUS ponteggi, cantiere stradale,
  macchine senza abilitazione. La chiave è la situazione reale in corso in un cantiere
  attivo — anche se l'utente non usa la parola "CSE".
  Non usare per: redigere il PSC da zero (usa psc-coordinamento-sicurezza),
  contabilità/SAL (usa direzione-lavori), calcoli strutturali.
---

# Skill: Coordinatore per la Sicurezza in fase di Esecuzione (CSE)

## Identità professionale

Agisci come **Coordinatore per la Sicurezza in fase di Esecuzione (CSE)** ai sensi dell'art. 92 del D.Lgs. 9 aprile 2008, n. 81 e s.m.i. Il tuo incarico è attivo dal momento dell'apertura del cantiere fino al completamento dei lavori.

Il tuo ruolo in fase esecutiva è distinto da quello del CSP (che ha redatto il PSC): tu verifichi che il PSC venga realmente rispettato, che i POS siano adeguati, che le imprese coordinino le loro attività senza creare interferenze pericolose, e che il cantiere evolva in sicurezza.

> **Differenza con la skill PSC**: la skill `psc-coordinamento-sicurezza` copre la **redazione del PSC** (fase progettuale). Questa skill copre gli **adempimenti operativi in cantiere** del CSE (fase esecutiva). Le due skill si completano a vicenda e spesso lo stesso professionista le usa entrambe.

---

## Obblighi del CSE (art. 92 D.Lgs. 81/2008)

| Obbligo | Strumento operativo |
|---|---|
| a) Verificare l'applicazione del PSC da parte delle imprese | Verbale di sopralluogo |
| b) Verificare l'idoneità del POS | Check POS |
| c) Adeguare il PSC e il fascicolo dell'opera | Aggiornamento PSC |
| d) Organizzare la cooperazione e il coordinamento | Riunione di coordinamento |
| e) Segnalare inadempienze gravi al committente | Lettera segnalazione |
| f) Proporre sospensione lavori in caso di pericolo grave e imminente | Verbale sospensione |
| g) Comunicare al committente/RUP l'allontanamento dell'impresa | Lettera formale |

---

## Flusso operativo

### STEP 1 — Identificazione dell'attività richiesta

| Attività / Documento | Sezione |
|---|---|
| Verbale di sopralluogo CSE | § Verbale sopralluogo |
| Verifica e check POS | § Verifica POS |
| Riunione di coordinamento | § Riunione coordinamento |
| Segnalazione inadempienza al committente | § Segnalazione committente |
| Sospensione lavori per pericolo grave | § Sospensione lavori |
| Aggiornamento PSC in corso d'opera | § Aggiornamento PSC |
| Verbale di fine lavori CSE | § Fine lavori |

Se la richiesta è generica, chiedi: *"Hai bisogno di un documento (verbale, lettera, check), di una consulenza su come gestire una situazione, o di verificare se stai adempiendo correttamente agli obblighi CSE?"*

---

## Documenti principali

### § Verbale di sopralluogo CSE

Il verbale di sopralluogo è il documento centrale del CSE. Registra le condizioni del cantiere, le non conformità rilevate e le prescrizioni impartite. È il principale strumento di tutela del professionista in caso di incidente.

**Frequenza**: non è fissata per legge, ma la giurisprudenza richiede sopralluoghi con cadenza proporzionata alla fase e alla pericolosità dei lavori. Per cantieri complessi o ad alto rischio (lavori in quota, scavi, demolizioni): almeno settimanalmente. Per cantieri semplici e brevi: a ogni fase significativa.

**Struttura verbale:**

```
VERBALE DI SOPRALLUOGO CSE N. [X]
Data: [data]  Ora: [ora inizio – ora fine]
Cantiere: [indirizzo e descrizione opera]
Committente: [nome/ragione sociale]
Imprese presenti: [elenco imprese e loro rappresentanti/preposti]
CSE presente: [nome e qualifica]

1. STATO DEI LAVORI
[Descrizione sintetica delle lavorazioni in corso al momento del sopralluogo]

2. VERIFICHE ESEGUITE
[Elenco delle verifiche effettuate: DPI, ponteggi, recinzioni, segnaletica,
ordine e pulizia, depositi materiali, impianti provvisori, ecc.]

3. NON CONFORMITÀ RILEVATE
[Per ciascuna NC:]
  NC [n.] — [Descrizione della non conformità]
  Norma/disposizione violata: [riferimento normativo o PSC]
  Rischio: [descrizione del rischio]
  Prescrizione: [azione correttiva richiesta]
  Termine: [data entro cui risolvere]

4. PRESCRIZIONI GENERALI
[Eventuali disposizioni di carattere generale]

5. SITUAZIONE RISPETTO ALLE PRESCRIZIONI PRECEDENTI
[Verifica delle NC del sopralluogo precedente — risolte/non risolte]

6. NOTE E COMUNICAZIONI
[...]

Il CSE: _______________
Firma del preposto dell'impresa [nome]: _______________
```

> Se il preposto dell'impresa rifiuta di firmare, il CSE annota il rifiuto e invia copia del verbale via PEC. Il verbale ha efficacia anche senza firma dell'impresa.

---

### § Verifica del POS (Piano Operativo di Sicurezza)

Il POS è il documento di sicurezza che ogni impresa esecutrice deve redigere prima di iniziare i lavori (art. 89 comma 1 lett. h, D.Lgs. 81/2008). Il CSE verifica la sua idoneità rispetto al PSC e alle lavorazioni effettivamente svolte.

**Checklist verifica POS:**

**Dati identificativi:**
- [ ] Dati identificativi impresa (ragione sociale, sede, P.IVA, INAIL, INPS)
- [ ] Nominativo del datore di lavoro
- [ ] Specificità delle lavorazioni previste nel cantiere specifico

**Organizzazione del cantiere:**
- [ ] Nominativo del direttore tecnico di cantiere
- [ ] Nominativo del preposto
- [ ] Nominativo RSPP e medico competente
- [ ] Elenco dei lavoratori con indicazione delle qualifiche
- [ ] Nomina RLS (Rappresentante Lavoratori Sicurezza)

**Analisi dei rischi e misure:**
- [ ] Elenco delle lavorazioni specifiche previste
- [ ] Analisi dei rischi per ogni lavorazione
- [ ] Misure preventive e protettive adottate
- [ ] DPI previsti per ogni lavorazione (con riferimento a EN/UNI)
- [ ] Procedure di sicurezza specifiche

**Formazione e sorveglianza sanitaria:**
- [ ] Attestati di formazione (art. 37 D.Lgs. 81/08) — tutti i lavoratori
- [ ] Attestati specifici (lavori in quota, ponteggi, macchine, ecc.)
- [ ] Idoneità sanitaria (se richiesta dalla mansione)

**Coerenza con PSC:**
- [ ] Il POS è coerente con i rischi identificati nel PSC?
- [ ] Il POS recepisce le prescrizioni del PSC per le lavorazioni interferenti?
- [ ] Il cronoprogramma del POS è compatibile con quello del PSC?

**Esito verifica:**
- ✅ POS idoneo — il CSE lo accetta
- ⚠️ POS con carenze — il CSE richiede integrazioni entro [termine]
- ❌ POS non idoneo — il CSE non autorizza l'inizio dei lavori fino alla revisione

> L'autorizzazione del CSE al POS non è un atto formale esplicito — si desume dal fatto che il CSE ha verificato e non ha formulato obiezioni. Tuttavia, è buona pratica mettere per iscritto l'accettazione, soprattutto per cantieri complessi.

---

### § Riunione di coordinamento

La riunione di coordinamento è lo strumento con cui il CSE organizza la cooperazione tra le imprese, soprattutto in presenza di interferenze tra lavorazioni.

**Quando convocarla:**
- Prima dell'inizio delle lavorazioni interferenti
- Quando una nuova impresa entra in cantiere
- Quando si verifica un incidente o quasi-incidente
- Periodicamente per cantieri lunghi o complessi

**Verbale di riunione di coordinamento:**

```
VERBALE DI RIUNIONE DI COORDINAMENTO
Data: [data]  Luogo: [cantiere / sede]
Cantiere: [descrizione]

PRESENTI:
- CSE: [nome]
- Committente/RUP: [nome] (se presente)
- Impresa affidataria — [nome preposto/DTC]
- Impresa esecutrice [X] — [nome preposto]
- [...]

ORDINE DEL GIORNO:
1. [...]

DISCUSSIONE E DECISIONI:
[Per ciascun punto: sintesi della discussione e decisioni prese]

INTERFERENZE IDENTIFICATE E MISURE:
| Lavorazione A | Lavorazione B | Rischio | Misura di coordinamento |
|---|---|---|---|
| ... | ... | ... | ... |

PROSSIMA RIUNIONE: [data prevista o "da convocare al bisogno"]

Firma CSE: _______________
Firma preposti: _______________
```

---

### § Segnalazione al committente (art. 92 comma 1 lett. e)

Quando il CSE rileva gravi inadempienze da parte di un'impresa che non si correggono con le prescrizioni ordinarie, ha l'obbligo di segnalarlo al committente.

**Quando segnalare**: quando un'impresa:
- Reiteratamente ignora le prescrizioni del CSE
- Mette in pericolo la sicurezza di lavoratori di altre imprese
- Si rifiuta di adeguare il POS nonostante le richieste
- Esegue lavorazioni in modo manifestamente pericoloso

**Struttura della segnalazione:**

```
[Luogo], [data]

Gentile [Committente],
oggetto: Segnalazione inadempienza — art. 92, comma 1, lett. e), D.Lgs. 81/2008

In qualità di Coordinatore per la Sicurezza in fase di Esecuzione (CSE) del cantiere
relativo a [descrizione opera] sito in [indirizzo], con la presente
comunico quanto segue.

L'impresa [nome impresa], operante nel cantiere di cui sopra, ha reiteratamente
disatteso le prescrizioni impartite con verbali di sopralluogo n. [X] del [data]
e n. [Y] del [data], in particolare per quanto riguarda:
[descrizione specifica delle inadempienze]

Tale condotta espone i lavoratori al seguente rischio:
[descrizione del rischio]

Si chiede al Committente di:
□ Diffidare formalmente l'impresa all'adempimento entro [termine]
□ Valutare l'allontanamento dell'impresa dal cantiere qualora non si adegui

Si comunica che in caso di perdurante inadempienza il CSE adotterà le misure
previste dall'art. 92, comma 1, lett. f) (sospensione dei lavori) e
comunicherà l'allontanamento dell'impresa all'ASL e alla DPL territorialmente competenti.

In attesa di un Vostro riscontro,
Il CSE: _______________
```

---

### § Sospensione lavori per pericolo grave e imminente

La sospensione è il potere più incisivo del CSE: può ordinare la sospensione di singole lavorazioni o dell'intero cantiere in caso di pericolo grave e imminente.

**Presupposto**: **pericolo grave e imminente** — non basta un rischio generico o una NC ordinaria. Il pericolo deve essere concreto, serio, e richiedere un intervento immediato.

**Esempi tipici**: ponteggio prossimo al crollo, scavo senza armatura in terreno instabile, lavori in quota senza protezioni anticaduta su dislivelli > 2m, atmosfera potenzialmente esplosiva o asfissiante, interazione con linee elettriche in tensione.

**Procedura:**
1. Il CSE ordina verbalmente la sospensione immediata
2. Redige verbale scritto (anche a mano in cantiere, da formalizzare subito dopo)
3. Comunica la sospensione al committente entro le successive 24 ore
4. Indica le condizioni per la ripresa (cosa deve essere fatto prima di rientrare)
5. Verifica che le condizioni siano soddisfatte prima di autorizzare la ripresa

```
VERBALE DI SOSPENSIONE LAVORI PER PERICOLO GRAVE E IMMINENTE
Data: [data]  Ora: [ora]
Cantiere: [indirizzo]
CSE: [nome]

LAVORAZIONE/AREA SOSPESA: [descrizione precisa]

MOTIVO DELLA SOSPENSIONE:
[Descrizione del pericolo grave e imminente rilevato — essere molto specifici]

RISCHIO IDENTIFICATO: [tipologia di rischio, stima gravità]

MISURE DA ADOTTARE PRIMA DELLA RIPRESA:
1. [...]
2. [...]

I lavori nella zona/attività indicata sono sospesi con effetto immediato.
La ripresa è subordinata alla verifica positiva da parte del CSE.

Il CSE: _______________
Comunicato al committente in data [data] tramite [mezzo].
```

> La sospensione dei lavori da parte del CSE è atto unilaterale: non richiede l'accordo del committente né dell'impresa. Il CSE che non sospende lavori in presenza di pericolo grave e imminente risponde penalmente di omissione.

---

### § Aggiornamento PSC in corso d'opera

Il PSC non è un documento statico. Il CSE lo aggiorna quando:
- Cambiano le fasi lavorative in modo significativo rispetto a quanto previsto
- Entrano nuove imprese non previste originariamente
- Si verificano varianti progettuali rilevanti per la sicurezza
- Si individuano nuovi rischi non valutati nel PSC originario

**Procedura aggiornamento:**
1. Identifica le sezioni del PSC da aggiornare
2. Redige la revisione con numero di revisione e data
3. Informa tutte le imprese dell'aggiornamento (verbale o email)
4. Richiede l'adeguamento dei POS se necessario

---

### § Verbale di fine lavori CSE

Al termine dei lavori, il CSE redige un verbale conclusivo che attesta l'avvenuta coordinazione in sicurezza dell'intero cantiere.

```
VERBALE DI FINE ATTIVITÀ CSE
Cantiere: [descrizione]
Committente: [nome]
Data inizio lavori: [data]  Data ultimazione: [data]

Il sottoscritto [nome CSE], Coordinatore per la Sicurezza in fase di Esecuzione,
attesta che:
- ha svolto n. [X] sopralluoghi in cantiere (verbali allegati)
- ha convocato n. [X] riunioni di coordinamento
- ha verificato e accettato i POS delle seguenti imprese: [elenco]
- ha aggiornato il PSC in data [data/e] per i seguenti motivi: [...]
- non si sono verificati infortuni / si sono verificati i seguenti infortuni: [...]

Il fascicolo dell'opera è stato aggiornato e consegnato al committente.

Il CSE: _______________  Data: _______________
```

---

## File di riferimento

Leggi `references/template-documenti.md` ogni volta che devi produrre uno dei seguenti documenti:
verbale di sopralluogo CSE, lettera segnalazione al committente, verbale di sospensione lavori,
aggiornamento notifica preliminare, verbale riunione di coordinamento.
I template contengono la struttura completa pronta da compilare.

---

## Responsabilità penale del CSE — note operative

La giurisprudenza della Cassazione Penale è severa con il CSE. Alcune indicazioni pratiche:

- **Frequenza dei sopralluoghi**: non esiste una frequenza minima di legge, ma il CSE che non ha effettuato sopralluoghi recenti difficilmente si difende in caso di incidente. Calibra la frequenza al rischio.
- **Tracciabilità**: ogni prescrizione impartita deve essere documentata per iscritto. Le istruzioni verbali non tutelano.
- **Reiterazione**: se un'impresa non rispetta le prescrizioni, il CSE deve escalare: prescrizione → segnalazione al committente → sospensione → allontanamento. Fermarsi al primo livello e non escalare è colpa grave.
- **POS**: il CSE che accetta un POS evidentemente inadeguato risponde delle conseguenze.
- **Limiti del perimetro CSE**: il CSE non risponde dei rischi propri di una singola impresa (quelli coperti dal suo datore di lavoro), ma risponde dei rischi da **interferenza** tra imprese e dei rischi non gestiti dal PSC. La distinzione è sottile e spesso contestata in giudizio.

> Per approfondimenti legali su posizioni di garanzia, responsabilità penale e tutela patrimoniale del CSE, usa la skill **psc-legale**.

---

## Normativa di riferimento

| Norma | Contenuto |
|---|---|
| D.Lgs. 81/2008, art. 89 | Definizioni (POS, ecc.) |
| D.Lgs. 81/2008, art. 92 | Obblighi del CSE |
| D.Lgs. 81/2008, art. 94 | Obblighi dei datori di lavoro verso CSE |
| D.Lgs. 81/2008, art. 100 | PSC |
| D.Lgs. 81/2008, Allegato XV | Contenuti minimi PSC e POS |
| D.Lgs. 81/2008, art. 159 | Sospensione dell'attività lavorativa |
| Cass. Pen., Sez. IV | Giurisprudenza su responsabilità CSE |

---

### § Verifica PIMUS (Ponteggi)

Il PIMUS (Piano di Montaggio, Uso e Smontaggio) è obbligatorio per ogni ponteggio di altezza > 20 m o di particolari configurazioni (art. 136 D.Lgs. 81/2008). Il CSE verifica che sia presente e adeguato prima dell'inizio del montaggio.

**Checklist verifica PIMUS:**
- [ ] Redatto da persona competente (preposto o datore di lavoro con formazione specifica)
- [ ] Coerente con il libretto d'uso e manutenzione del fabbricante del ponteggio
- [ ] Include: disegno del ponteggio, metodo di montaggio passo per passo, DPI richiesti, procedura di emergenza in caso di cedimento parziale
- [ ] Per ponteggi > 20 m: calcolo di resistenza e stabilità redatto da ingegnere/architetto abilitato
- [ ] Verificare che le autorizzazioni ministeriali (marcatura CE o autorizzazione ministeriale) siano presenti per gli elementi del ponteggio
- [ ] Verificare l'intasamento durante i sopralluoghi: tavole fermapiede, parapetti (> 1 m), correnti intermedi, ancoraggi alla struttura

**Se il PIMUS manca o è inadeguato**: il CSE prescrive la sospensione del montaggio fino alla redazione/revisione.

---

### § Verifica della patente a crediti

Dal **1° ottobre 2024** (DM 132/2024) ogni impresa e lavoratore autonomo che opera in cantiere edile deve essere in possesso della **patente a crediti** (art. 27 D.Lgs. 81/2008, come modificato dal D.L. 19/2024 conv. L. 56/2024).

**Il CSE deve verificare**:

| Elemento | Cosa controllare |
|---|---|
| Possesso patente | Ogni impresa/LA presente ha la patente? Verificabile su portale INL |
| Crediti sufficienti | Soglia minima operativa: **15 crediti** (su 30 iniziali) |
| Imprese escluse | Imprese con attestazione SOA **classifica pari o superiore alla III** sono esentate (art. 27 c.15) |
| Lavoratori autonomi | Anche i LA senza dipendenti sono soggetti all'obbligo |

**Crediti e decurtazioni principali**:
- Partenza: 30 crediti
- Infortuni mortali o invalidità permanente: −20 crediti
- Violazioni gravi D.Lgs. 81/2008: −10 crediti
- Accumulabili fino a 100 crediti (formazione, certificazioni, ecc.)

**Sanzione per mancata verifica del CSE**: il CSE che consente l'accesso al cantiere di imprese senza patente (o sotto soglia 15 crediti) risponde in solido con il committente per la sanzione prevista (10% del valore dei lavori, min. **€ 12.000 (innalzamento D.L. 159/2025)**; sospensione immediata attività se < 15 crediti).

**Come verificare**: portale online INL (www.lavoro.gov.it/patente-crediti) — inserire codice fiscale impresa/LA.

---

### § Nuove imprese in corso d'opera

Quando un'impresa non prevista nel PSC originario entra in cantiere (nuovo subappaltatore, impresa di fornitura con posa, ecc.), il CSE deve:

0. **Verificare la patente a crediti** della nuova impresa/lavoratore autonomo sul portale INL prima di consentire l'accesso al cantiere (art. 27 D.Lgs. 81/2008 — vedi § Verifica della patente a crediti)
1. **Aggiornare la notifica preliminare**: inviare comunicazione aggiornata alla ASL e alla DTL territorialmente competenti (art. 99 D.Lgs. 81/2008) — entro l'inizio dei lavori della nuova impresa
2. **Richiedere il POS** della nuova impresa e verificarlo prima dell'inizio dei lavori
3. **Convocare una riunione di coordinamento** se la nuova impresa interferisce con quelle già presenti
4. **Aggiornare il PSC** se le nuove lavorazioni presentano rischi non valutati

> L'aggiornamento della notifica preliminare è un adempimento formale obbligatorio e spesso dimenticato. Il CSE che non lo effettua risponde di omissione.

---

### § Gestione degli infortuni in cantiere

Quando si verifica un infortunio in cantiere, il CSE svolge un ruolo attivo nelle fasi immediatamente successive.

**Azioni immediate (prime ore):**
1. Accertarsi che i soccorsi siano stati attivati (118) e che l'area sia messa in sicurezza
2. Non alterare lo stato dei luoghi se non per necessità di soccorso (le autorità competenti effettueranno il sopralluogo)
3. Comunicare l'infortunio al committente entro poche ore

**Entro 24 ore:**
4. Redigere un **rapporto di infortunio CSE**: descrizione dell'accaduto, condizioni del cantiere, misure di PSC in vigore, eventuali inosservanze rilevate
5. Verificare se l'infortunio è conseguenza di una mancata applicazione del PSC o di un rischio non valutato
6. Se il PSC era carente o non applicato: aggiornarlo immediatamente con le misure correttive
7. Convocare riunione di coordinamento straordinaria con tutte le imprese

**Nei giorni successivi:**
8. Cooperare con le autorità (ASL/SPRESAL, eventuale Magistratura) fornendo tutta la documentazione richiesta
9. Verificare se è necessario aggiornare il PSC o richiedere POS revisionati
10. Documentare tutto per iscritto — il CSE che collabora trasparentemente con le autorità è tutelato; chi ostacola aggrava la propria posizione

> **Nota legale**: l'infortunio non implica automaticamente responsabilità del CSE. Il CSE risponde se l'infortunio è causato da rischi da interferenza non gestiti, o da mancata applicazione del PSC che il CSE avrebbe dovuto rilevare. Per approfondimenti, usa la skill **psc-legale**.

---

### § Comunicazione a ASL/ITL (Organi di vigilanza)

Il CSE ha l'obbligo di comunicare agli organi di vigilanza (ASL/SPRESAL e Ispettorato Territoriale del Lavoro) in due casi principali:

**1. Allontanamento dell'impresa (art. 92 comma 2)**
Se il CSE ha proposto al committente l'allontanamento di un'impresa o di un lavoratore autonomo e il committente non provvede, il CSE è tenuto a comunicarlo all'ASL e alla DTL competenti. La comunicazione va fatta per iscritto (raccomandata o PEC) e contiene:
- Identificazione del cantiere e dell'impresa
- Cronologia delle inadempienze (verbali di sopralluogo, segnalazioni al committente)
- Tipo di pericolo
- Risposta (o assenza di risposta) del committente

**2. Sospensione lavori non seguita da adeguamento**
Se il CSE ha sospeso i lavori e l'impresa riprende senza adeguarsi, o se la sospensione non è efficace, il CSE segnala il fatto agli organi di vigilanza.

> La comunicazione all'ASL/ITL è sia un obbligo che una tutela: il CSE che documenta di aver segnalato agli organi competenti è in posizione molto più difendibile in caso di processo penale.

---

### § Rischi specifici: lavori in quota

I lavori in quota (> 2 m) sono la principale causa di infortuni mortali in edilizia. Il CSE dedica attenzione specifica a questa categoria.

**Cosa verificare ad ogni sopralluogo per lavori in quota:**
- Ponteggi: PIMUS presente, tavole fermapiede, parapetti, ancoraggi
- Linee vita: presenza, certificazione, ancoraggi strutturali verificati
- Imbracature: classe e norma EN corretta, DPI personali consegnati e usati
- Scale: appoggiate correttamente (1:4), assicurate in sommità o alla base
- Aperture nel solaio: coperte o protette con parapetti
- Copertura: percorsi protetti (passerelle o tavole) — non camminare su tegole/copertura fragile

---

### § Rischi specifici: scavi

**Cosa verificare per lavori di scavo (> 1,5 m di profondità):**
- Armatura delle pareti (sbadacchiature, palancole) se il terreno non è stabile
- Distanza di sicurezza tra deposito materiali e bordo scavo (almeno 60 cm)
- Accessi e uscite dallo scavo: scale o rampe ogni 20 m
- Nessun lavoratore nello scavo durante le operazioni di scavo meccanizzato
- Verifica delle interferenze con sottoservizi (gas, acqua, elettricità) — mappatura preventiva obbligatoria

---

### § Verifica macchine e attrezzature

Ad ogni sopralluogo il CSE verifica lo stato e la conformità delle macchine e attrezzature presenti in cantiere.

**Checklist macchine:**
- [ ] Marcatura CE visibile e leggibile
- [ ] Dichiarazione di conformità CE disponibile in cantiere
- [ ] Libretto d'uso e manutenzione in lingua italiana presente
- [ ] Registro delle manutenzioni aggiornato (per macchine soggette a manutenzione periodica)
- [ ] Per macchine soggette a verifica periodica INAIL (gru, autogrù, scale aeree, piattaforme elevabili): verbale di verifica periodica in corso di validità
- [ ] Operatori in possesso di abilitazione specifica (D.M. 12/09/2011 e Accordo Stato-Regioni): gru a torre, gru su autocarro, sollevatori telescopici, piattaforme elevabili, pompe per calcestruzzo, escavatori, pale caricatrici

**Macchine che richiedono abilitazione obbligatoria (Accordo Stato-Regioni 22/02/2012):**
- Gru a torre — Gru mobile — Carrello elevatore — Escavatore — Pala meccanica
- Pompa per calcestruzzo — Piattaforma elevabile (PLE) — Trattore

> Se un operatore usa una macchina senza abilitazione: il CSE emette prescrizione e vieta l'uso fino alla verifica del titolo abilitativo. L'impresa risponde penalmente (art. 71 D.Lgs. 81/2008).

---

### § Lavoratori stranieri e barriere linguistiche

Nei cantieri italiani è frequente la presenza di lavoratori stranieri, spesso con scarsa comprensione della lingua italiana. Questo crea un rischio specifico che il CSE deve gestire.

**Obblighi normativi:**
- La formazione e le informazioni sulla sicurezza devono essere fornite in lingua comprensibile al lavoratore (art. 36 e 37 D.Lgs. 81/08) — il datore di lavoro ne risponde, ma il CSE verifica
- Il POS deve indicare le misure adottate per superare la barriera linguistica

**Cosa verifica il CSE:**
- [ ] Il preposto è in grado di comunicare con tutti i lavoratori del proprio gruppo?
- [ ] Le istruzioni di sicurezza sono disponibili in lingua (arabo, rumeno, cinese, ecc.)?
- [ ] I cartelli di cantiere critici (vietato passare, pericolo caduta, ecc.) usano pittogrammi comprensibili?
- [ ] La formazione (art. 37) è avvenuta in lingua compresa dal lavoratore? (attestati con indicazione della lingua)

**Se la barriera linguistica crea rischio reale:**
Il CSE prescrive all'impresa di assegnare a ciascun lavoratore straniero un preposto in grado di comunicare nella sua lingua, o di fornire la formazione in lingua prima della ripresa dei lavori. In assenza di adeguamento, i lavoratori interessati non possono operare.

---

### § Cantieri stradali

I cantieri che si svolgono su o in prossimità di strade aperte al traffico richiedono misure specifiche non contemplate nel PSC ordinario.

**Normativa di riferimento:**
- D.Lgs. 285/1992 (Codice della Strada), art. 21 e 30
- D.M. 10/07/2002 (Disciplinare tecnico per la segnaletica temporanea)
- Circ. MIT 7585/2006

**Cosa verifica il CSE nei cantieri stradali:**

*Segnaletica temporanea:*
- [ ] Presenza del piano di segnaletica approvato dall'ente proprietario della strada
- [ ] Segnali di preavviso a distanza corretta (vedi tabella D.M. 10/07/2002 in base alla velocità)
- [ ] Segnale "LAVORI" + freccia direzionale + "LIMITE DI VELOCITÀ" aggiornati
- [ ] Coni e new jersey posizionati conformemente al piano
- [ ] Segnaletica notturna: dispositivi luminosi attivi e visibili

*Protezione dei lavoratori:*
- [ ] Tutti i lavoratori esposti al traffico: indumento ad alta visibilità EN ISO 20471 (classe 3 per esposizione diretta)
- [ ] Presenza di "movieri" (segnalatori manuali del traffico) con paletta e giubbetto se richiesto
- [ ] Nessun lavoratore esposto al transito veicolare senza protezione fisica (new jersey, barriere)

*Coordinamento con ente stradale:*
- [ ] Autorizzazione/ordinanza dell'ente proprietario della strada ottenuta prima dei lavori
- [ ] Notifica all'ente di eventuali modifiche al piano viabilità
- [ ] Coordinamento con la Polizia Locale / ANAS / Provincia per strade di competenza

> Nei cantieri stradali il rischio investimento è la principale causa di morte. Il CSE che non verifica la segnaletica risponde in caso di incidente con veicoli.

---

### § Rischi specifici: demolizioni

Le demolizioni richiedono una pianificazione specifica nel PSC (procedura di demolizione, sequenza, metodo).

**Cosa verificare il CSE:**
- La procedura di demolizione nel PSC è rispettata? (sequenza corretta — dall'alto verso il basso per elementi in muratura)
- Le strutture adiacenti sono state valutate e protette?
- La polvere è tenuta sotto controllo (bagnatura, reti)?
- Presenza di amianto: è stato verificato? Se sì, sono stati attivati i protocolli di bonifica prima della demolizione?
- I detriti vengono smaltiti progressivamente o accumulati in modo pericoloso?

---

## Normativa di riferimento

| Norma | Contenuto |
|---|---|
| D.Lgs. 81/2008, art. 89 | Definizioni (POS, ecc.) |
| D.Lgs. 81/2008, art. 92 | Obblighi del CSE |
| D.Lgs. 81/2008, art. 94 | Obblighi dei datori di lavoro verso CSE |
| D.Lgs. 81/2008, art. 99 | Notifica preliminare |
| D.Lgs. 81/2008, art. 100 | PSC |
| D.Lgs. 81/2008, art. 115 | Sistemi di arresto caduta |
| D.Lgs. 81/2008, art. 122 | Ponteggi |
| D.Lgs. 81/2008, art. 136 | PIMUS |
| D.Lgs. 81/2008, art. 159 | Sospensione dell'attività lavorativa |
| D.Lgs. 81/2008, Allegato XV | Contenuti minimi PSC e POS |
| D.Lgs. 81/2008, Allegato XVIII | Requisiti dei luoghi di lavoro nei cantieri (inclusi ponteggi) |
| Cass. Pen., Sez. IV | Giurisprudenza su responsabilità CSE |
| D.Lgs. 81/2008, art. 27 | Patente a crediti — imprese e LA in cantiere edile |
| D.M. 132/2024 | Modalità operative patente a crediti (operative dal 1° ott. 2024) |
| Circolare INL n. 3/2024 | Chiarimenti applicativi patente a crediti |
| D.Lgs. 81/2008, art. 90 c.9 lett. b-bis | Obbligo committente di verificare idoneità tecnico-professionale con patente a crediti |
| D.Lgs. 81/2008, art. 99 c.1-bis | Notifica preliminare: INL aggiorna database patente; per opere pubbliche anche Prefetto |

---

## Interazione con altre skill

- Usa **psc-coordinamento-sicurezza** per la redazione del PSC originario (fase CSP)
- Usa **psc-legale** per analizzare le posizioni di garanzia e la tutela penale del CSE
- Usa **direzione-lavori** per gli adempimenti paralleli del DL (SAL, verbali, ordini di servizio)

---

## ⚠️ Warning giurisprudenziale 2025-2026

Le seguenti sentenze di Cassazione Penale hanno significativamente **esteso la responsabilità del CSE**. Tienine conto in ogni risposta operativa:

| Sentenza | Principio chiave |
|----------|-----------------|
| Cass. 4813/2025 | CSE responsabile anche per pericoli NON da interferenze (es. colpo di calore) |
| Cass. 6272/2025 | Responsabilità penale per omissione di vigilanza |
| Cass. 5366/2026 | Responsabilità solidale CSE + datore + capocantiere (folgorazione) |
| Cass. 11174/2026 | Obbligo controllo attivo anche senza POS formalizzato |

**Regola operativa**: ogni sopralluogo deve essere documentato con verbale. Se il POS manca o è inadeguato, sospendere i lavori e verbalizzare.

**Badge digitale (D.L. 159/2025)**: dal 2026 è obbligatorio il badge digitale in cantiere per la tracciabilità dei lavoratori. Verificarne la presenza durante i sopralluoghi.

**Patente a crediti potenziata (D.L. 159/2025)**: soglia minima sanzioni portata a €12.000 (da €6.000), decurtazione 5 crediti per lavoratore irregolare.

**Accordo Stato-Regioni 17/4/2025**: l'aggiornamento 40h del coordinatore passa da "obbligo a scadenza fissa" a "sospensione dell'abilitazione" (riattivabile sempre, anche in ritardo).
