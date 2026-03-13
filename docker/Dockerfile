# Use the official Grafana image
FROM grafana/grafana:latest

# Switch to root to install plugin and set up permissions
USER root

# Install BigQuery datasource plugin
RUN grafana-cli plugins install grafana-google-bigquery-datasource

# Create directory for dashboards
RUN mkdir -p /etc/grafana/dashboards/agent-analytics

# Copy dashboard templates
COPY *.template.json /etc/grafana/dashboards/agent-analytics/

# Copy provisioning configurations
COPY docker/provisioning /etc/grafana/provisioning/

# Copy entrypoint script
COPY docker/entrypoint.sh /usr/bin/entrypoint.sh
RUN chmod +x /usr/bin/entrypoint.sh

# Switch back to grafana user
USER grafana

# Use custom entrypoint to handle placeholder replacement
ENTRYPOINT ["/usr/bin/entrypoint.sh"]
