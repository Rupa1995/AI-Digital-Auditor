from datetime import datetime
import time

import streamlit as st

from services.evidence_service import EvidenceService
from services.gemini_service import GeminiService
from services.governance_knowledge_service import (
    GovernanceKnowledgeService,
)
from services.technology_control_engine import (
    TechnologyControlEngine,
)
from services.workpaper_service import WorkpaperService
from ui.layout import hero_section


def _choose_cloudsql_adr(governance):

    adrs = governance.get("adrs", [])

    for adr in adrs:
        document = adr.get("document", "").lower()
        content = adr.get("content", "").lower()

        if (
            "cloud_sql" in document
            or "cloud sql" in document
            or "cloud sql" in content
        ):
            return adr

    if adrs:
        return adrs[0]

    return {
        "document": "No ADR Available",
        "content": "",
    }


def _build_evidence_objects(
        evidence_service,
        project_id,
        discovery):
    """
    Builds every evidence object supported by the MVP.
    """

    evidence_objects = []

    cloud_sql_instances = (
        discovery.get(
            "resources",
            {}
        ).get(
            "cloudSqlInstances",
            []
        )
    )

    for instance in cloud_sql_instances:
        name = instance.get("name")

        if not name:
            continue

        evidence_objects.append(
            evidence_service.load_live_evidence(
                project_id,
                name
            )
        )

    storage_buckets = (
        discovery.get(
            "resources",
            {}
        ).get(
            "storageBuckets",
            []
        )
    )

    for bucket in storage_buckets:
        bucket_name = (
            bucket.get("name")
            or bucket.get("url")
            or bucket.get("id")
        )

        if not bucket_name:
            continue

        evidence_objects.append(
            evidence_service.load_live_storage_evidence(
                project_id,
                bucket_name
            )
        )

    # IAM is a project-level resource. It is audited even when
    # the service-account count is zero because public project
    # bindings can still exist.
    evidence_objects.append(
        evidence_service.load_live_iam_evidence(
            project_id
        )
    )

    return evidence_objects


def _aggregate_results(
        project_id,
        execution_plan,
        adr,
        resource_workpapers,
        resource_results,
        resource_evidence,
        discovery):

    findings = []
    total_controls = 0
    passed = 0
    failed = 0
    not_verified = 0
    validation_checks = 0
    validation_passed = 0
    validation_failed = 0
    validation_not_verified = 0

    for evidence, results in resource_results:
        summary = results.get("summary", {})

        total_controls += summary.get(
            "controlsEvaluated",
            0,
        )
        passed += summary.get(
            "controlsPassed",
            0,
        )
        failed += summary.get(
            "controlsFailed",
            0,
        )
        not_verified += summary.get(
            "controlsNotVerified",
            0,
        )
        validation_checks += summary.get(
            "validationChecks",
            0,
        )
        validation_passed += summary.get(
            "validationChecksPassed",
            0,
        )
        validation_failed += summary.get(
            "validationChecksFailed",
            0,
        )
        validation_not_verified += summary.get(
            "notVerified",
            0,
        )

        findings.extend(
            results.get(
                "findings",
                []
            )
        )

    if validation_checks:
        evidence_coverage = round(
            (
                (
                    validation_passed
                    + validation_failed
                )
                / validation_checks
            )
            * 100,
            2,
        )
    else:
        evidence_coverage = 0.0

    if failed > 0:
        opinion = "ADVERSE"
    elif not_verified > 0 or validation_not_verified > 0:
        opinion = "QUALIFIED"
    else:
        opinion = "UNQUALIFIED"

    first_workpaper = (
        resource_workpapers[0][1]
        if resource_workpapers
        else {}
    )

    engagement = first_workpaper.get(
        "auditEngagement",
        {
            "auditId": "AUD-2026-0001",
            "auditDate": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "auditType": "Enterprise Technology Audit",
            "auditor": "AI-assisted Technology Auditor",
        },
    )

    technologies_audited = sorted(
        set(
            evidence.get(
                "resource",
                {}
            ).get(
                "service",
                "Unknown"
            )
            for evidence in resource_evidence
        )
    )

    resource_names = [
        evidence.get(
            "resource",
            {}
        ).get(
            "resourceName",
            "Unknown"
        )
        for evidence in resource_evidence
    ]

    return {
        "auditEngagement": engagement,
        "auditScope": {
            "cloudPlatform": "Google Cloud Platform",
            "projectId": project_id,
            "project": project_id,
            "environment": "Production",
            "scope": "Single Project",
            "technologies": technologies_audited,
            "technologyCount": len(technologies_audited),
            "resourceType": "Multi-technology Project Estate",
            "resourceCount": len(resource_evidence),
            "resourcesAudited": resource_names,
            "discoveredTechnologies": discovery.get(
                "services",
                []
            ),
        },
        "governance": {
            "adr": adr,
            "controls": execution_plan.get(
                "controls",
                [],
            ),
        },
        "findings": findings,
        "summary": {
            "uniqueControls": len(
                execution_plan.get(
                    "controls",
                    [],
                )
            ),
            "resourcesAudited": len(resource_evidence),
            "technologiesAudited": len(technologies_audited),
            "controlsEvaluated": total_controls,
            "passed": passed,
            "failed": failed,
            "notVerified": not_verified,
            "validationChecks": validation_checks,
            "validationChecksPassed": validation_passed,
            "validationChecksFailed": validation_failed,
            "evidenceCoverage": evidence_coverage,
            "overallOpinion": opinion,
        },
        "resourceEvidence": resource_evidence,
        "technicalEvidence": {
            "resourcesAudited": len(resource_evidence),
            "technologiesAudited": technologies_audited,
            "evidenceMode": "LIVE_GCLOUD",
        },
        "metadata": {
            "aggregationMode": "PROJECT_MULTI_TECHNOLOGY",
            "collector": "EvidenceService",
            "resourceCount": len(resource_evidence),
        },
    }


def show_audit_progress():

    request = st.session_state.get("audit_request", {})

    if not request:
        st.error("No audit request is available.")
        return "new_audit"

    project_id = request.get("identifier")
    discovery = request.get(
        "environmentDiscovery",
        {}
    )

    hero_section(
        title="Execute the AI-scoped live audit.",
        subtitle="Run live evidence collection, AI governance analysis, and audit aggregation in one flow.",
        description=(
            "This audit execution page validates your cloud project, builds the AI audit plan, "
            "and generates the consolidated workpaper that powers the executive dashboard."
        ),
    )
    st.divider()

    st.markdown(
        """
        <div class="section-shell">
            <div class="section-header">
                <h2>Audit target</h2>
                <span class="step-pill">Live execution</span>
            </div>
            <div class="detail-grid">
                <div class="detail-card"><strong>Requestor</strong><p>{requestor}</p></div>
                <div class="detail-card"><strong>Cloud Platform</strong><p>{platform}</p></div>
                <div class="detail-card"><strong>Project</strong><p>{project}</p></div>
                <div class="detail-card"><strong>Audit Scope</strong><p>{scope}</p></div>
                <div class="detail-card"><strong>Technologies Discovered</strong><p>{technologies}</p></div>
                <div class="detail-card"><strong>MVP Audit Technologies</strong><p>{auditable}</p></div>
            </div>
        </div>
        """.format(
            requestor=request.get("requestor", ""),
            platform=request.get("platform", ""),
            project=project_id,
            scope=request.get("scope", ""),
            technologies=len(discovery.get("services", [])),
            auditable=", ".join(request.get("auditableServices", [])),
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    if st.session_state.get("workpaper") is not None:
        st.success(
            "Enterprise Technology Audit Completed Successfully"
        )

        if st.button(
            "Open Executive Dashboard",
            type="primary",
            use_container_width=True,
        ):
            return "dashboard"

        return None

    try:
        evidence_service = EvidenceService()
        governance_service = GovernanceKnowledgeService()
        gemini_service = GeminiService()
        control_engine = TechnologyControlEngine()
        workpaper_service = WorkpaperService()

        with st.status(
            "Running AI-scoped live audit...",
            expanded=True,
        ) as audit_status:

            st.write("Validating Google Cloud project...")

            project = evidence_service.validate_project(
                project_id
            )

            if not project.get("valid"):
                raise RuntimeError(
                    project.get(
                        "message",
                        "Google Cloud project validation failed.",
                    )
                )

            st.write("Loading enterprise governance...")

            governance = governance_service.load_governance()

            if not governance.get("controls"):
                raise RuntimeError(
                    "No enterprise controls were loaded."
                )

            st.write(
                "AI is analysing discovered technologies and "
                "determining control applicability..."
            )

            discovered_services = {
                "project": project_id,
                "services": discovery.get(
                    "services",
                    []
                ),
            }

            execution_plan = (
                gemini_service.generate_audit_execution_plan(
                    governance,
                    discovered_services,
                )
            )

            if not execution_plan.get("success"):
                raise RuntimeError(
                    execution_plan.get(
                        "message",
                        "AI audit planning failed.",
                    )
                )

            st.session_state.execution_plan = execution_plan

            st.write(
                "Collecting live evidence for Cloud SQL, Cloud Storage and IAM..."
            )

            evidence_objects = _build_evidence_objects(
                evidence_service,
                project_id,
                discovery
            )

            adr = _choose_cloudsql_adr(
                governance
            )

            resource_workpapers = []
            resource_results = []
            resource_evidence = []

            progress = st.progress(0)
            progress_text = st.empty()

            for index, evidence in enumerate(
                    evidence_objects,
                    start=1):

                resource = evidence.get(
                    "resource",
                    {}
                )
                resource_name = resource.get(
                    "resourceName",
                    "Unknown Resource"
                )
                service = resource.get(
                    "service",
                    "Unknown Technology"
                )

                progress_text.write(
                    f"Auditing {service} resource "
                    f"{index} of {len(evidence_objects)}: "
                    f"**{resource_name}**"
                )

                results = control_engine.execute(
                    execution_plan,
                    evidence,
                )

                workpaper = workpaper_service.build_workpaper(
                    evidence,
                    adr,
                    execution_plan["controls"],
                    results,
                )

                resource_results.append(
                    (
                        evidence,
                        results,
                    )
                )
                resource_workpapers.append(
                    (
                        resource_name,
                        workpaper,
                    )
                )
                resource_evidence.append(
                    evidence
                )

                progress.progress(
                    index / len(evidence_objects)
                )

                time.sleep(0.1)

            progress_text.write(
                "All supported resources were assessed."
            )

            consolidated = _aggregate_results(
                project_id=project_id,
                execution_plan=execution_plan,
                adr=adr,
                resource_workpapers=resource_workpapers,
                resource_results=resource_results,
                resource_evidence=resource_evidence,
                discovery=discovery,
            )

            st.session_state.resource_evidence = resource_evidence
            st.session_state.live_evidence = {
                "projectId": project_id,
                "discovery": discovery,
                "resources": resource_evidence,
            }
            st.session_state.audit_results = {
                "findings": consolidated["findings"],
                "summary": consolidated["summary"],
            }
            st.session_state.workpaper = consolidated
            st.session_state.audit_report = consolidated

            st.write(
                "Generating multi-technology executive commentary..."
            )

            commentary = (
                gemini_service.generate_audit_commentary(
                    consolidated
                )
            )

            st.session_state.ai_commentary = commentary

            audit_status.update(
                label=(
                    "AI-scoped multi-technology audit completed"
                ),
                state="complete",
                expanded=False,
            )

    except Exception as ex:
        st.error(
            f"Audit execution failed: {str(ex)}"
        )

        with st.expander("Technical Details"):
            st.code(str(ex))

        if st.button(
            "Return to Audit Setup",
            use_container_width=True,
        ):
            return "new_audit"

        return None

    st.divider()

    summary = st.session_state.workpaper.get(
        "summary",
        {},
    )

    st.success(
        "Enterprise Technology Audit Completed Successfully"
    )

    st.subheader("Consolidated Audit Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Technologies Audited",
        summary.get("technologiesAudited", 0),
    )
    col2.metric(
        "Resources Audited",
        summary.get("resourcesAudited", 0),
    )
    col3.metric(
        "Passed",
        summary.get("passed", 0),
    )
    col4.metric(
        "Failed",
        summary.get("failed", 0),
    )
    col5.metric(
        "Evidence Coverage",
        f"{summary.get('evidenceCoverage', 0)}%",
    )

    opinion = summary.get(
        "overallOpinion",
        "QUALIFIED",
    )

    if opinion == "UNQUALIFIED":
        st.success("Overall Opinion: UNQUALIFIED")
    elif opinion == "QUALIFIED":
        st.warning("Overall Opinion: QUALIFIED")
    else:
        st.error("Overall Opinion: ADVERSE")

    st.divider()

    if st.button(
        "Open Executive Dashboard",
        type="primary",
        use_container_width=True,
    ):
        return "dashboard"

    return None
