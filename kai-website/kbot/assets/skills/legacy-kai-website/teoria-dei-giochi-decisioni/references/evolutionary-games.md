# Teoria evolutiva dei giochi

Usa questo file quando il problema **non è un'interazione tra giocatori razionali** che calcolano equilibri, ma una **dinamica di popolazione** in cui strategie sopravvivono, si diffondono o si estinguono nel tempo in base al successo. Introdotta da Maynard Smith per la biologia, è uno strumento potente per dinamiche di mercato di lungo periodo.

## Il cambio di paradigma

Nella teoria classica, i giocatori sono razionali e scelgono strategie. Nella teoria evolutiva:

- Ci sono **popolazioni** di attori che "portano" strategie (imprese, prodotti, pratiche, norme culturali).
- Le strategie si riproducono in proporzione al loro successo (fitness).
- Nel lungo periodo, solo le strategie **evolutivamente stabili** sopravvivono.

Questo è spesso più realistico del paradigma razionalistico quando: gli attori hanno conoscenza limitata, imitano invece che calcolare, l'orizzonte temporale è lungo, l'ingresso e l'uscita dal "gioco" sono continui.

## ESS — Evolutionarily Stable Strategy

Una strategia S è **evolutivamente stabile** se, quando adottata dalla quasi totalità della popolazione, resiste all'invasione di una piccola frazione di mutanti che usa una strategia diversa S'. In formula: S fa meglio contro S di quanto S' faccia contro S, oppure — se pareggiano — S fa meglio contro S' di quanto S' faccia contro S'.

**Proprietà chiave**: ogni ESS è un equilibrio di Nash, ma non ogni equilibrio di Nash è ESS. L'ESS è un raffinamento che scarta gli equilibri "fragili", vulnerabili a piccole deviazioni casuali.

**Esempio biologico canonico**: hawk-dove. In una popolazione di "colombe" (che cedono sempre), un mutante "falco" (che attacca sempre) si diffonde facilmente. In una popolazione di soli falchi, i costi di combattimento erodono la fitness e una mutazione "colomba" può prosperare. L'ESS è una proporzione mista di falchi e colombe determinata dai payoff.

## Replicator dynamics

Il modo matematico di formalizzare come le strategie si diffondono:

```
Δ(share di strategia i) ∝ share × (fitness_i − fitness_media)
```

Strategie con fitness sopra la media crescono; sotto la media decrescono. Nel lungo periodo si converge su un ESS (se esiste) o su un attrattore più complesso (ciclo, caos).

In business questo corrisponde a: quote di mercato che crescono se il prodotto "fa meglio" della media, e decrescono altrimenti. Non serve nessun decisore razionale che calcola — basta che il meccanismo di selezione (clienti che comprano, dipendenti che scelgono dove lavorare, investitori che allocano) funzioni.

## Applicazioni in business

**1. Diffusione di innovazione e standard.** Quali tecnologie "vincono" nel lungo periodo non è solo questione di qualità ma di fitness evolutiva — effetti rete, learning curves, costi di switching. Strategie "leggere ma virali" spesso battono strategie "superiori ma costose da adottare".

**2. Cultura aziendale ed ecologia delle pratiche.** Le pratiche manageriali che sopravvivono in un'azienda sono quelle che "si riproducono" (vengono insegnate ai nuovi, imitate dagli altri, premiate dal sistema). Cambiare cultura richiede modificare la fitness di pratiche nuove, non solo deciderle.

**3. Dinamiche di mercato di lungo periodo.** Quali modelli di business sopravvivono in un settore non è predetto dalla razionalità istantanea ma dalla pressione selettiva. Un'azienda "razionalmente ottima" oggi può essere spazzata via da una dinamica evolutiva su 10 anni.

**4. Contagio di comportamenti competitivi.** Se un competitor adotta tattiche aggressive e ha successo, altri le imitano. La tattica si diffonde come fitness-maximizing anche se nessuno l'ha "scelta" razionalmente. Vedi anche `behavioral.md` per il meccanismo imitativo.

**5. Norme settoriali e compliance.** Le norme "di fatto" in un settore (dilazione di pagamento, standard di servizio, livelli di trasparenza) sono equilibri evolutivi. Cambiarle come singolo attore è difficile: devi creare condizioni di fitness per la nuova norma.

## Implicazioni operative

- **Orizzonte temporale lungo**: se stai pensando a 3+ anni, il ragionamento evolutivo è spesso più predittivo di quello razionalistico.
- **Non serve che qualcuno "decida"**: le dinamiche emergono dal meccanismo di selezione. Chiediti: "cosa premia il mio ambiente?" → quella pratica si diffonderà.
- **Piccoli vantaggi composti**: l'evoluzione amplifica piccole differenze di fitness nel tempo. Un +2% di efficienza rispetto al competitor può portare a dominio in 5-10 anni se la selezione è abbastanza intensa.
- **Strategie robuste > strategie ottime**: in contesti evolutivi, una strategia "buona contro tanti avversari diversi" batte una "ottima contro un avversario specifico". Tit-for-tat di Axelrod è l'esempio paradigmatico.

## Limite

La teoria evolutiva è potente per **trend di lungo periodo** ma non per **mosse tattiche**. Per la negoziazione di domani non ti serve pensare in termini di fitness — ti serve `game-theory-core.md`. Per decidere se il tuo modello di business è sostenibile tra 5 anni, pensare in termini di fitness evolutiva è quasi sempre meglio che fare forecasting deterministico.
