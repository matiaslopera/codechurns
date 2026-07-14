import streamlit as st

from core.explain import explain_client
from core.i18n import t

DECISION_OPTIONS = ["pending", "approved", "edited", "discarded"]

_COLUMN_WEIGHTS = [1.3, 3.2, 1.3, 2.4]


def decision_key(client):
    return f"decision_{client}"


def action_text_key(client):
    return f"action_text_{client}"


def render_table_header(lang):
    col_name, col_text, col_decision, col_final = st.columns(_COLUMN_WEIGHTS)
    col_name.markdown(f"**{t('column_client', lang)}**")
    col_text.markdown(f"**{t('dashboard_title', lang)}**")
    col_decision.markdown(f"**{t('decision_label', lang)}**")
    col_final.markdown(f"**{t('edit_textarea_label', lang)}**")
    st.divider()


def render_client_row(row, lang, priority):
    client = row["client"]
    result = explain_client(row, lang)
    action = result["action"]

    st.session_state.setdefault(decision_key(client), "pending")
    st.session_state.setdefault(action_text_key(client), action["description"] if action else "")

    col_name, col_text, col_decision, col_final = st.columns(_COLUMN_WEIGHTS)

    with col_name:
        st.markdown(f"**#{priority} — {client}**")

    with col_text:
        st.write(result["explanation"])
        if action:
            st.caption(f"**{action['label']}**")

    with col_decision:
        st.selectbox(
            t("decision_label", lang),
            options=DECISION_OPTIONS,
            format_func=lambda k: t(f"decision_{k}", lang),
            key=decision_key(client),
            label_visibility="collapsed",
        )

    with col_final:
        st.text_area(
            t("edit_textarea_label", lang),
            key=action_text_key(client),
            label_visibility="collapsed",
            height=100,
        )

    st.divider()
