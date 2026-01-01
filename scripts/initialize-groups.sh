#!/bin/bash
#
# Initialize Django Groups (for workflow permissions)
#

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Initialize Django Groups (Workflow Permissions)${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo -e "${YELLOW}IMPORTANT: This is different from Roles!${NC}"
echo ""
echo "The EDMS system uses TWO permission systems:"
echo "  1. Role Model (RBAC) - New system for fine-grained permissions"
echo "  2. Django Groups - Used by workflow code for document operations"
echo ""
echo "This command creates Django Groups that the workflow actually checks:"
echo "  - Document Admins"
echo "  - Document Reviewers"
echo "  - Document Approvers"
echo "  - Senior Document Approvers"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo -e "${BLUE}Creating Django Groups...${NC}"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py create_default_groups

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Django Groups Created!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "To assign users to groups, use Django Admin:"
echo "  http://172.28.1.148/admin/auth/group/"
echo ""
echo "Or via Python shell:"
echo "  docker compose exec backend python manage.py shell"
echo "  >>> from django.contrib.auth.models import Group"
echo "  >>> from apps.users.models import User"
echo "  >>> user = User.objects.get(username='author01')"
echo "  >>> group = Group.objects.get(name='Document Reviewers')"
echo "  >>> user.groups.add(group)"
echo ""
