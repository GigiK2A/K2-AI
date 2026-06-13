from aios.sim.world import SimWorld, content_quality


def test_quality_rewards_numbers_voice_penalizes_buzzwords():
    hi = content_quality({"contenuto": "Recuperi 5 ore a settimana con l'agente AI", "tipo": "caption"})
    lo = content_quality({"contenuto": "La rivoluzionaria trasformazione digitale all'avanguardia", "tipo": "caption"})
    assert hi > lo
    assert 0.0 <= hi <= 1.0 and 0.0 <= lo <= 1.0


def test_publish_increases_engagement_and_followers_deterministically():
    w1 = SimWorld(seed=42, followers=100)
    w2 = SimWorld(seed=42, followers=100)
    good = {"contenuto": "Caso reale: 70% email gestite, 5 ore/sett recuperate", "tipo": "caption"}
    w1.publish(good); w2.publish(good)
    w1.advance_day(); w2.advance_day()
    assert w1.snapshot() == w2.snapshot()
    assert w1.followers >= 100
    assert w1.snapshot()["reach"] > 0


def test_better_content_outperforms_worse_over_a_day():
    good = SimWorld(seed=7, followers=200)
    bad = SimWorld(seed=7, followers=200)
    good.publish({"contenuto": "3 numeri concreti: 70%, 5 ore, 30 giorni", "tipo": "caption"})
    bad.publish({"contenuto": "innovativo e rivoluzionario", "tipo": "caption"})
    good.advance_day(); bad.advance_day()
    assert good.snapshot()["reach"] >= bad.snapshot()["reach"]
