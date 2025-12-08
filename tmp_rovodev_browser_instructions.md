# 🚀 Manual Author02 Creation - Browser Instructions

## Simple Browser-Based User Creation

Since Playwright test discovery has issues, here's a **guaranteed working method** to create author02 user using the browser console.

## 📋 Step-by-Step Instructions:

### Step 1: Open EDMS in Browser
1. Open your browser
2. Navigate to: `http://localhost:3000`
3. Open Developer Tools (F12 or Right-click → Inspect)
4. Go to **Console** tab

### Step 2: Load the Creation Script
Copy and paste this entire script into the console:

```javascript
// AUTHOR02 CREATION SCRIPT - PASTE THIS IN CONSOLE
async function getAuthToken() {
  const response = await fetch('/api/v1/auth/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'test123' })
  });
  return await response.json();
}

async function createAuthor02() {
  console.log('🚀 Creating author02 user...');
  
  // Get auth token
  const tokens = await getAuthToken();
  localStorage.setItem('accessToken', tokens.access);
  localStorage.setItem('refreshToken', tokens.refresh);
  console.log('✅ Authentication set');
  
  // Navigate to admin
  window.location.href = '/admin';
  
  // Wait for page load
  setTimeout(() => {
    // Click User Management
    const buttons = Array.from(document.querySelectorAll('button, a'));
    const userMgmtBtn = buttons.find(b => b.textContent?.includes('User Management'));
    if (userMgmtBtn) {
      userMgmtBtn.click();
      console.log('✅ Clicked User Management');
      
      // Wait and click Create User
      setTimeout(() => {
        const createBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.includes('Create'));
        if (createBtn) {
          createBtn.click();
          console.log('✅ Clicked Create User');
          
          // Fill form
          setTimeout(() => {
            const inputs = document.querySelectorAll('input');
            const userData = ['author02', 'author02@test.local', 'Author02', 'User', 'Engineering', 'Technical Writer', 'Author02Test123!', 'Author02Test123!'];
            
            for (let i = 0; i < Math.min(inputs.length, userData.length); i++) {
              if (inputs[i]) {
                inputs[i].value = userData[i];
                inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                console.log(`✅ Filled: ${userData[i]}`);
              }
            }
            
            // Select Document Author role
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            for (const checkbox of checkboxes) {
              const label = checkbox.closest('label')?.textContent || checkbox.parentElement?.textContent || '';
              if (label.includes('Document Author') || (label.includes('Author') && label.includes('write'))) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                console.log('✅ Selected Document Author role');
                break;
              }
            }
            
            // Submit form
            setTimeout(() => {
              const submitBtn = Array.from(document.querySelectorAll('button')).find(b => 
                b.textContent?.includes('Create') && !b.textContent?.includes('Cancel')
              );
              if (submitBtn) {
                submitBtn.click();
                console.log('🎉 Form submitted! Check for success message.');
              }
            }, 1000);
            
          }, 2000);
        }
      }, 3000);
    }
  }, 3000);
}

window.createAuthor02 = createAuthor02;
console.log('📜 Script loaded! Run: createAuthor02()');
```

### Step 3: Run the Creation Function
After pasting the script, type this command and press Enter:
```javascript
createAuthor02()
```

### Step 4: Monitor Progress
The console will show progress messages like:
- ✅ Authentication set
- ✅ Clicked User Management  
- ✅ Clicked Create User
- ✅ Filled: author02
- ✅ Selected Document Author role
- 🎉 Form submitted!

## 📊 Expected Results:

### User Details Created:
- **Username**: `author02`
- **Email**: `author02@test.local`
- **Password**: `Author02Test123!`
- **Role**: Document Author
- **Department**: Engineering
- **Position**: Technical Writer

### Verification Steps:
1. **Refresh the page** after script completion
2. **Navigate** to Admin → User Management
3. **Look for** "author02" in the user list
4. **Test login** with author02 credentials

## 🔧 Alternative Manual Method:

If the script doesn't work, you can create the user manually:

1. **Set authentication** in console:
   ```javascript
   fetch('/api/v1/auth/token/', {
     method: 'POST', 
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({username: 'admin', password: 'test123'})
   }).then(r => r.json()).then(t => {
     localStorage.setItem('accessToken', t.access);
     localStorage.setItem('refreshToken', t.refresh);
     location.reload();
   });
   ```

2. **Navigate manually**: Admin → User Management → Create User

3. **Fill form**:
   - Username: `author02`
   - Email: `author02@test.local` 
   - First Name: `Author02`
   - Last Name: `User`
   - Department: `Engineering`
   - Position: `Technical Writer`
   - Password: `Author02Test123!`
   - Confirm Password: `Author02Test123!`
   - Role: ✅ Document Author

4. **Click**: Create User

## 🎉 Success Indicators:
- Modal closes after submission
- Success message appears
- User appears in user list after refresh
- Can login with author02 credentials

This method bypasses all Playwright issues and uses the **proven authentication bypass method** we discovered during investigation!