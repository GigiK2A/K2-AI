"""OCR recovery formule matematiche via Gemini Vision (NT-2.1).

SDK: google-genai (nuovo, `from google import genai` + `client.models.generate_content`).
Modello default: gemini-2.5-flash (OCR formule eccellente, costo ~$0.01/pagina,
molto più rapido del pro). Cache locale JSON per idempotenza e zero re-spesa.

La key è letta da GEMINI_API_KEY (env) con fallback a `.env` nel cwd (gitignored).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional

from PIL import Image

CACHE_DIR = Path("data/ocr_workspace/cache")
DEFAULT_MODEL = "gemini-2.5-flash"

EXTRACTION_PROMPT = """Sei un OCR specializzato in matematica scientifica italiana.

Questa è una pagina della Circolare 7/2019 (commentario alle NTC 2018), capitolo
C4.2 Costruzioni in acciaio. Contiene testo italiano, formule matematiche e tabelle.

Estrai TUTTE le formule matematiche presenti, in JSON. Per ogni formula:
- "formula_unicode": forma Unicode leggibile (es. "N_pl,Rd = A·f_yk/γ_M0")
- "formula_latex": forma LaTeX (es. "N_{pl,Rd} = \\\\frac{A \\\\cdot f_{yk}}{\\\\gamma_{M0}}")
- "context": breve descrizione (es. "Resistenza plastica di calcolo a trazione")
- "section_ref": riferimento sezione se visibile (es. "C4.2.4.1.2")

Rispondi SOLO con JSON valido:
{"formulas": [{"formula_unicode": "...", "formula_latex": "...", "context": "...", "section_ref": "..."}], "page_topic": "..."}
Se non ci sono formule: {"formulas": [], "page_topic": "..."}.
Nessun preambolo o commento fuori dal JSON.
"""

# Costo stimato per pagina (input image ~ qualche centinaio di token + output).
_COST_PER_PAGE = {"pro": 0.05, "flash": 0.01}


def _load_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    env = Path(".env")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("GEMINI_API_KEY mancante (env o .env)")


def _client():
    from google import genai
    return genai.Client(api_key=_load_api_key())


def _cache_key(image_path: Path) -> Path:
    h = hashlib.sha1(image_path.read_bytes()).hexdigest()[:16]
    return CACHE_DIR / f"{image_path.stem}_{h}.json"


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    if text.lstrip().startswith("json"):
        text = text.lstrip()[4:].lstrip()
    return text.strip()


def ocr_page(image_path: Path, model_name: str = DEFAULT_MODEL,
             use_cache: bool = True, retries: int = 2,
             client=None) -> dict:
    """OCR di una pagina PNG. Ritorna dict con formulas, page_topic, page_number, cached, model."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_key(image_path)
    if use_cache and cache_file.exists():
        r = json.loads(cache_file.read_text())
        r["cached"] = True
        return r

    if client is None:
        client = _client()

    page_num = None
    try:
        page_num = int(image_path.stem.split("_")[-1])
    except (ValueError, IndexError):
        pass

    image = Image.open(image_path)
    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = client.models.generate_content(
                model=model_name, contents=[EXTRACTION_PROMPT, image]
            )
            result = json.loads(_strip_json_fences(resp.text))
            result.update({"page_number": page_num, "cached": False, "model": model_name})
            cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        except json.JSONDecodeError as e:
            last_err = e
            print(f"  ⚠️ JSON decode attempt {attempt+1}: {e}")
            time.sleep(2)
        except Exception as e:  # rate limit, network, ...
            last_err = e
            print(f"  ⚠️ Gemini error attempt {attempt+1}: {str(e)[:120]}")
            time.sleep(5)
    return {"formulas": [], "page_topic": "OCR FAILED", "page_number": page_num,
            "cached": False, "model": model_name, "error": str(last_err)}


def ocr_pages_batch(image_dir: Path, model_name: str = DEFAULT_MODEL,
                    pages_filter: Optional[list[int]] = None,
                    cost_cap_usd: float = 10.0) -> dict:
    images = sorted(image_dir.glob("page_*.png"))
    if pages_filter:
        images = [i for i in images if int(i.stem.split("_")[-1]) in pages_filter]
    print(f"Batch OCR: {len(images)} pagine, model={model_name}")

    client = _client()
    cost_per_page = _COST_PER_PAGE["pro" if "pro" in model_name else "flash"]
    results, cost = {}, 0.0
    start = time.time()
    for i, img in enumerate(images, 1):
        print(f"[{i}/{len(images)}] {img.name}", end=" ")
        r = ocr_page(img, model_name, client=client)
        if r.get("cached"):
            print(f"✅ cached ({len(r.get('formulas', []))} formule)")
        else:
            cost += cost_per_page
            print(f"📝 {len(r.get('formulas', []))} formule, ~${cost:.2f}"
                  + (f"  ❌ {r['error'][:60]}" if "error" in r else ""))
        if r.get("page_number") is not None:
            results[r["page_number"]] = r
        if cost > cost_cap_usd:
            print(f"🛑 STOP: costo ${cost:.2f} > cap ${cost_cap_usd}")
            break
    dur = time.time() - start
    print(f"\n✅ Batch: {len(results)} pagine, {dur:.0f}s, ~${cost:.2f}")
    return {"results": results, "cost_estimate_usd": round(cost, 2), "duration_sec": round(dur, 1)}


def main() -> None:
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 -m k2a_norme_tecniche.ocr.formula_ocr <image_dir> [model]")
        sys.exit(1)
    model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL
    batch = ocr_pages_batch(Path(sys.argv[1]), model_name=model)
    summary = {
        "total_pages": len(batch["results"]),
        "total_formulas": sum(len(r.get("formulas", [])) for r in batch["results"].values()),
        "pages_failed": [p for p, r in batch["results"].items() if "error" in r],
        "model": model,
        "cost_estimate_usd": batch["cost_estimate_usd"],
        "duration_sec": batch["duration_sec"],
    }
    out = Path(sys.argv[1]).parent / "ocr_batch_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Summary -> {out}: {summary}")


if __name__ == "__main__":
    main()
