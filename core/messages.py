from core.actions import ACTION_DISCOUNT
from core.i18n import t

# --- Tunable parameters -----------------------------------------------------
# n_visits at or above this counts as a "frequent" client -> suggest a more
# informal, familiar tone by default when the owner hasn't picked one.
FREQUENT_VISITS_THRESHOLD = 6
# -----------------------------------------------------------------------------

TONE_AUTO = "auto"
TONE_FORMAL = "formal"
TONE_INFORMAL = "informal"

# action_key (None means a plain check-in, no discount/offer) -> (formal, informal) template keys
_MESSAGE_TEMPLATE_KEYS = {
    None: ("message_greeting_formal", "message_greeting_informal"),
    "reminder": ("message_reminder_formal", "message_reminder_informal"),
    ACTION_DISCOUNT: ("message_discount_formal", "message_discount_informal"),
    "personal_outreach": ("message_outreach_formal", "message_outreach_informal"),
}

# Same tiers, but used once the owner has entered a concrete discount amount
# (mirrors core.actions.build_action_text's with-value/generic split).
_MESSAGE_TEMPLATE_KEYS_WITH_VALUE = {
    ACTION_DISCOUNT: ("message_discount_formal_with_value", "message_discount_informal_with_value"),
}


def _fmt_num(x):
    return str(int(x)) if float(x).is_integer() else f"{x:.1f}"


def suggest_tone(n_visits):
    """Frequent clients default to a more informal, familiar tone."""
    if n_visits is not None and n_visits >= FREQUENT_VISITS_THRESHOLD:
        return TONE_INFORMAL
    return TONE_FORMAL


def build_message(row, action_key, lang="es", tone=None, discount_value=None):
    """Ready-to-copy customer-facing message for one client.

    tone: TONE_FORMAL, TONE_INFORMAL, or TONE_AUTO/None to auto-suggest from
    the client's visit frequency. action_key is one of core.actions' ACTION_*
    constants, or None for a plain check-in greeting with no discount/offer
    mentioned. Every fact used (cycle, days since last visit) comes straight
    off the row. For ACTION_DISCOUNT, discount_value (e.g. "15%") is embedded
    verbatim when the owner has entered one; otherwise the offer is left as a
    placeholder for the owner to fill in, since the app has no basis to invent one.
    """
    if action_key not in _MESSAGE_TEMPLATE_KEYS:
        raise ValueError(f"Unknown action_key: {action_key!r}")

    if tone is None or tone == TONE_AUTO:
        tone = suggest_tone(row.get("n_visits"))

    discount_value = (discount_value or "").strip()
    if action_key in _MESSAGE_TEMPLATE_KEYS_WITH_VALUE and discount_value:
        formal_key, informal_key = _MESSAGE_TEMPLATE_KEYS_WITH_VALUE[action_key]
    else:
        formal_key, informal_key = _MESSAGE_TEMPLATE_KEYS[action_key]
    template_key = informal_key if tone == TONE_INFORMAL else formal_key

    cycle = row.get("normal_cycle_days")
    return t(
        template_key,
        lang,
        client=row["client"],
        cycle=_fmt_num(cycle) if cycle is not None else "",
        days_since=row.get("days_since_last_visit"),
        value=discount_value,
    )
