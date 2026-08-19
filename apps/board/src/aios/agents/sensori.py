"""Lettura dei sensori con isolamento del guasto e provenienza esplicita.

Due problemi veri, visti in produzione ad agosto 2026:

1. Un sensore rotto azzerava il reparto. Con il token Instagram invalidato, `_gather()`
   del marketing sollevava sul primo read e l'agente non produceva NIENTE per giorni.
   Un reparto marketing non dipende da un canale social, e nessun reparto deve fermarsi
   perché una fonte è giù.
2. L'agente non distingueva "nessuna fattura scaduta" da "non riesco a leggere le
   fatture", e riempiva il vuoto inventando lavoro: 10 insert su un registro vuoto,
   solleciti su fatture inesistenti, 50 varianti di un'assunzione immaginaria. La coda
   era arrivata a 646 proposte da annullare in blocco.

Qui la lettura ritorna sempre, registra com'è andata, e il blocco di stato dice
all'agente cosa può e non può usare.
"""
from __future__ import annotations

from typing import Any, Callable

OK = "ok"
VUOTO = "vuoto"
GUASTO = "guasto"


def leggi_sicuro(reader: Callable[..., Any], nome: str, fonti: dict[str, str],
                 **args: Any) -> Any:
    """Legge un sensore isolando il guasto. Ritorna i dati, o None se vuoto/guasto,
    e scrive in `fonti[nome]`: 'ok (n righe)' | 'vuoto' | 'guasto: <causa>'."""
    try:
        out = reader(nome, **args)
    except Exception as exc:
        fonti[nome] = f"{GUASTO}: {str(exc)[:120]}"
        return None
    # Molti sensori non sollevano: ritornano {"error": ...} (connettori env-gated).
    if isinstance(out, dict) and out.get("error"):
        fonti[nome] = f"{GUASTO}: {str(out['error'])[:120]}"
        return None
    if out is None or (isinstance(out, (list, dict, str, tuple)) and len(out) == 0):
        fonti[nome] = VUOTO
        return None
    fonti[nome] = f"{OK} ({len(out)} righe)" if isinstance(out, list) else OK
    return out


def blocco_stato(fonti: dict[str, str]) -> str:
    """Blocco di provenienza da mettere nel prompt: cosa ha dati, cosa è vuoto, cosa è
    rotto e perché — più le regole per non inventare lavoro sul vuoto."""
    if not fonti:
        return ""
    ok = [n for n, s in fonti.items() if s.startswith(OK)]
    vuote = [n for n, s in fonti.items() if s == VUOTO]
    rotte = {n: s[len(GUASTO) + 2:] for n, s in fonti.items() if s.startswith(GUASTO)}
    righe = ["\n\n# STATO DELLE FONTI (leggilo prima di proporre)"]
    if ok:
        righe.append("Con dati: " + ", ".join(ok))
    if vuote:
        righe.append("VUOTE (rispondono ma non contengono nulla): " + ", ".join(vuote))
    if rotte:
        righe.append("GUASTE (non leggibili adesso): "
                     + "; ".join(f"{n} → {c}" for n, c in rotte.items()))
    righe.append(
        "Regole non negoziabili: lavora sulle funzioni coperte dalle fonti CON DATI. "
        "Su una fonte VUOTA l'unica proposta legittima è UNA azione di avvio (collegare la "
        "fonte, importare i dati, creare il primo record) — mai attività operative su dati "
        "che non esistono, mai numeri inventati. Su una fonte GUASTA non proporre nulla che "
        "dipenda da lei: è un problema tecnico, non una decisione di business. Una fonte "
        "spenta non ferma il reparto: copri le altre funzioni.")
    return "\n".join(righe)
