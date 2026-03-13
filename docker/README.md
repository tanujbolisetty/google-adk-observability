# 🐳 Agent Analytics - Docker Distribution

This directory contains the necessary components to run the **Agent Analytics** suite in a zero-config, portable environment using Docker.

## 🚀 Instant Deployment

The Docker setup automatically installs the BigQuery plugin, provisions your datasource, and pre-loads all 5 analytical dashboards.

### 1. Prerequisite: Authenticate Local Machine
The container is designed to leverage your local **Application Default Credentials (ADC)**. Ensure you are logged in on your host machine:
```bash
gcloud auth application-default login
```

### 2. Configure Environment
Create a `.env` file in this directory or export these variables:
```bash
export GCP_PROJECT="your-project-id"
export BQ_DATASET="your_dataset"
export BQ_TABLE="your_base_table"
```

### 3. Start the Suite
From the project root:
```bash
docker-compose -f docker/docker-compose.yml up --build
```

---

## 🏗️ How it Works

### 1. Authentication Strategy (ADC)
The `docker-compose.yml` mounts your local `${HOME}/.config/gcloud` directory into the container. This allows the internal Grafana process to "inherit" your existing GCP connectivity without requiring you to manage service account JSON keys manually.

### 2. Automatic Dashboard Provisioning
On startup, the `entrypoint.sh` script performs a "Search & Replace" on the dashboard template files. It injects your `GCP_PROJECT`, `BQ_DATASET`, and `BQ_TABLE` variables directly into the JSON models.

### 3. Cleanup
To stop the services:
```bash
docker-compose -f docker/docker-compose.yml down
```

---

## ☁️ Cloud Deployment (GKE / Cloud Run)

When deploying to managed Google Cloud environments, you **do not** need to mount local credentials.

### 1. Native Authentication
GKE and Cloud Run use **Service Account Delegation**. Instead of mounting a `.config/gcloud` folder, you simply assign a Service Account to the pod or service with the following roles:
- `BigQuery Data Viewer`
- `BigQuery Job User`

### 2. No Code Changes Needed
The Google BigQuery plugin for Grafana is "Cloud Aware." If it doesn't find a mounted key, it automatically queries the **GCP Metadata Server** for a token. This means the same Docker image works locally *and* in production without modification.

### 3. Environment Variables
In your GKE Manifest or Cloud Run configuration, simply provide the standard environment variables:
- `GCP_PROJECT`
- `BQ_DATASET`
- `BQ_TABLE`

---

*Note: For manual setup instructions without Docker, refer to the root [README.md](../README.md).*
