/**
 * Document Create Modal Component (EDMS Step 1)
 * 
 * Implements EDMS Step 1: Author creates document placeholder and basic information
 * Per EDMS specification lines 4-5: Create document with DRAFT status (no reviewer selection)
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import apiService from '../../services/api.ts';
import DocumentSelector from './DocumentSelector.tsx';

interface DocumentCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateSuccess: (document: any) => void;
  editDocument?: Document | null; // Document to edit (null for create mode)
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
  onCreateSuccess,
  editDocument = null
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
  
  // Draft-only editing controls
  const [documentTypeChanged, setDocumentTypeChanged] = useState(false);
  const [showNumberChangeWarning, setShowNumberChangeWarning] = useState(false);
  
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
  const [dependencies, setDependencies] = useState<Array<{
    id: number;
    document_number: string;
    title: string;
    dependency_type: string;
    is_critical: boolean;
  }>>([]);

  // Dependency types for the select dropdown
  const dependencyTypes = [
    { value: 'references', label: 'References' },
    { value: 'template', label: 'Template' },
    { value: 'supersedes', label: 'Supersedes' },
    { value: 'incorporates', label: 'Incorporates' },
    { value: 'supports', label: 'Supports' },
    { value: 'implements', label: 'Implements' }
  ];

  // Load reference data and populate form for edit mode
  useEffect(() => {
    if (isOpen && authenticated) {
      loadReferenceData();
    }
  }, [isOpen, authenticated]);

  // Separate effect for form population after reference data is loaded
  useEffect(() => {
    if (isOpen && editDocument && documentTypes.length > 0 && documentSources.length > 0) {
      console.log('🔍 Populating edit form with document:', editDocument);
      console.log('🔍 Available document properties:', Object.keys(editDocument));
      console.log('🔍 Full document object for inspection:', editDocument);
      
      setTitle(editDocument.title || '');
      setDescription(editDocument.description || '');
      setKeywords(editDocument.keywords || '');
      
      // Debug: Log each field access attempt
      console.log('🔍 Field access attempts:');
      console.log('  title:', editDocument.title);
      console.log('  description:', editDocument.description);
      console.log('  keywords:', editDocument.keywords);
      console.log('  priority:', editDocument.priority);
      console.log('  requires_training:', editDocument.requires_training);
      console.log('  document_type:', editDocument.document_type);
      console.log('  document_type_id:', editDocument.document_type_id);
      console.log('  document_source:', editDocument.document_source);
      console.log('  document_source_id:', editDocument.document_source_id);
      
      // Handle document_type - check all possible property names
      let documentTypeId = '';
      if (editDocument.document_type) {
        if (typeof editDocument.document_type === 'object' && editDocument.document_type.id) {
          documentTypeId = editDocument.document_type.id.toString();
        } else {
          documentTypeId = editDocument.document_type.toString();
        }
      } else if (editDocument.document_type_id) {
        documentTypeId = editDocument.document_type_id.toString();
      }
      setDocumentType(documentTypeId);
      
      // Handle document_source - check all possible property names
      let documentSourceId = '';
      if (editDocument.document_source) {
        if (typeof editDocument.document_source === 'object' && editDocument.document_source.id) {
          documentSourceId = editDocument.document_source.id.toString();
        } else {
          documentSourceId = editDocument.document_source.toString();
        }
      } else if (editDocument.document_source_id) {
        documentSourceId = editDocument.document_source_id.toString();
      }
      setDocumentSource(documentSourceId);
      
      setPriority(editDocument.priority || 'normal');
      setRequiresTraining(editDocument.requires_training || false);
      
      // Populate dependencies if available
      if (editDocument.dependencies && Array.isArray(editDocument.dependencies)) {
        console.log('🔍 Raw editDocument.dependencies:', editDocument.dependencies);
        
        // Convert backend dependencies to local dependencies format
        const mappedDependencies = editDocument.dependencies.map(dep => {
          let docId, dependencyType = 'references', isCritical = false;
          
          // The backend returns DocumentDependency objects with 'depends_on' field
          if (typeof dep === 'object' && dep.depends_on) {
            docId = dep.depends_on; // This is the document ID we want
            dependencyType = dep.dependency_type || 'references';
            isCritical = dep.is_critical || false;
          } else if (typeof dep === 'object' && dep.id) {
            docId = dep.id; // Fallback for different object structure
          } else {
            docId = dep; // Fallback for primitive values
          }

          // Find the document details from available documents
          const docDetails = availableDocuments.find(doc => doc.id === docId);
          
          return {
            id: docId,
            document_number: docDetails?.document_number || 'Unknown',
            title: docDetails?.title || 'Unknown Document',
            dependency_type: dependencyType,
            is_critical: isCritical
          };
        }).filter(dep => 
          // Only include dependencies where we found the document details
          availableDocuments.some(doc => doc.id === dep.id)
        );
        
        console.log('🔍 Mapped dependencies:', mappedDependencies);
        
        // Set both dependencies and selectedDependencies
        setDependencies(mappedDependencies);
        setSelectedDependencies(mappedDependencies.map(dep => dep.id));
        console.log('🔍 Dependencies populated:', mappedDependencies.length, 'items');
      } else {
        // Clear dependencies if none exist
        setDependencies([]);
        setSelectedDependencies([]);
        console.log('🔍 No dependencies to populate, cleared arrays');
      }
      
      // Note: File information is available but not pre-populated for security reasons
      // Users need to re-upload files when editing
      if (editDocument.file_name && editDocument.file_path) {
        console.log('🔍 Document has existing file:', {
          fileName: editDocument.file_name,
          filePath: editDocument.file_path,
          fileSize: editDocument.file_size
        });
        // Could show file info but not pre-populate the file input for security
      }
      
      // Reset change tracking for fresh edit session
      setDocumentTypeChanged(false);
      setShowNumberChangeWarning(false);
      
      console.log('✅ Form populated with values:', {
        title: editDocument.title,
        description: editDocument.description,
        keywords: editDocument.keywords,
        documentType: typeof editDocument.document_type === 'object' ? editDocument.document_type.id : editDocument.document_type,
        documentSource: typeof editDocument.document_source === 'object' ? editDocument.document_source.id : editDocument.document_source,
        priority: editDocument.priority,
        requiresTraining: editDocument.requires_training,
        dependencies: editDocument.dependencies?.length || 0,
        hasExistingFile: !!(editDocument.file_name && editDocument.file_path)
      });
    }
  }, [isOpen, editDocument, documentTypes.length, documentSources.length]);

  const loadReferenceData = async () => {
    try {
      setLoading(true);
      
      const [typesResponse, sourcesResponse, documentsResponse] = await Promise.all([
        apiService.get('/documents/types/'),
        apiService.get('/documents/sources/'),
        apiService.get('/documents/documents/?status=APPROVED_AND_EFFECTIVE')
      ]);
      
      setDocumentTypes(Array.isArray(typesResponse) ? typesResponse : typesResponse.results || []);
      setDocumentSources(Array.isArray(sourcesResponse) ? sourcesResponse : sourcesResponse.results || []);
      setAvailableDocuments(Array.isArray(documentsResponse) ? documentsResponse : documentsResponse.results || []);
      
      // Set defaults ONLY if not editing (to avoid overriding populated values)
      if (!editDocument) {
        if (typesResponse && typesResponse.length > 0) {
          setDocumentType(typesResponse[0].id.toString());
        }
        if (sourcesResponse && sourcesResponse.length > 0) {
          setDocumentSource(sourcesResponse[0].id.toString());
        }
      }
      
    } catch (error: any) {
      console.error('❌ Error loading reference data:', error);
      setError('Failed to load reference data');
    } finally {
      setLoading(false);
    }
  };

  // Dependency management functions
  const handleDependencyAdd = (document: any) => {
    console.log('🔍 Adding dependency:', document);
    
    // Check if already added
    if (dependencies.some(dep => dep.id === document.id)) {
      console.log('❌ Dependency already exists:', document.id);
      return;
    }

    const newDependency = {
      id: document.id,
      document_number: document.document_number,
      title: document.title,
      dependency_type: 'references', // Default type
      is_critical: false
    };

    setDependencies(prev => [...prev, newDependency]);
    setSelectedDependencies(prev => [...prev, document.id]);
    console.log('✅ Dependency added:', newDependency);
  };

  const removeDependency = (dependencyId: number) => {
    console.log('🗑️ Removing dependency:', dependencyId);
    setDependencies(prev => prev.filter(dep => dep.id !== dependencyId));
    setSelectedDependencies(prev => prev.filter(id => id !== dependencyId));
  };

  const updateDependencyType = (dependencyId: number, newType: string) => {
    console.log('🔄 Updating dependency type:', dependencyId, 'to', newType);
    setDependencies(prev => 
      prev.map(dep => 
        dep.id === dependencyId 
          ? { ...dep, dependency_type: newType }
          : dep
      )
    );
  };

  const toggleDependencyCritical = (dependencyId: number) => {
    console.log('🔄 Toggling dependency critical status:', dependencyId);
    setDependencies(prev => 
      prev.map(dep => 
        dep.id === dependencyId 
          ? { ...dep, is_critical: !dep.is_critical }
          : dep
      )
    );
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

  // Check if core fields can be edited (only in DRAFT status)
  const canEditCoreFields = editDocument ? editDocument.status === 'DRAFT' : true;
  
  // Handle document type changes with warning
  const handleDocumentTypeChange = (newTypeId: string) => {
    // Get original document type ID for comparison
    let originalTypeId = '';
    if (editDocument && editDocument.document_type) {
      if (typeof editDocument.document_type === 'object' && editDocument.document_type.id) {
        originalTypeId = editDocument.document_type.id.toString();
      } else {
        originalTypeId = editDocument.document_type.toString();
      }
    }
    
    if (editDocument && originalTypeId && originalTypeId !== newTypeId) {
      setDocumentTypeChanged(true);
      setShowNumberChangeWarning(true);
    } else {
      setDocumentTypeChanged(false);
      setShowNumberChangeWarning(false);
    }
    setDocumentType(newTypeId);
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

      // Add dependencies BEFORE debugging FormData
      console.log('🔍 Debug - dependencies:', dependencies);
      console.log('🔍 Debug - dependencies length:', dependencies.length);
      console.log('🔍 Debug - selectedDependencies:', selectedDependencies);
      
      if (dependencies.length > 0) {
        console.log('✅ Adding dependencies to FormData...');
        dependencies.forEach((dep, index) => {
          console.log(`  Adding dependency ${index}: ${dep.id}`);
          // Backend expects simple array of dependency IDs
          formData.append(`dependencies[${index}]`, dep.id.toString());
        });
      } else {
        console.log('❌ No dependencies to add (dependencies array is empty)');
      }

      // Debug FormData contents
      console.log('📋 FormData contents:');
      for (let pair of formData.entries()) {
        console.log(`  ${pair[0]}: ${JSON.stringify(pair[1])}`);
      }

      // Include document type change flag for backend processing
      if (editDocument && documentTypeChanged) {
        formData.append('document_type_changed', 'true');
        
        // Get original document type ID
        let originalTypeId = '';
        if (editDocument.document_type) {
          if (typeof editDocument.document_type === 'object' && editDocument.document_type.id) {
            originalTypeId = editDocument.document_type.id.toString();
          } else {
            originalTypeId = editDocument.document_type.toString();
          }
        }
        formData.append('old_document_type', originalTypeId);
      }

      // Use direct fetch for FormData uploads (create or update)
      const apiUrl = editDocument 
        ? `http://localhost:8000/api/v1/documents/documents/${editDocument.uuid}/`
        : 'http://localhost:8000/api/v1/documents/documents/';
      
      const method = editDocument ? 'PATCH' : 'POST';
      
      // Get fresh token to avoid expiration issues
      const currentToken = localStorage.getItem('accessToken');
      console.log('🔑 Using token for request:', currentToken ? 'Token available' : 'No token found');
      
      const response = await fetch(apiUrl, {
        method: method,
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          // Don't set Content-Type - let browser set multipart boundary
        },
        body: formData,
      });
      
      console.log(`📡 ${method} request to:`, apiUrl);
      console.log('📡 Response status:', response.status);
      console.log('📡 Response ok:', response.ok);

      if (response.ok) {
        const updatedDocument = await response.json();
        console.log(`✅ Document ${editDocument ? 'updated' : 'created'} successfully:`, updatedDocument);
        
        // Show success message
        console.log('📋 Changes applied:', {
          title: titleValue,
          description: descriptionValue,
          keywords: keywords.trim(),
          priority: priority,
          requiresTraining: requiresTraining,
          documentType: documentType,
          documentSource: documentSource
        });
        
        onCreateSuccess(updatedDocument);
        
        // Reset form only for create mode, not edit mode
        if (!editDocument) {
          setTitle('');
          setDescription('');
          setKeywords('');
          setDocumentType('');
          setDocumentSource('');
          setPriority('normal');
          setRequiresTraining(false);
          setSelectedFile(null);
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.log('❌ API Error Response:', errorData);
        console.log('❌ Response status:', response.status);
        console.log('❌ Response headers:', response.headers);
        throw new Error(`HTTP ${response.status}: ${JSON.stringify(errorData)}`);
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
    // Reset form with debugging
    console.log('🔍 Form reset - before clearing dependencies:', dependencies);
    setTitle('');
    setDescription('');
    setKeywords('');
    setDocumentType('');
    setDocumentSource('');
    setPriority('normal');
    setRequiresTraining(false);
    setSelectedFile(null);
    setSelectedDependencies([]);
    setDependencies([]);
    console.log('🔍 Form reset - after clearing dependencies: []');
    setError(null);
    setDocumentTypeChanged(false);
    setShowNumberChangeWarning(false);
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
                {editDocument ? '✏️ Edit Document' : '📝 Create Document (Step 1)'}
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
            <h3 className="text-sm font-semibold text-blue-900 mb-2">
              {editDocument ? '✏️ Edit Document Mode' : '📋 EDMS Workflow Step 1'}
            </h3>
            <p className="text-blue-800 text-sm">
              {editDocument 
                ? `Editing: ${editDocument.document_number} - ${editDocument.title}`
                : 'Create document placeholder with basic information'
              }
            </p>
            {!editDocument && (
              <p className="text-blue-700 text-xs mt-1">
                Per EDMS specification lines 4-5: Document status will be DRAFT. Reviewer selection happens in Step 2.
              </p>
            )}
          </div>

          <div className="px-6 py-6 space-y-6">
            
            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Document File <span className="text-xs text-gray-500">(Optional)</span>
                {editDocument && editDocument.file_name && (
                  <span className="text-xs text-blue-600 ml-2">
                    Current: {editDocument.file_name}
                  </span>
                )}
              </label>
              
              {/* Show existing file information */}
              {editDocument && editDocument.file_name && editDocument.file_path && !selectedFile && (
                <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <div>
                        <p className="text-sm font-medium text-blue-800">{editDocument.file_name}</p>
                        {editDocument.file_size && (
                          <p className="text-xs text-blue-600">
                            {(editDocument.file_size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-blue-600">Upload new file to replace</p>
                  </div>
                </div>
              )}
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

            {/* Document Dependencies */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Document Dependencies
                </label>
                <span className="text-xs text-gray-500">
                  {dependencies.length} selected
                </span>
              </div>
              
              <div className="space-y-4">
                {/* Search and Add Dependencies */}
                <div>
                  <DocumentSelector 
                    onSelect={handleDependencyAdd}
                    placeholder="Search for documents to add as dependencies..."
                    excludeIds={dependencies.map(dep => dep.id)}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Search by document number, title, or type to add dependencies
                  </p>
                </div>
                
                {/* Selected Dependencies List */}
                {dependencies.length > 0 && (
                  <div className="border rounded-lg p-4 bg-gray-50">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">
                      Selected Dependencies ({dependencies.length})
                    </h4>
                    <div className="space-y-3">
                      {dependencies.map((dep) => (
                        <div 
                          key={dep.id} 
                          className="flex items-start justify-between p-3 bg-white border rounded-lg"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              <p className="text-sm font-medium text-gray-900">
                                {dep.document_number}
                              </p>
                              {dep.is_critical && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                  Critical
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mb-2">
                              {dep.title}
                            </p>
                            
                            {/* Dependency Type Selection */}
                            <div className="flex items-center space-x-3">
                              <select
                                value={dep.dependency_type}
                                onChange={(e) => updateDependencyType(dep.id, e.target.value)}
                                className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-blue-500 focus:border-blue-500"
                              >
                                {dependencyTypes.map((type) => (
                                  <option key={type.value} value={type.value}>
                                    {type.label}
                                  </option>
                                ))}
                              </select>
                              
                              {/* Critical Dependency Toggle */}
                              <label className="flex items-center space-x-1">
                                <input
                                  type="checkbox"
                                  checked={dep.is_critical}
                                  onChange={() => toggleDependencyCritical(dep.id)}
                                  className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                                />
                                <span className="text-xs text-gray-600">Critical</span>
                              </label>
                            </div>
                          </div>
                          
                          {/* Remove Button */}
                          <button
                            type="button"
                            onClick={() => removeDependency(dep.id)}
                            className="ml-3 text-red-600 hover:text-red-800 text-sm"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                    
                    <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-xs text-blue-800">
                        <strong>Dependency Types:</strong> References (cites content), Template (based on), 
                        Supersedes (replaces), Incorporates (includes content), Supports (supporting doc), 
                        Implements (implements requirements). Critical dependencies require notification when changed.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Basic Document Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                  Document Title *
                  {!canEditCoreFields && (
                    <span className="text-xs text-amber-600 ml-1">(Read-only after DRAFT)</span>
                  )}
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                    !canEditCoreFields ? 'bg-gray-100 cursor-not-allowed' : ''
                  }`}
                  placeholder="Enter document title"
                  disabled={loading || !canEditCoreFields}
                />
                {!canEditCoreFields && editDocument && (
                  <p className="text-sm text-amber-600 mt-1">
                    ⚠️ Title cannot be changed after submitting for review. Contact administrator if changes needed.
                  </p>
                )}
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
                  {!canEditCoreFields && (
                    <span className="text-xs text-amber-600 ml-1">(Read-only after DRAFT)</span>
                  )}
                </label>
                <select
                  id="documentType"
                  value={documentType}
                  onChange={(e) => handleDocumentTypeChange(e.target.value)}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 ${
                    !canEditCoreFields ? 'bg-gray-100 cursor-not-allowed' : ''
                  }`}
                  disabled={loading || !canEditCoreFields}
                >
                  <option value="">Select document type</option>
                  {documentTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name} ({type.code})
                    </option>
                  ))}
                </select>
                
                {/* Document Type Change Warning */}
                {showNumberChangeWarning && editDocument && (
                  <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <div className="flex">
                      <svg className="w-5 h-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <div>
                        <h4 className="text-sm font-medium text-yellow-800">⚠️ Document Number Will Change</h4>
                        <p className="text-sm text-yellow-700 mt-1">
                          Changing document type will generate a new document number.
                        </p>
                        <p className="text-xs text-yellow-600 mt-1">
                          <strong>Current:</strong> {editDocument.document_number} → <strong>New:</strong> [Generated automatically on save]
                        </p>
                        <p className="text-xs text-yellow-600 mt-1">
                          This change will be logged in the audit trail for compliance.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                
                {!canEditCoreFields && editDocument && (
                  <p className="text-sm text-amber-600 mt-1">
                    ⚠️ Document type cannot be changed after submitting for review. Contact administrator if changes needed.
                  </p>
                )}
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
              {loading 
                ? (editDocument ? 'Updating...' : 'Creating...') 
                : (editDocument ? 'Update Document' : 'Create Document')
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentCreateModal;