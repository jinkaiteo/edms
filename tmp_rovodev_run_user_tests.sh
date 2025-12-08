#!/bin/bash

echo "🚀 EDMS User Creation Test Suite"
echo "================================="
echo ""

# Ensure test-results directory exists
mkdir -p test-results

# Check if EDMS is running
echo "📋 Pre-flight checks..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "❌ Frontend not accessible on http://localhost:3000"
    echo "Please start the EDMS frontend first"
    exit 1
fi

if curl -s http://localhost:8000/api/v1/health/ > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend not accessible on http://localhost:8000"
    echo "Please start the EDMS backend first"
    exit 1
fi

echo ""
echo "🧪 Running user creation tests..."
echo ""

# Run the focused test suite
if npx playwright test tests/tmp_rovodev_user_creation_focused.spec.js --reporter=line; then
    echo ""
    echo "✅ User creation tests completed successfully!"
    echo ""
    echo "📊 Test Results:"
    echo "- Check test-results/ directory for detailed logs"
    echo "- Created users can be found in the user management interface"
    echo "- All users use password: PlaywrightTest123!"
    echo ""
    echo "🔧 Created Test Users:"
    echo "- playwright_author (Document Author)"
    echo "- playwright_reviewer (Document Reviewer)"
    echo "- playwright_approver (Document Approver)"
    echo ""
    echo "🧹 Cleanup (optional):"
    echo "Set CLEANUP_TEST_USERS=true to auto-remove test users"
    echo ""
else
    echo ""
    echo "❌ Some tests failed. Check the output above for details."
    echo ""
    echo "📋 Troubleshooting:"
    echo "1. Verify EDMS frontend and backend are running"
    echo "2. Check that admin credentials (admin/test123) work"
    echo "3. Review test-results/ directory for detailed logs"
    echo ""
    exit 1
fi

# Run comprehensive tests if requested
if [ "$1" = "comprehensive" ]; then
    echo ""
    echo "🔍 Running comprehensive test suite..."
    npx playwright test tests/tmp_rovodev_user_creation_comprehensive.spec.js --reporter=line
fi

echo ""
echo "🎉 User creation testing complete!"
echo ""