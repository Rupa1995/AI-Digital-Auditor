# AI Digital Auditor

> **AI-Assisted Enterprise Technology Audit Platform for Google Cloud**

## Executive Summary

AI Digital Auditor is a governance-driven audit platform that combines **Enterprise Controls**, **AI reasoning**, **live Google Cloud evidence collection**, and **deterministic validation** to automate infrastructure audits.

Unlike traditional compliance scanners that simply execute predefined technical checks, AI Digital Auditor starts with **enterprise governance**. The AI interprets enterprise controls, determines which cloud technologies are in scope, orchestrates evidence collection, executes deterministic validators, and produces an explainable audit assessment.

---

# High-Level Architecture

```text
                   Enterprise Governance
         (Controls, Standards, ADRs, Methodology)
                           │
                           ▼
                AI Audit Intelligence Engine
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
 Technology Discovery   Evidence        AI Planning &
 (Cloud SQL/IAM/       Collection       Commentary
 Cloud Storage)
          │                │
          └────────────────┼────────────────┘
                           ▼
              Deterministic Validation Engine
                           │
                           ▼
                 Audit Workpaper & Dashboard
                           │
                           ▼
                    Ask AI Auditor (Chat)
```

---

# Audit Lifecycle

```text
User Starts Audit
        │
        ▼
Discover GCP Resources
        │
        ▼
Load Enterprise Controls
        │
        ▼
AI Interprets Controls
        │
        ▼
Collect Live Evidence
        │
        ▼
Execute Deterministic Validation
        │
        ▼
Generate Workpaper
        │
        ▼
Generate AI Commentary
        │
        ▼
Interactive AI Auditor
```

---

# Repository Structure

```text
AI-Digital-Auditor/
│
├── app.py                 Application entry point
├── streamlit_app.py       Streamlit launcher
│
├── ui/                    User interface pages
├── services/              Core business services
├── governance/            Enterprise controls & standards
├── evidence/              Sample/mock evidence
├── prompts/               Gemini prompts
├── schemas/               JSON schemas
├── assets/                Images & branding
├── deployment/            Docker & Cloud Run scripts
└── requirements.txt
```

---

# Core Components

## 1. Streamlit UI

Provides the end-user experience.

Responsibilities:

- Authentication
- Project selection
- Audit execution
- Dashboard
- AI Chat

---

## 2. AI Audit Intelligence

Central reasoning engine.

Responsibilities:

- Reads enterprise controls
- Interprets control intent
- Maps controls to cloud technologies
- Produces audit commentary
- Answers audit questions

The AI **does not** perform technical validation.

---

## 3. Technology Discovery

Discovers supported GCP services.

Current MVP:

- Cloud SQL
- IAM
- Cloud Storage

Returns discovered resources for downstream validation.

---

## 4. Governance Repository

Contains enterprise governance artefacts.

Includes:

- Enterprise Controls
- Technology Controls
- Standards
- ADRs
- Audit Methodology

These documents drive AI reasoning.

---

## 5. Evidence Collection

Collects authoritative evidence from Google Cloud APIs.

Examples:

- Cloud SQL configuration
- IAM policies
- Storage bucket metadata

---

## 6. Deterministic Validation Engine

Executes repeatable technical controls.

Current validators include:

- Cloud SQL encryption
- Backup & PITR
- Public IAM access
- Service Account Owner role
- Storage encryption

Produces objective PASS/FAIL findings.

---

## 7. Audit Workpaper

Consolidates:

- Evidence
- Findings
- Risks
- Recommendations
- Executive Summary

Acts as the single source of truth for the audit.

---

## 8. AI Commentary

Consumes the completed workpaper.

Generates:

- Executive summary
- Business impact
- Overall audit assessment

AI commentary never changes technical findings.

---

## 9. Ask AI Auditor

Interactive chat grounded on the completed audit.

Typical questions:

- Which controls failed?
- Which resources are non-compliant?
- Why is the audit opinion adverse?

---

# Request Flow

```text
Browser
   │
   ▼
Streamlit
   │
   ▼
Discovery Service
   │
   ▼
Evidence Service
   │
   ▼
Validation Engine
   │
   ▼
Workpaper
   │
   ├──► Dashboard
   └──► Gemini Commentary
           │
           ▼
     Ask AI Auditor
```

---

# Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python |
| UI | Streamlit |
| AI | Gemini |
| Cloud | Google Cloud Platform |
| Runtime | Cloud Run |
| Container | Docker |
| Build | Cloud Build |
| Registry | Artifact Registry |

---

# Adding a New Technology

To support another GCP service:

1. Extend Technology Discovery.
2. Add an evidence collector.
3. Implement deterministic validators.
4. Register technology controls.
5. Update AI prompts if required.

No UI changes are typically required.

---

# Deployment

```text
Developer
    │
Docker Build
    │
Cloud Build
    │
Artifact Registry
    │
Cloud Run
    │
Gemini + Google Cloud APIs
```

---

# Current MVP Scope

- Governance-driven auditing
- Enterprise control interpretation
- Cloud SQL auditing
- IAM auditing
- Cloud Storage auditing
- AI executive commentary
- Interactive AI Auditor
- Cloud Run deployment

---

# Future Roadmap

- Evidence-centric audit methodology
- Interview-based evidence collection
- Document analysis
- Multi-cloud support
- Additional GCP services
- Architecture assurance

---

## Design Philosophy

AI Digital Auditor separates **AI reasoning** from **technical validation**.

- **AI** understands governance, explains results, and assists auditors.
- **Deterministic validators** perform objective technical verification.

This architecture provides explainable, repeatable, and extensible enterprise audits.
