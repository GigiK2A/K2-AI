"""NT-7.3 — Hybrid retrieval: Reciprocal Rank Fusion (RRF) di FTS5 + semantic.

Combina `search` (FTS5, forte su keyword) e `search_semantic` (forte su NL) con
RRF, più un boost opzionale sui chunk normativi primari (paragrafo non-null) — DN-18.

NB sulla chiave di fusione: `search` ritorna `chunk_id` INTERO (chunks.id), mentre
`search_semantic` ritorna `chunk_id_originale` (stringa). Si fondono mappando gli id
FTS → chunk_id_originale via DB, e usando `chunk_id_originale` come chiave comune.
"""

from __future__ import annotations

from .db import get_connection, init_schema
from .schemas import SearchInput, SearchSemanticInput
from .tools import search, search_semantic


def _retrieve(query: str, documento: str | None, n: int):
    fts = search(SearchInput(query=query, documento=documento, limit=n)).risultati
    sem = search_semantic(SearchSemanticInput(query=query, documento=documento, limit=n)).risultati
    return fts, sem


def rank_lists(query: str, documento: str | None = None, n: int = 20):
    """Ritorna (fts_rank, sem_rank, meta) keyed su chunk_id_originale.

    Separato da search_hybrid così la grid search può fondere a parametri vari
    senza rieseguire i retrieval (costosi: il semantico embedda la query)."""
    fts, sem = _retrieve(query, documento, n)
    conn = get_connection()
    init_schema(conn)
    try:
        # map id intero (FTS) → chunk_id_originale + meta
        fts_ids = [h.chunk_id for h in fts]
        id2orig: dict[int, str] = {}
        meta: dict[str, dict] = {}
        if fts_ids:
            ph = ",".join("?" * len(fts_ids))
            for r in conn.execute(
                f"SELECT c.id, c.chunk_id_originale o, c.paragrafo, c.titolo, c.pagina_pdf_inizio, "
                f"d.codice cod, c.contenuto FROM chunks c JOIN documenti d ON d.id=c.documento_id "
                f"WHERE c.id IN ({ph})", fts_ids
            ):
                id2orig[r["id"]] = r["o"]
                meta[r["o"]] = {"paragrafo": r["paragrafo"], "titolo": r["titolo"],
                                "pagina_pdf": r["pagina_pdf_inizio"], "documento": r["cod"],
                                "snippet": (r["contenuto"] or "")[:300]}
    finally:
        conn.close()

    fts_rank = {id2orig[h.chunk_id]: i for i, h in enumerate(fts) if h.chunk_id in id2orig}
    sem_rank = {}
    for i, h in enumerate(sem):
        sem_rank[h.chunk_id] = i
        meta.setdefault(h.chunk_id, {"paragrafo": h.paragrafo, "titolo": h.titolo,
                                     "pagina_pdf": h.pagina_pdf, "documento": h.documento,
                                     "snippet": h.snippet})
    return fts_rank, sem_rank, meta


def fuse(fts_rank, sem_rank, meta, limit=10, k_rrf=60,
         weights=(1.0, 1.0), boost_primary=True, boost_factor=1.5):
    """RRF + boost opzionale. Ritorna lista ordinata di (chunk_id_originale, score)."""
    all_c = set(fts_rank) | set(sem_rank)
    scores = {}
    for c in all_c:
        s = 0.0
        if c in fts_rank:
            s += weights[0] / (k_rrf + fts_rank[c] + 1)
        if c in sem_rank:
            s += weights[1] / (k_rrf + sem_rank[c] + 1)
        if boost_primary and (meta.get(c, {}).get("paragrafo")):
            s *= boost_factor
        scores[c] = s
    top = sorted(scores, key=scores.get, reverse=True)[:limit]
    return [(c, scores[c]) for c in top]


def search_hybrid(query: str, documento: str | None = None, limit: int = 10,
                  k_rrf: int = 60, weights: tuple[float, float] = (1.0, 1.0),
                  boost_primary: bool = True, boost_factor: float = 2.0) -> dict:
    """Hybrid retrieval RRF (FTS5 + semantic) con boost chunk primari (DN-18)."""
    fts_rank, sem_rank, meta = rank_lists(query, documento, n=20)
    top = fuse(fts_rank, sem_rank, meta, limit, k_rrf, weights, boost_primary, boost_factor)
    risultati = []
    for cid, score in top:
        m = meta.get(cid, {})
        risultati.append({
            "chunk_id": cid, "documento": m.get("documento"), "paragrafo": m.get("paragrafo"),
            "titolo": m.get("titolo"), "snippet": m.get("snippet"),
            "pagina_pdf": m.get("pagina_pdf"), "score": round(score, 5),
        })
    return {"query": query, "totale": len(risultati), "modello": "hybrid-rrf", "risultati": risultati}
