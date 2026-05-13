# Framework Revenue Management Ricettive — HostBoost

Riferimento operativo per la diagnosi revenue management di piccole strutture ricettive italiane (5-30 camere). Non e un manuale teorico: e il manuale che serve al revenue manager simulato dalla skill per prendere decisioni coerenti.

## 1. Le tre metriche ossatura: ADR, Occupancy, RevPAR

### ADR — Average Daily Rate
Prezzo medio di vendita della camera.
Formula: `ADR = Ricavi camera / Notti vendute`

Esempio: se l'agriturismo ha fatto 80.000 EUR di ricavi alloggio vendendo 1.200 notti, l'ADR e 66,67 EUR.

Interpretazione:
- ADR alto + occupancy bassa = prezzi probabilmente troppo alti per il mercato
- ADR basso + occupancy alta = probabile sottoprezzo, si lascia margine sul tavolo
- ADR stabile YoY con inflazione al 5% = erosione reale del prezzo

### Occupancy Rate
Percentuale di camere vendute sulle camere disponibili.
Formula: `Occupancy = Notti vendute / Notti disponibili`

Dove `Notti disponibili = N. camere x Giorni di apertura`.

Per strutture stagionali considerare solo i giorni di apertura effettivi. Un agriturismo aperto 200 giorni l'anno con 8 camere ha 1.600 notti disponibili.

Interpretazione:
- Occupancy > 85% su tutto l'anno = mercato saturato, pricing troppo basso in alcuni periodi
- Occupancy tra 60% e 80% = range salutare per stagionali
- Occupancy < 50% = problema strutturale (pricing, visibilita, prodotto)

### RevPAR — Revenue Per Available Room
La metrica che unisce le due sopra. E la piu importante.
Formula: `RevPAR = Ricavi camera / Notti disponibili` oppure `RevPAR = ADR x Occupancy`

Esempio: 80.000 EUR / 1.600 notti disponibili = 50 EUR di RevPAR.

Il RevPAR dice se il business sta crescendo realmente, al netto di occupancy e pricing. Due strutture possono avere lo stesso fatturato con logiche diverse: una piena a prezzi bassi, una mezza vuota a prezzi alti. Il RevPAR e il tiebreaker.

## 2. Metriche estese per diagnosi completa

### TRevPAR — Total RevPAR
Include ricavi ancillari (ristorazione, spa, attivita).
Formula: `TRevPAR = (Ricavi camera + Ricavi F&B + Ricavi altri servizi) / Notti disponibili`

Utile quando la struttura genera ricavi significativi oltre la camera (agriturismi con ristorante, boutique hotel con spa).

### GOPPAR — Gross Operating Profit Per Available Room
Il RevPAR dei profitti.
Formula: `GOPPAR = GOP / Notti disponibili` dove `GOP = Ricavi totali - Costi operativi diretti`

Se disponibili i costi, e la metrica che dice se il business e sostenibile. Un RevPAR di 80 EUR con GOPPAR di 12 EUR dice che il business e grasso di ricavi ma sottile di margini.

### ALOS — Average Length of Stay
Durata media del soggiorno.
Formula: `ALOS = Notti vendute / Numero prenotazioni`

ALOS 1.3 = mordi e fuggi, alta rotazione, alti costi di pulizia e acquisizione.
ALOS 2.5-3 = equilibrio tipico di destinazione non citta d'arte.
ALOS > 4 = soggiorni lunghi, tipico agriturismo o mare, margini migliori ma meno flessibilita.

Leva operativa: alzare il minimum stay nei weekend aumenta ALOS e riduce gap fra check-in e check-out.

### Booking Window / Lead Time
Giorni medi fra la data di prenotazione e la data di check-in.
- Booking window corto (< 14 giorni) = last minute, prezzi tipicamente piu bassi, meno programmazione
- Booking window lungo (> 60 giorni) = early booking, leva per pricing piu alto con promo early

### Cancellation Rate
Percentuale di prenotazioni cancellate prima del check-in.
Benchmark: 15-25% su Booking.com e normale. > 35% e segno di problema (tariffe non rimborsabili troppo poche, overpromise, gestione revenue aggressiva).

### Disparity Rate
Scarto fra prezzo camera per stessa data fra canali.
Molti OTA obbligano parita. Disparity involontaria (dimenticanze su channel manager) puo generare commissioni aggiuntive o sospensioni. Verificare a campione.

## 3. Regole di pricing dinamico

### BAR — Best Available Rate
La tariffa piu bassa vendibile pubblicamente per quella data. Tutte le altre tariffe derivano da BAR:
- Non rimborsabile = BAR - 5% / -10%
- Early booking (>60gg) = BAR - 10% / -15%
- Last minute (<3gg) = BAR o BAR - 5% (dipende dall'occupancy residua)
- Mezza pensione = BAR + costo marginale F&B
- Pacchetto weekend = sconto lungo soggiorno su 2 notti

### Regola del pick-up
Se a 30 giorni dalla data ho venduto il 70% delle camere, la data e in pick-up forte: aumentare BAR.
Se a 30 giorni dalla data ho venduto < 30% delle camere, la data e in pick-up debole: tenere BAR o abbassare selettivamente per non cannibalizzare.

Tabella pick-up tipica per agriturismo:
| Giorni alla data | Pick-up atteso | Azione se sotto soglia |
|---|---|---|
| 60 | 15-25% | Monitorare, normale |
| 30 | 40-60% | Attenzione, verificare prezzo vs compset |
| 14 | 65-80% | Abbassare selettivamente, lanciare last minute |
| 7 | 80-95% | Last minute aggressivo, mobile-only rate |

### DBI — Demand-Based Index
Indice di domanda per data, da 0 (bassa) a 10 (altissima). Costruito da: stagione, giorno settimana, eventi locali, ponti, festivita, ricerche Google Hotel Ads per la destinazione, dati storici.

Azione: BAR scala con DBI.
- DBI 0-2: BAR bassa stagione minima
- DBI 3-5: BAR media
- DBI 6-7: BAR media alta
- DBI 8-10: BAR alta + minimum stay + no discount

### Minimum Stay
Impone un numero minimo di notti per prenotare una data.
Regola: usare minimum stay per:
- Weekend in alta/media stagione (MLS 2)
- Ponti festivi (MLS 3)
- Eventi locali fortemente attrattori (MLS 3-4)

Mai usare minimum stay come regola di default: riduce la conversione su prenotazioni corte che riempirebbero comunque.

### Closed to Arrival / Closed to Departure
Usare per evitare check-in/check-out in giorni operativamente difficili (es. lunedi quando la reception e chiusa).

## 4. Mix canali e commissioni

### Commissioni tipiche in Italia (2024-2025)
| Canale | Commissione | Note |
|---|---|---|
| Booking.com standard | 15% | 17% se Preferred Partner, 18-20% se Genius |
| Booking.com Preferred Plus | 17% | +2% su standard, visibilita maggiore |
| Expedia (base) | 15% | Spesso 18% come Compete o Accelerator |
| Airbnb | 3% host + 14% ospite | O 15% host-only se in programma alloggi tradizionali |
| Agoda / Hotels.com | 15-18% | Inclusi in pacchetti Expedia |
| HRS / eDreams | 10-15% | Volumi inferiori |
| Tour operator | 20-30% | In cambio di volume pre-stagione |

### Net ADR per canale
Formula: `Net ADR = ADR - Commissione - Costi acquisizione`

Per il canale diretto i costi acquisizione sono: Google Ads (~50-150 EUR/mese per piccola struttura), metasearch (Trivago / Google Hotel Ads, 10-15% CPC per camera), booking engine (50-200 EUR/mese).

Esempio: ADR lordo 100 EUR.
- Booking.com: 100 - 17 = 83 EUR net
- Diretto con costi acquisizione medi: 100 - 12 = 88 EUR net (e circa il 5-6% piu redditizio, non enormemente)

La battaglia per il diretto vale, ma va vinta sulla qualita (fidelizzazione, servizio, upsell post-soggiorno) non solo sulla commissione.

### Dipendenza OTA
- Booking.com > 60% dei ricavi = rischio, concentrazione
- Booking.com + Expedia > 80% = rischio forte
- Target sano: Booking 40-50% / Expedia 10-15% / Airbnb 5-15% / diretto 25-35%

## 5. Stagionalita italiana

### Profilo Italia turistica
- **Alta stagione**: giugno-agosto (mare), dicembre-gennaio e febbraio per montagna, aprile-ottobre per arte, autunno per laghi
- **Bassa stagione**: novembre-marzo (escluso natale) per la maggior parte delle destinazioni
- **Spalla**: marzo-aprile, settembre-ottobre — il tesoro per il revenue manager

Azione classica: estendere la spalla di 2-3 settimane con pricing aggressivo e lead gen mirata (weekend romantici in ottobre, Pasqua anticipata, ponti).

### Eventi italiani ad alta domanda
- Ponti civili: 25 aprile, 1 maggio, 2 giugno, Ferragosto, 1 novembre, 8 dicembre
- Eventi locali: sagre, festival (es. Vinitaly Verona, Salone del Mobile Milano, Mostra del Cinema Venezia)
- Capodanno, Pasqua, Epifania

Segnare nel calendario pricing tutte le date a DBI 8-10 con almeno 18 mesi di anticipo.

## 6. Recensioni e reputation

### Soglie di rating
| Rating medio Booking | Giudizio | Impatto conversione |
|---|---|---|
| > 9.0 | Eccellente | Conversion +30% vs media zona |
| 8.5-9.0 | Molto buono | Conversion in linea |
| 8.0-8.5 | Buono | Conversion -10% |
| 7.5-8.0 | Sufficiente | Conversion -25% |
| < 7.5 | Problema | Conversion -40%, serve action plan urgente |

### Gestione recensioni
- Rispondere a tutte le recensioni negative entro 48h, tono professionale, non difensivo
- Rispondere al 50-70% delle recensioni positive (selezione ragionata)
- Non ignorare. Un 7.8 in risalita verso 8.2 e molto piu venditore di un 8.5 stagnante

### Temi ricorrenti
Text analytics su ultime 50 recensioni. Se il tema "colazione" appare in 40% delle negative, e la priorita numero uno. Se appare in 40% delle positive, e un asset da comunicare.

## 7. Canale diretto: gli strumenti minimi

Per piccola struttura che vuole passare dal 10% al 30% di diretto:

1. **Sito mobile-first** con motore di ricerca camere visibile sopra la piega. Booking engine integrato (Octorate, Hotel Runner, Simplebooking, Vertical Booking). Budget: 1.500-3.500 EUR una tantum + 50-200 EUR/mese.
2. **Miglior prezzo garantito** vs OTA con -5% o -10% sconto pubblicizzato. Serve attivare parity con tutti i canali dove applicare lo sconto privato.
3. **Google Business Profile** ottimizzato, foto aggiornate, orari, categoria corretta, recensioni con risposta.
4. **Google Hotel Ads** con budget minimo 200-500 EUR/mese tramite meta-partner (Triptease, The Hotels Network, Hotellaunch).
5. **Newsletter post-soggiorno** con codice sconto per prenotazione futura. Apertura dal 25% al 40% tipica per hospitality.
6. **WhatsApp Business** come canale di contatto. Risposta sotto 1 ora. Tasso di conversione WhatsApp-booking 40-60% in hospitality italiana.

## 8. Segnali di sofferenza da non ignorare

Se trovi uno di questi segnali, segnalalo in rosso nel report:

- RevPAR in calo 2 anni consecutivi
- Rating Booking < 7.5
- Cancellation rate > 35%
- Dipendenza Booking.com > 75%
- Assenza totale di canale diretto digitale
- Nessuna risposta alle recensioni degli ultimi 6 mesi
- Foto pubblicate su OTA con qualita < standard (sfocate, luce pessima, camera disordinata)
- Descrizione OTA generica, < 200 caratteri
- Orari check-in / check-out rigidi non compatibili con clientela target
- Minimum stay impostato male (2 notti anche in giorni a bassa domanda)
