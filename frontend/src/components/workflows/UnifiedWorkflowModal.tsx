/**
 * Unified Workflow Assignment Modal
 * 
 * Replaces both SubmitForReviewModal and RouteForApprovalModal with a single,
 * configurable component that handles both reviewer and approver assignment.
 * Includes enhanced rejection workflow awareness.
 */

import React, { useState, useEffect } from 'react';
import { RejectionHistoryModal } from './rejection/RejectionHistoryModal.tsx';

interface User {
  id: string;
  username: string;
  full_name: string;
  first_name: string;
  last_name: string;
  email: string;
  active_roles?: Array<{ name: string; permission_level: string }>;
  is_superuser: boolean;
}

type WorkflowAction = 'submit_for_review' | 'route_for_approval';

interface UnifiedWorkflowModalProps {
  // Core props
  document: any;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  
  // Configuration props (determines modal behavior)
  workflowAction: WorkflowAction;
  title?: string;
  description?: string;
  theme?: 'blue' | 'green';
  
  // Enhanced rejection workflow props
  enableRejectionAwareness?: boolean;
}

const UnifiedWorkflowModal: React.FC<UnifiedWorkflowModalProps> = ({
  document,
  isOpen,
  onClose,
  onSuccess,
  workflowAction,
  title,
  description,
  theme,
  enableRejectionAwareness = true
}) => {
  // Unified state management
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [users, setUsers] = useState<User[]>([]);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Rejection awareness state
  const [showRejectionHistory, setShowRejectionHistory] = useState(false);
  const [rejectionWarnings, setRejectionWarnings] = useState<any[]>([]);
  const [showWarnings, setShowWarnings] = useState(false);
  const [acknowledgeWarnings, setAcknowledgeWarnings] = useState(false);
  const [recommendations, setRecommendations] = useState<any>(null);
  
  // Use direct fetch instead of useApi hook to avoid dependency issues
  const apiCall = async (url: string, options: any = {}) => {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(`/api/v1${url}`, {
      method: options.method || 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: options.data ? JSON.stringify(options.data) : undefined
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return { success: true, ...data };
  };

  // Dynamic configuration based on workflow action
  const config = {
    submit_for_review: {
      title: 'Submit for Review',
      userType: 'reviewer',
      userTypePlural: 'reviewers',
      roleFilters: ['Document Reviewer', 'Document Approver', 'Senior Document Approver'],
      permissionLevels: ['review', 'approve'],
      apiAction: 'submit_for_review',
      fieldName: 'reviewer',
      theme: 'blue',
      icon: '📤',
      successMessage: 'Document submitted for review successfully',
      nextStepInfo: 'The document will be moved to PENDING_REVIEW status and the selected reviewer will be notified.',
      workflowStep: 'EDMS Workflow Step 2: Author selects reviewer and routes document for review'
    },
    route_for_approval: {
      title: 'Route for Approval',
      userType: 'approver',
      userTypePlural: 'approvers',
      roleFilters: ['Document Approver', 'Senior Document Approver'],
      permissionLevels: ['approve'],
      apiAction: 'route_for_approval',
      fieldName: 'approver_id',
      theme: 'green',
      icon: '✅',
      successMessage: 'Document routed for approval successfully',
      nextStepInfo: 'The document will be moved to PENDING_APPROVAL status and the selected approver will be notified.',
      workflowStep: 'EDMS Workflow: Route reviewed document for final approval'
    }
  }[workflowAction];

  // Override config with props
  const finalConfig = {
    ...config,
    title: title || config.title,
    theme: theme || config.theme
  };

  useEffect(() => {
    if (isOpen) {
      loadUsers();
      if (enableRejectionAwareness) {
        loadRejectionRecommendations();
      }
      resetForm();
    }
  }, [isOpen, workflowAction]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`🔍 Loading eligible ${config.userTypePlural} with role-based filtering...`);
      
      // Get authentication token
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Use the users API to get all users
      const response = await fetch('/api/v1/users/users/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to load users: HTTP ${response.status}`);
      }
      
      const data = await response.json();
      const allUsers = data.results || [];
      
      // DEBUG: Log document object to see what fields are available
      if (allUsers.length > 0) {
        console.log('🔍 DEBUG - Document object:', {
          hasDocument: !!document,
          documentKeys: document ? Object.keys(document) : [],
          author: document?.author,
          author_id: document?.author_id,
          authorId: document?.author?.id
        });
      }
      
      // Unified user filtering logic with Segregation of Duties enforcement
      const eligibleUsers = allUsers.filter((user: any) => {
        console.log(`Checking ${config.userType} ${user.username}: active_roles =`, user.active_roles, 'is_superuser =', user.is_superuser);
        
        // Check role-based permissions
        const hasRequiredRole = user.active_roles?.some((role: any) => 
          config.roleFilters.includes(role.name) || 
          config.permissionLevels.includes(role.permission_level)
        );
        
        // CRITICAL: Segregation of Duties - Exclude document author from selection
        // Check multiple possible field names for author ID
        const authorId = document?.author || document?.author_id || document?.author?.id;
        const isSelfAssignment = user.id === authorId;
        
        // Include superusers and users with required role, but exclude self-assignment
        const isEligible = (user.is_superuser || hasRequiredRole) && !isSelfAssignment;
        
        console.log(`${config.userType} ${user.username} eligible: ${isEligible} (hasRole: ${hasRequiredRole}, notSelf: ${!isSelfAssignment}, authorId: ${authorId})`);
        return isEligible;
      });
      
      console.log(`✅ Found ${eligibleUsers.length} eligible ${config.userTypePlural} with proper permissions`);
      
      if (eligibleUsers.length === 0) {
        setError(`No eligible ${config.userTypePlural} found with proper permissions. Please contact an administrator.`);
        setUsers([]);
        return;
      }
      
      // Normalize user data
      const normalizedUsers = eligibleUsers.map((user: any) => ({
        id: user.id,
        username: user.username,
        full_name: user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username,
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email,
        active_roles: user.active_roles,
        is_superuser: user.is_superuser
      }));
      
      setUsers(normalizedUsers);
      
    } catch (error: any) {
      console.error(`❌ Error loading eligible ${config.userTypePlural}:`, error);
      setError(`Failed to load ${config.userTypePlural}: ${error.message}`);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const loadRejectionRecommendations = async () => {
    if (!enableRejectionAwareness || !document?.uuid) return;
    
    try {
      const response = await apiCall(`/workflows/documents/${document.uuid}/assignment-recommendations/`);
      if (response.success) {
        setRecommendations(response.recommendations);
        setRejectionWarnings(response.warnings || []);
      }
    } catch (error) {
      console.warn('Failed to load rejection recommendations:', error);
      // Don't show error to user for this optional feature
    }
  };

  const handleSubmit = async () => {
    if (!selectedUser) {
      setError(`Please select a ${config.userType}`);
      return;
    }

    console.log(`🚀 UNIFIED MODAL: Starting ${config.apiAction}`);
    console.log(`📄 Document UUID: ${document.uuid}`);
    console.log(`👤 Selected ${config.userType} ID: ${selectedUser}`);

    setLoading(true);
    setError(null);

    try {
      // For submit_for_review, use enhanced endpoint if rejection awareness is enabled
      if (workflowAction === 'submit_for_review' && enableRejectionAwareness) {
        const response = await apiCall(`/workflows/documents/${document.uuid}/submit-for-review-enhanced/`, {
          method: 'POST',
          data: {
            reviewer_id: selectedUser,
            comment: comment || 'Document submitted for review',
            acknowledge_warnings: acknowledgeWarnings
          }
        });

        // Handle warning confirmation flow
        if (response.requires_confirmation && !acknowledgeWarnings) {
          setRejectionWarnings(response.warnings);
          setShowWarnings(true);
          setLoading(false);
          return;
        }

        if (response.success) {
          console.log('✅ Enhanced submit for review successful');
          onSuccess();
          onClose();
          resetForm();
          return;
        } else {
          throw new Error(response.error || 'Enhanced submission failed');
        }
      }

      // For route_for_approval, skip the PATCH step and go directly to workflow API
      if (workflowAction === 'route_for_approval') {
        console.log(`🔄 Route for approval: Calling workflow API directly...`);
        
        // Step 1: Submit workflow action with approver assignment
        const workflowData: any = {
          action: config.apiAction,
          approver_id: selectedUser,
          comment: comment || `Document ${config.apiAction.replace('_', ' ')}`
        };

        const workflowResponse = await apiCall(`/documents/documents/${document.uuid}/workflow/`, {
          method: 'POST',
          data: workflowData
        });

        console.log('📊 Workflow API response:', workflowResponse);

        // Check if the response indicates success or failure
        if (workflowResponse.success === false) {
          console.error('❌ Backend returned success=false');
          console.error('❌ Error details:', workflowResponse.error);
          throw new Error(workflowResponse.error || 'Workflow submission failed');
        }

        console.log('🎉 Route for approval successful');
        
        // Success
        onSuccess();
        onClose();
        resetForm();
        return;
      }

      // For submit_for_review, use the two-step process
      console.log(`🔄 Step 1: Assigning ${config.userType}...`);
      
      // Step 1: Assign user to document
      const assignResponse = await apiCall(`/documents/documents/${document.uuid}/`, {
        method: 'PATCH',
        data: {
          [config.fieldName]: selectedUser
        }
      });
      
      console.log(`✅ ${config.userType} assignment response:`, assignResponse);

      console.log(`🔄 Step 2: Calling workflow API...`);
      
      // Step 2: Submit workflow action
      const workflowData: any = {
        action: config.apiAction,
        comment: comment || `Document ${config.apiAction.replace('_', ' ')}`
      };

      // Add specific field for route_for_approval
      if (workflowAction === 'route_for_approval') {
        workflowData.approver_id = selectedUser;
      }

      const workflowResponse = await apiCall(`/documents/documents/${document.uuid}/workflow/`, {
        method: 'POST',
        data: workflowData
      });

      console.log('📊 Workflow API response:', workflowResponse);

      // Check if the response indicates success or failure
      if (workflowResponse.success === false) {
        console.error('❌ Backend returned success=false');
        console.error('❌ Error details:', workflowResponse.error);
        throw new Error(workflowResponse.error || 'Workflow submission failed');
      }

      console.log('🎉 All API calls successful');
      
      // Success
      onSuccess();
      onClose();
      resetForm();

    } catch (error: any) {
      console.error(`💥 Error in ${config.apiAction}:`, error);
      console.error('💥 Error response:', error.response);
      
      const errorMessage = error.response?.data?.error || error.message || `Failed to ${config.apiAction.replace('_', ' ')}. Please try again.`;
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmWithWarnings = () => {
    setAcknowledgeWarnings(true);
    setShowWarnings(false);
    setTimeout(() => handleSubmit(), 100);
  };

  const resetForm = () => {
    setSelectedUser('');
    setComment('');
    setError(null);
    setRejectionWarnings([]);
    setShowWarnings(false);
    setAcknowledgeWarnings(false);
  };

  const themeClasses = {
    blue: {
      primary: 'bg-blue-600 hover:bg-blue-700 text-white',
      border: 'border-blue-500 focus:ring-blue-500 focus:border-blue-500',
      icon: 'text-blue-600',
      bg: 'bg-blue-50 border-blue-400',
      accent: 'text-blue-900'
    },
    green: {
      primary: 'bg-green-600 hover:bg-green-700 text-white',
      border: 'border-green-500 focus:ring-green-500 focus:border-green-500', 
      icon: 'text-green-600',
      bg: 'bg-green-50 border-green-400',
      accent: 'text-green-900'
    }
  }[finalConfig.theme];

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75">
        <div className="flex items-center justify-center min-h-screen p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  <span className="mr-2">{finalConfig.icon}</span>
                  {finalConfig.title}
                </h2>
                <button
                  onClick={onClose}
                  disabled={loading}
                  className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="px-6 py-3 bg-red-50 border-l-4 border-red-400">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            {/* Rejection Awareness Info */}
            {enableRejectionAwareness && recommendations?.has_rejections && !showWarnings && (
              <div className="px-6 py-3 bg-blue-50 border-l-4 border-blue-400">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-blue-800 font-medium">
                      💡 This document has rejection history ({recommendations.rejection_count} rejection{recommendations.rejection_count > 1 ? 's' : ''})
                    </p>
                    <p className="text-xs text-blue-700">
                      Tip: Reassigning to the same reviewer provides continuity and efficiency.
                    </p>
                  </div>
                  <button
                    onClick={() => setShowRejectionHistory(true)}
                    className="text-xs text-blue-600 hover:text-blue-800 underline"
                  >
                    View History
                  </button>
                </div>
              </div>
            )}

            {/* Assignment Guidance */}
            {showWarnings && rejectionWarnings.length > 0 && (
              <div className="px-6 py-4">
                <h3 className="font-medium text-gray-800 mb-2">💡 Assignment Guidance</h3>
                {rejectionWarnings.map((warning, index) => {
                  const isDifferentReviewer = warning.type === 'different_reviewer_guidance';
                  const bgColor = isDifferentReviewer ? 'bg-orange-50 border-orange-300' : 'bg-yellow-50 border-yellow-300';
                  const textColor = isDifferentReviewer ? 'text-orange-800' : 'text-yellow-800';
                  
                  return (
                    <div key={index} className={`mb-3 p-3 border rounded ${bgColor}`}>
                      <p className={`font-medium text-sm ${textColor}`}>{warning.title}</p>
                      <p className={`text-xs mt-1 ${textColor}`}>{warning.message}</p>
                      {warning.rejection_comment && (
                        <p className={`text-xs mt-2 italic ${textColor}`}>
                          Previous feedback: "{warning.rejection_comment}"
                        </p>
                      )}
                      {warning.suggestion && (
                        <p className={`text-xs mt-1 font-medium ${textColor}`}>{warning.suggestion}</p>
                      )}
                    </div>
                  );
                })}
                
                <div className="flex justify-between mt-4">
                  <button
                    onClick={() => setShowWarnings(false)}
                    className="px-3 py-1 text-sm bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                  >
                    Choose Different {config.userType}
                  </button>
                  <button
                    onClick={handleConfirmWithWarnings}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Proceed with Assignment
                  </button>
                </div>
              </div>
            )}

            {/* Main Form (hidden during warning confirmation) */}
            {!showWarnings && (
              <div className="max-h-[60vh] overflow-y-auto">
                {/* Document Information */}
                <div className={`px-6 py-4 ${themeClasses.bg} border-l-4`}>
                  <h3 className={`text-sm font-semibold ${themeClasses.accent} mb-2`}>Document Details</h3>
                  <p><strong>Number:</strong> {document?.document_number}</p>
                  <p><strong>Title:</strong> {document?.title}</p>
                  <p><strong>Status:</strong> <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">{document?.status_display || document?.status}</span></p>
                </div>

                {/* Workflow Information */}
                <div className="px-6 py-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-2">📋 {finalConfig.workflowStep}</h3>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 text-sm">
                    <p className="text-yellow-800">
                      <strong>Next Step:</strong> {finalConfig.nextStepInfo}
                    </p>
                  </div>
                </div>

                {/* User Selection */}
                <div className="px-6 py-4">
                  <label htmlFor="user" className="block text-sm font-medium text-gray-700 mb-2">
                    Select {config.userType.charAt(0).toUpperCase() + config.userType.slice(1)} * 
                    <span className="text-xs text-gray-500 ml-1">(Required)</span>
                  </label>
                  
                  {loading && users.length === 0 ? (
                    <div className="flex items-center space-x-2 py-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm text-gray-600">Loading {config.userTypePlural}...</span>
                    </div>
                  ) : (
                    <select
                      id="user"
                      value={selectedUser}
                      onChange={(e) => setSelectedUser(e.target.value)}
                      className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${themeClasses.border}`}
                      disabled={loading}
                    >
                      <option value="">-- Select a {config.userType} --</option>
                      {users.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.full_name} ({user.username})
                        </option>
                      ))}
                    </select>
                  )}
                  
                  {users.length > 0 && (
                    <div className="mt-2 text-sm text-gray-600">
                      <p>Found {users.length} eligible {config.userType}{users.length !== 1 ? 's' : ''} with {config.userType} permissions</p>
                    </div>
                  )}
                  {users.length === 0 && !loading && (
                    <p className="text-sm text-red-600 mt-1">No eligible {config.userTypePlural} found with proper permissions. Please contact an administrator.</p>
                  )}
                </div>

                {/* Comment */}
                <div className="px-6 py-4">
                  <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
                    {workflowAction === 'submit_for_review' ? 'Submission Comments' : 'Routing Comments'} 
                    <span className="text-xs text-gray-500 ml-1">(Optional)</span>
                  </label>
                  <textarea
                    id="comment"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder={`Add any comments for the ${config.userType}...`}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    disabled={loading}
                  />
                </div>

                {/* Action Buttons */}
                <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                  <button
                    onClick={onClose}
                    disabled={loading}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={loading || !selectedUser}
                    className={`px-4 py-2 text-sm font-medium rounded-md focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${themeClasses.primary}`}
                  >
                    {loading ? 'Processing...' : finalConfig.title}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rejection History Modal */}
      {enableRejectionAwareness && (
        <RejectionHistoryModal
          documentId={document?.uuid}
          isOpen={showRejectionHistory}
          onClose={() => setShowRejectionHistory(false)}
        />
      )}
    </>
  );
};

export default UnifiedWorkflowModal;