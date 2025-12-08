import { test, expect } from '@playwright/test';

// verify admin login
test('admin login', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('admin');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('test123');
  await page.getByRole('button', { name: 'Show password' }).click();
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByText('EDMSDocument LibraryMy').nth(1)).toBeVisible();
  await expect(page.locator('div').filter({ hasText: /^Document Library$/ }).nth(2)).toBeVisible();
  await expect(page.locator('div').filter({ hasText: 'Document LibraryManage,' }).nth(4)).toBeVisible();
  await expect(page.getByText('FiltersEffective')).toBeVisible();
  await expect(page.locator('.w-full > .bg-white')).toBeVisible();
  await expect(page.locator('.bg-white.rounded-lg.shadow-sm.border.border-gray-200.p-8')).toBeVisible();
  await page.getByRole('button', { name: 'Administration' }).click();
  await expect(page.getByRole('button', { name: '👥User Management' })).toBeVisible();
  await page.getByRole('button', { name: '👥User Management' }).click();
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

// test create viewer
test('create viewer01', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('admin');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('test123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('button', { name: 'Administration' }).click();
  await page.getByRole('button', { name: '👥User Management' }).click();
  await page.getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('textbox').first().click();
  await page.getByRole('textbox').first().fill('viewer01');
  await page.getByRole('textbox').first().press('Tab');
  await page.locator('input[type="email"]').fill('viewer01@edms.local');
  await page.locator('input[type="email"]').press('Tab');
  await page.getByRole('textbox').nth(2).fill('viewer01');
  await page.getByRole('textbox').nth(2).press('Tab');
  await page.getByRole('textbox').nth(3).fill('edms');
  await page.getByRole('textbox').nth(3).press('Tab');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).fill('P@ssword1234');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).press('Tab');
  await page.getByRole('textbox', { name: 'Confirm password...' }).fill('P@ssword1234');
  await page.getByRole('button', { name: 'Show password' }).first().click();
  await page.getByRole('button', { name: 'Show password' }).click();
  await page.getByRole('checkbox', { name: 'Document Author (write)' }).check();
  await page.locator('form').getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

// test create author
test('create author01', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('admin');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('test123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('button', { name: 'Administration' }).click();
  await page.getByRole('button', { name: '👥User Management' }).click();
  await page.getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('textbox').first().click();
  await page.getByRole('textbox').first().fill('author01');
  await page.getByRole('textbox').first().press('Tab');
  await page.locator('input[type="email"]').fill('author01@edms.local');
  await page.locator('input[type="email"]').press('Tab');
  await page.getByRole('textbox').nth(2).fill('author01');
  await page.getByRole('textbox').nth(2).press('Tab');
  await page.getByRole('textbox').nth(3).fill('edms');
  await page.getByRole('textbox').nth(3).press('Tab');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).fill('P@ssword1234');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).press('Tab');
  await page.getByRole('textbox', { name: 'Confirm password...' }).fill('P@ssword1234');
  await page.getByRole('button', { name: 'Show password' }).first().click();
  await page.getByRole('button', { name: 'Show password' }).click();
  await page.getByRole('checkbox', { name: 'Document Author (write)' }).check();
  await page.locator('form').getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

// test create reviewer
test('create reviewer01', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('admin');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('test123');
  await page.getByRole('button', { name: 'Show password' }).click();
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByText('EDMSDocument LibraryMy').nth(1)).toBeVisible();
  await expect(page.locator('div').filter({ hasText: /^Document Library$/ }).nth(2)).toBeVisible();
  await expect(page.locator('div').filter({ hasText: 'Document LibraryManage,' }).nth(4)).toBeVisible();
  await expect(page.getByText('FiltersEffective')).toBeVisible();
  await expect(page.locator('.w-full > .bg-white')).toBeVisible();
  await expect(page.locator('.bg-white.rounded-lg.shadow-sm.border.border-gray-200.p-8')).toBeVisible();
  await page.getByRole('button', { name: 'Administration' }).click();
  await expect(page.getByRole('button', { name: '👥User Management' })).toBeVisible();
  await page.getByRole('button', { name: '👥User Management' }).click();
  await page.getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('textbox').first().click();
  await page.getByRole('textbox').first().fill('reviewer01');
  await page.getByRole('textbox').first().press('Tab');
  await page.locator('input[type="email"]').fill('reviewer01@edms.local');
  await page.locator('input[type="email"]').press('Tab');
  await page.getByRole('textbox').nth(2).fill('reviewer01');
  await page.getByRole('textbox').nth(2).press('Tab');
  await page.getByRole('textbox').nth(3).fill('edms');
  await page.getByRole('textbox').nth(3).press('Tab');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).fill('');
  await page.getByRole('button', { name: 'Show password' }).first().click();
  await page.getByRole('textbox', { name: 'Enter secure password...' }).click();
  await page.getByRole('textbox', { name: 'Enter secure password...' }).fill('P@ssword1234');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).press('Tab');
  await page.getByRole('button', { name: 'Show password' }).click();
  await page.getByRole('textbox', { name: 'Confirm password...' }).click();
  await page.getByRole('textbox', { name: 'Confirm password...' }).fill('P@ssword1234');
  await page.getByRole('checkbox', { name: 'Document Reviewer (review)' }).check();
  await page.locator('form').getByRole('button', { name: 'Create User' }).click(); 
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

// test create approver
test('create approver01', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('admin');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('test123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('button', { name: 'Administration' }).click();
  await page.getByRole('button', { name: '👥User Management' }).click();
  await page.getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('textbox').first().click();
  await page.getByRole('textbox').first().fill('approver01');
  await page.getByRole('textbox').first().press('Tab');
  await page.locator('input[type="email"]').fill('approver01@edms.local');
  await page.locator('input[type="email"]').press('Tab');
  await page.getByRole('textbox').nth(2).fill('approver01');
  await page.getByRole('textbox').nth(2).press('Tab');
  await page.getByRole('textbox').nth(3).fill('edms');
  await page.getByRole('textbox').nth(3).press('Tab');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).fill('P@ssword1234');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).press('Tab');
  await page.getByRole('textbox', { name: 'Confirm password...' }).fill('P@ssword1234');
  await page.getByRole('button', { name: 'Show password' }).first().click();
  await page.getByRole('button', { name: 'Show password' }).click();
  await page.getByRole('checkbox', { name: 'Document Approver (approve)' }).check();
  await page.locator('form').getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});

// test create admin
test('create admin01', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('admin');
  await page.getByRole('textbox', { name: 'Username' }).press('Tab');
  await page.getByRole('textbox', { name: 'Password' }).fill('test123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('button', { name: 'Administration' }).click();
  await page.getByRole('button', { name: '👥User Management' }).click();
  await page.getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('textbox').first().click();
  await page.getByRole('textbox').first().fill('admin01');
  await page.getByRole('textbox').first().press('Tab');
  await page.locator('input[type="email"]').fill('admin01@edms.local');
  await page.locator('input[type="email"]').press('Tab');
  await page.getByRole('textbox').nth(2).fill('admin01');
  await page.getByRole('textbox').nth(2).press('Tab');
  await page.getByRole('textbox').nth(3).fill('edms');
  await page.getByRole('textbox').nth(3).press('Tab');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).fill('P@ssword1234');
  await page.getByRole('textbox', { name: 'Enter secure password...' }).press('Tab');
  await page.getByRole('textbox', { name: 'Confirm password...' }).fill('P@ssword1234');
  await page.getByRole('button', { name: 'Show password' }).first().click();
  await page.getByRole('button', { name: 'Show password' }).click();
  await page.getByRole('checkbox', { name: 'Document Approver (approve)' }).check();
  await page.locator('form').getByRole('button', { name: 'Create User' }).click();
  await page.getByRole('button', { name: 'Account Options' }).click();
  await page.getByRole('button', { name: 'Logout' }).click();
});
