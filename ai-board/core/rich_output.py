"""Estrae grafici e documenti dal testo prodotto da un agente.

Gli agenti possono includere nel loro output blocchi fenced:

    ```grafico
    {"type": "bar", "data": {...}}
    ```

    ```documento
    {"format": "pdf", "title": "...", "content": "..."}
    ```

Questo modulo separa quei blocchi dal testo discorsivo così che le interfacce
(Telegram, e in prospettiva il sito) possano renderli come immagine/file invece
di mostrare JSON grezzo.

`extract_rich_output(text)` restituisce un RichOutput con:
- `text`: il testo ripulito, con un breve segnaposto al posto di ogni blocco
- `charts`: lista di config grafico (dict) da passare a chart_render
- `documents`: lista di spec documento (dict) da passare a document_render

Il parsing è tollerante: un blocco con JSON non valido viene lasciato come
segnaposto testuale e loggato, senza far fallire l'intera risposta.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

# Cattura ```<tag> ... ``` con tag grafico/chart/documento/document.
_BLOCK_RE = re.compile(
    r"```(?P<tag>grafico|chart|documento|document)\s*\n(?P<body>.*?)```",
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class RichOutput:
    text: str
    charts: list[dict[str, Any]] = field(default_factory=list)
    documents: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_attachments(self) -> bool:
        return bool(self.charts or self.documents)


def _parse_json_body(body: str) -> Any:
    """Prova a caricare il JSON del blocco, tollerando fence/commenti residui."""
    text = body.strip()
    # A volte gli agenti annidano un ulteriore fence ```json.
    inner = re.match(r"^```(?:json)?\s*\n(.*?)```$", text, re.DOTALL)
    if inner:
        text = inner.group(1).strip()
    return json.loads(text)


def extract_rich_output(raw_text: Any) -> RichOutput:
    text = "" if raw_text is None else str(raw_text)
    if "```" not in text:
        return RichOutput(text=text)

    charts: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    def _replace(match: re.Match[str]) -> str:
        tag = match.group("tag").lower()
        body = match.group("body")
        is_chart = tag in ("grafico", "chart")
        try:
            payload = _parse_json_body(body)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(f"Blocco {tag} con JSON non valido, lasciato come testo: {exc}")
            # Lascia il blocco invariato: meglio JSON grezzo che perdere contenuto.
            return match.group(0)

        if not isinstance(payload, dict):
            return match.group(0)

        if is_chart:
            charts.append(payload)
            title = str(payload.get("title") or "").strip()
            return f"\n📊 [grafico{f': {title}' if title else ''}]\n"

        documents.append(payload)
        label = str(payload.get("title") or payload.get("filename") or "documento").strip()
        fmt = str(payload.get("format") or "pdf").strip().lower()
        return f"\n📎 [{fmt.upper()}: {label}]\n"

    cleaned = _BLOCK_RE.sub(_replace, text)
    # Compatta eventuali righe vuote multiple lasciate dai segnaposto.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return RichOutput(text=cleaned, charts=charts, documents=documents)
