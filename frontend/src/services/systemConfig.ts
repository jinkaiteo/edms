/**
 * System Configuration Service
 * Handles logo upload, company branding, and system settings
 */
import { apiService } from './api.ts';

export interface SystemConfig {
  company_name: string;
  logo_url: string | null;
  has_logo: boolean;
  updated_at: string;
}

export interface UploadLogoResponse {
  message: string;
  logo_url: string;
  updated_at: string;
}

export const systemConfigService = {
  /**
   * Get current system configuration
   */
  async getConfig(): Promise<SystemConfig> {
    return await apiService.get('/system/config/');
  },

  /**
   * Upload company logo
   * @param file - Logo file (PNG/JPG, max 2MB)
   */
  async uploadLogo(file: File): Promise<UploadLogoResponse> {
    const formData = new FormData();
    formData.append('logo', file);
    
    return await apiService.post('/system/config/logo/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Delete company logo
   */
  async deleteLogo(): Promise<{ message: string }> {
    return await apiService.delete('/system/config/logo/delete/');
  },

  /**
   * Update company name
   */
  async updateCompanyName(companyName: string): Promise<{ message: string; company_name: string }> {
    return await apiService.put('/system/config/company-name/', {
      company_name: companyName,
    });
  },
};
