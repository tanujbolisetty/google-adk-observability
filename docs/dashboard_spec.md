# 📊 Dashboard Specification: Metrics & Insights

This document defines the **technical architecture and visual requirements** for the Agent Analytics Suite.

> [!IMPORTANT]
> **Minimum Requirement**: Google ADK **v1.28.0+** is required to ensure consistent metadata propagation across all forensic views.

---

## 🏗️ Design Philosophy: "Forensic Symmetricity"
To balance global monitoring with surgical forensic isolation, the suite implements a **Symmetric Selection** architecture.

### 1. Dual-Design Patterns
- **Summary Dashboards** (Home, FinOps, Diagnostics, Guide):
    - **Default State**: "All" (`includeAll: true` acting as `Select_User` / `Select_Session` pass-through).
    - **Goal**: Fleet-wide KPIs, trend discovery, and broad documentation access.
- **Forensic Dashboards** (Traces, Transcripts, LLM Audit):
    - **Default State**: Mandatory Selection (`Select_User` / `Select_Session`).
    - **Goal**: Precision isolation and sub-millisecond payload audit.

### 2. Standardized Logic & UX
- **Infrastructure Visibility (v1.3.25)**: Technical variables (`gcp_project`, `bq_dataset`, `bq_table`, `datasource`) are preset with **`hide: 0` (Visible)**. This allows for manual verification of the target environment and easy switching between multi-tenant datasets directly from the dashboard header.
- **2-Line Infrastructure Status Bar**: Standardized Navigation Panel (**ID 999**) across all templates. Includes a dedicated 2nd line displaying the active Project, Dataset, Table, and Datasource UID for persistent environmental awareness.
- **Symmetric Selection (v1.4)**: Every dashboard now supports an **Application** dropdown. Selections for Application, User, and Session are preserved across the entire suite. Summary dashboards use `allValue` placeholders (e.g., `Select_Application`, `Select_User`) to ensure that "All" states propagate correctly to forensic dashboards without passing empty strings.
- **Recency-First Sorting**: All dropdowns (Users, Sessions) are sorted by `timestamp DESC` to ensure the most relevant data appears first.
- **Forensic Table Aesthetics (Transcripts)**: Implements the **"Wide Open Display"** standard:
    - `cellHeight: auto` (Panel level).
    - `message` override: `wrapText: true`, `width: auto`, `cellType: auto`.
    - `inspect: true` (Field level) to ensure zero truncation of large agent payloads.
    - Metadata columns (`speaker`, `time`) are fixed-width to maximize wrapping area.

---

## 🔍 The 7-Dashboard Analytical Flow

### 1. 🏠 Agent Home (Landing Page)
**Goal**: Fleet KPIs (Total Sessions, User Questions, Token Volume, Total Cost) and multi-app distribution.
- **Panel Breakdown**:
    - **Total Sessions (Stat)**: Unique conversation count. (Source: `v_aaa_session_summary`)
    - **Total User Questions (Stat)**: Total count of human-initiated prompts. Sourced from `v_aaa_user_intent` to prioritize "What did the human ask?" over internal technical reprocessing. (Source: `v_aaa_user_intent`)
    - **Total Tokens (Stat)**: Cumulative volume of input and output tokens. (Source: `v_aaa_session_summary`)
    - **Total Estimated Cost (Stat)**: Aggregated USD consumption. (Source: `v_aaa_session_summary`)
    - **Sessions Per Day (Bar Chart)**: Daily volume of active sessions grouped by application. (Source: `v_aaa_session_summary`)
    - **Questions Per Day (Bar Chart)**: Daily volume of human queries. (Source: `v_aaa_user_intent`)
    - **Token Distribution by App (Donut Chart)**: Visualizing proportional usage across the fleet (v1.5). (Source: `v_aaa_session_summary`)
    - **Cost Distribution by App (Donut Chart)**: Identifying budget-heavy applications (v1.5). (Source: `v_aaa_session_summary`)
    - **Daily Token Consumption (Time Series)**: Daily input/output tokens trends. (Source: `v_aaa_session_summary`)
    - **User Questions (Intent) (Table)**: Captured human prompts with full-width layout and zero-scroll visibility. (Source: `v_aaa_user_intent`)
    - **Recent Sessions by User (Table)**: Latest 20 user sessions with activity and cost summaries. (Source: `v_aaa_session_summary`)

### 2. 💰 Token FinOps
**Goal**: Cost drivers and budget tracking.
- **Panel Breakdown**:
    - **Session Cost Over Time (Time Series)**: Per-session cost trending over time. (Source: `v_aaa_session_summary`)
    - **Tokens Consumed Per Turn (Time Series)**: Average context payload per turn. (Source: `v_aaa_turn_summary`)
    - **Token Usage by Model Version (Bar Chart)**: Token and cost split across model versions. (Source: `v_aaa_llm_calls`)
    - **Cost Breakdown Per Session (Table)**: Table detailing token and cost breakdown per session. (Source: `v_aaa_llm_calls`)
    - **Token Usage by Specialist (Bar Chart)**: Tracking specialist assistant resource consumption. Configured with a `-45°` x-axis label rotation to support long specialist name formatting. (Source: `v_aaa_llm_calls`)
    - **Top 10 Spenders (USD) (Bar Chart)**: Top 10 users generating the highest operational costs. Configured with a `-45°` x-axis label rotation to support long User ID formatting. (Source: `v_aaa_session_summary`)

### 3. ⚙️ System Diagnostics
**Goal**: Latency attribution and error tracking.
- **Panel Breakdown**:
    - **Total Errors (Stat)**: Count of failing interactions. (Source: base table)
    - **Max TTFT (Stat)**: Identifying peak inference lag. Note: A high TTFT relative to Total Duration suggests streaming optimization is working; identical values suggest blocking `run()` calls. (Source: base table)
    - **Turning Cost (USD) (Stat)**: Total estimated cost of LLM calls in the current session/period. (Source: `v_aaa_llm_calls`)
    - **Success Rate (Stat)**: Percentage of agent turns that finished without an error. (Source: `v_aaa_turn_summary`)
    - **Turn Latency Attribution (Avg vs P95) (Table)**: Average and P95 latency breakdown for LLM reasoning, Tool execution, and Overhead. (Source: `v_aaa_turn_summary`)
    - **Turn Latency Distribution (Histogram)**: Bucketized distribution of turn durations. (Source: `v_aaa_turn_summary`)
    - **Turn Latency Attribution Trend (Time Series)**: Stacked bar chart showing LLM reasoning, Tool execution, and Overhead trend over time. (Source: `v_aaa_turn_summary`)
    - **System Latency Trend (TTFT) (Scatter Plot)**: TTFT trends for outlier spikes over time. (Source: base table)
    - **Slowest Tools (Bar Chart)**: Tool names ranked by average execution latency. (Source: `v_aaa_tool_usage`)
    - **Orchestrator Handoffs (Bar Chart)**: Routing volume to sub-agents. (Source: `v_aaa_agent_routing`)
    - **Agent & Tool Distribution (Table)**: Frequency and performance of specific tool calls mapped to agents. (Source: `v_aaa_tool_usage`)
    - **Error Rate by Specialist (Table)**: Granular log of all system errors. (Source: base table)

### 4. 💬 Chat Transcripts
**Goal**: Qualitative audit of human-agent conversations.
- **Display Standard**: **Wide Open Display** (Auto-height, mandatory message wrapping).
- **Panel Breakdown**:
    - **Conversation Flow (Transcript) (Table)**: Optimized chat record for user feedback auditing. Includes a `duration_ms` column (calculated via `LAG()`) to measure the precise interval between human/agent messages. (Source: `v_aaa_session_transcript`)

### 5. 🔎 Agent Technical Traces
**Goal**: Deep technical autopsy of tool payloads and orchestrator logic.
- **Panel Breakdown**:
    - **Session Performance Profile (Bar Gauge)**: Session-level aggregated latency breakdown (LLM time, Tool time, Overhead). (Source: `v_aaa_turn_summary`)
    - **Session Duration (Stat)**: Total interaction time health check. (Source: `v_aaa_session_summary`)
    - **Total LLM Calls (Stat)**: Volume of inference triggers. (Source: `v_aaa_session_summary`)
    - **Total Tool Calls (Stat)**: Volume of external API triggers. (Source: `v_aaa_session_summary`)
    - **Session Chronology (Unified Turn Flow) (Table)**: Master audit of step logic and payloads. (Source: `v_aaa_session_chronology`)

### 6. 🧠 LLM & Prompt Audit
**Goal**: Technical tracing of model reasoning and prompt quality.
- **Panel Breakdown**:
    - **Total Session Tokens (Stat)**: Accumulative payload volume. (Source: `v_aaa_llm_calls`)
    - **Session Context Inflation (Tokens Per Turn) (Bar Chart)**: Visualizing context growth per interaction step. **Interactive Hover**: Shows the associated `invocation_id` for each turn. (Source: `v_aaa_turn_summary`)
    - **LLM Inference & Prompt Audit (Full Content) (Table)**: Side-by-side audit of Prompt vs. Response. (Source: `v_aaa_llm_calls`)

### 7. 📖 Agent Intelligence Guide
**Goal**: Onboarding and technical reference.
- **Panel Breakdown**:
    - **Metrics Glossary**: Definitions of all suite KPIs (TTFT, Overhead). (Source: Static/Markdown)
    - **Forensic Workflow**: Guided instructions for drill-down analysis. (Source: Static/Markdown)

---

## 🔗 Data Link Ecosystem
Dashboards are connected via context-aware **URL Data Links**. Preserved variables:
- `var-application`, `var-user_id`, `var-session_id`, `var-datasource`, `var-gcp_project`, `var-bq_dataset`, `var-bq_table`.

---

*For technical schema details, refer to [bq_dashboard_views.md](bq_dashboard_views.md).*
