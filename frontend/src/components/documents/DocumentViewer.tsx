import React, { useState, useEffect } from 'react';
import { Document, WorkflowInstance, ElectronicSignature } from '../../types/api';
import UnifiedWorkflowInterface from '../workflows/UnifiedWorkflowInterface.tsx';
import SubmitForReviewModalUnified from '../workflows/SubmitForReviewModalUnified.tsx';
import RouteForApprovalModalUnified from '../workflows/RouteForApprovalModalUnified.tsx';
// SetEffectiveDateModal removed - no longer needed in simplified workflow
import CreateNewVersionModal from '../workflows/CreateNewVersionModal.tsx';
import MarkObsoleteModal from '../workflows/MarkObsoleteModal.tsx';
import ViewReviewStatus from '../workflows/ViewReviewStatus.tsx';
import TerminateDocumentModal from './TerminateDocumentModal.tsx';
import DownloadActionMenu from './DownloadActionMenu.tsx';
import DocumentCreateModal from './DocumentCreateModal.tsx';
import WorkflowHistory from '../workflows/WorkflowHistory.tsx';
import PeriodicReviewModal from './PeriodicReviewModal.tsx';
import { useAuth } from '../../contexts/AuthContext.tsx';
import apiService from '../../services/api.ts';

// Helper function to format dates
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return 'Invalid Date';
  }
};

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
  // TODO: Electronic Signatures feature exists but not operational - hidden until tested and documented
  const [activeTab, setActiveTab] = useState<'details' | 'workflow' | 'history'>('details');
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowInstance | null>(null);
  const [signatures, setSignatures] = useState<ElectronicSignature[]>([]);
  const [completeDocument, setCompleteDocument] = useState<Document | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showUnifiedWorkflowInterface, setShowUnifiedWorkflowInterface] = useState(false);
  const [workflowMode, setWorkflowMode] = useState<'review' | 'approval'>('review');
  
  // Workflow modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);
  const [showSubmitForReviewModal, setShowSubmitForReviewModal] = useState(false);
  const [showRouteForApprovalModal, setShowRouteForApprovalModal] = useState(false);
  // showSetEffectiveDateModal removed - no longer needed in simplified workflow
  const [showCreateNewVersionModal, setShowCreateNewVersionModal] = useState(false);
  const [showMarkObsoleteModal, setShowMarkObsoleteModal] = useState(false);
  const [showViewReviewStatus, setShowViewReviewStatus] = useState(false);
  const [showTerminateModal, setShowTerminateModal] = useState(false);
  const [isTerminating, setIsTerminating] = useState(false);
  const [showPeriodicReviewModal, setShowPeriodicReviewModal] = useState(false);
  const [periodicReviewContext, setPeriodicReviewContext] = useState<{
    outcome: string;
    comments: string;
    nextReviewMonths: number;
  } | null>(null);
  
  // Auth context for role-based visibility
  const { authenticated, user } = useAuth();

  useEffect(() => {
    if (document) {
      // Reset complete document when document prop changes
      setCompleteDocument(null);
      loadDocumentData();
    }
  }, [document]);

  const loadDocumentData = async () => {
    if (!document) return;
    try {
      // CRITICAL FIX: Fetch complete document data first to ensure we have description and all fields
      // List endpoint doesn't include description, but detail endpoint does
      const completeDocumentResponse = await fetch(`/api/v1/documents/documents/${document.uuid}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (completeDocumentResponse.ok) {
        const fetchedCompleteDocument = await completeDocumentResponse.json();
        console.log('✅ DocumentViewer: Fetched complete document with description:', {
          uuid: fetchedCompleteDocument.uuid,
          title: fetchedCompleteDocument.title,
          description: fetchedCompleteDocument.description,
          hasDescription: !!fetchedCompleteDocument.description
        });
        
        // DEBUG: Check dependencies data
        console.log('🔍 DEPENDENCIES DEBUG:', {
          hasDependenciesKey: 'dependencies' in fetchedCompleteDocument,
          dependenciesValue: fetchedCompleteDocument.dependencies,
          dependenciesType: typeof fetchedCompleteDocument.dependencies,
          dependenciesLength: fetchedCompleteDocument.dependencies?.length,
          hasDependentsKey: 'dependents' in fetchedCompleteDocument,
          dependentsValue: fetchedCompleteDocument.dependents,
          dependentsLength: fetchedCompleteDocument.dependents?.length,
          allKeys: Object.keys(fetchedCompleteDocument)
        });
        
        // CRITICAL FIX: Store complete document data in state for display
        setCompleteDocument(fetchedCompleteDocument);
        
        // Update parent component with complete document data
        window.dispatchEvent(new CustomEvent('documentUpdated', { 
          detail: { 
            document: fetchedCompleteDocument,
            uuid: document.uuid,
            action: 'complete_data_loaded'
          } 
        }));
      }
      
      // Fetch real workflow status from backend - but only if we have valid IDs
      const apiCalls = [];
      
      // Add workflow status call if we have document UUID
      if (document.uuid) {
        apiCalls.push(
          fetch(`/api/v1/workflows/documents/${document.uuid}/status/`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
              'Content-Type': 'application/json',
            },
          }).then(res => res.ok ? res.json() : null).catch(() => null)
        );
      } else {
        apiCalls.push(Promise.resolve(null));
      }
      
      // Add signatures call if we have document ID
      if (document.id && document.id !== undefined) {
        apiCalls.push(
          fetch(`/api/v1/security/signatures/?document_id=${document.id}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
              'Content-Type': 'application/json',
            },
          }).then(res => res.ok ? res.json() : null).catch(() => null)
        );
      } else {
        apiCalls.push(Promise.resolve(null));
      }

      const [workflowResponse, signaturesResponse] = await Promise.all(apiCalls);

      // Use real data only - no mock data fallback
      setWorkflowStatus(workflowResponse || null);
      setSignatures(signaturesResponse?.results || []);

      // Set document preview URL
      if (document.file_path) {
        setPreviewUrl(`/api/v1/documents/${document.id}/preview/`);
      }

    } catch (error) {
      console.error('Failed to load document data:', error);
      setWorkflowStatus(null);
      setSignatures([]);
    }
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
        // EDMS Review Process: Open unified workflow interface for review
        setWorkflowMode('review');
        setShowUnifiedWorkflowInterface(true);
        return;
        
      case 'open_approver_interface':
        // EDMS Approval Process: Open unified workflow interface for approval
        setWorkflowMode('approval');
        setShowUnifiedWorkflowInterface(true);
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
        
      case 'mark_obsolete':
      case 'initiate_obsolescence':
        // EDMS Mark Obsolete: Open obsolescence modal
        setShowMarkObsoleteModal(true);
        return;

      case 'view_review_status':
        // EDMS View Review Status: Open review status modal
        setShowViewReviewStatus(true);
        return;
        
      case 'terminate_document':
        // EDMS Terminate Document: Open terminate modal
        setShowTerminateModal(true);
        return;
      
      case 'complete_periodic_review':
        // Periodic Review: Open periodic review modal
        setShowPeriodicReviewModal(true);
        return;
        
      default:
        // Handle other workflow actions through parent component
        if (onWorkflowAction && document) {
          onWorkflowAction(document, actionKey);
        }
    }
  };
  
  const handleWorkflowComplete = async () => {
    setShowUnifiedWorkflowInterface(false);
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

  // Removed unused handleEffectiveDateSet function

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

  // Removed unused handleTerminateClick function

  const handleTerminateConfirm = async (reason: string) => {
    if (!document) return;
    
    setIsTerminating(true);
    try {
      // Call the termination API using document ID (backend terminate endpoint expects integer ID)
      console.log('🛑 Terminating document:', {
        uuid: document.uuid,
        id: document.id,
        pk: document.pk,
        document_number: document.document_number,
        completeDocument: completeDocument
      });
      
      // Try to get document ID from complete document data first, then fallback to document prop
      let documentId = completeDocument?.id || document.id;
      
      // If we still don't have an ID, fetch the complete document to get the ID
      if (!documentId && document.uuid) {
        console.log('📡 Fetching document ID from UUID for termination...');
        const response = await fetch(`/api/v1/documents/documents/${document.uuid}/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const fetchedDocument = await response.json();
          documentId = fetchedDocument.id;
          console.log('✅ Retrieved document ID for termination:', documentId);
        } else {
          throw new Error('Failed to fetch document ID for termination');
        }
      }
      
      if (!documentId) {
        console.error('Document object:', document);
        console.error('Complete document object:', completeDocument);
        throw new Error('Document ID is required for termination but could not be retrieved');
      }
      
      console.log('🛑 Using document ID for termination:', documentId);
      
      await apiService.post(`/documents/documents/${documentId}/terminate/`, {
        reason: reason
      });
      
      setShowTerminateModal(false);
      
      // Show success message
      console.log(`Document ${document.document_number} has been terminated successfully.`);
      
      // Clear selection since terminated documents are hidden from the list
      window.dispatchEvent(new CustomEvent('clearDocumentSelection'));
      
      // Refresh document state
      await forceRefreshDocumentState();
      
    } catch (error: any) {
      console.error('Failed to terminate document:', error);
      // You might want to show an error toast here
      alert(`Error: ${error.response?.data?.error || 'Failed to terminate document'}`);
    } finally {
      setIsTerminating(false);
    }
  };

  const handleTerminateCancel = () => {
    setShowTerminateModal(false);
  };

  const handleCreateDocumentSuccess = (updatedDocument: any) => {
    console.log('📝 Document update callback received:', updatedDocument);
    setShowCreateModal(false);
    setEditingDocument(null);
    
    // Force reload of the current document data
    
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
      const response = await fetch(`/api/v1/documents/documents/${documentUuid}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const freshDocumentData = await response.json();
        
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
    
    
    try {
      // 1. Fetch latest document data
      await fetchUpdatedDocumentData(document.uuid);
      
      // 2. Reload workflow data
      await loadDocumentData();
      
      // 3. Force re-render of action buttons
      // Loading state removed - not needed for UI refresh
      
    } catch (error) {
      console.error('Error force refreshing document state:', error);
    }
  };

  const handleEditDocument = async () => {
    // Fetch complete document data for editing (not just the summary from props)
    if (document) {
      try {
        // Fetch full document details using the document UUID
        const response = await fetch(`/api/v1/documents/documents/${document.uuid}/`, {
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
      }
    }
  };

  // Removed unused handleFileUpload function

  const uploadFileForDocument = async (file: File, doc: Document) => {
    try {
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
    const hasApprovalPermission = userHasApprovalRole || user.is_staff || isAssignedApprover;
    

    

    // Note: Backend uses uppercase status values (DRAFT, PENDING_REVIEW, etc.)
    // Converting to uppercase for consistent comparison
    
    switch (document.status.toUpperCase()) {
      case 'DRAFT':
        // EDMS Step 1 & 2: Check if file is uploaded before allowing review submission
        // Per EDMS_details.txt line 114: Author must upload document before submitting for review
        const hasUploadedFile = !!(document.file_path && document.file_name);
        
        
        // Only document author can upload files and submit for review
        if (isDocumentAuthor) {
          if (!hasUploadedFile) {
            // Step 1: File upload required first
            actions.push({ 
              key: 'upload_file', 
              label: '📁 Upload File (Required)', 
              color: 'blue',
              description: 'Upload document file before submitting for review'
            });
          } else {
            // Step 2: File uploaded, can now submit for review
            actions.push({ 
              key: 'submit_for_review', 
              label: '📤 Submit for Review', 
              color: 'blue',
              description: 'Select reviewer and route document for review'
            });
          }
          
          // Terminate button - available to document author for pre-effective statuses
          actions.push({
            key: 'terminate_document',
            label: '🗑️ Terminate Document',
            color: 'red',
            description: 'Permanently terminate this document (irreversible)'
          });
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
        
        // Terminate button - available to document author for pre-effective statuses
        if (isDocumentAuthor) {
          actions.push({
            key: 'terminate_document',
            label: '🗑️ Terminate Document',
            color: 'red',
            description: 'Permanently terminate this document (irreversible)'
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
        
        // Terminate button - available to document author for pre-effective statuses
        if (isDocumentAuthor) {
          actions.push({
            key: 'terminate_document',
            label: '🗑️ Terminate Document',
            color: 'red',
            description: 'Permanently terminate this document (irreversible)'
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
          
          // Terminate button - available to document author for pre-effective statuses
          actions.push({
            key: 'terminate_document',
            label: '🗑️ Terminate Document',
            color: 'red',
            description: 'Permanently terminate this document (irreversible)'
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
        
        // Terminate button - available to document author for pre-effective statuses
        if (isDocumentAuthor) {
          actions.push({
            key: 'terminate_document',
            label: '🗑️ Terminate Document',
            color: 'red',
            description: 'Permanently terminate this document (irreversible)'
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

      case 'EFFECTIVE':
        // Document is approved and currently effective
        // Show Periodic Review button if document needs review
        if (document.next_review_date && new Date(document.next_review_date) <= new Date()) {
          actions.push({
            key: 'complete_periodic_review',
            label: '📋 Complete Periodic Review',
            color: 'orange',
            description: 'Complete periodic review for regulatory compliance'
          });
        }
        
        // Allow all authenticated users to initiate up-versioning (approval required anyway)
        actions.push({
          key: 'create_new_version',
          label: '📝 Create New Version',
          color: 'blue', 
          description: 'Start up-versioning workflow for document revision'
        });
        
        // Mark Obsolete - only show to authorized users (approvers/admins)
        // Match backend authorization: user == document.approver || user.is_staff || user.is_superuser
        const canObsolete = (
          isAssignedApprover || // Document approver
          user.is_staff ||      // System admin
          user.is_superuser     // Superuser
        );
        
        if (canObsolete) {
          actions.push({
            key: 'mark_obsolete',
            label: '🗑️ Mark Obsolete', 
            color: 'red',
            description: 'Start obsolete workflow to retire this document'
          });
        }
        break;
    }


    return actions;
  };

  // Removed unused hasDocumentDependencies function

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
              <span>{document.base_document_number || document.document_number?.split('-v')[0] || document.document_number}</span>
              <span>•</span>
              <span>Version {document.version_string || document.version || '1.0'}</span>
              <span>•</span>
              <span>
                {document.document_type_display || 
                 (document.document_type && typeof document.document_type === 'object' 
                   ? document.document_type.name 
                   : document.document_type) || 
                 'Unknown Type'}
              </span>
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
            {/* Clear Selection Button */}
            <button
              onClick={() => {
                // Call the parent's onDocumentSelect with null to clear selection
                // This requires updating the DocumentManagement to handle null selection
                if (onClose) {
                  onClose(); // For full viewer mode
                } else {
                  // For split view, dispatch a custom event to clear selection
                  window.dispatchEvent(new CustomEvent('clearDocumentSelection'));
                }
              }}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              title="Clear selection"
            >
              ✖️ Clear
            </button>
            
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
          {/* 'signatures' tab hidden - TODO: Implement and test Electronic Signatures feature */}
          {['details', 'workflow', 'history'].map((tab) => (
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
          <div className="space-y-8">
            {/* Document Information - Optimized Single Column Layout */}
            <div className="max-w-4xl">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-6">Document Information</h3>
                
                {/* Optimized Grid Layout */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
                  {/* Column 1: Basic Information */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-gray-700 border-b border-gray-200 pb-2">Basic Details</h4>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Document Type</dt>
                      <dd className="text-sm text-gray-900 mt-1">
                        {document.document_type_display || 
                         (document.document_type && typeof document.document_type === 'object' 
                           ? document.document_type.name 
                           : document.document_type) || 
                         'Unknown Type'}
                      </dd>
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
                      <dt className="text-sm font-medium text-gray-500">Author</dt>
                      <dd className="text-sm text-gray-900 mt-1">{document.author_display || 'Unknown Author'}</dd>
                    </div>
                  </div>
                  
                  {/* Column 2: Dates and Lifecycle */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-gray-700 border-b border-gray-200 pb-2">Timeline</h4>
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
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Next Review Date</dt>
                      <dd className="text-sm text-gray-900 mt-1">
                        {document.next_review_date ? (
                          <>
                            {formatDate(document.next_review_date)}
                            {new Date(document.next_review_date) < new Date() && (
                              <span className="ml-2 text-red-600 text-xs font-medium">(Overdue)</span>
                            )}
                          </>
                        ) : (
                          <span className="text-gray-500">None</span>
                        )}
                      </dd>
                    </div>
                    {document.last_review_date && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Last Review Date</dt>
                        <dd className="text-sm text-gray-900 mt-1">
                          {formatDate(document.last_review_date)}
                          {document.last_reviewed_by_display && (
                            <span className="text-xs text-gray-500"> by {document.last_reviewed_by_display}</span>
                          )}
                        </dd>
                      </div>
                    )}
                  </div>
                  
                  {/* Column 3: Description and Additional Info */}
                  <div className="space-y-3 md:col-span-2 lg:col-span-1">
                    <h4 className="text-sm font-semibold text-gray-700 border-b border-gray-200 pb-2">Description</h4>
                    <div>
                      <dd className="text-sm text-gray-900">{(completeDocument?.description || document.description) || 'No description provided'}</dd>
                    </div>
                  </div>

                </div>
                
                {/* Obsolescence Information - Full Width Alert */}
                {(document.status === 'SCHEDULED_FOR_OBSOLESCENCE' || document.obsolescence_date) && (
                  <div className="mt-6 border-l-4 border-orange-400 bg-orange-50 p-4 rounded">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="ml-3 flex-1">
                        <h4 className="text-sm font-medium text-orange-800 mb-2">
                          📅 Scheduled for Obsolescence
                        </h4>
                        <div className="space-y-1">
                          {document.obsolescence_date && (
                            <div>
                              <dt className="inline text-xs font-medium text-orange-700">Obsolescence Date: </dt>
                              <dd className="inline text-sm text-orange-800 font-medium">
                                {formatDate(document.obsolescence_date)}
                              </dd>
                            </div>
                          )}
                          {document.obsolescence_reason && (
                            <div>
                              <dt className="inline text-xs font-medium text-orange-700">Reason: </dt>
                              <dd className="inline text-sm text-orange-800">{document.obsolescence_reason}</dd>
                            </div>
                          )}
                          {(document.obsoleted_by_display || document.obsoleted_by) && (
                            <div>
                              <dt className="inline text-xs font-medium text-orange-700">Initiated By: </dt>
                              <dd className="inline text-sm text-orange-800">{document.obsoleted_by_display || document.obsoleted_by}</dd>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Document Dependencies Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">🔗 Document Dependencies</h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Dependencies - What this document depends on */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold text-gray-700">📥 Dependencies</h4>
                  </div>
                  
                  {(completeDocument?.dependencies || document.dependencies) && (completeDocument?.dependencies || document.dependencies).length > 0 ? (
                    <div className="space-y-3">
                      {(completeDocument?.dependencies || document.dependencies).map((dep: any) => (
                        <div key={dep.id} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="text-sm font-medium text-blue-900">
                                  {dep.depends_on_display || `Document ${dep.depends_on}`}
                                </span>
                                {dep.is_critical && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    Critical
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center space-x-2 text-xs text-blue-700">
                                <span className="capitalize">{(dep.dependency_type_display || dep.dependency_type || 'references').toLowerCase()}</span>
                                {dep.created_at && (
                                  <>
                                    <span>•</span>
                                    <span>Added {formatDate(dep.created_at)}</span>
                                  </>
                                )}
                              </div>
                              {dep.description && (
                                <p className="text-xs text-blue-600 mt-1">{dep.description}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6">
                      <div className="text-gray-400 mb-2">
                        <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                      </div>
                      <p className="text-sm text-gray-500">No dependencies</p>
                      <p className="text-xs text-gray-400 mt-1">This document does not depend on other documents</p>
                    </div>
                  )}
                </div>

                {/* Dependents - What depends on this document */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold text-gray-700">📤 Dependents</h4>
                  </div>
                  
                  {(completeDocument?.dependents || document.dependents) && (completeDocument?.dependents || document.dependents).length > 0 ? (
                    <div className="space-y-3">
                      {(completeDocument?.dependents || document.dependents).map((dep: any) => (
                        <div key={dep.id} className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="text-sm font-medium text-green-900">
                                  {dep.document_display || `Document ${dep.document}`}
                                </span>
                                {dep.is_critical && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    Critical
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center space-x-2 text-xs text-green-700">
                                <span className="capitalize">{(dep.dependency_type_display || dep.dependency_type || 'references').toLowerCase()}</span>
                                {dep.created_at && (
                                  <>
                                    <span>•</span>
                                    <span>Added {formatDate(dep.created_at)}</span>
                                  </>
                                )}
                              </div>
                              {dep.description && (
                                <p className="text-xs text-green-600 mt-1">{dep.description}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6">
                      <div className="text-gray-400 mb-2">
                        <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                      </div>
                      <p className="text-sm text-gray-500">No dependents</p>
                      <p className="text-xs text-gray-400 mt-1">No other documents depend on this one</p>
                    </div>
                  )}
                </div>
              </div>
              
            </div>

            {/* Workflow Assignment Information */}
            <div>
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

              {/* Metadata */}
              {document.metadata && Object.keys(document.metadata).length > 0 && (
                <div className="pt-4 border-t border-gray-200">
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
                    Created
                  </div>
                  <div className="flex-1 h-px bg-blue-200 mx-3"></div>
                  <div className={`flex items-center ${['pending_review', 'under_review'].includes(document.status.toLowerCase()) ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                    <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                    Under Review
                  </div>
                  <div className="flex-1 h-px bg-blue-200 mx-3"></div>
                  <div className={`flex items-center ${['pending_approval', 'under_approval', 'approved'].includes(document.status.toLowerCase()) ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                    <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                    Approved
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

        {activeTab === 'signatures' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Digital Signatures</h3>
              {/* Electronic Signature Section */}
              {(document.status === 'EFFECTIVE') && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-4">
                    This document is approved and effective. Electronic signatures can be applied.
                  </p>
                  <button
                    onClick={() => setShowSignModal(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Sign Document
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Document History</h3>
              <WorkflowHistory document={document} />
            </div>
          </div>
        )}
      </div>

      {/* EDMS Workflow Modals */}
      
      {/* Unified Workflow Interface (EDMS Review & Approval Process) */}
      {showUnifiedWorkflowInterface && document && (
        <UnifiedWorkflowInterface
          isOpen={showUnifiedWorkflowInterface}
          onClose={() => setShowUnifiedWorkflowInterface(false)}
          document={document}
          mode={workflowMode}
          onComplete={handleWorkflowComplete}
        />
      )}

      {/* Submit for Review Modal (EDMS Step 2) */}
      {showSubmitForReviewModal && document && (
        <SubmitForReviewModalUnified
          document={document}
          isOpen={showSubmitForReviewModal}
          onClose={() => setShowSubmitForReviewModal(false)}
          onSubmitSuccess={handleSubmitForReviewSuccess}
        />
      )}

      {/* Route for Approval Modal (EDMS Approval Routing) */}
      {showRouteForApprovalModal && document && (
        <RouteForApprovalModalUnified
          isOpen={showRouteForApprovalModal}
          onClose={() => setShowRouteForApprovalModal(false)}
          document={document}
          onApprovalRouted={handleApprovalRouted}
        />
      )}

      {/* Set Effective Date Modal (EDMS Effective Date Setting) */}
      {/* SetEffectiveDateModal removed - no longer needed in simplified workflow */}

      {/* Create New Version Modal (EDMS Versioning) */}
      {showCreateNewVersionModal && document && (
        <CreateNewVersionModal
          isOpen={showCreateNewVersionModal}
          onClose={() => {
            setShowCreateNewVersionModal(false);
            setPeriodicReviewContext(null); // Clear stored comments
          }}
          document={document}
          onVersionCreated={async (newDocument: any) => {
            // If this was triggered by periodic review, complete the review now
            if (periodicReviewContext) {
              try {
                await apiService.completePeriodicReview(document.uuid, {
                  outcome: periodicReviewContext.outcome,
                  comments: periodicReviewContext.comments,
                  next_review_months: periodicReviewContext.nextReviewMonths
                });
                console.log('✅ Periodic review completed with outcome:', periodicReviewContext.outcome);
                alert('✅ Periodic review completed successfully!\n\nOutcome: ' + periodicReviewContext.outcome + '\nNew version created: ' + (newDocument?.document_number || 'created'));
              } catch (error) {
                console.error('Failed to complete periodic review:', error);
                alert('⚠️ Version created but failed to complete periodic review. Please contact administrator.');
              }
              setPeriodicReviewContext(null); // Clear stored context
            }
            
            // Call original success handler
            handleVersionCreated(newDocument);
          }}
        />
      )}

      {/* Mark Obsolete Modal (EDMS Obsolescence) */}
      {showMarkObsoleteModal && document && (
        <MarkObsoleteModal
          isOpen={showMarkObsoleteModal}
          onClose={() => setShowMarkObsoleteModal(false)}
          onSuccess={handleObsolescenceInitiated}
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

      {/* Terminate Document Modal (EDMS Termination Process) */}
      {showTerminateModal && document && (
        <TerminateDocumentModal
          isOpen={showTerminateModal}
          onClose={handleTerminateCancel}
          onConfirm={handleTerminateConfirm}
          documentNumber={document.document_number}
          documentTitle={document.title}
          isLoading={isTerminating}
        />
      )}

      {/* Periodic Review Modal */}
      {showPeriodicReviewModal && document && (
        <PeriodicReviewModal
          isOpen={showPeriodicReviewModal}
          onClose={() => setShowPeriodicReviewModal(false)}
          document={document}
          onSuccess={async () => {
            setShowPeriodicReviewModal(false);
            await forceRefreshDocumentState();
          }}
          onUpversion={(reviewContext) => {
            // Store review context and open version creation modal
            setPeriodicReviewContext(reviewContext);
            setShowPeriodicReviewModal(false);
            setShowCreateNewVersionModal(true);
          }}
        />
      )}
    </div>
  );
};

export default DocumentViewer;