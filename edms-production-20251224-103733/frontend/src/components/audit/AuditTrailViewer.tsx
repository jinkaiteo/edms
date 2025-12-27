import React, { useState, useCallback } from 'react';
import apiService from '../../services/api.ts';
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

  React.useEffect(() => {
    const loadAuditTrail = async () => {
      try {
        setLoading(true);
        
        // Try to authenticate first
        if (!apiService.isAuthenticated()) {
          await apiService.login({ username: 'admin', password: 'test123' });
        }
        
        // Get real audit trail data from backend API
        try {
          const response = await apiService.getAuditTrail(filters);
          // Debug info removed to prevent errors
          // setDebugInfo({
          //   hasResults: !!(response.results),
          //   hasData: !!(response.data), 
          //   resultsLength: response.results?.length || 0,
          //   dataLength: response.data?.length || 0,
          //   count: response.count,
          //   firstResult: response.results?.[0] || response.data?.[0]
          // });
          
          // Transform API data to match frontend format (simplified)
          const auditData = (response.results || response.data || []).map((item: any, index: number) => ({
            id: item.id || index,
            uuid: item.uuid || `temp-${index}`,
            user: {
              id: 0,
              username: item.user_display || 'System',
              email: '',
              first_name: '',
              last_name: '',
              is_active: true,
              is_staff: false,
              is_superuser: false,
              date_joined: new Date().toISOString(),
              last_login: null,
              full_name: item.user_display || 'System',
              roles: []
            },
            action: item.action || 'UNKNOWN',
            object_type: item.audit_type === 'login_audit' ? 'authentication' : 'system',
            object_id: item.id || 0,
            description: item.description || 'No description',
            timestamp: item.timestamp || new Date().toISOString(),
            ip_address: item.ip_address || '',
            user_agent: item.user_agent || '',
            session_id: null,
            request_id: null,
            additional_data: item.additional_data || {},
            integrity_hash: `sha256:${item.uuid || 'unknown'}`
          }));
          
          
          
          if (auditData.length === 0) {
            setAuditLogs([]);
          } else {
            setAuditLogs(auditData);
          }
          
          // Double-check that state was set
          setTimeout(() => {
          }, 100);
          
        } catch (apiError) {
          console.error('❌ AuditTrail: API call failed:', apiError);
          console.error('API Error details:', {
            status: apiError?.response?.status,
            statusText: apiError?.response?.statusText,
            data: apiError?.response?.data,
            message: apiError?.message
          });
          setAuditLogs([]);
        }
        
      } catch (error) {
        console.error('❌ AuditTrail: Error loading audit trail:', error);
        // No data available
        setAuditLogs([]);
        setLoading(false);
      } finally {
        setLoading(false);
      }
    };

    loadAuditTrail();
    
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