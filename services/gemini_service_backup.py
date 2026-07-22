import json
import os

from dotenv import load_dotenv
from google import genai


class GeminiService:
    """
    Gemini AI Service

    Generates executive-level AI commentary.

    Gemini NEVER performs the audit.

    The audit findings are produced by the deterministic
    Technology Control Engine.

    Gemini only explains the audit results for executives.
    """

    def generate_audit_commentary(self, workpaper):
        """
        Main entry point.
        """

        try:

            prompt = self._build_prompt(workpaper)

            print("\n================ PROMPT SENT TO GEMINI ================\n")
            print(prompt)
            print("\n=======================================================\n")

            response = self._call_llm(prompt)

            commentary = self._parse_response(response)

            commentary["success"] = True

            return commentary

        except Exception as ex:

            return {

                "success": False,

                "message":
                    "AI commentary is currently unavailable.\n\n"
                    f"{str(ex)}"

            }

    def _build_prompt(self, workpaper):
        """
        Converts the enterprise workpaper into
        a Gemini prompt.
        """

        summary = workpaper["summary"]

        findings = workpaper["findings"]

        adr = workpaper["governance"]["adr"]

        prompt = f"""
You are a Senior Enterprise Technology Auditor.

IMPORTANT

The audit has already been completed.

You are NOT auditing the environment.

The PASS / FAIL decisions have already been determined
by a deterministic Enterprise Technology Control Engine.

You MUST NOT change any audit findings.

Your responsibility is ONLY to prepare an executive
audit commentary.

==================================================

Architecture Decision Record

ID:
{adr["id"]}

Title:
{adr["title"]}

==================================================

Audit Summary

Controls Evaluated:
{summary["controlsEvaluated"]}

Controls Passed:
{summary["passed"]}

Controls Failed:
{summary["failed"]}

Overall Opinion:
{summary["overallOpinion"]}

==================================================

Control Findings

"""

        for finding in findings:

            prompt += f"""

Control:
{finding["controlName"]}

Status:
{finding["status"]}

Expected:
{finding["expected"]}

Actual:
{finding["actual"]}

Risk:
{finding["risk"]}

Observation:
{finding["observation"]}

Recommendation:
{finding["recommendation"]}

------------------------------------------

"""

        prompt += """

==================================================

Prepare:

1. Executive Summary

2. Positive Observations

3. Key Risks

4. Business Impact

5. Management Recommendations

6. Overall Auditor Commentary

Return ONLY JSON.

{
  "executiveSummary":"",

  "positiveObservations":[
  ],

  "keyRisks":[
  ],

  "businessImpact":"",

  "managementRecommendations":[
  ],

  "overallCommentary":""
}

Do not return markdown.

Do not return code blocks.

Do not invent facts.

Do not modify the audit findings.

"""

        return prompt
    
    def _call_llm(self, prompt):
        """
        Calls Google Gemini using the official SDK.
        """

        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise Exception(
                "GEMINI_API_KEY was not found in the .env file."
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

        text = response.text.strip()

        if text.startswith("```json"):
            text = text.replace("```json", "", 1)

        if text.startswith("```"):
            text = text.replace("```", "", 1)

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:

            return json.loads(text)

        except Exception:

            return {

                "executiveSummary":
                    "Unable to parse Gemini response.",

                "positiveObservations": [],

                "keyRisks": [],

                "businessImpact": "",

                "managementRecommendations": [],

                "overallCommentary": text

            }

    def _parse_response(self, response):
        """
        Returns the parsed Gemini response.
        """

        return response