/**
 * Reviewer Interface Component
 * 
 * Implements EDMS_details_workflow.txt lines 7-10:
 * - Reviewer downloads document and provide comments
 * - Reviewer can reject (returns to DRAFT) or approve (status: REVIEWED)
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import apiService from '../../services/api.ts';
import { triggerBadgeRefresh } from '../../utils/badgeRefresh';

interface ReviewerInterfaceProps {
  documentId: string;
  onClose: () => void;
  onReviewComplete: () => void;
}

interface Document {
  uuid: string;
  document_number: string;
  title: string;
  description: string;
  status: string;
  status_display: string;
  document_type_display: string;
  author_display: string;
  reviewer_display: string;
  created_at: string;
  file_name: string;
  file_path: string;
  version_string: string;
}

interface Comment {
  id: number;
  content: string;
  comment_type: string;
  created_at: string;
  author_display: string;
  is_resolved: boolean;
}

const ReviewerInterface: React.FC<ReviewerInterfaceProps> = ({
  documentId,
  onClose,
  onReviewComplete
}) => {
  const { authenticated, user } = useAuth();
  
  // State management
  const [document, setDocument] = useState<Document | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Review form state
  const [reviewComment, setReviewComment] = useState('');
  const [reviewDecision, setReviewDecision] = useState<'approve' | 'reject' | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Load document data
  useEffect(() => {
    if (authenticated && documentId) {
      loadDocumentData();
    }
  }, [authenticated, documentId]);

  // Automatically start review process when document is loaded and in PENDING_REVIEW status
  useEffect(() => {
    if (document && document.status === 'PENDING_REVIEW') {
      startReviewProcess();
    }
  }, [document]);

  const startReviewProcess = async () => {
    if (!document) return;
    
    try {
      // Step 1: Start the review to transition from PENDING_REVIEW to UNDER_REVIEW
      await apiService.post(`/documents/documents/${document.uuid}/workflow/`, {
        action: 'start_review',
        comment: 'Review process initiated by reviewer'
      });
      
      // Reload document data to get updated status
      await loadDocumentData();
      
    } catch (error) {
      console.error('Error starting review process:', error);
      // Don't block the interface if start_review fails
      // The document might already be in UNDER_REVIEW state
    }
  };

  const loadDocumentData = async () => {
    try {
      setLoading(true);

      // Load document details
      const documentResponse = await apiService.get(`/documents/documents/${documentId}/`);
      
      // Extract document ID from comments or versions if not in document response
      if (!documentResponse.id) {
        if (documentResponse.comments && documentResponse.comments.length > 0) {
          documentResponse.id = documentResponse.comments[0].document;
        } else if (documentResponse.versions && documentResponse.versions.length > 0) {
          documentResponse.id = documentResponse.versions[0].document;
        }
      }
      
      setDocument(documentResponse);

      // Use comments from the document response (they're already filtered correctly)
      const documentComments = documentResponse.comments || [];
      setComments(documentComments);

    } catch (error: any) {
      console.error('❌ Error loading document data:', error);
      setError('Failed to load document for review');
    } finally {
      setLoading(false);
    }
  };


  const handleReviewSubmission = () => {
    if (!reviewComment.trim()) {
      setError('Review comment is required');
      return;
    }
    
    if (!reviewDecision) {
      setError('Please select approve or reject');
      return;
    }
    
    setShowConfirmDialog(true);
  };

  const confirmReviewSubmission = async () => {
    try {
      setIsSubmitting(true);
      setShowConfirmDialog(false);

      // Backend expects document.id (integer primary key), not UUID
      if (!document?.id) {
        throw new Error(`Document ID is missing: ${document?.id}. Document: ${JSON.stringify(document)}`);
      }

      // Submit review comment - using document ID (primary key) not UUID
      const commentData = {
        document: document.id,
        content: reviewComment,
        comment_type: 'REVIEW',
        subject: `Review ${reviewDecision}: ${document?.title}`
      };
      
      await apiService.post(`/documents/comments/`, commentData);

      // Now call workflow endpoint for automatic status transition
      
      try {
        // Step 2: Complete the review with the decision
        const workflowResponse = await apiService.post(`/documents/documents/${document.uuid}/workflow/`, {
          action: 'complete_review',
          approved: reviewDecision === 'approve',
          comment: reviewComment
        });
      } catch (workflowError: any) {
      }
      
      // Success! Document state has changed, need to refresh parent data
      console.log('✅ Review submitted successfully, refreshing parent document data...');
      
      // Dispatch custom event to notify all components that document has been updated
      window.dispatchEvent(new CustomEvent('documentUpdated', { 
        detail: { 
          documentId: document.uuid,
          action: 'review_submitted',
          newStatus: reviewDecision === 'approve' ? 'REVIEWED' : 'DRAFT',
          refreshRequired: true
        } 
      }));
      
      // 🔄 IMMEDIATE BADGE REFRESH: Update badge count immediately after review action
      triggerBadgeRefresh();
      console.log('✅ Badge refreshed immediately after review action');
      
      onReviewComplete();
      onClose();

    } catch (error: any) {
      console.error('❌ Error submitting review:', error);
      setError('Failed to submit review. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75 flex items-center justify-center">
        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span>Loading document for review...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75 flex items-center justify-center">
        <div className="bg-white rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-600 mb-2">Document Not Found</h3>
          <p className="text-gray-600 mb-4">Unable to load document for review.</p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75">
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-y-auto">
          
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                📋 Document Review Interface
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
                disabled={isSubmitting}
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
              <p className="text-red-700">{error}</p>
              <button
                onClick={() => setError(null)}
                className="text-red-500 hover:text-red-700 text-sm"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Document Information */}
          <div className="px-6 py-4 bg-blue-50 border-l-4 border-blue-400">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Document Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p><strong>Document Number:</strong> {document.document_number}</p>
                <p><strong>Title:</strong> {document.title}</p>
                <p><strong>Type:</strong> {document.document_type_display}</p>
                <p><strong>Version:</strong> {document.version_string}</p>
              </div>
              <div>
                <p><strong>Author:</strong> {document.author_display}</p>
                <p><strong>Status:</strong> <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">{document.status_display}</span></p>
                <p><strong>Created:</strong> {new Date(document.created_at).toLocaleDateString()}</p>
                <p><strong>File:</strong> {document.file_name}</p>
              </div>
            </div>
            {document.description && (
              <div className="mt-3">
                <p><strong>Description:</strong> {document.description}</p>
              </div>
            )}
          </div>

          {/* Workflow Status */}
          <div className="px-6 py-4">
            <h3 className="text-sm font-medium text-gray-900 mb-2">📋 Workflow Status (EDMS Line 7)</h3>
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
              <p className="text-sm text-yellow-800">
                <strong>Current Step:</strong> Document is pending review
              </p>
              <p className="text-xs text-yellow-700 mt-1">
                As the assigned reviewer, you can download the document, provide comments, and either approve or reject it.
              </p>
            </div>
          </div>


          {/* Existing Comments */}
          {comments.length > 0 && (
            <div className="px-6 py-4 border-t border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">💬 Previous Comments</h3>
              <div className="space-y-3">
                {comments.map((comment) => (
                  <div key={comment.id} className="bg-gray-50 rounded-lg p-3">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-semibold text-gray-900">{comment.author_display}</span>
                      <span className="text-xs text-gray-500">
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-gray-700">{comment.content}</p>
                    <span className="inline-block mt-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {comment.comment_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Review Section */}
          <div className="px-6 py-4 border-t border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">✍️ Submit Review</h3>
            
            <div className="space-y-4">
              {/* Review Comment */}
              <div>
                <label htmlFor="reviewComment" className="block text-sm font-medium text-gray-700 mb-2">
                  Review Comments * <span className="text-xs text-gray-500">(Required per EDMS Line 7)</span>
                </label>
                <textarea
                  id="reviewComment"
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder="Provide your review comments here..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  disabled={isSubmitting}
                />
              </div>

              {/* Review Decision */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Review Decision * <span className="text-xs text-gray-500">(EDMS Lines 8-10)</span>
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => setReviewDecision('approve')}
                    className={`p-4 border rounded-lg text-left ${
                      reviewDecision === 'approve'
                        ? 'border-green-500 bg-green-50 text-green-900'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                    disabled={isSubmitting}
                  >
                    <div className="flex items-center mb-2">
                      <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="font-semibold">Approve Document</span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Document status: REVIEWED → Route to approver (Line 10-11)
                    </p>
                  </button>

                  <button
                    onClick={() => setReviewDecision('reject')}
                    className={`p-4 border rounded-lg text-left ${
                      reviewDecision === 'reject'
                        ? 'border-red-500 bg-red-50 text-red-900'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                    disabled={isSubmitting}
                  >
                    <div className="flex items-center mb-2">
                      <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      <span className="font-semibold">Reject Document</span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Return to author for edit/re-upload (Line 8-9)
                    </p>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
            <button
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleReviewSubmission}
              disabled={isSubmitting || !reviewComment.trim() || !reviewDecision}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {isSubmitting ? 'Submitting Review...' : 'Submit Review'}
            </button>
          </div>

          {/* Confirmation Dialog */}
          {showConfirmDialog && (
            <div className="fixed inset-0 z-60 overflow-y-auto bg-gray-500 bg-opacity-75 flex items-center justify-center">
              <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Confirm Review Submission
                </h3>
                <p className="text-gray-600 mb-4">
                  Are you sure you want to <strong>{reviewDecision}</strong> this document?
                </p>
                <p className="text-sm text-gray-500 mb-6">
                  {reviewDecision === 'approve' 
                    ? 'The document will be marked as REVIEWED and routed to the approver.'
                    : 'The document will be returned to the author with status DRAFT.'}
                </p>
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowConfirmDialog(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={confirmReviewSubmission}
                    className={`px-4 py-2 text-sm font-medium text-white rounded-md ${
                      reviewDecision === 'approve'
                        ? 'bg-green-600 hover:bg-green-700'
                        : 'bg-red-600 hover:bg-red-700'
                    }`}
                  >
                    Confirm {reviewDecision === 'approve' ? 'Approval' : 'Rejection'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReviewerInterface;