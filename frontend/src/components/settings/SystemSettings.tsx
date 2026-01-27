import React, { useState, useCallback } from 'react';
import { SystemConfiguration, FeatureToggle } from '../../types/api';

interface SystemSettingsProps {
  className?: string;
}

const SystemSettings: React.FC<SystemSettingsProps> = ({ className = '' }) => {
  const [settings, setSettings] = useState<SystemConfiguration[]>([]);
  const [features, setFeatures] = useState<FeatureToggle[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'features' | 'appearance' | 'notifications'>('notifications'); // Default to the only working tab
  const [hasChanges, setHasChanges] = useState(false);
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  const [testEmailResult, setTestEmailResult] = useState<{ success: boolean; message: string; recipients?: string[] } | null>(null);

  // Mock settings data
  const mockSettings: SystemConfiguration[] = [
    {
      id: 1,
      uuid: 'sys-company-name',
      key: 'company_name',
      display_name: 'Company Name',
      description: 'Name of the organization using the EDMS system',
      category: 'SYSTEM',
      setting_type: 'STRING',
      value: 'EDMS Corporation',
      default_value: 'Your Company',
      validation_rules: { required: true, max_length: 100 },
      allowed_values: [],
      is_sensitive: false,
      requires_restart: false,
      is_user_configurable: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      updated_by: {
        id: 1,
        username: 'admin',
        email: 'admin@edms.local',
        first_name: 'System',
        last_name: 'Administrator',
        is_active: true,
        is_staff: true,
        is_superuser: true,
        date_joined: '2024-01-01T00:00:00Z',
        last_login: '2024-11-22T02:30:00Z',
        full_name: 'System Administrator',
        roles: []
      }
    },
    {
      id: 2,
      uuid: 'sys-session-timeout',
      key: 'session_timeout_minutes',
      display_name: 'Session Timeout (minutes)',
      description: 'User session timeout duration in minutes',
      category: 'SECURITY',
      setting_type: 'INTEGER',
      value: '480',
      default_value: '480',
      validation_rules: { min: 30, max: 1440 },
      allowed_values: [],
      is_sensitive: false,
      requires_restart: true,
      is_user_configurable: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      updated_by: null
    },
    {
      id: 3,
      uuid: 'sys-max-file-size',
      key: 'max_file_size_mb',
      display_name: 'Maximum File Size (MB)',
      description: 'Maximum allowed file size for document uploads',
      category: 'SYSTEM',
      setting_type: 'INTEGER',
      value: '50',
      default_value: '25',
      validation_rules: { min: 1, max: 100 },
      allowed_values: [],
      is_sensitive: false,
      requires_restart: false,
      is_user_configurable: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      updated_by: null
    },
    {
      id: 4,
      uuid: 'sys-email-notifications',
      key: 'enable_email_notifications',
      display_name: 'Enable Email Notifications',
      description: 'Send email notifications for workflow events',
      category: 'NOTIFICATION',
      setting_type: 'BOOLEAN',
      value: 'true',
      default_value: 'false',
      validation_rules: {},
      allowed_values: [],
      is_sensitive: false,
      requires_restart: false,
      is_user_configurable: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      updated_by: null
    },
    {
      id: 5,
      uuid: 'sys-theme-color',
      key: 'primary_theme_color',
      display_name: 'Primary Theme Color',
      description: 'Primary color for the application theme',
      category: 'APPEARANCE',
      setting_type: 'COLOR',
      value: '#3B82F6',
      default_value: '#3B82F6',
      validation_rules: { pattern: '^#[0-9A-Fa-f]{6}$' },
      allowed_values: [],
      is_sensitive: false,
      requires_restart: false,
      is_user_configurable: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      updated_by: null
    },
    {
      id: 6,
      uuid: 'sys-backup-retention',
      key: 'backup_retention_days',
      display_name: 'Backup Retention (days)',
      description: 'Number of days to retain system backups',
      category: 'SYSTEM',
      setting_type: 'INTEGER',
      value: '30',
      default_value: '30',
      validation_rules: { min: 7, max: 365 },
      allowed_values: [],
      is_sensitive: false,
      requires_restart: false,
      is_user_configurable: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      updated_by: null
    }
  ];

  // Mock feature toggles
  const mockFeatures: FeatureToggle[] = [
    {
      id: 1,
      uuid: 'ft-ocr-processing',
      key: 'enable_ocr_processing',
      name: 'OCR Processing',
      description: 'Enable optical character recognition for scanned documents',
      toggle_type: 'RELEASE',
      is_enabled: false,
      conditions: {},
      target_users: [],
      target_roles: [],
      rollout_percentage: 0,
      start_date: null,
      end_date: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      created_by: {
        id: 1,
        username: 'admin',
        email: 'admin@edms.local',
        first_name: 'System',
        last_name: 'Administrator',
        is_active: true,
        is_staff: true,
        is_superuser: true,
        date_joined: '2024-01-01T00:00:00Z',
        last_login: '2024-11-22T02:30:00Z',
        full_name: 'System Administrator',
        roles: []
      }
    },
    {
      id: 2,
      uuid: 'ft-advanced-search',
      key: 'enable_advanced_search',
      name: 'Advanced Search',
      description: 'Enable Elasticsearch-powered advanced search capabilities',
      toggle_type: 'RELEASE',
      is_enabled: true,
      conditions: {},
      target_users: [],
      target_roles: [],
      rollout_percentage: 100,
      start_date: '2024-01-01T00:00:00Z',
      end_date: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      created_by: {
        id: 1,
        username: 'admin',
        email: 'admin@edms.local',
        first_name: 'System',
        last_name: 'Administrator',
        is_active: true,
        is_staff: true,
        is_superuser: true,
        date_joined: '2024-01-01T00:00:00Z',
        last_login: '2024-11-22T02:30:00Z',
        full_name: 'System Administrator',
        roles: []
      }
    },
    {
      id: 3,
      uuid: 'ft-digital-signatures',
      key: 'enable_digital_signatures',
      name: 'Digital Signatures',
      description: 'Enable PKI-based digital signatures for documents',
      toggle_type: 'RELEASE',
      is_enabled: true,
      conditions: {},
      target_users: [],
      target_roles: [],
      rollout_percentage: 100,
      start_date: '2024-01-01T00:00:00Z',
      end_date: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-11-22T02:00:00Z',
      created_by: {
        id: 1,
        username: 'admin',
        email: 'admin@edms.local',
        first_name: 'System',
        last_name: 'Administrator',
        is_active: true,
        is_staff: true,
        is_superuser: true,
        date_joined: '2024-01-01T00:00:00Z',
        last_login: '2024-11-22T02:30:00Z',
        full_name: 'System Administrator',
        roles: []
      }
    }
  ];

  React.useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setSettings(mockSettings);
      setFeatures(mockFeatures);
      setLoading(false);
    }, 800);
  }, []);

  const handleSettingChange = useCallback((settingId: number, newValue: string) => {
    setSettings(prev => prev.map(setting => 
      setting.id === settingId ? { ...setting, value: newValue } : setting
    ));
    setHasChanges(true);
  }, []);

  const handleFeatureToggle = useCallback((featureId: number) => {
    setFeatures(prev => prev.map(feature => 
      feature.id === featureId ? { ...feature, is_enabled: !feature.is_enabled } : feature
    ));
    setHasChanges(true);
  }, []);

  const handleSaveChanges = useCallback(() => {
    // TODO: Implement save functionality
    alert('Settings save functionality will be implemented in the backend integration phase.');
    setHasChanges(false);
  }, []);

  const handleResetToDefaults = useCallback(() => {
    if (window.confirm('Are you sure you want to reset all settings to their default values?')) {
      setSettings(prev => prev.map(setting => ({ ...setting, value: setting.default_value })));
      setHasChanges(true);
    }
  }, []);

  const handleSendTestEmail = useCallback(async () => {
    setSendingTestEmail(true);
    setTestEmailResult(null);

    try {
      // Get JWT token from localStorage (how the app authenticates)
      // The app stores it as 'accessToken', not 'token'
      const token = localStorage.getItem('accessToken') || localStorage.getItem('authToken');
      console.log('🔍 Debug - Token from localStorage:', token ? 'EXISTS' : 'NULL');
      console.log('🔍 Debug - Checked keys: accessToken, authToken');
      
      // Get CSRF token from cookie (fallback for session auth)
      const getCookie = (name: string) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop()?.split(';').shift();
        return null;
      };

      const csrfToken = getCookie('csrftoken');
      console.log('🔍 Debug - CSRF token:', csrfToken ? 'EXISTS' : 'NULL');
      console.log('🔍 Debug - All cookies:', document.cookie);
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      // Add JWT token if available (primary auth method)
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        console.log('✅ Added Authorization header');
      } else {
        console.warn('⚠️ No token found in localStorage!');
      }
      
      // Add CSRF token if available (for session auth)
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
        console.log('✅ Added CSRF header');
      }
      
      console.log('🔍 Debug - Final headers:', headers);
      
      const response = await fetch('/api/v1/settings/email/send-test/', {
        method: 'POST',
        headers: headers,
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok) {
        setTestEmailResult({
          success: data.success,
          message: data.message,
          recipients: data.recipients || [],
        });

        if (data.success) {
          setTimeout(() => setTestEmailResult(null), 10000);
        }
      } else {
        // Handle HTTP errors
        let errorMessage = data.message || 'Failed to send test email';
        
        if (response.status === 401) {
          errorMessage = 'Authentication failed. Please refresh the page and try again.';
        } else if (response.status === 403) {
          errorMessage = 'Permission denied. Admin access required.';
        }

        setTestEmailResult({
          success: false,
          message: errorMessage,
          recipients: [],
        });
      }
    } catch (error: any) {
      setTestEmailResult({
        success: false,
        message: error.message || 'Failed to send test email. Please check your connection.',
        recipients: [],
      });
    } finally {
      setSendingTestEmail(false);
    }
  }, []);

  const getSettingsByCategory = (category: string) => {
    return settings.filter(setting => setting.category === category.toUpperCase());
  };

  const renderSettingInput = (setting: SystemConfiguration) => {
    switch (setting.setting_type) {
      case 'BOOLEAN':
        return (
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={setting.value === 'true'}
              onChange={(e) => handleSettingChange(setting.id, e.target.checked ? 'true' : 'false')}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-900">Enable</span>
          </label>
        );
      case 'INTEGER':
        return (
          <input
            type="number"
            value={setting.value}
            onChange={(e) => handleSettingChange(setting.id, e.target.value)}
            min={setting.validation_rules.min}
            max={setting.validation_rules.max}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        );
      case 'COLOR':
        return (
          <div className="flex items-center space-x-2">
            <input
              type="color"
              value={setting.value}
              onChange={(e) => handleSettingChange(setting.id, e.target.value)}
              className="h-10 w-16 border border-gray-300 rounded"
            />
            <input
              type="text"
              value={setting.value}
              onChange={(e) => handleSettingChange(setting.id, e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              pattern="^#[0-9A-Fa-f]{6}$"
            />
          </div>
        );
      default:
        return (
          <input
            type="text"
            value={setting.value}
            onChange={(e) => handleSettingChange(setting.id, e.target.value)}
            maxLength={setting.validation_rules.max_length}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        );
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Email Notifications</h3>
            <p className="text-sm text-gray-500">
              Configure email notifications and view notification types
            </p>
          </div>
          {hasChanges && (
            <div className="flex space-x-3">
              <button
                onClick={handleResetToDefaults}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Reset to Defaults
              </button>
              <button
                onClick={handleSaveChanges}
                className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700"
              >
                Save Changes
              </button>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex space-x-8" aria-label="Tabs">
            {[
              // Hide non-implemented tabs - only show Notifications (fully functional)
              // { key: 'general', label: 'General' }, // Not implemented
              // { key: 'security', label: 'Security' }, // Not implemented
              // { key: 'features', label: 'Features' }, // Not implemented
              // { key: 'appearance', label: 'Appearance' }, // Not implemented
              { key: 'notifications', label: 'Notifications' } // ✅ Fully functional
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as typeof activeTab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'notifications' ? (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-start">
                <svg className="w-6 h-6 text-blue-600 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <h4 className="text-lg font-semibold text-blue-900 mb-2">Email Notification Configuration</h4>
                  <p className="text-sm text-blue-800 mb-4">
                    Email notifications are configured via environment variables on the server. 
                    To change email settings, you'll need SSH/terminal access to the server.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full mr-3 text-sm font-bold">1</span>
                  Access the Server
                </h4>
                <div className="ml-11 bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-sm text-gray-700 mb-3">Connect to your server via SSH:</p>
                  <code className="block bg-gray-900 text-green-400 px-4 py-3 rounded text-sm font-mono">
                    ssh user@your-server-address
                  </code>
                </div>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full mr-3 text-sm font-bold">2</span>
                  Edit the Environment File
                </h4>
                <div className="ml-11 bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-sm text-gray-700 mb-3">Navigate to the EDMS directory and edit the .env file:</p>
                  <code className="block bg-gray-900 text-green-400 px-4 py-3 rounded text-sm font-mono mb-3">
                    cd /path/to/edms<br/>
                    nano .env
                  </code>
                  <p className="text-sm text-gray-600 mt-2">
                    <strong>Note:</strong> Use <code className="bg-gray-200 px-1 py-0.5 rounded">vim</code> or your preferred text editor if nano is not available.
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full mr-3 text-sm font-bold">3</span>
                  Update Email Configuration
                </h4>
                <div className="ml-11 space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h5 className="font-medium text-gray-900 mb-2">Email Settings to Configure:</h5>
                    <div className="space-y-3 text-sm">
                      <div>
                        <code className="text-blue-600 font-mono">EMAIL_BACKEND</code>
                        <p className="text-gray-600 ml-4">Should be: <code className="bg-gray-200 px-1 rounded">django.core.mail.backends.smtp.EmailBackend</code></p>
                      </div>
                      <div>
                        <code className="text-blue-600 font-mono">EMAIL_HOST</code>
                        <p className="text-gray-600 ml-4">SMTP server address (e.g., smtp.gmail.com, smtp.office365.com)</p>
                      </div>
                      <div>
                        <code className="text-blue-600 font-mono">EMAIL_PORT</code>
                        <p className="text-gray-600 ml-4">Typically: <code className="bg-gray-200 px-1 rounded">587</code> (TLS) or <code className="bg-gray-200 px-1 rounded">465</code> (SSL)</p>
                      </div>
                      <div>
                        <code className="text-blue-600 font-mono">EMAIL_USE_TLS</code>
                        <p className="text-gray-600 ml-4">Set to: <code className="bg-gray-200 px-1 rounded">True</code> for port 587</p>
                      </div>
                      <div>
                        <code className="text-blue-600 font-mono">EMAIL_HOST_USER</code>
                        <p className="text-gray-600 ml-4">Your email address (e.g., notifications@company.com)</p>
                      </div>
                      <div>
                        <code className="text-blue-600 font-mono">EMAIL_HOST_PASSWORD</code>
                        <p className="text-gray-600 ml-4">⚠️ Use app password (not your regular password)</p>
                      </div>
                      <div>
                        <code className="text-blue-600 font-mono">DEFAULT_FROM_EMAIL</code>
                        <p className="text-gray-600 ml-4">Display name and email (e.g., "EDMS System &lt;notifications@company.com&gt;")</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-start">
                      <svg className="w-5 h-5 text-yellow-600 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <div className="flex-1">
                        <h5 className="font-medium text-yellow-900 mb-1">Important: Use App Passwords</h5>
                        <p className="text-sm text-yellow-800 mb-2">
                          Gmail and Microsoft 365 require app-specific passwords when 2FA is enabled:
                        </p>
                        <ul className="text-sm text-yellow-800 space-y-1 ml-4 list-disc">
                          <li><strong>Gmail:</strong> Create at <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline">https://myaccount.google.com/apppasswords</a></li>
                          <li><strong>Microsoft 365:</strong> Create at <a href="https://account.microsoft.com/security" target="_blank" rel="noopener noreferrer" className="underline">https://account.microsoft.com/security</a></li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <h5 className="font-medium text-gray-900 mb-2">Example Configuration:</h5>
                    <pre className="bg-gray-900 text-green-400 px-4 py-3 rounded text-xs font-mono overflow-x-auto">
{`# Gmail Example
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL="EDMS System <your-email@gmail.com>"

# Microsoft 365 Example
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@company.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL="EDMS System <your-email@company.com>"`}
                    </pre>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full mr-3 text-sm font-bold">4</span>
                  Restart the Backend Service
                </h4>
                <div className="ml-11 bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-sm text-gray-700 mb-3">After saving changes, restart the backend to apply new settings:</p>
                  <code className="block bg-gray-900 text-green-400 px-4 py-3 rounded text-sm font-mono">
                    docker compose restart backend celery_worker celery_beat
                  </code>
                  <p className="text-sm text-gray-600 mt-3">
                    This will restart all services that send email notifications.
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full mr-3 text-sm font-bold">5</span>
                  Test Email Configuration
                </h4>
                <div className="ml-11 space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <p className="text-sm text-gray-700 mb-4">
                      Send a test email to verify your configuration is working correctly. 
                      The test email will be sent to all administrator accounts.
                    </p>
                    
                    <button
                      onClick={handleSendTestEmail}
                      disabled={sendingTestEmail}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 
                                 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center
                                 transition-colors duration-200"
                    >
                      {sendingTestEmail ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" 
                               xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" 
                                    stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" 
                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 
                                     7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Sending Test Email...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 
                                     00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                          Send Test Email
                        </>
                      )}
                    </button>
                    
                    {testEmailResult && (
                      <div className={`mt-4 p-4 rounded-lg border ${
                        testEmailResult.success 
                          ? 'bg-green-50 border-green-200' 
                          : 'bg-red-50 border-red-200'
                      }`}>
                        <div className="flex items-start">
                          <div className="flex-shrink-0">
                            {testEmailResult.success ? (
                              <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            ) : (
                              <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>
                          <div className="ml-3 flex-1">
                            <p className={`text-sm font-medium ${
                              testEmailResult.success ? 'text-green-800' : 'text-red-800'
                            }`}>
                              {testEmailResult.message}
                            </p>
                            {testEmailResult.recipients && testEmailResult.recipients.length > 0 && (
                              <p className="text-xs text-green-700 mt-1">
                                Recipients: {testEmailResult.recipients.join(', ')}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Email Notification Types - Merged from emails tab */}
              <div className="border-t pt-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">🔄</span>
                  Workflow Notifications (6 Types)
                </h4>
                <div className="space-y-3 mb-6">
                  {[
                    { event: 'Submit for Review', recipient: 'Reviewer', subject: 'New Task Assigned: REVIEW', when: 'Author submits document' },
                    { event: 'Review Approved', recipient: 'Author', subject: 'Review Approved - Action Required', when: 'Reviewer approves document' },
                    { event: 'Review Rejected', recipient: 'Author', subject: 'Review Rejected - Revision Required', when: 'Reviewer rejects document' },
                    { event: 'Route for Approval', recipient: 'Approver', subject: 'New Task Assigned: APPROVE', when: 'Author routes to approver' },
                    { event: 'Document Approved', recipient: 'Author', subject: 'Document Approved', when: 'Approver approves document' },
                    { event: 'Approval Rejected', recipient: 'Author', subject: 'Document Approval Rejected', when: 'Approver rejects document' },
                  ].map((notif, index) => (
                    <div key={index} className="flex items-start p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex-shrink-0 mr-3">
                        <div className="w-8 h-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm font-semibold">
                          {index + 1}
                        </div>
                      </div>
                      <div className="flex-1">
                        <h5 className="text-sm font-semibold text-gray-900">{notif.event}</h5>
                        <p className="text-xs text-gray-600 mt-1">
                          <strong>When:</strong> {notif.when}<br />
                          <strong>Recipient:</strong> {notif.recipient}<br />
                          <strong>Subject:</strong> {notif.subject}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">🤖</span>
                  Automated System Notifications (6 Types)
                </h4>
                <div className="space-y-3">
                  {[
                    { event: 'Document Becomes Effective', recipient: 'Author', subject: 'Document Now Effective', when: 'Scheduled effective date arrives' },
                    { event: 'Scheduled for Obsolescence', recipient: 'Author & Stakeholders', subject: 'Document Scheduled for Obsolescence', when: 'Obsolescence is scheduled' },
                    { event: 'Document Becomes Obsolete', recipient: 'Author & Stakeholders', subject: 'Document Now Obsolete', when: 'Obsolescence date arrives' },
                    { event: 'Document Superseded', recipient: 'Users of old version', subject: 'Document Superseded', when: 'New version replaces old' },
                    { event: 'Workflow Timeout', recipient: 'Current Assignee', subject: 'Overdue Workflow', when: 'Task is overdue' },
                    { event: 'Daily Health Report', recipient: 'All Admins', subject: 'EDMS Daily Health Report', when: 'Every day at 7:00 AM' },
                  ].map((notif, index) => (
                    <div key={index} className="flex items-start p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex-shrink-0 mr-3">
                        <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                          {index + 1}
                        </div>
                      </div>
                      <div className="flex-1">
                        <h5 className="text-sm font-semibold text-gray-900">{notif.event}</h5>
                        <p className="text-xs text-gray-600 mt-1">
                          <strong>When:</strong> {notif.when}<br />
                          <strong>Recipient:</strong> {notif.recipient}<br />
                          <strong>Subject:</strong> {notif.subject}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Troubleshooting Section */}
              <div className="border-t pt-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">🔧</span>
                  Troubleshooting
                </h4>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h5 className="text-sm font-semibold text-yellow-900 mb-2">Not Receiving Emails?</h5>
                  <ul className="text-sm text-yellow-800 space-y-2 ml-4 list-disc">
                    <li><strong>Check Spam Folder:</strong> Gmail often flags system emails as spam</li>
                    <li><strong>Verify Email Address:</strong> Ensure your user profile has a valid email</li>
                    <li><strong>Check SMTP Configuration:</strong> Review the configuration steps above</li>
                    <li><strong>Test Email Delivery:</strong> Use the "Send Test Email" task in Scheduler</li>
                    <li><strong>Contact Administrator:</strong> If issues persist, contact your system admin</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        ) : activeTab === 'features' ? (
          <div className="space-y-4">
            <h4 className="text-md font-medium text-gray-900 mb-4">Feature Toggles</h4>
            {features.map((feature) => (
              <div key={feature.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h5 className="text-sm font-medium text-gray-900">{feature.name}</h5>
                    <p className="text-sm text-gray-600 mt-1">{feature.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>Type: {feature.toggle_type}</span>
                      <span>Rollout: {feature.rollout_percentage}%</span>
                    </div>
                  </div>
                  <label className="flex items-center ml-4">
                    <input
                      type="checkbox"
                      checked={feature.is_enabled}
                      onChange={() => handleFeatureToggle(feature.id)}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-900">
                      {feature.is_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </label>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-6">
            {getSettingsByCategory(activeTab).map((setting) => (
              <div key={setting.id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-900">
                      {setting.display_name}
                      {setting.validation_rules.required && (
                        <span className="text-red-500 ml-1">*</span>
                      )}
                    </label>
                    <p className="text-sm text-gray-600 mt-1">{setting.description}</p>
                  </div>
                  {setting.requires_restart && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Requires Restart
                    </span>
                  )}
                </div>
                <div className="mt-2">
                  {renderSettingInput(setting)}
                </div>
                {setting.value !== setting.default_value && (
                  <p className="text-xs text-gray-500">
                    Default: {setting.default_value}
                  </p>
                )}
              </div>
            ))}

            {getSettingsByCategory(activeTab).length === 0 && (
              <div className="text-center py-8">
                <div className="text-gray-400 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-1">No Settings Available</h3>
                <p className="text-gray-500">No settings are configured for this category.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemSettings;