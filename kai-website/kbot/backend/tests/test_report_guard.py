from app.lib.report_guard import ReportQualityError, validate_report
from app.lib.xlsx_renderer import _typed_cell


def _base():
    return {
        "meta": {
            "title": "Analisi Acme",
            "subtitle_lines": ["Acme S.r.l."],
            "client_meta_lines": ["Acme S.r.l.", "Generato il 20 giugno 2026"],
        },
        "blocks": [
            {"type": "executive_summary", "body_html": "Sintesi verificata."},
            {"type": "conclusions", "left": {}, "right": {}},
        ],
    }


def test_rejects_generic_client():
    d = _base()
    d["meta"]["client_meta_lines"] = ["Cliente", "Documento 2026"]
    try:
        validate_report(d)
        assert False, "expected ReportQualityError"
    except ReportQualityError:
        pass


def test_rejects_projection_without_assumptions():
    d = _base()
    d["blocks"].insert(1, {
        "type": "data_table", "title": "Proiezione ricavi",
        "columns": ["Anno", "Ricavi"], "rows": [["2027", "€120.000"]],
    })
    try:
        validate_report(d)
        assert False, "expected ReportQualityError"
    except ReportQualityError:
        pass


def test_accepts_projection_with_assumptions_and_kpi_provenance():
    d = _base()
    d["blocks"].insert(1, {
        "type": "kpi_grid", "items": [
            {"label": "Ricavi", "value": "€100.000", "verified": True},
            {"label": "Target", "value": "€110.000", "verified": False,
             "note": "Scenario illustrativo; assunzione +10% da validare"},
        ],
    })
    d["blocks"].insert(2, {
        "type": "data_table", "title": "Proiezione ricavi",
        "intro": "Assunzioni: crescita illustrativa del 10%, da validare.",
        "columns": ["Anno", "Ricavi"], "rows": [["2027", "€110.000"]],
    })
    assert validate_report(d) is d


def test_excel_cells_keep_numbers_percentages_and_formulas():
    assert _typed_cell("€ 12.345,67")[0] == 12345.67
    assert _typed_cell("15,4%")[0] == 0.154
    assert _typed_cell("=SUM(B2:B4)")[0] == "=SUM(B2:B4)"
