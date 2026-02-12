import React, { useState, useEffect } from 'react';
import apiService from '../../services/api.ts';
import { useAuth } from '../../contexts/AuthContext.tsx';
import SensitivityBadge from '../common/SensitivityBadge.tsx';

interface Document {
  id?: number;
  uuid: string;
  title: string;
  document_number: string;
  document_type_display?: string;
  description?: string;
  status: string;
  author?: number;
  author_display?: string;
  author_username?: string;
  created_at: string;
  file_size?: number;
  version_string?: string;
  supersedes?: string;
}

interface DocumentListProps {
  onDocumentSelect?: (document: Document) => void;
  refreshTrigger?: number; // Add refresh trigger prop
  selectedDocument?: Document | null; // Add selected document prop
  filterType?: 'pending' | 'approved' | 'archived' | 'obsolete' | 'periodic_review';
  searchQuery?: string; // Add search query prop
  searchFilters?: any; // Add search filters prop
}

const DocumentList: React.FC<DocumentListProps> = ({
  onDocumentSelect,
  refreshTrigger,
  selectedDocument,
  filterType = 'all',
  searchQuery = '',
  searchFilters = {},
}) => {
  console.log('🔍 DocumentList: Received props:', { filterType, refreshTrigger, selectedDocument: selectedDocument?.uuid });
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [sortBy, setSortBy] = useState<'title' | 'created_at' | 'status' | 'document_type'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  // Hide inactive documents EXCEPT on Obsolete Documents page
  const showInactive = filterType === 'obsolete';

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
        // Extract version numbers for proper sorting (supports zero-padded versions)
        const getVersionNumber = (docNum: string) => {
          const versionMatch = docNum.match(/-v(\d+)\.(\d+)$/);
          if (versionMatch) {
            return { major: parseInt(versionMatch[1], 10), minor: parseInt(versionMatch[2], 10) };
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

  // Helper functions for formatting
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'draft': return '📝';
      case 'pending_review': return '⏳';
      case 'under_review': return '👀';
      case 'reviewed': return '✅';
      case 'pending_approval': return '⏰';
      case 'approved_and_effective': return '📋';
      case 'effective': return '📋';
      case 'superseded': return '📂';
      case 'obsolete': return '🗂️';
      case 'terminated': return '🛑';
      default: return '📄';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'pending_review': return 'bg-yellow-100 text-yellow-800';
      case 'under_review': return 'bg-blue-100 text-blue-800';
      case 'reviewed': return 'bg-green-100 text-green-800';
      case 'pending_approval': return 'bg-orange-100 text-orange-800';
      case 'approved_and_effective': return 'bg-green-100 text-green-800';
      case 'effective': return 'bg-green-100 text-green-800';
      case 'superseded': return 'bg-gray-100 text-gray-600';
      case 'obsolete': return 'bg-red-100 text-red-800';
      case 'terminated': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Helper function to check if document is selected
  const isDocumentSelected = (document: Document) => {
    if (!selectedDocument) return false;
    return selectedDocument.uuid === document.uuid || 
           (selectedDocument.id && document.id && selectedDocument.id === document.id);
  };

  // Helper function to check if document belongs to logged-in user
  const isMyDocument = (document: Document) => {
    if (!user || !document.author) return false;
    return user.id === document.author;
  };;


  // Fetch documents
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        console.log('🔄 DocumentList: Fetching documents...', refreshTrigger ? `(trigger: ${refreshTrigger})` : '(initial load)', `[filter: ${filterType}]`);
        console.log('📍 DocumentList: Current URL:', window.location.pathname);
        
        // Build API endpoint with filter parameter  
        const filterParam = filterType === 'approved' ? 'approved_latest' : 
                           filterType === 'pending' ? 'my_tasks' :
                           filterType === 'archived' ? 'archived' :
                           filterType === 'obsolete' ? 'obsolete' :
                           filterType === 'periodic_review' ? 'periodic_review' :
                           filterType === 'all' ? 'library' : '';
        
        // ADMIN OVERRIDE: For admins/superusers, default to no filter (see all documents)
        const shouldShowAllForAdmin = !filterType && user?.is_superuser;
        
        console.log('👤 User admin status:', { 
          username: user?.username, 
          is_superuser: user?.is_superuser,
          filterType,
          shouldShowAllForAdmin 
        });
        
        console.log('🔧 DocumentList: Filter mapping:', { filterType, filterParam });
        
        // Build search parameters
        const searchParams = new URLSearchParams();
        
        // Add filter parameter
        if (filterParam) {
          searchParams.append('filter', filterParam);
        }
        
        // Add search query
        if (searchQuery.trim()) {
          searchParams.append('search', searchQuery.trim());
          console.log('🔍 DocumentList: Adding search query:', searchQuery.trim());
        }
        
        // Add additional search filters
        Object.entries(searchFilters).forEach(([key, value]) => {
          if (value && key !== 'search') {
            // Handle array filters (document_type, status, author, reviewer, approver)
            if (Array.isArray(value)) {
              value.forEach(item => {
                if (item) {
                  searchParams.append(key, String(item));
                  console.log('🔍 DocumentList: Adding array search filter:', key, '=', item);
                }
              });
            } else {
              // Handle string filters (title, description, document_number, keywords, etc.)
              searchParams.append(key, String(value));
              console.log('🔍 DocumentList: Adding search filter:', key, '=', value);
            }
          }
        });
        
        const endpoint = `/documents/documents/${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
        console.log('🔗 DocumentList: Final endpoint:', endpoint);
        
        const response = await apiService.get(endpoint);
        console.log('📥 DocumentList: Raw API response:', response);
        
        let documentsData = [];
        if (response && response.results && Array.isArray(response.results)) {
          documentsData = response.results;
        } else if (response && response.data && Array.isArray(response.data)) {
          documentsData = response.data;
        } else if (response && Array.isArray(response)) {
          documentsData = response;
        } else {
          console.warn('⚠️ DocumentList: Unexpected response format, defaulting to empty array');
          documentsData = [];
        }
        
        setDocuments(documentsData);
        console.log('✅ DocumentList: Documents set successfully:', documentsData.length, 'documents');
        setError(null);
      } catch (error) {
        console.error('❌ DocumentList: Error fetching documents:', error);
        setError('Failed to fetch documents');
        setDocuments([]); // Ensure documents is always an array
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, [refreshTrigger, filterType, searchQuery, searchFilters]); // Add search parameters to dependency array

  if (loading) {
    return <div className="text-center py-8">Loading documents...</div>;
  }

  if (error) {
    return <div className="text-center py-8 text-red-600">Error: {error}</div>;
  }

  // Filter documents based on inactive status toggle (hide obsolete and terminated by default)
  // Safety check to ensure documents is an array
  const documentsArray = Array.isArray(documents) ? documents : [];
  const filteredDocuments = showInactive 
    ? documentsArray 
    : documentsArray.filter(doc => doc.status !== 'OBSOLETE' && doc.status !== 'TERMINATED');

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
    <div className="w-full">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">Documents</h3>
            
            <div className="flex items-center space-x-4">
              {/* Sort dropdown */}
              <select
                value={sortBy + '-' + sortOrder}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-');
                  setSortBy(field as typeof sortBy);
                  setSortOrder(order as 'asc' | 'desc');
                }}
                className="border border-gray-300 rounded-md px-3 py-2 pr-8 text-sm bg-white"
              >
                <option value="created_at-desc">Newest First</option>
                <option value="created_at-asc">Oldest First</option>
                <option value="title-asc">Title A-Z</option>
                <option value="title-desc">Title Z-A</option>
                <option value="status-desc">Status Z-A</option>
                <option value="status-asc">Status A-Z</option>
                <option value="document_type-asc">Type A-Z</option>
              </select>

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
        </div>

        {filteredDocuments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No documents found.
          </div>
        ) : viewMode === 'list' ? (
          // Grouped list view with version history
          <div className="space-y-4 p-4">
            {sortedGroupKeys.map((baseNumber) => {
              const groupDocuments = documentGroups[baseNumber];
              const currentVersion = groupDocuments[0]; // Newest version
              const olderVersions = groupDocuments.slice(1); // Superseded versions
              const isExpanded = expandedGroups.has(baseNumber);

              return (
                <div key={baseNumber} className="border border-gray-200 rounded-lg">
                  {/* Current Version */}
                  <div
                    className={`p-4 hover:shadow-md transition-all cursor-pointer ${
                      isDocumentSelected(currentVersion) 
                        ? 'bg-blue-50 border-l-4 border-blue-500 shadow-md' 
                        : 'hover:bg-gray-50'
                    }`}
                    onClick={() => onDocumentSelect?.(currentVersion)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-2xl">{getStatusIcon(currentVersion.status)}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h4 className="text-sm font-medium text-gray-900 truncate">
                                {currentVersion.title}
                              </h4>
                              {isMyDocument(currentVersion) && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 flex-shrink-0" title="You are the author">
                                  👤 Mine
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-500">
                              {getBaseDocumentNumber(currentVersion.document_number)} • {currentVersion.document_type_display || 
                               (currentVersion.document_type && typeof currentVersion.document_type === 'object' 
                                 ? currentVersion.document_type.name 
                                 : currentVersion.document_type) || 'Unknown Type'}
                              {(currentVersion.status === 'EFFECTIVE') && (
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
                          {olderVersions.map((oldVersion) => (
                            <div
                              key={oldVersion.id || oldVersion.uuid}
                              className={`px-4 py-3 cursor-pointer border-b border-gray-100 last:border-b-0 transition-all ${
                                isDocumentSelected(oldVersion)
                                  ? 'bg-blue-100 border-l-4 border-blue-500'
                                  : 'hover:bg-gray-100'
                              }`}
                              onClick={(e) => {
                                e.stopPropagation();
                                onDocumentSelect?.(oldVersion);
                              }}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-sm font-medium text-gray-700">
                                      {getBaseDocumentNumber(oldVersion.document_number)}
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
        ) : (
          // Grid view
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredDocuments.map((document) => (
                <div
                  key={document.id || document.uuid || Math.random()}
                  className={`border rounded-lg p-4 transition-all cursor-pointer ${
                    isDocumentSelected(document)
                      ? 'border-blue-500 bg-blue-50 shadow-md ring-2 ring-blue-200'
                      : 'border-gray-200 hover:shadow-md hover:border-gray-300'
                  }`}
                  onClick={() => onDocumentSelect?.(document)}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-3xl">{getStatusIcon(document.status)}</span>
                      <div className="flex items-center gap-2">
                        {isMyDocument(document) && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800" title="You are the author">
                            👤 Mine
                          </span>
                        )}
                        {document.sensitivity_label && (
                          <SensitivityBadge label={document.sensitivity_label} size="sm" />
                        )}
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                          {document.status.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
                        {document.title}
                      </h4>
                      <p className="text-sm text-gray-500 mb-2">
                        {getBaseDocumentNumber(document.document_number)}
                      </p>
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {document.description}
                      </p>
                    </div>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>
                        {document.document_type_display || 
                         (document.document_type && typeof document.document_type === 'object' 
                           ? document.document_type.name 
                           : document.document_type) || 'Unknown Type'}
                      </div>
                      <div>By {document.author_display || 'Unknown Author'}</div>
                      <div>{formatDate(document.created_at)}</div>
                      {document.file_size && <div>{formatFileSize(document.file_size)}</div>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
    </div>
  );
};

export default DocumentList;