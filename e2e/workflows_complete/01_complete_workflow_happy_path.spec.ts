/**
 * Complete Document Workflow E2E Test - Happy Path
 * 
 * This test covers the complete document lifecycle from creation to effective status:
 * 1. Author creates document with file upload
 * 2. Author submits for review
 * 3. Reviewer approves document
 * 4. Author/Reviewer routes for approval
 * 5. Approver approves with effective date
 * 6. Document becomes EFFECTIVE
 * 
 * This is a REGRESSION TEST for all the issues fixed on 2026-01-10:
 * - Document creation with author field
 * - API endpoints working (document-types, document-sources)
 * - Complete workflow transitions
 */

import { test, expect, Page } from '@playwright/test';
import path from 'path';

// Test data
const testDocument = {
  title: 'E2E Test SOP-001',
  description: 'Complete workflow test document',
  type: 'SOP',
  source: 'Original Digital Draft',
  file: 'test_doc/test_document.docx'
};

const testUsers = {
  author: { username: 'author01', password: 'test123' },
  reviewer: { username: 'reviewer01', password: 'test123' },
  approver: { username: 'approver01', password: 'test123' }
};

/**
 * Helper function to login
 */
async function login(page: Page, username: string, password: string) {
  await page.goto('http://localhost:3001');
  
  // Wait for login form
  await page.waitForSelector('input[name="username"]', { timeout: 5000 });
  
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  
  // Wait for successful login (dashboard or main page)
  await page.waitForURL(/\/(dashboard|documents)/, { timeout: 10000 });
}

/**
 * Helper function to logout
 */
async function logout(page: Page) {
  // Look for logout button (may vary by implementation)
  const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout"), [data-testid="logout"]').first();
  
  if (await logoutButton.isVisible()) {
    await logoutButton.click();
    await page.waitForURL(/\/login/, { timeout: 5000 });
  }
}

test.describe('Complete Document Workflow - Happy Path', () => {
  
  test.beforeEach(async ({ page }) => {
    // Start with clean slate
    await page.goto('http://localhost:3001');
  });
  
  test('Complete workflow: Author creates → Reviewer approves → Approver approves', async ({ page }) => {
    
    // ========================================
    // STEP 1: Author Creates Document
    // ========================================
    console.log('STEP 1: Author creates document');
    
    await login(page, testUsers.author.username, testUsers.author.password);
    
    // Navigate to documents
    await page.click('text=Documents');
    await page.waitForTimeout(1000);
    
    // Click create document button
    const createButton = page.locator('button:has-text("Create Document"), button:has-text("New Document")').first();
    await createButton.click();
    
    // Wait for create modal/form
    await page.waitForSelector('input[name="title"], [placeholder*="title" i]', { timeout: 5000 });
    
    // Fill in document details
    await page.fill('input[name="title"], [placeholder*="title" i]', testDocument.title);
    await page.fill('textarea[name="description"], [placeholder*="description" i]', testDocument.description);
    
    // Select document type (REGRESSION TEST - this was causing 404)
    const typeSelect = page.locator('select[name="document_type"], select[name="documentType"]').first();
    await typeSelect.selectOption({ label: testDocument.type });
    
    // Select document source (REGRESSION TEST - this was causing 404)
    const sourceSelect = page.locator('select[name="document_source"], select[name="documentSource"]').first();
    await sourceSelect.selectOption({ label: testDocument.source });
    
    // Upload file
    const fileInput = page.locator('input[type="file"]').first();
    const filePath = path.resolve(testDocument.file);
    await fileInput.setInputFiles(filePath);
    
    // Submit form (REGRESSION TEST - author field now included automatically)
    await page.click('button[type="submit"]:has-text("Create"), button:has-text("Submit")');
    
    // Wait for success message
    await expect(page.locator('text=/created successfully/i, text=/success/i')).toBeVisible({ timeout: 10000 });
    
    console.log('✓ Document created successfully');
    
    // Get document ID for later steps
    const documentUrl = page.url();
    const documentId = documentUrl.match(/documents\/(\d+)/)?.[1];
    
    // ========================================
    // STEP 2: Author Submits for Review
    // ========================================
    console.log('STEP 2: Author submits for review');
    
    // Find and click "Submit for Review" button
    const submitReviewButton = page.locator('button:has-text("Submit for Review"), button:has-text("Send to Review")').first();
    await submitReviewButton.click();
    
    // Select reviewer
    const reviewerSelect = page.locator('select[name="reviewer"], select[name="reviewer_id"]').first();
    if (await reviewerSelect.isVisible()) {
      await reviewerSelect.selectOption({ label: testUsers.reviewer.username });
    }
    
    // Confirm submission
    await page.click('button:has-text("Submit"), button:has-text("Confirm")');
    
    // Wait for success
    await expect(page.locator('text=/submitted.*review/i')).toBeVisible({ timeout: 5000 });
    
    console.log('✓ Document submitted for review');
    
    // Logout author
    await logout(page);
    
    // ========================================
    // STEP 3: Reviewer Approves Document
    // ========================================
    console.log('STEP 3: Reviewer approves document');
    
    await login(page, testUsers.reviewer.username, testUsers.reviewer.password);
    
    // Go to My Tasks or Documents
    await page.click('text=My Tasks, text=Tasks');
    await page.waitForTimeout(1000);
    
    // Find the document
    const documentLink = page.locator(`text=${testDocument.title}`).first();
    await documentLink.click();
    
    // Click approve button
    const approveButton = page.locator('button:has-text("Approve")').first();
    await approveButton.click();
    
    // Add comment
    const commentField = page.locator('textarea[name="comment"], input[name="comment"]').first();
    if (await commentField.isVisible()) {
      await commentField.fill('Document reviewed and approved - looks good');
    }
    
    // Confirm approval
    await page.click('button:has-text("Confirm"), button:has-text("Submit")');
    
    // Wait for success
    await expect(page.locator('text=/approved/i, text=/success/i')).toBeVisible({ timeout: 5000 });
    
    console.log('✓ Document approved by reviewer');
    
    // Logout reviewer
    await logout(page);
    
    // ========================================
    // STEP 4: Approver Final Approval
    // ========================================
    console.log('STEP 4: Approver gives final approval');
    
    await login(page, testUsers.approver.username, testUsers.approver.password);
    
    // Go to My Tasks
    await page.click('text=My Tasks, text=Tasks');
    await page.waitForTimeout(1000);
    
    // Find the document
    await page.click(`text=${testDocument.title}`);
    
    // Click approve button
    await page.click('button:has-text("Approve")');
    
    // Set effective date (today for immediate activation)
    const effectiveDateField = page.locator('input[name="effective_date"], input[type="date"]').first();
    if (await effectiveDateField.isVisible()) {
      const today = new Date().toISOString().split('T')[0];
      await effectiveDateField.fill(today);
    }
    
    // Add comment
    const approverComment = page.locator('textarea[name="comment"], input[name="comment"]').first();
    if (await approverComment.isVisible()) {
      await approverComment.fill('Final approval granted - document is compliant');
    }
    
    // Confirm approval
    await page.click('button:has-text("Confirm"), button:has-text("Submit")');
    
    // Wait for success
    await expect(page.locator('text=/approved/i')).toBeVisible({ timeout: 5000 });
    
    console.log('✓ Document approved by approver');
    
    // ========================================
    // STEP 5: Verify Final Status
    // ========================================
    console.log('STEP 5: Verify document is EFFECTIVE or APPROVED');
    
    // Navigate to document details
    await page.goto(`http://localhost:3001/documents/${documentId || ''}`);
    
    // Check for EFFECTIVE or APPROVED status
    const statusBadge = page.locator('[class*="status"], [data-testid="status"]').first();
    const statusText = await statusBadge.textContent();
    
    expect(statusText?.toLowerCase()).toMatch(/effective|approved/);
    
    console.log(`✓ Document status: ${statusText}`);
    
    // Logout
    await logout(page);
    
    console.log('✓✓✓ COMPLETE WORKFLOW TEST PASSED ✓✓✓');
  });
  
  test('Verify document creation includes author field', async ({ page }) => {
    /**
     * REGRESSION TEST for the bug fixed on 2026-01-10
     * where author field was missing from document creation
     */
    
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document"), button:has-text("New Document")');
    
    // Fill minimal required fields
    await page.fill('input[name="title"]', 'Test Author Field Document');
    await page.fill('textarea[name="description"]', 'Testing author field is included');
    
    const typeSelect = page.locator('select[name="document_type"]').first();
    await typeSelect.selectOption({ index: 1 });
    
    const sourceSelect = page.locator('select[name="document_source"]').first();
    await sourceSelect.selectOption({ index: 1 });
    
    // Upload file
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(path.resolve(testDocument.file));
    
    // Submit - should NOT get 400 error about missing author
    await page.click('button[type="submit"]:has-text("Create")');
    
    // Should see success, not error
    await expect(page.locator('text=/error.*author/i')).not.toBeVisible({ timeout: 2000 });
    await expect(page.locator('text=/success|created/i')).toBeVisible({ timeout: 5000 });
    
    await logout(page);
  });
  
  test('Verify document-types and document-sources endpoints exist', async ({ page }) => {
    /**
     * REGRESSION TEST for the 404 errors fixed on 2026-01-10
     * where /document-types/ and /document-sources/ were not accessible
     */
    
    await login(page, testUsers.author.username, testUsers.author.password);
    
    // Open create document modal
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document")');
    
    // Wait for dropdowns to load
    await page.waitForTimeout(2000);
    
    // Check document type dropdown has options (means API worked)
    const typeSelect = page.locator('select[name="document_type"]');
    const typeOptions = await typeSelect.locator('option').count();
    expect(typeOptions).toBeGreaterThan(1); // At least 1 option + placeholder
    
    // Check document source dropdown has options (means API worked)
    const sourceSelect = page.locator('select[name="document_source"]');
    const sourceOptions = await sourceSelect.locator('option').count();
    expect(sourceOptions).toBeGreaterThan(1); // At least 1 option + placeholder
    
    console.log(`✓ Document types: ${typeOptions} options loaded`);
    console.log(`✓ Document sources: ${sourceOptions} options loaded`);
    
    await logout(page);
  });
});
