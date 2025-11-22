#!/bin/bash
#
# EDMS Docker Network Setup Script
# 
# Sets up isolated Docker networks for multi-app server environment
# with proper network segmentation and security

set -e

echo "🐳 EDMS Docker Network Setup"
echo "============================="

# Check if Docker is running
if ! systemctl is-active --quiet docker; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Remove existing EDMS networks if they exist
echo "🧹 Cleaning up existing networks..."
docker network rm edms_network 2>/dev/null || true
docker network rm edms_backend_network 2>/dev/null || true
docker network rm edms_frontend_network 2>/dev/null || true

# Create main EDMS network with custom subnet
echo "🌐 Creating main EDMS network..."
docker network create \
    --driver bridge \
    --subnet=172.20.0.0/16 \
    --ip-range=172.20.240.0/20 \
    --gateway=172.20.0.1 \
    --opt com.docker.network.bridge.name=br-edms \
    --opt com.docker.network.bridge.enable_icc=true \
    --opt com.docker.network.bridge.enable_ip_masquerade=true \
    --opt com.docker.network.driver.mtu=1500 \
    --label project=edms \
    --label environment=production \
    edms_network

# Create backend-specific network for database and cache
echo "🔙 Creating backend services network..."
docker network create \
    --driver bridge \
    --subnet=172.21.0.0/16 \
    --ip-range=172.21.240.0/20 \
    --gateway=172.21.0.1 \
    --opt com.docker.network.bridge.name=br-edms-backend \
    --opt com.docker.network.bridge.enable_icc=true \
    --opt com.docker.network.bridge.enable_ip_masquerade=false \
    --label project=edms \
    --label tier=backend \
    edms_backend_network

# Create frontend-specific network
echo "🎨 Creating frontend network..."
docker network create \
    --driver bridge \
    --subnet=172.22.0.0/16 \
    --ip-range=172.22.240.0/20 \
    --gateway=172.22.0.1 \
    --opt com.docker.network.bridge.name=br-edms-frontend \
    --opt com.docker.network.bridge.enable_icc=false \
    --label project=edms \
    --label tier=frontend \
    edms_frontend_network

# Configure iptables rules for network isolation
echo "🔒 Configuring network isolation rules..."

# Allow communication within EDMS networks
sudo iptables -I DOCKER-ISOLATION-STAGE-1 -i br-edms -o br-edms-backend -j ACCEPT
sudo iptables -I DOCKER-ISOLATION-STAGE-1 -i br-edms-backend -o br-edms -j ACCEPT
sudo iptables -I DOCKER-ISOLATION-STAGE-1 -i br-edms -o br-edms-frontend -j ACCEPT
sudo iptables -I DOCKER-ISOLATION-STAGE-1 -i br-edms-frontend -o br-edms -j ACCEPT

# Block communication between frontend and backend networks
sudo iptables -I DOCKER-ISOLATION-STAGE-1 -i br-edms-frontend -o br-edms-backend -j DROP
sudo iptables -I DOCKER-ISOLATION-STAGE-1 -i br-edms-backend -o br-edms-frontend -j DROP

# Block access to host network from containers (except specific ports)
sudo iptables -I DOCKER-USER -i br-edms+ -d 172.17.0.1 -j DROP
sudo iptables -I DOCKER-USER -i br-edms+ -d 172.20.0.1 -p tcp --dport 22 -j ACCEPT
sudo iptables -I DOCKER-USER -i br-edms+ -d 172.20.0.1 -p tcp --dport 8000 -j ACCEPT

# Create network monitoring script
echo "📊 Creating network monitoring script..."
cat > /opt/edms/monitoring/scripts/network-monitor.sh << 'EOF'
#!/bin/bash
#
# EDMS Network Monitor
# Monitors Docker network status and connectivity

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/opt/edms/monitoring/logs/network-monitor.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "=== EDMS Network Status - $TIMESTAMP ===" >> "$LOG_FILE"

# Check network existence
NETWORKS=("edms_network" "edms_backend_network" "edms_frontend_network")
for network in "${NETWORKS[@]}"; do
    if docker network ls | grep -q "$network"; then
        echo "✅ Network $network exists" >> "$LOG_FILE"
        
        # Get network details
        SUBNET=$(docker network inspect "$network" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
        GATEWAY=$(docker network inspect "$network" --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}')
        echo "   Subnet: $SUBNET, Gateway: $GATEWAY" >> "$LOG_FILE"
        
        # Count connected containers
        CONTAINERS=$(docker network inspect "$network" --format '{{len .Containers}}')
        echo "   Connected containers: $CONTAINERS" >> "$LOG_FILE"
    else
        echo "❌ Network $network missing" >> "$LOG_FILE"
    fi
done

# Check iptables rules
echo "" >> "$LOG_FILE"
echo "Active DOCKER-ISOLATION rules:" >> "$LOG_FILE"
sudo iptables -L DOCKER-ISOLATION-STAGE-1 -n | grep "br-edms" >> "$LOG_FILE" 2>/dev/null || echo "No isolation rules found" >> "$LOG_FILE"

# Check for network conflicts
echo "" >> "$LOG_FILE"
echo "Network interface status:" >> "$LOG_FILE"
ip addr show | grep "br-edms" | head -5 >> "$LOG_FILE"

echo "===========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
EOF

chmod +x /opt/edms/monitoring/scripts/network-monitor.sh

# Create network management script
echo "🛠️  Creating network management script..."
cat > /usr/local/bin/edms-network-manager << 'EOF'
#!/bin/bash
#
# EDMS Network Manager
# Manages EDMS Docker networks

case "$1" in
    status)
        echo "=== EDMS Docker Networks ==="
        docker network ls | grep edms
        echo ""
        echo "=== Network Details ==="
        for network in edms_network edms_backend_network edms_frontend_network; do
            if docker network ls | grep -q "$network"; then
                echo "Network: $network"
                docker network inspect "$network" --format "  Subnet: {{range .IPAM.Config}}{{.Subnet}}{{end}}"
                docker network inspect "$network" --format "  Gateway: {{range .IPAM.Config}}{{.Gateway}}{{end}}"
                docker network inspect "$network" --format "  Containers: {{len .Containers}}"
                echo ""
            fi
        done
        ;;
    
    connectivity)
        echo "=== Testing Network Connectivity ==="
        
        # Test if containers can reach each other
        if docker ps | grep -q edms_backend; then
            echo "Testing backend to database connectivity..."
            docker exec edms_backend ping -c 2 edms_db 2>/dev/null && echo "✅ Backend -> Database: OK" || echo "❌ Backend -> Database: Failed"
            
            echo "Testing backend to Redis connectivity..."
            docker exec edms_backend ping -c 2 edms_redis 2>/dev/null && echo "✅ Backend -> Redis: OK" || echo "❌ Backend -> Redis: Failed"
        fi
        
        if docker ps | grep -q edms_frontend; then
            echo "Testing frontend connectivity..."
            docker exec edms_frontend ping -c 2 edms_backend 2>/dev/null && echo "✅ Frontend -> Backend: OK" || echo "❌ Frontend -> Backend: Failed"
        fi
        ;;
    
    reset)
        echo "🔄 Resetting EDMS networks..."
        docker-compose down 2>/dev/null || true
        
        # Remove networks
        for network in edms_network edms_backend_network edms_frontend_network; do
            docker network rm "$network" 2>/dev/null || true
        done
        
        # Recreate networks
        /opt/edms/scripts/docker-network-setup.sh
        echo "✅ Networks reset successfully"
        ;;
    
    cleanup)
        echo "🧹 Cleaning up unused networks..."
        docker network prune -f
        echo "✅ Cleanup completed"
        ;;
    
    *)
        echo "EDMS Network Manager"
        echo "Usage: $0 {status|connectivity|reset|cleanup}"
        echo ""
        echo "Commands:"
        echo "  status      - Show network status and details"
        echo "  connectivity - Test network connectivity between services"
        echo "  reset       - Reset and recreate all EDMS networks"
        echo "  cleanup     - Remove unused Docker networks"
        exit 1
        ;;
esac
EOF

sudo chmod +x /usr/local/bin/edms-network-manager

# Update docker-compose.yml to use the new networks
echo "📝 Creating network configuration for docker-compose..."
cat > /tmp/docker-networks.yml << 'EOF'
# Add this to your docker-compose.yml networks section:

networks:
  edms_network:
    external: true
  edms_backend_network:
    external: true
  edms_frontend_network:
    external: true

# Service network assignments:
# - Database and Redis: edms_backend_network + edms_network
# - Django Backend: edms_network + edms_backend_network  
# - Frontend: edms_network + edms_frontend_network
# - Celery: edms_network + edms_backend_network
EOF

# Add network monitoring to cron
echo "⏰ Adding network monitoring to cron..."
(crontab -l 2>/dev/null | grep -v "network-monitor") > /tmp/crontab-temp
echo "*/15 * * * * /opt/edms/monitoring/scripts/network-monitor.sh # edms-network-monitoring" >> /tmp/crontab-temp
crontab /tmp/crontab-temp
rm /tmp/crontab-temp

echo ""
echo "✅ Docker network setup completed!"
echo ""
echo "🌐 Networks Created:"
echo "   ✅ edms_network (172.20.0.0/16) - Main application network"
echo "   ✅ edms_backend_network (172.21.0.0/16) - Database & cache network"
echo "   ✅ edms_frontend_network (172.22.0.0/16) - Frontend network"
echo ""
echo "🔒 Security Features:"
echo "   ✅ Network isolation between tiers"
echo "   ✅ Blocked direct frontend-to-backend communication"
echo "   ✅ Restricted host network access"
echo "   ✅ Custom subnets for better organization"
echo ""
echo "🛠️  Management Commands:"
echo "   Status:         edms-network-manager status"
echo "   Connectivity:   edms-network-manager connectivity"
echo "   Reset:          edms-network-manager reset"
echo "   Cleanup:        edms-network-manager cleanup"
echo ""
echo "📊 Monitoring:"
echo "   Network logs:   /opt/edms/monitoring/logs/network-monitor.log"
echo "   Monitor script: /opt/edms/monitoring/scripts/network-monitor.sh"
echo ""
echo "📝 Next Steps:"
echo "   1. Update your docker-compose.yml to use these networks"
echo "   2. See /tmp/docker-networks.yml for configuration example"
echo "   3. Test connectivity with: edms-network-manager connectivity"
echo ""