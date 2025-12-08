/**
 * MANUAL AUTHOR02 CREATION SCRIPT
 * Run this directly in browser console after opening EDMS
 */

// Step 1: Get authentication token
async function getAuthToken() {
  console.log('🔐 Getting authentication token...');
  
  const response = await fetch('/api/v1/auth/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'test123' })
  });
  
  if (!response.ok) {
    throw new Error(`Authentication failed: ${response.status}`);
  }
  
  const tokens = await response.json();
  console.log('✅ Authentication token received');
  return tokens;
}

// Step 2: Set authentication
async function setAuth() {
  try {
    const tokens = await getAuthToken();
    localStorage.setItem('accessToken', tokens.access);
    localStorage.setItem('refreshToken', tokens.refresh);
    console.log('✅ Authentication tokens set in localStorage');
    console.log('🔄 Reloading page to activate authentication...');
    window.location.reload();
    return true;
  } catch (error) {
    console.error('❌ Authentication failed:', error);
    return false;
  }
}

// Step 3: Navigate to User Management (run after page reload)
function navigateToUserManagement() {
  console.log('🚀 Navigating to User Management...');
  
  // Navigate to admin page
  window.location.href = '/admin';
  
  // Wait for page load, then click User Management
  setTimeout(() => {
    const userMgmtButton = document.querySelector('*:has-text("👥User Management"), *:has-text("User Management")');
    if (userMgmtButton) {
      userMgmtButton.click();
      console.log('✅ Clicked User Management');
      
      // Wait and look for Create User button
      setTimeout(() => {
        findAndClickCreateUser();
      }, 2000);
    } else {
      console.log('❌ User Management button not found');
      console.log('🔍 Available buttons:', 
        Array.from(document.querySelectorAll('button')).map(b => b.textContent?.trim()).filter(t => t)
      );
    }
  }, 3000);
}

// Step 4: Find and click Create User button
function findAndClickCreateUser() {
  console.log('🔍 Looking for Create User button...');
  
  const createSelectors = [
    'button:contains("Create User")',
    'button:contains("Add User")', 
    'button:contains("Create")',
    '[role="button"]:contains("Create")'
  ];
  
  let createButton = null;
  
  // Try jQuery-style selectors if available
  if (window.jQuery) {
    for (const selector of ['button:contains("Create User")', 'button:contains("Create")']) {
      createButton = jQuery(selector).first()[0];
      if (createButton) break;
    }
  } else {
    // Fallback to manual search
    const allButtons = document.querySelectorAll('button');
    for (const button of allButtons) {
      const text = button.textContent?.trim() || '';
      if (text.includes('Create') && (text.includes('User') || text === 'Create')) {
        createButton = button;
        break;
      }
    }
  }
  
  if (createButton) {
    console.log('✅ Found Create User button');
    createButton.click();
    console.log('🎯 Clicked Create User button');
    
    setTimeout(() => {
      fillUserForm();
    }, 2000);
  } else {
    console.log('❌ Create User button not found');
    console.log('🔍 Available buttons:', 
      Array.from(document.querySelectorAll('button')).map(b => b.textContent?.trim()).filter(t => t)
    );
  }
}

// Step 5: Fill user creation form
function fillUserForm() {
  console.log('📝 Filling user creation form...');
  
  const inputs = document.querySelectorAll('input:visible, input');
  console.log(`📊 Found ${inputs.length} input fields`);
  
  if (inputs.length < 4) {
    console.log('❌ Insufficient form fields found');
    return;
  }
  
  // Author02 data
  const userData = [
    'author02',                    // username
    'author02@test.local',         // email
    'Author02',                    // first name 
    'User',                        // last name
    'Engineering',                 // department
    'Technical Writer',            // position
    'Author02Test123!',            // password
    'Author02Test123!'             // confirm password
  ];
  
  // Fill form fields
  for (let i = 0; i < Math.min(inputs.length, userData.length); i++) {
    if (inputs[i] && userData[i]) {
      inputs[i].value = userData[i];
      inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
      inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
      console.log(`✅ Filled field ${i + 1}: ${userData[i]}`);
    }
  }
  
  // Select Document Author role
  setTimeout(() => {
    selectDocumentAuthorRole();
  }, 1000);
}

// Step 6: Select Document Author role
function selectDocumentAuthorRole() {
  console.log('🎭 Selecting Document Author role...');
  
  const checkboxes = document.querySelectorAll('input[type="checkbox"]');
  console.log(`📊 Found ${checkboxes.length} checkboxes`);
  
  for (const checkbox of checkboxes) {
    const parent = checkbox.closest('label') || checkbox.parentElement;
    const labelText = parent ? parent.textContent : '';
    
    if (labelText.includes('Document Author') || (labelText.includes('Author') && labelText.includes('write'))) {
      checkbox.checked = true;
      checkbox.dispatchEvent(new Event('change', { bubbles: true }));
      console.log('✅ Selected Document Author role');
      break;
    }
  }
  
  setTimeout(() => {
    submitForm();
  }, 1000);
}

// Step 7: Submit form
function submitForm() {
  console.log('📤 Submitting user creation form...');
  
  const submitButtons = document.querySelectorAll('button');
  let submitButton = null;
  
  for (const button of submitButtons) {
    const text = button.textContent?.trim() || '';
    if (text.includes('Create') && !text.includes('Cancel')) {
      submitButton = button;
      break;
    }
  }
  
  if (submitButton) {
    submitButton.click();
    console.log('✅ Form submitted');
    
    setTimeout(() => {
      verifyCreation();
    }, 3000);
  } else {
    console.log('❌ Submit button not found');
    console.log('💡 Try pressing Enter or looking for submit button manually');
  }
}

// Step 8: Verify creation
function verifyCreation() {
  console.log('🔍 Verifying user creation...');
  
  // Check if modal closed
  const modals = document.querySelectorAll('[role="dialog"], .modal');
  if (modals.length === 0) {
    console.log('✅ Modal closed - likely success');
  }
  
  // Check for success message
  const bodyText = document.body.textContent;
  if (bodyText.includes('success') || bodyText.includes('created')) {
    console.log('✅ Success message found');
  }
  
  console.log('🎉 User creation process complete!');
  console.log('');
  console.log('📋 Next steps:');
  console.log('   1. Reload page and check user list');
  console.log('   2. Try logging in as author02 with password: Author02Test123!');
  console.log('   3. Test document creation capabilities');
}

// Main execution function
function createAuthor02User() {
  console.log('🚀 STARTING AUTHOR02 USER CREATION');
  console.log('==================================');
  console.log('');
  console.log('This script will:');
  console.log('1. Authenticate as admin');
  console.log('2. Navigate to User Management'); 
  console.log('3. Create author02 user with Document Author role');
  console.log('');
  
  const hasAuth = localStorage.getItem('accessToken');
  
  if (!hasAuth) {
    console.log('🔐 No authentication found, setting up auth...');
    setAuth();
  } else {
    console.log('🔐 Authentication found, proceeding...');
    navigateToUserManagement();
  }
}

// Export for manual use
window.createAuthor02User = createAuthor02User;
window.navigateToUserManagement = navigateToUserManagement;
window.setAuth = setAuth;

console.log('📜 Author02 Creation Script Loaded');
console.log('');
console.log('🎯 To create author02 user, run: createAuthor02User()');
console.log('🔄 If already authenticated, run: navigateToUserManagement()');
console.log('🔐 To set authentication only, run: setAuth()');
console.log('');

// Auto-run if page is ready
if (document.readyState === 'complete') {
  console.log('💡 Page is ready. Run createAuthor02User() to start!');
} else {
  console.log('⏳ Page still loading. Script will be available when ready.');
}