"""Invio di risposte agente ricche su Telegram.

Un'unica funzione, `send_rich_reply`, che prende il testo grezzo di un agente e:
1. estrae i blocchi ```grafico``` / ```documento``` (core.rich_output);
2. invia il testo discorsivo in HTML (grassetti, corsivi, code, link, emoji e
   caratteri speciali resi correttamente via markdown_to_telegram_html);
3. renderizza ogni grafico come immagine PNG e lo invia come foto;
4. genera ogni documento come file reale (PDF/DOCX/XLSX) e lo invia come allegato.

Se un rendering fallisce, la risposta testuale arriva comunque e l'errore viene
segnalato in modo non tecnico. Il testo non viene mai troncato: se supera il
limite Telegram viene spezzato in più messaggi.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from loguru import logger
from telegram import InlineKeyboardMarkup, Message
from telegram.constants import ParseMode

from core.chart_render import render_chart_png
from core.document_render import render_document
from core.rich_output import extract_rich_output
from core.text import markdown_to_telegram_html

_TG_TEXT_MAX = 3500  # margine sotto i 4096 per l'espansione delle entity HTML


def _split_plain(text: str, max_len: int = _TG_TEXT_MAX) -> list[str]:
    """Spezza il testo in chunk ≤ max_len su paragrafi/newline/parole. Non tronca."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n\n", 0, max_len)
        if split_at <= 0:
            split_at = text.rfind("\n", 0, max_len)
        if split_at <= 0:
            split_at = text.rfind(" ", 0, max_len)
        if split_at <= 0:
            split_at = max_len
        chunks.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip("\n")
    return chunks


async def _send_text(
    message: Message,
    text: str,
    placeholder: Message | None,
    keyboard: InlineKeyboardMarkup | None,
) -> None:
    chunks = _split_plain(text)
    if not chunks:
        chunks = ["(nessun contenuto)"]

    for index, chunk in enumerate(chunks):
        html = markdown_to_telegram_html(chunk)
        # La keyboard va solo sull'ultimo chunk.
        kb = keyboard if index == len(chunks) - 1 else None
        try:
            if index == 0 and placeholder is not None:
                await placeholder.edit_text(html, parse_mode=ParseMode.HTML, reply_markup=kb)
            else:
                await message.reply_text(html, parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception as exc:
            # Fallback senza parse_mode: meglio testo grezzo che nessun messaggio.
            logger.warning(f"Invio HTML fallito, fallback plain: {exc}")
            if index == 0 and placeholder is not None:
                await placeholder.edit_text(chunk, reply_markup=kb)
            else:
                await message.reply_text(chunk, reply_markup=kb)


async def _send_charts(message: Message, charts: list[dict[str, Any]]) -> None:
    for config in charts:
        try:
            png = render_chart_png(config)
        except Exception as exc:
            logger.warning(f"Grafico non renderizzato: {exc}")
            await message.reply_text("⚠️ Non sono riuscita a disegnare uno dei grafici.")
            continue
        try:
            title = str(config.get("title") or "").strip()
            buffer = BytesIO(png)
            buffer.name = "grafico.png"
            await message.reply_photo(photo=buffer, caption=title[:1000] or None)
        except Exception as exc:
            logger.warning(f"Invio grafico fallito: {exc}")


async def _send_documents(message: Message, documents: list[dict[str, Any]]) -> None:
    for spec in documents:
        try:
            rendered = render_document(spec)
        except ValueError as exc:
            await message.reply_text(f"⚠️ Documento non generato: {exc}")
            continue
        except Exception as exc:
            logger.warning(f"Documento non renderizzato: {exc}")
            await message.reply_text("⚠️ Non sono riuscita a generare uno dei documenti.")
            continue
        try:
            buffer = BytesIO(rendered.content)
            buffer.name = rendered.filename
            await message.reply_document(
                document=buffer,
                filename=rendered.filename,
                caption=str(spec.get("title") or rendered.filename)[:1000],
            )
        except Exception as exc:
            logger.warning(f"Invio documento fallito: {exc}")


async def send_rich_reply(
    message: Message,
    raw_text: Any,
    placeholder: Message | None = None,
    keyboard: InlineKeyboardMarkup | None = None,
) -> None:
    """Invia una risposta agente completa: testo HTML + grafici + documenti.

    `message`: il messaggio Telegram su cui rispondere (update.message).
    `placeholder`: se presente, il primo chunk di testo lo modifica invece di
        creare un nuovo messaggio (utile per sostituire un "…" di attesa).
    """
    rich = extract_rich_output(raw_text)
    await _send_text(message, rich.text or "(nessun contenuto)", placeholder, keyboard)
    if rich.charts:
        await _send_charts(message, rich.charts)
    if rich.documents:
        await _send_documents(message, rich.documents)
