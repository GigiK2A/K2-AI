---
name: psy-personalita
description: >
  Psicologia della personalità (MIT 9.00SC + Yale PSYC 110). Usa SEMPRE per: Big Five
  OCEAN (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism), teoria
  psicoanalitica (Freud — Es/Io/Super-Io, meccanismi di difesa, inconscio), psicologia
  umanistica (Maslow piramide dei bisogni, Rogers autorealizzazione), approccio
  cognitivo-sociale (Bandura self-efficacy, Mischel), disturbi di personalità DSM-5
  (cluster A/B/C), stabilità della personalità nel ciclo di vita. Attiva per: "Big Five",
  "OCEAN personalità", "Freud personalità", "Maslow bisogni", "meccanismi difesa",
  "disturbi personalità", "narcisismo", "estroversione introversione", "coscienziosità",
  "personalità e lavoro", "self-efficacy", "autorealizzazione", "psicoanalisi
  personalità", "carattere e temperamento".
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


# Psicologia della Personalità (MIT 9.00SC + Yale PSYC 110)

## La domanda fondamentale

**Cosa rende una persona *quella persona* — stabile nel tempo e unica rispetto agli
altri?** La personalità è il pattern relativamente stabile di pensieri, emozioni e
comportamenti che caratterizza un individuo. Le teorie divergono su struttura,
origine e misurabilità.

## Il Big Five — OCEAN

Il modello più robusto empiricamente. Cinque fattori ortogonali, stabili tra culture
e metodi di misura, con base genetica moderata (~40-60% ereditabilità):

| Tratto | Polo alto | Polo basso | Predittori |
|--------|-----------|-----------|-----------|
| **Openness** (Apertura) | Curioso, creativo, amante delle idee | Convenzionale, pratico | Creatività, rendimento artistico |
| **Conscientiousness** (Coscienziosità) | Organizzato, disciplinato, affidabile | Impulsivo, disorganizzato | Successo lavorativo, salute, longevità |
| **Extraversion** (Estroversione) | Socievole, energico, assertivo | Riservato, introspettivo | Soddisfazione di vita, leadership |
| **Agreeableness** (Amabilità) | Cooperativo, empatico, fiducioso | Competitivo, scettico | Relazioni, lavoro di team |
| **Neuroticism** (Nevroticismo) | Ansioso, emotivamente instabile | Emotivamente stabile, calmo | Rischio depressione/ansia |

**Il più predittivo per il lavoro**: Conscientiousness — predice performance in
quasi tutti i ruoli. Neuroticism predice negativamente.

**Stabilità nel tempo**: la personalità è sorprendentemente stabile dopo i 30 anni,
ma può cambiare gradualmente (mediamente verso maggiore Agreeableness e
Conscientiousness con l'età — "maturazione della personalità").

## Freud e la psicoanalisi

### Struttura della mente

| Istanza | Principio | Funzione |
|---------|-----------|---------|
| **Es (Id)** | Piacere | Impulsi primitivi, sessualità, aggressività; inconscio |
| **Io (Ego)** | Realtà | Mediazione tra Es e Super-Io; in parte conscio |
| **Super-Io (Super-Ego)** | Moralità | Norme interiorizzate, ideale dell'Io, senso di colpa |

### Meccanismi di difesa (Anna Freud)

| Meccanismo | Descrizione | Esempio |
|-----------|-------------|---------|
| **Rimozione** | Impulso inaccettabile spinto nell'inconscio | Dimenticare un trauma |
| **Proiezione** | Attribuiamo agli altri sentimenti nostri inaccettabili | "È lui che ce l'ha con me" |
| **Razionalizzazione** | Giustificazione logica per azione irrazionale | "L'ho fatto per il suo bene" |
| **Spostamento** | Impulso diretto su obiettivo alternativo | Prendersela col cane dopo lavoro stressante |
| **Sublimazione** | Energia istintuale → attività socialmente accettata | Arte, sport |
| **Regressione** | Tornare a comportamenti di fase precedente sotto stress | Adulto che fa i capricci |
| **Formazione reattiva** | Trasformare impulso nel suo opposto | Ossessivo che nega scrupoli da paura |

*Validità empirica*: I meccanismi di difesa sono descrittivamente utili; la teoria
psicoanalitica complessiva è criticata per non falsificabilità (Popper).

## Psicologia umanistica

### Maslow — Gerarchia dei bisogni

```
5. Autorealizzazione — diventare ciò che si può diventare
4. Stima — autostima, riconoscimento, status
3. Appartenenza — amore, amicizia, intimità
2. Sicurezza — corpo, lavoro, risorse, salute
1. Fisiologici — cibo, acqua, sonno, sesso
```

*Critica*: la gerarchia è rigida e WEIRD-centrica — in molte culture il
collettivo precede il bisogno individuale. Scarso supporto empirico per
l'ordine fisso.

### Rogers — La persona pienamente funzionante

Carl Rogers: gli esseri umani tendono naturalmente all'**autorealizzazione** (actualizing
tendency). Il problema: il bisogno di approvazione condizionata ("ti voglio bene *se*...")
crea un gap tra Sé reale e Sé ideale, producendo incongruenza e nevrosi.

**Terapia centrata sul cliente**: il terapeuta offre *considerazione positiva
incondizionata*, empatia e autenticità — la crescita fa il resto.

## Approccio cognitivo-sociale

**Bandura — Self-efficacy**: la credenza nella propria capacità di eseguire un
comportamento è il predittore più forte di se ci proviamo e persistiamo.
Fonti: esperienze di padronanza, apprendimento vicario, persuasione verbale, stati fisiologici.

**Mischel e la persona-situazione**: il comportamento varia molto tra situazioni (bassa
cross-situational consistency). La "persona" è definita da pattern SE-ALLORA
("*se* in contesto competitivo, *allora* aggressivo").

## Temperamento — origini biologiche della personalità

Il temperamento (reattività, regolazione emotiva, tendenza all'approccio/ritiro)
è visibile già nei neonati e predice tratti di personalità adulta:
- Easy (~40%): adattabile, umore positivo
- Difficult (~10%): irregolare, intenso
- Slow-to-warm-up (~15%): reticente, graduale

**Interazione gene-ambiente**: stessi geni → personalità diversa in ambienti diversi.

## Disturbi di personalità (DSM-5)

Tre cluster — pattern di personalità pervasivi, inflessibili, che causano distress o
disfunzione:

| Cluster | Caratteristica | Esempi |
|---------|--------------|--------|
| **A** (Strano/eccentrico) | Bizzarria, distanza sociale | Paranoide, Schizoide, Schizotipico |
| **B** (Drammatico/emotivo) | Instabilità, drammaticità | Antisociale, Borderline, Istrionico, Narcisistico |
| **C** (Ansioso/timoroso) | Paura, ansia | Evitante, Dipendente, Ossessivo-Compulsivo |

**Disturbo narcisistico**: grandiosità, bisogno di ammirazione, mancanza di empatia.
Distinto dall'autostima sana per fragilità sottostante e incapacità di tollerare
la critica.

## Punto operativo K2-AI

La personalità predice comportamento organizzativo (Conscientiousness → performance),
compatibilità nei team (Agreeableness, Extraversion), rischio di burnout
(Neuroticism), creatività (Openness). Il Big Five è lo strumento più valido per
la selezione e lo sviluppo del personale. I meccanismi di difesa aiutano a
interpretare comportamenti disfunzionali nei contesti professionali.

## Connessioni nell'ecosistema

- `psy-orchestrator` — routing cross-dominio
- `psy-sviluppo` — personalità si forma nel ciclo di vita
- `psy-cliniche-base` — disturbi di personalità nel DSM-5
- `psy-organizzativa` — Big Five e performance lavorativa
- `psy-sociale` — interazione tra personalità e situazione
- `marketing-strategico` — Big Five applicato a segmentazione psicografica
- `phil-metafisica` — identità personale nel tempo
