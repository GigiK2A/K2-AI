from __future__ import annotations

import re
from typing import Any

_WORD = re.compile(r"[a-zà-ù0-9]{3,}")


def _chunks(text: str, size: int = 900) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    paras = re.split(r"\n\s*\n", text)
    out, buf = [], ""
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if buf and len(buf) + len(p) > size:
            out.append(buf.strip())
            buf = p
        else:
            buf = (buf + "\n\n" + p) if buf else p
    if buf.strip():
        out.append(buf.strip())
    # hard-split any chunk still much larger than size
    final = []
    for c in out:
        while len(c) > size * 2:
            final.append(c[:size])
            c = c[size:]
        final.append(c)
    return [c for c in final if c.strip()]


def _terms(s: str) -> set[str]:
    return set(_WORD.findall((s or "").lower()))


class KnowledgeStore:
    """Strato ① Contesto: base di conoscenza interrogabile (su Supabase aios_knowledge)."""

    def __init__(self, client: Any) -> None:
        self._c = client

    def add(
        self,
        *,
        source: str,
        chunk: str,
        titolo: str | None = None,
        tags: str | None = None,
    ) -> Any:
        return self._c.insert(
            "aios_knowledge",
            {"source": source, "chunk": chunk, "titolo": titolo, "tags": tags},
        )

    def ingest_text(
        self,
        *,
        source: str,
        text: str,
        titolo: str | None = None,
        chunk_size: int = 900,
    ) -> int:
        n = 0
        for c in _chunks(text, chunk_size):
            self.add(source=source, chunk=c, titolo=titolo)
            n += 1
        return n

    def search(self, query: str, k: int = 5) -> list[str]:
        rows = self._c.select("aios_knowledge", {"select": "*"})
        qt = _terms(query)
        scored = []
        for r in rows:
            score = len(qt & _terms(r.get("chunk", "")))
            if score:
                scored.append((score, r["chunk"]))
        scored.sort(key=lambda x: -x[0])
        return [c for _, c in scored[:k]]
