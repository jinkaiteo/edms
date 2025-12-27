import { Document, DocumentType, SearchFilters } from '../../types/api';

export interface DocumentUploadProps {
  onUploadSuccess?: (document: Document) => void;
  onUploadError?: (error: string) => void;
  documentTypes?: DocumentType[];
  className?: string;
}

export interface DocumentListProps {
  onDocumentSelect?: (document: Document) => void;
  onDocumentEdit?: (document: Document) => void;
  onDocumentDelete?: (document: Document) => void;
  filters?: SearchFilters & { search?: string };
  className?: string;
}

export interface DocumentViewerProps {
  document: Document | null;
  onClose?: () => void;
  onEdit?: (document: Document) => void;
  onSign?: (document: Document) => void;
  onWorkflowAction?: (document: Document, action: string) => void;
  className?: string;
}

export interface DocumentSearchProps {
  onSearch?: (query: string, filters: SearchFilters) => void;
  onFilterChange?: (filters: SearchFilters) => void;
  documentTypes?: DocumentType[];
  className?: string;
}