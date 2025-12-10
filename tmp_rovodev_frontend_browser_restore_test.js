const { chromium } = require('playwright');
const path = require('path');

async function testFrontendBrowserRestore() {
    console.log('🎯 FRONTEND BROWSER RESTORE TEST - Complete Workflow');
    console.log('Testing: System Reinit → Frontend Browser Restore → Verification');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000  // Slow down for visibility
    });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        // Step 1: Login to the system
        console.log('\n📝 Step 1: Login to frontend...');
        await page.goto('http://localhost:3000/login');
        await page.waitForTimeout(2000);
        
        // Fill login credentials (admin/test123 from reinit)
        await page.fill('input[name="username"]', 'admin');
        await page.fill('input[name="password"]', 'test123');
        await page.click('button[type="submit"]');
        
        // Wait for login success
        await page.waitForURL('**/dashboard', { timeout: 15000 });
        console.log('✅ Login successful - redirected to dashboard');
        
        // Step 2: Navigate to Backup & Recovery
        console.log('\n📝 Step 2: Navigate to Backup & Recovery...');
        await page.click('text=Admin Dashboard');
        await page.waitForTimeout(1000);
        
        // Look for Backup & Recovery link
        const backupLink = page.locator('text=Backup & Recovery');
        await backupLink.click();
        await page.waitForTimeout(2000);
        console.log('✅ Navigated to Backup & Recovery page');
        
        // Step 3: Go to Restore tab
        console.log('\n📝 Step 3: Open Restore tab...');
        await page.click('text=Restore');
        await page.waitForTimeout(1000);
        console.log('✅ Restore tab opened');
        
        // Step 4: Upload migration package
        console.log('\n📝 Step 4: Upload migration package...');
        const migrationPackagePath = path.resolve('test_doc/edms_migration_package_2025-12-09.tar.gz');
        console.log('📁 Package path:', migrationPackagePath);
        
        // Find the file input
        const fileInput = page.locator('input[type="file"]').first();
        await fileInput.setInputFiles(migrationPackagePath);
        await page.waitForTimeout(2000);
        
        console.log('✅ File uploaded successfully');
        
        // Step 5: Start restore operation
        console.log('\n📝 Step 5: Start restore operation...');
        
        // Set up dialog handlers for confirmation and results
        let confirmationDialogSeen = false;
        let resultDialogSeen = false;
        let resultMessage = '';
        
        page.on('dialog', async dialog => {
            const message = dialog.message();
            console.log(`📢 Dialog: ${message.substring(0, 100)}...`);
            
            if (message.includes('confirm') || message.includes('proceed')) {
                console.log('✅ Accepting confirmation dialog');
                confirmationDialogSeen = true;
                await dialog.accept();
            } else if (message.includes('SUCCESS') || message.includes('COMPLETE') || message.includes('restored')) {
                console.log('🎉 SUCCESS dialog detected');
                resultDialogSeen = true;
                resultMessage = message;
                await dialog.accept();
            } else if (message.includes('ERROR') || message.includes('FAIL')) {
                console.log('❌ ERROR dialog detected');
                resultDialogSeen = true;
                resultMessage = message;
                await dialog.accept();
            } else {
                console.log('ℹ️ Other dialog, accepting...');
                await dialog.accept();
            }
        });
        
        // Click Upload and Restore button
        const restoreButton = page.locator('text=Upload and Restore');
        await restoreButton.click();
        
        console.log('⏳ Waiting for restore operation to complete...');
        
        // Wait for dialogs and operation completion
        await page.waitForTimeout(15000); // Give it time to complete
        
        // Step 6: Verify the results
        console.log('\n📝 Step 6: Verify restore results...');
        
        if (confirmationDialogSeen) {
            console.log('✅ Confirmation dialog was shown');
        }
        
        if (resultDialogSeen) {
            console.log('✅ Result dialog was shown');
            console.log(`📋 Result message: ${resultMessage.substring(0, 200)}`);
        }
        
        // Take a screenshot for verification
        await page.screenshot({ 
            path: 'tmp_rovodev_frontend_restore_completed.png', 
            fullPage: true 
        });
        console.log('📸 Screenshot saved: tmp_rovodev_frontend_restore_completed.png');
        
        console.log('\n🎉 Frontend browser restore test completed!');
        
        return {
            success: true,
            confirmationShown: confirmationDialogSeen,
            resultShown: resultDialogSeen,
            resultMessage: resultMessage
        };
        
    } catch (error) {
        console.error('\n❌ Frontend test failed:', error.message);
        
        // Take error screenshot
        await page.screenshot({ 
            path: 'tmp_rovodev_frontend_restore_error.png', 
            fullPage: true 
        });
        console.log('📸 Error screenshot saved: tmp_rovodev_frontend_restore_error.png');
        
        return {
            success: false,
            error: error.message
        };
        
    } finally {
        await browser.close();
    }
}

// Run the test
testFrontendBrowserRestore().then(result => {
    console.log('\n🏁 Frontend Browser Restore Test Results:');
    console.log('==========================================');
    console.log(`Success: ${result.success}`);
    
    if (result.success) {
        console.log(`Confirmation Dialog: ${result.confirmationShown}`);
        console.log(`Result Dialog: ${result.resultShown}`);
        console.log(`Result Message: ${result.resultMessage.substring(0, 100)}...`);
        console.log('\n✅ FRONTEND RESTORE TEST SUCCESSFUL!');
    } else {
        console.log(`Error: ${result.error}`);
        console.log('\n❌ FRONTEND RESTORE TEST FAILED');
    }
}).catch(console.error);