"""Titoli brevi delle conversazioni («Ammortamento computer», «Ritardi dipendente»).

Prima il titolo era la prima frase dell'utente tagliata a 48 caratteri («Abbiamo comprato un computer da 2.500 euro
per l»). Qui: una chiamata corta al modello (temperatura 0, ≈15 token) UNA volta per conversazione, con riserva
deterministica (le prime parole significative) se il modello non risponde o risponde con un titolo generico.
KBOT_TITOLI_LLM=0 usa solo la riserva.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

log = logging.getLogger(__name__)

MAX_PAROLE = 5
MAX_CARATTERI = 48
GENERICI = re.compile(r"^(nuova (?:chat|conversazione|pratica)|richiesta(?: di)? assistenza|domanda aziendale|"
                      r"domanda|richiesta|conversazione|chat|pratica|consulenza|assistenza|senza titolo)$", re.I)
_STOP = set("""a ad al allo alla ai agli alle anche ancora che chi ci come con contro cosa cui da dal dallo dalla dai dagli dalle
degli dei del dell dello della delle di dopo e ed è ho hai ha abbiamo avete hanno era ero fa fare far gli ha i il in io
la le lo loro lui lei ma mi mio mia miei mie molto ne nel nello nella nei negli nelle noi non nostro nostra nostri nostre
o per più poi può posso possiamo possono potrei potremmo quale quali quando quanto quanti quanta quante questo questa
questi queste se si sia siamo sono su sul sullo sulla sui sugli sulle suo sua tra tuo tua un uno una vi voi vorrei
volevo vogliamo vuole voglio devo dobbiamo deve devono sto sta stiamo stanno stato fatto fatta fatti fatte ora adesso
oggi ieri qui lì là così già solo sempre mai meno tutto tutti tutte tutta ogni altro altra altri altre stesso stessa
cosa cose modo volta volte caso per favore grazie salve buongiorno buonasera ciao""".split())


def pulisci(titolo: str) -> Optional[str]:
    """Titolo ripulito (senza virgolette né punto finale, al massimo 5 parole e 48 caratteri), o None se generico/vuoto."""
    t = re.sub(r"\s+", " ", str(titolo or "")).strip().strip("\"'«»“”‘’`*#").strip()
    t = re.sub(r"^(?:titolo|oggetto)\s*:\s*", "", t, flags=re.I).strip(" .:;,-–—")
    if not t or GENERICI.match(t):
        return None
    parole = t.split(" ")[:MAX_PAROLE]
    t = " ".join(parole)
    if len(t) > MAX_CARATTERI:
        t = t[:MAX_CARATTERI].rsplit(" ", 1)[0]
    t = t.strip(" .:;,-–—")
    return (t[:1].upper() + t[1:]) if t and not GENERICI.match(t) else None


def titolo_di_riserva(testo: str) -> str:
    """Le prime parole significative della prima frase («Abbiamo comprato un computer da 2.500 euro…» → «Comprato computer 2.500 euro»)."""
    frase = re.split(r"[.?!](?:\s|$)|\n", re.sub(r"\s+", " ", str(testo or "")).strip(), maxsplit=1)[0]
    parole = [p for p in re.findall(r"[\wàèéìòù.,%€/-]+", frase) if p.lower().strip(".,") not in _STOP]
    t = pulisci(" ".join(parole[:4]))
    return t or "Nuova pratica"


_SISTEMA = (
    "Dai un titolo breve (da 2 a 5 parole, in italiano, senza punto finale) all'argomento principale di questa "
    "domanda di un'azienda. Il titolo nomina la cosa concreta, non la frase dell'utente.\n"
    "Esempi: «Modifiche gratuite a un progetto» → Modifiche contrattuali; «Abbiamo comprato un computer da 2.500 euro, "
    "conviene ammortizzarlo?» → Ammortamento computer; «Il server è lento quando lavoriamo in tanti» → Server aziendale "
    "lento; «Un dipendente arriva spesso in ritardo» → Ritardi dipendente; «Una fattura scaduta da tre mesi» → "
    "Recupero fattura.\nNon usare titoli generici come «Nuova conversazione», «Richiesta assistenza», «Domanda "
    "aziendale». Rispondi SOLO con il titolo."
)


def genera(client, modello: str, testo: str, timeout: float = 10.0) -> str:
    """Il titolo per `testo`: dal modello se possibile, altrimenti la riserva. Non solleva mai."""
    riserva = titolo_di_riserva(testo)
    if os.getenv("KBOT_TITOLI_LLM", "1") == "0" or len((testo or "").strip()) < 8:
        return riserva
    try:
        base = dict(model=modello, max_tokens=30, system=_SISTEMA,
                    messages=[{"role": "user", "content": str(testo).strip()[:1200]}], timeout=timeout)
        try:
            r = client.messages.create(**base, extra_body={"temperature": 0})
        except Exception as e:
            if isinstance(e, TypeError) or getattr(e, "status_code", None) in (400, 422):
                r = client.messages.create(**base)
            else:
                raise
        out = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return pulisci(out.strip().splitlines()[0] if out.strip() else "") or riserva
    except Exception:
        log.warning("titoli: generazione fallita, uso la riserva", exc_info=True)
        return riserva
