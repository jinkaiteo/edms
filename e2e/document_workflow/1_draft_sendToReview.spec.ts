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
  
  await page.getByRole('link', { name: 'My Tasks' }).click();
  await page.getByRole('button', { name: '📝 Create Document' }).click();
  await page.getByRole('button', { name: 'Click to upload' }).click();
  
  // Define the path to the file you want to upload
  const filePath = path.join(__dirname, 'edms_template.docx'); // Assuming 'edms_template.docx' is in the same directory
  await page.getByRole('button', { name: 'Click to upload' }).click();
  // Locate the file input element and set the file
  await page.locator('input[type="file"]').setInputFiles(filePath);
  // await page.getByRole('button', { name: 'Click to upload' }).setInputFiles(filePath);
  
  await page.getByRole('textbox', { name: 'Document Title *' }).dblclick();
  await page.getByRole('textbox', { name: 'Document Title *' }).fill('Policy_01');
  await page.getByRole('textbox', { name: 'Description *' }).click();
  await page.getByRole('textbox', { name: 'Description *' }).fill('This is the first policy.');
  await page.getByLabel('Document Type *').selectOption('4');
  await page.getByLabel('Document Source *').selectOption('1');
  await page.getByRole('button', { name: 'Create Document', exact: true }).click();
});
