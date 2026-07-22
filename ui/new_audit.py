import streamlit as st

from services.evidence_service import EvidenceService
from services.governance_knowledge_service import (
    GovernanceKnowledgeService,
)


AUDITABLE_SERVICES = {
    "Cloud SQL",
    "IAM",
    "Cloud Storage",
}


def _load_control_preview():

    governance = GovernanceKnowledgeService().load_governance()

    controls = []

    for library in governance.get("controls", []):
        for control in library.get("controls", []):
            controls.append({
                "id": control.get("id", "Unknown"),
                "title": control.get("title", ""),
                "statement": control.get("statement", ""),
            })

    return controls


def _clear_discovery_state():

    for key in (
        "project",
        "environment_discovery",
        "connected_project_id",
    ):
        st.session_state.pop(key, None)


def show_new_audit():

    evidence_service = EvidenceService()

    st.title("New Audit Engagement")
    st.caption(
        f"Signed in as: {st.session_state.user}"
    )
    st.divider()

    st.subheader("Step 1 - Select Cloud Platform")

    platform = st.selectbox(
        "Cloud Platform",
        (
            "-- Select Cloud Platform --",
            "Google Cloud Platform (GCP)",
            "Microsoft Azure",
        ),
    )

    if platform == "-- Select Cloud Platform --":
        return None

    if platform == "Microsoft Azure":
        st.info(
            "Azure support will be available in the next release."
        )
        return None

    st.divider()

    st.subheader("Step 2 - Select Audit Scope")

    scope = st.radio(
        "Audit Scope",
        (
            "Entire GCP Organisation",
            "Single Project",
            "Application",
            "Technology Service",
        ),
        label_visibility="collapsed",
    )

    st.divider()

    st.subheader("Step 3 - Scope Details")

    if scope != "Single Project":
        st.info(
            "The current MVP supports automatic discovery "
            "and audit of a single Google Cloud project."
        )
        return None

    project_id = st.text_input(
        "Google Cloud Project ID",
        placeholder="playground-s-11-17660622",
    ).strip()

    if not project_id:
        return None

    if (
        st.session_state.get("connected_project_id")
        and st.session_state.connected_project_id != project_id
    ):
        _clear_discovery_state()

    st.divider()

    st.subheader("Step 4 - Discover Google Cloud Environment")

    if st.button(
        "Connect and Discover Environment",
        use_container_width=True,
    ):
        with st.status(
            "Discovering the live Google Cloud environment...",
            expanded=True,
        ) as status:

            st.write("Validating Google Cloud project...")

            project = evidence_service.validate_project(
                project_id
            )

            if not project.get("valid"):
                st.error(
                    project.get(
                        "message",
                        "Unable to validate the project.",
                    )
                )
                return None

            st.write(
                "Discovering Cloud SQL, IAM, Storage, VPC, "
                "Pub/Sub and Secret Manager..."
            )

            discovery = evidence_service.discover_environment(
                project_id
            )

            st.session_state.project = project
            st.session_state.environment_discovery = discovery
            st.session_state.connected_project_id = project_id

            status.update(
                label="Environment discovery completed",
                state="complete",
                expanded=False,
            )

    if "project" not in st.session_state:
        return None

    project = st.session_state.project
    discovery = st.session_state.environment_discovery

    st.success(
        "Successfully connected to Google Cloud."
    )

    st.divider()

    st.subheader("Connected Google Cloud Environment")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Project ID**")
        st.write(project.get("projectId", ""))

        st.write("**Project Name**")
        st.write(project.get("projectName", ""))

    with col2:
        st.write("**Project Number**")
        st.write(project.get("projectNumber", ""))

        st.write("**Lifecycle State**")
        st.write(project.get("state", ""))

    st.divider()

    st.subheader("Step 5 - AI Environment Discovery")

    rows = []

    for service in discovery.get("services", []):
        service_name = service.get("service")
        count = service.get("resourceCount", 0)

        rows.append({
            "Technology": service_name,
            "Resources Discovered": count,
            "MVP Audit Capability": (
                "Live deterministic audit"
                if service_name in AUDITABLE_SERVICES
                and (
                    count > 0
                    or service_name == "IAM"
                )
                else
                "Discovery and AI scoping only"
            ),
        })

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )

    auditable_services = [
        service
        for service in discovery.get("services", [])
        if service.get("service") in AUDITABLE_SERVICES
        and (
            service.get("resourceCount", 0) > 0
            or service.get("service") == "IAM"
        )
    ]

    st.info(
        "The AI Audit Planner will analyse all discovered "
        "technologies. Deterministic live validation is currently "
        "implemented for Cloud SQL, IAM and Cloud Storage."
    )

    if discovery.get("errors"):
        with st.expander("Discovery Warnings"):
            for service_name, message in discovery["errors"].items():
                st.warning(
                    f"{service_name}: {message}"
                )

    st.divider()

    st.subheader(
        "Step 6 - Review Enterprise Controls Available for Assessment"
    )

    controls = _load_control_preview()

    with st.expander(
        "Enterprise Control Library",
        expanded=True,
    ):
        st.write(
            "The AI Audit Planner will determine which controls "
            "apply to the discovered technologies and explain "
            "why other controls are excluded."
        )

        for control in controls:
            st.markdown(
                f"**{control['title'] or control['id']}**"
            )
            st.write(control["statement"])
            st.write("")

    st.divider()

    st.subheader("Audit Target Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Cloud Platform**")
        st.write("Google Cloud Platform")

        st.write("**Audit Scope**")
        st.write(scope)

        st.write("**Project ID**")
        st.write(project.get("projectId", ""))

    with col2:
        st.write("**Technologies Discovered**")
        st.write(
            len(discovery.get("services", []))
        )

        st.write("**Technologies Auditable in MVP**")
        st.write(
            ", ".join([
                item.get("service")
                for item in auditable_services
            ])
            or "None"
        )

        st.write("**Controls Available**")
        st.write(f"{len(controls)} Controls")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Launch AI-scoped Live Audit",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.audit_request = {
                "requestor": st.session_state.user,
                "platform": "Google Cloud Platform",
                "scope": scope,
                "identifier": project.get("projectId", project_id),
                "environmentDiscovery": discovery,
                "auditableServices": [
                    item.get("service")
                    for item in auditable_services
                ],
                "evidenceMode": "Live",
            }

            for key in (
                "workpaper",
                "audit_report",
                "audit_results",
                "execution_plan",
                "live_evidence",
                "resource_evidence",
                "ai_commentary",
                "chat_history",
            ):
                st.session_state.pop(key, None)

            _clear_discovery_state()

            return "audit_progress"

    with col2:
        if st.button(
            "Cancel",
            use_container_width=True,
        ):
            _clear_discovery_state()
            return "welcome"

    return None
