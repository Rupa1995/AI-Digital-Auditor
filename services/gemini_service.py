"""
Gemini Service

Purpose
-------
Provides the generative AI capabilities used by the
AI Digital Auditor.

Responsibilities
----------------
1. Generate an AI Audit Execution Plan.
2. Generate executive audit commentary.

Important
---------
Gemini never determines PASS or FAIL.

The deterministic Technology Control Engine performs
all audit validations.
"""

import json
import os

from dotenv import load_dotenv
from google import genai


class GeminiService:
    """
    Gemini AI Service.
    """

    def generate_audit_execution_plan(
            self,
            governance,
            discovered_services):
        """
        Generates the AI Audit Execution Plan.
        """

        try:
            prompt = self._build_audit_planning_prompt(
                governance,
                discovered_services
            )

            print(
                "\n================ PROMPT SENT TO GEMINI ================\n"
            )
            print(prompt)
            print(
                "\n=======================================================\n"
            )

            response = self._call_llm(prompt)

            if "controls" not in response:
                raise Exception(
                    "Gemini response does not contain "
                    "the required 'controls' element."
                )

            response["success"] = True
            return response

        except Exception as ex:
            return {
                "success": False,
                "message":
                    "Unable to generate AI Audit "
                    "Execution Plan.\n\n"
                    f"{str(ex)}"
            }

    def generate_audit_commentary(
            self,
            workpaper):
        """
        Generates executive-level audit commentary.
        """

        try:
            prompt = self._build_commentary_prompt(
                workpaper
            )

            print(
                "\n================ PROMPT SENT TO GEMINI ================\n"
            )
            print(prompt)
            print(
                "\n=======================================================\n"
            )

            response = self._call_llm(prompt)
            response["success"] = True
            return response

        except Exception as ex:
            return {
                "success": False,
                "message":
                    "AI commentary is currently "
                    "unavailable.\n\n"
                    f"{str(ex)}"
            }

    def _build_audit_planning_prompt(
            self,
            governance,
            discovered_services):
        """
        Builds the AI Audit Planning prompt.
        """

        prompt = """
You are a Senior Enterprise IT Infrastructure Auditor.

Your responsibility is to transform enterprise governance
into an executable Audit Execution Plan.

You are provided with:

1. Enterprise Control Library
2. Enterprise Architecture Decision Records
3. Discovered services and resources

IMPORTANT

You are planning the audit.

You are NOT performing the audit.

You MUST NOT determine PASS or FAIL.

PASS, FAIL and NOT VERIFIED are determined later by a
deterministic Technology Control Engine.

==================================================
REQUIREMENT EXTRACTION
==================================================

For EACH Enterprise Control:

1. Read the complete control title, statement and objective.

2. Extract the exact requirement expressed by the control.

3. If the control contains an explicit measurable target,
   use that target directly.

4. Do not require an ADR, standard or policy when the control
   already defines the target state.

5. Use ADRs only when the control is high-level and does not
   define the required implementation or measurable target.

6. Do not invent requirements.

7. Do not claim governance is missing when the control itself
   already contains the requirement.

Example:

Control Statement:
All passwords shall be a minimum of eight characters in length.

Required interpretation:

requirementSource:
CONTROL

extractedRequirement:
All passwords shall be a minimum of eight characters in length.

expectedValue:
8

validationObjective:
MINIMUM_PASSWORD_LENGTH

Example:

Control Statement:
All production databases shall be encrypted.

If an ADR requires CMEK:

requirementSource:
ADR

expectedValue:
CMEK

validationObjective:
DATABASE_ENCRYPTION

==================================================
CONTROL APPLICABILITY
==================================================

For EACH Enterprise Control:

1. Analyse EVERY discovered service or resource.

2. Determine whether the control is Applicable or
   Not Applicable to each discovered item.

3. Explain every applicability decision.

4. Do not omit any discovered item.

5. Apply the control only where the underlying mechanism is
   technically relevant.

6. For enterprise-level data-at-rest encryption controls:

   - interpret the control statement itself; do not require the
     control to name a specific technology;

   - apply the control to every discovered service that stores
     persistent data, including Cloud SQL and Cloud Storage;

   - mark IAM and network-only services Not Applicable to a
     data-at-rest encryption control;

   - generate a separate structured validation check for each
     applicable technology;

   - use validationObjective DATA_AT_REST_ENCRYPTION;

   - for Cloud SQL, use an applicable ADR to determine whether the
     approved target is CMEK;

   - for Cloud Storage, verify that data-at-rest encryption is
     enabled. Do not infer a CMEK mandate unless an authoritative
     control or ADR explicitly requires CMEK for Cloud Storage;

   - one enterprise control may therefore produce multiple
     technology-specific validation checks without duplicating the
     control itself.

Example:

Control Statement:
Data at rest must be encrypted using enterprise-approved encryption mechanisms.

Discovered Cloud SQL:
Applicable. Generate DATA_AT_REST_ENCRYPTION and use the relevant
ADR to determine the approved database encryption target.

Discovered Cloud Storage:
Applicable. Generate DATA_AT_REST_ENCRYPTION and verify that the
bucket uses platform encryption at rest; use CMEK only when an
authoritative source explicitly requires it.

Discovered IAM:
Not Applicable because IAM is an access-control service rather than
a persistent data repository for this control.

7. For identity and authentication controls:

   - distinguish Cloud IAM and service-account controls from
     password-bearing identity controls;

   - Cloud IAM service accounts do not use passwords and must
     not be assessed against password-length requirements;

   - controls prohibiting public principals apply to project IAM
     bindings containing allUsers or allAuthenticatedUsers;

   - controls restricting excessive service-account privilege
     apply to project IAM role bindings assigned to service
     accounts;

   - a discovered IAM service represents the project IAM policy
     and service-account estate, even when the service-account
     resource count is zero;

   - when an enterprise control explicitly mentions allUsers,
     allAuthenticatedUsers, public IAM principals or unrestricted
     public IAM access, mark IAM as applicable and generate one
     project-level validation check;

   - when an enterprise control explicitly prohibits service
     accounts from receiving the Owner role, mark IAM as
     applicable and generate one project-level validation check;

   - do not mark IAM controls Not Applicable merely because IAM is
     a platform capability rather than a deployable workload
     service;

   - identify every discovered technology or resource that
     supports password-based authentication;

   - password-bearing identities may include database users,
     operating-system users, directory users, application
     users, local administrative users and identity-provider
     users;

   - do not limit password controls to human identity
     platforms;

   - if a discovered technology supports local or native
     password authentication, the password control is
     applicable;

   - Cloud SQL is applicable when native database users can
     authenticate using passwords;

   - do not assume a password control is not applicable
     merely because IAM is also available;

   - service accounts, workload identities, API tokens,
     certificates, cryptographic keys and OAuth tokens are
     not passwords and must not be evaluated against
     password-length controls;

   - when identities are federated, identify the
     authoritative identity provider and generate the test
     against that provider only when evidence is available;

   - explain every applicability decision using the actual
     authentication mechanism.

Example:

Control Statement:
All passwords shall be a minimum of eight characters in length.

Cloud SQL:
Applicable when native database users authenticate by
password.

Required validation output:

validationObjective:
MINIMUM_PASSWORD_LENGTH

technology:
Cloud SQL

resourceType:
Database User

identityType:
Local Database User

requirementSource:
CONTROL

extractedRequirement:
All passwords shall be a minimum of eight characters in length.

expectedValue:
8

Example:

Control Statement:
No Google Cloud project IAM policy shall grant access to
allUsers or allAuthenticatedUsers unless an approved exception
has been recorded.

IAM:
Applicable because the project IAM policy can contain public
principals.

Required validation output:

validationObjective:
PUBLIC_IAM_ACCESS

technology:
IAM

resourceType:
Project IAM Policy

identityType:
Public Principal

requirementSource:
CONTROL

expectedValue:
NO_PUBLIC_PRINCIPALS

Example:

Control Statement:
Google Cloud service accounts shall not be assigned the project
Owner role.

IAM:
Applicable because project IAM bindings assign roles to service
accounts.

Required validation output:

validationObjective:
SERVICE_ACCOUNT_OWNER_ROLE

technology:
IAM

resourceType:
Project IAM Policy

identityType:
Service Account

requirementSource:
CONTROL

expectedValue:
NO_SERVICE_ACCOUNT_OWNER

==================================================
VALIDATION OBJECTIVE DESIGN
==================================================

For every applicable control and resource:

1. Determine the single required target state.

2. Generate the minimum number of non-overlapping validation
   objectives needed to determine whether that target state
   is satisfied.

3. Do not create multiple PASS or FAIL outcomes for evidence
   attributes that support the same control outcome.

4. Supporting information such as key references, metadata,
   configuration exports and IAM mappings belongs under
   evidenceRequired.

5. Generate one concise validationObjective for each
   independent control outcome.

6. The validationObjective must be technology-neutral and
   written in UPPER_SNAKE_CASE.

7. Derive the validationObjective dynamically from the
   control and governance.

8. Do not rely on a predefined list of validation
   objectives.

9. Also identify:

   - technology
   - resourceType
   - identityType when relevant
   - requirementSource
   - extractedRequirement
   - expectedValue
   - description

10. Every validation check must be specific to one
    applicable service or resource.

11. If no deterministic implementation exists, still
    generate the correct validationObjective. The
    deterministic engine will return NOT VERIFIED.

==================================================
ENTERPRISE CONTROL LIBRARY
==================================================

"""

        for library in governance.get("controls", []):
            prompt += f"""

Document
--------
{library.get("document", "Unknown Control Library")}

"""

            for control in library.get("controls", []):
                prompt += f"""

Control ID
----------
{control.get("id", "")}

Title
-----
{control.get("title", "")}

Statement
---------
{control.get("statement", "")}

Objective
---------
{control.get("objective", "")}

--------------------------------------------------

"""

        prompt += """

==================================================
ENTERPRISE ARCHITECTURE DECISION RECORDS
==================================================

"""

        for adr in governance.get("adrs", []):
            prompt += f"""

Document
--------
{adr.get("document", "Unknown ADR")}

Content
-------
{adr.get("content", "")}

--------------------------------------------------

"""

        prompt += """

==================================================
DISCOVERED ENVIRONMENT
==================================================

"""

        for service in discovered_services.get("services", []):
            prompt += f"""

Service
-------
{service.get("service", "")}

Resource Count
--------------
{service.get("resourceCount", "Unknown")}

Discovered
----------
{service.get("discovered", True)}

--------------------------------------------------

"""

        prompt += """

==================================================
EXPECTED JSON RESPONSE
==================================================

Return ONLY valid JSON.

The response must contain one entry for every Enterprise
Control.

For every Enterprise Control, serviceAnalysis must contain
one entry for every discovered service.

Do not omit controls.

Do not omit services.

Do not create controls that do not exist in the Enterprise
Control Library.

Use the complete control statement from the Enterprise
Control Library in controlStatement.

{
  "controls": [
    {
      "controlId": "",
      "controlStatement": "",
      "serviceAnalysis": [
        {
          "service": "",
          "applicable": true,
          "reason": ""
        }
      ],
      "selectedServices": [
        ""
      ],
      "relatedADRs": [
        ""
      ],
      "targetState": "",
      "executionPlan": {
        "auditProcedures": [
          ""
        ],
        "evidenceRequired": [
          ""
        ],
        "validationChecks": [
          {
            "validationObjective": "",
            "technology": "",
            "resourceType": "",
            "identityType": "",
            "requirementSource": "",
            "extractedRequirement": "",
            "description": "",
            "expectedValue": ""
          }
        ]
      },
      "governanceFindings": [
        ""
      ]
    }
  ]
}

Do not return markdown.

Do not return code blocks.

Do not include explanations outside JSON.
"""

        return prompt

    def _build_commentary_prompt(
            self,
            workpaper):
        """
        Builds a resource-aware executive commentary prompt.

        The context is generated dynamically from the completed
        workpaper and supports one resource, many resources and,
        later, multiple technologies.
        """

        context = self._build_commentary_context(
            workpaper
        )

        prompt = f"""
You are a Senior Enterprise Technology Auditor.

IMPORTANT

The audit has already been completed.

You are NOT auditing the environment.

All PASS, FAIL and NOT VERIFIED outcomes were determined
by a deterministic Technology Control Engine.

You MUST NOT change, reinterpret or override any audit result.

Your responsibility is ONLY to prepare executive commentary
from the structured completed-audit context supplied below.

==================================================
COMMENTARY RULES
==================================================

1. Write dynamically from the supplied counts and resource data.

2. Never assume a fixed number of resources.

3. Never assume the audit contains only one technology.

4. State the actual number of resources assessed when that
   information is available.

5. When results differ across resources:

   - describe the mixed outcome explicitly;
   - state how many resources passed, failed or were not verified;
   - do not generalise a PASS, FAIL or NOT VERIFIED result to the
     entire environment unless it applies to every relevant
     resource.

6. Distinguish clearly between:

   - systemic issues affecting all assessed resources;
   - widespread issues affecting most resources;
   - isolated exceptions affecting only some resources;
   - evidence gaps resulting in NOT VERIFIED outcomes;
   - controls that consistently passed.

7. Do not say that a requirement is met when any relevant
   resource is FAIL or NOT VERIFIED.

8. Do not say that all resources require remediation unless all
   relevant resources failed that control.

9. Recommendations must target only the affected resources or
   the systemic population identified by the deterministic
   results.

10. Use resource names only when useful for highlighting
    exceptions or priority remediation. Avoid producing an
    unnecessarily long inventory in the executive summary.

11. Treat NOT VERIFIED as an evidence or assurance limitation,
    not automatically as a control failure.

12. Do not invent percentages, resource counts, technologies,
    findings, business impacts or governance requirements.

13. Use the overall opinion exactly as supplied.

14. Keep the language suitable for executives, enterprise
    architects, risk teams and technology management.

15. Explicitly distinguish enterprise controls from
    technology-specific controls:

    - Enterprise controls express the organisation-wide control
      intent and may apply across multiple technologies.
    - Technology-specific controls apply to a particular platform
      or resource type.
    - Deterministic findings remain resource- and
      technology-specific.

16. When an enterprise control applies across multiple
    technologies:

    - name the enterprise control;
    - state which discovered technologies it was applied to;
    - describe the aggregate result accurately;
    - identify technology-specific or resource-specific exceptions;
    - do not imply that one technology result automatically applies
      to every technology.

17. Where EC-* controls exist, the executive summary must explain
    that AI interpreted the enterprise control statement and
    translated it into technology-specific validation objectives.
    Do not claim that AI determined PASS or FAIL.

18. Do not describe an EC-* control as fully satisfied when any
    applicable resource is FAIL or NOT VERIFIED.

==================================================
COMPLETED AUDIT COMMENTARY CONTEXT
==================================================

{json.dumps(context, indent=2, default=str)}

==================================================
REQUIRED OUTPUT
==================================================

Prepare:

1. Executive Summary
   - State the audit scope dynamically.
   - State the number of resources and technologies assessed.
   - State the overall opinion.
   - Summarise the dominant cross-resource outcomes.
   - Identify any enterprise-level controls interpreted by AI and
     the technologies to which they were applied.
   - Explain that deterministic validators, not AI, produced the
     PASS, FAIL and NOT VERIFIED outcomes.

2. Positive Observations
   - Include only controls or patterns supported by PASS results.
   - Qualify partial success accurately.

3. Key Risks
   - Prioritise systemic and high-risk failures.
   - Identify affected resource counts.
   - Include evidence limitations where material.

4. Business Impact
   - Explain the impact of the supplied findings without
     inventing unsupported consequences.

5. Management Recommendations
   - Prioritise remediation based on risk and prevalence.
   - Target affected resources accurately.

6. Overall Auditor Commentary
   - Provide a balanced, resource-aware conclusion.
   - Distinguish systemic issues, isolated exceptions and
     evidence gaps.

Return ONLY valid JSON using this exact structure:

{{
  "executiveSummary": "",
  "positiveObservations": [],
  "keyRisks": [],
  "businessImpact": "",
  "managementRecommendations": [],
  "overallCommentary": ""
}}

Do not return markdown.

Do not return code blocks.

Do not include explanations outside JSON.

Do not modify the deterministic audit findings.
"""

        return prompt

    def _build_commentary_context(
            self,
            workpaper):
        """
        Creates a scalable structured context for executive
        commentary.

        The method aggregates results across any number of
        resources and validation objectives before sending the
        context to Gemini.
        """

        summary = workpaper.get(
            "summary",
            {}
        )

        scope = workpaper.get(
            "auditScope",
            {}
        )

        findings = workpaper.get(
            "findings",
            []
        )

        resource_evidence = workpaper.get(
            "resourceEvidence",
            []
        )

        governance = workpaper.get(
            "governance",
            {}
        )

        adr = governance.get(
            "adr",
            {}
        )

        adr_id, adr_title = self._derive_adr_identity(
            adr
        )

        resource_names = self._collect_resource_names(
            scope=scope,
            findings=findings,
            resource_evidence=resource_evidence
        )

        technologies = self._collect_technologies(
            scope=scope,
            findings=findings,
            resource_evidence=resource_evidence
        )

        resource_summary = self._build_resource_summary(
            resource_names,
            findings
        )

        control_summary = self._build_control_summary(
            findings,
            len(resource_names)
        )

        risk_summary = self._build_risk_summary(
            findings
        )

        representative_findings = (
            self._build_representative_findings(
                findings,
                limit=30
            )
        )

        governance_controls = governance.get(
            "controls",
            []
        )

        governance_interpretation = (
            self._build_governance_interpretation(
                governance_controls,
                findings
            )
        )

        resources_audited = summary.get(
            "resourcesAudited"
        )

        if resources_audited is None:
            resources_audited = scope.get(
                "resourceCount"
            )

        if resources_audited is None:
            resources_audited = len(
                resource_names
            )

        if (
            not resources_audited
            and findings
        ):
            resources_audited = 1

        return {
            "auditScope": {
                "cloudPlatform":
                    scope.get(
                        "cloudPlatform",
                        "Not Specified"
                    ),

                "projectId":
                    scope.get(
                        "projectId",
                        scope.get(
                            "project",
                            "Not Specified"
                        )
                    ),

                "scope":
                    scope.get(
                        "scope",
                        "Not Specified"
                    ),

                "environment":
                    scope.get(
                        "environment",
                        "Not Specified"
                    ),

                "technologies":
                    technologies,

                "technologyCount":
                    len(technologies),

                "resourcesAudited":
                    resources_audited,

                "resourceNames":
                    resource_names
            },

            "governance": {
                "adrId":
                    adr_id,

                "adrTitle":
                    adr_title,

                "adrDocument":
                    adr.get(
                        "document",
                        "Not Available"
                    ),

                "interpretation":
                    governance_interpretation
            },

            "overallSummary": {
                "uniqueControls":
                    summary.get(
                        "uniqueControls",
                        self._count_unique_controls(
                            findings
                        )
                    ),

                "controlEvaluations":
                    summary.get(
                        "controlsEvaluated",
                        len(findings)
                    ),

                "passed":
                    summary.get(
                        "passed",
                        self._count_status(
                            findings,
                            "PASS"
                        )
                    ),

                "failed":
                    summary.get(
                        "failed",
                        self._count_status(
                            findings,
                            "FAIL"
                        )
                    ),

                "notVerified":
                    summary.get(
                        "notVerified",
                        self._count_status(
                            findings,
                            "NOT VERIFIED"
                        )
                    ),

                "validationChecks":
                    summary.get(
                        "validationChecks",
                        len(findings)
                    ),

                "evidenceCoverage":
                    summary.get(
                        "evidenceCoverage",
                        0
                    ),

                "overallOpinion":
                    summary.get(
                        "overallOpinion",
                        "QUALIFIED"
                    )
            },

            "riskSummary":
                risk_summary,

            "resourceSummary":
                resource_summary,

            "controlOutcomeSummary":
                control_summary,

            "representativeFindings":
                representative_findings,

            "contextNotes": {
                "resourceSummaryComplete":
                    True,

                "controlSummaryComplete":
                    True,

                "representativeFindingLimit":
                    30,

                "representativeFindingsTruncated":
                    len(findings) > 30
            }
        }

    def _collect_resource_names(
            self,
            scope,
            findings,
            resource_evidence):
        """
        Returns all unique audited resource names.
        """

        names = []

        for resource in resource_evidence:
            name = resource.get(
                "resourceName"
            )

            if not name:
                name = (
                    resource.get(
                        "resource",
                        {}
                    ).get(
                        "resourceName"
                    )
                )

            if name and name not in names:
                names.append(name)

        for finding in findings:
            name = finding.get(
                "resourceName",
                finding.get(
                    "instanceName"
                )
            )

            if name and name not in names:
                names.append(name)

        scoped_resources = scope.get(
            "resourcesAudited",
            []
        )

        if isinstance(
                scoped_resources,
                list):
            for name in scoped_resources:
                if name and name not in names:
                    names.append(name)

        single_name = scope.get(
            "resourceName",
            scope.get(
                "instanceName"
            )
        )

        if single_name and single_name not in names:
            names.append(single_name)

        return names

    def _collect_technologies(
            self,
            scope,
            findings,
            resource_evidence):
        """
        Returns all unique technologies represented by the
        completed audit.
        """

        technologies = []

        scoped_technology = scope.get(
            "service",
            scope.get(
                "technology"
            )
        )

        if scoped_technology:
            technologies.append(
                scoped_technology
            )

        for finding in findings:
            technology = finding.get(
                "technology",
                finding.get(
                    "service"
                )
            )

            if (
                technology
                and technology not in technologies
            ):
                technologies.append(
                    technology
                )

        for resource in resource_evidence:
            resource_data = resource.get(
                "resource",
                {}
            )

            technology = resource_data.get(
                "service",
                resource_data.get(
                    "resourceType"
                )
            )

            if (
                technology
                and technology not in technologies
            ):
                technologies.append(
                    technology
                )

        return technologies

    def _build_governance_interpretation(
            self,
            governance_controls,
            findings):
        """
        Summarises how AI interpreted enterprise and
        technology-specific controls and how deterministic
        outcomes were distributed across technologies.
        """

        interpretation = {
            "enterpriseControls": [],
            "technologyControls": [],
            "enterpriseControlCount": 0,
            "technologyControlCount": 0
        }

        for control in governance_controls:
            control_id = control.get(
                "controlId",
                "Unknown Control"
            )

            control_statement = control.get(
                "controlStatement",
                ""
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

            applicable_services = self._unique_values(
                [
                    item.get("service")
                    for item in service_analysis
                    if item.get("applicable")
                ]
            )

            not_applicable_services = self._unique_values(
                [
                    item.get("service")
                    for item in service_analysis
                    if item.get("applicable") is False
                ]
            )

            control_findings = [
                finding
                for finding in findings
                if finding.get("controlId") == control_id
            ]

            technology_outcomes = {}

            for finding in control_findings:
                technology = finding.get(
                    "technology",
                    finding.get(
                        "service",
                        "Unknown Technology"
                    )
                )

                if technology not in technology_outcomes:
                    technology_outcomes[technology] = {
                        "passed": 0,
                        "failed": 0,
                        "notVerified": 0,
                        "affectedResources": []
                    }

                status = finding.get(
                    "status",
                    "NOT VERIFIED"
                )

                if status == "PASS":
                    technology_outcomes[technology]["passed"] += 1
                elif status == "FAIL":
                    technology_outcomes[technology]["failed"] += 1
                else:
                    technology_outcomes[technology]["notVerified"] += 1

                resource_name = finding.get(
                    "resourceName"
                )

                if resource_name:
                    technology_outcomes[technology][
                        "affectedResources"
                    ].append(resource_name)

            for outcome in technology_outcomes.values():
                outcome["affectedResources"] = (
                    self._unique_values(
                        outcome["affectedResources"]
                    )
                )

            item = {
                "controlId":
                    control_id,

                "controlStatement":
                    control_statement,

                "controlType":
                    (
                        "ENTERPRISE"
                        if str(control_id).startswith("EC-")
                        else "TECHNOLOGY"
                    ),

                "applicableTechnologies":
                    applicable_services,

                "notApplicableTechnologies":
                    not_applicable_services,

                "aiDerivedValidationObjectives":
                    self._unique_values(
                        [
                            check.get(
                                "validationObjective"
                            )
                            for check in validation_checks
                            if isinstance(check, dict)
                        ]
                    ),

                "technologyOutcomes":
                    technology_outcomes
            }

            if item["controlType"] == "ENTERPRISE":
                interpretation["enterpriseControls"].append(
                    item
                )
            else:
                interpretation["technologyControls"].append(
                    item
                )

        interpretation["enterpriseControlCount"] = len(
            interpretation["enterpriseControls"]
        )

        interpretation["technologyControlCount"] = len(
            interpretation["technologyControls"]
        )

        return interpretation

    def _build_resource_summary(
            self,
            resource_names,
            findings):
        """
        Builds PASS, FAIL and NOT VERIFIED totals per
        resource.
        """

        summary = []

        if not resource_names and findings:
            resource_names = [
                "Audited Resource"
            ]

        for resource_name in resource_names:
            resource_findings = []

            for finding in findings:
                finding_resource = finding.get(
                    "resourceName",
                    finding.get(
                        "instanceName"
                    )
                )

                if finding_resource is None:
                    if len(resource_names) == 1:
                        resource_findings.append(
                            finding
                        )

                elif finding_resource == resource_name:
                    resource_findings.append(
                        finding
                    )

            statuses = [
                finding.get(
                    "status",
                    "NOT VERIFIED"
                )
                for finding in resource_findings
            ]

            if "FAIL" in statuses:
                overall_status = "FAIL"

            elif "NOT VERIFIED" in statuses:
                overall_status = (
                    "NOT VERIFIED"
                )

            elif statuses:
                overall_status = "PASS"

            else:
                overall_status = (
                    "NO RESULTS"
                )

            summary.append({
                "resourceName":
                    resource_name,

                "evaluations":
                    len(resource_findings),

                "passed":
                    statuses.count(
                        "PASS"
                    ),

                "failed":
                    statuses.count(
                        "FAIL"
                    ),

                "notVerified":
                    statuses.count(
                        "NOT VERIFIED"
                    ),

                "overallStatus":
                    overall_status,

                "failedObjectives":
                    self._unique_values(
                        [
                            finding.get(
                                "validationObjective"
                            )
                            for finding in resource_findings
                            if finding.get(
                                "status"
                            ) == "FAIL"
                        ]
                    ),

                "notVerifiedObjectives":
                    self._unique_values(
                        [
                            finding.get(
                                "validationObjective"
                            )
                            for finding in resource_findings
                            if finding.get(
                                "status"
                            ) == "NOT VERIFIED"
                        ]
                    )
            })

        return summary

    def _build_control_summary(
            self,
            findings,
            total_resources):
        """
        Aggregates deterministic outcomes by control and
        validation objective.
        """

        groups = {}

        for finding in findings:
            control_id = finding.get(
                "controlId",
                "Unknown Control"
            )

            objective = finding.get(
                "validationObjective",
                "Unknown Objective"
            )

            key = (
                control_id,
                objective
            )

            if key not in groups:
                groups[key] = {
                    "controlId":
                        control_id,

                    "controlStatement":
                        finding.get(
                            "controlName",
                            finding.get(
                                "controlStatement",
                                "Unknown Control"
                            )
                        ),

                    "validationObjective":
                        objective,

                    "risk":
                        finding.get(
                            "risk",
                            "Not Assigned"
                        ),

                    "requirementSource":
                        finding.get(
                            "requirementSource",
                            "Not Specified"
                        ),

                    "expected":
                        finding.get(
                            "expected",
                            "Not Specified"
                        ),

                    "passedResources":
                        [],

                    "failedResources":
                        [],

                    "notVerifiedResources":
                        []
                }

            resource_name = finding.get(
                "resourceName",
                finding.get(
                    "instanceName",
                    "Audited Resource"
                )
            )

            status = finding.get(
                "status",
                "NOT VERIFIED"
            )

            if status == "PASS":
                groups[key][
                    "passedResources"
                ].append(resource_name)

            elif status == "FAIL":
                groups[key][
                    "failedResources"
                ].append(resource_name)

            else:
                groups[key][
                    "notVerifiedResources"
                ].append(resource_name)

        result = []

        for group in groups.values():
            group["passedResources"] = (
                self._unique_values(
                    group[
                        "passedResources"
                    ]
                )
            )

            group["failedResources"] = (
                self._unique_values(
                    group[
                        "failedResources"
                    ]
                )
            )

            group[
                "notVerifiedResources"
            ] = self._unique_values(
                group[
                    "notVerifiedResources"
                ]
            )

            passed = len(
                group[
                    "passedResources"
                ]
            )

            failed = len(
                group[
                    "failedResources"
                ]
            )

            not_verified = len(
                group[
                    "notVerifiedResources"
                ]
            )

            evaluated_resources = (
                passed
                + failed
                + not_verified
            )

            group["resourceCounts"] = {
                "evaluated":
                    evaluated_resources,

                "passed":
                    passed,

                "failed":
                    failed,

                "notVerified":
                    not_verified
            }

            if (
                total_resources > 0
                and failed == total_resources
            ):
                pattern = (
                    "SYSTEMIC_FAILURE"
                )

            elif (
                total_resources > 0
                and passed == total_resources
            ):
                pattern = (
                    "CONSISTENT_PASS"
                )

            elif (
                total_resources > 0
                and not_verified == total_resources
            ):
                pattern = (
                    "SYSTEMIC_EVIDENCE_GAP"
                )

            elif failed > 0:
                pattern = (
                    "PARTIAL_FAILURE"
                )

            elif not_verified > 0:
                pattern = (
                    "PARTIAL_EVIDENCE_GAP"
                )

            elif passed > 0:
                pattern = (
                    "CONSISTENT_PASS"
                )

            else:
                pattern = (
                    "NO_RESULT"
                )

            group["crossResourcePattern"] = (
                pattern
            )

            result.append(group)

        result.sort(
            key=lambda item: (
                self._risk_rank(
                    item.get(
                        "risk"
                    )
                ),
                item.get(
                    "controlId",
                    ""
                ),
                item.get(
                    "validationObjective",
                    ""
                )
            )
        )

        return result

    def _build_risk_summary(
            self,
            findings):
        """
        Aggregates failed findings by risk rating.
        """

        summary = {
            "HIGH": {
                "failedEvaluations": 0,
                "affectedResources": []
            },

            "MEDIUM": {
                "failedEvaluations": 0,
                "affectedResources": []
            },

            "LOW": {
                "failedEvaluations": 0,
                "affectedResources": []
            },

            "NOT_ASSIGNED": {
                "failedEvaluations": 0,
                "affectedResources": []
            }
        }

        for finding in findings:
            if finding.get(
                    "status") != "FAIL":
                continue

            risk = str(
                finding.get(
                    "risk",
                    "NOT_ASSIGNED"
                )
            ).upper()

            if risk not in summary:
                risk = "NOT_ASSIGNED"

            summary[risk][
                "failedEvaluations"
            ] += 1

            resource_name = finding.get(
                "resourceName",
                finding.get(
                    "instanceName",
                    "Audited Resource"
                )
            )

            summary[risk][
                "affectedResources"
            ].append(resource_name)

        for value in summary.values():
            value[
                "affectedResources"
            ] = self._unique_values(
                value[
                    "affectedResources"
                ]
            )

            value[
                "affectedResourceCount"
            ] = len(
                value[
                    "affectedResources"
                ]
            )

        return summary

    def _build_representative_findings(
            self,
            findings,
            limit):
        """
        Supplies concise finding details to support accurate
        narrative generation without requiring an unbounded
        prompt.
        """

        ordered = sorted(
            findings,
            key=lambda finding: (
                self._status_rank(
                    finding.get(
                        "status"
                    )
                ),
                self._risk_rank(
                    finding.get(
                        "risk"
                    )
                ),
                finding.get(
                    "resourceName",
                    finding.get(
                        "instanceName",
                        ""
                    )
                ),
                finding.get(
                    "controlId",
                    ""
                )
            )
        )

        result = []

        for finding in ordered[
                :limit]:
            result.append({
                "resourceName":
                    finding.get(
                        "resourceName",
                        finding.get(
                            "instanceName",
                            "Audited Resource"
                        )
                    ),

                "controlId":
                    finding.get(
                        "controlId",
                        "Unknown Control"
                    ),

                "control":
                    finding.get(
                        "controlName",
                        finding.get(
                            "controlStatement",
                            "Unknown Control"
                        )
                    ),

                "validationObjective":
                    finding.get(
                        "validationObjective",
                        "Not Specified"
                    ),

                "status":
                    finding.get(
                        "status",
                        "NOT VERIFIED"
                    ),

                "risk":
                    finding.get(
                        "risk",
                        "Not Assigned"
                    ),

                "requirementSource":
                    finding.get(
                        "requirementSource",
                        "Not Specified"
                    ),

                "expected":
                    finding.get(
                        "expected",
                        "Not Specified"
                    ),

                "actual":
                    finding.get(
                        "actual",
                        "Not Specified"
                    ),

                "observation":
                    finding.get(
                        "observation",
                        "No observation recorded."
                    ),

                "recommendation":
                    (
                        finding.get(
                            "recommendation"
                        )
                        or
                        "No remediation required."
                    )
            })

        return result

    def _derive_adr_identity(
            self,
            adr):
        """
        Derives ADR ID and title across current and legacy
        governance schemas.
        """

        document = adr.get(
            "document",
            "No ADR Available"
        )

        content = adr.get(
            "content",
            ""
        )

        adr_id = adr.get(
            "id"
        )

        if not adr_id:
            adr_id = document.split(
                "_",
                1
            )[0]

        adr_title = adr.get(
            "title"
        )

        if not adr_title:
            adr_title = document

            for line in content.splitlines():
                line = line.strip()

                if not line.startswith(
                        "ADR-"):
                    continue

                if "–" in line:
                    adr_title = line.split(
                        "–",
                        1
                    )[1].strip()
                    break

                if " - " in line:
                    adr_title = line.split(
                        " - ",
                        1
                    )[1].strip()
                    break

        return adr_id, adr_title

    def _count_unique_controls(
            self,
            findings):
        """
        Counts unique control IDs in the findings.
        """

        return len(
            self._unique_values(
                [
                    finding.get(
                        "controlId"
                    )
                    for finding in findings
                ]
            )
        )

    def _count_status(
            self,
            findings,
            status):
        """
        Counts findings with the supplied deterministic
        status.
        """

        return len(
            [
                finding
                for finding in findings
                if finding.get(
                    "status"
                ) == status
            ]
        )

    def _unique_values(
            self,
            values):
        """
        Returns ordered unique non-empty values.
        """

        result = []

        for value in values:
            if (
                value is not None
                and value != ""
                and value not in result
            ):
                result.append(value)

        return result

    def _status_rank(
            self,
            status):
        """
        Sorts FAIL first, then NOT VERIFIED, then PASS.
        """

        ranks = {
            "FAIL": 0,
            "NOT VERIFIED": 1,
            "PASS": 2
        }

        return ranks.get(
            status,
            3
        )

    def _risk_rank(
            self,
            risk):
        """
        Sorts higher risks first.
        """

        ranks = {
            "HIGH": 0,
            "MEDIUM": 1,
            "LOW": 2
        }

        return ranks.get(
            str(
                risk
            ).upper(),
            3
        )

    def _call_llm(
            self,
            prompt):
        """
        Calls Google Gemini using the official SDK.
        """

        load_dotenv()

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise Exception(
                "GEMINI_API_KEY was not found "
                "in the .env file."
            )

        model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.0-flash"
        )

        client = genai.Client(
            api_key=api_key
        )

        response = client.models.generate_content(
            model=model,
            contents=prompt
        )

        if not response.text:
            raise Exception(
                "Gemini returned an empty response."
            )

        text = response.text.strip()

        if text.startswith("```json"):
            text = text.replace(
                "```json",
                "",
                1
            )

        if text.startswith("```"):
            text = text.replace(
                "```",
                "",
                1
            )

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)

        except json.JSONDecodeError as ex:
            return {
                "rawResponse": text,
                "parseError": str(ex)
            }
