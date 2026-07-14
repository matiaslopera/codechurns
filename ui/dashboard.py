import streamlit as st

from core.actions import build_action
from core.explain import explain_client
from core.export import build_workbook
from core.i18n import t
from core.risk_engine import STATUS_AT_RISK, STATUS_INSUFFICIENT_DATA, STATUS_ON_TRACK
from ui.review_panel import action_text_key, action_type_key, decision_key, render_client_row, render_table_header


def _build_export_rows(at_risk_df, lang):
    rows = []
    for _, row in at_risk_df.iterrows():
        client = row["client"]
        # Use the owner's current strategy choice (may have been overridden from
        # the system's original suggestion), not the initial suggestion itself.
        action_type = st.session_state.get(action_type_key(client))
        action = build_action(action_type, lang) if action_type else None
        rows.append(
            {
                "client": client,
                "normal_cycle_days": row["normal_cycle_days"],
                "days_since_last_visit": row["days_since_last_visit"],
                "risk_ratio": row["risk_ratio"],
                "explanation": explain_client(row, lang)["explanation"],
                "action_key": action["key"] if action else None,
                "action_label": action["label"] if action else "",
                "decision": st.session_state.get(decision_key(client), "pending"),
                "final_action_text": st.session_state.get(action_text_key(client), ""),
            }
        )
    return rows


def render(risk_df, lang):
    at_risk_df = risk_df[risk_df["status"] == STATUS_AT_RISK]
    on_track_df = risk_df[risk_df["status"] == STATUS_ON_TRACK]
    insufficient_df = risk_df[risk_df["status"] == STATUS_INSUFFICIENT_DATA]

    st.header(t("dashboard_title", lang))
    st.caption(t("action_disclaimer", lang))

    if at_risk_df.empty:
        st.info(t("no_at_risk_clients", lang))
    else:
        render_table_header(lang)
        for priority, (_, row) in enumerate(at_risk_df.iterrows(), start=1):
            render_client_row(row, lang, priority)

    export_rows = _build_export_rows(at_risk_df, lang)
    if export_rows:
        workbook = build_workbook(export_rows, lang)
        file_name = "clientes_en_riesgo.xlsx" if lang == "es" else "at_risk_customers.xlsx"
        st.download_button(
            label=t("export_button", lang),
            data=workbook,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.caption(t("export_no_data", lang))

    with st.expander(t("on_track_section_title", lang, n=len(on_track_df))):
        if not on_track_df.empty:
            st.dataframe(
                on_track_df[["client", "normal_cycle_days", "days_since_last_visit"]],
                use_container_width=True,
            )

    with st.expander(t("insufficient_section_title", lang, n=len(insufficient_df))):
        if not insufficient_df.empty:
            st.dataframe(
                insufficient_df[["client", "n_visits", "days_since_last_visit"]],
                use_container_width=True,
            )
