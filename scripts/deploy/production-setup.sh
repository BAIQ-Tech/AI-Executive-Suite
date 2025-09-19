#!/bin/bash
set -e

echo "Setting up AI Executive Suite Production Infrastructure"

# Check if required environment variables are set
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.prod to .env and configure it."
    exit 1
fi

# Load environment variables
source .env

# Create necessary directories
mkdir -p nginx/ssl
mkdir -p backups
mkdir -p logs

# Generate SSL certificates (self-signed for development, replace with real certs for production)
if [ ! -f nginx/ssl/cert.pem ]; then
    echo "Generating SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Update replication password in init script
sed -i "s/REPLICATION_PASSWORD_PLACEHOLDER/$REPLICATION_PASSWORD/g" postgres/init-replication.sql

# Build Docker images
echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Create Docker networks
docker network create app-network || true

# Start infrastructure services first
echo "Starting infrastructure services..."
docker-compose -f docker-compose.prod.yml up -d postgres-primary redis-cluster

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 30

# Run database migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm app1 python -c "
from models import db
from app import app
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"

# Start replica database
echo "Starting replica database..."
docker-compose -f docker-compose.prod.yml up -d postgres-replica

# Wait for replica to sync
sleep 20

# Start application instances
echo "Starting application instances..."
docker-compose -f docker-compose.prod.yml up -d app1 app2 app3

# Start load balancer
echo "Starting load balancer..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Start backup service
echo "Starting backup service..."
docker-compose -f docker-compose.prod.yml up -d backup-service

# Health check
echo "Performing health checks..."
sleep 10

# Check if services are running
services=("nginx" "app1" "app2" "app3" "postgres-primary" "postgres-replica" "redis-cluster" "backup-service")
for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "$service.*Up"; then
        echo "✓ $service is running"
    else
        echo "✗ $service is not running"
        exit 1
    fi
done

# Test application endpoints
echo "Testing application endpoints..."
if curl -k -f https://localhost/health > /dev/null 2>&1; then
    echo "✓ Application health check passed"
else
    echo "✗ Application health check failed"
    exit 1
fi

echo ""
echo "Production infrastructure setup completed successfully!"
echo ""
echo "Services running:"
echo "- Load Balancer: https://localhost"
echo "- Application instances: 3 instances behind load balancer"
echo "- Database: PostgreSQL with read replica"
echo "- Cache: Redis cluster"
echo "- Backup service: Automated backups to S3"
echo ""
echo "Next steps:"
echo "1. Configure your domain and SSL certificates"
echo "2. Set up monitoring and alerting"
echo "3. Configure external integrations"
echo "4. Test disaster recovery procedures"