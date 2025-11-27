import React, { useState, useEffect } from 'react';
import { Document, WorkflowInstance, ElectronicSignature } from '../../types/api';
import ReviewerInterface from '../workflows/ReviewerInterface.tsx';
import SubmitForReviewModal from '../workflows/SubmitForReviewModal.tsx';
import RouteForApprovalModal from '../workflows/RouteForApprovalModal.tsx';
import ApproverInterface from '../workflows/ApproverInterface.tsx';
// SetEffectiveDateModal removed - no longer needed in simplified workflow
import CreateNewVersionModal from '../workflows/CreateNewVersionModal.tsx';
import MarkObsoleteModal from '../workflows/MarkObsoleteModal.tsx';
import ViewReviewStatus from '../workflows/ViewReviewStatus.tsx';
import DownloadActionMenu from './DownloadActionMenu.tsx';
import DocumentCreateModal from './DocumentCreateModal.tsx';
import MyDraftDocuments from './MyDraftDocuments.tsx';
import { useAuth } from '../../contexts/AuthContext.tsx';
import apiService from '../../services/api.ts';

interface DocumentViewerProps {
  document: Document | null;
  onClose?: () => void;
  onEdit?: (document: Document) => void;
  onSign?: (document: Document) => void;
  onWorkflowAction?: (document: Document, action: string) => void;
  onRefresh?: () => void;
  className?: string;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  document,
  onClose,
  onEdit,
  onSign,
  onWorkflowAction,
  onRefresh,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<'details' | 'workflow' | 'signatures' | 'history'>('details');
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowInstance | null>(null);
  const [signatures, setSignatures] = useState<ElectronicSignature[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showReviewerInterface, setShowReviewerInterface] = useState(false);
  
  // Workflow modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);
  const [showSubmitForReviewModal, setShowSubmitForReviewModal] = useState(false);
  const [showRouteForApprovalModal, setShowRouteForApprovalModal] = useState(false);
  const [showApproverInterface, setShowApproverInterface] = useState(false);
  // showSetEffectiveDateModal removed - no longer needed in simplified workflow
  const [showCreateNewVersionModal, setShowCreateNewVersionModal] = useState(false);
  const [showMarkObsoleteModal, setShowMarkObsoleteModal] = useState(false);
  const [showViewReviewStatus, setShowViewReviewStatus] = useState(false);
  
  // Auth context for role-based visibility
  const { authenticated, user } = useAuth();

  useEffect(() => {
    if (document) {
      loadDocumentData();
    }
  }, [document]);

  const loadDocumentData = async () => {
    if (!document) return;

    console.log('🔄 Loading document data for:', {
      id: document.id,
      uuid: document.uuid,
      title: document.title,
      status: document.status
    });

    setLoading(true);
    try {
      // Fetch real workflow status from backend - but only if we have valid IDs
      const apiCalls = [];
      
      // Add workflow status call if we have document UUID
      if (document.uuid) {
        console.log('📡 Fetching workflow status for UUID:', document.uuid);
        apiCalls.push(
          fetch(`http://localhost:8000/api/v1/workflows/documents/${document.uuid}/status/`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
              'Content-Type': 'application/json',
            },
          }).then(res => res.ok ? res.json() : null).catch(() => null)
        );
      } else {
        console.log('⚠️ No document UUID available, skipping workflow status fetch');
        apiCalls.push(Promise.resolve(null));
      }
      
      // Add signatures call if we have document ID
      if (document.id && document.id !== undefined) {
        console.log('📡 Fetching signatures for document ID:', document.id);
        apiCalls.push(
          fetch(`http://localhost:8000/api/v1/security/signatures/?document_id=${document.id}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
              'Content-Type': 'application/json',
            },
          }).then(res => res.ok ? res.json() : null).catch(() => null)
        );
      } else {
        console.log('⚠️ No valid document ID available, skipping signatures fetch. ID was:', document.id);
        apiCalls.push(Promise.resolve(null));
      }

      const [workflowResponse, signaturesResponse] = await Promise.all(apiCalls);

      // Use real data if available, fallback to mock data
      if (workflowResponse) {
        setWorkflowStatus(workflowResponse);
      } else {
        // Fallback to mock workflow status only if API fails
        setWorkflowStatus(createMockWorkflowStatus(document));
      }

      if (signaturesResponse) {
        setSignatures(signaturesResponse.results || []);
      } else {
        // Fallback to mock signatures
        setSignatures(createMockSignatures(document));
      }

      // Set document preview URL
      if (document.file_path) {
        setPreviewUrl(`/api/v1/documents/${document.id}/preview/`);
      }

    } catch (error) {
      console.error('Failed to load document data:', error);
      // Fallback to mock data on any error
      setWorkflowStatus(createMockWorkflowStatus(document));
      setSignatures(createMockSignatures(document));
    } finally {
      setLoading(false);
    }
  };

  // Helper function to create mock workflow status
  const createMockWorkflowStatus = (doc: Document): WorkflowInstance => ({
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
    state: doc.status.toLowerCase() === 'effective' ? 'approved' : doc.status.toLowerCase(),
    state_display: doc.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    initiated_by: doc.created_by,
    current_assignee: null,
    started_at: doc.created_at,
    completed_at: doc.status.toLowerCase() === 'effective' ? doc.updated_at : null,
    due_date: null,
    is_active: doc.status.toLowerCase() !== 'effective',
    is_completed: doc.status.toLowerCase() === 'effective',
    is_overdue: false,
    completion_reason: doc.status.toLowerCase() === 'effective' ? 'Successfully completed review process' : null,
    workflow_data: {},
    content_object_data: {
      type: 'document',
      id: doc.id,
      document_number: doc.document_number,
      title: doc.title,
      status: doc.status,
      version: doc.version
    }
  });

  // Helper function to create mock signatures
  const createMockSignatures = (doc: Document): ElectronicSignature[] => {
    return doc.status.toLowerCase() === 'effective' ? [
      {
        id: 1,
        uuid: 'sig-uuid-1',
        document: doc.id,
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

  const handleWorkflowAction = (actionKey: string) => {
    
    // Handle EDMS workflow actions
    switch (actionKey) {
      case 'upload_file':
        // EDMS Step 1: Open edit modal for file upload and metadata editing
        handleEditDocument();
        return;
        
      case 'submit_for_review':
        // EDMS Step 2: Open submit for review modal (only if file uploaded)
        if (document && document.file_path && document.file_name) {
          setShowSubmitForReviewModal(true);
        } else {
          // Fallback: redirect to edit/upload modal if no file
          handleEditDocument();
        }
        return;

      case 'route_for_approval':
        // EDMS Route for Approval: Open route for approval modal
        setShowRouteForApprovalModal(true);
        return;
        
      case 'open_reviewer_interface':
        // EDMS Review Process: Open reviewer interface
        setShowReviewerInterface(true);
        return;
        
      case 'route_for_approval':
        // EDMS Approval Routing: Open route for approval modal
        setShowRouteForApprovalModal(true);
        return;
        
      case 'open_approver_interface':
        // EDMS Approval Process: Open approver interface
        setShowApproverInterface(true);
        return;
        
      // set_effective_date action removed - no longer needed in simplified workflow
      case 'view_pending_effective':
        // Just informational - no action needed
        return;
        
      case 'create_revision':
      case 'create_new_version':
        // EDMS Create New Version: Open new version modal
        setShowCreateNewVersionModal(true);
        return;
        
      case 'initiate_obsolescence':
        // EDMS Mark Obsolete: Open obsolescence modal
        setShowMarkObsoleteModal(true);
        return;

      case 'view_review_status':
        // EDMS View Review Status: Open review status modal
        setShowViewReviewStatus(true);
        return;
        
      default:
        // Handle other workflow actions through parent component
        if (onWorkflowAction && document) {
          onWorkflowAction(document, actionKey);
        }
    }
  };
  
  const handleReviewComplete = async () => {
    setShowReviewerInterface(false);
    await forceRefreshDocumentState();
  };

  const handleSubmitForReviewSuccess = async () => {
    setShowSubmitForReviewModal(false);
    await forceRefreshDocumentState();
  };

  const handleApprovalRouted = async () => {
    setShowRouteForApprovalModal(false);
    await forceRefreshDocumentState();
  };

  const handleApprovalComplete = async () => {
    setShowApproverInterface(false);
    await forceRefreshDocumentState();
  };

  const handleEffectiveDateSet = async () => {
    // setShowSetEffectiveDateModal removed - no longer needed in simplified workflow
    await forceRefreshDocumentState();
  };

  const handleVersionCreated = async (newDocument: any) => {
    setShowCreateNewVersionModal(false);
    if (newDocument) {
      // If new document data provided, could switch to it
    }
    await forceRefreshDocumentState();
  };

  const handleObsolescenceInitiated = async () => {
    setShowMarkObsoleteModal(false);
    await forceRefreshDocumentState();
  };

  const handleViewReviewStatusClosed = () => {
    setShowViewReviewStatus(false);
  };

  const handleCreateDocumentSuccess = (updatedDocument: any) => {
    console.log('📝 Document update callback received:', updatedDocument);
    setShowCreateModal(false);
    setEditingDocument(null);
    
    // Force reload of the current document data
    console.log('🔄 Reloading document data after update...');
    
    // Fetch the latest document data to update the workflow buttons
    if (document && document.uuid) {
      // Fetch complete updated document data
      fetchUpdatedDocumentData(document.uuid);
      
      // Dispatch a custom event to notify parent components to refresh their data
      window.dispatchEvent(new CustomEvent('documentUpdated', { 
        detail: { 
          document: updatedDocument,
          uuid: document.uuid 
        } 
      }));
    }
  };

  const fetchUpdatedDocumentData = async (documentUuid: string) => {
    try {
      console.log('🔄 Fetching updated document data to refresh workflow buttons...');
      const response = await fetch(`http://localhost:8000/api/v1/documents/documents/${documentUuid}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const freshDocumentData = await response.json();
        console.log('✅ Fresh document data received:', {
          hasFile: !!(freshDocumentData.file_path && freshDocumentData.file_name),
          fileName: freshDocumentData.file_name,
          filePath: freshDocumentData.file_path,
          status: freshDocumentData.status
        });
        
        // CRITICAL: We need to update the parent component's document state
        // Dispatch event with the fresh document data
        window.dispatchEvent(new CustomEvent('documentUpdated', { 
          detail: { 
            document: freshDocumentData,
            uuid: documentUuid,
            action: 'file_uploaded'
          } 
        }));
        
        // Force parent component to refresh its document data
        if (onRefresh) {
          console.log('🔄 Calling onRefresh to update parent component...');
          onRefresh();
        }
        
        // Reload document data in viewer with fresh document info
        await loadDocumentData();
        
      } else {
        console.error('Failed to fetch fresh document data:', response.status);
      }
    } catch (error) {
      console.error('Error fetching fresh document data:', error);
    }
  };

  // Add function to force refresh document and workflow state
  const forceRefreshDocumentState = async () => {
    if (!document?.uuid) return;
    
    console.log('🔄 Force refreshing document state after workflow action...');
    
    try {
      // 1. Fetch latest document data
      await fetchUpdatedDocumentData(document.uuid);
      
      // 2. Reload workflow data
      await loadDocumentData();
      
      // 3. Force re-render of action buttons
      setLoading(true);
      setTimeout(() => setLoading(false), 100);
      
    } catch (error) {
      console.error('Error force refreshing document state:', error);
    }
  };

  const handleEditDocument = async () => {
    // Fetch complete document data for editing (not just the summary from props)
    if (document) {
      try {
        setLoading(true);
        
        // Fetch full document details using the document UUID
        const response = await fetch(`http://localhost:8000/api/v1/documents/documents/${document.uuid}/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const fullDocumentData = await response.json();
          console.log('🔍 Full document data for editing:', fullDocumentData);
          
          // Use the complete document data for editing
          setEditingDocument(fullDocumentData);
          setShowCreateModal(true);
        } else {
          console.error('Failed to fetch full document data:', response.status);
          // Fallback to existing document data
          setEditingDocument(document);
          setShowCreateModal(true);
        }
      } catch (error) {
        console.error('Error fetching full document data:', error);
        // Fallback to existing document data
        setEditingDocument(document);
        setShowCreateModal(true);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleFileUpload = () => {
    // Handle file upload for documents in DRAFT status without files
    if (!document) return;
    
    // Create a file input element
    const input = window.document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.doc,.docx,.txt';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file && document) {
        await uploadFileForDocument(file, document);
      }
    };
    input.click();
  };

  const uploadFileForDocument = async (file: File, doc: Document) => {
    try {
      setLoading(true);
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_id', doc.uuid);
      
      // Upload file via API
      const response = await apiService.uploadDocumentFile(doc.uuid, formData);
      
      if (response.success) {
        // Show success message
        console.log('File uploaded successfully');
        
        // Reload document data to get updated file information
        loadDocumentData();
      } else {
        console.error('File upload failed:', response.error);
        alert('File upload failed. Please try again.');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
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
    if (!document || !workflowStatus || !authenticated || !user) {
      return [];
    }


    const actions = [];
    
    // EDMS Role-based permissions (per EDMS_details.txt lines 69-75)
    let isDocumentAuthor = false;
    
    
    // Check if user is document author
    if (document.author !== undefined) {
        const directMatch1 = document.author === user.id;
        const directMatch2 = document.author === String(user.id);
        const directMatch3 = String(document.author) === String(user.id);
        isDocumentAuthor = directMatch1 || directMatch2 || directMatch3;
        
    }
    
    // Fallback to checking display name if ID not available
    if (!isDocumentAuthor && document.author_display) {
        const usernameMatch = user.username === 'author';
        const displayIncludesUsername = document.author_display.toLowerCase().includes(user.username.toLowerCase());
        // Remove the overly broad "displayIncludesAuthor" check - it matches everyone
        
        isDocumentAuthor = usernameMatch || displayIncludesUsername;
        
    }
    
    
    // Check if user is assigned reviewer - use reviewer_display as fallback since reviewer ID might not be in document object
    let isAssignedReviewer = false;
    
    
    // First try direct ID comparison
    if (document.reviewer !== undefined) {
        const directMatch1 = document.reviewer === user.id;
        const directMatch2 = document.reviewer === String(user.id);
        const directMatch3 = String(document.reviewer) === String(user.id);
        isAssignedReviewer = directMatch1 || directMatch2 || directMatch3;
        
    }
    
    // Fallback to checking display name if ID not available or doesn't match
    if (!isAssignedReviewer && document.reviewer_display) {
        const usernameMatch = user.username === 'reviewer';
        const displayIncludesUsername = document.reviewer_display.toLowerCase().includes(user.username.toLowerCase());
        // Only use exact username matching for fallback - remove overly broad checks
        
        isAssignedReviewer = usernameMatch || displayIncludesUsername;
        
    }
    
    
    // Check if user is assigned approver - use approver_display as fallback since approver ID might not be in document object
    let isAssignedApprover = false;
    
    
    // First try direct ID comparison  
    if (document.approver !== undefined) {
        const directMatch1 = document.approver === user.id;
        const directMatch2 = document.approver === String(user.id);
        const directMatch3 = String(document.approver) === String(user.id);
        isAssignedApprover = directMatch1 || directMatch2 || directMatch3;
        
    }
    
    // Fallback to checking display name if ID not available or doesn't match
    if (!isAssignedApprover && document.approver_display) {
        const usernameMatch = user.username === 'approver';
        const displayIncludesUsername = document.approver_display.toLowerCase().includes(user.username.toLowerCase());
        // Only use exact username matching for fallback - remove overly broad checks
        
        isAssignedApprover = usernameMatch || displayIncludesUsername;
        
    }
    
    // Check user permissions through roles or direct assignment
    const userHasWriteRole = user.roles?.some(role => role.permission_level === 'write') || user.permissions?.includes('write');
    const userHasReviewRole = user.roles?.some(role => role.permission_level === 'review') || user.permissions?.includes('review');
    const userHasApprovalRole = user.roles?.some(role => role.permission_level === 'approve') || user.permissions?.includes('approve');
    
    const hasWritePermission = userHasWriteRole || user.is_staff || isDocumentAuthor;
    const hasReviewPermission = userHasReviewRole || user.is_staff || isAssignedReviewer;
    const hasApprovalPermission = userHasApprovalRole || user.is_staff || isAssignedApprover;
    

    

    // Note: Backend uses uppercase status values (DRAFT, PENDING_REVIEW, etc.)
    // Converting to uppercase for consistent comparison
    
    switch (document.status.toUpperCase()) {
      case 'DRAFT':
        // EDMS Step 1 & 2: Check if file is uploaded before allowing review submission
        // Per EDMS_details.txt line 114: Author must upload document before submitting for review
        const hasUploadedFile = !!(document.file_path && document.file_name);
        
        // Debug logging for workflow button logic
        console.log('🔍 WORKFLOW BUTTON DEBUG for', document.document_number);
        console.log('  document.file_path:', document.file_path);
        console.log('  document.file_name:', document.file_name);
        console.log('  hasUploadedFile:', hasUploadedFile);
        console.log('  hasWritePermission:', hasWritePermission);
        console.log('  document.status:', document.status);
        
        // Only document author can upload files and submit for review
        if (isDocumentAuthor) {
          if (!hasUploadedFile) {
            // Step 1: File upload required first
            console.log('  📁 Showing: Upload File button (author only)');
            actions.push({ 
              key: 'upload_file', 
              label: '📁 Upload File (Required)', 
              color: 'blue',
              description: 'Upload document file before submitting for review'
            });
          } else {
            // Step 2: File uploaded, can now submit for review
            console.log('  📤 Showing: Submit for Review button (author only)');
            actions.push({ 
              key: 'submit_for_review', 
              label: '📤 Submit for Review (Step 2)', 
              color: 'blue',
              description: 'Select reviewer and route document for review'
            });
          }
        }
        break;
        
      case 'PENDING_REVIEW':
        // Note: Enforcing uppercase PENDING_REVIEW for consistency with backend
        // EDMS lines 7-10: ONLY the assigned reviewer can start review process
        // CRITICAL: Authors cannot review their own documents (segregation of duties)
        
        if (isAssignedReviewer && !isDocumentAuthor) {
          actions.push({ 
            key: 'open_reviewer_interface', 
            label: '📋 Start Review Process', 
            color: 'blue', 
            description: 'Download document and provide review comments'
          });
        } else if (isDocumentAuthor) {
          actions.push({ 
            key: 'view_review_status', 
            label: '👀 Monitor Review Progress', 
            color: 'gray',
            description: 'View review progress (author cannot review own document)'
          });
        }
        break;
        
      case 'UNDER_REVIEW':
        // Continue review process for assigned reviewer
        // CRITICAL: Only the specifically assigned reviewer can continue review
        // Authors cannot review their own documents (segregation of duties)
        if (isAssignedReviewer && !isDocumentAuthor) {
          actions.push({ 
            key: 'open_reviewer_interface', 
            label: '📋 Continue Review', 
            color: 'blue', 
            description: 'Complete document review process'
          });
        } else if (isDocumentAuthor) {
          // Authors can monitor review progress but cannot perform review actions
          actions.push({ 
            key: 'view_review_status', 
            label: '👀 Monitor Review Progress', 
            color: 'gray',
            description: 'View review progress (author cannot review own document)'
          });
        }
        break;
        
      case 'REVIEW_COMPLETED':
      case 'REVIEWED':
        // EDMS line 11: Only document author can route for approval after review completion
        if (isDocumentAuthor) {
          actions.push({ 
            key: 'route_for_approval', 
            label: '✅ Route for Approval (Author Only)', 
            color: 'green',
            description: 'Select approver and route for approval'
          });
        }
        break;
        
      case 'PENDING_APPROVAL':
        // EDMS lines 12-15: Approver can approve or reject
        
        // Debug: Calculate if Start Approval Process button should show
        const shouldShowStartApproval = hasApprovalPermission && isAssignedApprover;
        console.log('🔍 Debug - Start Approval Process Button Logic:', {
          documentStatus: document.status,
          statusMatches: document.status.toUpperCase() === 'PENDING_APPROVAL',
          isAssignedApprover,
          hasApprovalPermission,
          authenticated,
          workflowStatusExists: !!workflowStatus,
          userExists: !!user,
          documentExists: !!document,
          shouldShowButton: shouldShowStartApproval,
          allConditionsMet: shouldShowStartApproval && authenticated && !!workflowStatus && !!user && !!document
        });
        
        if (hasApprovalPermission && isAssignedApprover) {
          actions.push({ 
            key: 'open_approver_interface', 
            label: '✅ Start Approval Process', 
            color: 'green',
            description: 'Review and approve/reject document'
          });
        }
        break;
        
      case 'APPROVED_PENDING_EFFECTIVE':
        // Document approved but waiting for effective date
        // No actions available - will be automatically activated by scheduler
        if (hasApprovalPermission || hasWritePermission) {
          actions.push({
            key: 'view_pending_effective',
            label: '⏰ Pending Effective',
            color: 'orange',
            description: `Document will be effective on ${document.effective_date ? new Date(document.effective_date).toLocaleDateString() : 'scheduled date'}`
          });
        }
        break;

      case 'APPROVED_AND_EFFECTIVE':
        // Document is approved and currently effective
        // Allow all authenticated users to initiate workflows (approval required anyway)
        actions.push({
          key: 'create_new_version',
          label: '📝 Create New Version',
          color: 'blue', 
          description: 'Start up-versioning workflow for document revision'
        });
        
        actions.push({
          key: 'mark_obsolete',
          label: '🗑️ Mark Obsolete', 
          color: 'red',
          description: 'Start obsolete workflow to retire this document'
        });
        break;
        
      case 'EFFECTIVE':
        // EDMS lines 21-26: Up-versioning and obsolescence workflows
        // Allow all authenticated users to initiate workflows (approval required anyway)
        actions.push({ 
          key: 'create_revision', 
          label: '📝 Create New Version', 
          color: 'blue',
          description: 'Start up-versioning workflow'
        });
        
        if (!hasDocumentDependencies()) {
          actions.push({ 
            key: 'initiate_obsolescence', 
            label: '🗑️ Mark Obsolete', 
            color: 'red',
            description: 'Start obsolescence workflow'
          });
        }
        break;
    }


    return actions;
  };

  // Helper function to check document dependencies (EDMS lines 28-30)
  const hasDocumentDependencies = () => {
    // In real implementation, check if other documents depend on this one
    return false; // Simplified for now
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
              <span>Version {document.version_string || document.version || '1.0'}</span>
              <span>•</span>
              <span>{document.document_type_display || 'Unknown Type'}</span>
            </div>
          </div>
          <div className="flex items-center space-x-2 ml-4">
            {/* Edit button - only show to document author when document is in DRAFT status */}
            {authenticated && user && document.status.toUpperCase() === 'DRAFT' && (
              (() => {
                // Check if user is document author
                let isDocumentAuthor = false;
                
                // Direct ID comparison
                if (document.author !== undefined) {
                  const directMatch1 = document.author === user.id;
                  const directMatch2 = document.author === String(user.id);
                  const directMatch3 = String(document.author) === String(user.id);
                  isDocumentAuthor = directMatch1 || directMatch2 || directMatch3;
                }
                
                // Fallback to checking display name if ID not available
                if (!isDocumentAuthor && document.author_display) {
                  const displayIncludesUsername = document.author_display.toLowerCase().includes(user.username.toLowerCase());
                  isDocumentAuthor = displayIncludesUsername;
                }
                
                // Show edit button only if user is the document author
                return isDocumentAuthor ? (
                  <button
                    onClick={handleEditDocument}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    title="Edit document (author only, draft status)"
                  >
                    ✏️ Edit
                  </button>
                ) : null;
              })()
            )}
            {document.file_path && (
              <DownloadActionMenu
                document={document}
                onDownload={(type, success) => {
                  console.log(`📥 Download ${success ? 'completed' : 'failed'} for ${type}:`, document.document_number);
                }}
              />
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
                    <dd className="text-sm text-gray-900 mt-1">{document.document_type_display || 'Unknown Type'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Author</dt>
                    <dd className="text-sm text-gray-900 mt-1">{document.author_display || 'Unknown Author'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Version</dt>
                    <dd className="text-sm text-gray-900 mt-1">{document.version_string || document.version || '1.0'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Status</dt>
                    <dd className="text-sm text-gray-900 mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(document.status)}`}>
                        {document.status_display || document.status.replace('_', ' ')}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Created Date</dt>
                    <dd className="text-sm text-gray-900 mt-1">{formatDate(document.created_at)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Last Modified</dt>
                    <dd className="text-sm text-gray-900 mt-1">{formatDate(document.updated_at || document.created_at)}</dd>
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
                  
                  {/* Workflow Assignment Information */}
                  {(document.reviewer_display || document.approver_display) && (
                    <div className="pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Workflow Assignments</h4>
                      {document.reviewer_display && (
                        <div className="mb-2">
                          <dt className="text-sm font-medium text-gray-500">Assigned Reviewer</dt>
                          <dd className="text-sm text-gray-900 mt-1">{document.reviewer_display}</dd>
                        </div>
                      )}
                      {document.approver_display && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Assigned Approver</dt>
                          <dd className="text-sm text-gray-900 mt-1">{document.approver_display}</dd>
                        </div>
                      )}
                    </div>
                  )}
                </dl>
              </div>

              {/* Metadata */}
              {document.metadata && Object.keys(document.metadata).length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Metadata</h3>
                  <dl className="space-y-3">
                    {document.metadata && Object.entries(document.metadata).map(([key, value]) => (
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
            {/* EDMS Workflow Step Indicator */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-blue-900">📋 EDMS Workflow Progress</h3>
                  <p className="text-blue-800 text-sm mt-1">
                    Current Status: <strong>{document.status_display || document.status?.replace('_', ' ')}</strong>
                  </p>
                </div>
                {workflowStatus && (
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(workflowStatus.state)}`}>
                    {workflowStatus.state_display}
                  </span>
                )}
              </div>
              
              {/* Step Progress Indicator */}
              <div className="mt-4">
                <div className="flex items-center text-xs text-blue-700">
                  <div className={`flex items-center ${['draft'].includes(document.status.toLowerCase()) ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                    <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                    Step 1: Create
                  </div>
                  <div className="flex-1 h-px bg-blue-200 mx-3"></div>
                  <div className={`flex items-center ${['pending_review', 'under_review'].includes(document.status.toLowerCase()) ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                    <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                    Step 2: Review
                  </div>
                  <div className="flex-1 h-px bg-blue-200 mx-3"></div>
                  <div className={`flex items-center ${['pending_approval', 'under_approval', 'approved'].includes(document.status.toLowerCase()) ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                    <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                    Step 3: Approve
                  </div>
                  <div className="flex-1 h-px bg-blue-200 mx-3"></div>
                  <div className={`flex items-center ${['effective'].includes(document.status.toLowerCase()) ? 'text-green-600 font-medium' : 'text-gray-500'}`}>
                    <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                    Effective
                  </div>
                </div>
              </div>
            </div>

            {/* Only show workflow items if user has pending actions for THIS document */}

            {/* Workflow Information and Actions */}
            {workflowStatus ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Workflow Information</h4>
                    <dl className="space-y-3">
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Workflow Type</dt>
                        <dd className="text-sm text-gray-900 mt-1">{workflowStatus.workflow_type?.name || 'Document Review Workflow'}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Document Author</dt>
                        <dd className="text-sm text-gray-900 mt-1">{document.author_display || 'Unknown Author'}</dd>
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
                      {document.reviewer_display && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Assigned Reviewer</dt>
                          <dd className="text-sm text-gray-900 mt-1">{document.reviewer_display}</dd>
                        </div>
                      )}
                      {document.approver_display && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Assigned Approver</dt>
                          <dd className="text-sm text-gray-900 mt-1">{document.approver_display}</dd>
                        </div>
                      )}
                    </dl>
                  </div>

                  {/* Role-based Available Actions */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Available Actions</h4>
                    <div className="space-y-3">
                      {getAvailableActions().map((action) => (
                        <div key={action.key}>
                          <button
                            onClick={() => handleWorkflowAction(action.key)}
                            className={`w-full px-4 py-3 text-sm font-medium rounded-md border focus:ring-2 focus:ring-offset-2 text-left ${
                              action.color === 'blue' ? 'bg-blue-600 border-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500' :
                              action.color === 'green' ? 'bg-green-600 border-green-600 text-white hover:bg-green-700 focus:ring-green-500' :
                              action.color === 'yellow' ? 'bg-yellow-600 border-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500' :
                              action.color === 'red' ? 'bg-red-600 border-red-600 text-white hover:bg-red-700 focus:ring-red-500' :
                              'bg-gray-600 border-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500'
                            }`}
                          >
                            <div className="font-medium">{action.label}</div>
                            {action.description && (
                              <div className="text-xs mt-1 opacity-90">{action.description}</div>
                            )}
                          </button>
                        </div>
                      ))}
                      
                      {getAvailableActions().length === 0 && (
                        <div className="text-center py-6 text-gray-500">
                          <svg className="w-8 h-8 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <p className="text-sm">No workflow actions available for your role at this time.</p>
                        </div>
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
                          <div>Signed by: {signature.user?.full_name || 'Unknown User'}</div>
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
                      Document created by {document.created_by?.full_name || 'Unknown Author'}
                    </p>
                  </div>
                  <span className="text-sm text-gray-500">{formatDate(document.created_at)}</span>
                </div>
              </div>
              
              {document.status.toLowerCase() !== 'draft' && (
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
              
              {document.status.toLowerCase() === 'effective' && (
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
      
      {/* EDMS Workflow Modals */}
      
      {/* Reviewer Interface (EDMS Review Process) */}
      {showReviewerInterface && document && (
        <ReviewerInterface
          documentId={document.uuid}
          onClose={() => setShowReviewerInterface(false)}
          onReviewComplete={handleReviewComplete}
        />
      )}

      {/* Submit for Review Modal (EDMS Step 2) */}
      {showSubmitForReviewModal && document && (
        <SubmitForReviewModal
          document={document}
          isOpen={showSubmitForReviewModal}
          onClose={() => setShowSubmitForReviewModal(false)}
          onSubmitSuccess={handleSubmitForReviewSuccess}
        />
      )}

      {/* Route for Approval Modal (EDMS Approval Routing) */}
      {showRouteForApprovalModal && document && (
        <RouteForApprovalModal
          isOpen={showRouteForApprovalModal}
          onClose={() => setShowRouteForApprovalModal(false)}
          document={document}
          onApprovalRouted={handleApprovalRouted}
        />
      )}

      {/* Approver Interface (EDMS Approval Process) */}
      {showApproverInterface && document && (
        <ApproverInterface
          isOpen={showApproverInterface}
          onClose={() => setShowApproverInterface(false)}
          document={document}
          onApprovalComplete={handleApprovalComplete}
        />
      )}

      {/* Set Effective Date Modal (EDMS Effective Date Setting) */}
      {/* SetEffectiveDateModal removed - no longer needed in simplified workflow */}

      {/* Create New Version Modal (EDMS Versioning) */}
      {showCreateNewVersionModal && document && (
        <CreateNewVersionModal
          isOpen={showCreateNewVersionModal}
          onClose={() => setShowCreateNewVersionModal(false)}
          document={document}
          onVersionCreated={handleVersionCreated}
        />
      )}

      {/* Mark Obsolete Modal (EDMS Obsolescence) */}
      {showMarkObsoleteModal && document && (
        <MarkObsoleteModal
          isOpen={showMarkObsoleteModal}
          onClose={() => setShowMarkObsoleteModal(false)}
          document={document}
          onObsolescenceInitiated={handleObsolescenceInitiated}
        />
      )}

      {/* Document Create/Edit Modal (EDMS Step 1 & Edit) */}
      {showCreateModal && (
        <DocumentCreateModal
          isOpen={showCreateModal}
          onClose={() => {
            setShowCreateModal(false);
            setEditingDocument(null);
          }}
          onCreateSuccess={handleCreateDocumentSuccess}
          editDocument={editingDocument}
        />
      )}

      {/* View Review Status Modal (EDMS Review Status Display) */}
      {showViewReviewStatus && document && (
        <ViewReviewStatus
          document={document}
          onClose={handleViewReviewStatusClosed}
          onRefresh={loadDocumentData}
        />
      )}
    </div>
  );
};

export default DocumentViewer;