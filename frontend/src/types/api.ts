/**
 * API Types for EDMS Frontend
 * 
 * TypeScript type definitions for API responses and requests
 * corresponding to the backend REST API implementation.
 */

// Base API response structure
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  success: boolean;
  errors?: Record<string, string[]>;
  pagination?: PaginationInfo;
}

export interface PaginationInfo {
  count: number;
  next: string | null;
  previous: string | null;
  page: number;
  page_size: number;
  total_pages: number;
}

// Authentication types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
  permissions: string[];
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login: string | null;
  full_name: string;
  roles: UserRole[];
}

export interface UserRole {
  id: number;
  role: Role;
  is_active: boolean;
  assigned_at: string;
  assigned_by: User;
}

export interface Role {
  id: number;
  name: string;
  description: string;
  module: string;
  permission_level: 'read' | 'write' | 'review' | 'approve' | 'admin';
  permissions: string[];
}

// Document types
export interface Document {
  id?: number;
  uuid: string;
  document_number: string;
  title: string;
  description?: string;
  document_type?: DocumentType | string; // Can be object or string
  document_type_display?: string;       // API provides this field
  status: DocumentStatus;
  status_display?: string;         // API provides this field
  version?: string;
  version_string?: string;         // API provides this field
  created_by?: User;
  author?: number;                 // Author user ID
  author_display?: string;         // API provides this field
  reviewer?: number;               // Reviewer user ID - MISSING FIELD ADDED
  reviewer_display?: string;       // Reviewer display name - MISSING FIELD ADDED
  approver?: number;               // Approver user ID - MISSING FIELD ADDED  
  approver_display?: string;       // Approver display name - MISSING FIELD ADDED
  created_at: string;
  updated_at?: string;
  effective_date: string | null;
  review_date?: string | null;
  obsolete_date?: string | null;
  file_path?: string | null;
  file_size?: number | null;
  file_checksum?: string | null;
  metadata?: Record<string, any>;
  dependencies?: Document[];
  workflow_state?: string;
  current_workflow?: WorkflowInstance;
  is_controlled?: boolean;         // API provides this field
  requires_training?: boolean;     // API provides this field
}

export interface DocumentType {
  id: number;
  code?: string;              // backend returns code
  name: string;
  description?: string;
  prefix?: string;            // legacy field; prefer code/numbering_prefix
  numbering_prefix?: string;  // backend document type numbering prefix
  is_active: boolean;
  workflow_required?: boolean;
  retention_period?: number | null;
  template?: string | null;
}

export type DocumentStatus = 
  | 'DRAFT' 
  | 'PENDING_REVIEW'
  | 'UNDER_REVIEW'
  | 'REVIEW_COMPLETED'
  | 'PENDING_APPROVAL'
  | 'UNDER_APPROVAL'
  | 'APPROVED'
  | 'APPROVED_PENDING_EFFECTIVE' 
  | 'EFFECTIVE' 
  | 'SCHEDULED_FOR_OBSOLESCENCE'
  | 'SUPERSEDED' 
  | 'OBSOLETE' 
  | 'TERMINATED';

export interface DocumentCreateRequest {
  document_number?: string;
  title: string;
  description: string;
  document_type_id: number;
  metadata?: Record<string, any>;
  file?: File;
}

export interface DocumentUpdateRequest {
  title?: string;
  description?: string;
  metadata?: Record<string, any>;
  file?: File;
}

// Workflow types
export interface WorkflowInstance {
  id: number;
  uuid: string;
  workflow_type: WorkflowType;
  state: string;
  state_display: string;
  initiated_by: User;
  current_assignee: User | null;
  started_at: string;
  completed_at: string | null;
  due_date: string | null;
  is_active: boolean;
  is_completed: boolean;
  is_overdue: boolean;
  completion_reason: string | null;
  workflow_data: Record<string, any>;
  content_object_data: {
    type: string;
    id: number;
    document_number?: string;
    title?: string;
    status?: string;
    version?: string;
  } | null;
}

export interface WorkflowType {
  id: number;
  uuid: string;
  name: string;
  workflow_type: 'REVIEW' | 'APPROVAL' | 'UP_VERSION' | 'OBSOLETE' | 'TERMINATE';
  description: string;
  is_active: boolean;
  requires_approval: boolean;
  timeout_days: number;
  reminder_days: number;
}

export interface WorkflowTask {
  id: number;
  uuid: string;
  workflow_instance: number;
  task_type: string;
  title: string;
  description: string;
  assigned_to: User;
  created_at: string;
  due_date: string | null;
  completed_at: string | null;
  completed_by: User | null;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  completion_notes: string;
  task_data: Record<string, any>;
}

export interface WorkflowTransitionRequest {
  transition_name: string;
  reason?: string;
  transition_data?: Record<string, any>;
}

// Search types
export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  page?: number;
  page_size?: number;
  sort_by?: 'relevance' | 'title' | 'document_number' | 'created_date' | 'effective_date' | 'author' | 'status' | 'type';
}

export interface SearchFilters {
  document_type?: string[];
  status?: DocumentStatus[];
  created_after?: string;
  created_before?: string;
  author?: string[];
  // Added relevant backend-supported filters:
  title?: string;
  description?: string;
  document_number?: string;
  keywords?: string;
  priority?: string;
  reviewer?: string[];
  approver?: string[];
  // Removed irrelevant filters:
  // - department (not supported by backend)
  // - effective_after/before (different usage pattern)
  // - version (backend uses version_major/version_minor)
}

export interface SearchResponse {
  query: string;
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  documents: DocumentSearchResult[];
  facets: SearchFacets;
  suggestions: string[];
  response_time: number;
  applied_filters: SearchFilters;
  error?: string;
}

export interface DocumentSearchResult {
  id: number;
  document_number: string;
  title: string;
  description: string;
  document_type: string | null;
  status: DocumentStatus;
  version: string;
  created_by: string | null;
  created_at: string;
  effective_date: string | null;
  relevance_score: number;
  url: string;
  metadata: Record<string, any>;
}

export interface SearchFacets {
  [key: string]: {
    display_name: string;
    type: string;
    values: SearchFacetValue[];
  };
}

export interface SearchFacetValue {
  value: string;
  label?: string;
  count: number;
  selected: boolean;
}

export interface AutocompleteRequest {
  query: string;
  limit?: number;
}

export interface AutocompleteSuggestion {
  text: string;
  document_number?: string;
  document_type?: string;
  url?: string;
  rank?: number;
  type?: string;
  frequency?: number;
}

// Electronic Signature types
export interface ElectronicSignature {
  id: number;
  uuid: string;
  document: number;
  user: User;
  signature_type: 'APPROVAL' | 'REVIEW' | 'AUTHOR' | 'WITNESS' | 'VERIFICATION';
  reason: string;
  signature_timestamp: string;
  document_hash: string;
  signature_data: Record<string, any>;
  certificate: UserCertificate;
  signature_method: 'PKI_DIGITAL' | 'BIOMETRIC' | 'PASSWORD' | 'TOKEN';
  is_valid: boolean;
  invalidated_at: string | null;
  invalidation_reason: string;
}

export interface UserCertificate {
  id: number;
  uuid: string;
  user: number;
  certificate_type: 'SIGNING' | 'ENCRYPTION' | 'AUTHENTICATION' | 'MULTI_PURPOSE';
  serial_number: string;
  subject_dn: string;
  issuer_dn: string;
  issued_at: string;
  expires_at: string;
  is_active: boolean;
  revoked_at: string | null;
  revocation_reason: string;
}

export interface SignatureRequest {
  document_id: number;
  signature_reason: string;
  signature_type: 'APPROVAL' | 'REVIEW' | 'AUTHOR' | 'WITNESS' | 'VERIFICATION';
  password?: string;
}

// Template types
export interface DocumentTemplate {
  id: number;
  uuid: string;
  name: string;
  description: string;
  template_type: 'DOCX' | 'PDF' | 'HTML' | 'TEXT';
  file_path: string;
  output_filename_pattern: string;
  processing_rules: Record<string, any>;
  version: string;
  status: 'DRAFT' | 'ACTIVE' | 'INACTIVE' | 'ARCHIVED';
  is_default: boolean;
  usage_count: number;
  last_used: string | null;
  created_at: string;
  updated_at: string;
  created_by: User;
  placeholders_count: number;
  usage_statistics: {
    total_generations: number;
    successful_generations: number;
    failed_generations: number;
    last_used: string | null;
  };
}

export interface PlaceholderDefinition {
  id: number;
  uuid: string;
  name: string;
  display_name: string;
  description: string;
  placeholder_type: 'DOCUMENT' | 'USER' | 'WORKFLOW' | 'SYSTEM' | 'DATE' | 'CUSTOM';
  data_source: 'DOCUMENT_MODEL' | 'USER_MODEL' | 'WORKFLOW_MODEL' | 'SYSTEM_CONFIG' | 'COMPUTED' | 'JSONB_FIELD';
  source_field: string;
  format_string: string;
  date_format: string;
  default_value: string;
  validation_rules: Record<string, any>;
  is_active: boolean;
  requires_permission: string;
  cache_duration: number;
  created_at: string;
  updated_at: string;
  created_by: User;
  template_syntax: string;
}

export interface DocumentGeneration {
  id: number;
  uuid: string;
  template: DocumentTemplate;
  source_document: number | null;
  output_format: string;
  context_data: Record<string, any>;
  generation_options: Record<string, any>;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  output_file_path: string;
  output_filename: string;
  file_size: number | null;
  file_size_mb: number | null;
  file_checksum: string;
  started_at: string | null;
  completed_at: string | null;
  processing_time: string | null;
  processing_time_seconds: number | null;
  error_message: string;
  requested_by: User;
  created_at: string;
}

// System Configuration types
export interface SystemConfiguration {
  id: number;
  uuid: string;
  key: string;
  display_name: string;
  description: string;
  category: 'SYSTEM' | 'SECURITY' | 'APPEARANCE' | 'NOTIFICATION' | 'INTEGRATION' | 'WORKFLOW' | 'BACKUP' | 'AUDIT';
  setting_type: 'STRING' | 'INTEGER' | 'FLOAT' | 'BOOLEAN' | 'JSON' | 'FILE_PATH' | 'URL' | 'EMAIL' | 'COLOR';
  value: string;
  default_value: string;
  validation_rules: Record<string, any>;
  allowed_values: any[];
  is_sensitive: boolean;
  requires_restart: boolean;
  is_user_configurable: boolean;
  created_at: string;
  updated_at: string;
  updated_by: User | null;
}

export interface FeatureToggle {
  id: number;
  uuid: string;
  key: string;
  name: string;
  description: string;
  toggle_type: 'RELEASE' | 'EXPERIMENT' | 'OPERATIONAL' | 'PERMISSION';
  is_enabled: boolean;
  conditions: Record<string, any>;
  target_users: User[];
  target_roles: string[];
  rollout_percentage: number;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  updated_at: string;
  created_by: User;
}

// Audit types
export interface AuditTrail {
  id: number;
  uuid: string;
  user: User | null;
  action: string;
  object_type: string | null;
  object_id: number | null;
  description: string;
  timestamp: string;
  ip_address: string | null;
  user_agent: string | null;
  session_id: string | null;
  request_id: string | null;
  additional_data: Record<string, any>;
  integrity_hash: string | null;
}

// API Status types
export interface ApiStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  environment: string;
  checks?: {
    database: 'healthy' | 'unhealthy';
    cache: 'healthy' | 'unhealthy';
    api: 'healthy' | 'unhealthy';
  };
}

export interface ApiInfo {
  title: string;
  description: string;
  version: string;
  documentation_url: string;
  contact: {
    name: string;
    email: string;
  };
  authentication: string[];
  rate_limits: {
    authenticated: string;
    anonymous: string;
  };
  features: Record<string, boolean>;
}

// Error types
export interface ApiError {
  error: {
    code: string;
    message: string;
    timestamp?: number;
    debug?: {
      exception_type: string;
      exception_message: string;
    };
  };
}

// Generic request/response types
export interface ListResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface IdNamePair {
  id: number;
  name: string;
}

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

// Form types
export interface FormErrors {
  [fieldName: string]: string[] | string;
}

export interface PaginatedRequest {
  page?: number;
  page_size?: number;
}

export interface FilterRequest {
  [key: string]: any;
}

// Dashboard types
export interface DashboardMetrics {
  total_documents: number;
  pending_reviews: number;
  pending_approvals: number;
  effective_documents: number;
  recent_activity: AuditTrail[];
  workflow_summary: {
    active_workflows: number;
    completed_today: number;
    overdue_tasks: number;
  };
  system_health: {
    status: 'healthy' | 'warning' | 'critical';
    last_backup: string | null;
    storage_usage: number;
    active_users: number;
  };
}

export interface ActivityItem {
  id: string;
  type: 'document_created' | 'document_updated' | 'document_deleted' | 'document_signed' | 'user_login' | 'workflow_completed' | 'workflow_updated' | 'system_activity';
  title: string;
  description: string;
  timestamp: string;
  user: string;
  icon: string;
  iconColor: string;
}

export interface DashboardStats {
  user_stats: {
    total_documents: number;
    pending_tasks: number;
    my_documents: number;
    action_required: number;
  };
  system_stats: {
    total_documents: number;
    active_workflows: number;
    total_users: number;
    system_status: string;
  };
  document_breakdown: Record<string, number>;
  // New stat cards
  stat_cards?: {
    total_documents: number;
    documents_needing_action: number;
    active_users_24h: number;
    system_health: 'healthy' | 'degraded' | 'down';
  };
  // Legacy fields
  total_documents: number;
  pending_reviews: number;
  active_workflows: number;
  active_users: number;
  placeholders: number;
  audit_entries_24h: number;
  recent_activity: ActivityItem[];
  timestamp: string;
  cache_duration: number;
  last_updated: string;
  success: boolean;
}

// Notification types
export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: string;
  read: boolean;
  action_url?: string;
  action_text?: string;
}