import React, { useState, useCallback } from 'react';
import { SystemConfiguration, FeatureToggle } from '../../types/api';

interface SystemSettingsProps {
  className?: string;
}

const SystemSettings: React.FC<SystemSettingsProps> = ({ className = '' }) => {
  const [settings, setSettings] = useState<SystemConfiguration[]>([]);
  const [features, setFeatures] = useState<FeatureToggle[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'features' | 'appearance' | 'notifications'>('general');
  const [hasChanges, setHasChanges] = useState(false);

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
            <h3 className="text-lg font-semibold text-gray-900">System Settings</h3>
            <p className="text-sm text-gray-500">
              Configure system-wide settings and feature toggles
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
              { key: 'general', label: 'General' },
              { key: 'security', label: 'Security' },
              { key: 'features', label: 'Features' },
              { key: 'appearance', label: 'Appearance' },
              { key: 'notifications', label: 'Notifications' }
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
        {activeTab === 'features' ? (
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