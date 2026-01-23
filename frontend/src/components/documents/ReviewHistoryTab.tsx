/**
 * Review History Tab Component
 * 
 * Displays the complete periodic review history for a document
 */

import React, { useState, useEffect } from 'react';
import { Document, DocumentReview } from '../../types/api';
import apiService from '../../services/api.ts';

interface ReviewHistoryTabProps {
  document: Document;
}

const ReviewHistoryTab: React.FC<ReviewHistoryTabProps> = ({ document }) => {
  const [reviews, setReviews] = useState<DocumentReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReviewHistory();
  }, [document.uuid]);

  const loadReviewHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getReviewHistory(document.uuid);
      setReviews(response.reviews || []);
    } catch (err: any) {
      console.error('Failed to load review history:', err);
      setError('Failed to load review history');
    } finally {
      setLoading(false);
    }
  };

  const getOutcomeIcon = (outcome: string) => {
    switch (outcome) {
      case 'CONFIRMED': return '✅';
      case 'UPVERSION_REQUIRED': return '🔄';
      // Legacy support for old outcomes
      case 'MINOR_UPVERSION': return '📝';
      case 'MAJOR_UPVERSION': return '🔄';
      case 'UPDATED': return '📝';
      case 'UPVERSIONED': return '🔄';
      default: return '📋';
    }
  };

  const getOutcomeColor = (outcome: string) => {
    switch (outcome) {
      case 'CONFIRMED': return 'bg-green-100 text-green-800';
      case 'UPVERSION_REQUIRED': return 'bg-blue-100 text-blue-800';
      // Legacy support for old outcomes
      case 'MINOR_UPVERSION': return 'bg-blue-100 text-blue-800';
      case 'MAJOR_UPVERSION': return 'bg-orange-100 text-orange-800';
      case 'UPDATED': return 'bg-blue-100 text-blue-800';
      case 'UPVERSIONED': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
          <p className="text-gray-600 text-sm">Loading review history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={loadReviewHistory}
          className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (reviews.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <div className="text-4xl mb-3">📋</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No Review History
        </h3>
        <p className="text-gray-600 text-sm">
          This document has not undergone any periodic reviews yet.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Periodic Review History
        </h3>
        <span className="text-sm text-gray-600">
          {reviews.length} review{reviews.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="space-y-4">
        {reviews.map((review, index) => (
          <div
            key={review.uuid}
            className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{getOutcomeIcon(review.outcome)}</span>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-gray-900">
                      Review #{reviews.length - index}
                    </h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getOutcomeColor(review.outcome)}`}>
                      {review.outcome_display}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {new Date(review.review_date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              </div>
            </div>

            {/* Reviewer Info */}
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                <span className="font-medium">Reviewed by:</span>{' '}
                {review.reviewed_by.full_name || review.reviewed_by.username}
                {' '}({review.reviewed_by.username})
              </p>
            </div>

            {/* Comments */}
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Comments:</p>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded border border-gray-200 whitespace-pre-wrap">
                {review.comments || 'No comments provided'}
              </p>
            </div>

            {/* Additional Info */}
            <div className="flex flex-wrap gap-4 text-sm text-gray-600">
              <div>
                <span className="font-medium">Next Review Scheduled:</span>{' '}
                {new Date(review.next_review_date).toLocaleDateString()}
              </div>
              {review.new_version && (
                <div>
                  <span className="font-medium">Created New Version:</span>{' '}
                  <a
                    href={`/documents/${review.new_version.uuid}`}
                    className="text-blue-600 hover:text-blue-800 underline"
                  >
                    {review.new_version.document_number}
                  </a>
                </div>
              )}
            </div>

            {/* Outcome Details */}
            {(review.outcome === 'UPVERSION_REQUIRED' || review.outcome === 'MAJOR_UPVERSION' || review.outcome === 'MINOR_UPVERSION' || review.outcome === 'UPVERSIONED' || review.outcome === 'UPDATED') && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                <p className="text-xs text-blue-800">
                  🔄 This review identified that up-versioning was required. A new version was created through the version creation workflow.
                  {review.new_version && (
                    <span className="block mt-1 font-medium">
                      New version: {review.new_version.document_number}
                    </span>
                  )}
                </p>
              </div>
            )}
            {review.outcome === 'CONFIRMED' && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
                <p className="text-xs text-green-800">
                  ✅ This review confirmed the document remains accurate with no changes needed.
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReviewHistoryTab;
