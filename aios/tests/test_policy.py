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


def test_clean_approvals_promote_l1_to_l2():
    pe = PolicyEngine(promotion_threshold=3)
    pe.set_level(AT, AutonomyLevel.L1_PROPOSE)
    for _ in range(3):
        pe.record_outcome(AT, clean=True)
    assert pe.level_for(AT) == AutonomyLevel.L2_ROUTINE


def test_correction_resets_streak():
    pe = PolicyEngine(promotion_threshold=3)
    pe.set_level(AT, AutonomyLevel.L1_PROPOSE)
    pe.record_outcome(AT, clean=True)
    pe.record_outcome(AT, clean=False)
    pe.record_outcome(AT, clean=True)
    assert pe.level_for(AT) == AutonomyLevel.L1_PROPOSE


def test_cap_blocks_auto_promotion():
    pe = PolicyEngine(promotion_threshold=2)
    pe.set_level(AT, AutonomyLevel.L1_PROPOSE)
    pe.set_cap(AT, AutonomyLevel.L1_PROPOSE)  # money/contracts style cap
    for _ in range(5):
        pe.record_outcome(AT, clean=True)
    assert pe.level_for(AT) == AutonomyLevel.L1_PROPOSE


def test_no_auto_promotion_beyond_l2():
    pe = PolicyEngine(promotion_threshold=2)
    pe.set_level(AT, AutonomyLevel.L2_ROUTINE)
    for _ in range(10):
        pe.record_outcome(AT, clean=True)
    assert pe.level_for(AT) == AutonomyLevel.L2_ROUTINE  # L2->L3 is manual only
