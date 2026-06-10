---
name: phil-etica
description: >
  Etica normativa e metaetica basata su MIT 24.231 Ethics (Brink) + MIT 24.00. Usa
  SEMPRE per: utilitarismo (Bentham, Mill, preferenze vs benessere), deontologia
  kantiana (imperativo categorico, autonomia, doveri morali), etica della virtù
  (Aristotele, eudaimonia, carattere morale), metaetica (realismo morale, relativismo,
  soggettivismo, emotivismo), dilемmi etici, giustizia, obblighi morali, responsabilità,
  punizione, diritti, contractualismo. Attiva per: "cosa è giusto fare", "etica",
  "utilitarismo", "imperativo categorico Kant", "virtù Aristotele", "dilemma etico",
  "trolley problem", "relativismo morale", "obblighi morali", "coscienza", "punizione",
  "giustizia distributiva", "diritti umani", "verità morale", "metaetica".
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --materia tributario --limit 5
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

Knowledge pack norme: `~/normattiva_ai/knowledge_packs/tributario/`

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Etica (MIT 24.231 — Brink + MIT 24.00)

## La domanda fondamentale

**Cosa dovremmo fare, e perché?** L'etica normativa risponde cercando principi 
generali di condotta giusta. La metaetica chiede se questi principi possano essere
*veri* in qualche senso — o se "giusto" e "sbagliato" siano mere proiezioni di
sentimenti soggettivi.

## Struttura dell'etica filosofica

```
METAETICA             → Che cos'è la moralità? Le affermazioni morali possono essere vere?
  ↓
ETICA NORMATIVA       → Quali principi determinano cosa è giusto?
  ↓
ETICA APPLICATA       → Come si applicano questi principi a casi concreti?
```

## Le tre grandi teorie normative

### 1. Utilitarismo (Bentham, Mill)

**Principio fondamentale**: Un'azione è giusta se e solo se massimizza il benessere
complessivo di tutti i soggetti coinvolti.

| Versione | Unità di valore | Autore |
|----------|----------------|--------|
| Edonista | Piacere - dolore | Bentham |
| Delle preferenze | Soddisfazione dei desideri | Mill, Singer |
| Del benessere oggettivo | Lista di beni oggettivi | Parfit |

**Forza**: cattura l'idea che le conseguenze contano; imparzialità morale.

**Obiezioni classiche**:
- *Problema della giustizia*: giustifica violazioni di diritti individuali se il totale
  di benessere è maggiore (sacrificare un innocente per salvare cinque?)
- *Problema dell'integrità*: richiede di abbandonare i propri progetti e valori
- *Demandingness*: richiede di donare quasi tutto finché il costo marginale = beneficio
- *Incommensurabilità*: come misurare e aggregare il benessere di persone diverse?

### 2. Deontologia Kantiana (Kant)

**Principio fondamentale**: Le azioni hanno valore morale intrinseco, indipendentemente
dalle conseguenze, quando derivano da un senso del dovere e rispettano l'autonomia
razionale delle persone.

**Imperativo Categorico** — tre formulazioni equivalenti:
1. **Universalizzabilità**: "Agisci solo secondo quella massima per cui puoi al tempo
   stesso volere che diventi una legge universale."
2. **Formula dell'umanità**: "Agisci in modo da trattare l'umanità, sia nella tua
   persona sia in quella di ogni altro, sempre come fine, mai semplicemente come mezzo."
3. **Formula del regno dei fini**: "Agisci secondo massime di un membro legislatore
   universale in un possibile regno dei fini."

**Forza**: rispetta la dignità e l'autonomia delle persone; cattura l'idea che
alcune cose sono semplicemente sbagliate indipendentemente dalle conseguenze.

**Obiezioni classiche**:
- *Rigidità*: niente bugie nemmeno per salvare vite (il nazista alla porta)
- *Conflitti tra doveri*: cosa fare quando due doveri si contraddicono?
- *Fondamento*: da dove viene l'autorità dell'imperativo categorico?

### 3. Etica della Virtù (Aristotele)

**Principio fondamentale**: La moralità non riguarda principalmente le azioni, ma
il *carattere*. Una persona virtuosa è chi ha sviluppato le disposizioni (virtù)
che la portano ad agire bene e a fiorire come essere umano (eudaimonia).

| Concetto | Spiegazione |
|---------|-------------|
| Eudaimonia | "Felicità" nel senso di fioritura umana, vita ben vissuta |
| Virtù | Disposizione del carattere a scegliere il giusto mezzo tra due estremi |
| Dottrina del giusto mezzo | Coraggio = via di mezzo tra codardia e temerarietà |
| Phronesis | Saggezza pratica — capacità di discernere il giusto in ogni situazione |
| Aretē | Eccellenza o virtù: ciò che rende qualcosa eccellente nel suo genere |

**Forza**: cattura l'importanza del carattere, dell'educazione morale, del contesto.

**Obiezioni classiche**:
- Circolarità: un'azione virtuosa è quella che farebbe una persona virtuosa (come
  riconoscere chi è virtuoso?)
- Variabilità culturale: le virtù variano tra culture
- Guida limitata: non fornisce regole chiare per casi difficili

## Metaetica — la struttura profonda della moralità

| Posizione | Tesi | Esponenti |
|-----------|------|-----------|
| Realismo morale | Ci sono fatti morali oggettivi, indipendenti da noi | Parfit, Brink |
| Costruttivismo | Le verità morali sono costruite dalla ragione/accordo | Kant, Rawls |
| Emotivismo | "X è sbagliato" = espressione di disapprovazione, non verità | Ayer |
| Relativismo | La moralità varia per cultura, nessuna è oggettivamente superiore | |
| Errore-teoria | Le affermazioni morali pretendono di essere vere ma sono tutte false | Mackie |
| Soggettivismo | Le affermazioni morali descrivono stati psicologici del parlante | |

**Argomento di Mackie contro il realismo**: Le proprietà morali oggettive sarebbero
"strane" (ontologicamente bizzarre) e inspiegabile come le conosceremo (queerness).

## Casi dilemmatici classici

| Caso | Domanda | Tensione |
|------|---------|---------|
| Trolley Problem | Deviare il tram per salvare 5 uccidendo 1? | Consequenzialismo vs deontologia |
| Fat Man | Spingere una persona grassa per fermare il tram? | Uccidere vs lasciar morire |
| Violinista (Thomson) | Sei connesso a un violinista famoso per 9 mesi | Aborto e diritti corporei |
| Sacrificare l'innocente | Uccidere uno per organi per salvare cinque? | Utilitarismo estremo |
| Bugie pietose | Mentire ai nazisti per proteggere gli ebrei | Doveri assoluti vs conseguenze |

## Frankfurt e la responsabilità morale

Harry Frankfurt: la responsabilità morale non richiede il libero arbitrio nel senso
incompatibilista, ma richiede che tu abbia **volontà di secondo ordine** — che tu
voglia avere i desideri che hai. Un tossicodipendente che vuole smettere ma non ci
riesce non è pienamente responsabile; un tossicodipendente che non vuole smettere
e agisce di conseguenza lo è di più.

## Punto operativo K2-AI

L'etica applicata emerge in ogni contesto professionale: decisioni di IA e algoritmi,
etica medica, dilemmi aziendali (whistleblowing, greenwashing), giustizia distributiva
nelle politiche pubbliche. Il framework K2-AI: identificare quale teoria normativa
parla a favore e quale contro ogni opzione, poi valutare quale considerazione pesa
di più nel contesto specifico.

## Connessioni nell'ecosistema

- `phil-orchestrator` — punto di ingresso per questioni etiche complesse
- `phil-metafisica` — libero arbitrio e responsabilità morale (Frankfurt)
- `phil-politica` — giustizia distributiva, diritti, contratto sociale
- `phil-tecnologia-AI` — etica dell'intelligenza artificiale e degli algoritmi
- `psy-decisioni` — psicologia delle scelte morali, bias etici
- `diritto-italiano` — il diritto come codificazione dell'etica
