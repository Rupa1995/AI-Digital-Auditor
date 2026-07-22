"""
Technology Control Engine

Executes AI-generated validation objectives against normalised
live evidence. The engine is deterministic and never uses AI.
"""

from datetime import datetime


class ObjectiveNormalizer:

    @staticmethod
    def normalize(
            objective,
            description="",
            expected_value=None):

        raw = str(
            objective or ""
        ).strip().upper()

        text = " ".join([
            raw,
            str(description or "").upper(),
            str(expected_value or "").upper()
        ])

        if (
            "PASSWORD" in text
            and (
                "LENGTH" in text
                or "MINIMUM" in text
                or "MIN" in text
            )
        ):
            return "MINIMUM_PASSWORD_LENGTH"

        if (
            (
                "DATA AT REST" in text
                or "DATA_AT_REST" in text
                or "PERSISTENT DATA" in text
            )
            and "ENCRYPT" in text
        ):
            return "DATA_AT_REST_ENCRYPTION"

        if (
            "ENCRYPT" in text
            and (
                "DATABASE" in text
                or "CLOUD SQL" in text
                or "CLOUD_SQL" in text
                or "CMEK" in text
            )
        ):
            return "DATABASE_ENCRYPTION"

        if (
            (
                "ALLUSERS" in text
                or "ALLAUTHENTICATEDUSERS" in text
                or "PUBLIC PRINCIPAL" in text
                or "PUBLIC IAM" in text
                or "PUBLIC ACCESS" in text
                or "NO_PUBLIC_PRINCIPALS" in text
            )
            and (
                "IAM" in text
                or "PRINCIPAL" in text
                or "ACCESS" in text
            )
        ):
            return "PUBLIC_IAM_ACCESS"

        if (
            (
                "SERVICE ACCOUNT" in text
                or "NO_SERVICE_ACCOUNT_OWNER" in text
            )
            and (
                "OWNER" in text
                or "ROLES/OWNER" in text
                or "NO_SERVICE_ACCOUNT_OWNER" in text
            )
        ):
            return "SERVICE_ACCOUNT_OWNER_ROLE"

        return raw or "UNKNOWN_VALIDATION_OBJECTIVE"


class TechnologyControlEngine:

    def __init__(self):

        self.normalizer = ObjectiveNormalizer()

        self.validators = {
            (
                "DATA_AT_REST_ENCRYPTION",
                "Cloud SQL"
            ):
                self._validate_cloudsql_data_at_rest_encryption,

            (
                "DATA_AT_REST_ENCRYPTION",
                "Cloud Storage"
            ):
                self._validate_storage_data_at_rest_encryption,

            (
                "DATABASE_ENCRYPTION",
                "Cloud SQL"
            ):
                self._validate_cloudsql_database_encryption,

            (
                "MINIMUM_PASSWORD_LENGTH",
                "Cloud SQL"
            ):
                self._validate_cloudsql_minimum_password_length,

            (
                "PUBLIC_IAM_ACCESS",
                "IAM"
            ):
                self._validate_public_iam_access,

            (
                "SERVICE_ACCOUNT_OWNER_ROLE",
                "IAM"
            ):
                self._validate_service_account_owner_role
        }

    def execute(
            self,
            execution_plan,
            evidence):

        findings = []
        controls = execution_plan.get(
            "controls",
            []
        )
        control_results = []

        target_service = (
            evidence.get(
                "resource",
                {}
            ).get(
                "service"
            )
        )

        total_validation_checks = 0
        validation_checks_passed = 0
        validation_checks_failed = 0
        validation_checks_not_verified = 0

        for control in controls:
            control_findings = []

            applicable_services = [
                service
                for service in control.get(
                    "serviceAnalysis",
                    []
                )
                if service.get(
                    "applicable",
                    False
                )
                and self._service_matches(
                    service.get("service"),
                    target_service
                )
            ]

            validation_checks = (
                control.get(
                    "executionPlan",
                    {}
                ).get(
                    "validationChecks",
                    []
                )
            )

            for service_analysis in applicable_services:
                service_name = service_analysis.get(
                    "service",
                    target_service or "Unknown Service"
                )

                for validation_check in validation_checks:
                    if not self._validation_check_matches(
                            validation_check,
                            service_name):
                        continue

                    total_validation_checks += 1

                    finding = self._execute_validation(
                        control=control,
                        service=service_name,
                        validation_check=validation_check,
                        evidence=evidence
                    )

                    findings.append(finding)
                    control_findings.append(finding)

                    if finding["status"] == "PASS":
                        validation_checks_passed += 1
                    elif finding["status"] == "FAIL":
                        validation_checks_failed += 1
                    else:
                        validation_checks_not_verified += 1

            if not applicable_services:
                control_status = "NOT APPLICABLE"
            else:
                control_status = self._determine_control_status(
                    control_findings,
                    applicable_services
                )

            control_results.append({
                "controlId":
                    control.get(
                        "controlId",
                        "Unknown Control"
                    ),
                "status":
                    control_status
            })

        controls_passed = len([
            result
            for result in control_results
            if result["status"] == "PASS"
        ])

        controls_failed = len([
            result
            for result in control_results
            if result["status"] == "FAIL"
        ])

        controls_not_verified = len([
            result
            for result in control_results
            if result["status"] == "NOT VERIFIED"
        ])

        summary = {
            "controlsEvaluated":
                (
                    controls_passed
                    + controls_failed
                    + controls_not_verified
                ),
            "controlsPassed":
                controls_passed,
            "controlsFailed":
                controls_failed,
            "controlsNotVerified":
                controls_not_verified,
            "validationChecks":
                total_validation_checks,
            "validationChecksPassed":
                validation_checks_passed,
            "validationChecksFailed":
                validation_checks_failed,
            "notVerified":
                validation_checks_not_verified
        }

        summary["evidenceCoverage"] = (
            self._calculate_evidence_coverage(
                summary
            )
        )

        summary["overallOpinion"] = (
            self._determine_overall_opinion(
                summary
            )
        )

        return {
            "auditDate":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            "targetService":
                target_service,
            "findings":
                findings,
            "controlResults":
                control_results,
            "summary":
                summary
        }

    def _service_matches(
            self,
            planned_service,
            target_service):

        if not planned_service or not target_service:
            return False

        planned = str(
            planned_service
        ).strip().lower()

        target = str(
            target_service
        ).strip().lower()

        aliases = {
            "iam": {
                "iam",
                "cloud iam",
                "google cloud iam",
                "gcp iam",
                "identity and access management",
                "project iam",
                "project iam policy",
                "service account",
                "service accounts"
            },
            "cloud sql": {
                "cloud sql",
                "gcp cloud sql",
                "google cloud sql"
            },
            "cloud storage": {
                "cloud storage",
                "google cloud storage",
                "gcp cloud storage",
                "storage",
                "storage bucket",
                "storage buckets",
                "gcs"
            }
        }

        for canonical, values in aliases.items():
            if planned in values:
                planned = canonical

            if target in values:
                target = canonical

        return planned == target

    def _validation_check_matches(
            self,
            validation_check,
            service_name):

        if not isinstance(
                validation_check,
                dict):
            return True

        technology = validation_check.get(
            "technology"
        )

        if not technology:
            return True

        return self._service_matches(
            technology,
            service_name
        )

    def _execute_validation(
            self,
            control,
            service,
            validation_check,
            evidence):

        if not isinstance(
                validation_check,
                dict):
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=(
                    "UNSTRUCTURED_VALIDATION"
                ),
                technology=service,
                resource_type="Unknown",
                identity_type="",
                requirement_source="Unknown",
                extracted_requirement="",
                description=str(validation_check),
                expected=(
                    "Structured validation check"
                ),
                actual=(
                    "Legacy free-text validation"
                ),
                observation=(
                    "The execution plan contains a "
                    "free-text validation check."
                ),
                recommendation=(
                    "Regenerate the execution plan "
                    "using the structured contract."
                ),
                evidence=evidence
            )

        raw_objective = validation_check.get(
            "validationObjective",
            ""
        )
        description = validation_check.get(
            "description",
            "Validation description not provided."
        )
        expected_value = validation_check.get(
            "expectedValue"
        )

        validation_objective = (
            self.normalizer.normalize(
                objective=raw_objective,
                description=description,
                expected_value=expected_value
            )
        )

        technology = service
        resource_type = validation_check.get(
            "resourceType",
            "Unknown"
        )
        identity_type = validation_check.get(
            "identityType",
            ""
        )
        requirement_source = validation_check.get(
            "requirementSource",
            "Unknown"
        )
        extracted_requirement = validation_check.get(
            "extractedRequirement",
            ""
        )

        validator = self.validators.get(
            (
                validation_objective,
                technology
            )
        )

        if validator is None:
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=validation_objective,
                technology=technology,
                resource_type=resource_type,
                identity_type=identity_type,
                requirement_source=requirement_source,
                extracted_requirement=extracted_requirement,
                description=description,
                expected=(
                    expected_value
                    if expected_value not in (
                        None,
                        ""
                    )
                    else
                    "Deterministic validator available"
                ),
                actual="Validator Not Implemented",
                observation=(
                    "No deterministic validator exists "
                    f"for objective "
                    f"'{validation_objective}' and "
                    f"technology '{technology}'."
                ),
                recommendation=(
                    "Implement a deterministic validator "
                    "for this objective and technology."
                ),
                evidence=evidence
            )

        return validator(
            control=control,
            service=service,
            validation_objective=validation_objective,
            technology=technology,
            resource_type=resource_type,
            identity_type=identity_type,
            requirement_source=requirement_source,
            extracted_requirement=extracted_requirement,
            description=description,
            expected_value=expected_value,
            evidence=evidence
        )

    def _validate_cloudsql_data_at_rest_encryption(
            self,
            **kwargs):
        """Uses the Cloud SQL encryption validator for EC-001."""

        return self._validate_cloudsql_database_encryption(
            **kwargs
        )

    def _validate_storage_data_at_rest_encryption(
            self,
            control,
            service,
            validation_objective,
            technology,
            resource_type,
            identity_type,
            requirement_source,
            extracted_requirement,
            description,
            expected_value,
            evidence):

        technical = evidence.get(
            "technicalEvidence",
            {}
        )

        encrypted = technical.get(
            "dataAtRestEncrypted"
        )
        actual_encryption = technical.get(
            "encryption"
        )

        if encrypted is None:
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=validation_objective,
                technology=technology,
                resource_type=resource_type,
                identity_type=identity_type,
                requirement_source=requirement_source,
                extracted_requirement=extracted_requirement,
                description=description,
                expected="Data at rest encrypted",
                actual="Evidence Not Available",
                observation=(
                    "Cloud Storage encryption-at-rest evidence "
                    "was not collected."
                ),
                recommendation=(
                    "Collect the live Cloud Storage bucket "
                    "encryption configuration."
                ),
                evidence=evidence
            )

        expected_text = str(
            expected_value or "ENCRYPTED"
        ).upper()

        if "CMEK" in expected_text:
            passed = actual_encryption == "CMEK"
            expected_display = "CMEK"
        else:
            passed = bool(encrypted)
            expected_display = "Data at rest encrypted"

        return self._build_finding(
            control=control,
            service=service,
            validation_objective=validation_objective,
            technology=technology,
            resource_type=resource_type,
            identity_type=identity_type,
            requirement_source=requirement_source,
            extracted_requirement=extracted_requirement,
            description=description,
            status="PASS" if passed else "FAIL",
            expected=expected_display,
            actual=(
                actual_encryption
                if actual_encryption
                else "Not encrypted"
            ),
            risk="HIGH",
            observation=(
                "The Cloud Storage bucket satisfies the "
                "data-at-rest encryption control."
                if passed
                else
                "The Cloud Storage bucket does not satisfy the "
                "required data-at-rest encryption target."
            ),
            recommendation=(
                None
                if passed
                else
                "Configure an enterprise-approved encryption "
                "mechanism for the Cloud Storage bucket."
            ),
            evidence=evidence
        )

    def _validate_cloudsql_database_encryption(
            self,
            control,
            service,
            validation_objective,
            technology,
            resource_type,
            identity_type,
            requirement_source,
            extracted_requirement,
            description,
            expected_value,
            evidence):

        technical = evidence.get(
            "technicalEvidence",
            {}
        )
        actual_encryption = technical.get(
            "encryption"
        )

        if actual_encryption is None:
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=validation_objective,
                technology=technology,
                resource_type=resource_type,
                identity_type=identity_type,
                requirement_source=requirement_source,
                extracted_requirement=extracted_requirement,
                description=description,
                expected=(
                    expected_value
                    or "Encryption Enabled"
                ),
                actual="Evidence Not Available",
                observation=(
                    "Cloud SQL encryption evidence "
                    "was not collected."
                ),
                recommendation=(
                    "Collect the Cloud SQL encryption "
                    "configuration."
                ),
                evidence=evidence
            )

        actual = str(
            actual_encryption
        ).strip().upper()

        expected = (
            str(expected_value).strip().upper()
            if expected_value not in (
                None,
                ""
            )
            else "ENABLED"
        )

        if "CMEK" in expected:
            passed = actual == "CMEK"
            expected_display = "CMEK"
            failure_observation = (
                "Cloud SQL is not encrypted using "
                "Customer-Managed Encryption Keys."
            )
            failure_recommendation = (
                "Configure the Cloud SQL instance "
                "to use a Customer-Managed Encryption "
                "Key through Cloud KMS."
            )
        else:
            passed = actual not in {
                "",
                "NONE",
                "DISABLED",
                "FALSE",
                "UNENCRYPTED"
            }
            expected_display = (
                expected_value
                or "Encryption Enabled"
            )
            failure_observation = (
                "Cloud SQL encryption at rest "
                "is not enabled."
            )
            failure_recommendation = (
                "Enable encryption at rest for "
                "the Cloud SQL instance."
            )

        return self._build_finding(
            control=control,
            service=service,
            validation_objective=validation_objective,
            technology=technology,
            resource_type=resource_type,
            identity_type=identity_type,
            requirement_source=requirement_source,
            extracted_requirement=extracted_requirement,
            description=description,
            status="PASS" if passed else "FAIL",
            expected=expected_display,
            actual=actual,
            risk="HIGH",
            observation=(
                "Cloud SQL satisfies the required "
                "database encryption target state."
                if passed
                else failure_observation
            ),
            recommendation=(
                None
                if passed
                else failure_recommendation
            ),
            evidence=evidence
        )

    def _validate_cloudsql_minimum_password_length(
            self,
            control,
            service,
            validation_objective,
            technology,
            resource_type,
            identity_type,
            requirement_source,
            extracted_requirement,
            description,
            expected_value,
            evidence):

        technical = evidence.get(
            "technicalEvidence",
            {}
        )
        actual_value = technical.get(
            "minimumPasswordLength"
        )

        required_length = self._to_integer(
            expected_value,
            default_value=None
        )

        if required_length is None:
            required_length = self._to_integer(
                extracted_requirement,
                default_value=None
            )

        if required_length is None:
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=validation_objective,
                technology=technology,
                resource_type=resource_type,
                identity_type=identity_type,
                requirement_source=requirement_source,
                extracted_requirement=extracted_requirement,
                description=description,
                expected=(
                    "Measurable minimum password length"
                ),
                actual=expected_value,
                observation=(
                    "The AI execution plan did not "
                    "provide a measurable password "
                    "length."
                ),
                recommendation=(
                    "Regenerate the execution plan from "
                    "the explicit control requirement."
                ),
                evidence=evidence
            )

        if actual_value is None:
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=validation_objective,
                technology=technology,
                resource_type=resource_type,
                identity_type=identity_type,
                requirement_source=requirement_source,
                extracted_requirement=extracted_requirement,
                description=description,
                expected=(
                    f"Minimum {required_length} characters"
                ),
                actual="Evidence Not Available",
                observation=(
                    "The Cloud SQL instance does not expose "
                    "a configured minimum-password-length "
                    "policy in the collected live evidence."
                ),
                recommendation=(
                    "Configure and enable the Cloud SQL "
                    "password-validation policy with a "
                    f"minimum length of at least "
                    f"{required_length} characters, or "
                    "provide authoritative database-level "
                    "evidence demonstrating equivalent "
                    "enforcement."
                ),
                evidence=evidence
            )

        actual_length = self._to_integer(
            actual_value,
            default_value=None
        )

        if actual_length is None:
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=validation_objective,
                technology=technology,
                resource_type=resource_type,
                identity_type=identity_type,
                requirement_source=requirement_source,
                extracted_requirement=extracted_requirement,
                description=description,
                expected=(
                    f"Minimum {required_length} characters"
                ),
                actual=actual_value,
                observation=(
                    "The collected minimum password "
                    "length is not a valid number."
                ),
                recommendation=(
                    "Correct the password-policy "
                    "evidence format."
                ),
                evidence=evidence
            )

        passed = actual_length >= required_length

        return self._build_finding(
            control=control,
            service=service,
            validation_objective=validation_objective,
            technology=technology,
            resource_type=resource_type,
            identity_type=identity_type,
            requirement_source=requirement_source,
            extracted_requirement=extracted_requirement,
            description=description,
            status="PASS" if passed else "FAIL",
            expected=f"Minimum {required_length} characters",
            actual=f"{actual_length} characters",
            risk="MEDIUM",
            observation=(
                "The configured minimum password "
                "length satisfies the control."
                if passed
                else
                "The configured minimum password "
                "length does not satisfy the control."
            ),
            recommendation=(
                None
                if passed
                else
                "Configure the minimum password "
                f"length to at least "
                f"{required_length} characters."
            ),
            evidence=evidence
        )

    def _validate_public_iam_access(
            self,
            control,
            service,
            validation_objective,
            technology,
            resource_type,
            identity_type,
            requirement_source,
            extracted_requirement,
            description,
            expected_value,
            evidence):

        technical = evidence.get(
            "technicalEvidence",
            {}
        )
        public_bindings = technical.get(
            "publicBindings"
        )

        if public_bindings is None:
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=validation_objective,
                technology=technology,
                resource_type=resource_type,
                identity_type=identity_type,
                requirement_source=requirement_source,
                extracted_requirement=extracted_requirement,
                description=description,
                expected=(
                    "No allUsers or "
                    "allAuthenticatedUsers bindings"
                ),
                actual="Evidence Not Available",
                observation=(
                    "Project IAM policy evidence was "
                    "not collected."
                ),
                recommendation=(
                    "Collect the project IAM policy."
                ),
                evidence=evidence
            )

        passed = len(public_bindings) == 0

        return self._build_finding(
            control=control,
            service=service,
            validation_objective=validation_objective,
            technology=technology,
            resource_type=resource_type,
            identity_type=identity_type,
            requirement_source=requirement_source,
            extracted_requirement=extracted_requirement,
            description=description,
            status="PASS" if passed else "FAIL",
            expected=(
                "No allUsers or "
                "allAuthenticatedUsers bindings"
            ),
            actual=(
                "No public principals detected"
                if passed
                else public_bindings
            ),
            risk="HIGH",
            observation=(
                "No public principals were detected "
                "in the project IAM policy."
                if passed
                else
                "The project IAM policy grants access "
                "to public principals."
            ),
            recommendation=(
                None
                if passed
                else
                "Remove allUsers and "
                "allAuthenticatedUsers bindings unless "
                "an approved exception exists."
            ),
            evidence=evidence
        )

    def _validate_service_account_owner_role(
            self,
            control,
            service,
            validation_objective,
            technology,
            resource_type,
            identity_type,
            requirement_source,
            extracted_requirement,
            description,
            expected_value,
            evidence):

        technical = evidence.get(
            "technicalEvidence",
            {}
        )
        owner_accounts = technical.get(
            "ownerRoleServiceAccounts"
        )

        if owner_accounts is None:
            return self._build_not_verified_finding(
                control=control,
                service=service,
                validation_objective=validation_objective,
                technology=technology,
                resource_type=resource_type,
                identity_type=identity_type,
                requirement_source=requirement_source,
                extracted_requirement=extracted_requirement,
                description=description,
                expected=(
                    "No service account assigned roles/owner"
                ),
                actual="Evidence Not Available",
                observation=(
                    "Service-account role assignment "
                    "evidence was not collected."
                ),
                recommendation=(
                    "Collect the project IAM policy and "
                    "service-account inventory."
                ),
                evidence=evidence
            )

        passed = len(owner_accounts) == 0

        return self._build_finding(
            control=control,
            service=service,
            validation_objective=validation_objective,
            technology=technology,
            resource_type=resource_type,
            identity_type=identity_type,
            requirement_source=requirement_source,
            extracted_requirement=extracted_requirement,
            description=description,
            status="PASS" if passed else "FAIL",
            expected=(
                "No service account assigned roles/owner"
            ),
            actual=(
                "No service accounts with Owner role"
                if passed
                else owner_accounts
            ),
            risk="HIGH",
            observation=(
                "No service account is assigned the "
                "project Owner role."
                if passed
                else
                "One or more service accounts are "
                "assigned the project Owner role."
            ),
            recommendation=(
                None
                if passed
                else
                "Remove the Owner role from the affected "
                "service accounts and assign only the "
                "minimum required predefined or custom "
                "roles."
            ),
            evidence=evidence
        )

    def _build_finding(
            self,
            control,
            service,
            validation_objective,
            technology,
            resource_type,
            identity_type,
            requirement_source,
            extracted_requirement,
            description,
            status,
            expected,
            actual,
            risk,
            observation,
            recommendation,
            evidence):

        resource = evidence.get(
            "resource",
            {}
        )

        return {
            "controlId":
                control.get(
                    "controlId",
                    "Unknown Control"
                ),
            "controlStatement":
                control.get(
                    "controlStatement",
                    "Unknown Control"
                ),
            "service":
                service,
            "resourceName":
                resource.get(
                    "resourceName",
                    "Unknown Resource"
                ),
            "projectId":
                resource.get(
                    "projectId"
                ),
            "validationObjective":
                validation_objective,
            "technology":
                technology,
            "resourceType":
                resource_type,
            "identityType":
                identity_type,
            "requirementSource":
                requirement_source,
            "extractedRequirement":
                extracted_requirement,
            "validationCheck":
                description,
            "status":
                status,
            "expected":
                expected,
            "actual":
                actual,
            "risk":
                risk,
            "observation":
                observation,
            "recommendation":
                recommendation
        }

    def _build_not_verified_finding(
            self,
            control,
            service,
            validation_objective,
            technology,
            resource_type,
            identity_type,
            requirement_source,
            extracted_requirement,
            description,
            expected,
            actual,
            observation,
            recommendation,
            evidence):

        return self._build_finding(
            control=control,
            service=service,
            validation_objective=validation_objective,
            technology=technology,
            resource_type=resource_type,
            identity_type=identity_type,
            requirement_source=requirement_source,
            extracted_requirement=extracted_requirement,
            description=description,
            status="NOT VERIFIED",
            expected=expected,
            actual=actual,
            risk="Not Assigned",
            observation=observation,
            recommendation=recommendation,
            evidence=evidence
        )

    def _determine_control_status(
            self,
            control_findings,
            applicable_services):

        if not applicable_services:
            return "NOT APPLICABLE"

        if not control_findings:
            return "NOT VERIFIED"

        statuses = [
            finding.get(
                "status",
                "NOT VERIFIED"
            )
            for finding in control_findings
        ]

        if "FAIL" in statuses:
            return "FAIL"

        if "NOT VERIFIED" in statuses:
            return "NOT VERIFIED"

        return "PASS"

    def _calculate_evidence_coverage(
            self,
            summary):

        total = summary.get(
            "validationChecks",
            0
        )

        if total == 0:
            return 0.0

        executed = (
            summary.get(
                "validationChecksPassed",
                0
            )
            +
            summary.get(
                "validationChecksFailed",
                0
            )
        )

        return round(
            (executed / total) * 100,
            2
        )

    def _determine_overall_opinion(
            self,
            summary):

        if summary.get(
                "controlsFailed",
                0) > 0:
            return "ADVERSE"

        if (
            summary.get(
                "controlsNotVerified",
                0
            ) > 0
            or summary.get(
                "notVerified",
                0
            ) > 0
        ):
            return "QUALIFIED"

        return "UNQUALIFIED"

    def _to_integer(
            self,
            value,
            default_value=None):

        if value is None:
            return default_value

        if isinstance(value, bool):
            return default_value

        if isinstance(value, int):
            return value

        text = str(value)

        digits = "".join(
            character
            for character in text
            if character.isdigit()
        )

        if not digits:
            return default_value

        return int(digits)
