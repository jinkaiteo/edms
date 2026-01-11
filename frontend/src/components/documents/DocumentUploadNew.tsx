import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api.ts';

// Backend-compliant interfaces
interface DocumentType {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
}

interface DocumentSource {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
}

interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
}

interface DocumentCreateRequest {
  title: string;
  description?: string;
  keywords?: string;
  document_type: number;
  document_source: number;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  reviewer?: number;
  approver?: number;
  file_name?: string;
  file_path?: string;
  mime_type?: string;
  effective_date?: string;
  reason_for_change?: string;
  requires_training?: boolean;
  is_controlled?: boolean;
  file?: File;
}

const DocumentUploadNew: React.FC = () => {
  
  // State for form data
  const [formData, setFormData] = useState<DocumentCreateRequest>({
    title: '',
    description: '',
    keywords: '',
    document_type: 0,
    document_source: 0,
    priority: 'normal',
    reviewer: 0,
    approver: 0,
    reason_for_change: '',
    requires_training: false,
    is_controlled: true,
  });
  
  // State for dropdown data
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [documentSources, setDocumentSources] = useState<DocumentSource[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // State for UI
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Load reference data on component mount
  useEffect(() => {
    loadReferenceData();
  }, []);
  
  const loadReferenceData = async () => {
    try {
      
      // Load document types
      const typesResponse = await apiService.get('/document-types/');
      setDocumentTypes(Array.isArray(typesResponse) ? typesResponse : typesResponse.results || []);
      
      // Load document sources
      const sourcesResponse = await apiService.get('/document-sources/');
      setDocumentSources(Array.isArray(sourcesResponse) ? sourcesResponse : sourcesResponse.results || []);
      
      // Load users for reviewer/approver assignment
      const usersResponse = await apiService.get('/auth/users/');
      setUsers(Array.isArray(usersResponse) ? usersResponse : usersResponse.results || []);
      
      
    } catch (error) {
      console.error('❌ Failed to load reference data:', error);
      setError('Failed to load form data. Please refresh the page.');
    }
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : 
              type === 'number' ? parseInt(value) || 0 : value
    }));
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setFormData(prev => ({
        ...prev,
        file_name: file.name,
        mime_type: file.type
      }));
    }
  };
  
  const validateForm = (): string[] => {
    const errors: string[] = [];
    
    if (!formData.title.trim()) {
      errors.push('Title is required');
    }
    
    if (!formData.document_type || formData.document_type === 0) {
      errors.push('Document type is required');
    }
    
    if (!formData.document_source || formData.document_source === 0) {
      errors.push('Document source is required');
    }
    
    return errors;
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    // Validate form
    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
      setError(`Validation errors: ${validationErrors.join(', ')}`);
      return;
    }
    
    setIsLoading(true);
    
    try {
      
      // Create FormData for file upload
      const formDataToSend = new FormData();
      
      // Add required fields
      formDataToSend.append('title', formData.title);
      formDataToSend.append('document_type', formData.document_type.toString());
      formDataToSend.append('document_source', formData.document_source.toString());
      
      // Add reviewer and approver (required for SOP document type)
      if (formData.reviewer && formData.reviewer > 0) {
        formDataToSend.append('reviewer', formData.reviewer.toString());
      } else {
        // Default to reviewer user if none selected
        const defaultReviewer = users.find(u => u.username === 'reviewer');
        if (defaultReviewer) {
          formDataToSend.append('reviewer', defaultReviewer.id.toString());
        }
      }
      
      if (formData.approver && formData.approver > 0) {
        formDataToSend.append('approver', formData.approver.toString());
      } else {
        // Default to approver user if none selected
        const defaultApprover = users.find(u => u.username === 'approver');
        if (defaultApprover) {
          formDataToSend.append('approver', defaultApprover.id.toString());
        }
      }
      
      // Add optional fields only if they have values
      if (formData.description?.trim()) {
        formDataToSend.append('description', formData.description);
      }
      
      if (formData.keywords?.trim()) {
        formDataToSend.append('keywords', formData.keywords);
      }
      
      if (formData.priority && formData.priority !== 'normal') {
        formDataToSend.append('priority', formData.priority);
      }
      
      // Reviewer and approver already handled above in required section
      
      if (formData.reason_for_change?.trim()) {
        formDataToSend.append('reason_for_change', formData.reason_for_change);
      }
      
      if (formData.effective_date) {
        formDataToSend.append('effective_date', formData.effective_date);
      }
      
      formDataToSend.append('requires_training', formData.requires_training?.toString() || 'false');
      formDataToSend.append('is_controlled', formData.is_controlled?.toString() || 'true');
      
      // Add file if selected
      if (selectedFile) {
        formDataToSend.append('file', selectedFile);
        formDataToSend.append('file_name', selectedFile.name);
        formDataToSend.append('mime_type', selectedFile.type);
      }
      
      
      // Send to backend using direct fetch for FormData
      let token = localStorage.getItem('accessToken') || localStorage.getItem('token') || localStorage.getItem('access_token') || localStorage.getItem('authToken');
      
      if (!token) {
        // Try to get token from context or other storage methods
        
        // Check all localStorage items for potential tokens
        const allItems = {};
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key) {
            allItems[key] = localStorage.getItem(key)?.substring(0, 20) + '...';
          }
        }
        
        throw new Error('Authentication token not found. Please log in to access document upload.');
      }
      
      
      const response = await fetch('/api/v1/documents/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          // Don't set Content-Type - let browser set it with boundary for FormData
        },
        body: formDataToSend
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      const successMessage = `Document created successfully: ${result.document_number || 'New Document'}`;
      setSuccess(successMessage);
      
      // Emit event for modal integration
      const documentCreatedEvent = new CustomEvent('documentCreated', {
        detail: result
      });
      window.dispatchEvent(documentCreatedEvent);
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        keywords: '',
        document_type: 0,
        document_source: 0,
        priority: 'normal',
        reviewer: 0,
        approver: 0,
        reason_for_change: '',
        requires_training: false,
        is_controlled: true,
      });
      setSelectedFile(null);
      
    } catch (error: any) {
      console.error('❌ Document creation failed:', error);
      setError(`Failed to create document: ${error.message || 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="max-w-4xl mx-auto p-6 bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Document</h2>
      
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700">{error}</p>
        </div>
      )}
      
      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <p className="text-green-700">{success}</p>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Document Title *
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter document title"
            />
          </div>
          
          <div>
            <label htmlFor="document_type" className="block text-sm font-medium text-gray-700 mb-1">
              Document Type *
            </label>
            <select
              id="document_type"
              name="document_type"
              value={formData.document_type}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Select Document Type</option>
              {documentTypes.map(type => (
                <option key={type.id} value={type.id}>
                  {type.name} ({type.code})
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* Document Source and Priority */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="document_source" className="block text-sm font-medium text-gray-700 mb-1">
              Document Source *
            </label>
            <select
              id="document_source"
              name="document_source"
              value={formData.document_source}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Select Document Source</option>
              {documentSources.map(source => (
                <option key={source.id} value={source.id}>
                  {source.name}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Choose the source type that best describes how this document was created
            </p>
          </div>
          
          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <select
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
        </div>
        
        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter document description"
          />
        </div>
        
        {/* Keywords */}
        <div>
          <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 mb-1">
            Keywords (comma-separated)
          </label>
          <input
            type="text"
            id="keywords"
            name="keywords"
            value={formData.keywords}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="keyword1, keyword2, keyword3"
          />
        </div>
        
        {/* Reviewer and Approver */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="reviewer" className="block text-sm font-medium text-gray-700 mb-1">
              Reviewer
            </label>
            <select
              id="reviewer"
              name="reviewer"
              value={formData.reviewer}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Select Reviewer</option>
              {users.filter(user => user.is_active).map(user => (
                <option key={user.id} value={user.id}>
                  {user.first_name} {user.last_name} ({user.username})
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label htmlFor="approver" className="block text-sm font-medium text-gray-700 mb-1">
              Approver
            </label>
            <select
              id="approver"
              name="approver"
              value={formData.approver}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Select Approver</option>
              {users.filter(user => user.is_active).map(user => (
                <option key={user.id} value={user.id}>
                  {user.first_name} {user.last_name} ({user.username})
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* File Upload */}
        <div>
          <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-1">
            Document File
          </label>
          <input
            type="file"
            id="file"
            name="file"
            onChange={handleFileChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            accept=".pdf,.doc,.docx,.txt,.md"
          />
          {selectedFile && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>
        
        {/* Additional Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="requires_training"
              name="requires_training"
              checked={formData.requires_training}
              onChange={handleInputChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="requires_training" className="ml-2 block text-sm text-gray-700">
              Requires Training
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_controlled"
              name="is_controlled"
              checked={formData.is_controlled}
              onChange={handleInputChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_controlled" className="ml-2 block text-sm text-gray-700">
              Controlled Document
            </label>
          </div>
        </div>
        
        {/* Reason for Change */}
        <div>
          <label htmlFor="reason_for_change" className="block text-sm font-medium text-gray-700 mb-1">
            Reason for Change
          </label>
          <input
            type="text"
            id="reason_for_change"
            name="reason_for_change"
            value={formData.reason_for_change}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter reason for creating this document"
          />
        </div>
        
        {/* Submit Button */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => {
              setFormData({
                title: '',
                description: '',
                keywords: '',
                document_type: 0,
                document_source: 0,
                priority: 'normal',
                reviewer: 0,
                approver: 0,
                reason_for_change: '',
                requires_training: false,
                is_controlled: true,
              });
              setSelectedFile(null);
              setError(null);
              setSuccess(null);
            }}
            className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          >
            Reset
          </button>
          
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Creating...' : 'Create Document'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default DocumentUploadNew;