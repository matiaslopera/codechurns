import warnings

import pandas as pd

CLIENT_KEYWORDS = ["cliente", "client", "customer", "nombre", "name", "paciente", "socio", "member"]
AMOUNT_KEYWORDS = ["monto", "precio", "price", "amount", "total", "valor", "venta", "importe", "cost", "costo"]

# Date columns are matched in tiers: specific visit/appointment keywords win over
# generic "fecha"/"date" ones, so a file with both a birthdate and a visit date
# column doesn't pick the wrong one. Columns matching DATE_EXCLUDE_KEYWORDS are
# never auto-selected as the visit date, even as a last resort.
DATE_KEYWORD_TIERS = [
    ["visita", "cita", "appointment", "compra", "purchase"],
    ["fecha", "date", "dia", "día", "day"],
]
DATE_EXCLUDE_KEYWORDS = ["nacimiento", "birth"]

MIN_DATE_PARSE_RATE = 0.8
MIN_NUMERIC_PARSE_RATE = 0.8

# Currency symbols/separators to strip before parsing an amount column, so
# values like "$1,200.50" or "S/ 45.00" are read as numbers instead of failing
# detection entirely.
_CURRENCY_NOISE_PATTERN = r"[^\d,.\-]"


class IngestError(Exception):
    """Raised for user-facing ingestion failures. `key` maps to an i18n string."""

    def __init__(self, key, **kwargs):
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)


def load_file(uploaded_file):
    name = getattr(uploaded_file, "name", str(uploaded_file))
    try:
        if name.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
    except Exception as e:
        raise IngestError("error_file_read") from e

    if df.empty:
        raise IngestError("error_empty_file")
    return df


def _match_by_keyword(columns, keywords):
    for col in columns:
        col_norm = str(col).strip().lower()
        if any(kw in col_norm for kw in keywords):
            return col
    return None


def _match_date_column(columns):
    for keywords in DATE_KEYWORD_TIERS:
        for col in columns:
            col_norm = str(col).strip().lower()
            if any(ex in col_norm for ex in DATE_EXCLUDE_KEYWORDS):
                continue
            if any(kw in col_norm for kw in keywords):
                return col
    return None


def _clean_numeric_series(series):
    # Assumes "," is a thousands separator and "." is the decimal point
    # (e.g. "$1,200.50" -> 1200.50), the most common format in POS/CRM exports.
    cleaned = series.astype(str).str.replace(_CURRENCY_NOISE_PATTERN, "", regex=True)
    cleaned = cleaned.str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def _looks_like_date(series, sample_size=20):
    sample = series.dropna().head(sample_size)
    if sample.empty:
        return False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(sample, errors="coerce")
    return parsed.notna().mean() >= MIN_DATE_PARSE_RATE


def _looks_numeric(series):
    sample = series.dropna()
    if sample.empty:
        return False
    coerced = _clean_numeric_series(sample)
    return coerced.notna().mean() >= MIN_NUMERIC_PARSE_RATE


def detect_columns(df):
    columns = list(df.columns)

    client_col = _match_by_keyword(columns, CLIENT_KEYWORDS)
    date_col = _match_date_column(columns)
    amount_col = _match_by_keyword(columns, AMOUNT_KEYWORDS)

    if date_col is None:
        for col in columns:
            if col in (client_col, amount_col):
                continue
            col_norm = str(col).strip().lower()
            if any(ex in col_norm for ex in DATE_EXCLUDE_KEYWORDS):
                continue
            if _looks_like_date(df[col]):
                date_col = col
                break

    if amount_col is None:
        for col in columns:
            if col in (client_col, date_col):
                continue
            if _looks_numeric(df[col]):
                amount_col = col
                break

    if client_col is None:
        best_col, best_repeat_ratio = None, -1
        for col in columns:
            if col in (date_col, amount_col):
                continue
            series = df[col].dropna()
            if series.empty:
                continue
            n_unique, n_total = series.nunique(), len(series)
            if n_unique >= n_total:
                continue  # no repeats -> unlikely to be a recurring client identifier
            repeat_ratio = 1 - (n_unique / n_total)
            if repeat_ratio > best_repeat_ratio:
                best_col, best_repeat_ratio = col, repeat_ratio
        client_col = best_col

    return {"client": client_col, "date": date_col, "amount": amount_col}


def normalize(df, columns):
    if columns.get("client") is None:
        raise IngestError("error_no_client_col")
    if columns.get("date") is None:
        raise IngestError("error_no_date_col")

    out = pd.DataFrame()
    out["client"] = df[columns["client"]].astype(str).str.strip()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        out["date"] = pd.to_datetime(df[columns["date"]], errors="coerce")
    out["amount"] = _clean_numeric_series(df[columns["amount"]]) if columns.get("amount") is not None else pd.NA

    out = out.drop_duplicates()  # exact repeats (e.g. an accidental double-upload) shouldn't count as two visits
    out = out.dropna(subset=["date"]).sort_values(["client", "date"]).reset_index(drop=True)

    if out.empty:
        raise IngestError("error_no_valid_dates")
    return out
