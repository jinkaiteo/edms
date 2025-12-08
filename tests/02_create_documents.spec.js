const { test, expect } = require('@playwright/test');
const { config, testDocuments } = require('../playwright_test_suite.js');
const path = require('path');

test.describe('Document Creation Tests', () => {
  let userTokens = {};

  test.beforeAll(async ({ request }) => {
    // Get auth tokens for all test users
    console.log('🔐 Getting authentication tokens for test users...');
    
    const testUsernames = ['author01', 'author02'];
    
    for (const username of testUsernames) {
      try {
        const loginResponse = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/auth/token/`, {
          data: {
            username: username,
            password: 'test123'
          }
        });
        
        const loginData = await loginResponse.json();
        userTokens[username] = loginData.access;
        console.log(`✅ Got token for ${username}`);
      } catch (e) {
        console.error(`Failed to get token for ${username}: ${e.message}`);
      }
    }
  });

  test('Upload and create test documents', async ({ page }) => {
    console.log('📄 Starting document creation process...');
    
    for (let i = 0; i < testDocuments.length; i++) {
      const doc = testDocuments[i];
      console.log(`Creating document ${i + 1}/${testDocuments.length}: ${doc.title}`);
      
      // Login as the document author
      await page.goto(config.baseURL);
      await page.fill('input[name="username"]', doc.author);
      await page.fill('input[name="password"]', 'test123');
      await page.click('button[type="submit"]');
      
      // Wait for dashboard to load
      await expect(page.locator('text=Dashboard')).toBeVisible({ timeout: config.timeout });
      
      // Navigate to document management
      await page.click('text=Documents, text=Document Management');
      await expect(page.locator('text=Document Management, text=Documents')).toBeVisible();
      
      // Click create/upload document button
      const createButtons = [
        'button:has-text("Upload Document")',
        'button:has-text("Create Document")',
        'button:has-text("New Document")',
        'button:has-text("Add Document")'
      ];
      
      let buttonClicked = false;
      for (const buttonSelector of createButtons) {
        try {
          await page.click(buttonSelector, { timeout: 2000 });
          buttonClicked = true;
          break;
        } catch (e) {
          continue;
        }
      }
      
      if (!buttonClicked) {
        // Try clicking any button that looks like it creates documents
        await page.click('button[class*="upload"], button[class*="create"], button[class*="add"]');
      }
      
      // Wait for upload/create modal to appear
      await page.waitForSelector('input[type="file"], input[name="title"], input[placeholder*="title" i]', { timeout: 10000 });
      
      // Upload the test document file
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.count() > 0) {
        await fileInput.setInputFiles(config.testDocumentPath);
        console.log(`📎 File uploaded: ${path.basename(config.testDocumentPath)}`);
        
        // Wait for file to be processed
        await page.waitForTimeout(2000);
      }
      
      // Fill document metadata
      await page.fill('input[name="title"], input[placeholder*="title" i]', doc.title);
      await page.fill('textarea[name="description"], input[name="description"], textarea[placeholder*="description" i]', doc.description);
      
      // Select document type
      const docTypeSelectors = [
        `select[name="documentType"] option[value="${doc.documentType}"]`,
        `select[name="document_type"] option[value="${doc.documentType}"]`,
        `option:has-text("${doc.documentType}")`,
        `button:has-text("${doc.documentType}")`,
        `input[value="${doc.documentType}"]`
      ];
      
      for (const selector of docTypeSelectors) {
        try {
          await page.click(selector, { timeout: 2000 });
          break;
        } catch (e) {
          continue;
        }
      }
      
      // Set department if available
      try {
        await page.fill('input[name="department"], select[name="department"]', doc.department);
      } catch (e) {
        console.log('Department field not found, skipping...');
      }
      
      // Submit document creation
      const submitButtons = [
        'button[type="submit"]',
        'button:has-text("Create")',
        'button:has-text("Save")',
        'button:has-text("Upload")',
        'button:has-text("Submit")'
      ];
      
      for (const buttonSelector of submitButtons) {
        try {
          await page.click(buttonSelector, { timeout: 2000 });
          break;
        } catch (e) {
          continue;
        }
      }
      
      // Wait for success message or document to appear in list
      try {
        await expect(page.locator('text=successfully created, text=Document created, text=Success, text=uploaded')).toBeVisible({ timeout: 10000 });
        console.log(`✅ Document ${doc.title} created successfully`);
      } catch (e) {
        // Check if document appears in the list
        await expect(page.locator(`text=${doc.title}`)).toBeVisible({ timeout: 10000 });
        console.log(`✅ Document ${doc.title} appears in document list`);
      }
      
      // Close any modals
      const modalCloseSelectors = [
        'button[aria-label="Close"]',
        'button:has-text("Close")',
        'button.close',
        '[data-testid="close-button"]'
      ];
      
      for (const closeSelector of modalCloseSelectors) {
        try {
          await page.click(closeSelector, { timeout: 1000 });
          break;
        } catch (e) {
          continue;
        }
      }
      
      // Wait between document creations
      await page.waitForTimeout(2000);
      
      // Logout to prepare for next user
      try {
        await page.click('text=Logout, button[aria-label="Logout"], [data-testid="logout"]');
      } catch (e) {
        // If logout button not found, continue anyway
      }
    }
    
    console.log('🎉 Document creation completed successfully!');
  });

  test('Verify all documents were created', async ({ page }) => {
    console.log('🔍 Verifying document creation...');
    
    // Login as admin to see all documents
    await page.goto(config.baseURL);
    await page.fill('input[name="username"]', config.adminCredentials.username);
    await page.fill('input[name="password"]', config.adminCredentials.password);
    await page.click('button[type="submit"]');
    
    // Navigate to document management
    await page.click('text=Documents, text=Document Management');
    await expect(page.locator('text=Document Management, text=Documents')).toBeVisible();
    
    // Verify each document exists
    for (const doc of testDocuments) {
      await expect(page.locator(`text=${doc.title}`)).toBeVisible();
      console.log(`✅ Verified document: ${doc.title}`);
    }
    
    console.log(`🎯 All ${testDocuments.length} documents verified successfully!`);
  });

  test('Check document details and metadata', async ({ page }) => {
    console.log('📋 Checking document details...');
    
    // Login as admin
    await page.goto(config.baseURL);
    await page.fill('input[name="username"]', config.adminCredentials.username);
    await page.fill('input[name="password"]', config.adminCredentials.password);
    await page.click('button[type="submit"]');
    
    // Navigate to documents
    await page.click('text=Documents, text=Document Management');
    await expect(page.locator('text=Document Management, text=Documents')).toBeVisible();
    
    // Check first document details
    const firstDoc = testDocuments[0];
    
    // Click on the document title or view button
    try {
      await page.click(`text=${firstDoc.title}`);
    } catch (e) {
      // Try clicking a view/details button near the document
      await page.click(`tr:has-text("${firstDoc.title}") button:has-text("View"), tr:has-text("${firstDoc.title}") button:has-text("Details")`);
    }
    
    // Verify document details are displayed
    await expect(page.locator(`text=${firstDoc.title}`)).toBeVisible();
    await expect(page.locator(`text=${firstDoc.description}`)).toBeVisible();
    
    console.log(`✅ Document details verified for: ${firstDoc.title}`);
  });

  test('Create documents via API for additional coverage', async ({ request }) => {
    console.log('🔌 Creating additional documents via API...');
    
    const apiDocuments = [
      {
        title: 'Emergency Procedures V1.0',
        description: 'Emergency response procedures for all departments',
        document_type: 'PROC',
        author: 'author01'
      },
      {
        title: 'Code of Conduct V3.0',
        description: 'Updated employee code of conduct',
        document_type: 'POL', 
        author: 'author02'
      }
    ];
    
    for (const doc of apiDocuments) {
      if (!userTokens[doc.author]) {
        console.log(`No token available for ${doc.author}, skipping API document creation`);
        continue;
      }
      
      try {
        const response = await request.post(`${config.baseURL.replace('3000', '8000')}/api/v1/documents/`, {
          headers: {
            'Authorization': `Bearer ${userTokens[doc.author]}`,
            'Content-Type': 'application/json'
          },
          data: {
            title: doc.title,
            description: doc.description,
            document_type: doc.document_type,
            status: 'DRAFT'
          }
        });
        
        if (response.ok()) {
          console.log(`✅ API document created: ${doc.title}`);
        } else {
          console.log(`❌ Failed to create document via API: ${doc.title} - ${response.status()}`);
        }
      } catch (e) {
        console.log(`❌ API document creation failed for ${doc.title}: ${e.message}`);
      }
    }
    
    console.log('🎉 API document creation completed!');
  });
});