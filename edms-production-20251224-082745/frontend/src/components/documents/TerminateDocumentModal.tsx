import React, { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface TerminateDocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason: string) => void;
  documentNumber: string;
  documentTitle: string;
  isLoading?: boolean;
}

const TerminateDocumentModal: React.FC<TerminateDocumentModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  documentNumber,
  documentTitle,
  isLoading = false
}) => {
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!reason.trim()) {
      setError('Termination reason is required');
      return;
    }

    if (reason.trim().length < 10) {
      setError('Please provide a more detailed reason (at least 10 characters)');
      return;
    }

    setError('');
    onConfirm(reason.trim());
  };

  const handleClose = () => {
    setReason('');
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <span className="text-2xl">🛑</span>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Terminate Document
                </h3>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
              disabled={isLoading}
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Document Info */}
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm font-medium text-gray-900">{documentNumber}</p>
            <p className="text-sm text-gray-600">{documentTitle}</p>
          </div>

          {/* Warning */}
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-red-500 text-sm">⚠️</span>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-red-800">
                  This action cannot be undone
                </h4>
                <p className="text-sm text-red-700 mt-1">
                  Terminating this document will permanently stop its workflow process. 
                  The document will be marked as terminated and cannot be reactivated.
                </p>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
                Reason for Termination *
              </label>
              <textarea
                id="reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Please provide a detailed reason for terminating this document..."
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500"
                disabled={isLoading}
                maxLength={500}
              />
              {error && (
                <p className="mt-1 text-sm text-red-600">{error}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                {reason.length}/500 characters
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isLoading || !reason.trim()}
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Terminating...
                  </>
                ) : (
                  '🛑 Terminate Document'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TerminateDocumentModal;