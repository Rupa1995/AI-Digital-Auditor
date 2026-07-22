"""
AI Digital Auditor
Live End-to-End Integration Test

Workflow
--------
1. Validate the active gcloud session.
2. Validate the Google Cloud project.
3. Discover live Cloud SQL instances.
4. Select a Cloud SQL instance.
5. Load enterprise governance.
6. Generate the AI Audit Execution Plan.
7. Collect live Cloud SQL evidence.
8. Execute deterministic controls.
9. Build the audit workpaper.
10. Generate executive commentary.
"""

import os
from pprint import pprint

from services.evidence_service import EvidenceService
from services.gemini_service import GeminiService
from services.governance_knowledge_service import (
    GovernanceKnowledgeService
)
from services.technology_control_engine import (
    TechnologyControlEngine
)
from services.workpaper_service import WorkpaperService


def select_instance(
        instances):
    """
    Selects the Cloud SQL instance to audit.

    CLOUDSQL_INSTANCE can be supplied as an environment
    variable. Otherwise, the user selects interactively.
    """

    configured_instance = os.getenv(
        "CLOUDSQL_INSTANCE"
    )

    instance_names = [
        instance.get("name")
        for instance in instances
        if instance.get("name")
    ]

    if configured_instance:
        if configured_instance not in instance_names:
            raise ValueError(
                "CLOUDSQL_INSTANCE does not match any "
                "discovered Cloud SQL instance."
            )

        return configured_instance

    if len(instance_names) == 1:
        return instance_names[0]

    print(
        "\nDiscovered Cloud SQL Instances\n"
    )

    for index, instance_name in enumerate(
            instance_names,
            start=1):
        print(
            f"  {index}. {instance_name}"
        )

    while True:
        selection = input(
            "\nSelect the instance number to audit: "
        ).strip()

        try:
            index = int(selection) - 1

            if 0 <= index < len(
                    instance_names):
                return instance_names[index]

        except ValueError:
            pass

        print(
            "Enter a valid instance number."
        )


def main():
    """
    Executes the live end-to-end audit.
    """

    print(
        "\n================================================"
    )
    print(
        " AI DIGITAL AUDITOR"
    )
    print(
        " LIVE GOOGLE CLOUD AUDIT"
    )
    print(
        "================================================\n"
    )

    evidence_service = EvidenceService()

    #
    # Validate gcloud authentication
    #

    print(
        "Validating gcloud authentication...\n"
    )

    session = (
        evidence_service
        .validate_gcloud_session()
    )

    if not session.get("valid"):
        print(
            "gcloud authentication validation failed."
        )
        print(
            session.get(
                "message",
                "Unknown authentication error."
            )
        )
        return

    print(
        f"Authenticated Account : "
        f"{session['account']}"
    )

    #
    # Resolve and validate project
    #

    project_id = os.getenv(
        "GCP_PROJECT_ID",
        "playground-s-11-31442f33"
    )

    print(
        f"\nValidating Project    : {project_id}\n"
    )

    project = evidence_service.validate_project(
        project_id
    )

    if not project.get("valid"):
        print(
            "Google Cloud project validation failed."
        )
        print(
            project.get(
                "message",
                "Unknown project validation error."
            )
        )
        return

    print(
        f"Project Name          : "
        f"{project['projectName']}"
    )
    print(
        f"Project Number        : "
        f"{project['projectNumber']}"
    )
    print(
        f"Project State         : "
        f"{project['state']}"
    )

    #
    # Live Cloud SQL discovery
    #

    print(
        "\nDiscovering Cloud SQL instances...\n"
    )

    instances = (
        evidence_service
        .list_cloudsql_instances(
            project_id
        )
    )

    if not instances:
        print(
            "No Cloud SQL instances were discovered."
        )
        return

    instance_name = select_instance(
        instances
    )

    print(
        f"\nSelected Instance     : "
        f"{instance_name}"
    )

    #
    # Load enterprise governance
    #

    print(
        "\nLoading Enterprise Governance...\n"
    )

    governance_service = (
        GovernanceKnowledgeService()
    )

    governance = (
        governance_service
        .load_governance()
    )

    print(
        f"Enterprise Controls Loaded : "
        f"{len(governance['controls'])}"
    )

    print(
        f"Enterprise ADRs Loaded     : "
        f"{len(governance['adrs'])}"
    )

    #
    # Discovered services supplied to AI planning
    #

    discovered_services = {
        "project":
            project_id,

        "services": [
            {
                "service":
                    "Cloud SQL"
            }
        ]
    }

    print(
        "\nGenerating AI Audit Execution Plan...\n"
    )

    gemini = GeminiService()

    execution_plan = (
        gemini
        .generate_audit_execution_plan(
            governance,
            discovered_services
        )
    )

    if not execution_plan.get(
            "success"):
        print(
            "\nAI Audit Planning Failed\n"
        )
        pprint(
            execution_plan
        )
        return

    print(
        "\n================================================"
    )
    print(
        " AI GENERATED AUDIT EXECUTION PLAN"
    )
    print(
        "================================================\n"
    )

    pprint(
        execution_plan
    )

    #
    # Collect live evidence
    #

    print(
        "\nCollecting Live Cloud SQL Evidence...\n"
    )

    evidence = (
        evidence_service
        .load_live_evidence(
            project_id,
            instance_name
        )
    )

    print(
        "Live Evidence Collected.\n"
    )

    print(
        "Normalised Technical Evidence\n"
    )

    pprint(
        evidence.get(
            "technicalEvidence",
            {}
        )
    )

    #
    # Execute deterministic controls
    #

    print(
        "\nExecuting Technology Control Engine...\n"
    )

    engine = TechnologyControlEngine()

    audit_results = engine.execute(
        execution_plan,
        evidence
    )

    print(
        "\n================================================"
    )
    print(
        " DETERMINISTIC AUDIT RESULTS"
    )
    print(
        "================================================\n"
    )

    pprint(
        audit_results
    )

    #
    # Build audit workpaper
    #

    print(
        "\nGenerating Audit Workpaper...\n"
    )

    workpaper_service = WorkpaperService()

    if governance.get("adrs"):
        adr = governance["adrs"][0]
    else:
        adr = {
            "document":
                "No ADR Available",
            "content":
                ""
        }

    workpaper = (
        workpaper_service
        .build_workpaper(
            evidence,
            adr,
            execution_plan["controls"],
            audit_results
        )
    )

    print(
        "\n================================================"
    )
    print(
        " AUDIT WORKPAPER"
    )
    print(
        "================================================\n"
    )

    pprint(
        workpaper
    )

    #
    # Generate executive commentary
    #

    print(
        "\nGenerating Executive Commentary...\n"
    )

    commentary = (
        gemini
        .generate_audit_commentary(
            workpaper
        )
    )

    print(
        "\n================================================"
    )
    print(
        " EXECUTIVE COMMENTARY"
    )
    print(
        "================================================\n"
    )

    pprint(
        commentary
    )

    #
    # Final summary
    #

    summary = workpaper["summary"]

    print(
        "\n================================================"
    )
    print(
        " FINAL AUDIT SUMMARY"
    )
    print(
        "================================================\n"
    )

    print(
        f"Controls Evaluated : "
        f"{summary['controlsEvaluated']}"
    )

    print(
        f"Controls Passed    : "
        f"{summary['passed']}"
    )

    print(
        f"Controls Failed    : "
        f"{summary['failed']}"
    )

    print(
        f"Not Verified       : "
        f"{summary['notVerified']}"
    )

    print(
        f"Validation Checks  : "
        f"{summary.get('validationChecks', 0)}"
    )

    print(
        f"Evidence Coverage  : "
        f"{summary.get('evidenceCoverage', 0)}%"
    )

    print(
        f"Overall Opinion    : "
        f"{summary['overallOpinion']}"
    )

    print(
        "\n================================================"
    )
    print(
        " LIVE AUDIT COMPLETED"
    )
    print(
        "================================================\n"
    )


if __name__ == "__main__":
    main()
