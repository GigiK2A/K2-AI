from aios.sim.engine import SimLLM, run_simulation


def test_simllm_is_deterministic_and_returns_proposte():
    a = SimLLM(seed=1).complete_json(system="s", user="u")
    b = SimLLM(seed=1).complete_json(system="s", user="u")
    assert a == b
    assert isinstance(a["proposte"], list) and len(a["proposte"]) >= 1
    assert "contenuto" in a["proposte"][0]


def test_run_simulation_produces_timeline_and_growth():
    res = run_simulation(days=21, seed=3, approve_rate=0.8)
    tl = res["timeline"]
    assert len(tl) == 21
    assert all({"day", "followers", "reach"} <= set(row) for row in tl)
    assert tl[-1]["followers"] >= tl[0]["followers"]
    assert res["final_autonomy_level"] >= 1


def test_multiverse_runs_multiple_seeds():
    mv = run_simulation.multiverse(days=14, seeds=[1, 2, 3])
    assert len(mv) == 3
    assert all("timeline" in r for r in mv)
