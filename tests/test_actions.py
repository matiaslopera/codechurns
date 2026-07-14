from core import actions
from core.actions import (
    ACTION_DISCOUNT,
    ACTION_OUTREACH,
    ACTION_REMINDER,
    build_action,
    suggest_action_key,
)
from core.risk_engine import RISK_THRESHOLD_MULTIPLIER


def test_no_action_when_ratio_is_none():
    assert suggest_action_key(None) is None


def test_no_action_when_on_track():
    assert suggest_action_key(RISK_THRESHOLD_MULTIPLIER - 0.01) is None


def test_reminder_tier_just_above_threshold():
    assert suggest_action_key(RISK_THRESHOLD_MULTIPLIER) == ACTION_REMINDER


def test_discount_tier():
    ratio = RISK_THRESHOLD_MULTIPLIER * actions.TIER_REMINDER_MAX_MULTIPLIER
    assert suggest_action_key(ratio) == ACTION_DISCOUNT


def test_outreach_tier_for_severe_delay():
    ratio = RISK_THRESHOLD_MULTIPLIER * actions.TIER_DISCOUNT_MAX_MULTIPLIER
    assert suggest_action_key(ratio) == ACTION_OUTREACH


def test_tiers_configurable(monkeypatch):
    monkeypatch.setattr(actions, "TIER_REMINDER_MAX_MULTIPLIER", 1.1)
    ratio = RISK_THRESHOLD_MULTIPLIER * 1.2
    assert suggest_action_key(ratio) == ACTION_DISCOUNT


def test_build_action_returns_localized_text():
    action_es = build_action(ACTION_REMINDER, lang="es")
    action_en = build_action(ACTION_REMINDER, lang="en")
    assert action_es["key"] == ACTION_REMINDER
    assert action_es["label"] != action_en["label"]
    assert action_es["description"] != action_en["description"]


def test_build_action_none_key_returns_none():
    assert build_action(None) is None
