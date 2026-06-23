"""MCP server entrypoint per k2a-budget.

Espone 3 tool: budget_36m, budget_sensitivity, budget_scenari.
Pattern stesso del k2a-quant (stdio).
"""
from __future__ import annotations

from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - mcp opzionale per i test
    FastMCP = None

from .engine import budget_36m as _budget_36m
from .scenari import budget_scenari as _budget_scenari
from .sensitivity import budget_sensitivity as _budget_sensitivity


def _build_app():
    app = FastMCP("k2a-budget")

    @app.tool()
    def budget_36m(
        bilancio_base: dict,
        assunzioni: Optional[dict] = None,
        aliquota_imposte_pct: Optional[float] = None,
        pfn_iniziale_eur: Optional[float] = None,
    ) -> dict:
        """Proiezione budget 36 mesi (P&L + FCF) deterministica e tracciabile."""
        return _budget_36m(bilancio_base, assunzioni, aliquota_imposte_pct, pfn_iniziale_eur)

    @app.tool()
    def budget_sensitivity(
        bilancio_base: dict,
        assunzioni: Optional[dict] = None,
        aliquota_imposte_pct: Optional[float] = None,
        delta_pct: float = 10.0,
    ) -> dict:
        """Sensitivity ±Δ% su 3 leve (ricavi, margine_variabile, costi_fissi)."""
        return _budget_sensitivity(bilancio_base, assunzioni, aliquota_imposte_pct, delta_pct)

    @app.tool()
    def budget_scenari(
        bilancio_base: dict,
        assunzioni: Optional[dict] = None,
        aliquota_imposte_pct: Optional[float] = None,
        pfn_iniziale_eur: Optional[float] = None,
    ) -> dict:
        """3 scenari: pessimistico (-2pp crescita), base, ottimistico (+3pp crescita)."""
        return _budget_scenari(bilancio_base, assunzioni, aliquota_imposte_pct, pfn_iniziale_eur)

    return app


def main() -> None:
    if FastMCP is None:
        raise RuntimeError("mcp non installato; pip install 'mcp[cli]'")
    app = _build_app()
    app.run()


if __name__ == "__main__":
    main()
