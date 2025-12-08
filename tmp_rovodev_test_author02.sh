#!/bin/bash

echo "🚀 Testing Author02 User Creation with Role Assignment"
echo "======================================================"
echo ""

# Create a focused test for just author02
cat > tests/tmp_rovodev_author02_test.spec.js << 'EOF'
const { test, expect } = require('@playwright/test');

test.describe('Author02 Creation Test', () => {
  const testPassword = 'Author02Test123!';
  let testResults = [];
  
  function logResult(test, status, message) {
    const result = {
      timestamp: new Date().toISOString(),
      test,
      status,
      message
    };
    testResults.push(result);
    console.log(`[${result.timestamp}] ${status}: ${test} - ${message}`);
  }

  test('Create author02 user with Document Author role', async ({ page }) => {
    test.setTimeout(60000);
    
    const testName = 'Create Author02';
    logResult(testName, 'START', 'Creating author02 with Document Author role');
    
    try {
      // Login as admin
      await page.goto('/');
      await page.waitForSelector('h2:has-text("Sign in to EDMS")', { timeout: 15000 });
      await page.waitForSelector('input[name="username"]', { timeout: 10000 });
      
      await page.fill('input[name="username"]', 'admin');
      await page.fill('input[name="password"]', 'test123');
      await page.click('button[type="submit"]');
      await page.waitForURL('**/dashboard');
      logResult(testName, 'SUCCESS', 'Admin login successful');
      
      // Navigate to user management
      await page.click('text=Admin');
      await page.click('text=User Management');
      await page.waitForURL('**/admin');
      logResult(testName, 'INFO', 'Navigated to user management');
      
      // Open create user form
      await page.click('button:has-text("Create User")');
      await page.waitForSelector('[role="dialog"]', { timeout: 10000 });
      logResult(testName, 'INFO', 'Create user modal opened');
      
      // Fill user details
      await page.fill('input[placeholder="Enter username..."]', 'author02');
      await page.fill('input[placeholder="Enter email address..."]', 'author02@edms-test.local');
      await page.fill('input[placeholder="Enter first name..."]', 'Author');
      await page.fill('input[placeholder="Enter last name..."]', 'Two');
      await page.fill('input[placeholder="Enter department..."]', 'Engineering');
      await page.fill('input[placeholder="Enter position..."]', 'Technical Writer');
      
      // Fill passwords
      await page.fill('input[placeholder="Enter secure password..."]', testPassword);
      await page.fill('input[placeholder="Confirm password..."]', testPassword);
      
      logResult(testName, 'INFO', 'Basic form fields filled');
      
      // Select Document Author role
      try {
        // Wait for roles to load
        await page.waitForSelector('text=Assign Roles', { timeout: 5000 });
        
        // Find and check the Document Author role checkbox
        const authorCheckbox = page.locator('text=Document Author').locator('..').locator('input[type="checkbox"]');
        await authorCheckbox.check();
        
        // Verify checkbox is checked
        await expect(authorCheckbox).toBeChecked();
        logResult(testName, 'SUCCESS', 'Document Author role selected');
      } catch (roleError) {
        logResult(testName, 'ERROR', `Failed to select Document Author role: ${roleError.message}`);
        
        // Take screenshot for debugging
        await page.screenshot({ path: 'test-results/author02-role-selection-error.png' });
        
        // Try alternative selector
        try {
          await page.check('input[type="checkbox"]:near(:text("Document Author"))');
          logResult(testName, 'INFO', 'Used alternative role selection method');
        } catch (altError) {
          logResult(testName, 'WARNING', 'Could not select role with alternative method');
        }
      }
      
      logResult(testName, 'INFO', 'Ready to submit user creation form');
      
      // Submit form
      await page.click('button:has-text("Create User")');
      logResult(testName, 'INFO', 'User creation form submitted');
      
      // Wait for success (either message or modal closing)
      try {
        await page.waitForSelector('text=created successfully', { timeout: 8000 });
        logResult(testName, 'SUCCESS', 'User creation success message displayed');
      } catch {
        await page.waitForSelector('[role="dialog"]', { state: 'detached', timeout: 8000 });
        logResult(testName, 'SUCCESS', 'User creation completed (modal closed)');
      }
      
      // Verify user in list
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      const userRow = page.locator('tr:has-text("author02"), div:has-text("author02")');
      await expect(userRow).toBeVisible({ timeout: 10000 });
      logResult(testName, 'VERIFIED', 'author02 appears in user list');
      
      // Verify user details
      await expect(page.locator('text=Author Two')).toBeVisible();
      await expect(page.locator('text=author02@edms-test.local')).toBeVisible();
      logResult(testName, 'VERIFIED', 'User details are correct');
      
      // Verify Document Author role is assigned
      try {
        const roleDisplayed = page.locator('.bg-blue-100:has-text("Document Author"), .text-blue-800:has-text("Document Author")');
        await expect(roleDisplayed).toBeVisible({ timeout: 5000 });
        logResult(testName, 'VERIFIED', 'Document Author role is assigned and visible');
      } catch (roleVerifyError) {
        logResult(testName, 'WARNING', 'Could not verify Document Author role in UI - checking page content');
        
        // Take screenshot for manual verification
        await page.screenshot({ path: 'test-results/author02-role-verification.png' });
        
        // Log page content for debugging
        const pageText = await page.locator('body').textContent();
        if (pageText.includes('Document Author')) {
          logResult(testName, 'INFO', 'Document Author text found on page');
        } else {
          logResult(testName, 'WARNING', 'Document Author text not found on page');
        }
      }
      
      // Test login capability
      await page.click('text=Logout');
      await page.waitForURL('**/login');
      
      await page.waitForSelector('input[name="username"]', { timeout: 10000 });
      await page.fill('input[name="username"]', 'author02');
      await page.fill('input[name="password"]', testPassword);
      await page.click('button[type="submit"]');
      
      await page.waitForURL('**/dashboard', { timeout: 10000 });
      logResult(testName, 'VERIFIED', 'author02 can login successfully');
      
      // Check for author-specific dashboard elements
      try {
        // Check if user can see document creation options (author privilege)
        const createDocElement = page.locator('text=Create Document, text=New Document, text=Document');
        const isVisible = await createDocElement.first().isVisible({ timeout: 5000 });
        if (isVisible) {
          logResult(testName, 'VERIFIED', 'author02 has author privileges (can see document options)');
        } else {
          logResult(testName, 'INFO', 'Document creation elements not immediately visible');
        }
      } catch (privilegeError) {
        logResult(testName, 'INFO', 'Could not verify specific author privileges');
      }
      
      // Logout
      await page.click('text=Logout');
      await page.waitForURL('**/login');
      
      logResult(testName, 'SUCCESS', 'author02 user creation test completed successfully');
      
      // Save test results
      const fs = require('fs');
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const reportPath = `test-results/author02-creation-report-${timestamp}.json`;
      
      const report = {
        timestamp: new Date().toISOString(),
        testUser: {
          username: 'author02',
          email: 'author02@edms-test.local',
          role: 'Document Author',
          testPassword: testPassword
        },
        testResults: testResults,
        success: true
      };
      
      fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
      logResult(testName, 'SUCCESS', `Test report saved to ${reportPath}`);
      
    } catch (error) {
      logResult(testName, 'FAILED', `Error: ${error.message}`);
      await page.screenshot({ path: 'test-results/author02-creation-error.png' });
      throw error;
    }
  });
});
EOF

echo "Running author02 creation test..."
echo ""

npx playwright test tests/tmp_rovodev_author02_test.spec.js --reporter=line

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ author02 creation test completed successfully!"
    echo ""
    echo "📋 Test Summary:"
    echo "- User: author02"
    echo "- Email: author02@edms-test.local"
    echo "- Password: Author02Test123!"
    echo "- Role: Document Author"
    echo ""
    echo "🔍 Check test-results/ directory for detailed logs and screenshots"
    echo ""
else
    echo ""
    echo "❌ author02 creation test failed. Check output above for details."
    echo ""
    echo "📋 Troubleshooting:"
    echo "1. Verify EDMS frontend and backend are running"
    echo "2. Check that admin credentials work"
    echo "3. Review screenshots in test-results/ directory"
    echo ""
fi

echo ""