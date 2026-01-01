#!/bin/bash
#
# Initialize default roles in the database
#

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Initialize Default EDMS Roles${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo "This will create 15 default roles in the system:"
echo "  - O1: Document Management (5 roles)"
echo "  - S1: User Management (2 roles)"
echo "  - S2: Audit Trail (2 roles)"
echo "  - S3: Scheduler (1 role)"
echo "  - S4: Backup & Health (1 role)"
echo "  - S5: Workflow Settings (2 roles)"
echo "  - S6: Placeholder Management (1 role)"
echo "  - S7: App Settings (1 role)"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo -e "${BLUE}Running management command...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_roles

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Roles Initialized!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Verify roles were created:"
echo "  bash scripts/check-user-roles-simple.sh"
echo ""
echo "Now you can assign roles to users via:"
echo "  - Django Admin: http://172.28.1.148/admin/"
echo "  - API: POST /api/v1/users/users/{user_id}/assign_role/"
echo ""
