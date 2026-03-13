#!/bin/bash

# Configuration
DASHBOARD_DIR="/etc/grafana/dashboards/agent-analytics"

echo "🚀 Provisioning Agent Analytics dashboards..."
echo "📍 Project: $GCP_PROJECT"
echo "📍 Dataset: $BQ_DATASET"
echo "📍 Table: $BQ_TABLE"

# Replace placeholders in all dashboard templates
if [ -d "$DASHBOARD_DIR" ]; then
    for file in "$DASHBOARD_DIR"/*.template.json; do
        if [ -f "$file" ]; then
            echo "Processing $(basename "$file")..."
            sed -i "s/REPLACE_ME_PROJECT/$GCP_PROJECT/g" "$file"
            sed -i "s/REPLACE_ME_DATASET/$BQ_DATASET/g" "$file"
            sed -i "s/REPLACE_ME_TABLE/$BQ_TABLE/g" "$file"
            # Move to a standard .json extension for Grafana to pick up
            mv "$file" "${file%.template.json}.json"
        fi
    done
fi

# Hand over to the original Grafana entrypoint
exec /run.sh "$@"
