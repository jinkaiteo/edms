/**
 * Document Create Modal Component (EDMS Step 1)
 * 
 * Implements EDMS Step 1: Author creates document placeholder and basic information
 * Per EDMS specification lines 4-5: Create document with DRAFT status (no reviewer selection)
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import apiService from '../../services/api.ts';

interface DocumentCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateSuccess: (document: any) => void;
}

interface DocumentType {
  id: number;
  name: string;
  description: string;
  code: string;
}

interface DocumentSource {
  id: number;
  name: string;
  source_type: string;
  description: string;
}

const DocumentCreateModal: React.FC<DocumentCreateModalProps> = ({
  isOpen,
  onClose,
  onCreateSuccess
}) => {
  const { authenticated } = useAuth();
  
  // Form state - Step 1 only (no reviewer/approver)
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [keywords, setKeywords] = useState('');
  const [documentType, setDocumentType] = useState('');
  const [documentSource, setDocumentSource] = useState('');
  const [priority, setPriority] = useState('normal');
  const [requiresTraining, setRequiresTraining] = useState(false);
  
  // File upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Data and state
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [documentSources, setDocumentSources] = useState<DocumentSource[]>([]);
  const [availableDocuments, setAvailableDocuments] = useState<any[]>([]);
  const [selectedDependencies, setSelectedDependencies] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load reference data
  useEffect(() => {
    if (isOpen && authenticated) {
      loadReferenceData();
    }
  }, [isOpen, authenticated]);

  const loadReferenceData = async () => {
    try {
      setLoading(true);
      
      const [typesResponse, sourcesResponse, documentsResponse] = await Promise.all([
        apiService.get('/documents/types/'),
        apiService.get('/documents/sources/'),
        apiService.get('/documents/documents/?status=EFFECTIVE')
      ]);
      
      setDocumentTypes(Array.isArray(typesResponse) ? typesResponse : typesResponse.results || []);
      setDocumentSources(Array.isArray(sourcesResponse) ? sourcesResponse : sourcesResponse.results || []);
      setAvailableDocuments(Array.isArray(documentsResponse) ? documentsResponse : documentsResponse.results || []);
      
      // Set defaults
      if (typesResponse && typesResponse.length > 0) {
        setDocumentType(typesResponse[0].id.toString());
      }
      if (sourcesResponse && sourcesResponse.length > 0) {
        setDocumentSource(sourcesResponse[0].id.toString());
      }
      
    } catch (error: any) {
      console.error('❌ Error loading reference data:', error);
      setError('Failed to load reference data');
    } finally {
      setLoading(false);
    }
  };

  // File handling
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  }, []);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelection(file);
    }
  };

  const handleFileSelection = (file: File) => {
    // Validate file
    const maxSize = 50 * 1024 * 1024; // 50MB
    const allowedTypes = ['.pdf', '.docx', '.doc', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

    if (file.size > maxSize) {
      setError('File size must be less than 50MB');
      return;
    }

    if (!allowedTypes.includes(fileExtension)) {
      setError('Only PDF, DOCX, DOC, and TXT files are allowed');
      return;
    }

    setSelectedFile(file);
    setError(null);
    
    // Auto-generate title from filename if not set
    if (!title) {
      const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, "");
      setTitle(nameWithoutExtension);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setError(null);
  };

  const handleCreateDocument = async () => {
    try {
      // Enhanced validation with debugging
      console.log('🔍 Debug - Form values before validation:', {
        title: JSON.stringify(title),
        description: JSON.stringify(description),
        titleLength: title.length,
        descriptionLength: description.length,
        documentType,
        documentSource
      });

      if (!title || !title.trim()) {
        setError('Title is required and cannot be empty');
        return;
      }
      if (!description || !description.trim()) {
        setError('Description is required and cannot be empty');
        return;
      }
      if (!documentType) {
        setError('Document type is required');
        return;
      }
      if (!documentSource) {
        setError('Document source is required');
        return;
      }

      setLoading(true);
      setError(null);

      // Create FormData for file upload with defensive values
      const formData = new FormData();
      const titleValue = title.trim();
      const descriptionValue = description.trim();
      
      formData.append('title', titleValue);
      formData.append('description', descriptionValue);
      formData.append('keywords', keywords.trim());
      formData.append('document_type', documentType);
      formData.append('document_source', documentSource);
      formData.append('priority', priority);
      formData.append('requires_training', requiresTraining.toString());
      formData.append('is_controlled', 'true'); // Add missing field
      
      // Debug selectedFile state
      console.log('🔍 Debug - selectedFile:', selectedFile);
      console.log('🔍 Debug - selectedFile type:', typeof selectedFile);
      console.log('🔍 Debug - selectedFile size:', selectedFile?.size);
      console.log('🔍 Debug - selectedFile instanceof File:', selectedFile instanceof File);
      
      // Only append file if it's actually selected and not empty
      if (selectedFile && selectedFile instanceof File && selectedFile.size > 0) {
        console.log('✅ Adding file to FormData:', selectedFile.name);
        formData.append('file', selectedFile);
      } else {
        console.log('❌ NOT adding file to FormData - selectedFile invalid or empty');
      }

      // Debug FormData contents
      console.log('📋 FormData contents:');
      for (let pair of formData.entries()) {
        console.log(`  ${pair[0]}: ${JSON.stringify(pair[1])}`);
      }

      // Add dependencies
      if (selectedDependencies.length > 0) {
        selectedDependencies.forEach((depId, index) => {
          formData.append(`dependencies[${index}]`, depId.toString());
        });
      }

      // Use direct fetch instead of apiService for FormData uploads
      const response = await fetch('http://localhost:8000/api/v1/documents/documents/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          // Don't set Content-Type - let browser set multipart boundary
        },
        body: formData,
      });

      if (response.ok) {
        const newDocument = await response.json();
        console.log('✅ Document created successfully:', newDocument);
        onCreateSuccess(newDocument);
        
        // Reset form
        setTitle('');
        setDescription('');
        setKeywords('');
        setDocumentType('');
        setDocumentSource('');
        setPriority('normal');
        setRequiresTraining(false);
        setSelectedFile(null);
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.log('❌ API Error Response:', errorData);
        throw new Error(JSON.stringify(errorData));
      }
      handleClose();

    } catch (error: any) {
      console.log('🔍 Debug - Full error object:', error);
      console.log('🔍 Debug - Error response:', error.response);
      console.log('🔍 Debug - Error response data:', error.response?.data);
      console.error('❌ Error creating document:', error);
      setError(`Failed to create document: ${JSON.stringify(error.response?.data || error.message || 'Unknown error')}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    // Reset form
    setTitle('');
    setDescription('');
    setKeywords('');
    setDocumentType('');
    setDocumentSource('');
    setPriority('normal');
    setRequiresTraining(false);
    setSelectedFile(null);
    setSelectedDependencies([]);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75">
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
          
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                📝 Create Document (Step 1)
              </h2>
              <button
                onClick={handleClose}
                className="text-gray-400 hover:text-gray-600"
                disabled={loading}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="px-6 py-3 bg-red-50 border-l-4 border-red-400">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Workflow Information */}
          <div className="px-6 py-4 bg-blue-50 border-l-4 border-blue-400">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">📋 EDMS Workflow Step 1</h3>
            <p className="text-blue-800 text-sm">
              <strong>Current Step:</strong> Create document placeholder with basic information
            </p>
            <p className="text-blue-700 text-xs mt-1">
              Per EDMS specification lines 4-5: Document status will be DRAFT. Reviewer selection happens in Step 2.
            </p>
          </div>

          <div className="px-6 py-6 space-y-6">
            
            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Document File <span className="text-xs text-gray-500">(Optional)</span>
              </label>
              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                  isDragOver
                    ? 'border-blue-400 bg-blue-50'
                    : selectedFile
                    ? 'border-green-400 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                {selectedFile ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-center space-x-2">
                      <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm font-medium text-green-700">{selectedFile.name}</span>
                    </div>
                    <p className="text-sm text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <button
                      type="button"
                      onClick={removeFile}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <svg className="w-8 h-8 text-gray-400 mx-auto" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <div className="space-y-1">
                      <p className="text-sm text-gray-600">
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="text-blue-600 hover:text-blue-500 font-medium"
                        >
                          Click to upload
                        </button>
                        {' '}or drag and drop
                      </p>
                      <p className="text-xs text-gray-500">PDF, DOCX, DOC, or TXT (max 50MB)</p>
                    </div>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileInputChange}
                  className="hidden"
                />
              </div>
            </div>

            {/* Basic Document Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                  Document Title *
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter document title"
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <select
                  id="priority"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  disabled={loading}
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe the document purpose and content"
                disabled={loading}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="documentType" className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type *
                </label>
                <select
                  id="documentType"
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  disabled={loading}
                >
                  <option value="">Select document type</option>
                  {documentTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name} ({type.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="documentSource" className="block text-sm font-medium text-gray-700 mb-1">
                  Document Source *
                </label>
                <select
                  id="documentSource"
                  value={documentSource}
                  onChange={(e) => setDocumentSource(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  disabled={loading}
                >
                  <option value="">Select document source</option>
                  {documentSources.map((source) => (
                    <option key={source.id} value={source.id}>
                      {source.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 mb-1">
                Keywords <span className="text-xs text-gray-500">(Optional)</span>
              </label>
              <input
                type="text"
                id="keywords"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter keywords separated by commas"
                disabled={loading}
              />
            </div>

            <div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="requiresTraining"
                  checked={requiresTraining}
                  onChange={(e) => setRequiresTraining(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  disabled={loading}
                />
                <label htmlFor="requiresTraining" className="ml-2 block text-sm text-gray-900">
                  Requires Training
                </label>
              </div>
            </div>

            {/* Document Dependencies */}
            {availableDocuments.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Document Dependencies <span className="text-xs text-gray-500">(Only approved and effective documents)</span>
                </label>
                <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-md p-2 space-y-1">
                  {availableDocuments.map((doc) => (
                    <label key={`doc-${doc.id}`} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedDependencies.includes(doc.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDependencies([...selectedDependencies, doc.id]);
                          } else {
                            setSelectedDependencies(selectedDependencies.filter(id => id !== doc.id));
                          }
                        }}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        disabled={loading}
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        {doc.document_number} - {doc.title}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
            <button
              onClick={handleClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateDocument}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Document'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentCreateModal;