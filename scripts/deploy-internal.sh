#!/bin/bash
#
# EDMS Internal Deployment Script
# 
# Simplified deployment script for internal HTTP-only deployment
# with security hardening and operational monitoring

set -e

echo "🚀 EDMS Internal Deployment"
echo "==========================="

# Configuration
EDMS_USER=${EDMS_USER:-edms}
EDMS_HOME=${EDMS_HOME:-/opt/edms}
DOCKER_COMPOSE_VERSION=${DOCKER_COMPOSE_VERSION:-"2.23.0"}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root"
   echo "Please run as the edms user or a user with sudo privileges"
   exit 1
fi

# Verify prerequisite scripts have been run
echo "🔍 Verifying prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please run ./scripts/infrastructure-setup.sh first"
    exit 1
fi

if ! sudo ufw status | grep -q "Status: active"; then
    echo "❌ UFW firewall not configured. Please run ./scripts/firewall-config.sh first"
    exit 1
fi

if [ ! -d "/opt/edms/monitoring" ]; then
    echo "❌ Monitoring not configured. Please run ./scripts/monitoring-setup.sh first"
    exit 1
fi

# Create deployment directories
echo "📁 Setting up deployment structure..."
sudo mkdir -p $EDMS_HOME/{app,logs,storage,backups,certificates,scripts}
sudo mkdir -p $EDMS_HOME/storage/{documents,media,temp}
sudo mkdir -p $EDMS_HOME/backups/{database,documents,system}

# Set proper ownership
sudo chown -R $USER:$USER $EDMS_HOME

# Copy application files
echo "📦 Deploying application files..."
if [ -d "./backend" ] && [ -d "./frontend" ]; then
    cp -r ./* $EDMS_HOME/app/
    echo "✅ Application files copied"
else
    echo "❌ Application files not found. Please run from the EDMS root directory."
    exit 1
fi

# Copy and set up environment configuration
echo "⚙️  Configuring environment..."
if [ ! -f "$EDMS_HOME/app/backend/.env" ]; then
    if [ -f "./backend/.env.example" ]; then
        cp ./backend/.env.example $EDMS_HOME/app/backend/.env
        echo "📋 Environment template created at $EDMS_HOME/app/backend/.env"
        echo "⚠️  Please edit this file with your production settings"
    else
        echo "❌ Environment template not found"
        exit 1
    fi
fi

# Set up Docker networks
echo "🌐 Setting up Docker networks..."
cd $EDMS_HOME/app && ./scripts/docker-network-setup.sh

# Generate SSL certificates for future use (self-signed for internal)
echo "🔐 Generating self-signed certificates..."
CERT_DIR="$EDMS_HOME/certificates"
if [ ! -f "$CERT_DIR/edms.crt" ]; then
    openssl req -x509 -newkey rsa:4096 -keyout "$CERT_DIR/edms.key" \
        -out "$CERT_DIR/edms.crt" -days 365 -nodes \
        -subj "/C=US/ST=Internal/L=Internal/O=EDMS/CN=edms.internal" 2>/dev/null || echo "⚠️  Certificate generation skipped (openssl not available)"
    
    if [ -f "$CERT_DIR/edms.crt" ]; then
        chmod 600 "$CERT_DIR/edms.key"
        chmod 644 "$CERT_DIR/edms.crt"
        echo "✅ Self-signed certificates generated"
    fi
fi

# Build and start services
echo "🐳 Building and starting services..."
cd $EDMS_HOME/app

# Build containers
docker-compose build --no-cache

# Start database and cache first
docker-compose up -d db redis

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Initialize database
echo "🗄️  Initializing database..."
./scripts/initialize-database.sh

# Start all services
docker-compose up -d

# Create test users
echo "👥 Creating test users..."
./scripts/create-test-users.sh

# Set up log rotation for deployment
echo "📝 Configuring log rotation..."
sudo tee /etc/logrotate.d/edms-deployment > /dev/null <<EOF
$EDMS_HOME/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
    postrotate
        /bin/systemctl reload rsyslog > /dev/null 2>&1 || true
        /usr/local/bin/docker-compose -f $EDMS_HOME/app/docker-compose.yml exec backend python manage.py clearsessions > /dev/null 2>&1 || true
    endscript
}
EOF

# Set up automated backup
echo "💾 Setting up automated backup..."
cat > $EDMS_HOME/scripts/backup.sh << 'EOF'
#!/bin/bash
#
# EDMS Automated Backup Script

BACKUP_DIR="/opt/edms/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Database backup
echo "Creating database backup..."
docker-compose -f /opt/edms/app/docker-compose.yml exec -T db pg_dump -U edms_user -d edms_db | gzip > "$BACKUP_DIR/database/edms_db_$DATE.sql.gz"

# Documents backup
echo "Creating documents backup..."
tar -czf "$BACKUP_DIR/documents/edms_documents_$DATE.tar.gz" -C /opt/edms/storage documents/

# System configuration backup
echo "Creating configuration backup..."
tar -czf "$BACKUP_DIR/system/edms_config_$DATE.tar.gz" -C /opt/edms/app backend/.env docker-compose.yml

# Cleanup old backups
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
EOF

chmod +x $EDMS_HOME/scripts/backup.sh

# Add backup to cron
(crontab -l 2>/dev/null || echo "") | grep -v "edms-backup" > /tmp/crontab-backup
echo "0 2 * * * $EDMS_HOME/scripts/backup.sh # edms-backup" >> /tmp/crontab-backup
crontab /tmp/crontab-backup
rm /tmp/crontab-backup

# Create systemd service for auto-start
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/edms.service > /dev/null <<EOF
[Unit]
Description=EDMS Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$EDMS_HOME/app
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable edms

# Set up health monitoring
echo "🏥 Setting up health monitoring..."
cat > $EDMS_HOME/scripts/health-check.sh << 'EOF'
#!/bin/bash
#
# EDMS Health Check Script

EDMS_URL="http://localhost:8000"
ALERT_EMAIL=${ALERT_EMAIL:-"admin@edms-project.com"}
LOG_FILE="/opt/edms/logs/health-check.log"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check if EDMS is responding
if curl -s -f "$EDMS_URL/health/" > /dev/null 2>&1; then
    log_message "EDMS health check passed"
    exit 0
else
    log_message "EDMS health check failed - attempting restart"
    
    # Try to restart services
    cd /opt/edms/app
    docker-compose restart backend
    
    # Wait and check again
    sleep 30
    if curl -s -f "$EDMS_URL/health/" > /dev/null 2>&1; then
        log_message "EDMS health check passed after restart"
        exit 0
    else
        log_message "EDMS health check still failing after restart"
        # Could send alert email here if configured
        exit 1
    fi
fi
EOF

chmod +x $EDMS_HOME/scripts/health-check.sh

# Add health check to cron
(crontab -l 2>/dev/null || echo "") | grep -v "edms-health" > /tmp/crontab-health
echo "*/5 * * * * $EDMS_HOME/scripts/health-check.sh # edms-health" >> /tmp/crontab-health
crontab /tmp/crontab-health
rm /tmp/crontab-health

# Create management shortcuts
echo "🛠️  Creating management shortcuts..."
sudo tee /usr/local/bin/edms-status > /dev/null <<EOF
#!/bin/bash
cd $EDMS_HOME/app && docker-compose ps
EOF

sudo tee /usr/local/bin/edms-logs > /dev/null <<EOF
#!/bin/bash
cd $EDMS_HOME/app && docker-compose logs -f \${1:-backend}
EOF

sudo tee /usr/local/bin/edms-restart > /dev/null <<EOF
#!/bin/bash
cd $EDMS_HOME/app && docker-compose restart
EOF

sudo chmod +x /usr/local/bin/edms-*

# Final verification
echo "✅ Verifying deployment..."
sleep 10

# Check services
if docker-compose -f $EDMS_HOME/app/docker-compose.yml ps | grep -q "Up"; then
    echo "✅ Services are running"
else
    echo "⚠️  Some services may not be running properly"
fi

# Check HTTP response
if curl -s -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "✅ EDMS application is responding"
else
    echo "⚠️  EDMS application is not responding yet (may need more time to start)"
fi

echo ""
echo "🎉 EDMS Internal Deployment Completed!"
echo "======================================"
echo ""
echo "📊 Deployment Summary:"
echo "   ✅ Application deployed to: $EDMS_HOME"
echo "   ✅ Docker services configured and started"
echo "   ✅ Database initialized with sample data"
echo "   ✅ Test users created"
echo "   ✅ Automated backup configured (daily at 2 AM)"
echo "   ✅ Health monitoring configured (every 5 minutes)"
echo "   ✅ Log rotation configured"
echo "   ✅ Systemd service created for auto-start"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Admin Panel: http://localhost:8000/admin"
echo "   API Docs:    http://localhost:8000/api/v1/docs/"
echo ""
echo "🔐 Default Credentials:"
echo "   Admin: admin / EDMSAdmin2024!"
echo "   (Change immediately after first login)"
echo ""
echo "🛠️  Management Commands:"
echo "   Status:      edms-status"
echo "   Logs:        edms-logs [service]"
echo "   Restart:     edms-restart"
echo "   Dashboard:   edms-dashboard"
echo "   Health:      $EDMS_HOME/scripts/health-check.sh"
echo "   Backup:      $EDMS_HOME/scripts/backup.sh"
echo ""
echo "📁 Important Directories:"
echo "   Application: $EDMS_HOME/app"
echo "   Logs:        $EDMS_HOME/logs"
echo "   Storage:     $EDMS_HOME/storage"
echo "   Backups:     $EDMS_HOME/backups"
echo "   Scripts:     $EDMS_HOME/scripts"
echo ""
echo "⚠️  Security Notes:"
echo "   - Change default passwords immediately"
echo "   - Configure proper SSL certificates for production"
echo "   - Review firewall settings"
echo "   - Set up proper backup retention policies"
echo "   - Configure email alerts for health checks"
echo ""
echo "📚 Next Steps:"
echo "   1. Change admin password"
echo "   2. Configure organization-specific settings"
echo "   3. Create user accounts and assign roles"
echo "   4. Import or create initial documents"
echo "   5. Configure email settings"
echo "   6. Test backup and restore procedures"
echo ""