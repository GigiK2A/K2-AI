"""Controlli del banco di prova della chat K-BOT.

Funzioni pure, solo libreria standard: si testano senza rete (vedi
tests/test_evals_checks.py) e non dipendono dal modello in uso.

Due famiglie:
  * GENERICI: valgono per ogni risposta (lingua, frasi integre, nessuna
    auto-correzione, nessuna fuga del prompt, testo letto = testo finale...).
  * SPECIFICI: dichiarati nel caso (`attese`): fatti che devono esserci,
    affermazioni che non devono esserci, rinvio al professionista.

Ogni controllo ritorna (ok: bool, dettaglio: str). Il dettaglio dice COSA ha
fatto fallire il controllo, per poterlo leggere nel rapporto senza riaprire la
risposta.
"""
from __future__ import annotations

import re
from typing import Iterable

# ── pattern ──────────────────────────────────────────────────────────────────
_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯]")

# Artefatti lasciati dalle guardie quando sostituiscono un pezzo di frase
# («di nel termine previsto…», «a un importo previsto dalla normativa»).
_PREP = r"(?:di|a|da|con|per|tra|fra|su|in)"
_SOSTITUTI = (r"(?:nel termine previsto dalla normativa|un importo previsto dalla normativa|"
              r"una quota non determinabile|la normativa di riferimento)")
_FRASE_ROTTA = [
    re.compile(rf"\b{_PREP}\s+{_SOSTITUTI}", re.I),
    re.compile(r"\bl['’]il\s+codice", re.I),
    re.compile(r"\bdi\s+nel\b", re.I),
    re.compile(r"\ba\s+nel\s+termine", re.I),
    re.compile(r"\b(?:è|sono)\s+(?:pari\s+)?(?:una quota non determinabile|un importo previsto dalla normativa)", re.I),
]

_AUTOCORREZIONE = re.compile(
    r"(?:^|[.!?]\s+|\n)\s*(?:Aspetta|Correzione|Mi correggo|Anzi|Ops|Scusa,? (?:ho sbagliato|errore))\b\s*[:,.!]"
    r"|\bNo\s*[\u2014\u2013-]+\s*correggo\b|\bcorreggo con certezza\b",
    re.I)

# Commento interno del critico di qualità finito nel testo per l'utente (visto in produzione il
# 15/10/2026: «La bozza contiene una diagnosi assertiva… Ecco la versione corretta e prudente»).
_TESTO_DEL_CRITICO = re.compile(
    r"\bLa bozza (?:contiene|presenta|è|risulta)\b|\bEcco la versione (?:corretta|riveduta|prudente)\b|"
    r"\bversione corretta e prudente\b|\bdiagnosi assertiva\b|\bpremature_summary\b|"
    r"\bdepth_mismatch\b|\bdrastic_actions\b|\bassertive_diagnosis\b", re.I)

_FUGA_PROMPT = re.compile(
    r"REGOLE FISSE|NON NEGOZIABILI|FASE COMPRENSIONE|CONSULENZA_SUMMARY|DIAGNOSI_STATO|"
    r"FASE INTERVISTA|build_system_prompt", re.I)

_PROFESSIONISTA = re.compile(
    r"avvocat\w*|legale\b|commercialista|consulente (?:del lavoro|fiscale|legale)|professionista|"
    r"notaio|\bDPO\b|dottore commercialista|studio legale", re.I)

_URGENZA = re.compile(
    r"subito|urgent\w*|senza ritardo|immediatament\w*|tempestivament\w*|"
    r"\bentro\s+(?:il\s+)?\d|\b\d+\s*(?:giorni|ore)\b|scadenz\w+|termine", re.I)

_VENDITA = re.compile(r"report (?:completo|PDF|a pagamento|dedicato)|\bPDF\b|19\s?€|19 euro|abbonament\w+", re.I)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


# ── controlli generici ───────────────────────────────────────────────────────
def risposta_non_vuota(testo: str, minimo: int = 20):
    n = len(_norm(testo))
    return n >= minimo, f"{n} caratteri" if n < minimo else ""


def nessuna_lingua_estranea(testo: str):
    m = _CJK.findall(testo or "")
    return not m, f"caratteri non latini: {''.join(m[:6])}" if m else ""


def frasi_integre(testo: str):
    for rx in _FRASE_ROTTA:
        m = rx.search(testo or "")
        if m:
            a = max(0, m.start() - 30)
            return False, f"…{_norm((testo or '')[a:m.end() + 30])}…"
    return True, ""


def nessuna_autocorrezione(testo: str):
    m = _AUTOCORREZIONE.search(testo or "")
    return (m is None), (f"«{_norm(m.group(0))}»" if m else "")


def nessun_testo_del_critico(testo: str):
    m = _TESTO_DEL_CRITICO.search(testo or "")
    return (m is None), (f"«{m.group(0)}»" if m else "")


def nessuna_fuga_prompt(testo: str):
    m = _FUGA_PROMPT.search(testo or "")
    return (m is None), (f"«{m.group(0)}»" if m else "")


_TIPOGRAFIA = str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
                             "\u00ab": '"', "\u00bb": '"', "\u2013": "-", "\u2014": "-"})


def _senza_forma(s: str) -> str:
    """Toglie ciò che il rendering cambia di proposito: apostrofi/virgolette tipografiche,
    marcatori markdown, puntini elenco, spazi. Resta la SOSTANZA del testo."""
    s = (s or "").translate(_TIPOGRAFIA)
    s = re.sub(r"[*_`#\u2022\u25aa\u2023\u00b7]", "", s)
    s = re.sub(r"(?m)^\s*-\s+", "", s)
    return re.sub(r"\s+", "", s)


def testo_letto_uguale_finale(streamato: str, finale: str):
    """Quello che l'utente legge in streaming deve essere quello che resta. Le differenze solo
    di forma (apostrofi, grassetto, spazi) non contano: conta se una CIFRA, una frase o un
    termine cambiano sotto gli occhi di chi legge."""
    a, b = _senza_forma(streamato), _senza_forma(finale)
    if a == b:
        return True, ""
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return False, f"diverge dal carattere {i}: \u00ab{a[i:i + 40]}\u00bb \u2192 \u00ab{b[i:i + 40]}\u00bb"


def nessun_errore_di_stream(errori: Iterable[str], eccezione: str | None = None):
    errori = list(errori or [])
    if eccezione:
        return False, eccezione
    return (not errori), "; ".join(errori)[:160]


def entro_budget(valore: float | None, budget: float, etichetta: str):
    if valore is None:
        return False, f"{etichetta}: nessun dato"
    return valore <= budget, f"{etichetta} {valore:.1f}s > {budget:.0f}s" if valore > budget else ""


GENERICI = ("risposta_non_vuota", "nessuna_lingua_estranea", "frasi_integre",
            "nessuna_autocorrezione", "nessun_testo_del_critico", "nessuna_fuga_prompt",
            "testo_letto_uguale_finale",
            "nessun_errore_di_stream")


# ── controlli specifici (dal caso) ───────────────────────────────────────────
def _cerca(rx: str, testo: str):
    return re.search(rx, testo or "", re.I | re.S)


def attese_tutti(testo: str, voci: list[dict]):
    """Ogni voce {nome, re} deve comparire."""
    mancano = [v["nome"] for v in voci if not _cerca(v["re"], testo)]
    return not mancano, ("manca: " + ", ".join(mancano)) if mancano else ""


def attese_una_di(testo: str, gruppi: list[dict]):
    """Per ogni gruppo {nome, res:[...]} almeno una regex deve comparire."""
    mancano = [g["nome"] for g in gruppi if not any(_cerca(r, testo) for r in g["res"])]
    return not mancano, ("nessuna alternativa per: " + ", ".join(mancano)) if mancano else ""


def attese_nessuno(testo: str, voci: list[dict]):
    """Nessuna voce {nome, re} deve comparire (affermazioni note come sbagliate)."""
    trovate = []
    for v in voci:
        m = _cerca(v["re"], testo)
        if m:
            a = max(0, m.start() - 25)
            trovate.append(f"{v['nome']} «{_norm(testo[a:m.end() + 25])}»")
    return not trovate, "; ".join(trovate)


def escalation(testo: str, livello: str):
    """nessuna → nessun controllo; consigliata → rinvia a un professionista;
    urgente → rinvia a un professionista E dà un'indicazione di tempo."""
    if livello in (None, "", "nessuna"):
        return True, ""
    if not _PROFESSIONISTA.search(testo or ""):
        return False, "non rinvia a un professionista"
    if livello == "urgente" and not _URGENZA.search(testo or ""):
        return False, "rinvia ma senza alcuna indicazione di tempo"
    return True, ""


def non_spinge_vendita(testo: str):
    m = _VENDITA.search(testo or "")
    return (m is None), (f"«{m.group(0)}»" if m else "")
