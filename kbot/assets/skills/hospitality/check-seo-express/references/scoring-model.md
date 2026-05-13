# Modello di Scoring — check-seo-express

## Formula di calcolo

Il punteggio globale e una **media ponderata normalizzata a 100**:

```
Score = (somma di (score_fattore_i * peso_i) per i=1..10) / (somma di (10 * peso_i) per i=1..10) * 100
```

Ogni fattore ha un punteggio da 0 a 10 e un peso da 1 a 10.
Il denominatore massimo e: (10 * 70) = 700.

Quindi: **Score = (punti ottenuti / 700) * 100**

---

## Tabella dei 10 fattori

### 1. HTTPS attivo
- **Peso**: 8
- **Come si verifica**: controllare se l'URL usa il protocollo `https://`. Verificare che non ci siano redirect da HTTPS a HTTP.
- **Soglie**:
  - Verde (8-10): HTTPS attivo e funzionante
  - Giallo (5-7): HTTPS presente ma con mixed content (alcuni elementi caricati via HTTP)
  - Rosso (0-4): Sito servito in HTTP senza certificato SSL
- **Spiegazione per il cliente**: "Il lucchetto nella barra del browser dice ai visitatori che il sito e sicuro. Senza, Google lo penalizza e i clienti non si fidano a comprare o lasciare i dati."

### 2. Mobile-friendly
- **Peso**: 10
- **Come si verifica**: cercare il meta tag `viewport` nell'HTML. In modalita piattaforma, usare i dati Lighthouse per verificare il punteggio mobile. Verificare assenza di elementi con larghezza fissa che eccedono lo schermo.
- **Soglie**:
  - Verde (8-10): viewport configurato, layout responsive, nessun problema di usabilita mobile
  - Giallo (5-7): viewport presente ma con problemi minori (testo troppo piccolo, pulsanti ravvicinati)
  - Rosso (0-4): nessun viewport, layout fisso non adattabile al cellulare
- **Spiegazione per il cliente**: "Piu del 60% delle persone visita i siti dal telefono. Se il tuo sito non si vede bene sul cellulare, la maggior parte dei potenziali clienti se ne va dopo pochi secondi."

### 3. Velocita di caricamento
- **Peso**: 9
- **Come si verifica**: in modalita piattaforma usare `lighthouse_audit` per ottenere metriche di performance. In modalita consulenziale stimare dalla dimensione dell'HTML, numero di risorse esterne, presenza di script bloccanti.
- **Soglie**:
  - Verde (8-10): caricamento stimato sotto 3 secondi, HTML leggero, poche risorse bloccanti
  - Giallo (5-7): caricamento stimato 3-6 secondi, HTML medio, alcune risorse pesanti
  - Rosso (0-4): caricamento stimato oltre 6 secondi, HTML pesante, molte risorse bloccanti
- **Spiegazione per il cliente**: "Ogni secondo di attesa in piu fa perdere circa il 10% dei visitatori. Se il sito e lento, le persone tornano su Google e vanno dal concorrente."

### 4. Title tag
- **Peso**: 8
- **Come si verifica**: estrarre il contenuto del tag `<title>` dall'HTML. Verificare che esista, che non sia vuoto, che contenga parole chiave pertinenti, che sia lungo tra 30 e 60 caratteri.
- **Soglie**:
  - Verde (8-10): title presente, lunghezza corretta (30-60 caratteri), contiene parole chiave pertinenti al business
  - Giallo (5-7): title presente ma troppo corto/lungo, o generico (es. "Home", "Benvenuti")
  - Rosso (0-4): title assente o completamente irrilevante
- **Spiegazione per il cliente**: "Il titolo della pagina e la prima cosa che le persone vedono su Google. Se non dice chiaramente cosa fai e dove sei, nessuno clicca sul tuo risultato."

### 5. Meta description
- **Peso**: 7
- **Come si verifica**: cercare il tag `<meta name="description">` nell'HTML. Verificare che esista, non sia vuoto, sia lungo tra 120 e 160 caratteri, contenga una descrizione pertinente.
- **Soglie**:
  - Verde (8-10): meta description presente, lunghezza corretta (120-160 caratteri), pertinente e persuasiva
  - Giallo (5-7): presente ma troppo corta/lunga, o generica
  - Rosso (0-4): assente o irrilevante
- **Spiegazione per il cliente**: "La descrizione che appare sotto il titolo su Google. Se manca o non e convincente, le persone scelgono un altro risultato anche se il tuo sito e migliore."

### 6. H1 presente e pertinente
- **Peso**: 7
- **Come si verifica**: cercare il tag `<h1>` nell'HTML. Verificare che ci sia esattamente un H1, che contenga parole chiave pertinenti, che sia diverso dal title tag.
- **Soglie**:
  - Verde (8-10): un solo H1 presente, pertinente, con parole chiave rilevanti
  - Giallo (5-7): H1 presente ma generico, oppure piu di un H1
  - Rosso (0-4): H1 assente o vuoto
- **Spiegazione per il cliente**: "Il titolo principale della pagina dice a Google di cosa parla il sito. Se manca o e vago, Google fatica a capire quando mostrarti nei risultati di ricerca."

### 7. Alt tag immagini
- **Peso**: 5
- **Come si verifica**: contare le immagini (`<img>`) nell'HTML e verificare quante hanno l'attributo `alt` compilato con testo descrittivo (non vuoto, non generico tipo "image1.jpg").
- **Soglie**:
  - Verde (8-10): oltre l'80% delle immagini ha alt tag descrittivo
  - Giallo (5-7): tra il 40% e l'80% delle immagini ha alt tag
  - Rosso (0-4): meno del 40% delle immagini ha alt tag
- **Spiegazione per il cliente**: "Le descrizioni delle immagini aiutano Google a capire cosa mostri nel sito. In piu, rendono il sito accessibile a persone con difficolta visive. Due vantaggi in uno."

### 8. Internal linking
- **Peso**: 6
- **Come si verifica**: contare i link interni (`<a href>` che puntano allo stesso dominio) nell'HTML della homepage. Verificare che ce ne siano un numero ragionevole e che puntino a pagine importanti.
- **Soglie**:
  - Verde (8-10): almeno 10 link interni ben distribuiti verso pagine rilevanti
  - Giallo (5-7): tra 3 e 9 link interni, oppure link presenti ma solo nel menu
  - Rosso (0-4): meno di 3 link interni o nessun link interno nel contenuto
- **Spiegazione per il cliente**: "I collegamenti tra le pagine del sito aiutano Google a scoprire e capire tutto il tuo contenuto. Senza, alcune pagine restano invisibili ai motori di ricerca."

### 9. Presenza sitemap.xml
- **Peso**: 5
- **Come si verifica**: tentare di accedere a `[dominio]/sitemap.xml`. Verificare che esista, che sia un XML valido, che contenga URL del sito.
- **Soglie**:
  - Verde (8-10): sitemap.xml presente, valida, con URL aggiornati
  - Giallo (5-7): sitemap.xml presente ma incompleta o con errori
  - Rosso (0-4): sitemap.xml assente o non raggiungibile
- **Spiegazione per il cliente**: "La mappa del sito e come un indice che dai a Google per fargli trovare tutte le pagine. Senza, alcune pagine potrebbero non comparire mai nei risultati di ricerca."

### 10. Google Business Profile (attivita locali)
- **Peso**: 5
- **Come si verifica**: cercare nell'HTML riferimenti a Google Maps embed, schema.org LocalBusiness, indirizzo fisico strutturato. Verificare coerenza dei dati NAP (Nome, Indirizzo, Telefono).
- **Soglie**:
  - Verde (8-10): dati strutturati LocalBusiness presenti, NAP coerente, riferimento a Google Maps
  - Giallo (5-7): indirizzo presente ma non strutturato, nessun markup schema.org
  - Rosso (0-4): nessun riferimento geografico o dati di contatto strutturati
  - **Nota**: se il business non e locale (es. e-commerce puro, SaaS), assegnare 7/10 di default e segnalare che il fattore e meno rilevante
- **Spiegazione per il cliente**: "Se hai un negozio o un ufficio, Google Business Profile e fondamentale per farti trovare da chi cerca nella tua zona. E come essere sulle Pagine Gialle, ma gratis e molto piu efficace."

---

## Fasce di giudizio

| Fascia | Punteggio | Messaggio per il cliente | CTA |
|--------|-----------|--------------------------|-----|
| Critico | 0-30 | "Il tuo sito ha problemi seri che probabilmente ti stanno facendo perdere molti clienti. Serve un intervento urgente." | "Ti consigliamo un Audit SEO Tecnico completo per identificare tutti i problemi e creare un piano d'azione prioritizzato. Contattaci per un preventivo." |
| Insufficiente | 31-50 | "Il sito ha parecchi punti deboli. Con alcuni interventi mirati puoi migliorare molto la tua visibilita su Google." | "Con un Audit SEO Tecnico possiamo mapparti esattamente cosa sistemare e in che ordine per ottenere i risultati migliori nel minor tempo." |
| Sufficiente | 51-70 | "Il sito funziona ma sta lasciando sul tavolo delle opportunita. Con i giusti accorgimenti puoi fare un salto di qualita." | "Un Audit SEO Tecnico ti mostrera le opportunita nascoste e come sfruttarle per superare i concorrenti nei risultati di ricerca." |
| Buono | 71-85 | "Buon lavoro! Il sito ha una base solida. Ci sono ancora margini di miglioramento per scalare le posizioni su Google." | "Con un Audit SEO Tecnico possiamo individuare gli ultimi dettagli da ottimizzare per portarti nelle prime posizioni." |
| Eccellente | 86-100 | "Complimenti! Il sito e ben ottimizzato. Ci sono solo piccoli dettagli da perfezionare per raggiungere l'eccellenza." | "Un Audit SEO Tecnico puo aiutarti a mantenere questo livello e trovare opportunita avanzate che i concorrenti non sfruttano." |
