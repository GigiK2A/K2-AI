# Modello di Scoring — check-sicurezza-express

## Formula di calcolo

Il punteggio globale e una **media ponderata normalizzata a 100**:

```
Score = (somma di (score_fattore_i * peso_i) per i=1..6) / (somma di (10 * peso_i) per i=1..6) * 100
```

Ogni fattore ha un punteggio da 0 a 10 e un peso specifico.
Il denominatore massimo e: (10 * 100) = 1000.

Quindi: **Score = (punti ottenuti / 1000) * 100**

---

## Tabella dei 6 fattori

### 1. Obbligo PSC
- **Peso**: 20
- **Come si valuta**: verificare se sussiste l'obbligo di redazione del Piano di Sicurezza e Coordinamento ai sensi dell'art. 100 D.Lgs. 81/2008. L'obbligo scatta quando nel cantiere operano piu imprese esecutrici, anche non contemporaneamente. Valutare anche se l'entita del cantiere rientra nei casi di cui all'Allegato XI. Se una sola impresa ma con subappalti previsti, il PSC potrebbe comunque essere necessario.
- **Soglie**:
  - Verde (8-10): obbligo PSC chiaramente non sussistente (1 sola impresa senza subappalti) oppure PSC gia redatto e aggiornato
  - Giallo (5-7): obbligo PSC probabile ma non ancora confermato; oppure PSC da redigere/aggiornare
  - Rosso (0-4): obbligo PSC evidente e non ancora adempiuto; piu imprese senza coordinamento
- **Spiegazione per il cliente**: "Il Piano di Sicurezza e Coordinamento e un documento obbligatorio quando in cantiere lavorano piu ditte. Serve a evitare che il lavoro di una ditta metta in pericolo i lavoratori di un'altra. Senza, il cantiere puo essere fermato."

### 2. Nomina CSP/CSE
- **Peso**: 15
- **Come si valuta**: verificare se il committente ha nominato il Coordinatore per la Sicurezza in fase di Progettazione (CSP) e il Coordinatore per la Sicurezza in fase di Esecuzione (CSE) ai sensi degli artt. 90-92 D.Lgs. 81/2008. L'obbligo sussiste negli stessi casi in cui e obbligatorio il PSC. Il committente e il responsabile della nomina e rischia sanzioni penali in caso di omissione.
- **Soglie**:
  - Verde (8-10): CSP e CSE nominati e con requisiti professionali verificati (art. 98 D.Lgs. 81/2008)
  - Giallo (5-7): nomina necessaria, incarico in corso di conferimento; oppure solo CSE nominato senza CSP
  - Rosso (0-4): nomina obbligatoria ma non effettuata; committente esposto a responsabilita penale
- **Spiegazione per il cliente**: "Il coordinatore della sicurezza e il 'direttore d'orchestra' della sicurezza in cantiere. Se servono piu ditte, e obbligatorio nominarne uno. Se non lo fai, rischi sanzioni penali come committente."

### 3. Notifica preliminare
- **Peso**: 10
- **Come si valuta**: verificare se sussiste l'obbligo di invio della notifica preliminare all'ASL e alla Direzione Territoriale del Lavoro ai sensi dell'art. 99 D.Lgs. 81/2008. L'obbligo scatta quando: (a) il cantiere occupa piu di 200 uomini/giorno, oppure (b) i lavori comportano rischi particolari (Allegato XI), oppure (c) nel cantiere operano piu imprese anche non contemporaneamente.
- **Soglie**:
  - Verde (8-10): notifica non obbligatoria, oppure gia inviata correttamente
  - Giallo (5-7): obbligo notifica presente, da inviare prima dell'inizio lavori
  - Rosso (0-4): obbligo notifica presente e cantiere gia avviato senza invio
- **Spiegazione per il cliente**: "Per cantieri di una certa dimensione, bisogna avvisare l'ASL prima di iniziare i lavori. E come una comunicazione ufficiale: 'Stiamo per iniziare un cantiere qui'. Se non la mandi, rischi una multa."

### 4. POS imprese
- **Peso**: 15
- **Come si valuta**: verificare se ogni impresa esecutrice ha redatto il proprio Piano Operativo di Sicurezza (POS) ai sensi dell'art. 96 D.Lgs. 81/2008. Il POS e obbligatorio per tutte le imprese che operano in cantiere, anche quelle in subappalto. Deve essere coerente con il PSC (se presente) e specifico per le lavorazioni svolte.
- **Soglie**:
  - Verde (8-10): tutte le imprese hanno POS redatto, coerente con PSC, verificato dal CSE
  - Giallo (5-7): POS presenti ma non ancora verificati, oppure alcune imprese devono ancora redigerlo
  - Rosso (0-4): POS assenti o gravemente carenti; imprese operanti senza POS
- **Spiegazione per il cliente**: "Ogni ditta che lavora nel tuo cantiere deve avere il suo 'piano di sicurezza operativo'. E il documento che dice come quella specifica ditta gestisce i rischi del suo lavoro. Senza, la ditta non puo entrare in cantiere."

### 5. Formazione lavoratori
- **Peso**: 20
- **Come si valuta**: verificare che tutti i lavoratori presenti in cantiere abbiano ricevuto la formazione obbligatoria ai sensi dell'art. 37 D.Lgs. 81/2008 e Accordo Stato-Regioni 21/12/2011. Verificare: formazione generale (4 ore), formazione specifica rischio alto per cantieri (12 ore), aggiornamento quinquennale, formazione per attrezzature specifiche (ponteggi, gru, PLE, ecc.), formazione preposti e dirigenti.
- **Soglie**:
  - Verde (8-10): tutti i lavoratori formati e con attestati validi e aggiornati
  - Giallo (5-7): formazione presente ma alcuni attestati in scadenza o da aggiornare
  - Rosso (0-4): formazione assente o gravemente carente; lavoratori senza attestati
- **Spiegazione per il cliente**: "Ogni lavoratore in cantiere deve avere una formazione specifica sulla sicurezza, con un attestato valido. Se i lavoratori non sono formati, l'ispettore del lavoro puo fermare il cantiere e multare sia te che le imprese."

### 6. DPI e attrezzature
- **Peso**: 20
- **Come si valuta**: verificare la disponibilita e l'adeguatezza dei Dispositivi di Protezione Individuale e delle attrezzature di lavoro. DPI obbligatori in cantiere: casco, scarpe antinfortunistiche, guanti, imbracature per lavori in quota. Attrezzature: verifiche periodiche (art. 71 D.Lgs. 81/2008), conformita CE, manutenzione documentata. Per lavori in quota: parapetti, ponteggi a norma, sistemi anticaduta.
- **Soglie**:
  - Verde (8-10): DPI adeguati disponibili per tutti, attrezzature conformi e verificate periodicamente
  - Giallo (5-7): DPI presenti ma da integrare per alcune lavorazioni; verifiche attrezzature da aggiornare
  - Rosso (0-4): DPI assenti o inadeguati; attrezzature senza verifiche periodiche o non conformi
- **Spiegazione per il cliente**: "Caschi, scarpe, imbracature e attrezzature sicure non sono optional: sono obbligatori per legge. Se mancano o non sono a norma, il cantiere puo essere fermato e il committente e corresponsabile."

---

## Fasce di giudizio

| Fascia | Punteggio | Messaggio per il cliente | CTA |
|--------|-----------|--------------------------|-----|
| Critico | 0-30 | "Il cantiere presenta gravi carenze in materia di sicurezza. Rischi concreti di sospensione lavori e sanzioni penali. Serve un intervento immediato." | "Ti consigliamo la Redazione PSC Completa e/o DVR per mettere in regola il cantiere prima di procedere. Contattaci per un intervento urgente." |
| Insufficiente | 31-50 | "Ci sono diverse criticita da risolvere per garantire la conformita del cantiere. Alcune sono urgenti." | "Con la Redazione del PSC e la verifica della documentazione di sicurezza possiamo portare il cantiere in piena conformita." |
| Sufficiente | 51-70 | "Il cantiere ha una base accettabile ma servono integrazioni importanti per la piena conformita." | "Un PSC Completo o un aggiornamento del DVR ti mette al riparo da rischi e ti garantisce la tranquillita durante i lavori." |
| Buono | 71-85 | "Buona conformita! Il cantiere e ben organizzato, ci sono pochi aspetti da perfezionare." | "Con un check-up documentale completo possiamo verificare gli ultimi dettagli e garantirti la piena conformita." |
| Eccellente | 86-100 | "Ottimo! Il cantiere risulta ben organizzato e conforme. Solo verifiche periodiche di routine." | "Un aggiornamento periodico del PSC/DVR ti garantisce il mantenimento della conformita per tutta la durata dei lavori." |
