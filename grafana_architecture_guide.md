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

| Filter | Agent Home | FinOps | Diagnostics | Transcript | Traces | LLM Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **User ID** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Session ID** | ✅ Yes (All) | ✅ Yes (All) | ✅ Yes | ✅ Yes (Req)| ✅ Yes (Req)| ✅ Yes (Req)|
| **Agent Name** | ❌ No | ❌ No | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| **Tool Name** | ❌ No | ❌ No | ✅ Yes | ❌ No | ✅ Yes | ❌ No |

### 2. Variable Logic & Cascading
- **Cascading Filters**: Filters are "aware" of each other. For example, selecting a **User ID** automatically limits the **Session ID** list to only that user's sessions.
- **Global Context Tracking**: If you select a specific User/Session on the FinOps page, those selections follow you when you click to Transcripts or Diagnostics. (The "Home" page is the exception, defaulting cleanly to fleet-overview).
- **Symmetric Defaults**: Summary dashboards default to "All" (overview) while forensic dashboards default to explicitly requiring a "Select_User" selection. By propagating variable context seamlessly, users no longer face empty "Blank Box" filter regressions when moving between layers.
- **Diagnostics Multi-Filter**: The Diagnostics page is the only one that uses the **Agent** and **Tool** filters, allowing you to narrow down system-wide bottlenecks.

### 3. URL Data Links
We use custom **Data Links** on tables and charts to preserve full environment context. For example, clicking on a "Session ID" will route you to:
`/d/agent-transcript?${__url_time_range}&var-datasource=${datasource}&var-gcp_project=${gcp_project}&var-user_id=${user_id}&var-session_id=${__value.raw}`

This ensures that when you land on the Transcripts page, it is **already filtered** to the exact session you were investigating.

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
- **Metadata Visibility**: Infrastructure-level labels (Project ID, Dataset ID, Table) are **Visible** (`hide: 0`) by default to allow for rapid environment verification.

---

### 8. V2 Stabilization & Robustness
- **Arithmetic Safety**: All rate-based charts use `SAFE_DIVIDE` to prevent "Divide by Zero" errors during low-traffic periods.
- **Variable Fallbacks**: SQL filters handle empty or placeholder states (`IN ('Select_User', '', 'All')`) to ensure panels render correctly even when context is being loaded from the URL.
- **Forensic Isolation**: Deep-dive dashboards (Traces, Transcript, LLM Audit) strictly enforce single-session selection by disabling the "All" option, preventing "No Data" regressions.

---

## 🔗 Global Navigation Header
Every dashboard features a persistent HTML navigation bar at the top, organized into three distinct visual pills to separate contexts:
- **📊 SUMMARY**: `🏠 Home` | `💰 FinOps` | `🛠️ Diagnostics`
- **🔍 FORENSICS**: `💬 Transcripts` | `📜 Traces` | `🧠 LLM Audit`
- **📚 RESOURCES**: `📖 Guide`

This unified header allows for rapid context switching and deep-dive exploration without losing selected dashboard variables.

---

*Empowering Transparent AI - Scalable Observability for Agentic Workflows.*
