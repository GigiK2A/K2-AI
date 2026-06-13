from aios.autonomy import AutonomyLevel, ActionType, DEFAULT_PROMOTION_THRESHOLD


def test_levels_are_ordered():
    assert AutonomyLevel.L0_OBSERVE < AutonomyLevel.L1_PROPOSE
    assert AutonomyLevel.L1_PROPOSE < AutonomyLevel.L2_ROUTINE
    assert AutonomyLevel.L2_ROUTINE < AutonomyLevel.L3_AUTO


def test_action_type_key():
    at = ActionType(domain="marketing", capability="social.publish_post")
    assert at.key == "marketing.social.publish_post"


def test_default_threshold():
    assert DEFAULT_PROMOTION_THRESHOLD == 10
