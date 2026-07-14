import streamlit as st

from core.i18n import t
from core.ingest import IngestError, detect_columns, load_file, normalize
from core.risk_engine import compute_risk
from ui.dashboard import render as render_dashboard

st.set_page_config(page_title="Customer Retention Agent", page_icon="📋")

if "lang" not in st.session_state:
    st.session_state.lang = "es"

lang = st.sidebar.selectbox(
    t("language_label", st.session_state.lang),
    options=["es", "en"],
    index=["es", "en"].index(st.session_state.lang),
    format_func=lambda code: {"es": "Español", "en": "English"}[code],
)
st.session_state.lang = lang

st.title(t("app_title", lang))
st.caption(t("app_subtitle", lang))

uploaded_file = st.file_uploader(
    t("upload_label", lang),
    type=["csv", "xlsx", "xls"],
    help=t("upload_help", lang),
)

if uploaded_file is not None:
    try:
        raw_df = load_file(uploaded_file)
        columns = detect_columns(raw_df)
        normalized_df = normalize(raw_df, columns)
    except IngestError as e:
        st.error(t(e.key, lang, **e.kwargs))
    else:
        with st.expander(t("detected_columns", lang)):
            na = t("not_detected", lang)
            col1, col2, col3 = st.columns(3)
            col1.metric(t("column_client", lang), columns["client"] or na)
            col2.metric(t("column_date", lang), columns["date"] or na)
            col3.metric(t("column_amount", lang), columns["amount"] or na)

            st.subheader(t("preview_title", lang))
            st.caption(t("rows_loaded", lang, n=len(normalized_df), file=uploaded_file.name))
            st.dataframe(normalized_df, use_container_width=True)

        risk_df = compute_risk(normalized_df)
        render_dashboard(risk_df, lang)
