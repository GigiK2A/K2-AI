# Hospitality Skills Integration — Design Spec
**Date:** 2026-05-12  
**Status:** Approved

## Goal

Integrate 29 K-bot Hospitality skills (from `k-bot-hospitality-skills (1).zip`) into the existing kbot skill pool so the bot automatically uses hospitality-specific knowledge when users ask about revenue management, B&B, OTA, RevPAR, agriturismi, pricing dinamico, ecc.

## Architecture

### File layout (after change)

```
assets/skills/
├── skills sito k2-ai 2/          ← existing, unchanged
│   ├── P01 - Agenti Email e CRM/skills.md
│   └── ... (P01-P19)
└── hospitality/                  ← new
    ├── orchestratore-hospitality/SKILL.md
    ├── check-host-express/SKILL.md
    ├── flusso-hostboost-ricettive/SKILL.md
    ├── property-management-revenue/SKILL.md
    └── ... (25 support skills)
```

### Backend changes (`backend/app/main.py`)

**Only two changes:**

1. Replace single `SKILLS_ROOT` with `SKILLS_ROOTS` list:
   ```python
   SKILLS_ROOTS = [
       ROOT / "assets" / "skills" / "skills sito k2-ai 2",
       ROOT / "assets" / "skills" / "hospitality",
   ]
   ```

2. Update `get_skill_packs()` to iterate both roots and accept either `skills.md` or `SKILL.md` (case-insensitive, first found wins):
   ```python
   def get_skill_packs() -> list[dict[str, str]]:
       packs = []
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

All downstream functions (`find_relevant_skills`, `select_skills_for_context`, `build_prompt`) are unchanged — they consume the unified pool.

### Routing behavior (no code change needed)

The existing keyword-scoring in `find_relevant_skills` handles routing:
- General PMI query → P01-P19 win (have those keywords)
- "RevPAR", "B&B", "OTA", "agriturismo", "occupancy", "pricing", "ricettivo" → hospitality skills win
- Mixed query → highest-scoring mix returned (up to `limit=6`)

### Frontend

No changes. `usedSkills` in the response already shows whichever skills were selected.

## Data flow

```
User message
  → select_skills_for_context()
      → get_skill_packs()  ← now scans 2 roots
      → find_relevant_skills()  ← keyword score on unified pool
  → build_prompt()  ← top-N skill markdowns injected
  → Claude API
  → response with usedSkills
```

## Out of scope

- New UI mode for hospitality
- Dedicated hospitality system prompt / funnel enforcement
- XLSX/HTML report generation from check-host-express template
- Payment/lead capture for 149/1499/2999 EUR packages (backend unchanged)

## Steps

1. Extract zip → `assets/skills/hospitality/` (exclude `__MACOSX`, `.DS_Store`)
2. Update `backend/app/main.py`: `SKILLS_ROOT` → `SKILLS_ROOTS`, update `get_skill_packs()`
3. Smoke test: `GET /api/skills` must return ≥ 29 more skills than before
4. Smoke test: send "come aumentare il RevPAR del mio agriturismo" → `usedSkills` contains at least one hospitality skill
