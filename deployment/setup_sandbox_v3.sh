#!/bin/bash

###############################################################################
#
# AI Digital Auditor
#
# Version : 3.0
#
# Google Cloud Run Deployment Script
#
# Purpose
# -------
# Builds the current application container, pushes it to Artifact Registry,
# passes the Gemini API key to Cloud Run as an environment variable and
# deploys a new immutable Cloud Run revision into the active Google Cloud project.
#
###############################################################################

set -euo pipefail

###############################################################################
# Helper Functions
###############################################################################

success() {
    echo "✅ $1"
}

info() {
    echo "ℹ️  $1"
}

warning() {
    echo "⚠️  $1"
}

error() {
    echo ""
    echo "❌ ERROR"
    echo ""
    echo "$1"
    echo ""
    exit 1
}

###############################################################################
# Step 1 - Verify Required Local Tools
###############################################################################

info "Checking required local tools..."

command -v gcloud >/dev/null 2>&1 || \
    error "Google Cloud SDK is not installed."

command -v python >/dev/null 2>&1 || \
    error "Python is not available in the active environment."

success "Required local tools found"

###############################################################################
# Step 2 - Verify Authentication
###############################################################################

info "Checking Google Cloud authentication..."

if ! gcloud auth print-access-token >/dev/null 2>&1
then
    error "Authentication failed.

Execute:

gcloud auth login"
fi

ACCOUNT=$(gcloud config get-value account 2>/dev/null)

[ -n "${ACCOUNT}" ] || \
    error "No authenticated Google Cloud account was detected."

success "Authentication valid"
success "Authenticated account: ${ACCOUNT}"

###############################################################################
# Step 3 - Detect Active Project
###############################################################################

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]
then
    error "No active Google Cloud project is configured.

Execute:

gcloud config set project PROJECT_ID"
fi

###############################################################################
# Configuration
###############################################################################

REGION="us-central1"
REPOSITORY="ai-digital-auditor"
SERVICE="ai-digital-auditor-mvp"
RUNTIME_SA=""

# Immutable deployment tag.
TAG="v1.0-hackathon-$(date -u +%Y%m%d-%H%M%S)"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/ai-digital-auditor:${TAG}"

###############################################################################
# Display Configuration
###############################################################################

echo ""
echo "----------------------------------------------------------"
echo "Deployment Configuration"
echo "----------------------------------------------------------"
echo "Account          : ${ACCOUNT}"
echo "Project          : ${PROJECT_ID}"
echo "Region           : ${REGION}"
echo "Repository       : ${REPOSITORY}"
echo "Service          : ${SERVICE}"
echo "Runtime identity : Existing Cloud Run identity or project default"
echo "Image tag        : ${TAG}"
echo "----------------------------------------------------------"
echo ""

###############################################################################
# Step 4 - Verify Project Files
###############################################################################

info "Checking project files..."

[ -f Dockerfile ] || error "Dockerfile not found."
[ -f requirements.txt ] || error "requirements.txt not found."
[ -f streamlit_app.py ] || error "streamlit_app.py not found."
[ -d services ] || error "services directory not found."
[ -d ui ] || error "ui directory not found."
[ -d governance/controls ] || error "governance/controls directory not found."
[ -f .env ] || error ".env file not found."

success "Project files verified"

###############################################################################
# Step 5 - Local Syntax Verification
###############################################################################

info "Running local Python syntax verification..."

python -m py_compile services/*.py
python -m py_compile ui/*.py
python -m py_compile streamlit_app.py

success "Python syntax verification completed"

###############################################################################
# Step 6 - Load Local Deployment Variables
###############################################################################

info "Loading local environment variables..."

set -a
# shellcheck disable=SC1091
source .env
set +a

[ -n "${GEMINI_API_KEY:-}" ] || \
    error "GEMINI_API_KEY is missing from .env."

GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"

success "Local deployment variables loaded"

###############################################################################
# Step 7 - Configure Region
###############################################################################

info "Configuring Cloud Run region..."

gcloud config set run/region "${REGION}" \
    --quiet >/dev/null

success "Region configured"

###############################################################################
# Step 8 - Enable Required APIs
###############################################################################

info "Enabling required Google Cloud APIs..."

gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    compute.googleapis.com \
    pubsub.googleapis.com \
    --quiet >/dev/null

success "Required APIs enabled"

###############################################################################
# Step 9 - Wait for Cloud Build
###############################################################################

info "Waiting for Cloud Build service..."

MAX_RETRIES=12
RETRY=1

while [ "${RETRY}" -le "${MAX_RETRIES}" ]
do
    if gcloud builds list --limit=1 >/dev/null 2>&1
    then
        success "Cloud Build is ready"
        break
    fi

    echo "   Waiting... (${RETRY}/${MAX_RETRIES})"
    sleep 10
    RETRY=$((RETRY + 1))
done

if [ "${RETRY}" -gt "${MAX_RETRIES}" ]
then
    error "Cloud Build did not become ready within 2 minutes."
fi

###############################################################################
# Step 10 - Artifact Registry
###############################################################################

info "Checking Artifact Registry..."

if gcloud artifacts repositories describe \
    "${REPOSITORY}" \
    --location="${REGION}" >/dev/null 2>&1
then
    success "Artifact Registry already exists"
else
    info "Creating Artifact Registry..."

    gcloud artifacts repositories create \
        "${REPOSITORY}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="AI Digital Auditor Docker Repository" \
        --quiet >/dev/null

    success "Artifact Registry created"
fi

###############################################################################
# Step 11 - Detect Existing Runtime Identity
###############################################################################

info "Checking existing Cloud Run runtime identity..."

EXISTING_RUNTIME_SA=$(gcloud run services describe \
    "${SERVICE}" \
    --region="${REGION}" \
    --format="value(spec.template.spec.serviceAccountName)" \
    2>/dev/null || true)

if [ -n "${EXISTING_RUNTIME_SA}" ]
then
    RUNTIME_SA="${EXISTING_RUNTIME_SA}"
    success "Existing runtime identity detected: ${RUNTIME_SA}"
else
    RUNTIME_SA=""
    warning "No existing Cloud Run runtime identity detected."
    warning "Cloud Run will use the sandbox project's default runtime identity."
fi

warning "Project IAM bindings are not modified because this sandbox"
warning "does not grant resourcemanager.projects.setIamPolicy."

###############################################################################
# Step 12 - Build and Push Immutable Docker Image
###############################################################################

info "Building and pushing Docker image..."

gcloud builds submit \
    --quiet \
    --tag="${IMAGE}" \
    .

success "Docker image built and pushed"
success "Image: ${IMAGE}"

###############################################################################
# Step 13 - Deploy Cloud Run Revision
###############################################################################

info "Deploying Cloud Run service..."

if [ -n "${RUNTIME_SA}" ]
then
    gcloud run deploy "${SERVICE}" \
        --quiet \
        --image="${IMAGE}" \
        --region="${REGION}" \
        --service-account="${RUNTIME_SA}" \
        --allow-unauthenticated \
        --port=8080 \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300 \
        --min-instances=1 \
        --max-instances=1 \
        --concurrency=10 \
        --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},GEMINI_MODEL=${GEMINI_MODEL}" \
        >/dev/null
else
    gcloud run deploy "${SERVICE}" \
        --quiet \
        --image="${IMAGE}" \
        --region="${REGION}" \
        --allow-unauthenticated \
        --port=8080 \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300 \
        --min-instances=1 \
        --max-instances=1 \
        --concurrency=10 \
        --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},GEMINI_MODEL=${GEMINI_MODEL}" \
        >/dev/null
fi

success "Cloud Run deployment completed"

###############################################################################
# Step 14 - Verify Deployment
###############################################################################

info "Retrieving Cloud Run deployment details..."

URL=$(gcloud run services describe \
    "${SERVICE}" \
    --region="${REGION}" \
    --format="value(status.url)")

REVISION=$(gcloud run services describe \
    "${SERVICE}" \
    --region="${REGION}" \
    --format="value(status.latestReadyRevisionName)")

if [ -z "${URL}" ]
then
    error "Unable to retrieve Cloud Run URL."
fi

success "Application deployed successfully"

###############################################################################
# Step 15 - Deployment Summary
###############################################################################

echo ""
echo "=============================================================="
echo "           AI DIGITAL AUDITOR"
echo "          DEPLOYMENT SUCCESSFUL"
echo "=============================================================="
echo ""
echo "Google Cloud Account"
echo "    ${ACCOUNT}"
echo ""
echo "Google Cloud Project"
echo "    ${PROJECT_ID}"
echo ""
echo "Region"
echo "    ${REGION}"
echo ""
echo "Cloud Run Service"
echo "    ${SERVICE}"
echo ""
echo "Runtime Identity"
if [ -n "${RUNTIME_SA}" ]
then
    echo "    ${RUNTIME_SA}"
else
    echo "    Project default Cloud Run identity"
fi
echo ""
echo "Cloud Run Revision"
echo "    ${REVISION}"
echo ""
echo "Container Image"
echo "    ${IMAGE}"
echo ""
echo "Application URL"
echo "    ${URL}"
echo ""
echo "=============================================================="
echo ""
echo "Smoke-test checklist:"
echo "  1. Login page loads"
echo "  2. Project discovery completes"
echo "  3. Cloud SQL, IAM and Cloud Storage are discovered"
echo "  4. Enterprise and technology controls load"
echo "  5. AI planning completes"
echo "  6. Deterministic validation completes"
echo "  7. Dashboard, commentary and AI chat work"
echo ""
echo "For a future sandbox project:"
echo ""
echo "    gcloud auth login"
echo "    gcloud config set project PROJECT_ID"
echo "    ./deployment/setup_sandbox_v3.sh"
echo ""
echo "=============================================================="
echo ""
