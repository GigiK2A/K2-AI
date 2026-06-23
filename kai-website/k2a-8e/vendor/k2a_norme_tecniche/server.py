"""Entrypoint MCP server (FastMCP — stesso pattern di `normattiva`).

I tool sono funzioni decorate con @mcp.tool() che ritornano dict (FastMCP serializza).
La logica vive in tools.py (ritorna pydantic, testabile); qui si fa solo il wiring.

Fix M-infra-1 (29/05/2026):
  - Single-instance lock (DN-25): impedisce zombie stdio contention tra 2 PID concorrenti.
  - Warning fastembed soppressi: il warning "mean pooling" di fastembed inquinava i log
    ad ogni chiamata search_semantic.
"""

from __future__ import annotations

import warnings

# Fix B — Sopprime il warning fastembed "The model now uses mean pooling instead of
# CLS embedding" che appare ad ogni search_semantic e inquina i log MCP.
# Il warning è informativo (comportamento corretto, nessun impatto funzionale).
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

from mcp.server.fastmcp import FastMCP

from . import tools as _tools
from .schemas import (
    CercaArticoloInput,
    GetCapitoloInput,
    GetDocumentoInput,
    GetParagrafoInput,
    SearchInput,
    SearchSemanticInput,
)

mcp = FastMCP("k2a-mcp-norme-tecniche")


@mcp.tool()
def freschezza() -> dict:
    """Diagnostica della KB norme tecniche: conteggio documenti, chunks, ultimo aggiornamento.

    Usalo all'inizio di una sessione per sapere quali norme tecniche sono caricate.
    """
    return _tools.freschezza().model_dump(mode="json")


@mcp.tool()
def lista_documenti() -> dict:
    """Elenco dei documenti normativi disponibili (NTC, Circolare, Eurocodici)."""
    return _tools.lista_documenti().model_dump(mode="json")


@mcp.tool()
def search(query: str, documento: str | None = None,
           capitolo: str | None = None, limit: int = 10) -> dict:
    """Ricerca full-text FTS5 nelle norme tecniche.

    Operatori FTS5: AND/OR/NOT, "frase esatta", prefisso*, NEAR(a b, 5).

    Args:
        query: parole chiave o espressione FTS5.
        documento: filtro opzionale per codice documento (es. "circolare_7_2019").
        capitolo: filtro opzionale per capitolo (es. "C4").
        limit: numero massimo di risultati (default 10).
    """
    return _tools.search(
        SearchInput(query=query, documento=documento, capitolo=capitolo, limit=limit)
    ).model_dump(mode="json")


@mcp.tool()
def search_semantic(query: str, documento: str | None = None, limit: int = 10) -> dict:
    """Ricerca SEMANTICA (per significato) sulle norme tecniche, complementare a `search`.

    Trova passaggi pertinenti anche senza parole in comune (sinonimi/parafrasi),
    via embeddings locali + kNN. Usa `search` (FTS5) per match lessicali esatti
    (termini, sigle, codici di paragrafo); usa `search_semantic` per domande in
    linguaggio naturale. Se l'indice vettoriale non è pronto: `disponibile=false`.
    """
    return _tools.search_semantic(
        SearchSemanticInput(query=query, documento=documento, limit=limit)
    ).model_dump(mode="json")


@mcp.tool()
def search_hybrid(query: str, documento: str | None = None, limit: int = 10) -> dict:
    """Ricerca IBRIDA (FTS5 + semantica) via Reciprocal Rank Fusion — DEFAULT per query in linguaggio naturale.

    Combina la precisione lessicale di `search` con il recall semantico di
    `search_semantic` (RRF, k=60, pesi 1:1) e dà boost ai chunk normativi primari
    (paragrafo non-null). Più robusto di entrambi presi singolarmente, Trap 0%.

    Quando usarlo: domande discorsive / NL ("quando va aggiornato il DVR?", "obblighi
    del CSE in caso di pericolo grave"). **Per un articolo NOTO ("art. 28") usa prima
    `cerca_articolo`** (più diretto). `search` e `search_semantic` restano per usi avanzati.
    """
    from .hybrid import search_hybrid as _hybrid
    return _hybrid(query, documento=documento, limit=limit)


@mcp.tool()
def cerca_articolo(query: str, documento: str | None = None, limit: int = 5) -> dict:
    """Trova l'ARTICOLO giusto per tema, cercando tra i TITOLI degli articoli.

    Usa questo PRIMA di `get_paragrafo` quando NON conosci il numero ma sai il tema
    (es. "sanzioni omessa valutazione" → art. 55; "sorveglianza sanitaria" → art. 41):
    è più affidabile di `search_semantic` per individuare l'articolo canonico, perché
    cerca direttamente nei titoli. Ritorna numero+titolo+pagina; poi chiama
    `get_paragrafo(documento, numero)` per il testo completo.
    """
    return _tools.cerca_articolo(
        CercaArticoloInput(query=query, documento=documento, limit=limit)
    ).model_dump(mode="json")


@mcp.tool()
def get_documento(documento: str) -> dict:
    """Recupera titolo + lista capitoli di un documento normativo (es. "circolare_7_2019")."""
    return _tools.get_documento(GetDocumentoInput(documento=documento)).model_dump(mode="json")


@mcp.tool()
def get_capitolo(documento: str, capitolo: str) -> dict:
    """Recupera tutti i paragrafi di un capitolo (es. C4 della Circolare 7/2019)."""
    return _tools.get_capitolo(
        GetCapitoloInput(documento=documento, capitolo=capitolo)
    ).model_dump(mode="json")


@mcp.tool()
def get_paragrafo(documento: str, paragrafo: str) -> dict:
    """Recupera il testo di un paragrafo; aggrega le parti se multi-chunk (DN-11)."""
    # exclude_unset: nel caso mono-chunk i campi `n_parts`/`parts` non vengono
    # impostati → restano fuori dall'output (contract backward-compatible).
    return _tools.get_paragrafo(
        GetParagrafoInput(documento=documento, paragrafo=paragrafo)
    ).model_dump(mode="json", exclude_unset=True)


def main() -> None:
    """Console-script entry point: avvia il server MCP su stdio.

    Fix M-infra-1: acquisisce il single-instance lock prima di avviare il server.
    Se un'altra istanza è già in esecuzione, exit con errore (vedi single_instance.py).
    """
    from .single_instance import acquire_single_instance_lock
    acquire_single_instance_lock()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
