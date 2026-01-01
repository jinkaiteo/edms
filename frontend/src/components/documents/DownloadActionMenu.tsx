/**
 * Download Action Menu Component
 * 
 * Provides a dropdown menu with three download options:
 * 1. Download Original Document - The unmodified uploaded file
 * 2. Download Annotated Document - Document with metadata placeholders filled
 * 3. Download Official PDF - Digitally signed PDF (approved documents only)
 * 
 * Based on EDMS specification lines 158-178
 */

import React, { useState, useRef, useEffect } from 'react';
import { Document } from '../../types/api';
import { useAuth } from '../../contexts/AuthContext.tsx';

interface DownloadActionMenuProps {
  document: Document;
  onDownload?: (type: string, success: boolean) => void;
  className?: string;
  disabled?: boolean;
}

interface DownloadOption {
  key: 'original' | 'annotated' | 'official_pdf';
  label: string;
  icon: string;
  description: string;
  available: boolean;
  requiresApproval?: boolean;
}

const DownloadActionMenu: React.FC<DownloadActionMenuProps> = ({
  document,
  onDownload,
  className = '',
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  
  const { authenticated } = useAuth();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    // Use window.document to avoid conflict with the document prop
    window.document.addEventListener('mousedown', handleClickOutside);
    return () => {
      window.document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Get file extension for proper filename
  const getFileExtension = (filename: string): string => {
    return filename.split('.').pop()?.toLowerCase() || 'pdf';
  };

  // Determine available download options based on document state
  const getAvailableDownloadOptions = (): DownloadOption[] => {
    const hasFile = !!(document.file_path && document.file_name);
    const isApproved = ['APPROVED', 'EFFECTIVE', 'APPROVED_AND_EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE'].includes(
      document.status.toUpperCase()
    );

    return [
      {
        key: 'original',
        label: 'Download Original Document',
        icon: '📄',
        description: 'The original unmodified file as uploaded',
        available: hasFile
      },
      {
        key: 'annotated',
        label: 'Download Annotated Document', 
        icon: '📝',
        description: 'Document with metadata placeholders filled',
        available: hasFile
      },
      {
        key: 'official_pdf',
        label: 'Download Official PDF',
        icon: '🔒',
        description: 'Digitally signed PDF (approved documents only)',
        available: hasFile && isApproved,
        requiresApproval: true
      }
    ];
  };

  // Handle download action
  const handleDownload = async (downloadType: 'original' | 'annotated' | 'official_pdf') => {
    console.log('🎯 Download Action Menu - Starting download:', downloadType);
    console.log('🎯 Document:', {
      uuid: document.uuid,
      file_name: document.file_name,
      status: document.status
    });

    if (!authenticated) {
      setError('Authentication required for downloads');
      return;
    }

    if (!document.file_path || !document.file_name) {
      setError('No file available for download');
      return;
    }

    try {
      setDownloading(downloadType);
      setError(null);
      setIsOpen(false); // Close menu when download starts

      let downloadUrl = '';
      switch (downloadType) {
        case 'original':
          downloadUrl = `/api/v1/documents/documents/${document.uuid}/download/original/`;
          break;
        case 'annotated':
          downloadUrl = `/api/v1/documents/documents/${document.uuid}/download/annotated/`;
          break;
        case 'official_pdf':
          downloadUrl = `/api/v1/documents/documents/${document.uuid}/download/official/`;
          break;
      }

      console.log('🔍 Making download request to:', downloadUrl);

      const response = await fetch(downloadUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });

      console.log('🔍 Download response:', {
        status: response.status,
        statusText: response.statusText,
        headers: [...response.headers.entries()]
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Download failed:', errorText);
        throw new Error(`Download failed: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      console.log('🔍 Blob received:', { size: blob.size, type: blob.type });

      // Extract filename from Content-Disposition header (server knows the correct extension)
      let filename = '';
      const contentDisposition = response.headers.get('Content-Disposition');
      
      if (contentDisposition && contentDisposition.includes('filename=')) {
        // Extract filename from Content-Disposition header
        const matches = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
          console.log('🔍 Using server-provided filename:', filename);
        }
      }
      
      // Fallback to constructed filename if header extraction fails
      if (!filename) {
        console.log('⚠️ No Content-Disposition filename found, using fallback');
        switch (downloadType) {
          case 'original':
            filename = `${document.document_number}_original.${getFileExtension(document.file_name)}`;
            break;
          case 'annotated':
            filename = `${document.document_number}_annotated.${getFileExtension(document.file_name)}`;
            break;
          case 'official_pdf':
            filename = `${document.document_number}_official.pdf`;
            break;
        }
      }

      // Create and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = filename;
      
      // Append to body, click, and cleanup
      window.document.body.appendChild(link);
      link.click();
      window.document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      console.log('✅ Download completed successfully:', filename);
      
      // Notify parent component
      if (onDownload) {
        onDownload(downloadType, true);
      }

    } catch (error: any) {
      console.error('❌ Download failed:', error);
      setError(`Download failed: ${error.message || 'Unknown error'}`);
      
      // Notify parent component of failure
      if (onDownload) {
        onDownload(downloadType, false);
      }
    } finally {
      setDownloading(null);
    }
  };

  // Get status-based styling
  const getDownloadOptionStyle = (option: DownloadOption): string => {
    if (!option.available) {
      return 'text-gray-400 cursor-not-allowed opacity-50';
    }
    return 'text-gray-700 hover:bg-gray-50 hover:text-gray-900 cursor-pointer';
  };

  // Get download options
  const downloadOptions = getAvailableDownloadOptions();
  const hasAvailableOptions = downloadOptions.some(option => option.available);

  if (!hasAvailableOptions) {
    return (
      <button
        disabled={true}
        className={`px-3 py-2 text-sm text-gray-400 bg-gray-100 border border-gray-200 rounded-md cursor-not-allowed ${className}`}
      >
        📥 No Downloads Available
      </button>
    );
  }

  return (
    <div className={`relative inline-block text-left ${className}`} ref={menuRef}>
      {/* Main Download Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || downloading !== null}
        className={`inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed ${
          isOpen ? 'ring-2 ring-blue-500 ring-offset-2' : ''
        }`}
      >
        {downloading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            Downloading...
          </>
        ) : (
          <>
            📥 Download
            <svg className="ml-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </>
        )}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
          <div className="py-1">
            {/* Menu Header */}
            <div className="px-4 py-2 border-b border-gray-100">
              <h3 className="text-sm font-medium text-gray-900">Download Options</h3>
              <p className="text-xs text-gray-500">Choose download format for {document.document_number}</p>
            </div>

            {/* Download Options */}
            {downloadOptions.map((option) => (
              <button
                key={option.key}
                onClick={() => option.available && handleDownload(option.key)}
                disabled={!option.available || downloading !== null}
                className={`block w-full text-left px-4 py-3 transition-colors duration-150 ${getDownloadOptionStyle(option)}`}
              >
                <div className="flex items-start">
                  <span className="text-lg mr-3 flex-shrink-0">{option.icon}</span>
                  <div className="flex-grow">
                    <div className={`font-medium ${!option.available ? 'text-gray-400' : 'text-gray-900'}`}>
                      {option.label}
                    </div>
                    <div className={`text-sm ${!option.available ? 'text-gray-300' : 'text-gray-500'}`}>
                      {option.description}
                    </div>
                    {option.requiresApproval && !option.available && (
                      <div className="text-xs text-orange-500 mt-1">
                        ⚠️ Requires document approval
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))}

            {/* Footer Info */}
            <div className="px-4 py-2 border-t border-gray-100 bg-gray-50">
              <p className="text-xs text-gray-500">
                💡 <strong>Original:</strong> Unmodified file • <strong>Annotated:</strong> With metadata • <strong>Official PDF:</strong> Digitally signed
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="absolute top-full left-0 mt-2 w-full bg-red-50 border border-red-200 rounded-md p-2 z-50">
          <div className="flex items-center text-sm text-red-700">
            <svg className="w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="mt-1 text-xs text-red-600 hover:text-red-800"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};

export default DownloadActionMenu;