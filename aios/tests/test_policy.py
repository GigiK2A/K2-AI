from aios.autonomy import ActionType, AutonomyLevel
from aios.policy import PolicyEngine, Decision

AT = ActionType("marketing", "social.publish_post")


def test_unknown_action_defaults_to_l0():
    pe = PolicyEngine()
    assert pe.level_for(AT) == AutonomyLevel.L0_OBSERVE


def test_decision_l0_is_deny():
    pe = PolicyEngine()
    assert pe.decide(AT) == Decision.DENY


def test_decision_l1_is_propose():
    pe = PolicyEngine()
    pe.set_level(AT, AutonomyLevel.L1_PROPOSE)
    assert pe.decide(AT) == Decision.PROPOSE


def test_decision_l2_and_l3_are_execute():
    pe = PolicyEngine()
    pe.set_level(AT, AutonomyLevel.L2_ROUTINE)
    assert pe.decide(AT) == Decision.EXECUTE
    pe.set_level(AT, AutonomyLevel.L3_AUTO)
    assert pe.decide(AT) == Decision.EXECUTE
