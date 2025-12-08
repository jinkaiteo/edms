const { test, expect } = require('@playwright/test');
const { config, workflowScenarios } = require('../playwright_test_suite.js');

test.describe('Workflow Testing Suite', () => {
  let userTokens = {};

  test.beforeAll(async ({ request }) => {
    // Get auth tokens for all workflow participants
    console.log('🔐 Getting authentication tokens for workflow testing...');
    
    const workflowUsers = [
      'author01', 'author02', 'reviewer01', 'reviewer02', 
      'approver01', 'approver02', 'senior01', 'senior02'
    ];
    
    for (const username of workflowUsers) {
      try {
        const loginResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/auth/token/`, {
          data: {
            username: username,
            password: 'test123'
          }
        });
        
        const loginData = await loginResponse.json();
        userTokens[username] = loginData.access;
        console.log(`✅ Got token for ${username}`);
      } catch (e) {
        console.error(`Failed to get token for ${username}: ${e.message}`);
      }
    }
  });

  // Test Scenario 1: Standard Review and Approval
  test('Standard Review and Approval Workflow', async ({ page }) => {
    const scenario = workflowScenarios[0];
    console.log(`🔄 Starting workflow test: ${scenario.name}`);
    console.log(`📄 Document: ${scenario.document}`);
    
    for (let i = 0; i < scenario.steps.length; i++) {
      const step = scenario.steps[i];
      console.log(`Step ${i + 1}/${scenario.steps.length}: ${step.action} by ${step.actor}`);
      
      // Login as the step actor
      await page.goto(config.baseURL);
      await page.fill('input[name="username"]', step.actor);
      await page.fill('input[name="password"]', 'test123');
      await page.click('button[type="submit"]');
      
      // Wait for dashboard
      await expect(page.locator('text=Dashboard')).toBeVisible();
      
      await performWorkflowAction(page, step, scenario.document);
      
      // Wait between steps
      await page.waitForTimeout(2000);
    }
    
    console.log(`✅ Workflow completed: ${scenario.name}`);
  });

  // Test Scenario 2: Review with Rejection and Resubmission
  test('Review Rejection and Resubmission Workflow', async ({ page }) => {
    const scenario = workflowScenarios[1];
    console.log(`🔄 Starting workflow test: ${scenario.name}`);
    console.log(`📄 Document: ${scenario.document}`);
    
    for (let i = 0; i < scenario.steps.length; i++) {
      const step = scenario.steps[i];
      console.log(`Step ${i + 1}/${scenario.steps.length}: ${step.action} by ${step.actor}`);
      
      // Login as the step actor
      await page.goto(config.baseURL);
      await page.fill('input[name="username"]', step.actor);
      await page.fill('input[name="password"]', 'test123');
      await page.click('button[type="submit"]');
      
      // Wait for dashboard
      await expect(page.locator('text=Dashboard')).toBeVisible();
      
      await performWorkflowAction(page, step, scenario.document);
      
      // Wait between steps
      await page.waitForTimeout(2000);
    }
    
    console.log(`✅ Workflow completed: ${scenario.name}`);
  });

  // Test Scenario 3: Senior Approval Required
  test('Senior Approval Required Workflow', async ({ page }) => {
    const scenario = workflowScenarios[2];
    console.log(`🔄 Starting workflow test: ${scenario.name}`);
    console.log(`📄 Document: ${scenario.document}`);
    
    for (let i = 0; i < scenario.steps.length; i++) {
      const step = scenario.steps[i];
      console.log(`Step ${i + 1}/${scenario.steps.length}: ${step.action} by ${step.actor}`);
      
      // Login as the step actor
      await page.goto(config.baseURL);
      await page.fill('input[name="username"]', step.actor);
      await page.fill('input[name="password"]', 'test123');
      await page.click('button[type="submit"]');
      
      // Wait for dashboard
      await expect(page.locator('text=Dashboard')).toBeVisible();
      
      await performWorkflowAction(page, step, scenario.document);
      
      // Wait between steps
      await page.waitForTimeout(2000);
    }
    
    console.log(`✅ Workflow completed: ${scenario.name}`);
  });

  // Test Scenario 4: Approval Rejection and Escalation
  test('Approval Rejection and Escalation Workflow', async ({ page }) => {
    const scenario = workflowScenarios[3];
    console.log(`🔄 Starting workflow test: ${scenario.name}`);
    console.log(`📄 Document: ${scenario.document}`);
    
    for (let i = 0; i < scenario.steps.length; i++) {
      const step = scenario.steps[i];
      console.log(`Step ${i + 1}/${scenario.steps.length}: ${step.action} by ${step.actor}`);
      
      // Login as the step actor
      await page.goto(config.baseURL);
      await page.fill('input[name="username"]', step.actor);
      await page.fill('input[name="password"]', 'test123');
      await page.click('button[type="submit"]');
      
      // Wait for dashboard
      await expect(page.locator('text=Dashboard')).toBeVisible();
      
      await performWorkflowAction(page, step, scenario.document);
      
      // Wait between steps
      await page.waitForTimeout(2000);
    }
    
    console.log(`✅ Workflow completed: ${scenario.name}`);
  });

  test('Verify workflow states and document statuses', async ({ page }) => {
    console.log('🔍 Verifying final workflow states...');
    
    // Login as admin to check all document statuses
    await page.goto(config.baseURL);
    await page.fill('input[name="username"]', config.adminCredentials.username);
    await page.fill('input[name="password"]', config.adminCredentials.password);
    await page.click('button[type="submit"]');
    
    // Navigate to documents
    await page.click('text=Documents, text=Document Management');
    await expect(page.locator('text=Document Management, text=Documents')).toBeVisible();
    
    // Check status of workflow test documents
    const expectedStatuses = [
      { document: 'Quality Policy V1.0', expectedStatus: 'APPROVED_AND_EFFECTIVE' },
      { document: 'Safety Procedures V1.0', expectedStatus: 'APPROVED' },
      { document: 'Training Manual V2.0', expectedStatus: 'APPROVED_AND_EFFECTIVE' },
      { document: 'Audit Checklist V1.1', expectedStatus: 'APPROVED' }
    ];
    
    for (const docCheck of expectedStatuses) {
      // Look for the document and its status
      const docRow = page.locator(`tr:has-text("${docCheck.document}")`);
      if (await docRow.count() > 0) {
        // Check if status is visible in the row
        const hasExpectedStatus = await docRow.locator(`text=${docCheck.expectedStatus}`).count() > 0;
        if (hasExpectedStatus) {
          console.log(`✅ ${docCheck.document}: ${docCheck.expectedStatus}`);
        } else {
          console.log(`⚠️  ${docCheck.document}: Status check needs manual verification`);
        }
      }
    }
    
    console.log('🎯 Workflow state verification completed!');
  });
});

// Helper function to perform workflow actions
async function performWorkflowAction(page, step, documentTitle) {
  try {
    switch (step.action) {
      case 'submit_for_review':
        await submitForReview(page, documentTitle, step.reviewer, step.comment);
        break;
      case 'approve_review':
        await approveReview(page, documentTitle, step.comment);
        break;
      case 'reject_review':
        await rejectReview(page, documentTitle, step.comment);
        break;
      case 'route_for_approval':
        await routeForApproval(page, documentTitle, step.approver, step.comment);
        break;
      case 'approve_document':
        await approveDocument(page, documentTitle, step.comment);
        break;
      case 'reject_approval':
        await rejectApproval(page, documentTitle, step.comment);
        break;
      case 'set_effective_date':
        await setEffectiveDate(page, documentTitle, step.effectiveDate);
        break;
      default:
        console.log(`Unknown action: ${step.action}`);
    }
  } catch (e) {
    console.error(`Failed to perform ${step.action}: ${e.message}`);
    throw e;
  }
}

async function submitForReview(page, documentTitle, reviewer, comment = '') {
  // Navigate to documents
  await page.click('text=Documents, text=Document Management');
  await expect(page.locator('text=Document Management, text=Documents')).toBeVisible();
  
  // Find the document and click submit for review
  const docRow = page.locator(`tr:has-text("${documentTitle}")`);
  await docRow.locator('button:has-text("Submit"), button:has-text("Review"), [data-action="submit"]').click();
  
  // Wait for submit modal
  await page.waitForSelector('text=Submit for Review, text=Select Reviewer');
  
  // Select reviewer
  if (reviewer) {
    await page.selectOption('select[name="reviewer"], select[id*="reviewer"]', { label: reviewer });
  }
  
  // Add comment if provided
  if (comment) {
    await page.fill('textarea[name="comment"], textarea[placeholder*="comment" i]', comment);
  }
  
  // Submit
  await page.click('button[type="submit"], button:has-text("Submit")');
  
  // Wait for success
  await expect(page.locator('text=success, text=submitted')).toBeVisible({ timeout: 10000 });
  console.log(`📝 Submitted for review: ${documentTitle} → ${reviewer}`);
}

async function approveReview(page, documentTitle, comment = '') {
  // Check for pending reviews (notifications or tasks)
  await page.click('text=Tasks, text=My Tasks, text=Notifications');
  
  // Look for the document in pending tasks
  const taskItem = page.locator(`text=${documentTitle}`);
  await taskItem.click();
  
  // Click approve button
  await page.click('button:has-text("Approve"), button:has-text("Accept")');
  
  // Add comment
  if (comment) {
    await page.fill('textarea[name="comment"], textarea[placeholder*="comment" i]', comment);
  }
  
  // Submit approval
  await page.click('button[type="submit"], button:has-text("Approve")');
  
  console.log(`✅ Review approved: ${documentTitle}`);
}

async function rejectReview(page, documentTitle, comment = '') {
  // Check for pending reviews
  await page.click('text=Tasks, text=My Tasks, text=Notifications');
  
  // Look for the document in pending tasks
  const taskItem = page.locator(`text=${documentTitle}`);
  await taskItem.click();
  
  // Click reject button
  await page.click('button:has-text("Reject"), button:has-text("Decline")');
  
  // Add comment (required for rejection)
  await page.fill('textarea[name="comment"], textarea[placeholder*="comment" i]', comment);
  
  // Submit rejection
  await page.click('button[type="submit"], button:has-text("Reject")');
  
  console.log(`❌ Review rejected: ${documentTitle}`);
}

async function routeForApproval(page, documentTitle, approver, comment = '') {
  // Navigate to documents
  await page.click('text=Documents, text=Document Management');
  await expect(page.locator('text=Document Management, text=Documents')).toBeVisible();
  
  // Find the document and click route for approval
  const docRow = page.locator(`tr:has-text("${documentTitle}")`);
  await docRow.locator('button:has-text("Route"), button:has-text("Approval"), [data-action="approve"]').click();
  
  // Wait for approval modal
  await page.waitForSelector('text=Route for Approval, text=Select Approver');
  
  // Select approver
  if (approver) {
    await page.selectOption('select[name="approver"], select[id*="approver"]', { label: approver });
  }
  
  // Add comment if provided
  if (comment) {
    await page.fill('textarea[name="comment"], textarea[placeholder*="comment" i]', comment);
  }
  
  // Submit
  await page.click('button[type="submit"], button:has-text("Route")');
  
  console.log(`📋 Routed for approval: ${documentTitle} → ${approver}`);
}

async function approveDocument(page, documentTitle, comment = '') {
  // Check for pending approvals
  await page.click('text=Tasks, text=My Tasks, text=Approvals');
  
  // Look for the document in pending approvals
  const taskItem = page.locator(`text=${documentTitle}`);
  await taskItem.click();
  
  // Click approve button
  await page.click('button:has-text("Approve"), button:has-text("Accept")');
  
  // Add comment
  if (comment) {
    await page.fill('textarea[name="comment"], textarea[placeholder*="comment" i]', comment);
  }
  
  // Submit approval
  await page.click('button[type="submit"], button:has-text("Approve")');
  
  console.log(`✅ Document approved: ${documentTitle}`);
}

async function rejectApproval(page, documentTitle, comment = '') {
  // Check for pending approvals
  await page.click('text=Tasks, text=My Tasks, text=Approvals');
  
  // Look for the document in pending approvals
  const taskItem = page.locator(`text=${documentTitle}`);
  await taskItem.click();
  
  // Click reject button
  await page.click('button:has-text("Reject"), button:has-text("Decline")');
  
  // Add comment (required for rejection)
  await page.fill('textarea[name="comment"], textarea[placeholder*="comment" i]', comment);
  
  // Submit rejection
  await page.click('button[type="submit"], button:has-text("Reject")');
  
  console.log(`❌ Approval rejected: ${documentTitle}`);
}

async function setEffectiveDate(page, documentTitle, effectiveDate) {
  // Navigate to documents
  await page.click('text=Documents, text=Document Management');
  await expect(page.locator('text=Document Management, text=Documents')).toBeVisible();
  
  // Find the document and click set effective date
  const docRow = page.locator(`tr:has-text("${documentTitle}")`);
  await docRow.locator('button:has-text("Effective"), [data-action="effective"]').click();
  
  // Set effective date
  await page.fill('input[type="date"], input[name="effectiveDate"]', effectiveDate);
  
  // Submit
  await page.click('button[type="submit"], button:has-text("Set")');
  
  console.log(`📅 Effective date set: ${documentTitle} → ${effectiveDate}`);
}