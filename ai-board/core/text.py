import re
from html import escape
from typing import Any


_FENCED_CODE_RE = re.compile(r"```(?:[\w-]+)?\s*\n(.*?)```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
_BLOCKQUOTE_RE = re.compile(r"^\s*>\s?", re.MULTILINE)
_HR_RE = re.compile(r"^\s*[-*_]{3,}\s*$", re.MULTILINE)
_BOLD_RE = re.compile(r"(\*\*|__)(.*?)\1", re.DOTALL)
_ITALIC_STAR_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_ITALIC_UNDERSCORE_RE = re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)")
_MULTIBLANK_RE = re.compile(r"\n{3,}")


def markdown_to_plain_text(value: Any) -> str:
    text = "" if value is None else str(value)
    if not text.strip():
        return ""

    text = _FENCED_CODE_RE.sub(lambda match: match.group(1).strip(), text)
    text = _INLINE_CODE_RE.sub(r"\1", text)
    text = _IMAGE_RE.sub(lambda match: match.group(1).strip(), text)
    text = _LINK_RE.sub(lambda match: match.group(1).strip(), text)
    text = _HEADING_RE.sub("", text)
    text = _BLOCKQUOTE_RE.sub("", text)
    text = _HR_RE.sub("", text)
    text = _BOLD_RE.sub(lambda match: match.group(2), text)
    text = _ITALIC_STAR_RE.sub(lambda match: match.group(1), text)
    text = _ITALIC_UNDERSCORE_RE.sub(lambda match: match.group(1), text)

    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            cleaned_lines.append("")
            continue

        if "|" in line:
            candidate = stripped.strip("|")
            cells = [cell.strip() for cell in candidate.split("|")]
            if len(cells) > 1:
                if all(cell and set(cell) <= {"-", ":"} for cell in cells):
                    continue
                line = " | ".join(cell for cell in cells if cell)

        line = re.sub(r"^\s*[-*+]\s+", "• ", line)
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = _MULTIBLANK_RE.sub("\n\n", text)
    return text.strip()


def truncate_text(value: Any, length: int = 80, suffix: str = "…") -> str:
    text = "" if value is None else str(value)
    if len(text) <= length:
        return text
    if length <= len(suffix):
        return suffix[:length]
    return text[: length - len(suffix)].rstrip() + suffix


_FENCE_HTML_RE = re.compile(r"```(?:[\w-]+)?\s*\n(.*?)```", re.DOTALL)
_INLINE_CODE_HTML_RE = re.compile(r"`([^`]+)`")
_LINK_HTML_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD_HTML_RE = re.compile(r"(\*\*|__)(.+?)\1", re.DOTALL)
_ITALIC_HTML_STAR_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_ITALIC_HTML_UNDERSCORE_RE = re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)")


def markdown_to_telegram_html(value: Any) -> str:
    text = "" if value is None else str(value)
    if not text:
        return ""

    placeholders: dict[str, str] = {}
    counter = 0

    def stash(fragment: str) -> str:
        nonlocal counter
        key = f"@@TGHTML_{counter}@@"
        placeholders[key] = fragment
        counter += 1
        return key

    def _fence(match: re.Match[str]) -> str:
        code = escape(match.group(1).strip("\n"))
        return stash(f"<pre><code>{code}</code></pre>")

    def _inline_code(match: re.Match[str]) -> str:
        code = escape(match.group(1))
        return stash(f"<code>{code}</code>")

    def _link(match: re.Match[str]) -> str:
        label = escape(match.group(1))
        href = escape(match.group(2), quote=True)
        return stash(f'<a href="{href}">{label}</a>')

    def _bold(match: re.Match[str]) -> str:
        content = escape(match.group(2))
        return stash(f"<b>{content}</b>")

    def _italic_star(match: re.Match[str]) -> str:
        content = escape(match.group(1))
        return stash(f"<i>{content}</i>")

    def _italic_underscore(match: re.Match[str]) -> str:
        content = escape(match.group(1))
        return stash(f"<i>{content}</i>")

    text = _FENCE_HTML_RE.sub(_fence, text)
    text = _INLINE_CODE_HTML_RE.sub(_inline_code, text)
    text = _LINK_HTML_RE.sub(_link, text)
    text = _BOLD_HTML_RE.sub(_bold, text)
    text = _ITALIC_HTML_STAR_RE.sub(_italic_star, text)
    text = _ITALIC_HTML_UNDERSCORE_RE.sub(_italic_underscore, text)
    text = escape(text)

    for key, fragment in placeholders.items():
        text = text.replace(escape(key), fragment)
    return text
