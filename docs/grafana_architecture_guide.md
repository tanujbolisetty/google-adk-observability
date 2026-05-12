# 🏗️ Grafana Architecture: Navigation & Drill-Downs

To keep Agent telemetry clean and performant, this interface is designed as a multi-page **Dashboard Application** rather than a single, monolithic screen. This document explains how the pages interconnect.

---

## 🏗️ The 4-Tier Navigation Flow

The suite is architected to move a user from **High-Level Outcomes** to **Low-Level Traces** seamlessly:

1.  **Level 1: Agent Home (Landing Page)**
    *   *The Entry Point.* Aggregated KPIs (Total Sessions, Total Tokens).
    *   *Exit Action:* Drill into a specific **Session** or **Financial Trend**.
2.  **Level 2: Agent FinOps & Agent Diagnostics**
    *   *The Contextual View.* Performance and cost metrics filtered by User or Model.
    *   *Exit Action:* Drill into a specific **Turn** or **Prompt Trace**.
3.  **Level 3: Agent Transcript (Chat Logs) & Technical Traces**
    *   *The Qualitative & Forensic Analysis.* Viewing exactly what happened in a single conversation or tool execution.
4.  **Level 4: Agent LLM & Prompt Audit & Intelligence Guide**
    *   *Technical Governance.* Auditing model reasoning, context inflation, and metric definitions.

---

## ⚙️ Navigation State Preservation

The system preserves your view context (Time Range, User ID, Session ID) as you navigate between pages using two mechanisms:

### 1. Unified Variable Control Bar
Every dashboard shares a common set of variables. Here is how they apply across the suite:

| Filter | Agent Home | FinOps | Diagnostics | Transcript | Traces | LLM Audit | Guide |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| User ID | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| Session ID | ❌ No | ✅ Yes (All) | ✅ Yes (All) | ✅ Yes (Req)| ✅ Yes (Req)| ✅ Yes (Req)| ❌ No |
| Agent Name | ❌ No | ❌ No | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |
| Tool Name | ❌ No | ❌ No | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |

### 2. Variable Logic & Cascading
- **Cascading Filters**: Filters are "aware" of each other. For example, selecting a **User ID** automatically limits the **Session ID** list to only that user's sessions.
- **Full Symmetric Selection (v1.4)**: The system now preserves your selected User and Session context across the **entire suite**. If you are investigating a specific session in the Transcripts or Traces dashboard and click back to "Home", "FinOps", or "Diagnostics", the panels will automatically restrict their view to that specific session/user. This allows for localized "Summary Autopsies" where you can see the cost and performance impact of a single conversation within the context of the summary views.
- **Symmetric Defaults**: Summary dashboards default to "All" (fleet-wide overview) while forensic dashboards default to explicitly requiring a "Select_User" selection.
- **Diagnostics Multi-Filter**: The Diagnostics page is the only one that uses the **Agent** and **Tool** filters, allowing you to narrow down system-wide bottlenecks.

### 3. URL Data Links
We use custom **Data Links** on tables and charts to preserve full environment context. Every navigation link in the top header and every "Drill Down" link in tables propagates the following variables:
`${__url_time_range}&var-datasource=${datasource}&var-gcp_project=${gcp_project}&var-bq_dataset=${bq_dataset}&var-bq_table=${bq_table}&var-application=${application}&var-user_id=${user_id}&var-session_id=${session_id}`

This ensures that your "investigative state" remains perfectly intact as you jump between layers.

### 4. Recency-First Variable Sorting
To ensure forensic usability, all `user_id` and `session_id` dropdowns are configured with a mandatory **Recency-First** pattern:
- **Database Level**: SQL queries use `ORDER BY last_seen DESC` (where `last_seen` is `MAX(timestamp)`).
- **Grafana Level**: The variable property `sort` is set to `0` (Disabled). This forces Grafana to respect the database-level sort order rather than reverting to an alphabetical list.

### 5. Interactive Traceability (Hover Metadata)
To bridge the gap between visual charts and raw technical logs, we use **Hidden Metadata Overrides**:
- **Implementation**: Charts (like "Session Performance Profile" and "Context Inflation") include the full `invocation_id` in their SQL results.
- **Visual Hygiene**: A Grafana field override is applied to set `custom.hidden: true` for the `invocation_id` field.
- **Result**: The ID is invisible in the graph bars/legend but appears in the **hover tooltip**, allowing developers to copy-paste the exact ID into the "Traces" or "LLM Audit" table filters for a surgical autopsy of a specific turn.

---

### 6. Context Window vs. Billable Tokens
The suite maintains a clear distinction between **Financial Consumption** and **Technical Capacity**:
- **Financial Truth (Billable)**: Calculated as the **`SUM()`** of all tokens across all model calls in a session. This is shown in the **Home** and **FinOps** dashboards. Every byte sent is billed, even if it is repeated history.
- **Technical Truth (Capacity)**: Calculated as the **`MAX()`** of prompt tokens per turn. This is shown in the **LLM & Prompt Audit** "Context Inflation" chart. It represents the peak window utilization for debugging context-limits and "lost-in-the-middle" problems without the "Sawtooth Bug" of double-counting reasoning steps.

### 7. White-Labeling & Branding Standards
The project is architected for **Generic Agent Observability**:
- **Naming Standard**: Use **"Agent Analytics"** for all folder names, documentation headers, and skill definitions.
- **Project Isolation**: All dashboard templates use the `var-datasource` and `var-gcp_project` variables to ensure they can be deployed to any environment without hardcoded strings (Setup script performs literal injection for V2 stability).
- **Metadata Visibility (v1.3)**: Infrastructure-level labels (Project ID, Dataset ID, Table, Datasource) are **Visible** (`hide: 0`) by default across all dashboards to allow for rapid environment and data-path verification.
- **Purple Theme (Help Guide)**: The **Agent Intelligence Guide** uses a specialized **Purple Theme (`#B08CF5`)** to distinguish technical documentation from operational charts. This color is also used for "Agent Overhead" metrics to provide visual continuity for system diagnostics.

---

### 8. V2 Stabilization & Robustness
- **Arithmetic Safety**: All rate-based charts use `SAFE_DIVIDE` to prevent "Divide by Zero" errors during low-traffic periods.
- **Variable Fallbacks**: SQL filters handle empty or placeholder states (`IN ('Select_User', '', 'All')`) to ensure panels render correctly even when context is being loaded from the URL.
- **Forensic Isolation**: Deep-dive dashboards (Traces, Transcript, LLM Audit) strictly enforce single-session selection by disabling the "All" option, preventing "No Data" regressions.

---

## 🔗 Global Navigation Header
Every dashboard features a persistent, **2-line HTML navigation bar** at the top.

### Line 1: Functional Navigation (Pills)
Organized into three distinct visual categories to separate contexts:
- **📊 SUMMARY**: `🏠 Home` | `💰 FinOps` | `🛠️ Diagnostics`
- **🔍 FORENSICS**: `💬 Transcripts` | `📜 Traces` | `🧠 LLM Audit`
- **📚 RESOURCES**: `📖 Guide`

### Line 2: Infrastructure Status Bar (v1.3)
A non-intrusive metadata block providing persistent environment awareness:
- **🌐 Project** | **📂 Dataset** | **📄 Table** | **🔌 Source**

This unified header allows for rapid context switching while maintaining clear visibility into exactly which GCP/BigQuery environment is being audited.

---

*Empowering Transparent AI - Scalable Observability for Agentic Workflows.*
