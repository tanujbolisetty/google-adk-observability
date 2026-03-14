# 🗄️ BigQuery Data Layer: The "Master Views"

This document serves as the **Technical Specification** for the Master Analytical Views. It explains the "Why" and "How" behind the data processing pipeline, detailing the logic used to transform raw JSON logs into actionable metrics.

---

## 🏗️ Architecture Overview
Agent Analytics uses a **View-on-Table** pattern. Instead of modifying raw event data, we layer SQL logic on top. This ensures:
- **Zero Data Duplication**: All metrics are calculated dynamically.
- **Financial Traceability**: model performance is paired with real-time model pricing.
- **Standardization**: Complex JSON structures are flattened into a consistent schema.

---

## 📊 View 1: Session Summary (`v_session_summary`)
**Goal:** High-level KPIs tracking the complete lifecycle of human-agent conversations.

### 📋 Captured Fields:
- `session_id` / `user_id`: Identifiers for the conversation and human participant.
- `session_duration_ms`: Total wall-clock time from the first user message to the final agent response.
- `total_turns`: Count of individual request/response interactions within the session.
- `session_total_tokens`: Aggregated token volume across all turns.
- `session_prompt_tokens`: Cumulative input tokens (Prompts).
- `session_completion_tokens`: Cumulative output tokens (Candidates).
- `session_total_cost_usd`: Estimated budget impact based on input/candidate model pricing.
- `max_ttft_ms`: The single highest "Time to First Token" delay recorded during the session.

### 🧠 Analytical Logic:
- **Financial Calculation**: The view performs a `LEFT JOIN` with the `model_pricing` matrix. It multiplies `prompt_token_count` by input rates and `candidates_token_count` by output rates for every `LLM_RESPONSE` event.
- **Time Boxing**: It uses `MIN(timestamp)` and `MAX(timestamp)` per session to determine the full conversation "envelope".
- **Productivity Ratios**: It counts `USER_MESSAGE_RECEIVED` vs `TOOL_COMPLETED` events to differentiate between simple chat turns and complex autonomous actions.

---

## ⚡ View 2: Turn Summary (`v_turn_summary`)
**Goal:** Granular performance profiling using the **3-Tier Latency Model**.

### 📋 Captured Fields:
- `total_llm_latency_ms`: Combined reasoning time of all model calls in a single turn.
- `total_tool_latency_ms`: Combined execution time of all external dependencies in a single turn.
- `turn_overhead_ms`: The "System Tax"—time spent in orchestration, prompt building, or network transit.
- `turn_duration_ms`: Total time elapsed for one User/Agent interaction.

### 🧠 Analytical Logic:
- **Latency Attribution**: 
  - **LLM Time**: Derived from `LLM_RESPONSE` event metadata (`latency_ms.total_ms`).
  - **Tool Time**: Derived from `TOOL_COMPLETED` event metadata (`latency_ms.total_ms`).
  - **Overhead**: Calculated as `Total Duration - (LLM + Tool)`. The logic uses `GREATEST(0, ...)` to protect against negative values caused by non-sequential log delivery in high-concurrency environments.
- **Cost Isolation**: Aggregates token costs per `invocation_id` to show the financial impact of a specific turn (e.g., identifying when a "Reasoning Loop" becomes expensive).

---

## 🔎 View 3: LLM Calls & Trace (`v_llm_calls`)
**Goal:** Technical autopsy of model reasoning and prompt/candidate auditing.

### 📋 Captured Fields:
- `model`: The specific model version used (e.g., Gemini 1.5 Pro).
- `prompt` / `response`: The raw input provided to the model and the raw result returned.
- `prompt_tokens` / `completion_tokens`: Granular token breakdown for the specific call.
- `calculated_usd_cost`: Precision cost tracking at the individual call level.

### 🧠 Analytical Logic:
- **Payload Extraction**: Uses `JSON_VALUE` to pull the `content.prompt` and `content.response` into top-level columns.
- **Granular Costing**: Unlike the Session Summary (which globals costs), this view calculates the price of **every single inference**, allowing researchers to find specific expensive prompts.

---

## 🛠️ View 4: Tool Performance (`v_tool_usage`)
**Goal:** Auditing external tool integration and payload accuracy.

### 📋 Captured Fields:
- `tool_name` / `status`: Identification of the tool and whether it succeeded/errored.
- `latency_ms`: Duration of the external execution.
- `input_args`: The parameters passed to the tool.
- `output_result`: The value returned by the tool to the agent.

### 🧠 Analytical Logic:
- **Hybrid Extraction Pattern**: This view implements a complex `JOIN` between `TOOL_STARTING` and `TOOL_COMPLETED` events.
- **Schema Robustness**: It uses a `COALESCE` strategy to capture payloads across multiple SDK versions. It checks for `args`, `arguments`, `parameters`, and `input` fields simultaneously using `TO_JSON_STRING(JSON_QUERY(...))`. This ensures tool data is never hidden, even if the logging schema changes.

---

## 🤖 View 5: Agent Routing (`v_agent_routing`)
**Goal:** Visualizing the Orchestrator's delegation and handoff sequence.

### 🧠 Analytical Logic:
- **Handoff Tracking**: Filters specifically for `AGENT_COMPLETED` and `LLM_REQUEST` events. 
- **Delegation Mapping**: Maps the `root_agent_name` (the decision-maker) to the `agent` (the execution specialist) to show exactly how a user request was distributed across the system.

---

## 💬 View 6: Session Transcript (`v_session_transcript`)
**Goal:** Chronological reconstruction for professional Conversation Replay.

### 🧠 Analytical Logic:
- **Human Feed Integrity**: Uses `COALESCE` on `content.text` and `content.text_summary` to ensure human input is captured regardless of whether the client sent raw text or a summary.
- **Agent Clean-Up (Replay Filtering)**: 
  - To prevent "Double-Speak" in the UI, the view uses a `ROW_NUMBER()` window function partitioned by `invocation_id`. 
  - It sorts by timestamp and selects only the **Final Success Response** for the turn. This effectively hides internal reasoning, failed retries, and tool-call noise, presenting a clean Human-Agent dialogue.

---

## 🚀 Key Performance Principle: "True-Idle"
All logic within these views is hardened with **Placeholder Guards**. By checking for values like `-- Select --`, the views return empty results with **zero scan cost**. This allows the Dashboards to remain open and active without consuming BigQuery budget while in an idle state.

