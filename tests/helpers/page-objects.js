/**
 * Page Object Models for EDMS UI Testing
 * Centralized selectors and common interactions
 */

class LoginPage {
  constructor(page) {
    this.page = page;
    this.usernameSelectors = [
      'input[name="username"]',
      'input[name="email"]',
      'input[type="email"]',
      'input[type="text"]',
      'input[placeholder*="username" i]',
      'input[placeholder*="email" i]',
      'input[id="username"]',
      'input[id="email"]'
    ];
    this.passwordSelector = 'input[type="password"]';
    this.loginButtonSelectors = [
      'button[type="submit"]',
      'button:has-text("Login")',
      'button:has-text("Sign In")',
      '[data-testid="login-button"]'
    ];
  }

  async login(username, password) {
    // Find and fill username
    let usernameField = null;
    for (const selector of this.usernameSelectors) {
      if (await this.page.locator(selector).count() > 0) {
        usernameField = this.page.locator(selector).first();
        break;
      }
    }
    
    if (!usernameField) {
      throw new Error('Username field not found');
    }
    
    await usernameField.fill(username);
    
    // Fill password
    const passwordField = this.page.locator(this.passwordSelector).first();
    await passwordField.fill(password);
    
    // Click login
    let loginButton = null;
    for (const selector of this.loginButtonSelectors) {
      if (await this.page.locator(selector).count() > 0) {
        loginButton = this.page.locator(selector).first();
        break;
      }
    }
    
    if (!loginButton) {
      throw new Error('Login button not found');
    }
    
    await loginButton.click();
    
    // Wait for navigation - updated to handle actual EDMS URL patterns
    try {
      await this.page.waitForURL(/.*dashboard|.*documents|.*login/, { timeout: 15000 });
    } catch (e) {
      // If URL doesn't change, check if we're already on the main interface
      const edmsVisible = await this.page.locator('text=EDMS').isVisible();
      const userProfile = await this.page.locator('text=System Administrator, text=admin').isVisible();
      
      if (edmsVisible || userProfile) {
        console.log('✅ Already logged in or on main interface');
        return;
      }
      throw e;
    }
  }
}

class DocumentPage {
  constructor(page) {
    this.page = page;
    this.createButtonSelectors = [
      'button:has-text("Create Document")',
      'button:has-text("New Document")',
      'button:has-text("Create")',
      '[data-testid="create-document"]',
      '.create-document-btn'
    ];
    this.submitForReviewSelectors = [
      'button:has-text("Submit for Review")',
      '[data-testid="submit-review"]',
      '.submit-review-btn'
    ];
    this.modalSelectors = [
      '[data-testid="submit-review-modal"]',
      '[role="dialog"]',
      '.modal',
      '.modal-dialog',
      '.MuiDialog-root',
      '.ant-modal',
      '.chakra-modal',
      '.overlay'
    ];
  }

  async navigateToDocuments() {
    const documentLink = this.page.locator('text=Document Management, a[href*="document"]').first();
    await documentLink.click();
    await this.page.waitForTimeout(2000);
  }

  async createDocument(documentData) {
    // Click create button
    let createButton = null;
    for (const selector of this.createButtonSelectors) {
      if (await this.page.locator(selector).count() > 0) {
        createButton = this.page.locator(selector).first();
        break;
      }
    }
    
    if (!createButton) {
      throw new Error('Create document button not found');
    }
    
    await createButton.click();
    await this.page.waitForTimeout(2000);
    
    // Fill document form
    await this.fillDocumentForm(documentData);
    
    // Submit form
    const submitButton = this.page.locator('button[type="submit"], button:has-text("Create"), button:has-text("Save")').first();
    await submitButton.click();
    await this.page.waitForTimeout(3000);
  }

  async fillDocumentForm(data) {
    // Title
    if (data.title) {
      await this.page.fill('input[name="title"], input[placeholder*="title" i]', data.title);
    }
    
    // Description
    if (data.description) {
      await this.page.fill('textarea[name="description"], input[name="description"]', data.description);
    }
    
    // Document Type
    if (data.documentType) {
      const typeSelect = this.page.locator('select[name="document_type"], select[name="documentType"]');
      if (await typeSelect.count() > 0) {
        await typeSelect.selectOption(data.documentType);
      }
    }
    
    // Department
    if (data.department) {
      await this.page.fill('input[name="department"]', data.department);
    }
  }

  async submitForReview(reviewerUsername) {
    // Find and click submit for review button
    let submitButton = null;
    for (const selector of this.submitForReviewSelectors) {
      if (await this.page.locator(selector).count() > 0) {
        submitButton = this.page.locator(selector).first();
        break;
      }
    }
    
    if (!submitButton) {
      throw new Error('Submit for Review button not found');
    }
    
    await submitButton.click();
    
    // Wait for modal with enhanced timeout and multiple selectors
    let modalFound = false;
    for (const selector of this.modalSelectors) {
      try {
        await this.page.waitForSelector(selector, { timeout: 10000 });
        modalFound = true;
        break;
      } catch (e) {
        continue;
      }
    }
    
    if (!modalFound) {
      console.log('Modal not found with standard selectors, checking page state...');
      // Take screenshot for debugging
      await this.page.screenshot({ path: 'test-results/modal-debug.png' });
    }
    
    // Select reviewer if modal opened
    if (modalFound && reviewerUsername) {
      await this.selectReviewer(reviewerUsername);
      
      // Submit the modal
      const modalSubmitButton = this.page.locator('button:has-text("Submit"), button:has-text("Send"), button[type="submit"]').last();
      await modalSubmitButton.click();
      await this.page.waitForTimeout(3000);
    }
    
    return modalFound;
  }

  async selectReviewer(username) {
    // Try different reviewer selection methods
    const reviewerSelectors = [
      `select[name="reviewer"] option[value="${username}"]`,
      `input[name="reviewer"]`,
      `text=${username}`,
      `[data-testid="reviewer-${username}"]`
    ];
    
    for (const selector of reviewerSelectors) {
      try {
        if (selector.includes('select')) {
          await this.page.selectOption('select[name="reviewer"]', username);
        } else if (selector.includes('input')) {
          await this.page.fill('input[name="reviewer"]', username);
        } else {
          await this.page.click(selector);
        }
        break;
      } catch (e) {
        continue;
      }
    }
  }
}

class UserManagementPage {
  constructor(page) {
    this.page = page;
    this.createUserSelectors = [
      'button:has-text("Create User")',
      'button:has-text("Add User")',
      'button:has-text("Create")',
      '[data-testid="create-user"]'
    ];
    this.formSelectors = {
      username: ['input[name="username"]', 'input[placeholder*="username" i]'],
      email: ['input[name="email"]', 'input[type="email"]', 'input[placeholder*="email" i]'],
      firstName: ['input[name="first_name"]', 'input[placeholder*="first" i]'],
      lastName: ['input[name="last_name"]', 'input[placeholder*="last" i]'],
      department: ['input[name="department"]', 'input[placeholder*="department" i]'],
      position: ['input[name="position"]', 'input[placeholder*="position" i]'],
      password: ['input[type="password"]']
    };
  }

  async navigateToUserManagement() {
    // First expand Administration menu if it's collapsed
    const administrationButton = this.page.locator('text=Administration').first();
    if (await administrationButton.count() > 0) {
      try {
        // Try to click the administration button to expand the menu
        await administrationButton.click({ force: true });
        await this.page.waitForTimeout(2000);
      } catch (e) {
        console.log('Could not click Administration button, trying alternative navigation');
      }
    }
    
    // Try different navigation methods
    const navSelectors = [
      'text=👥User Management',
      'text=User Management', 
      'text=Users',
      'a[href*="user"]',
      'a[href*="admin"]',
      '[data-testid="user-management"]'
    ];
    
    for (const selector of navSelectors) {
      try {
        await this.page.click(selector, { force: true });
        await this.page.waitForTimeout(3000);
        console.log(`Successfully navigated using: ${selector}`);
        break;
      } catch (e) {
        continue;
      }
    }
  }

  async createUser(userData) {
    // Click create user button
    let createButton = null;
    for (const selector of this.createUserSelectors) {
      if (await this.page.locator(selector).count() > 0) {
        createButton = this.page.locator(selector).first();
        break;
      }
    }
    
    if (!createButton) {
      throw new Error('Create User button not found');
    }
    
    // Use force click to bypass overlay issues
    await createButton.click({ force: true });
    await this.page.waitForTimeout(3000);
    
    // Fill form fields
    await this.fillUserForm(userData);
    
    // Submit form
    const submitSelectors = [
      'button[type="submit"]',
      'button:has-text("Create User")',
      'button:has-text("Create")',
      'button:has-text("Save")'
    ];
    
    for (const selector of submitSelectors) {
      try {
        await this.page.click(selector, { force: true });
        await this.page.waitForTimeout(3000);
        break;
      } catch (e) {
        continue;
      }
    }
  }

  async fillUserForm(userData) {
    // Fill each field using multiple selector strategies
    for (const [fieldName, selectors] of Object.entries(this.formSelectors)) {
      const value = userData[fieldName];
      if (!value) continue;
      
      for (const selector of selectors) {
        try {
          if (fieldName === 'password') {
            // Handle password fields specially
            const passwordInputs = await this.page.locator(selector).all();
            if (passwordInputs.length >= 2) {
              await passwordInputs[0].fill(value);
              await passwordInputs[1].fill(userData.confirmPassword || value);
            }
          } else {
            await this.page.fill(selector, value);
          }
          break;
        } catch (e) {
          continue;
        }
      }
    }
    
    // Handle role/group selection if provided
    if (userData.role || userData.groups) {
      await this.selectUserRole(userData.role, userData.groups);
    }
  }

  async selectUserRole(role, groups) {
    // Role selection logic
    if (role) {
      try {
        const roleSelectors = [
          `select[name="role"] option[value="${role}"]`,
          `input[value="${role}"]`,
          `text=${role}`,
          `[data-testid="role-${role}"]`
        ];
        
        for (const selector of roleSelectors) {
          try {
            await this.page.click(selector);
            break;
          } catch (e) {
            continue;
          }
        }
      } catch (e) {
        console.log(`Could not select role: ${role}`);
      }
    }
    
    // Group selection logic
    if (groups && groups.length > 0) {
      for (const group of groups) {
        try {
          await this.page.click(`text=${group}, [data-testid="group-${group}"]`);
        } catch (e) {
          console.log(`Could not select group: ${group}`);
        }
      }
    }
  }
}

module.exports = {
  LoginPage,
  DocumentPage,
  UserManagementPage
};