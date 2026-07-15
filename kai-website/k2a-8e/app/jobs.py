"""Job store in-memory (Phase-1, non durabile). Phase-2: storage esterno."""
from __future__ import annotations

import logging
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Optional

from .settings import JOB_TIMEOUT_S, OUT_DIR

log = logging.getLogger("8e.jobs")

_LOCK = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}

# H8 — il job store in-memory e le cartelle OUT_DIR/<job_id>/ crescono senza limite
# (memory + disk leak su un processo long-running). Prune LRU/TTL a ogni create():
#  - TTL: si evictano i job più vecchi di _JOB_TTL_S (già serviti da un pezzo);
#  - CAP: comunque non più di _JOB_MAX entry, tenendo le _JOB_MAX più recenti.
# I job recenti ancora in polling restano (TTL ampio + cap alto). Best-effort: gli
# errori di IO nel cleanup delle cartelle non devono mai far fallire una create().
_JOB_TTL_S = 6 * 3600      # 6h: oltre, un job è stato quasi certamente già scaricato
_JOB_MAX = 500             # tetto duro sul numero di entry tenute in RAM
_OUT_TTL_S = 6 * 3600      # cartelle OUT_DIR più vecchie: rimosse best-effort


def _prune_jobs_locked() -> list[str]:
    """Evict TTL + CAP. DEVE girare col _LOCK già preso. Ritorna i job_id evicti."""
    now = time.time()
    evicted: list[str] = []
    # 1. TTL — entry più vecchie della finestra.
    for jid, j in list(_JOBS.items()):
        if now - float(j.get("created_at", now)) > _JOB_TTL_S:
            _JOBS.pop(jid, None)
            evicted.append(jid)
    # 2. CAP — se ancora troppe, tieni le più recenti per created_at. Il prune gira PRIMA
    # dell'inserimento del nuovo job, quindi si lascia spazio a 1: si scende a _JOB_MAX-1
    # così dopo l'insert il totale è esattamente _JOB_MAX (niente off-by-one).
    keep = max(0, _JOB_MAX - 1)
    if len(_JOBS) > keep:
        ordered = sorted(_JOBS.items(), key=lambda kv: float(kv[1].get("created_at", 0)))
        for jid, _ in ordered[: len(_JOBS) - keep]:
            _JOBS.pop(jid, None)
            evicted.append(jid)
    return evicted


def _cleanup_out_dirs(evicted: list[str]) -> None:
    """Best-effort: rimuove le cartelle dei job evicti + qualsiasi cartella OUT_DIR
    più vecchia di _OUT_TTL_S (orfani da run precedenti). Mai solleva."""
    try:
        base = OUT_DIR
        if not base.exists():
            return
        # cartelle dei job appena evicti
        for jid in evicted:
            d = base / jid
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
        # sweep TTL su tutte le cartelle job (orfani non più in _JOBS)
        now = time.time()
        for d in base.iterdir():
            if not d.is_dir():
                continue
            try:
                if now - d.stat().st_mtime > _OUT_TTL_S:
                    shutil.rmtree(d, ignore_errors=True)
            except OSError:
                continue
    except Exception as exc:  # noqa: BLE001 — cleanup non deve mai rompere una create()
        log.warning("OUT_DIR cleanup best-effort fallito: %s", exc)


def create(service_id: str, blueprint_id: str, confidence: float) -> str:
    job_id = "job_" + uuid.uuid4().hex[:12]
    with _LOCK:
        evicted = _prune_jobs_locked()
        _JOBS[job_id] = {
            "job_id": job_id,
            "service_id": service_id,
            "blueprint_id": blueprint_id,
            "confidence": confidence,
            "status": "routed",
            "created_at": time.time(),
            "outputs": None,
            "validation": None,
            "citazioni": [],
            "refusal_reason": None,
            "error": None,
        }
    if evicted:
        _cleanup_out_dirs(evicted)
    return job_id


def update(job_id: str, **fields: Any) -> None:
    with _LOCK:
        if job_id in _JOBS:
            _JOBS[job_id].update(fields)


def get(job_id: str) -> Optional[dict]:
    with _LOCK:
        j = _JOBS.get(job_id)
        return dict(j) if j else None


def run_with_timeout(job_id: str, service_id: str, inputs: dict,
                     auth_level: str = "FULL", case_facts: dict | None = None) -> None:
    """C5 — watchdog sul tempo totale di generazione. `pipeline.run` non aveva alcun
    timeout complessivo: una filiera LLM appesa (upstream lento, context enorme) lasciava
    il job 'running' all'infinito. Qui si esegue run() in un thread e si aspetta al più
    JOB_TIMEOUT_S: oltre, il job va in 'error' con un messaggio pulito e azionabile invece
    di restare bloccato per sempre. Da usare come target del BackgroundTask al posto di run().

    NB: il thread di lavoro NON è killabile (limite Python): oltre il timeout continua in
    background finché non termina da solo, ma il job è già stato marcato 'error' e la risorsa
    di polling ha una risposta. È il comportamento voluto (fail-fast lato client)."""
    from . import pipeline  # lazy: pipeline importa jobs (evita import circolare)
    # NB: niente `with ThreadPoolExecutor(...)` — il suo __exit__ fa shutdown(wait=True) e
    # bloccherebbe sul thread appeso, annullando il timeout. Si chiude con wait=False.
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"8e-run-{job_id}")
    future = pool.submit(pipeline.run, job_id, service_id, inputs, auth_level, case_facts)
    try:
        future.result(timeout=JOB_TIMEOUT_S)
        pool.shutdown(wait=False)
    except FuturesTimeoutError:
        log.warning("job %s superato il timeout massimo (%ss) → error", job_id, JOB_TIMEOUT_S)
        update(job_id, status="error",
               error="La generazione ha superato il tempo massimo. Riprova; se persiste, "
                     "semplifica o accorcia la richiesta.",
               error_detail=f"job timeout dopo {JOB_TIMEOUT_S}s")
        # il worker appeso non è killabile: si abbandona il pool (wait=False) e il thread
        # terminerà da solo; il job è già 'error' e il client ha una risposta.
        pool.shutdown(wait=False)
    except Exception as exc:  # noqa: BLE001 — run() gestisce già i propri errori; backstop
        log.exception("run_with_timeout backstop per job %s", job_id)
        update(job_id, status="error",
               error="La generazione non è riuscita per un problema tecnico temporaneo.",
               error_detail=str(exc))
        pool.shutdown(wait=False)
