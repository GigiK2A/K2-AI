import pytest

from aios.db import dsn_from_env, MissingDSNError


def test_dsn_from_env_reads_var(monkeypatch):
    monkeypatch.setenv("AIOS_TEST_DATABASE_URL", "postgresql://x")
    assert dsn_from_env("AIOS_TEST_DATABASE_URL") == "postgresql://x"


def test_dsn_from_env_missing_raises(monkeypatch):
    monkeypatch.delenv("AIOS_TEST_DATABASE_URL", raising=False)
    with pytest.raises(MissingDSNError):
        dsn_from_env("AIOS_TEST_DATABASE_URL")
