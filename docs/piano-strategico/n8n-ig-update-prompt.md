# Prompt per l'agente che gestisce il workflow n8n IG

> Copia-incolla integralmente al tuo agente / collaboratore che ha
> costruito il workflow n8n "Spotlight Instagram" (Workflow 07).
> È self-contained: contiene tutto il context che serve.

---

## INIZIO PROMPT

Ciao. Abbiamo aggiunto un **blog autopilot** al sito K2-AI
(https://www.k2-ai.it/blog). Da questa settimana il blog pubblica un
articolo ogni giovedì alle 06:00 CET, sullo stesso topic della riga del
Google Sheet "Servizi" che tu poi userai per il post Instagram alle
18:00 dello stesso giorno.

Il tuo workflow n8n attuale (Spotlight Instagram, lanciato giovedì
18:00) deve essere **modificato in modo non distruttivo** per:

1. Leggere 3 colonne nuove dal Sheet
2. Non pubblicare se il blog non è uscito
3. Includere il link al blog nella caption

---

### CONTESTO TECNICO

**Foglio Google Sheets**:
- Stesso file che già usi
- Tab: `Servizi`
- Colonne nuove aggiunte dopo le 6 esistenti:

| Colonna | Nome | Significato |
|---|---|---|
| G | `blog_slug` | slug dell'articolo blog (es. `automatizzare-email-pmi`) |
| H | `blog_pubblicato` | data ISO `YYYY-MM-DD` di quando il blog è uscito |
| I | `blog_url` | path assoluto sul sito (es. `/blog/automatizzare-email-pmi`) |
| J | `pillar_padre` | codice pillar K2-AI (P01-P20) |
| K | `pillar_url` | URL pillar (es. `/suite-ai/agenti-email-crm.html`) |

Il blog autopilot **gira prima di te** (giovedì 06:00). Quando il blog
pubblica, scrive le colonne G, H, I della stessa riga.

Il tuo workflow attuale guarda solo la colonna E (`Stato`) per scegliere
la riga, poi marca `Stato=usato` + scrive `Data` dopo aver pubblicato.

---

### MODIFICHE RICHIESTE AL WORKFLOW

**1. Filtro nuovo per la riga**

Sostituisci la condizione attuale `Stato = "da usare"` con:

```
Stato = "da usare"
AND blog_pubblicato != ""   (non vuoto)
```

Se nessuna riga soddisfa entrambe → manda alert Telegram
(`📭 IG: nessuna riga con blog pubblicato per oggi`) e **termina senza
pubblicare**. Questo previene post IG che linkano a un blog che non
esiste.

**2. Verifica che l'URL blog risponda 200**

Prima di pubblicare il post IG, fai una HEAD request a:

```
https://www.k2-ai.it{blog_url}
```

Se status != 200, salta la riga, alert Telegram
(`❌ IG: blog_url ${blog_url} ritorna ${status}. Skip.`) e **termina**.

**3. Modifica template caption Instagram**

Aggiungi alla fine della caption che generi con GPT-4o-mini questo
blocco:

```
📖 Articolo completo (lettura 7 min):
https://www.k2-ai.it{blog_url}

#K2AI #AIperPMI #AutomazioneAI
```

Lo so che IG NON rende cliccabili i link nelle caption (solo bio).
Va bene comunque: l'utente vede il link e lo apre da bio o cerca su
Google. Importante: il link va citato esplicitamente per chiarezza.

**4. (Bonus opzionale) Pin del link in bio settimanale**

Se vuoi automatizzare anche l'aggiornamento del link in bio Instagram:
ogni giovedì 18:01 (dopo la pubblicazione del post), aggiorna il link
in bio a:

```
https://www.k2-ai.it{blog_url}
```

API IG Graph supporta `business_discovery` ma non l'edit bio
direttamente — serve passaggio manuale, oppure servizio terzo come
Linktree con sync automatico. Lascia perdere se è troppo per ora,
metti solo il link in caption.

**5. State machine — NON CAMBIA**

Mantieni il tuo comportamento attuale:
- Dopo pubblicazione IG → `Stato = "usato"` + `Data = oggi`
- Le colonne blog (G, H, I) NON le toccare: le scrive il blog bot

---

### PROMPT DI ESEMPIO PER GPT-4o-mini

Aggiungi al system prompt che già usi (qualcosa tipo "genera caption
Instagram per servizio K2-AI") questa istruzione finale:

```
Alla fine della caption (PRIMA degli hashtag), inserisci sempre questo
blocco esatto:

---
📖 Articolo completo (lettura 7 min):
https://www.k2-ai.it{blog_url}

Dove {blog_url} è il valore della colonna I del Sheet. NON modificare
il dominio. NON aggiungere "https://" se è già presente. Mantieni il
testo "Articolo completo (lettura 7 min)" esattamente come scritto.
```

---

### CHECKLIST POST-MODIFICA

- [ ] Filtro riga aggiornato (Stato=`da usare` AND blog_pubblicato!=vuoto)
- [ ] HEAD request verso `https://www.k2-ai.it{blog_url}` aggiunta
- [ ] Telegram alert per caso "no blog oggi"
- [ ] Caption GPT include il link al blog
- [ ] State machine `Stato=usato` + `Data=oggi` ancora attiva
- [ ] Test manuale: trigger workflow ora, verifica:
  - se nessuna riga ha `blog_pubblicato` → alert + skip (atteso)
  - se aggiungo manualmente `blog_pubblicato=2026-05-29` e `blog_url=/blog/test` su una riga → pubblica con quel link in caption

### DOMANDE FREQUENTI

**Q: cosa succede se il blog bot fallisce un giovedì?**
A: il tuo workflow IG trova zero righe con `blog_pubblicato != ""` per
quella settimana. Skip + alert. Settimana saltata. Riprende il giovedì
successivo.

**Q: cosa succede se IG fallisce ma blog è OK?**
A: la riga ha `blog_pubblicato` valorizzato ma `Stato` ancora `da usare`.
Il giovedì successivo, blog bot vede `Stato=da usare` AND
`blog_pubblicato != vuoto` → **skippa** quella riga e va alla
successiva (perché blog bot pubblica solo righe con
blog_pubblicato=vuoto). IG ritenta. Coerente.

**Q: posso ancora aggiungere righe nuove al Sheet?**
A: sì. Aggiungi solo nelle colonne A-F come fai oggi, e compila J e K
(pillar) per le righe nuove. G, H, I lasciale vuote — le compila il
blog bot.

**Q: cosa succede se blog bot pubblica DUE righe in un giorno (es. dopo
un fix manuale)?**
A: blog bot pubblica una sola riga per esecuzione (la prima che
matcha). Se vuoi forzare due, esegui due volte il workflow. IG legge la
prima con blog_pubblicato del giorno corrente (LIFO) — ordina per
`Data` desc se preferisci controllo esplicito.

---

### CONTATTO

Per chiarimenti: scrivere a info@k2-ai.it o sulla chat Telegram
`278384928` dove arrivano gli alert.

Riferimenti tecnici:
- Codice blog bot: `/Volumes/PARASSITA/K-AI/tools/blog-bot/`
- GitHub Actions: `.github/workflows/blog-autopilot.yml`
- Sheet setup: `docs/piano-strategico/sheet-setup-guide.md`

## FINE PROMPT
