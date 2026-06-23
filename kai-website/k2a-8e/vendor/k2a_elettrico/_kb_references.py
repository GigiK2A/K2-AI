"""Recupero riferimenti KB on-demand per output asseverativo (Tappa 2).

Pattern: lazy, attivato da `with_kb_references=True` (default OFF → backward compat
e performance).
- Default: snapshot statico di `_kb_mapping.py` (`fonte=snapshot_statico_v1`).
- `dynamic_kb=True` (Fase 2): recupero verbatim live dalla KB norme-tecniche
  (`fonte=kb_runtime_v1`). Se la KB non è disponibile o il paragrafo non è
  recuperabile (es. CEI 64-8 con section_code assente nel chunking DOCX), si
  ricade sul verbatim statico — graceful degradation, mai un'eccezione al chiamante.
"""
from __future__ import annotations

from ._kb_mapping import NORME_IN_KB, get_kb_references_for_tool


def build_kb_references(tool_name: str, output_context: dict | None = None,
                        dynamic_kb: bool = False) -> list[dict]:
    """Costruisce la lista di riferimenti KB normalizzati per l'output asseverativo.

    Campi per riferimento:
      norma, paragrafo, titolo, testo_verbatim (str|None),
      applicabile_a (condizione), in_kb (norma caricata in KB?),
      verbatim_disponibile (estratto presente?), fonte.

    Args:
      dynamic_kb: se True, prova a recuperare il verbatim live dalla KB; in caso
        di successo sovrascrive lo snapshot e marca `fonte=kb_runtime_v1`.
    """
    refs = get_kb_references_for_tool(tool_name, output_context)
    live_fn = None
    if dynamic_kb:
        try:
            from ._kb_dynamic import is_kb_available, recupera_verbatim_dinamico
            if is_kb_available():
                live_fn = recupera_verbatim_dinamico
        except Exception:  # noqa: BLE001 — KB non importabile: resta statico
            live_fn = None

    out: list[dict] = []
    for r in refs:
        verbatim = r.get("testo_verbatim")
        fonte = "snapshot_statico_v1"
        if live_fn is not None:
            live = live_fn(r["norma"], r["paragrafo"])
            if live:
                verbatim = live
                fonte = "kb_runtime_v1"
        out.append({
            "norma": r["norma"],
            "paragrafo": r["paragrafo"],
            "titolo": r["titolo"],
            "testo_verbatim": verbatim,
            "applicabile_a": r["contesto_uso"],
            "in_kb": r["norma"] in NORME_IN_KB,
            "verbatim_disponibile": verbatim is not None,
            "fonte": fonte,
        })
    return out
