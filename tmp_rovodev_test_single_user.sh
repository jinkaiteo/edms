#!/bin/bash

echo "🧪 Testing Single User Creation - Quick Test"
echo "============================================"
echo ""

# Create a simple single test file
cat > tests/tmp_rovodev_single_user_test.spec.js << 'EOF'
const { test, expect } = require('@playwright/test');

test.describe('Single User Creation Test', () => {
  test('Create one test user through frontend', async ({ page }) => {
    test.setTimeout(60000);
    
    console.log('🚀 Starting single user creation test...');
    
    try {
      // Navigate to login
      await page.goto('/');
      console.log('✅ Navigated to homepage');
      
      // Wait for React app to load
      await page.waitForSelector('h2:has-text("Sign in to EDMS")', { timeout: 15000 });
      await page.waitForSelector('input[name="username"]', { timeout: 10000 });
      console.log('✅ Login form loaded');
      
      // Login as admin
      await page.fill('input[name="username"]', 'admin');
      await page.fill('input[name="password"]', 'test123');
      console.log('✅ Filled login credentials');
      
      await page.click('button[type="submit"]');
      await page.waitForURL('**/dashboard', { timeout: 15000 });
      console.log('✅ Successfully logged in');
      
      // Navigate to user management
      await page.click('text=Admin');
      await page.waitForSelector('text=User Management');
      await page.click('text=User Management');
      await page.waitForURL('**/admin', { timeout: 15000 });
      console.log('✅ Navigated to user management');
      
      // Verify page loaded
      await expect(page.locator('h1')).toContainText('User Management');
      console.log('✅ User management page verified');
      
      // Click create user
      await page.click('button:has-text("Create User")');
      await page.waitForSelector('[role="dialog"]', { timeout: 10000 });
      console.log('✅ Create user modal opened');
      
      // Test password unmasking
      const passwordInput = page.locator('input[placeholder*="secure password"]');
      await passwordInput.fill('TestPassword123');
      
      // Verify password is masked
      await expect(passwordInput).toHaveAttribute('type', 'password');
      console.log('✅ Password field is masked by default');
      
      // Find and click eye icon
      const toggleBtn = passwordInput.locator('..').locator('button').first();
      await toggleBtn.click();
      
      // Verify unmasked
      await expect(passwordInput).toHaveAttribute('type', 'text');
      console.log('✅ Password unmasking works');
      
      // Fill user details
      await page.fill('input[placeholder="Enter username..."]', 'test_playwright_user');
      await page.fill('input[placeholder="Enter email address..."]', 'test@playwright.local');
      await page.fill('input[placeholder="Enter first name..."]', 'Test');
      await page.fill('input[placeholder="Enter last name..."]', 'Playwright');
      await page.fill('input[placeholder="Enter department..."]', 'Testing');
      await page.fill('input[placeholder="Enter position..."]', 'Test User');
      
      await page.fill('input[placeholder="Confirm password..."]', 'TestPassword123');
      console.log('✅ Filled all user details');
      
      // Submit form
      await page.click('button:has-text("Create User")');
      console.log('✅ Submitted user creation form');
      
      // Wait for success (either message or modal closing)
      try {
        await page.waitForSelector('text=created successfully', { timeout: 8000 });
        console.log('✅ Success message displayed');
      } catch {
        await page.waitForSelector('[role="dialog"]', { state: 'detached', timeout: 8000 });
        console.log('✅ Modal closed (alternative success)');
      }
      
      // Verify in user list
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      const userRow = page.locator('tr:has-text("test_playwright_user")');
      await expect(userRow).toBeVisible({ timeout: 10000 });
      console.log('✅ User appears in user list');
      
      // Test login
      await page.click('text=Logout');
      await page.waitForURL('**/login');
      
      await page.waitForSelector('input[name="username"]', { timeout: 10000 });
      await page.fill('input[name="username"]', 'test_playwright_user');
      await page.fill('input[name="password"]', 'TestPassword123');
      await page.click('button[type="submit"]');
      
      await page.waitForURL('**/dashboard', { timeout: 10000 });
      console.log('✅ New user can login successfully');
      
      console.log('');
      console.log('🎉 Single user creation test PASSED!');
      console.log('');
      
    } catch (error) {
      console.error('❌ Test failed:', error.message);
      throw error;
    }
  });
});
EOF

echo "Running single user creation test..."
echo ""

npx playwright test tests/tmp_rovodev_single_user_test.spec.js --reporter=line

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Single user test passed! Ready for full test suite."
    echo ""
    echo "To run full test suite:"
    echo "./tmp_rovodev_run_user_tests.sh"
else
    echo ""
    echo "❌ Single user test failed. Fix issues before running full suite."
fi

echo ""