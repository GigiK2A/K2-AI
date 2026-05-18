"""RAG helpers for K-BOT: chunking, persistence, BM25 retrieval.

Strategia MVP: BM25 in-memory (rank_bm25). Niente embedding/vector DB.
I chunk vivono in `kbot_file_chunks` con page_number → citazioni "(pag. N)"
restituite nel prompt.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional

from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)

CHUNKS_TABLE = "kbot_file_chunks"

# ~1000 token = ~4000 char. Chunk size conservativo per modelli con context grande.
_CHUNK_CHARS = 1500
_CHUNK_OVERLAP = 200

_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ0-9]+", re.UNICODE)


def _split_page(text: str) -> List[str]:
    """Split a single page text into ~1500-char chunks with overlap."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= _CHUNK_CHARS:
        return [text]
    out: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + _CHUNK_CHARS, n)
        out.append(text[start:end])
        if end >= n:
            break
        start = end - _CHUNK_OVERLAP
    return out


def build_chunks_from_pages(
    session_id: str, file_name: str, pages: List[dict]
) -> List[dict]:
    """pages = [{n: int, text: str}, ...]  →  list of chunk rows."""
    rows: List[dict] = []
    idx = 0
    for p in pages:
        page_n = int(p.get("n") or 0)
        text = str(p.get("text") or "")
        for piece in _split_page(text):
            rows.append(
                {
                    "session_id": session_id,
                    "file_name": file_name,
                    "page_number": page_n,
                    "chunk_index": idx,
                    "content": piece,
                }
            )
            idx += 1
    return rows


def persist_chunks(rows: List[dict]) -> None:
    if not rows:
        return
    try:
        client = get_admin_client()
        # Batch insert
        client.table(CHUNKS_TABLE).insert(rows).execute()
    except Exception:
        log.exception("persist_chunks failed (session=%s)", rows[0].get("session_id"))


def fetch_chunks(session_id: str, limit: int = 500) -> List[dict]:
    try:
        client = get_admin_client()
        res = (
            client.table(CHUNKS_TABLE)
            .select("file_name,page_number,chunk_index,content")
            .eq("session_id", session_id)
            .order("chunk_index", desc=False)
            .limit(limit)
            .execute()
        )
        return list(res.data or [])
    except Exception:
        log.exception("fetch_chunks failed (session=%s)", session_id)
        return []


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def bm25_top_k(query: str, chunks: List[dict], k: int = 10) -> List[dict]:
    """Return top-k chunks ranked by BM25 against the query.

    Fallback: if rank_bm25 missing or empty corpus, returns first-k as-is.
    """
    if not chunks:
        return []
    q_tokens = _tokenize(query)
    if not q_tokens:
        return chunks[:k]
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
    except Exception:
        log.warning("rank_bm25 not installed; falling back to first-k")
        return chunks[:k]
    corpus = [_tokenize(c.get("content") or "") for c in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(q_tokens)
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [c for _s, c in ranked[:k] if _s > 0] or chunks[:k]


def format_chunks_for_prompt(chunks: List[dict]) -> str:
    """Render chunks for the system prompt with [pag.N] markers."""
    lines: List[str] = []
    for c in chunks:
        name = (c.get("file_name") or "file").strip()
        page = c.get("page_number") or 0
        text = str(c.get("content") or "").strip()
        if not text:
            continue
        safe = text.replace("</UNTRUSTED_FILE_CONTENT>", "<_/UNTRUSTED_FILE_CONTENT>")
        marker = f"[pag.{page}]" if page else "[pag.?]"
        lines.append(f"--- {name} {marker} ---\n{safe}")
    return "\n\n".join(lines)


def latest_user_message(messages: List[dict]) -> Optional[str]:
    for m in reversed(messages or []):
        if m.get("role") == "user":
            content = str(m.get("content") or "").strip()
            if content:
                return content
    return None
