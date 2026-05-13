# Modello di Scoring — check-tlc-express

## Formula di calcolo

Il punteggio globale e una **media ponderata normalizzata a 100**:

```
Score = (somma di (score_fattore_i * peso_i) per i=1..6) / (somma di (10 * peso_i) per i=1..6) * 100
```

Ogni fattore ha un punteggio da 0 a 10 e un peso specifico.
Il denominatore massimo e: (10 * 100) = 1000.

Quindi: **Score = (punti ottenuti / 1000) * 100**

**Nota**: in questa skill il punteggio alto indica massima prontezza / minima complessita. Un punteggio basso indica sito molto complesso con iter lungo e costoso.

---

## Tabella dei 6 fattori

### 1. Complessita urbanistica
- **Peso**: 15
- **Come si valuta**: valutare la zona urbanistica in cui ricade il sito e il relativo iter autorizzativo. Zone agricole o industriali = iter semplice (SCIA o autorizzazione unica). Centri storici, zone residenziali dense = iter complesso (Permesso di Costruire, conferenza servizi). Verificare se il comune ha un regolamento specifico per antenne/SRB e se esiste un piano antenne comunale.
- **Soglie**:
  - Verde (8-10): zona industriale/agricola/commerciale senza restrizioni specifiche; comune con regolamento SRB favorevole
  - Giallo (5-7): zona residenziale con iter standard; comune senza piano antenne specifico
  - Rosso (0-4): centro storico, zona di pregio, comune con moratoria o regolamento restrittivo per SRB
- **Spiegazione per il cliente**: "La zona urbanistica determina la complessita dell'iter autorizzativo. In centro storico o zone di pregio, ottenere i permessi richiede piu tempo e documentazione rispetto a una zona industriale."

### 2. Vincoli paesaggistici / ENAC
- **Peso**: 20
- **Come si valuta**: verificare la presenza di vincoli ai sensi del D.Lgs. 42/2004 (paesaggistici), vincoli ENAC (prossimita aeroporti, eliporti — necessario nulla osta per strutture che superano i 45 m o ricadono in zone di rispetto), vincoli militari, vincoli ambientali (SIC, ZPS, aree protette). La compresenza di piu vincoli moltiplica la complessita.
- **Soglie**:
  - Verde (8-10): nessun vincolo presente, oppure vincoli gia verificati con esito favorevole
  - Giallo (5-7): vincolo paesaggistico generico (art. 142 D.Lgs. 42/2004) con procedura semplificata; oppure ENAC con nulla osta ottenibile
  - Rosso (0-4): vincolo monumentale diretto; zona di rispetto ENAC critica; vincoli multipli sovrapposti; area SIC/ZPS
- **Spiegazione per il cliente**: "I vincoli paesaggistici e aeronautici sono i principali 'ostacoli' per un sito TLC. Se il sito ricade in zona vincolata, servono autorizzazioni aggiuntive che allungano i tempi anche di 3-6 mesi."

### 3. Accessibilita area
- **Peso**: 10
- **Come si valuta**: valutare la raggiungibilita del sito per mezzi di cantiere (autogrù, camion) e per la manutenzione ordinaria. Per rawland: verificare presenza di strade di accesso carrabile, distanza da viabilita principale, necessita di realizzare pista di accesso. Per rooftop: verificare possibilita di accesso con scale/ascensore per materiali, portata solai.
- **Soglie**:
  - Verde (8-10): accesso carrabile diretto, area di manovra adeguata per autogrù; per rooftop: accesso agevole e portata solaio verificata
  - Giallo (5-7): accesso esistente ma con limitazioni (strada stretta, peso limitato); per rooftop: accesso con difficolta logistiche
  - Rosso (0-4): nessun accesso carrabile, necessita di realizzare pista; per rooftop: accesso impossibile per mezzi pesanti, solaio non verificato
- **Spiegazione per il cliente**: "Se il sito e difficile da raggiungere con i mezzi di cantiere, i costi di installazione aumentano significativamente. Un buon accesso riduce tempi e costi sia per l'installazione che per la manutenzione futura."

### 4. Complessita strutturale
- **Peso**: 20
- **Come si valuta**: valutare la complessita dell'intervento strutturale in base al tipo di sito. Per rawland: tipo di fondazione necessaria (plinto, pali), tipo di struttura porta-antenne (palo, traliccio), altezza. Per rooftop: necessita di rinforzi strutturali al solaio, tipo di supporto (bipiede, tripiede, palo su plinto in copertura), verifica strutturale dell'edificio esistente. Per upgrade: verifica capacita residua della struttura esistente.
- **Soglie**:
  - Verde (8-10): intervento strutturale standard (palo h < 24m su rawland pianeggiante; bipiede leggero su rooftop con solaio verificato)
  - Giallo (5-7): complessita media (palo h > 24m; necessita di rinforzo solaio per rooftop; terreno con problemi geotecnici lievi)
  - Rosso (0-4): complessita elevata (traliccio alto; rinforzo strutturale pesante su edificio vecchio; terreno con problemi geotecnici gravi; struttura esistente al limite di capacita)
- **Spiegazione per il cliente**: "La struttura porta-antenne e il 'cuore' del sito. Se richiede fondazioni speciali, rinforzi al tetto o strutture complesse, i costi e i tempi di progettazione aumentano notevolmente."

### 5. Complessita impiantistica
- **Peso**: 15
- **Come si valuta**: valutare la complessita degli impianti necessari: alimentazione elettrica (distanza dal punto di consegna, necessita di nuovo allaccio ENEL, gruppo elettrogeno), impianto di terra, protezione dalle scariche atmosferiche (LPS), predisposizione per fibra ottica, impianto di condizionamento shelter. Per upgrade: compatibilita con impianti esistenti.
- **Soglie**:
  - Verde (8-10): punto di consegna ENEL esistente e prossimo; predisposizioni impiantistiche presenti; per colocation: impianti condivisi disponibili
  - Giallo (5-7): necessita di nuovo allaccio ENEL ma con cabina prossima; impianti da realizzare ex novo ma standard
  - Rosso (0-4): punto di consegna ENEL distante (> 500m); necessita di cabina MT/BT dedicata; impianti complessi (gruppo elettrogeno obbligatorio, LPS in zona ceraunica elevata)
- **Spiegazione per il cliente**: "Gli impianti elettrici e le predisposizioni tecnologiche sono fondamentali per il funzionamento del sito. Se l'allaccio elettrico e lontano o servono impianti speciali, i costi possono aumentare anche del 30-50%."

### 6. Documentazione necessaria
- **Peso**: 20
- **Come si valuta**: valutare la quantita e complessita della documentazione da produrre per l'iter autorizzativo. Documentazione base: TSSR, progetto architettonico, relazione strutturale, relazione impiantistica, dichiarazione ARPA (limiti di campo elettromagnetico). Documentazione aggiuntiva (se vincoli): relazione paesaggistica, VINCA (Valutazione di Incidenza), nulla osta ENAC, nulla osta militare, parere Soprintendenza.
- **Soglie**:
  - Verde (8-10): documentazione standard sufficiente (TSSR + progetto base); nessun parere aggiuntivo richiesto
  - Giallo (5-7): documentazione standard + 1-2 pareri aggiuntivi (es. autorizzazione paesaggistica semplificata)
  - Rosso (0-4): documentazione complessa con 3+ pareri aggiuntivi; conferenza di servizi obbligatoria; VINCA necessaria
- **Spiegazione per il cliente**: "La quantita di documenti da produrre determina i tempi e i costi della progettazione. Un sito semplice richiede pochi documenti standard; un sito vincolato puo richiedere decine di elaborati e pareri di enti diversi."

---

## Fasce di giudizio

| Fascia | Punteggio | Messaggio per il cliente | CTA |
|--------|-----------|--------------------------|-----|
| Critico | 0-30 | "Il sito presenta una complessita molto elevata con vincoli multipli e iter lungo. Valutare attentamente il rapporto costi-benefici e possibili alternative." | "Ti consigliamo un Progetto Esecutivo PE Completo per gestire tutte le complessita e massimizzare le probabilita di successo dell'iter. Contattaci per un preventivo." |
| Insufficiente | 31-50 | "Il sito ha diverse criticita da gestire. L'iter sara complesso ma fattibile con la giusta progettazione." | "Con un Progetto Esecutivo PE Completo possiamo affrontare ogni criticita e guidarti attraverso l'intero iter autorizzativo." |
| Sufficiente | 51-70 | "Il sito e fattibile ma con complessita da gestire attentamente. Tempi e costi medi." | "Un Progetto Esecutivo PE professionale ti garantisce un iter senza intoppi e tempi ottimizzati." |
| Buono | 71-85 | "Buona fattibilita! Il sito ha poche criticita e un iter ragionevolmente semplice." | "Con un Progetto Esecutivo PE possiamo gestire l'intero iter in tempi rapidi e con costi contenuti." |
| Eccellente | 86-100 | "Ottimo! Il sito presenta complessita minima e un iter autorizzativo snello. Tempi e costi contenuti." | "Un Progetto Esecutivo PE standard ti permette di procedere rapidamente all'installazione." |
