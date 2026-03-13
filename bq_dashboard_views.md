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
**Purpose:** Top-level KPIs per session for the Landing Page.
- **Columns:** `session_id`, `user_id`, `session_start`, `session_end`, `session_duration_ms`, `total_turns`, `session_total_tokens`, `session_total_cost_usd`, `max_ttft_ms`.
- **Behind the Logic:** This view calculates the complete "Wall Clock" lifecycle of a conversation. It identifies the first and last events per `session_id` to determine total duration. It performs a session-wide aggregation of token costs by joining with the `model_pricing` lookup. The `max_ttft_ms` metric is specifically tracked to identify the worst-case initial response latency across the entire user experience.

### 2️⃣ View: Turn Summary
**Purpose:** Granular turn-by-turn performance and the 3-Tier Latency Model.
- **Columns:** `invocation_id`, `turn_start`, `tokens`, `cost`, `total_llm_latency_ms`, `total_tool_latency_ms`, `turn_overhead_ms`, `turn_duration_ms`.
- **Behind the Logic:** This is the core diagnostic engine. It groups events by `invocation_id` (a single User/Agent interaction).
  - **LLM Latency:** Sum of all specific model reasoning times within the turn.
  - **Tool Latency:** Sum of all external API or tool execution times.
  - **Agent Overhead:** Calculated as `(Total Turn Duration) - (LLM + Tool)`. We use `GREATEST(0, ...)` to protect against negative values caused by out-of-order log arrival in high-concurrency systems.

### 3️⃣ View: LLM Calls & Trace
**Purpose:** Deep audit of individual model interactions and raw prompts.
- **Columns:** `prompt`, `response`, `total_tokens`, `calculated_usd_cost`.
- **Behind the Logic:** Flattens the complex `attributes` and `content` JSON structures. It provides a row for every single model inference, calculating the exact USD cost based on the specific model version used (Gemini 1.5, 2.0, etc.) via a pricing join.

---

### 4️⃣ View: Tool Usage
**Purpose:** Performance profiling of external dependencies.
- **Behind the Logic:** Extracts data from `TOOL_COMPLETED` events. It parses the JSON arguments and results to show exactly what went into a tool and what came out. This allows you to differentiate between a slow tool (high latency) and a failing tool (ERROR status).

---

### 5️⃣ View: Model Routing Flow
**Purpose:** Visualizing the orchestrator's decision-making process.
- **Behind the Logic:** Tracks the transit between the `root_agent_name` (the Orchestrator) and the `agent` (the Specialist). By filtering for assignment events, it builds the sequence needed for the "Chain of Thought" flow diagrams.

---

### 6️⃣ View: User Intent Tracking
**Purpose:** Semantic profiling of human-initiated messages.
- **Behind the Logic:** Focuses on the "Input" side of the agent. It extracts `text_summary` and metadata such as the user's timezone to help analyze intent patterns and geographic performance variations.

### 7️⃣ View: Full Session Transcript
**Purpose:** Chronological reconstruction of the conversation for Chat Replay.
- **Behind the Logic:**
  - **Human Side:** Uses `COALESCE(text, text_summary)` to ensure user messages are captured regardless of whether the logger used raw or summarized formats.
  - **Agent Side:** Employs a `ROW_NUMBER()` window function partitioned by `invocation_id`. This identifies the **final** successful response from the agent for a turn, effectively hiding all internal "thinking" steps, tool-calls, and intermediate reasoning for a clean, user-friendly replay.

---

*For the full SQL source code of these views, refer to setup_bq_views.py.*
