# Banco di prova della chat K-BOT

Fase 0 dello studio `docs/studio-struttura-chat-kbot-2026-10.md`: misurare prima di cambiare.
Lancia domande reali contro un K-BOT in esecuzione, controlla le risposte e scrive un rapporto
confrontabile fra modelli e fra versioni.

## Uso

```bash
cd kai-website/kbot/backend
python3 evals/run_eval.py --base-url https://www.k2-ai.it/api/kbot \
    --modello "nome del modello provato" --etichetta base-AAAA-MM-GG
```

Opzioni utili: `--solo id1,id2` · `--veloci` (salta i casi multi-turno) · `--ripetizioni N` ·
`--budget-latenza 90` · `--budget-primo-token 20` · `--strict` (exit 1 se un caso con attese fallisce)
· `--rivaluta FILE` (ricalcola gli esiti da un file salvato, senza richiamare il modello) ·
`--confronta A.json B.json` (vedi sotto).

**Il modello non è deterministico: usa almeno `--ripetizioni 3`.** Con una sola esecuzione per caso
una differenza di uno o due controlli fra due file non dice niente: il 15/10/2026 lo stesso caso
sul limite del contante è andato bene in un'esecuzione e male in quella dopo, e su 3 ripetizioni
il fatto atteso (5.000 €) c'era 2 volte su 3.

Solo libreria standard, nessuna dipendenza. Il base URL è **obbligatorio**: ogni caso crea
sessioni anonime e consuma il modello vero, quindi non si parte mai contro la produzione per
default. Risultati in `evals/risultati/<etichetta>.json` (`meta`, `riepilogo`, risposte intere,
testo streamato e finale di ogni turno).

## Cosa controlla

**Generici** (ogni risposta):
`risposta_non_vuota` · `nessuna_lingua_estranea` (ideogrammi) · `frasi_integre` (artefatti delle
guardie, «di nel termine previsto…») · `nessuna_autocorrezione` («Aspetta: …») ·
`nessun_testo_del_critico` (il commento interno del critico di qualità non deve arrivare al
cliente) · `nessuna_fuga_prompt` · `testo_letto_uguale_finale` (quello letto in streaming = quello
che resta; le differenze solo di forma, come apostrofi e grassetto, non contano) ·
`nessun_errore_di_stream`.

**Specifici** (dal caso, `attese`): `tutti` (fatti che devono esserci), `una_di` (almeno
un'alternativa), `nessuno` (affermazioni note come sbagliate), `escalation`
(`nessuna|consigliata|urgente`: rinvio al professionista, e per `urgente` anche un'indicazione
di tempo), `non_spinge_vendita`.

**Prestazioni** (separate, dipendono dal modello e dalla macchina): latenza e primo token.

## Due insiemi di casi: sviluppo e held-out

- `casi.json` (17): i casi su cui si SVILUPPA. Servono a vedere cosa si rompe, quindi inevitabilmente
  si tarano le modifiche anche su di essi.
- `casi_held_out.json` (8): argomenti DIVERSI (caparra, penale, impugnazione delle decisioni della srl,
  appalto, orario massimo, ferie, giusta causa, patto di non concorrenza), con fonte aperta sul corpus.
  **Non vanno usati per costruire mappe, regole o prompt.** Misurano se un meccanismo generalizza o se ha
  solo imparato i casi di sviluppo: si lanciano con `--casi evals/casi_held_out.json`.

Un miglioramento che compare solo sui casi di sviluppo non è un miglioramento verificato.

## Misurare una modifica senza pubblicarla: backend locale

`evals/server_locale.py` avvia il backend in locale con Supabase finto (in memoria), l'LLM vero dello shim
e il corpus vero. Due istanze dello STESSO codice con un flag diverso, lanciate insieme, danno un confronto
alla pari (stesso modello servito nello stesso momento):

```bash
python3 evals/server_locale.py --porta 8123 --evidenza 0 &
python3 evals/server_locale.py --porta 8124 --evidenza 1 &
python3 evals/run_eval.py --base-url http://127.0.0.1:8123/api/kbot --ripetizioni 3 --etichetta locale-senza
python3 evals/run_eval.py --base-url http://127.0.0.1:8124/api/kbot --ripetizioni 3 --etichetta locale-con
python3 evals/run_eval.py --confronta evals/risultati/locale-senza.json evals/risultati/locale-con.json
```

Non è uguale alla produzione: niente ricerca web, PostHog o Stripe. Il confronto fra le due istanze è alla
pari; quello con i risultati della produzione no.

## I casi (`casi.json`)

17 casi. Ogni caso ha `fonti`: cosa è stato **aperto** e come (corpus Normattiva con
`find_by_estremi`, scadenzario dell'Agenzia delle Entrate, Garante privacy, calcolo). Stati:
`fonte-verificata` · `fonte-secondaria` (web non ufficiale, da confermare) · `calcolo` ·
`capacita` (memoria, lunghezza, prompt) · `solo-rinvio`.

> **Nessun caso è validato da un professionista** (`validato_da: null`). Le attese vengono
> da fonti aperte, non da un parere. Prima di usare le percentuali come obiettivo di
> prodotto, un avvocato/commercialista deve confermarle.

Trappole note nei dati, già annotate nei casi:
- `fis-contanti`: il comma 1 dell'art. 49 D.Lgs. 231/2007 riporta ancora **3.000 €**; vale il
  comma 3-bis (**5.000 €** dal 1° gennaio 2023). Un modello che legge solo il comma 1 sbaglia.
- `lav-telecamere`: il testo nel corpus indica la «Direzione territoriale del lavoro» (versione
  originale); l'ente oggi competente non è verificato, quindi non è richiesto.

## Come aggiungere un caso

1. Apri la fonte (articolo, scadenzario, calcolo) e copia in `fonti` l'estratto e la data.
2. Scrivi le `attese` con regex tolleranti alla forma ma non al contenuto.
3. Aggiungi in `tests/test_evals_checks.py` una risposta **giusta** e una **sbagliata** (meglio
   se vista davvero): il test deve bocciare la seconda e promuovere la prima. Un caso che non
   boccia l'errore che dovrebbe cogliere è inutile.

Il file `casi.json` oggi è generato a mano; per crescere verso 60-100 casi conviene tenerlo
come unica fonte.

## Confrontare modelli o versioni

Stesso comando con `--modello`, `--etichetta` e `--ripetizioni 3` (o più) diversi, poi:

```bash
python3 evals/run_eval.py --confronta evals/risultati/A.json evals/risultati/B.json
```

Per ogni metrica mostra media e deviazione standard fra le ripetizioni di ciascun file, la
differenza, e dice se **supera la variazione osservata** (soglia: 2 deviazioni standard) o è
**non distinguibile dal rumore**. Se nessuna delle due parti ha ripetizioni rifiuta di dare un
verdetto («variazione non misurabile»); se ce l'ha solo una (tipico: una base a esecuzione singola
contro una nuova esecuzione ripetuta) usa la sua deviazione anche per l'altra e lo dichiara come
**ipotesi**, non come misura. Elenca anche i **controlli instabili**: quelli che sullo stesso
caso passano in alcune ripetizioni e falliscono in altre. Le attese specifiche sono lo stesso
metro per tutti: serve a rispondere a «quale modello regge il ruolo?» con dati e non a impressione.

Con poche ripetizioni la soglia è indicativa, non un test statistico.

## Pulizia

Ogni esecuzione crea sessioni **anonime** nel database del servizio provato. Gli id sono in
`meta.sessioni_create` del file dei risultati: la cancellazione si fa per id, mai per intervallo
di date.

## Limiti noti

- I controlli sono su regex: promuovono una risposta che contiene i fatti attesi, non ne
  giudicano la qualità né la completezza.
- `testo_letto_uguale_finale` misura la divergenza dello streaming; non dice quale dei due
  testi sia quello giusto.
- `rinvio_al_professionista` riconosce la parola, non la sua pertinenza.
- Un solo turno per caso (tranne i multi-turno): non valuta la conduzione di un'intera
  consulenza.
- Quando si correggono i controlli o le attese, vanno rivalutati TUTTI i file da confrontare
  con `--rivaluta`, altrimenti il confronto non è alla pari.
