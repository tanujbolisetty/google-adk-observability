# 🗄️ BigQuery Data Layer: The "Master Views"

This document serves as the **Technical Specification** for the Master Analytical Views. It explains the "Why" and "How" behind the data processing pipeline, detailing the logic used to transform raw JSON logs into actionable metrics.

---

## 🏗️ Architecture Overview
Agent Analytics uses a **View-on-Table** pattern. Instead of modifying raw event data, we layer SQL logic on top. This ensures:
- **Zero Data Duplication**: All metrics are calculated dynamically.
- **Financial Traceability**: model performance is paired with real-time model pricing.
- **Standardization**: Complex JSON structures are flattened into a consistent schema.

---

## 📊 View 1: Session Summary (`v_aaa_session_summary`)
**Goal:** High-level KPIs tracking the complete lifecycle of human-agent conversations.
**Primary Usage**: **Agent Home** (Landing Page), **Technical Traces** (Session Duration), **LLM Audit** (Session Totals).

### 📋 Captured Fields:
- `session_id` / `user_id`: Identifiers for the conversation and human participant.
- `session_duration_ms`: Total wall-clock time from the first user message to the final agent response.
- `total_turns`: Count of individual request/response interactions within the session.
- `session_total_tokens`: Aggregated token volume across all turns.
- `session_total_cost_usd`: Estimated budget impact based on input/candidate model pricing.

### 🧩 Source Events:
- `USER_MESSAGE_RECEIVED` (Turn Counting)
- `LLM_RESPONSE` (Tokens, Costs, TTFT)
- `TOOL_COMPLETED` (Tool Counting)

---

## ⚡ View 2: Turn Summary (`v_aaa_turn_summary`)
**Goal:** Granular performance profiling using the **3-Tier Latency Model**.
**Primary Usage**: **System Diagnostics** (Latency Attribution), **FinOps** (Cost Over Time), **Technical Traces** (Performance Profile).

### 📋 Captured Fields:
- `total_llm_latency_ms`: Combined reasoning time of all model calls in a single turn.
- `total_tool_latency_ms`: Combined execution time of all external dependencies in a single turn.
- `turn_overhead_ms`: The "System Tax"—orchestration and transit time.
- `turn_duration_ms`: Total time elapsed for one User/Agent interaction.

### 🧩 Source Events:
- `LLM_RESPONSE` (LLM Latency, Tokens, Turn Costs)
- `TOOL_COMPLETED` (Tool Latency)

---

## 🔎 View 3: LLM Calls & Trace (`v_aaa_llm_calls`)
**Goal:** Technical autopsy of model reasoning and prompt/candidate auditing.
**Primary Usage**: **LLM Audit** (Inference Log), **FinOps** (Usage by Model Version).

### 📋 Captured Fields:
- `model`: The specific model version used (e.g., Gemini 1.5 Pro).
- `prompt` / `response`: The raw input provided to the model and the raw result returned.
- `calculated_usd_cost`: Precision cost tracking at the individual call level.
- `invocation_id`: Critical identifier used for **Interactive Hover Detail** in the LLM Audit dashboard.

### 🧩 Source Events:
- `LLM_RESPONSE` (Main Payload & Metadata)
- `LLM_REQUEST` (Prompt Fallback)

### 🧠 Analytical Logic:
- **Granular Costing**: Unlike the Session Summary (which globals costs), this view calculates the price of **every single inference**, allowing researchers to find specific expensive prompts.
- **Pricing Resilience (v1.3)**: All cost calculations (`v_aaa_session_summary`, `v_aaa_turn_summary`, `v_aaa_llm_calls`) use `COALESCE(..., 0)` logic. If a model version is missing from the `model_pricing` table, the system will display a `$0.00` cost instead of returning `NULL`. This ensures sessions are always visible in visualizations even if pricing data is briefly out of sync.

> [!CAUTION]
> If using `JSON_VALUE` for prompts, the displayed text length will often not match the `prompt_token_count` because hidden orchestrator context (system instructions) is filtered out. Always use the "Inspect" icon in Grafana to view the full `JSON_QUERY` payload.

---

## 🛠️ View 4: Tool Performance (`v_aaa_tool_usage`)
**Goal:** Auditing external tool integration and payload accuracy.
**Primary Usage**: **System Diagnostics** (Slowest Tools), **Technical Traces** (Drill-down).

### 📋 Captured Fields:
- `tool_name` / `status`: Identification of the tool and whether it succeeded/errored.
- `latency_ms`: Duration of the external execution.
- `input_args` / `output_result`: The value returned by the tool to the agent.

### 🧩 Source Events:
- `TOOL_STARTING` (Arguments & Identity)
- `TOOL_COMPLETED` (Latency, Status & Result)

---

## 🤖 View 5: Agent Routing (`v_aaa_agent_routing`)
**Goal:** Visualizing the Orchestrator's delegation and handoff sequence.
**Primary Usage**: **System Diagnostics** (Orchestrator Handoffs).

### 📋 Captured Fields:
- `orchestrator`: The root agent that received the user's initial request.
- `assigned_specialist`: The sub-agent or tool-specialist delegated to handle the logic.

### 🧩 Source Events:
- `LLM_REQUEST` (Intent & Delegation Phase)
- `AGENT_COMPLETED` (Handoff Resolution)

---

## 👤 View 6: User Intent (`v_aaa_user_intent`)
**Goal:** Capturing the initial user prompt and system state.
**Primary Usage**: **Agent Home** (User Questions), **System Diagnostics**.

### 📋 Captured Fields:
- `raw_user_prompt`: The summary text of the user's initial message.
- `user_timezone`: The detected timezone from the session metadata.

### 🧩 Source Events:
- `USER_MESSAGE_RECEIVED` (Main Prompt & Metadata)

---

## 💬 View 7: Session Transcript (`v_aaa_session_transcript`)
**Goal:** Chronological reconstruction for professional Conversation Replay.
**Primary Usage**: **Chat Transcripts**.

### 📋 Captured Fields:
- `timestamp`: Chronological event time enabling interactive interval calculations like Turn Duration (`LAG`).
- `speaker`: Identifies the message source as either "Human" or "Agent".
- `message`: The clean, high-level text content of the interaction.

### 🧩 Source Events:
- `USER_MESSAGE_RECEIVED` (Human Speech)
- `LLM_RESPONSE` (Agent Speech)

---

## 🕒 View 8: Unified Session Chronology (`v_aaa_session_chronology`)
**Goal:** A step-by-step master audit log charting every model thought, tool call, and human message.
**Primary Usage**: **Technical Traces** (Unified Turn Flow).

### 📋 Captured Fields:
- `step_type`: Human-readable event classification (e.g., `👤 Human Input`).
- `actor`: The entity performing the action (Orchestrator or Specialist).
- `message`: The primary conversation content (Includes all agent responses).
- `technical_details`: Collapsed JSON payloads for internal reasoning.

### 🧩 Source Events:
- `USER_MESSAGE_RECEIVED`, `LLM_REQUEST`, `LLM_RESPONSE`, `TOOL_STARTING`, `TOOL_COMPLETED`, `AGENT_STARTING`, `AGENT_COMPLETED`

---

## 🚀 Key Performance Principle: "True-Idle"
All logic within these views is hardened with **Placeholder Guards**. By checking for values like `Select_User`, the views return empty results with **zero scan cost**.

*Refer to [dashboard_spec.md](dashboard_spec.md) for panel-level visualization details.*
