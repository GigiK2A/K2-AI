"""Fatti VERIFICATI dal sito (social link + SEO on-page) — deterministici, contro la
confabulazione dei canali del cliente ('LinkedIn assente' asserito senza guardare).
Fixture, niente rete."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.lib import url_fetcher as uf  # noqa: E402

_CON_LINKEDIN = """<html><head><title>Studio X</title>
<meta name="description" content="Studio di ingegneria"></head>
<body><footer><a href="https://www.linkedin.com/company/studio-x">LinkedIn</a>
<a href="https://instagram.com/studiox">IG</a></footer></body></html>"""

_SENZA_SOCIAL = """<html><head><title>Studio Y</title></head>
<body><p>Niente social qui</p></body></html>"""


def _vf(html):
    data = uf.extract_html_content(html, "https://x.it")
    return uf.extract_verified_facts(html, data)


def test_rileva_social_e_seo_presenti():
    vf = _vf(_CON_LINKEDIN)
    soc = vf["social_link_nel_sito"]
    assert soc["linkedin"] is True
    assert soc["instagram"] is True
    assert soc["facebook"] is False
    assert vf["seo_onpage"]["title_presente"] is True
    assert vf["seo_onpage"]["meta_description_presente"] is True


def test_social_assenti_non_confabulati():
    vf = _vf(_SENZA_SOCIAL)
    assert all(v is False for v in vf["social_link_nel_sito"].values())
    assert vf["seo_onpage"]["title_presente"] is True
    assert vf["seo_onpage"]["meta_description_presente"] is False
    # il summary deve dichiarare i social NON linkati (per groundare il report)
    s = uf.build_verified_summary(vf)
    assert "NESSUNO" in s and "linkedin" in s.lower()


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
