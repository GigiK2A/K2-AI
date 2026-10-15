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

Opzioni utili: `--solo id1,id2` · `--veloci` (salta i casi multi-turno) · `--budget-latenza 90`
· `--budget-primo-token 20` · `--strict` (exit 1 se un caso con attese fallisce).

Solo libreria standard, nessuna dipendenza. Il base URL è **obbligatorio**: ogni caso crea
sessioni anonime e consuma il modello vero, quindi non si parte mai contro la produzione per
default. Risultati in `evals/risultati/<etichetta>.json` (`meta`, `riepilogo`, risposte intere,
testo streamato e finale di ogni turno).

## Cosa controlla

**Generici** (ogni risposta):
`risposta_non_vuota` · `nessuna_lingua_estranea` (ideogrammi) · `frasi_integre` (artefatti delle
guardie, «di nel termine previsto…») · `nessuna_autocorrezione` («Aspetta: …») ·
`nessuna_fuga_prompt` · `testo_letto_uguale_finale` (quello letto in streaming = quello che
resta) · `nessun_errore_di_stream`.

**Specifici** (dal caso, `attese`): `tutti` (fatti che devono esserci), `una_di` (almeno
un'alternativa), `nessuno` (affermazioni note come sbagliate), `escalation`
(`nessuna|consigliata|urgente`: rinvio al professionista, e per `urgente` anche un'indicazione
di tempo), `non_spinge_vendita`.

**Prestazioni** (separate, dipendono dal modello e dalla macchina): latenza e primo token.

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

Stesso comando con `--modello` e `--etichetta` diversi, poi confronta `riepilogo` nei due file
(`controlli_specifici`, `per_controllo`, latenze). Le attese specifiche sono lo stesso metro
per tutti: serve a rispondere a «quale modello regge il ruolo?» con dati e non a impressione.

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
