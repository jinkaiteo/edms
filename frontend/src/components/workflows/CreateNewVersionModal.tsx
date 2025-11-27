/**
 * Create New Version Modal Component
 * 
 * Allows users to initiate up-versioning workflow for effective documents.
 * Creates a new document version and starts the review process.
 */

import React, { useState } from 'react';
import { apiService } from '../../services/api.ts';
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

  const getNewVersionString = () => {
    if (versionType === 'major') {
      return `${document.version_major + 1}.0`;
    } else {
      return `${document.version_major}.${document.version_minor + 1}`;
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


      setLoading(true);
      setError(null);

      // Create new version through workflow API
      const versionData = {
        action: 'create_new_version',
        version_type: versionType,
        major_increment: versionType === 'major',
        reason_for_change: reasonForChange,
        change_summary: changeSummary,
        version_comment: versionComment || `New ${versionType} version created`,
        metadata: {
          source_document: document.uuid,
          source_version: document.version_string,
          created_by: 'author'
        }
      };


      const workflowResponse = await apiService.post(`/documents/documents/${document.uuid}/workflow/`, versionData);

      // Check if a new document was created or if we get the new document data
      let newDocument = null;
      if (workflowResponse.new_document) {
        newDocument = workflowResponse.new_document;
      } else if (workflowResponse.document) {
        newDocument = workflowResponse.document;
      }


      if (newDocument) {
        onVersionCreated(newDocument);
      } else {
        // Fallback: just trigger refresh
        onVersionCreated(null);
      }

      onClose();

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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
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

          {/* Error Display */}
          {error && (
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
                    Minor Version ({document.version_major}.{document.version_minor + 1})
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
                    Major Version ({document.version_major + 1}.0)
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
            disabled={loading || !reasonForChange.trim() || !changeSummary.trim()}
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