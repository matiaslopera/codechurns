from core import actions
from core.actions import (
    ACTION_DISCOUNT,
    ACTION_OUTREACH,
    ACTION_REMINDER,
    build_action,
    build_action_text,
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


def test_build_action_text_discount_with_value_embeds_it():
    text = build_action_text(ACTION_DISCOUNT, "15%", lang="es")
    assert "15%" in text


def test_build_action_text_discount_without_value_falls_back_to_generic():
    generic = build_action(ACTION_DISCOUNT, lang="es")["description"]
    text = build_action_text(ACTION_DISCOUNT, "", lang="es")
    assert text == generic


def test_build_action_text_non_discount_ignores_value():
    text = build_action_text(ACTION_REMINDER, "15%", lang="es")
    assert "15%" not in text
    assert text == build_action(ACTION_REMINDER, lang="es")["description"]


def test_build_action_text_none_type_returns_empty_string():
    assert build_action_text(None, "15%", lang="es") == ""


def test_build_action_text_localized_english():
    text = build_action_text(ACTION_DISCOUNT, "$15", lang="en")
    assert "$15" in text
    assert "discount" in text.lower()
