"""Evidence pack NORMATIVO della chat: il testo di legge entra nel contesto PRIMA della risposta.

Il problema (misurato il 15/10/2026): in chat il modello risponde a memoria. Il corpus Normattiva
(62k articoli) c'è, ma serviva solo a cancellare numeri DOPO. Risultato: «il periodo di prova non è
fissato da una norma», «recesso del socio: la legge non fissa un termine», il limite del contante a
3.000 € letto dal comma sbagliato. Qui si fa il contrario: si RECUPERA la norma e la si mette nel
prompt, con la fonte, e le guardie a valle la riconoscono.

Flusso (per turno, tutto fail-open):
  1. gate: la domanda è di ambito normativo? (niente chiamate sulle chiacchiere)
  2. riferimenti: quelli citati dall'utente + la MAPPA TEMI (dati, da validare) + quelli PROPOSTI da
     una chiamata corta al modello (solo la forma «art. 2473 c.c.», mai la risposta);
  3. recupero PER ESTREMI dal corpus (mai dalla memoria del modello): il riferimento o esiste e
     ritorna il testo vero, o non ritorna nulla;
  4. filtro di pertinenza sui riferimenti proposti dal modello (esistenza ≠ pertinenza);
  5. lettura PER COMMI con la vigenza: nello stesso articolo convivono testo storico e vigente
     (art. 49 D.Lgs. 231/2007: il comma 1 dice ancora 3.000 €, il 3-bis porta il limite a 5.000 € dal
     2023). Si tengono i commi pertinenti e quelli con decorrenza; le note di aggiornamento si tolgono;
  6. pacchetto: blocco di prompt + elenco delle fonti + numeri «fondati» (le guardie non cancellano
     un numero che sta nel testo di legge recuperato).

Il lettore del corpus è `app/normattiva.py` dell'8e, caricato PER PERCORSO: il pacchetto `app`
dell'8e e quello della chat hanno lo stesso nome e non si possono importare insieme.

KBOT_NORME_EVIDENCE=0 spegne tutto. Senza corpus raggiungibile il modulo è inerte.
"""
from __future__ import annotations

import concurrent.futures
import contextvars
import functools
import importlib.util
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import norme_ue

log = logging.getLogger(__name__)

# ── configurazione ───────────────────────────────────────────────────────────────────────
MAX_RIFERIMENTI = int(os.getenv("KBOT_NORME_MAX_RIF", "5"))
MAX_CHARS_ARTICOLO = int(os.getenv("KBOT_NORME_MAX_CHARS_ARTICOLO", "2400"))
MAX_CHARS_TOTALE = int(os.getenv("KBOT_NORME_MAX_CHARS", "7500"))
# Un comma lunghissimo (il comma 1 dell'art. 49 D.Lgs. 231/2007 ha 1.450 caratteri) non deve consumare
# il budget degli altri: si taglia a una frase e si segna «[…]».
MAX_CHARS_COMMA = int(os.getenv("KBOT_NORME_MAX_CHARS_COMMA", "650"))
_TIMEOUT_PROPOSTA = float(os.getenv("KBOT_NORME_TIMEOUT_PROPOSTA", "25"))
_TEMPERATURA = float(os.getenv("KBOT_NORME_TEMPERATURA", "0"))


def abilitato() -> bool:
    return os.getenv("KBOT_NORME_EVIDENCE", "1") != "0"


def _flag(nome: str) -> bool:
    """Funzionalità del pacchetto spegnibili una per una (per isolarle nelle misure)."""
    return os.getenv(nome, "1") != "0"


# ═══ 1 · lettore del corpus (app/normattiva.py dell'8e, caricato per percorso) ═════════════
_LETTORE = None
_LETTORE_PROVATO = False


def _candidati_lettore() -> list[Path]:
    qui = Path(__file__).resolve()
    out: list[Path] = []
    if os.getenv("K2A_NORMATTIVA_MODULE"):
        out.append(Path(os.environ["K2A_NORMATTIVA_MODULE"]))
    for i, nome in ((3, "engine-8e"), (4, "k2a-8e")):          # container / repo
        try:
            out.append(qui.parents[i] / nome / "app" / "normattiva.py")
        except IndexError:
            pass
    return out


def _candidati_db() -> list[Path]:
    qui = Path(__file__).resolve()
    out = [Path("/corpus/normattiva.db")]
    try:
        out.append(qui.parents[3] / "engine-8e" / "normattiva.db")
    except IndexError:
        pass
    return out


def lettore():
    """Il modulo del corpus, o None se non c'è. Nessuna eccezione verso l'alto."""
    global _LETTORE, _LETTORE_PROVATO
    if _LETTORE_PROVATO:
        return _LETTORE
    _LETTORE_PROVATO = True
    for p in _candidati_lettore():
        if not p.is_file():
            continue
        try:
            spec = importlib.util.spec_from_file_location("_k2a_normattiva_8e", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)                      # type: ignore[union-attr]
            _LETTORE = mod
            break
        except Exception:
            log.warning("norme_evidence: lettore %s non caricabile", p, exc_info=True)
    if _LETTORE is not None and not os.environ.get("NORMATTIVA_DB_PATH"):
        for db in _candidati_db():
            if db.is_file():
                os.environ["NORMATTIVA_DB_PATH"] = str(db)
                break
    return _LETTORE


def disponibile() -> bool:
    m = lettore()
    try:
        return bool(m and m.available())
    except Exception:
        return False


# ═══ 2 · numeri in cifre e in parole (per riconoscere i numeri «fondati») ══════════════════
_UNITA = {"uno": 1, "una": 1, "un": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7,
          "otto": 8, "nove": 9}
_SPECIALI = {"dieci": 10, "undici": 11, "dodici": 12, "tredici": 13, "quattordici": 14, "quindici": 15,
             "sedici": 16, "diciassette": 17, "diciotto": 18, "diciannove": 19}
_DECINE = {"venti": 20, "trenta": 30, "quaranta": 40, "cinquanta": 50, "sessanta": 60, "settanta": 70,
           "ottanta": 80, "novanta": 90}


def _genera_parole() -> dict[str, int]:
    """'quaranta' → 40, 'venticinque' → 25, 'centottanta' → 180, 'cinquemila' → 5000."""
    w: dict[str, int] = {}
    w.update(_UNITA)
    w.update(_SPECIALI)
    w.update(_DECINE)
    for d, vd in _DECINE.items():
        for u, vu in _UNITA.items():
            if u == "una" or u == "un":
                continue
            forma = d[:-1] if u in ("uno", "otto") else d      # ventuno, ventotto (elisione)
            w[forma + u] = vd + vu
            w[d + u] = vd + vu
    base = dict(w)
    w["cento"] = 100
    for u, vu in _UNITA.items():
        if u in ("una", "un", "uno"):
            continue
        w[u + "cento"] = vu * 100
    centinaia = {k: v for k, v in w.items() if v % 100 == 0 and 100 <= v <= 900}
    for c, vc in centinaia.items():
        for p, vp in base.items():
            if vp >= 100 or p in ("una", "un"):
                continue
            forma = c[:-1] if p[0] in "ou" else c              # centottanta, centuno
            w[forma + p] = vc + vp
            w[c + p] = vc + vp
    w["mille"] = 1000
    for u, vu in list(_UNITA.items()) + list(_SPECIALI.items()):
        if u not in ("una", "un", "uno"):
            w[u + "mila"] = vu * 1000
    return w


PAROLE_NUMERO = _genera_parole()
_RE_NUM = re.compile(r"\b(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?\b|\b(?:" + "|".join(
    sorted(PAROLE_NUMERO, key=len, reverse=True)) + r")\b", re.I)
_UNITA_TEMPO = r"(giorn\w*|mes[ei]|settiman\w*|ann[io]|or[ae])"
_RE_COPPIA = re.compile(r"(?P<n>\d{1,3}(?:\.\d{3})+|\d+|" + "|".join(sorted(PAROLE_NUMERO, key=len, reverse=True)) +
                        r")\s*(?P<u>" + _UNITA_TEMPO + r")\b", re.I)


def valore(tok: str) -> Optional[int]:
    """'5.000' → 5000, 'quaranta' → 40, '25' → 25, '3,5' → None (non intero)."""
    t = tok.strip().lower()
    if t in PAROLE_NUMERO:
        return PAROLE_NUMERO[t]
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", t):
        return int(t.replace(".", ""))
    if t.isdigit():
        return int(t)
    return None


def _stelo_unita(u: str) -> str:
    return u.lower()[:3]


def numeri_nel_testo(testo: str) -> set[int]:
    out: set[int] = set()
    for m in _RE_NUM.finditer(testo or ""):
        v = valore(m.group(0))
        if v is not None:
            out.add(v)
    return out


# Importi in euro: «516,46 euro», «2.500 €», «euro 5.000». Prima gli importi si verificavano come numeri nudi: «300 €»
# risultava fondato perché «300» compariva per caso altrove nel pacchetto, e i decimali (516,46) non erano registrati.
_NUM_IMPORTO = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"
_RE_IMPORTO = re.compile(r"(?:(?:€|\beuro\b|\beur\b)\s*(?P<a>" + _NUM_IMPORTO + r")|(?P<b>" + _NUM_IMPORTO +
                         r")\s*(?:€|\beuro\b|\beur\b))", re.I)


def _norm_importo(tok: str) -> str:
    """'2.500' → '2500', '516,46' → '516.46', '2.000,00' → '2000'."""
    t = tok.strip().replace(".", "")
    if "," in t:
        intero, dec = t.split(",", 1)
        dec = dec.rstrip("0")
        return intero + ("." + dec if dec else "")
    return t


def importi_nel_testo(testo: str) -> set[str]:
    return {_norm_importo(m.group("a") or m.group("b")) for m in _RE_IMPORTO.finditer(testo or "")}


def coppie_nel_testo(testo: str) -> set[tuple[int, str]]:
    out: set[tuple[int, str]] = set()
    for m in _RE_COPPIA.finditer(testo or ""):
        v = valore(m.group("n"))
        if v is not None:
            out.add((v, _stelo_unita(m.group("u"))))
    return out


# ═══ 3 · modello dei dati e variabile di contesto ═════════════════════════════════════════
@dataclass
class Fonte:
    citazione: str                 # «R.D. 262/1942, art. 2473»
    tipo: str
    anno: int
    numero: str
    articolo: str
    rubrica: str = ""
    sigla: str = ""                # forma breve per l'utente: «c.c. art. 2473»
    origine: str = ""              # utente | mappa | proposta | norma | affine
    testo: str = ""                # ciò che entra nel pacchetto
    note: str = ""                 # modifiche successive che toccano cifre (non incorporate nel testo)
    avviso: str = ""               # «cifra vigente X; la cifra Y del testo è superata» (deterministico)


@dataclass
class Pacchetto:
    testo: str                                         # blocco da aggiungere al prompt di sistema
    fonti: list[Fonte] = field(default_factory=list)
    numeri: set[int] = field(default_factory=set)
    coppie: set[tuple[int, str]] = field(default_factory=set)
    importi: set[str] = field(default_factory=set)


_CORRENTE: contextvars.ContextVar[Optional[Pacchetto]] = contextvars.ContextVar("norme_pacchetto", default=None)


def imposta(p: Optional[Pacchetto]) -> None:
    _CORRENTE.set(p)


def pacchetto_corrente() -> Optional[Pacchetto]:
    return _CORRENTE.get()


# ═══ 4 · riferimenti: utente, mappa temi, proposta del modello ═════════════════════════════
_AMBITO = re.compile(
    r"\b(contratt\w+|clausol\w+|penale|caparra|recess\w+|socio|soci\b|srl|s\.r\.l|quota|quote|statuto|"
    r"assemble\w+|dipendent\w+|lavorator\w+|assunzion\w+|assumer\w+|licenzi\w+|dimission\w+|"
    r"prova|ferie|straordinar\w+|orario|\bccnl\b|tfr|sindacat\w+|appalt\w+|subappalt\w+|"
    r"fattur\w+|iva\b|imposta|imposte|tribut\w+|fiscal\w+|dedu\w+|deduc\w+|irpef|ires|irap|f24|"
    r"ravvedimento|sanzion\w+|cartella|accertament\w+|dichiarazion\w+|versament\w+|contant\w+|"
    r"pagament\w+|interess\w+|mora|creditor\w+|credit\w+|debit\w+|ingiunz\w+|decreto|opposizion\w+|"
    r"impugn\w+|termin\w+|scadenz\w+|prescrizion\w+|decadenz\w+|risarcim\w+|inadempi\w+|"
    r"privacy|gdpr|dati personali|data breach|garante|telecamer\w+|videosorveglianza|"
    r"sicurezza|dvr|infortun\w+|ispezion\w+|norma\b|norme\b|legge\b|obblig\w+|divieto|vietat\w+|"
    r"successione|eredit\w+|locazion\w+|affitto|sfratto|societ\w+|amministrator\w+|liquidazione|"
    r"bilancio|concorrenza|non concorrenza|brevett\w+|marchio|diritto d'autore|antiriciclaggio|"
    r"consumator\w+|garanzia|appalto|subappalto|fornitur\w+)\b", re.I)

_STOP = set("""che con per una uno gli le lo la il del dei della delle dello degli nel nella nei nelle sul sulla sui
sulle dal dalla dai dalle alla alle allo agli ai al da di in su tra fra non più anche come cosa cose fare fatto
fatta abbiamo ho ha hanno essere stato stata sono siamo vogliamo posso possiamo deve devo dobbiamo quando quanto
quale quali questo questa questi queste quello quella quelli loro suo sua suoi nostro nostra nostri nostre mio mia
dopo prima ancora sempre mai molto poco tutto tutti ogni altro altra altri altre solo anche però quindi perché
poi subito entro oggi ieri domani anno anni mese mesi giorno giorni""".split())


_CHITCHAT = re.compile(r"^\s*(?:ciao|salve|buongiorno|buonasera|grazie|ok|va bene|perfetto|capito|certo|si|sì|no|"
                       r"come stai|tutto bene|a presto|arrivederci)\b[^.?!]{0,40}[.?!]*\s*$", re.I)


def serve_evidenza(testo: str, contesto: str = "") -> bool:
    """Si prova a recuperare la norma per OGNI messaggio sostanziale; è la chiamata corta al modello a dire se
    c'è una norma (lista vuota se non c'è). Un tempo il gate era un elenco di parole chiave di ambito
    normativo: scritto guardando i casi di sviluppo, su 8 domande mai viste ne mancava 2 («macchinario»,
    «capannone», «difetto»…) e il pacchetto non partiva. Un elenco di parole è fragile per costruzione;
    qui si scartano solo le chiacchiere e i messaggi troppo corti. KBOT_NORME_GATE=parole ripristina l'elenco."""
    t = (testo or "").strip()
    if len(t) < 25 or len(t.split()) < 4:
        return False
    if os.getenv("KBOT_NORME_GATE", "") == "parole":
        return bool(_AMBITO.search(t) or _AMBITO.search(contesto or "") and len(t) < 80)
    return not _CHITCHAT.match(t)


def _parole_chiave(testo: str) -> list[str]:
    out, visti = [], set()
    for w in re.findall(r"[a-zàèéìòù]{6,}", (testo or "").lower()):
        if w in _STOP or w in visti:
            continue
        visti.add(w)
        out.append(w)
    return out[:14]


def riferimenti_da_testo(testo: str, solo_con_articolo: bool = True) -> list[dict]:
    """Riferimenti con estremi già scritti nel testo («art. 2473 c.c.», «D.Lgs. 231/2002 art. 4»). Con
    solo_con_articolo=False si tengono anche le norme senza articolo («D.Lgs. 276/2003»): il modello debole
    spesso indovina la norma e sbaglia l'articolo, e dentro la norma si può cercare per parole."""
    m = lettore()
    if not m or not testo:
        return []
    try:
        return [r for r in m.extract_norm_refs(testo) if (r.get("articolo") or not solo_con_articolo)]
    except Exception:
        return []


_MAPPA_PATH = Path(__file__).resolve().parent.parent / "data" / "mappa_temi.json"


@functools.lru_cache(maxsize=1)
def _mappa() -> list[dict]:
    try:
        d = json.load(open(_MAPPA_PATH, encoding="utf-8"))
        voci = d.get("temi", []) if isinstance(d, dict) else d
        out = []
        bozze = os.getenv("KBOT_MAPPA_BOZZE", "0") == "1"
        for v in voci:
            # una voce senza professionista che l'abbia validata è una BOZZA: inattiva in produzione
            if isinstance(v, dict) and not (v.get("validato_da") or "").strip() and not bozze:
                continue
            if isinstance(v, dict) and v.get("trigger") and v.get("riferimenti"):
                out.append({"id": v.get("id", ""), "trigger": [re.compile(t, re.I) for t in v["trigger"]],
                            "riferimenti": list(v["riferimenti"])})
        return out
    except FileNotFoundError:
        return []
    except Exception:
        log.warning("norme_evidence: mappa temi non leggibile", exc_info=True)
        return []


def riferimenti_da_mappa(testo: str) -> list[dict]:
    refs: list[dict] = []
    for voce in _mappa():
        if any(t.search(testo or "") for t in voce["trigger"]):
            refs += riferimenti_da_testo("; ".join(voce["riferimenti"]))
    return refs


_SISTEMA_PROPOSTA = (
    "Sei un indicizzatore giuridico per un consulente d'impresa italiano. Dato il quesito, indica quali "
    "NORME ITALIANE disciplinano il punto, così che il sistema possa recuperarne il testo. NON rispondere al "
    "quesito. Rispondi SOLO con un oggetto JSON: {\"norme\":[...],\"parole\":[...]}.\n"
    "'norme': fino a 5 riferimenti precisi, uno per voce, nella forma standard: 'art. 2473 c.c.', "
    "'art. 641 c.p.c.', 'D.Lgs. 231/2002 art. 4', 'L. 300/1970 art. 4', 'D.P.R. 633/1972 art. 7'. Scrivi solo "
    "riferimenti di cui sei ragionevolmente certo (numero di norma, anno e articolo); se sei certo della NORMA ma "
    "non dell'articolo, scrivi la norma senza articolo ('D.Lgs. 276/2003'): il sistema cercherà l'articolo "
    "dentro la norma.\n"
    "'parole': da 3 a 6 parole italiane tecniche che compaiono nel testo di legge pertinente (sostantivi e "
    "verbi giuridici, niente articoli o preposizioni).\n"
    "Se il quesito NON riguarda norme di legge (strategia, marketing, organizzazione, tecnica) o è una "
    "chiacchiera, rispondi {\"norme\":[],\"parole\":[]}.\n"
    "ATTENZIONE ai calcoli: un calcolo puramente aritmetico su dati dati dall'utente (costo per contatto, margine) "
    "non ha norme. Ma un calcolo che APPLICA aliquote, soglie, coefficienti o limiti di legge (IVA, IRES, IRPEF, "
    "ammortamento, deducibilità, detraibilità, sanzioni, interessi) le ha: indica le norme che li fissano, "
    "anche se la domanda è «calcolami…» o «ricontrolla i calcoli» (in tal caso guarda il contesto). Esempi: "
    "ammortamento di un bene → 'D.P.R. 917/1986 art. 102'; aliquota IRES → 'D.P.R. 917/1986 art. 77'; "
    "detrazione dell'IVA sugli acquisti → 'D.P.R. 633/1972 art. 19'.\n"
    "RICHIAMI FREQUENTI (norme che servono spesso e che di solito si dimenticano; segnalati dal test del 20/10/2026, "
    "da far validare a un professionista): stare in giudizio senza avvocato, decreto ingiuntivo «in proprio», giudice di "
    "pace → 'art. 82 c.p.c.' oltre agli articoli sul procedimento; il cliente che recede da un incarico professionale o "
    "di progettazione → 'art. 2237 c.c.'; il committente che recede da un appalto o da un'opera → 'art. 1671 c.c.'; "
    "interessi di mora fra imprese → 'D.Lgs. 231/2002 art. 4' e 'D.Lgs. 231/2002 art. 5'; sospendere il pagamento per "
    "inadempimento o difetti della controparte → 'art. 1460 c.c.'; difetti di un'opera o di un software su commessa → 'art. 1667 c.c.' "
    "e 'art. 1668 c.c.'; qualificare il contratto (appalto, contratto d'opera, vendita) → 'art. 1655 c.c.' e 'art. 2222 c.c.'; "
    "mediazione obbligatoria → 'D.Lgs. 28/2010 art. 5'."
)


def _json_tollerante(testo: str) -> Optional[dict]:
    t = (testo or "").strip()
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        v = json.loads(t[a:b + 1])
        return v if isinstance(v, dict) else None
    except json.JSONDecodeError:
        return None


def proponi(client, modello: str, quesito: str, contesto: str = "") -> tuple[list[dict], list[str]]:
    """Riferimenti e parole chiave PROPOSTI dal modello. Fail-open: ([], [])."""
    try:
        utente = f"QUESITO:\n{quesito.strip()[:1200]}"
        if contesto.strip():
            utente = f"CONTESTO (messaggi precedenti dell'utente):\n{contesto.strip()[-900:]}\n\n" + utente
        # temperatura 0: la scelta degli articoli deve essere RIPRODUCIBILE. Con una temperatura alta lo stesso
        # quesito dava articoli diversi a ogni esecuzione (misurato il 15/10/2026), e questo rumore copriva
        # l'effetto di ogni modifica al recupero. L'SDK attuale NON ha il parametro `temperature` (TypeError:
        # la proposta falliva sempre, in silenzio, per il fail-open): si passa da extra_body, e se l'API lo
        # rifiuta (alcuni modelli non accettano la temperatura) si riprova una volta senza.
        base = dict(model=modello, max_tokens=320, system=_SISTEMA_PROPOSTA,
                    messages=[{"role": "user", "content": utente}], timeout=_TIMEOUT_PROPOSTA)
        try:
            r = client.messages.create(**base, extra_body={"temperature": _TEMPERATURA})
        except Exception as e:
            if isinstance(e, TypeError) or getattr(e, "status_code", None) in (400, 422):
                r = client.messages.create(**base)
            else:
                raise
        out = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        v = _json_tollerante(out)
        if not v:
            return [], []
        norme = [str(x) for x in (v.get("norme") or []) if isinstance(x, (str, int))][:8]
        parole = [str(x).lower() for x in (v.get("parole") or []) if isinstance(x, str)][:8]
        return riferimenti_da_testo("; ".join(norme), solo_con_articolo=False), parole
    except Exception:
        log.warning("norme_evidence: proposta dei riferimenti fallita (fail-open)", exc_info=True)
        return [], []


# ═══ 5 · recupero e lettura per commi ══════════════════════════════════════════════════════
_NOTE = re.compile(r"-{5,}\s*AGGIORNAMENTO", re.I)
_RIF_NOTA = re.compile(r"\(\(\s*\d+\s*\)\)|(?<=[.;:])\s*\(\d{1,3}\)(?=\s)")
_RUBRICA = re.compile(r"Art\.\s*[\w\-]+(?:\s+—[^\n]*)?\s*\.?\s*\(([^)]{3,90})\)")
_SUFFISSI = r"(?:-(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies))?"
_COMMA = re.compile(r"(?:(?<=\s)|^)(\d{1,2}" + _SUFFISSI + r")\.\s+(?=[A-ZÀÈÉÌÒÙ«\"(])")
_DECORRENZA = re.compile(r"\b(a decorrere dal|a partire dal|dal 1°|dal \d{1,2} (?:gennaio|febbraio|marzo|aprile|maggio|"
                         r"giugno|luglio|agosto|settembre|ottobre|novembre|dicembre) \d{4}|fino al|non oltre il|"
                         r"entro il 31|in vigore dal)\b", re.I)


# Le NOTE DI AGGIORNAMENTO del corpus non sono rumore: a volte contengono una modifica che il testo non ha
# incorporato. Caso reale (15/10/2026): l'art. 25 D.P.R. 600/1973 riporta nel corpo «ritenuta del 15 per
# cento»; la nota (54) dice che la L. 449/1997 ha sostituito «19 per cento» con «20 per cento» al primo comma.
# Senza le note il pacchetto avrebbe dato al modello una cifra superata con l'aria di una fonte.
_NOTA_SPLIT = re.compile(r"-{5,}\s*AGGIORNAMENTO\s*\((\d+)\)", re.I)
_NOTA_MODIFICA = re.compile(
    r"sostituit\w+\s+(?:le parole|dalle seguenti|dal seguente)|le parole\s*[:«\"]|"
    r"(?:\be'|\bè|\bsono)\s+(?:elevat|ridott|aumentat|adeguat)\w+\s+(?:al|a|di|all')\b", re.I)
_NOTA_QUANTITA = re.compile(r"\d+\s*(?:per cento|euro|giorni|mesi|anni|punti)|\b(?:per cento|euro)\b", re.I)
MAX_NOTE = int(os.getenv("KBOT_NORME_MAX_NOTE", "3"))
MAX_CHARS_NOTA = int(os.getenv("KBOT_NORME_MAX_CHARS_NOTA", "280"))


def note_rilevanti(testo_grezzo: str) -> str:
    """Le note di aggiornamento che modificano CIFRE (sostituzioni, aumenti, riduzioni), le più recenti per
    anno della norma citata, tagliate. '' se non ce ne sono o se la funzione è spenta."""
    if not _flag("KBOT_NORME_NOTE"):
        return ""
    parti = _NOTA_SPLIT.split(re.sub(r"\s+", " ", (testo_grezzo or "").replace("**", "")))
    note = []
    for i in range(1, len(parti) - 1, 2):
        t = parti[i + 1].strip()
        if _NOTA_MODIFICA.search(t) and _NOTA_QUANTITA.search(t):
            anno = re.search(r"\b(19\d{2}|20\d{2})\b", t[:140])
            note.append((int(anno.group(1)) if anno else 0, int(parti[i]), t))
    note.sort(key=lambda x: (-x[0], -x[1]))
    out = []
    for _, n, t in note[:MAX_NOTE]:
        out.append(f"({n}) " + (t if len(t) <= MAX_CHARS_NOTA else t[:MAX_CHARS_NOTA].rstrip() + " […]"))
    return " ".join(out)


_SOSTITUTA = re.compile(r"sostituit\w+\s+dalle\s+seguenti\s*:?\s*[\"«“]\s*([^\"»”]{3,60}?)\s*[\"»”]", re.I)
_ELEVATA = re.compile(r"(?:e'|è|sono)\s+(?:elevat|ridott|aumentat)\w+\s+(?:al|a|di)\s+(\d+(?:,\d+)?\s*per cento)", re.I)
_QUANT_UNITA = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?|" + "|".join(sorted(PAROLE_NUMERO, key=len, reverse=True)) +
                          r")\s*(per cento|euro|giorni|mesi|anni)", re.I)


def vigenza_avviso(testo_grezzo: str, corpo: str) -> str:
    """Le note dicono che una cifra è stata SOSTITUITA ma il corpo riporta ancora quella vecchia: il corpus non
    ha incorporato la modifica (art. 25 D.P.R. 600/1973: corpo «15 per cento»; nota: «19» → «20 per cento»). Il
    modello, davanti a una cifra nel testo e a una nota, si fida del testo (misurato il 15/10/2026: 15% in 2 prove
    su 3 anche con la nota nel pacchetto, mentre senza pacchetto sapeva 20%). Qui si dice ESPLICITAMENTE quale
    cifra è vigente e quale è superata. Solo per le unità «per cento», «euro», «giorni», «mesi», «anni»."""
    if not _flag("KBOT_NORME_NOTE") or not _flag("KBOT_NORME_AVVISO"):
        return ""
    parti = _NOTA_SPLIT.split(re.sub(r"\s+", " ", (testo_grezzo or "").replace("**", "")))
    candidate = []
    for i in range(1, len(parti) - 1, 2):
        t = parti[i + 1]
        anno = re.search(r"\b(19\d{2}|20\d{2})\b", t[:140])
        for m in list(_SOSTITUTA.finditer(t)) + list(_ELEVATA.finditer(t)):
            nuova = m.group(1).strip()
            mq = _QUANT_UNITA.fullmatch(nuova) or re.fullmatch(r"(\d+(?:,\d+)?)\s*(per cento)", nuova, re.I)
            if mq:
                comma = re.search(r"\bal\s+(primo|secondo|terzo|quarto|quinto)\s+comma", t[:m.start()], re.I)
                candidate.append((int(anno.group(1)) if anno else 0, int(parti[i]), nuova, mq.group(2).lower(),
                                  valore(mq.group(1)) if valore(mq.group(1)) is not None else mq.group(1),
                                  {"primo": "1", "secondo": "2", "terzo": "3", "quarto": "4", "quinto": "5"}[comma.group(1).lower()] if comma else None))
    if not candidate:
        return ""
    candidate.sort(key=lambda x: (-x[0], -x[1]))
    anno, _, nuova, unita, valnuovo, n_comma = candidate[0]
    ambito = corpo or ""
    if n_comma:                                    # «al primo comma…»: si guardano le cifre di QUEL comma
        trovato = False
        for et, t in dividi_commi(corpo or ""):
            if et == n_comma:
                ambito, trovato = t, True
                break
        if not trovato and n_comma == "1":         # articolo senza commi numerati: il primo è all'inizio
            ambito = (corpo or "")[:700]
    body_q = {}
    for m in _QUANT_UNITA.finditer(ambito):
        v = valore(m.group(1)) if valore(m.group(1)) is not None else m.group(1)
        body_q.setdefault(m.group(2).lower(), set()).add(v)
    stessa = body_q.get(unita, set())
    if not stessa or valnuovo in stessa:
        return ""                                   # il testo contiene già la cifra nuova (o non ne ha dello stesso tipo)
    vecchie = ", ".join(sorted(f"{v} {unita}" for v in stessa if isinstance(v, (int, str)))[:3])
    return (f"ATTENZIONE VIGENZA: secondo le modifiche successive la cifra vigente è «{nuova}»; "
            f"le cifre «{vecchie}» riportate nel testo di questo articolo sono SUPERATE. Usa «{nuova}».")


def _ripulisci(testo: str) -> tuple[str, bool]:
    """(corpo senza note di aggiornamento né marcatori, abrogato)."""
    corpo = _NOTE.split(testo or "", maxsplit=1)[0]
    abrogato = bool(re.search(r"ARTICOLO ABROGATO", corpo, re.I)) and len(corpo) < 500
    corpo = _RIF_NOTA.sub("", corpo)
    corpo = corpo.replace("((", "").replace("))", "").replace("**", "")      # «**1.**» → «1.»
    corpo = re.sub(r"\s+", " ", corpo).strip()
    return corpo, abrogato


def dividi_commi(corpo: str) -> list[tuple[str, str]]:
    """[(etichetta, testo)]. L'etichetta '' è l'intestazione prima del comma 1. Si accettano solo
    numerazioni plausibili (1, 2, 3, 3-bis, 4…): evita di scambiare «n. 196. L'articolo» per un comma."""
    atteso, ultimo, tagli = 1, 0, []
    for m in _COMMA.finditer(corpo):
        etichetta = m.group(1)
        n = int(re.match(r"\d+", etichetta).group(0))
        suff = etichetta[len(str(n)):]
        if (n == atteso and not suff) or (n == ultimo and suff):
            tagli.append((m.start(), m.end(), etichetta))
            if not suff:
                ultimo, atteso = n, n + 1
    if not tagli:
        return [("", corpo)]
    out = []
    if tagli[0][0] > 0:
        out.append(("", corpo[:tagli[0][0]].strip()))
    for i, (_, fine, et) in enumerate(tagli):
        stop = tagli[i + 1][0] if i + 1 < len(tagli) else len(corpo)
        out.append((et, corpo[fine:stop].strip()))
    return out


def _punteggio(testo: str, steli: set[str]) -> int:
    t = testo.lower()
    return sum(1 for s in steli if s in t)


def _intenti(quesito: str) -> tuple[bool, bool]:
    """(il quesito chiede un TERMINE, il quesito chiede un IMPORTO/soglia)."""
    q = (quesito or "").lower()
    tempo = bool(re.search(r"\b(quando|quanto tempo|entro|termine|termini|scadenz\w*|scade|giorni|mesi|anni|"
                           r"tempi|durata|prescri\w+|decad\w+)\b", q))
    soldi = bool(re.search(r"\b(euro|importo|soglia|limite|massimo|minimo|quanto costa|sanzion\w+|multa|"
                           r"interess\w+|percentuale|aliquota)\b|€", q))
    return tempo, soldi


def _taglia(t: str, cap: int) -> str:
    """Taglia un comma troppo lungo a fine frase prima del tetto, con «[…]»."""
    if len(t) <= cap:
        return t
    punto = max(t.rfind(". ", 0, cap), t.rfind("; ", 0, cap))
    return (t[:punto + 1] if punto > cap * 0.45 else t[:cap].rstrip()) + " […]"


_CAP_LIVELLO = {1: 1500, 2: 700, 3: 450}      # intestazione e comma 1 · commi con decorrenza · gli altri


def seleziona_indici(commi: list[tuple[str, str]], parole: list[str], budget: int,
                     quesito: str = "") -> tuple[list[int], dict[int, Optional[int]]]:
    """(indici dei commi da tenere, tetto di caratteri per ciascuno). Tutti e interi se ci stanno.
    Altrimenti, per LIVELLI:
      1. intestazione e comma 1: mai tagliati (fino a 1.500 car.);
      2. commi con DECORRENZA («a decorrere dal…»): portano la regola vigente (art. 49 c.3-bis: 5.000 €
         dal 2023 mentre il comma 1 dice ancora 3.000), tagliati a 700;
      3. gli altri, per pertinenza alle parole del quesito, con un aiuto a chi contiene termini o importi
         quando il quesito li chiede, tagliati a 450.
    Un comma lunghissimo non consuma così il budget degli altri. Ordine originale."""
    if sum(len(t) + 12 for _, t in commi) <= budget:
        return list(range(len(commi))), {}
    steli = {w[:5] for w in parole if len(w) >= 5}
    tempo, soldi = _intenti(quesito)
    livello: dict[int, int] = {}
    punti: dict[int, int] = {}
    for i, (et, t) in enumerate(commi):
        liv = 1 if (i == 0 or et == "1") else (2 if _DECORRENZA.search(t) else 3)
        p = _punteggio(t, steli) * 10
        if tempo and coppie_nel_testo(t):
            p += 25
        if soldi and any(n >= 100 for n in numeri_nel_testo(t)):
            p += 25
        livello[i], punti[i] = liv, p
    cap_livelli = dict(_CAP_LIVELLO)
    cap_livelli[1] = min(cap_livelli[1], int(budget * 0.55))     # il comma 1 non deve schiacciare gli altri
    tenuti, caps, usato = [], {}, 0
    for i in sorted(livello, key=lambda i: (livello[i], -punti[i], i)):
        cap = cap_livelli[livello[i]]
        c = min(len(commi[i][1]), cap) + 12
        if usato + c > budget and tenuti:
            continue
        tenuti.append(i)
        caps[i] = cap if len(commi[i][1]) > cap else None
        usato += c
    # una frase con decorrenza («Fino alla scadenza…, gli stessi datori…») si riferisce a quella prima:
    # si porta dietro il predecessore se c'è spazio (utile per gli articoli senza commi numerati)
    for i in sorted(t for t in tenuti if livello[t] == 2):
        if i > 0 and i - 1 not in tenuti and not commi[i - 1][0]:
            c = min(len(commi[i - 1][1]), _CAP_LIVELLO[3]) + 12
            if usato + c <= budget:
                tenuti.append(i - 1)
                caps[i - 1] = _CAP_LIVELLO[3] if len(commi[i - 1][1]) > _CAP_LIVELLO[3] else None
                usato += c
    return sorted(tenuti), caps


def _frasi(corpo: str) -> list[tuple[str, str]]:
    """I commi del codice civile NON sono numerati: per selezionare si lavora per frasi."""
    return [("", f.strip()) for f in re.split(r"(?<=[.;:])\s+(?=[A-ZÀÈÉÌÒÙ«\"(])", corpo) if f.strip()]


def _formatta(commi: list[tuple[str, str]], idx: list[int], caps: Optional[dict] = None) -> str:
    righe, prec = [], None
    for i in idx:
        et, t = commi[i]
        salto = prec is not None and i != prec + 1
        if caps and caps.get(i):
            t = _taglia(t, caps[i])
        righe.append(((("  […]\n" if et else "[…] ") if salto else "") + (f"  comma {et}: {t}" if et else t)))
        prec = i
    if all(not commi[i][0] for i in idx):
        return "  " + " ".join(righe)
    return "\n".join(r if r.startswith("  ") or r.startswith("[") else "  " + r for r in righe)


def _sigla(est: dict) -> str:
    """Forma breve per l'utente: «art. 2473 c.c.» per i codici, la citazione del lettore per il resto
    (il corpus ha prefissi propri: un D.Lgs può stare sotto 'legge_AAAA_N')."""
    tipo, num, anno, art = est.get("tipo", ""), str(est.get("numero", "")), est.get("anno"), est.get("articolo", "")
    codici = {("regio_decreto", "262", 1942): "c.c.", ("regio_decreto", "1443", 1940): "c.p.c.",
              ("regio_decreto", "1398", 1930): "c.p.",
              ("decreto_presidente_repubblica", "447", 1988): "c.p.p."}
    c = codici.get((tipo, num, anno))
    return f"art. {art} {c}" if c else (est.get("citazione") or f"art. {art} {num}/{anno}")


_CACHE_ARTICOLI: dict[tuple, dict] = {}


def _articolo(tipo: str, anno: int, numero: str, articolo: str) -> Optional[dict]:
    chiave = (tipo, int(anno), str(numero), _norm_art(articolo))
    if chiave in _CACHE_ARTICOLI:
        return _CACHE_ARTICOLI[chiave]
    m = lettore()
    if not m:
        return None
    try:
        r = m.find_by_estremi(int(anno), str(numero), tipo, str(articolo), limit=1)
    except Exception:
        log.warning("norme_evidence: lettura %s %s/%s art. %s fallita", tipo, numero, anno, articolo, exc_info=True)
        return None
    if r:
        if len(_CACHE_ARTICOLI) > 600:
            _CACHE_ARTICOLI.clear()
        _CACHE_ARTICOLI[chiave] = r[0]          # si memorizzano solo i successi: un errore non resta
        return r[0]
    return None


def recupera(rif: dict, parole: list[str], origine: str, budget: int, quesito: str = "") -> Optional[Fonte]:
    rec = _articolo(rif.get("tipo") or "", rif["anno"], rif["numero"], rif["articolo"])
    if not rec:
        return None
    corpo, abrogato = _ripulisci(rec.get("testo") or "")
    if abrogato or len(corpo) < 20:
        return None
    rub = _RUBRICA.search(corpo)
    commi = dividi_commi(corpo)
    if len(commi) == 1 and len(corpo) > budget:
        commi = _frasi(corpo)
    idx, caps = seleziona_indici(commi, parole, budget, quesito)
    testo = _formatta(commi, idx, caps)
    return Fonte(citazione=rec.get("citazione", ""), tipo=rec.get("tipo", ""), anno=int(rec.get("anno") or rif["anno"]),
                 numero=str(rec.get("numero") or rif["numero"]), articolo=str(rec.get("articolo") or rif["articolo"]),
                 rubrica=rub.group(1).strip() if rub else "", sigla=_sigla(rec), origine=origine, testo=testo,
                 note=note_rilevanti(rec.get("testo") or ""),
                 avviso=vigenza_avviso(rec.get("testo") or "", corpo))


_SUFFISSI_AFFINI = ("bis", "ter", "quater", "quinquies", "sexies", "septies", "octies", "novies", "decies")


def _steli(parole: list[str]) -> list[str]:
    return sorted({w[:6] for w in parole if len(w) >= 5})


def cerca_in_norma(rif: dict, parole: list[str], budget: int, quesito: str = "") -> list[Fonte]:
    """La norma è nota ma l'articolo no: ricerca per PAROLE dentro quella norma (indice FTS del corpus,
    colonna file = estremi) e si tengono i primi due articoli che contengono almeno due parole del quesito."""
    m, steli = lettore(), _steli(parole)
    if not m or not steli or not rif.get("anno") or not rif.get("numero"):
        return []
    q = (f"file:{int(rif['anno'])} AND file:{re.sub(r'[^0-9]', '', str(rif['numero']))} AND testo:("
         + " OR ".join(f"{w}*" for w in steli[:8]) + ")")
    try:
        righe = m.search(q, limit=12)
    except Exception:
        return []
    out: list[Fonte] = []
    for r in righe:
        if r.get("anno") != int(rif["anno"]) or str(r.get("numero")) != re.sub(r"[^0-9]", "", str(rif["numero"])):
            continue
        f = recupera({"tipo": r.get("tipo", ""), "anno": r["anno"], "numero": r["numero"], "articolo": r["articolo"]},
                     parole, "norma", budget, quesito)
        if f and _punteggio(f.testo + " " + f.rubrica, set(steli)) >= 2:
            out.append(f)
        if len(out) >= 2:
            break
    return out


def articoli_affini(rif: dict, parole: list[str], budget: int, quesito: str = "") -> list[Fonte]:
    """Gli articoli «bis, ter, quater…» di un articolo proposto: nei codici le norme gemelle stanno
    insieme (2479 → 2479-ter «impugnazione delle decisioni»). Si tengono solo se pertinenti (≥2 parole)."""
    art = str(rif.get("articolo") or "")
    if not re.fullmatch(r"\d+", art):
        return []
    steli, out = set(_steli(parole)), []
    for suf in _SUFFISSI_AFFINI:
        f = recupera({**rif, "articolo": f"{art}-{suf}"}, parole, "affine", budget, quesito)
        if f and _punteggio(f.testo + " " + f.rubrica, steli) >= 2:
            out.append(f)
    return out


def _pertinente(f: Fonte, parole: list[str]) -> bool:
    """Un riferimento PROPOSTO dal modello entra solo se il suo testo contiene almeno una delle parole
    del quesito: l'art. 2099 esiste ma non parla di patto di prova. Utente e mappa non passano da qui."""
    steli = {w[:5] for w in parole if len(w) >= 5}
    return not steli or _punteggio(f.testo + " " + f.rubrica, steli) >= 1


_ISTRUZIONI = (
    "COME USARLE:\n"
    "- Per ogni fatto di legge (termini, soglie, importi, requisiti) usa QUESTE fonti e non la memoria. Un termine "
    "o una cifra che qui non compare non va presentato come certo.\n"
    "- Cita la fonte fra parentesi dopo il fatto, nella forma indicata a sinistra di ogni fonte, ad esempio "
    "«(art. 2473 c.c.)». Puoi citare SOLO gli articoli elencati qui: è l'unica eccezione alla regola «niente "
    "numeri di articolo».\n"
    "- Se nello stesso articolo commi diversi danno cifre diverse, vale il comma con la decorrenza più recente "
    "(«a decorrere dal…»); il comma 1 può riportare ancora il testo storico.\n"
    "- Dove compare «Modifiche successive al testo», quelle cifre prevalgono su quelle del testo; se non sei sicuro "
    "di quale sia vigente, dì che la cifra va verificata.\n"
    "- Se in un turno precedente hai dato una cifra, una soglia o un'interpretazione che NON sta in queste fonti e non "
    "l'ha detta l'utente, non difenderla: ritirala dicendo che era un'ipotesi senza fonte, o sostituiscila con quella "
    "delle fonti. Se hai ammesso di non avere una fonte, la conclusione che ne dipendeva non resta in piedi.\n"
    "- Se un passaggio non riguarda il caso, ignoralo senza citarlo. Se le fonti non coprono il punto, dillo e "
    "indirizza al professionista invece di inventare.\n"
    "- Il testo può non essere aggiornato all'ultima modifica: per scadenze e importi che pesano sulla decisione "
    "ricorda di verificare la vigenza."
)


def costruisci_blocco(fonti: list[Fonte]) -> str:
    righe = ["FONTI NORMATIVE PER QUESTO TURNO (testo ufficiale dal corpus Normattiva, recuperato dal sistema):"]
    for i, f in enumerate(fonti, 1):
        titolo = f"[{i}] ({f.sigla}) {f.citazione}" + (f" — {f.rubrica}" if f.rubrica else "")
        righe.append(titolo)
        if f.avviso:
            righe.append("  " + f.avviso)
        righe.append(f.testo)
        if f.note:
            righe.append("  Modifiche successive al testo (non ancora riportate sopra; se indicano una cifra diversa da "
                         "quella del testo, vale quella più recente): " + f.note)
    righe.append(_ISTRUZIONI)
    return "\n" + "\n".join(righe) + "\n"


def costruisci(quesito: str, contesto: str, client=None, modello: str = "") -> Optional[Pacchetto]:
    """Il pacchetto per questo turno, o None (non serve / corpus assente / nulla trovato). Fail-open."""
    if not abilitato() or not serve_evidenza(quesito, contesto) or not disponibile():
        return None
    try:
        testo_tot = f"{contesto}\n{quesito}"
        fonti_ue = norme_ue.fonti_ue(testo_tot, Fonte)       # norme UE che il corpus Normattiva non ha (es. GDPR)
        parole = _parole_chiave(quesito)
        candidati: list[tuple[dict, str]] = [(r, "utente") for r in riferimenti_da_testo(testo_tot)]
        candidati += [(r, "mappa") for r in riferimenti_da_mappa(testo_tot)]
        if client is not None:
            proposti, parole_modello = proponi(client, modello, quesito, contesto)
            parole = list(dict.fromkeys(parole_modello + parole))
            candidati += [(r, "proposta") for r in proposti]
        visti, uniche = set(), []
        for r, o in candidati:
            k = (r.get("tipo"), str(r.get("numero")), r.get("anno"), re.sub(r"[^0-9a-z]", "", str(r.get("articolo") or "").lower()))
            if k not in visti:
                visti.add(k)
                uniche.append((r, o))
        con_art = [(r, o) for r, o in uniche if r.get("articolo")][:MAX_RIFERIMENTI + 3]
        senza_art = [(r, o) for r, o in uniche if not r.get("articolo")][:2]
        budget = MAX_CHARS_ARTICOLO
        if not con_art and not senza_art and not fonti_ue:
            return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            dirette = list(ex.map(lambda ro: recupera(ro[0], parole, ro[1], budget, quesito), con_art))
            extra: list[Fonte] = []
            if _flag("KBOT_NORME_AFFINI"):
                for lista in ex.map(lambda ro: articoli_affini(ro[0], parole, budget, quesito), con_art[:3]):
                    extra += lista
            if _flag("KBOT_NORME_RICERCA_NORMA"):
                for lista in ex.map(lambda ro: cerca_in_norma(ro[0], parole, budget, quesito), senza_art):
                    extra += lista
        fonti: list[Fonte] = []
        totale = 0
        visti_f: set[tuple] = set()
        escluse = norme_ue.escluse(testo_tot)                  # (numero, anno) da non proporre quando una norma UE regge il caso
        for f in dirette + extra:
            if f is None or (f.origine in ("proposta", "affine", "norma") and not _pertinente(f, parole)):
                continue
            if f.origine != "utente" and (str(f.numero), f.anno) in escluse:
                continue
            chiave = (f.numero, f.anno, _norm_art(f.articolo))
            if chiave in visti_f:
                continue
            if totale + len(f.testo) > MAX_CHARS_TOTALE and fonti:
                continue
            visti_f.add(chiave)
            fonti.append(f)
            totale += len(f.testo)
            if len(fonti) >= MAX_RIFERIMENTI:
                break
        fonti = fonti_ue + fonti
        if not fonti:
            return None
        blocco = costruisci_blocco(fonti)
        corpo = " ".join(f.testo + " " + f.note for f in fonti)
        return Pacchetto(testo=blocco, fonti=fonti, numeri=numeri_nel_testo(corpo), coppie=coppie_nel_testo(corpo),
                        importi=importi_nel_testo(corpo))
    except Exception:
        log.warning("norme_evidence: costruzione del pacchetto fallita (fail-open)", exc_info=True)
        return None


# ═══ 6 · uso a valle: citazioni consentite, numeri fondati, elenco delle fonti ═════════════
def _norm_art(a: str) -> str:
    return re.sub(r"[^0-9a-z]", "", str(a or "").lower())


# TESTO DELL'UTENTE (messaggi + documenti che ha caricato): i numeri e le citazioni che LUI ha scritto non sono
# «numeri a memoria del modello». Misurato il 19/10/2026: le guardie sostituivano con «nella misura prevista dalla
# normativa» la penale del 30% e del 40% scritta nel contratto dell'utente, il «3 giorni» della sua lettera di
# contestazione, il «120 giorni» del suo contratto. Qui si tiene l'insieme di ciò che ha scritto l'utente nel turno.
_testo_utente: contextvars.ContextVar = contextvars.ContextVar("kbot_testo_utente", default=None)


_MESI = {m: i for i, m in enumerate(("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
                                     "settembre", "ottobre", "novembre", "dicembre"), 1)}
_RE_DATA_NUM = re.compile(r"(?<![\d/])(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})(?![\d/])")
_RE_DATA_TXT = re.compile(r"\b(\d{1,2})\s+(" + "|".join(_MESI) + r")\s+(\d{4})\b", re.I)


def _date_nel_testo(testo: str) -> list:
    import datetime as _dt
    out = []
    for g, m, a in [(x.group(1), x.group(2), x.group(3)) for x in _RE_DATA_NUM.finditer(testo)] + \
                   [(x.group(1), _MESI[x.group(2).lower()], x.group(3)) for x in _RE_DATA_TXT.finditer(testo)]:
        try:
            d = _dt.date(int(a), int(m), int(g))
        except ValueError:
            continue
        if d not in out:
            out.append(d)
    return out[:12]


def durate_dalle_date(testo: str) -> set:
    """Le durate che si ricavano dalle date scritte dall'utente (es. 14/04/2026 → 14/06/2026 = 61 giorni, 2 mesi):
    sono numeri CALCOLATI dai suoi dati, non numeri a memoria del modello. Si tollera ±1 giorno e l'arrotondamento
    a 10 giorni / ai mesi interi, perché il modello dice «60 giorni» per 61. Misurato il 19/10/2026: la guardia
    sostituiva con «il termine previsto dalla normativa» anche questa durata."""
    date = _date_nel_testo(testo or "")
    out: set = set()
    for i in range(len(date)):
        for j in range(i + 1, len(date)):
            giorni = abs((date[j] - date[i]).days)
            if giorni == 0:
                continue
            for g in {giorni - 1, giorni, giorni + 1, round(giorni / 10) * 10, round(giorni / 30.44) * 30}:
                if g > 0:
                    out.add((g, "gio"))
            mesi = round(giorni / 30.44)
            if mesi >= 1:
                out.add((mesi, "mes"))
            if giorni >= 7:
                out.add((round(giorni / 7), "set"))
            if giorni >= 365:
                out.add((round(giorni / 365.25), "ann"))
    return out


def imposta_testo_utente(testo: Optional[str]) -> None:
    if not testo:
        _testo_utente.set(None)
        return
    norm = re.sub(r"\s+", " ", testo).lower()
    coppie = set(coppie_nel_testo(testo)) | durate_dalle_date(testo)
    _testo_utente.set((coppie, numeri_nel_testo(testo), norm, importi_nel_testo(testo)))


def testo_utente_corrente():
    return _testo_utente.get()


def citazione_consentita(span: str) -> bool:
    """Una citazione come «art. 2473 c.c.» o «art. 4 D.Lgs. 231/2002» è consentita solo se quell'articolo
    sta nel pacchetto del turno: la regola del 17 luglio («niente numeri di articolo, esistenza ≠
    pertinenza») resta, con l'eccezione delle fonti che il sistema ha recuperato e fatto leggere."""
    p = pacchetto_corrente()
    if not span:
        return False
    u = _testo_utente.get()
    if u and re.sub(r"\s+", " ", span).strip().lower() in u[2]:
        return True                                   # la citazione l'ha scritta l'utente (messaggio o documento)
    if not p:
        return False
    s = re.sub(r"\s+", " ", span)
    ma = re.search(r"art\w*\.?\s*(\d+[\w\-‑–]*)", s, re.I)
    if not ma:
        return False
    art = _norm_art(ma.group(1))
    if re.search(r"\bc\.\s?c\.|codice civile|cod\.\s*civ", s, re.I):
        chiave = ("262", 1942)
    else:
        mn = re.search(r"(\d+)\s*[/.]\s*(\d{2,4})", s)
        if not mn:
            return False
        a = int(mn.group(2))
        chiave = (mn.group(1), a if a >= 100 else (2000 + a if a <= 30 else 1900 + a))
    return any(_norm_art(f.articolo) == art and (str(f.numero), f.anno) == chiave for f in p.fonti)


def numero_fondato(span: str) -> bool:
    """True se i numeri di un'espressione di scadenza/soglia («entro 40 giorni», «5.000 euro») compaiono
    nel testo di legge recuperato per questo turno, con la stessa unità quando c'è."""
    p, u = pacchetto_corrente(), _testo_utente.get()
    if not span or (not p and not u):
        return False
    importi = importi_nel_testo(span)
    if importi:                      # un importo in euro si verifica come importo (non come numero nudo)
        return all((p and i in p.importi) or (u and len(u) > 3 and i in u[3]) for i in importi)
    coppie = coppie_nel_testo(span)
    if coppie:
        return all((p and c in p.coppie) or (u and c in u[0]) for c in coppie)
    nums = numeri_nel_testo(span)
    return bool(nums) and all((p and n in p.numeri) or (u and n in u[1]) for n in nums)


def aggiungi_fonti(testo: str) -> str:
    """In coda alla risposta, l'elenco delle fonti del pacchetto che il testo ha davvero citato. Lo fa il
    codice, non il modello: la fonte c'è anche quando il modello non la scrive."""
    p = pacchetto_corrente()
    if not p or not testo or re.search(r"(?m)^Fonti:", testo):
        return testo
    usate = []
    for f in p.fonti:
        art = re.escape(f.articolo)
        if re.search(rf"\bart\w*\.?\s*{art}\b", testo, re.I) or f.sigla.lower() in testo.lower():
            usate.append(f.sigla)
    if not usate:
        return testo
    elenco = "; ".join(dict.fromkeys(usate))
    return testo.rstrip() + "\n\nFonti: " + elenco + ("" if elenco.endswith(".") else ".")
