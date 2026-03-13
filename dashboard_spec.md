# 📊 Dashboard Specification: Metrics & Insights

This document defines the **purpose and metrics** for the agent observability suite. It serves as a blueprint for understanding what is being measured and how the data is visualized.

---

## 🚀 Performance Paradigm: "True-Idle"
All dashboards in this suite are optimized for **Zero-Cost Idle States** and a unified user experience.
- **Silent on Load**: No BigQuery scans are triggered when a dashboard is first opened.
- **SQL Guards**: Panels remain completely silent until both a **User** and **Session** are explicitly selected.
- **Optimized Metadata**: Variable metadata scans are restricted and throttled to prevent background "blinking".
- **6-Hour Default Window**: All views default to `now-6h` to ensure fast initial loads and operational relevance.
- **Global Time Sync**: Navigation links preserve selected timeframes (`?from=${__from}&to=${__to}`) as users move between dashboards.
- **Hierarchical Discovery**: Filters follow a context-aware "Parent-Child" chain (Time -> User -> Session -> Tool) to maintain relevance.

---

## 🏠 Dashboard 1: Agent Home (Landing Page)
**Goal:** High-level executive KPIs and usage trends across all agents.

### Key Metrics:
- **Total Sessions:** Unique count of all user-agent conversations.
- **Total Tokens:** Aggregated token consumption (Input + Output).
- **Total Cost (USD):** Estimated dollar cost based on model pricing.
- **Usage Trends:** Daily breakdown of sessions and token volume.

---

## 💰 Dashboard 2: Token FinOps
**Goal:** Identifying cost drivers, model efficiency, and budget tracking.

### Key Metrics:
- **Cost Over Time:** Session-level cost breakdown.
- **Tokens Per Turn:** Granular view of model efficiency per interaction.
- **Usage by Model:** Comparison of token consumption across Gemini versions.
- **Usage by Agent:** Identifying which specialized agents are the most "expensive".

---

## ⚙️ Dashboard 3: System Diagnostics
**Goal:** Engineering health check, latency bottleneck discovery, and error tracking.

### Key Metrics:
- **TTFT (Time To First Token):** Latency of the initial model response per individual model call.
- **📊 Turn Latency Distribution:** Histogram of complete User/Agent interaction durations. Identifies consistency and outliers.
- **📈 Turn Latency Attribution Trend:** Stacked trend showing the balance between LLM, Tools, and Overhead over time.
- **⏱️ Turn Latency Attribution (Avg vs P95):** Precision table comparing typical vs. worst-case latencies for the 3-tier model.
- **Orchestrator Handoffs:** Distribution of requests across specialized sub-agents.

---

## 💬 Dashboard 4: Chat Transcripts
**Goal:** Qualitative audit of human-agent conversations for QA and CX improvement.

### Key Metrics:
- **Transcript Feed:** Chronological reconstruction including both Human (Input) and Agent (Response) messages. 
- **Session Duration:** Total elapsed "Wall Clock" time, including human thinking time between turns.
- **⚡ Session Performance Profile:** Visual bar per turn indicating the 3-tier breakdown:
  - **🟦 Blue:** LLM Reasoning
  - **🟧 Orange:** Tool Execution
  - **⬜ Gray:** Agent/Orchestrator Overhead
- **🤖 Counters**: At-a-glance counts for LLM and Tool calls in the current session.

---

## 📖 Dashboard 5: Agent Intelligence Guide
**Goal:** Onboarding and technical reference for dashboard users.

### Key Features:
- **Metric Definitions:** Clear explanations of TTFT, Turn latency, and 3-tier attribution logic.
- **🚀 Latency Optimization Guide:** Dynamic advice on reducing LLM reasoning time, parallelizing tool calls, and minimizing system overhead.
- **Navigation Map:** Cross-dashboard drill-down shortcuts.
- **Logic Guide:** Technical breakdown of the BigQuery views and processing pipeline.

---

## 🔎 Dashboard 6: Agent Technical Traces
**Goal:** Deep technical autopsy and payload audit for specific sessions.

### Key Features:
- **🛠️ Raw Tool Traces:** Detailed audit of tool arguments and execution results (Uses Hybrid JSON extraction for robust payload capture).
- **🧠 Agent Reasoning Logs:** Deep trace of raw LLM prompts and model responses.
- **Drill-down Integration:** 1-click jump from Chat Transcript interaction counters.

---

*For detailed SQL queries and BigQuery view logic, refer to bq_dashboard_views.md.*
