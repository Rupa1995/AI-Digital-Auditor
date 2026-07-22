# Developer Guide

# AI Digital Auditor

> Developer onboarding and implementation guide.

---

# 1. Purpose

This guide explains how the application is organised, how the modules interact, and how to extend the platform.

Audience:

- Software Developers
- Infrastructure Engineers
- Platform Engineers

---

# 2. Application Startup

Application entry points:

```text
streamlit_app.py   -> Streamlit launcher
app.py             -> Main application orchestration
```

Startup flow:

```text
User
  |
  v
Streamlit
  |
  v
Application Bootstrap
  |
  v
Service Initialization
  |
  v
Audit Execution
```

---

# 3. Project Structure

```text
AI-Digital-Auditor/

app.py
streamlit_app.py

assets/
deployment/
evidence/
governance/
prompts/
schemas/
services/
ui/
```

| Folder | Description |
|---------|-------------|
| services | Core application logic |
| ui | Streamlit pages and widgets |
| governance | Enterprise controls, standards, ADRs |
| prompts | Gemini prompt templates |
| evidence | Sample or cached evidence |
| deployment | Docker and Cloud Run deployment |
| schemas | JSON schemas |
| assets | Static assets |

---

# 4. Core Services

## Discovery Service

Responsibilities

- Discover Cloud SQL
- Discover IAM
- Discover Cloud Storage

Output

A normalized inventory used by downstream services.

---

## Evidence Service

Collects live configuration from Google Cloud APIs.

Responsibilities

- Retrieve metadata
- Normalize evidence
- Return evidence objects

---

## Validation Engine

Executes deterministic technical checks.

Typical validators

- Cloud SQL
- IAM
- Cloud Storage

Returns

- PASS
- FAIL
- Observation
- Recommendation

---

## Governance Service

Loads enterprise governance artefacts.

Includes

- Enterprise Controls
- Technology Controls
- Standards
- ADRs

These artefacts are consumed by the AI layer.

---

## AI Service

Uses Gemini to:

- Interpret governance
- Generate executive commentary
- Power Ask AI Auditor

The AI is not responsible for PASS/FAIL decisions.

---

# 5. Request Processing

```text
Start Audit
    |
    v
Discovery
    |
    v
Governance Load
    |
    v
Evidence Collection
    |
    v
Validation
    |
    v
Workpaper
    |
    +--> Dashboard
    |
    +--> AI Commentary
    |
    +--> AI Chat
```

---

# 6. Adding a New Technology

To onboard a new Google Cloud service:

1. Add discovery logic.
2. Add evidence collection.
3. Implement deterministic validators.
4. Create technology controls.
5. Register the technology with the orchestration flow.

Example targets:

- Compute Engine
- GKE
- BigQuery
- Cloud KMS
- Secret Manager

---

# 7. Coding Guidelines

- Keep services independent.
- Separate AI reasoning from deterministic validation.
- Avoid embedding business logic in the UI.
- Reuse common data models.
- Prefer configuration over hardcoding.

---

# 8. Deployment

Development

```text
Local
  |
Docker
  |
Cloud Build
  |
Artifact Registry
  |
Cloud Run
```

Environment variables

```text
GEMINI_API_KEY
GEMINI_MODEL
```

---

# 9. Troubleshooting

## Discovery fails

Check:

- Active GCP project
- Authentication
- Required APIs
- Runtime permissions

## AI responses fail

Check:

- GEMINI_API_KEY
- Network connectivity
- Gemini model configuration

## Deployment fails

Verify:

- Dockerfile
- requirements.txt
- Cloud Build logs
- Cloud Run logs

---

# 10. Design Philosophy

The application deliberately separates responsibilities.

| Layer | Responsibility |
|-------|----------------|
| Governance | Defines what should be audited |
| AI | Understands governance and explains results |
| Discovery | Finds in-scope resources |
| Evidence | Collects cloud configuration |
| Validation | Executes deterministic controls |
| Workpaper | Stores audit results |
| UI | Presents results |

This separation makes the platform easier to maintain, test and extend.

---

# 11. Extensibility Checklist

When introducing a new audit capability:

- [ ] Discovery implemented
- [ ] Evidence collector implemented
- [ ] Validator implemented
- [ ] Controls updated
- [ ] AI prompt reviewed
- [ ] Dashboard updated (if required)
- [ ] Documentation updated

---

# 12. Future Enhancements

Planned evolution includes:

- Evidence-centric audit methodology
- Additional GCP services
- Multi-cloud support
- Document evidence ingestion
- Interview-based evidence collection
- Enhanced AI audit planning
