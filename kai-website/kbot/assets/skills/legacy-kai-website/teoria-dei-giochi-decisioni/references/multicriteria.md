# Analisi multicriterio (AHP lite)

Quando devi decidere tra opzioni su dimensioni eterogenee (costo, qualità, tempo, rischio, reputazione...), un AHP semplificato è spesso lo strumento giusto. È veloce, trasparente, riproducibile e comunica bene.

## Procedura in 6 passi

### 1. Definisci l'obiettivo

Una frase che inizia con "Scegliere l'opzione che massimizza/minimizza X entro il vincolo Y". L'obiettivo chiaro previene criteri mal allineati.

### 2. Identifica i criteri

Max 6-7 criteri (oltre diventa confuso). Regola: i criteri devono essere:
- **Rilevanti** per l'obiettivo
- **Indipendenti** tra loro (no doppi conteggi)
- **Misurabili** (almeno su scala ordinale)
- **Completi** (coprono i fattori chiave della decisione)

Esempi di criteri comuni:
- Costo totale di possesso (TCO)
- Tempo di implementazione
- Rischio di esecuzione
- Scalabilità
- Competenze del team
- Rischio regolatorio
- Flessibilità futura
- Impatto sul brand
- Facilità di reverse (costo di uscita)

### 3. Pesa i criteri

Distribuisci 100 punti tra i criteri secondo la loro importanza relativa per questo obiettivo specifico. Esempio:

| Criterio | Peso |
|---|---|
| TCO | 30 |
| Time-to-market | 25 |
| Scalabilità | 20 |
| Competenze team | 15 |
| Rischio esecuzione | 10 |
| **Totale** | **100** |

**Check di sanità**: se il criterio con peso 10 scompare dall'analisi, la decisione cambierebbe? No → OK, è marginale. Sì → forse pesa di più di quanto pensavi.

### 4. Scoring delle opzioni

Per ogni opzione, dai un punteggio 1-5 (o 1-10) su ogni criterio. Scala consigliata:

| Punteggio | Interpretazione |
|---|---|
| 5 | Eccellente — quasi l'ideale su questo criterio |
| 4 | Molto buono |
| 3 | Accettabile / standard |
| 2 | Debole, problematico |
| 1 | Grave deficit, potenziale dealbreaker |

Prima di passare alla matematica, annota 1 frase che giustifica ogni punteggio. Quella frase vale quanto il numero — è ciò che rende l'analisi difendibile.

### 5. Calcola e confronta

Punteggio pesato = Σ (peso × score / 100) per ciascuna opzione.

Esempio:

| Criterio | Peso | Opzione A | Opzione B | Opzione C |
|---|---|---|---|---|
| TCO | 30 | 5 | 3 | 4 |
| Time-to-market | 25 | 3 | 5 | 4 |
| Scalabilità | 20 | 4 | 2 | 5 |
| Competenze team | 15 | 2 | 5 | 3 |
| Rischio esecuzione | 10 | 4 | 4 | 3 |
| **Totale pesato** | | **3.75** | **3.65** | **3.95** |

### 6. Sensitivity check

**Questo è il passo più importante e quello che viene più saltato.** Chiediti:

- Se cambio il peso del criterio più importante del 20%, la classifica cambia?
- Se il punteggio dell'opzione vincente su un criterio scende di 1, la classifica cambia?
- Quali coppie di criteri hanno pesi "giusti alla soglia"? Queste sono le leve critiche della decisione.

Se la decisione è robusta a piccole variazioni → fidati del risultato. Se è fragile → la vera domanda è "qual è il peso giusto del criterio X?" — lavora su quello, non sulla media pesata.

## Trattamento dei dealbreaker

Alcuni criteri non possono essere compensati da altri: un'opzione che fallisce un criterio critico (es. "non compatibile con il regolatore", "viola policy di sicurezza") va **eliminata a priori**, non solo penalizzata nel punteggio.

Processo a due fasi:
1. **Filtro binario**: elimina opzioni che falliscono i criteri dealbreaker.
2. **Scoring pesato**: applica AHP alle opzioni sopravvissute.

## Quando NON usare AHP

- **Decisioni con un attore strategico** che reagisce → usa teoria dei giochi invece.
- **Decisioni ad alta incertezza probabilistica** → alberi decisionali + EV.
- **Decisioni con solo 2 opzioni molto diverse** → un pro/contro ragionato spesso è più chiaro di una tabella a 5 criteri.
- **Quando i criteri sono indefinibili** → prima chiarisci obiettivo e criteri, poi decidi se usare AHP.

## Errori frequenti

- **Pesi uguali per tutti i criteri**: vuol dire che non stai davvero pensando. I pesi sono l'essenza dell'analisi.
- **Scoring senza giustificazione scritta**: diventa una manipolazione del risultato desiderato.
- **Troppe opzioni o troppi criteri**: 3-5 opzioni × 5-6 criteri è il sweet spot. Oltre, la cognizione umana si perde.
- **Non fare la sensitivity**: un'analisi senza sensitivity non è un'analisi, è un post-razionalizzazione.
