# UX psychology — leggi e pattern applicati a siti, landing, app

Fonte: Steve Krug (*Don't Make Me Think*), Jakob Nielsen (heuristics), Don Norman, psicologia della Gestalt, ricerca UXR consolidata 2000-2024.

---

## 1. Hick's law — paralisi da scelta

Il tempo di decisione cresce col **logaritmo** del numero di opzioni. Raddoppiare le opzioni non raddoppia il tempo: lo aumenta di una quantità minore, ma sufficiente a far abbandonare.

**Applicazione**:
- **Un CTA primario per schermata**, al massimo uno secondario sottotono.
- **Menu** con massimo 5-7 voci. Se ne hai 15, raggruppale in macro-categorie.
- **Piani prezzi**: 3 > 7.
- **Form a step multipli** (un campo per pagina) convertono meglio di form lunghi.

**Eccezione**: contesti di esplorazione/scoperta (cataloghi, marketplace). Qui le opzioni sono parte del valore. Usa filtri e ricerca potenti, non riduzione brutale.

---

## 2. Fitts's law — target di click

Il tempo per raggiungere un target è funzione della distanza e della dimensione. **Bottoni grandi e centrali convertono di più**.

**Applicazione**:
- **Target mobile**: minimo 44×44 px (linea guida Apple), meglio 48×48 px (Android). Sotto = frizione + rage taps.
- **CTA principale**: dimensione superiore ai CTA secondari.
- **Spazio attorno al bottone**: white space = "non cliccare altro".
- **Desktop**: sfrutta gli angoli dello schermo (pixel infiniti). I menu di sistema sono lì per questo.

---

## 3. Von Restorff — isolation effect

Un elemento visivamente diverso si ricorda e si nota di più.

**Applicazione**:
- Un solo elemento con il colore accent del brand per schermata.
- Badge "Più scelto" su un piano tra 3.
- In una lista di feature, un'icona diversa per evidenziare la feature strategica.

**Rischio**: usarlo su tutto. Se tutto è "speciale", niente lo è più.

---

## 4. Legge di Miller (magical number seven, plus or minus two)

La memoria di lavoro gestisce 7±2 elementi simultaneamente. In contesti di attenzione moderna (mobile, multitasking) si parla più spesso di 4-5.

**Applicazione**:
- **Feature list**: 3-5 benefici principali. Sotto ci si perde.
- **Navigation**: menu principali con 5-7 voci.
- **Checkout steps**: se il processo ha 8 step, sembra infinito. Raggruppa in 3-4 macro-fasi con progress bar.

---

## 5. Gestalt — come il cervello raggruppa gli elementi

Le leggi della Gestalt descrivono come percepiamo automaticamente gruppi e relazioni tra elementi visivi.

**Prossimità**: elementi vicini sono percepiti come gruppo. → Raggruppa benefici, separa il prezzo.

**Somiglianza**: elementi simili (colore, forma, dimensione) sono percepiti come correlati. → Usa stessa forma/colore per cose della stessa categoria.

**Chiusura**: il cervello completa forme incomplete. → Puoi usare linee spezzate, il lettore chiude la figura.

**Continuità**: l'occhio segue linee continue. → Layout con flusso direzionale guida la lettura.

**Figura/sfondo**: un elemento è "primo piano", il resto è "sfondo". → Usa contrasto per rendere il CTA figura e il resto sfondo.

---

## 6. Friction audit

Ogni click, scroll, campo form, loading è **una tassa** sulla conversione. Misure reali:

| Frizione | Perdita conversione |
|---|---|
| Ogni secondo aggiuntivo di caricamento | -7% circa |
| Ogni campo aggiuntivo in form | -5% a -15% |
| Ogni step aggiuntivo in checkout | -10% a -30% |
| Richiesta di registrazione prima di poter fare qualsiasi cosa | fino a -40% |

**Rimuovi**:
- Campi form non indispensabili (chiedi solo email, il resto dopo).
- Account obbligatori dove potrebbe bastare guest checkout.
- Popup intrusivi su mobile (penalizzati da Google, frustrano l'utente).
- Step in cui l'utente inserisce dati che già potresti dedurre (es. CAP → città automatica).

**Aggiungi frizione *buona*** dove serve:
- Conferma prima di azioni distruttive ("Sei sicuro di voler cancellare il tuo account?").
- Attesa tra due decisioni importanti se vuoi ridurre l'impulsività (es. acquisti a rischio).
- Pausa intenzionale per far riflettere su un upgrade rilevante.

---

## 7. Zeigarnik effect — compiti incompleti

Ricordiamo meglio i compiti incompleti. Il cervello "tiene aperta" la tensione.

**Applicazione**:
- **Progress bar** "3 di 5 completati" → aumenta drasticamente il completamento (onboarding, checkout, profilo).
- **Checklist gamificate** in dashboard: l'utente torna per "chiudere la tensione".
- **Serie di contenuti** ("ti invio la prima parte ora, il resto domani"): trattiene l'attenzione.

---

## 8. F-pattern e Z-pattern — come l'occhio scansiona

Studi di eye tracking (Nielsen, 2006 e successivi) mostrano pattern ricorrenti:

**F-pattern**: pagine dense di testo (blog, articoli, liste).
- Due orizzontali all'inizio, poi una verticale lungo il bordo sinistro.
- → Headline e prime parole di ogni bullet pesano tantissimo.

**Z-pattern**: pagine con poco testo e forte visual (landing, hero section).
- In alto a sx → in alto a dx → diagonale verso il basso a sx → in basso a dx.
- → Logo top-left, CTA top-right, messaggio centrale, CTA finale bottom-right.

**Implicazioni**:
- Logo top-left non è convenzione casuale.
- Navigation top-right per accessibilità (ma su mobile va centrale o full-width).
- CTA nel punto di arrivo dello sguardo.

---

## 9. Above the fold (visible senza scroll)

Il 70% del traffico italiano è mobile. "Above the fold" su mobile = ~600 px di altezza.

**Cosa deve esserci sopra la piega mobile**:
1. Proposta di valore chiara (headline + sub-headline)
2. Prova sociale minima (numero, logo, stellina)
3. Un CTA primario

Tutto il resto può scrollare.

**Errore classico**: hero mobile con solo immagine e logo, senza headline leggibile. Il 40% degli utenti non scrolla oltre.

---

## 10. Law of proximity applicata ai prezzi

Se il prezzo è visivamente *vicino* al valore (benefici, testimonianze), sembra ragionevole. Se è isolato in alto a destra, sembra alto.

**Pattern**:
- **Non isolare il prezzo**. Mettilo sotto una lista di benefici concreti.
- **Prezzo al mese** sopra prezzo all'anno (se entrambi rilevanti).
- **Valore totale** prima del prezzo di acquisto ("Contenuti che trovi a 800€ altrove — qui 99€").

---

## 11. Principi di accessibilità come principi di conversione

Spesso dimenticati, ma l'accessibilità coincide con la conversione.

- **Contrasto colore** (WCAG AA: 4.5:1 per testo normale, 3:1 per testo grande). Senza contrasto, il CTA non viene visto.
- **Font size** minimo 16px su body mobile. Sotto, l'utente 45+ abbandona.
- **Alt text** sulle immagini importanti: SEO + screen reader + contesto quando l'immagine non carica.
- **Etichette form chiare** (non solo placeholder che sparisce appena clicchi).
- **Error state** chiari e gentili ("la password deve avere almeno 8 caratteri" > "errore").

---

## 12. Peak-end UX — chiudi meglio che inizi

La peak-end rule (Kahneman) applicata alla UX:

**Momenti "wow"** da curare:
- Primo login / primo "successo" dell'utente.
- Completamento di un compito importante (grazie personalizzato, animazione).
- Messaggio post-acquisto (email dettagliata, pacchetto curato).
- Primo risultato tangibile del servizio.

**Chiusure da curare**:
- Email di benvenuto dopo signup.
- Messaggio di commiato se l'utente si disiscrive (mai colpevolizzare, mai trucchi per trattenere: l'esperienza finale viene ricordata e raccontata).
- Fine checkout: conferma chiara con prossimi step, tempo di consegna, contatto.

---

## 13. Velocità = emozione

Performance tecnica è esperienza psicologica.

- **Sotto 1s**: percepito istantaneo, genera fiducia.
- **1-3s**: percepito come rapido.
- **Oltre 3s**: il 53% degli utenti mobile abbandona (dati Google).
- **Oltre 5s**: abbandono quasi totale.

**Trucchi psicologici per mascherare attesa** (dove l'ottimizzazione tecnica è al limite):
- **Skeleton screens** (placeholder che mostrano la struttura) percepiscono più veloce di spinner generico.
- **Progress bar** (anche fittizia) riduce l'ansia d'attesa.
- **Feedback di azione immediato** (UI risponde subito, anche se il server ci mette 2s): ottimismo UI.

---

## 14. Dark pattern da NON usare

Evita assolutamente, per etica e per regolamentazione (GDPR, EU Consumer Protection, Digital Services Act).

- **Confirmshaming**: "No grazie, non voglio risparmiare" (colpevolizzare chi rifiuta).
- **Roach motel**: facile entrare (iscrizione), impossibile uscire (disiscrizione nascosta dietro 14 click).
- **Privacy Zuckering**: impostazioni privacy volutamente confuse.
- **Hidden costs**: prezzo mostrato senza spedizione/IVA, aggiunti solo in checkout.
- **Forced continuity**: trial "gratuito" che diventa abbonamento automatico senza chiaro preavviso.
- **Misdirection**: pulsante "accetta tutti" ben visibile, "rifiuta" nascosto in grigio piccolo.
- **Bait and switch**: annuncio di una cosa, consegna di un'altra.

**Regola generale**: se un pattern fa guadagnare a breve termine penalizzando il cliente, distrugge fiducia a medio termine. I big player (Booking, Ryanair, Amazon) hanno preso multe milionarie per dark pattern negli ultimi 3 anni.

---

## 15. Checklist audit UX rapida

Quando valuti una pagina esistente:

1. **3-second test**: un estraneo, in 3 secondi, capisce cosa offri, a chi e perché dovrebbe cliccare?
2. **Mobile first**: sopra la piega c'è tutto l'essenziale?
3. **Un CTA dominante**: è visivamente isolato e chiaramente primo?
4. **Prova sociale visibile** già nella hero section?
5. **Tempo di caricamento** sotto 3 secondi su 4G?
6. **Contrasto** leggibile in condizioni di luce reali (non solo studio)?
7. **Form**: chiedo il minimo indispensabile per questo step?
8. **Chiusura**: il momento finale (grazie, conferma, email) è memorabile?
9. **Nessun dark pattern**?
10. **Coerenza con il brand**: tono, colori, font, voce sono coerenti con ciò che il cliente si aspetta dopo aver letto gli ads?

Se anche uno di questi punti è debole, quello è il primo posto dove lavorare.
