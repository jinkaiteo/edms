/**
 * Submit For Review Modal Component
 * 
 * Implements EDMS Step 2: Author select reviewer and route to document for review
 * Separates reviewer selection from document creation per EDMS specification
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import apiService from '../../services/api.ts';

interface SubmitForReviewModalProps {
  document: any;
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess: () => void;
}

interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
}

const SubmitForReviewModal: React.FC<SubmitForReviewModalProps> = ({
  document,
  isOpen,
  onClose,
  onSubmitSuccess
}) => {
  const { authenticated } = useAuth();
  
  // State management
  const [reviewers, setReviewers] = useState<User[]>([]);
  const [selectedReviewer, setSelectedReviewer] = useState<number | null>(null);
  const [submissionComment, setSubmissionComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available reviewers
  useEffect(() => {
    if (isOpen && authenticated) {
      loadReviewers();
    }
  }, [isOpen, authenticated]);

  const loadReviewers = async () => {
    try {
      setLoading(true);
      
      // Try to load users from API, fallback to mock data
      try {
        const response = await apiService.get('/auth/users/');
        const usersList = Array.isArray(response) ? response : response.results || [];
        const availableReviewers = usersList.filter(user => user.id !== document?.author);
        setReviewers(availableReviewers);
      } catch (apiError) {
        // Use test users from EDMS_Test_Users_Credentials.md
        const testReviewers = [
          {
            id: 4,
            username: 'reviewer',
            first_name: 'Document',
            last_name: 'Reviewer', 
            email: 'reviewer@edms.local'
          },
          {
            id: 5,
            username: 'approver',
            first_name: 'Document',
            last_name: 'Approver',
            email: 'approver@edms.local' 
          },
          {
            id: 1,
            username: 'admin',
            first_name: 'Admin',
            last_name: 'User',
            email: 'admin@edms.local'
          }
        ];
        setReviewers(testReviewers);
      }
    } catch (error: any) {
      console.error('❌ Error loading reviewers:', error);
      setError('Failed to load available reviewers');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitForReview = async () => {
    try {
      if (!selectedReviewer) {
        setError('Please select a reviewer');
        return;
      }


      setLoading(true);
      setError(null);

      // Step 1: Assign reviewer to document (ignore audit logging errors)
      let reviewerAssigned = false;
      try {
        const assignResponse = await apiService.patch(`/documents/documents/${document.uuid}/`, {
          reviewer: selectedReviewer
        });
        reviewerAssigned = true;
      } catch (reviewerError: any) {
        console.error('❌ Failed to assign reviewer:', reviewerError);
        throw new Error(`Failed to assign reviewer: ${reviewerError.message || 'Unknown error'}`);
      }

      // Step 2: Submit for review using workflow action  
      try {
        const workflowResponse = await apiService.post(`/documents/documents/${document.uuid}/workflow/`, {
          action: 'submit_for_review',
          comment: submissionComment || 'Document submitted for review'
        });
      } catch (workflowError: any) {
        console.error('❌ WORKFLOW: Failed to submit for review:', workflowError);
        throw new Error(`Failed to submit document for review: ${workflowError.message || 'Unknown error'}`);
      }

      // Success - check if we have reviewer assignment
      if (reviewerAssigned) {
        onSubmitSuccess();
        onClose();
      } else {
        throw new Error('Failed to assign reviewer to document');
      }

    } catch (error: any) {
      console.error('❌ WORKFLOW: Failed to submit for review - full error:', error);
      setError('Failed to submit document for review. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75">
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
          
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                📤 Submit for Review
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
                disabled={loading}
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

          {/* Document Information */}
          <div className="px-6 py-4 bg-blue-50 border-l-4 border-blue-400">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Document Details</h3>
            <p><strong>Number:</strong> {document?.document_number}</p>
            <p><strong>Title:</strong> {document?.title}</p>
            <p><strong>Status:</strong> <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">{document?.status_display}</span></p>
          </div>

          {/* Workflow Information */}
          <div className="px-6 py-4">
            <h3 className="text-sm font-medium text-gray-900 mb-2">📋 EDMS Workflow Step 2</h3>
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 text-sm">
              <p className="text-yellow-800">
                <strong>Current Step:</strong> Author selects reviewer and routes document for review
              </p>
              <p className="text-yellow-700 text-xs mt-1">
                Per EDMS specification line 6: Document status will change from DRAFT to PENDING_REVIEW
              </p>
            </div>
          </div>

          {/* Reviewer Selection */}
          <div className="px-6 py-4">
            <label htmlFor="reviewer" className="block text-sm font-medium text-gray-700 mb-2">
              Select Reviewer * <span className="text-xs text-gray-500">(Required)</span>
            </label>
            
            {loading ? (
              <div className="flex items-center space-x-2 py-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm text-gray-600">Loading reviewers...</span>
              </div>
            ) : (
              <select
                id="reviewer"
                value={selectedReviewer || ''}
                onChange={(e) => setSelectedReviewer(Number(e.target.value) || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                disabled={loading}
              >
                <option value="">-- Select a reviewer --</option>
                {reviewers.map((reviewer) => (
                  <option key={reviewer.id} value={reviewer.id}>
                    {reviewer.first_name} {reviewer.last_name} ({reviewer.username})
                  </option>
                ))}
              </select>
            )}
            
            {reviewers.length === 0 && !loading && (
              <p className="text-sm text-red-600 mt-1">No reviewers available. Please contact an administrator.</p>
            )}
          </div>

          {/* Submission Comment */}
          <div className="px-6 py-4">
            <label htmlFor="submissionComment" className="block text-sm font-medium text-gray-700 mb-2">
              Submission Comments <span className="text-xs text-gray-500">(Optional)</span>
            </label>
            <textarea
              id="submissionComment"
              value={submissionComment}
              onChange={(e) => setSubmissionComment(e.target.value)}
              placeholder="Add any comments for the reviewer..."
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
              onClick={handleSubmitForReview}
              disabled={loading || !selectedReviewer}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit for Review'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubmitForReviewModal;