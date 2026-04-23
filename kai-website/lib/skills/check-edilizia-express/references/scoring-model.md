# Modello di Scoring — check-edilizia-express

## Formula di calcolo

Il punteggio globale e una **media ponderata normalizzata a 100**:

```
Score = (somma di (score_fattore_i * peso_i) per i=1..7) / (somma di (10 * peso_i) per i=1..7) * 100
```

Ogni fattore ha un punteggio da 0 a 10 e un peso specifico.
Il denominatore massimo e: (10 * 100) = 1000.

Quindi: **Score = (punti ottenuti / 1000) * 100**

---

## Tabella dei 7 fattori

### 1. Titolo abilitativo corretto
- **Peso**: 20
- **Come si valuta**: in base al tipo di intervento, verificare quale titolo abilitativo e richiesto secondo il DPR 380/2001 (Testo Unico Edilizia) e successive modifiche. CILA per manutenzione straordinaria leggera, SCIA per ristrutturazione edilizia, Permesso di Costruire per nuova costruzione/ampliamento volumetrico. Verificare coerenza tra intervento dichiarato e titolo necessario.
- **Soglie**:
  - Verde (8-10): il titolo abilitativo corretto e chiaramente identificato e coerente con l'intervento
  - Giallo (5-7): il titolo e identificabile ma ci sono dubbi sull'inquadramento (es. confine SCIA/PDC)
  - Rosso (0-4): il titolo non e chiaro, oppure l'intervento sembra richiedere un titolo piu gravoso di quello ipotizzato
- **Spiegazione per il cliente**: "Ogni tipo di lavoro edilizio richiede un 'permesso' diverso. Scegliere quello sbagliato puo bloccare i lavori o portare a sanzioni. E come guidare con la patente sbagliata."

### 2. Conformita urbanistica
- **Peso**: 20
- **Come si valuta**: verificare la coerenza dell'intervento con la zona PRG/PGT dichiarata. Ogni zona ha indici (copertura, altezza, distanze, destinazione d'uso) che l'intervento deve rispettare. Se l'utente indica centro storico o zona agricola, le restrizioni sono maggiori.
- **Soglie**:
  - Verde (8-10): intervento pienamente coerente con la zona urbanistica, nessun conflitto apparente
  - Giallo (5-7): intervento compatibile ma al limite degli indici, oppure informazioni insufficienti per conferma
  - Rosso (0-4): intervento apparentemente in contrasto con la destinazione di zona o con gli indici urbanistici
- **Spiegazione per il cliente**: "Ogni zona del tuo comune ha regole precise su cosa si puo costruire, quanto in alto, quanto grande. Se il tuo progetto non rispetta queste regole, il comune lo boccia."

### 3. Vincoli paesaggistici / monumentali
- **Peso**: 15
- **Come si valuta**: verificare se l'area e soggetta a vincoli ai sensi del D.Lgs. 42/2004 (Codice dei Beni Culturali). Vincoli paesaggistici (art. 136, 142), vincoli monumentali (art. 10-12), vincoli idrogeologici. La presenza di vincoli non impedisce l'intervento ma richiede autorizzazioni aggiuntive (nulla osta Soprintendenza, autorizzazione paesaggistica).
- **Soglie**:
  - Verde (8-10): nessun vincolo presente, oppure vincolo gia verificato con parere favorevole
  - Giallo (5-7): vincoli presenti ma gestibili (es. vincolo paesaggistico generico con procedura semplificata)
  - Rosso (0-4): vincoli monumentali diretti o vincoli multipli sovrapposti, o vincoli non ancora verificati in area sensibile
- **Spiegazione per il cliente**: "Se il tuo immobile o la zona sono 'vincolati', servono permessi aggiuntivi dalla Soprintendenza o da altri enti. Non vuol dire che non puoi fare i lavori, ma che ci vuole piu tempo e attenzione nel progetto."

### 4. Requisiti igienico-sanitari
- **Peso**: 10
- **Come si valuta**: verificare la coerenza dell'intervento con i requisiti minimi di igiene edilizia (DM 5/7/1975 e regolamenti locali di igiene): altezze interne minime (2,70 m abitabili, 2,40 m servizi), rapporti aeroilluminanti (1/8), superfici minime dei locali. Per cambi d'uso, verificare compatibilita della destinazione con i requisiti igienici.
- **Soglie**:
  - Verde (8-10): intervento coerente con requisiti igienico-sanitari standard, nessuna criticita
  - Giallo (5-7): possibili criticita su altezze o rapporti aeroilluminanti, da verificare in dettaglio
  - Rosso (0-4): altezze insufficienti, locali ciechi per destinazione abitativa, carenze evidenti
- **Spiegazione per il cliente**: "Ci sono regole precise su quanto devono essere alti i soffitti, quanta luce deve entrare dalle finestre e quanto grandi devono essere le stanze. Se il tuo intervento non le rispetta, l'ASL puo bloccare l'agibilita."

### 5. Barriere architettoniche
- **Peso**: 10
- **Come si valuta**: verificare gli obblighi di accessibilita ai sensi della L. 13/1989 e DM 236/1989. Per nuove costruzioni e ristrutturazioni importanti: obbligo di accessibilita. Per edifici residenziali: obbligo di adattabilita. Verificare coerenza con il tipo di intervento e la destinazione d'uso.
- **Soglie**:
  - Verde (8-10): intervento conforme ai requisiti di accessibilita/adattabilita previsti
  - Giallo (5-7): requisiti applicabili ma non ancora verificati nel dettaglio
  - Rosso (0-4): evidente non conformita ai requisiti di accessibilita per il tipo di intervento
- **Spiegazione per il cliente**: "La legge richiede che gli edifici siano accessibili (o almeno adattabili) alle persone con disabilita. Se il tuo progetto non prevede questi accorgimenti, la pratica puo essere respinta."

### 6. Documentazione
- **Peso**: 15
- **Come si valuta**: verificare la disponibilita dei documenti necessari per la pratica edilizia: titoli edilizi precedenti, planimetrie catastali aggiornate, visure catastali, certificato di agibilita, eventuali condoni, attestazioni di conformita impiantistica. La completezza della documentazione accelera enormemente l'iter.
- **Soglie**:
  - Verde (8-10): documentazione completa e aggiornata disponibile (titoli, catasto, agibilita)
  - Giallo (5-7): documentazione parziale, alcuni documenti da reperire o aggiornare
  - Rosso (0-4): documentazione assente o gravemente incompleta, possibili abusi non sanati
- **Spiegazione per il cliente**: "La documentazione del tuo immobile e come i documenti di un'auto: senza libretto, assicurazione e revisione non puoi circolare. Allo stesso modo, senza i documenti giusti non puoi presentare la pratica edilizia."

### 7. Conformita catastale
- **Peso**: 10
- **Come si valuta**: verificare la coerenza tra stato di fatto dell'immobile e planimetria catastale. Dal 2010 (DL 78/2010) la conformita catastale e obbligatoria per compravendite. Verificare se ci sono difformita note tra catasto e stato di fatto, e se la destinazione catastale e coerente con l'uso previsto.
- **Soglie**:
  - Verde (8-10): immobile conforme alla planimetria catastale, categoria coerente con l'uso
  - Giallo (5-7): piccole difformita catastali sanabili con variazione catastale
  - Rosso (0-4): difformita catastali rilevanti, oppure catasto non aggiornato da decenni
- **Spiegazione per il cliente**: "Il catasto deve riflettere esattamente come e fatto il tuo immobile. Se ci sono differenze (una parete spostata, una stanza in piu), vanno sistemate prima di fare qualsiasi pratica edilizia."

---

## Fasce di giudizio

| Fascia | Punteggio | Messaggio per il cliente | CTA |
|--------|-----------|--------------------------|-----|
| Critico | 0-30 | "La pratica edilizia presenta criticita importanti che rischiano di bloccare l'intervento. Serve un professionista per impostare correttamente l'iter." | "Ti consigliamo un Progetto Architettonico Completo per risolvere le criticita e impostare correttamente la pratica edilizia. Contattaci per un preventivo." |
| Insufficiente | 31-50 | "Ci sono diversi aspetti da sistemare prima di poter presentare la pratica. Con la giusta consulenza si risolvono." | "Con un Progetto Architettonico Completo possiamo mappare tutte le criticita e guidarti passo dopo passo fino all'ottenimento del titolo abilitativo." |
| Sufficiente | 51-70 | "La pratica e impostabile ma richiede attenzione su alcuni aspetti. Meglio farsi seguire da un professionista esperto." | "Un Progetto Architettonico Completo ti garantisce che ogni aspetto sia curato e che la pratica vada a buon fine al primo tentativo." |
| Buono | 71-85 | "Buona base! La pratica e ben impostata, ci sono pochi aspetti da perfezionare prima della presentazione." | "Con un Progetto Architettonico possiamo curare gli ultimi dettagli e garantirti un iter rapido e senza intoppi." |
| Eccellente | 86-100 | "Ottimo! La situazione appare favorevole per presentare la pratica. Solo verifiche finali di dettaglio." | "Un Progetto Architettonico professionale ti assicura la conformita totale e un iter senza sorprese." |
