import streamlit as st


def show_login():

    st.title("Enterprise Authentication")

    st.write(
        "Please sign in using your enterprise email address."
    )

    st.divider()

    email = st.text_input(
        "Enterprise Email Address",
        placeholder="john.doe@company.com"
    )

    st.write("")

    col1, col2, col3 = st.columns([2, 2, 2])

    with col2:

        if st.button(
            "Continue",
            use_container_width=True
        ):

            if email.strip() == "":

                st.warning(
                    "Please enter your enterprise email address."
                )

                return None

            st.session_state.user = email.strip()

            return "new_audit"

    return None