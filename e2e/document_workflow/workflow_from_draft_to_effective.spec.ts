import { test, expect } from '@playwright/test';
import { BASE_URL, AUTHOR_USERNAME, AUTHOR_PASSWORD, REVIEWER_USERNAME, REVIEWER_PASSWORD, APPROVER_USERNAME, APPROVER_PASSWORD, DOC_TYPE_ID, DOC_SOURCE_ID, REVIEWER_ID, APPROVER_ID } from '../helpers/testConfig';

async function login(page, username: string, password: string) {
  await page.goto(`${BASE_URL}/login`);
  await page.getByRole('textbox', { name: 'Username' }).fill(username);
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

// 1) Author creates draft and submits for review
test('create draft document', async ({ page }) => { 
  await login(page, AUTHOR_USERNAME, AUTHOR_PASSWORD);

  await page.getByRole('link', { name: 'My Tasks' }).click();
  await page.getByRole('button', { name: '📝 Create Document' }).click();
  await page.getByRole('button', { name: 'Click to upload' }).click();
  await page.getByRole('button', { name: 'Click to upload' }).setInputFiles('e2e/document_workflow/edms_template.docx');
  await page.getByRole('textbox', { name: 'Document Title *' }).fill('Policy_01');
  await page.getByRole('textbox', { name: 'Description *' }).fill('This is the first policy.');
  await page.getByLabel('Document Type *').selectOption(DOC_TYPE_ID);
  await page.getByLabel('Document Source *').selectOption(DOC_SOURCE_ID);
  await page.getByRole('button', { name: 'Create Document', exact: true }).click();

  await page.getByRole('textbox', { name: 'Search documents by title,' }).fill('Policy_01');
  await page.getByRole('button').filter({ hasText: /^$/ }).first().click();
  await expect(page.getByRole('main')).toContainText('Policy_01');

  await page.getByRole('button', { name: 'workflow' }).click();
  await page.getByRole('button', { name: '📤 Submit for Review' }).click();
  await page.getByLabel('Select Reviewer *(Required)').selectOption(REVIEWER_ID);
  await page.getByRole('textbox', { name: 'Submission Comments(Optional)' }).fill('for your review');
  await page.getByRole('button', { name: 'Submit for Review', exact: true }).click();
  await expect(page.getByRole('main')).toContainText('PENDING REVIEW');
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

// 2) Reviewer reviews and approves
test('review document', async ({ page }) => {
  await login(page, REVIEWER_USERNAME, REVIEWER_PASSWORD);
  await page.getByRole('link', { name: 'My Tasks' }).click();
  await page.getByRole('textbox', { name: 'Search documents by title,' }).fill('Policy_01');
  await page.getByRole('button').filter({ hasText: /^$/ }).first().click();
  await page.getByRole('button', { name: 'workflow' }).click();
  await page.getByRole('button', { name: '📋 Start Review Process' }).click();
  await page.getByRole('button', { name: 'Approve Document' }).click();
  await page.getByRole('textbox', { name: 'Provide your review comments' }).fill('Looks good.');
  await page.getByRole('button', { name: 'Submit Review' }).click();
  await page.getByRole('button', { name: 'Confirm Approval' }).click();
  await expect(page.getByRole('main')).toContainText('REVIEWED');
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

// 3) Author routes for approval
test('send for approval', async ({ page }) => {
  await login(page, AUTHOR_USERNAME, AUTHOR_PASSWORD);
  await page.getByRole('link', { name: 'My Tasks' }).click();
  await expect(page.getByRole('main')).toContainText('REVIEWED');
  await page.getByRole('button', { name: 'workflow' }).click();
  await page.getByRole('button', { name: '✅ Route for Approval' }).click();
  await page.getByLabel('Select Approver *(Required)').selectOption(APPROVER_ID);
  await page.getByRole('textbox', { name: 'Routing Comments(Optional)' }).fill('for your approval');
  await page.getByRole('button', { name: 'Route for Approval', exact: true }).click();
  await expect(page.getByRole('main')).toContainText('PENDING APPROVAL');
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

// 4) Approver approves and document becomes effective
test('approve document', async ({ page }) => {
  await login(page, APPROVER_USERNAME, APPROVER_PASSWORD);
  await page.getByRole('link', { name: 'My Tasks' }).click();
  await page.getByRole('textbox', { name: 'Search documents by title,' }).fill('Policy_01');
  await page.getByRole('button').filter({ hasText: /^$/ }).first().click();
  await expect(page.getByRole('main')).toContainText('PENDING APPROVAL');
  await page.getByRole('button', { name: 'workflow' }).click();
  await page.getByRole('button', { name: '✅ Start Approval Process' }).click();
  await page.getByRole('button', { name: 'Approve Document' }).click();
  await page.getByRole('textbox', { name: 'Provide your approval' }).fill('Approved.');
  await page.getByRole('button', { name: 'Submit Approval Decision' }).click();
  await page.getByRole('button', { name: 'Confirm Approval' }).click();
  await page.getByRole('link', { name: 'Document Library' }).click();
  await page.getByRole('textbox', { name: 'Search documents by title,' }).fill('Policy_01');
  await page.getByRole('button').filter({ hasText: /^$/ }).first().click();
  await expect(page.getByRole('main')).toContainText('EFFECTIVE');
});
