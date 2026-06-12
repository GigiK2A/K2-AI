# Per Luca — ci serve il MODELLO ECONOMICO completo + prezziario

*Da Luigi (runtime 8e / payment layer K-BOT). Abbiamo verificato il codice: c'è il listino e l'idraulica dei pagamenti, ma NON il modello economico. Pensiamo sia un PdM tuo/dell'ecosistema. Sotto: cosa abbiamo, cosa manca, cosa ci serve da te.*

---

## 0. Perché te lo chiediamo
Per cablare correttamente il livello pagamenti di K-BOT (Stripe + Supabase) ci serve la **fonte di verità economica**. Oggi nel repo c'è solo il listino e il pay-per-use; manca il modello (abbonamenti, crediti, unit economics, proiezioni). Non lo inventiamo noi: se esiste un documento/PdM, mandacelo; se non esiste, va costruito e dev'essere tuo.

## 1. Cosa è GIÀ implementato (codice, verificato)
- **Pagamenti**: solo `mode=payment` (una-tantum). Due flussi: report **19€** (`REPORT_PRICE_EUR_CENTS`) + **boost à-la-carte** (prezzo dal catalogo, 490-2500€).
- **Gratis**: preview con quota **2/mese** (`kbot_preview_usage`, gate W8).
- **Tier 1 (49€)**: form Airtable (lead), non Stripe.
- **Catalogo**: `catalog.json` v1.0.0 — 81 servizi, 15 generabili 8e, prezzi presenti.
- **Scaffolding abbonamenti**: esiste `prezzo_per_piano(servizio, piano)` con `sconto_tappa_pct`, MA `abbonamenti: []` è **VUOTO** → mai attivo.
- **Crediti/wallet**: **non esistono**.

## 2. Cosa MANCA (è quello che ti chiediamo)
Il file canonico `docs/piano-strategico/piano-crescita-K2-AI.json` (citato in CLAUDE.md come fonte di pricing ladder + modello 3 anni) **NON è nel repo**. Con esso manca:

1. **Definizione abbonamenti (L3)**
   - quali piani esistono (nomi, fasce)?
   - prezzo di ciascuno (mensile/annuale)?
   - cosa includono: sconto % sui boost (`sconto_tappa_pct`)? n. documenti inclusi? accesso a quali boost?
   - struttura dati attesa per popolare `abbonamenti: []` nel catalogo.

2. **Modello a crediti — esiste o no?**
   - è previsto un sistema a crediti/wallet (compri N crediti, ogni boost ne consuma X)?
   - oppure il modello resta à-la-carte + abbonamento, senza crediti?
   - se crediti: conversione €→credito, consumo per boost, scadenza.

3. **Pricing ladder completa (L0→L3)**
   - L0 preview gratis (oggi 2/mese: confermato? definitivo o A/B?),
   - L1 report 19€ (confermato?),
   - L2 boost à-la-carte: i prezzi 490-2500€ sono **validati** o da rivedere?
   - L3 abbonamento: vedi punto 1.
   - eventuali **bundle/percorsi** (il catalogo ha già `percorsi`: come si prezzano?).

4. **Unit economics / modello 3 anni**
   - margine atteso per boost (al netto del costo API ~0,4-0,8€/doc),
   - conversione attesa preview→pagato, target di churn/retention,
   - proiezione ricavi e mix (one-time vs abbonamento).

5. **Tier 1 (49€) e Tier upgrade**
   - resta lead Airtable o diventa self-serve?
   - come si incastra con boost e abbonamento?

6. **Il file canonico**
   - esiste `piano-crescita-K2-AI.json` (o equivalente) da qualche parte? Mandacelo: diventa la fonte di verità e lo agganciamo al codice.
   - se non esiste, va creato — ed è un PdM tuo (strategia/ecosistema), non runtime.

## 3. Formato risposta utile
- Per ogni livello L0-L3: prezzo, cosa include, struttura dati.
- Crediti: sì/no, e se sì le regole.
- Prezzi boost: validati/da rivedere (lista).
- Unit economics: anche solo i numeri-chiave.
- Il file canonico: link/allegato, o "da costruire".

## 4. Come si lega all'implementazione (così la tua risposta è azionabile)
- **Abbonamenti** → popolano `catalog.abbonamenti[]` + attivano `prezzo_per_piano()` (già pronto).
- **Crediti** → richiederebbero una tabella Supabase nuova (`kbot_credits`/wallet) + consumo nel checkout: dimmi se serve e progetto lo schema.
- **Prezzi** → restano nel catalogo (fonte unica), price_id Stripe mappati.

---

**In una riga:** mandaci il modello economico (abbonamenti + crediti + ladder + unit economics) o il file `piano-crescita-K2-AI.json`. Il listino c'è; il **modello** no, e crediamo sia un PdM tuo.
