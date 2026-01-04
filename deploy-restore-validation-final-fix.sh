#!/bin/bash
# Deploy final fix for restore validation - handle non-dict fields

echo "=========================================="
echo "FINAL FIX: Restore Validation"
echo "=========================================="
echo ""
echo "Root Cause: Set comprehension was calling .get() on fields"
echo "            BEFORE checking if it's a dict"
echo ""
echo "Error: 'str' object has no attribute 'get'"
echo ""
echo "Fix: Changed to explicit loops with isinstance check FIRST"
echo ""

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "1. Pull final fix..."
git pull origin develop

echo ""
echo "2. Latest commits:"
git log --oneline -3

echo ""
echo "3. Verify fix is present (should see 'for rec in db_data:'):"
grep -A 3 "Extract type codes" backend/apps/backup/api_views.py | head -5

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
sleep 25

echo ""
echo "8. Check backend status:"
docker compose -f docker-compose.prod.yml ps backend

echo ""
echo "9. Check backend health:"
curl -s http://localhost:8001/health/ | python3 -m json.tool

echo ""
echo "10. Check backend logs for any errors:"
docker compose -f docker-compose.prod.yml logs backend --tail=20

ENDSSH

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "✅ Final restore validation fix deployed"
echo ""
echo "What was fixed:"
echo "  - Set comprehension was calling .get('code') on fields"
echo "  - But fields could be a string, not a dict"
echo "  - isinstance check came AFTER the .get() call (too late!)"
echo "  - Changed to explicit loops: check isinstance FIRST, then access"
echo ""
echo "Next steps:"
echo "1. Go to http://172.28.1.148:3001"
echo "2. Navigate to Admin > Backup & Restore"
echo "3. Upload your backup file: edms_migration_package_20260102_162557.tar.gz"
echo "4. Click Restore"
echo ""
echo "Expected result:"
echo "  - Should validate without 'str' object error"
echo "  - May show validation errors about missing types/sources (that's OK)"
echo "  - Should NOT crash with AttributeError"
echo ""
