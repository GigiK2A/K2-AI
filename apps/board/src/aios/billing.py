"""Metering dei costi LLM e budget con hard-stop per agente.

Prima di oggi l'AIOS non misurava un solo token: gli agenti potevano proporre
all'infinito senza tetto di spesa. Questo modulo aggiunge il primitivo mancante,
ispirato a Paperclip ("when they hit the limit, they stop, automatically"):

- **metering**: ogni chiamata LLM registra input/output token e il costo stimato,
  attribuito all'agente corrente (via `attribute(actor)`);
- **budget per agente**: un tetto mensile in EUR per attore;
- **hard-stop**: quando l'attore supera il tetto, il suo prossimo run viene bloccato.

Progettato per funzionare SENZA database (aggregato in memoria, così i test sono
ermetici) e per persistere su Supabase quando un client è disponibile
(`aios_cost_ledger` append-only + `aios_budget_state` running, come `aios_policy_state`).

Il metering non solleva MAI verso il chiamante LLM: un errore di contabilità non
deve rompere una risposta. Il blocco è deciso a monte del run dell'agente.
"""

from __future__ import annotations

import contextlib
import contextvars
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

# ── Listino prezzi (USD per 1M token: input, output) ──────────────────────────
# Fonte: listino Anthropic. Configurabile via env AIOS_PRICING_JSON per non
# hard-codare i prezzi nel codice. Modelli locali / sconosciuti = costo 0
# (tracciamo comunque i token, ma non stimiamo un prezzo a caso).
_DEFAULT_PRICING_USD: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet": (3.0, 15.0),
    "claude-opus-4": (15.0, 75.0),
    "claude-opus": (15.0, 75.0),
    "claude-haiku": (1.0, 5.0),
}


def _load_pricing() -> dict[str, tuple[float, float]]:
    pricing = dict(_DEFAULT_PRICING_USD)
    raw = os.environ.get("AIOS_PRICING_JSON", "").strip()
    if raw:
        try:
            for model, pair in json.loads(raw).items():
                pricing[str(model)] = (float(pair[0]), float(pair[1]))
        except Exception:
            pass
    return pricing


_PRICING_USD = _load_pricing()
_EUR_PER_USD = float(os.environ.get("AIOS_EUR_PER_USD", "0.92"))


def _price_for(model: str) -> tuple[float, float]:
    """(input, output) USD per 1M token. Match esatto, poi per prefisso, poi 0."""
    m = (model or "").strip().lower()
    if m in _PRICING_USD:
        return _PRICING_USD[m]
    for key, price in _PRICING_USD.items():
        if m.startswith(key):
            return price
    return (0.0, 0.0)


def cost_eur(model: str, input_tokens: int, output_tokens: int) -> float:
    """Costo stimato in EUR di una chiamata. 0 per modelli locali/sconosciuti."""
    pin, pout = _price_for(model)
    usd = (input_tokens / 1_000_000) * pin + (output_tokens / 1_000_000) * pout
    return round(usd * _EUR_PER_USD, 6)


# ── Attribuzione: chi sta spendendo adesso ────────────────────────────────────
# Impostata dall'agente attorno alle sue chiamate LLM. Il layer LLM la legge per
# addebitare il costo all'attore giusto senza cambiare le firme di complete().
_ctx_actor: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "aios_billing_actor", default=None)


@contextlib.contextmanager
def attribute(actor: str):
    token = _ctx_actor.set(actor)
    try:
        yield
    finally:
        _ctx_actor.reset(token)


def current_actor() -> Optional[str]:
    return _ctx_actor.get()


def _period_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


# ── Stato budget ──────────────────────────────────────────────────────────────
@dataclass
class BudgetStatus:
    actor: str
    period: str
    spent_eur: float
    cap_eur: Optional[float]   # None = nessun tetto

    @property
    def remaining_eur(self) -> Optional[float]:
        return None if self.cap_eur is None else round(self.cap_eur - self.spent_eur, 4)

    @property
    def over(self) -> bool:
        return self.cap_eur is not None and self.spent_eur >= self.cap_eur

    @property
    def ratio(self) -> Optional[float]:
        if not self.cap_eur:
            return None
        return round(self.spent_eur / self.cap_eur, 4)

    def near(self, warn_ratio: float) -> bool:
        r = self.ratio
        return r is not None and r >= warn_ratio and not self.over


class CostMeter:
    """Contabilità costi + gate di budget. Thread-safe. DB opzionale.

    `budgets`: {actor: tetto_mensile_eur}. Attori senza voce usano `default_cap`
    (None = illimitato). L'aggregato di spesa è in memoria (fonte di verità per
    i test); se `client` è presente si persiste anche su Supabase e si può
    reidratare al riavvio dal running-state `aios_budget_state`.
    """

    LEDGER_TABLE = "aios_cost_ledger"
    STATE_TABLE = "aios_budget_state"

    def __init__(self, client: Any = None, *, budgets: Optional[dict[str, float]] = None,
                 default_cap: Optional[float] = None, warn_ratio: float = 0.8) -> None:
        self._client = client
        self._budgets: dict[str, float] = dict(budgets or {})
        self._default_cap = default_cap
        self._warn_ratio = warn_ratio
        self._lock = threading.Lock()
        self._spend: dict[tuple[str, str], float] = {}
        self._hydrated: set[tuple[str, str]] = set()

    # -- budget config -----------------------------------------------------
    def set_budget(self, actor: str, cap_eur: Optional[float]) -> None:
        with self._lock:
            if cap_eur is None:
                self._budgets.pop(actor, None)
            else:
                self._budgets[actor] = float(cap_eur)

    def cap_for(self, actor: str) -> Optional[float]:
        if actor in self._budgets:
            return self._budgets[actor]
        return self._default_cap

    # -- persistence -------------------------------------------------------
    def _hydrate(self, actor: str, period: str) -> None:
        """Reidrata la spesa del periodo dal running-state (una volta per chiave)."""
        key = (actor, period)
        if key in self._hydrated or self._client is None:
            return
        self._hydrated.add(key)
        try:
            rows = self._client.select(self.STATE_TABLE, {
                "select": "spent_eur", "actor": f"eq.{actor}", "period": f"eq.{period}",
                "limit": "1"})
            if rows:
                self._spend[key] = float(rows[0].get("spent_eur") or 0.0)
        except Exception:
            pass

    def _persist(self, actor: str, period: str, model: str,
                 input_tokens: int, output_tokens: int, cost: float, new_total: float) -> None:
        if self._client is None:
            return
        try:  # ledger append-only
            self._client.insert(self.LEDGER_TABLE, {
                "actor": actor, "period": period, "model": model,
                "input_tokens": int(input_tokens), "output_tokens": int(output_tokens),
                "cost_eur": cost})
        except Exception:
            pass
        try:  # running-state upsert (O(1) per il gate)
            self._client.upsert(self.STATE_TABLE, {
                "actor": actor, "period": period, "spent_eur": round(new_total, 6),
                "updated_at": datetime.now(timezone.utc).isoformat()},
                on_conflict="actor,period")
        except Exception:
            pass

    # -- metering ----------------------------------------------------------
    def record_usage(self, model: str, input_tokens: int, output_tokens: int,
                     actor: Optional[str] = None) -> float:
        """Registra una chiamata LLM. Ritorna il costo EUR. Non solleva mai."""
        try:
            actor = actor or current_actor() or "system"
            period = _period_now()
            cost = cost_eur(model, input_tokens or 0, output_tokens or 0)
            with self._lock:
                self._hydrate(actor, period)
                key = (actor, period)
                new_total = self._spend.get(key, 0.0) + cost
                self._spend[key] = new_total
            self._persist(actor, period, model, input_tokens or 0, output_tokens or 0,
                          cost, new_total)
            return cost
        except Exception:
            return 0.0

    # -- lettura / gate ----------------------------------------------------
    def spent(self, actor: str, period: Optional[str] = None) -> float:
        period = period or _period_now()
        with self._lock:
            self._hydrate(actor, period)
            return round(self._spend.get((actor, period), 0.0), 6)

    def status(self, actor: str, period: Optional[str] = None) -> BudgetStatus:
        period = period or _period_now()
        return BudgetStatus(actor=actor, period=period,
                            spent_eur=self.spent(actor, period), cap_eur=self.cap_for(actor))

    def check(self, actor: str) -> BudgetStatus:
        """Stato budget per il gate hard-stop. `.over` = bloccare l'agente."""
        return self.status(actor)

    def report(self, actors: Optional[list[str]] = None) -> list[dict[str, Any]]:
        """Snapshot per attore (per cockpit/Telegram)."""
        names = actors if actors is not None else sorted({a for a, _ in self._spend} | set(self._budgets))
        out = []
        for a in names:
            s = self.status(a)
            out.append({"actor": a, "period": s.period, "spent_eur": round(s.spent_eur, 4),
                        "cap_eur": s.cap_eur, "remaining_eur": s.remaining_eur,
                        "ratio": s.ratio, "over": s.over, "warn": s.near(self._warn_ratio)})
        return out


# ── Singleton di processo, cablato da build_platform ──────────────────────────
_METER: Optional[CostMeter] = None
_METER_LOCK = threading.Lock()


def set_meter(meter: CostMeter) -> None:
    global _METER
    with _METER_LOCK:
        _METER = meter


def get_meter() -> CostMeter:
    """Meter corrente; se non cablato, ne crea uno in memoria (no-DB, no-cap)."""
    global _METER
    if _METER is None:
        with _METER_LOCK:
            if _METER is None:
                _METER = CostMeter()
    return _METER


def record_usage(model: str, input_tokens: int, output_tokens: int,
                 actor: Optional[str] = None) -> float:
    return get_meter().record_usage(model, input_tokens, output_tokens, actor)


def budgets_from_env() -> tuple[dict[str, float], Optional[float]]:
    """Legge i tetti da env:
    - AIOS_AGENT_BUDGETS = '{"finance_agent": 15, "marketing_agent": 25}' (EUR/mese)
    - AIOS_DEFAULT_AGENT_BUDGET_EUR = tetto di default per agenti non elencati (opz.)
    """
    budgets: dict[str, float] = {}
    raw = os.environ.get("AIOS_AGENT_BUDGETS", "").strip()
    if raw:
        try:
            for actor, cap in json.loads(raw).items():
                budgets[str(actor)] = float(cap)
        except Exception:
            pass
    default_raw = os.environ.get("AIOS_DEFAULT_AGENT_BUDGET_EUR", "").strip()
    default_cap = float(default_raw) if default_raw else None
    return budgets, default_cap
