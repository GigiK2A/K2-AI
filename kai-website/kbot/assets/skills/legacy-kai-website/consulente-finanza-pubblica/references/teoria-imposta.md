# Teoria dell'Imposta

## Classificazione delle Imposte

### Imposte Dirette e Indirette

**Imposte dirette** colpiscono direttamente la capacità contributiva del soggetto (reddito, patrimonio, consumi):
- IRPEF (persone fisiche): basata sul principio della capacità economica
- IRES (imprese): aliquota proporzionale, non progressiva
- Imposta di successione

**Imposte indirette** colpiscono transazioni e consumi:
- IVA: imposta sui consumi, neutrale in teoria, applicata a ogni stadio della filiera
- Accise: imposte specifiche su beni (carburanti, alcol, tabacco)
- Dazi doganali

La scelta fra imposte dirette e indirette riflette trade-off fra:
- **Progressività**: le dirette possono essere progressive (aliquote crescenti), le indirette sono regressive (colpiscono meno ricchi in proporzione)
- **Efficienze comportamentali**: dirette più distorsive (disincentivano lavoro e risparmio), indirette meno visibili
- **Gettito**: le indirette hanno gettito più stabile, le dirette più elastiche al ciclo economico

## Progressività, Proporzionalità, Regressività

Un'imposta è:
- **Progressiva** se l'aliquota media aumenta al crescere della base imponibile: τ = t(Y), dτ/dY > 0
- **Proporzionale** se aliquota costante: τ = t (costante)
- **Regressiva** se aliquota media diminuisce al crescere della base: dτ/dY < 0

*Esempio IRPEF italiana*:
- Scaglioni progressivi: 23%, 27%, 38%, 41%, 43%
- Funzione redistributiva attraverso progressività
- Effetto: riduce disuguaglianza rispetto a imposte indirette

L'**indice di Gini** misura la diseguaglianza; imposte progressive riducono il Gini post-imposte rispetto a pre-imposte.

## Incidenza dell'Imposta

L'**incidenza economica** (chi effettivamente paga) spesso diverge dall'**incidenza legale** (chi la normativa designa pagatore).

### Caso: Imposta sugli Ombrelli

Se lo Stato tassa l'ombrello con accisa €10:
- Legalmente: pagano i venditori
- Economicamente: il carico si ripartisce tra consumatori e venditori a seconda dell'elasticità
  - Se domanda elastica: consumatori assorbono poco, venditori perdono margini
  - Se domanda rigida: consumatori assorbono tutto il carico

Formula semplificata per mercati concorrenziali:
$$\text{quota carico su consumatori} = \frac{E_O}{E_O - E_D}$$

dove E_O = elasticità offerta, E_D = elasticità domanda (in valore assoluto).

## Effetti Comportamentali e Curva di Laffer

### Curva di Laffer

Mostra la relazione fra **aliquota fiscale** (asse x) e **gettito totale** (asse y). Forma di campana:
- Aliquota 0%: gettito zero
- Aliquota intermedia t*: gettito massimo
- Aliquota 100%: gettito zero (nessuno lavora)

**Implicazione**: aumentare l'aliquota oltre t* può ridurre il gettito se gli effetti comportamentali (minore offerta di lavoro, evasione) superano l'effetto meccanico.

**In pratica**, per la maggior parte delle imposte, il picco della curva di Laffer si situa a livelli molto elevati (70%+); per IRPEF italiana (aliquota max 43%), siamo probabilmente sul ramo crescente, quindi aumentare l'aliquota aumenta il gettito netto.

## Effetti Distorsivi delle Imposte

Imposte creano **perdite di benessere economico** oltre al gettito:

1. **Eccesso di pressione (deadweight loss)**: imposte inducono agenti a cambiare comportamento; il beneficio dello Stato (gettito) è inferiore al danno per i contribuenti
   - Formula approssimata: DWL ≈ 0.5 × t × ΔQ, dove ΔQ è la riduzione quantità
   - Dipende dall'elasticità: beni con domanda elastica subiscono DWL maggiore

2. **Distorsioni del mercato del lavoro**: imposte sul reddito riducono incentivi a lavorare
   - Trade-off fra efficienza (scegliere imposte con bassa elasticità) e equità (progressività)

3. **Distorsioni risparmio-consumo**: se imposte disuguali fra redditi del lavoro e rendite, si distorce scelta intertemporale

## Imposte Ottimali

### Principio di Ramsey (1927)

In assenza di progressività redistributiva, la struttura fiscale ottimale minimizza l'eccesso di pressione totale. Regola: **tassare i beni con elasticità di domanda minore** (meno sensibili a variazioni di prezzo).

Formalizzazione: per un'imposta sul bene i, l'aliquota ottimale è:
$$t_i \propto \frac{1}{E_i}$$

*Esempio*: pane (elasticità ≈ 0,2) dovrebbe essere tassato più di carne (elasticità ≈ 0,6).

Questo contrasta con equità (il pane è necessità per i poveri), da cui nasce il **trade-off equity-efficiency**.

### Imposta Ottima con Redistribuzione

Se l'obiettivo include equità, occorre bilanciare:
- **Efficienza**: imposte su beni inelastici, sui redditi con bassa elasticità
- **Equità**: progressività, tassazione margini di profitto, prelievi su rendite

L'imposta negativa sul reddito (NIT) o reddito universale incondizionato (UBI) rappresentano soluzioni alternative a imposte progressive tradizionali, minimizzando distorsioni comportamentali (agenti non hanno disincentivo al lavoro margginale, solo al lavoro totale).

## Progressività e Incentivi

### Problema del Moral Hazard Comportamentale

Imposte marginali molto elevate creano disincentivi; individui con IRPEF marginale 43% hanno incentivo a:
- Ridurre ore lavoro
- Investire in evasione (costi amministrativi/legali)
- Emigrare

### Evidenza Empirica Italiana

- Italia: pressione fiscale ≈ 42% del PIL (2023), fra le più alte UE
- Evasione fiscale: 15-20% del gettito stimato non pagato (black economy)
- High earners: elasticità offerta lavoro 0,5-1,5 (diminuzione reddito lordo dell'1%, riduzione ore 0,5%-1,5%)

Questo suggerisce che ulteriori aumenti IRPEF marginalale avrebbero DWL crescente.

## Riferimenti Italiani

### Reforma IRPEF (2021-2022)
- Riduzione numero scaglioni da 5 a 4 (poi 3 da proposta)
- Aumento detrazione base per bassissimi redditi
- Obiettivo: aumentare progressività per famiglie medie, ridurre pressure su poveri

### Convergenza UE
- Italia 42% pressione fiscale vs media UE 41%
- Composizione diversa: Italia più su lavoro (47%), meno su consumi (26% vs 30% UE)
- Sostenibilità: pressione alta, bassa elasticità aumento gettito
