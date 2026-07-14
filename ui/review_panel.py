import streamlit as st

from core.explain import explain_client
from core.i18n import t
from core.messages import TONE_AUTO, TONE_FORMAL, TONE_INFORMAL, build_message, suggest_tone

DECISION_OPTIONS = ["pending", "approved", "edited", "discarded"]
TONE_OPTIONS = [TONE_AUTO, TONE_FORMAL, TONE_INFORMAL]

_COLUMN_WEIGHTS = [1.3, 3.2, 1.3, 2.4]


def decision_key(client):
    return f"decision_{client}"


def action_text_key(client):
    return f"action_text_{client}"


def tone_key(client):
    return f"tone_{client}"


def message_text_key(client):
    return f"message_text_{client}"


def _resolved_tone(client, row):
    tone = st.session_state.get(tone_key(client), TONE_AUTO)
    return suggest_tone(row["n_visits"]) if tone == TONE_AUTO else tone


def _regenerate_message(client, row, action_key, lang):
    tone = _resolved_tone(client, row)
    st.session_state[message_text_key(client)] = build_message(row, action_key, lang, tone=tone)


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
    action_key = action["key"] if action else None

    st.session_state.setdefault(decision_key(client), "pending")
    st.session_state.setdefault(action_text_key(client), action["description"] if action else "")
    st.session_state.setdefault(tone_key(client), TONE_AUTO)
    st.session_state.setdefault(
        message_text_key(client), build_message(row, action_key, lang, tone=_resolved_tone(client, row))
    )

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

    with st.expander(t("message_section_title", lang)):
        st.selectbox(
            t("message_tone_label", lang),
            options=TONE_OPTIONS,
            format_func=lambda k: t(f"message_tone_{k}", lang),
            key=tone_key(client),
            on_change=_regenerate_message,
            args=(client, row, action_key, lang),
        )
        st.text_area(
            t("message_textarea_label", lang),
            key=message_text_key(client),
            height=100,
        )

    st.divider()
