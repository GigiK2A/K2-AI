"""La skill fiscale non deve più insegnare le percentuali del ravvedimento di prima del D.Lgs. 87/2024.

Fonte: testo vigente art. 13 D.Lgs. 472/1997 e art. 13 D.Lgs. 471/1997 (Normattiva, 20/10/2026). Le tre copie della
skill (produzione, board, legacy) devono restare identiche.
"""
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[3]
COPIE = [
    RADICE / "lib/skills/fiscale-tributario-italiano",
    RADICE.parent / "apps/board/src/aios/skills_lib/fiscale-tributario-italiano",
    RADICE / "kbot/assets/skills/legacy-kai-website/fiscale-tributario-italiano",
]


@pytest.mark.parametrize("d", COPIE, ids=lambda d: d.parts[-4])
def test_tabella_ravvedimento_aggiornata(d):
    for nome in ("SKILL.md", "references/accertamenti-contenzioso.md"):
        t = (d / nome).read_text(encoding="utf-8")
        assert "1,39%" in t and "3,125%" in t and "3,57%" in t and "25%" in t
        assert "4,29%" not in t and "**3,75%**" not in t       # i numeri della vecchia tabella
        assert "1° gennaio 2027" in t                           # abrogazione dell'art. 13 segnalata


def test_le_tre_copie_sono_identiche():
    for nome in ("SKILL.md", "references/accertamenti-contenzioso.md"):
        testi = {(d / nome).read_text(encoding="utf-8") for d in COPIE}
        assert len(testi) == 1
