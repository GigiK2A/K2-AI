# Verbali CSE — Template Operativi

Questo reference contiene i template per i 5 verbali che il CSE produce durante l'esecuzione dei lavori.
Leggi solo il template che ti serve — non caricare tutto il file se non necessario.

## Indice rapido

| # | Tipo verbale | Quando usarlo |
|---|---|---|
| V.1 | Verbale di sopralluogo CSE | Ad ogni visita in cantiere (obbligatorio) |
| V.2 | Verbale di contestazione / diffida all'impresa | Inadempienza alle prescrizioni PSC/POS |
| V.3 | Verbale di sospensione lavori | Pericolo grave e imminente (art. 92 c.1 lett. f) |
| V.4 | Verbale di riunione di coordinamento | Inizio lavori nuova impresa / lavorazioni interferenti |
| V.5 | Verbale di ripresa lavori | Dopo sospensione, a seguito di adeguamento |

---

## Istruzioni generali

**Come usare questi template:**
1. Identifica il tipo di verbale richiesto dall'utente
2. Chiedi i dati mancanti contrassegnati con `[…]`
3. Produci il verbale come file `.docx` usando la skill `docx`
4. Salva in `outputs/Verbale_[TIPO]_[CANTIERE o SITO]_[DATA].docx`

**Dati fissi del CSE** (già in `references/professionista.md`):
- Nome: **Ing. Luca Rossi**
- Studio: **Studio Associato Evolution**, Via A. Manzoni 84, 06135 Ponte San Giovanni (PG)
- Tel: 075 9114040 | Email: studioassociatoevolution@gmail.com
- Ordine Ingegneri Perugia, Sez. A, n. A2212

**Riferimento normativo comune:** D.Lgs. 9 aprile 2008, n. 81, art. 92.

---

## V.1 — Verbale di Sopralluogo CSE

**Base normativa:** art. 92 c.1 lett. a), b), c) D.Lgs. 81/08
**Periodicità:** ad ogni visita; almeno settimanale per cantieri attivi
**Conservazione:** fascicolo CSE + copia all'impresa affidataria

### Dati da raccogliere

- Cantiere (indirizzo / codice sito) e data/ora
- Persone presenti (capocantiere, DL, RLS, ecc.)
- Lavorazioni in corso e numero lavoratori
- Conformità DPI / segnaletica / opere provvisionali / PSC-POS
- Prescrizioni impartite (se presenti) e scadenza adeguamento

### Template

```
─────────────────────────────────────────────────────────────────
VERBALE DI SOPRALLUOGO CSE N. [NUMERO]
─────────────────────────────────────────────────────────────────

CANTIERE: [descrizione lavori]
INDIRIZZO / SITO: [indirizzo completo / codice sito]
COMMITTENTE: [nome/ragione sociale]
IMPRESA AFFIDATARIA: [ragione sociale]
DATA: [gg/mm/aaaa]    ORA: [hh:mm]

PRESENTI:
- Ing. Luca Rossi — CSE (Studio Associato Evolution)
- [Nome Cognome] — [qualifica: capocantiere / DL / RLS]
- [Nome Cognome] — [qualifica]

─────────────────────────────────────
SITUAZIONE RILEVATA
─────────────────────────────────────

Lavorazioni in corso: [descrizione]
Lavoratori presenti: [N]

DPI:                ☐ Conformi  ☐ Parzialmente  ☐ Non conformi
                    Note: [difformità o "nessuna"]

Segnaletica:        ☐ Conforme  ☐ Non conforme
                    Note: [o "nessuna"]

Opere provvisionali: ☐ Conformi  ☐ Parzialmente  ☐ Non presenti
                    Note: [o "nessuna"]

PSC / POS:          ☐ Piena conformità  ☐ Difformità  ☐ POS non consegnato
                    Note: [o "nessuna"]

─────────────────────────────────────
PRESCRIZIONI IMPARTITE
─────────────────────────────────────

[Se nessuna:]
Non si rilevano inadempienze. Il cantiere risulta conforme al PSC e al POS.

[Se presenti:]
Si impartiscono le seguenti prescrizioni, da attuare entro il [gg/mm/aaaa]:

1. [Prescrizione — specifica]
   Rif. normativo: [art. D.Lgs. se applicabile]
   Termine: [data]

2. [Prescrizione 2 — se presente]

Il mancato adeguamento comporterà i provvedimenti di cui all'art. 92 c.1
lett. e) e f) D.Lgs. 81/08, ivi compresa la sospensione dei lavori.

─────────────────────────────────────
PROSSIMO SOPRALLUOGO PREVISTO: [data indicativa]
─────────────────────────────────────

Verbale redatto in duplice copia; una copia è consegnata al capocantiere.

Ponte San Giovanni (PG), [gg/mm/aaaa]

Il CSE — Ing. Luca Rossi              Il Capocantiere / Resp. impresa
Studio Associato Evolution             [Nome Cognome]
_____________________________         _____________________________
```

---

## V.2 — Verbale di Contestazione / Diffida Formale

**Base normativa:** art. 92 c.1 lett. e) D.Lgs. 81/08
**Quando:** prescrizione non adempiuta, o inadempienza grave al PSC/POS
**Destinatari:** impresa affidataria + committente (in copia)
**Valore legale:** documento difensivo che tutela la posizione di garanzia del CSE

### Dati da raccogliere

- Riferimento al verbale precedente (data e numero) con la prescrizione rimasta inevasa
- Descrizione dell'inadempienza e norma/capitolo PSC violati
- Nuovo termine per l'adeguamento

### Template

```
─────────────────────────────────────────────────────────────────
VERBALE DI CONTESTAZIONE — DIFFIDA FORMALE N. [NUMERO]
─────────────────────────────────────────────────────────────────

CANTIERE: [descrizione]
INDIRIZZO / SITO: [indirizzo / codice sito]
COMMITTENTE: [nome/ragione sociale]
IMPRESA AFFIDATARIA: [ragione sociale] — L.R.: [nome]
DATA: [gg/mm/aaaa]

─────────────────────────────────────
PREMESSE
─────────────────────────────────────

Con verbale di sopralluogo n. [NUMERO] del [gg/mm/aaaa], si impartiva la seguente prescrizione con termine al [gg/mm/aaaa]:

«[Testo della prescrizione impartita]»

─────────────────────────────────────
INADEMPIENZA RILEVATA
─────────────────────────────────────

In data [gg/mm/aaaa], in sede di verifica, si constata che l'impresa NON ha provveduto all'adeguamento.

Inadempienza: [descrizione specifica]
Norma / prescrizione PSC violata: [art. D.Lgs. o Cap. PSC]

─────────────────────────────────────
DIFFIDA FORMALE
─────────────────────────────────────

Si DIFFIDA FORMALMENTE l'impresa [ragione sociale] a:

1. [Azione richiesta — specifica]
2. [Azione richiesta 2 — se presente]

entro e non oltre il [gg/mm/aaaa].

In caso di mancato adeguamento:
- Comunicazione al committente ex art. 92 c.1 lett. e) D.Lgs. 81/08
  con proposta di sospensione dell'impresa o risoluzione contrattuale.
- In presenza di pericolo imminente: sospensione immediata dei lavori
  ex art. 92 c.1 lett. f) D.Lgs. 81/08 senza ulteriore preavviso.

Copia trasmessa al committente [nome] per conoscenza.

─────────────────────────────────────

Ponte San Giovanni (PG), [gg/mm/aaaa]

Il CSE — Ing. Luca Rossi
Studio Associato Evolution
_____________________________

Per ricevuta — Il L.R. / Capocantiere [nome]
_____________________________
```

---

## V.3 — Verbale di Sospensione Lavori per Pericolo Grave e Imminente

**Base normativa:** art. 92 c.1 lett. f) D.Lgs. 81/08
**Efficacia:** immediata — i lavori si fermano al momento della firma
**Destinatari:** impresa + committente (contestuale o entro 24h)
**⚠ Nota legale:** la sospensione tutela il CSE solo se il pericolo è reale e documentato. Scatta foto sul posto — sono prova in caso di contestazione giudiziaria.

### Dati da raccogliere

- Data e ora esatta del sopralluogo
- Descrizione circostanziata del pericolo (cosa, dove, chi è esposto, perché è imminente)
- Lavorazioni sospese (tutte o solo alcune — specificare)
- Condizioni per la ripresa (una o più azioni specifiche richieste all'impresa)
- Testimoni presenti

### Template

```
─────────────────────────────────────────────────────────────────
VERBALE DI SOSPENSIONE DEI LAVORI N. [NUMERO]
art. 92, c. 1, lett. f) — D.Lgs. 9 aprile 2008, n. 81
─────────────────────────────────────────────────────────────────

CANTIERE: [descrizione]
INDIRIZZO / SITO: [indirizzo / codice sito]
COMMITTENTE: [nome/ragione sociale]
IMPRESA AFFIDATARIA: [ragione sociale]
DATA: [gg/mm/aaaa]    ORA: [hh:mm]

─────────────────────────────────────
PERICOLO RILEVATO
─────────────────────────────────────

Il sottoscritto CSE, in corso di sopralluogo, rileva la seguente
situazione di PERICOLO GRAVE E IMMINENTE:

[Descrizione dettagliata:
- cosa: es. "assenza di parapetto sul lato nord della copertura"
- dove: posizione nel cantiere
- quota di caduta / entità del rischio
- chi è esposto
- perché il pericolo è imminente]

Norma violata: [art. D.Lgs. — es. "art. 122 D.Lgs. 81/08"]
Prescrizione PSC non rispettata: [Cap. — se applicabile]

─────────────────────────────────────
PROVVEDIMENTO
─────────────────────────────────────

Il CSE dispone con effetto IMMEDIATO la sospensione di:
☐ TUTTE le lavorazioni in corso
☐ Le seguenti lavorazioni: [specificare]

I lavoratori nell'area a rischio sono allontanati immediatamente.

─────────────────────────────────────
CONDIZIONI PER LA RIPRESA
─────────────────────────────────────

La ripresa è subordinata al soddisfacimento di TUTTE le seguenti condizioni:

1. [Condizione 1 — specifica, es. "Installazione parapetto H ≥ 1 m
   con corrente intermedio e tavola fermapiedi lungo l'intero bordo esposto"]
2. [Condizione 2 — se presente]
3. Verifica e autorizzazione scritta del CSE prima della ripresa.

Copia del presente verbale è trasmessa immediatamente al committente [nome].

─────────────────────────────────────

Ponte San Giovanni (PG), [gg/mm/aaaa] ore [hh:mm]

Il CSE — Ing. Luca Rossi              Il Capocantiere [nome]
Studio Associato Evolution             dichiara di aver ricevuto copia
_____________________________         _____________________________

Testimoni (se presenti):
[Nome Cognome] — [qualifica] ___________________________
```

---

## V.4 — Verbale di Riunione di Coordinamento

**Base normativa:** art. 92 c.1 lett. b) D.Lgs. 81/08
**Quando:** avvio lavori nuova impresa; modifica rilevante al PSC; lavorazioni interferenti; riunione periodica
**Partecipanti:** CSE + rappresentante di ogni impresa presente + RLS (se nominato)

### Dati da raccogliere

- Data, ora e luogo della riunione
- Partecipanti (nome, qualifica, impresa)
- Ordine del giorno
- Punti discussi, decisioni e prescrizioni

### Template

```
─────────────────────────────────────────────────────────────────
VERBALE DI RIUNIONE DI COORDINAMENTO N. [NUMERO]
─────────────────────────────────────────────────────────────────

CANTIERE: [descrizione]
INDIRIZZO / SITO: [indirizzo / codice sito]
COMMITTENTE: [nome/ragione sociale]
DATA: [gg/mm/aaaa]  ORA: [hh:mm]
LUOGO: [es. "in cantiere" / "presso Studio Evolution" / "videoconferenza"]

─────────────────────────────────────
PRESENTI
─────────────────────────────────────

| Nome e Cognome     | Qualifica                    | Impresa / Studio         |
|--------------------|------------------------------|--------------------------|
| Ing. Luca Rossi    | CSE                          | Studio Associato Evolution |
| [Nome]             | [capocantiere / legale rapp.]| [Impresa]                |
| [Nome]             | [RLS]                        | [Impresa]                |
| [Nome]             | [DL / committente]           | [Studio / azienda]       |

─────────────────────────────────────
ORDINE DEL GIORNO
─────────────────────────────────────

1. [es. "Avvio lavori Impresa X — illustrazione PSC"]
2. [es. "Interferenze lavorazioni strutturali / impianti"]
3. Varie ed eventuali

─────────────────────────────────────
SVOLGIMENTO
─────────────────────────────────────

Punto 1 — [Titolo]
[Resoconto discussione e decisioni]

Punto 2 — [Titolo]
[Resoconto]

Varie ed eventuali: [Resoconto o "Nessun argomento"]

─────────────────────────────────────
PRESCRIZIONI
─────────────────────────────────────

1. [Prescrizione — a carico di: [impresa] — entro: [data]]
[Oppure: "Nessuna prescrizione. Imprese confermano conformità al PSC."]

─────────────────────────────────────
PROSSIMA RIUNIONE: [data / "da concordare"]
─────────────────────────────────────

Ponte San Giovanni (PG), [gg/mm/aaaa]

Ing. Luca Rossi (CSE)     [Partecipante 1]     [Partecipante 2]
_________________         _________________    _________________
```

---

## V.5 — Verbale di Ripresa Lavori (dopo sospensione)

**Base normativa:** art. 92 c.1 lett. f) D.Lgs. 81/08 — a contrario
**Prerequisito:** il CSE deve aver verificato personalmente l'adeguamento in sopralluogo

### Dati da raccogliere

- Riferimento al verbale di sospensione (numero e data)
- Data del sopralluogo di verifica
- Adeguamenti verificati (cosa ha fatto concretamente l'impresa)
- Adeguamento completo o parziale

### Template

```
─────────────────────────────────────────────────────────────────
VERBALE DI RIPRESA LAVORI N. [NUMERO]
─────────────────────────────────────────────────────────────────

CANTIERE: [descrizione]
INDIRIZZO / SITO: [indirizzo / codice sito]
COMMITTENTE: [nome/ragione sociale]
IMPRESA AFFIDATARIA: [ragione sociale]

DATA SOPRALLUOGO DI VERIFICA: [gg/mm/aaaa]  ORA: [hh:mm]
RIFERIMENTO: Verbale di Sospensione n. [NUMERO] del [gg/mm/aaaa]

─────────────────────────────────────
ESITO DELLA VERIFICA
─────────────────────────────────────

Il CSE constata che l'impresa ha provveduto ai seguenti adeguamenti:

1. [Adeguamento verificato — descrizione specifica di quanto realizzato]
2. [Adeguamento 2 — se presente]

[Se parziale: "Le condizioni 1 e 2 risultano soddisfatte. La condizione 3
([descrizione]) non è ancora completata."]

─────────────────────────────────────
AUTORIZZAZIONE ALLA RIPRESA
─────────────────────────────────────

[Se completo:]
Il CSE autorizza la ripresa di TUTTE le lavorazioni sospese, con effetto immediato.

[Se parziale:]
Il CSE autorizza la ripresa delle sole lavorazioni: [elenco]
Rimane sospesa: [lavorazione] — da completare entro: [data]

─────────────────────────────────────
PRESCRIZIONI RESIDUE
─────────────────────────────────────

[Se presenti: indicare prescrizioni]
[Oppure: "Nessuna prescrizione residua."]

─────────────────────────────────────

Ponte San Giovanni (PG), [gg/mm/aaaa]

Il CSE — Ing. Luca Rossi              Il Capocantiere [nome]
Studio Associato Evolution
_____________________________         _____________________________
```

---

## Note operative per il CSE

**Numerazione:** registro progressivo per tipo per anno (es. SOPL/2026/01, CONT/2026/01, SOSP/2026/01…)

**Archivio difensivo:**
- Ogni verbale va firmato da tutti i presenti (o annotata la mancata firma)
- Conservato nel fascicolo CSE
- V.2 e V.3: inviare copia al committente tramite **PEC o raccomandata AR**
- V.3: allegare sempre le foto scattate durante il sopralluogo

**Integrazione con il PSC:** se il verbale comporta una modifica (nuova impresa, variante lavorativa, aggiornamento rischi), aggiornare il PSC e allegare il verbale alla revisione come appendice.
