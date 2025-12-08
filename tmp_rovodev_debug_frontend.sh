#!/bin/bash

echo "🔍 Debugging Frontend State"
echo "=========================="
echo ""

# Create a debug test to see what's actually on the page
cat > tests/tmp_rovodev_debug_test.spec.js << 'EOF'
const { test, expect } = require('@playwright/test');

test.describe('Frontend Debug Test', () => {
  test('Debug what is actually on the page', async ({ page }) => {
    test.setTimeout(60000);
    
    console.log('🔍 Debugging frontend state...');
    
    try {
      // Navigate to homepage
      await page.goto('/');
      console.log('✅ Navigated to homepage');
      
      // Wait a moment for any loading
      await page.waitForTimeout(3000);
      
      // Get page title
      const title = await page.title();
      console.log('📄 Page title:', title);
      
      // Get page URL
      const url = page.url();
      console.log('🌐 Current URL:', url);
      
      // Check if we're redirected to dashboard (user already logged in)
      if (url.includes('/dashboard')) {
        console.log('ℹ️  Already logged in - on dashboard page');
        
        // Try to logout first
        try {
          await page.click('text=Logout', { timeout: 5000 });
          await page.waitForURL('**/login', { timeout: 10000 });
          console.log('✅ Successfully logged out');
        } catch (e) {
          console.log('⚠️  Could not find logout button or already on login');
        }
      }
      
      // Wait for page content to load
      await page.waitForLoadState('networkidle');
      
      // Check what headings are present
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').allTextContents();
      console.log('📋 Page headings:', headings);
      
      // Check for login form elements
      const usernameInput = await page.locator('input[name="username"]').count();
      const passwordInput = await page.locator('input[name="password"], input[type="password"]').count();
      console.log('🔐 Username inputs found:', usernameInput);
      console.log('🔐 Password inputs found:', passwordInput);
      
      // Check for login-related text
      const loginText = await page.locator('text=Sign in').count();
      const edmsText = await page.locator('text=EDMS').count();
      console.log('📝 "Sign in" text found:', loginText);
      console.log('📝 "EDMS" text found:', edmsText);
      
      // Get all text on page for debugging
      const bodyText = await page.locator('body').textContent();
      console.log('📄 First 200 chars of page:', bodyText?.substring(0, 200));
      
      // Take a screenshot for manual review
      await page.screenshot({ path: 'test-results/debug-frontend-state.png' });
      console.log('📸 Screenshot saved to test-results/debug-frontend-state.png');
      
      // Check if there are any error messages
      const errors = await page.locator('.error, .alert-error, [class*="error"]').allTextContents();
      if (errors.length > 0) {
        console.log('❌ Errors found on page:', errors);
      }
      
      // List all visible buttons
      const buttons = await page.locator('button:visible').allTextContents();
      console.log('🔘 Visible buttons:', buttons);
      
      // List all links
      const links = await page.locator('a:visible').allTextContents();
      console.log('🔗 Visible links:', links.slice(0, 10)); // Limit to first 10
      
    } catch (error) {
      console.error('❌ Debug test error:', error.message);
      await page.screenshot({ path: 'test-results/debug-frontend-error.png' });
      console.log('📸 Error screenshot saved');
      throw error;
    }
  });
});
EOF

echo "Running frontend debug test..."
echo ""

npx playwright test tests/tmp_rovodev_debug_test.spec.js --project=chromium --reporter=line

echo ""
echo "✅ Debug test complete. Check the output above and screenshot in test-results/"
echo ""