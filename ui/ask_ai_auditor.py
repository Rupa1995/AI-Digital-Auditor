import streamlit as st

from services.audit_chat_service import AuditChatService


def show_ask_ai_auditor():

    workpaper = st.session_state.get("workpaper")

    if workpaper is None:
        st.error("No audit workpaper available.")

        if st.button(
            "Start New Audit",
            use_container_width=True,
        ):
            return "new_audit"

        return None

    st.title("AI Digital Auditor")

    st.subheader("💬 Ask AI Auditor")

    st.caption(
        "Ask questions grounded in the completed live audit, "
        "its evidence, findings and governance references."
    )

    st.divider()

    with st.expander(
        "Example Questions",
        expanded=True,
    ):
        st.markdown(
            """
- Why did database encryption fail?
- Which control passed and why?
- What evidence supports the password-policy result?
- Which requirement came directly from the control?
- Which requirement came from the ADR?
- What should management remediate first?
- Summarise the audit for a non-technical executive.
"""
        )

    question = st.text_area(
        "Your Question",
        height=140,
        placeholder="Ask a question about this completed audit...",
    )

    if st.button(
        "💬 Ask AI Auditor",
        type="primary",
        use_container_width=True,
    ):
        if not question.strip():
            st.warning(
                "Please enter a question."
            )
        else:
            with st.spinner(
                "AI Auditor is analysing the completed audit..."
            ):
                chat_service = AuditChatService()

                response = chat_service.answer_question(
                    workpaper,
                    question,
                )

            if response.get("success"):
                st.success(
                    "Answer generated successfully."
                )

                st.subheader(
                    "AI Auditor Response"
                )

                st.write(
                    response.get(
                        "answer",
                        "",
                    )
                )
            else:
                st.error(
                    "AI Auditor is currently unavailable."
                )

                with st.expander(
                    "Technical Details"
                ):
                    st.code(
                        response.get(
                            "message",
                            "Unknown error",
                        )
                    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "← Executive Dashboard",
            use_container_width=True,
        ):
            return "dashboard"

    with col2:
        if st.button(
            "📄 Detailed Report",
            use_container_width=True,
        ):
            return "audit_report"

    return None
