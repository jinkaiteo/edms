/**
 * Document Rejection Workflow E2E Tests
 * 
 * Tests rejection scenarios at different workflow stages:
 * 1. Reviewer rejects document
 * 2. Approver rejects document
 * 3. Document returns to DRAFT after rejection
 * 4. Author can revise and resubmit
 * 5. Multiple rejection cycles
 */

import { test, expect, Page } from '@playwright/test';
import path from 'path';

const testUsers = {
  author: { username: 'author01', password: 'test123' },
  reviewer: { username: 'reviewer01', password: 'test123' },
  approver: { username: 'approver01', password: 'test123' }
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

test.describe('Document Rejection Workflows', () => {
  
  test('Reviewer rejects document with comments', async ({ page }) => {
    console.log('TEST: Reviewer rejection workflow');
    
    // Step 1: Author creates and submits document
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document")');
    
    await page.fill('input[name="title"]', 'Doc for Rejection Test');
    await page.fill('textarea[name="description"]', 'Will be rejected by reviewer');
    await page.locator('select[name="document_type"]').first().selectOption({ index: 1 });
    await page.locator('select[name="document_source"]').first().selectOption({ index: 1 });
    
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(path.resolve('test_doc/test_document.docx'));
    
    await page.click('button[type="submit"]:has-text("Create")');
    await page.waitForTimeout(2000);
    
    // Submit for review
    await page.click('button:has-text("Submit for Review")');
    const reviewerSelect = page.locator('select[name="reviewer"]').first();
    if (await reviewerSelect.isVisible()) {
      await reviewerSelect.selectOption({ label: testUsers.reviewer.username });
    }
    await page.click('button:has-text("Submit")');
    await page.waitForTimeout(1000);
    
    await logout(page);
    
    // Step 2: Reviewer rejects with detailed comments
    await login(page, testUsers.reviewer.username, testUsers.reviewer.password);
    
    await page.click('text=My Tasks');
    await page.click('text=Doc for Rejection Test');
    
    // Click reject button
    await page.click('button:has-text("Reject")');
    
    // Fill in rejection reason
    const rejectionComment = (
      "Document requires revision:\n" +
      "1. Section 2 has incorrect procedure\n" +
      "2. Missing safety warnings\n" +
      "3. Needs management approval signature"
    );
    
    const commentField = page.locator('textarea[name="comment"], textarea[placeholder*="comment" i]').first();
    await commentField.fill(rejectionComment);
    
    // Confirm rejection
    await page.click('button:has-text("Confirm"), button:has-text("Submit")');
    
    // Verify rejection success message
    await expect(page.locator('text=/rejected/i')).toBeVisible({ timeout: 5000 });
    
    console.log('✓ Document rejected by reviewer');
    
    await logout(page);
    
    // Step 3: Verify document back to DRAFT for author
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('text=Doc for Rejection Test');
    
    // Check status is DRAFT
    const statusBadge = page.locator('[class*="status"]').first();
    const statusText = await statusBadge.textContent();
    expect(statusText?.toLowerCase()).toContain('draft');
    
    console.log('✓ Document returned to DRAFT status');
    
    await logout(page);
  });
  
  test('Approver rejects document', async ({ page }) => {
    console.log('TEST: Approver rejection workflow');
    
    // Setup: Create document that goes through review to approval stage
    await login(page, testUsers.author.username, testUsers.author.password);
    
    // Create document
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document")');
    
    await page.fill('input[name="title"]', 'Doc for Approver Rejection');
    await page.fill('textarea[name="description"]', 'Will be rejected by approver');
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
    
    // Reviewer approves (so it reaches approver)
    await login(page, testUsers.reviewer.username, testUsers.reviewer.password);
    
    await page.click('text=My Tasks');
    await page.click('text=Doc for Approver Rejection');
    await page.click('button:has-text("Approve")');
    
    const reviewComment = page.locator('textarea[name="comment"]').first();
    if (await reviewComment.isVisible()) {
      await reviewComment.fill('Reviewed and approved');
    }
    await page.click('button:has-text("Confirm")');
    await page.waitForTimeout(1000);
    
    await logout(page);
    
    // Approver rejects
    await login(page, testUsers.approver.username, testUsers.approver.password);
    
    await page.click('text=My Tasks');
    await page.click('text=Doc for Approver Rejection');
    
    // Reject button
    await page.click('button:has-text("Reject")');
    
    // Fill rejection reason
    const rejectionReason = (
      "Document does not meet regulatory requirements:\n" +
      "- Missing FDA compliance references\n" +
      "- Procedure not aligned with 21 CFR Part 11\n" +
      "- Requires complete rewrite"
    );
    
    const commentField = page.locator('textarea[name="comment"]').first();
    await commentField.fill(rejectionReason);
    
    // Confirm
    await page.click('button:has-text("Confirm")');
    
    // Verify rejection
    await expect(page.locator('text=/rejected/i')).toBeVisible({ timeout: 5000 });
    
    console.log('✓ Document rejected by approver');
    
    await logout(page);
    
    // Verify back to DRAFT
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('text=Doc for Approver Rejection');
    
    const statusBadge = page.locator('[class*="status"]').first();
    const statusText = await statusBadge.textContent();
    expect(statusText?.toLowerCase()).toContain('draft');
    
    console.log('✓ Document returned to DRAFT after approver rejection');
    
    await logout(page);
  });
  
  test('Author can revise and resubmit rejected document', async ({ page }) => {
    console.log('TEST: Resubmission after rejection');
    
    // Create and submit document
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document")');
    
    await page.fill('input[name="title"]', 'Doc for Resubmission Test');
    await page.fill('textarea[name="description"]', 'First attempt');
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
    
    await logout(page);
    
    // Reviewer rejects
    await login(page, testUsers.reviewer.username, testUsers.reviewer.password);
    
    await page.click('text=My Tasks');
    await page.click('text=Doc for Resubmission Test');
    await page.click('button:has-text("Reject")');
    
    const commentField = page.locator('textarea[name="comment"]').first();
    await commentField.fill('Please revise section 3');
    await page.click('button:has-text("Confirm")');
    await page.waitForTimeout(1000);
    
    await logout(page);
    
    // Author revises and resubmits
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('text=Doc for Resubmission Test');
    
    // Edit document (if edit functionality available)
    const editButton = page.locator('button:has-text("Edit")').first();
    if (await editButton.isVisible()) {
      await editButton.click();
      await page.fill('textarea[name="description"]', 'Revised version - addressed reviewer feedback');
      await page.click('button:has-text("Save")');
      await page.waitForTimeout(1000);
    }
    
    // Resubmit for review
    const resubmitButton = page.locator('button:has-text("Submit for Review")').first();
    
    // Document should allow resubmission
    expect(await resubmitButton.isVisible()).toBeTruthy();
    
    await resubmitButton.click();
    await page.waitForTimeout(500);
    await page.click('button:has-text("Submit")');
    
    // Should succeed
    await expect(page.locator('text=/submitted/i')).toBeVisible({ timeout: 5000 });
    
    console.log('✓ Document successfully resubmitted after revision');
    
    await logout(page);
  });
});
