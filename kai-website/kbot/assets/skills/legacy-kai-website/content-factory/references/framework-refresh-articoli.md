# Framework refresh articoli esistenti

## Perché il refresh vale quanto un nuovo articolo

Google premia i contenuti aggiornati. Un articolo che scivola dalla top 10 alla pagina 2 non è "morto" — ha autorità accumulata, ha backlink, ha storico. Aggiornarlo costa 1/3 del tempo di scriverne uno nuovo e spesso recupera più traffico.

## Criteri di selezione: quali articoli refreshare

### Priorità massima (refresh nel mese corrente)

- Articolo era top 10 ultimi 6 mesi, ora è pagina 2-3
- Articolo contiene dati obsoleti che impattano credibilità (es. "nel 2023...", prezzi vecchi, normativa superata)
- Articolo ha meta title/description che non riflettono il contenuto attuale
- Articolo è stagionale e si avvicina il picco (4-6 settimane prima)
- Articolo ha keyword primaria il cui intent è cambiato (Google ha ridefinito la SERP)

### Priorità media (refresh entro 2-3 mesi)

- Articolo ha traffico calante (-20% o più sui 3 mesi)
- Articolo manca di CTA chiara o la CTA è obsoleta (promo scaduta)
- Articolo è lungo < 800 parole e la SERP oggi vuole 1.500+
- Articolo manca di schema markup (FAQ, HowTo, Article)
- Articolo ha immagini brutte / grandi / senza alt

### Priorità bassa (refresh opportunistico)

- Articoli con buon traffico ma brutto UX (migliorare leggibilità)
- Articoli che potrebbero fare da pillar per cluster nuovi (espansione)

## Come identificare candidati al refresh

Strumenti (in ordine di efficacia):
1. **Google Search Console** → pagine con impression alti ma click in calo (CTR che scende)
2. **Google Analytics 4** → pagine con traffico calante mese su mese
3. **Ahrefs / Semrush** (se disponibili) → pagine che hanno perso posizioni
4. **Controllo manuale** → `site:dominio.it [keyword]` e verificare posizione attuale

## Tipologie di refresh

### 1. Aggiornamento leggero (2 ore)

- Aggiornare anno ("Guida 2025" → "Guida 2026")
- Aggiornare statistiche/numeri (sostituire dati vecchi con versione più recente)
- Aggiornare screenshot di interfacce (se UI è cambiata)
- Correggere link rotti
- Aggiornare meta title/description

**Quando usarlo**: articolo sostanzialmente buono ma con piccoli segni di invecchiamento.

### 2. Espansione (4-6 ore)

- Aggiungere 2-4 H2 nuovi (domande dalla PAA attuale)
- Aggiungere sezione FAQ (3-5 domande)
- Aggiungere schema markup (Article + FAQ)
- Espandere sezioni troppo brevi (portare da 80 parole a 200)
- Rinforzare internal linking

**Quando usarlo**: articolo ha buon posizionamento ma la SERP chiede più profondità.

### 3. Riscrittura parziale (6-8 ore)

- Riscrivere intro con hook più forte
- Riscrivere conclusione con CTA nuova
- Riorganizzare gli H2 (ordine diverso, più logico)
- Cambiare meta title/description per migliorare CTR
- Sostituire immagini obsolete

**Quando usarlo**: articolo ha calo di CTR pur restando posizionato, segno che il click non convince.

### 4. Riscrittura totale (8-12 ore)

- Cambiare angolo dell'articolo pur mantenendo URL e keyword primaria
- Rifare outline da zero basandosi sulla SERP attuale
- Redirect eventuale da vecchi URL correlati

**Quando usarlo**: articolo era scritto per un intent che oggi è cambiato, o il posizionamento è crollato drasticamente.

## Regola d'oro: preservare URL e ID canonical

Refresh ≠ pubblicare un nuovo articolo. L'URL deve restare identico (o redirect 301 se cambia lo slug). Questo preserva backlink e autorità.

## Tracciamento post-refresh

Dopo ogni refresh, annotare:
- Data refresh
- Tipologia (lieve/espansione/parziale/totale)
- Posizione keyword primaria PRIMA del refresh
- Posizione keyword primaria 4 settimane DOPO il refresh
- Traffico organico 30 giorni PRIMA vs 30 giorni DOPO
- Verdetto: recupero riuscito / parziale / fallito

## Segnali di successo

Un refresh è riuscito se entro 4-6 settimane:
- Posizione keyword primaria migliora di almeno 3 posizioni
- Traffico organico all'articolo aumenta di almeno 15%
- CTR in Search Console sale (se aveva impression stabili)

Se dopo 8 settimane non c'è recupero, il problema non è il contenuto: è la keyword stessa (intent cambiato, concorrenti molto più forti, keyword in declino). In quel caso, valutare deprecazione articolo e redirect verso contenuto più forte.

## Cadenza refresh consigliata

- Piano Light (2 refresh/mese): ogni articolo pubblicato negli ultimi 3 anni candidato almeno 1 volta/anno
- Piano Standard (3 refresh/mese): articoli top performer ogni 6 mesi, altri 1/anno
- Piano Intensive (4 refresh/mese): articoli top performer ogni 4 mesi, altri ogni 8-10 mesi
