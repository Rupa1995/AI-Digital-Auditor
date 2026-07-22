import streamlit as st

from ui.layout import hero_section


def show_login():

    hero_section(
        title="Enterprise authentication built for modern audit workflows.",
        subtitle="Sign in with your work email to access audit discovery, governance reasoning, and executive reports.",
        description=(
            "This secure sign-in step verifies your identity and prepares your workspace for a live audit experience. "
            "Enter your enterprise email to continue."
        ),
    )

    st.markdown(
        """
        <div class="glass-panel">
            <div class="glass-panel-title">Continue with your enterprise email</div>
            <div class="glass-panel-body">
                Use a verified corporate email address and we will take you straight into the audit setup flow.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    email = st.text_input(
        "Enterprise Email Address",
        placeholder="john.doe@company.com"
    )

    st.write("")

    if st.button("Continue", use_container_width=True):

        if email.strip() == "":

            st.warning(
                "Please enter your enterprise email address."
            )

            return None

        st.session_state.user = email.strip()

        return "new_audit"

    return None