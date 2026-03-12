# 🏗️ Grafana Architecture: Navigation & Drill-Downs

To keep Agent telemetry clean and performant, this interface is designed as a multi-page **Dashboard Application** rather than a single, monolithic screen. This document explains how the pages interconnect.

---

## 🏗️ The 4-Tier Navigation Flow

The suite is architected to move a user from **High-Level Outcomes** to **Low-Level Traces** seamlessly:

1.  **Level 1: Agent Home (Landing)**
    *   *The Entry Point.* Aggregated KPIs (Total Sessions, Total Tokens).
    *   *Exit Action:* Drill into a specific **Session** or **Financial Trend**.
2.  **Level 2: FinOps & Diagnostics**
    *   *The Contextual View.* Performance and cost metrics filtered by User or Model.
    *   *Exit Action:* Drill into a specific **Turn** or **Prompt Trace**.
3.  **Level 3: Session Transcript (Chat)**
    *   *The Qualitative Analysis.* Viewing exactly what happened in a single conversation.

---

## ⚙️ Navigation State Preservation

The system preserves your view context (Time Range, User ID, Session ID) as you navigate between pages using two mechanisms:

### 1. Unified Variable Control Bar
Every dashboard shares a common set of variables. Here is how they apply across the suite:

| Filter | Landing Page | FinOps | Diagnostics | Transcripts |
| :--- | :--- | :--- | :--- | :--- |
| **User ID** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Session ID** | ❌ No | ❌ No | ✅ Yes | ✅ Yes (Required) |
| **Agent Name** | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **Tool Name** | ❌ No | ❌ No | ✅ Yes | ❌ No |

### 2. Variable Logic & Cascading
- **Cascading Filters**: Filters are "aware" of each other. For example, selecting a **User ID** automatically limits the **Session ID** list to only that user's sessions.
- **Global Context**: If you change a filter on the Diagnostics page and then click "FinOps" in the header, your **User ID** selection will follow you.
- **Diagnostics Multi-Filter**: The Diagnostics page is the only one that uses the **Agent** and **Tool** filters, allowing you to narrow down system-wide bottlenecks.
- **Transcript Focus**: The Transcript page *must* have a specific **Session ID** selected to show the chat flow.

### 3. URL Data Links
We use custom **Data Links** on tables and charts. For example, clicking on a "Session ID" in the Diagnostics table will route you to:
`/d/agent-transcript?var-session_id=${__value.text}&var-user_id=${user_id}`

This ensures that when you land on the Transcript page, it is **already filtered** to the exact session you were investigating.

---

## 🔗 Global Navigation Header
Every dashboard features a persistent HTML navigation bar at the top:
`🏠 Home | 💰 FinOps | 💬 Transcripts | ⚙️ Diagnostics`

This allows for rapid context switching without having to return to the Grafana home folder.

---

*Empowering Transparent AI - Scalable Observability for Agentic Workflows.*
