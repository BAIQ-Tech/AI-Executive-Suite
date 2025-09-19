#!/bin/bash
set -e

echo "AI Executive Suite Production Health Check"
echo "========================================"

# Check Docker services
echo "Checking Docker services..."
services=("nginx" "app1" "app2" "app3" "postgres-primary" "postgres-replica" "redis-cluster" "backup-service")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "$service.*Up"; then
        echo "✓ $service is running"
    else
        echo "✗ $service is not running"
        all_healthy=false
    fi
done

# Check application endpoints
echo ""
echo "Checking application endpoints..."

# Health endpoint
if curl -k -f https://localhost/health > /dev/null 2>&1; then
    echo "✓ Health endpoint responding"
else
    echo "✗ Health endpoint not responding"
    all_healthy=false
fi

# Main application
if curl -k -f https://localhost/ > /dev/null 2>&1; then
    echo "✓ Main application responding"
else
    echo "✗ Main application not responding"
    all_healthy=false
fi

# API endpoints
if curl -k -f https://localhost/api/executives > /dev/null 2>&1; then
    echo "✓ API endpoints responding"
else
    echo "✗ API endpoints not responding"
    all_healthy=false
fi

# Check database connectivity
echo ""
echo "Checking database connectivity..."
if docker-compose -f docker-compose.prod.yml exec -T postgres-primary pg_isready -U ai_exec_user -d ai_executive_suite > /dev/null 2>&1; then
    echo "✓ Primary database is ready"
else
    echo "✗ Primary database is not ready"
    all_healthy=false
fi

if docker-compose -f docker-compose.prod.yml exec -T postgres-replica pg_isready -U ai_exec_user -d ai_executive_suite > /dev/null 2>&1; then
    echo "✓ Replica database is ready"
else
    echo "✗ Replica database is not ready"
    all_healthy=false
fi

# Check Redis connectivity
echo ""
echo "Checking Redis connectivity..."
if docker-compose -f docker-compose.prod.yml exec -T redis-cluster redis-cli ping | grep -q "PONG"; then
    echo "✓ Redis is responding"
else
    echo "✗ Redis is not responding"
    all_healthy=false
fi

# Check disk space
echo ""
echo "Checking disk space..."
df -h | grep -E "(/$|/var)" | while read line; do
    usage=$(echo $line | awk '{print $5}' | sed 's/%//')
    if [ $usage -gt 80 ]; then
        echo "⚠ High disk usage: $line"
    else
        echo "✓ Disk usage OK: $line"
    fi
done

# Check memory usage
echo ""
echo "Checking memory usage..."
free -h | grep Mem | awk '{
    used = $3
    total = $2
    printf "Memory usage: %s / %s\n", used, total
}'

# Check load average
echo ""
echo "Checking system load..."
uptime | awk '{
    print "Load average:", $(NF-2), $(NF-1), $NF
}'

# Summary
echo ""
echo "========================================"
if [ "$all_healthy" = true ]; then
    echo "✓ All systems healthy"
    exit 0
else
    echo "✗ Some systems are unhealthy"
    exit 1
fi