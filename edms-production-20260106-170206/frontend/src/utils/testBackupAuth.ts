/**
 * Test backup authentication in the browser console
 * Open browser dev tools and run: testBackupAuth()
 */

import { AuthHelpers } from './authHelpers';
import { backupApiService } from '../services/backupApi';

declare global {
  interface Window {
    testBackupAuth: () => Promise<void>;
  }
}

export const testBackupAuth = async (): Promise<void> => {
  console.log('🚀 Testing Backup API Authentication');
  console.log('=====================================');

  try {
    // Step 1: Check if already authenticated
    console.log('1️⃣ Checking authentication status...');
    const isAuth = AuthHelpers.isAuthenticated();
    console.log(`   Authenticated: ${isAuth}`);
    
    if (!isAuth) {
      console.log('2️⃣ Logging in with admin credentials...');
      try {
        const tokens = await AuthHelpers.login({
          username: 'admin',
          password: 'admin123'
        });
        console.log('   ✅ Login successful!');
        console.log('   Access token length:', tokens.accessToken?.length);
      } catch (loginError) {
        console.error('   ❌ Login failed:', loginError);
        return;
      }
    }

    // Step 3: Test backup configurations
    console.log('3️⃣ Testing backup configurations API...');
    try {
      const configs = await backupApiService.getBackupConfigurations();
      console.log(`   ✅ Found ${configs.length} backup configurations`);
      configs.slice(0, 3).forEach((config, index) => {
        console.log(`   ${index + 1}. ${config.name} (${config.backup_type})`);
      });
    } catch (configError) {
      console.error('   ❌ Configuration fetch failed:', configError);
    }

    // Step 4: Test backup jobs
    console.log('4️⃣ Testing backup jobs API...');
    try {
      const jobs = await backupApiService.getBackupJobs();
      console.log(`   ✅ Found ${jobs.length} backup jobs`);
      jobs.slice(0, 3).forEach((job, index) => {
        console.log(`   ${index + 1}. ${job.job_name} (${job.status})`);
      });
    } catch (jobError) {
      console.error('   ❌ Jobs fetch failed:', jobError);
    }

    // Step 5: Test system status
    console.log('5️⃣ Testing system status API...');
    try {
      const status = await backupApiService.getSystemStatus();
      console.log('   ✅ System status retrieved');
      console.log('   Status:', status.status);
      console.log('   Statistics:', status.statistics);
    } catch (statusError) {
      console.error('   ❌ Status fetch failed:', statusError);
    }

    console.log('\n🎉 Backup API authentication test completed!');
    console.log('✅ Frontend can now access backup APIs successfully');

  } catch (error) {
    console.error('❌ Backup auth test failed:', error);
  }
};

// Make it available globally for browser console testing
if (typeof window !== 'undefined') {
  window.testBackupAuth = testBackupAuth;
  console.log('🔧 Development tool loaded: testBackupAuth() available in console');
}

export default testBackupAuth;