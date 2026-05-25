# Skill: articolo-blog-k2ai (revise pass)

Rileggi questo articolo HTML come editor finale. Output: ARTICOLO
REVISIONATO completo, stesso formato dell'input (HTML body + blocco META).

## COSA CORREGGERE

1. **Frasi AI-typical**: rimuovi "in conclusione", "è importante notare",
   "vale la pena di", "nel mondo di oggi", "nell'era digitale",
   "in un'epoca in cui", "non è più sufficiente". Riformula naturalmente.

2. **Generalità vaghe**: dove leggi "molte aziende", "spesso",
   "alcuni studi", sostituisci con numeri concreti dal brief o con
   range plausibili ("4 PMI su 10", "3-5 minuti").

3. **Frasi troppo lunghe**: se una frase supera 25 parole, spezzala
   in 2.

4. **Ripetizioni**: se la stessa idea torna in 2 paragrafi diversi,
   tieni quella più forte e cancella l'altra.

5. **Marketing implicito**: se trovi "il nostro metodo", "la nostra
   esperienza dimostra che", "K2-AI è leader in...", riscrivi senza
   prima persona o promozione. Il tono deve essere editorial, non
   commerciale.

6. **Teaser leak**: se trovi istruzioni implementative (config
   specifiche, codice, step-by-step >5 item), RIMUOVILE e sostituisci
   con frame generico.

7. **Numeri dubbi**: se trovi un numero puntuale (es. "il 73,4%") non
   presente nel brief originale, sostituisci con range
   ("circa 70-80%") o cancella.

8. **Lede troppo introduttiva**: il lede deve agganciare al problema
   nelle prime 2 righe. Se inizia con "Nel mondo dell'AI..." → cancella
   e ricomincia dal pain concreto.

## COSA NON TOCCARE

- Struttura sezioni (01-05 + FAQ): NON cambiare l'ordine
- Classi CSS: NON modificare class="..." (servono al template)
- Blocco `<!--META ... -->`: aggiornalo solo se hai cambiato H1/lede
- Tono complessivo: non rendere più formale, lascia l'italiano diretto

## OUTPUT

Articolo intero rivisto, stesso formato. Niente preamboli.
