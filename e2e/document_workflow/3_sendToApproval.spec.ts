import { test, expect } from '@playwright/test';

test('send for approval', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('author01');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('P@ssword1234');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'My Tasks' }).click();
  await expect(page.getByRole('main')).toContainText('REVIEWED');
  await page.getByRole('button', { name: 'workflow' }).click();
  await page.getByRole('button', { name: '✅ Route for Approval (Author' }).click();
  await page.getByLabel('Select Approver *(Required)').selectOption('120');
  await page.getByRole('textbox', { name: 'Routing Comments(Optional)' }).click();
  await page.getByRole('textbox', { name: 'Routing Comments(Optional)' }).fill('for your approval');
  await page.getByRole('button', { name: 'Route for Approval', exact: true }).click();
  await expect(page.getByRole('main')).toContainText('PENDING APPROVAL');
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});
