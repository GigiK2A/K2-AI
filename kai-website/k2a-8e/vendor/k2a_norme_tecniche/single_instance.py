"""
Single-instance lock per il server MCP k2a-mcp-norme-tecniche.

Previene la zombie stdio contention (DN-25): se Claude Desktop rilancia il server
senza aver terminato il vecchio processo, si ottengono 2 istanze che condividono
lo stesso canale stdio. Le richieste MCP vengono consumate da uno dei due processi
in modo non deterministico → timeout sporadici dal lato client.

Il lock file contiene il PID del processo server corrente. Al successivo avvio:
  1. Se il lock esiste e il PID è ancora vivo → exit con errore (siamo la 2a istanza)
  2. Se il lock esiste ma il PID è morto → sovrascriviamo (processo precedente crashato)
  3. Se il lock non esiste → creiamo il lock e registriamo cleanup all'exit

Il lock file viene rimosso via atexit quando il processo termina normalmente.
In caso di crash senza atexit (SIGKILL), rimane un lock stale — ma la verifica
os.kill(pid, 0) lo rileva e lo sovrascrive al successivo avvio.

Fix M-infra-1 — validato con stress test 60 min (29/05/2026).
"""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path

LOCK_FILE = Path("/tmp/k2a-mcp-norme-tecniche.lock")


def acquire_single_instance_lock() -> None:
    """Tenta di acquisire il lock per questa istanza.

    Se un'altra istanza è già in esecuzione, stampa un messaggio su stderr
    e termina con exit code 1. Se il lock è stale (PID morto), lo sovrascrive.

    Da chiamare all'avvio del server, prima di mcp.run().
    """
    if LOCK_FILE.exists():
        try:
            old_pid = int(LOCK_FILE.read_text().strip())
            # os.kill(pid, 0) non invia nessun segnale, ma verifica se il processo esiste.
            # Solleva OSError(ESRCH) se il PID non esiste; OSError(EPERM) se esiste
            # ma non abbiamo permessi (il processo è di un altro utente — improbabile
            # ma gestiamo: in quel caso consideriamo il lock valido per sicurezza).
            try:
                os.kill(old_pid, 0)
                # PID vivo → siamo la 2a istanza, exit
                print(
                    f"[k2a-mcp-norme-tecniche] ERRORE: server già in esecuzione "
                    f"(PID {old_pid}). "
                    f"Terminare il processo prima di rilanciare:\n"
                    f"  kill {old_pid}\n"
                    f"oppure riavviare Claude Desktop completamente.",
                    file=sys.stderr,
                )
                sys.exit(1)
            except OSError as e:
                import errno
                if e.errno == errno.EPERM:
                    # Processo di altro utente — lock valido, exit per sicurezza
                    print(
                        f"[k2a-mcp-norme-tecniche] ERRORE: lock file presente con PID "
                        f"{old_pid} (processo di altro utente). "
                        f"Rimuovere manualmente: rm {LOCK_FILE}",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                # ESRCH o altri errori: PID non esiste → lock stale, sovrascrivi
                pass
        except (ValueError, OSError):
            # Lock file corrotto (contenuto non numerico o errore lettura) → sovrascrivi
            pass

    # Scrivi il nostro PID nel lock file
    LOCK_FILE.write_text(str(os.getpid()))

    # Registra la rimozione del lock all'exit (normale o via signal gestiti)
    atexit.register(_release_lock)


def _release_lock() -> None:
    """Rimuove il lock file all'exit, solo se contiene il nostro PID."""
    try:
        if LOCK_FILE.exists():
            content = LOCK_FILE.read_text().strip()
            if content == str(os.getpid()):
                LOCK_FILE.unlink()
    except OSError:
        pass  # Non critico se la rimozione fallisce


def lock_status() -> dict:
    """Diagnostica: stato corrente del lock file (per health check).

    Returns:
        dict con: lock_exists, lock_pid, pid_alive, our_pid
    """
    our_pid = os.getpid()
    if not LOCK_FILE.exists():
        return {"lock_exists": False, "lock_pid": None, "pid_alive": None, "our_pid": our_pid}

    try:
        lock_pid = int(LOCK_FILE.read_text().strip())
        try:
            os.kill(lock_pid, 0)
            pid_alive = True
        except OSError:
            pid_alive = False
        return {"lock_exists": True, "lock_pid": lock_pid, "pid_alive": pid_alive, "our_pid": our_pid}
    except (ValueError, OSError):
        return {"lock_exists": True, "lock_pid": None, "pid_alive": None, "our_pid": our_pid}
