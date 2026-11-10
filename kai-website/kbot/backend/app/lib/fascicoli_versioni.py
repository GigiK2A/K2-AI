"""Versionamento, deduplicazione, storico e consolidamento dei record dei fascicoli (audit 8).

Tre dimensioni DISTINTE su ogni record (mai un solo booleano):
  * `stato_record`  (asse temporale): attuale · da_verificare · superata · contestata · archiviata
  * `verifica`      (asse della fonte): non_verificato · verificato (fonte esterna) · confermato (soggetto autorizzato)
  * `origine`       (come è stato acquisito): letto_da_documento · dichiarato_utente · calcolato · verificato_esterno · confermato_autorizzato
Nulla si cancella: un valore sostituito diventa «superata» con `valido_fino`; si può sapere cosa era valido a una data.
Un valore diverso NON sovrascrive: nasce una proposta («da_verificare», `sostituisce` = record corrente) che l'utente conferma.
Ogni modifica scrive un evento (prima/dopo/motivo/attore) — anche il consolidamento dei duplicati, che archivia e si può annullare.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

STATI = ("attuale", "da_verificare", "superata", "contestata", "archiviata")
VERIFICHE = ("non_verificato", "verificato", "confermato")
ORIGINI = ("letto_da_documento", "dichiarato_utente", "calcolato", "verificato_esterno", "confermato_autorizzato")
ATTIVI = ("attuale", "da_verificare", "contestata")     # stati che partecipano a dedup e confronto

_STOP = set("il lo la i gli le un uno una di a da in con su per tra fra e ed o ma che del dello della dei degli delle al allo alla ai agli alle "
            "dal dallo dalla dai dagli dalle nel nello nella nei negli nelle sul sullo sulla sui sugli sulle è sono non si come eur euro "
            "verificato verificata documento sul calcolato aperta confermare conferma riportato riportata dichiarato dichiarata".split())


def _F():
    from . import fascicoli
    return fascicoli


def _ora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── normalizzazione ────────────────────────────────────────────────────────────────────────────────────
def _fold(t: Any) -> str:
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9.,% ]+", " ", t)).strip()


def numeri(s: Any) -> List[float]:
    """Importi/numeri di un testo, in forma italiana (1.234,56) e semplice (15250)."""
    out = []
    for m in re.finditer(r"\d[\d.]*(?:,\d+)?", str(s or "")):
        t = m.group(0).rstrip(".,")
        t = t.replace(".", "").replace(",", ".") if "," in t or re.search(r"\.\d{3}(?!\d)", t) else t
        try:
            out.append(round(float(t), 2))
        except ValueError:
            pass
    return out


def parole(s: Any) -> set:
    return {w for w in re.findall(r"[a-z]{3,}", _fold(s)) if w not in _STOP}


def _vuoto(x: Any) -> str:
    return _fold(x) if x not in (None, "") else ""


def stato_di(v: dict) -> str:
    s = v.get("stato_record")
    if s in STATI:
        return s
    return "contestata" if v.get("verifica") == "contraddittorio" else "attuale"


def origine_di(v: dict) -> str:
    o = v.get("origine")
    if o in ORIGINI:
        return o
    t = str(v.get("testo") or "")
    if t.upper().startswith("CALCOLATO"):
        return "calcolato"
    return "letto_da_documento" if (v.get("fonte") or {}).get("origine") in ("documento",) else "dichiarato_utente"


def fonti_di(v: dict) -> List[dict]:
    f = v.get("fonti")
    if isinstance(f, list) and f:
        return f
    return [v["fonte"]] if v.get("fonte") else []


def firma(v: dict) -> str:
    """Chiave di deduplicazione: stesso tipo, campo, unità, periodo e contesto. Senza `chiave` si usano le parole significative."""
    campo = _fold(v.get("chiave")) or ("w:" + "-".join(sorted(parole(v.get("testo")))[:8]))
    return "|".join([str(v.get("tipo") or "dato"), campo, _vuoto(v.get("unita")), _vuoto(v.get("periodo")), _vuoto(v.get("contesto"))])


def stesso_valore(a: dict, b: dict) -> bool:
    na, nb = numeri(a.get("valore")), numeri(b.get("valore"))
    if na and nb:
        return sorted(na) == sorted(nb)
    va, vb = _fold(a.get("valore")), _fold(b.get("valore"))
    return bool(va) and va == vb


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def equivalenti(a: dict, b: dict) -> bool:
    """Stessa informazione? Con `chiave` in entrambi: stessa firma. Senza: stesso tipo + stessi numeri + parole simili (dati storici)."""
    if a.get("tipo") != b.get("tipo"):
        return False
    if (a.get("chiave") or "") and (b.get("chiave") or ""):
        # l'unità mancante da una parte è un'omissione, non una differenza; periodo e contesto invece distinguono i dati
        u_a, u_b = _vuoto(a.get("unita")), _vuoto(b.get("unita"))
        return (_fold(a.get("chiave")) == _fold(b.get("chiave")) and _vuoto(a.get("periodo")) == _vuoto(b.get("periodo"))
                and _vuoto(a.get("contesto")) == _vuoto(b.get("contesto")) and (not u_a or not u_b or u_a == u_b))
    if _vuoto(a.get("periodo")) != _vuoto(b.get("periodo")) or _vuoto(a.get("contesto")) != _vuoto(b.get("contesto")):
        return False
    na, nb = numeri(a.get("valore")), numeri(b.get("valore"))
    j = _jaccard(parole(a.get("testo")), parole(b.get("testo")))
    if na and nb:
        # stessi numeri e valore scritto identico → soglia più bassa (le formulazioni del modello cambiano, il dato no)
        return sorted(na) == sorted(nb) and j >= (0.25 if _fold(a.get("valore")) == _fold(b.get("valore")) else 0.34)
    return stesso_valore(a, b) and j >= 0.5


# ── eventi ─────────────────────────────────────────────────────────────────────────────────────────────
def evento(uid: str, fid: str, voce_id: Optional[str], azione: str, prima: Any = None, dopo: Any = None, motivo: str = "", attore: str = "sistema") -> str:
    r = _F()._db().table("kbot_fascicolo_eventi").insert({"fascicolo_id": fid, "user_id": uid, "voce_id": voce_id, "azione": azione, "prima": prima,
                                                           "dopo": dopo, "motivo": motivo or None, "attore": attore}).execute().data[0]
    return str(r["id"])


def _upd(uid: str, vid: str, patch: dict) -> None:
    _F()._db().table(_F().T_VOCI).update({**patch, "updated_at": _ora()}).eq("id", vid).eq("user_id", uid).execute()


def _snap(v: dict) -> dict:
    return {k: v.get(k) for k in ("id", "stato_record", "verifica", "valore", "valido_fino", "sostituita_da", "fonti", "motivo", "origine")}


# ── inserimento con deduplicazione ─────────────────────────────────────────────────────────────────────
def _chiave_fonte(f: dict) -> Tuple:
    return (f.get("doc"), f.get("pag"), f.get("quote"), f.get("origine") if not f.get("doc") else None)


def inserisci(ctx, fid: str, v: dict, esistenti: List[dict], attore: str = "modello") -> dict:
    """Una voce in ingresso: duplicato (A/C), proposta di aggiornamento (B) o record nuovo. Non solleva per dati strani."""
    uid = ctx.user_id
    F = _F()
    testo = str(v.get("testo") or "").strip()[:600]
    if not testo:
        return {"esito": "ignorata"}
    fonte: Dict[str, Any] = {"session_id": ctx.session_id}
    for k in ("doc", "pag", "quote", "doc_versione"):
        if v.get(k) not in (None, ""):
            fonte[k] = v[k]
    org = v.get("origine") if v.get("origine") in ("letto_da_documento", "dichiarato_utente", "calcolato") else None
    org = org or ("letto_da_documento" if v.get("doc") else "dichiarato_utente")
    fonte["origine"] = "documento" if org == "letto_da_documento" else ("calcolo" if org == "calcolato" else "utente")
    nuova = {"tipo": v.get("tipo") if v.get("tipo") in F.TIPI_VOCE else "dato", "chiave": (str(v.get("chiave") or "").strip().casefold() or None),
             "testo": testo, "valore": str(v.get("valore") or "").strip()[:120] or None, "unita": (str(v.get("unita") or "").strip() or None),
             "periodo": (str(v.get("periodo") or "").strip() or None), "contesto": (str(v.get("contesto") or "").strip()[:120] or None)}
    attivi = [e for e in esistenti if stato_di(e) in ATTIVI]
    for e in attivi:
        if not equivalenti(nuova, e):
            continue
        if stesso_valore(nuova, e) or not (nuova["valore"] and e.get("valore")):
            fonti = fonti_di(e)
            if any(_chiave_fonte(f) == _chiave_fonte(fonte) for f in fonti) or not (fonte.get("doc") or v.get("pag")) and fonti:
                return {"esito": "duplicato", "id": str(e["id"]), "dettaglio": "già presente con la stessa fonte"}
            nuove = fonti + [fonte]
            _upd(uid, str(e["id"]), {"fonti": nuove})
            e["fonti"] = nuove
            evento(uid, fid, str(e["id"]), "aggiunge_fonte", None, {"fonte": fonte}, "stesso valore da un'altra fonte", attore)
            return {"esito": "fonte_aggiunta", "id": str(e["id"]), "dettaglio": "stesso valore: aggiunta la nuova fonte al record esistente"}
        # stessa informazione, valore diverso → proposta, mai sovrascrittura
        riga = {"fascicolo_id": fid, "user_id": uid, **nuova, "fonte": fonte, "fonti": [fonte], "origine": org, "verifica": "non_verificato",
                "stato_record": "da_verificare", "sostituisce": str(e["id"]), "valido_dal": _ora(), "data_verifica": _ora(), "modificato_da": attore,
                "motivo": str(v.get("motivo") or "valore diverso da quello corrente: in attesa di conferma")[:300], "firma": firma(nuova),
                "doc_versione": str(v.get("doc_versione") or "") or None}
        r = F._db().table(F.T_VOCI).insert(riga).execute().data[0]
        esistenti.append(r)
        evento(uid, fid, str(r["id"]), "propone", _snap(e), {"valore": nuova["valore"], "origine": org}, riga["motivo"], attore)
        return {"esito": "proposta", "id": str(r["id"]), "corrente": str(e["id"]), "dettaglio":
                f"«{e.get('chiave') or e.get('testo', '')[:40]}»: corrente {e.get('valore')} → proposto {nuova['valore']} (non sostituisce finché l'utente conferma)"}
    stato = "da_verificare" if v.get("stato") == "da_verificare" or str(testo).upper().startswith("DA CONFERMARE") else "attuale"
    riga = {"fascicolo_id": fid, "user_id": uid, **nuova, "fonte": fonte, "fonti": [fonte], "origine": org, "verifica": "non_verificato",
            "stato_record": stato, "valido_dal": _ora(), "data_verifica": _ora(), "modificato_da": attore, "firma": firma(nuova),
            "doc_versione": str(v.get("doc_versione") or "") or None, "data_efficacia": v.get("data_efficacia") or None}
    if org == "dichiarato_utente" and not v.get("doc") and attore == "utente":
        riga["verifica"] = "confermato"
    r = F._db().table(F.T_VOCI).insert(riga).execute().data[0]
    esistenti.append(r)
    evento(uid, fid, str(r["id"]), "crea", None, {"valore": nuova["valore"], "stato": stato, "origine": org}, "", attore)
    return {"esito": "creata", "id": str(r["id"]), "dettaglio": ""}


# ── azioni dell'utente sui record (da chiamare solo dopo la conferma) ──────────────────────────────────
def azione(ctx, fid: str, vid: str, act: str, motivo: str = "", attore: str = "modello") -> dict:
    uid = ctx.user_id
    F = _F()
    tutte = F.voci(uid, fid)
    v = next((x for x in tutte if str(x["id"]).startswith(vid) and len(vid) >= 6 or str(x["id"]) == vid), None)
    if not v:
        return {"ok": False, "errore": "record non trovato"}
    vid = str(v["id"])
    ora = _ora()
    if act == "sostituisci":
        old_id = v.get("sostituisce")
        old = next((x for x in tutte if str(x["id"]) == str(old_id)), None)
        if stato_di(v) != "da_verificare" or not old:
            return {"ok": False, "errore": "il record non è una proposta di sostituzione"}
        _upd(uid, str(old["id"]), {"stato_record": "superata", "valido_fino": ora, "sostituita_da": vid, "motivo": motivo or "sostituito da una versione confermata", "modificato_da": attore})
        _upd(uid, vid, {"stato_record": "attuale", "valido_dal": ora, "motivo": motivo or v.get("motivo"), "modificato_da": attore})
        evento(uid, fid, vid, "sostituisce", _snap(old), _snap({**v, "stato_record": "attuale"}), motivo, attore)
        return {"ok": True, "dettaglio": f"«{old.get('valore')}» ora è superato; valore attuale: {v.get('valore')}"}
    if act == "contesta":
        ids = [vid] + ([str(v["sostituisce"])] if v.get("sostituisce") else [])
        for i in ids:
            _upd(uid, i, {"stato_record": "contestata", "motivo": motivo or "discrepanza non risolta", "modificato_da": attore})
        evento(uid, fid, vid, "contesta", None, {"ids": ids}, motivo, attore)
        return {"ok": True, "dettaglio": "record segnati come contestati"}
    if act in ("archivia", "scarta"):
        _upd(uid, vid, {"stato_record": "archiviata", "valido_fino": ora, "motivo": motivo or ("proposta scartata" if act == "scarta" else "archiviato"), "modificato_da": attore})
        evento(uid, fid, vid, "archivia", _snap(v), None, motivo, attore)
        return {"ok": True, "dettaglio": "record archiviato (resta nello storico)"}
    if act == "conferma":
        _upd(uid, vid, {"verifica": "confermato", "modificato_da": attore, "motivo": motivo or v.get("motivo")})
        evento(uid, fid, vid, "conferma", _snap(v), {"verifica": "confermato"}, motivo, attore)
        return {"ok": True, "dettaglio": "confermato da un soggetto autorizzato"}
    if act == "verifica_esterna":
        _upd(uid, vid, {"verifica": "verificato", "origine": "verificato_esterno" if origine_di(v) != "letto_da_documento" else origine_di(v), "modificato_da": attore, "motivo": motivo or v.get("motivo")})
        evento(uid, fid, vid, "verifica_esterna", _snap(v), {"verifica": "verificato"}, motivo, attore)
        return {"ok": True, "dettaglio": "verificato su fonte esterna"}
    return {"ok": False, "errore": "azione sconosciuta"}


# ── storico e valore a una data ────────────────────────────────────────────────────────────────────────
def _catena(tutte: List[dict], base: dict) -> List[dict]:
    ids = {str(base["id"])}
    cambiato = True
    while cambiato:
        cambiato = False
        for x in tutte:
            if str(x["id"]) in ids:
                continue
            if str(x.get("sostituisce") or "") in ids or str(x.get("sostituita_da") or "") in ids or any(str(i) == str(x.get("sostituisce") or "") for i in ids):
                ids.add(str(x["id"])); cambiato = True
    sim = [x for x in tutte if str(x["id"]) not in ids and equivalenti(base, x) and (base.get("chiave") and x.get("chiave"))]
    return [x for x in tutte if str(x["id"]) in ids] + sim


def storico(uid: str, fid: str, rif: str = "", alla_data: str = "") -> str:
    F = _F()
    tutte = F.voci(uid, fid)
    if alla_data:
        try:
            d = datetime.fromisoformat(alla_data[:10]).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            return "Data non valida (usa AAAA-MM-GG)."
        d = d[:10] + "T23:59:59+00:00"
        vivi = [x for x in tutte if stato_di(x) in ("attuale", "superata", "contestata") and str(x.get("valido_dal") or x.get("created_at") or "") <= d
                and (not x.get("valido_fino") or str(x["valido_fino"]) > d)]
        if rif:
            vivi = [x for x in vivi if rif.casefold() in f"{x.get('chiave') or ''} {x.get('testo') or ''}".casefold() or str(x["id"]).startswith(rif)]
        return (f"Valori considerati validi al {alla_data[:10]}:\n" + "\n".join(riga(x) for x in vivi)) if vivi else f"Nessun valore valido al {alla_data[:10]}."
    base = next((x for x in tutte if str(x["id"]).startswith(rif) and len(rif) >= 6), None)
    if not base and rif:
        c = [x for x in tutte if rif.casefold() in f"{x.get('chiave') or ''} {x.get('testo') or ''} {x.get('valore') or ''}".casefold()]
        base = c[0] if c else None
    if not base:
        return "Record non trovato."
    righe = []
    for x in sorted(_catena(tutte, base), key=lambda r: str(r.get("valido_dal") or r.get("created_at") or "")):
        righe.append(riga(x) + (f" · valido dal {str(x.get('valido_dal') or '')[:10]}" + (f" al {str(x['valido_fino'])[:10]}" if x.get("valido_fino") else "")))
    ev = [e for e in _F()._db().table("kbot_fascicolo_eventi").select("*").eq("user_id", uid).eq("fascicolo_id", fid).execute().data or []
          if str(e.get("voce_id")) in {str(x["id"]) for x in _catena(tutte, base)}]
    ev.sort(key=lambda e: str(e.get("created_at") or ""))
    return "STORICO\n" + "\n".join(righe) + "\nCRONOLOGIA\n" + "\n".join(f"- {str(e.get('created_at'))[:16]} {e.get('azione')} ({e.get('attore')}) {e.get('motivo') or ''}" for e in ev[-15:])


def riga(v: dict) -> str:
    fo = fonti_di(v)
    fonti = "; ".join(("doc " + str(f.get("doc")) + (f" pag. {f.get('pag')}" if f.get("pag") else "")) if f.get("doc") else str(f.get("origine") or "?") for f in fo[:3]) or "nessuna"
    extra = (" ← propone di sostituire " + str(v["sostituisce"])[:8]) if v.get("sostituisce") and stato_di(v) == "da_verificare" else ""
    return (f"- {str(v['id'])[:8]} [{v.get('tipo')}] {v.get('testo')}" + (f" = {v['valore']}" if v.get("valore") else "") +
            f" ({stato_di(v)}; verifica {v.get('verifica') or 'non_verificato'}; origine {origine_di(v)}; fonti: {fonti}){extra}")


# ── confronto fra versioni ─────────────────────────────────────────────────────────────────────────────
def confronta(uid: str, fid: str, nuovi: List[dict], con_documento: bool) -> str:
    F = _F()
    attuali = [x for x in F.voci(uid, fid) if stato_di(x) in ATTIVI]
    out, toccati = [], set()
    for n in nuovi[:40]:
        cand = [e for e in attuali if equivalenti({**n, "tipo": n.get("tipo") or e.get("tipo")}, e)] if n.get("chiave") or n.get("testo") else []
        if not cand:
            out.append(f"+ NUOVO: {n.get('chiave') or n.get('testo')} = {n.get('valore')}")
            continue
        e = cand[0]; toccati.add(str(e["id"]))
        out.append(f"= INVARIATO: {e.get('chiave') or e.get('testo', '')[:50]} = {e.get('valore')}" if stesso_valore(n, e)
                   else f"≠ DIVERSO: {e.get('chiave') or e.get('testo', '')[:50]}: documentato {e.get('valore')} ({str(e['id'])[:8]}) → nuovo {n.get('valore')}")
    assenti = [e for e in attuali if str(e["id"]) not in toccati and e.get("chiave")]
    if assenti and nuovi:
        out.append("- NON PRESENTI nel nuovo (verifica se rimossi o solo omessi): " + ", ".join(str(e.get("chiave")) for e in assenti[:10]))
    out.append("REGOLA: " + ("i valori diversi diventano PROPOSTE da confermare; i record documentati restano validi finché l'utente non conferma." if con_documento else
               "nessun nuovo documento caricato: è una revisione DICHIARATA, i valori restano «da_verificare» e non sostituiscono l'ultima versione documentata."))
    return "CONFRONTO\n" + "\n".join(out)


# ── duplicati e consolidamento ─────────────────────────────────────────────────────────────────────────
_RANGO_ORIGINE = {"confermato_autorizzato": 5, "verificato_esterno": 4, "letto_da_documento": 3, "calcolato": 2, "dichiarato_utente": 1}


def _rango(v: dict) -> Tuple:
    return (stato_di(v) == "attuale", {"confermato": 2, "verificato": 1}.get(v.get("verifica"), 0), _RANGO_ORIGINE.get(origine_di(v), 0),
            len(fonti_di(v)), "".join(chr(255 - ord(c)) if c.isdigit() else c for c in str(v.get("created_at") or "")))


def duplicati(uid: str, fid: str) -> List[dict]:
    vv = [x for x in _F().voci(uid, fid) if stato_di(x) in ATTIVI]
    gruppi: List[List[dict]] = []
    for v in vv:
        for g in gruppi:
            if equivalenti(v, g[0]) and stesso_valore(v, g[0]):
                g.append(v); break
        else:
            gruppi.append([v])
    out = []
    for g in gruppi:
        if len(g) < 2:
            continue
        ref = max(g, key=_rango)
        diff = [f"{str(x['id'])[:8]}: {x.get('testo', '')[:60]}" for x in g if x is not ref and _fold(x.get("testo")) != _fold(ref.get("testo"))]
        out.append({"riferimento": str(ref["id"]), "duplicati": [str(x["id"]) for x in g if x is not ref],
                    "fonti": sum(len(fonti_di(x)) for x in g), "differenze": diff, "membri": g})
    return out


def descrivi_duplicati(gr: List[dict]) -> str:
    if not gr:
        return "Nessun duplicato."
    righe = []
    for i, g in enumerate(gr, 1):
        righe.append(f"Gruppo {i}: tengo {g['riferimento'][:8]}, archivio {', '.join(d[:8] for d in g['duplicati'])} (fonti totali {g['fonti']})")
        righe += [riga(m) for m in g["membri"]]
        if g["differenze"]:
            righe.append("  differenze di formulazione: " + " | ".join(g["differenze"]))
    return "\n".join(righe)


def consolida(ctx, fid: str, riferimenti: Optional[List[str]] = None, attore: str = "modello") -> dict:
    """Archivia i duplicati (non li cancella) unendone le fonti al record di riferimento. Solo per gruppi RICONOSCIUTI dal rilevatore."""
    uid = ctx.user_id
    F = _F()
    fatti = []
    for g in duplicati(uid, fid):
        if riferimenti and not any(g["riferimento"].startswith(r) for r in riferimenti):
            continue
        ref = next(m for m in g["membri"] if str(m["id"]) == g["riferimento"])
        fonti = fonti_di(ref)
        prima = {"ref": _snap(ref), "duplicati": [_snap(m) for m in g["membri"] if str(m["id"]) != g["riferimento"]]}
        for m in g["membri"]:
            if str(m["id"]) == g["riferimento"]:
                continue
            for f in fonti_di(m):
                if not any(_chiave_fonte(x) == _chiave_fonte(f) for x in fonti):
                    fonti = fonti + [f]
            _upd(uid, str(m["id"]), {"stato_record": "archiviata", "valido_fino": _ora(), "motivo": f"duplicato di {g['riferimento'][:8]}", "modificato_da": attore})
        _upd(uid, g["riferimento"], {"fonti": fonti})
        eid = evento(uid, fid, g["riferimento"], "consolida", prima, {"fonti": len(fonti), "archiviati": g["duplicati"]}, "consolidamento duplicati", attore)
        fatti.append({"riferimento": g["riferimento"], "archiviati": g["duplicati"], "evento": eid})
    return {"ok": True, "gruppi": fatti}


def annulla_consolidamento(uid: str, evento_id: str) -> bool:
    F = _F()
    ev = next((e for e in F._db().table("kbot_fascicolo_eventi").select("*").eq("user_id", uid).execute().data or []
               if str(e["id"]) == evento_id and e.get("azione") == "consolida"), None)
    if not ev or not ev.get("prima"):
        return False
    p = ev["prima"]
    for d in p.get("duplicati") or []:
        _upd(uid, str(d["id"]), {"stato_record": d.get("stato_record") or "attuale", "valido_fino": d.get("valido_fino"), "motivo": d.get("motivo")})
    if p.get("ref"):
        _upd(uid, str(p["ref"]["id"]), {"fonti": p["ref"].get("fonti") or []})
    evento(uid, str(ev["fascicolo_id"]), str(ev.get("voce_id")), "annulla", None, {"evento": evento_id}, "annullato il consolidamento", "utente")
    return True
