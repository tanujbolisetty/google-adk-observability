# 📊 Dashboard Specification: Metrics & Insights

This document defines the **technical architecture and visual requirements** for the Agent Analytics Suite.

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
- **Hidden Metadata**: Technical variables (`gcp_project`, `bq_dataset`, `bq_table`) are preset with `hide: 2`. This prevents user error while allowing drill-downs to pass environment context via URL parameters.
- **Symmetric Selection**: Summary dashboards use `allValue: "Select_User"` to ensure that "All" selections propagate correctly to forensic dashboards without passing empty strings.
- **Recency-First Sorting**: All dropdowns (Users, Sessions) are sorted by `timestamp DESC` to ensure the most relevant data appears first.
- **Forensic Table Aesthetics (Transcripts)**: Implements the **"Wide Open Display"** standard:
    - `cellHeight: auto` (Panel level).
    - `message` override: `wrapText: true`, `width: auto`, `cellType: auto`.
    - `inspect: true` (Field level) to ensure zero truncation of large agent payloads.
    - Metadata columns (`speaker`, `time`) are fixed-width to maximize wrapping area.

---

## 🔍 The 7-Dashboard Analytical Flow

### 1. 🏠 Agent Home (Landing Page)
**Goal**: Fleet KPIs (Total Sessions, Token Volume, Total Cost).
- **Panel Breakdown**:
    - **Total Sessions (Stat)**: Unique conversation count. (Source: `v_aaa_session_summary`)
    - **Total Tokens (Stat)**: Cumulative volume of input and output tokens. (Source: `v_aaa_session_summary`)
    - **Total Estimated Cost (Stat)**: Aggregated USD consumption. (Source: `v_aaa_session_summary`)
    - **Usage Trends (Mixed Time Series)**: Daily token volume (Logarithmic). (Source: `v_aaa_session_summary`)
    - **Cost by User (Bar Chart)**: Top 10 most active users. (Source: `v_aaa_session_summary`)

### 2. 💰 Token FinOps
**Goal**: Cost drivers and budget tracking.
- **Panel Breakdown**:
    - **Cost Over Time (Time Series)**: Per-session cost trending. (Source: `v_aaa_turn_summary`)
    - **Tokens Per Turn (Time Series)**: Average context payload per interaction. (Source: `v_aaa_turn_summary`)
    - **Usage by Model (Bar Chart)**: Token split (Gemini 1.0 vs 1.5 Pro/Flash). (Source: `v_aaa_llm_calls`)
    - **Usage by Agent (Bar Chart)**: Tracking specialist assistant resource consumption. (Source: `v_aaa_turn_summary`)

### 3. ⚙️ System Diagnostics
**Goal**: Latency attribution and error tracking.
- **Panel Breakdown**:
    - **Total Errors (Stat)**: count of failing interactions. (Source: `v_aaa_turn_summary`)
    - **Max TTFT (Stat)**: Identifying peak inference lag. (Source: `v_aaa_turn_summary`)
    - **Success Rate (Stat)**: Fleet performance health. (Source: `v_aaa_turn_summary`)
    - **Turn Latency Breakdown (Stacked Area)**: Visualizing time spent in LLM vs. Tools vs. Overhead. (Source: `v_aaa_turn_summary`)
    - **Orchestrator Handoffs (Bar Chart)**: Routing volume to sub-agents. (Source: `v_aaa_agent_routing`)
    - **User Questions (Intent) (Table)**: Captured human prompts. (Source: `v_aaa_user_intent`)
    - **Error Details (Table)**: Granular log for technical debugging. (Source: `v_aaa_turn_summary`)

### 4. 💬 Chat Transcripts
**Goal**: Qualitative audit of human-agent conversations.
- **Display Standard**: **Wide Open Display** (Auto-height, mandatory message wrapping).
- **Panel Breakdown**:
    - **Conversation Flow (Transcript) (Table)**: Optimized chat record for user feedback auditing. Includes a `duration_ms` column (calculated via `LAG()`) to measure the precise interval between human/agent messages. (Source: `v_aaa_session_transcript`)

### 5. 🔎 Agent Technical Traces
**Goal**: Deep technical autopsy of tool payloads and orchestrator logic.
- **Panel Breakdown**:
    - **Session Performance Profile (Bar Gauge)**: Per-turn latency breakdown. (Source: `v_aaa_turn_summary`)
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
    - **Metrics Glossary**: Definitions of all suite KPIs (TTFT, Overhead).
    - **Forensic Workflow**: Guided instructions for drill-down analysis.

---

## 🔗 Data Link Ecosystem
Dashboards are connected via context-aware **URL Data Links**. Preserved variables:
- `var-user_id`, `var-session_id`, `var-datasource`, `var-gcp_project`, `var-bq_dataset`, `var-bq_table`.

---

*For technical schema details, refer to [bq_dashboard_views.md](bq_dashboard_views.md).*
