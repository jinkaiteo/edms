import React, { useState, useCallback } from 'react';
import { Document, SearchFilters, DocumentType } from '../types/api';
import Layout from '../components/common/Layout.tsx';
// DocumentUpload removed - replaced with EDMS-compliant DocumentCreateModal
import DocumentCreateModal from '../components/documents/DocumentCreateModal.tsx';
import DocumentList from '../components/documents/DocumentList.tsx';
import DocumentViewer from '../components/documents/DocumentViewer.tsx';
import DocumentSearch from '../components/documents/DocumentSearch.tsx';
import DocumentUploadNewModal from '../components/documents/DocumentUploadNewModal';

const DocumentManagement: React.FC = () => {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({});
  const [viewMode, setViewMode] = useState<'split' | 'full-list' | 'full-viewer'>('split');
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

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
      console.log('🔄 DocumentManagement: Refreshing selected document data...');
      try {
        const response = await fetch(`http://localhost:8000/api/v1/documents/documents/${selectedDocument.uuid}/`, {
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
            documentNumber: updatedDocument.document_number
          });
          
          // Update the selected document with fresh data
          setSelectedDocument(updatedDocument);
          console.log('✅ DocumentManagement: selectedDocument state updated!');
        } else {
          console.error('Failed to refresh document:', response.status);
        }
      } catch (error) {
        console.error('Error refreshing document:', error);
      }
    }
  }, [selectedDocument]);

  // EDMS Step 1: Document creation handlers
  const handleCreateDocumentSuccess = useCallback((document: any) => {
    const documentTitle = document?.title || document?.document_number || 'New Document';
    setUploadSuccess(`Document "${documentTitle}" created successfully! (EDMS Step 1 Complete)`);
    setUploadError(null);
    // Clear success message after 5 seconds
    setTimeout(() => setUploadSuccess(null), 5000);
    // No page reload - let the document list refresh naturally
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
              onDocumentEdit={handleDocumentEdit}
              onDocumentDelete={handleDocumentDelete}
              filters={getSearchFilters()}
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
                onDocumentEdit={handleDocumentEdit}
                onDocumentDelete={handleDocumentDelete}
                filters={getSearchFilters()}
              />
            </div>
            <div className="lg:sticky lg:top-6 lg:h-fit">
              <DocumentViewer
                document={selectedDocument}
                onEdit={handleDocumentEdit}
                onSign={handleDocumentSign}
                onWorkflowAction={handleWorkflowAction}
                onRefresh={handleDocumentRefresh}
              />
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
              <h1 className="text-3xl font-bold text-gray-900">Document Management</h1>
              <p className="text-gray-600 mt-2">
                Manage, upload, and review documents in your EDMS system
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

              {/* Create Document Button (EDMS Step 1) */}
              <button
                onClick={handleOpenCreateModal}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span>📝 Create Document (Step 1)</span>
              </button>
            </div>
          </div>
        </div>

        {/* EDMS Workflow Information */}
        {!showUpload && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">📋 EDMS Two-Step Document Workflow</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="bg-white rounded-md p-3 border border-blue-200">
                <h4 className="font-medium text-blue-800 mb-1">📝 Step 1: Create Document</h4>
                <p className="text-blue-700">Create document placeholder with basic information (Title, Type, Source, etc.)</p>
                <p className="text-blue-600 text-xs mt-1">Status: DRAFT • No reviewer selection yet</p>
              </div>
              <div className="bg-white rounded-md p-3 border border-blue-200">
                <h4 className="font-medium text-blue-800 mb-1">📤 Step 2: Submit for Review</h4>
                <p className="text-blue-700">Select reviewer and route document through approval workflow</p>
                <p className="text-blue-600 text-xs mt-1">Status: DRAFT → PENDING_REVIEW → EFFECTIVE</p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        {renderContent()}

        {/* Quick Stats */}
        {!showUpload && (
          <div className="mt-12 grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Documents</dt>
                    <dd className="text-lg font-medium text-gray-900">3</dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Effective</dt>
                    <dd className="text-lg font-medium text-gray-900">1</dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Pending Review</dt>
                    <dd className="text-lg font-medium text-gray-900">1</dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Drafts</dt>
                    <dd className="text-lg font-medium text-gray-900">1</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        )}

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