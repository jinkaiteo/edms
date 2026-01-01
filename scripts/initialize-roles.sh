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

echo "This will create 7 essential EDMS roles:"
echo "  - Document Admin (admin)"
echo "  - Document Approver (approve)"
echo "  - Document Reviewer (review)"
echo "  - Document Author (write)"
echo "  - Document Viewer (read)"
echo "  - User Admin (admin)"
echo "  - Placeholder Admin (admin)"
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
