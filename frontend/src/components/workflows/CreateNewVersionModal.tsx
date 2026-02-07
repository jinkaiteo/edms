/**
 * Create New Version Modal Component
 * 
 * Allows users to initiate up-versioning workflow for effective documents.
 * Creates a new document version and starts the review process.
 */

import React, { useState } from 'react';
import { apiService } from '../../services/api.ts';
import { triggerBadgeRefresh } from '../../utils/badgeRefresh.ts';
import { 
  XMarkIcon,
  DocumentPlusIcon,
  ClockIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface Document {
  uuid: string;
  document_number: string;
  title: string;
  status: string;
  version_major: number;
  version_minor: number;
  version_string: string;
  author_display: string;
  effective_date: string;
}

interface CreateNewVersionModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document;
  onVersionCreated: (newDocument: any) => void;
}

const CreateNewVersionModal: React.FC<CreateNewVersionModalProps> = ({
  isOpen,
  onClose,
  document,
  onVersionCreated
}) => {
  const [versionType, setVersionType] = useState<'major' | 'minor'>('minor');
  const [reasonForChange, setReasonForChange] = useState<string>('');
  const [changeSummary, setChangeSummary] = useState<string>('');
  const [versionComment, setVersionComment] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkingExistingVersions, setCheckingExistingVersions] = useState(false);
  const [hasOngoingVersion, setHasOngoingVersion] = useState(false);
  const [ongoingVersionInfo, setOngoingVersionInfo] = useState<any>(null);

  const getNewVersionString = () => {
    const currentMajor = document?.version_major || 0;
    const currentMinor = document?.version_minor || 0;
    
    if (versionType === 'major') {
      return `${(currentMajor + 1).toString().padStart(2, '0')}.00`;
    } else {
      return `${currentMajor.toString().padStart(2, '0')}.${(currentMinor + 1).toString().padStart(2, '0')}`;
    }
  };


  const checkForOngoingVersions = async () => {
    setCheckingExistingVersions(true);
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Check for existing documents with same base number but higher versions in draft/review status
      const response = await fetch(`/api/v1/documents/documents/?search=${document.document_number}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const documents = data.results || [];
        
        // Look for documents with same base number but in draft/review status (ongoing versions)
        const baseDocNumber = document.document_number.split('-v')[0]; // Extract base: SOP-2025-0001 from SOP-2025-0001-v01.00
        
        const ongoingVersions = documents.filter((doc: any) => {
          const docBaseNumber = doc.document_number.split('-v')[0];
          return (
            docBaseNumber === baseDocNumber && 
            doc.uuid !== document.uuid && // Not the current document
            ['DRAFT', 'UNDER_REVIEW', 'REVIEWED', 'PENDING_APPROVAL'].includes(doc.status) // Ongoing workflow states
          );
        });

        if (ongoingVersions.length > 0) {
          setHasOngoingVersion(true);
          setOngoingVersionInfo(ongoingVersions[0]); // Show info about the first ongoing version
          setError(`Cannot create new version: There is already an ongoing version (${ongoingVersions[0].document_number}) in ${ongoingVersions[0].status} status.`);
        } else {
          setHasOngoingVersion(false);
          setOngoingVersionInfo(null);
        }
      }
    } catch (error: any) {
      console.error('Error checking for ongoing versions:', error);
      // Don't block version creation if check fails, just log the error
    } finally {
      setCheckingExistingVersions(false);
    }
  };

  const handleCreateNewVersion = async () => {
    try {
      if (!reasonForChange.trim()) {
        setError('Please provide a reason for the version change');
        return;
      }

      if (!changeSummary.trim()) {
        setError('Please provide a summary of changes');
        return;
      }

      if (hasOngoingVersion) {
        setError('Cannot create new version while another version is in progress');
        return;
      }


      setLoading(true);
      setError(null);

      // Create new version through workflow API
      const versionData = {
        action: 'start_version_workflow',
        major_increment: versionType === 'major',
        reason_for_change: reasonForChange,
        change_summary: changeSummary,
        title: document.title,
        description: document.description || ''  // Ensure description is never null
      };

      // Debug logging can be removed in production
      
      const workflowResponse = await apiService.post(`/workflows/documents/${document.uuid}/`, versionData);

      // Check if a new document was created or if we get the new document data
      let newDocument = null;
      // Extract new document from response (not currently used)
      // let newDocument;
      // if (workflowResponse.new_document) {
      //   newDocument = workflowResponse.new_document;
      // } else if (workflowResponse.document) {
      //   newDocument = workflowResponse.document;
      // }

      if (workflowResponse.success) {
        // Trigger badge refresh to update "My Tasks" count immediately
        triggerBadgeRefresh();
        console.log('✅ Badge refreshed immediately after new version creation');
        
        onVersionCreated({
          success: true,
          message: workflowResponse.message,
          newDocumentId: workflowResponse.new_document_id,
          newDocumentNumber: workflowResponse.new_document_number,
          newVersion: workflowResponse.new_version
        });
        onClose();
      } else {
        setError(workflowResponse.error || 'Failed to create new version');
      }

    } catch (workflowError: any) {
      console.error('❌ WORKFLOW: Failed to create new version - full error:', workflowError);
      
      if (workflowError.response?.status === 400) {
        setError(workflowError.response?.data?.detail || 'Invalid version creation request. Please check the form data.');
      } else {
        setError('Failed to create new version. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setVersionType('minor');
      setReasonForChange('');
      setChangeSummary('');
      setVersionComment('');
      setError(null);
      onClose();
    }
  };

  // Check for ongoing versions when modal opens
  React.useEffect(() => {
    if (isOpen) {
      checkForOngoingVersions();
    }
  }, [isOpen, document.uuid]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 overflow-y-auto bg-gray-500 bg-opacity-75 flex items-center justify-center p-4" style={{ zIndex: 9999 }}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <DocumentPlusIcon className="h-6 w-6 text-blue-600" />
              <h3 className="text-lg font-medium text-gray-900">
                Create New Version
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
          {/* Current Document Info */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">Current Document</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-700">Document:</span>
                <p className="font-medium">{document.document_number}</p>
              </div>
              <div>
                <span className="text-blue-700">Current Version:</span>
                <p className="font-medium">{document.version_string}</p>
              </div>
              <div>
                <span className="text-blue-700">Author:</span>
                <p>{document.author_display}</p>
              </div>
              <div>
                <span className="text-blue-700">Effective Date:</span>
                <p>{new Date(document.effective_date).toLocaleDateString()}</p>
              </div>
            </div>
          </div>

          {/* Loading Check */}
          {checkingExistingVersions && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center space-x-2">
                <ClockIcon className="h-5 w-5 text-blue-400 animate-spin" />
                <p className="text-sm text-blue-700">Checking for ongoing version workflows...</p>
              </div>
            </div>
          )}

          {/* Ongoing Version Warning */}
          {hasOngoingVersion && ongoingVersionInfo && (
            <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-md">
              <div className="flex items-start space-x-3">
                <ExclamationTriangleIcon className="h-5 w-5 text-amber-400 mt-0.5" />
                <div>
                  <h4 className="font-medium text-amber-900">Ongoing Version Detected</h4>
                  <div className="text-sm text-amber-700 mt-1">
                    <p><strong>{ongoingVersionInfo.document_number}</strong> is currently in <strong>{ongoingVersionInfo.status}</strong> status.</p>
                    <p className="mt-1">Please wait for this version to complete its workflow before creating a new version.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && !hasOngoingVersion && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center space-x-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Version Type Selection */}
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Version Type</h4>
            <div className="space-y-3">
              <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  name="versionType"
                  value="minor"
                  checked={versionType === 'minor'}
                  onChange={(e) => setVersionType(e.target.value as 'minor')}
                  disabled={loading}
                  className="text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-medium text-gray-900">
                    Minor Version ({(document?.version_major || 0).toString().padStart(2, '0')}.{((document?.version_minor || 0) + 1).toString().padStart(2, '0')})
                  </div>
                  <div className="text-sm text-gray-600">
                    Small changes, corrections, or updates that don't affect the core content significantly.
                  </div>
                </div>
              </label>
              
              <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  name="versionType"
                  value="major"
                  checked={versionType === 'major'}
                  onChange={(e) => setVersionType(e.target.value as 'major')}
                  disabled={loading}
                  className="text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="font-medium text-gray-900">
                    Major Version ({((document?.version_major || 0) + 1).toString().padStart(2, '0')}.00)
                  </div>
                  <div className="text-sm text-gray-600">
                    Significant changes that substantially alter the document content or structure.
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Reason for Change */}
          <div className="mb-6">
            <label htmlFor="reasonForChange" className="block text-sm font-medium text-gray-700 mb-2">
              Reason for Change <span className="text-red-500">*</span>
            </label>
            <textarea
              id="reasonForChange"
              value={reasonForChange}
              onChange={(e) => setReasonForChange(e.target.value)}
              disabled={loading}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
              placeholder="Explain why a new version is needed (e.g., regulatory changes, process improvements, corrections...)"
              required
            />
          </div>

          {/* Change Summary */}
          <div className="mb-6">
            <label htmlFor="changeSummary" className="block text-sm font-medium text-gray-700 mb-2">
              Summary of Changes <span className="text-red-500">*</span>
            </label>
            <textarea
              id="changeSummary"
              value={changeSummary}
              onChange={(e) => setChangeSummary(e.target.value)}
              disabled={loading}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
              placeholder="Describe what changes will be made in this new version..."
              required
            />
          </div>

          {/* Version Comment */}
          <div className="mb-6">
            <label htmlFor="versionComment" className="block text-sm font-medium text-gray-700 mb-2">
              Version Notes (Optional)
            </label>
            <textarea
              id="versionComment"
              value={versionComment}
              onChange={(e) => setVersionComment(e.target.value)}
              disabled={loading}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
              placeholder="Additional notes about this version..."
            />
          </div>

          {/* Process Information */}
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <InformationCircleIcon className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-amber-900">Version Creation Process</h4>
                <div className="text-sm text-amber-700 mt-1 space-y-1">
                  <p>
                    • A new <strong>{getNewVersionString()}</strong> version will be created in <strong>DRAFT</strong> status
                  </p>
                  <p>
                    • The current version ({document.version_string}) will remain <strong>EFFECTIVE</strong> until the new version is approved
                  </p>
                  <p>
                    • You can edit and upload the new document file after creation
                  </p>
                  <p>
                    • The new version will go through the standard review and approval workflow
                  </p>
                  {versionType === 'major' && (
                    <p className="font-medium">
                      • <strong>Major version:</strong> Dependent documents may need review for impact assessment
                    </p>
                  )}
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
            onClick={handleCreateNewVersion}
            disabled={loading || !reasonForChange.trim() || !changeSummary.trim() || hasOngoingVersion || checkingExistingVersions}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            {loading && <ClockIcon className="h-4 w-4 animate-spin" />}
            <DocumentPlusIcon className="h-4 w-4" />
            <span>
              {loading 
                ? 'Creating...' 
                : `Create Version ${getNewVersionString()}`
              }
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateNewVersionModal;