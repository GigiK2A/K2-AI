---
name: verifica-pe-terzi
description: >
  Skill per la verifica e il controllo di qualità dei Progetti Esecutivi (PE) iliad Italia S.p.A.
  redatti da fornitori o appaltatori terzi. Usa SEMPRE questa skill quando l'utente dice
  "verificare il PE", "controllare il progetto", "revisionare gli elaborati", "check PE terzi",
  "verifica conformità PE iliad", "controllare se il progetto è completo", "trovare le
  non conformità nel PE", "revisione PE fornitore", "approvare il PE", "audit PE iliad",
  "checklist verifica progetto esecutivo", "il PE è corretto?", "mancano documenti?".
metadata:
  version: "0.2.1"
  author: "Luca Rossi"
  riferimento: "Linea Guida Progetti Esecutivi iliad v.1.1"
  changelog: "0.2.1 — Aggiunta verifica dettagliata impianti per tavola (IMP-01÷09.1), controllo coerenza quantità cavi coassiali per settore, NC tipiche impianti aggiornate da case study FI50137_802"
---

# Verifica PE Terzi — Controllo Qualità Progetto Esecutivo iliad

Questa skill esegue la verifica sistematica di un Progetto Esecutivo iliad redatto da un fornitore terzo, producendo un report di conformità con le non conformità rilevate.

La checklist completa con tutti i criteri di dettaglio è in `references/checklist-verifica.md`.

## Procedura di Verifica

### Fase 1 — Identificazione e raccolta dati

Richiedere all'utente (o leggere dagli elaborati):
- Codice sito e nome sito
- Tipologia sito (NS-RL / NS-RT / TC-RL / TC-RT)
- Elenco degli elaborati consegnati dal fornitore (lista file o cartella)
- Versione PE e data

### Fase 2 — Verifica completezza elaborati

Confrontare gli elaborati consegnati con la matrice obbligatoria per la tipologia del sito (Sezione A di `references/checklist-verifica.md`).

Classificare ogni elaborato come:
- ✅ **PRESENTE** — elaborato consegnato e identificabile
- ⚠️ **INCOMPLETO** — presente ma mancano sottoelementi richiesti
- ❌ **MANCANTE** — elaborato non consegnato

### Fase 3 — Verifica contenuto elaborati

Per ogni elaborato presente, verificare la conformità dei contenuti secondo i criteri in `references/checklist-verifica.md`.

**Criteri generali per tutti gli elaborati:**
- Cartiglio completo (Codice Sito, Nome, Fornitore, Progettista, Data, Rev.)
- Dati identificativi sito coerenti con la Scheda Radio
- Scala indicata e coerente con il contenuto
- Firma/timbro del professionista (dove richiesto)
- Versione interna coerente con versione frontespizio PE (NC MA se mismatch)

### Fase 4 — Verifica strutturale (se applicabile)

Per le relazioni di calcolo strutturale verificare (Sezione E di `references/checklist-verifica.md`):
- Struttura 16 capitoli LG VS v1.4
- Marginalità degli sfruttamenti ≥ 15-20% (limite massimo 80-85%)
- Normativa di riferimento citata (NTC 2018, Eurocodici incluso EC8)
- Carichi di vento coerenti con la zona sismica e climatica del sito
- **Assenza di errori numerici (#VALORE!, #RIF!, #DIV/0!) nel foglio di calcolo** — NC BL se presenti
- **Tutti gli elementi strutturali verificati** (inclusi pennoni, sbracci, fari) — NC BL se esclusi senza dati
- Per pali nuovi: relazione di calcolo + tabella sfruttamenti + piano manutenzione + unifilare
- Per fondazioni NS-RL: relazione di calcolo + tabella sfruttamenti (marginalità 15-20%)

### Fase 5 — Verifica impianti elettrici (Sezione D + F_BIS di `references/checklist-verifica.md`)

#### 5.1 Verifica presenza tavole (IMP-01 ÷ IMP-09.1)

Verificare la presenza di tutti gli elaborati grafici impianti:
- **IMP-01**: Schema allacci fibra ottica — percorsi FO, legenda cavi, lunghezze
- **IMP-02**: Pianta impianto elettrico — posizione quadri, percorso cavi, tabella componenti
- **IMP-03**: Dettaglio armadio stradale — tipologia, dimensioni, specifiche tecniche
- **IMP-04**: Schema unifilare ICA — arrivo rete, protezioni, tipo differenziale (AC/A/B/F)
- **IMP-05**: Schema unifilare MiniTD / DC Panel — distribuzione DC -48V, separazione da AC
- **IMP-05.1**: Schema unifilare QPL / QIA Small (se previsto)
- **IMP-06**: Schema a blocchi impianto iliad — tutti i settori, apparati, legenda cavi con sezioni e lunghezze
- **IMP-06.1**: Schema a blocchi operatore ospitato (se TC/colocation)
- **IMP-07**: Schema impianto MAT — piastre equipotenziali, piastra antenne subito sotto le antenne, calata verticale
- **IMP-08**: Dettaglio pozzetto / dispersore verticale — DN ≥ 18 mm, L ≥ 1,5 m, pozzetto prefabbricato
- **IMP-09**: Riepilogo cavi iliad (FO, MAT, alimentazione, coassiali, segnale)
- **IMP-09.1**: Riepilogo cavi operatore ospitato (se TC/colocation)

#### 5.2 Controllo quantità cavi coassiali (⚠ obbligatorio)

Leggere il riepilogo cavi (IMP-09) ed eseguire il controllo di coerenza tra settori (Sezione D2 di `references/checklist-verifica.md`):

1. Estrarre il numero di cavi coassiali per ogni settore
2. Calcolare il rapporto max/min tra settori
3. **Se rapporto > 2:1 senza giustificazione → NC MA** (fornitore deve documentare configurazione RRH/porte per settore)

Valori di riferimento:
- Nokia AirScale T3 feederless: cavo 1/2", L ≤ 10 m, ~4÷12 pz per settore standard
- RRU on-pole feeder: cavo 7/8", L 8÷12 m, simmetria tra settori attesa
- Settore Multibeam/MIMO con molti RRH: quantità più alta accettabile se documentata

#### 5.3 Verifiche normative impianti

- Tecnico abilitato D.M. 37/08 indicato
- Cavi con marcatura CPR EU 305/2011 indicata → NC MA se assente
- Tipo differenziale (AC/A/B/F) indicato per ogni circuito in IMP-04 → NC MA se assente
- Separazione circuiti DC -48V da circuiti AC

### Fase 6 — Verifica elaborati grafici costruttivi (Sezione C di `references/checklist-verifica.md`)

Per NS-RL verificare:
- Presenza tracciamento con coordinate
- Sezioni di sito con indicazione plinto/platea e tabella mc di scavo
- Sviluppo fondazione con volumi cls e peso ferri
- Sviluppo platea con pozzetti e tubazioni
- Cancello di ingresso e recinzione
- Carpenteria: incidenza bulloni e zincatura ≤ 10%

Per NS-RT verificare:
- Tracciamento baggioli
- Sviluppo baggioli con demolizioni/ripristini e tipologia resine
- Tavole di assieme carpenteria
- Distinta carpenteria con incidenza bulloni e zincatura ≤ 10%

Per TC-RL verificare:
- Tavola di tracciamento per individuazione univoca carpenterie a terra
- Carpenteria in quota con distinta peso (bulloni+zincatura ≤ 10%)

### Fase 7 — Generazione report NC

Produrre un report strutturato in formato .docx (attivare la skill **docx**) con:

```
REPORT VERIFICA PE
==================
Codice Sito: [XX00000_000]
Nome Sito: [Nome]
Tipologia: [NS-RL / NS-RT / TC-RL / TC-RT]
Data verifica: [gg/mm/aaaa]

COMPLETEZZA ELABORATI
---------------------
[Tabella con stato di ogni elaborato]

NON CONFORMITÀ RILEVATE
-----------------------
NC-001: [Descrizione NC — elaborato — gravità]
NC-002: ...

GIUDIZIO
--------
[ ] CONFORME — PE approvabile
[ ] NON CONFORME — PE da integrare/correggere
[ ] NON VALUTABILE — mancano troppi elaborati
```

### Classificazione Gravità Non Conformità

| Codice | Gravità | Descrizione | Azione richiesta |
|--------|---------|-------------|------------------|
| **BL** | Bloccante | Elaborato mancante o errore tecnico grave (es. #VALORE! in foglio calcolo, elemento strutturale non verificato) | Integrazione obbligatoria prima dell'approvazione |
| **MA** | Maggiore | Contenuto incompleto o non conforme a linea guida | Correzione richiesta |
| **MI** | Minore | Formale/cartiglio/scala | Correggibile in revisione successiva |
| **OS** | Osservazione | Suggerimento migliorativo | A discrezione del fornitore |

## Output Atteso

Produrre:
1. **Report .docx** di verifica con sezioni: completezza elaborati, verifica cartiglio, elaborati costruttivi, relazione strutturale, impianti elettrici, tabella riepilogativa NC, legenda
2. **Giudizio complessivo**: CONFORME / NON CONFORME / NON VALUTABILE
3. **Lettera di trasmissione** (opzionale) per comunicazione formale al fornitore
