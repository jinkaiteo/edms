import React, { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';
import { UserSelector } from '../UserSelector';
import { RejectionHistoryModal } from './RejectionHistoryModal';

interface Warning {
  type: string;
  severity: 'low' | 'medium' | 'high';
  title: string;
  message: string;
  suggestion: string;
  rejection_comment?: string;
  rejection_date?: string;
}

interface Recommendation {
  has_rejections: boolean;
  rejection_count: number;
  previously_rejected_reviewers: string[];
  previously_rejected_approvers: string[];
  latest_rejection?: any;
  recommendations: {
    consider_different_reviewer: boolean;
    consider_different_approver: boolean;
    review_rejection_comments: boolean;
    address_concerns_first: boolean;
  };
}

interface EnhancedSubmitForReviewModalProps {
  documentId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const EnhancedSubmitForReviewModal: React.FC<EnhancedSubmitForReviewModalProps> = ({
  documentId,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [selectedReviewer, setSelectedReviewer] = useState<any>(null);
  const [comment, setComment] = useState('');
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [showWarnings, setShowWarnings] = useState(false);
  const [acknowledgeWarnings, setAcknowledgeWarnings] = useState(false);
  const [showRejectionHistory, setShowRejectionHistory] = useState(false);
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation | null>(null);
  const { apiCall } = useApi();

  useEffect(() => {
    if (isOpen && documentId) {
      fetchRecommendations();
    }
  }, [isOpen, documentId]);

  const fetchRecommendations = async () => {
    try {
      const response = await apiCall(`/workflows/documents/${documentId}/assignment-recommendations/`);
      if (response.success) {
        setRecommendations(response.recommendations);
        setWarnings(response.warnings || []);
      }
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    }
  };

  const handleSubmit = async () => {
    if (!selectedReviewer) {
      alert('Please select a reviewer');
      return;
    }

    setLoading(true);
    try {
      const response = await apiCall(`/workflows/documents/${documentId}/submit-for-review-enhanced/`, {
        method: 'POST',
        data: {
          reviewer_id: selectedReviewer.id,
          comment: comment,
          acknowledge_warnings: acknowledgeWarnings
        }
      });

      if (response.success) {
        // Check if warnings require confirmation
        if (response.requires_confirmation) {
          setWarnings(response.warnings);
          setShowWarnings(true);
          setLoading(false);
          return;
        }

        // Success
        onSuccess();
        onClose();
        resetForm();
      } else {
        alert(`Failed to submit: ${response.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to submit for review:', error);
      alert('Failed to submit document for review');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmWithWarnings = () => {
    setAcknowledgeWarnings(true);
    setShowWarnings(false);
    // Automatically resubmit with acknowledgment
    setTimeout(() => handleSubmit(), 100);
  };

  const resetForm = () => {
    setSelectedReviewer(null);
    setComment('');
    setWarnings([]);
    setShowWarnings(false);
    setAcknowledgeWarnings(false);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'border-red-300 bg-red-50 text-red-800';
      case 'medium': return 'border-yellow-300 bg-yellow-50 text-yellow-800';
      case 'low': return 'border-blue-300 bg-blue-50 text-blue-800';
      default: return 'border-gray-300 bg-gray-50 text-gray-800';
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-800">Submit for Review</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          {/* Show recommendations if available */}
          {recommendations?.has_rejections && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-yellow-800 font-medium">
                    ⚠️ This document has been rejected {recommendations.rejection_count} time(s)
                  </p>
                  <p className="text-xs text-yellow-700">
                    Consider reviewing rejection comments before reassigning.
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

          {/* Warning Display */}
          {showWarnings && warnings.length > 0 && (
            <div className="mb-4 space-y-2">
              <h3 className="font-medium text-gray-800">⚠️ Assignment Warnings</h3>
              {warnings.map((warning, index) => (
                <div key={index} className={`p-3 border rounded ${getSeverityColor(warning.severity)}`}>
                  <p className="font-medium text-sm">{warning.title}</p>
                  <p className="text-xs mt-1">{warning.message}</p>
                  {warning.rejection_comment && (
                    <p className="text-xs mt-2 italic">
                      Previous rejection: "{warning.rejection_comment}"
                    </p>
                  )}
                  <p className="text-xs mt-1 font-medium">{warning.suggestion}</p>
                </div>
              ))}
              
              <div className="flex justify-between mt-4">
                <button
                  onClick={() => setShowWarnings(false)}
                  className="px-3 py-1 text-sm bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                >
                  Choose Different Reviewer
                </button>
                <button
                  onClick={handleConfirmWithWarnings}
                  className="px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700"
                >
                  Proceed Anyway
                </button>
              </div>
            </div>
          )}

          {/* Main Form */}
          {!showWarnings && (
            <>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Reviewer *
                </label>
                <UserSelector
                  selectedUser={selectedReviewer}
                  onUserSelect={setSelectedReviewer}
                  roleFilter="reviewer"
                  excludeCurrentUser={true}
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Comment (Optional)
                </label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Add any comments for the reviewer..."
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={!selectedReviewer || loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {loading ? 'Submitting...' : 'Submit for Review'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Rejection History Modal */}
      <RejectionHistoryModal
        documentId={documentId}
        isOpen={showRejectionHistory}
        onClose={() => setShowRejectionHistory(false)}
      />
    </>
  );
};