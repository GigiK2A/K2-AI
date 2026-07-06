# Struttura Documenti — Template di Redazione

## DOC 1 — SCIA art. 45

**Intestazione:** lettera formale a più destinatari (DPU, SUAP, Poteri Sostitutivi, Municipio, ARPA Lazio per Roma; Comune + ARPA per comuni provincia)

**Struttura:**

```
[Numero reversale] / [anno]

Spett.le [DESTINATARI — vedi references/documenti-richiesti.md]

SEGNALAZIONE CERTIFICATA DI INIZIO ATTIVITÀ
ai sensi dell'art. 45 del Codice delle Comunicazioni Elettroniche (D.Lgs. n. 259/2003 s.m.i.)

TIPOLOGIA INTERVENTO: Modifica radioelettrica Stazione Radio Base per rete di
                       telefonia mobile di Iliad Italia S.p.A.
CODICE IMPIANTO: [CODICE] – [NOME SITO]
INDIRIZZO: [Comune e Municipio] - [Via, numero civico] - Foglio n. [N], P.lla n. [N], Sez. [X]

ILIAD ITALIA S.p.A. [...dati fissi...]

in persona del Sig. Andrea Longari [...procura fisso...]

Premesso che [testo boilerplate premessa]

SEGNALA
l'inizio dell'attività relativa alla modifica radioelettrica di un impianto di
telecomunicazioni per telefonia mobile denominato [CODICE] – [NOME SITO], sito nel
Comune di [COMUNE], [Municipio se Roma], in [indirizzo], [...dati catastali...]

Il progettista incaricato è: [TECNICO INCARICATO] [...dati tecnico...]

ELENCO ALLEGATI
1. [SCIA] — solo come richiamo al documento stesso
2. [DELEGA]
3. [MISE-PROCURA]
4. [RT]
5. [PDM]
6. [ASSEVERAZIONI]
7. [B40/RELAIE]
8. [IMPEGNO ARPA]
9. [DICH. SOSTITUTIVA]
10. [ATTO D'OBBLIGO]
[11. DIAGRAMMI ANGOLARI — se presenti]
[13. NULLA OSTA CELLNEX — se sito Cellnex]

[Luogo, Data]
ILIAD ITALIA S.p.A.
Andrea Longari
Procuratore Speciale
```

---

## DOC 2 — Delega alla Presentazione

**Oggetto:** Incarico per la sottoscrizione digitale e la presentazione telematica

**Struttura:**

```
Spett.le [DESTINATARI — stessi della SCIA]

INCARICO PER LA SOTTOSCRIZIONE DIGITALE E LA PRESENTAZIONE TELEMATICA
(art.19 L. 241/1990; art. 38 DPR 445/2000)

SCIA ai sensi dell'art. 45 D.Lgs. 259/2003 s.m.i.
TIPOLOGIA: Modifica radioelettrica SRB Iliad Italia S.p.A.
CODICE: [CODICE] [NOME SITO]
INDIRIZZO: [Comune e Municipio] - [Via, n. civico] - Foglio [N], P.lla [N], [Sez.]

La ILIAD ITALIA S.p.A. [...dati fissi + procura Andrea Longari...]

delega
i professionisti di seguito indicati alla sottoscrizione digitale e alla presentazione
telematica della pratica in oggetto, conferendo loro ogni facoltà di eseguire eventuali
rettifiche di errori formali inerenti alla modulistica prodotta:

[TECNICO INCARICATO] C.F. [CF TECNICO], iscritto all'Ordine [...] con il n. [N.ISCRIZIONE],
domiciliato per la carica presso K2A Srls in Via Alessandro Manzoni, 84 – Perugia (PG);

In fede
Per Accettazione
[TECNICO INCARICATO]
(K2A srls)
(Documento firmato digitalmente)
```

---

## DOC 4 — RT Relazione Tecnico Illustrativa

**Titolo pagina di copertina:**
"Progetto di modifica radioelettrica di impianto tecnologico di radiotelecomunicazioni per telefonia cellulare Sistema [SISTEMA RADIOMOBILE]"

**Struttura:**

```
RELAZIONE TECNICO-ILLUSTRATIVA

Premessa
Oggetto: Progetto per la modifica radioelettrica di una Stazione Radio Base per la
telefonia mobile a servizio del gestore ILIAD ITALIA SPA, da realizzarsi nel Comune di
[COMUNE], [Municipio], su [tipo supporto: edificio / terreno] in [VIA], [N.CIVICO],
distinto al N.C.E.U. di [Comune] al Foglio [N], P.lla n. [N], Sez. [X].

Il sottoscritto [TECNICO], in qualità di progettista incaricato da ILIAD Italia S.p.A.
con studio c/o K2A s.r.l.s. [...], relaziona quanto segue.

DATI IDENTIFICATIVI DELL'IMMOBILE
[tabella: Codice/Nome sito | Indirizzo | Comune | Proprietà | Catasto | Coordinate]

STRALCIO P.R.G. (da compilare post verifica urbanistica)
- Sistemi e regole (Tav. 3_10): [DA COMPILARE]
- Rete ecologica (Tav. 4_10): [DA COMPILARE]
- Carta per la qualità (Tav. G1_10): [DA COMPILARE]

STRALCIO P.T.P.R. (da compilare post verifica paesaggistica)
- Sistemi ed ambiti del paesaggio (Tav. A): [DA COMPILARE]
- Beni Paesaggistici (Tav. B): [DA COMPILARE]
- Beni Culturali (Tav. C): [DA COMPILARE]

DESCRIZIONE DELL'INTERVENTO
[descrizione tecnica dell'impianto: tipo antenne, settori, sistema radiomobile,
 tipo di supporto, caratteristiche dell'edificio/terreno, modifica rispetto allo stato
 di fatto]

CONFORMITÀ NORMATIVA
[richiamo alle norme: D.Lgs. 259/2003 art. 45, L. 36/2001, DPCM 8/7/2003,
 compatibilità con PRG]

[Luogo, Data]
[TECNICO INCARICATO]
```

---

## DOC 6 — Asseverazioni

Il documento contiene **5 asseverazioni distinte e consecutive**, una per ciascuna dichiarazione tecnica obbligatoria per Roma Capitale. Ogni asseverazione ha intestazione completa ai destinatari, oggetto proprio, corpo specifico, e firma in calce (il documento si sviluppa su più pagine, una per asseverazione).

**Le 5 asseverazioni obbligatorie (Roma Capitale) nell'ordine:**

1. **Asseverazione indirizzo completo** — attesta indirizzo, dati catastali e coordinate WGS84
2. **Asseverazione vincoli** — attesta gli esiti della verifica urbanistica/paesaggistica (PRG, PTPR, ENAC, sismica, vincoli)
3. **Asseverazione di legittimità** — attesta che l'impianto esistente è autorizzato ex lege e conforme agli ultimi titoli (elenca tutti i protocolli)
4. **Asseverazione di idoneità statica** — attesta che la modifica radioelettrica non comporta modifiche strutturali al manufatto
5. **Asseverazione degli impianti** — attesta la conformità degli impianti al D.M. 37/08

**Intestazione comune (ripetuta all'inizio di ciascuna asseverazione, Roma Capitale):**

```
Spett.le
ROMA CAPITALE
Dipartimento Programmazione Urbanistica
Direzione Pianificazione Generale
Servizio Pianificazione Ambientale e Demanio
U.O. – Piano Regolatore
Ufficio Stazioni Radio Base
Viale della Civiltà del Lavoro, 10
00144 - Roma
pec: protocollo.programmazioneurbanistica@pec.comune.roma.it

Spett.
ROMA CAPITALE
Direzione S.U.A.P.
Dipartimento Sviluppo Economico e Attività Produttive
Via dei Cerchi, 6 00186 Roma
pec: protocollo.attivitaproduttive@pec.comune.roma.it

Spett.le
MUNICIPIO [N ROMANO] (ex [N])
[Indirizzo Municipio]
[CAP] – Roma
pec: protocollo.municipioroma[NN]@pec.comune.roma.it
(da inoltrare a cura del DPU)
```

**Formula soggetto comune (ripetuta in ciascuna asseverazione):**

```
Il sottoscritto [TECNICO], C.F. [CF], domiciliato per la carica presso K2A S.r.l.s.
in Via Alessandro Manzoni, n°84, Perugia (PG), iscritto all'Ordine degli Ingegneri
di [PROVINCIA] con numero [N.ISCRIZIONE], in qualità di tecnico incaricato da
ILIAD ITALIA S.p.A., relativamente all'impianto di telecomunicazioni in oggetto
```

**Firma in calce comune (ripetuta in ciascuna asseverazione):**

```
[Luogo], [Data]
[TECNICO INCARICATO]
```

---

### DOC 6.1 — Asseverazione Indirizzo Completo

```
[INTESTAZIONE COMUNE]

OGGETTO: Asseverazione indirizzo completo relativa alla modifica radioelettrica di
una Stazione Radio base per rete di telefonia mobile di ILIAD ITALIA S.P.A.
denominata [CODICE] - [NOME SITO], [Via, n. civico], [Municipio] – [Comune] ([PROV]).

[FORMULA SOGGETTO COMUNE]
ASSEVERA CHE

INDIRIZZO COMPLETO
[Via, n. civico],
[Municipio] – [Comune] ([PROV])

DATI CATASTALI
N.C.E.U. di [Comune] Foglio [N], P.lla [N], Sez. [X]

COORDINATE GEOGRAFICHE WGS84
Lat. [XX.XXXXXX] N; Long. [XX.XXXXXX] E

[FIRMA IN CALCE]
```

---

### DOC 6.2 — Asseverazione Vincoli

```
[INTESTAZIONE COMUNE]

OGGETTO: Asseverazione vincoli relativa alla modifica radioelettrica di una Stazione
Radio base per rete di telefonia mobile di ILIAD ITALIA S.P.A. denominata
[CODICE] - [NOME SITO], [Via, n. civico], [Municipio] – [Comune] ([PROV]).

[FORMULA SOGGETTO COMUNE]

A seguito delle verifiche effettuate presso gli uffici competenti sull'area sita
nel Comune di [Comune], distinto nel N.C.E.U. di [Comune] Foglio [N], P.lla [N],
Sez. [X], è emerso che:

STRALCIO P.R.G.
Sistemi e regole (Tav. 3_[ANNO]): [ESITO]
Rete ecologica (Tav. 4_[ANNO]): [ESITO]
Carta per la qualità (Tav. G1_[ANNO]): [ESITO]

STRALCIO P.T.P.R.
Sistemi ed ambiti del paesaggio (Tav. A): [ESITO]
Beni Paesaggistici (Tav. B): [ESITO]
Beni del Patrimonio Naturale e Culturale (Tav. C): [ESITO]
Recepimento delle proposte comunali di modifica dei PTP (Tav. D): [ESITO]

Mappe di vincolo limitazioni relative agli ostacoli ed ai pericoli per la
navigazione aerea (Aeroporto "[NOME AEROPORTO]"): [ESITO]

Zona Sismica: [ZONA — es. "3A - Zona con pericolosità sismica bassa"]

Vincoli: [ELENCO VINCOLI — es. "A.Mi. – ininfluente ai fini dell'intervento"]

Si precisa che:
- Per le opere in progetto non è necessario richiedere il Parere del Dipartimento
  Ciclo dei Rifiuti visto che l'area di intervento non rientra tra quelle indicate
  all'art. 5 co. 5 del Nuovo Regolamento del Comune di Roma (Deliberazione n. 78
  del 27/09/2024).
- Per le opere in progetto non è necessario acquisire il parere dell'Aeronautica
  Militare in quanto non sono previste modifiche plano-altimetriche all'impianto
  esistente.

[FIRMA IN CALCE]
```

**Note di compilazione DOC 6.2:**
- Gli esiti P.R.G. tipici: "Sistema insediativo – Città consolidata – Tessuto di
  espansione novecentesca a tipologia edilizia libera – T3" / "Area non caratterizzata"
- Gli esiti P.T.P.R. tipici: "Paesaggio degli Insediamenti Urbani" / "Area non
  caratterizzata" / "Sistema dell'insediamento archeologico – Viabilità antica
  (fascia di rispetto 50mt)" / "Accolta – Parzialmente accolta, con prescrizione"
- ENAC tipico: "Area interessata da limitazione e non interferente con la superficie
  di inviluppo"
- I due paragrafi "Si precisa che" sono boilerplate Roma Capitale e vanno mantenuti

---

### DOC 6.3 — Asseverazione di Legittimità

```
[INTESTAZIONE COMUNE]

OGGETTO: Asseverazione di legittimità relativa alla modifica radioelettrica di
una Stazione Radio base per rete di telefonia mobile di ILIAD ITALIA S.P.A.
denominata [CODICE] - [NOME SITO], [Via, n. civico], [Municipio] – [Comune] ([PROV]).

[FORMULA SOGGETTO COMUNE]
ASSEVERA

che l'impianto Iliad esistente è autorizzato ex lege e che lo stato attuale è
conforme agli ultimi titoli autorizzativi:

- S.C.I.A. ai sensi dell'art. 45 del D.Lgs. 259/2003 s.m.i. trasmessa al Comune
  di [Comune] a mezzo pec in data [DATA] e assunta al prot. n. [PROT] del [DATA];
- Parere favorevole Arpa Lazio – Sezione Provinciale di [Prov] trasmesso con
  prot. n. [PROT] del [DATA];
- Parere favorevole del Dipartimento Ciclo dei Rifiuti (VAP) trasmesso con
  prot. n. [PROT] del [DATA];
- Parere favorevole ENAC prot. n. [PROT] del [DATA];
- Determinazione di conclusione della conferenza dei servizi trasmessa dal
  Comune di [Comune] con prot. n. [PROT] del [DATA];
- S.C.I.A. ai sensi dell'art. 45 del D.Lgs. 259/2003 s.m.i. presentata al Comune
  di [Comune] tramite PEC in data [DATA], registrata con prot. n. [PROT DPU]
  del [DATA] (DPU) e prot. n. [PROT SUAP] del [DATA] (SUAP).

[FIRMA IN CALCE]
```

**Note di compilazione DOC 6.3:**
- Elencare l'intera storia autorizzativa del sito in ordine cronologico
- Includere solo i protocolli effettivamente esistenti; se il sito non ha VAP o
  ENAC saltare la riga
- L'ultima riga è tipicamente la SCIA immediatamente precedente a quella in
  redazione (quella che legittima lo stato di fatto)

---

### DOC 6.4 — Asseverazione di Idoneità Statica

```
[INTESTAZIONE COMUNE]

OGGETTO: Asseverazione di idoneità statica relativa alla modifica radioelettrica
di una Stazione Radio base per rete di telefonia mobile di ILIAD ITALIA S.P.A.
denominata [CODICE] - [NOME SITO], [Via, n. civico], [Municipio] – [Comune] ([PROV]).

[FORMULA SOGGETTO COMUNE]
ASSEVERA

che la modifica in progetto riguarda un adeguamento radioelettrico senza apportare
modifiche strutturali al manufatto esistente.

[FIRMA IN CALCE]
```

**Note di compilazione DOC 6.4:**
- Formula standard invariabile — usare solo quando effettivamente non ci sono
  modifiche strutturali. Se ci fossero modifiche strutturali, sostituire con
  asseverazione di idoneità statica supportata da relazione di calcolo.

---

### DOC 6.5 — Asseverazione degli Impianti

```
[INTESTAZIONE COMUNE]

OGGETTO: Asseverazione degli impianti relativa alla modifica radioelettrica di
una Stazione Radio base per rete di telefonia mobile di ILIAD ITALIA S.P.A.
denominata [CODICE] - [NOME SITO], [Via, n. civico], [Municipio] – [Comune] ([PROV]).

[FORMULA SOGGETTO COMUNE]
ASSEVERA

che gli impianti relativi all'impianto di comunicazioni elettroniche in oggetto
saranno realizzati in conformità a quanto previsto nel D.M. 37/08.

[FIRMA IN CALCE]
```

**Note di compilazione DOC 6.5:**
- Formula standard invariabile — riferimento fisso al D.M. 37/08 (Decreto
  Ministero Sviluppo Economico).

---

**Note generali DOC 6:**
- Le 5 asseverazioni devono essere redatte come **unico documento .docx** con
  salti pagina tra una asseverazione e l'altra (non come file separati).
- Tutti i dati anagrafici del sito (indirizzo, catasto, coordinate, codice,
  municipio, comune) devono essere **identici** in tutte le 5 asseverazioni e
  **coerenti** con la Relazione Tecnica (DOC 4) e la SCIA (DOC 1).
- Tutti i dati del tecnico (nome, CF, ordine, numero iscrizione) devono essere
  **identici** in tutte le 5 asseverazioni.
- Luogo e data di firma devono essere **identici** in tutte le 5 asseverazioni.
- Le informazioni specifiche di DOC 6.2 (vincoli) e DOC 6.3 (legittimità) si
  estraggono dalla Relazione Tecnica; DOC 6.1 dai dati anagrafici del sito;
  DOC 6.4 e DOC 6.5 sono formule standard invariabili.

---

## DOC 7 — B40/RELAIE — Analisi di Impatto Elettromagnetico

**Struttura completa (indice):**

```
1. ANAGRAFE IMPIANTO
   1.1 Caratteristiche di identificazione dell'impianto
       [tabella: codice, nome, indirizzo, comune, provincia, regione, quota s.l.m., coordinate WGS84, coordinate UTM]
   1.2 Gestore dell'impianto
       [tabella: denominazione, indirizzo sede legale, CAP, comune, provincia, regione]

2. PREMESSA
   [scopo del documento: valutare l'intensità del campo elettrico generato dall'impianto]

3. NORMATIVA RIGUARDANTE I LIMITI DI ESPOSIZIONE
   3.1 Riferimenti normativi
       [L. 36/2001, DPCM 8/7/2003, D.Lgs. 259/2003, D.M. MATTM 2/12/2014,
        Raccomandazione CEE 1999/519/CE, Direttiva 2013/35/UE]
   3.2 Legislazione Italiana (D.P.C.M. del 8 LUGLIO 2003)
       [tabella limiti: 20 V/m, 6 V/m valore attenzione, 6 V/m obiettivo qualità]

4. DESCRIZIONE DELL'AREA E DEL PUNTO DI INSTALLAZIONE
   4.1 Descrizione del terreno circostante
   4.2 Planimetria in scala 1:2000
   4.3 Valutazione delle quote degli edifici e dei punti significativi
   4.4 Documentazione fotografica [INSERIRE FOTO SITO]

5. CARATTERISTICHE RADIOELETTRICHE DELLA SRB
   5.1 Descrizione dell'impianto
   5.2 Caratteristiche dei sistemi di antenna [tabella antenne per settore]
   5.3 Gamme di frequenza di ricezione e trasmissione [tabella frequenze/potenze]
   5.4 Collegamenti punto-punto ponte radio [se presenti]

6. SCHEDA RADIO DELL'IMPIANTO
   [tabella dettagliata: settore, frequenza, EIRP, azimuth, tilt, tipo antenna, altezza]

7. VALUTAZIONE DELL'IMPATTO ELETTROMAGNETICO
   7.1 Introduzione
   7.2 Individuazione punti significativi e misure del campo EM preesistente
       7.2.1 Sopralluogo e misure di fondo
       7.2.2 Metodologia di misura [strumenti, norma CEI, calibrazione]
       7.2.3 Punti di misura e di stima [tabella punti con coordinate e tipo]
       7.2.4 Planimetria con indicazione dei punti [INSERIRE PLANIMETRIA]
       7.2.5 Documentazione fotografica dei punti [INSERIRE FOTO PUNTI]

8. VALUTAZIONE DELLE INTENSITÀ DEI CAMPI ELETTRICI
   8.1 Valutazione per frequenze 3 < f < 3000 MHz [calcoli teorici/simulazione]
   8.2 Valutazione per frequenze 3 < f < 300 GHz [solo se mmWave presenti]
   8.3 Volumi di Rispetto
       8.3.1 Limiti di Esposizione (20 V/m)
       8.3.2 Limiti di Attenzione (6 V/m)
   8.4 Elaborati Grafici
       8.4.1 Isolinee orizzontali [6-15-20-40 V/m] su planimetria 1:2000
       8.4.2 Volumi di rispetto e sezioni verticali per settore

9. CONCLUSIONI E ATTESTAZIONE DI CONFORMITÀ
   [attestazione che i valori calcolati sono inferiori ai limiti DPCM 8/7/2003;
    valore di campo EM stimato inferiore a 6 V/m nei punti significativi]

10. ALLEGATI
    10.1 Cartografia con indicazione settori e altre emittenti
    10.2 Datasheet antenne
    10.3 Curriculum del tecnico incaricato
    10.4 Copia dei certificati di calibrazione
```

---

## DOC 8 — Impegno al Pagamento ARPA Roma

Documento più breve, intestato solo ad **ARPA Lazio**.

```
Spett.le ARPALAZIO — Sede Provinciale di Roma [...]

OGGETTO: Impegno al pagamento art. 45 [...]

ILIAD ITALIA S.p.A. [...dati fissi + procura Andrea Longari...]
SI IMPEGNA al pagamento delle tariffe previste dall'art. 45 [...]
per l'impianto denominato [CODICE] – [NOME SITO] in [indirizzo].

[Luogo, Data]
Andrea Longari — Procuratore Speciale
```

---

## DOC 9 — Dichiarazione Sostitutiva ALPHA24

```
DICHIARAZIONE SOSTITUTIVA DELL'ATTO DI NOTORIETÀ
(ART.47 D.P.R. 28 dicembre 2000, n.445)

Oggetto: Dichiarazione sostitutiva [...] relativamente all'adozione del coefficiente di
riduzione della potenza in antenna α24h, per la modifica radioelettrica di un impianto
di telefonia mobile, sito nel Comune di [COMUNE], [Municipio], in [VIA, N.CIVICO]
- Foglio [N], P.lla n. [N], Sez. [X].
Codice impianto: [CODICE] - [NOME SITO]

La ILIAD ITALIA S.p.A. [...dati fissi + procura Andrea Longari...]

Premesso che:
con Decreto del Ministero Dell'Ambiente e della Tutela del Territorio e del Mare (MATTM)
2 dicembre 2014 [...linee guida α24h...]

il 31 dicembre 2023 è entrata in vigore la legge n. 214/2023 che, all'art. 10, ha disposto
la modifica radioelettrica dei limiti dei campi elettromagnetici;

dichiara
che il valore di α24h, da applicare nelle stime previsionali per la modifica radioelettrica
dell'impianto [CODICE] – [NOME SITO], è pari a [VALORE α24h].

[Luogo, Data]
Andrea Longari — Procuratore Speciale
```

---

## DOC 10 — Atto Unilaterale d'Obbligo

```
Spett.le [DESTINATARI — stessi SCIA]

OGGETTO: ATTO UNILATERALE D'OBBLIGO

ILIAD ITALIA S.P.A. [...dati fissi + procura Andrea Longari...]

Con la presente
SI IMPEGNA
Entro il termine di 3 mesi a far data dalla fine dell'utilizzazione dell'Impianto
denominato [CODICE] – [NOME SITO], a dismettere l'impianto, a smontare, demolire ed
asportare tutto quanto installato ed a ricostruire lo stato dei luoghi preesistente
a propria cura e spese.

[Luogo, Data]
Andrea Longari
Procuratore Speciale
Iliad Italia SpA
(Documento firmato digitalmente)

La Scrivente resta a disposizione per qualsiasi chiarimento e richiesta al seguente indirizzo:
Arch. Benedetta Bellussi (Permit Coordinator) - cell 3519174637 – mail: bbellussi@it.iliad.com

Si prega di inoltrare al seguente indirizzo eventuali comunicazioni formali:
PEC: svilupporete.iliaditalia@legalmail.it
```
