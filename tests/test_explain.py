import pandas as pd

from core.explain import explain_client
from core.risk_engine import STATUS_AT_RISK, STATUS_INSUFFICIENT_DATA, STATUS_ON_TRACK


def _row(**overrides):
    base = {
        "client": "Ana",
        "n_visits": 5,
        "last_visit_date": pd.Timestamp("2026-06-01"),
        "days_since_last_visit": 42,
        "normal_cycle_days": 14.0,
        "expected_next_visit_date": pd.Timestamp("2026-06-15"),
        "risk_ratio": 3.0,
        "status": STATUS_AT_RISK,
    }
    base.update(overrides)
    return base


def test_insufficient_data_has_no_action():
    row = _row(status=STATUS_INSUFFICIENT_DATA, n_visits=2, normal_cycle_days=None, risk_ratio=None)
    result = explain_client(row, lang="es")
    assert result["action"] is None
    assert "2" in result["explanation"]


def test_on_track_has_no_action():
    row = _row(status=STATUS_ON_TRACK, risk_ratio=0.5)
    result = explain_client(row, lang="es")
    assert result["action"] is None
    assert "14" in result["explanation"]


def test_at_risk_has_explanation_and_action():
    row = _row()
    result = explain_client(row, lang="es")
    assert result["action"] is not None
    assert "14" in result["explanation"]
    assert "42" in result["explanation"]
    assert "3.00" in result["explanation"]


def test_explanation_facts_are_traceable_to_row_not_invented():
    row = _row(normal_cycle_days=21.0, days_since_last_visit=99, risk_ratio=4.71)
    result = explain_client(row, lang="es")
    assert "21" in result["explanation"]
    assert "99" in result["explanation"]
    assert "4.71" in result["explanation"]


def test_explanation_localized_to_english():
    row = _row()
    result_es = explain_client(row, lang="es")
    result_en = explain_client(row, lang="en")
    assert result_es["explanation"] != result_en["explanation"]
    assert result_es["action"]["label"] != result_en["action"]["label"]


def test_date_format_differs_by_language():
    row = _row(last_visit_date=pd.Timestamp("2026-03-05"))
    result_es = explain_client(row, lang="es")
    result_en = explain_client(row, lang="en")
    assert "05/03/2026" in result_es["explanation"]
    assert "03/05/2026" in result_en["explanation"]
