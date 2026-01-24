#!/bin/bash
# Quick Start Script for Fresh Staging Server Deployment

set -e

cat << 'BANNER'
════════════════════════════════════════════════════════════════
  EDMS Fresh Staging Server - Quick Start
════════════════════════════════════════════════════════════════

This script will help you deploy EDMS to a fresh staging server
with all optimizations applied.

Prerequisites:
  • Ubuntu 20.04+ / Debian 11+
  • 2GB+ RAM, 20GB+ disk space
  • Sudo privileges
  • Internet connection

BANNER

echo ""
read -p "Ready to begin? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Step 1: Checking Prerequisites"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if running on Linux
if [[ ! "$(uname)" == "Linux" ]]; then
    echo "❌ This script requires Linux (Ubuntu/Debian)"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker installed: $(docker --version)"
else
    echo "⚠ Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    sudo usermod -aG docker $USER
    echo "✓ Docker installed"
    echo ""
    echo "⚠ You need to log out and back in for Docker group to take effect"
    echo "   Then run this script again"
    exit 0
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "✓ Docker Compose installed"
else
    echo "⚠ Docker Compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✓ Docker Compose installed"
fi

# Check Git
if command -v git &> /dev/null; then
    echo "✓ Git installed: $(git --version)"
else
    echo "⚠ Git not found. Installing..."
    sudo apt update && sudo apt install -y git
    echo "✓ Git installed"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Step 2: Clone Repository"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ -d ".git" ]; then
    echo "✓ Already in EDMS repository"
    echo "  Pulling latest changes..."
    git pull origin main
else
    echo "Cloning EDMS repository..."
    read -p "Repository URL (press Enter for default): " REPO_URL
    REPO_URL=${REPO_URL:-https://github.com/jinkaiteo/edms.git}
    
    cd ~
    if [ -d "edms" ]; then
        echo "⚠ Directory ~/edms already exists"
        read -p "Remove and re-clone? (y/N): " remove_confirm
        if [[ "$remove_confirm" =~ ^[Yy]$ ]]; then
            rm -rf edms
            git clone "$REPO_URL" edms
        else
            cd edms
            git pull origin main
        fi
    else
        git clone "$REPO_URL" edms
    fi
    cd ~/edms
    echo "✓ Repository cloned"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Step 3: Verify Latest Optimizations"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Latest commits:"
git log --oneline -5

echo ""
echo "Checking for optimizations:"
if git log --oneline -5 | grep -q "collectstatic"; then
    echo "✓ Collectstatic optimization present"
else
    echo "⚠ Collectstatic optimization not found (may be older commit)"
fi

if git log --oneline -5 | grep -q "env_file"; then
    echo "✓ env_file directive fix present"
else
    echo "⚠ env_file fix not found (may be older commit)"
fi

if [ -f "deploy-interactive-fast.sh" ]; then
    echo "✓ Optimized deployment script available"
else
    echo "⚠ Optimized deployment script not found"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Step 4: Pre-Deployment Check"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Checking available ports..."
if lsof -i :8001 &> /dev/null; then
    echo "⚠ Port 8001 is in use"
    lsof -i :8001
    read -p "Continue anyway? (y/N): " port_confirm
    [[ ! "$port_confirm" =~ ^[Yy]$ ]] && exit 1
else
    echo "✓ Port 8001 available (backend)"
fi

if lsof -i :3001 &> /dev/null; then
    echo "⚠ Port 3001 is in use"
    lsof -i :3001
    read -p "Continue anyway? (y/N): " port_confirm
    [[ ! "$port_confirm" =~ ^[Yy]$ ]] && exit 1
else
    echo "✓ Port 3001 available (frontend)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Step 5: Email Configuration (Optional)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Email configuration tips:"
echo "  • Gmail: Requires 2FA and app password"
echo "    Create at: https://myaccount.google.com/apppasswords"
echo "  • Microsoft 365: Requires app password"
echo "  • You can skip and configure later in .env file"
echo ""

read -p "Have email credentials ready? (y/N): " email_ready
if [[ ! "$email_ready" =~ ^[Yy]$ ]]; then
    echo ""
    echo "⚠ You can configure email later by editing .env file"
    echo "   See backend/.env.example for examples"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Step 6: Start Deployment"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Ready to deploy with optimized script!"
echo ""
echo "The deployment will:"
echo "  1. ✅ Configure email BEFORE deployment (no restart)"
echo "  2. ✅ Build Docker images with static files baked in"
echo "  3. ✅ Start containers (optimized 5-10s startup)"
echo "  4. ✅ Initialize database, roles, users, placeholders"
echo "  5. ✅ Test email configuration"
echo "  6. ✅ Set up automated backups"
echo ""
echo "Estimated time: 10-15 minutes"
echo ""

read -p "Start deployment now? (y/N): " deploy_confirm
if [[ "$deploy_confirm" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting optimized deployment..."
    echo ""
    
    if [ -x "./deploy-interactive-fast.sh" ]; then
        ./deploy-interactive-fast.sh
    elif [ -x "./deploy-interactive.sh" ]; then
        echo "⚠ Using standard script (fast script not found)"
        ./deploy-interactive.sh
    else
        echo "❌ Deployment script not found or not executable"
        echo "   Run: chmod +x deploy-interactive-fast.sh"
        exit 1
    fi
else
    echo ""
    echo "Deployment cancelled. To deploy later, run:"
    echo "  cd ~/edms"
    echo "  ./deploy-interactive-fast.sh"
    echo ""
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Quick Start Complete"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [[ "$deploy_confirm" =~ ^[Yy]$ ]]; then
    echo "Next steps:"
    echo "  1. Verify deployment: ./verify_static_files.sh"
    echo "  2. Access frontend: http://$(hostname -I | awk '{print $1}'):3001"
    echo "  3. Access backend: http://$(hostname -I | awk '{print $1}'):8001/admin"
    echo "  4. Review logs: docker compose logs -f"
    echo ""
    echo "Documentation:"
    echo "  • FRESH_STAGING_DEPLOYMENT_GUIDE.md - Complete guide"
    echo "  • COLLECTSTATIC_OPTIMIZATION.md - Performance details"
    echo "  • EMAIL_CONFIGURATION_ROOT_CAUSE_FIX.md - Email setup"
else
    echo "To start deployment:"
    echo "  cd ~/edms"
    echo "  ./deploy-interactive-fast.sh"
    echo ""
    echo "Or run this script again:"
    echo "  ./FRESH_DEPLOYMENT_QUICK_START.sh"
fi

echo ""
