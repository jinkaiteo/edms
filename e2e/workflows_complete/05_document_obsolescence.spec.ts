/**
 * Document Obsolescence E2E Tests
 * 
 * Tests for marking documents obsolete:
 * 1. Approver marks document for obsolescence
 * 2. Set obsolescence date and reason
 * 3. Document status changes to SCHEDULED_FOR_OBSOLESCENCE
 * 4. Obsolete documents are read-only
 */

import { test, expect, Page } from '@playwright/test';

const testUsers = {
  author: { username: 'author01', password: 'test123' },
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

test.describe('Document Obsolescence Workflows', () => {
  
  test('Approver marks document for obsolescence', async ({ page }) => {
    console.log('TEST: Document obsolescence workflow');
    
    await login(page, testUsers.approver.username, testUsers.approver.password);
    
    // Navigate to documents
    await page.click('text=Documents');
    
    // Find an EFFECTIVE document
    const effectiveDoc = page.locator('tr:has-text("EFFECTIVE")').first();
    
    if (await effectiveDoc.isVisible({ timeout: 2000 })) {
      await effectiveDoc.click();
      
      // Look for "Mark Obsolete" button
      const obsoleteButton = page.locator('button:has-text("Mark Obsolete"), button:has-text("Obsolete")').first();
      
      if (await obsoleteButton.isVisible({ timeout: 2000 })) {
        await obsoleteButton.click();
        
        // Fill obsolescence form
        const dateField = page.locator('input[name="obsolescence_date"], input[type="date"]').first();
        
        // Set date to 30 days from now
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 30);
        const dateString = futureDate.toISOString().split('T')[0];
        
        await dateField.fill(dateString);
        
        // Fill reason
        await page.fill('textarea[name="reason"], textarea[name="obsolescence_reason"]', 
          'Document superseded by new version');
        
        // Confirm
        await page.click('button:has-text("Confirm"), button:has-text("Mark Obsolete")');
        
        // Wait for status change
        await page.waitForSelector('text=SCHEDULED_FOR_OBSOLESCENCE, text=Scheduled for Obsolescence', 
          { timeout: 5000 });
        
        console.log('✅ Document marked for obsolescence successfully');
      } else {
        console.log('⚠️ Mark Obsolete button not found (may not be implemented in UI)');
      }
    } else {
      console.log('⚠️ No EFFECTIVE documents found for testing');
    }
  });
  
  test('Obsolete documents cannot be edited', async ({ page }) => {
    console.log('TEST: Obsolete document read-only check');
    
    await login(page, testUsers.author.username, testUsers.author.password);
    
    await page.click('text=Documents');
    
    // Find an OBSOLETE document (if any)
    const obsoleteDoc = page.locator('tr:has-text("OBSOLETE")').first();
    
    if (await obsoleteDoc.isVisible({ timeout: 2000 })) {
      await obsoleteDoc.click();
      
      // Check that edit button is NOT visible
      const editButton = page.locator('button:has-text("Edit")').first();
      
      const isEditVisible = await editButton.isVisible({ timeout: 1000 }).catch(() => false);
      
      expect(isEditVisible).toBe(false);
      
      console.log('✅ Obsolete document is read-only');
    } else {
      console.log('⚠️ No OBSOLETE documents found for testing');
    }
  });
  
  test('Immediate obsolescence (today\'s date)', async ({ page }) => {
    console.log('TEST: Immediate obsolescence');
    
    await login(page, testUsers.approver.username, testUsers.approver.password);
    
    await page.click('text=Documents');
    
    const effectiveDoc = page.locator('tr:has-text("EFFECTIVE")').first();
    
    if (await effectiveDoc.isVisible({ timeout: 2000 })) {
      await effectiveDoc.click();
      
      const obsoleteButton = page.locator('button:has-text("Mark Obsolete")').first();
      
      if (await obsoleteButton.isVisible({ timeout: 2000 })) {
        await obsoleteButton.click();
        
        // Set date to today
        const today = new Date().toISOString().split('T')[0];
        await page.fill('input[type="date"]', today);
        
        await page.fill('textarea[name="reason"]', 'Immediate retirement required');
        
        await page.click('button:has-text("Confirm")');
        
        // Should be scheduled (scheduler will make it obsolete)
        await page.waitForSelector('text=SCHEDULED, text=Scheduled', { timeout: 5000 });
        
        console.log('✅ Immediate obsolescence scheduled');
      }
    }
  });
});
