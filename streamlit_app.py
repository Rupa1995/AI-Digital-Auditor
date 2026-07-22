import streamlit as st

from ui.welcome import show_welcome
from ui.login import show_login
from ui.new_audit import show_new_audit
from ui.audit_progress import show_audit_progress
from ui.dashboard import show_dashboard
from ui.audit_report import show_audit_report
from ui.ask_ai_auditor import show_ask_ai_auditor


# ----------------------------------------------------
# Page Configuration
# ----------------------------------------------------

st.set_page_config(
    page_title="AI Digital Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------
# Load CSS
# ----------------------------------------------------

try:

    with open("assets/style.css") as css:

        st.markdown(
            f"<style>{css.read()}</style>",
            unsafe_allow_html=True
        )

except FileNotFoundError:

    pass


# ----------------------------------------------------
# Session State
# ----------------------------------------------------

defaults = {

    "page": "welcome",

    "user": "",

    "audit_request": {},

    "workpaper": None,

    "audit_report": None,

    "ai_commentary": None

}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ----------------------------------------------------
# Navigation
# ----------------------------------------------------

page = st.session_state.page

if page == "welcome":

    next_page = show_welcome()

    if next_page:

        st.session_state.page = next_page

        st.rerun()

elif page == "login":

    next_page = show_login()

    if next_page:

        st.session_state.page = next_page

        st.rerun()

elif page == "new_audit":

    next_page = show_new_audit()

    if next_page:

        st.session_state.page = next_page

        st.rerun()
elif page == "audit_progress":

    next_page = show_audit_progress()

    if next_page:

        st.session_state.page = next_page

        st.rerun()

# ----------------------------------------------------
# Executive Dashboard
# ----------------------------------------------------

elif page == "dashboard":

    next_page = show_dashboard()

    if next_page == "audit_report":

        st.session_state.page = "audit_report"

        st.rerun()

    elif next_page == "ai_commentary":

        st.session_state.open_ai_commentary = True

        st.session_state.page = "audit_report"

        st.rerun()
    
    elif next_page == "ask_ai_auditor":

        st.session_state.page = "ask_ai_auditor"

        st.rerun()

    elif next_page == "new_audit":

        st.session_state.page = "new_audit"

        st.rerun()

# ----------------------------------------------------
# Detailed Audit Report
# ----------------------------------------------------

elif page == "audit_report":

    next_page = show_audit_report()

    if next_page == "dashboard":

        st.session_state.page = "dashboard"

        st.rerun()

    elif next_page == "new_audit":

        st.session_state.page = "new_audit"

        st.rerun()

# ----------------------------------------------------
# Ask AI Auditor
# ----------------------------------------------------

elif page == "ask_ai_auditor":

    next_page = show_ask_ai_auditor()

    if next_page:

        st.session_state.page = next_page

        st.rerun()