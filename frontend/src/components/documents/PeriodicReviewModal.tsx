/**
 * Periodic Review Modal Component
 * 
 * Handles the three periodic review outcomes:
 * - CONFIRMED: No changes needed
 * - UPDATED: Minor changes applied
 * - UPVERSIONED: Major changes required (creates new version)
 */

import React, { useState } from 'react';
import { Document, ReviewOutcome } from '../../types/api';
import apiService from '../../services/api.ts';
import { triggerBadgeRefresh } from '../../utils/badgeRefresh.ts';

interface PeriodicReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document;
  onSuccess: () => void;
  onUpversion?: (reviewContext: { outcome: ReviewOutcome; comments: string; nextReviewMonths: number }) => void; // Callback to open version modal with review context
}

type ReviewStep = 'outcome' | 'details';

const PeriodicReviewModal: React.FC<PeriodicReviewModalProps> = ({
  isOpen,
  onClose,
  document,
  onSuccess,
  onUpversion
}) => {
  const [step, setStep] = useState<ReviewStep>('outcome');
  const [selectedOutcome, setSelectedOutcome] = useState<ReviewOutcome | null>(null);
  const [comments, setComments] = useState('');
  const [nextReviewMonths, setNextReviewMonths] = useState(12);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleOutcomeSelect = (outcome: ReviewOutcome) => {
    setSelectedOutcome(outcome);
    setStep('details');
  };

  const handleBack = () => {
    setStep('outcome');
    setError(null);
  };

  const handleSubmit = async () => {
    if (!selectedOutcome) return;

    if (!comments.trim()) {
      setError('Comments are required');
      return;
    }

    // For up-versioning outcome: Open the up-version modal instead
    if (selectedOutcome === 'UPVERSION_REQUIRED') {
      if (onUpversion) {
        // Store the periodic review context
        const reviewContext = {
          outcome: selectedOutcome,
          comments: comments.trim(),
          nextReviewMonths: nextReviewMonths
        };
        
        // Trigger badge refresh - review task completed, version creation will add new task
        triggerBadgeRefresh();
        console.log('✅ Badge refreshed immediately after periodic review up-version initiated');
        
        // Close this modal and trigger upversion flow
        onClose();
        onUpversion(reviewContext);
        
        // Reset form
        setStep('outcome');
        setSelectedOutcome(null);
        setComments('');
        setNextReviewMonths(12);
      } else {
        setError('Version creation is not available. Please contact administrator.');
      }
      return;
    }

    // For CONFIRMED: Complete review immediately
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiService.completePeriodicReview(document.uuid, {
        outcome: selectedOutcome,
        comments: comments.trim(),
        next_review_months: nextReviewMonths
      });

      console.log('Periodic review completed:', response);
      
      // Trigger badge refresh to update "My Tasks" count immediately
      triggerBadgeRefresh();
      console.log('✅ Badge refreshed immediately after periodic review confirmation');
      
      // Show success message
      alert(`✅ Periodic review completed successfully!\n\nOutcome: ${selectedOutcome}\nNext review: ${response.next_review_date}`);
      
      onSuccess();
      onClose();
      
      // Reset form
      setStep('outcome');
      setSelectedOutcome(null);
      setComments('');
      setNextReviewMonths(12);
      
    } catch (err: any) {
      console.error('Failed to complete review:', err);
      setError(err.response?.data?.error || 'Failed to complete periodic review. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
      // Reset after close animation
      setTimeout(() => {
        setStep('outcome');
        setSelectedOutcome(null);
        setComments('');
        setNextReviewMonths(12);
        setError(null);
      }, 300);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-2xl font-semibold text-gray-900">
              Complete Periodic Review
            </h2>
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="text-gray-400 hover:text-gray-500 disabled:opacity-50"
            >
              <span className="text-2xl">&times;</span>
            </button>
          </div>

          {/* Document Info */}
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="text-sm">
              <p className="font-medium text-gray-900">{document.document_number}</p>
              <p className="text-gray-600 mt-1">{document.title}</p>
              {document.last_review_date && (
                <p className="text-gray-500 mt-2 text-xs">
                  Last Review: {new Date(document.last_review_date).toLocaleDateString()} 
                  {document.last_reviewed_by_display && ` by ${document.last_reviewed_by_display}`}
                </p>
              )}
              {document.next_review_date && (
                <p className="text-gray-500 text-xs">
                  Review Due: {new Date(document.next_review_date).toLocaleDateString()}
                  {new Date(document.next_review_date) < new Date() && (
                    <span className="ml-2 text-red-600 font-medium">(Overdue)</span>
                  )}
                </p>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-6">
            {step === 'outcome' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Select Review Outcome
                </h3>
                <p className="text-sm text-gray-600 mb-6">
                  Choose the appropriate outcome based on your review of the document:
                </p>

                <div className="space-y-3">
                  {/* CONFIRMED Option */}
                  <button
                    onClick={() => handleOutcomeSelect('CONFIRMED')}
                    className="w-full text-left p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors"
                  >
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                          <span className="text-green-600 text-xl">✓</span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <h4 className="text-base font-medium text-gray-900">
                          Confirmed - No changes needed
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">
                          Document remains accurate and current. No changes required.
                        </p>
                      </div>
                    </div>
                  </button>

                  {/* UPVERSION_REQUIRED Option */}
                  <button
                    onClick={() => handleOutcomeSelect('UPVERSION_REQUIRED')}
                    className="w-full text-left p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                  >
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-blue-600 text-xl">🔄</span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <h4 className="text-base font-medium text-gray-900">
                          Up-Version Required
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">
                          Changes needed - opens version creation modal where you can select minor (v1.0 → v1.1) or major (v1.0 → v2.0).
                        </p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            )}

            {step === 'details' && selectedOutcome && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-medium text-gray-900">
                    {selectedOutcome === 'CONFIRMED' && 'Confirm Review'}
                    {selectedOutcome === 'UPVERSION_REQUIRED' && 'Up-Version Required'}
                  </h3>
                  <button
                    onClick={handleBack}
                    disabled={isSubmitting}
                    className="text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50"
                  >
                    ← Back
                  </button>
                </div>

                {/* Outcome-specific content */}
                {selectedOutcome === 'CONFIRMED' && (
                  <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-800">
                      ℹ️ The document will remain EFFECTIVE. Review history will be updated and audit trail created.
                    </p>
                  </div>
                )}

                {selectedOutcome === 'UPVERSION_REQUIRED' && (
                  <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800 font-medium mb-2">
                      🔄 Up-Version Required
                    </p>
                    <p className="text-sm text-blue-700">
                      Clicking "Continue to Version Creation" will:
                    </p>
                    <ol className="text-sm text-blue-700 list-decimal list-inside space-y-1 mt-2">
                      <li>Open the version creation modal</li>
                      <li>Allow you to select minor or major version</li>
                      <li>Create new version after you provide details</li>
                      <li>Automatically complete this periodic review</li>
                    </ol>
                    <p className="text-sm text-blue-700 mt-2">
                      Current version remains EFFECTIVE until new version is approved.
                    </p>
                  </div>
                )}

                {/* Comments Field */}
                <div className="mb-6">
                  <label htmlFor="comments" className="block text-sm font-medium text-gray-700 mb-2">
                    Review Comments <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    id="comments"
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    disabled={isSubmitting}
                    rows={5}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    placeholder={
                      selectedOutcome === 'CONFIRMED'
                        ? 'Describe what was verified during the review...'
                        : 'Describe why up-version is needed and what will be changed...'
                    }
                  />
                  {comments.trim().length === 0 && error && (
                    <p className="mt-1 text-sm text-red-600">{error}</p>
                  )}
                </div>

                {/* Next Review Schedule */}
                <div className="mb-6">
                  <label htmlFor="nextReview" className="block text-sm font-medium text-gray-700 mb-2">
                    Next Review Schedule
                  </label>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-2 sm:space-y-0">
                    <select
                      id="nextReview"
                      value={nextReviewMonths}
                      onChange={(e) => setNextReviewMonths(parseInt(e.target.value))}
                      disabled={isSubmitting}
                      className="w-full sm:w-auto px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 appearance-none bg-white"
                      style={{ backgroundImage: 'url("data:image/svg+xml,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 fill=%27none%27 viewBox=%270 0 20 20%27%3e%3cpath stroke=%27%236b7280%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27 stroke-width=%271.5%27 d=%27M6 8l4 4 4-4%27/%3e%3c/svg%3e")', backgroundPosition: 'right 0.5rem center', backgroundRepeat: 'no-repeat', backgroundSize: '1.5em 1.5em' }}
                    >
                      <option value={6}>6 months</option>
                      <option value={12}>12 months (Annual)</option>
                      <option value={18}>18 months</option>
                      <option value={24}>24 months (Biennial)</option>
                      <option value={36}>36 months</option>
                    </select>
                    <span className="text-sm text-gray-600">
                      Next Review: {new Date(Date.now() + nextReviewMonths * 30 * 24 * 60 * 60 * 1000).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-800">❌ {error}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            
            {step === 'details' && (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting || !comments.trim()}
                className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Processing...' : 
                  selectedOutcome === 'UPVERSION_REQUIRED' ? 'Continue to Version Creation' : 
                  'Complete Review'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PeriodicReviewModal;
