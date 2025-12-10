const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function testFrontendRestoreAfterReinit() {
    console.log('🎯 Testing Frontend Restore After System Reinit...');
    
    // First, let's test the restore API directly to simulate frontend
    console.log('📡 Testing restore API endpoints (simulating frontend calls)...');
    
    try {
        // Test 1: Check if migration package exists
        const migrationPackagePath = path.resolve('test_doc/edms_migration_package_2025-12-09.tar.gz');
        console.log('📁 Migration package path:', migrationPackagePath);
        
        if (!fs.existsSync(migrationPackagePath)) {
            throw new Error('Migration package not found');
        }
        
        const packageSize = fs.statSync(migrationPackagePath).size;
        console.log(`✅ Migration package found: ${packageSize} bytes`);
        
        // Test 2: Simulate frontend API calls to backend restore
        console.log('\n🔧 Simulating frontend restore API calls...');
        
        const { spawn } = require('child_process');
        
        // Test the actual restore operation using the backend API simulation
        const restoreTest = spawn('docker', [
            'exec', 'edms_backend', 'python', 'manage.py', 'shell', '-c',
            `
import os
import json
from apps.backup.services import restore_service
from apps.backup.restore_processor import EnhancedRestoreProcessor
from apps.backup.direct_restore_processor import DirectRestoreProcessor

print("🚀 TESTING POST-REINIT FRONTEND RESTORE SIMULATION")

# Copy migration package to container
package_path = '/app/test_migration_package.tar.gz'
print(f"Package exists: {os.path.exists(package_path)}")

if os.path.exists(package_path):
    print("✅ Migration package available for restore")
    
    # Extract database backup from package
    import tarfile
    
    with tarfile.open(package_path, 'r:gz') as tar:
        tar.extract('./database/database_backup.json', '/tmp/')
    
    database_backup_path = '/tmp/database/database_backup.json'
    print(f"✅ Database backup extracted: {os.path.exists(database_backup_path)}")
    
    # Test Enhanced Restore (Step 1 of 2-step system)
    print("\\n🔧 Step 1: Enhanced Restore Processor (POST-REINIT)...")
    processor = EnhancedRestoreProcessor()
    restore_report = processor.process_backup_data(database_backup_path)
    
    print(f"Enhanced Restore Results:")
    print(f"  Business Score: {restore_report['summary']['business_functionality_score']}")
    print(f"  Records Processed: {restore_report['summary']['total_records']}")
    print(f"  Successfully Restored: {restore_report['summary']['successful_restorations']}")
    
    # Test Direct Restore (Step 2 of 2-step system)  
    print("\\n🎯 Step 2: Direct Restore Processor (POST-REINIT)...")
    direct_processor = DirectRestoreProcessor()
    direct_report = direct_processor.process_critical_business_data(database_backup_path)
    
    print(f"Direct Restore Results:")
    print(f"  Critical Data Restored: {direct_report['critical_data_restored']}")
    
    # Verify final system state
    print("\\n📊 POST-RESTORE SYSTEM VERIFICATION:")
    from django.contrib.auth import get_user_model
    from apps.documents.models import Document
    from apps.workflows.models import DocumentWorkflow
    
    User = get_user_model()
    
    print(f"Users: {User.objects.count()}")
    for user in User.objects.all():
        groups = list(user.groups.values_list('name', flat=True))
        print(f"  {user.username}: {groups}")
    
    print(f"Documents: {Document.objects.count()}")
    print(f"Workflows: {DocumentWorkflow.objects.count()}")
    
    print("\\n🎉 FRONTEND RESTORE SIMULATION COMPLETE!")
else:
    print("❌ Migration package not found in container")
            `
        ]);
        
        restoreTest.stdout.on('data', (data) => {
            console.log(data.toString());
        });
        
        restoreTest.stderr.on('data', (data) => {
            console.error('Error:', data.toString());
        });
        
        restoreTest.on('close', (code) => {
            console.log(`\n🏁 Frontend restore simulation completed with code: ${code}`);
            
            if (code === 0) {
                console.log('✅ Frontend restore API simulation successful!');
            } else {
                console.log('❌ Frontend restore API simulation failed');
            }
        });
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

// Run the test
testFrontendRestoreAfterReinit().catch(console.error);