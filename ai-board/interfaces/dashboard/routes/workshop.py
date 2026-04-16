from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json
import re
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger

from core.board_auth import is_admin
from core.config import settings
from core.memory import get_memory, set_memory
from interfaces.dashboard.routes import base_context, render

router = APIRouter()

WORKSHOP_MEMORY_KEY = "offers.workshop_packages"
WORKSHOP_UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads" / "workshop"
WORKSHOP_ASSETS_DIR = WORKSHOP_UPLOADS_DIR / "assets"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
ALLOWED_IMAGE_MIMETYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
}
WORKSHOP_DEFAULT_PACKAGES = [
    {
        "id": "starter-14gg",
        "title": "Starter 14 giorni",
        "subtitle": "Diagnosi + prototipo",
        "price": "Da €2.500",
        "delivery": "14 giorni",
        "description": "Analisi del flusso, prototipo operativo e verifica KPI sul processo reale.",
        "includes": [
            "Workshop iniziale",
            "Mappa attriti + priorita",
            "Prototipo testabile",
            "Consegna con prossimo step chiaro",
        ],
        "cta_label": "Richiedi workshop",
        "cta_href": "/contatti.html",
        "html_file": None,
        "active": True,
    },
    {
        "id": "ops-ai-pack",
        "title": "Operations AI Pack",
        "subtitle": "Workflow pronto all'uso",
        "price": "Da €4.900",
        "delivery": "3-5 settimane",
        "description": "Setup end-to-end per task ripetitivi e passaggi manuali ad alta frequenza.",
        "includes": [
            "Automazioni operative",
            "Controlli umani nel flusso",
            "Dashboard minima di monitoraggio",
            "Training team",
        ],
        "cta_label": "Voglio questo pacchetto",
        "cta_href": "/contatti.html",
        "html_file": None,
        "active": True,
    },
]


def _require_admin(request: Request) -> None:
    if not (settings.board_auth_enabled or settings.app_env == "production"):
        return
    if not is_admin(getattr(request.state, "board_user", None)):
        raise HTTPException(status_code=403, detail="Solo admin")


def _as_text(value: str | None, *, max_len: int = 300) -> str:
    return str(value or "").strip()[:max_len]


def _normalize_includes(raw_items: list[str] | None) -> list[str]:
    output: list[str] = []
    for item in raw_items or []:
        value = _as_text(item, max_len=220)
        if value:
            output.append(value)
    return output


def _normalize_package(raw: dict) -> dict:
    package_id = _as_text(raw.get("id"), max_len=120).lower() or str(uuid.uuid4())
    html_file = raw.get("html_file")
    package = {
        "id": package_id,
        "title": _as_text(raw.get("title"), max_len=120) or "Pacchetto",
        "subtitle": _as_text(raw.get("subtitle"), max_len=160),
        "price": _as_text(raw.get("price"), max_len=80),
        "delivery": _as_text(raw.get("delivery"), max_len=80),
        "description": _as_text(raw.get("description"), max_len=500),
        "includes": _normalize_includes(raw.get("includes") if isinstance(raw.get("includes"), list) else []),
        "cta_label": _as_text(raw.get("cta_label"), max_len=80) or "Richiedi info",
        "cta_href": _as_text(raw.get("cta_href"), max_len=200) or "/contatti.html",
        "html_file": _as_text(html_file, max_len=300) if html_file else None,
        "active": bool(raw.get("active", True)),
    }
    return package


def _load_workshop_packages() -> list[dict]:
    raw = get_memory(WORKSHOP_MEMORY_KEY, WORKSHOP_DEFAULT_PACKAGES)
    if not isinstance(raw, list):
        return [_normalize_package(item) for item in WORKSHOP_DEFAULT_PACKAGES]
    packages = [_normalize_package(item) for item in raw if isinstance(item, dict)]
    return [item for item in packages if item.get("id")]


def _save_workshop_packages(packages: list[dict], updated_by: str = "admin") -> None:
    normalized = [_normalize_package(item) for item in packages]
    set_memory(
        WORKSHOP_MEMORY_KEY,
        normalized,
        category="offers",
        updated_by=updated_by,
    )


_HTML_SIGNATURES = (b"<!doctype", b"<html", b"<!DOCTYPE", b"<HTML")


def _is_html_content(data: bytes) -> bool:
    """Verifica che il file contenga HTML valido (magic bytes)."""
    sample = data[:512].lstrip()
    return any(sample.startswith(sig) for sig in _HTML_SIGNATURES)


async def _save_html_upload(upload: UploadFile) -> str:
    """Salva il file HTML caricato e restituisce il web path."""
    WORKSHOP_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    content = await upload.read()
    if len(content) > 2 * 1024 * 1024:  # 2 MB max
        raise HTTPException(status_code=400, detail="File troppo grande (max 2 MB)")
    if not _is_html_content(content):
        raise HTTPException(status_code=400, detail="Il file non è un HTML valido")
    safe_name = f"{uuid.uuid4()}.html"
    dest = WORKSHOP_UPLOADS_DIR / safe_name
    dest.write_bytes(content)
    return f"/uploads/workshop/{safe_name}"


def _delete_html_file(web_path: str) -> None:
    """Rimuove il file HTML dal disco se esiste."""
    if not web_path:
        return
    try:
        relative = web_path.lstrip("/")  # uploads/workshop/xxx.html
        full = Path(__file__).resolve().parents[3] / relative
        if full.exists() and full.is_relative_to(WORKSHOP_UPLOADS_DIR):
            full.unlink(missing_ok=True)
    except Exception:
        pass


# ── Estrazione AI da HTML ─────────────────────────────────────────────────────

_EXTRACT_PROMPT = """Analizza il seguente contenuto HTML di una scheda/pacchetto commerciale ed estraiil testo rilevante.
Rispondi SOLO con un oggetto JSON valido (nessun testo extra, nessun markdown) con questi campi:

{
  "title": "titolo principale del pacchetto",
  "subtitle": "sottotitolo o tagline breve (max 80 char)",
  "price": "prezzo indicato (es. Da €2.500), stringa vuota se assente",
  "delivery": "tempi di consegna/durata (es. 14 giorni), stringa vuota se assente",
  "description": "descrizione breve del pacchetto (max 300 char)",
  "includes": ["voce 1", "voce 2", "..."],
  "cta_label": "testo del pulsante call-to-action principale, o stringa vuota",
  "cta_href": "link del pulsante CTA se presente (deve iniziare con / o https://), altrimenti /contatti.html"
}

Regole:
- Non inventare dati non presenti nell'HTML.
- Se un campo non è presente, usa stringa vuota o lista vuota.
- includes deve essere una lista di stringhe, una per ogni voce/feature elencata.
- Rispondi SOLO con il JSON, senza commenti.
"""


def _strip_html_tags(html: str) -> str:
    """Rimuove i tag HTML lasciando solo il testo leggibile (max 8000 char)."""
    text = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:8000]


async def _extract_fields_with_ai(html_content: str) -> dict:
    """Chiama OpenAI (con fallback su Anthropic) per estrarre i campi dal testo HTML."""
    text = _strip_html_tags(html_content)
    if not text:
        raise ValueError("Il file HTML non contiene testo leggibile")

    # Prova OpenAI
    if settings.openai_api_key and settings.openai_api_key.strip():
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.default_openai_mini_model,
                messages=[
                    {"role": "system", "content": _EXTRACT_PROMPT},
                    {"role": "user", "content": f"HTML da analizzare:\n\n{text}"},
                ],
                temperature=0,
                max_tokens=1000,
            )
            raw = response.choices[0].message.content or ""
            return json.loads(raw.strip())
        except Exception as exc:
            logger.warning(f"Estrazione AI OpenAI fallita: {exc}")

    # Fallback Anthropic
    if settings.anthropic_api_key and settings.anthropic_api_key.strip():
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            response = await client.messages.create(
                model=settings.default_anthropic_model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": f"{_EXTRACT_PROMPT}\n\nHTML da analizzare:\n\n{text}"},
                ],
            )
            raw = response.content[0].text if response.content else ""
            return json.loads(raw.strip())
        except Exception as exc:
            logger.warning(f"Estrazione AI Anthropic fallita: {exc}")

    raise HTTPException(status_code=503, detail="Nessun provider AI disponibile per l'estrazione")


@router.post("/workshop-admin/extract-fields")
async def workshop_extract_fields(
    request: Request,
    html_file: UploadFile = File(...),
):
    """Riceve un file HTML e restituisce i campi del pacchetto estratti via AI."""
    _require_admin(request)
    content_bytes = await html_file.read()
    if len(content_bytes) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande (max 2 MB)")
    html_text = content_bytes.decode("utf-8", errors="ignore")
    fields = await _extract_fields_with_ai(html_text)
    return JSONResponse({"ok": True, "fields": fields})


# ── API pubblica ──────────────────────────────────────────────────────────────

@router.get("/api/workshop/packages")
async def workshop_packages_api():
    packages = []
    for item in _load_workshop_packages():
        if not item.get("active"):
            continue
        pkg = dict(item)
        # Espone html_url solo se il file esiste fisicamente su disco
        if pkg.get("html_file"):
            relative = pkg["html_file"].lstrip("/")
            full_path = Path(__file__).resolve().parents[3] / relative
            if full_path.exists() and full_path.is_relative_to(WORKSHOP_UPLOADS_DIR):
                pkg["html_url"] = f"/api/workshop/packages/{pkg['id']}/html"
            else:
                pkg["html_url"] = None
        else:
            pkg["html_url"] = None
        packages.append(pkg)
    return JSONResponse(
        {
            "ok": True,
            "updated_at": datetime.now(UTC).isoformat(),
            "packages": packages,
        }
    )


_FRONTEND_ORIGIN = "https://www.k2-ai.it"
_FRONTEND_LOGO_URL = "https://www.k2-ai.it/logo-nav.png"

# Attributi che possono contenere path assoluti del frontend
_ABSOLUTE_SRC_RE = re.compile(
    r"""((?:src|href|action)\s*=\s*["'])(/)""",
    re.IGNORECASE,
)

# Nomi file logo riconosciuti (relativi, senza leading slash)
_LOGO_FILENAMES_RE = re.compile(
    r"""(src\s*=\s*["'])(?!https?://)(?!data:)(\.{0,2}\/?)?(logo[\w\-]*\.(?:png|svg|jpg|webp)|k2[\w\-]*logo[\w\-]*\.(?:png|svg|jpg|webp))(["'])""",
    re.IGNORECASE,
)


def _fix_mojibake(html: str) -> str:
    """Tenta di correggere UTF-8 doppiamente encodato (mojibake).

    Pattern tipico: il file è UTF-8 ma è stato letto come Latin-1 e
    risalvato, producendo sequenze tipo Â· (·), â¬ (€), Ã¨ (è).
    """
    try:
        fixed = html.encode("latin-1").decode("utf-8")
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        return html  # già ok o non recuperabile


def _rewrite_absolute_paths(html: str) -> str:
    """Riscrive src="/...", href="/..." con prefisso frontend e logo relativi.

    1) Path assoluti: src="/logo-nav.png" → src="https://www.k2-ai.it/logo-nav.png"
    2) Logo relativi: src="logo.png" / src="./logo.png" → URL frontend logo
    """
    # 1) Path assoluti con leading /
    html = _ABSOLUTE_SRC_RE.sub(
        lambda m: m.group(1) + _FRONTEND_ORIGIN + "/",
        html,
    )
    # 2) Nomi file logo relativi → URL assoluta logo K2-AI
    html = _LOGO_FILENAMES_RE.sub(
        lambda m: m.group(1) + _FRONTEND_LOGO_URL + m.group(4),
        html,
    )
    return html


def _inject_base_tag(html: str, package_id: str) -> str:
    """Inietta un <base href="..."> nel <head> dell'HTML se non presente.

    Questo fa sì che tutti i path relativi nelle immagini (src="foto.jpg")
    si risolvano contro /uploads/workshop/assets/{package_id}/ invece che
    contro l'URL dell'endpoint API, dove le immagini non esistono.

    Se l'HTML ha già un <base> tag lo lascia intatto.
    """
    # Non iniettare se c'è già un <base> tag
    if re.search(r"<base\b", html, re.IGNORECASE):
        return html

    base_url = f"/uploads/workshop/assets/{package_id}/"
    base_tag = f'<base href="{base_url}">'

    # Inserisci subito dopo <head> o <head ...>
    head_match = re.search(r"<head(?:[^>]*)>", html, re.IGNORECASE)
    if head_match:
        insert_at = head_match.end()
        return html[:insert_at] + "\n  " + base_tag + html[insert_at:]

    # Fallback: inserisci prima di qualsiasi altro tag se <head> manca
    return base_tag + "\n" + html


@router.get("/api/workshop/packages/{package_id}/html")
async def workshop_package_html(package_id: str):
    """Serve il file HTML del pacchetto con base tag iniettato per le immagini."""
    target_id = _as_text(package_id, max_len=120)
    packages = _load_workshop_packages()
    target = next((p for p in packages if p.get("id") == target_id), None)
    if not target or not target.get("html_file"):
        raise HTTPException(status_code=404, detail="File non disponibile")

    # Risolve il path fisico dal web path
    relative = target["html_file"].lstrip("/")  # uploads/workshop/xxx.html
    full_path = Path(__file__).resolve().parents[3] / relative
    if not full_path.exists() or not full_path.is_relative_to(WORKSHOP_UPLOADS_DIR):
        raise HTTPException(status_code=404, detail="File non trovato su disco")

    html = full_path.read_text(encoding="utf-8", errors="replace")
    # 0) Correggi mojibake (UTF-8 doppiamente encodato da editor sbagliato)
    html = _fix_mojibake(html)
    # 1) Riscrive path assoluti /... e logo relativi → https://www.k2-ai.it/...
    html = _rewrite_absolute_paths(html)
    # 2) Inietta base tag: altri path relativi → /uploads/workshop/assets/{id}/
    html = _inject_base_tag(html, target_id)

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


# ── Pannello admin ────────────────────────────────────────────────────────────

@router.get("/workshop-admin")
async def workshop_admin_page(
    request: Request,
    created: str | None = None,
    deleted: str | None = None,
    uploaded: str | None = None,
    removed_file: str | None = None,
):
    _require_admin(request)
    packages = _load_workshop_packages()
    context = base_context(
        request,
        active_page="workshop_admin",
        page_title="Workshop",
        page_subtitle="Pacchetti pronti lato sito",
    )
    context.update(
        {
            "packages": packages,
            "created": created == "1",
            "deleted": deleted == "1",
            "uploaded": uploaded == "1",
            "removed_file": removed_file == "1",
        }
    )
    return render(request, "workshop_admin.html", context)


@router.post("/workshop-admin/add")
async def workshop_admin_add(
    request: Request,
    title: str = Form(...),
    subtitle: str = Form(default=""),
    price: str = Form(default=""),
    delivery: str = Form(default=""),
    description: str = Form(default=""),
    includes: str = Form(default=""),
    cta_label: str = Form(default="Richiedi info"),
    cta_href: str = Form(default="/contatti.html"),
    html_file: UploadFile = File(default=None),
):
    _require_admin(request)
    packages = _load_workshop_packages()

    html_web_path: str | None = None
    if html_file and html_file.filename:
        html_web_path = await _save_html_upload(html_file)

    new_item = _normalize_package(
        {
            "id": str(uuid.uuid4()),
            "title": title,
            "subtitle": subtitle,
            "price": price,
            "delivery": delivery,
            "description": description,
            "includes": [line.strip() for line in str(includes).splitlines() if line.strip()],
            "cta_label": cta_label,
            "cta_href": cta_href,
            "html_file": html_web_path,
            "active": True,
        }
    )
    packages.append(new_item)
    actor = getattr(request.state, "board_user", {}) or {}
    _save_workshop_packages(packages, updated_by=str(actor.get("email") or "admin"))
    return RedirectResponse(url="/workshop-admin?created=1", status_code=303)


@router.post("/workshop-admin/{package_id}/upload-html")
async def workshop_admin_upload_html(
    request: Request,
    package_id: str,
    html_file: UploadFile = File(...),
):
    _require_admin(request)
    target_id = _as_text(package_id, max_len=120)
    packages = _load_workshop_packages()
    target = next((p for p in packages if p.get("id") == target_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Pacchetto non trovato")

    # Rimuovi il vecchio file se esiste
    if target.get("html_file"):
        _delete_html_file(target["html_file"])

    web_path = await _save_html_upload(html_file)
    target["html_file"] = web_path

    actor = getattr(request.state, "board_user", {}) or {}
    _save_workshop_packages(packages, updated_by=str(actor.get("email") or "admin"))
    return RedirectResponse(url="/workshop-admin?uploaded=1", status_code=303)


@router.post("/workshop-admin/{package_id}/remove-html")
async def workshop_admin_remove_html(request: Request, package_id: str):
    _require_admin(request)
    target_id = _as_text(package_id, max_len=120)
    packages = _load_workshop_packages()
    target = next((p for p in packages if p.get("id") == target_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Pacchetto non trovato")

    if target.get("html_file"):
        _delete_html_file(target["html_file"])
        target["html_file"] = None

    actor = getattr(request.state, "board_user", {}) or {}
    _save_workshop_packages(packages, updated_by=str(actor.get("email") or "admin"))
    return RedirectResponse(url="/workshop-admin?removed_file=1", status_code=303)


@router.post("/workshop-admin/{package_id}/upload-image")
async def workshop_admin_upload_image(
    request: Request,
    package_id: str,
    image_file: UploadFile = File(...),
):
    """Carica un'immagine associata a un pacchetto.

    Le immagini vengono salvate in /uploads/workshop/assets/{package_id}/
    e sono accessibili via /uploads/workshop/assets/{package_id}/{filename}.

    Il file HTML del pacchetto può usare questi path relativi direttamente
    (es. <img src="foto.jpg">) grazie al base tag iniettato automaticamente.
    """
    _require_admin(request)
    target_id = _as_text(package_id, max_len=120)
    packages = _load_workshop_packages()
    if not any(p.get("id") == target_id for p in packages):
        raise HTTPException(status_code=404, detail="Pacchetto non trovato")

    content = await image_file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB max per immagine
        raise HTTPException(status_code=400, detail="Immagine troppo grande (max 10 MB)")

    # Valida estensione
    original_name = image_file.filename or "image"
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato non supportato. Usa: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
        )

    # Salva in assets/{package_id}/
    pkg_assets_dir = WORKSHOP_ASSETS_DIR / target_id
    pkg_assets_dir.mkdir(parents=True, exist_ok=True)

    # Usa il nome originale (sanitizzato) per render facile nei path relativi HTML
    safe_name = re.sub(r"[^\w.\-]", "_", Path(original_name).stem) + ext
    dest = pkg_assets_dir / safe_name
    dest.write_bytes(content)

    web_url = f"/uploads/workshop/assets/{target_id}/{safe_name}"
    logger.info(f"Immagine caricata per pacchetto {target_id}: {web_url}")
    return RedirectResponse(
        url=f"/workshop-admin?uploaded_image=1&img_url={web_url}&pkg_id={target_id}",
        status_code=303,
    )


@router.get("/workshop-admin/{package_id}/images")
async def workshop_admin_list_images(request: Request, package_id: str):
    """Elenca le immagini caricate per un pacchetto (JSON, per uso admin)."""
    _require_admin(request)
    target_id = _as_text(package_id, max_len=120)
    pkg_assets_dir = WORKSHOP_ASSETS_DIR / target_id
    images = []
    if pkg_assets_dir.exists():
        for f in sorted(pkg_assets_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS:
                images.append({
                    "filename": f.name,
                    "url": f"/uploads/workshop/assets/{target_id}/{f.name}",
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })
    return JSONResponse({"ok": True, "images": images})


@router.post("/workshop-admin/{package_id}/delete")
async def workshop_admin_delete(request: Request, package_id: str):
    _require_admin(request)
    target_id = _as_text(package_id, max_len=120)
    packages = _load_workshop_packages()

    # Rimuovi file HTML e immagini associate
    target = next((p for p in packages if p.get("id") == target_id), None)
    if target and target.get("html_file"):
        _delete_html_file(target["html_file"])

    # Rimuovi la cartella immagini del pacchetto
    pkg_assets_dir = WORKSHOP_ASSETS_DIR / target_id
    if pkg_assets_dir.exists():
        import shutil
        try:
            shutil.rmtree(pkg_assets_dir)
        except Exception as exc:
            logger.warning(f"Impossibile rimuovere assets pacchetto {target_id}: {exc}")

    packages = [item for item in packages if item.get("id") != target_id]
    actor = getattr(request.state, "board_user", {}) or {}
    _save_workshop_packages(packages, updated_by=str(actor.get("email") or "admin"))
    return RedirectResponse(url="/workshop-admin?deleted=1", status_code=303)
