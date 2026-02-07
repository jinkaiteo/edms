/**
 * Set Effective Date Modal Component
 * 
 * Allows approvers to set when an approved document becomes effective.
 * Used when document status is APPROVED.
 */

import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api.ts';
import { 
  XMarkIcon,
  CalendarDaysIcon,
  ClockIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface Document {
  uuid: string;
  document_number: string;
  title: string;
  status: string;
  author_display: string;
  reviewer_display: string;
  approver_display: string;
  approval_date?: string;
}

interface SetEffectiveDateModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document;
  onEffectiveDateSet: () => void;
}

const SetEffectiveDateModal: React.FC<SetEffectiveDateModalProps> = ({
  isOpen,
  onClose,
  document,
  onEffectiveDateSet
}) => {
  const [effectiveDate, setEffectiveDate] = useState<string>('');
  const [effectiveTime, setEffectiveTime] = useState<string>('00:00');
  const [immediateEffective, setImmediateEffective] = useState<boolean>(false);
  const [comments, setComments] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Set default date to today
      const today = new Date();
      setEffectiveDate(today.toISOString().split('T')[0]);
      // Set current time as default instead of hardcoded 08:00
      const currentTime = today.toTimeString().slice(0, 5); // HH:MM format
      setEffectiveTime(currentTime);
      setComments('');
      setError(null);
    }
  }, [isOpen]);

  const getMinDate = () => {
    // Allow effective date from today onwards
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  const getMaxDate = () => {
    // Allow effective date up to 1 year from now
    const maxDate = new Date();
    maxDate.setFullYear(maxDate.getFullYear() + 1);
    return maxDate.toISOString().split('T')[0];
  };

  const handleSetEffectiveDate = async () => {
    try {
      if (!immediateEffective && !effectiveDate) {
        setError('Please select an effective date or choose immediate effectiveness');
        return;
      }

      if (effectiveDate && new Date(effectiveDate) < new Date().setHours(0, 0, 0, 0)) {
        setError('Effective date cannot be in the past');
        return;
      }


      setLoading(true);
      setError(null);

      // Calculate final effective date (date only for backend, datetime for workflow)
      let finalEffectiveDate: string;
      let finalEffectiveDateTime: string;
      
      if (immediateEffective) {
        const now = new Date();
        finalEffectiveDate = now.toISOString().split('T')[0]; // YYYY-MM-DD format for backend
        finalEffectiveDateTime = now.toISOString(); // Full datetime for workflow
      } else {
        finalEffectiveDate = effectiveDate; // Already in YYYY-MM-DD format
        const effectiveDateTime = new Date(`${effectiveDate}T${effectiveTime}`);
        finalEffectiveDateTime = effectiveDateTime.toISOString(); // Full datetime for workflow
      }

      // Step 1: Update document with effective date
      console.log('🔍 Debug - SetEffectiveDate data being sent:', {
        document_uuid: document.uuid,
        document_number: document.document_number,
        current_status: document.status,
        finalEffectiveDate: finalEffectiveDate,
        finalEffectiveDateTime: finalEffectiveDateTime,
        effectiveDate: effectiveDate,
        effectiveTime: effectiveTime,
        immediateEffective: immediateEffective
      });

      // Set effective date and transition to EFFECTIVE status via workflow action
      const workflowResponse = await apiService.post(`/documents/documents/${document.uuid}/workflow/`, {
        action: 'make_effective',
        comment: comments || `Document set to be effective ${immediateEffective ? 'immediately' : `on ${effectiveDate} at ${effectiveTime}`}`,
        effective_date: finalEffectiveDateTime, // Use full datetime for workflow
        metadata: {
          effective_date: finalEffectiveDateTime,
          immediate: immediateEffective,
          set_by: 'approver'
        }
      });


      onEffectiveDateSet();
      onClose();

    } catch (workflowError: any) {
      console.error('❌ WORKFLOW: Failed to set effective date - full error:', workflowError);
      setError('Failed to set effective date. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setEffectiveDate('');
      // Set current time as default
      const currentTime = new Date().toTimeString().slice(0, 5);
      setEffectiveTime(currentTime);
      setImmediateEffective(false);
      setComments('');
      setError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 overflow-y-auto" style={{ zIndex: 9999 }} bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CalendarDaysIcon className="h-6 w-6 text-blue-600" />
              <h3 className="text-lg font-medium text-gray-900">
                Set Effective Date
              </h3>
            </div>
            <button
              onClick={handleClose}
              disabled={loading}
              className="text-gray-400 hover:text-gray-500 disabled:opacity-50"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="px-6 py-4">
          {/* Document Info */}
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-medium text-green-900 mb-2">Approved Document</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-green-700">Document:</span>
                <p className="font-medium">{document.document_number}</p>
              </div>
              <div>
                <span className="text-green-700">Title:</span>
                <p className="font-medium">{document.title}</p>
              </div>
              <div>
                <span className="text-green-700">Author:</span>
                <p>{document.author_display}</p>
              </div>
              <div>
                <span className="text-green-700">Reviewer:</span>
                <p>{document.reviewer_display}</p>
              </div>
              <div>
                <span className="text-green-700">Approver:</span>
                <p>{document.approver_display}</p>
              </div>
              <div>
                <span className="text-green-700">Approval Date:</span>
                <p>{document.approval_date ? new Date(document.approval_date).toLocaleDateString() : 'Today'}</p>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center space-x-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Immediate Effective Option */}
          <div className="mb-6">
            <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
              <input
                type="checkbox"
                checked={immediateEffective}
                onChange={(e) => setImmediateEffective(e.target.checked)}
                disabled={loading}
                className="text-blue-600 focus:ring-blue-500 rounded"
              />
              <CheckCircleIcon className="h-5 w-5 text-blue-600" />
              <div>
                <div className="font-medium text-gray-900">Make Effective Immediately</div>
                <div className="text-sm text-gray-600">
                  Document will become effective right now when you confirm.
                </div>
              </div>
            </label>
          </div>

          {/* Scheduled Effective Date */}
          {!immediateEffective && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">Schedule Effective Date</h4>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="effectiveDate" className="block text-sm font-medium text-gray-700 mb-2">
                    Effective Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    id="effectiveDate"
                    value={effectiveDate}
                    min={getMinDate()}
                    max={getMaxDate()}
                    onChange={(e) => setEffectiveDate(e.target.value)}
                    disabled={loading}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
                    required
                  />
                </div>
                
                <div>
                  <label htmlFor="effectiveTime" className="block text-sm font-medium text-gray-700 mb-2">
                    Effective Time
                  </label>
                  <input
                    type="time"
                    id="effectiveTime"
                    value={effectiveTime}
                    onChange={(e) => setEffectiveTime(e.target.value)}
                    disabled={loading}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
                  />
                </div>
              </div>
              
              <p className="text-xs text-gray-500 mt-2">
                The document will become effective on the specified date and time. 
                Current timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}
              </p>
            </div>
          )}

          {/* Comments */}
          <div className="mb-6">
            <label htmlFor="comments" className="block text-sm font-medium text-gray-700 mb-2">
              Comments (Optional)
            </label>
            <textarea
              id="comments"
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              disabled={loading}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
              placeholder="Add any notes about when and why this effective date was chosen..."
            />
          </div>

          {/* Process Information */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900">What Happens Next</h4>
                <div className="text-sm text-blue-700 mt-1">
                  {immediateEffective ? (
                    <p>
                      The document will be immediately moved to <strong>EFFECTIVE</strong> status 
                      and will be available for use organization-wide.
                    </p>
                  ) : (
                    <p>
                      The document will be scheduled to become <strong>EFFECTIVE</strong> on{' '}
                      <strong>{effectiveDate ? new Date(effectiveDate).toLocaleDateString() : '[selected date]'}</strong>{' '}
                      at <strong>{effectiveTime}</strong>. It will remain in APPROVED status until then.
                    </p>
                  )}
                  <p className="mt-2">
                    Once effective, the document will be the official version and any previous 
                    versions will be superseded.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={handleClose}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSetEffectiveDate}
            disabled={loading || (!immediateEffective && !effectiveDate)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            {loading && <ClockIcon className="h-4 w-4 animate-spin" />}
            <CalendarDaysIcon className="h-4 w-4" />
            <span>
              {loading 
                ? 'Setting...' 
                : immediateEffective 
                  ? 'Make Effective Now' 
                  : 'Schedule Effective Date'
              }
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default SetEffectiveDateModal;