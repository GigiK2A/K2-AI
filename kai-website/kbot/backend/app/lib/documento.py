"""Documento di lavoro (PEC, lettera, registro, verbale…) separato dalla conversazione.

Problema (test 07/08, 20/10/2026): la PEC e la spiegazione giuridica stavano nello STESSO testo; l'interfaccia mostrava
«Documento in preparazione», «DA VERIFICARE», la spiegazione e la bozza insieme, e il documento comparso era un riquadro
fermo per minuti. Qui il modello racchiude il documento fra due righe di marcatura:

    <<<DOCUMENTO: PEC di contestazione>>>
    …testo del documento…
    <<<FINE DOCUMENTO>>>

Tutto ciò che sta fuori è conversazione (premessa breve, cosa verificare). I marcatori passano nello STREAM così il client
può mostrare il documento mentre si scrive, in uno spazio suo; il messaggio salvato li conserva, così dopo un ricaricamento
il documento è ancora separato. L'esportazione usa solo il blocco, senza intestazioni del sistema.
"""
from __future__ import annotations

import re
from typing import List, Optional, TypedDict

_APERTURA = re.compile(r"<<<\s*DOCUMENTO(?:\s*:\s*([^>\n]{1,120}?))?\s*>>>", re.I)
_CHIUSURA = re.compile(r"<<<\s*FINE\s+DOCUMENTO\s*>>>", re.I)

# Una richiesta di DOCUMENTO TESTUALE che la chat sa scrivere (non un report del motore 8e). «report», «analisi», «cruscotto»
# restano al flusso dei report: «genera il report» non è una richiesta di lettera.
_VERBI = (r"scrivi|scrivimi|redigi|redigimi|prepara|preparami|stendi|stendimi|compila|compilami|bozza|abbozza|stila|"
          r"fammi|formula|genera|generami|crea|creami|produci|elabora")
_DOCUMENTI = (r"lettera|diffida|mail|e-?mail|pec|raccomandata|contratto|atto|comunicazione|messaggio|risposta|reclamo|"
              r"contestazione|verbale|disdetta|recesso|preventivo|sollecito|informativa|testo|registro|documento|modulo|"
              r"modello|nomina|delega|autocertificazione|dichiarazione|valutazione|notifica|segnalazione|procedura|"
              r"policy|regolamento|istruzione operativa")
_RICHIESTA = re.compile(rf"\b(?:{_VERBI})\b.{{0,80}}?\b(?:{_DOCUMENTI})\b", re.I | re.S)
_REPORT = re.compile(r"\b(?:report|analisi|cruscotto|check-?up|bilancio|piano|pdf|excel|business plan)\b", re.I)

REGOLA = """
FORMATO DEL DOCUMENTO (obbligatorio): il documento richiesto va racchiuso fra una riga <<<DOCUMENTO: titolo breve>>> e una
riga <<<FINE DOCUMENTO>>>. Dentro i marcatori ci sono SOLO il testo del documento (intestazione, corpo, chiusura): niente
spiegazioni giuridiche, niente commenti, niente domande, niente «bozza»/«da verificare». Prima del documento al massimo due
righe di premessa; dopo, poche righe: cosa verificare e quali dati completare. Se l'utente aggiunge informazioni o chiede
modifiche, riscrivi il documento COMPLETO e aggiornato in un nuovo blocco (stesso titolo), senza ripetere le spiegazioni già
date. Non dire mai che non puoi generare il documento: dove manca un dato lascia un segnaposto [così].
""".strip()


class Blocco(TypedDict):
    titolo: str
    testo: str
    completo: bool          # False = il blocco è aperto e il testo sta ancora arrivando


def richiesta_documento(ultimo_utente: str) -> bool:
    """True se l'ultimo messaggio chiede di scrivere un documento testuale (PEC, lettera, registro, verbale…)."""
    t = ultimo_utente or ""
    if not _RICHIESTA.search(t):
        return False
    m = _RICHIESTA.search(t)
    # «genera il report/documento dell'analisi»: parole da report vicino al documento → resta al flusso dei report
    return not _REPORT.search(t[max(0, m.start() - 10): m.end() + 40])


def estrai(testo: str) -> List[Blocco]:
    """I blocchi-documento del testo, in ordine. Un blocco non ancora chiuso (stream in corso) ha completo=False."""
    out: List[Blocco] = []
    pos = 0
    t = testo or ""
    while True:
        a = _APERTURA.search(t, pos)
        if not a:
            break
        c = _CHIUSURA.search(t, a.end())
        corpo = t[a.end(): c.start() if c else len(t)].strip("\n").strip()
        out.append({"titolo": (a.group(1) or "Documento").strip(), "testo": corpo, "completo": bool(c)})
        if not c:
            break
        pos = c.end()
    return out


def fuori_dal_documento(testo: str) -> str:
    """La conversazione: il testo senza i blocchi-documento (resta una traccia del blocco aperto: nulla di ciò che sta dentro)."""
    t = testo or ""
    out, pos = [], 0
    for a in _APERTURA.finditer(t):
        if a.start() < pos:
            continue
        out.append(t[pos:a.start()])
        c = _CHIUSURA.search(t, a.end())
        pos = c.end() if c else len(t)
        if not c:
            break
    out.append(t[pos:])
    return re.sub(r"\n{3,}", "\n\n", "".join(out)).strip()


def ultimo_documento(testo: str) -> Optional[Blocco]:
    blocchi = estrai(testo)
    return blocchi[-1] if blocchi else None


def proteggi(testo: str):
    """Sostituisce i marcatori con segnaposto alfanumerici (le pulizie di forma come output_quality.polish tolgono tutto ciò che
    sembra un tag «<<<…>>>»). Ritorna (testo, mappa) da passare a `ripristina`."""
    mappa: dict = {}

    def _apri(m):
        k = f"KBOTDOCAPRI{len(mappa)}KBOT"
        mappa[k] = m.group(0)
        return k

    def _chiudi(m):
        k = f"KBOTDOCCHIUDI{len(mappa)}KBOT"
        mappa[k] = m.group(0)
        return k

    t = _APERTURA.sub(_apri, testo or "")
    t = _CHIUSURA.sub(_chiudi, t)
    return t, mappa


def ripristina(testo: str, mappa: dict) -> str:
    t = testo or ""
    for k, v in mappa.items():
        t = t.replace(k, v)
    return t
