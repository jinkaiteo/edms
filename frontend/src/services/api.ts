/**
 * API Service for EDMS Frontend
 * 
 * Centralized API client with authentication, error handling,
 * and request/response interceptors.
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { 
  ApiResponse, 
  ApiError, 
  LoginRequest, 
  LoginResponse,
  User,
  Document,
  DocumentCreateRequest,
  DocumentUpdateRequest,
  WorkflowInstance,
  WorkflowTransitionRequest,
  SearchRequest,
  SearchResponse,
  AutocompleteRequest,
  AutocompleteSuggestion,
  ElectronicSignature,
  SignatureRequest,
  DocumentTemplate,
  PlaceholderDefinition,
  SystemConfiguration,
  AuditTrail,
  ApiStatus,
  ApiInfo,
  DashboardMetrics
} from '../types/api';

class ApiService {
  private client: AxiosInstance;
  private baseURL: string;
  private token: string | null = null;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      withCredentials: true, // Enable session cookies
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.loadTokenFromStorage();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Token ${this.token}`;
        }
        
        // Temporarily disable request ID to avoid CORS issues
        // config.headers['X-Request-ID'] = this.generateRequestId();
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.handleUnauthorized();
        }
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private generateRequestId(): string {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }

  private loadTokenFromStorage(): void {
    this.token = localStorage.getItem('authToken');
  }

  private handleUnauthorized(): void {
    this.logout();
    window.location.href = '/login';
  }

  private handleError(error: AxiosError): ApiError {
    const apiError: ApiError = {
      error: {
        code: error.code || 'UNKNOWN_ERROR',
        message: error.message || 'An unknown error occurred',
        timestamp: Date.now()
      }
    };

    if (error.response?.data) {
      const responseData = error.response.data as any;
      apiError.error.message = responseData.message || responseData.detail || error.message;
      apiError.error.code = responseData.code || `HTTP_${error.response.status}`;
    }

    return apiError;
  }

  // Authentication methods
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<any>('/auth/login/', credentials);
    
    // Our Django backend doesn't use tokens, it uses sessions
    // Just return the user data
    return {
      user: response.data.user,
      token: '', // Not used with session auth
      permissions: [], // Add empty permissions array
      message: response.data.message
    };
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout/');
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.token = null;
      localStorage.removeItem('authToken');
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/user/');
    return response.data;
  }

  async refreshToken(): Promise<string> {
    const response = await this.client.post<{ token: string }>('/auth/refresh/');
    this.token = response.data.token;
    localStorage.setItem('authToken', this.token);
    return this.token;
  }

  // Document Management
  async getDocuments(params?: any): Promise<ApiResponse<Document[]>> {
    const response = await this.client.get<ApiResponse<Document[]>>('/documents/', { params });
    return response.data;
  }

  async getDocument(id: number): Promise<Document> {
    const response = await this.client.get<Document>(`/documents/${id}/`);
    return response.data;
  }

  async createDocument(data: DocumentCreateRequest): Promise<Document> {
    const formData = new FormData();
    
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined) {
        if (key === 'file' && value instanceof File) {
          formData.append(key, value);
        } else {
          formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
        }
      }
    });

    const response = await this.client.post<Document>('/documents/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async updateDocument(id: number, data: DocumentUpdateRequest): Promise<Document> {
    const formData = new FormData();
    
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined) {
        if (key === 'file' && value instanceof File) {
          formData.append(key, value);
        } else {
          formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
        }
      }
    });

    const response = await this.client.patch<Document>(`/documents/${id}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async deleteDocument(id: number): Promise<void> {
    await this.client.delete(`/documents/${id}/`);
  }

  async signDocument(data: SignatureRequest): Promise<ElectronicSignature> {
    const response = await this.client.post<ElectronicSignature>(`/documents/${data.document_id}/sign/`, data);
    return response.data;
  }

  async getDocumentWorkflowStatus(id: number): Promise<WorkflowInstance | null> {
    const response = await this.client.get<WorkflowInstance | null>(`/documents/${id}/workflow_status/`);
    return response.data;
  }

  // Workflow Management
  async getWorkflowInstances(params?: any): Promise<ApiResponse<WorkflowInstance[]>> {
    const response = await this.client.get<ApiResponse<WorkflowInstance[]>>('/workflow-instances/', { params });
    return response.data;
  }

  async getWorkflowInstance(id: number): Promise<WorkflowInstance> {
    const response = await this.client.get<WorkflowInstance>(`/workflow-instances/${id}/`);
    return response.data;
  }

  async transitionWorkflow(id: number, data: WorkflowTransitionRequest): Promise<WorkflowInstance> {
    const response = await this.client.post<WorkflowInstance>(`/workflow-instances/${id}/transition/`, data);
    return response.data;
  }

  // Search
  async searchDocuments(searchRequest: SearchRequest): Promise<SearchResponse> {
    const response = await this.client.get<SearchResponse>('/search/', { params: searchRequest });
    return response.data;
  }

  async getAutocomplete(request: AutocompleteRequest): Promise<AutocompleteSuggestion[]> {
    const response = await this.client.get<AutocompleteSuggestion[]>('/search/autocomplete/', { params: request });
    return response.data;
  }

  async recordSearchClick(queryId: string, documentId: number, rank: number): Promise<void> {
    await this.client.post('/search/click/', { query_id: queryId, document_id: documentId, rank });
  }

  // Templates and Generation
  async getDocumentTemplates(params?: any): Promise<ApiResponse<DocumentTemplate[]>> {
    const response = await this.client.get<ApiResponse<DocumentTemplate[]>>('/document-templates/', { params });
    return response.data;
  }

  async getDocumentTemplate(id: number): Promise<DocumentTemplate> {
    const response = await this.client.get<DocumentTemplate>(`/document-templates/${id}/`);
    return response.data;
  }

  async getPlaceholders(params?: any): Promise<ApiResponse<PlaceholderDefinition[]>> {
    const response = await this.client.get<ApiResponse<PlaceholderDefinition[]>>('/placeholders/', { params });
    return response.data;
  }

  // System Configuration
  async getSystemConfigurations(params?: any): Promise<ApiResponse<SystemConfiguration[]>> {
    const response = await this.client.get<ApiResponse<SystemConfiguration[]>>('/system-configurations/', { params });
    return response.data;
  }

  async updateSystemConfiguration(id: number, value: string): Promise<SystemConfiguration> {
    const response = await this.client.patch<SystemConfiguration>(`/system-configurations/${id}/`, { value });
    return response.data;
  }

  // Electronic Signatures
  async getElectronicSignatures(params?: any): Promise<ApiResponse<ElectronicSignature[]>> {
    const response = await this.client.get<ApiResponse<ElectronicSignature[]>>('/electronic-signatures/', { params });
    return response.data;
  }

  async getElectronicSignature(id: number): Promise<ElectronicSignature> {
    const response = await this.client.get<ElectronicSignature>(`/electronic-signatures/${id}/`);
    return response.data;
  }

  // Audit Trail
  async getAuditTrail(params?: any): Promise<ApiResponse<AuditTrail[]>> {
    const response = await this.client.get<ApiResponse<AuditTrail[]>>('/audit-trail/', { params });
    return response.data;
  }

  // System Status
  async getApiStatus(): Promise<ApiStatus> {
    // Use the available health endpoint
    const response = await axios.get('http://localhost:8000/health/', {
      withCredentials: true,
      timeout: 5000
    });
    return response.data;
  }

  async getApiInfo(): Promise<ApiInfo> {
    const response = await this.client.get<ApiInfo>('/info/');
    return response.data;
  }

  async getApiHealth(): Promise<ApiStatus> {
    const response = await this.client.get<ApiStatus>('/health/');
    return response.data;
  }

  // Dashboard
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await this.client.get<DashboardMetrics>('/dashboard/metrics/');
    return response.data;
  }

  // File Operations
  async downloadDocument(id: number): Promise<Blob> {
    const response = await this.client.get(`/documents/${id}/download/`, {
      responseType: 'blob'
    });
    return response.data;
  }

  async previewDocument(id: number): Promise<Blob> {
    const response = await this.client.get(`/documents/${id}/preview/`, {
      responseType: 'blob'
    });
    return response.data;
  }

  // Utility methods
  isAuthenticated(): boolean {
    // For session-based auth, we can't rely on token
    // This should be checked via API call instead
    return false; // Temporarily disabled
  }

  getToken(): string | null {
    return this.token;
  }

  getBaseURL(): string {
    return this.baseURL;
  }

  // Generic GET method
  async get<T>(endpoint: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(endpoint, { params });
    return response.data;
  }

  // Generic POST method
  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(endpoint, data);
    return response.data;
  }

  // Generic PUT method
  async put<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(endpoint, data);
    return response.data;
  }

  // Generic PATCH method
  async patch<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(endpoint, data);
    return response.data;
  }

  // Generic DELETE method
  async delete(endpoint: string): Promise<void> {
    await this.client.delete(endpoint);
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;