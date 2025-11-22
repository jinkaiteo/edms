import React, { useState, useEffect } from 'react';
import { Document, WorkflowInstance, ElectronicSignature } from '../../types/api';
import apiService from '../../services/api';

interface DocumentViewerProps {
  document: Document | null;
  onClose?: () => void;
  onEdit?: (document: Document) => void;
  onSign?: (document: Document) => void;
  onWorkflowAction?: (document: Document, action: string) => void;
  className?: string;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  document,
  onClose,
  onEdit,
  onSign,
  onWorkflowAction,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<'details' | 'workflow' | 'signatures' | 'history'>('details');
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowInstance | null>(null);
  const [signatures, setSignatures] = useState<ElectronicSignature[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (document) {
      loadDocumentData();
    }
  }, [document]);

  const loadDocumentData = async () => {
    if (!document) return;

    setLoading(true);
    try {
      // For now, use mock data. Replace with real API calls when backend is ready
      // const [workflowResponse, signaturesResponse] = await Promise.all([
      //   apiService.getDocumentWorkflowStatus(document.id),
      //   apiService.getElectronicSignatures({ document_id: document.id })
      // ]);

      // Mock workflow status
      const mockWorkflow: WorkflowInstance = {
        id: 1,
        uuid: 'workflow-uuid-1',
        workflow_type: {
          id: 1,
          uuid: 'type-uuid-1',
          name: 'Document Review',
          workflow_type: 'REVIEW',
          description: 'Standard document review workflow',
          is_active: true,
          requires_approval: true,
          timeout_days: 7,
          reminder_days: 2
        },
        state: document.status === 'effective' ? 'approved' : document.status,
        state_display: document.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        initiated_by: document.created_by,
        current_assignee: null,
        started_at: document.created_at,
        completed_at: document.status === 'effective' ? document.updated_at : null,
        due_date: null,
        is_active: document.status !== 'effective',
        is_completed: document.status === 'effective',
        is_overdue: false,
        completion_reason: document.status === 'effective' ? 'Successfully completed review process' : null,
        workflow_data: {},
        content_object_data: {
          type: 'document',
          id: document.id,
          document_number: document.document_number,
          title: document.title,
          status: document.status,
          version: document.version
        }
      };

      // Mock signatures
      const mockSignatures: ElectronicSignature[] = document.status === 'effective' ? [
        {
          id: 1,
          uuid: 'sig-uuid-1',
          document: document.id,
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
          signature_type: 'REVIEW',
          reason: 'Document review completed successfully',
          signature_timestamp: '2024-11-21T15:30:00Z',
          document_hash: 'sha256:abcdef123456...',
          signature_data: {},
          certificate: {
            id: 1,
            uuid: 'cert-uuid-1',
            user: 3,
            certificate_type: 'SIGNING',
            serial_number: 'CERT-001-2024',
            subject_dn: 'CN=Document Reviewer,O=EDMS,C=US',
            issuer_dn: 'CN=EDMS CA,O=EDMS,C=US',
            issued_at: '2024-01-01T00:00:00Z',
            expires_at: '2025-01-01T00:00:00Z',
            is_active: true,
            revoked_at: null,
            revocation_reason: ''
          },
          signature_method: 'PKI_DIGITAL',
          is_valid: true,
          invalidated_at: null,
          invalidation_reason: ''
        }
      ] : [];

      setWorkflowStatus(mockWorkflow);
      setSignatures(mockSignatures);

      // Mock document preview URL
      if (document.file_path) {
        // In a real app, this would be a proper preview URL from the backend
        setPreviewUrl(`/api/v1/documents/${document.id}/preview/`);
      }

    } catch (error) {
      console.error('Failed to load document data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
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

  const getAvailableActions = () => {
    if (!document || !workflowStatus) return [];

    const actions = [];
    
    switch (document.status) {
      case 'draft':
        actions.push({ key: 'submit_for_review', label: 'Submit for Review', color: 'blue' });
        break;
      case 'pending_review':
        actions.push({ key: 'start_review', label: 'Start Review', color: 'blue' });
        break;
      case 'under_review':
        actions.push({ key: 'complete_review', label: 'Complete Review', color: 'green' });
        actions.push({ key: 'request_changes', label: 'Request Changes', color: 'yellow' });
        break;
      case 'review_completed':
        actions.push({ key: 'approve', label: 'Approve Document', color: 'green' });
        actions.push({ key: 'reject', label: 'Reject Document', color: 'red' });
        break;
      case 'approved':
        actions.push({ key: 'make_effective', label: 'Make Effective', color: 'green' });
        break;
      case 'effective':
        actions.push({ key: 'create_revision', label: 'Create Revision', color: 'blue' });
        actions.push({ key: 'mark_obsolete', label: 'Mark Obsolete', color: 'red' });
        break;
    }

    return actions;
  };

  if (!document) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
        <div className="p-6 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No Document Selected</h3>
          <p className="text-gray-500">Select a document from the list to view its details.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-start">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-3 mb-2">
              <h2 className="text-xl font-semibold text-gray-900 truncate">
                {document.title}
              </h2>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                {document.status.replace('_', ' ')}
              </span>
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>{document.document_number}</span>
              <span>•</span>
              <span>Version {document.version}</span>
              <span>•</span>
              <span>{document.document_type.name}</span>
            </div>
          </div>
          <div className="flex items-center space-x-2 ml-4">
            {onEdit && (
              <button
                onClick={() => onEdit(document)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Edit
              </button>
            )}
            {document.file_path && (
              <button
                onClick={() => {
                  // In a real app, this would trigger a download
                  window.open(`/api/v1/documents/${document.id}/download/`, '_blank');
                }}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Download
              </button>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {['details', 'workflow', 'signatures', 'history'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as typeof activeTab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'details' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Document Information */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Document Information</h3>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Description</dt>
                    <dd className="text-sm text-gray-900 mt-1">{document.description}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Document Type</dt>
                    <dd className="text-sm text-gray-900 mt-1">{document.document_type.name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Created By</dt>
                    <dd className="text-sm text-gray-900 mt-1">{document.created_by.full_name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Created Date</dt>
                    <dd className="text-sm text-gray-900 mt-1">{formatDate(document.created_at)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Last Modified</dt>
                    <dd className="text-sm text-gray-900 mt-1">{formatDate(document.updated_at)}</dd>
                  </div>
                  {document.effective_date && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Effective Date</dt>
                      <dd className="text-sm text-gray-900 mt-1">{formatDate(document.effective_date)}</dd>
                    </div>
                  )}
                  {document.review_date && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Next Review Date</dt>
                      <dd className="text-sm text-gray-900 mt-1">{formatDate(document.review_date)}</dd>
                    </div>
                  )}
                  {document.file_size && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">File Size</dt>
                      <dd className="text-sm text-gray-900 mt-1">{formatFileSize(document.file_size)}</dd>
                    </div>
                  )}
                </dl>
              </div>

              {/* Metadata */}
              {Object.keys(document.metadata).length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Metadata</h3>
                  <dl className="space-y-3">
                    {Object.entries(document.metadata).map(([key, value]) => (
                      <div key={key}>
                        <dt className="text-sm font-medium text-gray-500 capitalize">{key.replace('_', ' ')}</dt>
                        <dd className="text-sm text-gray-900 mt-1">{String(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              )}
            </div>

            {/* Document Preview */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Document Preview</h3>
              <div className="border border-gray-200 rounded-lg p-4">
                {document.file_path ? (
                  <div className="text-center py-8">
                    <div className="text-gray-400 mb-4">
                      <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <p className="text-sm text-gray-500 mb-4">Document preview not available</p>
                    <button
                      onClick={() => window.open(`/api/v1/documents/${document.id}/download/`, '_blank')}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      View Document
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-400 mb-4">
                      <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                    </div>
                    <p className="text-sm text-gray-500">No file attached to this document</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'workflow' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">Workflow Status</h3>
              {workflowStatus && (
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(workflowStatus.state)}`}>
                  {workflowStatus.state_display}
                </span>
              )}
            </div>

            {workflowStatus ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Workflow Information</h4>
                    <dl className="space-y-3">
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Workflow Type</dt>
                        <dd className="text-sm text-gray-900 mt-1">{workflowStatus.workflow_type.name}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Started By</dt>
                        <dd className="text-sm text-gray-900 mt-1">{workflowStatus.initiated_by.full_name}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Started Date</dt>
                        <dd className="text-sm text-gray-900 mt-1">{formatDate(workflowStatus.started_at)}</dd>
                      </div>
                      {workflowStatus.completed_at && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Completed Date</dt>
                          <dd className="text-sm text-gray-900 mt-1">{formatDate(workflowStatus.completed_at)}</dd>
                        </div>
                      )}
                      {workflowStatus.current_assignee && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Current Assignee</dt>
                          <dd className="text-sm text-gray-900 mt-1">{workflowStatus.current_assignee.full_name}</dd>
                        </div>
                      )}
                    </dl>
                  </div>

                  {/* Available Actions */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Available Actions</h4>
                    <div className="space-y-2">
                      {getAvailableActions().map((action) => (
                        <button
                          key={action.key}
                          onClick={() => onWorkflowAction?.(document, action.key)}
                          className={`w-full px-4 py-2 text-sm font-medium rounded-md border focus:ring-2 focus:ring-offset-2 ${
                            action.color === 'blue' ? 'bg-blue-600 border-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500' :
                            action.color === 'green' ? 'bg-green-600 border-green-600 text-white hover:bg-green-700 focus:ring-green-500' :
                            action.color === 'yellow' ? 'bg-yellow-600 border-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500' :
                            action.color === 'red' ? 'bg-red-600 border-red-600 text-white hover:bg-red-700 focus:ring-red-500' :
                            'bg-gray-600 border-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500'
                          }`}
                        >
                          {action.label}
                        </button>
                      ))}
                      {getAvailableActions().length === 0 && (
                        <p className="text-sm text-gray-500">No actions available at this time.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-gray-500">No workflow information available.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'signatures' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Electronic Signatures</h3>
            
            {signatures.length > 0 ? (
              <div className="space-y-4">
                {signatures.map((signature) => (
                  <div key={signature.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-green-500">
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            </span>
                            <span className="text-sm font-medium text-gray-900">
                              {signature.signature_type} Signature
                            </span>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                              signature.is_valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {signature.is_valid ? 'Valid' : 'Invalid'}
                            </span>
                          </div>
                        </div>
                        <div className="space-y-1 text-sm text-gray-600">
                          <div>Signed by: {signature.user.full_name}</div>
                          <div>Date: {formatDate(signature.signature_timestamp)}</div>
                          <div>Reason: {signature.reason}</div>
                          <div>Method: {signature.signature_method.replace('_', ' ')}</div>
                        </div>
                      </div>
                      <button className="text-sm text-blue-600 hover:text-blue-800">
                        Verify
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-gray-400 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </div>
                <h4 className="text-lg font-medium text-gray-900 mb-1">No Signatures</h4>
                <p className="text-sm text-gray-500 mb-4">This document has not been electronically signed yet.</p>
                {onSign && (
                  <button
                    onClick={() => onSign(document)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Sign Document
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-900">Document History</h3>
            
            <div className="space-y-4">
              {/* Mock history entries */}
              <div className="border-l-4 border-blue-500 pl-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Document Created</h4>
                    <p className="text-sm text-gray-600">
                      Document created by {document.created_by.full_name}
                    </p>
                  </div>
                  <span className="text-sm text-gray-500">{formatDate(document.created_at)}</span>
                </div>
              </div>
              
              {document.status !== 'draft' && (
                <div className="border-l-4 border-yellow-500 pl-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Status Changed</h4>
                      <p className="text-sm text-gray-600">
                        Status changed to {document.status.replace('_', ' ')}
                      </p>
                    </div>
                    <span className="text-sm text-gray-500">{formatDate(document.updated_at)}</span>
                  </div>
                </div>
              )}
              
              {document.status === 'effective' && (
                <div className="border-l-4 border-green-500 pl-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Document Approved</h4>
                      <p className="text-sm text-gray-600">
                        Document approved and made effective
                      </p>
                    </div>
                    <span className="text-sm text-gray-500">{formatDate(document.updated_at)}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentViewer;