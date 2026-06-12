"""Implementazione dei tool MCP (versione stub: KB vuota in NT-1).

Le funzioni interrogano il DB e ritornano modelli pydantic (testabili a unita').
I wrapper FastMCP in server.py serializzano via model_dump.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from .db import EMBED_CACHE_DIR, EMBED_MODEL, get_connection, init_schema, load_vec
from .schemas import (
    ArticoloHit,
    CercaArticoloInput,
    CercaArticoloOutput,
    DocumentoItem,
    FreschezzaOutput,
    GetCapitoloInput,
    GetCapitoloOutput,
    GetDocumentoInput,
    GetDocumentoOutput,
    GetParagrafoInput,
    GetParagrafoOutput,
    ListaDocumentiOutput,
    ParteChunk,
    SearchHit,
    SearchInput,
    SearchOutput,
    SearchSemanticInput,
    SearchSemanticOutput,
    SemanticHit,
)

# Embedder fastembed caricato pigramente e riusato (cold-start ~1-2s una sola volta).
_EMBEDDER = None
_EMBEDDER_MODEL: str | None = None


def _get_embedder(model: str):
    global _EMBEDDER, _EMBEDDER_MODEL
    if _EMBEDDER is None or _EMBEDDER_MODEL != model:
        import warnings

        from fastembed import TextEmbedding  # import locale: dipendenza opzionale

        # Fix B (M-infra-1): sopprime il warning fastembed "mean pooling vs CLS embedding".
        # Informativo, nessun impatto funzionale; inquinava i log MCP ad ogni search_semantic.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*mean pooling.*",
                category=UserWarning,
            )
            warnings.filterwarnings(
                "ignore",
                message=".*CLS embedding.*",
                category=UserWarning,
            )
            EMBED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _EMBEDDER = TextEmbedding(model_name=model, cache_dir=str(EMBED_CACHE_DIR))
        _EMBEDDER_MODEL = model
    return _EMBEDDER


def _chunk_suffix(chunk_id: str | None) -> int | None:
    """Estrae il numero progressivo in coda al chunk_id (es. 'TU81_2026_01573' -> 1573).

    I chunk_id sono zero-padded → il sort lessicografico coincide col numerico, ma per
    decidere la *consecutività* (DN-11) serve il valore intero del suffisso.
    """
    if not chunk_id:
        return None
    m = re.search(r"(\d+)$", chunk_id)
    return int(m.group(1)) if m else None


def _conn():
    """Connessione con schema garantito (idempotente su KB vuota/nuova)."""
    conn = get_connection()
    init_schema(conn)
    return conn


def freschezza() -> FreschezzaOutput:
    conn = _conn()
    try:
        doc_count = conn.execute("SELECT COUNT(*) FROM documenti").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        last = conn.execute("SELECT MAX(data_ingestione) FROM documenti").fetchone()[0]
        last_dt = datetime.fromisoformat(last) if last else None
        codici = [
            r[0]
            for r in conn.execute(
                "SELECT codice FROM documenti ORDER BY codice"
            ).fetchall()
        ]
    finally:
        conn.close()

    # Nota di copertura DINAMICA, basata sui conteggi reali.
    if chunk_count == 0:
        nota = (
            "MCP k2a-mcp-norme-tecniche scaffold iniziale (NT-1). "
            "KB vuota. Ingestione prevista nelle fasi NT-1B/NT-2."
        )
    else:
        nota = (
            f"KB popolata con {chunk_count} chunks da {doc_count} documenti: "
            f"{', '.join(codici)}. "
            "Pulizia mirata sezioni critiche prevista in NT-2 (cfr. QUALITY_AUDIT.md)."
        )

    return FreschezzaOutput(
        totale_documenti=doc_count,
        totale_chunks=chunk_count,
        ultimo_aggiornamento=last_dt,
        nota_copertura=nota,
    )


def lista_documenti() -> ListaDocumentiOutput:
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT codice, titolo, anno, fonte, n_capitoli, n_paragrafi, n_chunks, "
            "vigenza, document_type FROM documenti ORDER BY anno DESC, codice"
        ).fetchall()
    finally:
        conn.close()

    docs = [DocumentoItem(**dict(r)) for r in rows]
    return ListaDocumentiOutput(totale=len(docs), documenti=docs)


def search(inp: SearchInput) -> SearchOutput:
    conn = _conn()
    try:
        sql = """
        SELECT c.id AS chunk_id, d.codice AS documento, c.paragrafo, c.titolo,
               snippet(chunks_fts, 2, '«', '»', '…', 16) AS snippet,
               bm25(chunks_fts) AS rank,
               c.pagina_pdf_inizio AS pagina_pdf
        FROM chunks_fts
        JOIN chunks c ON chunks_fts.rowid = c.id
        JOIN documenti d ON c.documento_id = d.id
        WHERE chunks_fts MATCH ?
        """
        params: list = [inp.query]
        if inp.documento:
            sql += " AND d.codice = ?"
            params.append(inp.documento)
        if inp.capitolo:
            sql += " AND c.capitolo = ?"
            params.append(inp.capitolo)
        sql += " ORDER BY rank LIMIT ?"
        params.append(inp.limit)
        rows = conn.execute(sql, params).fetchall()
    except Exception:
        # FTS5 puo' lanciare su KB vuota o query malformata: degrada a 0 risultati.
        rows = []
    finally:
        conn.close()

    hits = [SearchHit(**dict(r)) for r in rows]
    return SearchOutput(query=inp.query, totale=len(hits), risultati=hits)


_ART_NUM_RE = re.compile(r"Articolo\s+(\d+(?:[\-\s](?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies))?)", re.I)


def cerca_articolo(inp: CercaArticoloInput) -> CercaArticoloOutput:
    """Trova l'ARTICOLO pertinente per tema, cercando tra i TITOLI degli articoli.

    NT-5 (article-heading boost): risolve la debolezza di `search`/`search_semantic`
    sulle intestazioni (es. "sanzioni omessa valutazione" non faceva emergere l'art. 55).
    Cerca con FTS5 ristretto al campo `titolo` sui chunk-intestazione ("Articolo NN - …"),
    estrae il numero dal titolo (robusto ai chunk d'indice con `paragrafo` NULL) e
    risolve la pagina del CORPO. Ritorna i candidati: il consumer poi chiama `get_paragrafo`.
    """
    toks = [t for t in re.findall(r"\w+", inp.query.lower()) if len(t) > 2]
    if not toks:
        return CercaArticoloOutput(query=inp.query, totale=0, risultati=[])
    match = "titolo : (" + " OR ".join(toks) + ")"

    conn = _conn()
    try:
        sql = (
            "SELECT c.titolo AS titolo, d.codice AS codice, c.documento_id AS did "
            "FROM chunks_fts JOIN chunks c ON chunks_fts.rowid = c.id "
            "JOIN documenti d ON c.documento_id = d.id "
            "WHERE chunks_fts MATCH ? AND c.titolo LIKE 'Articolo %'"
        )
        params: list = [match]
        if inp.documento:
            sql += " AND d.codice = ?"
            params.append(inp.documento.strip())
        sql += " ORDER BY bm25(chunks_fts) LIMIT 60"
        try:
            rows = conn.execute(sql, params).fetchall()
        except Exception:
            rows = []

        seen: set = set()
        risultati: list[ArticoloHit] = []
        for r in rows:
            m = _ART_NUM_RE.match(r["titolo"].strip())
            if not m:
                continue
            # normalizza "286 bis"/"286-bis" -> "286-bis"; "55" -> "55"
            numero = re.sub(r"\s+", "-", m.group(1).strip()).lower()
            key = (r["codice"], numero)
            if key in seen:
                continue
            seen.add(key)
            titolo_clean = re.sub(r"\.{3,}.*$", "", r["titolo"]).strip(" .")
            # pagina del CORPO (chunk con paragrafo == numero), non dell'indice
            body = conn.execute(
                "SELECT pagina_pdf_inizio FROM chunks WHERE documento_id = ? AND paragrafo = ? "
                "ORDER BY chunk_id_originale LIMIT 1",
                (r["did"], numero),
            ).fetchone()
            risultati.append(ArticoloHit(
                numero=numero,
                titolo=titolo_clean,
                documento=r["codice"],
                pagina_pdf=body["pagina_pdf_inizio"] if body else None,
            ))
            if len(risultati) >= inp.limit:
                break
    finally:
        conn.close()

    return CercaArticoloOutput(query=inp.query, totale=len(risultati), risultati=risultati)


def get_documento(inp: GetDocumentoInput) -> GetDocumentoOutput:
    conn = _conn()
    try:
        doc = conn.execute(
            "SELECT codice, titolo, n_chunks FROM documenti WHERE codice = ?",
            (inp.documento,),
        ).fetchone()
        if not doc:
            return GetDocumentoOutput(
                codice=inp.documento, titolo="", n_chunks=0, capitoli=[], trovato=False
            )
        capitoli = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT capitolo FROM chunks WHERE documento_id = "
                "(SELECT id FROM documenti WHERE codice = ?) ORDER BY capitolo",
                (inp.documento,),
            ).fetchall()
            if r[0]
        ]
    finally:
        conn.close()

    return GetDocumentoOutput(
        codice=doc["codice"], titolo=doc["titolo"], n_chunks=doc["n_chunks"],
        capitoli=capitoli, trovato=True,
    )


def get_capitolo(inp: GetCapitoloInput) -> GetCapitoloOutput:
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT paragrafo, contenuto FROM chunks "
            "WHERE documento_id = (SELECT id FROM documenti WHERE codice = ?) "
            "AND capitolo = ? ORDER BY paragrafo",
            (inp.documento, inp.capitolo),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return GetCapitoloOutput(
            documento=inp.documento, capitolo=inp.capitolo,
            paragrafi=[], contenuto_completo=None, trovato=False,
        )

    # I chunk d'indice/frontmatter possono avere paragrafo NULL (cfr. soppressione
    # TOC dell'ingest TU 81/08): si filtrano dalla lista identificatori, ma il loro
    # contenuto resta nel testo completo del capitolo.
    paragrafi = [r["paragrafo"] for r in rows if r["paragrafo"]]
    contenuto = "\n\n---\n\n".join(r["contenuto"] for r in rows)
    return GetCapitoloOutput(
        documento=inp.documento, capitolo=inp.capitolo,
        paragrafi=paragrafi, contenuto_completo=contenuto, trovato=True,
    )


def search_semantic(inp: SearchSemanticInput) -> SearchSemanticOutput:
    """Ricerca semantica (kNN su embeddings locali) complementare alla FTS5 lessicale.

    NT-3. Trova chunk per *significato* anche senza overlap di parole (sinonimi,
    parafrasi). L'indice vettoriale (`chunks_vec`, sqlite-vec) va popolato con
    `scripts/embed_chunks.py`; se assente/vuoto ritorna `disponibile=False`.
    """
    import numpy as np

    conn = get_connection()
    try:
        init_schema(conn)
        if not load_vec(conn):
            return SearchSemanticOutput(
                query=inp.query, totale=0, modello=EMBED_MODEL,
                risultati=[], disponibile=False,
            )
        # Indice pronto?
        has_index = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks_vec'"
        ).fetchone()
        n_vec = conn.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0] if has_index else 0
        if not n_vec:
            return SearchSemanticOutput(
                query=inp.query, totale=0, modello=EMBED_MODEL,
                risultati=[], disponibile=False,
            )

        qv = np.asarray(
            list(_get_embedder(EMBED_MODEL).embed([inp.query]))[0], dtype=np.float32
        ).tobytes()

        # Filtro opzionale per documento (documento_id è colonna metadata di vec0).
        doc_id = None
        if inp.documento:
            row = conn.execute(
                "SELECT id FROM documenti WHERE codice = ?", (inp.documento.strip(),)
            ).fetchone()
            if row is None:
                return SearchSemanticOutput(
                    query=inp.query, totale=0, modello=EMBED_MODEL, risultati=[],
                )
            doc_id = row["id"]

        if doc_id is not None:
            knn = (
                "SELECT chunk_id, distance FROM chunks_vec "
                "WHERE embedding MATCH ? AND k = ? AND documento_id = ?"
            )
            params = (qv, inp.limit, doc_id)
        else:
            knn = "SELECT chunk_id, distance FROM chunks_vec WHERE embedding MATCH ? AND k = ?"
            params = (qv, inp.limit)

        rows = conn.execute(
            f"WITH knn AS ({knn}) "
            "SELECT k.distance AS distance, c.chunk_id_originale AS cid, d.codice AS codice, "
            "       c.paragrafo AS paragrafo, c.titolo AS titolo, c.contenuto AS contenuto, "
            "       c.pagina_pdf_inizio AS pagina "
            "FROM knn k JOIN chunks c ON c.id = k.chunk_id "
            "JOIN documenti d ON d.id = c.documento_id ORDER BY k.distance",
            params,
        ).fetchall()
    finally:
        conn.close()

    risultati = [
        SemanticHit(
            chunk_id=r["cid"],
            documento=r["codice"],
            paragrafo=r["paragrafo"],
            titolo=r["titolo"],
            snippet=(r["contenuto"] or "")[:300],
            distanza=round(float(r["distance"]), 4),
            pagina_pdf=r["pagina"],
        )
        for r in rows
    ]
    return SearchSemanticOutput(
        query=inp.query, totale=len(risultati), modello=EMBED_MODEL, risultati=risultati,
    )


def get_paragrafo(inp: GetParagrafoInput) -> GetParagrafoOutput:
    """Testo di un paragrafo, aggregando i chunk multipli quando presenti (DN-11, NT-2.6).

    Contract esteso e backward-compatible:
    - caso mono-chunk: identico a prima (nessun campo `n_parts`/`parts`);
    - caso multi-chunk: si aggregano SOLO i chunk con `chunk_id` CONSECUTIVI a partire
      dal primo match (le parti reali di un articolo sono un run contiguo; numeri di
      paragrafo che si ripetono altrove nel documento — collisioni, es. IEC/CEI — NON
      vengono fusi). Si aggiungono `n_parts` e `parts` e si mantiene `contenuto` come
      testo unico (parti separate da "\\n\\n").

    Non-found e mono-chunk impostano sempre tutti i campi base, così il server può
    serializzare con `exclude_unset` omettendo solo `n_parts`/`parts`.
    """
    # Normalizzazione input (robustezza su whitespace accidentale).
    documento_norm = inp.documento.strip()
    paragrafo_norm = inp.paragrafo.strip()

    conn = _conn()
    try:
        # Query robusta: matcha paragrafo OR section_code (resiliente a pacchetti in
        # cui solo `section_code` fosse popolato). Ordine per chunk_id_originale →
        # ordine documentale deterministico (i chunk_id sono zero-padded).
        rows = conn.execute(
            "SELECT chunk_id_originale, paragrafo, section_code, titolo, contenuto, "
            "pagina_pdf_inizio, pagina_pdf_fine, tags, ntc_riferimento FROM chunks "
            "WHERE documento_id = (SELECT id FROM documenti WHERE codice = ?) "
            "AND (paragrafo = ? OR section_code = ?) "
            "ORDER BY chunk_id_originale",
            (documento_norm, paragrafo_norm, paragrafo_norm),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        # Diagnostica utile in caso di miss (visibile nei log MCP/stderr).
        print(
            f"[get_paragrafo] nessun match: documento={documento_norm!r} "
            f"paragrafo/section_code={paragrafo_norm!r}"
        )
        return GetParagrafoOutput(
            documento=inp.documento,
            paragrafo=inp.paragrafo,
            titolo=None,
            contenuto=None,
            pagina_pdf_inizio=None,
            pagina_pdf_fine=None,
            tags=[],
            ntc_riferimento=None,
            trovato=False,
        )

    # Run consecutivo ancorato al primo match: include i chunk il cui suffisso
    # numerico è contiguo. Si ferma alla prima discontinuità (collisione altrove).
    run = [rows[0]]
    last = _chunk_suffix(rows[0]["chunk_id_originale"])
    for r in rows[1:]:
        s = _chunk_suffix(r["chunk_id_originale"])
        if last is not None and s == last + 1:
            run.append(r)
            last = s
        else:
            break

    paragrafo_val = rows[0]["paragrafo"] or rows[0]["section_code"]

    # Caso A — mono-chunk: contract identico a prima (niente n_parts/parts).
    if len(run) == 1:
        r = run[0]
        return GetParagrafoOutput(
            documento=inp.documento,
            paragrafo=paragrafo_val,
            titolo=r["titolo"],
            contenuto=r["contenuto"],
            pagina_pdf_inizio=r["pagina_pdf_inizio"],
            pagina_pdf_fine=r["pagina_pdf_fine"],
            tags=json.loads(r["tags"]) if r["tags"] else [],
            ntc_riferimento=r["ntc_riferimento"],
            trovato=True,
        )

    # Caso B — multi-chunk: aggrega il run.
    contenuto = "\n\n".join(r["contenuto"] for r in run if r["contenuto"])
    pagine_inizio = [r["pagina_pdf_inizio"] for r in run if r["pagina_pdf_inizio"] is not None]
    pagine_fine = [r["pagina_pdf_fine"] for r in run if r["pagina_pdf_fine"] is not None]
    titolo = next((r["titolo"] for r in run if r["titolo"]), None)
    ntc_rif = next((r["ntc_riferimento"] for r in run if r["ntc_riferimento"]), None)
    # tags = union ordinata (prima-vista) dei topic delle parti.
    tags: list[str] = []
    for r in run:
        for t in (json.loads(r["tags"]) if r["tags"] else []):
            if t not in tags:
                tags.append(t)

    return GetParagrafoOutput(
        documento=inp.documento,
        paragrafo=paragrafo_val,
        titolo=titolo,
        contenuto=contenuto,
        pagina_pdf_inizio=min(pagine_inizio) if pagine_inizio else None,
        pagina_pdf_fine=max(pagine_fine) if pagine_fine else None,
        tags=tags,
        ntc_riferimento=ntc_rif,
        trovato=True,
        n_parts=len(run),
        parts=[
            ParteChunk(
                chunk_id=r["chunk_id_originale"],
                contenuto=r["contenuto"],
                pagina_pdf_inizio=r["pagina_pdf_inizio"],
                pagina_pdf_fine=r["pagina_pdf_fine"],
            )
            for r in run
        ],
    )
