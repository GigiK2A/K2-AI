"""Skill loader, mirroring kai-website/lib/skills/loader.ts.

Layout per skill:
    <SKILLS_DIR>/<name>/SKILL.md         (required)
    <SKILLS_DIR>/<name>/references/*.md  (optional, sorted by filename)

Missing skills are silently skipped with a warning log.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional

from ..settings import SKILLS_DIR

log = logging.getLogger(__name__)


def _skill_root(name: str) -> Path:
    return SKILLS_DIR / name


def list_available_skills() -> List[str]:
    if not SKILLS_DIR.exists():
        return []
    return sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))


@lru_cache(maxsize=512)
def load_skill(name: str, include_references: bool = True, max_chars: Optional[int] = None) -> Optional[str]:
    root = _skill_root(name)
    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        # also accept legacy lowercase
        alt = root / "skills.md"
        if alt.exists():
            skill_md = alt
        else:
            log.warning("Skill not found: %s (looking at %s)", name, root)
            return None

    try:
        parts = [skill_md.read_text(encoding="utf-8")]
    except (OSError, UnicodeDecodeError) as exc:
        log.warning("Failed reading SKILL.md for %s: %s", name, exc)
        return None

    if include_references:
        refs_dir = root / "references"
        if refs_dir.is_dir():
            for ref_path in sorted(refs_dir.glob("*.md")):
                try:
                    parts.append(ref_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError) as exc:
                    log.warning("Skipping non-UTF8 reference %s: %s", ref_path, exc)
                    continue

    content = "\n\n".join(p.strip() for p in parts if p.strip())
    if max_chars and len(content) > max_chars:
        content = content[: max_chars - 1].rstrip() + "…"
    return content


# --- Caricamento per SEZIONI PERTINENTI --------------------------------------------------------------------
# Misurato il 20/10/2026: nella chat entrano solo i primi 5500 caratteri di ogni SKILL.md. Per `fiscale-tributario-italiano`
# (31 KB) sono 1 KB di descrizione + le sezioni 1-3 (raccolta dati, fondamenti costituzionali, obbligazione tributaria): le
# sezioni su IRES, ammortamento, IVA e ravvedimento — quelle che servivano per un computer da 2.500 euro — restavano fuori.
# Qui, a parità di dimensione, si tengono l'introduzione e le sezioni che somigliano alle ultime domande dell'utente.
_STOP_SEZ = set("""che chi con per tra fra una uno dei del della delle degli dello nel nella nelle negli sul sulla sulle sono essere
come cosa quando quanto quanti quale quali anche ancora questo questa questi queste loro suo sua miei nostro nostra possiamo posso
devo dobbiamo vorrei abbiamo hanno fatto fare dopo prima sempre mai molto tutto tutti ogni altro altra altri""".split())
_MAX_UNITA = 2500


def _stem_set(testo: str) -> set:
    return {t[:6] for t in re.findall(r"[a-zàèéìòù]{4,}", (testo or "").lower()) if t not in _STOP_SEZ}


@lru_cache(maxsize=512)
def _sezioni(name: str):
    """(intro, [(titolo, testo)]) del SKILL.md senza frontmatter; le sezioni lunghe si spezzano per sotto-titoli (###)."""
    root = _skill_root(name)
    f = root / "SKILL.md"
    if not f.exists():
        f = root / "skills.md"
    if not f.exists():
        return None
    try:
        t = f.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    t = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", t, count=1, flags=re.S).strip()
    parti = re.split(r"(?m)^(?=## )", t)
    intro = parti[0].strip() if parti and not parti[0].startswith("## ") else ""
    blocchi = [p for p in (parti[1:] if intro or (parti and not parti[0].startswith("## ")) else parti) if p.strip()]
    unita = []
    for b in blocchi:
        titolo = b.splitlines()[0].lstrip("# ").strip()
        if len(b) <= _MAX_UNITA:
            unita.append((titolo, b.strip()))
            continue
        sub = [x for x in re.split(r"(?m)^(?=### )", b) if x.strip()]
        if len(sub) <= 1:
            unita.append((titolo, b.strip()))
            continue
        for k, x in enumerate(sub):
            testo = x.strip() if k == 0 else f"## {titolo} (segue)\n\n{x.strip()}"
            unita.append((titolo if k == 0 else f"{titolo} / {x.splitlines()[0].lstrip('# ').strip()}", testo))
    return intro, unita


def load_skill_pertinente(name: str, query: str, max_chars: int) -> Optional[str]:
    """Introduzione + le sezioni della skill più vicine a `query`, in ordine di lettura, entro `max_chars`.
    Se la skill sta già nel limite, o `query` non assomiglia a nessuna sezione, si comporta come il vecchio taglio
    (ma senza il frontmatter). Mai più lunga di `max_chars`."""
    dati = _sezioni(name)
    if dati is None:
        return None
    intro, unita = dati
    intro = intro[:900].rstrip()
    corpo_intero = "\n\n".join(x for x in [intro] + [u[1] for u in unita] if x)
    if len(corpo_intero) <= max_chars:
        return corpo_intero
    q = _stem_set(query)
    punteggi = []
    for i, (titolo, testo) in enumerate(unita):
        if not q:
            punteggi.append((0, i))
            continue
        st_t, st_x = _stem_set(titolo), _stem_set(testo)
        punteggi.append((3 * len(q & st_t) + len(q & st_x), i))
    if not any(p for p, _ in punteggi):
        scelte = list(range(len(unita)))                      # nessuna somiglianza: ordine del file
    else:
        scelte = [i for p, i in sorted(punteggi, key=lambda x: (-x[0], x[1])) if p > 0]
    budget = max_chars - len(intro) - 2
    prese, usati = [], 0
    for i in scelte:
        testo = unita[i][1]
        if usati + len(testo) + 2 <= budget:
            prese.append(i)
            usati += len(testo) + 2
        elif budget - usati > 700 and not prese:
            prese.append(i)                                   # almeno una sezione, anche se lunga: si tronca sotto
            usati = budget
            break
    corpo = "\n\n".join(x for x in [intro] + [unita[i][1] for i in sorted(prese)] if x)
    if len(corpo) > max_chars:
        corpo = corpo[: max_chars - 1].rstrip() + "…"
    return corpo


def load_skill_bundle(
    names: Iterable[str],
    *,
    max_total_chars: int,
    max_per_skill_chars: int = 5500,
    include_references: bool = False,
    query: str = "",
) -> str:
    """Build a single string with header per skill, capped to total chars."""
    pieces: List[str] = []
    total = 0
    for name in names:
        if not name:
            continue
        if query and not include_references:
            body = load_skill_pertinente(name, query, max_per_skill_chars)
        else:
            body = load_skill(name, include_references=include_references, max_chars=max_per_skill_chars)
        if not body:
            continue
        header = f"\n{'=' * 60}\n# SKILL: {name}\n{'=' * 60}\n\n"
        chunk = header + body
        if total + len(chunk) > max_total_chars:
            remaining = max_total_chars - total
            if remaining > len(header) + 200:
                chunk = chunk[:remaining].rstrip() + "…"
                pieces.append(chunk)
                total += len(chunk)
            break
        pieces.append(chunk)
        total += len(chunk)
    return "".join(pieces)
