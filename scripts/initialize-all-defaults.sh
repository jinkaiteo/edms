#!/bin/bash
#
# Initialize ALL default data for EDMS system
# - Roles (7)
# - Django Groups (6)
# - Document Types (6)
# - Document Sources (3)
#

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Initialize All EDMS Default Data${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo "This will create all default data needed for EDMS:"
echo ""
echo "1. Roles (7):"
echo "   - Document Admin, Approver, Reviewer, Author, Viewer"
echo "   - User Admin"
echo "   - Placeholder Admin"
echo ""
echo "2. Django Groups (6):"
echo "   - Document Admins, Reviewers, Approvers"
echo "   - Senior Document Approvers"
echo "   - Document_Reviewers, Document_Approvers"
echo ""
echo "3. Document Types (6):"
echo "   - POL, SOP, WI, MAN, FRM, REC"
echo ""
echo "4. Document Sources (3):"
echo "   - Original Digital Draft"
echo "   - Scanned Original"
echo "   - Scanned Copy"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Starting Initialization...${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# 1. Create Roles
echo -e "${BLUE}1/4: Creating Roles...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_roles
echo ""

# 2. Create Django Groups
echo -e "${BLUE}2/4: Creating Django Groups...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_groups
echo ""

# 3. Create Document Types
echo -e "${BLUE}3/4: Creating Document Types...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_document_types
echo ""

# 4. Create Document Sources
echo -e "${BLUE}4/4: Creating Document Sources...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_document_sources
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}All Default Data Initialized!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Summary:"
echo "  ✓ 7 Roles created/verified"
echo "  ✓ 6 Django Groups created/verified"
echo "  ✓ 6 Document Types created/verified"
echo "  ✓ 3 Document Sources created/verified"
echo ""
echo "Next steps:"
echo "  1. Assign roles to users via Django Admin:"
echo "     http://172.28.1.148/admin/"
echo ""
echo "  2. Assign users to groups:"
echo "     http://172.28.1.148/admin/auth/group/"
echo ""
echo "  3. Users can now create documents with proper types and sources!"
echo ""
