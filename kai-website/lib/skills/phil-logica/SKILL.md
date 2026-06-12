---
name: phil-logica
description: >
  Logica formale basata su MIT 24.241 Logic I (McGee). Usa SEMPRE per: logica
  proposizionale, logica del predicato, validità e correttezza degli argomenti,
  tavole di verità, alberi di refutazione, dimostrazioni formali, modus ponens,
  modus tollens, quantificatori universali ed esistenziali, formalizzazione del
  linguaggio naturale, paradossi logici, sillogismi, inferenze. Attiva per:
  "argomento logicamente valido", "formalizzare in logica", "tavola di verità",
  "Modus Ponens Tollens", "sillogismo", "implicazione logica", "quantificatori",
  "logica del predicato", "se P allora Q", "la conclusione segue dalle premesse",
  "dimostrare che è valido", "fallacia logica", "paradosso del mentitore",
  "dimostrazione per assurdo", "albero di refutazione".
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
python3 ~/normattiva_ai/tools/rag_normattiva.py "<query>" --limit 5
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

Knowledge pack norme: (skill generalista — nessun pack)

### ⚠️ Disclaimer obbligatorio (chiusura output)
> *Il presente documento ha finalità informative e di ricerca giuridica. **Non costituisce parere legale** né si sostituisce alla consulenza di un avvocato abilitato. Le citazioni normative e giurisprudenziali (italiane, UE, CEDU, amministrative, di legittimità) sono verificate sulle fonti ma l'utente è tenuto a verificarne il testo vigente sulle fonti ufficiali (normattiva.it, cortecostituzionale.it, eur-lex.europa.eu, hudoc.echr.coe.it, giustizia-amministrativa.it, italgiure.giustizia.it) prima di qualsiasi uso operativo. Il DB CEDU copre solo casi con Italia convenuta; CdS/TAR copre 2024-2025 (in espansione); la Cassazione è consultata live su SentenzeWeb pubblico (finestra ~5 anni + storico parziale).*

Se una norma/sentenza non risulta nei DB o nel lookup live: dillo, non inventare. Cause possibili: (a) non esiste, (b) abrogata, (c) non scaricata/sessione assente, (d) fonte non ancora coperta.
<!-- /LEGAL-EVIDENCE-BLOCK-V7 -->


# Logica Formale (MIT 24.241 — McGee)

## La domanda fondamentale

**Quando un argomento è valido?** La logica formale risponde a questa domanda in
modo rigoroso e preciso: un argomento è **valido** se e solo se è impossibile che
le premesse siano tutte vere e la conclusione falsa. Niente di più, niente di meno.

Distinzione cruciale:
- **Validità** = struttura logica corretta (indipendente dalla verità delle premesse)
- **Solidità** (soundness) = valido + premesse vere
- **Correttezza** = in logica formale, sinonimo di solidità

## Logica Proposizionale (Sentential Logic)

### Connettivi logici fondamentali

| Simbolo | Nome | Lettura italiana | Condizione di verità |
|---------|------|-----------------|---------------------|
| ¬P | Negazione | "non P" | Vera se P è falsa |
| P ∧ Q | Congiunzione | "P e Q" | Vera solo se entrambe vere |
| P ∨ Q | Disgiunzione | "P o Q" | Vera se almeno una è vera |
| P → Q | Condizionale | "se P allora Q" | Falsa solo se P vera e Q falsa |
| P ↔ Q | Bicondizionale | "P se e solo se Q" | Vera se hanno stesso valore |

### Forme di inferenza valide fondamentali

| Nome | Schema | Esempio |
|------|--------|---------|
| Modus Ponens | P → Q, P ⊢ Q | "Se piove, è nuvoloso. Piove. Dunque è nuvoloso." |
| Modus Tollens | P → Q, ¬Q ⊢ ¬P | "Se è colpevole, mente. Non mente. Dunque non è colpevole." |
| Sillogismo ipotetico | P → Q, Q → R ⊢ P → R | Transitività del condizionale |
| Dilemma costruttivo | P → Q, R → S, P ∨ R ⊢ Q ∨ S | |
| Reductio ad absurdum | Assumere ¬C; derivare contraddizione ⊢ C | |

### Tavole di verità

Per verificare se una formula è **tautologia** (sempre vera), **contraddizione** 
(sempre falsa) o **contingente**, si costruisce la tavola di verità con tutte le
combinazioni possibili dei valori di verità delle variabili proposizionali.

Esempio: P → Q è falsa solo quando P=V e Q=F (l'unica combinazione "pericolosa").

## Logica del Predicato (Predicate Logic / FOL)

La logica proposizionale non cattura la struttura interna delle proposizioni.
La logica del predicato (First-Order Logic) lo fa, introducendo:

- **Predicati**: P(x) = "x ha la proprietà P"
- **Quantificatore universale ∀**: "per ogni x, …"
- **Quantificatore esistenziale ∃**: "esiste almeno un x tale che …"
- **Identità**: x = y

### Esempi di formalizzazione

| Italiano | FOL |
|----------|-----|
| "Tutti gli uomini sono mortali" | ∀x (Uomo(x) → Mortale(x)) |
| "Socrate è un uomo" | Uomo(Socrate) |
| "Qualcuno è felice" | ∃x Felice(x) |
| "Nessun filosofo è ricco" | ¬∃x (Filosofo(x) ∧ Ricco(x)) |
| "Solo i virtuosi sono felici" | ∀x (Felice(x) → Virtuoso(x)) |

### Attenzione alle ambiguità del linguaggio naturale

"Un professore ha insegnato a tutti gli studenti" può significare:
- (a) ∃y (Prof(y) ∧ ∀x (Studente(x) → Insegnato(y,x))) — un solo prof per tutti
- (b) ∀x (Studente(x) → ∃y (Prof(y) ∧ Insegnato(y,x))) — per ogni studente c'è un prof

L'ordine dei quantificatori cambia radicalmente il significato.

## Metateoria

| Proprietà | Definizione | Significato |
|-----------|-------------|-------------|
| Completezza (Gödel) | Ogni tautologia è dimostrabile | Il sistema cattura tutta la verità logica |
| Correttezza (Soundness) | Ogni teorema è una tautologia | Il sistema non dimostra falsità |
| Decidibilità | Esiste un algoritmo per stabilire la validità | Sì per proposizionale, No per predicati (Gödel/Turing) |

## Paradossi logici notevoli

| Paradosso | Formulazione | Problema |
|-----------|-------------|---------|
| Mentitore | "Questa frase è falsa" | Auto-referenzialità e bivalenza |
| Russell | L'insieme di tutti gli insiemi che non contengono sé stessi | Autoreferenzialità in set theory |
| Sorite | Un granello non forma un mucchio; + 1 granello → ancora non mucchio → mai mucchio | Vaghe zzza dei predicati |

## Fallacìe logiche comuni

- **Affermazione del conseguente**: P → Q, Q ⊢ P (INVALIDO)
- **Negazione dell'antecedente**: P → Q, ¬P ⊢ ¬Q (INVALIDO)
- **Ad hominem**: attaccare la persona invece dell'argomento
- **Appello all'autorità**: X lo dice, quindi è vero
- **Pendio scivoloso**: A porta a B porta a ... porta a Z (senza giustificazione)
- **Equivocazione**: uso ambiguo dello stesso termine in premesse diverse

## Punto operativo K2-AI

La logica è la struttura portante di ogni analisi rigorosa — in diritto 
(inferenze da norme), in strategia (scenari e condizionali), in etica (deduzione 
da principi), in matematica e programmazione. Usa questa skill ogni volta che 
l'utente presenta un argomento da valutare, formalizzare o smontare.

## Connessioni nell'ecosistema

- `phil-epistemologia` — la logica è lo strumento della giustificazione razionale
- `phil-etica` — gli argomenti etici devono essere formalmente validi
- `phil-metafisica` — argomenti su Dio, identità, libertà richiedono logica rigorosa
- `math-orchestrator` — per logica matematica avanzata (Gödel, teoria degli insiemi)
- `teoria-dei-giochi-decisioni` — ragionamento formale sotto incertezza
