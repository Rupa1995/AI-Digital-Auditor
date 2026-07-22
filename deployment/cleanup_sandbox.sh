#!/bin/bash

###############################################################################
#
# AI Digital Auditor
#
# Version : 1.0
#
# Google Cloud Sandbox Cleanup Script
#
###############################################################################

set -e

###############################################################################
# Helper Functions
###############################################################################

success() {

    echo "✅ $1"

}

info() {

    echo "ℹ️  $1"

}

###############################################################################
# Configuration
###############################################################################

PROJECT_ID=$(gcloud config get-value project)

REGION="us-central1"

REPOSITORY="ai-digital-auditor"

SERVICE="ai-digital-auditor-mvp"

###############################################################################
# Display
###############################################################################

echo ""

echo "=============================================================="

echo "           AI DIGITAL AUDITOR"

echo "             SANDBOX CLEANUP"

echo "=============================================================="

echo ""

echo "Project : ${PROJECT_ID}"

echo ""

read -p "Delete Cloud Run Service and Artifact Registry? (y/N): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]
then

    echo ""

    echo "Cleanup cancelled."

    echo ""

    exit 0

fi

###############################################################################
# Delete Cloud Run
###############################################################################

info "Removing Cloud Run service..."

if gcloud run services describe \
    ${SERVICE} \
    --region=${REGION} >/dev/null 2>&1
then

    gcloud run services delete \
        ${SERVICE} \
        --region=${REGION} \
        --quiet

    success "Cloud Run service deleted"

else

    info "Cloud Run service does not exist."

fi

###############################################################################
# Delete Artifact Registry
###############################################################################

info "Removing Artifact Registry..."

if gcloud artifacts repositories describe \
    ${REPOSITORY} \
    --location=${REGION} >/dev/null 2>&1
then

    gcloud artifacts repositories delete \
        ${REPOSITORY} \
        --location=${REGION} \
        --quiet

    success "Artifact Registry deleted"

else

    info "Artifact Registry does not exist."

fi

###############################################################################
# Summary
###############################################################################

echo ""

echo "=============================================================="

echo "Cleanup Completed"

echo ""

echo "Project : ${PROJECT_ID}"

echo ""

echo "=============================================================="

echo ""