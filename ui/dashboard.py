import streamlit as st

from ui.layout import hero_section


def _calculate_dashboard(workpaper):

    summary = workpaper.get("summary", {})
    findings = workpaper.get("findings", [])

    total = summary.get("controlsEvaluated", 0)
    passed = summary.get("passed", 0)

    compliance = 0

    if total > 0:
        compliance = round(
            (passed / total) * 100
        )

    high = len([
        finding
        for finding in findings
        if finding.get("risk") == "HIGH"
        and finding.get("status") == "FAIL"
    ])

    medium = len([
        finding
        for finding in findings
        if finding.get("risk") == "MEDIUM"
        and finding.get("status") == "FAIL"
    ])

    return {
        "compliance": compliance,
        "high": high,
        "medium": medium,
    }


def _control_type(control_id):
    """
    Identifies the governance layer from the control ID.
    """

    if str(control_id).startswith("EC-"):
        return "Enterprise Control"

    return "Technology Control"


def _display_ai_governance_interpretation(
        execution_plan):
    """
    Presents the AI Audit Planner output as a readable
    governance interpretation rather than raw JSON.
    """

    controls = execution_plan.get(
        "controls",
        []
    )

    if not controls:
        st.info(
            "No AI Audit Execution Plan is available."
        )
        return

    enterprise_controls = [
        control
        for control in controls
        if str(
            control.get("controlId", "")
        ).startswith("EC-")
    ]

    technology_controls = [
        control
        for control in controls
        if not str(
            control.get("controlId", "")
        ).startswith("EC-")
    ]

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Enterprise Controls Interpreted",
        len(enterprise_controls),
    )

    metric2.metric(
        "Technology Controls Analysed",
        len(technology_controls),
    )

    metric3.metric(
        "Total Controls Planned",
        len(controls),
    )

    for control in controls:
        control_id = control.get(
            "controlId",
            "Unknown Control"
        )

        control_statement = control.get(
            "controlStatement",
            ""
        )

        control_type = _control_type(
            control_id
        )

        service_analysis = control.get(
            "serviceAnalysis",
            []
        )

        validation_checks = (
            control.get(
                "executionPlan",
                {}
            ).get(
                "validationChecks",
                []
            )
        )

        applicable = [
            item
            for item in service_analysis
            if item.get("applicable")
        ]

        not_applicable = [
            item
            for item in service_analysis
            if item.get("applicable") is False
        ]

        expanded = control_type == "Enterprise Control"

        with st.expander(
            f"{control_id} — {control_statement}",
            expanded=expanded,
        ):
            st.caption(control_type)

            if control_type == "Enterprise Control":
                st.info(
                    "AI interpreted this high-level enterprise "
                    "control and translated it into "
                    "technology-specific validation objectives."
                )

            left, right = st.columns(2)

            with left:
                st.markdown("**Applicable Technologies**")

                if applicable:
                    for item in applicable:
                        st.markdown(
                            f"✅ **{item.get('service', 'Unknown')}**"
                        )
                        st.caption(
                            item.get(
                                "reason",
                                "No applicability rationale supplied.",
                            )
                        )
                else:
                    st.write("None")

            with right:
                st.markdown("**Not Applicable Technologies**")

                if not_applicable:
                    for item in not_applicable:
                        st.markdown(
                            f"➖ **{item.get('service', 'Unknown')}**"
                        )
                        st.caption(
                            item.get(
                                "reason",
                                "No exclusion rationale supplied.",
                            )
                        )
                else:
                    st.write("None")

            st.markdown("**AI-derived Validation Objectives**")

            if not validation_checks:
                st.warning(
                    "No structured validation checks were generated."
                )
            else:
                rows = []

                for check in validation_checks:
                    if not isinstance(check, dict):
                        rows.append({
                            "Technology": "Unknown",
                            "Validation Objective": str(check),
                            "Expected Target": "Not specified",
                            "Requirement Source": "Not specified",
                        })
                        continue

                    rows.append({
                        "Technology":
                            check.get(
                                "technology",
                                "Not specified",
                            ),

                        "Validation Objective":
                            check.get(
                                "validationObjective",
                                "Not specified",
                            ),

                        "Expected Target":
                            check.get(
                                "expectedValue",
                                "Not specified",
                            ),

                        "Requirement Source":
                            check.get(
                                "requirementSource",
                                "Not specified",
                            ),
                    })

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

            related_adrs = control.get(
                "relatedADRs",
                []
            )

            if related_adrs:
                st.markdown("**Related Architecture Decisions**")
                st.write(
                    ", ".join(related_adrs)
                )


def show_dashboard():

    workpaper = st.session_state.get("workpaper")

    if workpaper is None:
        st.error("No audit workpaper available.")

        if st.button("Start New Audit"):
            return "new_audit"

        return None

    summary = workpaper.get("summary", {})
    scope = workpaper.get("auditScope", {})
    findings = workpaper.get("findings", [])
    resources = workpaper.get(
        "resourceEvidence",
        [],
    )
    commentary = st.session_state.get(
        "ai_commentary",
        {}
    )

    dashboard = _calculate_dashboard(
        workpaper
    )

    hero_section(
        title="Executive audit insights in one place.",
        subtitle="Review compliance, control interpretation, and coverage across the completed audit.",
        description=(
            "This dashboard surfaces the most important executive metrics, governance interpretation, "
            "and operational evidence coverage from your completed audit."
        ),
    )
    st.divider()

    st.markdown(
        """
        <div class="section-shell">
            <div class="section-header">
                <h2>Audit scope</h2>
                <span class="step-pill">Executive Overview</span>
            </div>
            <div class="detail-grid">
                <div class="detail-card">
                    <strong>Project</strong>
                    <p>{project}</p>
                </div>
                <div class="detail-card">
                    <strong>Technologies Audited</strong>
                    <p>{technologies}</p>
                </div>
                <div class="detail-card">
                    <strong>Resources Audited</strong>
                    <p>{resource_count}</p>
                </div>
            </div>
        </div>
        """.format(
            project=scope.get(
                "projectId",
                scope.get("project", ""),
            ),
            technologies=", ".join(
                scope.get(
                    "technologies",
                    []
                )
            ),
            resource_count=scope.get(
                "resourceCount",
                len(resources),
            ),
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="metric-grid">
            <div class="metric-card"><strong>Audit Opinion</strong><span>{opinion}</span></div>
            <div class="metric-card"><strong>Compliance</strong><span>{compliance}%</span></div>
            <div class="metric-card"><strong>Technologies</strong><span>{technologies_audited}</span></div>
            <div class="metric-card"><strong>Resources</strong><span>{resources_audited}</span></div>
            <div class="metric-card"><strong>Failed</strong><span>{failed}</span></div>
            <div class="metric-card"><strong>Not Verified</strong><span>{not_verified}</span></div>
        </div>
        """.format(
            opinion=summary.get("overallOpinion", "UNKNOWN"),
            compliance=dashboard["compliance"],
            technologies_audited=summary.get("technologiesAudited", 0),
            resources_audited=summary.get("resourcesAudited", 0),
            failed=summary.get("failed", 0),
            not_verified=summary.get("notVerified", 0),
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("Executive Summary")

    if commentary.get("success"):
        st.markdown(
            """
            <div class="report-panel">
                <p>{summary}</p>
            </div>
            """.format(
                summary=commentary.get(
                    "executiveSummary",
                    "",
                ),
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "Executive commentary is unavailable. "
            "The deterministic audit results remain valid."
        )

    st.divider()

    st.subheader("AI Governance Interpretation")

    st.caption(
        "This view shows how the AI Audit Planner interpreted "
        "the governance documents, determined technology "
        "applicability and generated validation objectives. "
        "Deterministic validators produced the final audit results."
    )

    _display_ai_governance_interpretation(
        st.session_state.get(
            "execution_plan",
            {},
        )
    )

    st.divider()

    st.subheader("Environment Discovery and Audit Coverage")

    discovery_rows = []

    for item in scope.get(
            "discoveredTechnologies",
            []):
        technology = item.get("service")

        discovery_rows.append({
            "Technology": technology,
            "Resources Discovered":
                item.get("resourceCount", 0),
            "Deterministic Audit Executed":
                "Yes"
                if technology in scope.get(
                    "technologies",
                    []
                )
                else "No - scoped by AI only",
        })

    st.dataframe(
        discovery_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Technologies without implemented deterministic validators "
        "remain visible in the AI applicability plan but do not "
        "produce fabricated PASS or FAIL results."
    )

    st.divider()

    st.subheader("Resource Compliance Overview")

    rows = []

    for evidence in resources:
        resource = evidence.get("resource", {})
        name = resource.get(
            "resourceName",
            "Unknown"
        )
        service = resource.get(
            "service",
            "Unknown"
        )

        resource_findings = [
            finding
            for finding in findings
            if finding.get("resourceName") == name
        ]

        rows.append({
            "Technology": service,
            "Resource": name,
            "Passed": len([
                item
                for item in resource_findings
                if item.get("status") == "PASS"
            ]),
            "Failed": len([
                item
                for item in resource_findings
                if item.get("status") == "FAIL"
            ]),
            "Not Verified": len([
                item
                for item in resource_findings
                if item.get("status") == "NOT VERIFIED"
            ]),
            "Overall": (
                "FAIL"
                if any(
                    item.get("status") == "FAIL"
                    for item in resource_findings
                )
                else "NOT VERIFIED"
                if any(
                    item.get("status") == "NOT VERIFIED"
                    for item in resource_findings
                )
                else "PASS"
                if resource_findings
                else "NO APPLICABLE CONTROL"
            ),
        })

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("Control Findings by Technology and Resource")

    for evidence in resources:
        resource = evidence.get("resource", {})
        name = resource.get(
            "resourceName",
            "Unknown"
        )
        service = resource.get(
            "service",
            "Unknown"
        )

        resource_findings = [
            finding
            for finding in findings
            if finding.get("resourceName") == name
        ]

        st.markdown(
            f"### {service} — {name}"
        )

        if not resource_findings:
            st.info(
                "No applicable deterministic controls were "
                "executed for this resource."
            )
            continue

        for finding in resource_findings:
            status = finding.get(
                "status",
                "UNKNOWN"
            )

            with st.expander(
                (
                    f"{finding.get('controlId', 'Control')} — "
                    f"{finding.get('validationObjective', '')}"
                ),
                expanded=True,
            ):
                left, right = st.columns([1, 4])

                with left:
                    if status == "PASS":
                        st.success("PASS")
                    elif status == "FAIL":
                        st.error("FAIL")
                    else:
                        st.warning(status)

                    st.write(
                        f"**Risk:** "
                        f"{finding.get('risk', 'Not Assigned')}"
                    )

                with right:
                    st.write(
                        f"**Control:** "
                        f"{finding.get('controlStatement', '')}"
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
                        f"**Observation:** "
                        f"{finding.get('observation', '')}"
                    )

    st.divider()

    st.subheader("Technical Evidence")

    with st.expander(
        "Normalised Evidence by Resource",
        expanded=False,
    ):
        for evidence in resources:
            resource = evidence.get("resource", {})

            st.markdown(
                f"### {resource.get('service', 'Unknown')} — "
                f"{resource.get('resourceName', 'Unknown')}"
            )
            st.json(
                evidence.get(
                    "technicalEvidence",
                    {}
                )
            )

    with st.expander(
        "AI Audit Execution Plan",
        expanded=False,
    ):
        st.json(
            st.session_state.get(
                "execution_plan",
                {}
            )
        )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "📄 Detailed Report",
            use_container_width=True,
        ):
            return "audit_report"

    with col2:
        if st.button(
            "🧠 AI Commentary",
            use_container_width=True,
        ):
            st.session_state.open_ai_commentary = True
            return "audit_report"

    with col3:
        if st.button(
            "💬 Ask AI Auditor",
            use_container_width=True,
        ):
            return "ask_ai_auditor"

    st.divider()

    if st.button(
        "Start New Audit",
        use_container_width=True,
    ):
        return "new_audit"

    return None
