"""Engine di interpretazione delle sanity rules (quick win #7, L1.b).

Le regole vivono in data/sanity_rules.json e sono dichiarative. Questo modulo le
legge e fornisce primitive per applicarle. L'applicazione effettiva dentro i tool
e' rinviata a F11 W4 (vedi MANIFESTO_AUTOVERIFICA.md): qui si installa solo il
catalogo + l'engine di lettura.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def sanity_check_enabled() -> bool:
    """True se l'applicazione delle sanity rules nei tool e' attiva (default ON)."""
    return os.getenv("K2A_SANITY_CHECK", "1") != "0"

_RULES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sanity_rules.json"
_RULES_CACHE: list[dict] | None = None


def load_sanity_rules() -> list[dict]:
    """Carica (e memoizza) la lista di regole da data/sanity_rules.json."""
    global _RULES_CACHE
    if _RULES_CACHE is None:
        _RULES_CACHE = json.loads(_RULES_PATH.read_text())["rules"]
    return _RULES_CACHE


def rules_for_tool(tool_name: str) -> list[dict]:
    """Regole applicabili a un tool: quelle specifiche + quelle 'all'."""
    return [r for r in load_sanity_rules() if r["applies_to"] in (tool_name, "all")]


def _check_rule(rule: dict, output: dict) -> str | None:
    """Verifica una singola sanity rule contro un output (dict serializzato).

    Ritorna None se la rule passa, altrimenti una stringa descrittiva della violazione.
    I nomi dei campi sono quelli reali degli Output pydantic (verificati in W2.2).
    """
    rule_name = rule["rule"]

    if rule_name == "eta_must_be_positive":
        eta = output.get("eta_globale")
        if eta is None:
            eta = output.get("eta_interazione")
        if eta is not None and eta <= 0:
            return f"eta_globale={eta} <= 0"

    elif rule_name == "eta_warning_above_one":
        eta = output.get("eta_globale")
        if eta is None:
            eta = output.get("eta_interazione")
        if eta is not None and eta > 1.0:
            return f"eta_globale={eta} > 1 (profilo non verifica)"

    elif rule_name == "qb_positive":
        qb = output.get("q_b_Nm2")
        if qb is not None and qb <= 0:
            return f"q_b_Nm2={qb} <= 0"

    elif rule_name == "qb_reasonable_range":
        qb = output.get("q_b_Nm2")
        if qb is not None:
            qb_kn = qb / 1000.0  # N/m^2 -> kN/m^2
            r = rule.get("range_kN_m2", [0.2, 1.5])
            if qb_kn < r[0] or qb_kn > r[1]:
                return f"q_b={qb_kn:.3f} kN/m2 fuori range plausibile {r}"

    elif rule_name == "Se_positive":
        for pt in output.get("spectrum", []) or []:
            se = pt.get("S_e_g", 0.0)
            if se is not None and se < 0:
                return f"S_e_g(T={pt.get('T_s')})={se} < 0"

    elif rule_name == "TB_lt_TC_lt_TD":
        tb, tc, td = output.get("T_B_s"), output.get("T_C_s"), output.get("T_D_s")
        if tb is not None and tc is not None and td is not None:
            if not (tb < tc < td):
                return f"violazione TB<TC<TD: {tb}, {tc}, {td}"

    elif rule_name == "gamma_G_min_max":
        return None  # combine_loads: output non standard, non implementato qui

    elif rule_name == "Q_lim_positive":
        q = output.get("q_Rd_kPa")
        if q is not None and q <= 0:
            return f"q_Rd_kPa={q} <= 0"

    elif rule_name == "N_Rd_positive":
        n_rd = output.get("N_Rd_kN")
        if n_rd is None:
            n_rd = output.get("N_Rd_steel_kN")
        if n_rd is not None and n_rd <= 0:
            return f"N_Rd={n_rd} <= 0"

    elif rule_name == "monotonia_carico_deformazione":
        return None  # property test su solver_cantilever, non per singolo output

    elif rule_name == "inputs_hash_present":
        h = output.get("inputs_hash")
        if not h or len(h) != 16:
            return f"inputs_hash mancante o malformato: {h!r}"

    elif rule_name == "git_sha_optional_but_format":
        sha = output.get("git_sha")
        if sha is not None:
            if not isinstance(sha, str) or not (7 <= len(sha) <= 12):
                return f"git_sha malformato: {sha!r}"

    return None


def apply_sanity_rules_to_output(
    tool_name: str,
    output_dict: dict,
    *,
    raise_on_error: bool = False,
) -> list[str]:
    """Applica le sanity rules definite per il tool dato all'output_dict.

    Args:
        tool_name: nome del tool (es. "check_tubular_resistance").
        output_dict: dict serializzato dell'Output del tool (model_dump del pydantic).
        raise_on_error: se True, solleva ValueError sulla prima rule "error" violata.
                        Default False = ritorna lista di warning string (non-blocking).

    Returns:
        Lista di stringhe di warning. Vuota se tutte le rules passano.
        Format: "SR-NNN [severity]: descrizione (violazione)".
    """
    warnings: list[str] = []
    for rule in rules_for_tool(tool_name):
        violation = _check_rule(rule, output_dict)
        if violation is not None:
            msg = f"{rule['id']} [{rule['severity']}]: {rule['description']} ({violation})"
            if rule["severity"] == "error" and raise_on_error:
                raise ValueError(msg)
            warnings.append(msg)
    return warnings
