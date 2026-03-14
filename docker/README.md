# 🐳 Agent Analytics - Docker & GKE Distribution

This directory contains the necessary components to run the **Agent Analytics** suite in a zero-config, portable environment using Docker or Kubernetes.

## 🍎 Running on Mac (Docker Desktop)

The Docker setup allows you to run the entire stack locally with automatic project configuration.

### 1. Prerequisite: Authenticate Local Machine
The container leverages your local **Application Default Credentials (ADC)**. Ensure you are logged in:
```bash
gcloud auth application-default login
```

### 2. Configure Environment
Export your GCP and BigQuery details in your terminal:
```bash
export GCP_PROJECT="your-project-id"
export BQ_DATASET="adk_agent_logs"
export BQ_TABLE="mosa_agent_events_v2"
```

### 3. Launch the Stack
Run this command from the **root** of the repository:
```bash
docker-compose -f docker/docker-compose.yml up --build
```
*Wait for the logs to say "Grafana is now running". You can then access it at [http://localhost:3000](http://localhost:3000).*

---

## ☸️ Deploying to GKE

For cloud deployment, we use native GCP Workload Identity for authentication.

### 1. Build and Push Image
```bash
# Build the image from root
docker build -t gcr.io/${GCP_PROJECT}/agent-analytics:latest -f docker/Dockerfile .

# Push to your registry
docker push gcr.io/${GCP_PROJECT}/agent-analytics:latest
```

### 2. Configure Workload Identity
Ensure your GKE ServiceAccount has the `BigQuery Data Viewer` role.
```bash
# Example: Link K8s ServiceAccount to GCP ServiceAccount
gcloud iam service-accounts add-iam-policy-binding GSA_NAME@PROJECT_ID.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]"
```

### 3. Deploy Manifest
Apply the provided manifest:
```bash
kubectl apply -f docker/k8s-deployment.yaml
```

---

## 🏗️ How it Works

1.  **Zero-Config Entrypoint**: On startup, `entrypoint.sh` automatically injects your environment variables into the standardized `.template.json` files.
2.  **ADC Auth**: The `bigquery.yaml` datasource is configured for `gce` mode, which automatically detects credentials on Mac (via mount) and GKE (via Metadata Server).
3.  **Unified Nav**: Navigation variables are automatically persisted across all 5 dashboards.

---

### 🛑 Troubleshooting
- **Permission Denied**: On Mac, ensure Docker has permission to access `${HOME}/.config/gcloud`.
- **Placeholder Error**: If dashboards show "REPLACE_ME", verify your `GCP_PROJECT` and `BQ_DATASET` environment variables were set before running `docker-compose`.

