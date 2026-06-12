"""Pydantic models per input/output dei tool MCP."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FreschezzaOutput(BaseModel):
    totale_documenti: int
    totale_chunks: int
    ultimo_aggiornamento: datetime | None = None
    nota_copertura: str = ""


class DocumentoItem(BaseModel):
    codice: str
    titolo: str
    anno: int | None
    fonte: str | None
    n_capitoli: int
    n_paragrafi: int
    n_chunks: int
    vigenza: str
    document_type: str | None = None  # 'norma_tecnica' | 'circolare_applicativa' (NT-1B)


class ListaDocumentiOutput(BaseModel):
    totale: int
    documenti: list[DocumentoItem] = Field(default_factory=list)


class SearchInput(BaseModel):
    query: str
    documento: str | None = None         # filtro opzionale (es. "circolare_7_2019")
    capitolo: str | None = None          # filtro opzionale (es. "C4")
    limit: int = 10


class SearchHit(BaseModel):
    chunk_id: int
    documento: str
    paragrafo: str | None  # None per i chunk di frontmatter (senza section_code)
    titolo: str | None
    snippet: str
    rank: float
    pagina_pdf: int | None


class SearchOutput(BaseModel):
    query: str
    totale: int
    risultati: list[SearchHit] = Field(default_factory=list)


class SearchSemanticInput(BaseModel):
    query: str
    documento: str | None = None         # filtro opzionale per codice documento
    limit: int = 10


class SemanticHit(BaseModel):
    chunk_id: str | None                  # chunk_id_originale (es. "TU81_2026_01573")
    documento: str
    paragrafo: str | None
    titolo: str | None
    snippet: str
    distanza: float                       # distanza L2 (più bassa = più simile)
    pagina_pdf: int | None


class SearchSemanticOutput(BaseModel):
    query: str
    totale: int
    modello: str
    risultati: list[SemanticHit] = Field(default_factory=list)
    disponibile: bool = True              # False se l'indice vettoriale non è pronto


class CercaArticoloInput(BaseModel):
    query: str
    documento: str | None = None         # filtro opzionale per codice documento
    limit: int = 5


class ArticoloHit(BaseModel):
    numero: str                           # numero articolo nudo (es. "55", "286-bis")
    titolo: str                           # titolo dell'articolo (ripulito)
    documento: str
    pagina_pdf: int | None                # pagina del CORPO dell'articolo


class CercaArticoloOutput(BaseModel):
    query: str
    totale: int
    risultati: list[ArticoloHit] = Field(default_factory=list)


class GetDocumentoInput(BaseModel):
    documento: str


class GetDocumentoOutput(BaseModel):
    codice: str
    titolo: str
    n_chunks: int
    capitoli: list[str] = Field(default_factory=list)
    trovato: bool


class GetCapitoloInput(BaseModel):
    documento: str
    capitolo: str


class GetCapitoloOutput(BaseModel):
    documento: str
    capitolo: str
    paragrafi: list[str] = Field(default_factory=list)
    contenuto_completo: str | None = None
    trovato: bool


class GetParagrafoInput(BaseModel):
    documento: str
    paragrafo: str


class ParteChunk(BaseModel):
    """Una parte (chunk) di un paragrafo composto da più chunk consecutivi (DN-11)."""
    chunk_id: str
    contenuto: str | None = None
    pagina_pdf_inizio: int | None = None
    pagina_pdf_fine: int | None = None


class GetParagrafoOutput(BaseModel):
    documento: str
    paragrafo: str
    titolo: str | None = None
    contenuto: str | None = None
    pagina_pdf_inizio: int | None = None
    pagina_pdf_fine: int | None = None
    tags: list[str] = Field(default_factory=list)
    ntc_riferimento: str | None = None
    trovato: bool
    # DN-11 (NT-2.6): presenti SOLO nel caso multi-chunk (serializzati con
    # exclude_unset nel server → assenti nel caso mono-chunk, contract invariato).
    n_parts: int | None = None
    parts: list[ParteChunk] | None = None
