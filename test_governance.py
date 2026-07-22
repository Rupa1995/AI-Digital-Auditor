from services.governance_knowledge_service import GovernanceKnowledgeService

service = GovernanceKnowledgeService()

knowledge = service.load_governance()

print("\nControls\n")
for control in knowledge["controls"]:
    print(control["document"])
    print(control["technology"])
    print(control["content"][:300])
    print("-" * 60)

print("\nADRs\n")
for adr in knowledge["adrs"]:
    print(adr["document"])
    print(adr["content"][:300])
    print("-" * 60)