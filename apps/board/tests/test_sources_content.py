import os

import pytest

DSN = os.environ.get("AIOS_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="AIOS_DATABASE_URL not set")


def test_read_servizi_and_topics():
    import psycopg
    from aios.sources.content import read_servizi, read_topics
    with psycopg.connect(DSN) as conn:
        servizi = read_servizi(conn)
        topics = read_topics(conn)
    assert isinstance(servizi, list) and len(servizi) > 0
    assert "Servizio" in servizi[0] and "Stato" in servizi[0]
    assert isinstance(topics, list) and len(topics) > 0
    assert "Tema" in topics[0]
