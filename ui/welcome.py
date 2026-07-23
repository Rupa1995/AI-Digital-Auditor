import streamlit as st

from ui.layout import hero_section


def show_welcome():

    hero_section(
        title="Audit Smarter. Deliver Faster.",
        subtitle="AI-driven evidence collection, enterprise governance reasoning, and polished audit reports in one modern workflow.",
        description=(
            "AI Digital Auditor brings AI reasoning and live evidence into a single audit experience. "
            "It helps auditors discover controls, assess risk, and generate professional findings with speed, "
            "clarity, and governance confidence."
        ),
    )

    st.markdown(
        """
        <div class="glass-panel">
            <div class="glass-panel-title">Why this matters</div>
            <div class="glass-panel-body">
                Audits should be fast, repeatable, and grounded in evidence. This platform combines cloud discovery,
                enterprise governance, and AI-assisted reasoning so teams can audit complex environments with confidence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card">
                <h3>Live cloud discovery</h3>
                <p>Automatically identify audit-relevant services, resources, and security posture in a GCP project.</p>
            </div>
            <div class="feature-card">
                <h3>Governance-first controls</h3>
                <p>Apply enterprise control logic and technology policy thinking across every audit workflow.</p>
            </div>
            <div class="feature-card">
                <h3>Professional reports</h3>
                <p>Generate polished findings, risk summaries, and executive-ready audit commentary automatically.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Explore AI Digital Auditor", use_container_width=True):
        return "login"

    return None