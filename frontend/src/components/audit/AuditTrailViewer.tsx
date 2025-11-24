import React, { useState, useCallback, useEffect } from 'react';
// import apiService from '../../services/api'; // Temporarily disabled
import { AuditTrail } from '../../types/api';

interface AuditTrailViewerProps {
  className?: string;
}

const AuditTrailViewer: React.FC<AuditTrailViewerProps> = ({ className = '' }) => {
  const [auditLogs, setAuditLogs] = useState<AuditTrail[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    search: '',
    action: '',
    user: '',
    object_type: '',
    date_from: '',
    date_to: '',
    page: 1,
    page_size: 20
  });

  // Real audit data will be loaded from backend
  const mockAuditLogs: AuditTrail[] = [
    {
      id: 1,
      uuid: 'audit-001',
      user: {
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
      action: 'LOGIN_SUCCESS',
      object_type: 'user',
      object_id: 1,
      description: 'User successfully logged in to the system',
      timestamp: '2024-11-22T02:30:15Z',
      ip_address: '192.168.1.100',
      user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      session_id: 'session_12345',
      request_id: 'req_67890',
      additional_data: {
        login_method: 'username_password',
        success: true,
        location: 'Main Office'
      },
      integrity_hash: 'sha256:abcdef123456...'
    },
    {
      id: 2,
      uuid: 'audit-002',
      user: {
        id: 2,
        username: 'author',
        email: 'author@edms.local',
        first_name: 'Document',
        last_name: 'Author',
        is_active: true,
        is_staff: false,
        is_superuser: false,
        date_joined: '2024-01-01T00:00:00Z',
        last_login: '2024-11-21T08:00:00Z',
        full_name: 'Document Author',
        roles: []
      },
      action: 'DOCUMENT_CREATE',
      object_type: 'document',
      object_id: 123,
      description: 'New document created: Quality Manual v2.1',
      timestamp: '2024-11-22T01:45:30Z',
      ip_address: '192.168.1.105',
      user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      session_id: 'session_54321',
      request_id: 'req_09876',
      additional_data: {
        document_title: 'Quality Manual v2.1',
        document_type: 'Policy',
        file_size: 2048000,
        document_number: 'POL-001-v2.1'
      },
      integrity_hash: 'sha256:fedcba654321...'
    },
    {
      id: 3,
      uuid: 'audit-003',
      user: {
        id: 3,
        username: 'reviewer',
        email: 'reviewer@edms.local',
        first_name: 'Document',
        last_name: 'Reviewer',
        is_active: true,
        is_staff: false,
        is_superuser: false,
        date_joined: '2024-01-01T00:00:00Z',
        last_login: '2024-11-21T10:00:00Z',
        full_name: 'Document Reviewer',
        roles: []
      },
      action: 'WORKFLOW_TRANSITION',
      object_type: 'workflow',
      object_id: 456,
      description: 'Document moved to review state: SOP-001-v2.1',
      timestamp: '2024-11-22T01:15:22Z',
      ip_address: '192.168.1.110',
      user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101',
      session_id: 'session_98765',
      request_id: 'req_13579',
      additional_data: {
        document_number: 'SOP-001-v2.1',
        from_state: 'pending_review',
        to_state: 'under_review',
        workflow_type: 'REVIEW',
        reason: 'Starting document review process'
      },
      integrity_hash: 'sha256:123456abcdef...'
    },
    {
      id: 4,
      uuid: 'audit-004',
      user: {
        id: 4,
        username: 'approver',
        email: 'approver@edms.local',
        first_name: 'Document',
        last_name: 'Approver',
        is_active: true,
        is_staff: false,
        is_superuser: false,
        date_joined: '2024-01-01T00:00:00Z',
        last_login: '2024-11-20T16:00:00Z',
        full_name: 'Document Approver',
        roles: []
      },
      action: 'DOCUMENT_SIGN',
      object_type: 'electronic_signature',
      object_id: 789,
      description: 'Document electronically signed: POL-001-v1.0',
      timestamp: '2024-11-22T00:45:18Z',
      ip_address: '192.168.1.115',
      user_agent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
      session_id: 'session_24680',
      request_id: 'req_97531',
      additional_data: {
        document_number: 'POL-001-v1.0',
        signature_type: 'APPROVAL',
        signature_method: 'PKI_DIGITAL',
        certificate_serial: 'CERT-001-2024',
        reason: 'Final approval for policy document'
      },
      integrity_hash: 'sha256:987654321abc...'
    },
    {
      id: 5,
      uuid: 'audit-005',
      user: null,
      action: 'SYSTEM_BACKUP',
      object_type: 'system',
      object_id: null,
      description: 'Automated system backup completed successfully',
      timestamp: '2024-11-22T00:00:05Z',
      ip_address: null,
      user_agent: 'EDMS-BackupService/1.0',
      session_id: null,
      request_id: 'backup_123456',
      additional_data: {
        backup_type: 'automated',
        backup_size_mb: 1024,
        backup_location: '/backups/edms_20241122_000005.sql.gz',
        duration_seconds: 45,
        status: 'success'
      },
      integrity_hash: 'sha256:backup123456...'
    },
    {
      id: 6,
      uuid: 'audit-006',
      user: {
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
      action: 'USER_CREATE',
      object_type: 'user',
      object_id: 5,
      description: 'New user account created: newuser@edms.local',
      timestamp: '2024-11-21T23:30:42Z',
      ip_address: '192.168.1.100',
      user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      session_id: 'session_admin_001',
      request_id: 'req_user_create_001',
      additional_data: {
        new_user_email: 'newuser@edms.local',
        new_user_username: 'newuser',
        assigned_roles: ['Document Author'],
        account_active: true
      },
      integrity_hash: 'sha256:newuser123456...'
    }
  ];

  React.useEffect(() => {
    const loadAuditTrail = async () => {
      try {
        setLoading(true);
        // API service temporarily disabled - will show empty state
        console.log('Loading real audit data - currently showing empty state until API integration');
        
        // Show empty state if no real data
        setAuditLogs([]);
        setLoading(false);
      } catch (error) {
        console.error('Error loading audit trail:', error);
        setAuditLogs([]);
        setLoading(false);
      }
    };

    loadAuditTrail();
    
    // Legacy mock data code (now replaced with real data loading)
    /*
    setTimeout(() => {
      let filteredLogs = [];
      
      // Apply filters
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        filteredLogs = filteredLogs.filter(log => 
          log.description.toLowerCase().includes(searchTerm) ||
          log.action.toLowerCase().includes(searchTerm) ||
          (log.user && log.user.username.toLowerCase().includes(searchTerm))
        );
      }
      
      if (filters.action) {
        filteredLogs = filteredLogs.filter(log => log.action === filters.action);
      }
      
      if (filters.user) {
        filteredLogs = filteredLogs.filter(log => 
          log.user && log.user.username === filters.user
        );
      }
      
      if (filters.object_type) {
        filteredLogs = filteredLogs.filter(log => log.object_type === filters.object_type);
      }
      
      setAuditLogs(filteredLogs);
      setLoading(false);
    }, 1000);
    */
  }, [filters]);

  const handleFilterChange = useCallback((key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  }, []);

  const getActionColor = (action: string): string => {
    const colors: Record<string, string> = {
      LOGIN_SUCCESS: 'bg-green-100 text-green-800',
      LOGIN_FAILURE: 'bg-red-100 text-red-800',
      DOCUMENT_CREATE: 'bg-blue-100 text-blue-800',
      DOCUMENT_UPDATE: 'bg-yellow-100 text-yellow-800',
      DOCUMENT_DELETE: 'bg-red-100 text-red-800',
      DOCUMENT_SIGN: 'bg-purple-100 text-purple-800',
      WORKFLOW_TRANSITION: 'bg-indigo-100 text-indigo-800',
      USER_CREATE: 'bg-green-100 text-green-800',
      USER_UPDATE: 'bg-yellow-100 text-yellow-800',
      USER_DELETE: 'bg-red-100 text-red-800',
      SYSTEM_BACKUP: 'bg-gray-100 text-gray-800',
      SYSTEM_ERROR: 'bg-red-100 text-red-800'
    };
    return colors[action] || 'bg-gray-100 text-gray-800';
  };

  const getActionIcon = (action: string): string => {
    const icons: Record<string, string> = {
      LOGIN_SUCCESS: '🔐',
      LOGIN_FAILURE: '❌',
      DOCUMENT_CREATE: '📄',
      DOCUMENT_UPDATE: '✏️',
      DOCUMENT_DELETE: '🗑️',
      DOCUMENT_SIGN: '✍️',
      WORKFLOW_TRANSITION: '🔄',
      USER_CREATE: '👤',
      USER_UPDATE: '👥',
      USER_DELETE: '❌',
      SYSTEM_BACKUP: '💾',
      SYSTEM_ERROR: '⚠️'
    };
    return icons[action] || '📋';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-20 bg-gray-200 rounded"></div>
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
            <h3 className="text-lg font-semibold text-gray-900">Audit Trail</h3>
            <p className="text-sm text-gray-500">
              View system activities and compliance logs
            </p>
          </div>
          <div className="text-sm text-gray-500">
            {auditLogs.length} {auditLogs.length === 1 ? 'entry' : 'entries'}
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div>
            <input
              type="text"
              placeholder="Search activities..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <select
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Actions</option>
              <option value="LOGIN_SUCCESS">Login Success</option>
              <option value="DOCUMENT_CREATE">Document Create</option>
              <option value="DOCUMENT_SIGN">Document Sign</option>
              <option value="WORKFLOW_TRANSITION">Workflow</option>
              <option value="USER_CREATE">User Create</option>
              <option value="SYSTEM_BACKUP">System Backup</option>
            </select>
          </div>
          <div>
            <select
              value={filters.user}
              onChange={(e) => handleFilterChange('user', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Users</option>
              <option value="admin">admin</option>
              <option value="author">author</option>
              <option value="reviewer">reviewer</option>
              <option value="approver">approver</option>
            </select>
          </div>
          <div>
            <select
              value={filters.object_type}
              onChange={(e) => handleFilterChange('object_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Objects</option>
              <option value="document">Document</option>
              <option value="user">User</option>
              <option value="workflow">Workflow</option>
              <option value="system">System</option>
            </select>
          </div>
          <div>
            <button
              onClick={() => setFilters({
                search: '', action: '', user: '', object_type: '', date_from: '', date_to: '', page: 1, page_size: 20
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Audit Log Entries */}
        <div className="space-y-4">
          {auditLogs.map((log) => (
            <div
              key={log.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <div className="text-2xl">{getActionIcon(log.action)}</div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionColor(log.action)}`}>
                      {log.action.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-gray-500">
                      {formatDate(log.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-900 mb-2">{log.description}</p>
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>User: {log.user ? log.user.username : 'System'}</span>
                    {log.ip_address && <span>IP: {log.ip_address}</span>}
                    {log.object_type && <span>Type: {log.object_type}</span>}
                    {log.integrity_hash && (
                      <span title={log.integrity_hash}>
                        Hash: {log.integrity_hash.substring(0, 16)}...
                      </span>
                    )}
                  </div>
                  {/* Additional Data */}
                  {Object.keys(log.additional_data).length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                        View Details
                      </summary>
                      <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                        <pre className="whitespace-pre-wrap text-gray-700">
                          {JSON.stringify(log.additional_data, null, 2)}
                        </pre>
                      </div>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Legacy empty state - now handled above */}
        {false && auditLogs.length === 0 && (
          <div className="text-center py-8">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No Audit Entries Found</h3>
            <p className="text-gray-500">No audit entries match your current filters.</p>
          </div>
        )}

        {/* Export Options */}
        <div className="mt-6 flex justify-end space-x-2">
          <button
            onClick={() => alert('Export functionality will be implemented in the backend integration phase.')}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Export CSV
          </button>
          <button
            onClick={() => alert('Export functionality will be implemented in the backend integration phase.')}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Export PDF
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuditTrailViewer;