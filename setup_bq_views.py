import os
import argparse
from google.cloud import bigquery

def create_views(project_id, dataset_id, table_name):
    client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{dataset_id}"

    # 1. Model Pricing Table
    # Static table containing input/output token costs for various Gemini model versions. 
    # Used for calculating estimated USD cost of agent operations.
    pricing_sql = f"""
    CREATE OR REPLACE TABLE `{dataset_ref}.model_pricing` AS
    SELECT "gemini-1.5-flash" AS model_version, 0.075 / 1000000 AS input_cost_per_token, 0.30 / 1000000 AS output_cost_per_token UNION ALL
    SELECT "gemini-1.5-pro", 1.25 / 1000000, 5.00 / 1000000 UNION ALL
    SELECT "gemini-2.0-flash", 0.10 / 1000000, 0.40 / 1000000 UNION ALL
    SELECT "gemini-2.0-pro", 1.50 / 1000000, 6.00 / 1000000 UNION ALL
    SELECT "gemini-2.5-flash", 0.30 / 1000000, 2.50 / 1000000 UNION ALL
    SELECT "gemini-2.5-pro", 1.25 / 1000000, 10.00 / 1000000 UNION ALL
    SELECT "gemini-3.0-flash", 0.50 / 1000000, 3.00 / 1000000 UNION ALL
    SELECT "gemini-3.0-pro", 2.00 / 1000000, 12.00 / 1000000;
    """
    
    # 2. Master Session Summary
    # Aggregates all events at the `session_id` level. 
    # Purpose: Provide high-level KPIs (Total Cost, Tokens, Duration, Errors) for the entire conversation. 
    # Logic: Summarizes costs across all LLM responses in the session and calculates session-wide duration (End - Start).
    session_master_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_session_summary` AS
    WITH session_costs AS (
      SELECT 
        session_id,
        SUM(CAST(JSON_VALUE(attributes, '$.usage_metadata.total_token_count') AS INT64)) as total_tokens,
        SUM(
          (CAST(JSON_VALUE(attributes, '$.usage_metadata.prompt_token_count') AS INT64) * p.input_cost_per_token) + 
          (CAST(JSON_VALUE(attributes, '$.usage_metadata.candidates_token_count') AS INT64) * p.output_cost_per_token)
        ) as total_usd_cost
      FROM `{dataset_ref}.{table_name}` e
      LEFT JOIN `{dataset_ref}.model_pricing` p 
        ON JSON_VALUE(e.attributes, '$.model_version') = p.model_version
      WHERE event_type = 'LLM_RESPONSE'
      GROUP BY session_id
    )
    SELECT
      e.session_id,
      e.user_id,
      MIN(e.timestamp) AS session_start,
      MAX(e.timestamp) AS session_end,
      TIMESTAMP_DIFF(MAX(e.timestamp), MIN(e.timestamp), MILLISECOND) AS session_duration_ms,
      COUNT(DISTINCT e.invocation_id) AS total_turns,
      COUNTIF(e.event_type = 'USER_MESSAGE_RECEIVED') AS human_messages,
      COUNTIF(e.event_type = 'LLM_REQUEST') AS total_llm_calls,
      COUNTIF(e.event_type = 'TOOL_COMPLETED') AS total_tools_executed,
      COUNTIF(e.status = 'ERROR') AS total_errors,
      MAX(c.total_tokens) AS session_total_tokens,
      MAX(c.total_usd_cost) AS session_total_cost_usd,
      MAX(CAST(JSON_VALUE(e.latency_ms, '$.time_to_first_token_ms') AS INT64)) AS max_ttft_ms
    FROM `{dataset_ref}.{table_name}` e
    LEFT JOIN session_costs c ON e.session_id = c.session_id
    GROUP BY e.session_id, e.user_id;
    """

    # 3. Master Turn Summary
    # Aggregates events at the `invocation_id` (turn) level. 
    # Purpose: Analyze individual user interactions. 
    # Logic: Calculates Latency Attribution by summing LLM response times vs Tool execution times vs Total Turn Duration. 
    # This is the primary source for 'Performance Profile' charts.
    turn_master_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_turn_summary` AS
    WITH turn_costs AS (
      SELECT 
        session_id,
        invocation_id,
        SUM(CAST(JSON_VALUE(attributes, '$.usage_metadata.total_token_count') AS INT64)) as turn_tokens,
        SUM(
          (CAST(JSON_VALUE(attributes, '$.usage_metadata.prompt_token_count') AS INT64) * p.input_cost_per_token) + 
          (CAST(JSON_VALUE(attributes, '$.usage_metadata.candidates_token_count') AS INT64) * p.output_cost_per_token)
        ) as turn_usd_cost
      FROM `{dataset_ref}.{table_name}` e
      LEFT JOIN `{dataset_ref}.model_pricing` p 
        ON JSON_VALUE(e.attributes, '$.model_version') = p.model_version
      WHERE event_type = 'LLM_RESPONSE'
      GROUP BY session_id, invocation_id
    )
    SELECT
      e.session_id,
      e.invocation_id,
      e.user_id,
      MIN(e.timestamp) AS turn_start,
      MAX(e.timestamp) AS turn_end,
      COUNTIF(e.event_type = 'LLM_REQUEST') AS llm_calls_in_turn,
      COUNTIF(e.event_type = 'TOOL_COMPLETED') AS tools_in_turn,
      COUNTIF(e.status = 'ERROR') AS errors_in_turn,
      MAX(c.turn_tokens) AS tokens,
      MAX(c.turn_usd_cost) AS cost,
      SUM(IF(e.event_type = 'LLM_RESPONSE', CAST(JSON_VALUE(e.latency_ms, '$.total_ms') AS INT64), 0)) AS total_llm_latency_ms,
      SUM(IF(e.event_type = 'TOOL_COMPLETED', CAST(JSON_VALUE(e.latency_ms, '$.total_ms') AS INT64), 0)) AS total_tool_latency_ms,
      TIMESTAMP_DIFF(MAX(e.timestamp), MIN(e.timestamp), MILLISECOND) AS turn_duration_ms
    FROM `{dataset_ref}.{table_name}` e
    LEFT JOIN turn_costs c ON e.session_id = c.session_id AND e.invocation_id = c.invocation_id
    GROUP BY e.session_id, e.invocation_id, e.user_id;
    """

    # 4. Master LLM & Prompt Tracing
    # Flattens `LLM_RESPONSE` events to expose prompts and responses for audit. 
    # Purpose: Deep-dive into agent reasoning and prompt debugging. 
    # Logic: Joins with the pricing table to provide a granular cost per individual model call.
    llm_master_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_llm_calls` AS
    SELECT
      e.timestamp,
      e.session_id,
      e.invocation_id,
      e.user_id,
      e.agent,
      JSON_VALUE(e.attributes, '$.model_version') AS model,
      CAST(JSON_VALUE(e.attributes, '$.usage_metadata.prompt_token_count') AS INT64) AS prompt_tokens,
      CAST(JSON_VALUE(e.attributes, '$.usage_metadata.candidates_token_count') AS INT64) AS completion_tokens,
      CAST(JSON_VALUE(e.attributes, '$.usage_metadata.total_token_count') AS INT64) AS total_tokens,
      (
        (CAST(JSON_VALUE(e.attributes, '$.usage_metadata.prompt_token_count') AS INT64) * p.input_cost_per_token) + 
        (CAST(JSON_VALUE(e.attributes, '$.usage_metadata.candidates_token_count') AS INT64) * p.output_cost_per_token)
      ) AS calculated_usd_cost,
      JSON_VALUE(e.content, '$.prompt') AS prompt,
      JSON_VALUE(e.content, '$.response') AS response
    FROM `{dataset_ref}.{table_name}` e
    LEFT JOIN `{dataset_ref}.model_pricing` p 
      ON JSON_VALUE(e.attributes, '$.model_version') = p.model_version
    WHERE e.event_type = 'LLM_RESPONSE';
    """

    # 5. Master Tool Performance
    # Flattens `TOOL_COMPLETED` events for auditing external API performance. 
    # Purpose: Identify slow or failing external dependencies. 
    # Logic: Extracts tool names, arguments, results, and execution latencies.
    tool_master_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_tool_usage` AS
    SELECT
      timestamp,
      session_id,
      invocation_id,
      user_id,
      agent,
      JSON_VALUE(content, '$.tool') AS tool_name,
      status,
      error_message,
      CAST(JSON_VALUE(latency_ms, '$.total_ms') AS INT64) AS latency_ms,
      JSON_VALUE(content, '$.args') AS input_args,
      JSON_VALUE(content, '$.result') AS output_result
    FROM `{dataset_ref}.{table_name}`
    WHERE event_type = 'TOOL_COMPLETED';
    """

    # 6. Model Routing & Orchestrator Flow
    # Tracks how the orchestrator delegates tasks to specialist sub-agents. 
    # Purpose: Visualize agent handoffs and intent classification. 
    # Logic: Filters for `AGENT_COMPLETED` and `LLM_REQUEST` to see the flow of assignments.
    routing_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_agent_routing` AS
    SELECT
      timestamp,
      session_id,
      user_id,
      invocation_id,
      JSON_VALUE(attributes, '$.root_agent_name') AS orchestrator,
      agent as assigned_specialist,
      event_type
    FROM `{dataset_ref}.{table_name}`
    WHERE event_type IN ('AGENT_COMPLETED', 'LLM_REQUEST')
    ORDER BY timestamp DESC;
    """

    # 7. User Context & Intent
    # Extracts the 'User Message' events for semantic analysis. 
    # Purpose: High-level intent tracking and user environment context. 
    # Logic: Grabs raw text summaries and metadata like timezones from user-initiated events.
    intent_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_user_intent` AS
    SELECT
      timestamp,
      session_id,
      user_id,
      JSON_VALUE(content, '$.text_summary') AS raw_user_prompt,
      JSON_VALUE(attributes, '$.session_metadata.state.state."user:timezone"') AS user_timezone
    FROM `{dataset_ref}.{table_name}`
    WHERE event_type = 'USER_MESSAGE_RECEIVED'
    ORDER BY timestamp DESC;
    """

    # 8. Session Transcript (for Chat Replay)
    # Reconstructs the chronological chat feed for the transcript UI. 
    # Purpose: Human-readable playback of the conversation. 
    # Logic: Unions Human messages and Agent responses, using ROW_NUMBER to pick the final agent 
    # output per turn (hiding intermediate internal chain-of-thought/tool-call steps).
    transcript_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_session_transcript` AS
    SELECT 
      timestamp, 
      session_id, 
      user_id,
      'Human' as speaker, 
      JSON_VALUE(content, '$.text') as message
    FROM `{dataset_ref}.{table_name}`
    WHERE event_type = 'USER_MESSAGE_RECEIVED'
    UNION ALL
    SELECT 
      timestamp, 
      session_id, 
      user_id,
      'Agent' as speaker, 
      JSON_VALUE(content, '$.response') as message
    FROM (
      SELECT *, ROW_NUMBER() OVER(PARTITION BY session_id, invocation_id ORDER BY timestamp DESC) as rn
      FROM `{dataset_ref}.{table_name}`
      WHERE event_type = 'LLM_RESPONSE'
    )
    WHERE rn = 1;
    """

    queries = [
        ("Pricing Table", pricing_sql),
        ("Session Summary View", session_master_sql),
        ("Turn Summary View", turn_master_sql),
        ("LLM Calls View", llm_master_sql),
        ("Tool Usage View", tool_master_sql),
        ("Agent Routing View", routing_sql),
        ("User Intent View", intent_sql),
        ("Session Transcript View", transcript_sql)
    ]

    for name, sql in queries:
        try:
            query_job = client.query(sql)
            query_job.result()
            print(f"✅ Created: {name}")
        except Exception as e:
            print(f"❌ Failed to create {name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup BigQuery Views for Agent Analytics Dashboard")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--dataset", required=True, help="BigQuery Dataset ID")
    parser.add_argument("--table", required=True, help="Base BigQuery Table Name")
    
    args = parser.parse_args()
    
    print(f"🚀 Setting up views in {args.project}.{args.dataset} using base table {args.table}...")
    create_views(args.project, args.dataset, args.table)
    print("\n🎉 Setup complete! You can now import the Grafana JSONs and set the variables.")
