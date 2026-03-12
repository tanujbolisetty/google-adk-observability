# 📊 Dashboard Specification: Metrics & Insights

This document defines the **purpose and metrics** for the agent observability suite. It serves as a blueprint for understanding what is being measured and how the data is visualized.

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
- **TTFT (Time To First Token):** Latency of the initial model response.
- **Avg Tool Latency:** Performance of external tool calls and APIs.
- **Latency Attribution Profile:** Breakdown of time spent in LLM Reasoning vs. Tool Execution vs. System Overhead.
- **Orchestrator Handoffs:** Distribution of requests across sub-agents.
- **LLM Reasoning Logs:** Full traces of prompts and responses.

---

## 💬 Dashboard 4: Chat Transcripts
**Goal:** Qualitative audit of human-agent conversations for QA and CX improvement.

### Key Metrics:
- **Transcript Feed:** Chronological reconstruction of the chat session.
- **Speaker Attribution:** Differentiation between Human and Agent messages.
- **Session Duration:** Total elapsed time for the conversation.
- **Turn Performance Bar:** Visual indicator of LLM vs. Tool latency for every interaction in the session.

---

*For detailed SQL queries powering these panels, refer to bq_dashboard_views.md.*
