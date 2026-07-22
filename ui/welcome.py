import streamlit as st


def show_welcome():

    st.title("AI Digital Auditor")

    st.subheader("AI-assisted Technology Auditor")

    st.divider()

    st.markdown(
        """
### What is AI Digital Auditor?

AI Digital Auditor is an AI-assisted Technology Auditor that performs
evidence-based technology audits using enterprise governance and
AI reasoning to generate professional audit findings and reports.

Unlike traditional audit approaches, the platform combines
technical evidence, enterprise controls and AI analysis to assist
technology auditors in delivering consistent, high-quality audits.
"""
    )

    st.divider()

    st.markdown(
        """
### Why do organisations need it?

Technology environments change continuously while audits are often
performed periodically using manual evidence collection and expert
judgement. As technology estates continue to grow, maintaining
consistent audit quality becomes increasingly difficult.

AI Digital Auditor assists auditors by automating evidence collection,
assessing technology environments against enterprise governance and
producing AI-assisted audit findings that improve audit consistency,
quality and efficiency.
"""
    )

    st.divider()

    st.markdown(
        """
### Benefits

- Continuous audit readiness

- Reduced manual audit effort

- Faster evidence collection

- Evidence-based audit assessments

- Consistent application of enterprise governance

- AI-assisted audit findings and recommendations

- Professional audit reports
"""
    )

    st.divider()

    col1, col2, col3 = st.columns([2, 3, 2])

    with col2:

        if st.button(
            "Explore AI Digital Auditor",
            use_container_width=True
        ):
            return "login"

    return None