import json

template_path = 'dashboard_templates/grafana_landing_page.template.json'

with open(template_path, 'r') as f:
    dashboard = json.load(f)

# Find the panel with ID 15
panels = dashboard.get('panels', [])
target_index = -1
for i, panel in enumerate(panels):
    if panel.get('id') == 15:
        target_index = i
        break

if target_index != -1:
    # 1. Update Panel 15 to be Token Pie Chart
    panel_15 = panels[target_index]
    panel_15['type'] = 'piechart'
    panel_15['title'] = '💰 Token Distribution by App'
    panel_15['gridPos'] = {
        "h": 10,
        "w": 12,
        "x": 0,
        "y": 20
    }
    panel_15['fieldConfig'] = {
        "defaults": {
            "color": { "mode": "palette-classic" },
            "custom": { "hideFrom": { "legend": False, "tooltip": False, "viz": False } },
            "unit": "short"
        },
        "overrides": []
    }
    panel_15['options'] = {
        "reduceOptions": { "values": False, "calcs": ["sum"], "fields": "" },
        "pieType": "donut",
        "displayLabels": ["name", "percent"],
        "legend": { "showLegend": True, "displayMode": "list", "placement": "right" },
        "tooltip": { "mode": "single", "sort": "none" }
    }
    # SQL query for panel 15 remains the same (already groups by app_name)

    # 2. Create Panel 16 for Cost Pie Chart
    panel_16 = {
        "type": "piechart",
        "title": "💵 Cost Distribution by App",
        "gridPos": {
            "h": 10,
            "w": 12,
            "x": 12,
            "y": 20
        },
        "fieldConfig": {
            "defaults": {
                "color": { "mode": "palette-classic" },
                "custom": { "hideFrom": { "legend": False, "tooltip": False, "viz": False } },
                "unit": "usd"
            },
            "overrides": []
        },
        "options": {
            "reduceOptions": { "values": False, "calcs": ["sum"], "fields": "" },
            "pieType": "donut",
            "displayLabels": ["name", "percent"],
            "legend": { "showLegend": True, "displayMode": "list", "placement": "right" },
            "tooltip": { "mode": "single", "sort": "none" }
        },
        "targets": [
            {
                "rawSql": "SELECT app_name, SUM(session_total_cost_usd) as total_cost FROM `${gcp_project}.${bq_dataset}.v_aaa_session_summary` WHERE $__timeFilter(session_start) AND (app_name = '${application:raw}' OR '${application:raw}' IN ('All', 'Select_Application', '$__all')) AND (user_id = '${user_id:raw}' OR '${user_id:raw}' IN ('All', 'Select_User')) AND (session_id = '${session_id:raw}' OR '${session_id:raw}' IN ('All', 'Select_Session')) GROUP BY app_name ORDER BY total_cost DESC",
                "format": "table",
                "datasource": {
                    "type": "grafana-bigquery-datasource",
                    "uid": "${datasource}"
                }
            }
        ],
        "id": 16
    }

    # Insert Panel 16 after Panel 15
    panels.insert(target_index + 1, panel_16)
    
    # Save back to file
    with open(template_path, 'w') as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    print("Successfully updated landing page template with side-by-side pie charts.")
else:
    print("Could not find panel with ID 15.")
