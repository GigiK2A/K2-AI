"""Verifica ARITMETICA delle operazioni scritte nella risposta: «2.130.000 − 140.000 = 2.090.000» → 1.990.000.

Misurato il 19/10/2026 (modello locale): su 3 prove dello stesso calcolo della PFN, 2 sbagliavano la sottrazione
(2.090.000 invece di 1.990.000) e da lì l'indice (2,94 invece di 2,8). Un errore di calcolo scritto con aria di
certezza è peggio di un numero mancante. Qui il codice rifà le operazioni «a op b [op c…] = r» (solo + − × ÷, numeri in
formato italiano) e, se il risultato scritto non torna entro l'arrotondamento, lo SOSTITUISCE col valore giusto. Una
correzione si propaga: le occorrenze successive del vecchio risultato (anche come operando di un'operazione
successiva) diventano il valore corretto, e le operazioni che ne dipendono vengono rifatte.

Prudente di proposito: niente parentesi, niente percentuali, niente espressioni con parole; un «=» che non è
un'uguaglianza numerica (es. «=» in un elenco) non produce nessun numero e non viene toccato.
KBOT_ARITMETICA=0 spegne.
"""
from __future__ import annotations

import logging
import os
import re
from decimal import Decimal, InvalidOperation

log = logging.getLogger(__name__)

_N = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"
_OP = r"[+\-−–×x*/÷]"
_ESPR = re.compile(
    rf"(?<![\w.,/])(?P<ops>(?:{_N})(?:\s*{_OP}\s*(?:{_N})){{1,4}})\s*[=≈]\s*(?P<res>{_N})(?![\d.,]*\d)")
_TOK = re.compile(rf"({_N})|({_OP})")


def _dec(tok: str) -> Decimal:
    return Decimal(tok.replace(".", "").replace(",", "."))


def _fmt(v: Decimal, decimali: int, come: str) -> str:
    """Il valore nello stile del numero sbagliato: punti per le migliaia e virgola per i decimali."""
    q = Decimal(1).scaleb(-decimali)
    s = f"{v.quantize(q):f}"
    intero, _, dec = s.partition(".")
    neg = intero.startswith("-")
    intero = intero.lstrip("-")
    con_punti = re.sub(r"(?<=\d)(?=(\d{3})+$)", ".", intero) if ("." in come.split(",")[0] or len(intero) > 3) else intero
    return ("-" if neg else "") + con_punti + (("," + dec) if decimali else "")


def _valuta(tokens: list[str]) -> Decimal | None:
    """Valuta a op b op c con la precedenza usuale (× ÷ prima di + −)."""
    try:
        termini: list[Decimal] = [_dec(tokens[0])]
        segni: list[str] = []
        i = 1
        while i < len(tokens):
            op, n = tokens[i], _dec(tokens[i + 1])
            if op in "×x*":
                termini[-1] = termini[-1] * n
            elif op in "/÷":
                if n == 0:
                    return None
                termini[-1] = termini[-1] / n
            else:
                segni.append("-" if op in "-−–" else "+")
                termini.append(n)
            i += 2
        tot = termini[0]
        for sg, t in zip(segni, termini[1:]):
            tot = tot - t if sg == "-" else tot + t
        return tot
    except (InvalidOperation, ZeroDivisionError, IndexError):
        return None


def _primo_errore(testo: str):
    """(inizio, fine, vecchio, nuovo) del primo risultato sbagliato nel testo, oppure None."""
    for m in _ESPR.finditer(testo):
        toks = [a or b for a, b in _TOK.findall(m.group("ops"))]
        giusto = _valuta(toks)
        if giusto is None:
            continue
        scritto = m.group("res")
        dec = len(scritto.split(",")[1]) if "," in scritto else 0
        try:
            scritto_v = _dec(scritto)
        except InvalidOperation:
            continue
        tolleranza = Decimal("0.5") * Decimal(1).scaleb(-dec) + Decimal("0.0000001")
        # i numeri molto grandi scritti «a spanne» (arrotondati) non sono errori di calcolo
        if abs(scritto_v - giusto) <= max(tolleranza, abs(giusto) * Decimal("0.0005")):
            continue
        nuovo = _fmt(giusto, dec, scritto)
        if nuovo != scritto:
            return m.start("res"), m.end("res"), scritto, nuovo
    return None


def correggi(testo: str) -> str:
    """Corregge i risultati sbagliati uno alla volta, dal primo: dopo ogni correzione il vecchio valore, nelle
    occorrenze SUCCESSIVE (operandi di calcoli seguenti, citazioni a parole), diventa il valore giusto, e si riparte:
    così le operazioni che dipendono dal risultato sbagliato vengono rifatte con quello corretto."""
    if not testo or os.getenv("KBOT_ARITMETICA", "1") == "0" or ("=" not in testo and "≈" not in testo):
        return testo
    try:
        res, n = testo, 0
        for _ in range(12):
            err = _primo_errore(res)
            if not err:
                break
            a, b, vecchio, nuovo = err
            # la propagazione vale solo per risultati «riconoscibili» (≥4 cifre o con decimali): un «100» o un «2»
            # sbagliato compaiono altrove con altri significati e non vanno toccati
            riconoscibile = len(re.sub(r"\D", "", vecchio)) >= 4 or "," in vecchio
            coda = (re.sub(rf"(?<![\d.,]){re.escape(vecchio)}(?![\d]|[.,]\d)", nuovo, res[b:])
                    if riconoscibile else res[b:])
            res = res[:a] + nuovo + coda
            n += 1
        if n:
            log.warning("aritmetica_guard: %d risultato/i corretto/i nella risposta", n)
        return res
    except Exception:
        log.warning("aritmetica_guard: errore (fail-open)", exc_info=True)
        return testo
