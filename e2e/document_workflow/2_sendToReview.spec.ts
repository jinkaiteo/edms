import { test, expect } from '@playwright/test';
import * as path from 'path'; // Import path module for resolving file paths


test('create draft document', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('author01');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('P@ssword1234');
  await page.getByRole('button', { name: 'Show password' }).click();
  await page.getByRole('button', { name: 'Sign in' }).click();
  
  await page.getByRole('textbox', { name: 'Search documents by title,' }).click();
  await page.getByRole('textbox', { name: 'Search documents by title,' }).fill('Policy_01');
  await page.getByRole('button').filter({ hasText: /^$/ }).nth(5).click();
  await page.locator('.p-4.hover\\:shadow-md').waitFor({ state: 'visible' });
  await page.locator('.p-4.hover\\:shadow-md').click();
  await expect(page.getByRole('main')).toContainText('Policy_01');
  await expect(page.getByRole('main')).toContainText('DRAFT');
  
  await page.getByRole('button', { name: 'workflow' }).click();
  await page.getByRole('button', { name: '📤 Submit for Review Select' }).click();
  await page.getByLabel('Select Reviewer *(Required)').selectOption('119');
  await page.getByRole('textbox', { name: 'Submission Comments(Optional)' }).click();
  await page.getByRole('textbox', { name: 'Submission Comments(Optional)' }).fill('for your review');
  await page.getByRole('button', { name: 'Submit for Review', exact: true }).click();
  await expect(page.getByRole('main')).toContainText('PENDING REVIEW');
  await page.getByRole('button', { name: '👀 Monitor Review Progress' }).click();
  await expect(page.locator('div').filter({ hasText: /^📋 Review Status: Policy_01POL-2025-0001-v01\.00 • Version 1\.0Pending Review$/ }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Close' }).click();
  await page.getByRole('button', { name: '✖️ Clear' }).click();
  await expect(page.locator('.bg-white.rounded-lg.shadow-sm.border.border-gray-200.p-8')).toBeVisible();
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});
