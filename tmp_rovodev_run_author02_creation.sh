#!/bin/bash

echo "🚀 Author02 User Creation Script"
echo "================================"
echo ""
echo "This script will create the author02 user with Document Author role"
echo "using the proven authentication bypass and navigation methods."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Frontend not accessible on http://localhost:3000"
    echo "   Please start the EDMS frontend first"
    exit 1
fi

if ! curl -s http://localhost:8000/api/v1/health/ > /dev/null; then
    echo "❌ Backend not accessible on http://localhost:8000" 
    echo "   Please start the EDMS backend first"
    exit 1
fi

echo "✅ Frontend and backend are running"
echo ""

# Test authentication endpoint
echo "🔐 Testing authentication endpoint..."
AUTH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "test123"}')

if echo "$AUTH_RESPONSE" | grep -q "access"; then
    echo "✅ Authentication endpoint working"
else
    echo "❌ Authentication failed. Check admin credentials."
    echo "   Response: $AUTH_RESPONSE"
    exit 1
fi

echo ""
echo "🎯 Running author02 creation script..."
echo ""

# Run the Playwright script
npx playwright test tests/tmp_rovodev_create_author02_script.js --project=chromium --reporter=line

SCRIPT_RESULT=$?

echo ""
if [ $SCRIPT_RESULT -eq 0 ]; then
    echo "🎉 SUCCESS: author02 creation script completed!"
    echo ""
    echo "📋 User Details Created:"
    echo "   Username: author02"
    echo "   Email: author02@test.local"
    echo "   Password: Author02Test123!"
    echo "   Role: Document Author"
    echo ""
    echo "🔍 Verification Steps:"
    echo "   1. Login to EDMS as admin"
    echo "   2. Go to Admin → User Management"
    echo "   3. Look for 'author02' in the user list"
    echo "   4. Test login with author02 credentials"
    echo ""
    echo "🧪 Test Document Creation:"
    echo "   1. Login as author02"
    echo "   2. Go to Document Management"
    echo "   3. Try creating a new document"
    echo "   4. Verify Document Author permissions work"
    echo ""
else
    echo "❌ Script encountered issues. Check the output above for details."
    echo ""
    echo "📸 Screenshots saved in test-results/ directory"
    echo "🔍 Manual creation option:"
    echo "   1. Open browser to http://localhost:3000"
    echo "   2. Open browser console (F12)"
    echo "   3. Run: localStorage.setItem('accessToken', 'TOKEN_HERE')"
    echo "   4. Reload page and navigate to Admin → User Management"
    echo ""
    exit 1
fi

echo ""
echo "✅ Author02 creation process complete!"
echo ""