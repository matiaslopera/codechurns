import streamlit as st

from core.actions import ACTION_DISCOUNT, ACTION_REMINDER, ACTION_TYPES, build_action, build_action_text
from core.explain import explain_client
from core.i18n import t
from core.messages import TONE_AUTO, TONE_FORMAL, TONE_INFORMAL, build_message, suggest_tone

DECISION_OPTIONS = ["pending", "approved", "edited", "discarded"]
TONE_OPTIONS = [TONE_AUTO, TONE_FORMAL, TONE_INFORMAL]

_COLUMN_WEIGHTS = [1.1, 2.6, 1.8, 1.1, 2.2]


def decision_key(client):
    return f"decision_{client}"


def action_text_key(client):
    return f"action_text_{client}"


def action_type_key(client):
    return f"action_type_{client}"


def discount_value_key(client):
    return f"discount_value_{client}"


def tone_key(client):
    return f"tone_{client}"


def message_text_key(client):
    return f"message_text_{client}"


def _refresh_action_text(client, lang):
    action_type = st.session_state.get(action_type_key(client))
    discount_value = st.session_state.get(discount_value_key(client), "")
    st.session_state[action_text_key(client)] = build_action_text(action_type, discount_value, lang)


def _resolved_tone(client, row):
    tone = st.session_state.get(tone_key(client), TONE_AUTO)
    return suggest_tone(row["n_visits"]) if tone == TONE_AUTO else tone


def _regenerate_message(client, row, lang):
    action_type = st.session_state.get(action_type_key(client))
    discount_value = st.session_state.get(discount_value_key(client), "")
    tone = _resolved_tone(client, row)
    st.session_state[message_text_key(client)] = build_message(
        row, action_type, lang, tone=tone, discount_value=discount_value
    )


def _on_strategy_change(client, row, lang):
    _refresh_action_text(client, lang)
    _regenerate_message(client, row, lang)


def _on_discount_value_change(client, row, lang):
    _refresh_action_text(client, lang)
    _regenerate_message(client, row, lang)


def render_table_header(lang):
    col_name, col_text, col_strategy, col_decision, col_final = st.columns(_COLUMN_WEIGHTS)
    col_name.markdown(f"**{t('column_client', lang)}**")
    col_text.markdown(f"**{t('dashboard_title', lang)}**")
    col_strategy.markdown(f"**{t('strategy_label', lang)}**")
    col_decision.markdown(f"**{t('decision_label', lang)}**")
    col_final.markdown(f"**{t('edit_textarea_label', lang)}**")
    st.divider()


def render_client_row(row, lang, priority):
    client = row["client"]
    result = explain_client(row, lang)
    suggested_action = result["action"]
    suggested_type = suggested_action["key"] if suggested_action else ACTION_REMINDER
    if suggested_type not in ACTION_TYPES:
        suggested_type = ACTION_REMINDER

    st.session_state.setdefault(action_type_key(client), suggested_type)
    st.session_state.setdefault(discount_value_key(client), "")
    st.session_state.setdefault(decision_key(client), "pending")
    st.session_state.setdefault(
        action_text_key(client),
        build_action_text(
            st.session_state[action_type_key(client)],
            st.session_state[discount_value_key(client)],
            lang,
        ),
    )
    st.session_state.setdefault(tone_key(client), TONE_AUTO)
    st.session_state.setdefault(
        message_text_key(client),
        build_message(
            row,
            st.session_state[action_type_key(client)],
            lang,
            tone=_resolved_tone(client, row),
            discount_value=st.session_state[discount_value_key(client)],
        ),
    )

    col_name, col_text, col_strategy, col_decision, col_final = st.columns(_COLUMN_WEIGHTS)

    with col_name:
        st.markdown(f"**#{priority} — {client}**")

    with col_text:
        st.write(result["explanation"])

    with col_strategy:
        st.selectbox(
            t("strategy_label", lang),
            options=ACTION_TYPES,
            format_func=lambda k: build_action(k, lang)["label"],
            key=action_type_key(client),
            label_visibility="collapsed",
            on_change=_on_strategy_change,
            kwargs={"client": client, "row": row, "lang": lang},
        )
        if st.session_state[action_type_key(client)] == ACTION_DISCOUNT:
            st.text_input(
                t("discount_value_label", lang),
                key=discount_value_key(client),
                placeholder=t("discount_value_placeholder", lang),
                label_visibility="collapsed",
                on_change=_on_discount_value_change,
                kwargs={"client": client, "row": row, "lang": lang},
            )

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
            kwargs={"client": client, "row": row, "lang": lang},
        )
        st.text_area(
            t("message_textarea_label", lang),
            key=message_text_key(client),
            height=100,
        )

    st.divider()
