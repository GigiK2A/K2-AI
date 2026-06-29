"""Schema SQLite + FTS5 + utility di connessione.

Pattern ereditato dal MCP fratello `normattiva` (FTS5 + SQLite), ma con schema
ricco purpose-built per norme tecniche gerarchiche (documenti -> capitoli ->
paragrafi). Il file .db non e' versionato: e' ricostruibile dai chunks.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# Path del .db: override via env NORME_DB_PATH (deploy 8e → volume /corpus, come
# normattiva). Default = data/norme_tecniche.db (bundle locale / dev). Il .db non e'
# versionato (binario): in prod arriva sul volume via download-al-boot (seed_corpus.py).
DB_PATH = (Path(os.environ["NORME_DB_PATH"]) if os.environ.get("NORME_DB_PATH")
           else Path(__file__).resolve().parent.parent.parent / "data" / "norme_tecniche.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice TEXT UNIQUE NOT NULL,        -- es. "circolare_7_2019", "ntc_2018"
    titolo TEXT NOT NULL,
    anno INTEGER,
    fonte TEXT,                          -- "CSLP", "MIT", "CEN", "UNI"
    n_capitoli INTEGER DEFAULT 0,
    n_paragrafi INTEGER DEFAULT 0,
    n_chunks INTEGER DEFAULT 0,
    data_ingestione DATETIME DEFAULT CURRENT_TIMESTAMP,
    vigenza TEXT DEFAULT 'vigente'       -- 'vigente' | 'storica'
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER NOT NULL REFERENCES documenti(id),
    capitolo TEXT,                       -- es. "C4"
    sezione TEXT,                        -- es. "C4.1"
    paragrafo TEXT,                      -- es. "C4.1.2.2.4" (nullable: i chunk di frontmatter non hanno section_code)
    titolo TEXT,
    pagina_pdf_inizio INTEGER,
    pagina_pdf_fine INTEGER,
    livello INTEGER,                     -- 1=cap, 2=sez, 3=par, 4=sotto-par
    contenuto TEXT NOT NULL,
    contiene_formule INTEGER DEFAULT 0,  -- bool (sqlite int)
    contiene_tabelle INTEGER DEFAULT 0,
    contiene_esempi_worked INTEGER DEFAULT 0,
    ntc_riferimento TEXT,                -- per Circolare: es. "NTC 2018 §4.1.2.2.4"
    tags TEXT,                           -- JSON array
    file_md_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_chunks_documento ON chunks(documento_id);
CREATE INDEX IF NOT EXISTS idx_chunks_paragrafo ON chunks(documento_id, paragrafo);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    paragrafo,
    titolo,
    contenuto,
    tags,
    content='chunks',
    content_rowid='id',
    tokenize='unicode61'
);

-- Triggers di sync chunks <-> chunks_fts
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, paragrafo, titolo, contenuto, tags)
    VALUES (new.id, new.paragrafo, new.titolo, new.contenuto, new.tags);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, paragrafo, titolo, contenuto, tags)
    VALUES('delete', old.id, old.paragrafo, old.titolo, old.contenuto, old.tags);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, paragrafo, titolo, contenuto, tags)
    VALUES('delete', old.id, old.paragrafo, old.titolo, old.contenuto, old.tags);
    INSERT INTO chunks_fts(rowid, paragrafo, titolo, contenuto, tags)
    VALUES (new.id, new.paragrafo, new.titolo, new.contenuto, new.tags);
END;
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Apre connessione SQLite con foreign keys ON e row_factory dict-like."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Crea tabelle, indici, virtual table FTS5 e triggers se non esistono."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def upgrade_schema_nt1b(conn: sqlite3.Connection) -> None:
    """Aggiunge le colonne per l'ingest del pacchetto AI-chunked (NT-1B).

    Idempotente: verifica PRAGMA table_info prima di ogni ALTER. Non rinomina
    nulla (vincolo §12.11): `paragrafo` resta il campo principale (convenzione
    masterplan), `section_code` è aggiunto come campo separato.
    """
    cols_documenti = {r[1] for r in conn.execute("PRAGMA table_info(documenti)").fetchall()}
    cols_chunks = {r[1] for r in conn.execute("PRAGMA table_info(chunks)").fetchall()}

    statements: list[str] = []
    if "document_type" not in cols_documenti:
        statements.append("ALTER TABLE documenti ADD COLUMN document_type TEXT")
    if "chunk_id_originale" not in cols_chunks:
        statements.append("ALTER TABLE chunks ADD COLUMN chunk_id_originale TEXT")
    if "section_code" not in cols_chunks:
        statements.append("ALTER TABLE chunks ADD COLUMN section_code TEXT")
    if "part" not in cols_chunks:
        statements.append("ALTER TABLE chunks ADD COLUMN part INTEGER DEFAULT 1")
    if "sha1_originale" not in cols_chunks:
        statements.append("ALTER TABLE chunks ADD COLUMN sha1_originale TEXT")
    if "content_sha1" not in cols_chunks:
        statements.append("ALTER TABLE chunks ADD COLUMN content_sha1 TEXT")

    for stmt in statements:
        conn.execute(stmt)

    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_chunk_id_orig "
        "ON chunks(chunk_id_originale)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_section_code "
        "ON chunks(documento_id, section_code)"
    )
    conn.commit()
    print(f"Schema upgrade NT-1B applicato: {len(statements)} ALTER TABLE.")


def upgrade_schema_nt2(conn: sqlite3.Connection) -> None:
    """Aggiunge le colonne per il tracciamento della pulizia NT-2.

    Idempotente: verifica PRAGMA table_info prima di ogni ALTER.
    - cleaned_in_nt2: bool (0/1) — chunk rifinito in NT-2.
    - cleaned_at: timestamp ISO della pulizia.
    - cleaning_method: es. 'pdfplumber_v1'.
    - source_pdf_pages: JSON {"pdf": ..., "pages": [start, end]}.
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(chunks)").fetchall()}

    statements: list[str] = []
    if "cleaned_in_nt2" not in cols:
        statements.append("ALTER TABLE chunks ADD COLUMN cleaned_in_nt2 INTEGER DEFAULT 0")
    if "cleaned_at" not in cols:
        statements.append("ALTER TABLE chunks ADD COLUMN cleaned_at DATETIME")
    if "cleaning_method" not in cols:
        statements.append("ALTER TABLE chunks ADD COLUMN cleaning_method TEXT")
    if "source_pdf_pages" not in cols:
        statements.append("ALTER TABLE chunks ADD COLUMN source_pdf_pages TEXT")

    for stmt in statements:
        conn.execute(stmt)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_cleaned ON chunks(cleaned_in_nt2)")
    conn.commit()
    print(f"Schema upgrade NT-2 applicato: {len(statements)} ALTER TABLE.")


def upgrade_schema_nt2_1(conn: sqlite3.Connection) -> None:
    """NT-2.1: colonna `ocr_formulas` (JSON) per le formule recuperate via Gemini Vision.

    Idempotente. Il `contenuto` originale NON viene sovrascritto: le formule sono
    appese in coda e duplicate in `ocr_formulas` come JSON strutturato.
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(chunks)").fetchall()}
    if "ocr_formulas" not in cols:
        conn.execute("ALTER TABLE chunks ADD COLUMN ocr_formulas TEXT")
        print("Schema upgrade NT-2.1 applicato: +ocr_formulas.")
    else:
        print("Schema upgrade NT-2.1: ocr_formulas già presente.")
    conn.commit()


# --- NT-3: ricerca semantica (embeddings locali + sqlite-vec) -----------------
# Modello di embedding di default (fastembed, locale, multilingue, torch-free).
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384
# Cache modello FISSA e persistente (NON il tempdir di default di fastembed, che è
# /tmp/fastembed_cache: non deterministico tra processi, soggetto a pulizia, e causa
# un download dentro la prima richiesta MCP → timeout). Condivisa tra pipeline e server.
EMBED_CACHE_DIR = DB_PATH.parent / "fastembed_cache"


def load_vec(conn: sqlite3.Connection) -> bool:
    """Carica l'estensione sqlite-vec sulla connessione. Ritorna False se assente.

    Isolata in una funzione perché il caricamento di estensioni va abilitato
    esplicitamente e fallisce silenziosamente in ambienti senza sqlite-vec.
    """
    try:
        import sqlite_vec  # import locale: dipendenza opzionale (extra "semantic")
    except ImportError:
        return False
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return True


def upgrade_schema_nt3(conn: sqlite3.Connection) -> None:
    """NT-3: virtual table vettoriale + meta per embedding idempotente.

    - `chunks_vec` (vec0): embedding per chunk, con `documento_id` come colonna
      metadata per il filtro kNN per documento.
    - `chunks_embed_meta`: traccia (content_sha1, model) per re-embeddare solo i
      chunk cambiati o non ancora processati.
    Richiede sqlite-vec: se assente, no-op con avviso.
    """
    if not load_vec(conn):
        print("Schema upgrade NT-3: sqlite-vec non disponibile (extra 'semantic') — skip.")
        return
    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0("
        f"  chunk_id INTEGER PRIMARY KEY,"
        f"  documento_id INTEGER,"
        f"  embedding float[{EMBED_DIM}]"
        f")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chunks_embed_meta ("
        "  chunk_id INTEGER PRIMARY KEY REFERENCES chunks(id),"
        "  content_sha1 TEXT,"
        "  model TEXT"
        ")"
    )
    conn.commit()
    print("Schema upgrade NT-3 applicato: chunks_vec + chunks_embed_meta.")
