from core.actions import build_action, suggest_action_key
from core.i18n import t
from core.risk_engine import STATUS_AT_RISK, STATUS_INSUFFICIENT_DATA

_DATE_FORMATS = {"es": "%d/%m/%Y", "en": "%m/%d/%Y"}


def _fmt_date(date, lang):
    return date.strftime(_DATE_FORMATS.get(lang, _DATE_FORMATS["es"]))


def _fmt_num(x):
    return str(int(x)) if float(x).is_integer() else f"{x:.1f}"


def explain_client(row, lang="es"):
    """Build a plain-language explanation + suggested action for one client row
    (as produced by risk_engine.compute_risk). Every word traces back to a
    computed fact on the row — nothing here is invented."""
    status = row["status"]

    if status == STATUS_INSUFFICIENT_DATA:
        return {
            "explanation": t("explain_insufficient_data", lang, n_visits=row["n_visits"]),
            "action": None,
        }

    if status != STATUS_AT_RISK:
        return {
            "explanation": t(
                "explain_on_track",
                lang,
                cycle=_fmt_num(row["normal_cycle_days"]),
                days_since=row["days_since_last_visit"],
            ),
            "action": None,
        }

    explanation = t(
        "explain_at_risk",
        lang,
        cycle=_fmt_num(row["normal_cycle_days"]),
        days_since=row["days_since_last_visit"],
        last_visit=_fmt_date(row["last_visit_date"], lang),
        expected=_fmt_date(row["expected_next_visit_date"], lang),
        ratio=f"{row['risk_ratio']:.2f}",
    )
    action_key = suggest_action_key(row["risk_ratio"])
    return {"explanation": explanation, "action": build_action(action_key, lang)}
