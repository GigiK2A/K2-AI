from aios.killswitch import KillSwitch


def test_starts_disengaged():
    ks = KillSwitch()
    assert ks.engaged is False


def test_engage_and_release():
    ks = KillSwitch()
    ks.engage(reason="manual stop")
    assert ks.engaged is True
    assert ks.reason == "manual stop"
    ks.release()
    assert ks.engaged is False
    assert ks.reason is None
