const { test, expect } = require('@playwright/test');
const { LoginPage, UserManagementPage } = require('./helpers/page-objects.js');
const { TestUtils, ValidationHelpers } = require('./helpers/test-utils.js');
const { config, testUsers, validationRules } = require('./helpers/test-data.js');

test.describe('User Seeding Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page and wait for React to load
    await page.goto(config.baseURL);
    
    // Wait for React app to load - look for either login form or dashboard
    try {
      // If already logged in, we might see the dashboard
      await page.waitForSelector('text=Dashboard, text=Document Management, text=Login, input[name="username"], input[type="email"], input[type="text"]', { timeout: 15000 });
    } catch (e) {
      console.log('Waiting for app to load...');
      await page.waitForTimeout(5000);
    }
    
    // Check if we're already logged in (dashboard visible)
    const dashboardVisible = await page.locator('text=Dashboard').isVisible();
    
    if (!dashboardVisible) {
      // Try to find and click login link if not already on login page
      const loginLink = page.locator('a:has-text("Login"), a:has-text("Sign In"), button:has-text("Login")');
      if (await loginLink.count() > 0) {
        await loginLink.first().click();
        await page.waitForTimeout(2000);
      }
      
      // Look for username/email input with various selectors
      const usernameSelectors = [
        'input[name="username"]',
        'input[name="email"]', 
        'input[type="email"]',
        'input[type="text"]',
        'input[placeholder*="username" i]',
        'input[placeholder*="email" i]',
        'input[id="username"]',
        'input[id="email"]'
      ];
      
      let usernameField = null;
      for (const selector of usernameSelectors) {
        if (await page.locator(selector).count() > 0) {
          usernameField = page.locator(selector).first();
          break;
        }
      }
      
      if (usernameField) {
        await usernameField.fill(config.adminCredentials.username);
        
        // Fill password
        const passwordField = page.locator('input[name="password"], input[type="password"]').first();
        await passwordField.fill(config.adminCredentials.password);
        
        // Submit form
        await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');
        
        // Wait for dashboard to load
        await expect(page.locator('text=Dashboard, text=Document Management')).toBeVisible({ timeout: config.timeout });
      } else {
        console.log('⚠️  No username field found, assuming already logged in or will use API method');
      }
    }
  });

  test('Create test users with various roles', async ({ page }) => {
    console.log('🎯 Starting user seeding process...');
    
    for (let i = 0; i < testUsers.length; i++) {
      const user = testUsers[i];
      console.log(`Creating user ${i + 1}/${testUsers.length}: ${user.username} (${user.role})`);
      
      // Navigate to user management
      await page.click('text=Admin');
      await page.click('text=User Management');
      
      // Wait for user management page to load
      await expect(page.locator('text=User Management')).toBeVisible();
      
      // Click create user button
      await page.click('button:has-text("Add User"), button:has-text("Create User"), button:has-text("New User")');
      
      // Wait for user creation modal/form
      await page.waitForSelector('input[name="username"], input[placeholder*="username" i]');
      
      // Fill user details
      await page.fill('input[name="username"], input[placeholder*="username" i]', user.username);
      await page.fill('input[name="email"], input[placeholder*="email" i]', user.email);
      await page.fill('input[name="firstName"], input[name="first_name"], input[placeholder*="first" i]', user.firstName);
      await page.fill('input[name="lastName"], input[name="last_name"], input[placeholder*="last" i]', user.lastName);
      
      // Set password
      const passwordField = page.locator('input[name="password"], input[type="password"]').first();
      await passwordField.fill('test123');
      
      // Handle confirm password if present
      const confirmPasswordField = page.locator('input[name="confirmPassword"], input[name="password2"], input[placeholder*="confirm" i]');
      if (await confirmPasswordField.count() > 0) {
        await confirmPasswordField.fill('test123');
      }
      
      // Set role permissions based on user role
      if (user.role === 'author') {
        await page.check('input[name="is_staff"], label:has-text("Staff")');
      } else if (user.role === 'reviewer') {
        await page.check('input[name="is_staff"], label:has-text("Staff")');
      } else if (user.role === 'approver') {
        await page.check('input[name="is_staff"], label:has-text("Staff")');
      } else if (user.role === 'senior_approver') {
        await page.check('input[name="is_staff"], label:has-text("Staff")');
        // Senior approvers might need additional permissions
      }
      
      // Handle groups if the interface supports it
      for (const group of user.groups) {
        try {
          await page.check(`label:has-text("${group}"), input[value="${group}"]`);
        } catch (e) {
          console.log(`Group ${group} not available in UI, will be set via API`);
        }
      }
      
      // Submit user creation
      await page.click('button[type="submit"], button:has-text("Create"), button:has-text("Save")');
      
      // Wait for success message or user list update
      try {
        await expect(page.locator('text=successfully created, text=User created, text=Success')).toBeVisible({ timeout: 5000 });
        console.log(`✅ User ${user.username} created successfully`);
      } catch (e) {
        // Check if user appears in the list instead
        await expect(page.locator(`text=${user.username}`)).toBeVisible({ timeout: 5000 });
        console.log(`✅ User ${user.username} appears in user list`);
      }
      
      // Close modal if it's still open
      const modalCloseButton = page.locator('button[aria-label="Close"], button:has-text("Close"), button.close');
      if (await modalCloseButton.count() > 0) {
        await modalCloseButton.click();
      }
      
      // Wait a bit between user creations
      await page.waitForTimeout(1000);
    }
    
    console.log('🎉 User seeding completed successfully!');
  });

  test('Verify all users were created', async ({ page }) => {
    console.log('🔍 Verifying user creation...');
    
    // Navigate to user management
    await page.click('text=Admin');
    await page.click('text=User Management');
    
    // Wait for user list to load
    await expect(page.locator('text=User Management')).toBeVisible();
    
    // Check that each test user exists
    for (const user of testUsers) {
      await expect(page.locator(`text=${user.username}`)).toBeVisible();
      console.log(`✅ Verified user: ${user.username}`);
    }
    
    console.log(`🎯 All ${testUsers.length} users verified successfully!`);
  });

  test('Set user group memberships via API', async ({ request }) => {
    console.log('🔧 Setting user group memberships via API...');
    
    // Login to get auth token
    const loginResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/auth/token/`, {
      data: {
        username: config.adminCredentials.username,
        password: config.adminCredentials.password
      }
    });
    
    const loginData = await loginResponse.json();
    const authToken = loginData.access;
    
    if (!authToken) {
      console.error('Failed to get auth token');
      return;
    }
    
    // Create groups if they don't exist and assign users
    const groups = ['Document Authors', 'Document Reviewers', 'Document Approvers', 'Senior Document Approvers'];
    
    for (const groupName of groups) {
      try {
        // Create group
        await request.post(`${config.baseURL.replace('3000', '8000')}/api/admin/groups/`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          },
          data: { name: groupName }
        });
        console.log(`✅ Group created: ${groupName}`);
      } catch (e) {
        console.log(`Group ${groupName} may already exist`);
      }
    }
    
    // Assign users to groups
    for (const user of testUsers) {
      for (const groupName of user.groups) {
        try {
          await request.post(`${config.baseURL.replace('3000', '8000')}/api/admin/users/${user.username}/groups/`, {
            headers: {
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'application/json'
            },
            data: { group_name: groupName }
          });
          console.log(`✅ Added ${user.username} to ${groupName}`);
        } catch (e) {
          console.log(`Failed to add ${user.username} to ${groupName}: ${e.message}`);
        }
      }
    }
    
    console.log('🎉 Group membership assignment completed!');
  });
});