import React, { useState, useEffect } from 'react';
import { Document, DocumentStatus } from '../../types/api';
import { apiService } from '../../services/api.ts';

interface DocumentListProps {
  onDocumentSelect?: (document: Document) => void;
  onDocumentEdit?: (document: Document) => void;
  onDocumentDelete?: (document: Document) => void;
  filters?: {
    status?: DocumentStatus;
    document_type?: number;
    search?: string;
  };
  className?: string;
}

const DocumentList: React.FC<DocumentListProps> = ({
  onDocumentSelect,
  onDocumentEdit,
  onDocumentDelete,
  filters,
  className = ''
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [sortBy, setSortBy] = useState<'title' | 'created_at' | 'status' | 'document_type'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [showObsolete, setShowObsolete] = useState(false);

  // Helper function to extract base document number (remove version suffix)
  const getBaseDocumentNumber = (documentNumber: string): string => {
    if (documentNumber.includes('-v')) {
      return documentNumber.split('-v')[0];
    }
    return documentNumber;
  };

  // Helper function to group documents by base number
  const groupDocumentsByBase = (docs: Document[]) => {
    const groups: { [key: string]: Document[] } = {};
    
    docs.forEach(doc => {
      const baseNumber = getBaseDocumentNumber(doc.document_number);
      if (!groups[baseNumber]) {
        groups[baseNumber] = [];
      }
      groups[baseNumber].push(doc);
    });

    // Sort each group by version (newest first)
    Object.keys(groups).forEach(baseNumber => {
      groups[baseNumber].sort((a, b) => {
        // Extract version numbers for proper sorting
        const getVersionNumber = (docNum: string) => {
          const versionMatch = docNum.match(/-v(\d+)\.(\d+)$/);
          if (versionMatch) {
            return { major: parseInt(versionMatch[1]), minor: parseInt(versionMatch[2]) };
          }
          return { major: 1, minor: 0 }; // Default version
        };

        const versionA = getVersionNumber(a.document_number);
        const versionB = getVersionNumber(b.document_number);
        
        if (versionA.major !== versionB.major) {
          return versionB.major - versionA.major; // Newer major version first
        }
        return versionB.minor - versionA.minor; // Newer minor version first
      });
    });

    return groups;
  };

  const toggleGroupExpansion = (baseNumber: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(baseNumber)) {
      newExpanded.delete(baseNumber);
    } else {
      newExpanded.add(baseNumber);
    }
    setExpandedGroups(newExpanded);
  };



  // Mock documents for demonstration (keeping for potential fallback)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const mockDocuments: Document[] = [
    {
      id: 1,
      uuid: '550e8400-e29b-41d4-a716-446655440001',
      document_number: 'POL-001-v1.0',
      title: 'Quality Management Policy',
      description: 'Company-wide quality management policy document outlining standards and procedures.',
      document_type: {
        id: 1,
        name: 'Policy',
        description: 'Company policies',
        prefix: 'POL',
        is_active: true,
        workflow_required: true,
        retention_period: null,
        template: null
      },
      status: 'effective',
      version: '1.0',
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
        last_login: '2024-11-22T02:00:00Z',
        full_name: 'System Administrator',
        roles: []
      },
      created_at: '2024-11-20T10:00:00Z',
      updated_at: '2024-11-20T10:00:00Z',
      effective_date: '2024-11-21T00:00:00Z',
      review_date: '2025-11-21T00:00:00Z',
      obsolete_date: null,
      file_path: '/documents/pol-001-v1.0.pdf',
      file_size: 2048000,
      file_checksum: 'sha256:abc123...',
      metadata: { department: 'Quality Assurance', priority: 'high' },
      dependencies: [],
      workflow_state: 'effective'
    },
    {
      id: 2,
      uuid: '550e8400-e29b-41d4-a716-446655440002',
      document_number: 'SOP-001-v2.1',
      title: 'Document Control Standard Operating Procedure',
      description: 'Detailed procedures for document creation, review, approval, and management.',
      document_type: {
        id: 2,
        name: 'SOP',
        description: 'Standard Operating Procedures',
        prefix: 'SOP',
        is_active: true,
        workflow_required: true,
        retention_period: null,
        template: null
      },
      status: 'pending_review',
      version: '2.1',
      created_by: {
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
      created_at: '2024-11-21T14:30:00Z',
      updated_at: '2024-11-21T14:30:00Z',
      effective_date: null,
      review_date: null,
      obsolete_date: null,
      file_path: '/documents/sop-001-v2.1.docx',
      file_size: 1536000,
      file_checksum: 'sha256:def456...',
      metadata: { department: 'Quality Assurance', priority: 'medium' },
      dependencies: [],
      workflow_state: 'pending_review'
    },
    {
      id: 3,
      uuid: '550e8400-e29b-41d4-a716-446655440003',
      document_number: 'MAN-001-v1.0',
      title: 'User Training Manual',
      description: 'Comprehensive training manual for new users of the EDMS system.',
      document_type: {
        id: 3,
        name: 'Manual',
        description: 'User manuals',
        prefix: 'MAN',
        is_active: true,
        workflow_required: false,
        retention_period: null,
        template: null
      },
      status: 'draft',
      version: '1.0',
      created_by: {
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
      created_at: '2024-11-22T09:15:00Z',
      updated_at: '2024-11-22T09:15:00Z',
      effective_date: null,
      review_date: null,
      obsolete_date: null,
      file_path: '/documents/man-001-v1.0.pdf',
      file_size: 3072000,
      file_checksum: 'sha256:ghi789...',
      metadata: { department: 'Training', priority: 'low' },
      dependencies: [],
      workflow_state: 'draft'
    }
  ];

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);

    try {
      // Use real API call to fetch documents from backend
      const documentsData = await apiService.get('/documents/documents/');
      
      // API response should be array of documents or wrapped in a data property
      const documentsArray = Array.isArray(documentsData) ? documentsData : (documentsData.results || documentsData.data || []);
      let filteredDocs = [...documentsArray];
      
      // Apply filters
      
      // Only filter if status has actual value (not empty array)
      if (filters?.status && filters.status.length > 0) {
        filteredDocs = filteredDocs.filter(doc => doc.status.toLowerCase() === filters.status.toLowerCase());
      } else {
      }
      
      // Only filter if document_type has actual value (not empty array)  
      if (filters?.document_type && filters.document_type.length > 0) {
        filteredDocs = filteredDocs.filter(doc => doc.document_type?.id === filters.document_type);
      } else {
      }
      
      if (filters?.search) {
        const searchTerm = filters.search.toLowerCase();
        filteredDocs = filteredDocs.filter(doc => 
          doc.title?.toLowerCase().includes(searchTerm) ||
          doc.description?.toLowerCase().includes(searchTerm) ||
          doc.document_number?.toLowerCase().includes(searchTerm)
        );
      }
      
      // Apply sorting
      filteredDocs.sort((a, b) => {
        let aValue: any;
        let bValue: any;
        
        switch (sortBy) {
          case 'title':
            aValue = a.title.toLowerCase();
            bValue = b.title.toLowerCase();
            break;
          case 'created_at':
            aValue = new Date(a.created_at);
            bValue = new Date(b.created_at);
            break;
          case 'status':
            aValue = a.status;
            bValue = b.status;
            break;
          case 'document_type':
            aValue = a.document_type_display || '';
            bValue = b.document_type_display || '';
            break;
          default:
            return 0;
        }
        
        if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
      
      setDocuments(filteredDocs);
    } catch (error: any) {
      console.error('Failed to load documents:', error);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [filters]);

  // Listen for document updates from other components
  useEffect(() => {
    const handleDocumentUpdate = (event: CustomEvent) => {
      console.log('📄 Document update event received, refreshing list...');
      loadDocuments();
    };

    window.addEventListener('documentUpdated', handleDocumentUpdate as EventListener);
    
    return () => {
      window.removeEventListener('documentUpdated', handleDocumentUpdate as EventListener);
    };
  }, []);

  const getStatusColor = (status: DocumentStatus): string => {
    const colors: Record<DocumentStatus, string> = {
      draft: 'bg-gray-100 text-gray-800',
      pending_review: 'bg-yellow-100 text-yellow-800',
      under_review: 'bg-blue-100 text-blue-800',
      review_completed: 'bg-purple-100 text-purple-800',
      pending_approval: 'bg-orange-100 text-orange-800',
      approved: 'bg-green-100 text-green-800',
      effective: 'bg-green-100 text-green-800',
      superseded: 'bg-gray-100 text-gray-800',
      obsolete: 'bg-red-100 text-red-800',
      terminated: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status: DocumentStatus): string => {
    const icons: Record<DocumentStatus, string> = {
      draft: '📝',
      pending_review: '⏳',
      under_review: '👀',
      review_completed: '✅',
      pending_approval: '⌛',
      approved: '👍',
      effective: '🟢',
      superseded: '📋',
      obsolete: '🗑️',
      terminated: '❌'
    };
    return icons[status] || '📄';
  };

  const formatFileSize = (bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleSort = (field: typeof sortBy) => {
    if (field === sortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-red-200 ${className}`}>
        <div className="p-6 text-center">
          <div className="text-red-500 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">Error Loading Documents</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <button
            onClick={loadDocuments}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Try Again
          </button>
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
            <h3 className="text-lg font-semibold text-gray-900">Documents</h3>
            <p className="text-sm text-gray-500">
              {documents.length} {documents.length === 1 ? 'document' : 'documents'}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Sort dropdown */}
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field as typeof sortBy);
                setSortOrder(order as 'asc' | 'desc');
              }}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="created_at-desc">Newest First</option>
              <option value="created_at-asc">Oldest First</option>
              <option value="title-asc">Title A-Z</option>
              <option value="title-desc">Title Z-A</option>
              <option value="status-asc">Status A-Z</option>
              <option value="document_type-asc">Type A-Z</option>
            </select>
            
            {/* Show Obsolete Toggle */}
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showObsolete}
                onChange={(e) => setShowObsolete(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
              />
              <span className="text-sm font-medium text-gray-700">
                Show Obsolete ({documents.filter(doc => doc.status === 'OBSOLETE').length})
              </span>
            </label>

            {/* View mode toggle */}
            <div className="flex border border-gray-300 rounded-md">
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 text-sm ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-50'}`}
              >
                List
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 text-sm ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-50'}`}
              >
                Grid
              </button>
            </div>
          </div>
        </div>

        
        {/* Documents display */}
        {documents.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No Documents Found</h3>
            <p className="text-gray-500">No documents match your current filters.</p>
          </div>
        ) : viewMode === 'list' ? (
          // Grouped list view with version history
          (() => {
            // Filter documents based on obsolete toggle
            const filteredDocuments = showObsolete 
              ? documents 
              : documents.filter(doc => doc.status !== 'OBSOLETE');

            // Group filtered documents and get current versions for sorting
            const documentGroups = groupDocumentsByBase(filteredDocuments);
            const groupKeys = Object.keys(documentGroups);

            // Sort groups by the current (newest) version's properties
            const sortedGroupKeys = groupKeys.sort((a, b) => {
              const currentDocA = documentGroups[a][0]; // First item is newest due to our sorting
              const currentDocB = documentGroups[b][0];

              let aValue: any, bValue: any;

              switch (sortBy) {
                case 'title':
                  aValue = currentDocA.title.toLowerCase();
                  bValue = currentDocB.title.toLowerCase();
                  break;
                case 'created_at':
                  aValue = new Date(currentDocA.created_at);
                  bValue = new Date(currentDocB.created_at);
                  break;
                case 'status':
                  aValue = currentDocA.status.toLowerCase();
                  bValue = currentDocB.status.toLowerCase();
                  break;
                case 'document_type':
                  aValue = currentDocA.document_type_display?.toLowerCase() || '';
                  bValue = currentDocB.document_type_display?.toLowerCase() || '';
                  break;
                default:
                  return 0;
              }

              if (sortOrder === 'asc') {
                return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
              } else {
                return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
              }
            });

            return (
              <div className="space-y-4">
                {sortedGroupKeys.map((baseNumber) => {
              const groupDocuments = documentGroups[baseNumber];
              const currentVersion = groupDocuments[0]; // Newest version
              const olderVersions = groupDocuments.slice(1); // Superseded versions
              const isExpanded = expandedGroups.has(baseNumber);

              return (
                <div key={baseNumber} className="border border-gray-200 rounded-lg">
                  {/* Current Version */}
                  <div
                    className="p-4 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => onDocumentSelect?.(currentVersion)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-2xl">{getStatusIcon(currentVersion.status)}</span>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-gray-900 truncate">
                              {currentVersion.title}
                            </h4>
                            <p className="text-sm text-gray-500">
                              {currentVersion.document_number} • {currentVersion.document_type_display || 'Unknown Type'}
                              {currentVersion.status === 'APPROVED_AND_EFFECTIVE' && (
                                <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Current Version
                                </span>
                              )}
                            </p>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                          {currentVersion.description}
                        </p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>Status: {currentVersion.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                          {currentVersion.author_display && (
                            <span>Author: {currentVersion.author_display}</span>
                          )}
                          <span>Created: {formatDate(currentVersion.created_at)}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {onDocumentEdit && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDocumentEdit(currentVersion);
                            }}
                            className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                          >
                            Edit
                          </button>
                        )}
                        {onDocumentDelete && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDocumentDelete(currentVersion);
                            }}
                            className="text-red-600 hover:text-red-900 text-sm font-medium"
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Version History Toggle */}
                  {olderVersions.length > 0 && (
                    <div className="border-t border-gray-100">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleGroupExpansion(baseNumber);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-gray-600 hover:bg-gray-50 flex items-center justify-between"
                      >
                        <span>
                          {olderVersions.length} previous version{olderVersions.length !== 1 ? 's' : ''}
                        </span>
                        <svg
                          className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      {/* Previous Versions */}
                      {isExpanded && (
                        <div className="border-t border-gray-100 bg-gray-50">
                          {olderVersions.map((oldVersion, index) => (
                            <div
                              key={oldVersion.id || oldVersion.uuid}
                              className="px-4 py-3 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                              onClick={(e) => {
                                e.stopPropagation();
                                onDocumentSelect?.(oldVersion);
                              }}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-sm font-medium text-gray-700">
                                      {oldVersion.document_number}
                                    </span>
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-200 text-gray-700">
                                      {oldVersion.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-500 mt-1">
                                    Created: {formatDate(oldVersion.created_at)}
                                    {oldVersion.author_display && ` • Author: ${oldVersion.author_display}`}
                                  </p>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onDocumentSelect?.(oldVersion);
                                    }}
                                    className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                                  >
                                    View
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
              </div>
            );
          })()
        ) : (
          // Grid view
          (() => {
            const filteredDocuments = showObsolete 
              ? documents 
              : documents.filter(doc => doc.status !== 'OBSOLETE');
              
            return (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredDocuments.map((document) => (
              <div
                key={document.id || document.uuid || Math.random()}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => onDocumentSelect?.(document)}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-3xl">{getStatusIcon(document.status)}</span>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                      {document.status.replace('_', ' ')}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
                      {document.title}
                    </h4>
                    <p className="text-sm text-gray-500 mb-2">
                      {document.document_number}
                    </p>
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {document.description}
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>{document.document_type_display || 'Unknown Type'}</div>
                    <div>By {document.author_display || 'Unknown Author'}</div>
                    <div>{formatDate(document.created_at)}</div>
                    {document.file_size && <div>{formatFileSize(document.file_size)}</div>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentList;