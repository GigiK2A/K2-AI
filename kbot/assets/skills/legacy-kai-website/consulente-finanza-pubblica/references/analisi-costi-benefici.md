# Analisi Costi-Benefici (ACB) per Progetti Pubblici

## Principi Fondamentali

L'**Analisi Costi-Benefici (ACB)** è un metodo sistematico per valutare se un progetto pubblico è **socialmente conveniente** (i benefici sociali totali superano i costi sociali totali).

A differenza di un'analisi finanziaria privata (che conta soltanto flussi di cassa), l'ACB include:
- **Benefici sociali**: effetti di benessere di tutti gli agenti colpiti (non soltanto il Governo)
- **Costi sociali**: inclusi danni ambientali, esternalità, costi opportunità

### Differenza fra Analisi Finanziaria e Sociale

**Analisi finanziaria** (investitore privato):
- Ricavi - Costi operativi = Profitto
- Sconta al tasso di interesse privato (r ≈ 8-10%)
- Criterio: VAN > 0

**ACB Sociale** (settore pubblico):
- (Benefici sociali totali) - (Costi sociali totali) = Valore sociale netto
- Sconta al **saggio di sconto sociale** (r_s ≈ 3-4%, inferiore a privato)
- Criterio: VAN_sociale > 0

## Valutazione Monetaria dei Benefici

### Benefici Diretti e Indiretti

**Benefici diretti**: effetti immediati sull'output/qualità. Esempio: autostrada accorcia tempo viaggio.

**Benefici indiretti**: effetti spillover. Esempio: autostrada attrae nuove imprese nell'area, genera occupazione.

### Metodi di Valutazione

#### 1. **Prezzo di Mercato** (Revealed Preference)

Se esiste un mercato, usare il prezzo osservato.

*Esempio*: beneficio di riduzione tempo viaggio = (ore risparmiate) × (valore orario del tempo).

**Valore orario del tempo**:
- Lavoro: salario lordo (€20-30/ora in Italia)
- Tempo libero: ≈ 30-50% del salario

#### 2. **Prezzi Ombra** (Shadow Prices)

Quando non esiste mercato, stimare il valore implicitamente.

*Esempio*: beneficio di riduzione inquinamento = (tonnellate PM10 ridotte) × (costo/tonnellata dell'inquinamento).

**Stima costo inquinamento**: metodi epidemiologici
- Mortalità prematura per PM10: ≈ 5-10 €/kg di inquinante
- Malattie respiratorie, cardiovascolari: cost-of-illness approach
- Perdita output agricolo da inquinamento

**Risultato**: inquinamento atmosferico costa all'Italia ≈ 60-100 miliardi €/anno.

#### 3. **Metodi Revealed Preference (Hedonic)**

Usare comportamenti osservati per dedurre valore implicito.

*Esempio*: valore di una casa diminuisce se vicino a inquinamento. Differenziale prezzo casa = valore implicito della qualità aria.

#### 4. **Metodi Stated Preference (Survey)**

Domandare direttamente: "Quanto pagheresti per ridurre inquinamento del 20%?" (**WTP, Willingness to Pay**)

*Critica*: risposte ipotetiche, viziata da bias (strategico, informazione).

*Vantaggio*: cattura valore estetico/non-uso (p.es., preservazione biodiversità pur non usandola).

### Willingness to Pay (WTP) e Willingness to Accept (WTA)

**WTP**: quanto un individuo è disposto a pagare per un beneficio (p.es., qualità aria migliore).

**WTA**: quanto richiede di essere compensato per rinunciare a un bene (p.es., accettare inquinamento).

**Fenomeno empirico** (Kahneman-Tversky, perdita di avversione):
- WTA > WTP (spesso di 2-3 volte)
- Individui chiedono compensazione maggiore per perdere bene che per acquisirlo

**Implicazione ACB**: scelta fra WTP e WTA cambia risultati. Normativa UE raccomanda WTP (più conservativo, non sovrastima benefici).

## Sconto Temporale e Valore Attuale

### Valore Attuale Netto (VAN)

$$VAN = \sum_{t=0}^{T} \frac{B_t - C_t}{(1 + r)^t}$$

dove:
- B_t = benefici nell'anno t
- C_t = costi nell'anno t
- r = saggio di sconto
- T = orizzonte temporale (solitamente 30-50 anni per infrastrutture)

**Criterio decisionale**: VAN > 0 → conviene fare il progetto.

### Tasso di Sconto Sociale (TSS)

**Definizione**: tasso con cui la società attualizza i flussi futuri.

**TSS in Italia e UE**: 3-4% (vs privato 8-10%).

**Razionale**:
- Privato sconta al tasso di rendimento alternativo di investimento (alto)
- Pubblico: benefici su lunghe generazioni, equità intergenerazionale, esternalità positive

**Dibattito attuale**: con tassi di interesse BCE bassi (2020-2021), alcuni suggeriscono TSS ancora minore (1-2%), enfatizzando cambio climatico e benefici futuri.

*Sensibilità*: VAN di un progetto cambia molto se r varia. Analisi di sensibilità su r è cruciale.

## Casi di Studio: Infrastrutture Italiane

### Ponte sullo Stretto di Messina (Progetto mai realizzato)

**Caratteristiche**:
- Costo stimato: 10+ miliardi €
- Orizzonte temporale: 50 anni
- Benefici: riduzione tempo viaggio (1 ora → 10 minuti), stimolo sviluppo economico Sud

**ACB Pubblica (2009-2010)**:
- Benefici diretti (riduzione tempo viaggio): ≈ 2-3 mld € (VAN a r=3%)
- Benefici indiretti (crescita economia meridionale): molto incerti, stimate 2-4 mld €
- Costi operativi (manutenzione): ≈ 40 mln €/anno

**Risultato ACB**: marginale, dipendente da assunzioni su crescita meridionale.

**Perché non realizzato**:
- Incertezza ACB
- Rischi geologici (zone sismiche)
- Costi ambientali (ecosistema marino, visuale paesaggistica)
- Costi di opportunità (fondi meglio impiegabili in sanità, istruzione Sud)

### PEDEMONTANA (Autostrada)

**Progetto**: autostrada in Veneto, Nord-Est, 101 km.

**Costo**: ≈ 5 mld € (finanziamento pubblico-privato)

**ACB**:
- Riduzione tempo viaggio: 1 ora/tragitto medio
- Benefici: ≈ 1-1.5 mld € (VAN)
- Costi operativi: ≈ 30 mln €/anno

**Risultato ACB**: positivo ma marginale, molto sensibile al tasso di sconto.

**Criticità**:
- Debito pubblico alto: costi di finanziamento
- Ambientale: attraversa zona di pregio ambientale
- Alternative meno costose: potenziamento ferrovie regionali

## Valutazione di Progetti Sociali

### Istruzione e Capitale Umano

**Progetto**: investimento in formazione disoccupati.

**Benefici**:
- Aumento salari beneficiario: +€5,000/anno per 30 anni = VAN ≈ €100,000 (r=3%)
- Benefici fiscali (aumento tasse pagate): ≈ €1,500/anno × 30 = VAN ≈ €30,000
- Benefici sociali (minore criminalità, migliore salute): ≈ €500/anno × 30 = VAN ≈ €10,000
- Benefici spillover (migliore civicness, crescita innovazione): difficili da quantificare

**Costi**:
- Costo formazione: €10,000 (una tantum)
- Costo opportunità (tempo non lavorato): €2,000
- Costi amministrativi: €1,000

**VAN totale** ≈ €140,000 - €13,000 = €127,000 → **Molto conveniente**.

**Rapporto benefici/costi** = €140,000 / €13,000 ≈ 11 → per ogni euro speso, ritorno di 11 €.

### Sanità: Screening Cancro

**Progetto**: programma di screening mammografico per popolazione femminile 50-75 anni.

**Benefici**:
- Vite salvate: p.es., 100 vite/anno
- Valore di una vita statistica (VSL): stimato 1-3 mln € in Europa
- VAN benefici: 100 × €2 mln = €200 mln/anno

**Costi**:
- Test mammografico: €50 per donna, ≈ 2 mln donne → €100 mln/anno
- Falsi positivi (ansia, follow-up): €20 mln/anno
- Totale costi: €120 mln/anno

**Risultato ACB**: positivo (VAN ≈ €80 mln/anno), conveniente.

**Controverse**: VSL è contestato (non dovremmo mettere prezzo su vite umane), ma necessario per policy.

## Limitazioni e Critiche dell'ACB

### 1. Incommensurabilità

Alcuni benefici (p.es., biodiversità, diritti umani) possono non essere monetizzabili senza perdere significato.

### 2. Distribuzione e Equità

ACB non considera distribuzione (favorisce progetti benefici in media, anche se ineguali). Progetto che beneficia ricchi a danno poveri può avere VAN positivo.

**Soluzione**: pesare benefici/costi per gruppi vulnerabili (weighted ACB).

### 3. Incertezza

Progetti lunghi (30+ anni) hanno incertezza intrinseca. Analisi sensibilità necessaria.

### 4. Esternalità Non Osservate

Difficile catturare tutti gli effetti indiretti (spiking economico, effetti redistributivi a cascata).

### 5. Valore Etico

Chi decide cosa è "bene per la società"? ACB assume utilità totale maximizing, ma altre concezioni (diritti, giustizia procedurale) divergono.

## Best Practice Italiana

### Linee Guida Ministeriali (2017)

Governo italiano raccomanda:
- TSS = 3,5% baseline, sensibilità [2%, 5%]
- Inclusione effetti ambientali e sociali
- Coinvolgimento stakeholder in fase di disegno progetto
- Consultazione pubblica esplicita

### PNRR e ACB

Progetti PNRR richiedono formale ACB secondo standard UE:
- VAN > 0
- Rapporto benefici/costi > 1
- IRR (tasso interno di rendimento) > TSS

Sono stati finora positivi (media rapporto > 1,5), giustificando investimento.
