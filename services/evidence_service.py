"""
Evidence Service

Purpose
-------
Discovers Google Cloud technologies and collects normalised live
evidence for the AI Digital Auditor.

Supported live technologies
---------------------------
1. Cloud SQL
2. IAM / Service Accounts

Additional technologies are discovered for AI applicability
analysis even when deterministic validators are not yet available.
"""

from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess


class EvidenceService:

    def __init__(self):
        self.base_path = (
            Path(__file__).parent.parent
            / "evidence"
        )

    # ==========================================================
    # Generic gcloud execution
    # ==========================================================

    def _run_gcloud(
            self,
            command,
            timeout_seconds=30):
        """
        Executes a non-interactive gcloud command.

        A timeout prevents one unavailable API, permission issue
        or stalled gcloud component from blocking the complete
        environment-discovery workflow.
        """

        safe_command = list(command)

        if "--quiet" not in safe_command:
            safe_command.append("--quiet")

        try:
            result = subprocess.run(
                safe_command,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds
            )

        except subprocess.TimeoutExpired as ex:
            command_text = " ".join(safe_command)

            raise RuntimeError(
                f"gcloud command timed out after "
                f"{timeout_seconds} seconds: "
                f"{command_text}"
            ) from ex

        except FileNotFoundError as ex:
            raise RuntimeError(
                "The gcloud CLI was not found. "
                "Install Google Cloud CLI and ensure "
                "it is available on PATH."
            ) from ex

        if result.returncode != 0:
            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Unknown gcloud error."
            )

            raise RuntimeError(message)

        output = result.stdout.strip()

        if not output:
            return {}

        try:
            return json.loads(output)

        except json.JSONDecodeError as ex:
            raise RuntimeError(
                "gcloud did not return valid JSON. "
                f"{str(ex)}"
            ) from ex

    # ==========================================================
    # Local evidence fallback
    # ==========================================================

    def load_evidence(self, service, resource):

        file_path = (
            self.base_path
            / service
            / f"{resource}.json"
        )

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        with open(
                file_path,
                "r",
                encoding="utf-8") as file:
            return json.load(file)

    # ==========================================================
    # Session and project
    # ==========================================================

    def validate_gcloud_session(self):

        try:
            configuration = self._run_gcloud([
                "gcloud",
                "config",
                "list",
                "account",
                "--format=json"
            ])

            account = (
                configuration
                .get("core", {})
                .get("account")
            )

            if not account:
                return {
                    "valid": False,
                    "message":
                        "No active gcloud account was found. "
                        "Run: gcloud auth login"
                }

            return {
                "valid": True,
                "account": account
            }

        except Exception as ex:
            return {
                "valid": False,
                "message": str(ex)
            }

    def validate_project(self, project_id):

        try:
            project = self._run_gcloud([
                "gcloud",
                "projects",
                "describe",
                project_id,
                "--format=json"
            ])

            return {
                "valid": True,
                "projectId":
                    project["projectId"],
                "projectName":
                    project.get(
                        "name",
                        project["projectId"]
                    ),
                "projectNumber":
                    project["projectNumber"],
                "state":
                    project["lifecycleState"]
            }

        except Exception as ex:
            return {
                "valid": False,
                "message": str(ex)
            }

    # ==========================================================
    # Technology discovery
    # ==========================================================

    def discover_environment(self, project_id):
        """
        Discovers technologies in the target project.

        Discovery is best-effort. A service discovery failure is
        retained as an error for that service instead of aborting
        the whole environment discovery.
        """

        discovery = {
            "project": project_id,
            "services": [],
            "resources": {},
            "errors": {}
        }

        discovery_functions = [
            (
                "Cloud SQL",
                "cloudSqlInstances",
                self.list_cloudsql_instances
            ),
            (
                "IAM",
                "serviceAccounts",
                self.list_service_accounts
            ),
            (
                "Cloud Storage",
                "storageBuckets",
                self.list_storage_buckets
            ),
            (
                "VPC",
                "vpcNetworks",
                self.list_vpc_networks
            ),
            (
                "Pub/Sub",
                "pubsubTopics",
                self.list_pubsub_topics
            ),
            (
                "Secret Manager",
                "secrets",
                self.list_secrets
            )
        ]

        for service_name, resource_key, function in discovery_functions:

            try:
                resources = function(project_id)

                if not isinstance(resources, list):
                    resources = []

                discovery["resources"][resource_key] = resources

                discovery["services"].append({
                    "service": service_name,
                    "resourceCount": len(resources),
                    "discovered": len(resources) > 0
                })

            except Exception as ex:
                discovery["resources"][resource_key] = []
                discovery["errors"][service_name] = str(ex)

                discovery["services"].append({
                    "service": service_name,
                    "resourceCount": 0,
                    "discovered": False,
                    "discoveryError": str(ex)
                })

        return discovery

    # ==========================================================
    # Cloud SQL
    # ==========================================================

    def list_cloudsql_instances(self, project_id):

        instances = self._run_gcloud([
            "gcloud",
            "sql",
            "instances",
            "list",
            "--project",
            project_id,
            "--format=json"
        ])

        return instances if isinstance(instances, list) else []

    def describe_cloudsql_instance(
            self,
            project_id,
            instance_name):

        return self._run_gcloud([
            "gcloud",
            "sql",
            "instances",
            "describe",
            instance_name,
            "--project",
            project_id,
            "--format=json"
        ])

    def load_live_evidence(
            self,
            project_id,
            instance_name):

        instance = self.describe_cloudsql_instance(
            project_id,
            instance_name
        )

        settings = instance.get("settings", {})
        backup = settings.get("backupConfiguration", {})
        ip_configuration = settings.get(
            "ipConfiguration",
            {}
        )
        disk_encryption = instance.get(
            "diskEncryptionConfiguration",
            {}
        )
        password_policy = settings.get(
            "passwordValidationPolicy",
            {}
        )

        kms_key_name = disk_encryption.get("kmsKeyName")
        private_network = ip_configuration.get(
            "privateNetwork"
        )

        technical = {
            "databaseEngine":
                self._normalise_database_engine(
                    instance.get("databaseVersion")
                ),
            "databaseVersion":
                instance.get("databaseVersion"),
            "region":
                instance.get("region"),
            "state":
                instance.get("state"),
            "availabilityType":
                settings.get("availabilityType"),
            "highAvailability":
                settings.get("availabilityType") == "REGIONAL",
            "backupEnabled":
                backup.get("enabled", False),
            "pointInTimeRecoveryEnabled":
                backup.get(
                    "pointInTimeRecoveryEnabled",
                    False
                ),
            "storageAutoResize":
                settings.get(
                    "storageAutoResize",
                    False
                ),
            "deletionProtection":
                settings.get(
                    "deletionProtectionEnabled",
                    False
                ),
            "publicIpv4Enabled":
                ip_configuration.get(
                    "ipv4Enabled",
                    False
                ),
            "privateIp":
                bool(private_network),
            "privateNetwork":
                private_network,
            "sslMode":
                ip_configuration.get("sslMode"),
            "tier":
                settings.get("tier"),
            "edition":
                settings.get("edition"),
            "kmsKeyName":
                kms_key_name,
            "cmekConfigured":
                bool(kms_key_name),
            "encryption":
                "CMEK" if kms_key_name else "GMEK",
            "passwordPolicyEnabled":
                password_policy.get(
                    "enablePasswordPolicy"
                ),
            "minimumPasswordLength":
                password_policy.get("minLength"),
            "passwordComplexity":
                password_policy.get("complexity"),
            "passwordReuseInterval":
                password_policy.get("reuseInterval"),
            "disallowUsernameSubstring":
                password_policy.get(
                    "disallowUsernameSubstring"
                )
        }

        return {
            "rawEvidence": instance,
            "resource": {
                "cloudPlatform":
                    "Google Cloud Platform",
                "projectId":
                    project_id,
                "project":
                    project_id,
                "environment":
                    "Production",
                "service":
                    "Cloud SQL",
                "resourceType":
                    "Cloud SQL Instance",
                "resourceName":
                    instance_name,
                "instanceName":
                    instance_name,
                "location":
                    instance.get("region")
            },
            "technicalEvidence": technical,
            "operationalEvidence": {
                "auditSource":
                    "Google Cloud CLI",
                "collectionCommand":
                    "gcloud sql instances describe"
            },
            "metadata": self._metadata(
                completeness=self._determine_completeness(
                    technical,
                    [
                        "encryption",
                        "minimumPasswordLength"
                    ]
                )
            )
        }

    # ==========================================================
    # IAM discovery and evidence
    # ==========================================================

    def list_service_accounts(self, project_id):

        accounts = self._run_gcloud([
            "gcloud",
            "iam",
            "service-accounts",
            "list",
            "--project",
            project_id,
            "--format=json"
        ])

        return accounts if isinstance(accounts, list) else []

    def get_project_iam_policy(self, project_id):

        return self._run_gcloud([
            "gcloud",
            "projects",
            "get-iam-policy",
            project_id,
            "--format=json"
        ])

    def list_service_account_keys(
            self,
            project_id,
            service_account_email):

        keys = self._run_gcloud([
            "gcloud",
            "iam",
            "service-accounts",
            "keys",
            "list",
            "--iam-account",
            service_account_email,
            "--project",
            project_id,
            "--format=json"
        ])

        return keys if isinstance(keys, list) else []

    def load_live_iam_evidence(self, project_id):
        """
        Collects project-level IAM evidence.

        The IAM estate is treated as one audit resource while the
        underlying service accounts and bindings remain available
        as detailed evidence.
        """

        service_accounts = self.list_service_accounts(
            project_id
        )
        policy = self.get_project_iam_policy(
            project_id
        )

        bindings = policy.get("bindings", [])

        public_bindings = []
        owner_service_accounts = []

        for binding in bindings:
            role = binding.get("role", "")
            members = binding.get("members", [])

            public_members = [
                member
                for member in members
                if member in (
                    "allUsers",
                    "allAuthenticatedUsers"
                )
            ]

            if public_members:
                public_bindings.append({
                    "role": role,
                    "members": public_members
                })

            if role == "roles/owner":
                for member in members:
                    if member.startswith(
                            "serviceAccount:"):
                        owner_service_accounts.append(
                            member.split(
                                ":",
                                1
                            )[1]
                        )

        account_details = []
        user_managed_keys = []

        for account in service_accounts:
            email = account.get("email")

            keys = []

            if email:
                try:
                    keys = self.list_service_account_keys(
                        project_id,
                        email
                    )
                except Exception as ex:
                    keys = [{
                        "collectionError": str(ex)
                    }]

            account_user_keys = [
                key
                for key in keys
                if key.get("keyType") == "USER_MANAGED"
            ]

            for key in account_user_keys:
                user_managed_keys.append({
                    "serviceAccount": email,
                    "name": key.get("name"),
                    "validAfterTime":
                        key.get("validAfterTime"),
                    "validBeforeTime":
                        key.get("validBeforeTime"),
                    "disabled":
                        key.get("disabled", False)
                })

            account_details.append({
                "email": email,
                "displayName":
                    account.get("displayName"),
                "disabled":
                    account.get("disabled", False),
                "oauth2ClientId":
                    account.get("oauth2ClientId"),
                "userManagedKeyCount":
                    len(account_user_keys)
            })

        technical = {
            "serviceAccountCount":
                len(service_accounts),
            "serviceAccounts":
                account_details,
            "projectIamBindings":
                bindings,
            "publicBindings":
                public_bindings,
            "publicAccessDetected":
                len(public_bindings) > 0,
            "ownerRoleServiceAccounts":
                sorted(
                    set(
                        owner_service_accounts
                    )
                ),
            "ownerRoleServiceAccountCount":
                len(
                    set(
                        owner_service_accounts
                    )
                ),
            "userManagedServiceAccountKeys":
                user_managed_keys,
            "userManagedServiceAccountKeyCount":
                len(user_managed_keys)
        }

        return {
            "rawEvidence": {
                "serviceAccounts":
                    service_accounts,
                "iamPolicy":
                    policy
            },
            "resource": {
                "cloudPlatform":
                    "Google Cloud Platform",
                "projectId":
                    project_id,
                "project":
                    project_id,
                "environment":
                    "Production",
                "service":
                    "IAM",
                "resourceType":
                    "Project IAM Estate",
                "resourceName":
                    f"{project_id}-iam",
                "location":
                    "Global"
            },
            "technicalEvidence":
                technical,
            "operationalEvidence": {
                "auditSource":
                    "Google Cloud CLI",
                "collectionCommands": [
                    "gcloud iam service-accounts list",
                    "gcloud projects get-iam-policy",
                    "gcloud iam service-accounts keys list"
                ]
            },
            "metadata":
                self._metadata(
                    completeness="Complete"
                )
        }

    # ==========================================================
    # Additional discovery-only technologies
    # ==========================================================

    def list_storage_buckets(self, project_id):

        buckets = self._run_gcloud([
            "gcloud",
            "storage",
            "buckets",
            "list",
            "--project",
            project_id,
            "--format=json"
        ])

        return buckets if isinstance(buckets, list) else []


    def describe_storage_bucket(
            self,
            project_id,
            bucket_name):
        """Returns the live configuration of one Cloud Storage bucket."""

        name = str(bucket_name or "").strip()

        if not name:
            raise ValueError("Cloud Storage bucket name is required.")

        if not name.startswith("gs://"):
            name = f"gs://{name}"

        return self._run_gcloud([
            "gcloud",
            "storage",
            "buckets",
            "describe",
            name,
            "--project",
            project_id,
            "--format=json"
        ])

    def load_live_storage_evidence(
            self,
            project_id,
            bucket_name):
        """
        Collects normalised encryption-at-rest evidence for a
        Cloud Storage bucket.

        Google Cloud Storage encrypts data at rest by default.
        A configured default KMS key indicates CMEK; otherwise
        the bucket uses Google-managed encryption keys (GMEK).
        """

        bucket = self.describe_storage_bucket(
            project_id,
            bucket_name
        )

        encryption = bucket.get("encryption", {}) or {}
        default_kms_key = encryption.get("defaultKmsKeyName")

        normalised_name = (
            bucket.get("name")
            or str(bucket_name).replace("gs://", "")
        )

        technical = {
            "location": bucket.get("location"),
            "locationType": bucket.get("locationType"),
            "storageClass": bucket.get("storageClass"),
            "uniformBucketLevelAccess": (
                bucket.get("iamConfiguration", {})
                .get("uniformBucketLevelAccess", {})
                .get("enabled")
            ),
            "publicAccessPrevention": (
                bucket.get("iamConfiguration", {})
                .get("publicAccessPrevention")
            ),
            "defaultKmsKeyName": default_kms_key,
            "cmekConfigured": bool(default_kms_key),
            "encryption": "CMEK" if default_kms_key else "GMEK",
            "dataAtRestEncrypted": True
        }

        return {
            "rawEvidence": bucket,
            "resource": {
                "cloudPlatform": "Google Cloud Platform",
                "projectId": project_id,
                "project": project_id,
                "environment": "Production",
                "service": "Cloud Storage",
                "resourceType": "Cloud Storage Bucket",
                "resourceName": normalised_name,
                "location": bucket.get("location")
            },
            "technicalEvidence": technical,
            "operationalEvidence": {
                "auditSource": "Google Cloud CLI",
                "collectionCommand": "gcloud storage buckets describe"
            },
            "metadata": self._metadata(
                completeness="Complete"
            )
        }

    def list_vpc_networks(self, project_id):

        networks = self._run_gcloud([
            "gcloud",
            "compute",
            "networks",
            "list",
            "--project",
            project_id,
            "--format=json"
        ])

        return networks if isinstance(networks, list) else []

    def list_pubsub_topics(self, project_id):

        topics = self._run_gcloud([
            "gcloud",
            "pubsub",
            "topics",
            "list",
            "--project",
            project_id,
            "--format=json"
        ])

        return topics if isinstance(topics, list) else []

    def list_secrets(self, project_id):

        secrets = self._run_gcloud([
            "gcloud",
            "secrets",
            "list",
            "--project",
            project_id,
            "--format=json"
        ])

        return secrets if isinstance(secrets, list) else []

    # ==========================================================
    # Helpers
    # ==========================================================

    def _normalise_database_engine(
            self,
            database_version):

        value = str(
            database_version or ""
        ).upper()

        if value.startswith("POSTGRES"):
            return "PostgreSQL"

        if value.startswith("MYSQL"):
            return "MySQL"

        if value.startswith("SQLSERVER"):
            return "SQL Server"

        return database_version or "Unknown"

    def _metadata(self, completeness):

        return {
            "schemaVersion":
                "3.0",
            "collector":
                "EvidenceService",
            "collectedBy":
                "Evidence Acquisition Layer",
            "collectionMode":
                "LIVE_GCLOUD",
            "mode":
                "Live",
            "provider":
                "Google Cloud",
            "confidence":
                "High",
            "completeness":
                completeness,
            "snapshotTime":
                datetime.now(
                    timezone.utc
                ).isoformat()
        }

    def _determine_completeness(
            self,
            technical,
            required_fields):

        missing = [
            field
            for field in required_fields
            if technical.get(field) is None
        ]

        if not missing:
            return "Complete"

        return (
            "Partial - missing: "
            + ", ".join(missing)
        )
