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

## LUNGHEZZA (BLOCCANTE)

L'articolo deve restare ≥ 1.400 parole (validator boccia sotto 1.200).
Se durante la revisione cancelli ripetizioni o ridondanze e il word
count scende, ESPANDI le sezioni più magre con:
- un esempio quantificato in più
- un'implicazione concreta di non agire
- una FAQ con risposta da 130-150 parole
Non lasciare paragrafi sotto le 60 parole nelle sezioni 01-05.

## TITLE + META (BLOCCANTE)

Se `title_tag` supera 65 caratteri o `meta_description` è fuori dal
range 140-155 char, riscrivili. Il `title_h1` deve essere ≤ 55 char
così che `title_h1 + " | K2-AI"` resti dentro 65.

## OUTPUT

Articolo intero rivisto, stesso formato. Niente preamboli.
