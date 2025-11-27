import React, { useState, useRef, useCallback } from 'react';
import { DocumentCreateRequest, DocumentType } from '../../types/api';
import { apiService } from '../../services/api.ts';

interface DocumentUploadProps {
  onUploadSuccess?: (document: any) => void;
  onUploadError?: (error: string) => void;
  documentTypes?: DocumentType[];
  className?: string;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUploadSuccess,
  onUploadError,
  documentTypes = [],
  className = ''
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [formData, setFormData] = useState<Partial<DocumentCreateRequest>>({
    title: '',
    description: '',
    document_type_id: 1, // Use the only valid document type ID (Standard Operating Procedure)
    metadata: {},
    reviewer: 1, // Default to admin user
    approver: 1  // Default to admin user
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [availableUsers, setAvailableUsers] = useState<any[]>([]);
  const [reviewers, setReviewers] = useState<any[]>([]);
  const [approvers, setApprovers] = useState<any[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Use real document types that match backend IDs
  const defaultDocumentTypes: DocumentType[] = [
    { id: 1, name: 'Standard Operating Procedure', description: 'Standard Operating Procedures', prefix: 'SOP', is_active: true, workflow_required: true, retention_period: null, template: null },
    { id: 4, name: 'Policy', description: 'Company policies and guidelines', prefix: 'POL', is_active: true, workflow_required: true, retention_period: null, template: null },
    { id: 5, name: 'Manual', description: 'User manuals and handbooks', prefix: 'MAN', is_active: true, workflow_required: true, retention_period: null, template: null },
    { id: 6, name: 'Form', description: 'Forms and templates', prefix: 'FORM', is_active: true, workflow_required: true, retention_period: null, template: null }
  ];

  const availableDocumentTypes = documentTypes.length > 0 ? documentTypes : defaultDocumentTypes;

  // Load available users and filter by roles for reviewer/approver selection
  React.useEffect(() => {
    const loadUsers = async () => {
      try {
        const response = await apiService.get('/auth/users/');
        const users = response.results || [];
        setAvailableUsers(users);
        
        // Filter users based on their roles
        const filteredReviewers = users.filter(user => {
          if (!user.active_roles || user.active_roles.length === 0) return false;
          
          // Check if user has review permissions
          return user.active_roles.some(role => 
            role.permission_level === 'review' || 
            role.permission_level === 'admin' ||
            role.permission_level === 'write' || // Authors can review their own work
            role.name.toLowerCase().includes('review')
          );
        });
        
        const filteredApprovers = users.filter(user => {
          if (!user.active_roles || user.active_roles.length === 0) return false;
          
          // Check if user has approval permissions
          return user.active_roles.some(role => 
            role.permission_level === 'approve' ||
            role.permission_level === 'admin' ||
            role.name.toLowerCase().includes('approv')
          );
        });
        
        setReviewers(filteredReviewers);
        setApprovers(filteredApprovers);
        
        // Set default values to first available users with proper roles
        if (filteredReviewers.length > 0) {
          setFormData(prev => ({ ...prev, reviewer: filteredReviewers[0].id }));
        }
        if (filteredApprovers.length > 0) {
          setFormData(prev => ({ ...prev, approver: filteredApprovers[0].id }));
        }
        
        
      } catch (error) {
        console.error('Failed to load users:', error);
        // Fallback to admin user only
        const adminUser = { id: 1, username: 'admin', first_name: 'Admin', last_name: 'User', active_roles: [{ permission_level: 'admin' }] };
        setAvailableUsers([adminUser]);
        setReviewers([adminUser]);
        setApprovers([adminUser]);
      }
    };
    
    loadUsers();
  }, []);

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
      setErrors(prev => ({ ...prev, file: 'File size must be less than 50MB' }));
      return;
    }

    if (!allowedTypes.includes(fileExtension)) {
      setErrors(prev => ({ ...prev, file: 'Only PDF, DOCX, DOC, and TXT files are allowed' }));
      return;
    }

    setSelectedFile(file);
    setErrors(prev => ({ ...prev, file: '' }));
    
    // Auto-generate title from filename if not set
    if (!formData.title) {
      const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, "");
      setFormData(prev => ({ ...prev, title: nameWithoutExtension }));
    }
  };

  const handleInputChange = (field: keyof DocumentCreateRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title?.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.description?.trim()) {
      newErrors.description = 'Description is required';
    }

    if (!selectedFile) {
      newErrors.file = 'Please select a file to upload';
    }

    // Validate reviewer and approver for all documents
    if (!formData.reviewer) {
      newErrors.reviewer = 'Reviewer is required';
    }
    if (!formData.approver) {
      newErrors.approver = 'Approver is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsUploading(true);

    try {
      const uploadData: DocumentCreateRequest = {
        title: formData.title!,
        description: formData.description!,
        document_type_id: formData.document_type_id!,
        metadata: formData.metadata || {},
        file: selectedFile!,
        reviewer: formData.reviewer!,
        approver: formData.approver!
      };

      const result = await apiService.createDocument(uploadData);
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        document_type_id: 1,
        metadata: {},
        reviewer: 1,
        approver: 1
      });
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      onUploadSuccess?.(result);
    } catch (error: any) {
      const errorMessage = error.error?.message || 'Upload failed. Please try again.';
      setErrors({ general: errorMessage });
      onUploadError?.(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setErrors(prev => ({ ...prev, file: '' }));
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Document</h3>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Drag and drop zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
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
                  <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                <svg className="w-12 h-12 text-gray-400 mx-auto" stroke="currentColor" fill="none" viewBox="0 0 48 48">
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
          {errors.file && <p className="text-sm text-red-600">{errors.file}</p>}

          {/* Form fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                Document Title *
              </label>
              <input
                type="text"
                id="title"
                value={formData.title || ''}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter document title"
              />
              {errors.title && <p className="text-sm text-red-600 mt-1">{errors.title}</p>}
            </div>

            <div>
              <label htmlFor="document_type" className="block text-sm font-medium text-gray-700 mb-1">
                Document Type *
              </label>
              <select
                id="document_type"
                value={formData.document_type_id || 1}
                onChange={(e) => {
                  handleInputChange('document_type_id', parseInt(e.target.value));
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                {availableDocumentTypes.map(type => (
                  <option key={type.id} value={type.id}>
                    {type.name} - {type.description}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <textarea
              id="description"
              value={formData.description || ''}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Describe the document purpose and content"
            />
            {errors.description && <p className="text-sm text-red-600 mt-1">{errors.description}</p>}
          </div>

          {/* Reviewer and Approver fields for all documents */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="reviewer" className="block text-sm font-medium text-gray-700 mb-1">
                Reviewer * <span className="text-xs text-gray-500">(Users with review permissions)</span>
              </label>
              <select
                id="reviewer"
                value={formData.reviewer || (reviewers[0]?.id || 1)}
                onChange={(e) => handleInputChange('reviewer', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                required
              >
                {reviewers.length > 0 ? (
                  reviewers.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.first_name} {user.last_name} ({user.username})
                      {user.active_roles?.some(role => role.permission_level === 'admin') && ' - Admin'}
                    </option>
                  ))
                ) : (
                  <option value="">No users with review permissions available</option>
                )}
              </select>
              {errors.reviewer && <p className="text-sm text-red-600 mt-1">{errors.reviewer}</p>}
            </div>

            <div>
              <label htmlFor="approver" className="block text-sm font-medium text-gray-700 mb-1">
                Approver * <span className="text-xs text-gray-500">(Users with approval permissions)</span>
              </label>
              <select
                id="approver"
                value={formData.approver || (approvers[0]?.id || 1)}
                onChange={(e) => handleInputChange('approver', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                required
              >
                {approvers.length > 0 ? (
                  approvers.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.first_name} {user.last_name} ({user.username})
                      {user.active_roles?.some(role => role.permission_level === 'admin') && ' - Admin'}
                    </option>
                  ))
                ) : (
                  <option value="">No users with approval permissions available</option>
                )}
              </select>
              {errors.approver && <p className="text-sm text-red-600 mt-1">{errors.approver}</p>}
            </div>
          </div>

          {/* Error display */}
          {errors.general && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{errors.general}</p>
            </div>
          )}

          {/* Submit button */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => {
                setFormData({ 
                  title: '', 
                  description: '', 
                  document_type_id: 1,  // Force reset to valid ID
                  metadata: {}, 
                  reviewer: reviewers[0]?.id || 1, 
                  approver: approvers[0]?.id || 1 
                });
                setSelectedFile(null);
                setErrors({});
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              disabled={isUploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? (
                <div className="flex items-center space-x-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Uploading...</span>
                </div>
              ) : (
                'Upload Document'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DocumentUpload;