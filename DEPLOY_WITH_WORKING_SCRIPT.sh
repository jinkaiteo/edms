#!/bin/bash
# Deploy using the working deploy-interactive.sh script

echo "════════════════════════════════════════════════════════════════"
echo "  EDMS Deployment - Using Stable Script"
echo "════════════════════════════════════════════════════════════════"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

print_info "Using deploy-interactive.sh (working, stable script)"
echo ""
echo "This script has all optimizations:"
echo "  ✅ Email configuration working (env_file fix)"
echo "  ✅ No redundant collectstatic (10-20s faster)"
echo "  ✅ BuildKit enabled (15-20% faster builds)"
echo "  ✅ Health check timing fixed (no unhealthy errors)"
echo ""

if [ ! -f "deploy-interactive.sh" ]; then
    echo "Error: deploy-interactive.sh not found"
    echo "Run: git pull origin main"
    exit 1
fi

if [ ! -x "deploy-interactive.sh" ]; then
    chmod +x deploy-interactive.sh
    print_success "Made script executable"
fi

echo "Ready to deploy with stable script."
echo ""
read -p "Start deployment now? (y/N): " confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then
    echo ""
    print_info "Starting deployment with deploy-interactive.sh..."
    echo ""
    ./deploy-interactive.sh
else
    echo ""
    print_info "Deployment cancelled. To deploy later, run:"
    echo "  ./deploy-interactive.sh"
fi
