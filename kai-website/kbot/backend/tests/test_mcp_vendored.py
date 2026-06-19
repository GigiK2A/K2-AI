"""Fallback MCP vendorizzato: quando l'entrypoint pip non è installato (repo privati,
pip-da-git disattivato in build), mcp_client deve lanciare il server VENDORIZZATO
(`python -m k2a_quant.server`, PYTHONPATH=vendor). Senza, quant/health resta 503."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.lib import mcp_client  # noqa: E402


def test_quant_risolve_via_vendored():
    spec = mcp_client._resolve("quant")
    assert spec is not None, "quant MCP non risolvibile (vendor/k2a_quant/server.py mancante?)"
    cmd, args, env = spec
    # nel repo non c'è l'entrypoint pip → deve cadere sul server vendorizzato
    launched = " ".join([cmd, *args])
    assert "k2a_quant.server" in launched or cmd.endswith("k2a-quant"), launched
    if "k2a_quant.server" in launched:
        assert "PYTHONPATH" in env, "il subprocess vendorizzato deve avere vendor in PYTHONPATH"


def test_available_riflette_il_resolve():
    # mcp installato (in requirements) + vendor presente → almeno quant deve risultare ok
    assert mcp_client.available("quant")


def test_env_override_supporta_args():
    import os
    os.environ["K2A_MCP_QUANT_CMD"] = "python -m custom.server --flag"
    try:
        cmd, args, _ = mcp_client._resolve("quant")
        assert cmd == "python" and args == ["-m", "custom.server", "--flag"]
    finally:
        os.environ.pop("K2A_MCP_QUANT_CMD", None)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
