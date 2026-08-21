"""Gli agenti devono sapere che giorno è.

Nessun prompt del board lo diceva. Il 21 ago 2026 Vendite ha messo la prossima azione
di NOVE lead al «2023-11-20»: non un errore di formato — una data valida, accettata da
Postgres, e sbagliata di tre anni. Il modello, non sapendo la data, ha ripiegato su
quella del suo addestramento.

È un errore che non si vede: la riga si scrive, il campo è pieno, e la pipeline dice che
i solleciti erano da fare tre anni fa. Peggio dei 400 di ieri, che almeno urlavano.

Due parti, in due posti diversi perché servono a due cose:
- `blocco_data()` va nel prompt: l'agente sa la data e può calcolare «entro 7 giorni»;
- `data_assurda()` sta nell'attuatore: anche sapendola, un modello può sbagliarla, e
  una data di piano nel passato remoto va fermata prima del database.
"""
from __future__ import annotations

import time

_GIORNI = ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica")
_MESI = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
         "agosto", "settembre", "ottobre", "novembre", "dicembre")

# Quanto indietro può stare una data «di piano» prima di essere considerata inventata.
# Un sollecito con due settimane di ritardo è plausibile; tre anni è il 2023 del modello.
GIORNI_TOLLERANZA = 45


def oggi_iso(adesso: float | None = None) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(adesso if adesso else time.time()))


def blocco_data(adesso: float | None = None) -> str:
    """Il frammento di prompt con la data di oggi, scritta in chiaro e in ISO."""
    t = time.localtime(adesso if adesso else time.time())
    umano = f"{_GIORNI[t.tm_wday]} {t.tm_mday} {_MESI[t.tm_mon - 1]} {t.tm_year}"
    return ("\n\n# CHE GIORNO È\n"
            f"Oggi è {umano}, cioè {time.strftime('%Y-%m-%d', t)}. "
            "Ogni data che scrivi deve partire da questa: «entro 7 giorni» si calcola da "
            "oggi, non da una data che ricordi. Se stai per scrivere un anno diverso da "
            f"{t.tm_year}, fermati e ricontrolla.")


def data_assurda(valore: str, adesso: float | None = None) -> bool:
    """True se una data «di piano» è troppo nel passato per essere vera.

    Non giudica le date passate in generale: `last_contact_at` e `due_at` di un task in
    ritardo stanno legittimamente dietro. Chi chiama decide su quali colonne applicarla."""
    testo = str(valore or "").strip()[:10]
    try:
        quando = time.mktime(time.strptime(testo, "%Y-%m-%d"))
    except (ValueError, OverflowError):
        return False                      # non è una data ISO: non è questo il controllo
    riferimento = adesso if adesso else time.time()
    return (riferimento - quando) > GIORNI_TOLLERANZA * 86400
