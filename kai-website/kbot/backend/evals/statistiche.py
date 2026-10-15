"""Statistiche del banco di prova: quanto è stabile una misura e quando un confronto è reale.

Il modello non è deterministico: la stessa domanda può avere una risposta giusta in un'esecuzione e
sbagliata in quella dopo (visto il 15/10/2026 sul limite del contante). Con UNA sola esecuzione per
caso, una differenza di uno o due controlli fra due file di risultati non dice niente. Qui si misura
la variazione fra ripetizioni e si dichiara quando un confronto non può essere letto.

Solo libreria standard. Funzioni pure: nessuna rete.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Iterable

METRICHE = {
    "specifici_ok": "controlli specifici superati",
    "generici_ok": "controlli generici superati",
    "casi_tutte_attese": "casi con tutte le attese rispettate",
    "casi_senza_difetti_generici": "casi senza difetti generici",
}


def _rep(r: dict) -> int:
    return int(r.get("ripetizione", 1))


def ripetizioni(risultati: Iterable[dict]) -> list[int]:
    return sorted({_rep(r) for r in risultati})


def totali_per_ripetizione(risultati: list[dict]) -> list[dict]:
    """Un dizionario di totali per ogni ripetizione (i file senza `ripetizione` contano come 1)."""
    out = []
    for k in ripetizioni(risultati):
        rr = [r for r in risultati if _rep(r) == k]
        g_ok = g_tot = s_ok = s_tot = casi_attese = casi_senza_dif = 0
        for r in rr:
            g, s = r["esito"]["generici"], r["esito"]["specifici"]
            g_tot += len(g)
            g_ok += sum(1 for ok, _ in g.values() if ok)
            casi_senza_dif += all(ok for ok, _ in g.values())
            if s:
                s_tot += len(s)
                s_ok += sum(1 for ok, _ in s.values() if ok)
                casi_attese += all(ok for ok, _ in s.values())
        out.append({"ripetizione": k, "casi": len(rr), "generici_ok": g_ok, "generici_tot": g_tot,
                    "specifici_ok": s_ok, "specifici_tot": s_tot, "casi_tutte_attese": casi_attese,
                    "casi_senza_difetti_generici": casi_senza_dif})
    return out


def media_sd(valori: list[float]) -> tuple[float, float | None]:
    """Media e deviazione standard campionaria (None con meno di 2 valori)."""
    if not valori:
        return 0.0, None
    m = statistics.fmean(valori)
    return m, (statistics.stdev(valori) if len(valori) >= 2 else None)


def variazione(totali: list[dict]) -> dict:
    """{metrica: {valori, media, sd}} sulle ripetizioni."""
    out = {}
    for chiave in METRICHE:
        v = [t[chiave] for t in totali]
        m, sd = media_sd(v)
        out[chiave] = {"valori": v, "media": round(m, 2), "sd": None if sd is None else round(sd, 2)}
    return out


def instabili(risultati: list[dict]) -> list[dict]:
    """Controlli che sullo STESSO caso passano in alcune ripetizioni e falliscono in altre.
    Sono la prova diretta che la differenza fra due esecuzioni singole è rumore."""
    esiti: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for r in risultati:
        for gruppo in ("generici", "specifici"):
            for nome, (ok, _) in r["esito"][gruppo].items():
                esiti[(r["id"], f"{gruppo}.{nome}")].append(bool(ok))
    return [{"caso": c, "controllo": n, "ok": sum(v), "su": len(v)}
            for (c, n), v in sorted(esiti.items()) if 0 < sum(v) < len(v)]


def tassi_per_controllo(risultati: list[dict]) -> dict[str, tuple[int, int]]:
    """{gruppo.nome: (superati, totali)} su tutte le esecuzioni."""
    acc: dict[str, list[int]] = {}
    for r in risultati:
        for gruppo in ("generici", "specifici"):
            for nome, (ok, _) in r["esito"][gruppo].items():
                a = acc.setdefault(f"{gruppo}.{nome}", [0, 0])
                a[0] += bool(ok)
                a[1] += 1
    return {k: (a, b) for k, (a, b) in sorted(acc.items())}


def giudizio(a: list[float], b: list[float]) -> str:
    """Come leggere la differenza fra due serie di totali.

    Se SOLO una parte ha più ripetizioni (tipico: una base a esecuzione singola contro una
    nuova esecuzione ripetuta), si usa la sua deviazione standard anche per l'altra e lo si
    dichiara: è un'ipotesi (che la variazione sia simile), non una misura."""
    ma, sda = media_sd(a)
    mb, sdb = media_sd(b)
    delta = mb - ma
    if delta == 0:
        return "nessuna differenza"
    nota = ""
    if sda is None and sdb is None:
        return "variazione non misurabile: serve più di una ripetizione in almeno una parte"
    if sda is None or sdb is None:
        singola, ripetuta = ("A", "B") if sda is None else ("B", "A")
        soglia = 2 * (sdb if sda is None else sda)
        nota = (f" [ipotesi: la variazione di {singola} è simile a quella di {ripetuta}; "
                f"{singola} ha una sola esecuzione]")
    else:
        soglia = 2 * max(sda, sdb)
    if abs(delta) <= soglia:
        return f"entro la variazione osservata (2·sd = {soglia:.1f}): non distinguibile dal rumore{nota}"
    return f"oltre la variazione osservata (2·sd = {soglia:.1f}): differenza probabilmente reale{nota}"


def confronta(dati_a: dict, dati_b: dict) -> list[dict]:
    """Confronto fra due file di risultati: una riga per metrica."""
    ta, tb = totali_per_ripetizione(dati_a["risultati"]), totali_per_ripetizione(dati_b["risultati"])
    righe = []
    for chiave, etichetta in METRICHE.items():
        va, vb = [t[chiave] for t in ta], [t[chiave] for t in tb]
        ma, sda = media_sd(va)
        mb, sdb = media_sd(vb)
        righe.append({"metrica": chiave, "etichetta": etichetta,
                      "a": {"media": round(ma, 2), "sd": None if sda is None else round(sda, 2), "n": len(va), "valori": va},
                      "b": {"media": round(mb, 2), "sd": None if sdb is None else round(sdb, 2), "n": len(vb), "valori": vb},
                      "delta": round(mb - ma, 2), "giudizio": giudizio(va, vb)})
    return righe


def formatta_confronto(righe: list[dict], dati_a: dict, dati_b: dict) -> str:
    def f(x):
        sd = "n/d" if x["sd"] is None else f"{x['sd']:.1f}"
        return f"{x['media']:.1f} (n={x['n']}, sd {sd})"
    out = [f"A: {dati_a.get('meta', {}).get('modello') or '?'} · {dati_a.get('meta', {}).get('data', '')[:10]}",
           f"B: {dati_b.get('meta', {}).get('modello') or '?'} · {dati_b.get('meta', {}).get('data', '')[:10]}", ""]
    for r in righe:
        out.append(f"{r['etichetta']:42} A {f(r['a']):26} B {f(r['b']):26} Δ {r['delta']:+.1f}")
        out.append(f"{'':42} → {r['giudizio']}")
    ia, ib = instabili(dati_a["risultati"]), instabili(dati_b["risultati"])
    for nome, lista in (("A", ia), ("B", ib)):
        if lista:
            out.append(f"\nControlli instabili in {nome} (stesso caso, esiti diversi fra ripetizioni):")
            out += [f"  {i['caso']:34} {i['controllo']:48} {i['ok']}/{i['su']}" for i in lista]
    return "\n".join(out)
