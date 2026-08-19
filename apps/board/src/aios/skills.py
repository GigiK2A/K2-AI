"""SkillLibrary: catalogo skill per gli agenti, con progressive disclosure.

Due basi su disco (prima vince in caso di nome uguale):
1. `skills/`      — le skill locali del board (K2-specifiche, marketing-tuned)
2. `skills_lib/`  — la libreria master vendorizzata da kai-website/lib/skills
                    (SKILL.md + references/*.md; ~300 skill di TUTTI i domini)

Gli agenti non ricevono tutte le skill nel prompt: ottengono un INDICE compatto
del proprio reparto (auto-tag deterministico dalla description) e caricano il testo
pieno di una skill solo quando serve (`load`), oppure cercano in tutta la libreria
(`search`). Stesso principio delle skill di Claude Code: si apre ciò che serve.
"""

from __future__ import annotations

import re
from pathlib import Path

_SKILLS_DIR = Path(__file__).parent / "skills"          # locali (board)
_LIB_DIR = Path(__file__).parent / "skills_lib"          # master vendorizzata

# Banche di parole chiave per instradare una skill al reparto giusto (dalla sua
# description). Deterministico, nessun LLM. Una skill può finire in più reparti;
# quelle che non combaciano con nessuno restano raggiungibili solo via `search`.
_DOMAIN_KW: dict[str, tuple[str, ...]] = {
    "marketing": ("marketing", "seo", "brand", "content", "contenut", "campagn", "social",
                  "copy", "funnel", "newsletter", "email sequence", "ads", "advertis",
                  "growth", "posizionament", "keyword", "sentiment", "audience", "creativ"),
    "vendite": ("vendit", "sales", "lead", "crm", "pipeline", "prospect", "outreach",
                "offerta", "trattativ", "deal", "negozia", "b2b", "account", "closing",
                "preventiv", "commercial"),
    "finance": ("bilancio", "finanz", "budget", "cashflow", "cash flow", "ricav", "costi",
                "margine", "ebitda", "tesoreria", "forecast", "revenue", "kpi", "dcf",
                "valutazione d'azienda", "wacc", "fiscal", "iva", "ires", "irpef", "tribut",
                "tass", "contabil", "controllo di gestione", "de minimis", "agevolazion",
                "credito d'imposta", "transizione 5.0", "sabatini", "bancabil"),
    "operations": ("commessa", "commesse", "progett", "cantiere", "sicurezza", "psc",
                   "capitolato", "struttur", "ingegner", "architett", "bim", "collaudo",
                   "appalt", "telecom", "tlc", "antenn", "mmwave", "operativ", "milestone",
                   "workflow", "verifica", "agibilit", "monument", "edil", "d.lgs 36",
                   "d-lgs-36", "dpr 380"),
    "legal": ("legal", "contratt", "gdpr", "privacy", "compliance", "antitrust",
              "concorrenza", "nda", "marchio", "societ", "d.lgs", "d-lgs", "normativ",
              "diritto", "penal", "civil", "responsabilit", "clausol", "due diligence",
              "dma", "regolament"),
    "hr": ("hr", "assun", "dipendent", "recruit", "candidat", "onboarding", "ferie",
           "personale", "formazione", "payroll", "cedolino", "organico", "decontribuzione",
           "talent", "colloqui", "offboarding", "welfare"),
}


def _parse_description(text: str) -> str:
    """Extract description from YAML frontmatter or fallback to first line."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        fm = m.group(1)
        d = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        if d:
            return d.group(1).strip().strip('"').strip("'")
        n = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
        if n:
            return n.group(1).strip()
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and line != "---":
            return line
    return ""


class SkillLibrary:
    """Loader multi-base con ricerca e instradamento per dominio."""

    def __init__(self, base: Path | None = None,
                 extra_bases: list[Path] | None = None) -> None:
        bases = [base or _SKILLS_DIR]
        if _LIB_DIR.is_dir() and _LIB_DIR not in bases:
            bases.append(_LIB_DIR)
        for b in (extra_bases or []):
            if b not in bases:
                bases.append(b)
        self._bases = [b for b in bases if b.is_dir()] or [base or _SKILLS_DIR]
        # Retro-compat: base primaria (scrivibile) = la prima. DevelopmentLayer vi crea
        # le nuove skill; il resto legge da tutte le basi.
        self._base = base or self._bases[0]
        self._desc_cache: dict[str, str] = {}
        self._domain_cache: dict[str, list[str]] | None = None

    # ---- risoluzione file (prima base che ha la skill) ----
    def _file(self, name: str) -> Path | None:
        for b in self._bases:
            f = b / name / "SKILL.md"
            if f.is_file():
                return f
        return None

    def names(self) -> list[str]:
        """Unione dei nomi su tutte le basi (dedup, ordine alfabetico)."""
        seen: set[str] = set()
        for b in self._bases:
            for p in b.glob("*/SKILL.md"):
                seen.add(p.parent.name)
        return sorted(seen)

    def load(self, name: str) -> str:
        """Testo pieno di una skill (dalla prima base che la contiene)."""
        f = self._file(name)
        if f is None:
            raise KeyError(name)
        return f.read_text(encoding="utf-8")

    # Sezioni operative: se il playbook è più lungo del budget, meglio il metodo
    # dell'introduzione.
    _SEZIONI_OPERATIVE = ("## metodo", "## come", "## passi", "## procedura",
                          "## processo", "## checklist", "## framework", "## regole",
                          "## output", "## struttura", "## workflow", "## step")

    def estratto(self, name: str, cap: int = 2200) -> str:
        """Il METODO di una skill, non la sua etichetta.

        `load()` ritorna il file intero, frontmatter YAML compreso. Leggerne i primi
        500-700 caratteri — come facevano gli agenti fino al 19 ago 2026 — significa
        dare al modello `name`, `description`, `argument-hint` e il titolo: zero
        metodo. Con 312 playbook in libreria per 3,2 milioni di caratteri, gli agenti
        ne usavano lo 0,1%, e quella parte era intestazione.

        Qui si salta il frontmatter e, se il testo non entra nel budget, si parte dalla
        prima sezione operativa invece che dall'introduzione."""
        testo = self.load(name)
        if testo.startswith("---"):
            fine = testo.find("\n---", 3)
            if fine != -1:
                testo = testo[fine + 4:]
        testo = testo.strip()
        if len(testo) > cap:
            basso = testo.lower()
            inizi = [i for i in (basso.find(s) for s in self._SEZIONI_OPERATIVE) if i > 0]
            if inizi:
                testo = testo[min(inizi):]
        return testo[:cap].strip()

    def describe(self, name: str) -> str:
        """Description della skill (con cache)."""
        if name in self._desc_cache:
            return self._desc_cache[name]
        try:
            d = _parse_description(self.load(name))
        except KeyError:
            d = ""
        self._desc_cache[name] = d
        return d

    def menu(self) -> str:
        """Menu formattato di tutte le skill con description."""
        return self.index(self.names())

    def index(self, names: list[str], desc_len: int = 130) -> str:
        """Righe compatte 'nome: descrizione' per l'indice iniettato all'agente."""
        lines = []
        for n in names:
            d = self.describe(n)
            d = (d[:desc_len] + "…") if len(d) > desc_len else d
            lines.append(f"- {n}: {d}")
        return "\n".join(lines)

    # ---- ricerca su tutta la libreria ----
    def search(self, query: str, k: int = 8) -> list[dict]:
        """Cerca nelle skill per parole della query su nome+description. Ritorna
        [{nome, descrizione}] ordinate per pertinenza. Progressive disclosure: l'agente
        vede solo nome+desc, poi decide cosa caricare."""
        q = (query or "").lower()
        terms = [t for t in re.split(r"[^a-zà-ù0-9]+", q) if len(t) > 2]
        scored: list[tuple[int, str]] = []
        for n in self.names():
            hay = (n.replace("-", " ") + " " + self.describe(n)).lower()
            score = 0
            for t in terms:
                if t in hay:
                    score += 2 if t in n.replace("-", " ") else 1
            if score:
                scored.append((score, n))
        scored.sort(key=lambda x: (-x[0], x[1]))
        out = []
        for _s, n in scored[:k]:
            d = self.describe(n)
            out.append({"nome": n, "descrizione": (d[:200] + "…") if len(d) > 200 else d})
        return out

    # ---- instradamento per reparto (auto-tag, cache) ----
    def _build_domain_map(self) -> dict[str, list[str]]:
        scored: dict[str, list[tuple[int, str]]] = {d: [] for d in _DOMAIN_KW}
        for n in self.names():
            hay = (n.replace("-", " ") + " " + self.describe(n)).lower()
            for dom, kws in _DOMAIN_KW.items():
                s = sum(1 for kw in kws if kw in hay)
                if s:
                    scored[dom].append((s, n))
        out: dict[str, list[str]] = {}
        for dom, lst in scored.items():
            lst.sort(key=lambda x: (-x[0], x[1]))
            out[dom] = [n for _s, n in lst]
        return out

    def for_domain(self, domain: str, k: int = 12) -> list[str]:
        """Le skill più pertinenti a un reparto (auto-tag dalla description, cache)."""
        if self._domain_cache is None:
            self._domain_cache = self._build_domain_map()
        return list(self._domain_cache.get(domain, []))[:k]

    def pick_for(self, domain: str, query: str, k: int = 1) -> list[str]:
        """Le skill del REPARTO più pertinenti a QUESTA richiesta (metodo da applicare).
        Ranking = match della query su nome+descrizione tra le skill del dominio; se
        nulla combacia, ripiega sulle skill di default del reparto."""
        cands = self.for_domain(domain, 40)
        terms = [t for t in re.split(r"[^a-zà-ù0-9]+", (query or "").lower()) if len(t) > 2]
        scored: list[tuple[int, str]] = []
        for n in cands:
            hay = (n.replace("-", " ") + " " + self.describe(n)).lower()
            s = sum((2 if t in n.replace("-", " ") else 1) for t in terms if t in hay)
            if s:
                scored.append((s, n))
        scored.sort(key=lambda x: (-x[0], x[1]))
        picked = [n for _s, n in scored[:k]]
        return picked or self.for_domain(domain, k)
