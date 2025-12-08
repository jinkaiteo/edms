import { test, expect } from '@playwright/test';

test('system reset', async ({ page }) => {
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('admin');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('test123');
  await page.getByRole('textbox', { name: 'Password' }).press('Enter');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('button', { name: 'Administration' }).click();
  await page.getByRole('button', { name: '💾Backup & Recovery' }).click();
  await page.getByRole('button', { name: '⚠️ System Reset' }).click();
  await page.locator('label').filter({ hasText: 'I understand this is a' }).click();
  await page.getByRole('checkbox', { name: 'I acknowledge that ALL' }).check();
  await page.getByRole('checkbox', { name: 'I understand there is NO WAY' }).check();
  await page.getByRole('checkbox', { name: 'I confirm this is a TESTING/' }).check();
  await page.getByRole('checkbox', { name: 'I confirm no backup is needed' }).check();
  await page.getByRole('textbox', { name: 'Type the confirmation text' }).click();
  await page.getByRole('textbox', { name: 'Type the confirmation text' }).fill('RESET SYSTEM NOW');
  await page.getByRole('textbox', { name: 'Enter your password to' }).click();
  await page.getByRole('textbox', { name: 'Enter your password to' }).fill('test123');
  page.once('dialog', dialog => {
    console.log(`Dialog message: ${dialog.message()}`);
    dialog.dismiss().catch(() => {});
  });
  await page.getByRole('button', { name: '🚨 EXECUTE SYSTEM RESET &' }).click();
  await page.goto('http://localhost:3000/login');
});
