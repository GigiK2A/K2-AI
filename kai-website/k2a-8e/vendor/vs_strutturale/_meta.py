"""Metadati di audit trail per i CalcResult.

Espone il git_sha del commit corrente, fondamentale per l'audit trail e il
regression testing L6 (vedi MANIFESTO_AUTOVERIFICA.md): quando un CalcResult
sostiene un'asseverazione, si deve poter risalire al codice esatto che l'ha
generato.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@lru_cache(maxsize=1)
def get_git_sha() -> str | None:
    """SHA breve del commit HEAD corrente. None se non in un repo git.

    Memoizzato: il subprocess git gira una sola volta per processo (lo SHA è
    costante a parità di commit, quindi non intacca il determinismo dei tool).
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=_REPO_ROOT,
        )
        sha = result.stdout.strip()
        return sha or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
