# 🗄️ BigQuery Data Layer: The "Master Views"

This document explains the technical logic behind the **Master Analytical Views**. These views flatten complex ADK JSON logs into clean tables that power your Grafana dashboards without requiring any runtime calculations.

---

## 🏗️ Architecture Overview
Agent Analytics uses a **View-on-Table** pattern. Instead of modifying your raw event data, we layer SQL views on top. This ensures:
- **Zero Data Duplication**: Views are computed at query time.
- **Cost Transparency**: Token usage is automatically joined with a pricing matrix.
- **Context Preservation**: session and user IDs are normalized for easy filtering.

---

## Prerequisites: The Pricing Matrix
Before creating any views, you must create a static lookup table that maps model versions to their specific input/output token costs.

*Run the following in your target BigQuery project, replacing `<YOUR_PROJECT>.<YOUR_DATASET>` with your specific locations.*

```sql
CREATE OR REPLACE TABLE `<YOUR_PROJECT>.<YOUR_DATASET>.model_pricing` AS
SELECT "gemini-1.5-flash" AS model_version, 0.075 / 1000000 AS input_cost_per_token, 0.30 / 1000000 AS output_cost_per_token UNION ALL
SELECT "gemini-1.5-pro", 1.25 / 1000000, 5.00 / 1000000 UNION ALL
SELECT "gemini-2.0-flash", 0.10 / 1000000, 0.40 / 1000000 UNION ALL
SELECT "gemini-2.0-pro", 1.50 / 1000000, 6.00 / 1000000;
```

---

## The 7 Master Views

### 1️⃣ View: Session Summary
**Purpose:** Top-level KPIs per session.
- **Columns:** `session_id`, `user_id`, `session_start`, `session_end`, `session_duration_ms`, `session_total_tokens`, `session_total_cost_usd`, `max_ttft_ms`.
- **Behind the Logic:** This view aggregates all events for a `session_id`. It sums up the costs of every individual LLM call using the Pricing Matrix and calculates the total "Wall Clock" time by subtracting the first event's timestamp from the last.

### 2️⃣ View: Turn Summary
**Purpose:** Granular turn-by-turn metrics for drill-downs.
- **Columns:** `invocation_id`, `turn_start`, `tokens`, `cost`, `total_llm_latency_ms`, `total_tool_latency_ms`, `turn_duration_ms`.
- **Behind the Logic:** This is the most complex view. It groups events by `invocation_id` (a single user/agent turn). It calculates **Latency Attribution** by summing up all LLM processing time and all Tool execution time within that specific turn. Any remaining time in the `turn_duration_ms` is classified as "Overhead".

### 3️⃣ View: LLM Calls & Trace
**Purpose:** Deep traces of prompt/response interactions.
- **Columns:** `prompt`, `response`, `total_tokens`, `calculated_usd_cost`.
- **Behind the Logic:** Flattens the nested `attributes` and `content` JSON fields. It performs a real-time join with the `model_pricing` table to assign a dollar value to every individual model inference.

---

### 4️⃣ View: Tool Usage
**Purpose:** Performance metrics for individual tool executions.
- **Behind the Logic:** Specifically filters for `TOOL_COMPLETED` events. It Extracts the tool name and its execution latency, allowing you to identify which external APIs are the bottlenecks.

---

### 5️⃣ View: Model Routing Flow
**Purpose:** Visualizing orchestrator-to-specialist delegations.
- **Behind the Logic:** Uses `attributes.root_agent_name` to identify the starting point and `agent` to show where the work was delegated. This tracks the "Orchestrator Handoffs" in the Diagnostics dashboard.

---

### 6️⃣ View: User Intent Tracking
**Purpose:** Extracting and analyzing raw human inputs.
- **Behind the Logic:** Aggregates `USER_MESSAGE_RECEIVED` events. This provides the "input" side of the analysis, allowing you to see what users are actually asking for.

### 7️⃣ View: Full Session Transcript
**Purpose:** Reconstructing chronological conversation flows.
- **Behind the Logic:** This view uses a `UNION ALL` to combine human and agent messages. To ensure a clean transcript, it uses `ROW_NUMBER()` to select only the **final** agent response for each turn, suppressing internal technical steps like tool calls or reasoning iterations.

---

*For the full SQL source code of these views, refer to setup_bq_views.py.*
