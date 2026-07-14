import io

import pandas as pd
import pytest

from core.ingest import IngestError, detect_columns, load_file, normalize


def test_detect_columns_by_keyword():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Ana", "Beto"],
            "Fecha": ["2026-01-01", "2026-01-08", "2026-01-02"],
            "Monto": [10, 12, 15],
        }
    )
    columns = detect_columns(df)
    assert columns == {"client": "Cliente", "date": "Fecha", "amount": "Monto"}


def test_detect_columns_by_inference_with_unlabeled_headers():
    df = pd.DataFrame(
        {
            "col_a": ["Ana", "Ana", "Beto", "Beto"],
            "col_b": ["2026-01-01", "2026-01-08", "2026-01-02", "2026-01-15"],
            "col_c": [10.5, 12.0, 15.5, 9.0],
        }
    )
    columns = detect_columns(df)
    assert columns["date"] == "col_b"
    assert columns["amount"] == "col_c"
    assert columns["client"] == "col_a"


def test_detect_columns_missing_amount_is_none():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Ana", "Beto"],
            "Fecha": ["2026-01-01", "2026-01-08", "2026-01-02"],
        }
    )
    columns = detect_columns(df)
    assert columns["amount"] is None


def test_normalize_success():
    df = pd.DataFrame(
        {
            "Cliente": [" Ana ", "Beto"],
            "Fecha": ["2026-01-08", "2026-01-02"],
            "Monto": [12, 15],
        }
    )
    columns = {"client": "Cliente", "date": "Fecha", "amount": "Monto"}
    out = normalize(df, columns)
    assert list(out["client"]) == ["Ana", "Beto"]
    assert pd.api.types.is_datetime64_any_dtype(out["date"])


def test_normalize_raises_without_client_column():
    df = pd.DataFrame({"Fecha": ["2026-01-08"]})
    with pytest.raises(IngestError) as exc_info:
        normalize(df, {"client": None, "date": "Fecha", "amount": None})
    assert exc_info.value.key == "error_no_client_col"


def test_normalize_raises_without_date_column():
    df = pd.DataFrame({"Cliente": ["Ana"]})
    with pytest.raises(IngestError) as exc_info:
        normalize(df, {"client": "Cliente", "date": None, "amount": None})
    assert exc_info.value.key == "error_no_date_col"


def test_normalize_drops_unparseable_dates():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Beto"],
            "Fecha": ["2026-01-08", "not-a-date"],
        }
    )
    columns = {"client": "Cliente", "date": "Fecha", "amount": None}
    out = normalize(df, columns)
    assert len(out) == 1
    assert out.iloc[0]["client"] == "Ana"


def test_normalize_raises_when_no_valid_dates_remain():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Beto"],
            "Fecha": ["not-a-date", "tampoco"],
        }
    )
    columns = {"client": "Cliente", "date": "Fecha", "amount": None}
    with pytest.raises(IngestError) as exc_info:
        normalize(df, columns)
    assert exc_info.value.key == "error_no_valid_dates"


def test_normalize_dedupes_exact_duplicate_rows():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Ana", "Ana"],
            "Fecha": ["2026-01-08", "2026-01-08", "2026-01-15"],
            "Monto": [12, 12, 12],
        }
    )
    columns = {"client": "Cliente", "date": "Fecha", "amount": "Monto"}
    out = normalize(df, columns)
    assert len(out) == 2  # the exact-duplicate first row collapses into one visit


def test_normalize_keeps_same_day_visits_with_different_amounts():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Ana"],
            "Fecha": ["2026-01-08", "2026-01-08"],
            "Monto": [12, 30],
        }
    )
    columns = {"client": "Cliente", "date": "Fecha", "amount": "Monto"}
    out = normalize(df, columns)
    assert len(out) == 2  # two distinct services the same day are still two visits


def test_normalize_cleans_currency_symbols_from_amount():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Beto"],
            "Fecha": ["2026-01-08", "2026-01-09"],
            "Monto": ["$1,200.50", "S/ 45.00"],
        }
    )
    columns = {"client": "Cliente", "date": "Fecha", "amount": "Monto"}
    out = normalize(df, columns)
    assert list(out["amount"]) == [1200.50, 45.00]


def test_detect_columns_prefers_visit_date_over_generic_date_column():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Beto"],
            "Otra fecha": ["2026-01-01", "2026-01-02"],
            "Fecha de cita": ["2026-02-01", "2026-02-02"],
        }
    )
    columns = detect_columns(df)
    assert columns["date"] == "Fecha de cita"


def test_detect_columns_excludes_birthdate_from_keyword_match():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Beto"],
            "Fecha de nacimiento": ["1990-01-01", "1985-05-02"],
            "Fecha de visita": ["2026-02-01", "2026-02-02"],
        }
    )
    columns = detect_columns(df)
    assert columns["date"] == "Fecha de visita"


def test_detect_columns_excludes_birthdate_even_by_inference():
    df = pd.DataFrame(
        {
            "Cliente": ["Ana", "Ana", "Beto", "Beto"],
            "Fecha de nacimiento": ["1990-01-01", "1990-01-01", "1985-05-02", "1985-05-02"],
            "col_unlabeled": ["2026-01-01", "2026-01-08", "2026-01-02", "2026-01-15"],
        }
    )
    columns = detect_columns(df)
    assert columns["date"] == "col_unlabeled"


def test_load_file_csv():
    csv_bytes = io.BytesIO(b"Cliente,Fecha\nAna,2026-01-01\n")
    csv_bytes.name = "clientes.csv"
    df = load_file(csv_bytes)
    assert list(df.columns) == ["Cliente", "Fecha"]


def test_load_file_empty_raises():
    csv_bytes = io.BytesIO(b"Cliente,Fecha\n")
    csv_bytes.name = "vacio.csv"
    with pytest.raises(IngestError) as exc_info:
        load_file(csv_bytes)
    assert exc_info.value.key == "error_empty_file"
