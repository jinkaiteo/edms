import React, { useState, useCallback } from 'react';
import { PlaceholderDefinition } from '../../types/api';

interface PlaceholderManagementProps {
  className?: string;
}

const PlaceholderManagement: React.FC<PlaceholderManagementProps> = ({ className = '' }) => {
  const [placeholders, setPlaceholders] = useState<PlaceholderDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlaceholder, setSelectedPlaceholder] = useState<PlaceholderDefinition | null>(null);
  const [showCreatePlaceholder, setShowCreatePlaceholder] = useState(false);
  const [showEditPlaceholder, setShowEditPlaceholder] = useState(false);
  const [filter, setFilter] = useState<string>('all');

  // Load placeholders from API
  React.useEffect(() => {
    fetchPlaceholders();
  }, []);

  const fetchPlaceholders = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/placeholders/definitions/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`✅ Successfully fetched ${data.length} placeholders from API`);
        console.log(`🔍 First 3 placeholder types:`, data.slice(0, 3).map(p => p.placeholder_type));
        setPlaceholders(data);
      } else {
        console.error(`❌ Failed to fetch placeholders: ${response.status} ${response.statusText}`);
        // Fallback to mock data
        setPlaceholders(mockPlaceholders);
      }
    } catch (error) {
      console.error('❌ Error fetching placeholders:', error);
      console.log('🔄 Falling back to mock data (5 placeholders)');
      // Fallback to mock data
      setPlaceholders(mockPlaceholders);
    } finally {
      setLoading(false);
    }
  };

  // Mock placeholder data for fallback
  const mockPlaceholders: PlaceholderDefinition[] = [
    {
      id: 1,
      uuid: 'ph-doc-title',
      name: 'DOCUMENT_TITLE',
      display_name: 'Document Title',
      description: 'The title of the current document',
      placeholder_type: 'DOCUMENT',
      data_source: 'DOCUMENT_MODEL',
      source_field: 'title',
      format_string: '{title}',
      date_format: '',
      default_value: 'Untitled Document',
      validation_rules: { required: true, max_length: 200 },
      is_active: true,
      requires_permission: '',
      cache_duration: 0,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
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
      },
      template_syntax: '{{DOCUMENT_TITLE}}'
    },
    {
      id: 2,
      uuid: 'ph-doc-number',
      name: 'DOCUMENT_NUMBER',
      display_name: 'Document Number',
      description: 'Auto-generated document number',
      placeholder_type: 'DOCUMENT',
      data_source: 'DOCUMENT_MODEL',
      source_field: 'document_number',
      format_string: '{document_number}',
      date_format: '',
      default_value: 'DOC-XXXX',
      validation_rules: { required: true, pattern: '^[A-Z]+-\\d+' },
      is_active: true,
      requires_permission: '',
      cache_duration: 0,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
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
      },
      template_syntax: '{{DOCUMENT_NUMBER}}'
    },
    {
      id: 3,
      uuid: 'ph-author-name',
      name: 'AUTHOR_NAME',
      display_name: 'Author Name',
      description: 'Full name of the document author',
      placeholder_type: 'USER',
      data_source: 'USER_MODEL',
      source_field: 'full_name',
      format_string: '{first_name} {last_name}',
      date_format: '',
      default_value: 'Unknown Author',
      validation_rules: { required: true },
      is_active: true,
      requires_permission: '',
      cache_duration: 3600,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
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
      },
      template_syntax: '{{AUTHOR_NAME}}'
    },
    {
      id: 4,
      uuid: 'ph-current-date',
      name: 'CURRENT_DATE',
      display_name: 'Current Date',
      description: 'Current system date',
      placeholder_type: 'DATE',
      data_source: 'COMPUTED',
      source_field: 'now',
      format_string: '{date}',
      date_format: 'YYYY-MM-DD',
      default_value: '2024-01-01',
      validation_rules: { required: true },
      is_active: true,
      requires_permission: '',
      cache_duration: 0,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
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
      },
      template_syntax: '{{CURRENT_DATE}}'
    },
    {
      id: 5,
      uuid: 'ph-workflow-status',
      name: 'WORKFLOW_STATUS',
      display_name: 'Workflow Status',
      description: 'Current workflow state of the document',
      placeholder_type: 'WORKFLOW',
      data_source: 'WORKFLOW_MODEL',
      source_field: 'state_display',
      format_string: '{state_display}',
      date_format: '',
      default_value: 'Draft',
      validation_rules: { required: false },
      is_active: true,
      requires_permission: 'workflow.read',
      cache_duration: 300,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
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
      },
      template_syntax: '{{WORKFLOW_STATUS}}'
    },
    {
      id: 6,
      uuid: 'ph-company-logo',
      name: 'COMPANY_LOGO',
      display_name: 'Company Logo',
      description: 'Company logo image placeholder',
      placeholder_type: 'SYSTEM',
      data_source: 'SYSTEM_CONFIG',
      source_field: 'company_logo_url',
      format_string: '<img src="{company_logo_url}" alt="Company Logo" />',
      date_format: '',
      default_value: '/static/images/default-logo.png',
      validation_rules: { required: false },
      is_active: false,
      requires_permission: 'system.read',
      cache_duration: 86400,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
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
      },
      template_syntax: '{{COMPANY_LOGO}}'
    }
  ];

  // Removed duplicate useEffect that was overriding the API call with mock data

  const handleCreatePlaceholder = useCallback(() => {
    setSelectedPlaceholder(null);
    setShowCreatePlaceholder(true);
  }, []);

  const handleEditPlaceholder = useCallback((placeholder: PlaceholderDefinition) => {
    setSelectedPlaceholder(placeholder);
    setShowEditPlaceholder(true);
  }, []);

  const handleTogglePlaceholder = useCallback((placeholder: PlaceholderDefinition) => {
    const action = placeholder.is_active ? 'deactivate' : 'activate';
    if (window.confirm(`Are you sure you want to ${action} "${placeholder.display_name}"?`)) {
      // TODO: Implement placeholder toggle
      alert(`Placeholder ${action} will be implemented in the backend integration phase.`);
    }
  }, []);

  const getPlaceholderTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      DOCUMENT: 'bg-blue-100 text-blue-800',
      USER: 'bg-green-100 text-green-800',
      WORKFLOW: 'bg-purple-100 text-purple-800',
      SYSTEM: 'bg-orange-100 text-orange-800',
      DATE: 'bg-yellow-100 text-yellow-800',
      CUSTOM: 'bg-gray-100 text-gray-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getPlaceholderTypeIcon = (type: string): string => {
    const icons: Record<string, string> = {
      DOCUMENT: '📄',
      USER: '👤',
      WORKFLOW: '🔄',
      SYSTEM: '⚙️',
      DATE: '📅',
      CUSTOM: '🔧'
    };
    return icons[type] || '📄';
  };

  const filteredPlaceholders = placeholders.filter(placeholder => {
    if (filter === 'all') return true;
    if (filter === 'active') return placeholder.is_active;
    if (filter === 'inactive') return !placeholder.is_active;
    return placeholder.placeholder_type === filter;
  });

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
            <h3 className="text-lg font-semibold text-gray-900">Placeholder Management</h3>
            <p className="text-sm text-gray-500">
              Manage document template placeholders and their data sources
            </p>
          </div>
          <button
            onClick={handleCreatePlaceholder}
            className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Create Placeholder
          </button>
        </div>

        {/* Filters */}
        <div className="flex space-x-2 mb-6">
          {['all', 'active', 'inactive', 'DOCUMENT', 'USER', 'WORKFLOW', 'SYSTEM', 'DATE', 'CUSTOM'].map((filterType) => (
            <button
              key={filterType}
              onClick={() => setFilter(filterType)}
              className={`px-3 py-1 text-xs font-medium rounded-full ${
                filter === filterType
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {filterType === 'all' ? 'All' : filterType.charAt(0).toUpperCase() + filterType.slice(1).toLowerCase()}
            </button>
          ))}
        </div>

        {/* Placeholders List */}
        <div className="space-y-4">
          {filteredPlaceholders.map((placeholder) => (
            <div
              key={placeholder.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="text-2xl">
                    {getPlaceholderTypeIcon(placeholder.placeholder_type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="text-sm font-medium text-gray-900">
                        {placeholder.display_name}
                      </h4>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPlaceholderTypeColor(placeholder.placeholder_type)}`}>
                        {placeholder.placeholder_type}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{placeholder.description}</p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <code className="bg-gray-100 px-2 py-1 rounded">
                        {placeholder.template_syntax}
                      </code>
                      <span>Source: {placeholder.data_source}</span>
                      {placeholder.cache_duration > 0 && (
                        <span>Cache: {placeholder.cache_duration}s</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  {/* Status */}
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    placeholder.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {placeholder.is_active ? 'Active' : 'Inactive'}
                  </span>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEditPlaceholder(placeholder)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleTogglePlaceholder(placeholder)}
                      className={`text-sm hover:underline ${
                        placeholder.is_active 
                          ? 'text-red-600 hover:text-red-800' 
                          : 'text-green-600 hover:text-green-800'
                      }`}
                    >
                      {placeholder.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredPlaceholders.length === 0 && (
          <div className="text-center py-8">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No Placeholders Found</h3>
            <p className="text-gray-500">No placeholders match your current filter.</p>
          </div>
        )}

        {/* Modals */}
        {(showCreatePlaceholder || showEditPlaceholder) && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                {showCreatePlaceholder ? 'Create New Placeholder' : `Edit ${selectedPlaceholder?.display_name}`}
              </h4>
              <div className="space-y-4 mb-6">
                <p className="text-gray-600">
                  Placeholder configuration forms will be implemented in the next iteration.
                </p>
                {selectedPlaceholder && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h5 className="font-medium text-gray-900 mb-3">Current Configuration:</h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Name:</span>
                        <span className="ml-2 text-gray-600">{selectedPlaceholder.name}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Type:</span>
                        <span className="ml-2 text-gray-600">{selectedPlaceholder.placeholder_type}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Data Source:</span>
                        <span className="ml-2 text-gray-600">{selectedPlaceholder.data_source}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Source Field:</span>
                        <span className="ml-2 text-gray-600">{selectedPlaceholder.source_field}</span>
                      </div>
                      <div className="md:col-span-2">
                        <span className="font-medium text-gray-700">Template Syntax:</span>
                        <code className="ml-2 bg-gray-200 px-2 py-1 rounded text-gray-600">
                          {selectedPlaceholder.template_syntax}
                        </code>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreatePlaceholder(false);
                    setShowEditPlaceholder(false);
                    setSelectedPlaceholder(null);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
                <button
                  className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700"
                  onClick={() => alert('Placeholder configuration will be implemented in the next iteration.')}
                >
                  {showCreatePlaceholder ? 'Create' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaceholderManagement;