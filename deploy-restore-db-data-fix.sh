#!/bin/bash
# Deploy critical restore fix to staging - restore db_data loading

echo "=========================================="
echo "CRITICAL FIX: Restore db_data Loading"
echo "=========================================="
echo ""
echo "Issue: Line 797 was missing db_data = json.load(...)"
echo "       This caused 'db_data is not defined' errors"
echo ""

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "1. Pull critical fix..."
git pull origin develop

echo ""
echo "2. Latest commits:"
git log --oneline -3

echo ""
echo "3. Verify fix is present:"
grep -A 2 "with tar.extractfile(db_member) as fobj:" backend/apps/backup/api_views.py | head -3

echo ""
echo "4. Stop backend..."
docker compose -f docker-compose.prod.yml stop backend

echo ""
echo "5. Rebuild backend (REQUIRED - Python code change)..."
docker compose -f docker-compose.prod.yml build backend

echo ""
echo "6. Start backend..."
docker compose -f docker-compose.prod.yml up -d backend

echo ""
echo "7. Wait for backend to be ready..."
sleep 20

echo ""
echo "8. Check backend status:"
docker compose -f docker-compose.prod.yml ps backend

echo ""
echo "9. Check backend health:"
curl -s http://localhost:8001/health/ | python3 -m json.tool

ENDSSH

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "✅ Critical restore fix deployed"
echo ""
echo "What was fixed:"
echo "  - Restored missing db_data = json.load(...) line"
echo "  - This loads the backup data for validation"
echo "  - Without it, validation crashes with 'db_data not defined'"
echo ""
echo "Next steps:"
echo "1. Go to http://172.28.1.148:3001"
echo "2. Try your restore operation again"
echo "3. Should now properly validate backup file"
echo ""
