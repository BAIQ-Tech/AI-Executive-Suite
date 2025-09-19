# AI Executive Suite - Monitoring and Alerting Setup

This document describes the comprehensive monitoring and alerting system for the AI Executive Suite production deployment.

## Overview

The monitoring stack includes:
- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **AlertManager** - Alert routing and notifications
- **Loki** - Log aggregation
- **Promtail** - Log collection
- **Custom APM Agent** - Application performance monitoring

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Monitoring    │    │   Alerting      │
│   Instances     │───▶│   Stack         │───▶│   Channels      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
│                      │                      │
├─ App1 (metrics)     ├─ Prometheus         ├─ Email
├─ App2 (metrics)     ├─ Grafana            ├─ Slack
├─ App3 (metrics)     ├─ AlertManager       ├─ PagerDuty
├─ Database          ├─ Loki               └─ Webhooks
├─ Redis             ├─ Promtail
├─ Nginx             └─ APM Agent
└─ System Metrics
```

## Quick Start

### 1. Environment Setup

Copy the monitoring environment template:
```bash
cp .env.prod .env
```

Configure monitoring-specific variables in `.env`:
```bash
# Grafana
GRAFANA_ADMIN_PASSWORD=your_secure_password

# AlertManager
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_FROM_EMAIL=alerts@your-domain.com
CRITICAL_ALERT_EMAIL=critical@your-domain.com
WARNING_ALERT_EMAIL=warnings@your-domain.com

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# PagerDuty
PAGERDUTY_ROUTING_KEY=your_pagerduty_integration_key
```

### 2. Deploy Monitoring Stack

```bash
# Set up monitoring infrastructure
./scripts/monitoring/setup-monitoring.sh

# Or manually start services
docker-compose -f docker-compose.monitoring.yml up -d
```

### 3. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/your_password)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

## Metrics Collection

### Application Metrics

The application exposes metrics at several endpoints:

- `/metrics` - Prometheus format metrics
- `/api/metrics/business` - Business KPIs
- `/api/metrics/health` - Detailed health status
- `/api/metrics/db-metrics` - Database statistics

### Custom Metrics

Key business metrics tracked:
- Active users
- Decisions created (by executive type)
- Documents processed
- AI response accuracy
- Response times
- Error rates

### System Metrics

Collected via exporters:
- **Node Exporter** - System metrics (CPU, memory, disk)
- **cAdvisor** - Container metrics
- **PostgreSQL Exporter** - Database metrics
- **Redis Exporter** - Cache metrics
- **Nginx Exporter** - Web server metrics

## Dashboards

### Pre-configured Dashboards

1. **AI Executive Suite Overview**
   - Application health status
   - Response times and error rates
   - Database and Redis metrics
   - System resource usage

2. **Business Metrics Dashboard**
   - Daily active users
   - Decision creation trends
   - Document processing statistics
   - AI performance metrics

### Custom Dashboard Creation

1. Access Grafana at http://localhost:3000
2. Click "+" → "Dashboard"
3. Add panels with Prometheus queries
4. Save and organize in folders

Example queries:
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Response time 95th percentile
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active users
active_users_total

# Decisions by type
sum by (executive_type) (decisions_by_executive_total)
```

## Alerting

### Alert Rules

Critical alerts:
- Application down
- High error rate (>10%)
- Database connectivity issues
- High resource usage (>90%)

Warning alerts:
- High response time (>2s)
- Low AI accuracy (<70%)
- High resource usage (>80%)

### Notification Channels

Configure in AlertManager (`monitoring/alertmanager/alertmanager.yml`):

#### Email Notifications
```yaml
email_configs:
  - to: 'alerts@your-domain.com'
    subject: '[ALERT] AI Executive Suite'
    body: |
      Alert: {{ .GroupLabels.alertname }}
      Summary: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}
```

#### Slack Notifications
```yaml
slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: 'Alert: {{ .GroupLabels.alertname }}'
```

#### PagerDuty Integration
```yaml
pagerduty_configs:
  - routing_key: 'YOUR_PAGERDUTY_KEY'
    description: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

### Testing Alerts

Test alert rules:
```bash
# Trigger a test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert"
    }
  }]'
```

## Log Management

### Log Collection

Promtail collects logs from:
- Application containers
- System logs
- Nginx access/error logs
- Database logs

### Log Queries

Access logs in Grafana using Loki data source:

```logql
# Application errors
{job="ai-executive-suite"} |= "ERROR"

# Nginx 5xx errors
{job="nginx"} | json | status >= 500

# Database slow queries
{job="postgres"} |= "slow query"
```

### Log Retention

Configure in `monitoring/loki/loki.yml`:
```yaml
limits_config:
  retention_period: 30d  # Keep logs for 30 days
```

## Performance Monitoring

### APM Agent

The custom APM agent collects:
- Business metrics
- System performance
- Application health
- Custom KPIs

### Response Time Monitoring

Track response times for:
- API endpoints
- Database queries
- AI model responses
- External integrations

### Resource Monitoring

Monitor:
- CPU usage
- Memory consumption
- Disk I/O
- Network traffic
- Container resources

## Troubleshooting

### Common Issues

1. **Metrics not appearing**
   - Check if application is exposing `/metrics` endpoint
   - Verify Prometheus scrape configuration
   - Check network connectivity between services

2. **Alerts not firing**
   - Verify alert rules syntax
   - Check AlertManager configuration
   - Test notification channels

3. **Dashboard not loading**
   - Check Grafana data source configuration
   - Verify Prometheus is collecting metrics
   - Check dashboard JSON syntax

### Debug Commands

```bash
# Check service status
docker-compose -f docker-compose.monitoring.yml ps

# View service logs
docker-compose -f docker-compose.monitoring.yml logs prometheus
docker-compose -f docker-compose.monitoring.yml logs grafana
docker-compose -f docker-compose.monitoring.yml logs alertmanager

# Test metrics endpoint
curl http://localhost:5000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test AlertManager
curl http://localhost:9093/api/v1/status
```

## Maintenance

### Regular Tasks

1. **Monitor disk usage** - Prometheus and Loki data can grow large
2. **Update dashboards** - Keep dashboards current with application changes
3. **Review alert rules** - Adjust thresholds based on actual performance
4. **Test notifications** - Regularly test alert channels

### Backup

Important monitoring data to backup:
- Grafana dashboards and configuration
- Prometheus alert rules
- AlertManager configuration

```bash
# Backup Grafana dashboards
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3000/api/search | \
  jq -r '.[] | .uid' | \
  xargs -I {} curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3000/api/dashboards/uid/{} > dashboards_backup.json
```

### Scaling

For high-traffic deployments:
1. Use Prometheus federation for multiple instances
2. Implement Grafana clustering
3. Use external storage for metrics (e.g., Thanos)
4. Set up log shipping to external systems

## Security

### Access Control

1. **Grafana Authentication**
   - Enable LDAP/OAuth integration
   - Set up role-based access control
   - Use strong admin passwords

2. **Network Security**
   - Restrict access to monitoring ports
   - Use TLS for external access
   - Implement VPN for remote access

3. **Data Protection**
   - Encrypt metrics data at rest
   - Secure alert notification channels
   - Audit monitoring access

### Best Practices

1. Use service accounts for integrations
2. Rotate API keys regularly
3. Monitor the monitoring system itself
4. Keep monitoring stack updated
5. Document all customizations

## Integration with CI/CD

The monitoring stack integrates with the deployment pipeline:

1. **Health checks** during deployment
2. **Automated rollback** on alert conditions
3. **Performance regression** detection
4. **Deployment notifications** to monitoring channels

See the CI/CD documentation for more details on integration points.