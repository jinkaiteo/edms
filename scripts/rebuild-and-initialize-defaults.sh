#!/bin/bash
#
# Rebuild backend and initialize all defaults
#

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Rebuild Backend & Initialize Defaults${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo "This will:"
echo "  1. Rebuild backend Docker image (includes new management commands)"
echo "  2. Restart backend services"
echo "  3. Initialize all system defaults"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo -e "${BLUE}Step 1: Stopping backend services...${NC}"
docker compose -f docker-compose.prod.yml stop backend celery_worker celery_beat
echo -e "${GREEN}✅ Stopped${NC}"
echo ""

echo -e "${BLUE}Step 2: Rebuilding backend image...${NC}"
docker compose -f docker-compose.prod.yml build backend
echo -e "${GREEN}✅ Backend rebuilt${NC}"
echo ""

echo -e "${BLUE}Step 3: Starting backend services...${NC}"
docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat
echo -e "${GREEN}✅ Services started${NC}"
echo ""

echo -e "${BLUE}Step 4: Waiting for backend to be ready (30 seconds)...${NC}"
sleep 30
echo -e "${GREEN}✅ Ready${NC}"
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Now Initializing Default Data...${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Run initialization
bash scripts/initialize-all-defaults.sh

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
