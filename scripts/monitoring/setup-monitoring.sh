#!/bin/bash
set -e

echo "Setting up AI Executive Suite Monitoring Stack"
echo "============================================="

# Check if required environment variables are set
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please configure monitoring environment variables."
    exit 1
fi

# Load environment variables
source .env

# Create monitoring directories
mkdir -p monitoring/prometheus/rules
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/alertmanager
mkdir -p monitoring/loki
mkdir -p monitoring/promtail

# Set proper permissions
chmod -R 755 monitoring/

# Create monitoring network
docker network create monitoring-network || true

# Start monitoring stack
echo "Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Check if services are running
services=("prometheus" "grafana" "alertmanager" "loki" "node-exporter" "cadvisor")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.monitoring.yml ps | grep -q "$service.*Up"; then
        echo "✓ $service is running"
    else
        echo "✗ $service is not running"
        all_healthy=false
    fi
done

# Test service endpoints
echo ""
echo "Testing service endpoints..."

# Test Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✓ Prometheus is healthy"
else
    echo "✗ Prometheus health check failed"
    all_healthy=false
fi

# Test Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✓ Grafana is healthy"
else
    echo "✗ Grafana health check failed"
    all_healthy=false
fi

# Test AlertManager
if curl -f http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "✓ AlertManager is healthy"
else
    echo "✗ AlertManager health check failed"
    all_healthy=false
fi

# Import Grafana dashboards
echo ""
echo "Configuring Grafana dashboards..."
sleep 10

# The dashboards should be automatically loaded via provisioning
# But we can also import them via API if needed
GRAFANA_URL="http://admin:${GRAFANA_ADMIN_PASSWORD:-admin}@localhost:3000"

# Check if dashboards are loaded
dashboard_count=$(curl -s "$GRAFANA_URL/api/search" | jq length 2>/dev/null || echo "0")
echo "Loaded $dashboard_count dashboards"

# Set up alert notification channels
echo ""
echo "Configuring alert notification channels..."

# Create Slack notification channel if webhook is configured
if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST "$GRAFANA_URL/api/alert-notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "slack-alerts",
            "type": "slack",
            "settings": {
                "url": "'$SLACK_WEBHOOK_URL'",
                "channel": "#alerts",
                "title": "Grafana Alert",
                "text": "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}"
            }
        }' > /dev/null 2>&1 && echo "✓ Slack notification channel configured"
fi

# Create email notification channel if SMTP is configured
if [ ! -z "$SMTP_SERVER" ]; then
    curl -X POST "$GRAFANA_URL/api/alert-notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "email-alerts",
            "type": "email",
            "settings": {
                "addresses": "'${ALERT_EMAIL:-admin@example.com}'"
            }
        }' > /dev/null 2>&1 && echo "✓ Email notification channel configured"
fi

echo ""
echo "============================================="
if [ "$all_healthy" = true ]; then
    echo "✅ Monitoring stack setup completed successfully!"
    echo ""
    echo "Access URLs:"
    echo "- Grafana Dashboard: http://localhost:3000 (admin/${GRAFANA_ADMIN_PASSWORD:-admin})"
    echo "- Prometheus: http://localhost:9090"
    echo "- AlertManager: http://localhost:9093"
    echo ""
    echo "Next steps:"
    echo "1. Configure alert notification channels in Grafana"
    echo "2. Set up custom dashboards for your specific needs"
    echo "3. Configure external monitoring integrations"
    echo "4. Test alert rules and notifications"
else
    echo "❌ Some monitoring services failed to start properly"
    echo "Check the logs with: docker-compose -f docker-compose.monitoring.yml logs"
    exit 1
fi