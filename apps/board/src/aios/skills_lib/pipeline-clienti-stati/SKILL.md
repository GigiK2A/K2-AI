---
name: pipeline-clienti-stati
description: >-
  Tabella clienti e stati della pipeline vendite K2-AI (CRM interno): ciclo di vita del
  lead in pipeline_leads, quali stati avanzano da soli leggendo la posta e quali
  richiedono giudizio, come si legge il quadro commerciale, quando un lead è morto.
  Metodo vendite per prospect, outreach, trattativa B2B, offerta e closing su ogni
  account.
---

# Tabella clienti e stati — pipeline vendite

La tabella è `pipeline_leads`. Una riga per azienda, non per persona. Chi la aggiorna:
la posta per i fatti, tu per il giudizio.

## Gli stati, in ordine

| Stato | Significa | Chi lo mette |
|---|---|---|
| `nuovo` | trovato, mai contattato | ricerca clienti (`cerca_clienti`) |
| `contattato` | gli abbiamo scritto, nessuna risposta | automatico: email in uscita |
| `risposto` | ha risposto, contenuto ancora da valutare | automatico: email in entrata |
| `interessato` | dalla risposta si capisce che c'è interesse concreto | **tu**, leggendo l'email |
| `riunione` | call o incontro fissato, con data | **tu** |
| `proposta` | offerta economica inviata | **tu** |
| `cliente` | ha accettato | **tu** |
| `perso` | no esplicito, o silenzio dopo 3 tentativi in 6 settimane | **tu** |
| `scartato` | fuori target: non è un cliente possibile | **tu**, con il motivo |

Da `cliente`, `perso` e `scartato` non si torna indietro per un'email: quelli li muove
una persona. Un lead che rientra dopo mesi è un lead nuovo, con una nota che rimanda al
precedente.

## Cosa succede da solo

Il modulo `pipeline_clienti` gira nel loop di autonomia e accoppia le email di
`email_messages` ai lead per indirizzo esatto, poi per dominio (`info@` e
`commerciale@` della stessa azienda sono la stessa riga). Mai per nome dell'azienda nel
testo: «Modulo» dentro una newsletter accoppierebbe a caso.

Muove SOLO due stati, perché sono i due che sono fatti e non interpretazioni:

- email in uscita verso il lead → `contattato`
- email in entrata dal lead → `risposto`

Aggiorna sempre `last_contact_at`, anche quando lo stato non cambia. È quel campo che
dice quali lead stanno morendo: uno stato `risposto` fermo da tre settimane vale meno di
un `contattato` di ieri.

## Cosa tocca a te

Quando un lead arriva a `risposto`, **leggi l'email** e decidi. Le tre domande, in
quest'ordine:

1. Ha detto no? → `perso`, e scrivi in `notes` la ragione esatta con le sue parole.
2. Chiede qualcosa di concreto (prezzi, tempi, una call, un esempio)? → `interessato`,
   e metti in `next_action` la mossa specifica, con una data in `next_action_date`.
3. È una risposta di cortesia o un rinvio? → resta `risposto`, `next_action` = quando
    risollecitare e su cosa.

Non usare `interessato` per una risposta tiepida: gonfia la pipeline e ti fa lavorare
sui lead sbagliati. Meglio un `risposto` onesto.

## Come si legge il quadro

`pipeline_clienti.tabella()` dà le righe più il conteggio per stato e quanti sono
aperti. Usalo quando l'owner chiede «come va la pipeline»: rispondere a impressione,
con i dati a disposizione, è il modo più rapido per perdere la sua fiducia.

Numeri che contano più del totale:

- quanti `nuovo` mai contattati da più di 7 giorni → lavoro fermo
- quanti `contattato` senza risposta da più di 10 giorni → serve un sollecito
- quanti `risposto` non valutati → decisioni che stai rimandando
- quanti senza `next_action` → lead che nessuno sta muovendo

## Regole che non si negoziano

- **Un contatto non si inventa.** Se un lead non ha email, `next_action` è «trovare il
  contatto diretto», non un indirizzo plausibile. Un `info@` costruito a mente è un
  invio a vuoto e brucia il dominio.
- **`score` va da 1 a 10** in questa tabella, mentre `fit_score` dei prospect va da 0 a
  100. Sono due scale: 85 su 100 vale 9 su 10.
- **Le email al cliente restano all'approvazione dell'owner.** Aggiornare lo stato è
  interno e lo fai da solo; scrivere a un'azienda esce dall'azienda e si conferma.
- **Se sposti dieci lead e ne riesci a spostare sei, dici sei.** Elenca i quattro
  rimasti e il motivo.
- **Le date partono da oggi, e cadono in giorni lavorativi.** Una `next_action_date` di
  domenica viene spostata al lunedì dall'attuatore, ma arrivarci già giusta evita di far
  leggere all'owner un piano che non torna. Se stai per scrivere un anno diverso da
  quello corrente, hai sbagliato.
