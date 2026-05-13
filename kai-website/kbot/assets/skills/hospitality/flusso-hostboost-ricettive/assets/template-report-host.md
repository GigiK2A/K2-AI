# Template Report DOCX — HostBoost

Struttura del report executive consegnato al cliente al termine del flusso HostBoost. 12-15 pagine, tono revenue manager severo ma comprensibile. Generato via skill `docx`.

## Impostazione generale

- Formato: A4, margini 1 pollice (2.54 cm), font Calibri 11 pt
- Header: logo K2-AI (placeholder) + "HostBoost — Diagnosi revenue management"
- Footer: nome struttura + data + numero pagina
- Colori: H1 blu scuro `1F3864`, H2 blu medio `2E75B6`, semafori verde `548B54` / giallo `E6B800` / rosso `C0392B`

## Struttura capitoli

### Copertina
- Titolo: "HostBoost — Diagnosi revenue management per {Nome Struttura}"
- Sottotitolo: "Analisi dati {anno n-1} e {anno n} — Piano ricavi 12 mesi"
- Data consegna
- Logo K2-AI
- Claim di chiusura: "Il revenue manager che non hai, costruito su misura sulla tua struttura."

### Pagina 2 — Executive summary (1 pagina)
Una pagina sintetica con:
- 3 numeri chiave in evidenza (RevPAR attuale, gap vs mediana zona, RevPAR target 12 mesi nello scenario ottimistico)
- Diagnosi in 4 righe prose: "La tua struttura ha [sintesi della situazione]. Il problema principale e [criticita 1]. L'opportunita maggiore e [opportunita 1]. Con le azioni suggerite in 12 mesi si puo raggiungere [target]."
- 5 azioni prioritarie in bullet con impatto stimato

### Capitolo 1 — La tua struttura oggi (2 pagine)
Fotografia descrittiva:
- Dati struttura (tipologia, camere, zona, stagionalita, apertura)
- Mix canali attuale con grafico a torta
- Dati di input raccolti (periodo analizzato, qualita dati)
- Assunzioni usate dove i dati mancavano

### Capitolo 2 — Performance e KPI (3 pagine)
Il cuore quantitativo:

**2.1 I tre KPI core**
Tabella con ADR, Occupancy, RevPAR mensili ultimi 12 mesi + grafico RevPAR mensile + YoY se 24 mesi disponibili.

**2.2 Stagionalita**
Curva mensile occupancy + RevPAR. Identificazione bassa / spalla / alta stagione. Durata bassa stagione, gap fra picco e valle.

**2.3 Benchmark zona e segmento**
Tabella di confronto con 3 colonne: valore cliente / mediana zona+tipologia / top quartile. Semaforo per ogni KPI.

**2.4 Metriche estese**
ALOS, booking window, cancellation rate. Per ciascuna: valore e commento.

### Capitolo 3 — Distribuzione e canali (2 pagine)
**3.1 Mix canali attuale**
Tabella con: canale / % notti / % ricavi / ADR lordo / commissione / Net ADR / trend YoY.

**3.2 Dipendenza OTA**
Analisi concentrazione. Se Booking > 60% → segnalazione rischio con quantificazione (quanto perderesti con una sospensione temporanea del listing).

**3.3 Canale diretto**
Stato attuale: sito, booking engine, strumenti attivi. Gap tra dove sei e dove potresti stare.

**3.4 Disparity check**
Se rilevate disparity involontarie, elenco date con gap di prezzo fra canali.

### Capitolo 4 — Pricing e opportunita (2 pagine)
**4.1 Logica pricing attuale**
Descrizione tariffe (bassa/media/alta), offerte ricorrenti, minimum stay impostati.

**4.2 Gap pricing identificati**
Tabella mese per mese: dove il prezzo e troppo alto (occupancy bassa con prezzo alto) e dove e troppo basso (sold out con prezzo fermo). Quantificazione del gap in EUR/anno.

**4.3 Competitive set pricing**
Confronto su 20 date campione: prezzo cliente vs mediana compset (3-5 strutture). Tabella e grafico scatter.

### Capitolo 5 — Recensioni e reputation (1-2 pagine)
**5.1 Rating per piattaforma**
Tabella rating Booking / TripAdvisor / Google / Airbnb + trend YoY.

**5.2 Temi ricorrenti**
Top 5 temi positivi e top 5 temi negativi con frequenza %. Citazione di 2-3 recensioni campione per ciascun tema.

**5.3 Response rate**
Stato attuale della gestione recensioni da parte del titolare. Suggerimenti.

### Capitolo 6 — Piano ricavi 12 mesi (2-3 pagine)
**6.1 Tre scenari**
Tabella scenario con RevPAR atteso, Occupancy attesa, ADR atteso, Ricavi camera annuali attesi. Grafico a barre comparativo.

**6.2 Calendario pricing — sintesi**
Non l'intero calendario (sta nel cruscotto XLSX) ma una sintesi: BAR medio per fascia stagionale proposto vs attuale. Minimum stay suggeriti per weekend / ponti / alta stagione.

**6.3 Mix canali target**
Proposta di ribilanciamento canali a 12 mesi con quantificazione (se fai queste azioni, ti sposti dal 70%/20%/10% al 55%/35%/10%, riducendo commissioni di X EUR l'anno).

**6.4 Le 5 azioni prioritarie**
Per ciascuna delle 5 azioni:
- **Nome azione** (es. "Attivare Google Hotel Ads con budget 300 EUR/mese")
- **Impatto stimato** (es. "+8% diretto, +4% RevPAR generale")
- **Fattibilita** (alta / media / bassa)
- **Tempo implementazione** (es. "2 settimane")
- **Costo stimato** (es. "300 EUR/mese Google Ads + 500 EUR setup iniziale")
- **Come si fa** (2-3 righe pratiche)

### Capitolo 7 — Assunzioni e limitazioni (0.5 pagine)
Lista esplicita delle assunzioni fatte nell'analisi e delle limitazioni dovute a dati mancanti. Tono: trasparenza.

### Ultima pagina — Prossimi passi
- Sintesi risultati attesi
- Come usare il cruscotto XLSX per mantenere vivo il lavoro
- Proposta commerciale implicita per contratto continuativo K2-AI HOST (89 EUR/mese + 15% fee su delta RevPAR)
- Contatti K2-AI e come iniziare

## Note di stile

- **Mai un numero senza contesto**: ogni indicatore e seguito da benchmark e giudizio.
- **Tono diretto**: non "si consiglia di valutare l'opportunita di..." ma "aumenta il BAR di giugno del 10% a partire da oggi".
- **Paragrafi brevi**: massimo 5 righe per paragrafo. Il cliente non legge lenzuolate.
- **Bullet parsimoniosi**: solo nelle sezioni azioni e liste. Il resto in prosa.
- **Tabelle con semaforo**: ovunque possibile, una colonna semaforo per lettura visiva rapida.
- **Grafici nativi docx** dove utili: curve stagionalita, torta canali, barre scenari. Matplotlib pre-generato in caso se docx non li supporta nativamente.
- **No jargon**: "tariffa piu bassa vendibile" prima di introdurre il termine BAR. "Indice di domanda" prima di introdurre DBI.
