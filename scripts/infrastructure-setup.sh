#!/bin/bash
#
# EDMS Infrastructure Setup Script
# 
# Sets up Ubuntu 20.04.6 LTS server for EDMS deployment
# with security hardening and basic monitoring

set -e

echo "🚀 EDMS Infrastructure Setup"
echo "============================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root for security reasons"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

# Check if running on Ubuntu 20.04
if ! grep -q "Ubuntu 20.04" /etc/os-release; then
    echo "⚠️  This script is designed for Ubuntu 20.04.6 LTS"
    echo "Current system: $(lsb_release -d | cut -f2)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    tree \
    jq \
    fail2ban \
    ufw \
    logrotate \
    rsync \
    cron \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up the stable repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo "✅ Docker installed successfully"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION="2.23.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed successfully"
else
    echo "✅ Docker Compose already installed"
fi

# Configure Docker daemon
echo "⚙️  Configuring Docker daemon..."
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "userland-proxy": false,
  "experimental": false,
  "live-restore": true
}
EOF

# Start and enable Docker
sudo systemctl enable docker
sudo systemctl start docker

# Create EDMS directories
echo "📁 Creating EDMS directories..."
sudo mkdir -p /opt/edms/{logs,storage,backups,certificates}
sudo mkdir -p /opt/edms/storage/{documents,media,temp}
sudo chown -R $USER:$USER /opt/edms

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/edms > /dev/null <<EOF
/opt/edms/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
    postrotate
        /bin/kill -USR1 \$(cat /opt/edms/logs/edms.pid 2> /dev/null) 2> /dev/null || true
    endscript
}
EOF

# Configure system limits
echo "⚙️  Configuring system limits..."
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
# EDMS system limits
$USER soft nofile 65536
$USER hard nofile 65536
$USER soft nproc 32768
$USER hard nproc 32768
EOF

# Configure kernel parameters
echo "⚙️  Configuring kernel parameters..."
sudo tee -a /etc/sysctl.conf > /dev/null <<EOF
# EDMS kernel parameters
vm.max_map_count=262144
fs.file-max=2097152
net.core.somaxconn=32768
net.ipv4.tcp_max_syn_backlog=8192
EOF

sudo sysctl -p

# Install Python 3.11 (if not available)
echo "🐍 Setting up Python 3.11..."
if ! python3.11 --version &> /dev/null; then
    sudo apt install -y software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
fi

# Install Node.js 18
echo "📦 Installing Node.js 18..."
if ! node --version | grep -q "v18"; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# Create systemd service file
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/edms.service > /dev/null <<EOF
[Unit]
Description=EDMS Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/edms
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

echo "✅ Infrastructure setup completed!"
echo ""
echo "📋 Next Steps:"
echo "   1. Run ./scripts/firewall-config.sh to configure firewall"
echo "   2. Run ./scripts/monitoring-setup.sh for monitoring"
echo "   3. Logout and login again to apply Docker group membership"
echo "   4. Run docker --version to verify Docker installation"
echo ""
echo "🔧 Configuration Summary:"
echo "   - Docker and Docker Compose installed"
echo "   - EDMS directories created in /opt/edms"
echo "   - System limits and kernel parameters optimized"
echo "   - Log rotation configured"
echo "   - Systemd service created"
echo ""