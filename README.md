# 📊 Agent Analytics for Google ADK (Designed for BigQuery Agent Analytics Plugin data)

**Agent Analytics** is a comprehensive **LLM observability suite** designed for conversational agents built with the **Google Agent Development Kit (ADK)**. It transforms raw **BigQuery** agent logs configured from **BigQuery Agent Analytics Plugin** into actionable intelligence, providing powerful **Grafana dashboards** for tracking LLM token costs, system latency, precision metrics, and full-text session transcripts.

> **Keywords**: BigQuery Agent Analytics Plugin, Grafana Dashboards, Google Agent Development Kit, ADK, LLM Observability, Generative AI Metrics, Conversational Agent Monitoring, AI Telemetry.

**Minimum ADK Version:** 1.19.0  
**Tested With:** 1.26.0

> [!IMPORTANT]
> These **8 custom master views** are specific to this observability suite and its data layering strategy. They are distinct from the standard views functionality introduced in ADK version 1.27.0+.

---

---

## 🛠️ Requirements & Manual Setup

### Requirements
- **Google ADK Configured with BigQuery Agent Analytics Plugin**: Follow the [official integration guide](https://google.github.io/adk-docs/integrations/bigquery-agent-analytics/#use-with-agent) to ensure your agent is emitting logs to BigQuery.

       from google.adk.plugins.bigquery_agent_analytics_plugin import ( BigQueryAgentAnalyticsPlugin, BigQueryLoggerConfig)
  
- **Google Cloud SDK** (authenticated)
- **BigQuery** (with ADK logs)
- **Grafana** (with BigQuery Data Source plugin)

## 📈 Maintaining Model Pricing

The FinOps and LLM Audit dashboards calculate costs based on the `model_pricing` table created in `setup/setup_bq_views.py`. 

To update pricing or add new models:
1.  **Modify SQL**: Update rows in the `pricing_sql` block of [setup/setup_bq_views.py](setup/setup_bq_views.py) (lines 10-20).
2.  **Re-Run Setup**: Execute `python3 setup/setup_bq_views.py` with your environment parameters.

> [!TIP]
> **Pricing Resilience**: As of v1.3.25, the views use `COALESCE(..., 0)`. If a model is missing from the pricing table, the dashboard will display a **$0** cost instead of `NULL` (which would hide the session from some charts).

### Manual Setup Steps
If you prefer not to use the automated scripts, follow these steps:
1.  **Service Account**: Create a GCP Service Account with `BigQuery Data Viewer` and `BigQuery Job User` roles. Download the JSON key.
2.  **SQL Views**: Manually execute the queries found in [docs/bq_dashboard_views.md](docs/bq_dashboard_views.md).
3.  **Grafana Datasource**: Add the BigQuery datasource in Grafana using your Service Account key.
4.  **Import Dashboard JSONs**: Manually import the `.template.json` files from `dashboard_templates/`.
    *   **⚠️ CRITICAL**: You must manually Search & Replace these 4 placeholders in the JSON files before importing:
        *   `${gcp_project}` -> Your Google Cloud Project ID
        *   `${bq_dataset}` -> Your BigQuery Dataset ID
        *   `${bq_table}` -> Your Base BigQuery Table ID
        *   `${datasource}` -> Your Grafana BigQuery Datasource UID

---

## 🚀 Quick Start (2-Command Deployment)

Deploy the entire analytics stack using our automated scripts:

### 1. Setup the BigQuery Data Layer
Creates the **8 custom master analytical views** (flattened JSON, costs, latencies).
```bash
python3 setup/setup_bq_views.py --project <PROJECT_ID> --dataset <DATASET_ID> --table <TABLE_NAME>
```

### 2. Setup the Grafana Visual Layer (Optional)
Configures and imports 7 interconnected dashboards into your target Grafana folder. **Parameters like `--datasource-uid` can be auto-detected if omitted.**
```bash
python3 setup/setup_dashboards.py --project <PROJECT_ID> --dataset <DATASET_ID> --table <TABLE_NAME> --url <GRAFANA_URL>
```
> [!TIP]
> Both scripts are interactive. If you omit any required flags, the script will prompt you for them during execution.

---

## ⚙️ Installation & Managing Grafana (macOS/Homebrew)

### 1. Installation
If you don't have Grafana installed, use Homebrew:
```bash
# 1. Install Grafana
brew install grafana

# 2. Add BigQuery Plugin (Required)
grafana-cli plugins install grafana-google-bigquery-datasource
```

### 2. Service Management
Use these commands to manage the background service:

| Action | Command |
| :--- | :--- |
| **Start** | `brew services start grafana` |
| **Stop** | `brew services stop grafana` |
| **Restart** | `brew services restart grafana` |
| **Status** | `brew services list` |

> [!NOTE]
> Once started, access your local dashboard at [http://localhost:3000](http://localhost:3000).

The Agent Analytics Suite is now 100% production-ready, interactive, and calibrated for forensic recency (v1.3.0).

---

---

## 🖼️ Dashboard Gallery

### 🏠 Agent Home (Landing)
Executive overview of fleet performance (Sessions, User Questions, Tokens, Cost).
- **NEW (v1.3.29)**: Integrated **User Intent** (What people are asking) directly onto the homepage with a full-width, zero-scroll layout.
- **NEW (v1.3.28)**: Global **Column Filtering** enabled across all major tables.

![Home 1](assets/Home_v2.jpg)
![Home 2](assets/Home_2_v2.jpg)
![Home 3](assets/Home_3_v2.jpg)


### 💰 FinOps & 🛠️ Diagnostics
Deep dives into token costs and system latency/errors.

![FinOps 1](assets/Finops_v2.jpg)
![FinOps 2](assets/Finops2_v2.jpg)
![Diagnostics 1](assets/Diagnostcis1_v2.jpg)
![Diagnostics 2](assets/Diagnostcis2_v2.jpg)
![Diagnostics 3](assets/Diagnostcis3_v2.jpg)

### 💬 Transcripts & 📜 Technical Traces
Turn-by-turn chat logs and trace-level tool payload auditing with **Full Content Expansion (Inspect Mode)**.

![Transcripts](assets/Transcripts_v2.jpg)
![Technical Traces](assets/Traces_v2.jpg)

### 🧠 LLM & Prompt Audit
Context inflation tracking and raw prompt-response evaluation.

![LLM Audit](assets/LLM_Audit.jpg)

### 📖 Agent Intelligence Guide
A centralized documentation hub for metric glossaries and system architecture usage.

---

## 🏗️ Documentation Structure

| Document | Focus | Contents |
| :--- | :--- | :--- |
| README.md | **Setup** | Fast deployment & manual prep. |
| bq_dashboard_views.md | **Understanding Views** | [SQL logic & field mappings](docs/bq_dashboard_views.md). |
| dashboard_spec.md | **Understanding Dashboards** | [Business metrics & panel definitions](docs/dashboard_spec.md). |
| grafana_architecture_guide.md | **Architecture** | [Drill-down logic & navigation](docs/grafana_architecture_guide.md). |

---

## 👤 Author

Developed and maintained by **Tanuj Bolisetty**.

---

*Empowering Transparent AI - Built for Google ADK Developers.*
