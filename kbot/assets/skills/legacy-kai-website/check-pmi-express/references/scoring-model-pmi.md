# Scoring model — Check PMI Express

Sistema di scoring a 6 dimensioni per PMI italiane 5-50 dipendenti. Ogni dimensione produce un semaforo verde/giallo/rosso con soglie settoriali. Lo score globale e la somma pesata normalizzata a 0-100.

## Fasce dimensionali

| Fascia | Fatturato | Dipendenti |
|---|---|---|
| Micro | < 500k EUR | 1-4 |
| Piccola bassa | 500k - 2M EUR | 5-9 |
| Piccola alta | 2M - 10M EUR | 10-24 |
| Media | 10M - 50M EUR | 25-50 |

Check-PMI-express si concentra sulle 3 fasce superiori (5-50 dipendenti). Se il titolare indica < 5 dipendenti, segnalare "dimensione minima per AdvisorBoost — valutare percorso alternativo".

## 6 dimensioni e peso

| # | Dimensione | Peso | KPI principali |
|---|---|---|---|
| 1 | Redditualita | 25% | EBITDA margin, margine netto |
| 2 | Solidita | 20% | PFN/EBITDA, indice indebitamento |
| 3 | Liquidita | 15% | Current ratio proxy, DSO |
| 4 | Crescita | 15% | CAGR fatturato 1-3 anni vs trend settore |
| 5 | Posizionamento | 15% | Ricavi per dipendente, eta azienda, densita competitor |
| 6 | Dipendenza clienti | 10% | Concentrazione primo cliente |

Se dipendenza cliente non fornita: pesare 10% come "neutro" (1.5 punti automatici).

## Soglie semaforiche per dimensione

### Dimensione 1 — Redditualita

EBITDA margin rispetto alla mediana di settore (vedi `benchmark-pmi-integrato.md` per valori mediani per settore).

Logica:
- **Verde**: EBITDA margin >= mediana settore
- **Giallo**: 50% <= EBITDA margin < mediana
- **Rosso**: < 50% mediana oppure negativo

In alternativa, proxy via margine netto:
- Manifattura: verde > 5%, giallo 2-5%, rosso < 2%
- Servizi B2B: verde > 10%, giallo 4-10%, rosso < 4%
- Commercio: verde > 3%, giallo 1-3%, rosso < 1%
- Costruzioni: verde > 4%, giallo 1.5-4%, rosso < 1.5%
- TLC/IT: verde > 10%, giallo 4-10%, rosso < 4%
- Ricettivo: verde > 8%, giallo 3-8%, rosso < 3%

### Dimensione 2 — Solidita

Indicatore chiave: PFN/EBITDA.

| PFN/EBITDA | Semaforo |
|---|---|
| < 2x | Verde |
| 2x - 4x | Giallo |
| > 4x | Rosso |

Alert aggiuntivo: se PFN > 0 e PN < 10% totale attivo → forzare rosso (sotto-capitalizzata).

Se PFN negativa (cassa > debiti): forzare verde.

Se utile netto e negativo: forzare rosso a prescindere dal PFN.

### Dimensione 3 — Liquidita

Proxy rapido via crediti commerciali / fatturato (giorni medi incasso approssimati). Se non fornito:
- Stima da settore (manifattura B2B 75-90 gg, servizi 40-60 gg, commercio 50-70 gg, retail cash 5-15 gg).

| DSO stimato | Semaforo |
|---|---|
| < mediana settore | Verde |
| mediana - 1.3× mediana | Giallo |
| > 1.3× mediana | Rosso |

Alert aggiuntivo: se il titolare indica "paghiamo fornitori in ritardo" o "banche non ci danno piu credito" → forzare giallo minimo.

### Dimensione 4 — Crescita

Calcolo CAGR semplice:
- Se fornito fatturato anno precedente: `(fatturato_N / fatturato_N-1) - 1`
- Se non fornito: stima "stabile" (0%) con flag

Benchmark CAGR vs settore (vedi `benchmark-pmi-integrato.md`):
- **Verde**: CAGR >= media settore (tipicamente 3-5%)
- **Giallo**: 0% <= CAGR < media settore
- **Rosso**: CAGR < 0% in settore in crescita, oppure CAGR < -5% in qualsiasi settore

Correzione per settori ciclici o post-PNRR:
- Costruzioni 2025-2026: soglia rosso innalzata a -10% (settore in rallentamento post-Superbonus).
- TLC infrastrutture: soglia rosso a -3% (settore stabile).
- Software B2B: soglia verde innalzata a > 10% (crescita settore alta).

### Dimensione 5 — Posizionamento

Combinazione di 3 sub-indicatori:
- **Ricavi per dipendente** vs mediana settore (peso 50% della dimensione)
- **Eta azienda** (longevita come proxy di brand/relazioni consolidate, peso 25%)
- **Densita competitor dichiarati** (peso 25%)

Sub 1 — Ricavi per dipendente:
- Verde: >= 90% mediana settore
- Giallo: 70-90% mediana
- Rosso: < 70% mediana

Sub 2 — Eta azienda:
- Verde: > 15 anni
- Giallo: 5-15 anni
- Rosso: < 5 anni (piu fragile)

Sub 3 — Densita competitor:
- Verde: il titolare cita 0-2 competitor (nicchia difendibile)
- Giallo: 3-5 competitor (settore affollato ma gestibile)
- Rosso: > 5 competitor o "mercato commodity"

Semaforo finale dimensione 5: somma sub con pesi, soglia verde >= 2.4, giallo 1.2-2.4, rosso < 1.2 (su scala 0-3).

### Dimensione 6 — Dipendenza clienti

| Concentrazione primo cliente | Semaforo |
|---|---|
| < 25% | Verde |
| 25% - 40% | Giallo |
| > 40% | Rosso |

Alert aggiuntivo: se primi 3 clienti > 70% del fatturato (se dichiarato) → forzare rosso a prescindere dal primo cliente isolato.

Se dato non fornito: semaforo neutro (1.5 punti su 3), non rosso (il titolare potrebbe non sapere).

## Calcolo score globale

Formula:
```
score_grezzo = (
  verde_1 * 3 + giallo_1 * 1.5 + rosso_1 * 0) * 0.25 +
  (verde_2 * 3 + giallo_2 * 1.5 + rosso_2 * 0) * 0.20 +
  (verde_3 * 3 + giallo_3 * 1.5 + rosso_3 * 0) * 0.15 +
  (verde_4 * 3 + giallo_4 * 1.5 + rosso_4 * 0) * 0.15 +
  (verde_5 * 3 + giallo_5 * 1.5 + rosso_5 * 0) * 0.15 +
  (verde_6 * 3 + giallo_6 * 1.5 + rosso_6 * 0) * 0.10

score_finale = score_grezzo * 33.33  (normalizza 0-100)
```

Ogni dimensione produce un semaforo binario (verde=3, giallo=1.5, rosso=0), non un valore continuo.

## Fasce di giudizio

| Score | Giudizio | Messaggio UX |
|---|---|---|
| 85-100 | Eccellente | "Ottima salute strategico-finanziaria. Focus su consolidamento e crescita opportunistica." |
| 65-84 | Buono | "Azienda solida con 2-3 aree di miglioramento. AdvisorBoost per ottimizzare." |
| 45-64 | Sufficiente | "Molte aree di attenzione. AdvisorBoost consigliato per piano di crescita." |
| 25-44 | Preoccupante | "Segnali d'allarme multipli. AdvisorBoost con tono turnaround consigliato." |
| 0-24 | Critico | "Rischio continuita aziendale. Consultare commercialista subito + AdvisorBoost con focus CCII." |

## Alert CCII da segnalare a parte

Se lo score e < 45 e almeno uno di questi emerge dai dati dichiarati:
- PN negativo dichiarato
- Utile netto < 0 per 2 anni consecutivi
- Ritardi di pagamento fornitori/banche dichiarati
- PFN/EBITDA > 6

Inserire nella pagella un **box rosso esplicito**:
> "Alert potenziale soglia CCII. Valutare composizione negoziata o turnaround con consulente specializzato entro 60 giorni."

## Ragionamento top 3 criticita

Le 3 dimensioni con punteggio piu basso (semaforo rosso prima, giallo poi) generano le criticita. Per ciascuna:

Template:
- Titolo secco (es: "Margini sotto la mediana di settore")
- Sintesi di 2-3 righe in italiano semplice, senza gergo
- Impatto sulla continuita/crescita
- Azione entro 30 giorni concreta

Esempi di azioni 30 giorni per dimensione:

**Redditualita rossa**:
- "Analizza il margine per linea di prodotto: probabilmente il 20% del fatturato sta drenando il 50% della redditualita."
- "Rivedi il listino prezzi sulla categoria B: test aumento 5% su clienti low-churn."

**Solidita rossa**:
- "Richiedi al commercialista un piano di rientro bancario a 18-36 mesi."
- "Valuta consolidamento debiti a breve con finanziamento garantito Mediocredito Centrale."

**Liquidita rossa**:
- "Implementa solleciti a 15-30 giorni post-fattura, non 60-90."
- "Valuta factoring pro-soluto sui 5 clienti piu lenti."

**Crescita rossa**:
- "Mappa i 3 canali commerciali con ROI piu alto degli ultimi 12 mesi — duplica investimento la."
- "Se il settore cresce e tu no: e un problema di posizionamento, non di mercato."

**Posizionamento rosso**:
- "Definisci la nicchia: chi e il tuo cliente ideale? Se rispondi 'tutti' hai un problema."
- "Aumenta ricavi per dipendente via automazione o specializzazione."

**Dipendenza clienti rossa**:
- "Mappa i primi 10 clienti e stima cosa succede se perdi il cliente 1."
- "Prioritizza 3 nuovi clienti potenziali nel pipeline entro 90 giorni."

## Messaggio CTA post-pagella

Sempre presente a fondo pagella:

> "Questa pagella e un colpo d'occhio. Per capire DOVE ANDARE nei prossimi 36 mesi serve AdvisorBoost: la diagnosi completa strategico-finanziaria che il tuo commercialista non ti fa. Da 1.999 EUR, 30-40 pagine di report, cruscotto XLSX e piano azioni mese per mese. Prenota una call gratuita per valutare se fa al caso tuo."

## Limitazioni metodologiche

Il check PMI express e un proxy rapido. Limiti noti:
1. Usa solo dati dichiarati, non verificati (bilancio non letto).
2. EBITDA stimato da utile netto con coefficiente fisso (imprecisione ± 30%).
3. Settori con stagionalita forte possono essere penalizzati (es: ricettivo estivo).
4. Non considera contesto competitivo specifico ne barriere strutturali.
5. Non sostituisce analisi di bilancio (`analisi-bilancio-pmi`) ne diagnosi strategica (`flusso-advisorboost-pmi`).

Queste limitazioni devono essere dichiarate nel disclaimer e devono motivare la CTA verso AdvisorBoost.
