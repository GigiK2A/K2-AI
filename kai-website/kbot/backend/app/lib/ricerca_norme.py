"""Ricerca nel database normativo (Normattiva) come STRUMENTO del modello: riferimento esatto + testo, con fonte, comma e versione.

Test del 10/11/2026 (D.Lgs. 81/2008, art. 113 comma 2, scale verticali permanenti): in 4 prove su 4 il K-BOT non trovava l'articolo, anche
quando l'utente lo indicava per numero. Cause verificate: (1) il parser dei riferimenti non capiva «art. 113 comma 2 del D.Lgs. 81/2008»;
(2) il pacchetto automatico (norme_evidence) ha pochi posti e una voce fissa della mappa («lavori in quota») li riempiva con gli stessi 5
articoli; (3) il modello non aveva alcuno strumento per chiedere altro e dichiarava «ricevo solo un blocco di fonti».
Qui: `cerca()` fa il riferimento esatto (norma + articolo [+ comma]) e la ricerca testuale (FTS sulle radici delle parole, nel supplemento aggiornato
e nel corpus), restituisce articolo, comma, rubrica, versione e note di modifica; `esegui()` è lo strumento `cerca_norma` per il modello; le
consultazioni si registrano, così il codice può impedire al modello di dire «ho interrogato il database» quando ha letto solo un estratto.
Embeddings/ricerca semantica: non esistono nel corpus (solo indice FTS5); il «semantico» lo fa il modello scegliendo le parole della query.
"""
from __future__ import annotations

import contextvars
import functools
import logging
import re
import sqlite3
from typing import Any, Optional

from . import norme_evidence as N

log = logging.getLogger(__name__)

NOME_STRUMENTO = "cerca_norma"
_CONSULTAZIONI: contextvars.ContextVar = contextvars.ContextVar("kbot_consultazioni_norme", default=None)
_BUDGET_TESTO = 2400


def inizia_turno() -> None:
    _CONSULTAZIONI.set([])


def consultazioni() -> list[dict]:
    return list(_CONSULTAZIONI.get() or [])


def disponibile() -> bool:
    return N.abilitato() and N.disponibile()


def definizione() -> dict:
    return {
        "name": NOME_STRUMENTO,
        "description": (
            "Cerca nel database normativo ufficiale (Normattiva): leggi, decreti, codici. Usalo per leggere un articolo o un comma preciso "
            "(norma + articolo + comma) o per trovare gli articoli che trattano un argomento (parole chiave). Restituisce il testo vigente "
            "con fonte, comma, versione e note di modifica. Se non trova nulla, dillo all'utente: non ricostruire il testo a memoria."),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Argomento o parole chiave (es. «scale verticali permanenti gabbia di sicurezza»)."},
                "norma": {"type": "string", "description": "Norma, se nota (es. «D.Lgs. 81/2008», «L. 300/1970», «c.c.»)."},
                "articolo": {"type": "string", "description": "Numero dell'articolo, se noto (es. «113», «25-septies»)."},
                "comma": {"type": "string", "description": "Numero del comma, se noto (es. «2», «1-bis»)."},
            },
        },
    }


SYSTEM_HINT = (
    "\n\nSTRUMENTO cerca_norma — il blocco «FONTI NORMATIVE PER QUESTO TURNO» è solo un ESTRATTO scelto automaticamente: NON è l'intero "
    "database e può non contenere l'articolo che serve. Se ti serve un articolo o un comma che non c'è, o vuoi verificare un riferimento "
    "citato dall'utente, chiama `cerca_norma` (anche più volte). Cita solo ciò che il blocco o lo strumento ti hanno restituito, con "
    "articolo, comma e data della versione. Non dire MAI di aver interrogato o consultato il database se non hai chiamato lo strumento: "
    "se hai letto solo l'estratto, dì «dall'estratto di fonti che ho a disposizione». Se lo strumento non trova nulla, dillo.\n")


# ── lettura dal database, con versione ───────────────────────────────────────────────────────────────────
def _modulo():
    return N.lettore()


def _righe(db, match: str, limite: int) -> list[tuple[str, str, float]]:
    try:
        con = sqlite3.connect(f"file:{db}?immutable=1", uri=True, timeout=20)
    except sqlite3.Error:
        return []
    try:
        con.execute("PRAGMA busy_timeout=20000")
        return con.execute("SELECT file, testo, rank FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?",
                           (match, int(limite))).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()


def _db_ordinati(m) -> list[tuple[Any, str]]:
    """Prima il supplemento (articoli riscaricati dall'API ufficiale, con vigenza e note), poi il corpus consolidato."""
    out = []
    if m._supp_path():
        out.append((m._supp_path(), "supplemento"))
    if m._db_path():
        out.append((m._db_path(), "corpus"))
    return out


def _data_it(iso: str) -> str:
    return f"{iso[6:8]}/{iso[4:6]}/{iso[:4]}" if len(iso) == 8 else (f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}" if len(iso) == 10 else iso)


def versione(raw: str, origine: str = "") -> str:
    """Versione del testo, dai metadati del chunk: vigenza dall'API ufficiale, o data del consolidato del corpus."""
    fm = re.match(r"^﻿?\s*---\s*\n(.*?)\n---", raw or "", re.S)
    meta = fm.group(1) if fm else ""
    verif = re.search(r"data_vigenza:\s*'?(\d{4}-\d{2}-\d{2})", meta)
    inizio = re.search(r"inizio_vigenza_articolo:\s*'?(\d{4}-\d{2}-\d{2})", meta)
    consol = re.search(r"CONSOLIDATED/(\d{8})", meta)
    if inizio and verif and "api" in meta.lower():
        return f"testo vigente dal {_data_it(inizio.group(1))}, verificato sull'API ufficiale Normattiva il {_data_it(verif.group(1))}"
    if consol:
        return (f"testo consolidato al {_data_it(consol.group(1))} (corpus Normattiva): le modifiche successive potrebbero non esserci"
                + (f"; corpus aggiornato il {_data_it(verif.group(1))}" if verif else ""))
    if verif:
        return f"testo vigente al {_data_it(verif.group(1))}"
    return "versione non indicata nel corpus"


def _leggi(m, anno: int, numero: str, articolo: str, tipo: Optional[str] = None) -> Optional[dict]:
    num = re.sub(r"\D", "", str(numero))
    artnum = re.sub(r"\D", "", str(articolo))
    valid = m._TIPO_ALIASES.get(tipo) if tipo else None
    limite = 5000 if artnum in (num, str(anno)) else 60
    for db, origine in _db_ordinati(m):
        match = f"file:{int(anno)} AND file:{num}" + (f" AND file:{artnum}" if artnum else "")
        for file, testo, _rank in _righe(db, match, limite):
            e = m._estremi(file)
            if e.get("anno") != int(anno) or str(e.get("numero")) != num:
                continue
            if valid is not None and e.get("tipo") not in valid:
                continue
            if m._norm_art(e.get("articolo")) != m._norm_art(articolo):
                continue
            return {**e, "raw": testo, "origine_db": origine}
    return None


_GENERICI = re.compile(r"^(?:decreto\s+legislativo|decreto\s+legge|decreto|legge|codice\s+\w+|regio\s+decreto|d\.?\s?lgs\.?)$", re.I)


def _rubrica(chiaro: str) -> str:
    """Rubrica dell'articolo dall'intestazione del chunk: «# Art. 113 — Scale», oppure la riga tra parentesi che la segue."""
    testa = chiaro[:600]
    m = re.search(r"^#\s*Art\.?\s*[\w\-]+\s*[—–-]\s*(.+?)\s*$", testa, re.M)
    if m and not _GENERICI.match(m.group(1).strip()):
        return m.group(1).strip()
    m = re.search(r"^\s*\(+\s*\(?([^()\n]{3,120})\)+\s*$", testa, re.M)
    if m:
        return m.group(1).strip()
    # formato del supplemento: «# Art. 113 — Decreto Legislativo», riga vuota, rubrica su una riga, poi i commi
    m = re.search(r"^#\s*Art\.?[^\n]*\n+\s*([^\n]{3,120})\n", testa)
    if m and not re.match(r"^(?:\*\*)?\d+[.)]|^\(", m.group(1).strip()):
        return m.group(1).strip().strip("()")
    return ""


def note_di_aggiornamento(chiaro: str, comma: Optional[str] = None, massimo: int = 3, cap: int = 520) -> str:
    """Le note «AGGIORNAMENTO (n)» dell'articolo (quali norme l'hanno modificato e da quando): per un comma, quelle che lo citano; altrimenti
    le prime. Servono all'utente per sapere QUALE modifica è in vigore (es. D.L. 159/2025 conv. L. 198/2025 sull'art. 113 comma 2)."""
    note = re.findall(r"AGGIORNAMENTO\s*\((\d+)\)\s*\n(.+?)(?=\n-{5,}|\Z)", chiaro or "", re.S)
    if not note:
        return ""
    scelte = note
    if comma:
        k = re.escape(re.sub(r"\s+", "", str(comma)))
        legate = [(n, t) for n, t in note if re.search(rf"\bcomm[ai]\s*{k}\b", t, re.I)]
        scelte = legate or (note if len(note) <= massimo else [])
    out = []
    for n, t in scelte[:massimo]:
        t = re.sub(r"\s+", " ", t).strip()
        out.append(f"({n}) " + (t if len(t) <= cap else t[:cap].rstrip() + " […]"))
    return " | ".join(out)


def _scheda(m, rec: dict, comma: Optional[str], parole: list[str], origine: str, quesito: str = "") -> dict:
    corpo, abrogato = N._ripulisci(m._clean_testo(rec["raw"]))
    commi = N.dividi_commi(corpo)
    etichette = [et for et, _ in commi if et]
    avviso, testo = "", ""
    if comma:
        k = re.sub(r"\s+", "", str(comma)).lower()
        sel = [i for i, (et, _) in enumerate(commi) if et.replace(" ", "").lower() == k]
        if sel:
            testo = N._formatta(commi, sel)
        else:
            avviso = f"Il comma {comma} non risulta in questo articolo (commi trovati: {', '.join(etichette) or 'nessuno numerato'})."
    if not testo:
        idx, caps = N.seleziona_indici(commi, parole, _BUDGET_TESTO, quesito)
        testo = N._formatta(commi, idx, caps)
    return {
        "tipo": rec.get("tipo"), "anno": rec.get("anno"), "numero": rec.get("numero"), "articolo": str(rec.get("articolo")),
        "comma": (re.sub(r"\s+", "", str(comma)) if comma and not avviso else None),
        "rubrica": _rubrica(m._clean_testo(rec["raw"])), "sigla": N._sigla(rec), "citazione": rec.get("citazione", ""),
        "testo": testo, "versione": versione(rec["raw"], rec.get("origine_db", "")), "fonte": rec.get("origine_db", ""),
        "note": note_di_aggiornamento(m._clean_testo(rec["raw"]), comma if comma and not avviso else None) or N.note_rilevanti(m._clean_testo(rec["raw"])), "origine": origine, "avviso": avviso, "abrogato": abrogato,
    }


# ── ricerca testuale ─────────────────────────────────────────────────────────────────────────────────────
def _radici(testo: str) -> list[str]:
    """Radici delle parole significative (flessioni: scala/scale, verticale/verticali) e numeri."""
    out, visti = [], set()
    for w in re.findall(r"[a-zàèéìòù]{4,}|\d{2,4}", (testo or "").lower()):
        if w in N._STOP or w in ("articolo", "comma", "decreto", "legislativo", "legge", "norma", "norme", "quali", "della"):
            continue
        r = w if w.isdigit() else w[:max(4, min(6, len(w) - 2))]
        if r not in visti:
            visti.add(r)
            out.append(r)
    return out[:8]


def _cerca_testo(m, query: str, ref_norma: Optional[dict], limite: int, solo_and: bool = False) -> list[tuple[dict, int]]:
    radici = _radici(query)
    if not radici:
        return []
    ambito = f"file:{ref_norma['anno']} AND file:{re.sub(r'[^0-9]', '', str(ref_norma['numero']))} AND " if ref_norma else ""

    def _match(rad, op):
        return ambito + "testo:(" + f" {op} ".join(f'"{r}"*' if not r.isdigit() else f'"{r}"' for r in rad) + ")"

    trovati: dict[tuple, tuple[dict, int, float]] = {}
    tentativi = ((radici, "AND"), (radici[:5], "AND")) + (() if solo_and else ((radici, "OR"),))
    for rad, op in tentativi:
        for db, origine in _db_ordinati(m):
            for file, testo, rank in _righe(db, _match(rad, op), 40):
                e = m._estremi(file)
                if "articolo" not in e:
                    continue
                chiave = (e.get("tipo"), e.get("anno"), e.get("numero"), m._norm_art(e.get("articolo")))
                if chiave in trovati:
                    continue                                   # già dato dal supplemento (versione più recente)
                chiaro = m._clean_testo(testo) or ""
                t = chiaro.lower()
                punti = sum(1 for r in radici if r in t)
                rub = _rubrica(chiaro).lower()
                punti += 2 * sum(1 for r in radici if r and not r.isdigit() and r in rub)       # la rubrica dice di cosa tratta l'articolo
                trovati[chiave] = ({**e, "raw": testo, "origine_db": origine}, punti, rank)
        if len(trovati) >= limite:
            break
    ordinati = sorted(trovati.values(), key=lambda x: (-x[1], x[2]))
    return [(r, p) for r, p, _ in ordinati[:limite]]


# ── interfaccia ──────────────────────────────────────────────────────────────────────────────────────────
def cerca(query: str = "", norma: str = "", articolo: str = "", comma: str = "", limite: int = 4) -> dict:
    """{'risultati': [scheda…], 'avviso': str}. Riferimento esatto se norma+articolo (o scritti nella query), altrimenti ricerca testuale."""
    m = _modulo()
    if not m or not N.disponibile():
        return {"risultati": [], "avviso": "Il database normativo non è raggiungibile in questo momento."}
    limite = max(1, min(int(limite or 4), 6))
    testo_rif = " ".join(x for x in (norma, (f"art. {articolo}" if articolo else ""), (f"comma {comma}" if comma else ""), query) if x)
    refs = [r for r in m.extract_norm_refs(testo_rif)]
    risultati, avvisi, usati = [], [], set()
    parole = [w for w in N._parole_chiave(query)] or _radici(query)
    for r in refs:
        if not r.get("articolo"):
            continue
        rec = _leggi(m, int(r["anno"]), str(r["numero"]), r["articolo"], r.get("tipo"))
        if rec:
            usati.add((rec.get("tipo"), rec.get("anno"), rec.get("numero"), m._norm_art(rec.get("articolo"))))
            sch = _scheda(m, rec, r.get("comma") or comma or None, parole, "riferimento esatto", query)
            risultati.append(sch)
            if sch["avviso"]:
                avvisi.append(sch["avviso"])
        else:
            avvisi.append(f"Articolo {r['articolo']} di {r.get('label') or 'la norma indicata'}: NON presente nel database consultato.")
    if len(risultati) < limite:
        ref_norma = next((r for r in refs), None)
        for rec, _p in _cerca_testo(m, query or " ".join(parole), ref_norma, limite):
            k = (rec.get("tipo"), rec.get("anno"), rec.get("numero"), m._norm_art(rec.get("articolo")))
            if k in usati:
                continue
            usati.add(k)
            risultati.append(_scheda(m, rec, None, parole, "ricerca per parole", query))
            if len(risultati) >= limite:
                break
    if not risultati and not avvisi:
        avvisi.append("Nessun articolo trovato per questa ricerca: non risulta nel database consultato.")
    return {"risultati": risultati, "avviso": " ".join(avvisi)}


@functools.lru_cache(maxsize=512)
def versione_e_note(anno: int, numero: str, articolo: str, tipo: Optional[str] = None, comma: Optional[str] = None) -> tuple[str, str]:
    """(versione, note di aggiornamento) dell'articolo, per il pacchetto automatico. ('', '') se non si legge."""
    m = _modulo()
    rec = _leggi(m, anno, numero, articolo, tipo) if m else None
    if not rec:
        return "", ""
    return versione(rec["raw"], rec.get("origine_db", "")), note_di_aggiornamento(m._clean_testo(rec["raw"]), comma)


def candidati_testuali(quesito: str, candidati: list, limite: int = 3) -> list[dict]:
    """Riferimenti (tipo, anno, numero, articolo) che la DOMANDA indica con le sue parole, per il pacchetto automatico: prima nella norma più
    presente fra i candidati già noti, poi su tutto il corpus. Escludono ciò che c'è già."""
    m = _modulo()
    if not m or not (quesito or "").strip():
        return []
    gia = {(r.get("tipo"), int(r.get("anno") or 0), str(r.get("numero")), m._norm_art(r.get("articolo"))) for r, _o in candidati}
    norme = {}
    for r, _o in candidati:
        k = (r.get("tipo"), int(r.get("anno") or 0), str(r.get("numero")))
        norme[k] = norme.get(k, 0) + 1
    if not norme:
        return []                                      # nessuna norma indicata: niente ricerca lessicale libera sul corpus
    t, a, n = max(norme, key=norme.get)
    out: list[dict] = []
    for ambito in ({"tipo": t, "anno": a, "numero": n},):
        for rec, punti in _cerca_testo(m, quesito, ambito, limite + 2, solo_and=True):
            k = (rec.get("tipo"), rec.get("anno"), str(rec.get("numero")), m._norm_art(rec.get("articolo")))
            if k in gia or punti < 3:
                continue                               # almeno tre punti (radici della domanda, doppie se nella rubrica)
            gia.add(k)
            out.append({"tipo": rec.get("tipo"), "anno": rec.get("anno"), "numero": str(rec.get("numero")), "articolo": str(rec.get("articolo"))})
            if len(out) >= limite:
                return out
    return out


def _fonte_pacchetto(s: dict) -> N.Fonte:
    return N.Fonte(citazione=s["citazione"], tipo=s["tipo"] or "", anno=int(s["anno"] or 0), numero=str(s["numero"] or ""),
                   articolo=s["articolo"], rubrica=s["rubrica"], sigla=s["sigla"], origine="strumento", testo=s["testo"],
                   note="", avviso="", versione=s["versione"], aggiornamenti=s["note"])


def _registra_nel_pacchetto(risultati: list[dict]) -> None:
    """I risultati dello strumento entrano nel pacchetto del turno: le citazioni che ne derivano restano consentite (norma_guard) e i
    numeri del testo di legge risultano «fondati»."""
    p = N.pacchetto_corrente()
    if p is None:
        return
    noti = {(str(f.numero), f.anno, N._norm_art(f.articolo)) for f in p.fonti}
    for s in risultati:
        k = (str(s["numero"]), int(s["anno"] or 0), N._norm_art(s["articolo"]))
        if k in noti:
            continue
        f = _fonte_pacchetto(s)
        p.fonti.append(f)
        corpo = f.testo + " " + f.note
        p.numeri |= N.numeri_nel_testo(corpo)
        p.coppie |= N.coppie_nel_testo(corpo)
        p.importi |= N.importi_nel_testo(corpo)
        noti.add(k)


def formatta(esito: dict, n_consultazione: int) -> str:
    r = esito["risultati"]
    righe = [f"RISULTATI di cerca_norma (consultazione n. {n_consultazione}) — database normativo Normattiva"]
    for i, s in enumerate(r, 1):
        titolo = f"[{i}] {s['citazione'] or s['sigla']}" + (f", comma {s['comma']}" if s["comma"] else "") + (f" — {s['rubrica']}" if s["rubrica"] else "")
        righe.append(titolo)
        righe.append(f"  Fonte: {s['fonte'] or 'corpus'} · {s['versione']} · trovato per: {s['origine']}")
        righe.append(s["testo"])
        if s["note"]:
            righe.append("  Modifiche successive: " + s["note"])
    if esito["avviso"]:
        righe.append("AVVISO: " + esito["avviso"])
    if not r:
        righe.append("Non ricostruire il testo a memoria: dì all'utente che non l'hai trovato nel database.")
    return "\n".join(righe)


def esegui(args: dict) -> str:
    """Esecuzione dello strumento `cerca_norma` richiesto dal modello. Non solleva."""
    try:
        a = args if isinstance(args, dict) else {}
        esito = cerca(str(a.get("query") or ""), str(a.get("norma") or ""), str(a.get("articolo") or ""), str(a.get("comma") or ""))
        lista = _CONSULTAZIONI.get()
        if lista is not None:
            lista.append({"query": str(a.get("query") or "")[:120], "norma": str(a.get("norma") or ""), "articolo": str(a.get("articolo") or ""),
                          "comma": str(a.get("comma") or ""), "trovati": [s["sigla"] for s in esito["risultati"]]})
        _registra_nel_pacchetto(esito["risultati"])
        return formatta(esito, len(lista) if lista is not None else 1)
    except Exception:
        log.warning("cerca_norma: esecuzione fallita (fail-open)", exc_info=True)
        return "[cerca_norma non riuscita: non hai potuto consultare il database; non dichiarare di averlo fatto]"


# ── il modello non deve dire di aver interrogato un database che non ha interrogato ──────────────────────
_DICHIARA = re.compile(
    r"\b(?:ho|abbiamo|sto)\s+(?:appena\s+|già\s+)?(?:interrogat[oa]|consultat[oa]|cercat[oa]|verificat[oa]|controllat[oa]|query(?:ato)?)\s+"
    r"(?:nel\s+|il\s+|sul\s+|nella\s+|la\s+|l['’]\s*)?(?:database|data\s?base|banca\s+dati|archivio)(?:\s+(?:normativ\w+|di\s+legg\w+|ufficiale|Normattiva))*", re.I)


def correggi_dichiarazioni(testo: str) -> str:
    """Se in questo turno `cerca_norma` NON è stato chiamato, «ho interrogato/consultato il database» diventa «ho letto l'estratto di fonti che
    mi è stato fornito»: il blocco automatico non è una consultazione del database."""
    if not testo or consultazioni():
        return testo
    return _DICHIARA.sub("ho letto l'estratto di fonti normative che mi è stato fornito", testo)
