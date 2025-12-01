import React, { useState, useEffect } from 'react';
import { XMarkIcon, ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import { apiService } from '../../services/api.ts';

interface Document {
  uuid: string;
  document_number: string;
  title: string;
  status: string;
}

interface MarkObsoleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document;
  onSuccess: () => void;
}

const MarkObsoleteModal: React.FC<MarkObsoleteModalProps> = ({
  isOpen,
  onClose,
  document,
  onSuccess
}) => {
  const [reasonForObsolescence, setReasonForObsolescence] = useState<string>('');
  const [obsolescenceDate, setObsolescenceDate] = useState<string>('');
  const [dependencies, setDependencies] = useState<any[]>([]);
  const [checkingDependencies, setCheckingDependencies] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dependencyError, setDependencyError] = useState<string | null>(null);

  const hasDependencies = dependencies.length > 0;

  useEffect(() => {
    if (isOpen) {
      checkDocumentDependencies();
    }
  }, [isOpen, document.uuid]);

  const checkDocumentDependencies = async () => {
    try {
      setCheckingDependencies(true);
      setDependencyError(null);
      
      const response = await apiService.get(`/documents/documents/${document.uuid}/dependencies/`);
      
      if (response?.dependents) {
        // Enhanced dependency check - filter by document status, not just is_active flag
        // Any dependent document NOT in final states (TERMINATED, SUPERSEDED, OBSOLETE) blocks obsolescence
        const blockingDependents = [];
        
        for (const dep of response.dependents) {
          // Fetch the dependent document's current status using UUID, not database ID
          try {
            // We need to get the document UUID from the database ID
            // First get the document using its ID to find its UUID
            console.log('🔍 Checking dependency:', dep);
            
            // Use the document display name to find the document by document_number
            const searchResponse = await apiService.get(`/documents/documents/?search=${encodeURIComponent(dep.document_display)}`);
            
            let depDocStatus;
            if (searchResponse?.results && searchResponse.results.length > 0) {
              const depDoc = searchResponse.results[0];
              depDocStatus = depDoc.status;
              console.log(`📄 Found dependent document ${dep.document_display}: Status = ${depDocStatus}`);
            } else {
              throw new Error(`Document ${dep.document_display} not found`);
            }
            
            // Check if dependent document is in a non-final state
            if (!['TERMINATED', 'SUPERSEDED', 'OBSOLETE'].includes(depDocStatus)) {
              blockingDependents.push({
                ...dep,
                document_status: depDocStatus,
                document_number: dep.document_display || `Document ${dep.document}`
              });
            }
          } catch (docError) {
            console.error('Error fetching dependent document status:', docError);
            // If we can't get status, assume it's blocking to be safe
            blockingDependents.push({
              ...dep,
              document_status: 'UNKNOWN',
              document_number: dep.document_display || `Document ${dep.document}`
            });
          }
        }
        
        setDependencies(blockingDependents);
        
        if (blockingDependents.length > 0) {
          console.log('⚠️ Document has blocking dependencies:', blockingDependents);
          setDependencyError(
            `Cannot obsolete: ${blockingDependents.length} dependent document(s) must be terminated, superseded, or obsoleted first.`
          );
        } else {
          setDependencyError(null);
        }
      } else {
        setDependencies([]);
        setDependencyError(null);
      }
    } catch (error) {
      console.error('Error checking dependencies:', error);
      setDependencyError('Failed to check document dependencies');
      setDependencies([]);
    } finally {
      setCheckingDependencies(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (!reasonForObsolescence.trim()) {
        setError('Please provide a reason for marking the document obsolete');
        return;
      }
      
      if (!obsolescenceDate) {
        setError('Obsolescence date is required');
        return;
      }
      
      // Validate that obsolescence date is in the future
      const selectedDate = new Date(obsolescenceDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (selectedDate <= today) {
        setError('Obsolescence date must be in the future');
        return;
      }

      if (dependencies.length > 0) {
        setError('Cannot proceed: Document has dependencies that must be resolved first');
        return;
      }

      setLoading(true);
      setError(null);

      const workflowData = {
        action: 'obsolete_document_directly',
        reason: reasonForObsolescence,
        obsolescence_date: obsolescenceDate,
      };

      console.log('🚀 Submitting obsolescence request:', workflowData);

      const workflowResponse = await apiService.post(
        `/workflows/documents/${document.uuid}/`,
        workflowData
      );

      if (workflowResponse?.success) {
        console.log('✅ Obsolescence workflow started successfully');
        onSuccess();
        handleClose();
      } else {
        console.error('❌ Workflow response indicates failure:', workflowResponse);
        setError(workflowResponse?.message || 'Failed to initiate obsolescence');
      }
      
    } catch (workflowError: any) {
      console.error('❌ Error in obsolescence workflow:', workflowError);
      
      if (workflowError.response?.status === 403) {
        setError('You do not have authority to mark this document obsolete.');
      } else if (workflowError.response?.status === 400) {
        const errorData = workflowError.response?.data;
        if (errorData?.error) {
          setError(errorData.error);
        } else {
          setError('Invalid request. Please check your input and try again.');
        }
      } else {
        setError('Failed to initiate obsolescence. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setReasonForObsolescence('');
    setObsolescenceDate('');
    setDependencies([]);
    setError(null);
    setDependencyError(null);
    onClose();
  };

  if (!isOpen) return null;

  const canProceed = !hasDependencies && !checkingDependencies && reasonForObsolescence.trim().length > 0 && obsolescenceDate.length > 0;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={handleClose}></div>
        
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
        
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6 max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-gray-900">Mark Document Obsolete</h3>
            <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Document Info */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Document Information</h4>
              <p className="text-sm text-gray-700">
                <strong>Document:</strong> {document.document_number}
              </p>
              <p className="text-sm text-gray-700">
                <strong>Title:</strong> {document.title}
              </p>
              <p className="text-sm text-gray-700">
                <strong>Current Status:</strong> {document.status}
              </p>
            </div>

            {/* Reason for Obsolescence */}
            <div className="mb-6">
              <label htmlFor="reasonForObsolescence" className="block text-sm font-medium text-gray-700 mb-2">
                Reason for Obsolescence *
              </label>
              <textarea
                id="reasonForObsolescence"
                value={reasonForObsolescence}
                onChange={(e) => setReasonForObsolescence(e.target.value)}
                disabled={loading || hasDependencies}
                rows={3}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 disabled:opacity-50"
                placeholder="Provide a detailed reason for marking this document obsolete..."
              />
            </div>

            {/* Obsolescence Date - Required Field */}
            <div className="mb-6">
              <label htmlFor="obsolescenceDate" className="block text-sm font-medium text-gray-700 mb-2">
                Obsolescence Date *
                <span className="text-xs text-gray-500 ml-2">
                  (Document will become obsolete on this date)
                </span>
              </label>
              <input
                type="date"
                id="obsolescenceDate"
                value={obsolescenceDate}
                onChange={(e) => setObsolescenceDate(e.target.value)}
                min={new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0]} // Tomorrow
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Select a future date when this document will become obsolete. 
                All stakeholders will be notified immediately and on the obsolescence date.
              </p>
            </div>

            {/* Dependency Error Display */}
            {dependencyError && (
              <div className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded-md">
                <div className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-orange-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-orange-900 mb-2">Dependency Conflict</h4>
                    <p className="text-sm text-orange-700 mb-2">{dependencyError}</p>
                    {dependencies.length > 0 && (
                      <div className="text-sm text-orange-700">
                        <p className="font-medium mb-1">Blocking documents:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {dependencies.map((dep, index) => (
                            <li key={index}>
                              <strong>{dep.document_number}</strong> (Status: {dep.document_status})
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* General Error Display */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <div className="flex items-center space-x-2">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}


            {/* Action Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!canProceed || loading}
                className={`px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 ${
                  canProceed && !loading
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-gray-400 cursor-not-allowed'
                }`}
              >
                {loading ? 'Processing...' : 'Mark Obsolete'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default MarkObsoleteModal;