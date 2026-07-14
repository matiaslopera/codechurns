import streamlit as st

from core.explain import explain_client
from core.i18n import t

DECISION_OPTIONS = ["pending", "approved", "edited", "discarded"]


def decision_key(client):
    return f"decision_{client}"


def action_text_key(client):
    return f"action_text_{client}"


def render_client_card(row, lang, priority):
    client = row["client"]
    result = explain_client(row, lang)
    action = result["action"]

    st.session_state.setdefault(decision_key(client), "pending")
    st.session_state.setdefault(action_text_key(client), action["description"] if action else "")

    with st.expander(f"#{priority} — {client}", expanded=(priority == 1)):
        st.write(result["explanation"])
        if action:
            st.markdown(f"**{action['label']}**")

        st.radio(
            t("decision_label", lang),
            options=DECISION_OPTIONS,
            format_func=lambda k: t(f"decision_{k}", lang),
            horizontal=True,
            key=decision_key(client),
        )
        st.text_area(t("edit_textarea_label", lang), key=action_text_key(client))
