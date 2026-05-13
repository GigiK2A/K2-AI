# Hospitality Skills Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 29 K-bot Hospitality skills to the kbot skill pool so the bot uses hospitality-specific knowledge when users ask about RevPAR, B&B, OTA, agriturismi, pricing dinamico, ecc.

**Architecture:** Extract `k-bot-hospitality-skills (1).zip` into `assets/skills/hospitality/`. Update `get_skill_packs()` in the backend to scan two roots (`skills sito k2-ai 2/` and `hospitality/`) and accept either `skills.md` or `SKILL.md`. Unified pool — existing keyword scoring handles routing automatically.

**Tech Stack:** Python 3.13, FastAPI, existing `backend/app/main.py`. No new dependencies.

---

## File Map

| File | Change |
|---|---|
| `assets/skills/hospitality/` | Create — extracted from zip (29 skill folders, each with `SKILL.md`) |
| `backend/app/main.py` | Modify — `SKILLS_ROOT` → `SKILLS_ROOTS`, update `get_skill_packs()` |
| `backend/tests/test_skill_loader.py` | Create — pytest tests for the updated loader |

---

### Task 1: Add pytest to backend and write failing tests

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_skill_loader.py`

- [ ] **Step 1: Add pytest to requirements**

Append to `backend/requirements.txt`:
```
pytest==8.3.5
```

Install:
```bash
cd backend && .venv/bin/pip install pytest==8.3.5
```

Expected output: `Successfully installed pytest-8.3.5`

- [ ] **Step 2: Create tests package**

```bash
mkdir -p /Volumes/PARASSITA/kbot/backend/tests
touch /Volumes/PARASSITA/kbot/backend/tests/__init__.py
```

- [ ] **Step 3: Write failing tests**

Create `backend/tests/test_skill_loader.py`:

```python
"""Tests for multi-root skill loading (hospitality integration)."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import get_skill_packs, SKILLS_ROOTS


def test_skills_roots_is_list():
    """SKILLS_ROOTS must be a list of paths, not a single path."""
    assert isinstance(SKILLS_ROOTS, list)
    assert len(SKILLS_ROOTS) >= 2


def test_hospitality_root_exists():
    """The hospitality skills folder must exist on disk."""
    hosp_root = next((r for r in SKILLS_ROOTS if "hospitality" in str(r)), None)
    assert hosp_root is not None, "No hospitality root in SKILLS_ROOTS"
    assert hosp_root.exists(), f"Hospitality root missing: {hosp_root}"


def test_get_skill_packs_returns_hospitality_skills():
    """Pool must contain at least the 4 core hospitality skills."""
    packs = get_skill_packs()
    names = {p["name"] for p in packs}
    core = {
        "orchestratore-hospitality",
        "check-host-express",
        "flusso-hostboost-ricettive",
        "property-management-revenue",
    }
    missing = core - names
    assert not missing, f"Missing hospitality skills: {missing}"


def test_get_skill_packs_retains_general_skills():
    """Pool must still contain at least one general P0x skill."""
    packs = get_skill_packs()
    names = {p["name"] for p in packs}
    general = [n for n in names if n.startswith("p0") or n.startswith("p1")]
    assert general, "General P0x/P1x skills not found in pool"


def test_skill_packs_have_required_keys():
    """Every pack must have id, name, markdown."""
    packs = get_skill_packs()
    assert packs, "No skill packs loaded"
    for pack in packs:
        assert "id" in pack
        assert "name" in pack
        assert "markdown" in pack
        assert len(pack["markdown"]) > 0, f"Empty markdown in pack: {pack['name']}"
```

- [ ] **Step 4: Run tests — verify they fail**

```bash
cd /Volumes/PARASSITA/kbot/backend && .venv/bin/pytest tests/test_skill_loader.py -v
```

Expected: `FAILED` on `test_skills_roots_is_list` and `test_hospitality_root_exists` (SKILLS_ROOTS doesn't exist yet).

- [ ] **Step 5: Commit failing tests**

```bash
git add backend/requirements.txt backend/tests/
git commit -m "test: add skill loader tests for hospitality integration"
```

---

### Task 2: Extract hospitality skills to assets

**Files:**
- Create: `assets/skills/hospitality/` (29 subdirs, each with `SKILL.md`)

- [ ] **Step 1: Extract zip, exclude macOS artifacts**

```bash
cd /Volumes/PARASSITA/kbot && \
  unzip -q "k-bot-hospitality-skills (1).zip" \
    -x "__MACOSX/*" "*.DS_Store" "*._*" \
    -d /tmp/hosp-extract
```

Expected: no output (quiet mode).

- [ ] **Step 2: Move to assets**

```bash
mv /tmp/hosp-extract/k-bot-hospitality-skills /Volumes/PARASSITA/kbot/assets/skills/hospitality
```

- [ ] **Step 3: Verify folder structure**

```bash
ls /Volumes/PARASSITA/kbot/assets/skills/hospitality/ | head -10
find /Volumes/PARASSITA/kbot/assets/skills/hospitality -name "SKILL.md" | wc -l
```

Expected: folder list with 29 entries; `SKILL.md` count = 29.

- [ ] **Step 4: Commit extracted skills**

```bash
git add assets/skills/hospitality/
git commit -m "feat: add k-bot-hospitality-skills (29 SKILL.md packs)"
```

---

### Task 3: Update backend — multi-root skill loader

**Files:**
- Modify: `backend/app/main.py` (lines 27, 122–135)

- [ ] **Step 1: Replace SKILLS_ROOT with SKILLS_ROOTS**

In `backend/app/main.py`, replace:
```python
SKILLS_ROOT = ROOT / "assets" / "skills" / "skills sito k2-ai 2"
```
with:
```python
SKILLS_ROOTS = [
    ROOT / "assets" / "skills" / "skills sito k2-ai 2",
    ROOT / "assets" / "skills" / "hospitality",
]
```

- [ ] **Step 2: Update get_skill_packs()**

Replace the existing `get_skill_packs` function (lines ~122–135):
```python
def get_skill_packs() -> list[dict[str, str]]:
    packs: list[dict[str, str]] = []
    for root in SKILLS_ROOTS:
        if not root.exists():
            continue
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            md_path = next(
                (entry / name for name in ("skills.md", "SKILL.md") if (entry / name).exists()),
                None,
            )
            if md_path is None:
                continue
            markdown = md_path.read_text(encoding="utf-8", errors="ignore")
            packs.append({"id": to_id(entry.name), "name": entry.name, "markdown": markdown})
    return packs
```

- [ ] **Step 3: Run tests — verify they pass**

```bash
cd /Volumes/PARASSITA/kbot/backend && .venv/bin/pytest tests/test_skill_loader.py -v
```

Expected output:
```
PASSED tests/test_skill_loader.py::test_skills_roots_is_list
PASSED tests/test_skill_loader.py::test_hospitality_root_exists
PASSED tests/test_skill_loader.py::test_get_skill_packs_returns_hospitality_skills
PASSED tests/test_skill_loader.py::test_get_skill_packs_retains_general_skills
PASSED tests/test_skill_loader.py::test_skill_packs_have_required_keys
5 passed
```

- [ ] **Step 4: Smoke test via HTTP**

Start the backend (if not running):
```bash
cd /Volumes/PARASSITA/kbot/backend && .venv/bin/uvicorn app.main:app --reload --port 8000 &
sleep 2
```

Check skill count:
```bash
curl -s http://localhost:8000/api/skills | python3 -c "import sys,json; d=json.load(sys.stdin); print('Total skills:', d['total'])"
```

Expected: `Total skills: 48` (19 general + 29 hospitality).

Check hospitality routing:
```bash
curl -s -X POST http://localhost:8000/api/skills/match \
  -H "Content-Type: application/json" \
  -d '{"input": "come aumento il RevPAR del mio agriturismo in Toscana?", "limit": 6}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(s['name']) for s in d['skills']]"
```

Expected: at least `orchestratore-hospitality` or `property-management-revenue` in the list.

- [ ] **Step 5: Commit backend changes**

```bash
git add backend/app/main.py
git commit -m "feat: multi-root skill loader — add hospitality skills pool"
```

---

## Self-Review

**Spec coverage:**
- [x] Extract zip → `assets/skills/hospitality/` — Task 2
- [x] `SKILLS_ROOT` → `SKILLS_ROOTS` — Task 3 Step 1
- [x] `get_skill_packs()` reads both roots, both filenames — Task 3 Step 2
- [x] Smoke test `/api/skills` count ≥ 29 more — Task 3 Step 4
- [x] Smoke test RevPAR query → hospitality skill in usedSkills — Task 3 Step 4
- [x] No frontend changes — confirmed out of scope

**Placeholder scan:** None found.

**Type consistency:** `SKILLS_ROOTS` referenced identically in tests and main.py. `get_skill_packs()` signature unchanged.
