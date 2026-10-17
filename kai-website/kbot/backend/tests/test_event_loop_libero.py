"""Un modello lento o appeso non deve fermare il backend degli altri utenti.

Prima (15-17 ott 2026) lo stream usava il client Anthropic SINCRONO dentro una funzione async: con un
LLM finto che non risponde, backend e /health restavano fermi 357 s. Qui un finto «stream» che blocca
il thread per un secondo: nel frattempo il loop deve continuare a girare."""
import asyncio
import time

from app.api import message


class _Stream:
    def __init__(self, ritardo):
        self.ritardo = ritardo
        self.text_stream = self._gen()

    def _gen(self):
        time.sleep(self.ritardo)            # attesa BLOCCANTE, come l'SDK sincrono sul primo token
        yield "ciao "
        yield "mondo"

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return "FINALE"


class _Client:
    def __init__(self, ritardo, errore=None):
        self.ritardo, self.errore = ritardo, errore
        self.messages = self

    def stream(self, **kw):
        if self.errore:
            raise self.errore
        return _Stream(self.ritardo)


def _misura_loop(coro_factory):
    async def main():
        battiti = []

        async def cuore():
            while True:
                battiti.append(time.monotonic())
                await asyncio.sleep(0.05)

        t = asyncio.create_task(cuore())
        risultato = await coro_factory()
        t.cancel()
        buchi = [b - a for a, b in zip(battiti, battiti[1:])]
        return risultato, max(buchi) if buchi else 99.0

    return asyncio.run(main())


def test_stream_non_ferma_il_loop():
    async def consuma():
        out = []
        async for kind, payload in message._stream_off_loop(_Client(1.0), {}):
            out.append((kind, payload))
        return out

    out, buco_max = _misura_loop(consuma)
    assert out == [("chunk", "ciao "), ("chunk", "mondo"), ("final", "FINALE")]
    assert buco_max < 0.3, f"il loop si è fermato {buco_max:.2f}s durante l'attesa del modello"


def test_errori_dell_sdk_arrivano_al_chiamante():
    class Boom(Exception):
        pass

    async def consuma():
        try:
            async for _ in message._stream_off_loop(_Client(0, errore=Boom("x")), {}):
                pass
        except Boom:
            return "rilanciata"

    out, _ = _misura_loop(consuma)
    assert out == "rilanciata"


def test_off_loop_non_ferma_il_loop_e_copia_il_contesto():
    import contextvars
    v = contextvars.ContextVar("v", default="no")

    def lento():
        time.sleep(0.6)
        return v.get()

    async def corpo():
        v.set("si")
        return await message._off_loop(lento)

    out, buco_max = _misura_loop(corpo)
    assert out == "si"                      # il ContextVar (pacchetto normativo) è visibile nel thread
    assert buco_max < 0.3
