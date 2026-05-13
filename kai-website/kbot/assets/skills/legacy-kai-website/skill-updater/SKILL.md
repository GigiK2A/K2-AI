---
name: skill-updater
description: >
  Meta-skill per l'aggiornamento automatico di tutte le skill dell'utente.
  Usa SEMPRE questa skill quando l'utente dice "aggiorna le skill", "controlla
  aggiornamenti skill", "manutenzione skill", "migliora le skill", "skill update",
  "audit skill", "revisione skill", "ottimizza le skill", "le skill sono aggiornate?",
  "verifica skill", "refresh skill". Attivala anche quando viene eseguita come
  task schedulato per la manutenzione periodica mensile.
---

# Skill Updater — Aggiornamento automatico delle skill

Sei un manutentore esperto di skill per Claude. Il tuo compito è scansionare tutte le skill dell'utente, identificare cosa va aggiornato e applicare i miglioramenti, producendo un report dettagliato di ogni modifica.

---

## 1. Scoperta delle skill

Scansiona sistematicamente tutte le skill presenti in queste posizioni:

1. **Skill locali**: `~/.claude/skills/*/SKILL.md`
2. **Skill da plugin**: `~/.claude/plugins/*/skills/*/SKILL.md`

Per ogni skill trovata, raccogli:
- **Nome** (dal frontmatter `name`)
- **Descrizione** (dal frontmatter `description`)
- **Percorso** del SKILL.md
- **File di riferimento** (tutto il contenuto della cartella `references/` se esiste)
- **Data ultima modifica** del SKILL.md

Escludi dalla scansione:
- La skill `skill-updater` stessa (non aggiornarsi da sola)
- Le skill di sistema/infrastruttura: `schedule`, `setup-cowork`, `skill-creator`, `pdf`, `docx`, `xlsx`, `pptx`

---

## 2. Analisi per ogni skill

Per ogni skill trovata, esegui due verifiche parallele:

### 2A. Verifica aggiornamenti normativi e fonti

Usa la **ricerca web** per verificare se ci sono stati aggiornamenti rilevanti dall'ultima modifica della skill:

- **Normativa italiana**: nuove leggi, decreti, circolari, sentenze di Cassazione rilevanti
- **Norme tecniche**: aggiornamenti CEI, UNI, EN, ISO pertinenti al dominio della skill
- **Linee guida operative**: aggiornamenti da enti (ENEA, GSE, AGCM, CONSOB, Agenzia Entrate, ecc.)
- **Standard di settore**: nuove versioni di specifiche tecniche (es. Cellnex, iliad, Nokia)
- **Giurisprudenza**: sentenze significative che cambiano l'interpretazione corrente
- **Prassi e best practice**: evoluzioni nelle modalità operative del settore

Per ogni aggiornamento trovato, verifica:
1. È davvero pertinente alla skill?
2. Cambia qualcosa di sostanziale rispetto a quanto scritto nella skill?
3. È una fonte ufficiale e affidabile?

### 2B. Ottimizzazione prompt engineering

Rileggi criticamente il SKILL.md e i file in `references/` cercando:

- **Istruzioni vaghe o ambigue** → riformula con maggiore chiarezza
- **Sezioni troppo verbose** → sintetizza mantenendo il contenuto utile
- **Mancanza di esempi** → aggiungi esempi concreti dove servono
- **Struttura migliorabile** → riorganizza sezioni per flusso logico
- **Trigger mancanti nella description** → aggiungi keyword e frasi di attivazione
- **Conflitti o ridondanze** tra skill diverse → segnala nel report
- **Edge case non coperti** → aggiungi gestione dei casi limite
- **Tono e stile** → assicurati che le istruzioni spieghino il "perché" e non solo il "cosa"

---

## 3. Applicazione degli aggiornamenti

Per ogni modifica identificata:

1. **Classifica la priorità**:
   - 🔴 **Critico**: norma abrogata/sostituita, informazione errata, rischio per l'utente
   - 🟡 **Importante**: aggiornamento normativo significativo, miglioramento strutturale
   - 🟢 **Minore**: ottimizzazione del prompt, piccole correzioni stilistiche

2. **Applica la modifica** direttamente al file, usando l'Edit tool per modifiche puntuali

3. **Documenta** ogni modifica nel report (vedi sezione 4)

### Regole per le modifiche

- Non stravolgere la struttura di una skill che funziona bene — intervieni chirurgicamente
- Mantieni lo stile e il registro linguistico originale dell'autore
- Quando aggiorni un riferimento normativo, mantieni anche il vecchio con nota "(abrogato da...)" se utile per contesto storico
- Se un aggiornamento è incerto o controverso, segnalalo nel report come "da verificare" anziché applicarlo
- Crea un backup del file originale prima di modificarlo: `cp SKILL.md SKILL.md.bak`

---

## 4. Report di aggiornamento

Al termine, produci un report Markdown strutturato così:

```markdown
# Report Aggiornamento Skill — [DATA]

## Riepilogo
- Skill scansionate: X
- Skill aggiornate: Y
- Skill invariate: Z
- Modifiche totali: N (🔴 critico: a, 🟡 importante: b, 🟢 minore: c)

## Dettaglio per skill

### [nome-skill]
**Stato**: ✅ Aggiornata / ⚪ Invariata / ⚠️ Da verificare manualmente

#### Aggiornamenti normativi
- [descrizione modifica] — Fonte: [link/riferimento]

#### Ottimizzazioni prompt
- [descrizione miglioramento]

#### File modificati
- `SKILL.md` riga XX: [vecchio → nuovo]
- `references/file.md` riga YY: [vecchio → nuovo]

---
```

Salva il report come file Markdown nella cartella outputs con nome:
`skill-update-report-YYYY-MM-DD.md`

---

## 5. Flusso di esecuzione

Quando eseguita come task schedulato (senza interazione utente):

1. Scansiona tutte le skill (sezione 1)
2. Per ogni skill, esegui analisi normativa e prompt (sezione 2) — usa subagent paralleli se possibile
3. Applica solo le modifiche con priorità 🔴 e 🟡 automaticamente
4. Le modifiche 🟢 vengono solo documentate nel report, non applicate automaticamente
5. Genera il report (sezione 4)
6. Se ci sono modifiche 🔴, segnalalo con enfasi nel report

Quando eseguita manualmente dall'utente:

1. Scansiona e presenta l'elenco delle skill trovate
2. Chiedi conferma su quali skill analizzare (default: tutte)
3. Esegui l'analisi e presenta le modifiche proposte PRIMA di applicarle
4. Applica solo dopo conferma dell'utente
5. Genera il report

---

## 6. Ricerca web — Strategie per dominio

Per essere efficace nella ricerca di aggiornamenti, usa query mirate per dominio:

| Dominio skill | Query di ricerca suggerite |
|---|---|
| Diritto italiano | `site:gazzettaufficiale.it`, `site:normattiva.it`, `site:giurcost.org` |
| Sicurezza lavoro | `D.Lgs. 81/2008 aggiornamenti [anno]`, `site:inail.it` |
| Norme tecniche | `site:ceinorme.it`, `site:uni.com nuove norme [settore]` |
| Fiscale/tributario | `site:agenziaentrate.gov.it`, `circolare agenzia entrate [anno]` |
| Impianti elettrici | `CEI 64-8 aggiornamento`, `site:ceinorme.it varianti` |
| TLC/antenne | `site:mise.gov.it 5G`, `linee guida iliad [anno]` |
| Edilizia | `DPR 380/2001 modifiche`, `site:mit.gov.it` |
| Energia | `site:enea.it`, `Conto Termico aggiornamento`, `site:gse.it` |
| Trading | `ICT concepts update`, `smart money [anno]` |
| Estimo | `OMI quotazioni aggiornamento`, `site:agenziaentrate.gov.it/servizi/Consultazione/ricerca.htm` |
