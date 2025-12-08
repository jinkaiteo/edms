import { test, expect } from '@playwright/test';


test('review document', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('reviewer01');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('test123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('textbox', { name: 'Password' }).click();
  await page.getByRole('textbox', { name: 'Password' }).fill('P@ssword1234');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'My Tasks' }).click();
  await page.getByRole('textbox', { name: 'Search documents by title,' }).click();
  await page.getByRole('textbox', { name: 'Search documents by title,' }).fill('Policy_01');
  await page.getByRole('button').filter({ hasText: /^$/ }).nth(5).click();
  await page.getByRole('button', { name: 'workflow' }).click();
  await page.getByRole('button', { name: '📋 Start Review Process' }).click();
  await page.getByRole('button', { name: 'Approve Document will be' }).click();
  await page.getByRole('textbox', { name: 'Provide your review comments' }).click();
  await page.getByRole('textbox', { name: 'Provide your review comments' }).fill('good review.');
  await page.getByRole('button', { name: 'Submit Review' }).click();
  await page.getByRole('button', { name: 'Confirm Approval' }).click();
  await expect(page.getByRole('main')).toContainText('REVIEWED');
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

