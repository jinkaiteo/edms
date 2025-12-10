const { chromium } = require('playwright');
const path = require('path');

async function testFrontendRestore() {
    console.log('🚀 Starting Frontend Restore Test...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        // Step 1: Login to the system
        console.log('📝 Step 1: Logging in...');
        await page.goto('http://localhost:3000/login');
        await page.waitForTimeout(2000);
        
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'test123');
        await page.click('button[type="submit"]');
        
        // Wait for login success
        await page.waitForURL('**/dashboard', { timeout: 10000 });
        console.log('✅ Login successful');
        
        // Step 2: Navigate to Backup & Recovery
        console.log('📝 Step 2: Navigating to Backup & Recovery...');
        await page.click('text=Admin Dashboard');
        await page.waitForTimeout(1000);
        await page.click('text=Backup & Recovery');
        await page.waitForTimeout(2000);
        console.log('✅ Navigated to Backup & Recovery page');
        
        // Step 3: Go to Restore tab
        console.log('📝 Step 3: Opening Restore tab...');
        await page.click('text=Restore');
        await page.waitForTimeout(1000);
        console.log('✅ Restore tab opened');
        
        // Step 4: Upload migration package
        console.log('📝 Step 4: Uploading migration package...');
        const migrationPackagePath = path.resolve('test_doc/edms_migration_package_2025-12-09.tar.gz');
        console.log('📁 Package path:', migrationPackagePath);
        
        // Find and use the file input
        const fileInput = await page.locator('input[type="file"]').first();
        await fileInput.setInputFiles(migrationPackagePath);
        await page.waitForTimeout(1000);
        
        // Verify file is selected
        const selectedFile = await page.textContent('text=Selected:');
        if (selectedFile) {
            console.log('✅ File selected:', selectedFile);
        } else {
            console.log('⚠️ File selection not visible, proceeding...');
        }
        
        // Step 5: Click Upload and Restore
        console.log('📝 Step 5: Starting restore operation...');
        
        // Handle the confirmation dialog
        page.on('dialog', async dialog => {
            console.log('⚠️ Confirmation dialog:', dialog.message().substring(0, 100) + '...');
            await dialog.accept();
        });
        
        await page.click('text=Upload and Restore');
        
        // Wait for the operation to complete (this might take a while)
        console.log('⏳ Waiting for restore operation to complete...');
        await page.waitForTimeout(10000); // Wait 10 seconds for the operation
        
        // Step 6: Handle success/error dialogs
        page.on('dialog', async dialog => {
            const message = dialog.message();
            console.log('📢 Result dialog:', message.substring(0, 200));
            if (message.includes('SUCCESSFUL') || message.includes('SUCCESS')) {
                console.log('✅ Restore operation appears successful!');
            } else {
                console.log('❌ Restore operation may have failed:', message);
            }
            await dialog.accept();
        });
        
        await page.waitForTimeout(5000);
        
        console.log('🎉 Frontend restore test completed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        
        // Take screenshot for debugging
        await page.screenshot({ 
            path: 'tmp_rovodev_restore_test_error.png', 
            fullPage: true 
        });
        console.log('📸 Screenshot saved: tmp_rovodev_restore_test_error.png');
    } finally {
        await browser.close();
    }
}

// Run the test
testFrontendRestore().then(() => {
    console.log('🏁 Test script completed');
}).catch(console.error);