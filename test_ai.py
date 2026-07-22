from services.gemini_service import GeminiService

workpaper = {

    "summary": {
        "controlsEvaluated": 6,
        "passed": 5,
        "failed": 1,
        "overallOpinion": "QUALIFIED"
    },

    "governance": {
        "adr": {
            "id": "ADR-003",
            "title": "Cloud SQL Architecture"
        }
    },

    "findings": [

        {
            "controlName": "Backup Configuration",
            "status": "FAIL",
            "expected": "Enabled",
            "actual": "Disabled",
            "risk": "HIGH",
            "observation": "Backup has not been enabled.",
            "recommendation": "Enable automated backups."
        }

    ]

}

gemini = GeminiService()

commentary = gemini.generate_audit_commentary(workpaper)

print("\n================ GEMINI RESPONSE ================\n")

print(commentary)