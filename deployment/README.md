# AI Digital Auditor

## Google Cloud Deployment Guide

This folder contains the deployment utilities for the AI Digital Auditor MVP.

---

# Prerequisites

Before deploying the application, ensure the following:

- Google Cloud SDK is installed
- Python virtual environment is activated
- Dockerfile exists
- requirements.txt exists
- streamlit_app.py exists
- .env file exists

---

# Authentication

Authenticate using your Google Cloud account.

```bash
gcloud auth login
```

---

# Select the Google Cloud Project

Configure the active project.

```bash
gcloud config set project PROJECT_ID
```

Verify the project.

```bash
gcloud config get-value project
```

---

# Deploy the Application

Execute the deployment script.

```bash
./deployment/setup_sandbox.sh
```

The deployment script automatically performs the following tasks:

- Verifies Google Cloud SDK
- Verifies Google Cloud authentication
- Detects the active Google Cloud project
- Validates required project files
- Loads environment variables from .env
- Configures the Cloud Run region
- Enables required Google Cloud APIs
- Waits for Cloud Build readiness
- Creates the Artifact Registry (if required)
- Builds the Docker image
- Deploys the application to Cloud Run
- Displays the Cloud Run URL

---

# Access the Application

After deployment completes successfully, the script displays the application URL.

Example:

```
https://ai-digital-auditor-mvp-xxxxxxxxxx.us-central1.run.app
```

---

# Clean Up Resources

To remove the deployed resources:

```bash
./deployment/cleanup_sandbox.sh
```

The cleanup script removes:

- Cloud Run Service
- Artifact Registry Repository

The Google Cloud project itself is **not** deleted.

---

# Typical Development Workflow

Activate the Python virtual environment.

```bash
source .venv/bin/activate
```

Authenticate.

```bash
gcloud auth login
```

Select the Google Cloud project.

```bash
gcloud config set project PROJECT_ID
```

Deploy.

```bash
./deployment/setup_sandbox.sh
```

Open the application using the Cloud Run URL.

When development is complete (optional):

```bash
./deployment/cleanup_sandbox.sh
```

---

# MVP Deployment Architecture

```
Developer
      │
      ▼
setup_sandbox.sh
      │
      ▼
Google Cloud APIs
      │
      ├── Cloud Build
      ├── Artifact Registry
      ├── Cloud Run
      ├── Cloud Resource Manager
      └── Cloud SQL Admin
      │
      ▼
Docker Image
      │
      ▼
Cloud Run
      │
      ▼
AI Digital Auditor
```

---

# Design Principles

The deployment framework for the MVP was intentionally designed with the following principles:

- Simple
- Repeatable
- Automated
- Cloud Native
- Minimal manual intervention

---

# Future Improvements

The following enhancements are planned for future releases:

- Replace Google Cloud CLI with the Google Cloud Python SDK
- Store secrets in Google Secret Manager
- Implement CI/CD using Cloud Build or GitHub Actions
- Use dedicated service accounts with least-privilege IAM roles
- Persist audit reports in Cloud Storage or Firestore
- Add Cloud Monitoring dashboards
- Add centralized logging
- Add automated integration testing