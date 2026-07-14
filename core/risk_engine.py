import pandas as pd

# --- Tunable parameters -----------------------------------------------------
# How many times over a client's normal cycle counts as "at risk".
# e.g. 1.5 means: if a client normally comes every 20 days and 30+ days have
# passed (20 * 1.5), they're flagged. Raise/lower this after testing with
# real business data.
RISK_THRESHOLD_MULTIPLIER = 1.5

# Minimum number of visits needed to trust a computed cadence (need at least
# 2 intervals between visits, i.e. 3 visits, before treating the average gap
# as "normal" for that client).
MIN_VISITS_FOR_RELIABLE_CADENCE = 3
# -----------------------------------------------------------------------------

STATUS_AT_RISK = "at_risk"
STATUS_ON_TRACK = "on_track"
STATUS_INSUFFICIENT_DATA = "insufficient_data"


def _client_stats(client_df, as_of_date):
    client_df = client_df.sort_values("date")
    n_visits = len(client_df)
    last_visit_date = client_df["date"].iloc[-1]
    days_since_last_visit = (as_of_date - last_visit_date).days

    if n_visits < MIN_VISITS_FOR_RELIABLE_CADENCE:
        return {
            "n_visits": n_visits,
            "last_visit_date": last_visit_date,
            "days_since_last_visit": days_since_last_visit,
            "normal_cycle_days": None,
            "expected_next_visit_date": None,
            "risk_ratio": None,
            "status": STATUS_INSUFFICIENT_DATA,
        }

    intervals = client_df["date"].diff().dropna().dt.days
    normal_cycle_days = intervals.median()

    if not normal_cycle_days or normal_cycle_days <= 0:
        # Degenerate data (e.g. duplicate same-day entries) -> can't trust a cycle.
        return {
            "n_visits": n_visits,
            "last_visit_date": last_visit_date,
            "days_since_last_visit": days_since_last_visit,
            "normal_cycle_days": None,
            "expected_next_visit_date": None,
            "risk_ratio": None,
            "status": STATUS_INSUFFICIENT_DATA,
        }

    risk_ratio = days_since_last_visit / normal_cycle_days
    status = STATUS_AT_RISK if risk_ratio >= RISK_THRESHOLD_MULTIPLIER else STATUS_ON_TRACK

    return {
        "n_visits": n_visits,
        "last_visit_date": last_visit_date,
        "days_since_last_visit": days_since_last_visit,
        "normal_cycle_days": round(normal_cycle_days, 1),
        "expected_next_visit_date": last_visit_date + pd.Timedelta(days=normal_cycle_days),
        "risk_ratio": round(risk_ratio, 2),
        "status": status,
    }


def compute_risk(df, as_of_date=None):
    """df must be normalized (columns: client, date, amount). Returns one row per client."""
    if as_of_date is None:
        as_of_date = df["date"].max()

    rows = []
    for client, client_df in df.groupby("client"):
        stats = _client_stats(client_df, as_of_date)
        rows.append({"client": client, **stats})

    result = pd.DataFrame(rows)
    if result.empty:
        return result

    result = result.sort_values(
        by="risk_ratio", ascending=False, na_position="last", kind="stable"
    ).reset_index(drop=True)
    return result
