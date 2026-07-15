"""Regressione audit lug 2026 (spec "principal engineer" di Luca, 15 lug).

Un test per ciascun difetto di classe "report credibile ma falso":
- 1c: placeholder det-sample nel PDF ("esempio", nome-servizio, campi opzionali inventati)
- 1d: numeri hard-financial inventati etichettati e consegnati sui boost finanziari
- 1e: etichetta di intensità non mappabile → 0 ("nessun impatto")
"""
from __future__ import annotations

from app import llm, quality


# ── 1c: fallback stringhe dei campioni deterministici → N/D onesto ────────────────

def test_det_string_fallback_dice_nd_non_il_nome_servizio():
    s = llm._det_string("analisi_generale", {"type": "string"}, {}, "FinanceBoost")
    assert "N/D" in s and "FinanceBoost" not in s


def test_det_string_fallback_rispetta_min_max_length():
    s = llm._det_string("x", {"type": "string", "minLength": 120}, {}, "Svc")
    assert len(s) >= 120 and s.startswith("N/D")
    s2 = llm._det_string("x", {"type": "string", "maxLength": 30}, {}, "Svc")
    assert len(s2) <= 30


def test_det_sample_required_only_non_inventa_campi_opzionali():
    schema = {"type": "object",
              "properties": {"descrizione": {"type": "string", "minLength": 10},
                             "importo_eur": {"type": "number"},
                             "nota": {"type": "string"}},
              "required": ["descrizione"]}
    out = llm._det_sample(schema, schema, {}, "Svc", "sezione", required_only=True)
    assert set(out) == {"descrizione"}          # niente importo_eur=1 inventato
    full = llm._det_sample(schema, schema, {}, "Svc", "sezione")
    assert set(full) == {"descrizione", "importo_eur", "nota"}  # default invariato (meta)


# ── 1d: neutralizzazione numeri hard-financial non grounded ───────────────────────

def test_neutralize_rimuove_il_numero_inventato_e_marca():
    v = quality._neutralize_value("EBITDA stimato a 350.000 € nel periodo", known=set())
    assert "350.000" not in v and "N/D" in v and "non verificato" in v


def test_neutralize_conserva_il_numero_grounded():
    known = {round(720000.0, 4), round(720.0, 4)}  # entrambe le letture di '720.000'
    v = quality._neutralize_value("EBITDA dichiarato 720.000 € dal cliente", known)
    assert "720.000" in v and "N/D" not in v


def test_neutralize_rispetta_le_assunzioni_esplicite():
    v = quality._neutralize_value(
        "ricavi attesi 500.000 € (ipotesi da confermare)", known=set())
    assert "500.000" in v  # già etichettata onestamente → non si tocca


def test_neutralize_walk_annidato():
    d = {"scenari": [{"descrizione": "utile atteso 90.000 € a fine anno"}],
         "titolo": "Piano"}
    out = quality.neutralize_ungrounded_numbers(d, {}, {}, [])
    assert "90.000" not in out["scenari"][0]["descrizione"]
    assert out["titolo"] == "Piano"


# ── 1e: etichetta non mappabile → valore centrale, mai 0 ──────────────────────────

def test_clamp_label_intensita_mai_zero():
    schema = {"type": "integer"}
    assert llm._clamp_to_schema("elevata", schema, schema) == 3
    assert llm._clamp_to_schema("sconosciuta", schema, schema) == 2  # era 0
