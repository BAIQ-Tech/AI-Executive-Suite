#!/bin/bash
set -e

echo "AI Executive Suite Rollback Script"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Error: docker-compose.prod.yml not found. Are you in the right directory?"
    exit 1
fi

# Function to show available rollback versions
show_rollback_versions() {
    echo "Available rollback versions:"
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" | grep rollback | head -10
}

# Function to perform rollback
perform_rollback() {
    local rollback_version=$1
    
    if [ -z "$rollback_version" ]; then
        echo "Error: No rollback version specified"
        show_rollback_versions
        exit 1
    fi
    
    echo "Rolling back to version: $rollback_version"
    
    # Create backup of current state
    echo "Creating backup of current deployment..."
    docker tag ghcr.io/your-org/ai-executive-suite:latest ghcr.io/your-org/ai-executive-suite:pre-rollback-$(date +%Y%m%d-%H%M%S)
    
    # Update docker-compose to use rollback version
    echo "Updating docker-compose configuration..."
    cp docker-compose.prod.yml docker-compose.prod.yml.backup
    sed -i "s|ghcr.io/your-org/ai-executive-suite:latest|$rollback_version|g" docker-compose.prod.yml
    
    # Perform rolling restart
    echo "Performing rolling restart..."
    
    # Restart app instances one by one
    for app in app1 app2 app3; do
        echo "Restarting $app..."
        docker-compose -f docker-compose.prod.yml up -d --no-deps $app
        
        # Wait for health check
        echo "Waiting for $app to be healthy..."
        sleep 30
        
        # Check if the app is responding
        if ! ./scripts/deploy/health-check.sh > /dev/null 2>&1; then
            echo "Error: $app failed health check during rollback"
            echo "Attempting to restore previous version..."
            cp docker-compose.prod.yml.backup docker-compose.prod.yml
            docker-compose -f docker-compose.prod.yml up -d --no-deps $app
            exit 1
        fi
        
        echo "$app rollback completed successfully"
    done
    
    # Final health check
    echo "Performing final health check..."
    if ./scripts/deploy/health-check.sh; then
        echo "✅ Rollback completed successfully!"
        
        # Clean up backup
        rm docker-compose.prod.yml.backup
        
        # Update deployment metadata
        echo "ROLLBACK_VERSION=$rollback_version" >> .env
        echo "ROLLBACK_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .env
        
    else
        echo "❌ Rollback failed final health check"
        exit 1
    fi
}

# Function to show rollback status
show_status() {
    echo "Current deployment status:"
    echo "========================="
    
    # Show current image versions
    echo "Current image versions:"
    docker-compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Image}}\t{{.Status}}"
    
    echo ""
    echo "Recent rollback history:"
    grep "ROLLBACK_" .env 2>/dev/null || echo "No rollback history found"
    
    echo ""
    echo "Health status:"
    ./scripts/deploy/health-check.sh
}

# Main script logic
case "${1:-}" in
    "list")
        show_rollback_versions
        ;;
    "status")
        show_status
        ;;
    "rollback")
        if [ -z "$2" ]; then
            echo "Usage: $0 rollback <version>"
            echo ""
            show_rollback_versions
            exit 1
        fi
        perform_rollback "$2"
        ;;
    "auto")
        # Auto-rollback to most recent version
        latest_rollback=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep rollback | head -1)
        if [ -z "$latest_rollback" ]; then
            echo "Error: No rollback versions available"
            exit 1
        fi
        perform_rollback "$latest_rollback"
        ;;
    *)
        echo "Usage: $0 {list|status|rollback <version>|auto}"
        echo ""
        echo "Commands:"
        echo "  list                    - Show available rollback versions"
        echo "  status                  - Show current deployment status"
        echo "  rollback <version>      - Rollback to specific version"
        echo "  auto                    - Rollback to most recent version"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 rollback ghcr.io/your-org/ai-executive-suite:rollback-20231201-143022"
        echo "  $0 auto"
        exit 1
        ;;
esac