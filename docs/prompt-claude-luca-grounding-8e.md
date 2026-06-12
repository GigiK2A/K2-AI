# Prompt per il Claude di Luca — Grounding & infra per il motore 8e

> Copia tutto il blocco sotto e incollalo nella sessione di Claude di Luca.

---

## Chi sei e contesto

Stai lavorando con **Luca** (GitHub `inglucarossi73`), che presidia **backend, ecosistema, grounding normativo e strategia** del progetto **K2-AI**. Dall'altra parte c'è **Luigi** (il "braccio operativo"): frontend del sito, K-BOT, e il **motore di generazione documenti "8e"**.

Il **motore 8e** è già stato costruito e integrato (lato Luigi). È un generatore di deliverable deterministico:
- Pipeline a stadi: **routing** (catalogo chiuso) → **resolve** (fatti dallo *snapshot di grounding*, mai dal modello) → **filiera** (prosa Sonnet) → **validate** (schema JSON) → **render** (PDF premium).
- Codice in `kai-website/k2a-8e/`. Catalogo = 15 servizi / 12 tipi di boost (Legal, Fisco, Finance, Advisor, Strategy, Control, Agevolazioni, Web, Host, Safety, Build, MEP).
- Principio cardine (D-029): **i FATTI normativi NON li genera il modello** — vengono iniettati VERBATIM dallo snapshot e il modello scrive solo la prosa attorno.

La generazione profonda (report consulenziali 8-12 pagine) **funziona**: LegalBoost e FiscoBoost producono già PDF reali e corposi.

## Il problema da risolvere (è il tuo compito)

Lo **snapshot di grounding** (`kai-website/k2a-8e/grounding/grounding-snapshot.json`, prodotto dal tuo `build_snapshot.py` in `k2a-skills/snapshot/`) oggi garantisce **citazioni normative verbatim solo per LegalBoost**.

Per **tutti gli altri boost** (Fisco, Finance, Agevolazioni, Safety, ecc.) le citazioni sono attualmente **mediate dal modello**: plausibili ma non ancorate a una fonte verificata. Esempio reale appena generato da FiscoBoost: cita *"Art. 16 DPR 633/72"*, *"Art. 102 TUIR"*, *"Art. 19 DPR 633/72"* — corretti come riferimento ma **non verificati contro Normattiva** né forniti verbatim dallo snapshot.

Per un prodotto **a pagamento** (490–2500 €) di natura legale/fiscale, questo è un rischio di responsabilità inaccettabile. **Le norme citate nei deliverable devono provenire verbatim dallo snapshot, non dal modello.**

## Cosa ti chiedo (4 deliverable concreti)

### 1. Estendere lo snapshot di grounding ai boost prioritari
Per ogni boost che andrà live, popola lo snapshot con i **fatti normativi verbatim** necessari:
- testo dell'articolo/comma rilevante (verbatim, da Normattiva),
- `riferimento` leggibile (es. "Art. 16 DPR 633/72"),
- `fonte` (= `normattiva`), `vigenza` (data), e `override_locale` se serve.
- Struttura coerente con quanto già fatto per LegalBoost nello snapshot esistente.

Priorità sui boost del pilota (vedi punto 2). Per ogni boost indica **quali fatti** hai inserito e **quali restano scoperti** (gap dichiarati).

### 2. Decidere i boost del pilota
Quali 2-3 boost mandiamo live per primi? Così groundiamo **solo quelli** invece di tutti e 12. Serve la tua scelta + quella di Luigi (proposta: LegalBoost già pronto + 1 fiscale + 1 a scelta tua).

### 3. Segreti e deploy di produzione
- `K2A_ENTITLEMENT_SECRET`: stesso valore identico sui due servizi (kbot-backend **e** 8e). Confermami come/dove lo settiamo su Railway.
- URL del servizio **8e** deployato (a cui il kbot-backend deve puntare via env).
- Stripe: price/prodotti per ogni boost in catalogo (i prezzi nel `catalog.json`).

### 4. Confermare il modello economico per-documento
Ogni report profondo = **5-7 chiamate Sonnet in parallelo** (~4-6 min, ~0.4-0.8 € di API a documento). Per un deliverable da centinaia/migliaia di euro è marginale, ma confermami che il modello regge a volume.

## Formato risposta atteso

Rispondi con:
1. **Snapshot**: cosa hai groundato (per boost: lista fatti verbatim inseriti + gap residui).
2. **Pilota**: i boost scelti.
3. **Infra**: valore/posizione `K2A_ENTITLEMENT_SECRET`, URL 8e, stato price Stripe.
4. **Economics**: ok/non-ok + eventuali vincoli di volume.

Se qualcosa nel motore 8e non ti è chiaro (struttura snapshot, schema dei fatti, come `resolve()` li consuma), chiedi: Luigi ti gira i file esatti.
