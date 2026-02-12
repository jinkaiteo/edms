import React from 'react';
import ReactDOM from 'react-dom';
import { XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';

interface PDFViewerSimpleProps {
  pdfUrl: string;
  documentTitle?: string;
  documentNumber?: string;
  onClose: () => void;
}

/**
 * Simple PDF Viewer using browser's native PDF viewer
 * No external dependencies, works in all modern browsers
 */
const PDFViewerSimple: React.FC<PDFViewerSimpleProps> = ({ 
  pdfUrl, 
  documentTitle, 
  documentNumber,
  onClose 
}) => {
  // Use React Portal to render at document body level, bypassing all parent z-index contexts
  return ReactDOM.createPortal(
    <div className="fixed inset-0 z-[60] bg-white flex flex-col">
      {/* Header */}
      <div className="bg-gray-100 border-b px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {documentTitle || 'PDF Viewer'}
            </h3>
            {documentNumber && (
              <p className="text-sm text-gray-600">{documentNumber}</p>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Download Button */}
          <a
            href={pdfUrl}
            download
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            title="Download PDF"
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Download
          </a>
          
          {/* Close Button */}
          <button
            onClick={onClose}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            title="Close PDF Viewer"
          >
            <XMarkIcon className="h-4 w-4 mr-2" />
            Close
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 bg-gray-800">
        <iframe 
          src={pdfUrl}
          className="w-full h-full border-0"
          title={documentTitle || 'PDF Document'}
          style={{ minHeight: '100%' }}
        />
      </div>
    </div>,
    document.body // Render at body level, outside all parent components
  );
};

export default PDFViewerSimple;
