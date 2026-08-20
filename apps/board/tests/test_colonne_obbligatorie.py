"""Una colonna NOT NULL che l'agente chiama con un altro nome non deve costare la riga.

Il 20 ago 2026 Vendite ha provato ad aprire la pipeline da 10 prospect: PostgREST ha
risposto 400 (23502, `null value in column "name"`) su TUTTI e dieci. Chi apre un lead
ragiona in termini di azienda; `pipeline_leads.name` è NOT NULL senza default.
Verificato sullo schema reale via OpenAPI: `name` e `status` sono NOT NULL, ma solo
`name` non ha un default.
"""
import pytest

from aios.actuator import ActuatorError, _sanitize


def test_name_dedotto_da_company():
    out = _sanitize("pipeline_leads",
                    {"company": "Modulo S.r.l.", "email": "info@modulonet.com",
                     "sector": "manifatturiero"}, "insert")
    assert out["name"] == "Modulo S.r.l."
    assert out["company"] == "Modulo S.r.l."      # company resta al suo posto


def test_un_name_esplicito_non_viene_sovrascritto():
    out = _sanitize("pipeline_leads",
                    {"name": "Mario Rossi", "company": "Modulo S.r.l."}, "insert")
    assert out["name"] == "Mario Rossi"


def test_senza_company_si_ripiega_sull_email():
    out = _sanitize("pipeline_leads", {"email": "info@laintegra.com"}, "insert")
    assert out["name"] == "info@laintegra.com"


def test_su_update_non_si_inventa_niente():
    """In update la colonna è già valorizzata sulla riga: riempirla sarebbe sovrascriverla."""
    out = _sanitize("pipeline_leads", {"company": "Modulo S.r.l."}, "update")
    assert "name" not in out


def test_altre_tabelle_non_toccate():
    out = _sanitize("marketing_prospects", {"company": "Alfa", "fit_score": 80}, "insert")
    assert "name" not in out


def test_una_riga_che_non_ha_di_che_dedurre_resta_un_errore():
    """Niente company, niente email: meglio l'errore onesto che una riga senza nome."""
    with pytest.raises(ActuatorError):
        _sanitize("pipeline_leads", {"colonna_inventata": "x"}, "insert")
