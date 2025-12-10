/**
 * Dedicated backup API service with enhanced authentication handling
 */

import { AuthHelpers } from '../utils/authHelpers';

export interface BackupConfiguration {
  id: number;
  name: string;
  description: string;
  backup_type: string;
  frequency: string;
  is_enabled: boolean;
  status: string;
}

export interface BackupJob {
  id: number;
  job_name: string;
  backup_type: string;
  status: string;
  created_at: string;
  completed_at?: string;
  backup_size?: number;
}

export class BackupApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
  }

  /**
   * Get all backup configurations
   */
  async getBackupConfigurations(): Promise<BackupConfiguration[]> {
    try {
      const response = await AuthHelpers.authenticatedFetch(
        `${this.baseURL}/backup/configurations/`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch backup configurations: ${response.statusText}`);
      }

      const data = await response.json();
      return data.results || data;
    } catch (error) {
      console.error('Failed to fetch backup configurations:', error);
      throw error;
    }
  }

  /**
   * Get backup jobs
   */
  async getBackupJobs(): Promise<BackupJob[]> {
    try {
      const response = await AuthHelpers.authenticatedFetch(
        `${this.baseURL}/backup/jobs/`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch backup jobs: ${response.statusText}`);
      }

      const data = await response.json();
      return data.results || data;
    } catch (error) {
      console.error('Failed to fetch backup jobs:', error);
      throw error;
    }
  }

  /**
   * Create export package
   */
  async createExportPackage(options: {
    include_users?: boolean;
    compress?: boolean;
    encrypt?: boolean;
  } = {}): Promise<Blob> {
    try {
      const response = await AuthHelpers.authenticatedFetch(
        `${this.baseURL}/backup/system/create_export_package/`,
        {
          method: 'POST',
          body: JSON.stringify(options),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.message || `Export failed: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Failed to create export package:', error);
      throw error;
    }
  }

  /**
   * Get system status
   */
  async getSystemStatus(): Promise<any> {
    try {
      const response = await AuthHelpers.authenticatedFetch(
        `${this.baseURL}/backup/system/system_status/`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch system status: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      throw error;
    }
  }

  /**
   * Execute backup configuration
   */
  async executeBackup(configId: number): Promise<any> {
    try {
      const response = await AuthHelpers.authenticatedFetch(
        `${this.baseURL}/backup/configurations/${configId}/execute/`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.message || `Backup execution failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to execute backup:', error);
      throw error;
    }
  }

  /**
   * Upload and restore from backup file
   */
  async uploadAndRestore(file: File, options: {
    restore_type?: string;
    overwrite_existing?: boolean;
  } = {}): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('backup_file', file);
      formData.append('restore_type', options.restore_type || 'full');
      formData.append('overwrite_existing', String(options.overwrite_existing || false));

      const headers = AuthHelpers.getAllAuthHeaders();
      // Don't set Content-Type for FormData - let browser set boundary

      const response = await fetch(`${this.baseURL}/backup/system/restore/`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.message || `Restore failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to upload and restore:', error);
      throw error;
    }
  }

  /**
   * Download backup job
   */
  async downloadBackup(jobId: number): Promise<Blob> {
    try {
      const response = await AuthHelpers.authenticatedFetch(
        `${this.baseURL}/backup/jobs/${jobId}/download/`
      );

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Failed to download backup:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const backupApiService = new BackupApiService();
export default backupApiService;