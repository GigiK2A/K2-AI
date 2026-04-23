# Modello di Scoring — check-strutturale-express

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

### 1. Zona sismica / PGA di riferimento
- **Peso**: 15
- **Come si valuta**: classificare l'edificio in base alla zona sismica (OPCM 3274/2003 e successivi aggiornamenti). Il punteggio e inversamente proporzionale alla pericolosita: zona 4 = rischio basso = punteggio alto; zona 1 = rischio alto = punteggio basso. Se l'edificio e stato progettato ante-classificazione sismica del comune, penalizzare ulteriormente.
- **Soglie**:
  - Verde (8-10): Zona 4 oppure zona 3 con edificio progettato secondo NTC 2008/2018
  - Giallo (5-7): Zona 3 con progetto ante-NTC 2008, oppure zona 2 con progetto post-2008
  - Rosso (0-4): Zona 1 o 2 con edificio progettato prima della classificazione sismica del comune
- **Spiegazione per il cliente**: "La zona sismica indica quanto forte puo essere un terremoto nella tua zona. Se l'edificio e stato costruito prima che la zona fosse classificata come sismica, potrebbe non essere stato progettato per resistere ai terremoti previsti."

### 2. Vetusta della struttura
- **Peso**: 15
- **Come si valuta**: valutare l'eta dell'edificio in relazione alla normativa vigente al momento della costruzione. Edifici ante-1971 (ante legge sismica 64/1974): massima penalizzazione. Edifici 1971-1996: penalizzazione media. Edifici post-1996 (DM 96): penalizzazione lieve. Edifici post-2008 (NTC 2008): punteggio alto.
- **Soglie**:
  - Verde (8-10): costruito dopo il 2008 (NTC 2008) o dopo il 2018 (NTC 2018)
  - Giallo (5-7): costruito tra il 1975 e il 2008
  - Rosso (0-4): costruito prima del 1975, in particolare prima del 1971
- **Spiegazione per il cliente**: "Le regole per costruire edifici sicuri sono cambiate molto nel tempo. Un edificio degli anni '60 e stato costruito con regole molto diverse da quelle di oggi. Non significa che sia pericoloso, ma che potrebbe servire una verifica per assicurarsi che sia ancora adeguato."

### 3. Stato conservativo
- **Peso**: 15
- **Come si valuta**: basarsi sulla descrizione fornita dall'utente riguardo a: fessurazioni visibili, ammaloramento del calcestruzzo (copriferro, carbonatazione), stato delle armature (se visibili), deformazioni permanenti, infiltrazioni d'acqua, degrado dei giunti strutturali. Chiedere all'utente di descrivere eventuali segni visibili di degrado.
- **Soglie**:
  - Verde (8-10): nessun segno visibile di degrado, struttura in buone condizioni apparenti
  - Giallo (5-7): fessurazioni capillari, piccoli segni di umidita, degrado estetico superficiale
  - Rosso (0-4): fessurazioni significative, armature esposte, deformazioni visibili, infiltrazioni importanti
- **Spiegazione per il cliente**: "I segni visibili di degrado (crepe, macchie di ruggine, pezzi di intonaco che cadono dal soffitto) sono come i sintomi di una malattia: non sempre sono gravi, ma vanno sempre controllati da un esperto."

### 4. Conformita NTC 2018 + classe rischio DM 58/2017
- **Peso**: 20
- **Come si valuta**: verificare se l'edificio e stato progettato o verificato secondo le Norme Tecniche per le Costruzioni vigenti (DM 17/01/2018 e Circolare applicativa n.7/2019). Dal 23/03/2025 il DM 09/03/2023 (che sospendeva §11.4.2 e §11.5.2 NTC 2018 per acciai c.a.) e scaduto: le NTC 2018 tornano pienamente vigenti senza deroghe. Se esiste una classificazione rischio sismico DM 58/2017 (classi A+÷G) con eventuale miglioramento documentato, il punteggio migliora. Edifici non verificati rispetto alle NTC vigenti ricevono penalizzazione proporzionale.
- **Soglie**:
  - Verde (8-10): edificio progettato o verificato secondo NTC 2018; relazione di calcolo aggiornata e/o classe rischio sismico A+/A/B DM 58/2017 documentata
  - Giallo (5-7): edificio verificato secondo NTC 2008 o normativa precedente equivalente; oppure classe rischio C/D DM 58/2017 senza verifica NTC 2018 aggiornata
  - Rosso (0-4): nessuna verifica strutturale rispetto a normativa sismica moderna; classe rischio E/F/G DM 58/2017; o progetto originale ante legge 64/1974
- **Spiegazione per il cliente**: "Le norme attuali (NTC 2018) sono il 'metro' con cui si misura la sicurezza di un edificio oggi. In piu, il DM 58/2017 introduce una scala di classi di rischio sismico (dalla A+ alla G, come il frigorifero): sapere in quale classe si trova il tuo edificio e il modo piu diretto per capire il livello di rischio sismico attuale."

### 5. Documentazione disponibile
- **Peso**: 15
- **Come si valuta**: verificare quali documenti sono disponibili tra: progetto strutturale originale, relazione di calcolo, collaudo statico, certificato di agibilita, eventuali perizie successive, prove sui materiali, rilievi strutturali. Piu documentazione c'e, piu il punteggio e alto.
- **Soglie**:
  - Verde (8-10): progetto strutturale completo + collaudo statico + relazione di calcolo disponibili
  - Giallo (5-7): disponibile solo parte della documentazione (es. solo collaudo, o solo progetto senza calcoli)
  - Rosso (0-4): nessuna documentazione strutturale reperibile
- **Spiegazione per il cliente**: "I documenti del progetto strutturale sono come la 'cartella clinica' del tuo edificio. Senza, un ingegnere deve partire da zero per capire come e fatto, il che richiede piu tempo e piu indagini (e quindi piu costi)."

### 6. Interventi pregressi
- **Peso**: 20
- **Come si valuta**: verificare se sono stati eseguiti interventi di adeguamento, miglioramento sismico, rinforzo strutturale o ristrutturazione significativa. Valutare la qualita e l'epoca degli interventi: un miglioramento sismico recente (post-2008) secondo NTC vale molto; interventi di sola manutenzione ordinaria valgono meno.
- **Soglie**:
  - Verde (8-10): intervento di adeguamento o miglioramento sismico eseguito secondo NTC 2008/2018, documentato
  - Giallo (5-7): interventi di rinforzo locale documentati, oppure ristrutturazione significativa ma senza specifico miglioramento sismico
  - Rosso (0-4): nessun intervento strutturale dalla costruzione originale, oppure interventi non documentati
- **Spiegazione per il cliente**: "Un edificio che e stato rinforzato o migliorato nel tempo e come un'auto che ha fatto i tagliandi regolari: non importa solo quando e stata costruita, ma anche quanto e stata curata nel tempo."

---

## Fasce di giudizio

| Fascia | Punteggio | Messaggio per il cliente | CTA |
|--------|-----------|--------------------------|-----|
| Critico | 0-30 | "L'edificio presenta diverse criticita che richiedono un approfondimento urgente. Ti consigliamo di far eseguire una verifica strutturale completa il prima possibile." | "Ti consigliamo una Verifica Statica Completa con sopralluogo e prove in situ per valutare con precisione lo stato della struttura. Contattaci per un preventivo." |
| Insufficiente | 31-50 | "Ci sono aspetti importanti da approfondire sulla sicurezza strutturale dell'edificio. Non significa che sia pericoloso, ma che servono verifiche." | "Con una Verifica Statica possiamo darti un quadro preciso dello stato strutturale e indicarti se e quali interventi sono necessari." |
| Sufficiente | 51-70 | "L'edificio ha una base strutturale che regge, ma ci sono margini di miglioramento che vale la pena esplorare, soprattutto in ottica sismica." | "Una Verifica Statica ti permettera di capire esattamente dove intervenire per portare l'edificio agli standard attuali di sicurezza." |
| Buono | 71-85 | "L'edificio e in buone condizioni strutturali. Ci sono piccoli aspetti da perfezionare o da monitorare nel tempo." | "Con una Verifica Statica di dettaglio possiamo confermare la piena conformita e suggerirti eventuali interventi di ottimizzazione." |
| Eccellente | 86-100 | "Ottimo! L'edificio risulta in eccellente condizione strutturale con documentazione adeguata. Solo verifiche di routine consigliate." | "Una Verifica Statica periodica ti permette di mantenere questo livello e documentare la conformita per eventuali compravendite o certificazioni." |

---

## Nota sul framework di valutazione rapida IS-V

Il pagellino e strumento di triage, non sostituisce la Verifica Statica. Tuttavia la corrispondenza approssimativa tra il punteggio complessivo e il parametro IS-V (Indice di Sicurezza Sismica, ζE NTC §8.3) e indicativamente:

| Fascia pagellino | Punteggio | IS-V atteso | Classe rischio DM 58/2017 (indicativa) |
|------------------|-----------|-------------|----------------------------------------|
| Eccellente | 86-100 | > 1.0 | A+/A |
| Buono | 71-85 | 0.8-1.0 | B |
| Sufficiente | 51-70 | 0.6-0.8 | C |
| Insufficiente | 31-50 | 0.4-0.6 | D |
| Critico | 0-30 | < 0.4 | E/F/G |

IS-V = PGA_capacita / PGA_domanda. Valori < 0.6 → miglioramento sismico raccomandato. Valori < 0.3 → adeguamento/demolizione da valutare.

La stima della classe rischio dal solo pagellino e **puramente indicativa**: la classificazione ufficiale DM 58/2017 richiede calcolo strutturale completo secondo le Linee Guida (metodo convenzionale o semplificato per muratura).
