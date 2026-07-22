from services.evidence_service import EvidenceService

service = EvidenceService()

project_id = "playground-s-11-17660622"

instances = service.list_cloudsql_instances(project_id)

print("Instances Found:")
print("----------------")

for instance in instances:
    print(instance["name"])

print()

evidence = service.load_live_evidence(
    project_id,
    "sql"
)

print("Evidence")
print("--------")

for key, value in evidence.items():
    print(f"{key}: {value}")