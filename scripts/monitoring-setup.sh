#!/bin/bash
#
# EDMS Monitoring Setup Script
# 
# Sets up basic monitoring for EDMS system including
# system metrics, log monitoring, and health checks

set -e

echo "📊 EDMS Monitoring Setup"
echo "========================"

# Check if running with appropriate privileges
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

# Install monitoring packages
echo "📦 Installing monitoring packages..."
sudo apt update
sudo apt install -y \
    htop \
    iotop \
    nethogs \
    nload \
    ncdu \
    sysstat \
    logwatch \
    chkrootkit \
    rkhunter \
    lynis

# Create monitoring directories
echo "📁 Creating monitoring directories..."
sudo mkdir -p /opt/edms/monitoring/{scripts,logs,reports,alerts}
sudo chown -R $USER:$USER /opt/edms/monitoring

# System resource monitoring script
echo "🔧 Creating system resource monitoring script..."
cat > /opt/edms/monitoring/scripts/system-monitor.sh << 'EOF'
#!/bin/bash
#
# EDMS System Resource Monitor
# Collects system metrics and logs them for analysis

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/opt/edms/monitoring/logs/system-metrics.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# System metrics
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEMORY_USAGE=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
DISK_USAGE=$(df -h /opt/edms | awk 'NR==2 {print $5}' | cut -d'%' -f1)
LOAD_AVERAGE=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')

# Docker metrics (if Docker is running)
if systemctl is-active --quiet docker; then
    DOCKER_CONTAINERS=$(docker ps -q | wc -l)
    DOCKER_IMAGES=$(docker images -q | wc -l)
else
    DOCKER_CONTAINERS=0
    DOCKER_IMAGES=0
fi

# Network connections to EDMS
EDMS_CONNECTIONS=$(netstat -tn | grep :8000 | grep ESTABLISHED | wc -l)

# Log metrics
echo "$TIMESTAMP,CPU:${CPU_USAGE}%,Memory:${MEMORY_USAGE}%,Disk:${DISK_USAGE}%,Load:${LOAD_AVERAGE},Containers:${DOCKER_CONTAINERS},Connections:${EDMS_CONNECTIONS}" >> "$LOG_FILE"

# Check for critical thresholds
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "$TIMESTAMP - ALERT: High CPU usage: ${CPU_USAGE}%" >> /opt/edms/monitoring/logs/alerts.log
fi

if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
    echo "$TIMESTAMP - ALERT: High memory usage: ${MEMORY_USAGE}%" >> /opt/edms/monitoring/logs/alerts.log
fi

if (( DISK_USAGE > 90 )); then
    echo "$TIMESTAMP - ALERT: High disk usage: ${DISK_USAGE}%" >> /opt/edms/monitoring/logs/alerts.log
fi
EOF

chmod +x /opt/edms/monitoring/scripts/system-monitor.sh

# EDMS application health check script
echo "🏥 Creating EDMS health check script..."
cat > /opt/edms/monitoring/scripts/edms-health-check.sh << 'EOF'
#!/bin/bash
#
# EDMS Application Health Check
# Monitors EDMS application and service health

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/opt/edms/monitoring/logs/health-check.log"
ALERT_FILE="/opt/edms/monitoring/logs/alerts.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log_message() {
    echo "$TIMESTAMP - $1" >> "$LOG_FILE"
}

# Function to log alerts
log_alert() {
    echo "$TIMESTAMP - ALERT: $1" >> "$ALERT_FILE"
    echo "$TIMESTAMP - ALERT: $1" >> "$LOG_FILE"
}

# Check if EDMS application is responding
if curl -s -f http://localhost:8000/health/ > /dev/null 2>&1; then
    log_message "EDMS application is responding"
    EDMS_STATUS="UP"
else
    log_alert "EDMS application is not responding"
    EDMS_STATUS="DOWN"
fi

# Check Docker services
DOCKER_STATUS="UP"
SERVICES=("edms_db" "edms_redis" "edms_backend")

for service in "${SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "^$service$"; then
        log_message "Docker service $service is running"
    else
        log_alert "Docker service $service is not running"
        DOCKER_STATUS="DOWN"
    fi
done

# Check database connectivity
if docker exec edms_db pg_isready -U edms_user -d edms_db > /dev/null 2>&1; then
    log_message "PostgreSQL database is accessible"
    DB_STATUS="UP"
else
    log_alert "PostgreSQL database is not accessible"
    DB_STATUS="DOWN"
fi

# Check Redis connectivity
if docker exec edms_redis redis-cli ping | grep -q "PONG"; then
    log_message "Redis cache is accessible"
    REDIS_STATUS="UP"
else
    log_alert "Redis cache is not accessible"
    REDIS_STATUS="DOWN"
fi

# Check disk space for EDMS storage
STORAGE_USAGE=$(df /opt/edms/storage | awk 'NR==2 {print $5}' | cut -d'%' -f1)
if (( STORAGE_USAGE > 85 )); then
    log_alert "EDMS storage usage high: ${STORAGE_USAGE}%"
fi

# Log summary status
log_message "Health Check Summary: EDMS:$EDMS_STATUS, Docker:$DOCKER_STATUS, DB:$DB_STATUS, Redis:$REDIS_STATUS"

# Return appropriate exit code
if [ "$EDMS_STATUS" = "UP" ] && [ "$DOCKER_STATUS" = "UP" ] && [ "$DB_STATUS" = "UP" ] && [ "$REDIS_STATUS" = "UP" ]; then
    exit 0
else
    exit 1
fi
EOF

chmod +x /opt/edms/monitoring/scripts/edms-health-check.sh

# Log analysis script
echo "📈 Creating log analysis script..."
cat > /opt/edms/monitoring/scripts/log-analyzer.sh << 'EOF'
#!/bin/bash
#
# EDMS Log Analyzer
# Analyzes EDMS logs for security and performance issues

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_FILE="/opt/edms/monitoring/reports/log-analysis-$(date +%Y%m%d).log"

# Ensure report directory exists
mkdir -p "$(dirname "$REPORT_FILE")"

echo "EDMS Log Analysis Report - $TIMESTAMP" > "$REPORT_FILE"
echo "================================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Analyze EDMS application logs
if [ -f "/opt/edms/logs/edms.log" ]; then
    echo "=== EDMS Application Log Analysis ===" >> "$REPORT_FILE"
    
    # Count error levels
    ERROR_COUNT=$(grep -c "ERROR" /opt/edms/logs/edms.log 2>/dev/null || echo "0")
    WARNING_COUNT=$(grep -c "WARNING" /opt/edms/logs/edms.log 2>/dev/null || echo "0")
    
    echo "Error count (last 24h): $ERROR_COUNT" >> "$REPORT_FILE"
    echo "Warning count (last 24h): $WARNING_COUNT" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Recent errors
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "Recent errors:" >> "$REPORT_FILE"
        grep "ERROR" /opt/edms/logs/edms.log | tail -10 >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi
fi

# Analyze system metrics
if [ -f "/opt/edms/monitoring/logs/system-metrics.log" ]; then
    echo "=== System Performance Analysis ===" >> "$REPORT_FILE"
    
    # Calculate averages for the last 24 hours (assuming 5-minute intervals)
    tail -288 /opt/edms/monitoring/logs/system-metrics.log | awk -F',' '
    BEGIN { cpu_sum=0; mem_sum=0; disk_sum=0; count=0 }
    {
        split($2, cpu_arr, ":")
        split($3, mem_arr, ":")
        split($4, disk_arr, ":")
        
        cpu_sum += substr(cpu_arr[2], 1, length(cpu_arr[2])-1)
        mem_sum += substr(mem_arr[2], 1, length(mem_arr[2])-1)
        disk_sum += substr(disk_arr[2], 1, length(disk_arr[2])-1)
        count++
    }
    END {
        if (count > 0) {
            printf "Average CPU usage (24h): %.1f%%\n", cpu_sum/count
            printf "Average Memory usage (24h): %.1f%%\n", mem_sum/count
            printf "Average Disk usage (24h): %.1f%%\n", disk_sum/count
        }
    }' >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

# Analyze security events
if [ -f "/var/log/ufw.log" ]; then
    echo "=== Security Events Analysis ===" >> "$REPORT_FILE"
    
    # Count blocked connections in the last 24 hours
    BLOCKED_TODAY=$(grep "$(date +%b" "%d)" /var/log/ufw.log | grep "BLOCK" | wc -l)
    echo "Blocked connections today: $BLOCKED_TODAY" >> "$REPORT_FILE"
    
    # Top blocked IPs
    if [ "$BLOCKED_TODAY" -gt 0 ]; then
        echo "Top blocked source IPs:" >> "$REPORT_FILE"
        grep "$(date +%b" "%d)" /var/log/ufw.log | grep "BLOCK" | \
        grep -oE "SRC=[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | \
        cut -d'=' -f2 | sort | uniq -c | sort -nr | head -10 >> "$REPORT_FILE"
    fi
    echo "" >> "$REPORT_FILE"
fi

# Check for alerts
if [ -f "/opt/edms/monitoring/logs/alerts.log" ]; then
    ALERTS_TODAY=$(grep "$(date +%Y-%m-%d)" /opt/edms/monitoring/logs/alerts.log | wc -l)
    echo "=== Alerts Summary ===" >> "$REPORT_FILE"
    echo "Alerts today: $ALERTS_TODAY" >> "$REPORT_FILE"
    
    if [ "$ALERTS_TODAY" -gt 0 ]; then
        echo "Recent alerts:" >> "$REPORT_FILE"
        grep "$(date +%Y-%m-%d)" /opt/edms/monitoring/logs/alerts.log | tail -10 >> "$REPORT_FILE"
    fi
    echo "" >> "$REPORT_FILE"
fi

echo "Report generated: $REPORT_FILE"
EOF

chmod +x /opt/edms/monitoring/scripts/log-analyzer.sh

# Create system information script
echo "ℹ️  Creating system information script..."
cat > /opt/edms/monitoring/scripts/system-info.sh << 'EOF'
#!/bin/bash
#
# EDMS System Information
# Displays comprehensive system status

echo "=== EDMS System Information ==="
echo "Current Time: $(date)"
echo "Uptime: $(uptime -p)"
echo ""

echo "=== System Resources ==="
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)"
echo ""

echo "Memory Usage:"
free -h
echo ""

echo "Disk Usage:"
df -h /opt/edms /
echo ""

echo "Load Average:"
uptime | awk -F'load average:' '{print "Load Average:" $2}'
echo ""

echo "=== Docker Status ==="
if systemctl is-active --quiet docker; then
    echo "Docker Service: Running"
    echo "Running Containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "Docker Service: Not Running"
fi
echo ""

echo "=== EDMS Application Status ==="
if curl -s -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "EDMS Application: Responding"
else
    echo "EDMS Application: Not Responding"
fi

echo "Active connections to port 8000:"
netstat -tn | grep :8000 | grep ESTABLISHED | wc -l
echo ""

echo "=== Network Status ==="
echo "UFW Firewall:"
sudo ufw status | head -5
echo ""

echo "=== Recent Log Entries ==="
if [ -f "/opt/edms/monitoring/logs/alerts.log" ]; then
    echo "Recent Alerts (last 5):"
    tail -5 /opt/edms/monitoring/logs/alerts.log 2>/dev/null || echo "No alerts"
else
    echo "No alert log found"
fi
EOF

chmod +x /opt/edms/monitoring/scripts/system-info.sh

# Set up cron jobs for monitoring
echo "⏰ Setting up monitoring cron jobs..."
(crontab -l 2>/dev/null || echo "") | grep -v "edms-monitoring" > /tmp/crontab-backup

# Add monitoring cron jobs
cat >> /tmp/crontab-backup << EOF
# EDMS monitoring cron jobs
*/5 * * * * /opt/edms/monitoring/scripts/system-monitor.sh # edms-monitoring
*/10 * * * * /opt/edms/monitoring/scripts/edms-health-check.sh # edms-monitoring
0 6 * * * /opt/edms/monitoring/scripts/log-analyzer.sh # edms-monitoring
EOF

crontab /tmp/crontab-backup
rm /tmp/crontab-backup

# Configure logrotate for monitoring logs
echo "🔄 Configuring log rotation for monitoring..."
sudo tee /etc/logrotate.d/edms-monitoring > /dev/null <<EOF
/opt/edms/monitoring/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
}

/opt/edms/monitoring/reports/*.log {
    weekly
    missingok
    rotate 12
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
}
EOF

# Create monitoring dashboard script
echo "📊 Creating monitoring dashboard..."
cat > /usr/local/bin/edms-dashboard << 'EOF'
#!/bin/bash
#
# EDMS Monitoring Dashboard
# Interactive monitoring dashboard

while true; do
    clear
    echo "============================================"
    echo "    EDMS Monitoring Dashboard"
    echo "============================================"
    echo ""
    
    # Quick status
    /opt/edms/monitoring/scripts/system-info.sh
    
    echo ""
    echo "============================================"
    echo "Options:"
    echo "1) Refresh (auto-refresh in 30s)"
    echo "2) View detailed logs"
    echo "3) Run health check"
    echo "4) Generate analysis report"
    echo "5) Exit"
    echo "============================================"
    
    read -t 30 -p "Choose option (1-5): " choice
    
    case $choice in
        1|"")
            continue
            ;;
        2)
            echo "Recent alerts:"
            tail -20 /opt/edms/monitoring/logs/alerts.log 2>/dev/null || echo "No alerts"
            read -p "Press Enter to continue..."
            ;;
        3)
            echo "Running health check..."
            /opt/edms/monitoring/scripts/edms-health-check.sh
            echo "Health check completed. Check logs for details."
            read -p "Press Enter to continue..."
            ;;
        4)
            echo "Generating analysis report..."
            /opt/edms/monitoring/scripts/log-analyzer.sh
            echo "Report generated in /opt/edms/monitoring/reports/"
            read -p "Press Enter to continue..."
            ;;
        5)
            echo "Exiting dashboard..."
            exit 0
            ;;
        *)
            echo "Invalid option"
            sleep 1
            ;;
    esac
done
EOF

sudo chmod +x /usr/local/bin/edms-dashboard

echo ""
echo "✅ Monitoring setup completed!"
echo ""
echo "📊 Monitoring Components Installed:"
echo "   ✅ System resource monitoring (every 5 minutes)"
echo "   ✅ EDMS health checks (every 10 minutes)"
echo "   ✅ Daily log analysis reports"
echo "   ✅ Log rotation for monitoring files"
echo "   ✅ Interactive monitoring dashboard"
echo ""
echo "🛠️  Monitoring Commands:"
echo "   Dashboard:      edms-dashboard"
echo "   System info:    /opt/edms/monitoring/scripts/system-info.sh"
echo "   Health check:   /opt/edms/monitoring/scripts/edms-health-check.sh"
echo "   Log analysis:   /opt/edms/monitoring/scripts/log-analyzer.sh"
echo ""
echo "📁 Monitoring Files:"
echo "   Logs:           /opt/edms/monitoring/logs/"
echo "   Reports:        /opt/edms/monitoring/reports/"
echo "   Scripts:        /opt/edms/monitoring/scripts/"
echo ""
echo "⏰ Cron Jobs Added:"
echo "   System metrics: Every 5 minutes"
echo "   Health checks:  Every 10 minutes"
echo "   Log analysis:   Daily at 6 AM"
echo ""