# ------------------------------------------------------
# AI Digital Auditor
# Dockerfile for Google Cloud Run (MVP)
# ------------------------------------------------------

FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# ------------------------------------------------------
# Install OS packages + Google Cloud CLI
# ------------------------------------------------------

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    && curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
       | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
       > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update \
    && apt-get install -y google-cloud-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------
# Install Python dependencies
# ------------------------------------------------------

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------
# Copy application
# ------------------------------------------------------

COPY . .

# ------------------------------------------------------
# Cloud Run
# ------------------------------------------------------

EXPOSE 8080

CMD sh -c "streamlit run streamlit_app.py \
--server.port=${PORT:-8080} \
--server.address=0.0.0.0 \
--server.headless=true"