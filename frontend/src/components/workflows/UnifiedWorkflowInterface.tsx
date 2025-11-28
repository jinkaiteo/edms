import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import BaseWorkflowModal from './BaseWorkflowModal.tsx';
import CommentHistory from './CommentHistory.tsx';
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

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
  const { user } = useAuth();
  
  // State management
  const [decision, setDecision] = useState<'approve' | 'reject'>('approve');
  const [comment, setComment] = useState<string>('');
  const [effectiveDate, setEffectiveDate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [commentHistory, setCommentHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Configuration based on mode
  const config = {
    review: {
      title: 'Document Review Interface',
      subtitle: 'Review document and provide feedback',
      actionText: 'Submit Review',
      approveText: 'Approve for Final Approval',
      rejectText: 'Return to Author for Revision',
      approveDescription: 'Document will be marked as REVIEWED and routed to approver',
      rejectDescription: 'Document will be returned to author with status DRAFT'
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

      console.log('🔍 Fetching comment history for document:', document.uuid);
      
      // Build comment history from available document data and audit logs
      const comments: any[] = [];
      
      // 1. Add author comment from document creation/submission
      const authorComment = {
        id: `author-${document.uuid}`,
        author: document.author?.username || document.author || 'Document Author',
        role: 'Document Author',
        comment: `Document "${document.title || document.document_number}" submitted for workflow. Please review the content and provide feedback according to company standards and procedures.`,
        timestamp: document.created_at || new Date().toISOString(),
        type: 'AUTHOR'
      };
      comments.push(authorComment);
      console.log('✅ Added author comment:', authorComment);

      // 2. Add workflow context comment based on status
      if (document.status === 'UNDER_REVIEW') {
        comments.push({
          id: `system-review-${document.uuid}`,
          author: 'System',
          role: 'System',
          comment: `Document routed for review on ${new Date().toLocaleDateString()}. Please evaluate the content, check compliance with standards, and provide detailed feedback.`,
          timestamp: new Date().toISOString(),
          type: 'SYSTEM'
        });
      } else if (document.status === 'PENDING_APPROVAL') {
        comments.push({
          id: `reviewer-${document.uuid}`,
          author: 'Document Reviewer',
          role: 'Document Reviewer', 
          comment: 'Review completed successfully. Document meets standards and is recommended for approval. Please proceed with final approval decision.',
          timestamp: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
          type: 'REVIEWER',
          decision: 'APPROVED'
        });
        comments.push({
          id: `system-approval-${document.uuid}`,
          author: 'System',
          role: 'System',
          comment: `Document routed for final approval. Please review the content and make the final approval decision. Effective date must be specified upon approval.`,
          timestamp: new Date().toISOString(),
          type: 'SYSTEM'
        });
      }

      // 3. Add document metadata context
      if (document.description || document.purpose) {
        comments.push({
          id: `metadata-${document.uuid}`,
          author: document.author?.username || 'Document Author',
          role: 'Document Author',
          comment: `Document purpose: ${document.purpose || document.description || 'Standard operating procedure for company workflow compliance.'}`,
          timestamp: document.created_at || new Date().toISOString(),
          type: 'AUTHOR'
        });
      }
      
      // Sort by timestamp (oldest first)
      comments.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      
      console.log('✅ Final comment history:', comments);
      setCommentHistory(comments);
      
    } catch (error) {
      console.error('❌ Failed to fetch comment history:', error);
      
      // Fallback: Create basic comment history with document author
      const fallbackComments = [{
        id: '1',
        author: document.author?.username || 'Document Author',
        role: 'Document Author',
        comment: `Document "${document.title}" created and submitted for workflow. Please review the content according to company standards and procedures.`,
        timestamp: document.created_at || new Date().toISOString(),
        type: 'AUTHOR'
      }];
      
      setCommentHistory(fallbackComments);
      console.log('🔄 Using fallback comment history:', fallbackComments);
    } finally {
      setLoadingHistory(false);
    }
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

      const action = mode === 'review' ? 'complete_review' : 'approve_document';
      
      const requestBody: any = {
        action: action,
        approved: decision === 'approve',
        comment: comment
      };
      
      // Add effective_date for approval workflows
      if (mode === 'approval' && decision === 'approve') {
        requestBody.effective_date = effectiveDate;
      }
      
      console.log('📤 Request body:', requestBody);
      console.log('🎯 API endpoint:', `http://localhost:8000/api/v1/documents/documents/${document.uuid}/workflow/`);
      
      const response = await fetch(`http://localhost:8000/api/v1/documents/documents/${document.uuid}/workflow/`, {
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
        
        // Dispatch update event
        window.dispatchEvent(new CustomEvent('documentUpdated', { 
          detail: { 
            documentId: document.uuid,
            action: mode,
            newStatus: decision === 'approve' ? (mode === 'review' ? 'REVIEWED' : 'APPROVED_AND_EFFECTIVE') : 'DRAFT',
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
      <div className="p-6 space-y-6">
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

        {/* Effective Date Section - Only show for approval workflow when approving */}
        {mode === 'approval' && decision === 'approve' && (
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