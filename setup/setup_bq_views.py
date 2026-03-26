import os
import argparse
from google.cloud import bigquery

def create_views(project_id, dataset_id, table_name):
    client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{dataset_id}"

    # 1. Model Pricing Table
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
    session_master_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_aaa_session_summary` AS
    WITH session_costs AS (
      SELECT 
        session_id,
        SUM(CAST(JSON_VALUE(attributes, '$.usage_metadata.total_token_count') AS INT64)) as total_tokens,
        SUM(CAST(JSON_VALUE(attributes, '$.usage_metadata.prompt_token_count') AS INT64)) as prompt_tokens,
        SUM(CAST(JSON_VALUE(attributes, '$.usage_metadata.candidates_token_count') AS INT64)) as output_tokens,
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
      MAX(c.prompt_tokens) AS session_prompt_tokens,
      MAX(c.output_tokens) AS session_completion_tokens,
      MAX(c.total_usd_cost) AS session_total_cost_usd,
      MAX(CAST(JSON_VALUE(e.latency_ms, '$.time_to_first_token_ms') AS INT64)) AS max_ttft_ms
    FROM `{dataset_ref}.{table_name}` e
    LEFT JOIN session_costs c ON e.session_id = c.session_id
    GROUP BY e.session_id, e.user_id;
    """

    # 3. Master Turn Summary
    turn_master_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_aaa_turn_summary` AS
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
      ROW_NUMBER() OVER(PARTITION BY e.session_id ORDER BY MIN(e.timestamp)) as turn_index,
      MIN(e.timestamp) AS turn_start,
      MAX(e.timestamp) AS turn_end,
      COUNTIF(e.event_type = 'LLM_REQUEST') AS llm_calls_in_turn,
      COUNTIF(e.event_type = 'TOOL_COMPLETED') AS tools_in_turn,
      COUNTIF(e.status = 'ERROR') AS errors_in_turn,
      MAX(c.turn_tokens) AS tokens,
      MAX(c.turn_usd_cost) AS cost,
      SUM(IF(e.event_type = 'LLM_RESPONSE', CAST(JSON_VALUE(e.latency_ms, '$.total_ms') AS INT64), 0)) AS total_llm_latency_ms,
      SUM(IF(e.event_type = 'TOOL_COMPLETED', CAST(JSON_VALUE(e.latency_ms, '$.total_ms') AS INT64), 0)) AS total_tool_latency_ms,
      TIMESTAMP_DIFF(MAX(e.timestamp), MIN(e.timestamp), MILLISECOND) AS turn_duration_ms,
      GREATEST(0, TIMESTAMP_DIFF(MAX(e.timestamp), MIN(e.timestamp), MILLISECOND) - 
        SUM(IF(e.event_type = 'LLM_RESPONSE', CAST(JSON_VALUE(e.latency_ms, '$.total_ms') AS INT64), 0)) - 
        SUM(IF(e.event_type = 'TOOL_COMPLETED', CAST(JSON_VALUE(e.latency_ms, '$.total_ms') AS INT64), 0))) AS turn_overhead_ms
    FROM `{dataset_ref}.{table_name}` e
    LEFT JOIN turn_costs c ON e.session_id = c.session_id AND e.invocation_id = c.invocation_id
    GROUP BY e.session_id, e.invocation_id, e.user_id;
    """

    # 4. Master LLM & Prompt Tracing
    llm_master_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_aaa_llm_calls` AS
    WITH prompts AS (
      SELECT 
        invocation_id, 
        session_id,
        ANY_VALUE(COALESCE(
          TO_JSON_STRING(JSON_QUERY(content, '$.prompt')), 
          TO_JSON_STRING(JSON_QUERY(content, '$.request.prompt')),
          JSON_VALUE(content, '$.prompt'),
          JSON_VALUE(content, '$.request.prompt')
        )) as turn_prompt
      FROM `{dataset_ref}.{table_name}`
      WHERE event_type IN ('LLM_REQUEST', 'LLM_RESPONSE') 
        AND (JSON_QUERY(content, '$.prompt') IS NOT NULL OR JSON_QUERY(content, '$.request.prompt') IS NOT NULL)
      GROUP BY invocation_id, session_id
    )
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
      COALESCE(pr.turn_prompt, TO_JSON_STRING(JSON_QUERY(e.content, '$.prompt'))) AS prompt,
      COALESCE(
        JSON_VALUE(e.content, '$.response.text'), 
        JSON_VALUE(e.content, '$.response'), 
        JSON_VALUE(e.content, '$.text'),
        TO_JSON_STRING(JSON_QUERY(e.content, '$.response')),
        TO_JSON_STRING(e.content)
      ) AS response
    FROM `{dataset_ref}.{table_name}` e
    LEFT JOIN `{dataset_ref}.model_pricing` p 
      ON JSON_VALUE(e.attributes, '$.model_version') = p.model_version
    LEFT JOIN prompts pr
      ON e.invocation_id = pr.invocation_id AND e.session_id = pr.session_id
    WHERE e.event_type = 'LLM_RESPONSE';
    """

    # 5. Master Tool Performance
    tool_master_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_aaa_tool_usage` AS
    WITH tool_starts AS (
      SELECT 
        invocation_id, session_id, user_id, agent,
        JSON_VALUE(content, '$.tool') AS tool_name,
        COALESCE(
          TO_JSON_STRING(JSON_QUERY(content, '$.args')), JSON_VALUE(content, '$.args'),
          TO_JSON_STRING(JSON_QUERY(content, '$.arguments')), JSON_VALUE(content, '$.arguments'),
          TO_JSON_STRING(JSON_QUERY(content, '$.parameters')), JSON_VALUE(content, '$.parameters'),
          TO_JSON_STRING(JSON_QUERY(content, '$.input')), JSON_VALUE(content, '$.input')
        ) AS input_args
      FROM `{dataset_ref}.{table_name}`
      WHERE event_type = 'TOOL_STARTING'
    ),
    tool_completes AS (
      SELECT
        invocation_id, timestamp, status, error_message,
        JSON_VALUE(content, '$.tool') AS tool_name,
        CAST(JSON_VALUE(latency_ms, '$.total_ms') AS INT64) AS latency_ms,
        COALESCE(
          TO_JSON_STRING(JSON_QUERY(content, '$.result')), JSON_VALUE(content, '$.result'),
          TO_JSON_STRING(JSON_QUERY(content, '$.response')), JSON_VALUE(content, '$.response'),
          TO_JSON_STRING(JSON_QUERY(content, '$.output')), JSON_VALUE(content, '$.output')
        ) AS output_result
      FROM `{dataset_ref}.{table_name}`
      WHERE event_type = 'TOOL_COMPLETED'
    )
    SELECT
      tc.timestamp, ts.session_id, ts.invocation_id, ts.user_id, ts.agent, ts.tool_name,
      tc.status, tc.error_message, tc.latency_ms, ts.input_args, tc.output_result
    FROM tool_starts ts
    JOIN tool_completes tc 
      ON ts.invocation_id = tc.invocation_id 
      AND ts.tool_name = tc.tool_name;
    """

    # 6. Model Routing & Orchestrator Flow
    routing_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_aaa_agent_routing` AS
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
    intent_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_aaa_user_intent` AS
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

    # 8. Session Transcript (Chat Replay)
    transcript_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_aaa_session_transcript` AS
    SELECT 
      timestamp, 
      session_id, 
      user_id,
      'Human' as speaker, 
      COALESCE(JSON_VALUE(content, '$.text'), JSON_VALUE(content, '$.text_summary')) as message
    FROM `{dataset_ref}.{table_name}`
    WHERE event_type = 'USER_MESSAGE_RECEIVED'
    UNION ALL
    SELECT 
      timestamp, 
      session_id, 
      user_id,
      'Agent' as speaker, 
      COALESCE(JSON_VALUE(content, '$.response.text'), JSON_VALUE(content, '$.response'), JSON_VALUE(content, '$.text')) as message
    FROM (
      SELECT *, ROW_NUMBER() OVER(PARTITION BY session_id, invocation_id ORDER BY timestamp DESC) as rn
      FROM `{dataset_ref}.{table_name}`
      WHERE event_type = 'LLM_RESPONSE'
    )
    WHERE rn = 1;
    """

    
    # 9. Unified Session Chronology
    chronology_sql = f"""
    CREATE OR REPLACE VIEW `{dataset_ref}.v_aaa_session_chronology` AS
    WITH raw_data AS (
      SELECT
        timestamp as time,
        session_id,
        user_id,
        invocation_id,
        event_type,
        status,
        error_message,
        content,
        agent,
        attributes,
        latency_ms
      FROM `{dataset_ref}.{table_name}`
    ),
    prompts AS (
      -- Extract prompts from any event in the turn (LLM_REQUEST or LLM_RESPONSE)
      SELECT 
        invocation_id, 
        session_id,
        ANY_VALUE(COALESCE(JSON_VALUE(content, '$.prompt'), JSON_VALUE(content, '$.request.prompt'))) as turn_prompt
      FROM raw_data
      WHERE event_type IN ('LLM_REQUEST', 'LLM_RESPONSE') 
        AND (JSON_VALUE(content, '$.prompt') IS NOT NULL OR JSON_VALUE(content, '$.request.prompt') IS NOT NULL)
      GROUP BY invocation_id, session_id
    ),
    base_events AS (
      SELECT
        r.*,
        CASE 
          WHEN r.event_type = 'USER_MESSAGE_RECEIVED' THEN '👤 Human Input'
          WHEN r.event_type = 'TOOL_STARTING' THEN '🔧 Tool Starting'
          WHEN r.event_type = 'TOOL_COMPLETED' THEN '✅ Tool Execution Result'
          WHEN r.event_type = 'LLM_REQUEST' THEN '🧠 Agent Reasoning (Start)'
          WHEN r.event_type = 'LLM_RESPONSE' THEN '🗣️ Agent Output'
          WHEN r.event_type = 'AGENT_STARTING' THEN '🔀 Sub-Agent Routing'
          WHEN r.event_type = 'AGENT_COMPLETED' THEN '🏁 Sub-Agent Completed'
          ELSE r.event_type
        END as step_type,
        COALESCE(
          JSON_VALUE(r.content, '$.tool'),
          r.agent,
          JSON_VALUE(r.attributes, '$.root_agent_name'),
          'System'
        ) as actor,
        COALESCE(CAST(JSON_VALUE(r.latency_ms, '$.total_ms') AS INT64), 0) as duration_ms,
        p.turn_prompt
      FROM raw_data r
      LEFT JOIN prompts p ON r.invocation_id = p.invocation_id AND r.session_id = p.session_id
      WHERE r.event_type IN (
        'USER_MESSAGE_RECEIVED', 
        'LLM_REQUEST', 
        'LLM_RESPONSE', 
        'TOOL_STARTING', 
        'TOOL_COMPLETED', 
        'AGENT_STARTING', 
        'AGENT_COMPLETED'
      )
    )
    SELECT
      time, session_id, user_id, invocation_id, event_type, step_type, actor, duration_ms, status, error_message,
      -- 1. Conversation Message (Expanded UI - Identical to Transcripts)
      CASE
        WHEN event_type = 'USER_MESSAGE_RECEIVED' THEN 
          COALESCE(JSON_VALUE(content, '$.text'), JSON_VALUE(content, '$.text_summary'))
        WHEN event_type IN ('LLM_RESPONSE', 'AGENT_COMPLETED') AND (actor = JSON_VALUE(attributes, '$.root_agent_name') OR agent = JSON_VALUE(attributes, '$.root_agent_name')) THEN 
          COALESCE(JSON_VALUE(content, '$.response.text'), JSON_VALUE(content, '$.response'), JSON_VALUE(content, '$.text'))
        ELSE NULL
      END as message,
      -- 2. Technical Details (Collapsed UI with Eye Icon)
      CASE
        WHEN event_type = 'TOOL_STARTING' THEN 
          TO_JSON_STRING(COALESCE(JSON_QUERY(content, '$.args'), JSON_QUERY(content, '$.arguments'), JSON_QUERY(content, '$.parameters'), JSON_QUERY(content, '$.input'), content))
        WHEN event_type = 'TOOL_COMPLETED' THEN 
          TO_JSON_STRING(COALESCE(JSON_QUERY(content, '$.result'), JSON_QUERY(content, '$.response'), JSON_QUERY(content, '$.output'), content))
        WHEN event_type = 'LLM_REQUEST' THEN 
          CONCAT('🧠 Inference started (', actor, ')')
        WHEN event_type IN ('LLM_RESPONSE', 'AGENT_COMPLETED') AND NOT (actor = JSON_VALUE(attributes, '$.root_agent_name') OR agent = JSON_VALUE(attributes, '$.root_agent_name')) THEN 
          TO_JSON_STRING(content)
        ELSE NULL
      END as technical_details,
      -- 3. Always provide full details for the 'Inspect' side-drawer
      COALESCE(TO_JSON_STRING(content), '(No data)') as _full_details
    FROM base_events
    ORDER BY time ASC;
    """

    queries = [
        ("Pricing Table", pricing_sql),
        ("Session Summary View", session_master_sql),
        ("Turn Summary View", turn_master_sql),
        ("LLM Calls View", llm_master_sql),
        ("Tool Usage View", tool_master_sql),
        ("Agent Routing View", routing_sql),
        ("User Intent View", intent_sql),
        ("Session Transcript View", transcript_sql),
        ("Unified Session Chronology", chronology_sql)
    ]

    table_success = 0
    view_success = 0
    fail_count = 0

    for name, sql in queries:
        try:
            query_job = client.query(sql)
            query_job.result()
            print(f"✅ Created: {name}")
            if "Table" in name:
                table_success += 1
            else:
                view_success += 1
        except Exception as e:
            print(f"❌ Failed to create {name}: {e}")
            fail_count += 1

    print(f"\n📊 Summary: {table_success} Tables and {view_success} Views created successfully. ({fail_count} failed)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup BigQuery Views for Agent Analytics Dashboard")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--dataset", required=True, help="BigQuery Dataset ID")
    parser.add_argument("--table", required=True, help="Base BigQuery Table Name")
    
    args = parser.parse_args()
    
    print(f"🚀 Setting up views in {args.project}.{args.dataset} using base table {args.table}...")
    create_views(args.project, args.dataset, args.table)
    print("\n🎉 Setup complete! You can now import the Grafana JSONs and set the variables.")
