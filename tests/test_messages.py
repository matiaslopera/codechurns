import pytest

from core.actions import ACTION_DISCOUNT, ACTION_OUTREACH, ACTION_REMINDER
from core.messages import (
    FREQUENT_VISITS_THRESHOLD,
    TONE_FORMAL,
    TONE_INFORMAL,
    build_message,
    suggest_tone,
)


def _row(**overrides):
    base = {
        "client": "Ana",
        "n_visits": 5,
        "days_since_last_visit": 42,
        "normal_cycle_days": 14.0,
    }
    base.update(overrides)
    return base


def test_suggest_tone_formal_for_infrequent_client():
    assert suggest_tone(FREQUENT_VISITS_THRESHOLD - 1) == TONE_FORMAL


def test_suggest_tone_informal_for_frequent_client():
    assert suggest_tone(FREQUENT_VISITS_THRESHOLD) == TONE_INFORMAL


def test_suggest_tone_formal_when_unknown():
    assert suggest_tone(None) == TONE_FORMAL


def test_greeting_message_has_no_discount_language():
    row = _row()
    message = build_message(row, None, lang="es")
    assert "Ana" in message
    assert "descuento" not in message.lower()


def test_reminder_message_uses_row_facts():
    row = _row()
    message = build_message(row, ACTION_REMINDER, lang="es", tone=TONE_FORMAL)
    assert "Ana" in message
    assert "14" in message
    assert "42" in message


def test_discount_and_outreach_messages_leave_placeholder():
    row = _row()
    discount = build_message(row, ACTION_DISCOUNT, lang="es", tone=TONE_FORMAL)
    outreach = build_message(row, ACTION_OUTREACH, lang="es", tone=TONE_FORMAL)
    assert "[" in discount and "]" in discount
    assert "[" in outreach and "]" in outreach


def test_tone_changes_wording():
    row = _row()
    formal = build_message(row, ACTION_REMINDER, lang="es", tone=TONE_FORMAL)
    informal = build_message(row, ACTION_REMINDER, lang="es", tone=TONE_INFORMAL)
    assert formal != informal


def test_auto_tone_matches_suggested_tone_from_row():
    frequent_row = _row(n_visits=FREQUENT_VISITS_THRESHOLD)
    infrequent_row = _row(n_visits=1)
    frequent_message = build_message(frequent_row, ACTION_REMINDER, lang="es")
    explicit_informal = build_message(frequent_row, ACTION_REMINDER, lang="es", tone=TONE_INFORMAL)
    explicit_formal = build_message(infrequent_row, ACTION_REMINDER, lang="es", tone=TONE_FORMAL)
    assert frequent_message == explicit_informal
    assert build_message(infrequent_row, ACTION_REMINDER, lang="es") == explicit_formal


def test_localized_to_english():
    row = _row()
    message_es = build_message(row, ACTION_REMINDER, lang="es", tone=TONE_FORMAL)
    message_en = build_message(row, ACTION_REMINDER, lang="en", tone=TONE_FORMAL)
    assert message_es != message_en
    assert "Ana" in message_en


def test_unknown_action_key_raises():
    with pytest.raises(ValueError):
        build_message(_row(), "not_a_real_action", lang="es")


def test_discount_message_with_value_embeds_it_and_drops_placeholder():
    row = _row()
    message = build_message(row, ACTION_DISCOUNT, lang="es", tone=TONE_FORMAL, discount_value="15%")
    assert "15%" in message
    assert "[" not in message and "]" not in message


def test_discount_message_without_value_keeps_placeholder():
    row = _row()
    message = build_message(row, ACTION_DISCOUNT, lang="es", tone=TONE_FORMAL, discount_value="")
    assert "[" in message and "]" in message


def test_discount_value_ignored_for_non_discount_actions():
    row = _row()
    with_value = build_message(row, ACTION_REMINDER, lang="es", tone=TONE_FORMAL, discount_value="15%")
    without_value = build_message(row, ACTION_REMINDER, lang="es", tone=TONE_FORMAL)
    assert with_value == without_value
    assert "15%" not in with_value


def test_discount_message_with_value_localized_to_english():
    row = _row()
    message = build_message(row, ACTION_DISCOUNT, lang="en", tone=TONE_FORMAL, discount_value="$15")
    assert "$15" in message
    assert "discount" in message.lower()
