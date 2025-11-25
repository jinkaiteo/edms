/**
 * Document Upload Modal Component
 * 
 * Replaces the standalone document upload form with a modal
 * integrated into the Document Management page.
 */

import React, { useState, useEffect } from 'react';
import apiService from '../../services/api.ts';
import { useAuth } from '../../contexts/AuthContext.tsx';

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (document: any) => void;
  onError?: (error: string) => void;
}

interface DocumentType {
  id: number;
  name: string;
  description?: string;
}

interface DocumentSource {
  id: number;
  name: string;
  description?: string;
}

interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
}

const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  onError
}) => {
  const { authenticated: isAuthenticated, user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    document_type_id: '',
    document_source_id: '',
    reviewer_id: '',
    // approver_id removed - assigned later per workflow specification
    file: null as File | null
  });

  // Reference data
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [documentSources, setDocumentSources] = useState<DocumentSource[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  // Load reference data when modal opens
  useEffect(() => {
    if (isOpen) {
      loadReferenceData();
    }
  }, [isOpen]);

  const loadReferenceData = async () => {
    try {
      setLoadingData(true);
      console.log('📊 Loading reference data for document upload...');

      // Load document types using apiService.get() like DocumentUploadNew
      const typesResponse = await apiService.get('/documents/types/');
      console.log('📋 Document types response:', typesResponse);
      setDocumentTypes(Array.isArray(typesResponse) ? typesResponse : typesResponse.results || []);
      
      // Load document sources using apiService.get() like DocumentUploadNew
      const sourcesResponse = await apiService.get('/documents/sources/');
      console.log('📁 Document sources response:', sourcesResponse);
      setDocumentSources(Array.isArray(sourcesResponse) ? sourcesResponse : sourcesResponse.results || []);
      
      // Load users using direct API call like DocumentUploadNew
      const usersResponse = await apiService.get('/auth/users/');
      console.log('👥 Users response:', usersResponse);
      setUsers(Array.isArray(usersResponse) ? usersResponse : usersResponse.results || []);

      console.log('✅ Reference data loaded successfully');
    } catch (error) {
      console.error('❌ Error loading reference data:', error);
      setError?.('Failed to load form data. Please refresh the page.');
    } finally {
      setLoadingData(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setFormData(prev => ({
      ...prev,
      file
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    console.log('🎯 handleSubmit called!', e);
    e.preventDefault();
    console.log('🎯 Event prevented, proceeding with validation...');
    
    if (!isAuthenticated) {
      console.error('❌ Not authenticated');
      onError?.('Authentication required. Please log in first.');
      return;
    }
    console.log('✅ Authentication check passed');

    if (!formData.file) {
      console.error('❌ No file selected');
      onError?.('Please select a file to upload.');
      return;
    }
    console.log('✅ File validation passed');

    try {
      setIsSubmitting(true);
      console.log('🚀 Submitting document upload...', formData);

      // Prepare data for API call
      // Author is automatically set to current logged-in user per EDMS specification
      if (!user) {
        throw new Error('User information not available. Please refresh and try again.');
      }
      
      const uploadData = {
        title: formData.title,
        description: formData.description,
        document_type_id: parseInt(formData.document_type_id),
        document_source_id: parseInt(formData.document_source_id),
        author: user?.id || user?.uuid || 1, // Use user ID, fallback to UUID or default to 1
        reviewer: parseInt(formData.reviewer_id),
        // approver: Not assigned at creation - per EDMS workflow line 11
        file: formData.file
      };

      console.log('📤 Upload data prepared:', uploadData);

      // Create document via API service
      const newDocument = await apiService.createDocument(uploadData);
      
      console.log('✅ Document uploaded successfully:', newDocument);
      onSuccess?.(newDocument);
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        document_type_id: '',
        document_source_id: '',
        reviewer_id: '',
        // approver_id removed - per workflow specification
        file: null
      });
      
      onClose();

    } catch (error: any) {
      console.error('❌ Document upload failed:', error);
      console.error('Full error object:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      
      let errorMessage = 'Failed to upload document';
      
      if (error.response?.data) {
        const data = error.response.data;
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.error) {
          errorMessage = data.error;
        } else {
          errorMessage = `Server error: ${JSON.stringify(data)}`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      console.error('Final error message shown to user:', errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Upload New Document</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
              disabled={isSubmitting}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <form id="upload-form" onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {loadingData ? (
            <div className="text-center py-8">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
              </div>
              <p className="text-sm text-gray-500 mt-4">Loading form data...</p>
            </div>
          ) : (
            <>
              {/* Title */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                  Document Title *
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  required
                  value={formData.title}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter document title"
                />
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows={3}
                  value={formData.description}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter document description"
                />
              </div>

              {/* Document Type */}
              <div>
                <label htmlFor="document_type_id" className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type *
                </label>
                <select
                  id="document_type_id"
                  name="document_type_id"
                  required
                  value={formData.document_type_id}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select document type</option>
                  {documentTypes.map(type => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Document Source */}
              <div>
                <label htmlFor="document_source_id" className="block text-sm font-medium text-gray-700 mb-1">
                  Document Source *
                </label>
                <select
                  id="document_source_id"
                  name="document_source_id"
                  required
                  value={formData.document_source_id}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select document source</option>
                  {documentSources.map(source => (
                    <option key={source.id} value={source.id}>
                      {source.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* File Upload */}
              <div>
                <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-1">
                  Document File *
                </label>
                <input
                  type="file"
                  id="file"
                  name="file"
                  required
                  onChange={handleFileChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Supported formats: PDF, DOC, DOCX, TXT, PNG, JPG, JPEG
                </p>
              </div>

              {/* Author Assignment (Auto-assigned to current user) */}
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">Document Author</h3>
                    <div className="mt-1 text-sm text-blue-700">
                      <p><strong>Auto-assigned:</strong> {user ? `${user.first_name} ${user.last_name} (${user.username})` : 'Current User'}</p>
                      <p className="text-xs mt-1">As per EDMS specification, the document author is automatically set to the user who uploads the document.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Workflow Assignment - Initial Review Step */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Initial Workflow Assignment</h3>
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-xs text-blue-700 mb-2">
                      📋 <strong>Workflow Step 1:</strong> Document will be routed for review after creation
                    </p>
                    <p className="text-xs text-blue-600">
                      Approver will be assigned later by author after review is completed (per EDMS workflow specification)
                    </p>
                  </div>
                </div>

                <div>
                  <label htmlFor="reviewer_id" className="block text-sm font-medium text-gray-700 mb-1">
                    Reviewer * 
                    <span className="text-xs text-gray-500">(Required for initial review step)</span>
                  </label>
                  <select
                    id="reviewer_id"
                    name="reviewer_id"
                    required
                    value={formData.reviewer_id}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select reviewer for initial review</option>
                    {users.map(user => (
                      <option key={user.id} value={user.id}>
                        {user.first_name} {user.last_name} ({user.username})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </>
          )}
        </form>

        {!loadingData && (
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => {
                console.log('🧪 Test button clicked!');
                console.log('🧪 Form data:', formData);
                console.log('🧪 Is authenticated:', isAuthenticated);
                console.log('🧪 User:', user);
              }}
              className="px-4 py-2 text-sm font-medium text-yellow-700 bg-yellow-100 border border-yellow-300 rounded-md hover:bg-yellow-200"
            >
              🧪 Test
            </button>
            <button
              type="submit"
              form="upload-form"
              disabled={isSubmitting || !formData.file || !formData.reviewer_id}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading...
                </span>
              ) : (
                'Upload Document'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentUploadModal;