import pandas as pd
import pytest

from core import risk_engine
from core.risk_engine import (
    STATUS_AT_RISK,
    STATUS_INSUFFICIENT_DATA,
    STATUS_ON_TRACK,
    compute_risk,
)


def _df(rows):
    df = pd.DataFrame(rows, columns=["client", "date", "amount"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_client_with_one_visit_is_insufficient_data():
    df = _df([("Ana", "2026-01-01", 10)])
    result = compute_risk(df, as_of_date=pd.Timestamp("2026-06-01"))
    row = result[result["client"] == "Ana"].iloc[0]
    assert row["status"] == STATUS_INSUFFICIENT_DATA
    assert row["normal_cycle_days"] is None


def test_client_with_two_visits_is_insufficient_data():
    df = _df([("Ana", "2026-01-01", 10), ("Ana", "2026-01-08", 10)])
    result = compute_risk(df, as_of_date=pd.Timestamp("2026-06-01"))
    row = result[result["client"] == "Ana"].iloc[0]
    assert row["status"] == STATUS_INSUFFICIENT_DATA


def test_client_with_three_visits_on_track():
    # Weekly cadence, last visit only 5 days ago -> well within threshold.
    df = _df(
        [
            ("Ana", "2026-01-01", 10),
            ("Ana", "2026-01-08", 10),
            ("Ana", "2026-01-15", 10),
        ]
    )
    result = compute_risk(df, as_of_date=pd.Timestamp("2026-01-20"))
    row = result[result["client"] == "Ana"].iloc[0]
    assert row["normal_cycle_days"] == 7
    assert row["status"] == STATUS_ON_TRACK


def test_client_overdue_beyond_threshold_is_at_risk():
    # Weekly cadence (7 days), 15 days since last visit -> ratio ~2.14x >= 1.5x
    df = _df(
        [
            ("Carlos", "2026-01-01", 10),
            ("Carlos", "2026-01-08", 10),
            ("Carlos", "2026-01-15", 10),
        ]
    )
    result = compute_risk(df, as_of_date=pd.Timestamp("2026-01-30"))
    row = result[result["client"] == "Carlos"].iloc[0]
    assert row["status"] == STATUS_AT_RISK
    assert row["risk_ratio"] >= risk_engine.RISK_THRESHOLD_MULTIPLIER


def test_threshold_is_configurable(monkeypatch):
    df = _df(
        [
            ("Carlos", "2026-01-01", 10),
            ("Carlos", "2026-01-08", 10),
            ("Carlos", "2026-01-15", 10),
        ]
    )
    # 12 days since last visit, cycle = 7 -> ratio ~1.71
    as_of = pd.Timestamp("2026-01-27")

    monkeypatch.setattr(risk_engine, "RISK_THRESHOLD_MULTIPLIER", 1.5)
    result = compute_risk(df, as_of_date=as_of)
    assert result.iloc[0]["status"] == STATUS_AT_RISK

    monkeypatch.setattr(risk_engine, "RISK_THRESHOLD_MULTIPLIER", 2.0)
    result = compute_risk(df, as_of_date=as_of)
    assert result.iloc[0]["status"] == STATUS_ON_TRACK


def test_duplicate_same_day_visits_treated_as_insufficient_data():
    df = _df(
        [
            ("Ana", "2026-01-01", 10),
            ("Ana", "2026-01-01", 10),
            ("Ana", "2026-01-01", 10),
        ]
    )
    result = compute_risk(df, as_of_date=pd.Timestamp("2026-02-01"))
    row = result[result["client"] == "Ana"].iloc[0]
    assert row["status"] == STATUS_INSUFFICIENT_DATA


def test_results_sorted_by_risk_ratio_descending():
    df = _df(
        [
            ("LowRisk", "2026-01-01", 10),
            ("LowRisk", "2026-01-08", 10),
            ("LowRisk", "2026-02-10", 10),
            ("HighRisk", "2026-01-01", 10),
            ("HighRisk", "2026-01-08", 10),
            ("HighRisk", "2026-01-15", 10),
        ]
    )
    result = compute_risk(df, as_of_date=pd.Timestamp("2026-02-11"))
    assert result.iloc[0]["client"] == "HighRisk"


def test_defaults_as_of_date_to_max_date_in_data():
    df = _df(
        [
            ("Ana", "2026-01-01", 10),
            ("Ana", "2026-01-08", 10),
            ("Ana", "2026-01-15", 10),
        ]
    )
    result = compute_risk(df)  # no as_of_date passed
    row = result[result["client"] == "Ana"].iloc[0]
    assert row["days_since_last_visit"] == 0
    assert row["status"] == STATUS_ON_TRACK
