from datetime import datetime


class WorkpaperService:

    def build_workpaper(self, evidence, adr, controls=None, results=None):

        # Use deterministic control results when available
        if results is not None:
            findings = results.get("findings", [])
            summary = results.get("summary", {})
        else:
            findings = []
            technical = evidence["technicalEvidence"]


        if results is not None:
            return {
                "auditEngagement": {
                    "auditId": "AUD-2026-0001",
                    "auditDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "auditType": "Enterprise Technology Audit",
                    "auditor": "AI-assisted Technology Auditor"
                },
                "auditScope": evidence["resource"],
                "governance": {"adr": adr, "controls": controls or []},
                "findings": findings,
                "summary": {
                    "controlsEvaluated": summary.get("controlsEvaluated", 0),
                    "validationChecks": summary.get("validationChecks", 0),
                    "passed": summary.get("controlsPassed", 0),
                    "failed": summary.get("controlsFailed", 0),
                    "notVerified": summary.get("notVerified", 0),
                    "evidenceCoverage": summary.get("evidenceCoverage", 0),
                    "overallOpinion": summary.get("overallOpinion", "QUALIFIED")
                },
                "technicalEvidence": evidence["technicalEvidence"],
                "operationalEvidence": evidence["operationalEvidence"],
                "metadata": evidence["metadata"]
            }

        # ---------------------------------------------------------
        # CTRL-001
        # Production Database High Availability
        # ---------------------------------------------------------

        findings.append(
            self.evaluate_control(
                control_id="CTRL-001",
                control_name="Production Database High Availability",
                expected="REGIONAL",
                actual=technical["availabilityType"],
                passed=technical["availabilityType"] == "REGIONAL",
                risk="HIGH",
                recommendation="Deploy Cloud SQL using REGIONAL high availability."
            )
        )

        # ---------------------------------------------------------
        # CTRL-002
        # Database Backup Configuration
        # ---------------------------------------------------------

        findings.append(
            self.evaluate_control(
                control_id="CTRL-002",
                control_name="Database Backup Configuration",
                expected=True,
                actual=technical["backupEnabled"],
                passed=technical["backupEnabled"],
                risk="HIGH",
                recommendation="Enable automated database backups."
            )
        )

        # ---------------------------------------------------------
        # CTRL-003
        # Point-in-Time Recovery
        # ---------------------------------------------------------

        findings.append(
            self.evaluate_control(
                control_id="CTRL-003",
                control_name="Point-in-Time Recovery",
                expected=True,
                actual=technical["pointInTimeRecoveryEnabled"],
                passed=technical["pointInTimeRecoveryEnabled"],
                risk="MEDIUM",
                recommendation="Enable Point-in-Time Recovery."
            )
        )

        # ---------------------------------------------------------
        # CTRL-004
        # Public Network Exposure
        # ---------------------------------------------------------

        findings.append(
            self.evaluate_control(
                control_id="CTRL-004",
                control_name="Public Network Exposure",
                expected=False,
                actual=technical["publicIpv4Enabled"],
                passed=not technical["publicIpv4Enabled"],
                risk="HIGH",
                recommendation="Use Private IP connectivity and disable public IPv4 access."
            )
        )

        # ---------------------------------------------------------
        # CTRL-005
        # Deletion Protection
        # ---------------------------------------------------------

        findings.append(
            self.evaluate_control(
                control_id="CTRL-005",
                control_name="Deletion Protection",
                expected=True,
                actual=technical["deletionProtection"],
                passed=technical["deletionProtection"],
                risk="MEDIUM",
                recommendation="Enable deletion protection."
            )
        )

        # ---------------------------------------------------------
        # CTRL-006
        # Customer Managed Encryption Keys
        # ---------------------------------------------------------

        cmek = technical.get("cmekConfigured")

        if cmek is None:

            findings.append({

                "controlId": "CTRL-006",

                "controlName": "Data Encryption Using Customer Managed Keys",

                "expected": "CMEK Enabled",

                "actual": "Evidence Not Collected",

                "status": "NOT VERIFIED",

                "risk": "HIGH",

                "observation":
                    "Cloud KMS evidence has not yet been collected.",

                "recommendation":
                    "Collect Cloud KMS configuration before evaluating this control."

            })

        else:

            findings.append(
                self.evaluate_control(
                    control_id="CTRL-006",
                    control_name="Data Encryption Using Customer Managed Keys",
                    expected=True,
                    actual=cmek,
                    passed=cmek,
                    risk="HIGH",
                    recommendation="Configure Cloud SQL to use Cloud KMS Customer Managed Encryption Keys."
                )
            )

        # ---------------------------------------------------------
        # Summary
        # ---------------------------------------------------------

        passed = len(
            [f for f in findings if f["status"] == "PASS"]
        )

        failed = len(
            [f for f in findings if f["status"] == "FAIL"]
        )

        not_verified = len(
            [f for f in findings if f["status"] == "NOT VERIFIED"]
        )

        total = len(findings)

        if failed == 0:
            opinion = "UNQUALIFIED"

        elif failed <= 2:
            opinion = "QUALIFIED"

        else:
            opinion = "ADVERSE"

        workpaper = {

            "auditEngagement": {

                "auditId": "AUD-2026-0001",

                "auditDate":
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                "auditType":
                    "Enterprise Technology Audit",

                "auditor":
                    "AI-assisted Technology Auditor"

            },

            "auditScope": evidence["resource"],

            "governance": {

                "adr": adr

            },

            "findings": findings,

            "summary": {

                "controlsEvaluated": total,

                "passed": passed,

                "failed": failed,

                "notVerified": not_verified,

                "overallOpinion": opinion

            },

            "technicalEvidence":
                evidence["technicalEvidence"],

            "operationalEvidence":
                evidence["operationalEvidence"],

            "metadata":
                evidence["metadata"]

        }

        return workpaper

    def evaluate_control(
            self,
            control_id,
            control_name,
            expected,
            actual,
            passed,
            risk,
            recommendation):

        return {

            "controlId": control_id,

            "controlName": control_name,

            "expected": expected,

            "actual": actual,

            "status": "PASS" if passed else "FAIL",

            "risk": risk,

            "observation":
                "Control requirement satisfied."
                if passed
                else "Control requirement not satisfied.",

            "recommendation":
                None if passed else recommendation

        }