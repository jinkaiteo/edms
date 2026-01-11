#!/bin/bash

################################################################################
# EDMS Quick Deploy Script
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting EDMS Quick Deployment...${NC}"
echo ""

# Check if deploy-interactive.sh exists
if [ ! -f "./deploy-interactive.sh" ]; then
    echo -e "${RED}Error: deploy-interactive.sh not found${NC}"
    echo "Please run this script from the deployment package directory"
    exit 1
fi

# Make executable
chmod +x deploy-interactive.sh

# Run deployment
./deploy-interactive.sh

echo ""
echo -e "${GREEN}Quick deployment completed!${NC}"
