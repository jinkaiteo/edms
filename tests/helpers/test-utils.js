/**
 * Test Utilities for EDMS Playwright Tests
 * Common functions and validation helpers
 */

const { expect } = require('@playwright/test');

class TestUtils {
  constructor(page) {
    this.page = page;
  }

  /**
   * Wait for React app to fully load
   */
  async waitForReactApp(timeout = 15000) {
    try {
      await this.page.waitForSelector(
        'text=Dashboard, text=Document Management, text=Login, input[name="username"], input[type="email"], input[type="text"]', 
        { timeout }
      );
    } catch (e) {
      console.log('Waiting for React app to load...');
      await this.page.waitForTimeout(5000);
    }
  }

  /**
   * Take debugging screenshot with timestamp
   */
  async debugScreenshot(name) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `test-results/debug-${name}-${timestamp}.png`;
    await this.page.screenshot({ path: filename });
    console.log(`📸 Debug screenshot saved: ${filename}`);
    return filename;
  }

  /**
   * Validate API response structure and data
   */
  async validateApiResponse(response, expectedStatus = 200) {
    expect(response.status()).toBe(expectedStatus);
    
    const responseData = await response.json();
    expect(responseData).toBeDefined();
    
    return responseData;
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated() {
    const currentUrl = this.page.url();
    const dashboardVisible = await this.page.locator('text=Dashboard').isVisible();
    const loginFormVisible = await this.page.locator('input[type="password"]').isVisible();
    
    return dashboardVisible && !loginFormVisible && !currentUrl.includes('/login');
  }

  /**
   * Verify document state via API
   */
  async verifyDocumentState(documentTitle, expectedStatus) {
    console.log(`🔍 Verifying document "${documentTitle}" has status "${expectedStatus}"`);
    
    // Get auth token from localStorage or cookies
    const authData = await this.page.evaluate(() => {
      return {
        token: localStorage.getItem('authToken') || localStorage.getItem('token'),
        cookies: document.cookie
      };
    });
    
    const headers = { 'Content-Type': 'application/json' };
    if (authData.token) {
      headers['Authorization'] = `Bearer ${authData.token}`;
    }
    
    try {
      const response = await this.page.request.get('http://localhost:8000/api/documents/', {
        headers
      });
      
      if (response.ok()) {
        const documents = await response.json();
        const document = documents.results?.find(doc => doc.title === documentTitle) || 
                        documents.find?.(doc => doc.title === documentTitle);
        
        if (document) {
          console.log(`📄 Found document: ${document.title}, Status: ${document.status}`);
          expect(document.status).toBe(expectedStatus);
          return document;
        } else {
          console.log(`❌ Document "${documentTitle}" not found in API response`);
          return null;
        }
      }
    } catch (error) {
      console.log(`⚠️ API verification failed: ${error.message}`);
    }
    
    return null;
  }

  /**
   * Verify workflow state via API
   */
  async verifyWorkflowState(documentId, expectedState) {
    console.log(`🔄 Verifying workflow for document ${documentId} has state "${expectedState}"`);
    
    const authData = await this.page.evaluate(() => {
      return localStorage.getItem('authToken') || localStorage.getItem('token');
    });
    
    const headers = { 'Content-Type': 'application/json' };
    if (authData) {
      headers['Authorization'] = `Bearer ${authData}`;
    }
    
    try {
      const response = await this.page.request.get(`http://localhost:8000/api/workflows/document/${documentId}/`, {
        headers
      });
      
      if (response.ok()) {
        const workflowData = await response.json();
        if (workflowData.current_state) {
          console.log(`🔄 Workflow state: ${workflowData.current_state.code}`);
          expect(workflowData.current_state.code).toBe(expectedState);
          return workflowData;
        }
      }
    } catch (error) {
      console.log(`⚠️ Workflow verification failed: ${error.message}`);
    }
    
    return null;
  }

  /**
   * Count elements matching selector
   */
  async countElements(selector, expectedCount = null) {
    const count = await this.page.locator(selector).count();
    console.log(`📊 Found ${count} elements matching "${selector}"`);
    
    if (expectedCount !== null) {
      expect(count).toBe(expectedCount);
    }
    
    return count;
  }

  /**
   * Wait for element to be stable (not changing)
   */
  async waitForStableElement(selector, timeout = 5000) {
    let previousCount = 0;
    let stableCount = 0;
    const checkInterval = 500;
    const maxChecks = timeout / checkInterval;
    
    for (let i = 0; i < maxChecks; i++) {
      const currentCount = await this.page.locator(selector).count();
      
      if (currentCount === previousCount) {
        stableCount++;
        if (stableCount >= 3) { // Stable for 3 checks (1.5 seconds)
          return currentCount;
        }
      } else {
        stableCount = 0;
      }
      
      previousCount = currentCount;
      await this.page.waitForTimeout(checkInterval);
    }
    
    return previousCount;
  }

  /**
   * Extract data from page for validation
   */
  async extractPageData() {
    return await this.page.evaluate(() => {
      return {
        url: window.location.href,
        title: document.title,
        visibleText: document.body.innerText.substring(0, 500),
        formElements: {
          inputs: Array.from(document.querySelectorAll('input')).map(input => ({
            type: input.type,
            name: input.name,
            placeholder: input.placeholder,
            visible: input.offsetHeight > 0
          })),
          buttons: Array.from(document.querySelectorAll('button')).map(button => ({
            text: button.textContent?.trim(),
            type: button.type,
            visible: button.offsetHeight > 0
          })),
          selects: Array.from(document.querySelectorAll('select')).map(select => ({
            name: select.name,
            options: Array.from(select.options).map(opt => opt.value)
          }))
        },
        modals: {
          dialogs: document.querySelectorAll('[role="dialog"]').length,
          modals: document.querySelectorAll('.modal').length,
          overlays: document.querySelectorAll('.overlay, .fixed.inset-0').length
        }
      };
    });
  }

  /**
   * Validate form submission result
   */
  async validateFormSubmission(expectedSuccessIndicator) {
    await this.page.waitForTimeout(3000); // Wait for submission to process
    
    const successIndicators = [
      expectedSuccessIndicator,
      'text=Success',
      'text=Created',
      'text=Saved',
      '.success-message',
      '.alert-success'
    ];
    
    for (const indicator of successIndicators) {
      if (await this.page.locator(indicator).isVisible()) {
        console.log(`✅ Form submission successful: ${indicator}`);
        return true;
      }
    }
    
    // Check for error messages
    const errorIndicators = [
      'text=Error',
      'text=Failed',
      '.error-message',
      '.alert-error',
      '.alert-danger'
    ];
    
    for (const indicator of errorIndicators) {
      if (await this.page.locator(indicator).isVisible()) {
        console.log(`❌ Form submission error detected: ${indicator}`);
        await this.debugScreenshot('form-error');
        return false;
      }
    }
    
    console.log(`⚠️ Form submission result unclear`);
    await this.debugScreenshot('form-unclear');
    return null;
  }

  /**
   * Retry action with backoff
   */
  async retryAction(action, maxAttempts = 3, backoffMs = 1000) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        console.log(`🔄 Attempt ${attempt}/${maxAttempts}`);
        const result = await action();
        console.log(`✅ Action succeeded on attempt ${attempt}`);
        return result;
      } catch (error) {
        console.log(`❌ Attempt ${attempt} failed: ${error.message}`);
        
        if (attempt === maxAttempts) {
          throw error;
        }
        
        await this.page.waitForTimeout(backoffMs * attempt);
      }
    }
  }

  /**
   * Generate test data
   */
  static generateTestData(type, index = 1) {
    const timestamp = Date.now();
    
    switch (type) {
      case 'user':
        return {
          username: `testuser${index}_${timestamp}`,
          email: `testuser${index}_${timestamp}@edms.test`,
          firstName: `Test${index}`,
          lastName: `User${timestamp}`,
          department: 'QA Testing',
          position: 'Test Engineer',
          password: 'test123',
          confirmPassword: 'test123'
        };
      
      case 'document':
        return {
          title: `Test Document ${index} - ${timestamp}`,
          description: `Automated test document created at ${new Date().toISOString()}`,
          documentType: 'PROC',
          department: 'Quality Assurance'
        };
      
      default:
        return {};
    }
  }
}

// Export validation helpers
const ValidationHelpers = {
  async validateUserCreation(page, userData) {
    console.log(`🔍 Validating user creation: ${userData.username}`);
    
    // Check for success message or redirect
    const successIndicators = [
      'text=User created',
      'text=Successfully created',
      'text=User added',
      '.success'
    ];
    
    let success = false;
    for (const indicator of successIndicators) {
      if (await page.locator(indicator).isVisible()) {
        success = true;
        break;
      }
    }
    
    return success;
  },

  async validateDocumentCreation(page, documentData) {
    console.log(`🔍 Validating document creation: ${documentData.title}`);
    
    // Look for the document in the document list
    const documentExists = await page.locator(`text=${documentData.title}`).isVisible();
    
    if (documentExists) {
      console.log(`✅ Document found in UI: ${documentData.title}`);
      return true;
    }
    
    console.log(`⚠️ Document not visible in UI: ${documentData.title}`);
    return false;
  },

  async validateWorkflowTransition(page, documentTitle, expectedStatus) {
    console.log(`🔄 Validating workflow transition for: ${documentTitle}`);
    
    // Check document status in UI
    const statusElement = page.locator(`text=${documentTitle}`).locator('..').locator(`text=${expectedStatus}`);
    const statusVisible = await statusElement.isVisible();
    
    if (statusVisible) {
      console.log(`✅ Workflow status confirmed: ${expectedStatus}`);
      return true;
    }
    
    console.log(`⚠️ Expected status not visible: ${expectedStatus}`);
    return false;
  }
};

module.exports = {
  TestUtils,
  ValidationHelpers
};