# Modello di Scoring Competitivo

## Le 5 dimensioni competitive

Ogni dimensione viene valutata con un punteggio da 1 a 10 e ha un peso specifico da 1 a 5.

### 1. Prezzo (Peso: 4)

Valuta quanto l'azienda e competitiva sul prezzo rispetto al mercato di riferimento.

| Score | Significato |
|-------|------------|
| 1-3 | Prezzi significativamente piu alti del mercato senza giustificazione percepita |
| 4-5 | Prezzi sopra la media, qualche difficolta nel giustificare il premium |
| 6-7 | Prezzi allineati al mercato o premium giustificato da valore percepito |
| 8-10 | Prezzo molto competitivo oppure premium riconosciuto e accettato dal mercato |

**Semaforo**:
- Rosso: 1-3
- Giallo: 4-6
- Verde: 7-10

### 2. Qualita / Differenziazione (Peso: 5)

Valuta quanto l'offerta si distingue dai competitor per qualita, unicita, valore aggiunto.

| Score | Significato |
|-------|------------|
| 1-3 | Offerta indistinguibile dai competitor, nessun elemento unico |
| 4-5 | Qualche elemento differenziante ma non comunicato o non percepito |
| 6-7 | Differenziazione chiara su almeno 1-2 aspetti riconosciuti dai clienti |
| 8-10 | Offerta unica nel mercato, clienti scelgono specificamente per questa ragione |

**Semaforo**:
- Rosso: 1-3
- Giallo: 4-6
- Verde: 7-10

### 3. Distribuzione / Accessibilita (Peso: 3)

Valuta quanto e facile per il cliente trovare e acquistare il prodotto/servizio.

| Score | Significato |
|-------|------------|
| 1-3 | Canale unico, copertura limitata, nessuna presenza online efficace |
| 4-5 | Qualche canale attivo ma copertura inferiore ai competitor |
| 6-7 | Multi-canale funzionante, buona copertura territoriale o online |
| 8-10 | Presenza capillare, omnichannel, il cliente ti trova ovunque cerchi |

**Semaforo**:
- Rosso: 1-3
- Giallo: 4-6
- Verde: 7-10

### 4. Notorieta / Brand (Peso: 4)

Valuta quanto l'azienda e conosciuta e quale reputazione ha nel suo mercato.

| Score | Significato |
|-------|------------|
| 1-3 | Sconosciuta fuori dalla cerchia diretta, nessuna presenza online significativa |
| 4-5 | Conosciuta localmente o in una nicchia, presenza online basica |
| 6-7 | Buona reputazione nel territorio/settore, presenza online attiva |
| 8-10 | Brand riconosciuto, prima scelta nella mente del cliente target |

**Semaforo**:
- Rosso: 1-3
- Giallo: 4-6
- Verde: 7-10

### 5. Innovazione (Peso: 4)

Valuta la capacita dell'azienda di innovare prodotto, processo o modello di business.

| Score | Significato |
|-------|------------|
| 1-3 | Nessuna innovazione negli ultimi 3 anni, offerta statica |
| 4-5 | Qualche aggiornamento ma reattivo, non proattivo |
| 6-7 | Innovazione regolare, almeno 1 novita significativa/anno |
| 8-10 | Innovazione come DNA aziendale, spesso primi nel mercato |

**Semaforo**:
- Rosso: 1-3
- Giallo: 4-6
- Verde: 7-10

---

## Formula Competitiveness Index

```
Competitiveness Index = (somma(score_i * peso_i) / somma(max_score * peso_i)) * 100
```

Dove:
- `score_i` = punteggio della dimensione i (1-10)
- `peso_i` = peso della dimensione i
- `max_score` = 10

### Calcolo dettagliato

| Dimensione | Peso | Score (1-10) | Contributo |
|-----------|------|-------------|------------|
| Prezzo | 4 | score_1 | score_1 * 4 |
| Qualita/Differenziazione | 5 | score_2 | score_2 * 5 |
| Distribuzione/Accessibilita | 3 | score_3 | score_3 * 3 |
| Notorieta/Brand | 4 | score_4 | score_4 * 4 |
| Innovazione | 4 | score_5 | score_5 * 4 |
| **Totale** | **20** | | **somma contributi** |

```
Index = (somma contributi / 200) * 100
```

Il denominatore e 200 perche: peso_totale (20) * max_score (10) = 200.

---

## Fasce di giudizio

### Vulnerabile (0-30)

**Messaggio**: "La tua azienda e in una posizione critica. I competitor ti stanno superando su piu fronti e rischi di perdere clienti velocemente. Serve un piano d'azione immediato."

**CTA upsell**: "Richiedi un'analisi settoriale completa per capire dove intervenire subito e proteggere il tuo business. Il check-up approfondito ti da un piano d'azione in 5 mosse concrete."

### In difesa (31-50)

**Messaggio**: "Stai reggendo ma sei sotto pressione. I competitor si stanno muovendo e se non reagisci rischi di scivolare. Hai delle basi su cui costruire, ma servono scelte precise."

**CTA upsell**: "Con un'analisi settoriale completa identifichiamo le 3 mosse piu efficaci per passare dalla difesa all'attacco. Non aspettare che i competitor prendano altro terreno."

### Competitivo (51-70)

**Messaggio**: "Buona posizione! Sei nel gioco e hai delle carte da giocare. Ci sono margini concreti per migliorare e distanziarti dai rivali. Il momento e adesso."

**CTA upsell**: "Sei a un passo dal diventare il riferimento del tuo mercato. L'analisi settoriale completa ti mostra esattamente quali leve tirare per fare il salto di qualita."

### Forte (71-85)

**Messaggio**: "Posizione solida, complimenti. Hai vantaggi reali sui competitor. Ora il punto e consolidare quello che funziona e attaccare dove loro sono deboli."

**CTA upsell**: "Sei forte, ma puoi dominare. L'analisi settoriale completa ti rivela le vulnerabilita dei competitor e come sfruttarle prima che si rafforzino."

### Dominante (86-100)

**Messaggio**: "Sei il riferimento del tuo mercato. I competitor ti guardano e cercano di imitarti. Il tuo compito ora e proteggere il vantaggio e innovare per restare avanti."

**CTA upsell**: "Anche i leader devono guardarsi le spalle. L'analisi settoriale completa monitora le mosse dei competitor e ti avvisa prima che diventino una minaccia reale."
