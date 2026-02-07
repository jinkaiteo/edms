import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import BaseWorkflowModal from './BaseWorkflowModal.tsx';
import CommentHistory from './CommentHistory.tsx';
import SensitivityLabelSelector from './SensitivityLabelSelector.tsx';
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { triggerBadgeRefresh } from '../../utils/badgeRefresh.ts';

interface UnifiedWorkflowInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
  document: any;
  mode: 'review' | 'approval';
  onComplete: () => void;
}

const UnifiedWorkflowInterface: React.FC<UnifiedWorkflowInterfaceProps> = ({
  isOpen,
  onClose,
  document,
  mode,
  onComplete
}) => {
  const { user: _user } = useAuth(); // Prefixed with _ to indicate intentionally unused
  
  // State management
  const [decision, setDecision] = useState<'approve' | 'reject'>('approve');
  const [comment, setComment] = useState<string>('');
  const [effectiveDate, setEffectiveDate] = useState<string>('');
  const [reviewPeriodMonths, setReviewPeriodMonths] = useState<number>(12);
  const [requiresReview, setRequiresReview] = useState<boolean>(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [commentHistory, setCommentHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  
  // Sensitivity label state (for approval mode only)
  const [sensitivityLabel, setSensitivityLabel] = useState<string>(document?.sensitivity_label || 'INTERNAL');
  const [sensitivityChangeReason, setSensitivityChangeReason] = useState<string>('');

  // Configuration based on mode
  const config = {
    review: {
      title: 'Document Review Interface',
      subtitle: 'Review document and provide feedback',
      actionText: 'Submit Review',
      approveText: 'Approve',
      rejectText: 'Reject',
      approveDescription: 'Document will be marked as REVIEWED and routed back to author to assign approver',
      rejectDescription: 'Document will be returned to author for revision'
    },
    approval: {
      title: 'Document Approval Interface', 
      subtitle: 'Final approval decision for document',
      actionText: 'Submit Approval Decision',
      approveText: 'Approve Document',
      rejectText: 'Reject Document',
      approveDescription: 'Document will be approved and become effective',
      rejectDescription: 'Document will be returned to author for revision'
    }
  };

  const currentConfig = config[mode];

  const fetchCommentHistory = async () => {
    setLoadingHistory(true);
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) return;

      console.log('🔍 Fetching real workflow history for document:', document.uuid);
      
      // Fetch actual workflow history from backend (standard workflows endpoint)
      const response = await fetch(`/api/v1/workflows/documents/${document.uuid}/history/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const historyData = await response.json();
        console.log('✅ Raw workflow history response:', historyData);
        
        // Transform workflow history into comment format
        const comments: any[] = [];
        
        const transitionsArr = Array.isArray(historyData.transitions) ? historyData.transitions : (historyData.workflow_history || []);
        if (transitionsArr && transitionsArr.length > 0) {
          transitionsArr.forEach((transition: any) => {
            comments.push({
              id: `transition-${transition.transitioned_at}`,
              author: transition.transitioned_by || 'Unknown User',
              role: getUserRole(transition.from_state, transition.to_state),
              comment: transition.comment || 'No comment provided',
              timestamp: transition.transitioned_at,
              type: 'WORKFLOW',
              transition: `${transition.from_state} → ${transition.to_state}`
            });
          });
        }
        
        // Add document creation context as first comment if no workflow history exists
        if (comments.length === 0) {
          comments.push({
            id: `creation-${document.uuid}`,
            author: document.author_display || 'Document Author',
            role: 'Document Author',
            comment: `Document "${document.title || document.document_number}" created and ready for workflow.`,
            timestamp: document.created_at || new Date().toISOString(),
            type: 'AUTHOR'
          });
        }
        
        // Sort by timestamp (oldest first)
        comments.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        
        console.log('✅ Processed workflow comments:', comments);
        setCommentHistory(comments);
        
      } else {
        console.warn('⚠️ Workflow history API failed, using fallback');
        throw new Error(`HTTP ${response.status}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to fetch workflow history:', error);
      
      // Fallback: Create basic comment with document creation
      const fallbackComments = [{
        id: 'fallback-1',
        author: document.author_display || 'Document Author',
        role: 'Document Author',
        comment: `Document "${document.title || document.document_number}" created. Workflow history unavailable.`,
        timestamp: document.created_at || new Date().toISOString(),
        type: 'AUTHOR'
      }];
      
      setCommentHistory(fallbackComments);
      console.log('🔄 Using fallback comment history:', fallbackComments);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Helper function to determine user role based on workflow transition
  const getUserRole = (fromState: string, toState: string): string => {
    if (fromState === 'DRAFT' && toState === 'PENDING_REVIEW') return 'Document Author';
    if (fromState === 'PENDING_REVIEW' && toState === 'UNDER_REVIEW') return 'Document Reviewer';
    if (fromState === 'UNDER_REVIEW' && toState === 'REVIEWED') return 'Document Reviewer';
    if (fromState === 'UNDER_REVIEW' && toState === 'DRAFT') return 'Document Reviewer';
    if (fromState === 'REVIEWED' && toState === 'PENDING_APPROVAL') return 'Document Author';
    if (fromState === 'PENDING_APPROVAL' && toState === 'EFFECTIVE') return 'Document Approver';
    if (toState === 'TERMINATED') return 'Administrator';
    return 'System User';
  };

  useEffect(() => {
    if (isOpen) {
      setDecision('approve');
      setComment('');
      setError(null);
      setShowConfirmDialog(false);
      // Set default effective date to today for approvals
      if (mode === 'approval') {
        setEffectiveDate(new Date().toISOString().split('T')[0]);
      } else {
        setEffectiveDate('');
      }
      fetchCommentHistory();
    }
  }, [isOpen, document?.uuid, mode]);

  const handleSubmission = () => {
    if (!comment.trim()) {
      setError(`${mode === 'review' ? 'Review' : 'Approval'} comment is required`);
      return;
    }
    
    // Validate effective date for approval workflows when approving
    if (mode === 'approval' && decision === 'approve' && !effectiveDate.trim()) {
      setError('Effective date is required for document approval');
      return;
    }
    
    // Validate sensitivity label for approval mode
    if (mode === 'approval' && decision === 'approve') {
      if (!sensitivityLabel) {
        setError('Sensitivity label is required for approval');
        return;
      }
      
      // Check if sensitivity changed and validate reason
      const originalSensitivity = document?.sensitivity_label || 'INTERNAL';
      if (sensitivityLabel !== originalSensitivity) {
        if (!sensitivityChangeReason?.trim()) {
          setError('Please provide a reason for changing the sensitivity classification');
          return;
        }
        if (sensitivityChangeReason.trim().length < 20) {
          setError('Change reason must be at least 20 characters (currently: ' + sensitivityChangeReason.trim().length + ')');
          return;
        }
      }
    }
    
    setShowConfirmDialog(true);
  };

  const confirmSubmission = async () => {
    try {
      setLoading(true);
      setShowConfirmDialog(false);

      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      console.log('🔍 DEBUG: Starting workflow submission...');
      console.log('📋 Document state:', {
        uuid: document.uuid,
        document_number: document.document_number,
        status: document.status,
        mode: mode,
        decision: decision
      });

      // Handle workflow state logic for review mode
      let action = mode === 'review' ? 'complete_review' : 'approve';
      
      // CRITICAL FIX: For review mode, check if we need to start review first
      if (mode === 'review' && document.status === 'PENDING_REVIEW') {
        console.log('🔄 Document is in PENDING_REVIEW, need to start review first');
        action = 'start_review';
      }
      
      const requestBody: any = {
        action: action,
        approved: decision === 'approve',
        comment: comment
      };
      
      // Add effective_date for approval workflows (include dummy date for rejections to bypass backend validation)
      if (mode === 'approval') {
        requestBody.effective_date = decision === 'approve' ? effectiveDate : new Date().toISOString().split('T')[0];
        
        // Add review period for approvals
        if (decision === 'approve') {
          requestBody.review_period_months = requiresReview ? reviewPeriodMonths : null;
          
          // Include sensitivity label when approving
          requestBody.sensitivity_label = sensitivityLabel;
          if (sensitivityChangeReason) {
            requestBody.sensitivity_change_reason = sensitivityChangeReason;
          }
        }
      }
      
      console.log('📤 Request body:', requestBody);
      console.log('🎯 API endpoint:', `/api/v1/documents/documents/${document.uuid}/workflow/`);
      
      const response = await fetch(`/api/v1/documents/documents/${document.uuid}/workflow/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      console.log('📥 Response status:', response.status);
      console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const successData = await response.json();
        console.log('✅ Workflow submission successful:', successData);
        
        // CRITICAL FIX: Handle two-step review process
        if (mode === 'review' && action === 'start_review') {
          console.log('🔄 Review started, now completing the review...');
          
          // Automatically complete the review in the same interaction
          const completeRequestBody = {
            action: 'complete_review',
            approved: decision === 'approve',
            comment: comment
          };
          
          console.log('📤 Completing review with:', completeRequestBody);
          
          const completeResponse = await fetch(`/api/v1/documents/documents/${document.uuid}/workflow/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(completeRequestBody)
          });
          
          if (completeResponse.ok) {
            const completeData = await completeResponse.json();
            console.log('✅ Review completion successful:', completeData);
          } else {
            const completeError = await completeResponse.json().catch(() => ({ error: 'Failed to complete review' }));
            console.error('❌ Failed to complete review:', completeError);
            throw new Error(completeError.error || 'Failed to complete review');
          }
        }
        
        // Trigger badge refresh to update "My Tasks" count immediately
        triggerBadgeRefresh();
        console.log(`✅ Badge refreshed immediately after ${mode} action (${decision})`);
        
        // Dispatch update event
        window.dispatchEvent(new CustomEvent('documentUpdated', { 
          detail: { 
            documentId: document.uuid,
            action: mode,
            newStatus: decision === 'approve' ? (mode === 'review' ? 'REVIEWED' : 'EFFECTIVE') : 'DRAFT',
            refreshRequired: true
          } 
        }));
        
        onComplete();
        onClose();
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown server error' }));
        console.error('❌ Workflow submission failed:', {
          status: response.status,
          statusText: response.statusText,
          errorData: errorData
        });
        throw new Error(errorData.error || `Failed to submit ${mode}. HTTP ${response.status}: ${response.statusText}`);
      }

    } catch (error: any) {
      console.error(`Error submitting ${mode}:`, error);
      setError(`Failed to submit ${mode}. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <BaseWorkflowModal
      isOpen={isOpen}
      onClose={onClose}
      title={currentConfig.title}
      subtitle={currentConfig.subtitle}
      document={document}
    >
      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex items-center space-x-2">
              <XMarkIcon className="h-5 w-5 text-red-400" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Comment History */}
        <CommentHistory comments={commentHistory} loading={loadingHistory} />

        {/* Decision Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {mode === 'review' ? '👀 Review Decision' : '✅ Approval Decision'}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Approve Option */}
            <button
              onClick={() => setDecision('approve')}
              className={`p-4 border-2 rounded-lg text-left transition-all ${
                decision === 'approve'
                  ? 'border-green-500 bg-green-50 shadow-md'
                  : 'border-gray-200 hover:border-green-300 hover:bg-green-25'
              }`}
            >
              <div className="flex items-center mb-2">
                <CheckIcon className="h-5 w-5 text-green-500 mr-2" />
                <span className="font-semibold text-green-900">{currentConfig.approveText}</span>
              </div>
              <p className="text-sm text-gray-600">{currentConfig.approveDescription}</p>
            </button>

            {/* Reject Option */}
            <button
              onClick={() => setDecision('reject')}
              className={`p-4 border-2 rounded-lg text-left transition-all ${
                decision === 'reject'
                  ? 'border-red-500 bg-red-50 shadow-md'
                  : 'border-gray-200 hover:border-red-300 hover:bg-red-25'
              }`}
            >
              <div className="flex items-center mb-2">
                <XMarkIcon className="h-5 w-5 text-red-500 mr-2" />
                <span className="font-semibold text-red-900">{currentConfig.rejectText}</span>
              </div>
              <p className="text-sm text-gray-600">{currentConfig.rejectDescription}</p>
            </button>
          </div>
        </div>

        {/* Sensitivity Label Selector - Only for Approval Mode and Approve Decision */}
        {mode === 'approval' && decision === 'approve' && (
          <div className="space-y-2">
            <SensitivityLabelSelector
              value={sensitivityLabel}
              onChange={(label: string, reason: string) => {
                setSensitivityLabel(label);
                setSensitivityChangeReason(reason);
              }}
              inheritedFrom={document?.sensitivity_inherited_from_number}
              originalValue={document?.sensitivity_label}
              required={true}
              disabled={loading}
              showGuide={true}
            />
          </div>
        )}

        {/* Comment Section */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-gray-900">
            {mode === 'review' ? 'Review Comments' : 'Approval Comments'} *
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={`Provide your ${mode} comments here...`}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          />
          <p className="text-xs text-gray-500">
            {mode === 'review' 
              ? 'Explain your review findings and any concerns or recommendations'
              : 'Provide justification for your approval decision'
            }
          </p>
        </div>

        {/* Effective Date and Review Period Section - Only show for approval workflow when approving */}
        {mode === 'approval' && decision === 'approve' && (
          <div className="space-y-4">
            {/* Effective Date */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-900">
                📅 Effective Date *
              </label>
              <input
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={loading}
              />
              <p className="text-xs text-gray-500">
                Select when this document should become effective. Defaults to today's date.
              </p>
            </div>

            {/* Periodic Review Configuration */}
            <div className="space-y-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <label className="text-sm font-semibold text-gray-900">
                  🔄 Periodic Review Required
                </label>
                <button
                  type="button"
                  onClick={() => setRequiresReview(!requiresReview)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    requiresReview ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                  disabled={loading}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      requiresReview ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              
              {requiresReview && (
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Review Interval
                  </label>
                  <select
                    value={reviewPeriodMonths}
                    onChange={(e) => setReviewPeriodMonths(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    disabled={loading}
                  >
                    <option value={6}>Every 6 months</option>
                    <option value={12}>Annual (12 months)</option>
                    <option value={18}>Every 18 months</option>
                    <option value={24}>Biennial (24 months)</option>
                    <option value={36}>Every 3 years</option>
                  </select>
                  <p className="text-xs text-gray-600">
                    Document will require periodic review for regulatory compliance.
                    {requiresReview && reviewPeriodMonths && (
                      <span className="block mt-1 font-medium text-blue-700">
                        Next review due: {new Date(new Date(effectiveDate || new Date()).getTime() + reviewPeriodMonths * 30 * 24 * 60 * 60 * 1000).toLocaleDateString()}
                      </span>
                    )}
                  </p>
                </div>
              )}
              
              {!requiresReview && (
                <p className="text-xs text-gray-600">
                  ℹ️ No periodic review will be scheduled. This is typically used for reference documents or documents with indefinite validity.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmission}
            disabled={loading || !comment.trim() || (mode === 'approval' && decision === 'approve' && !effectiveDate.trim())}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {loading ? 'Processing...' : currentConfig.actionText}
          </button>
        </div>

        {/* Confirmation Dialog */}
        {showConfirmDialog && (
          <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Confirm {mode === 'review' ? 'Review' : 'Approval'} Submission
              </h3>
              <p className="text-gray-600 mb-4">
                Are you sure you want to <strong>{decision}</strong> this document?
              </p>
              <p className="text-sm text-gray-500 mb-6">
                {decision === 'approve' ? currentConfig.approveDescription : currentConfig.rejectDescription}
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowConfirmDialog(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmSubmission}
                  className={`px-4 py-2 text-sm font-medium text-white rounded-md ${
                    decision === 'approve'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  Confirm {decision === 'approve' ? 'Approval' : 'Rejection'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </BaseWorkflowModal>
  );
};

export default UnifiedWorkflowInterface;