#!/bin/bash

echo "🚀 Author02 User Creation - Playwright Test Runner"
echo "================================================="
echo ""

# Create test-results directory if it doesn't exist
mkdir -p test-results

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend running on http://localhost:3000"
else
    echo "❌ Frontend not accessible on http://localhost:3000"
    echo "   Please start the EDMS frontend first:"
    echo "   docker compose up frontend"
    exit 1
fi

# Check if backend is running
if curl -s http://localhost:8000/api/v1/health/ > /dev/null; then
    echo "✅ Backend running on http://localhost:8000"
else
    echo "❌ Backend not accessible on http://localhost:8000"
    echo "   Please start the EDMS backend first:"
    echo "   docker compose up backend"
    exit 1
fi

# Test authentication endpoint
echo "🔐 Testing admin authentication..."
AUTH_TEST=$(curl -s -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "test123"}')

if echo "$AUTH_TEST" | grep -q "access"; then
    echo "✅ Admin authentication working"
else
    echo "❌ Admin authentication failed"
    echo "   Response: $AUTH_TEST"
    echo "   Please check admin credentials"
    exit 1
fi

echo ""
echo "🧪 Running Author02 creation test..."
echo ""

# Run the specific Playwright test
npx playwright test tests/author02-user-creation.spec.js --project=chromium --reporter=line --timeout=90000

TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo "🎉 SUCCESS: Author02 user creation test passed!"
    echo ""
    echo "📋 User Details Created:"
    echo "   Username: author02"
    echo "   Email: author02@test.local"
    echo "   Password: Author02Test123!"
    echo "   Role: Document Author"
    echo "   Department: Engineering"
    echo "   Position: Technical Writer"
    echo ""
    echo "🔍 Verification Steps:"
    echo "   1. Login to EDMS as admin"
    echo "   2. Go to Admin → User Management"
    echo "   3. Look for 'author02' in the user list"
    echo ""
    echo "🧪 Test Login:"
    echo "   1. Logout from admin"
    echo "   2. Login as: author02 / Author02Test123!"
    echo "   3. Verify access to Document Management"
    echo "   4. Test document creation capabilities"
    echo ""
    echo "📸 Screenshots saved in test-results/ directory showing each step"
    echo ""
else
    echo "❌ Author02 creation test failed or had issues"
    echo ""
    echo "🔍 Debugging Information:"
    echo "   - Check test-results/ directory for screenshots"
    echo "   - Look for error screenshots and page content"
    echo "   - Review console output above for specific failures"
    echo ""
    echo "🔄 Alternative Methods:"
    echo "   1. Use browser console script (see tmp_rovodev_browser_instructions.md)"
    echo "   2. Manual creation through EDMS interface"
    echo "   3. Direct API creation using curl commands"
    echo ""
    exit 1
fi

echo "✅ Author02 user creation process complete!"
echo ""