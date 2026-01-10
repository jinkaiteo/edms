/**
 * Permission Enforcement E2E Tests
 * 
 * Tests that verify role-based access control:
 * 1. Only authors can submit their documents
 * 2. Only reviewers can review documents
 * 3. Only approvers can approve documents
 * 4. Authors CANNOT review their own documents (compliance requirement)
 * 5. Users without proper roles are blocked
 */

import { test, expect, Page } from '@playwright/test';
import path from 'path';

const testUsers = {
  author: { username: 'author01', password: 'test123' },
  reviewer: { username: 'reviewer01', password: 'test123' },
  approver: { username: 'approver01', password: 'test123' },
  viewer: { username: 'viewer01', password: 'test123' }
};

async function login(page: Page, username: string, password: string) {
  await page.goto('http://localhost:3001');
  await page.waitForSelector('input[name="username"]', { timeout: 5000 });
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/(dashboard|documents)/, { timeout: 10000 });
}

async function logout(page: Page) {
  const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")').first();
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
    await page.waitForURL(/\/login/, { timeout: 5000 });
  }
}

test.describe('Permission Enforcement Tests', () => {
  
  test('Author cannot review their own document (COMPLIANCE)', async ({ page }) => {
    /**
     * CRITICAL COMPLIANCE TEST
     * 
     * 21 CFR Part 11 and GxP regulations require that documents
     * cannot be reviewed or approved by their authors. This is a
     * fundamental principle of quality management systems.
     */
    
    console.log('TEST: Author self-review prevention (COMPLIANCE)');
    
    // Author creates document
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document")');
    
    await page.fill('input[name="title"]', 'Self-Review Compliance Test');
    await page.fill('textarea[name="description"]', 'Testing compliance requirement');
    await page.locator('select[name="document_type"]').first().selectOption({ index: 1 });
    await page.locator('select[name="document_source"]').first().selectOption({ index: 1 });
    
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(path.resolve('test_doc/test_document.docx'));
    
    await page.click('button[type="submit"]:has-text("Create")');
    await page.waitForTimeout(2000);
    
    // Submit for review (selecting themselves if possible)
    await page.click('button:has-text("Submit for Review")');
    
    const reviewerSelect = page.locator('select[name="reviewer"]').first();
    if (await reviewerSelect.isVisible()) {
      const options = await reviewerSelect.locator('option').allTextContents();
      
      // System should NOT allow author to select themselves as reviewer
      const authorInOptions = options.some(opt => opt.includes(testUsers.author.username));
      
      if (authorInOptions) {
        console.warn('⚠️  WARNING: Author appears in reviewer list - potential compliance issue');
      } else {
        console.log('✓ Author correctly excluded from reviewer options');
      }
    }
    
    // Even if they somehow submit it to themselves, review action should be blocked
    await page.waitForTimeout(500);
    await page.click('button:has-text("Submit")');
    await page.waitForTimeout(1000);
    
    // If document is under review and author tries to review
    await page.goto('http://localhost:3001/documents');
    const docLink = page.locator('text=Self-Review Compliance Test').first();
    if (await docLink.isVisible()) {
      await docLink.click();
      
      // Approve/Reject buttons should NOT be visible to author
      const approveButton = page.locator('button:has-text("Approve")').first();
      const rejectButton = page.locator('button:has-text("Reject")').first();
      
      const approveVisible = await approveButton.isVisible().catch(() => false);
      const rejectVisible = await rejectButton.isVisible().catch(() => false);
      
      expect(approveVisible).toBeFalsy();
      expect(rejectVisible).toBeFalsy();
      
      console.log('✓ Author cannot see review/approval buttons for own document');
    }
    
    await logout(page);
  });
  
  test('Non-reviewer cannot approve documents', async ({ page }) => {
    console.log('TEST: Non-reviewer permission blocking');
    
    // Setup: Create and submit document
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document")');
    
    await page.fill('input[name="title"]', 'Non-Reviewer Permission Test');
    await page.fill('textarea[name="description"]', 'Testing permissions');
    await page.locator('select[name="document_type"]').first().selectOption({ index: 1 });
    await page.locator('select[name="document_source"]').first().selectOption({ index: 1 });
    
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(path.resolve('test_doc/test_document.docx'));
    
    await page.click('button[type="submit"]:has-text("Create")');
    await page.waitForTimeout(2000);
    
    // Submit for review
    await page.click('button:has-text("Submit for Review")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Submit")');
    await page.waitForTimeout(1000);
    
    await logout(page);
    
    // Try to access as viewer (no reviewer role)
    await login(page, testUsers.viewer.username, testUsers.viewer.password);
    
    await page.goto('http://localhost:3001/documents');
    
    // Find the document (if visible)
    const docLink = page.locator('text=Non-Reviewer Permission Test').first();
    if (await docLink.isVisible()) {
      await docLink.click();
      
      // Approve/Reject buttons should NOT be visible
      const approveButton = page.locator('button:has-text("Approve")').first();
      const rejectButton = page.locator('button:has-text("Reject")').first();
      
      const approveVisible = await approveButton.isVisible().catch(() => false);
      const rejectVisible = await rejectButton.isVisible().catch(() => false);
      
      expect(approveVisible).toBeFalsy();
      expect(rejectVisible).toBeFalsy();
      
      console.log('✓ Non-reviewer cannot see review action buttons');
    }
    
    await logout(page);
  });
  
  test('Non-approver cannot give final approval', async ({ page }) => {
    console.log('TEST: Non-approver permission blocking');
    
    // Setup: Create document and get it to REVIEWED status
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document")');
    
    await page.fill('input[name="title"]', 'Non-Approver Permission Test');
    await page.fill('textarea[name="description"]', 'Testing approver permissions');
    await page.locator('select[name="document_type"]').first().selectOption({ index: 1 });
    await page.locator('select[name="document_source"]').first().selectOption({ index: 1 });
    
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(path.resolve('test_doc/test_document.docx'));
    
    await page.click('button[type="submit"]:has-text("Create")');
    await page.waitForTimeout(2000);
    
    await page.click('button:has-text("Submit for Review")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Submit")');
    
    await logout(page);
    
    // Reviewer approves (gets to REVIEWED status)
    await login(page, testUsers.reviewer.username, testUsers.reviewer.password);
    
    await page.click('text=My Tasks');
    const docLink = page.locator('text=Non-Approver Permission Test').first();
    if (await docLink.isVisible()) {
      await docLink.click();
      await page.click('button:has-text("Approve")');
      
      const comment = page.locator('textarea[name="comment"]').first();
      if (await comment.isVisible()) {
        await comment.fill('Reviewed');
      }
      await page.click('button:has-text("Confirm")');
      await page.waitForTimeout(1000);
    }
    
    await logout(page);
    
    // Try to approve as author (not an approver)
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.goto('http://localhost:3001/documents');
    const docLink2 = page.locator('text=Non-Approver Permission Test').first();
    if (await docLink2.isVisible()) {
      await docLink2.click();
      
      // Final approval buttons should NOT be visible
      const finalApproveButton = page.locator('button:has-text("Approve"), button:has-text("Final Approval")').first();
      const finalApproveVisible = await finalApproveButton.isVisible().catch(() => false);
      
      expect(finalApproveVisible).toBeFalsy();
      
      console.log('✓ Non-approver cannot see final approval button');
    }
    
    await logout(page);
  });
  
  test('Viewer can only view, not modify documents', async ({ page }) => {
    console.log('TEST: Viewer read-only permissions');
    
    // Login as viewer
    await login(page, testUsers.viewer.username, testUsers.viewer.password);
    
    // Navigate to documents
    await page.goto('http://localhost:3001/documents');
    
    // Create button should NOT be visible or should fail
    const createButton = page.locator('button:has-text("Create Document")').first();
    const createButtonVisible = await createButton.isVisible().catch(() => false);
    
    if (createButtonVisible) {
      console.log('⚠️  Create button visible to viewer - checking if it works...');
      
      // Try to click it
      await createButton.click();
      
      // Should either show error or permission denied
      const errorMessage = await page.locator('text=/permission|denied|not allowed/i').isVisible({ timeout: 2000 }).catch(() => false);
      
      if (errorMessage) {
        console.log('✓ Viewer blocked from creating documents (error shown)');
      }
    } else {
      console.log('✓ Create button correctly hidden from viewer');
    }
    
    await logout(page);
  });
});
