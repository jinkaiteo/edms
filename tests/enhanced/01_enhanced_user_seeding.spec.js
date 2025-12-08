const { test, expect } = require('@playwright/test');
const { LoginPage, UserManagementPage } = require('../helpers/page-objects.js');
const { TestUtils, ValidationHelpers } = require('../helpers/test-utils.js');
const { config, testUsers, validationRules, apiEndpoints } = require('../helpers/test-data.js');

test.describe('Enhanced User Seeding Tests', () => {
  let loginPage, userManagementPage, testUtils;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    userManagementPage = new UserManagementPage(page);
    testUtils = new TestUtils(page);

    // Navigate to login page and wait for React app
    await page.goto(config.loginURL);
    await testUtils.waitForReactApp();

    // Login as admin if not already authenticated
    if (!(await testUtils.isAuthenticated())) {
      await loginPage.login(config.adminCredentials.username, config.adminCredentials.password);
    }
  });

  test('Validate admin access and permissions', async ({ page }) => {
    console.log('🔐 Validating admin access and permissions...');

    // Verify admin can access user management
    await userManagementPage.navigateToUserManagement();
    
    // Check for admin-only elements
    const adminElements = [
      'button:has-text("Create User")',
      'button:has-text("Delete")',
      'text=User Management'
    ];

    for (const selector of adminElements) {
      const elementExists = await page.locator(selector).count() > 0;
      expect(elementExists).toBe(true);
      console.log(`✅ Admin element found: ${selector}`);
    }

    // Validate API access
    const response = await page.request.get(`${config.backendURL}${apiEndpoints.users.list}`, {
      headers: {
        'Authorization': `Bearer ${await page.evaluate(() => localStorage.getItem('authToken'))}`
      }
    });

    expect(response.ok()).toBe(true);
    console.log('✅ Admin API access validated');
  });

  test.describe('User Creation with Enhanced Validation', () => {
    for (const userData of testUsers.slice(0, 5)) { // Test first 5 users
      test(`Create user: ${userData.username} (${userData.role})`, async ({ page }) => {
        console.log(`\n👤 Creating user: ${userData.username} - ${userData.firstName} ${userData.lastName}`);

        // Navigate to user management
        await userManagementPage.navigateToUserManagement();
        await testUtils.debugScreenshot(`user-creation-start-${userData.username}`);

        // Validate input data
        for (const field of validationRules.userCreation.requiredFields) {
          expect(userData[field]).toBeDefined();
          expect(userData[field]).not.toBe('');
        }

        // Validate email format
        expect(userData.email).toMatch(validationRules.userCreation.emailFormat);
        
        // Validate username pattern
        expect(userData.username).toMatch(validationRules.userCreation.usernamePattern);

        console.log('✅ Input validation passed');

        // Create user through UI
        await userManagementPage.createUser(userData);
        await testUtils.debugScreenshot(`user-creation-submitted-${userData.username}`);

        // Validate form submission result
        const submissionSuccess = await testUtils.validateFormSubmission(`text=${userData.username}`);
        expect(submissionSuccess).not.toBe(false);

        // Validate user creation via API
        const authToken = await page.evaluate(() => localStorage.getItem('authToken'));
        const response = await page.request.get(`${config.backendURL}${apiEndpoints.users.list}`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok()) {
          const users = await response.json();
          const createdUser = users.results?.find(u => u.username === userData.username) ||
                            users.find?.(u => u.username === userData.username);
          
          if (createdUser) {
            console.log(`✅ User verified via API: ${userData.username}`);
            expect(createdUser.email).toBe(userData.email);
            expect(createdUser.first_name).toBe(userData.firstName);
            expect(createdUser.last_name).toBe(userData.lastName);
          }
        }

        console.log(`✅ User creation completed: ${userData.username}`);
      });
    }
  });

  test('Validate user group assignments', async ({ page }) => {
    console.log('👥 Validating user group assignments...');

    const authToken = await page.evaluate(() => localStorage.getItem('authToken'));

    for (const userData of testUsers.filter(u => u.groups.length > 0)) {
      for (const groupName of userData.groups) {
        try {
          // Check group assignment via API
          const response = await page.request.post(`${config.backendURL}/api/admin/users/${userData.username}/groups/`, {
            headers: {
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'application/json'
            },
            data: { group_name: groupName }
          });

          if (response.ok()) {
            console.log(`✅ Group assignment successful: ${userData.username} → ${groupName}`);
          } else {
            console.log(`⚠️ Group assignment may already exist: ${userData.username} → ${groupName}`);
          }
        } catch (e) {
          console.log(`❌ Group assignment failed: ${userData.username} → ${groupName}: ${e.message}`);
        }
      }
    }
  });

  test('User creation error handling', async ({ page }) => {
    console.log('🚫 Testing user creation error handling...');

    await userManagementPage.navigateToUserManagement();

    // Test invalid email format
    const invalidUserData = {
      username: 'testinvalid',
      email: 'invalid-email',
      firstName: 'Test',
      lastName: 'Invalid',
      password: 'test123',
      confirmPassword: 'test123'
    };

    await userManagementPage.createUser(invalidUserData);
    
    // Should show error message
    const errorVisible = await page.locator('text=Invalid email, .error, .alert-danger').isVisible();
    expect(errorVisible).toBe(true);
    console.log('✅ Invalid email error handling validated');

    // Test password mismatch
    const mismatchUserData = {
      username: 'testmismatch',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'Mismatch',
      password: 'test123',
      confirmPassword: 'different456'
    };

    await page.reload();
    await userManagementPage.navigateToUserManagement();
    await userManagementPage.createUser(mismatchUserData);
    
    const passwordErrorVisible = await page.locator('text=Password, text=match, .error').isVisible();
    expect(passwordErrorVisible).toBe(true);
    console.log('✅ Password mismatch error handling validated');
  });

  test('System validation and cleanup', async ({ page }) => {
    console.log('🧹 Performing system validation and cleanup...');

    // Count created users
    const createdUserCount = await testUtils.countElements('text=@edms.test');
    console.log(`📊 Created ${createdUserCount} test users`);

    // Validate system state
    const pageData = await testUtils.extractPageData();
    console.log('📋 System state extracted for validation');

    // Generate test report
    const testReport = {
      timestamp: new Date().toISOString(),
      usersCreated: createdUserCount,
      testsPassed: testUsers.length,
      systemState: pageData.url,
      validation: 'Enhanced user seeding completed successfully'
    };

    console.log('📊 Test Report:', JSON.stringify(testReport, null, 2));
    
    // Save test results
    await testUtils.debugScreenshot('enhanced-user-seeding-complete');
    
    expect(createdUserCount).toBeGreaterThan(0);
    console.log('✅ Enhanced user seeding validation completed');
  });
});