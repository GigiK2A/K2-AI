from aios.layers.knowledge import KnowledgeStore, _chunks


class FakeClient:
    def __init__(self):
        self.rows = []

    def insert(self, table, row):
        assert table == "aios_knowledge"
        r = {"id": len(self.rows) + 1, **row}
        self.rows.append(r)
        return [r]

    def select(self, table, params):
        return list(self.rows)


def test_chunks_splits_text():
    text = "Para uno.\n\n" + ("x" * 600) + "\n\n" + ("y" * 600)
    cs = _chunks(text, size=500)
    assert len(cs) >= 2 and all(c.strip() for c in cs)


def test_ingest_and_search_ranks_by_term_overlap():
    c = FakeClient()
    kb = KnowledgeStore(c)
    kb.add(source="claude.md", chunk="K2-AI vende sistemi AI operativi per PMI italiane 5-50 dipendenti")
    kb.add(source="docs", chunk="Ricetta della pasta al pomodoro con basilico")
    kb.add(source="claude.md", chunk="Posizionamento: automazione AI chiavi in mano in 30-60 giorni per PMI")
    hits = kb.search("automazione AI per PMI", k=2)
    assert len(hits) == 2
    assert any("PMI" in h for h in hits)
    assert "pomodoro" not in " ".join(hits)   # irrelevant chunk excluded


def test_ingest_text_creates_multiple_rows():
    c = FakeClient()
    kb = KnowledgeStore(c)
    n = kb.ingest_text(source="x", text="Blocco uno.\n\n" + ("z" * 1200))
    assert n >= 2 and len(c.rows) == n
