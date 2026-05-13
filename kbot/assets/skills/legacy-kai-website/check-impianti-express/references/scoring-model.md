# Modello di Scoring — check-impianti-express

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

### 1. Conformita DM 37/2008
- **Peso**: 20
- **Come si valuta**: verificare se gli impianti sono dotati di Dichiarazione di Conformita (DiCo) rilasciata da installatore abilitato ai sensi del DM 37/2008 (ex legge 46/90). In assenza di DiCo, verificare se esiste almeno una Dichiarazione di Rispondenza (DiRi) redatta da professionista abilitato. Impianti ante-1990 senza alcuna certificazione ricevono la massima penalizzazione.
- **Soglie**:
  - Verde (8-10): DiCo disponibile per tutti gli impianti, rilasciata da installatore abilitato
  - Giallo (5-7): DiCo parziale (solo alcuni impianti) oppure DiRi disponibile in sostituzione
  - Rosso (0-4): nessuna DiCo ne DiRi; impianti non certificati
- **Spiegazione per il cliente**: "La Dichiarazione di Conformita e il 'certificato di nascita' del tuo impianto: dice che e stato installato a regola d'arte. Senza questo documento, l'impianto risulta formalmente non a norma, anche se funziona."

### 2. Impianto di terra
- **Peso**: 15
- **Come si valuta**: verificare la presenza dell'impianto di messa a terra e la sua regolare verifica periodica. Per impianti in luoghi di lavoro (DPR 462/2001): verifica biennale obbligatoria da parte di organismo abilitato. Per impianti domestici: verifica consigliata. Chiedere all'utente se conosce la data dell'ultima verifica.
- **Soglie**:
  - Verde (8-10): impianto di terra presente e verificato periodicamente (ultimo verbale disponibile)
  - Giallo (5-7): impianto di terra presente ma verifica scaduta o mai effettuata
  - Rosso (0-4): impianto di terra assente o in stato sconosciuto
- **Spiegazione per il cliente**: "L'impianto di terra protegge le persone dalle scosse elettriche. E come la cintura di sicurezza dell'impianto elettrico: deve esserci e deve essere controllato regolarmente."

### 3. Protezioni differenziali
- **Peso**: 10
- **Come si valuta**: verificare la presenza di interruttori differenziali (salvavita) adeguati. Per ambienti ordinari: differenziale da 30 mA. Verificare se il differenziale e stato testato (pulsante di test) e se funziona correttamente. In edifici datati potrebbe mancare completamente.
- **Soglie**:
  - Verde (8-10): differenziali da 30 mA presenti su tutte le linee, testati e funzionanti
  - Giallo (5-7): differenziali presenti ma non su tutte le linee, oppure tipo e sensibilita da verificare
  - Rosso (0-4): differenziali assenti o non funzionanti
- **Spiegazione per il cliente**: "Il 'salvavita' e il dispositivo che stacca la corrente se qualcosa va storto, proteggendo le persone dalle scosse. Se manca o non funziona, il rischio di elettrocuzione e concreto."

### 4. Classe energetica
- **Peso**: 15
- **Come si valuta**: valutare la classe energetica dell'edificio sulla base dell'APE (Attestato di Prestazione Energetica) se disponibile, oppure stimarla in base all'anno di costruzione, tipo di isolamento, tipo di serramenti e tipo di impianto. Classi A4-B = ottime; C-D = accettabili; E-G = da migliorare.
- **Soglie**:
  - Verde (8-10): classe energetica A4-B, oppure edificio NZEB (Nearly Zero Energy Building)
  - Giallo (5-7): classe energetica C-D, edificio con margini di miglioramento
  - Rosso (0-4): classe energetica E-G, elevati consumi energetici
- **Spiegazione per il cliente**: "La classe energetica e come l'etichetta del frigorifero: ti dice quanto consuma il tuo edificio. Una classe bassa (E, F, G) significa bollette molto piu alte e un immobile che vale meno sul mercato."

### 5. Efficienza generazione
- **Peso**: 15
- **Come si valuta**: valutare l'efficienza del generatore di calore (caldaia, pompa di calore, ecc.). Caldaie a condensazione = alte efficienze. Caldaie tradizionali pre-2005 = basse efficienze. Pompe di calore con COP > 3.5 = ottimo. Verificare anche l'eta del generatore: oltre 15 anni, l'efficienza cala significativamente.
- **Soglie**:
  - Verde (8-10): generatore ad alta efficienza (caldaia a condensazione recente, pompa di calore COP > 3.5)
  - Giallo (5-7): generatore di media efficienza (caldaia a condensazione ante-2015, o tradizionale post-2005)
  - Rosso (0-4): generatore obsoleto (caldaia tradizionale ante-2005, oltre 15 anni, basso rendimento)
- **Spiegazione per il cliente**: "La caldaia o la pompa di calore e il 'motore' del tuo riscaldamento. Se e vecchia o inefficiente, brucia piu gas (o consuma piu elettricita) per ottenere lo stesso calore. Sostituirla puo farti risparmiare il 20-40% sulla bolletta."

### 6. Regolazione e contabilizzazione
- **Peso**: 10
- **Come si valuta**: verificare la presenza di sistemi di regolazione (termostati, valvole termostatiche, cronotermostati) e, per impianti centralizzati, sistemi di contabilizzazione individuale del calore (obbligatori dal D.Lgs. 102/2014). Per impianti autonomi: verificare almeno la presenza di cronotermostato ambiente.
- **Soglie**:
  - Verde (8-10): regolazione ambiente per ambiente (valvole termostatiche + cronotermostato); contabilizzazione individuale se impianto centralizzato
  - Giallo (5-7): regolazione parziale (solo cronotermostato centrale); contabilizzazione da installare
  - Rosso (0-4): nessuna regolazione ambiente; nessuna contabilizzazione su impianto centralizzato
- **Spiegazione per il cliente**: "Le valvole termostatiche e i termostati ti permettono di regolare il calore stanza per stanza, evitando di sprecare energia. Senza, e come lasciare tutte le luci accese in casa anche quando non serve."

### 7. Manutenzione
- **Peso**: 15
- **Come si valuta**: verificare la regolarita della manutenzione degli impianti. Per caldaie: manutenzione annuale obbligatoria con controllo fumi (DPR 74/2013, frequenza in base a potenza e tipo). Per impianti elettrici in luoghi di lavoro: verifiche periodiche DPR 462/2001. Chiedere all'utente la data dell'ultimo intervento di manutenzione.
- **Soglie**:
  - Verde (8-10): manutenzione regolare documentata, libretto impianto aggiornato, bollino blu valido
  - Giallo (5-7): manutenzione effettuata ma non regolare, libretto impianto da aggiornare
  - Rosso (0-4): manutenzione mai effettuata o scaduta da oltre 2 anni
- **Spiegazione per il cliente**: "La manutenzione della caldaia e come il tagliando dell'auto: e obbligatoria per legge e serve a garantire che l'impianto funzioni in sicurezza e senza sprechi. Senza manutenzione, rischi anche una multa."

---

## Fasce di giudizio

| Fascia | Punteggio | Messaggio per il cliente | CTA |
|--------|-----------|--------------------------|-----|
| Critico | 0-30 | "Gli impianti presentano gravi non conformita che mettono a rischio la sicurezza e comportano sanzioni. Serve un intervento urgente." | "Ti consigliamo un Audit Impiantistico Completo per mappare tutte le criticita e pianificare gli interventi di adeguamento. Contattaci per un preventivo." |
| Insufficiente | 31-50 | "Ci sono diverse criticita impiantistiche da risolvere. Alcuni interventi sono urgenti per la sicurezza." | "Con un Audit Impiantistico possiamo darti un quadro completo e un piano di interventi prioritizzato per costi e urgenza." |
| Sufficiente | 51-70 | "Gli impianti funzionano ma ci sono margini di miglioramento importanti, sia per la sicurezza che per l'efficienza energetica." | "Una Diagnosi Energetica e un check impiantistico ti mostrano esattamente dove intervenire per risparmiare e metterti in regola." |
| Buono | 71-85 | "Buona situazione impiantistica! Ci sono piccoli aspetti da perfezionare, soprattutto in ottica di risparmio energetico." | "Con un Audit Impiantistico di dettaglio possiamo identificare le ultime ottimizzazioni per massimizzare efficienza e risparmio." |
| Eccellente | 86-100 | "Ottimo! Gli impianti risultano conformi e efficienti. Solo manutenzione ordinaria e verifiche periodiche." | "Una Diagnosi Energetica avanzata puo aiutarti a esplorare opportunita come incentivi fiscali e tecnologie innovative." |
