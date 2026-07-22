class TechnologyControlService:
    """
    Enterprise Technology Control Evaluation Engine

    Compares enterprise controls against
    live cloud evidence.
    """

    # ---------------------------------------------------------
    # Read nested JSON value
    # ---------------------------------------------------------

    def get_value(self, data, path):

        value = data

        for part in path.split("."):

            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    # ---------------------------------------------------------
    # Evaluate expected vs actual
    # ---------------------------------------------------------

    def evaluate(self, expected, actual):

        if expected == "Enabled":
            return actual is True

        if expected == "Disabled":
            return actual is False

        if expected == "Configured":
            return actual not in (None, "", False)

        if "or more" in expected:

            minimum = int(expected.split()[0])

            try:
                return int(actual) >= minimum
            except Exception:
                return False

        return str(actual).upper() == str(expected).upper()

    # ---------------------------------------------------------
    # Evaluate all controls
    # ---------------------------------------------------------

    def evaluate_controls(self, controls, raw_evidence):

        findings = []

        passed = 0
        failed = 0

        for control in controls:

            actual = self.get_value(
                raw_evidence,
                control["evidence"]
            )

            passed_control = self.evaluate(
                control["expected"],
                actual
            )

            if passed_control:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1

            findings.append({

    "controlId": control["id"],

    "controlName": control["name"],

    "category": control["category"],

    "status": status,

    "expected": control["expected"],

    "actual": actual,

    "evidencePath": control["evidence"],

    "risk": control["risk"],

    "businessImpact": control["businessImpact"],

    "observation": (
        "Control requirement satisfied."
        if status == "PASS"
        else "Control requirement not satisfied."
    ),

    "recommendation": (
        None
        if status == "PASS"
        else control["recommendation"]
    )

})
        if failed == 0:
            opinion = "UNQUALIFIED"
        else:
            opinion = "QUALIFIED"

        return {

            "summary": {

                "controlsEvaluated": len(controls),

                "controlsPassed": passed,

                "controlsFailed": failed,

                "overallOpinion": opinion

            },

            "findings": findings

        }