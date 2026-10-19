"""Avvisi all'utente quando il bot NON ha letto tutto ciò che gli è stato dato.

Misurato il 19/10/2026: un contratto da 10 pagine arrivava al modello a pezzi (i 10 chunk più simili alla domanda,
circa metà del testo) e il bot rispondeva «ho letto tutto il documento, 45 articoli», senza vedere le clausole
alle pagine 8 e 10; un testo incollato da 12.000 caratteri veniva tagliato a 8.000 e il bot concludeva «nel testo
mancano le clausole» (la penale era in fondo). Qui si dice la verità, due volte: al MODELLO (nel prompt, perché non
dichiari di aver letto tutto né concluda sull'assenza di qualcosa) e all'UTENTE (riga in coda alla risposta).
"""
from __future__ import annotations

from typing import Optional


def testo_tagliato(lunghezza: int, tetto: int) -> Optional[tuple[str, str]]:
    """(nota per il modello, avviso per l'utente) se il messaggio supera il tetto, altrimenti None."""
    if lunghezza <= tetto:
        return None
    nota = (f"\nATTENZIONE — TESTO TAGLIATO: l'ultimo messaggio dell'utente è lungo {lunghezza} caratteri e ti è arrivato "
            f"troncato ai primi {tetto}: NON hai letto il resto. Non dire di aver letto tutto e non concludere che nel "
            "testo manchi qualcosa (clausole, dati, importi): potrebbe stare nella parte che non vedi. Dillo chiaramente "
            "all'utente e chiedigli di inviare il resto a parti.\n")
    avviso = (f"Nota: il testo che hai incollato è lungo {lunghezza:,} caratteri e ne ho letti solo i primi {tetto:,}: "
              "la parte finale non l'ho vista. Per un controllo completo mandamela a pezzi o caricala come file."
              ).replace(",", ".")
    return nota, avviso


def copertura_allegati(stat: list[dict]) -> Optional[tuple[str, str]]:
    """`stat`: [{file, mostrati, totale, pagine}] per ogni file. Se qualche file è letto solo in parte:
    (nota per il modello, avviso per l'utente), altrimenti None."""
    parziali = [s for s in stat if s.get("totale") and s.get("mostrati", 0) < s["totale"]]
    if not parziali:
        return None
    righe_m = "; ".join(f"«{s['file']}»: {s['mostrati']} parti su {s['totale']}"
                        + (f" (pagine {s['pagine']})" if s.get("pagine") else "") for s in parziali)
    nota = (f"\nCOPERTURA DEGLI ALLEGATI: di questi file vedi SOLO una parte — {righe_m}. NON hai letto i documenti per intero: "
            "non scrivere «ho letto tutto» e non concludere che un'informazione non ci sia; se la domanda riguarda il "
            "documento intero (rischi, clausole, controlli), dì che stai analizzando solo le parti mostrate e offri di "
            "proseguire sulle altre.\n")
    righe_u = "; ".join(f"«{s['file']}»: {s['mostrati']} parti su {s['totale']}" for s in parziali)
    avviso = (f"Nota: ho analizzato solo una parte del documento ({righe_u}). Per un controllo completo chiedimi di "
              "esaminare anche le altre parti.")
    return nota, avviso


def aggiungi(testo: str, avvisi: list[str]) -> str:
    """Accoda gli avvisi al testo visibile (una riga ciascuno, dopo una riga vuota)."""
    avvisi = [a for a in avvisi if a]
    if not avvisi:
        return testo
    return (testo or "").rstrip() + "\n\n" + "\n".join(avvisi)
