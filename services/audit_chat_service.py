"""
Audit Chat Service

Provides natural-language question answering over a completed
single-resource or multi-resource enterprise audit workpaper.
"""

import os

from dotenv import load_dotenv
from google import genai


class AuditChatService:

    def answer_question(
            self,
            workpaper,
            question):

        try:
            prompt = self._build_prompt(
                workpaper,
                question
            )

            response = self._call_llm(
                prompt
            )

            return {
                "success": True,
                "answer": response
            }

        except Exception as ex:
            return {
                "success": False,
                "message":
                    "AI Auditor is currently unavailable.\n\n"
                    f"Reason: {str(ex)}"
            }

    def _build_prompt(
            self,
            workpaper,
            question):

        summary = workpaper.get(
            "summary",
            {}
        )
        findings = workpaper.get(
            "findings",
            []
        )
        resources = workpaper.get(
            "resourceEvidence",
            []
        )
        adr = workpaper.get(
            "governance",
            {}
        ).get(
            "adr",
            {}
        )

        adr_id, adr_title = self._derive_adr_identity(
            adr
        )

        prompt = f"""
You are a Senior Enterprise Technology Auditor.

The audit has already been completed.

You are NOT performing another audit.

You MUST NOT change any audit findings.

Answer ONLY using the supplied audit workpaper.

If the answer cannot be determined, reply exactly:

"The available audit evidence does not contain sufficient information to answer this question."

====================================================

CONSOLIDATED AUDIT SUMMARY

Resources Audited:
{summary.get("resourcesAudited", len(resources))}

Unique Controls:
{summary.get("uniqueControls", 0)}

Control Evaluations:
{summary.get("controlsEvaluated", 0)}

Evaluations Passed:
{summary.get("passed", 0)}

Evaluations Failed:
{summary.get("failed", 0)}

Not Verified:
{summary.get("notVerified", 0)}

Evidence Coverage:
{summary.get("evidenceCoverage", 0)}%

Overall Opinion:
{summary.get("overallOpinion", "UNKNOWN")}

====================================================

ARCHITECTURE DECISION RECORD

ID:
{adr_id}

Title:
{adr_title}

====================================================

RESOURCE EVIDENCE

"""

        for resource in resources:
            technical = resource.get(
                "technicalEvidence",
                {}
            )

            prompt += f"""

Resource:
{resource.get("resourceName", "Unknown")}

Database Version:
{technical.get("databaseVersion", "Not Available")}

Availability:
{technical.get("availabilityType", "Not Available")}

Encryption:
{technical.get("encryption", "Not Available")}

Minimum Password Length:
{technical.get("minimumPasswordLength", "Not Available")}

Backup Enabled:
{technical.get("backupEnabled", "Not Available")}

Point-in-Time Recovery:
{technical.get("pointInTimeRecoveryEnabled", "Not Available")}

Public IPv4:
{technical.get("publicIpv4Enabled", "Not Available")}

Private IP:
{technical.get("privateIp", "Not Available")}

----------------------------------------------------
"""

        prompt += """

====================================================

CONTROL FINDINGS

"""

        for finding in findings:
            recommendation = finding.get(
                "recommendation"
            )

            if recommendation is None:
                recommendation = (
                    "No remediation required."
                )

            prompt += f"""

Resource:
{finding.get("resourceName", "Unknown")}

Control ID:
{finding.get("controlId", "Unknown")}

Control:
{finding.get("controlName", finding.get("controlStatement", "Unknown Control"))}

Validation Objective:
{finding.get("validationObjective", "Not Available")}

Status:
{finding.get("status", "UNKNOWN")}

Risk:
{finding.get("risk", "Not Assigned")}

Requirement Source:
{finding.get("requirementSource", "Not Available")}

Expected:
{finding.get("expected", "Not Available")}

Actual:
{finding.get("actual", "Not Available")}

Observation:
{finding.get("observation", "Not Available")}

Recommendation:
{recommendation}

----------------------------------------------------
"""

        prompt += f"""

====================================================

USER QUESTION

{question}

====================================================

Answer using only the completed workpaper.

Where appropriate, compare resources and identify the
specific resource associated with each result.

Never invent facts.

Never change audit findings.

Return plain text only.
"""

        return prompt

    def _derive_adr_identity(
            self,
            adr):

        document = adr.get(
            "document",
            "No ADR Available"
        )
        content = adr.get(
            "content",
            ""
        )

        adr_id = adr.get("id")

        if not adr_id:
            adr_id = document.split(
                "_",
                1
            )[0]

        adr_title = adr.get("title")

        if not adr_title:
            adr_title = document

            for line in content.splitlines():
                line = line.strip()

                if not line.startswith("ADR-"):
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

    def _call_llm(
            self,
            prompt):

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
            "gemini-2.5-flash"
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

        return response.text.strip()
