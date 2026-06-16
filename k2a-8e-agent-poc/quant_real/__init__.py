"""k2a-quant-patch — pezze del gap per il k2a_quant di Luca.

Da merge nel package canonico (vedi 00-LEGGIMI.md). Espone:
  - calc_result      envelope CalcResult (provenienza)
  - capm             capm_cost_of_equity (assunzioni dallo snapshot)
  - ev_multiples     ev_from_multiples
  - valida_assunzioni  il recinto del giudizio (OK/WARN/FAIL)
  - dcf_guard        g-range hard-reject sul DCF esistente
  - snapshot         helper + i 3 campi mancanti (g_range, banda_cagr, size_premium)
"""
from .calc_result import calc_result, make_call_id, inputs_hash  # noqa: F401
from .capm import capm_cost_of_equity  # noqa: F401
from .ev_multiples import ev_from_multiples  # noqa: F401
from .valida_assunzioni import valida_assunzioni  # noqa: F401
