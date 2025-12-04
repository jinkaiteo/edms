import React, { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Document, SearchFilters, DocumentType } from '../types/api';
import Layout from '../components/common/Layout.tsx';
// DocumentUpload removed - replaced with EDMS-compliant DocumentCreateModal
import DocumentCreateModal from '../components/documents/DocumentCreateModal.tsx';
import DocumentList from '../components/documents/DocumentList.tsx';
import DocumentViewer from '../components/documents/DocumentViewer.tsx';
import DocumentSearch from '../components/documents/DocumentSearch.tsx';
import DocumentUploadNewModal from '../components/documents/DocumentUploadNewModal';

interface DocumentManagementProps {
  filterType?: 'pending' | 'approved' | 'archived' | 'obsolete';
}

const DocumentManagement: React.FC<DocumentManagementProps> = ({ 
  filterType: propFilterType = 'all' 
}) => {
  const [searchParams] = useSearchParams();
  
  // Get filter from URL query parameter or use prop as fallback
  const urlFilter = searchParams.get('filter') as 'pending' | 'approved' | 'archived' | 'obsolete' | null;
  const filterType = urlFilter || propFilterType;
  
  console.log('📄 DocumentManagement: URL filter:', urlFilter);
  console.log('📄 DocumentManagement: Final filterType:', filterType);
  console.log('📍 DocumentManagement: Current URL:', window.location.href);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({});
  const [viewMode, setViewMode] = useState<'split' | 'full-list' | 'full-viewer'>('split');
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [documentListRefresh, setDocumentListRefresh] = useState<number>(0);

  // Add event listener for clear selection only (document refresh handled separately)
  useEffect(() => {
    const handleClearSelection = () => {
      setSelectedDocument(null);
    };

    window.addEventListener('clearDocumentSelection', handleClearSelection);
    return () => {
      window.removeEventListener('clearDocumentSelection', handleClearSelection);
    };
  }, []);

  // Mock document types for the upload component
  const documentTypes: DocumentType[] = [
    { id: 1, name: 'Policy', description: 'Company policies', prefix: 'POL', is_active: true, workflow_required: true, retention_period: null, template: null },
    { id: 2, name: 'SOP', description: 'Standard Operating Procedures', prefix: 'SOP', is_active: true, workflow_required: true, retention_period: null, template: null },
    { id: 3, name: 'Manual', description: 'User manuals', prefix: 'MAN', is_active: true, workflow_required: false, retention_period: null, template: null },
    { id: 4, name: 'Form', description: 'Forms and templates', prefix: 'FORM', is_active: true, workflow_required: false, retention_period: null, template: null }
  ];

  const handleDocumentSelect = useCallback((document: Document) => {
    setSelectedDocument(document);
    if (viewMode === 'full-list') {
      setViewMode('split');
    }
  }, [viewMode]);

  const handleDocumentRefresh = useCallback(async () => {
    // Refresh the currently selected document with latest data from API
    if (selectedDocument && selectedDocument.uuid) {
      try {
        const response = await fetch(`/api/v1/documents/documents/${selectedDocument.uuid}/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const updatedDocument = await response.json();
          console.log('✅ DocumentManagement: Updated document received:', {
            hasFile: !!(updatedDocument.file_path && updatedDocument.file_name),
            fileName: updatedDocument.file_name,
            documentNumber: updatedDocument.document_number,
            status: updatedDocument.status
          });
          
          // Update the selected document with fresh data
          setSelectedDocument(updatedDocument);
          console.log('✅ DocumentManagement: selectedDocument state updated!');
          
          // CRITICAL: Also refresh the document list to show updated status
          setDocumentListRefresh(prev => prev + 1);
          console.log('🔄 DocumentManagement: Document list refresh triggered after workflow action');
        } else {
          console.error('Failed to refresh document:', response.status);
        }
      } catch (error) {
        console.error('Error refreshing document:', error);
      }
    }
  }, [selectedDocument]);

  // Add event listener for document updates (after handleDocumentRefresh is defined)
  useEffect(() => {
    const handleDocumentUpdated = (event: any) => {
      console.log('📢 DocumentManagement: Received documentUpdated event:', event.detail);
      
      // Refresh the document list immediately
      setDocumentListRefresh(prev => {
        const newRefresh = prev + 1;
        console.log('🔄 DocumentManagement: Document list refresh triggered by event:', newRefresh);
        return newRefresh;
      });
      
      // If the updated document is currently selected, refresh it too
      if (selectedDocument && event.detail?.documentId === selectedDocument.uuid) {
        console.log('🔄 DocumentManagement: Refreshing selected document after workflow action');
        handleDocumentRefresh();
      }
    };

    window.addEventListener('documentUpdated', handleDocumentUpdated);
    
    return () => {
      window.removeEventListener('documentUpdated', handleDocumentUpdated);
    };
  }, [selectedDocument, handleDocumentRefresh]);

  // Clear selected document when filter type changes (Document Library, My Tasks, Obsolete Documents)
  useEffect(() => {
    console.log('🔄 DocumentManagement: Filter changed to:', filterType, 'clearing selected document');
    setSelectedDocument(null);
  }, [filterType]);

  // Clear selected document when navigating away from this page (to Administration)
  useEffect(() => {
    return () => {
      // Cleanup: Clear selected document when component unmounts (user navigates away)
      console.log('🔄 DocumentManagement: Clearing selected document on page navigation');
      setSelectedDocument(null);
    };
  }, []);

  // EDMS Document creation handlers
  const handleCreateDocumentSuccess = useCallback((document: any) => {
    const documentTitle = document?.title || document?.document_number || 'New Document';
    console.log('🎉 DocumentManagement: Document created successfully, triggering list refresh');
    
    setUploadSuccess(`Document "${documentTitle}" created successfully! (EDMS Step 1 Complete)`);
    setUploadError(null);
    
    // Trigger document list refresh
    setDocumentListRefresh(prev => prev + 1);
    console.log('🔄 DocumentManagement: Document list refresh triggered');
    
    // Clear success message after 5 seconds
    setTimeout(() => setUploadSuccess(null), 5000);
  }, []);

  const handleCreateDocumentError = useCallback((error: string) => {
    setUploadError(`Failed to create document: ${error}`);
    setUploadSuccess(null);
    // Clear error message after 10 seconds
    setTimeout(() => setUploadError(null), 10000);
  }, []);

  const handleOpenCreateModal = useCallback(() => {
    setShowUploadModal(true);
    setUploadError(null);
    setUploadSuccess(null);
  }, []);

  const handleDocumentEdit = useCallback((document: Document) => {
    // TODO: Implement document editing
    alert(`Edit functionality for "${document.title}" will be implemented in the next phase.`);
  }, []);

  const handleDocumentDelete = useCallback((document: Document) => {
    // TODO: Implement document deletion
    if (window.confirm(`Are you sure you want to delete "${document.title}"?`)) {
      alert(`Delete functionality for "${document.title}" will be implemented in the next phase.`);
    }
  }, []);

  const handleDocumentSign = useCallback((document: Document) => {
    // TODO: Implement electronic signature
    alert(`Electronic signature functionality for "${document.title}" will be implemented in the next phase.`);
  }, []);

  const handleWorkflowAction = useCallback((document: Document, action: string) => {
    // TODO: Implement workflow actions
    alert(`Workflow action "${action}" for "${document.title}" will be implemented in the next phase.`);
  }, []);



  const handleSearch = useCallback((query: string, filters: SearchFilters) => {
    setSearchQuery(query);
    setSearchFilters(filters);
  }, []);

  const handleFilterChange = useCallback((filters: SearchFilters) => {
    setSearchFilters(filters);
  }, []);

  const getSearchFilters = () => {
    const combinedFilters = { ...searchFilters };
    if (searchQuery) {
      combinedFilters.search = searchQuery;
    }
    return combinedFilters;
  };

  const renderContent = () => {
    // Note: Inline upload removed - all document creation now uses EDMS-compliant modal workflow

    switch (viewMode) {
      case 'full-list':
        return (
          <div className="space-y-6">
            <DocumentSearch
              onSearch={handleSearch}
              onFilterChange={handleFilterChange}
              documentTypes={documentTypes}
            />
            <DocumentList
              onDocumentSelect={handleDocumentSelect}
              refreshTrigger={documentListRefresh}
              selectedDocument={selectedDocument}
              filterType={filterType}
              searchQuery={searchQuery}
              searchFilters={getSearchFilters()}
            />
          </div>
        );

      case 'full-viewer':
        return (
          <DocumentViewer
            document={selectedDocument}
            onClose={() => setViewMode('split')}
            onEdit={handleDocumentEdit}
            onSign={handleDocumentSign}
            onWorkflowAction={handleWorkflowAction}
          />
        );

      case 'split':
      default:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              <DocumentSearch
                onSearch={handleSearch}
                onFilterChange={handleFilterChange}
                documentTypes={documentTypes}
              />
              <DocumentList
                onDocumentSelect={handleDocumentSelect}
                refreshTrigger={documentListRefresh}
                selectedDocument={selectedDocument}
                filterType={filterType}
                searchQuery={searchQuery}
                searchFilters={getSearchFilters()}
              />
            </div>
            <div className="lg:sticky lg:top-6 lg:h-fit">
              {selectedDocument ? (
                <DocumentViewer
                  document={selectedDocument}
                  onEdit={handleDocumentEdit}
                  onSign={handleDocumentSign}
                  onWorkflowAction={handleWorkflowAction}
                  onRefresh={handleDocumentRefresh}
                />
              ) : (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
                  <div className="text-center">
                    <div className="text-6xl text-gray-300 mb-4">📄</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Document Selected</h3>
                    <p className="text-gray-500 mb-4">Select a document from the list to view its details and manage workflow actions.</p>
                    {/* Show clear selection button if we came from a previous selection */}
                    <div className="text-xs text-gray-400">
                      Tip: Click on any document card to select it
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {filterType === 'pending' ? 'My Tasks' :
                 filterType === 'obsolete' ? 'Obsolete Documents' :
                 filterType === 'archived' ? 'Archived Documents' :
                 'Document Library'}
              </h1>
              <p className="text-gray-600 mt-2">
                {filterType === 'pending' ? 'Documents requiring your action and review' :
                 filterType === 'obsolete' ? 'View obsolete, superseded, and scheduled for obsolescence documents' :
                 filterType === 'archived' ? 'View archived document versions and terminated workflows' :
                 'Manage, upload, and review documents in your EDMS system'}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {/* View Mode Toggle */}
              <div className="hidden lg:flex border border-gray-300 rounded-md">
                <button
                  onClick={() => setViewMode('full-list')}
                  className={`px-3 py-2 text-sm font-medium ${
                    viewMode === 'full-list' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  title="Full List View"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('split')}
                  className={`px-3 py-2 text-sm font-medium ${
                    viewMode === 'split' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  title="Split View"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 4v16m6-16v16M4 8h16M4 16h16" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('full-viewer')}
                  className={`px-3 py-2 text-sm font-medium ${
                    viewMode === 'full-viewer' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  title="Full Viewer"
                  disabled={!selectedDocument}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
              </div>

              {/* Manual Refresh Button */}
              <button
                onClick={() => {
                  console.log('🔄 Manual refresh triggered by user');
                  setDocumentListRefresh(prev => prev + 1);
                  if (selectedDocument) {
                    handleDocumentRefresh();
                  }
                }}
                className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                title="Refresh document list and selected document data"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Refresh</span>
              </button>

              {/* Create Document Button */}
              <button
                onClick={handleOpenCreateModal}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span>📝 Create Document</span>
              </button>
            </div>
          </div>
        </div>


        {/* Main Content */}
        {renderContent()}


        {/* Success/Error Messages */}
        {uploadSuccess && (
          <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded-md">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              {uploadSuccess}
            </div>
          </div>
        )}

        {uploadError && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {uploadError}
            </div>
          </div>
        )}

        {/* EDMS Step 1: Document Creation Modal */}
        <DocumentCreateModal
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          onCreateSuccess={handleCreateDocumentSuccess}
        />
      </div>
    </Layout>
  );
};

export default DocumentManagement;