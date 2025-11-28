import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface BaseWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  document: any;
  children: React.ReactNode;
}

const BaseWorkflowModal: React.FC<BaseWorkflowModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  document,
  children
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Document Information Header */}
        <div className="px-6 py-4 bg-blue-50 border-b border-blue-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-semibold text-gray-700">Document:</span>
              <div className="text-gray-900 mt-1">{document.document_number}</div>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Title:</span>
              <div className="text-gray-900 mt-1">{document.title}</div>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Version:</span>
              <div className="text-gray-900 mt-1">
                {document.version_string || `${document.version_major || 1}.${document.version_minor || 0}`}
              </div>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Status:</span>
              <div className="text-gray-900 mt-1">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  document.status === 'UNDER_REVIEW' 
                    ? 'bg-purple-100 text-purple-800'
                    : document.status === 'PENDING_APPROVAL'
                    ? 'bg-orange-100 text-orange-800'
                    : document.status === 'REVIEWED'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {document.status}
                </span>
              </div>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Author:</span>
              <div className="text-gray-900 mt-1">{document.author?.username || 'Unknown'}</div>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Created:</span>
              <div className="text-gray-900 mt-1">
                {document.created_at ? new Date(document.created_at).toLocaleDateString() : 'Unknown'}
              </div>
            </div>
          </div>
        </div>

        {/* Modal Content */}
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
};

export default BaseWorkflowModal;