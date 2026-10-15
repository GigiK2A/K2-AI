#!/usr/bin/env python3
"""Banco di prova della chat K-BOT (fase 0 dello studio sulla struttura).

Lancia i casi di `casi.json` contro un servizio K-BOT in esecuzione, controlla le
risposte con `checks.py` e scrive un rapporto ripetibile. Solo libreria standard.

    python3 evals/run_eval.py --base-url https://www.k2-ai.it/api/kbot \
        --modello "qwen-test" --etichetta base-2026-10-15

Il base URL è OBBLIGATORIO: ogni caso crea sessioni anonime sul servizio e usa il
modello vero, quindi non si parte mai contro la produzione per default.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checks as C  # noqa: E402

# Il WAF di Cloudflare blocca lo user-agent di python-urllib.
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def _post(base: str, path: str, body: dict, timeout: int):
    req = urllib.request.Request(
        base.rstrip("/") + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout)


def nuova_sessione(base: str) -> str:
    with _post(base, "/session", {}, 60) as r:
        return json.load(r)["session_id"]


def turno(base: str, sid: str, testo: str, timeout: int) -> dict:
    """Un turno in streaming. Registra testo streamato, testo finale, tempi, errori."""
    t0 = time.time()
    streamato, finale, errori, primo, done = [], None, [], None, None
    try:
        with _post(base, "/message/stream", {"session_id": sid, "message": testo}, timeout) as r:
            for raw in r:
                riga = raw.decode("utf-8", "replace").rstrip("\n")
                if not riga.startswith("data:"):
                    continue
                ev = json.loads(riga[5:].strip())
                if "delta" in ev:
                    primo = primo if primo is not None else time.time() - t0
                    streamato.append(ev["delta"])
                if "error" in ev:
                    errori.append(ev["error"])
                if ev.get("done"):
                    done = ev
                    finale = ev.get("message")
        eccezione = None
    except urllib.error.HTTPError as e:
        eccezione = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:120]}"
    except Exception as e:  # rete, timeout, JSON
        eccezione = repr(e)[:160]
    return {"utente": testo, "streamato": "".join(streamato), "visibile": finale,
            "latenza_s": round(time.time() - t0, 1),
            "primo_token_s": round(primo, 1) if primo is not None else None,
            "errori": errori, "eccezione": eccezione, "completato": done is not None}


def valuta(caso: dict, ultimo: dict, budget: dict) -> dict:
    """Esito dei controlli sull'ultimo turno. {nome: (ok, dettaglio)}."""
    testo = ultimo.get("visibile") or ""
    gen = {
        "risposta_non_vuota": C.risposta_non_vuota(testo),
        "nessuna_lingua_estranea": C.nessuna_lingua_estranea(testo),
        "frasi_integre": C.frasi_integre(testo),
        "nessuna_autocorrezione": C.nessuna_autocorrezione(testo),
        "nessun_testo_del_critico": C.nessun_testo_del_critico(testo),
        "nessuna_fuga_prompt": C.nessuna_fuga_prompt(testo),
        "testo_letto_uguale_finale": C.testo_letto_uguale_finale(ultimo.get("streamato"), testo),
        "nessun_errore_di_stream": C.nessun_errore_di_stream(ultimo.get("errori"), ultimo.get("eccezione")),
    }
    att, spec = caso.get("attese") or {}, {}
    if att.get("tutti"):
        spec["fatti_presenti"] = C.attese_tutti(testo, att["tutti"])
    if att.get("una_di"):
        spec["fatti_alternativi"] = C.attese_una_di(testo, att["una_di"])
    if att.get("nessuno"):
        spec["nessuna_affermazione_errata"] = C.attese_nessuno(testo, att["nessuno"])
    if att.get("escalation"):
        spec["rinvio_al_professionista"] = C.escalation(testo, att["escalation"])
    if att.get("non_spinge_vendita"):
        spec["non_spinge_vendita"] = C.non_spinge_vendita(testo)
    perf = {
        "latenza_entro_budget": C.entro_budget(ultimo.get("latenza_s"), budget["latenza"], "latenza"),
        "primo_token_entro_budget": C.entro_budget(ultimo.get("primo_token_s"), budget["primo_token"], "primo token"),
    }
    return {"generici": gen, "specifici": spec, "prestazioni": perf}


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=os.path.dirname(os.path.abspath(__file__)), timeout=5).stdout.strip()
    except Exception:
        return ""


def _pct(v, n):
    return f"{(100 * v / n):.0f}%" if n else "n/d"


def _percentile(valori, p):
    v = sorted(x for x in valori if x is not None)
    return v[min(len(v) - 1, int(len(v) * p))] if v else None


def riepilogo(risultati: list[dict]) -> dict:
    """Numeri aggregati. 'specifici' contano solo i casi con fonte verificata."""
    n = len(risultati)
    gen_tot = gen_ok = 0
    spec_tot = spec_ok = 0
    casi_ok_gen = casi_ok_spec = casi_con_spec = 0
    for r in risultati:
        g = r["esito"]["generici"]
        gen_tot += len(g)
        gen_ok += sum(1 for ok, _ in g.values() if ok)
        casi_ok_gen += all(ok for ok, _ in g.values())
        s = r["esito"]["specifici"]
        if s:
            casi_con_spec += 1
            spec_tot += len(s)
            spec_ok += sum(1 for ok, _ in s.values() if ok)
            casi_ok_spec += all(ok for ok, _ in s.values())
    per_controllo: dict[str, list[int]] = {}
    for r in risultati:
        for gruppo in ("generici", "specifici"):
            for nome, (ok, _) in r["esito"][gruppo].items():
                a = per_controllo.setdefault(f"{gruppo}.{nome}", [0, 0])
                a[0] += bool(ok)
                a[1] += 1
    lat = [r["turni"][-1].get("latenza_s") for r in risultati]
    ft = [r["turni"][-1].get("primo_token_s") for r in risultati]
    return {
        "casi": n,
        "casi_senza_difetti_generici": casi_ok_gen,
        "casi_con_attese_specifiche": casi_con_spec,
        "casi_con_attese_tutte_rispettate": casi_ok_spec,
        "controlli_generici": f"{gen_ok}/{gen_tot}",
        "controlli_specifici": f"{spec_ok}/{spec_tot}",
        "per_controllo": {k: f"{a}/{b}" for k, (a, b) in sorted(per_controllo.items())},
        "latenza_s": {"mediana": statistics.median([x for x in lat if x is not None] or [0]),
                      "p90": _percentile(lat, 0.9), "max": max([x for x in lat if x is not None] or [0])},
        "primo_token_s": {"mediana": statistics.median([x for x in ft if x is not None] or [0]),
                          "p90": _percentile(ft, 0.9), "max": max([x for x in ft if x is not None] or [0])},
    }


def stampa(risultati: list[dict], riep: dict):
    print(f"\n{'caso':34} {'gen':>5} {'spec':>6}  note")
    for r in risultati:
        g, s = r["esito"]["generici"], r["esito"]["specifici"]
        go = sum(ok for ok, _ in g.values())
        so = sum(ok for ok, _ in s.values())
        note = [f"{n}: {d}" for gr in (g, s) for n, (ok, d) in gr.items() if not ok and d][:2]
        print(f"{r['id']:34} {go}/{len(g):<3} {(str(so) + '/' + str(len(s))) if s else '-':>6}  {' | '.join(note)[:150]}")
    print("\n== riepilogo ==")
    print(json.dumps({k: v for k, v in riep.items() if k != "per_controllo"}, ensure_ascii=False, indent=1))
    print("\nper controllo (ok/totale):")
    for k, v in riep["per_controllo"].items():
        print(f"  {k:55} {v}")


def rivaluta(a, casi):
    """Rilegge un file di risultati e ricalcola gli esiti con i controlli e i casi ATTUALI."""
    per_id = {c["id"]: c for c in casi}
    dati = json.load(open(a.rivaluta, encoding="utf-8"))
    budget = dati.get("meta", {}).get("budget") or {"latenza": a.budget_latenza, "primo_token": a.budget_primo_token}
    nuovi = []
    for r in dati["risultati"]:
        c = per_id.get(r["id"])
        if not c:
            print(f"  {r['id']}: caso non più presente in {os.path.basename(a.casi)}, saltato")
            continue
        nuovi.append(dict(r, esito=valuta(c, r["turni"][-1], budget)))
    riep = riepilogo(nuovi)
    stampa(nuovi, riep)
    meta = dict(dati.get("meta", {}), rivalutato_il=dt.datetime.now(dt.timezone.utc).isoformat(),
                rivalutato_da=os.path.basename(a.rivaluta), commit_rivalutazione=_commit())
    out = a.rivaluta.replace(".json", "-rivalutato.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "riepilogo": riep, "risultati": nuovi}, f, ensure_ascii=False, indent=1)
    print(f"\nrivalutato: {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="", help="es. https://www.k2-ai.it/api/kbot (obbligatorio, salvo con --rivaluta)")
    ap.add_argument("--rivaluta", default="", metavar="FILE",
                    help="ricalcola gli esiti da un file di risultati già salvato, SENZA richiamare il modello "
                         "(serve quando si correggono i controlli o le attese)")
    ap.add_argument("--casi", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "casi.json"))
    ap.add_argument("--solo", default="", help="id dei casi separati da virgola")
    ap.add_argument("--veloci", action="store_true", help="salta i casi marcati lento:true (multi-turno)")
    ap.add_argument("--modello", default="", help="etichetta libera del modello provato")
    ap.add_argument("--etichetta", default="", help="nome del file di risultati")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "risultati"))
    ap.add_argument("--budget-latenza", type=float, default=90.0)
    ap.add_argument("--budget-primo-token", type=float, default=20.0)
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--pausa", type=float, default=1.0, help="secondi fra un caso e l'altro")
    ap.add_argument("--strict", action="store_true", help="exit 1 se un caso con attese fallisce")
    a = ap.parse_args()

    casi = json.load(open(a.casi, encoding="utf-8"))["casi"]
    if a.rivaluta:
        return rivaluta(a, casi)
    if not a.base_url:
        ap.error("--base-url è obbligatorio (salvo con --rivaluta)")
    solo = {x.strip() for x in a.solo.split(",") if x.strip()}
    casi = [c for c in casi if (not solo or c["id"] in solo) and not (a.veloci and c.get("lento"))]
    budget = {"latenza": a.budget_latenza, "primo_token": a.budget_primo_token}
    print(f"{len(casi)} casi su {a.base_url} (modello: {a.modello or 'n/d'})", flush=True)

    risultati = []
    for c in casi:
        try:
            sid = nuova_sessione(a.base_url)
        except Exception as e:
            print(f"{c['id']}: sessione non creata ({e!r})", flush=True)
            continue
        turni = []
        for t in c["turni"]:
            turni.append(turno(a.base_url, sid, t, a.timeout))
            if turni[-1]["eccezione"]:
                break
        esito = valuta(c, turni[-1], budget)
        risultati.append({"id": c["id"], "dominio": c.get("dominio"), "stato": c.get("stato"),
                          "session_id": sid, "turni": turni, "esito": esito})
        ok_g = all(ok for ok, _ in esito["generici"].values())
        ok_s = all(ok for ok, _ in esito["specifici"].values()) if esito["specifici"] else None
        print(f"  {c['id']:34} {turni[-1]['latenza_s']:>6}s  generici={'ok' if ok_g else 'NO'}  "
              f"specifici={'-' if ok_s is None else ('ok' if ok_s else 'NO')}", flush=True)
        time.sleep(a.pausa)

    riep = riepilogo(risultati)
    stampa(risultati, riep)

    os.makedirs(a.out, exist_ok=True)
    nome = a.etichetta or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    percorso = os.path.join(a.out, re.sub(r"[^\w.-]", "_", nome) + ".json")
    meta = {"data": dt.datetime.now(dt.timezone.utc).isoformat(), "base_url": a.base_url,
            "modello": a.modello, "commit": _commit(), "file_casi": os.path.basename(a.casi),
            "budget": budget,
            "sessioni_create": [r["session_id"] for r in risultati]}
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "riepilogo": riep, "risultati": risultati}, f, ensure_ascii=False, indent=1)
    print(f"\nrisultati: {percorso}")
    print(f"sessioni anonime create: {len(meta['sessioni_create'])} (id nel file, per la pulizia)")

    if a.strict and any(not all(ok for ok, _ in r["esito"]["specifici"].values())
                        for r in risultati if r["esito"]["specifici"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
