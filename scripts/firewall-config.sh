#!/bin/bash
#
# EDMS Firewall Configuration Script
# 
# Configures UFW firewall for secure EDMS deployment
# with single port access and container network isolation

set -e

echo "🔥 EDMS Firewall Configuration"
echo "=============================="

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]] && ! sudo -n true 2>/dev/null; then
   echo "❌ This script requires sudo privileges"
   exit 1
fi

# Reset UFW to default state
echo "🔄 Resetting UFW to default state..."
sudo ufw --force reset

# Set default policies
echo "⚙️  Setting default policies..."
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port if you use non-standard SSH port)
SSH_PORT=${SSH_PORT:-22}
echo "🔐 Allowing SSH on port $SSH_PORT..."
sudo ufw allow $SSH_PORT/tcp comment 'SSH access'

# Allow HTTP port 8000 for EDMS (internal deployment)
echo "🌐 Allowing EDMS application on port 8000..."
sudo ufw allow 8000/tcp comment 'EDMS application'

# Allow loopback interface for local services
echo "🔄 Allowing loopback interface..."
sudo ufw allow in on lo
sudo ufw allow out on lo

# Docker-specific rules
echo "🐳 Configuring Docker network rules..."

# Allow Docker bridge network
sudo ufw allow in on docker0

# Create custom chain for Docker containers
sudo iptables -N DOCKER-ISOLATION-STAGE-1 2>/dev/null || true
sudo iptables -N DOCKER-ISOLATION-STAGE-2 2>/dev/null || true

# Configure Docker network isolation
cat > /tmp/docker-ufw-rules << 'EOF'
# Docker network isolation rules
*filter
:DOCKER-ISOLATION-STAGE-1 - [0:0]
:DOCKER-ISOLATION-STAGE-2 - [0:0]

# Allow communication within the same Docker network
-A DOCKER-ISOLATION-STAGE-1 -i br-+ ! -o br-+ -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -j RETURN
-A DOCKER-ISOLATION-STAGE-2 -o br-+ -j DROP
-A DOCKER-ISOLATION-STAGE-2 -j RETURN

COMMIT
EOF

# Apply Docker-specific iptables rules
sudo iptables-restore < /tmp/docker-ufw-rules 2>/dev/null || true
rm /tmp/docker-ufw-rules

# Rate limiting for SSH to prevent brute force attacks
echo "⚡ Configuring rate limiting for SSH..."
sudo ufw limit $SSH_PORT/tcp

# Rate limiting for EDMS application
echo "⚡ Configuring rate limiting for EDMS..."
sudo ufw limit 8000/tcp

# Deny access to common attack vectors
echo "🚫 Blocking common attack vectors..."

# Block most common ports used in attacks
BLOCKED_PORTS=(
    21      # FTP
    23      # Telnet
    25      # SMTP
    53      # DNS (if not needed)
    110     # POP3
    143     # IMAP
    993     # IMAPS
    995     # POP3S
    1433    # MSSQL
    1521    # Oracle
    3306    # MySQL
    3389    # RDP
    5432    # PostgreSQL (blocked from external access)
    6379    # Redis (blocked from external access)
    27017   # MongoDB
)

for port in "${BLOCKED_PORTS[@]}"; do
    sudo ufw deny $port comment "Block common attack vector port $port"
done

# Log dropped packets (for monitoring)
echo "📝 Enabling logging for dropped packets..."
sudo ufw logging on

# Create UFW application profile for EDMS
echo "📋 Creating UFW application profile..."
sudo tee /etc/ufw/applications.d/edms > /dev/null <<EOF
[EDMS]
title=Electronic Document Management System
description=21 CFR Part 11 Compliant EDMS Application
ports=8000/tcp

[EDMS Full]
title=EDMS with Database and Cache
description=EDMS with PostgreSQL and Redis access (internal only)
ports=8000/tcp
EOF

sudo ufw app update EDMS

# Configure fail2ban integration
echo "🔒 Configuring fail2ban integration..."
sudo tee /etc/fail2ban/filter.d/edms.conf > /dev/null <<EOF
[Definition]
failregex = ^.*Failed login attempt.*<HOST>.*$
            ^.*Invalid authentication.*<HOST>.*$
            ^.*Suspicious activity.*<HOST>.*$
ignoreregex =
EOF

sudo tee /etc/fail2ban/jail.d/edms.conf > /dev/null <<EOF
[edms]
enabled = true
port = 8000
filter = edms
logpath = /opt/edms/logs/edms.log
maxretry = 3
bantime = 3600
findtime = 600
EOF

# Restart fail2ban to apply new configuration
sudo systemctl restart fail2ban

# Create monitoring script for firewall status
echo "📊 Creating firewall monitoring script..."
sudo tee /usr/local/bin/edms-firewall-status > /dev/null <<'EOF'
#!/bin/bash
echo "=== EDMS Firewall Status ==="
echo "UFW Status:"
sudo ufw status verbose
echo ""
echo "Active connections to EDMS port:"
netstat -tulnp | grep :8000 || echo "No connections on port 8000"
echo ""
echo "Recent UFW logs (last 10 lines):"
sudo tail -n 10 /var/log/ufw.log 2>/dev/null || echo "No UFW logs found"
echo ""
echo "Fail2ban status for EDMS:"
sudo fail2ban-client status edms 2>/dev/null || echo "Fail2ban EDMS jail not active"
EOF

sudo chmod +x /usr/local/bin/edms-firewall-status

# Enable UFW
echo "🔥 Enabling UFW firewall..."
sudo ufw --force enable

# Show final status
echo ""
echo "✅ Firewall configuration completed!"
echo ""
echo "🔍 Current firewall status:"
sudo ufw status verbose
echo ""
echo "📋 Summary:"
echo "   ✅ UFW firewall enabled with secure defaults"
echo "   ✅ SSH access allowed on port $SSH_PORT with rate limiting"
echo "   ✅ EDMS application access allowed on port 8000 with rate limiting"
echo "   ✅ Docker network isolation configured"
echo "   ✅ Common attack vectors blocked"
echo "   ✅ Fail2ban integration configured"
echo "   ✅ UFW application profile created"
echo ""
echo "🛠️  Management commands:"
echo "   Check status: sudo ufw status verbose"
echo "   View logs: sudo tail -f /var/log/ufw.log"
echo "   EDMS status: /usr/local/bin/edms-firewall-status"
echo "   Fail2ban status: sudo fail2ban-client status"
echo ""
echo "⚠️  Important: Make sure you can access SSH before disconnecting!"
echo ""