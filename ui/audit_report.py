import json

import streamlit as st

from services.gemini_service import GeminiService


def _status_icon(status):

    if status == "PASS":
        return "✅ PASS"

    if status == "FAIL":
        return "❌ FAIL"

    return "⚠ NOT VERIFIED"


def _risk_badge(risk):

    if risk == "HIGH":
        return "🟥 HIGH"

    if risk == "MEDIUM":
        return "🟨 MEDIUM"

    if risk == "LOW":
        return "🟩 LOW"

    return "⬜ NOT ASSIGNED"


def _control_name(finding):

    return finding.get(
        "controlName",
        finding.get(
            "controlStatement",
            "Unknown Control",
        ),
    )


def _resource_identity(resource_evidence):
    """
    Returns technology and resource name across both the older
    flattened evidence schema and the current nested evidence schema.
    """

    resource = resource_evidence.get(
        "resource",
        {}
    )

    technology = (
        resource_evidence.get("service")
        or resource.get("service")
        or resource.get("resourceType")
        or "Unknown Technology"
    )

    resource_name = (
        resource_evidence.get("resourceName")
        or resource.get("resourceName")
        or resource.get("instanceName")
        or "Unknown Resource"
    )

    return technology, resource_name


def _adr_identity(adr):

    document = adr.get(
        "document",
        "No ADR Available",
    )

    content = adr.get(
        "content",
        "",
    )

    adr_id = adr.get("id")

    if not adr_id:
        adr_id = document.split("_", 1)[0]

    title = adr.get("title")

    if not title:
        title = document

        for line in content.splitlines():
            line = line.strip()

            if not line.startswith("ADR-"):
                continue

            if "–" in line:
                title = line.split("–", 1)[1].strip()
                break

            if " - " in line:
                title = line.split(" - ", 1)[1].strip()
                break

    return adr_id, title


def _display_commentary(commentary):

    if not commentary:
        return

    if not commentary.get("success"):
        st.warning(
            commentary.get(
                "message",
                "AI commentary is unavailable.",
            )
        )
        return

    st.subheader("Executive Summary")
    st.write(
        commentary.get(
            "executiveSummary",
            "",
        )
    )

    st.subheader("Positive Observations")
    for item in commentary.get(
            "positiveObservations",
            []):
        st.write(f"• {item}")

    st.subheader("Key Risks")
    for item in commentary.get(
            "keyRisks",
            []):
        st.write(f"• {item}")

    st.subheader("Business Impact")
    st.write(
        commentary.get(
            "businessImpact",
            "",
        )
    )

    st.subheader("Management Recommendations")
    for item in commentary.get(
            "managementRecommendations",
            []):
        st.write(f"• {item}")

    st.subheader("Overall Auditor Commentary")
    st.info(
        commentary.get(
            "overallCommentary",
            "",
        )
    )


def show_audit_report():

    workpaper = st.session_state.get("workpaper")

    if workpaper is None:
        st.error("No audit workpaper available.")

        if st.button(
            "Start New Audit",
            use_container_width=True,
        ):
            return "new_audit"

        return None

    engagement = workpaper.get(
        "auditEngagement",
        {},
    )
    scope = workpaper.get(
        "auditScope",
        {},
    )
    summary = workpaper.get(
        "summary",
        {},
    )
    findings = workpaper.get(
        "findings",
        [],
    )
    resources = workpaper.get(
        "resourceEvidence",
        [],
    )
    adr = workpaper.get(
        "governance",
        {},
    ).get(
        "adr",
        {},
    )

    st.caption("CONFIDENTIAL")
    st.title("AI Digital Auditor")
    st.subheader(
        "Enterprise Technology Assurance Report"
    )
    st.caption(
        "Evidence-driven Enterprise Technology Assurance"
    )
    st.divider()

    st.header("Audit Engagement")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Audit ID**")
        st.write(
            engagement.get(
                "auditId",
                "",
            )
        )

        st.write("**Audit Date**")
        st.write(
            engagement.get(
                "auditDate",
                "",
            )
        )

        st.write("**Audit Type**")
        st.write(
            engagement.get(
                "auditType",
                "",
            )
        )

    with col2:
        st.write("**Cloud Platform**")
        st.write(
            scope.get(
                "cloudPlatform",
                "Google Cloud Platform",
            )
        )

        st.write("**Technology**")
        st.write(
            scope.get(
                "service",
                "Cloud SQL",
            )
        )

        st.write("**Project**")
        st.write(
            scope.get(
                "projectId",
                scope.get("project", ""),
            )
        )

        st.write("**Resources Audited**")
        st.write(
            scope.get(
                "resourceCount",
                len(resources),
            )
        )

    st.divider()

    st.header("Overall Audit Opinion")

    opinion = summary.get(
        "overallOpinion",
        "UNKNOWN",
    )

    if opinion == "UNQUALIFIED":
        st.success("🟢 UNQUALIFIED")
    elif opinion == "QUALIFIED":
        st.warning("🟡 QUALIFIED")
    else:
        st.error("🔴 ADVERSE")

    st.divider()

    st.header("Executive Summary")

    commentary = st.session_state.get(
        "ai_commentary",
        {},
    )

    if commentary.get("success"):
        st.write(
            commentary.get(
                "executiveSummary",
                "",
            )
        )
    else:
        st.write(
            f"""
The audit evaluated **{summary.get('controlsEvaluated', 0)}
resource-control combinations** across
**{summary.get('resourcesAudited', len(resources))} Cloud SQL
resources** using live evidence collected from Google Cloud.

**Evaluations Passed:** {summary.get('passed', 0)}

**Evaluations Failed:** {summary.get('failed', 0)}

**Not Verified:** {summary.get('notVerified', 0)}

**Overall Audit Opinion:** {opinion}
"""
        )

    st.divider()

    st.header("Resource Assessment Summary")

    resource_rows = []

    for resource in resources:
        _, resource_name = _resource_identity(
            resource
        )

        resource_findings = [
            finding
            for finding in findings
            if finding.get("resourceName") == resource_name
        ]

        technology, resource_name = _resource_identity(
            resource
        )

        resource_rows.append({
            "Technology": technology,
            "Resource": resource_name,
            "Passed": len([
                finding
                for finding in resource_findings
                if finding.get("status") == "PASS"
            ]),
            "Failed": len([
                finding
                for finding in resource_findings
                if finding.get("status") == "FAIL"
            ]),
            "Not Verified": len([
                finding
                for finding in resource_findings
                if finding.get("status") == "NOT VERIFIED"
            ]),
        })

    st.dataframe(
        resource_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.header("Control Assessment Summary")

    table = []

    for finding in findings:
        table.append({
            "Resource":
                finding.get(
                    "resourceName",
                    "Unknown",
                ),
            "Control":
                _control_name(finding),
            "Objective":
                finding.get(
                    "validationObjective",
                    "",
                ),
            "Status":
                _status_icon(
                    finding.get(
                        "status",
                        "NOT VERIFIED",
                    )
                ),
            "Risk":
                _risk_badge(
                    finding.get(
                        "risk",
                        "Not Assigned",
                    )
                ),
        })

    if table:
        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No findings were produced.")

    st.divider()

    st.header("Detailed Control Assessment")

    for resource in resources:
        _, resource_name = _resource_identity(
            resource
        )

        technology, resource_name = _resource_identity(
            resource
        )

        st.subheader(
            f"{technology} — {resource_name}"
        )

        resource_findings = [
            finding
            for finding in findings
            if finding.get("resourceName") == resource_name
        ]

        for finding in resource_findings:
            with st.expander(
                f"{finding.get('controlId', 'Control')} - "
                f"{finding.get('validationObjective', '')}",
                expanded=True,
            ):
                st.write(
                    f"**Control:** {_control_name(finding)}"
                )
                st.write(
                    f"**Assessment:** "
                    f"{_status_icon(finding.get('status', 'NOT VERIFIED'))}"
                )
                st.write(
                    f"**Risk:** "
                    f"{_risk_badge(finding.get('risk', 'Not Assigned'))}"
                )
                st.write(
                    f"**Expected:** "
                    f"{finding.get('expected', '')}"
                )
                st.write(
                    f"**Actual:** "
                    f"{finding.get('actual', '')}"
                )
                st.write(
                    f"**Requirement Source:** "
                    f"{finding.get('requirementSource', '')}"
                )
                st.write(
                    f"**Extracted Requirement:** "
                    f"{finding.get('extractedRequirement', '')}"
                )
                st.write(
                    f"**Validation Check:** "
                    f"{finding.get('validationCheck', '')}"
                )

                st.write("**Observation**")
                st.info(
                    finding.get(
                        "observation",
                        "",
                    )
                )

                recommendation = finding.get(
                    "recommendation"
                )

                if recommendation:
                    st.write(
                        "**Management Recommendation**"
                    )
                    st.success(
                        recommendation
                    )

    st.divider()

    st.header("Executive Evidence Assessment")

    evidence_rows = []

    for resource in resources:
        technology, resource_name = _resource_identity(
            resource
        )

        technical = resource.get(
            "technicalEvidence",
            {},
        )

        if technology == "IAM":
            evidence_rows.append({
                "Technology": technology,
                "Resource": resource_name,
                "Public IAM Access": (
                    "Detected"
                    if technical.get("publicAccessDetected")
                    else "Not detected"
                    if technical.get("publicAccessDetected") is False
                    else "Not available"
                ),
                "Service Accounts": technical.get(
                    "serviceAccountCount",
                    "Not available",
                ),
                "Owner-role Service Accounts": technical.get(
                    "ownerRoleServiceAccountCount",
                    "Not available",
                ),
                "User-managed Keys": technical.get(
                    "userManagedServiceAccountKeyCount",
                    "Not available",
                ),
                "Encryption": "Not applicable",
                "Password Minimum": "Not applicable",
                "Availability": "Not applicable",
            })

        elif technology == "Cloud Storage":
            evidence_rows.append({
                "Technology": technology,
                "Resource": resource_name,
                "Public IAM Access": "Not applicable",
                "Service Accounts": "Not applicable",
                "Owner-role Service Accounts": "Not applicable",
                "User-managed Keys": "Not applicable",
                "Encryption": technical.get(
                    "encryption",
                    "Not available",
                ),
                "Password Minimum": "Not applicable",
                "Availability": technical.get(
                    "locationType",
                    "Not available",
                ),
            })

        else:
            evidence_rows.append({
                "Technology": technology,
                "Resource": resource_name,
                "Public IAM Access": "Not applicable",
                "Service Accounts": "Not applicable",
                "Owner-role Service Accounts": "Not applicable",
                "User-managed Keys": "Not applicable",
                "Encryption": technical.get(
                    "encryption",
                    "Not available",
                ),
                "Password Minimum": technical.get(
                    "minimumPasswordLength",
                    "Not available",
                ),
                "Availability": technical.get(
                    "availabilityType",
                    "Not available",
                ),
            })

    st.dataframe(
        evidence_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Evidence concerns are configuration observations. "
        "They become formal audit findings only where an approved "
        "control and deterministic validator have assessed them."
    )

    with st.expander(
        "Technical Evidence by Resource",
        expanded=False,
    ):
        for resource in resources:
            technology, resource_name = _resource_identity(
                resource
            )

            st.markdown(
                f"### {technology} — {resource_name}"
            )
            st.json(
                resource.get(
                    "technicalEvidence",
                    {},
                )
            )

    with st.expander(
        "Developer / Raw Audit Evidence",
        expanded=False,
    ):
        st.json(
            st.session_state.get(
                "live_evidence",
                {},
            )
        )

    st.divider()

    st.header("Governance Reference")

    adr_id, adr_title = _adr_identity(
        adr
    )

    st.write(
        f"**ID:** {adr_id}"
    )
    st.write(
        f"**Title:** {adr_title}"
    )

    with st.expander("View ADR Content"):
        st.text(
            adr.get(
                "content",
                "",
            )
        )

    st.divider()

    st.header("🧠 AI-assisted Auditor Commentary")

    auto_generate = st.session_state.pop(
        "open_ai_commentary",
        False,
    )

    generate = st.button(
        "Regenerate AI Commentary",
        use_container_width=True,
    )

    if generate or auto_generate:
        with st.spinner(
            "Generating AI commentary..."
        ):
            gemini = GeminiService()
            commentary = (
                gemini.generate_audit_commentary(
                    workpaper
                )
            )

        st.session_state.ai_commentary = commentary

    _display_commentary(
        st.session_state.get(
            "ai_commentary",
            {},
        )
    )

    st.divider()

    with st.expander("View AI Audit Execution Plan"):
        st.json(
            st.session_state.get(
                "execution_plan",
                {},
            )
        )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "← Executive Dashboard",
            use_container_width=True,
        ):
            return "dashboard"

    with col2:
        if st.button(
            "Start New Audit",
            use_container_width=True,
        ):
            return "new_audit"

    with col3:
        st.download_button(
            "Download Workpaper JSON",
            data=json.dumps(
                workpaper,
                indent=2,
                default=str,
            ),
            file_name=(
                "ai-digital-auditor-project-workpaper.json"
            ),
            mime="application/json",
            use_container_width=True,
        )

    return None
