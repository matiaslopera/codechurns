from core.i18n import t
from core.risk_engine import RISK_THRESHOLD_MULTIPLIER

# --- Tunable parameters -----------------------------------------------------
# Action tiers scale off risk_engine.RISK_THRESHOLD_MULTIPLIER (the ratio at
# which a client first counts as "at risk"). Raise/lower these multipliers to
# change how quickly suggestions escalate from a light nudge to a stronger,
# higher-touch offer.
TIER_REMINDER_MAX_MULTIPLIER = 1.5   # ratio < threshold * this -> just a reminder
TIER_DISCOUNT_MAX_MULTIPLIER = 2.5   # ratio < threshold * this -> reminder + small incentive
# ratio >= threshold * TIER_DISCOUNT_MAX_MULTIPLIER -> personal outreach + stronger offer
# -----------------------------------------------------------------------------

ACTION_REMINDER = "reminder"
ACTION_DISCOUNT = "personal_reminder_discount"
ACTION_OUTREACH = "personal_outreach"

_ACTION_I18N_KEYS = {
    ACTION_REMINDER: ("action_reminder_label", "action_reminder_description"),
    ACTION_DISCOUNT: ("action_discount_label", "action_discount_description"),
    ACTION_OUTREACH: ("action_outreach_label", "action_outreach_description"),
}


def suggest_action_key(risk_ratio):
    """Pick a suggested action key from how overdue the client is.

    Returns None when there's no reliable ratio to act on (e.g. insufficient
    data or on-track clients) — no action should be suggested in that case.
    """
    if risk_ratio is None or risk_ratio < RISK_THRESHOLD_MULTIPLIER:
        return None
    if risk_ratio < RISK_THRESHOLD_MULTIPLIER * TIER_REMINDER_MAX_MULTIPLIER:
        return ACTION_REMINDER
    if risk_ratio < RISK_THRESHOLD_MULTIPLIER * TIER_DISCOUNT_MAX_MULTIPLIER:
        return ACTION_DISCOUNT
    return ACTION_OUTREACH


def build_action(action_key, lang="es"):
    """Return the suggestion the owner sees: a label + description to review,
    edit, or discard. This never triggers any outreach by itself."""
    if action_key is None:
        return None
    label_key, description_key = _ACTION_I18N_KEYS[action_key]
    return {
        "key": action_key,
        "label": t(label_key, lang),
        "description": t(description_key, lang),
    }
