# Giochi ripetuti e reputazione

Quando interagirai **più volte** con gli stessi attori, la logica cambia radicalmente rispetto al gioco one-shot. Molte decisioni di business che sembrano one-shot sono in realtà ripetute (clienti ricorrenti, dipendenti, fornitori, concorrenti nello stesso settore).

## Il folk theorem (idea centrale)

Nei giochi ripetuti con orizzonte infinito (o incerto), **qualsiasi payoff individualmente razionale può essere sostenuto come equilibrio**, purché i giocatori diano sufficiente peso al futuro (discount factor alto). In pratica: la cooperazione, che sarebbe irrazionale one-shot, diventa sostenibile perché tradirla distruggerebbe la relazione futura.

**Implicazione manageriale**: nelle relazioni di lungo periodo, non giocare la mossa one-shot ottima — giocare una strategia che sostenga la cooperazione.

## Tit-for-tat (TFT)

La strategia più famosa nei giochi ripetuti (vinse il torneo di Axelrod sul dilemma del prigioniero iterato):

1. Alla prima mossa, **coopera**.
2. Dopo, **copia la mossa che l'avversario ha fatto al turno precedente**.

Proprietà:
- **Nice**: non defeziona per prima.
- **Retaliatory**: punisce immediatamente la defezione.
- **Forgiving**: dopo una punizione, torna a cooperare.
- **Clear**: l'avversario capisce subito la logica e impara a cooperare.

Varianti utili:
- **Generous tit-for-tat**: ogni tanto perdona una defezione, utile in presenza di "rumore" (errori di comunicazione).
- **Tit-for-two-tats**: punisci solo dopo due defezioni consecutive, più robusto al rumore.
- **Grim trigger**: coopera finché l'avversario coopera, alla prima defezione abbandona la cooperazione per sempre. Molto aggressivo, credibile solo se hai commitment per eseguirlo.

## Reputazione

In giochi ripetuti con **informazione imperfetta** (gli altri non sanno con certezza il tuo tipo), la reputazione diventa un asset strategico. Se puoi farti credere "il tipo di attore che punisce sempre chi sgarra", anche un piccolo sacrificio iniziale per stabilire quella reputazione ti ripaga nel lungo periodo.

Esempi di business:
- **Mai rinegoziare con chi non paga**. Perdi nel caso specifico, ma mantieni l'immagine di azienda rigida con i ritardatari futuri.
- **Rispondere aggressivamente al primo competitor che entra** nel tuo mercato. Scoraggia entry futuri.
- **Onorare sempre i piccoli impegni**. Chi ti vede onorare impegni senza consequenze apparenti capisce che onorerai anche i grandi.

## Discount factor (δ)

Quanto pesi il futuro rispetto al presente. In pratica: se δ è alto (orizzonte lungo, alta probabilità di interagire di nuovo, bassi tassi di interesse), la cooperazione è più sostenibile. Se δ è basso (sei vicino a uscire dal business, il cliente sta morendo, la relazione sta per chiudersi), il gioco diventa effettivamente one-shot e la tentazione di defezionare aumenta.

**End-game problem**: se entrambi sanno che questo è l'ultimo incontro, la backward induction fa collassare la cooperazione. Per questo le fusioni e le chiusure di rapporti sono momenti ad alto rischio di opportunismo.

## Trigger strategies

Tipo di strategia in cui:
- Coopera finché nessuno defeziona.
- Al primo segnale di defezione, attiva una "punizione" per N periodi (o per sempre).
- Poi eventualmente torna a cooperare.

La chiave è la **credibilità della punizione**: deve essere abbastanza dura da scoraggiare la defezione, ma non così autodistruttiva da essere poco credibile da eseguire.

## Applicazioni tipiche

- **Pricing in settore concentrato**: mantenere prezzi alti è possibile senza collusione esplicita tramite tit-for-tat ("se abbassi tu, abbasso anche io").
- **Partnership e fornitori strategici**: la relazione di lungo periodo sostiene qualità e affidabilità che un contratto rigido non potrebbe specificare.
- **Clienti ricorrenti**: un piccolo sconto/recovery dopo un errore costa poco ma protegge un flusso di ricavi futuri.
- **Team interno**: favoritismi e punizioni selettive distruggono la cooperazione; equità e prevedibilità la sostengono.

## Pericoli

- **Escalation involontaria**: se tu e un competitor vi ritrovate in tit-for-tat di ritorsione, il pattern può scendere in una spirale distruttiva. Qualcuno deve "offrire un ramo d'olivo" per uscirne — spesso chi ha più da perdere.
- **Illusione del gioco infinito**: se ti comporti come se la relazione durasse per sempre ma l'altro sa che sta uscendo dal mercato, ti frega.
- **Reputazione stantìa**: la reputazione "duro con chi sgarra" protegge ma può impedirti opportunità legittime di rinegoziare. Vale la pena mantenerla solo se i benefici di lungo periodo superano.
