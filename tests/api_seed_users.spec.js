const { test, expect } = require('@playwright/test');
const { config, testUsers } = require('../playwright_test_suite.js');

test.describe('API-Based User Seeding', () => {
  let authToken;

  test.beforeAll(async ({ request }) => {
    console.log('🔐 Getting admin authentication token...');
    
    // Get admin auth token
    try {
      const loginResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/auth/token/`, {
        data: {
          username: config.adminCredentials.username,
          password: config.adminCredentials.password
        }
      });
      
      if (loginResponse.ok()) {
        const loginData = await loginResponse.json();
        authToken = loginData.access;
        console.log('✅ Successfully obtained admin token');
      } else {
        const error = await loginResponse.text();
        console.log(`❌ Failed to get admin token: ${loginResponse.status()} - ${error}`);
      }
    } catch (e) {
      console.error(`❌ Authentication error: ${e.message}`);
    }
  });

  test('Create test users via API', async ({ request }) => {
    console.log('🎯 Starting API-based user creation...');
    
    if (!authToken) {
      console.log('❌ No auth token available, skipping user creation');
      return;
    }

    const headers = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    };

    // First, create groups
    const groups = ['Document Authors', 'Document Reviewers', 'Document Approvers', 'Senior Document Approvers'];
    
    for (const groupName of groups) {
      try {
        const groupResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/admin/groups/`, {
          headers,
          data: { name: groupName, permissions: [] }
        });
        
        if (groupResponse.ok()) {
          console.log(`✅ Group created: ${groupName}`);
        } else if (groupResponse.status() === 400) {
          console.log(`ℹ️  Group already exists: ${groupName}`);
        } else {
          console.log(`⚠️  Failed to create group ${groupName}: ${groupResponse.status()}`);
        }
      } catch (e) {
        console.log(`⚠️  Group creation error for ${groupName}: ${e.message}`);
      }
    }

    // Create users
    let createdCount = 0;
    let skippedCount = 0;

    for (const user of testUsers) {
      console.log(`Creating user: ${user.username} (${user.role})`);
      
      try {
        const userData = {
          username: user.username,
          email: user.email,
          first_name: user.firstName,
          last_name: user.lastName,
          password: 'test123',
          is_active: true,
          is_staff: user.role !== 'viewer',
          is_superuser: user.role === 'admin'
        };

        const userResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/admin/users/`, {
          headers,
          data: userData
        });

        if (userResponse.ok()) {
          const createdUser = await userResponse.json();
          console.log(`✅ User created: ${user.username} (ID: ${createdUser.id})`);
          createdCount++;

          // Assign to groups
          for (const groupName of user.groups) {
            try {
              await request.post(`${config.baseURL.replace('3000', '8000')}/api/admin/users/${user.username}/groups/`, {
                headers,
                data: { group_name: groupName }
              });
              console.log(`  ✅ Added to group: ${groupName}`);
            } catch (e) {
              console.log(`  ⚠️  Failed to add to group ${groupName}: ${e.message}`);
            }
          }

        } else if (userResponse.status() === 400) {
          const error = await userResponse.text();
          if (error.includes('already exists') || error.includes('username')) {
            console.log(`ℹ️  User already exists: ${user.username}`);
            skippedCount++;
          } else {
            console.log(`❌ Failed to create user ${user.username}: ${error}`);
          }
        } else {
          console.log(`❌ Failed to create user ${user.username}: ${userResponse.status()}`);
        }
        
      } catch (e) {
        console.log(`❌ Error creating user ${user.username}: ${e.message}`);
      }
      
      // Small delay between user creations
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    console.log(`\n🎉 User creation completed!`);
    console.log(`✅ Created: ${createdCount} users`);
    console.log(`ℹ️  Skipped (already exist): ${skippedCount} users`);
  });

  test('Verify users were created via API', async ({ request }) => {
    console.log('🔍 Verifying created users...');
    
    if (!authToken) {
      console.log('❌ No auth token available, skipping verification');
      return;
    }

    const headers = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    };

    try {
      const usersResponse = await request.get(`${config.baseURL.replace('3000', '8000')}/api/admin/users/`, {
        headers
      });

      if (usersResponse.ok()) {
        const users = await usersResponse.json();
        const userList = Array.isArray(users) ? users : users.results || [];
        
        console.log(`Total users in system: ${userList.length}`);
        
        // Check each test user
        let foundCount = 0;
        for (const testUser of testUsers) {
          const found = userList.find(u => u.username === testUser.username);
          if (found) {
            console.log(`✅ Verified: ${testUser.username} (${found.email})`);
            foundCount++;
          } else {
            console.log(`❌ Missing: ${testUser.username}`);
          }
        }
        
        console.log(`\n📊 Verification complete: ${foundCount}/${testUsers.length} test users found`);
        
      } else {
        console.log(`❌ Failed to fetch users: ${usersResponse.status()}`);
      }
    } catch (e) {
      console.log(`❌ Verification error: ${e.message}`);
    }
  });

  test('Test user authentication', async ({ request }) => {
    console.log('🔐 Testing user authentication...');
    
    // Test a few sample users
    const testSampleUsers = ['author01', 'reviewer01', 'approver01'];
    
    for (const username of testSampleUsers) {
      try {
        const loginResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/auth/token/`, {
          data: {
            username: username,
            password: 'test123'
          }
        });
        
        if (loginResponse.ok()) {
          const loginData = await loginResponse.json();
          console.log(`✅ Authentication successful: ${username}`);
          
          // Test profile access
          const profileResponse = await request.get(`${config.baseURL.replace('3000', '8000')}/api/v1/auth/profile/`, {
            headers: {
              'Authorization': `Bearer ${loginData.access}`
            }
          });
          
          if (profileResponse.ok()) {
            const profile = await profileResponse.json();
            console.log(`  Profile: ${profile.first_name} ${profile.last_name} (${profile.email})`);
          }
          
        } else {
          console.log(`❌ Authentication failed: ${username} (${loginResponse.status()})`);
        }
        
      } catch (e) {
        console.log(`❌ Authentication error for ${username}: ${e.message}`);
      }
    }
  });
});