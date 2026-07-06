# Scoring model — check-host-express

Benchmark e soglie per il calcolo dei 6 KPI del pagellino ricettivo. I valori sono mediane stimate da dati pubblici (Istat turismo 2024, STR, report HotelsCombined/ANAC, osservatorio Federalberghi) e conoscenza di mercato aggiornata a fine 2025. Servono come fallback quando la skill `benchmark-italia-business` non dispone del dato puntuale.

## Struttura dei benchmark

Ogni KPI ha 3 livelli di granularita:
1. **Tipologia** (6 categorie)
2. **Regione** (nord ovest, nord est, centro, sud, isole) — raggruppata per semplicita
3. **Stagionalita** (aperto tutto l'anno / stagionale estivo / stagionale invernale)

Il matching avviene con fallback a cascata: se manca la combinazione esatta, usare il livello superiore (es: tipologia × area invece di tipologia × regione).

## Tabella Master RevPAR mediano annuale (EUR)

Calcolato come RevPAR teorico: `ADR_mediano × Occupancy_mediana`. Riferito a strutture aperte tutto l'anno. Per stagionali moltiplicare occupancy per (365 / giorni apertura) e ADR invariato — il RevPAR normalizzato risulta diverso.

| Tipologia | Nord Ovest | Nord Est | Centro | Sud | Isole |
|---|---|---|---|---|---|
| Agriturismo | 52 | 68 | 74 | 48 | 58 |
| B&B piccolo (2-5 camere) | 38 | 45 | 52 | 36 | 42 |
| Affittacamere / casa vacanza | 34 | 42 | 48 | 32 | 38 |
| Hotel 3 stelle | 58 | 72 | 82 | 48 | 62 |
| Boutique hotel 4 stelle | 95 | 118 | 135 | 82 | 108 |
| Glamping / lodge | 72 | 88 | 95 | 68 | 92 |

**Soglie semaforo RevPAR** (rispetto alla mediana zona × tipologia):
- Verde: >= 100% mediana
- Giallo: 70% - 100% mediana
- Rosso: < 70% mediana

Esempio: agriturismo in Toscana con RevPAR di 55 EUR. Mediana Centro agriturismi = 74 EUR. Rapporto = 74%. Semaforo giallo.

## Occupancy mediana annuale

| Tipologia | Nord Ovest | Nord Est | Centro | Sud | Isole |
|---|---|---|---|---|---|
| Agriturismo | 45% | 52% | 58% | 42% | 48% |
| B&B piccolo | 48% | 55% | 62% | 45% | 52% |
| Affittacamere / casa vacanza | 42% | 50% | 55% | 38% | 46% |
| Hotel 3 stelle | 55% | 62% | 68% | 48% | 58% |
| Boutique hotel 4 stelle | 58% | 68% | 72% | 52% | 65% |
| Glamping / lodge | 62% | 70% | 68% | 65% | 72% |

**Soglie semaforo Occupancy assoluto**:
- Verde: >= 55%
- Giallo: 40% - 55%
- Rosso: < 40%

**Nota stagionalita**: se struttura aperta meno di 200 giorni anno, valutare Occupancy sui soli giorni aperti (piu indulgente). Soglia verde scende a 50%, gialla 35-50%, rossa < 35%.

## ADR mediano (EUR per notte)

Prezzo medio effettivo di vendita camera, netto IVA, include extra letto ma non colazione extra o F&B separato.

| Tipologia | Nord Ovest | Nord Est | Centro | Sud | Isole |
|---|---|---|---|---|---|
| Agriturismo | 115 | 130 | 128 | 115 | 120 |
| B&B piccolo | 79 | 82 | 84 | 80 | 81 |
| Affittacamere / casa vacanza | 81 | 84 | 87 | 84 | 83 |
| Hotel 3 stelle | 105 | 116 | 121 | 100 | 107 |
| Boutique hotel 4 stelle | 164 | 174 | 188 | 158 | 166 |
| Glamping / lodge | 116 | 126 | 140 | 105 | 128 |

**Soglie semaforo ADR** (rispetto alla mediana zona × tipologia):
- Verde: 85% - 115% mediana (in range sano)
- Giallo: 70% - 85% (sotto) oppure 115% - 130% (sopra, rischio volume)
- Rosso: < 70% (prezzo stracciato, segno di debolezza) oppure > 130% (rischio invenduto)

La logica "non troppo basso, non troppo alto" riflette la realta: un ADR molto sopra mediana senza posizionamento chiaro porta a bassa conversione. Un ADR molto sotto mediana e fuga sul prezzo che erode margini e reputation.

## Dipendenza OTA — quota Booking.com + Expedia

Quota % dei ricavi camera derivanti da OTA principali. Esclude Airbnb (considerata a parte per case vacanza).

**Soglie semaforo Dipendenza OTA**:
- Verde: < 50%
- Giallo: 50% - 65%
- Rosso: > 65%

Eccezione: per case vacanza e affittacamere <4 camere, soglie piu indulgenti (verde <65%, giallo 65-80%, rosso >80%) perche l'indipendenza dalle OTA richiede marketing che non scala su strutture micro.

## Rating Booking.com

Valore assoluto scala 1-10. Alcuni gestori riportano solo TripAdvisor (1-5) o Google (1-5) — convertire: `Booking_eq = TripAdvisor × 2`.

**Soglie semaforo Rating**:
- Verde: >= 8.7
- Giallo: 8.0 - 8.7
- Rosso: < 8.0

Sotto 8.0 la conversione cala drasticamente (sotto il cut-off di molti filtri Booking di default). Sopra 9.0 si entra nella fascia "Preferred" / badge Preferiti, con boost di visibilita.

Se mancano recensioni (< 10 review) il KPI non e calcolabile: assegnare giallo di default con nota "dati insufficienti".

## Quota diretto

% ricavi da canale diretto (sito ufficiale, WhatsApp, telefono, email, walk-in). Non include portali come Italywithus o siti di aggregazione.

**Soglie semaforo Quota diretto**:
- Verde: > 25%
- Giallo: 15% - 25%
- Rosso: < 15%

Eccezione per affittacamere micro (<4 camere): soglie spostate verso il basso (verde >15%, giallo 8-15%, rosso <8%) — e economicamente difficile spingere il diretto sotto quella soglia.

## Pesi score globale

Somma pesata dei 6 KPI, con conversione: Verde = 3 punti, Giallo = 1.5 punti, Rosso = 0 punti.

| KPI | Peso |
|---|---|
| RevPAR vs zona | 0.30 |
| Occupancy | 0.20 |
| ADR | 0.15 |
| Dipendenza OTA | 0.10 |
| Rating Booking | 0.15 |
| Quota diretto | 0.10 |

Formula: `Score = SUM(peso_i × punti_i) × 33.33` → risultato 0-100.

Esempio: tutti verdi = (0.30 + 0.20 + 0.15 + 0.10 + 0.15 + 0.10) × 3 × 33.33 = 100. Tutti rossi = 0. Mix misto proporzionato.

## Fasce giudizio finale

- **85-100 Eccellente**: continuare cosi, piccoli tuning trimestrali.
- **65-84 Buono**: qualche area da migliorare, niente urgenze strutturali.
- **45-64 Sufficiente**: serve un piano d'azione concreto entro 3-6 mesi.
- **25-44 Preoccupante**: problemi strutturali da affrontare subito.
- **0-24 Critico**: rischio economico reale, servizio HostBoost fortemente consigliato.

## Top 3 priorita — logica di selezione

1. Identificare i 3 KPI con semaforo rosso. Se meno di 3 rossi, completare con quelli gialli piu impattanti (peso piu alto prima).
2. Per ogni priorita generare un testo di 2-3 righe in italiano semplice, orientato all'azione:
   - Nome azione con verbo imperativo
   - Confronto numerico con la zona
   - Suggerimento operativo concreto ("risponditi alle recensioni degli ultimi 6 mesi", non "migliora la reputation")

## Regole regionali speciali

- **Sardegna/Sicilia estive**: occupancy alta (70%+) concentrata giugno-settembre. Se struttura aperta tutto l'anno, RevPAR annuo penalizzato da bassa stagione — considerare "RevPAR stagione alta" come indicatore complementare nella sezione note.
- **Trentino Alto Adige**: bi-stagionalita invernale (sci) + estiva (trekking). Mediane ADR piu elevate gia riflesse nel Nord Est.
- **Roma/Venezia/Firenze**: applicare moltiplicatore 1.15x alle mediane ADR del Centro per strutture in centro storico o zone top.
- **Borghi entroterra**: applicare moltiplicatore 0.85x alle mediane ADR della regione.

## Mapping regione → area

| Area | Regioni |
|---|---|
| Nord Ovest | Piemonte, Valle d'Aosta, Liguria, Lombardia |
| Nord Est | Trentino Alto Adige, Veneto, Friuli Venezia Giulia, Emilia Romagna |
| Centro | Toscana, Umbria, Marche, Lazio, Abruzzo |
| Sud | Molise, Campania, Puglia, Basilicata, Calabria |
| Isole | Sicilia, Sardegna |

## Aggiornamento benchmark

Questa tabella va rivalutata ogni 12 mesi con fonti aggiornate: STR reports Italia, Istat Tavole turismo, AIGO Observatory, Federalberghi. Versione attuale: 2025-Q4.
