from aios.layers.deliverable import build_deliverable


def test_deliverable_has_sections_and_sources():
    md = build_deliverable(
        titolo="Report Marketing K2-AI",
        insights=[{"titolo": "Engagement basso", "evidenza": "9 like su 5 post", "azione": "numeri nelle caption"}],
        proposte=[{"tipo": "caption", "titolo": "Caption con numero", "contenuto": "...", "motivo": "..."}],
        fonti=[{"campo": "9 like", "fonte": "Instagram Graph API", "valore": "total_interactions=9"}])
    assert "# Report Marketing K2-AI" in md
    assert "Engagement basso" in md
    assert "## Fonti" in md
    assert "Instagram Graph API" in md
