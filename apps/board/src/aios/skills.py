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

# Override espliciti: skill (spesso inglesi generiche o meta-skill di framework) che
# nessuna keyword italiana instrada. Assegnate a mano al reparto sensato → zero orfane.
# Entrano nel pool del reparto in CODA (score 0), quindi non spingono via le skill
# taggate per keyword; restano raggiungibili nell'indice e via search.
_DOMAIN_OVERRIDE: dict[str, tuple[str, ...]] = {
    # business per reparto
    "comp-analysis": ("hr",), "org-planning": ("hr",), "standup": ("hr", "operations"),
    "competitive-intelligence": ("marketing", "vendite"),
    "product-brainstorming": ("marketing",), "metrics-review": ("finance", "marketing"),
    "risk-assessment": ("operations", "legal"), "ticket-triage": ("operations",),
    "kb-article": ("operations", "marketing"), "process-doc": ("operations",),
    "change-request": ("operations",), "runbook": ("operations",),
    "report-premium-design": ("operations",), "cci-impianti-produzione": ("operations",),
    "draft-response": ("vendite", "operations"), "signature-request": ("legal",),
    "policy-lookup": ("legal", "hr"),
    # dati/analytics → finance (reporting) e dove serve
    "analyze": ("finance", "operations"), "sql-queries": ("finance", "operations"),
    "write-query": ("finance", "operations"), "validate-data": ("finance",),
    "create-viz": ("finance", "marketing"), "data-visualization": ("finance", "marketing"),
    # tecniche/dev/design → operations (reparto tecnico); design anche marketing
    "accessibility-review": ("operations", "marketing"), "api-integration": ("operations",),
    "architecture": ("operations",), "code-review": ("operations",), "debug": ("operations",),
    "tech-debt": ("operations",), "testing-strategy": ("operations",),
    "design-critique": ("operations", "marketing"), "design-handoff": ("operations",),
    "design-system": ("operations", "marketing"), "write-spec": ("operations",),
    "pdf": ("operations",),
    # meta/framework → operations (tooling interno), così niente resta orfano
    "search": ("operations",), "search-strategy": ("operations",),
    "source-management": ("operations",), "task-management": ("operations",),
    "schedule": ("operations",), "digest": ("operations",), "update": ("operations",),
    "start": ("operations",), "setup-cowork": ("operations",), "skill-creator": ("operations",),
    "consolidate-memory": ("operations",), "memory-management": ("operations",),
}


def _parse_description(text: str) -> str:
    """Extract description from YAML frontmatter or fallback to first line.
    Gestisce i block scalar YAML (`>`, `>-`, `|`, `|-`, …): senza questo, una
    `description: >-` multilinea veniva letta come ">-" (descrizione vuota → skill
    non instradabile a nessun reparto)."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if m:
        fm = m.group(1)
        lines = fm.splitlines()
        for i, line in enumerate(lines):
            dm = re.match(r"^description:\s*(.*)$", line)
            if not dm:
                continue
            val = dm.group(1).strip()
            # block scalar (indicatore > | eventualmente con +/- o vuoto) → raccogli
            # le righe indentate seguenti fino alla prossima chiave di frontmatter.
            if val == "" or val[0] in "|>":
                collected = []
                for nxt in lines[i + 1:]:
                    if nxt.strip() == "":
                        continue
                    if re.match(r"^\s+\S", nxt):     # indentata = corpo del blocco
                        collected.append(nxt.strip())
                    else:                             # de-indentata = nuova chiave → stop
                        break
                joined = " ".join(collected).strip()
                if joined:
                    return joined
            else:
                return val.strip('"').strip("'")
            break
        n = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
        if n:
            return n.group(1).strip().strip('"').strip("'")
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
        scored: dict[str, dict[str, int]] = {d: {} for d in _DOMAIN_KW}
        for n in self.names():
            hay = (n.replace("-", " ") + " " + self.describe(n)).lower()
            for dom, kws in _DOMAIN_KW.items():
                s = sum(1 for kw in kws if kw in hay)
                if s:
                    scored[dom][n] = s
        # override espliciti (score 0 = in coda al reparto, dopo i match per keyword)
        for name, doms in _DOMAIN_OVERRIDE.items():
            for dom in doms:
                if dom in scored and name not in scored[dom]:
                    scored[dom][name] = 0
        out: dict[str, list[str]] = {}
        for dom, d in scored.items():
            out[dom] = [n for n, _s in sorted(d.items(), key=lambda x: (-x[1], x[0]))]
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
