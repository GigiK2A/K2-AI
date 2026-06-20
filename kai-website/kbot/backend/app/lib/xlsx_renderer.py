"""Render a report-design-system analysis JSON to an .xlsx workbook.

Reuses the SAME `{meta, blocks[]}` payload produced by
`lib.analysis.generate_analysis_json` and rendered to PDF by `lib.pdf_renderer`.
Each `data_table` block becomes a real spreadsheet sheet (ideal for editorial
calendars, content pillars, financial projections); textual blocks
(executive_summary, narrative, conclusions, two_column) are summarised on a
leading "Sintesi" sheet.

Kept deliberately defensive: the LLM JSON shape can vary, so every field access
is guarded and unknown block types degrade to text instead of raising.
"""
from __future__ import annotations

import io
import re
from typing import Any, Dict, List

K2_GREEN = "0C7A6F"
K2_DARK = "063B36"
_MAX_SHEET_NAME = 31  # Excel hard limit


def _strip_html(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value if value is not None else ""))
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


_EURO_RE = re.compile(r"^€\s*(-?[\d.]+(?:,\d+)?)$")
_PCT_RE = re.compile(r"^(-?[\d.]+(?:,\d+)?)\s*%$")
_NUM_RE = re.compile(r"^-?[\d.]+(?:,\d+)?$")


def _typed_cell(value: Any) -> tuple[Any, str | None]:
    """Mantiene numeri/formule come tali; niente workbook composto solo da testo."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value, '#,##0.00;[Red](#,##0.00);-'
    text = _strip_html(value)
    if text.startswith("="):
        return text, None
    for rx, fmt, scale in ((_EURO_RE, '€ #,##0.00;[Red](€ #,##0.00);-', 1),
                           (_PCT_RE, '0.0%', 100), (_NUM_RE, '#,##0.00;[Red](#,##0.00);-', 1)):
        m = rx.match(text)
        if not m:
            continue
        raw = m.group(1) if m.lastindex else text
        try:
            n = float(raw.replace(".", "").replace(",", ".")) / scale
            return n, fmt
        except ValueError:
            pass
    return text, None


def _safe_sheet_title(title: str, used: set) -> str:
    name = re.sub(r"[\[\]:*?/\\]", " ", _strip_html(title) or "Foglio").strip() or "Foglio"
    name = name[:_MAX_SHEET_NAME]
    base, i = name, 2
    while name.lower() in used:
        suffix = f" {i}"
        name = (base[: _MAX_SHEET_NAME - len(suffix)] + suffix).strip()
        i += 1
    used.add(name.lower())
    return name


def _summary_lines(blocks: List[dict]) -> List[str]:
    """Flatten textual blocks into readable lines for the Sintesi sheet."""
    lines: List[str] = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        btype = b.get("type") or ""
        title = _strip_html(b.get("title") or b.get("heading") or "")
        if btype == "executive_summary":
            if title:
                lines.append(title.upper())
            score = b.get("score")
            if score not in (None, ""):
                lines.append(f"Punteggio: {score}")
            body = _strip_html(b.get("body") or b.get("summary"))
            if body:
                lines.append(body)
            lines.append("")
        elif btype in ("narrative", "callout", "text"):
            if title:
                lines.append(title.upper())
            body = _strip_html(b.get("body") or b.get("body_html"))
            if body:
                lines.append(body)
            lines.append("")
        elif btype == "two_column":
            for side in ("left", "right"):
                col = b.get(side) or {}
                if isinstance(col, dict):
                    h = _strip_html(col.get("heading"))
                    if h:
                        lines.append(h.upper())
                    items = col.get("items") or []
                    if isinstance(items, list):
                        for it in items:
                            lines.append(f"  • {_strip_html(it)}")
                    body = _strip_html(col.get("body") or col.get("body_html"))
                    if body:
                        lines.append(body)
            lines.append("")
        elif btype == "conclusions":
            lines.append(_strip_html(b.get("title") or "Conclusioni e prossimi passi").upper())
            left = b.get("left") or {}
            if isinstance(left, dict):
                if left.get("heading"):
                    lines.append(_strip_html(left.get("heading")))
                body = _strip_html(left.get("body_html") or left.get("body"))
                if body:
                    lines.append(body)
            right = b.get("right") or {}
            if isinstance(right, dict):
                if right.get("heading"):
                    lines.append(_strip_html(right.get("heading")))
                for m in right.get("milestones") or []:
                    if isinstance(m, dict):
                        label = _strip_html(m.get("label"))
                        items = ", ".join(_strip_html(i) for i in (m.get("items") or []))
                        lines.append(f"  • {label}: {items}" if items else f"  • {label}")
            lines.append("")
    return [ln for ln in lines]


def render_xlsx(analysis: Dict[str, Any]) -> bytes:
    """Return .xlsx bytes for a `{meta, blocks[]}` analysis payload."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    meta = analysis.get("meta") or {}
    blocks = [b for b in (analysis.get("blocks") or []) if isinstance(b, dict)]
    title = _strip_html(meta.get("title") or "Report K2-AI") or "Report K2-AI"

    header_fill = PatternFill("solid", fgColor=K2_GREEN)
    header_font = Font(bold=True, color="FFFFFF")
    title_font = Font(bold=True, size=14, color=K2_DARK)
    wrap = Alignment(wrap_text=True, vertical="top")
    thin = Side(style="thin", color="D0D5DD")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    wb = Workbook()
    used_names: set = set()

    # --- Sintesi sheet (always first) ---
    ws = wb.active
    ws.title = _safe_sheet_title("Sintesi", used_names)
    ws["A1"] = title
    ws["A1"].font = title_font
    row = 3
    for line in _summary_lines(blocks):
        cell = ws.cell(row=row, column=1, value=line)
        cell.alignment = wrap
        row += 1
    ws.column_dimensions["A"].width = 110

    # --- data_table blocks → one sheet each ---
    table_count = 0
    for b in blocks:
        if b.get("type") != "data_table":
            continue
        table_count += 1
        columns = [_strip_html(c) for c in (b.get("columns") or [])]
        rows = b.get("rows") or []
        sheet_name = _safe_sheet_title(b.get("title") or f"Tabella {table_count}", used_names)
        tws = wb.create_sheet(sheet_name)

        tws.cell(row=1, column=1, value=_strip_html(b.get("title") or sheet_name)).font = title_font
        header_row = 3
        ncols = max(len(columns), max((len(r) for r in rows if isinstance(r, list)), default=1))

        for ci in range(1, ncols + 1):
            label = columns[ci - 1] if ci - 1 < len(columns) else ""
            cell = tws.cell(row=header_row, column=ci, value=label)
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border
            cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")

        for ri, r in enumerate(rows, start=header_row + 1):
            cells = r if isinstance(r, list) else [r]
            for ci in range(1, ncols + 1):
                value = cells[ci - 1] if ci - 1 < len(cells) else ""
                typed, number_format = _typed_cell(value)
                cell = tws.cell(row=ri, column=ci, value=typed)
                if number_format:
                    cell.number_format = number_format
                cell.alignment = wrap
                cell.border = border

        # Column widths from longest cell (capped), then freeze the header.
        for ci in range(1, ncols + 1):
            longest = len(columns[ci - 1]) if ci - 1 < len(columns) else 10
            for r in rows:
                if isinstance(r, list) and ci - 1 < len(r):
                    longest = max(longest, len(_strip_html(r[ci - 1])))
            tws.column_dimensions[get_column_letter(ci)].width = min(max(longest + 2, 12), 50)
        tws.freeze_panes = tws.cell(row=header_row + 1, column=1)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
