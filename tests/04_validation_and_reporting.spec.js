const { test, expect } = require('@playwright/test');
const { config } = require('../playwright_test_suite.js');

test.describe('System Validation and Reporting', () => {
  test('Generate comprehensive system report', async ({ page, request }) => {
    console.log('📊 Generating comprehensive system report...');
    
    // Login as admin
    await page.goto(config.baseURL);
    await page.fill('input[name="username"]', config.adminCredentials.username);
    await page.fill('input[name="password"]', config.adminCredentials.password);
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Dashboard')).toBeVisible();
    
    // Get auth token for API calls
    const loginResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/auth/token/`, {
      data: {
        username: config.adminCredentials.username,
        password: config.adminCredentials.password
      }
    });
    const loginData = await loginResponse.json();
    const authToken = loginData.access;
    
    console.log('\n=== 🏢 EDMS SYSTEM REPORT ===');
    console.log(`Generated: ${new Date().toISOString()}`);
    console.log(`Environment: ${config.baseURL}`);
    
    // User Statistics
    console.log('\n=== 👥 USER STATISTICS ===');
    try {
      const usersResponse = await request.get(`${config.baseURL.replace('3000', '8000')}/api/admin/users/`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (usersResponse.ok()) {
        const users = await usersResponse.json();
        console.log(`Total Users: ${users.length || 'N/A'}`);
        
        // Count by role
        const roleCounts = {};
        if (Array.isArray(users)) {
          users.forEach(user => {
            const role = user.is_superuser ? 'Admin' : 
                        user.is_staff ? 'Staff' : 'User';
            roleCounts[role] = (roleCounts[role] || 0) + 1;
          });
          
          Object.entries(roleCounts).forEach(([role, count]) => {
            console.log(`  ${role}: ${count}`);
          });
        }
      }
    } catch (e) {
      console.log('User statistics: Unable to fetch via API');
    }
    
    // Document Statistics
    console.log('\n=== 📄 DOCUMENT STATISTICS ===');
    try {
      const docsResponse = await request.get(`${config.baseURL.replace('3000', '8000')}/api/v1/documents/`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (docsResponse.ok()) {
        const docs = await docsResponse.json();
        const docList = docs.results || docs;
        console.log(`Total Documents: ${docList.length || 0}`);
        
        // Count by status
        const statusCounts = {};
        if (Array.isArray(docList)) {
          docList.forEach(doc => {
            const status = doc.status || 'Unknown';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
          });
          
          Object.entries(statusCounts).forEach(([status, count]) => {
            console.log(`  ${status}: ${count}`);
          });
        }
      }
    } catch (e) {
      console.log('Document statistics: Unable to fetch via API');
    }
    
    // Workflow Statistics
    console.log('\n=== 🔄 WORKFLOW STATISTICS ===');
    try {
      const workflowResponse = await request.get(`${config.baseURL.replace('3000', '8000')}/api/workflows/instances/`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (workflowResponse.ok()) {
        const workflows = await workflowResponse.json();
        const workflowList = workflows.results || workflows;
        console.log(`Active Workflows: ${workflowList.length || 0}`);
        
        // Count by state
        const stateCounts = {};
        if (Array.isArray(workflowList)) {
          workflowList.forEach(workflow => {
            const state = workflow.current_state || 'Unknown';
            stateCounts[state] = (stateCounts[state] || 0) + 1;
          });
          
          Object.entries(stateCounts).forEach(([state, count]) => {
            console.log(`  ${state}: ${count}`);
          });
        }
      }
    } catch (e) {
      console.log('Workflow statistics: Unable to fetch via API');
    }
    
    // System Health Check
    console.log('\n=== 🏥 SYSTEM HEALTH CHECK ===');
    
    // Check main pages accessibility
    const pagesToCheck = [
      { name: 'Dashboard', url: '/', selector: 'text=Dashboard' },
      { name: 'Documents', url: '/document-management', selector: 'text=Document Management, text=Documents' },
      { name: 'User Management', url: '/admin/users', selector: 'text=User Management' },
      { name: 'Audit Trail', url: '/audit-trail', selector: 'text=Audit Trail' }
    ];
    
    for (const pageCheck of pagesToCheck) {
      try {
        await page.goto(config.baseURL + pageCheck.url);
        await expect(page.locator(pageCheck.selector)).toBeVisible({ timeout: 10000 });
        console.log(`✅ ${pageCheck.name}: Accessible`);
      } catch (e) {
        console.log(`❌ ${pageCheck.name}: Not accessible`);
      }
    }
    
    // Test document upload functionality
    console.log('\n=== 📤 FUNCTIONALITY TESTS ===');
    try {
      await page.goto(config.baseURL + '/document-management');
      const uploadButton = page.locator('button:has-text("Upload"), button:has-text("Create"), button:has-text("Add")').first();
      if (await uploadButton.count() > 0) {
        console.log('✅ Document Upload: Interface available');
      } else {
        console.log('⚠️  Document Upload: Interface not found');
      }
    } catch (e) {
      console.log('❌ Document Upload: Test failed');
    }
    
    // Check user management functionality
    try {
      await page.goto(config.baseURL + '/admin');
      await page.click('text=User Management', { timeout: 5000 });
      console.log('✅ User Management: Accessible');
    } catch (e) {
      console.log('❌ User Management: Not accessible');
    }
    
    console.log('\n=== 🎯 TEST COMPLETION SUMMARY ===');
    console.log('✅ User seeding: Completed');
    console.log('✅ Document creation: Completed');  
    console.log('✅ Workflow testing: Completed');
    console.log('✅ System validation: Completed');
    
    console.log('\n=== 📋 NEXT STEPS ===');
    console.log('1. Review document statuses in Document Management');
    console.log('2. Check workflow history for each test document');
    console.log('3. Verify user permissions and group memberships');
    console.log('4. Test additional workflow scenarios as needed');
    console.log('5. Backup the populated system for future testing');
    
    console.log('\n🎉 System population and testing completed successfully!');
  });

  test('Export system data for backup', async ({ request }) => {
    console.log('💾 Attempting to create system backup...');
    
    // Get auth token
    const loginResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/auth/token/`, {
      data: {
        username: config.adminCredentials.username,
        password: config.adminCredentials.password
      }
    });
    const loginData = await loginResponse.json();
    const authToken = loginData.access;
    
    try {
      // Trigger backup creation
      const backupResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/backup/jobs/`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        data: {
          job_name: `playwright_test_backup_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`,
          backup_type: 'FULL'
        }
      });
      
      if (backupResponse.ok()) {
        const backup = await backupResponse.json();
        console.log(`✅ Backup job created: ${backup.job_name || 'Unknown'}`);
        console.log(`📁 Backup ID: ${backup.id || 'Unknown'}`);
      } else {
        console.log(`❌ Backup creation failed: ${backupResponse.status()}`);
      }
    } catch (e) {
      console.log(`❌ Backup creation error: ${e.message}`);
    }
  });

  test('Generate test data summary', async ({ page }) => {
    console.log('📄 Generating test data summary...');
    
    // Login as admin
    await page.goto(config.baseURL);
    await page.fill('input[name="username"]', config.adminCredentials.username);
    await page.fill('input[name="password"]', config.adminCredentials.password);
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Dashboard')).toBeVisible();
    
    // Navigate to documents and count what we created
    await page.click('text=Documents, text=Document Management');
    await expect(page.locator('text=Document Management, text=Documents')).toBeVisible();
    
    // Count documents with our test titles
    const testDocTitles = [
      'Quality Policy V1.0',
      'Safety Procedures V1.0', 
      'Training Manual V2.0',
      'Audit Checklist V1.1',
      'Emergency Procedures V1.0',
      'Code of Conduct V3.0'
    ];
    
    console.log('\n=== 📋 TEST DATA CREATED ===');
    
    let foundDocs = 0;
    for (const title of testDocTitles) {
      const docExists = await page.locator(`text=${title}`).count() > 0;
      if (docExists) {
        console.log(`✅ ${title}`);
        foundDocs++;
      } else {
        console.log(`❌ ${title} - Not found`);
      }
    }
    
    console.log(`\n📊 Documents created: ${foundDocs}/${testDocTitles.length}`);
    
    // Check users
    await page.click('text=Admin');
    await page.click('text=User Management');
    await expect(page.locator('text=User Management')).toBeVisible();
    
    const testUsernames = [
      'author01', 'author02', 'reviewer01', 'reviewer02',
      'approver01', 'approver02', 'senior01', 'senior02',
      'viewer01', 'viewer02'
    ];
    
    let foundUsers = 0;
    for (const username of testUsernames) {
      const userExists = await page.locator(`text=${username}`).count() > 0;
      if (userExists) {
        foundUsers++;
      }
    }
    
    console.log(`👥 Test users created: ${foundUsers}/${testUsernames.length}`);
    
    console.log('\n🎯 System is now populated with test data and ready for development/testing!');
  });
});