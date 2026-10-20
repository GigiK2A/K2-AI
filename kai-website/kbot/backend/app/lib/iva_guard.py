"""Controllo deterministico «IVA inclusa»: se l'utente dice che un importo è IVA inclusa e la risposta calcola l'IVA come
se fosse l'imponibile (2.500 × 22% = 550) invece di scorporarla (2.049,18 + 450,82), il codice aggiunge una nota con i
valori giusti. Segnalato il 20/10/2026: «computer da 2.500 € IVA inclusa» → calcoli sull'IVA sbagliati e ripetuti anche
dopo le richieste di approfondimento. Non riscrive la risposta (potrebbe avere un senso diverso): la affianca.
KBOT_IVA_GUARD=0 spegne.
"""
from __future__ import annotations

import os
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

_N = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"
_INCLUSA = r"(?:iva\s+(?:inclusa|compresa)|ivata|iva\s+inclus\w+|comprensiv\w+\s+di\s+iva|con\s+iva\s+compresa)"
_RE_INCL = re.compile(rf"(?P<a>{_N})\s*(?:€|euro|eur\b)?\s*[,;]?\s*{_INCLUSA}|{_INCLUSA}\s*[:\-–]?\s*(?:di\s+|pari\s+a\s+)?(?:€\s*)?(?P<b>{_N})", re.I)
_RE_ESCLUSA = re.compile(r"\bpiù\s+iva\b|\+\s*iva\b|\biva\s+escl\w+|\boltre\s+iva\b|\bal\s+netto\s+(?:dell['’]\s*)?iva\b", re.I)
_RE_ALIQ = re.compile(r"iva[^.\n]{0,25}?\b(4|5|10|22)\s*%|\b(4|5|10|22)\s*%\s*(?:di\s+)?iva", re.I)


def _dec(t: str) -> Decimal:
    return Decimal(t.replace(".", "").replace(",", "."))


def _it(v: Decimal) -> str:
    s = f"{v.quantize(Decimal('0.01'), ROUND_HALF_UP):,.2f}"          # 2,049.18
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _forme(v: Decimal) -> set:
    """Come può comparire un importo nella risposta: «550», «550,00», «2.049,18», «2049,18»."""
    q = v.quantize(Decimal("0.01"), ROUND_HALF_UP)
    it = _it(q)
    out = {it, it.replace(".", "")}
    if q == q.to_integral():
        out |= {str(int(q)), f"{int(q):,}".replace(",", ".")}
    return out


def nota(testi_utente: list, risposta: str) -> Optional[str]:
    """La nota da aggiungere alla risposta, o None."""
    if os.getenv("KBOT_IVA_GUARD", "1") == "0" or not risposta:
        return None
    utente = "\n".join(t for t in testi_utente if isinstance(t, str))
    m = _RE_INCL.search(utente)
    if not m or _RE_ESCLUSA.search(utente):
        return None                                   # nessuna «IVA inclusa», oppure dichiarazioni in conflitto: non si tocca
    lordo = _dec(m.group("a") or m.group("b"))
    if lordo < 50:
        return None
    ma = _RE_ALIQ.search(risposta) or _RE_ALIQ.search(utente)
    aliquota = Decimal(ma.group(1) or ma.group(2)) if ma else Decimal(22)
    imponibile = (lordo / (Decimal(1) + aliquota / 100)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    iva = lordo - imponibile
    giusti = _forme(imponibile) | _forme(iva)
    sbagliato = _forme((lordo * aliquota / 100).quantize(Decimal("0.01"), ROUND_HALF_UP))
    r = risposta
    ha_giusti = any(re.search(rf"(?<![\d.,]){re.escape(f)}(?![\d]|[.,]\d)", r) for f in giusti)
    ha_sbagliato = any(re.search(rf"(?<![\d.,]){re.escape(f)}(?![\d]|[.,]\d)", r) for f in sbagliato)
    if ha_giusti or not ha_sbagliato:
        return None
    return (f"\n\nNota di controllo sull'IVA: hai detto che {_it(lordo).replace(',00', '')} € è IVA inclusa. In quel caso "
            f"l'imponibile è {_it(imponibile)} € e l'IVA {_it(iva)} € (aliquota {aliquota}%): i calcoli qui sopra che "
            f"applicano il {aliquota}% a {_it(lordo).replace(',00', '')} € ({_it(lordo * aliquota / 100)} €) partono da "
            f"un importo diverso da quello che hai indicato.")
