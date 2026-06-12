# Guida demo K-BOT — cosa chiedere, come funziona, cosa evitare

> Preparata per la demo a potenziali clienti. Tutto verificato l'11 giugno 2026.
> Backend test 130/130 · Frontend type-check pulito · I 3 generatori PDF allineati al design premium teal.

---

## 1. In 30 secondi: cos'è il K-BOT

Il K-BOT Premium è un **analista AI**: l'utente parla in chat, lui fa qualche domanda mirata,
poi genera un **report PDF professionale** (impaginazione premium, copertina, KPI, conclusioni).

**Non è** un consulente di automazioni. Se gli chiedi "fammi un agente che risponde alle mail"
ti rimanda al sito (k2-ai.it/suite-ai). Il suo unico output è un **documento di analisi scritto**.

---

## 2. Come funziona il flusso (3 fasi)

```
[1] DOMANDE            [2] RIEPILOGO            [3] PDF
utente scrive   →   K-BOT fa MIN 3        →   paghi 19€   →   PDF premium
il tema             domande mirate            (Stripe)        scaricabile in chat
                    (una alla volta)
```

1. **Raccolta** — il bot fa **minimo 3 domande**, una alla volta, per capire:
   obiettivo concreto, perimetro, dati interni disponibili, settore/dimensione, scadenza.
   Accetta risposte vaghe e prosegue (nessuna risposta è obbligatoria).
2. **Riepilogo** — quando ha abbastanza contesto, conferma e prepara il report
   (blocco interno `CONSULENZA_SUMMARY`, non visibile all'utente).
3. **Generazione** — Claude Sonnet scrive il contenuto, ReportLab impagina il PDF premium,
   email con allegato via Resend, link in chat.

**Campi che raccoglie** (in modo naturale, non come modulo): tipo report · tipo azienda ·
obiettivo · perimetro · dati disponibili · scadenza · note.

### Scorciatoia per la demo (saltare le domande)
Se vuoi il report **subito** senza rispondere a 3 domande, scrivi una di queste frasi **esatte**:
> `vai` · `procedi` · `fai il report senza domande` · `salta le domande` · `voglio il report subito` · `basta domande`

⚠️ Attenzione: "fai un audit", "voglio l'analisi", "report SEO" **NON** sono scorciatoie —
sono richieste di analisi e il bot farà comunque le domande. Servono le frasi letterali sopra.

---

## 3. ✅ Cosa PUOI chiedere (12 tipi di analisi)

Sono i report che il bot sa produrre. In demo, scegline uno coerente col settore del cliente:

| # | Tipo di analisi | Esempio di richiesta da fare in demo |
|---|---|---|
| 1 | **Analisi di bilancio / salute finanziaria** | "Analizza la salute finanziaria della mia azienda: flussi, margini, solvibilità" |
| 2 | **Analisi marketing** | "Voglio capire posizionamento, target e canali del mio business" |
| 3 | **Audit SEO** | "Fammi un audit SEO del mio sito" (poi rispondi alle domande) |
| 4 | **Analisi competitiva / benchmark** | "Confronta la mia offerta con i 3 competitor principali" |
| 5 | **Analisi di fattibilità** | "È fattibile aprire una seconda sede? Voglio un'analisi" |
| 6 | **Business plan / piano industriale** | "Aiutami a strutturare un business plan a 3 anni" |
| 7 | **Analisi investimenti** (ROI, payback) | "Vale la pena questo investimento da 80k? ROI e scenari" |
| 8 | **Analisi processi** (AS-IS → TO-BE, descrittiva) | "Mappa i colli di bottiglia del mio processo ordini" |
| 9 | **Due diligence** (commerciale/operativa/documentale) | "Due diligence commerciale su un'azienda che voglio acquisire" |
| 10 | **Analisi dati / report custom su file caricati** | (carichi un Excel/PDF) "Analizza questi dati di vendita" |
| 11 | **Studio di mercato / ricerca settoriale** | "Studio del mercato della ristorazione a Perugia" |
| 12 | **Analisi reputazione online / sentiment** | "Com'è percepito il mio brand online?" |

**Punto di forza per la demo**: il #10 (carica un file). Mostra che legge un documento reale,
cita le fonti con `(pag. N)` e produce un'analisi basata sui dati caricati. Molto convincente.

---

## 4. ❌ Cosa NON chiedere (verrà rifiutato → suite-ai)

Il K-BOT Premium produce **solo analisi/report scritti**. NON propone e NON costruisce software.
Se chiedi una di queste cose, risponde "esula da K-BOT Premium, trovi i servizi di automazione
su k2-ai.it/suite-ai" e torna sul tema analisi:

- ❌ "Costruiscimi un **agente AI** che risponde alle email"
- ❌ "Fammi una **microapp** / un'**integrazione** col gestionale"
- ❌ "Imposta un sistema **RAG** sui miei documenti"
- ❌ "**Automatizza** il mio flusso di fatturazione"
- ❌ "Scrivi il **codice** / sviluppa il software per…"

Questo è **voluto**, non un bug: l'automazione è un servizio diverso (progetti suite-ai),
il K-BOT è il prodotto self-serve da 19€. In demo, se serve, spiegalo come differenziazione:
*"il bot dà l'analisi; l'implementazione è un progetto a parte"*.

Altri limiti da sapere:
- Il **report vero non appare mai in chat** — solo nel PDF. La chat serve a capire e annunciare.
- Anteprima massima in chat: 3-5 bullet sintetici (<600 caratteri). Niente report lungo a schermo.
- Non mostra mai JSON, codice o tag interni di sistema.

---

## 5. Le 3 famiglie di documenti generati (tutte premium, stesso stile teal)

Il cliente potrebbe vedere documenti diversi a seconda del percorso. **Ora sono visivamente
coerenti** (stessa palette teal #00BFA6, font Syne/DMSans, copertina, KPI, footer):

| Famiglia | Cos'è | Pagamento | Generatore |
|---|---|---|---|
| **Report conversazionale** | l'analisi dalla chat (i 12 tipi sopra) | 19€ una-tantum | `pdf_renderer.py` |
| **Boost** | deliverable verticali approfonditi (8-12 pagine) | a prezzo (sconto abbonati) | motore 8e |
| **Check express** | calcoli deterministici (de minimis, KPI, ecc.) | a crediti (1cr=1€) | `check_renderer.py` |

> Fix di oggi: il report conversazionale usava un accento **oro** diverso dal resto. Ora è
> **teal** come boost e check → famiglia visiva unica. Inoltre il testo di fallback non è più
> a tema SEO (rischiava di mostrare "Google Search Console" a un cliente di ingegneria): ora è neutro.

---

## 6. Gli abbonamenti (catalogo Luca)

| Piano | Prezzo | Crediti/mese | Sconto Boost | Utenti | Esegue servizi |
|---|---|---|---|---|---|
| **Account gratuito** | 0€ | 0 | – | 1 | No (solo vetrina + esempi) |
| **Pro** | 49€/mese | 50 | −10% | 1 | Sì |
| **Studio** | 149€/mese | 200 | −20% | 3 | Sì |

Pacchetti crediti una-tantum: 49€→50cr · 199€→220cr (consigliato) · 499€→600cr.
I **crediti** pagano i Check express; i **Boost** restano a prezzo (mai a crediti).

---

## 6-bis. Motore unico 8e + demo mode (aggiornamento 11 giu)

In **demo mode** la chat non genera più col renderer conversazionale: instrada al **Boost giusto del catalogo** (selettore) e lo genera col **motore 8e** (profondo, validato, con citazioni). Dopo qualche domanda compare il pannello del documento; "Genera il documento completo (demo)" → 8e → PDF, **senza pagamento**.

**Env da impostare per la demo** (tutto OFF/assente = produzione invariata):

| Dove | Variabile | Valore |
|---|---|---|
| Backend kbot | `KBOT_DEMO_MODE` | `1` |
| Backend kbot | `K2A_8E_BASE_URL` | URL del motore 8e (Railway o `http://localhost:8800`) |
| Backend kbot | `K2A_8E_API_KEY` | stesso Bearer del motore 8e |
| Backend kbot | `ANTHROPIC_API_KEY` | la chiave |
| Motore 8e | `K2A_8E_ENTITLEMENT_DEV` | `true` (accetta il token demo) |
| Motore 8e | `K2A_8E_API_KEY` | stesso Bearer |
| Motore 8e | `ANTHROPIC_API_KEY` | la chiave (generazione profonda) |
| Frontend kbot | `NEXT_PUBLIC_KBOT_DEMO_MODE` | `1` + **rebuild** |
| Frontend kbot | `NEXT_PUBLIC_API_BASE_URL` | URL del backend kbot |

> Verificato: wiring chat→8e end-to-end sul mock, motore 8e reale fa boot (22 servizi, entitlement permissive). NON ancora fatto un giro di generazione 8e reale con la chiave (costa crediti) → fare 1 dry-run.

## 7. Checklist pre-demo (5 minuti prima)

- [ ] Frontend K-BOT su `/app/` parte e fa login Supabase
- [ ] Backend FastAPI risponde (`/api/kbot/engine/health` per il motore 8e)
- [ ] Hai **crediti Anthropic** sufficienti (ogni report reale consuma API)
- [ ] Hai pronto **1 file di esempio** (Excel/PDF) per mostrare l'analisi su dati caricati
- [ ] Sai già quale dei 12 tipi mostrerai, coerente col settore del cliente in sala
- [ ] Se vuoi velocità: ricorda la parola `procedi` per saltare le domande

### Copione demo suggerito (3 minuti)
1. Apri la chat, scrivi: *"Voglio un'analisi di fattibilità per aprire una seconda sede"*
2. Rispondi a 3 domande del bot (obiettivo, budget, scadenza)
3. Sblocca il PDF (19€) → mostra il documento premium impaginato
4. Bonus: carica un Excel e chiedi *"analizza questi dati"* → mostra le citazioni `(pag. N)`

---

## 8. Cosa è stato sistemato per la demo (sintesi tecnica)

- ✅ Report conversazionale allineato al design premium teal (era oro/incoerente)
- ✅ Rimosso il testo di fallback SEO-specifico → neutro per ogni settore
- ✅ Corrette le icone che rendevano come quadratini vuoti (tofu) nei PDF
- ✅ Backend: 130/130 test verdi · Frontend: type-check pulito
- ✅ Motore 8e (boost) e Check D1 già su design premium teal
