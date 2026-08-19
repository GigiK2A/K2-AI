"""I reparti non si svegliano tutti insieme.

Sintomo riportato dall'owner il 19 ago 2026: «le notifiche su Telegram arrivano tutte
insieme, come se gli agenti si svegliassero tutti insieme e basta». Era vero due volte:

- `due()` guardava solo "sono passati N secondi": al primo giro nessun dominio ha stato,
  quindi partivano TUTTI; `mark_ran` scriveva la stessa ora per tutti e 24 ore dopo erano
  di nuovo tutti dovuti nello stesso tick. Il branco non si sfasava mai da solo.
- le card partivano 8 per volta in un ciclo stretto, poi mezz'ora di silenzio.
"""
import autonomy_loop
from aios.heartbeat import HeartbeatScheduler

DOMINI = ["marketing", "vendite", "finance", "operations", "legal", "hr"]
INTERVALLI = {"marketing": 43200, "vendite": 43200, "finance": 86400,
              "operations": 86400, "legal": 86400, "hr": 86400}
T0 = 1755000000.0


def _sched():
    """Scheduler con la politica sfasata (in produzione la accende `from_env`)."""
    return HeartbeatScheduler(INTERVALLI, sfasa=True)


def test_di_default_resta_la_politica_storica():
    """Chi costruisce lo scheduler a mano non deve vedere cambiare il comportamento."""
    s = HeartbeatScheduler({"a": 100, "b": 100}, default_seconds=100)
    s.mark_ran("a", T0)
    s.mark_ran("b", T0)
    assert s.due(["a", "b"], T0 + 50) == []
    assert set(s.due(["a", "b"], T0 + 120)) == {"a", "b"}


def test_from_env_accende_lo_sfasamento(monkeypatch):
    monkeypatch.setenv("AIOS_HEARTBEATS", '{"finance": 86400}')
    monkeypatch.delenv("AIOS_SFASA_RISVEGLI", raising=False)
    assert HeartbeatScheduler.from_env()._sfasa is True
    monkeypatch.setenv("AIOS_SFASA_RISVEGLI", "0")
    assert HeartbeatScheduler.from_env()._sfasa is False


def test_sfasamento_stabile_fra_i_riavvii():
    """Deriva dal nome: nessuno stato in più, e non cambia al riavvio."""
    a, b = _sched(), _sched()
    for d in DOMINI:
        assert a.sfasamento(d) == b.sfasamento(d)
        assert 0 <= a.sfasamento(d) < a.interval_for(d)


def test_reparti_diversi_hanno_soglie_diverse():
    s = _sched()
    offset = {d: s.sfasamento(d) for d in DOMINI}
    assert len(set(offset.values())) >= 4, f"troppe collisioni: {offset}"


def test_mai_partiti_partono_subito():
    s = _sched()
    assert set(s.due(DOMINI, T0)) == set(DOMINI)


def test_dopo_un_avvio_sincronizzato_si_distribuiscono():
    """La prova del sintomo: partiti tutti insieme, non devono restare insieme."""
    s = _sched()
    for d in DOMINI:
        s._last[d] = T0
    risvegli: dict[float, list[str]] = {}
    for i in range(1, 3 * 48 + 1):            # 3 giorni di tick da 30 minuti
        t = T0 + i * 1800
        for d in s.due(DOMINI, t):
            risvegli.setdefault(t, []).append(d)
            s.mark_ran(d, t)
    assert risvegli, "nessun reparto si è mai svegliato"
    # dopo il primo giorno i risvegli devono essere sparsi: mai più di 2 reparti insieme
    dopo_24h = {t: v for t, v in risvegli.items() if t - T0 > 86400}
    assert dopo_24h, "nessun risveglio dopo le prime 24h"
    assert max(len(v) for v in dopo_24h.values()) <= 2, \
        f"si svegliano ancora in blocco: {[(round((t-T0)/3600,1), v) for t, v in dopo_24h.items()]}"
    assert len(dopo_24h) >= 4, "troppo pochi momenti distinti: non si sono distribuiti"


def test_il_periodo_a_regime_resta_quello_configurato():
    """Sfasare non deve accorciare il ritmo.

    Il PRIMO ciclo dopo l'adozione dello sfasamento può essere più corto (fra mezzo
    intervallo e uno intero: è il transitorio per agganciare la nuova fascia), poi il
    periodo si assesta sull'intervallo configurato."""
    s = _sched()
    s._last["finance"] = T0
    tempi = []
    for i in range(1, 6 * 48 + 1):
        t = T0 + i * 1800
        if "finance" in s.due(["finance"], t):
            tempi.append(t)
            s.mark_ran("finance", t)
    assert len(tempi) >= 3
    for prima, dopo in zip(tempi, tempi[1:]):
        assert 0.9 * 86400 <= (dopo - prima) <= 1.6 * 86400


def test_mai_un_risveglio_in_anticipo():
    """Sfasare non deve mai far girare un reparto prima del suo intervallo."""
    s = _sched()
    s._last["legal"] = T0
    ultimo = T0
    for i in range(1, 4 * 48 + 1):
        t = T0 + i * 1800
        if "legal" in s.due(["legal"], t):
            assert t - ultimo >= 86400 * 0.9
            ultimo = t
            s.mark_ran("legal", t)


def test_le_card_non_partono_a_raffica():
    assert autonomy_loop.MAX_CARD_PER_TICK <= 4, \
        "otto card in un ciclo stretto sono una raffica, non un collega che ti scrive"
