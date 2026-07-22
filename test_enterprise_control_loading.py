from services.governance_knowledge_service import GovernanceKnowledgeService

g=GovernanceKnowledgeService().load_governance()
for lib in g.get("controls",[]):
    for c in lib.get("controls",[]):
        print(c["id"], c.get("controlType"), c.get("statement"))
