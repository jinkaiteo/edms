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
  DashboardMetrics,
  DashboardStats
} from '../types/api';

class ApiService {
  private client: AxiosInstance;
  private baseURL: string;
  private token: string | null = null;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
    
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
        // Always get fresh token from localStorage
        const accessToken = localStorage.getItem('accessToken');
        if (accessToken) {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
        
        // Add CSRF token for session auth support
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
          config.headers['X-CSRFToken'] = csrfToken;
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Try to refresh token before giving up
          const refreshToken = localStorage.getItem('refreshToken');
          if (refreshToken && !error.config?.url?.includes('/auth/token/refresh/')) {
            try {
              const newToken = await this.refreshAccessToken();
              if (newToken && error.config) {
                // Retry original request with new token
                error.config.headers = error.config.headers || {};
                error.config.headers.Authorization = `Bearer ${newToken}`;
                return this.client.request(error.config);
              }
            } catch (refreshError) {
              console.error('Token refresh failed:', refreshError);
            }
          }
          this.handleUnauthorized();
        }
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private getCSRFToken(): string | null {
    const cookies = document.cookie.split(';');
    const csrfCookie = cookies.find(cookie => 
      cookie.trim().startsWith('csrftoken=')
    );
    
    if (csrfCookie) {
      return csrfCookie.split('=')[1];
    }
    
    return null;
  }

  private async refreshAccessToken(): Promise<string | null> {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) return null;

      const response = await this.client.post('/auth/token/refresh/', {
        refresh: refreshToken
      });

      const newToken = response.data.access;
      if (newToken) {
        localStorage.setItem('accessToken', newToken);
        this.token = newToken;
        return newToken;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }
    
    return null;
  }

  private generateRequestId(): string {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }

  private loadTokenFromStorage(): void {
    // Updated to use correct localStorage key
    this.token = localStorage.getItem('accessToken');
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

  // User Management methods  
  async getUser(id: number): Promise<User> {
    const response = await this.client.get<User>(`/users/users/${id}/`);
    return response.data;
  }

  async deleteUser(id: number): Promise<void> {
    await this.client.delete(`/users/users/${id}/`);
  }

  async assignRole(userId: number, roleId: number, reason?: string): Promise<any> {
    const response = await this.client.post(`/users/users/${userId}/assign_role/`, { 
      role_id: roleId,
      reason: reason || ''
    });
    return response.data;
  }

  async removeRole(userId: number, roleId: number, reason?: string): Promise<any> {
    const response = await this.client.post(`/users/users/${userId}/remove_role/`, { 
      role_id: roleId,
      reason: reason || ''
    });
    return response.data;
  }

  async resetPassword(userId: number, newPassword: string, newPasswordConfirm: string, reason?: string): Promise<any> {
    const response = await this.client.post(`/users/users/${userId}/reset_password/`, {
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
      reason: reason || ''
    });
    return response.data;
  }

  async createUser(userData: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    first_name?: string;
    last_name?: string;
    employee_id?: string;
    phone_number?: string;
    department?: string;
    position?: string;
    role_id?: number;
  }): Promise<any> {
    const response = await this.client.post('/users/users/', userData);
    return response.data;
  }

  async updateUser(userId: number, userData: Partial<{
    email: string;
    first_name: string;
    last_name: string;
    employee_id: string;
    phone_number: string;
    department: string;
    position: string;
    is_active: boolean;
  }>): Promise<any> {
    const response = await this.client.patch(`/users/users/${userId}/`, userData);
    return response.data;
  }

  async getUsers(): Promise<any[]> {
    const response = await this.client.get('/users/users/');
    return response.data.results || response.data;
  }

  async getRoles(params?: any): Promise<any[]> {
    const response = await this.client.get('/users/roles/', { params });
    return response.data.results || response.data;
  }

  // System Settings methods
  async getSystemSettings(params?: any): Promise<ApiResponse<SystemConfiguration[]>> {
    const response = await this.client.get<ApiResponse<SystemConfiguration[]>>('/settings/', { params });
    return response.data;
  }

  async updateSystemSetting(id: number, value: string): Promise<SystemConfiguration> {
    const response = await this.client.patch<SystemConfiguration>(`/settings/${id}/`, { value });
    return response.data;
  }

  // Workflow Management methods  
  async getWorkflowTypes(params?: any): Promise<ApiResponse<any[]>> {
    const response = await this.client.get<ApiResponse<any[]>>('/workflows/types/', { params });
    return response.data;
  }

  async updateWorkflowType(id: number, data: any): Promise<any> {
    const response = await this.client.patch(`/workflows/types/${id}/`, data);
    return response.data;
  }


  // Authentication methods
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      // Use the correct JWT token endpoint from URL configuration
      const response = await this.client.post<any>('/auth/token/', credentials);
      const loginData = response.data;
      
      // Set token for future requests if JWT is returned
      if (loginData.access) {
        this.setAuthToken(loginData.access);
      }
      
      return loginData;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout/');
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.token = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }

  // Add method to set auth token
  setAuthToken(token: string | null): void {
    this.token = token;
    if (token) {
      localStorage.setItem('accessToken', token);
      this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      delete this.client.defaults.headers.common['Authorization'];
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/profile/');
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
          // Fix field name mapping for backend compatibility
          let fieldName = key;
          if (key === 'document_type_id') {
            fieldName = 'document_type'; // Backend expects 'document_type' not 'document_type_id'
          } else if (key === 'document_source_id') {
            fieldName = 'document_source'; // Backend expects 'document_source' not 'document_source_id'
          }
          const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
          formData.append(fieldName, stringValue);
        }
      }
    });
    
    // Note: document_source should come from form data, not hardcoded
    
    // Debug: Log all FormData entries
    for (let [key, value] of formData.entries()) {
      if (value instanceof File) {
      } else {
      }
    }

    // Use the correct endpoint and let interceptor handle auth
    
    try {
      const response = await this.client.post<Document>('/documents/documents/', formData, {
        headers: { 
          // Don't set Content-Type for FormData - let browser set it with boundary
        }
      });
      return response.data;
    } catch (error: any) {
      console.error('❌ Document creation failed:', error);
      console.error('Full error object:', JSON.stringify(error, null, 2));
      console.error('Error response data:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('Error status text:', error.response?.statusText);
      console.error('Error headers:', error.response?.headers);
      console.error('Error message:', error.message);
      console.error('Error config:', error.config);
      throw error;
    }
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

  async uploadDocumentFile(documentUuid: string, formData: FormData): Promise<any> {
    try {
      const response = await this.client.patch(`/documents/${documentUuid}/upload/`, formData, {
        headers: {
          // Don't set Content-Type for FormData - let browser set it with boundary
        }
      });
      return { success: true, data: response.data };
    } catch (error: any) {
      console.error('File upload failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || error.message || 'File upload failed'
      };
    }
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
    const response = await this.client.get<ApiResponse<AuditTrail[]>>('/audit/combined/', { params });
    return response.data;
  }

  async getAuditTrailOnly(params?: any): Promise<ApiResponse<AuditTrail[]>> {
    const response = await this.client.get<ApiResponse<AuditTrail[]>>('/audit/trail/', { params });
    return response.data;
  }

  async getLoginAudit(params?: any): Promise<ApiResponse<any[]>> {
    const response = await this.client.get<ApiResponse<any[]>>('/audit/login/', { params });
    return response.data;
  }

  async getAuditStatistics(): Promise<any> {
    const response = await this.client.get('/audit/combined/statistics/');
    return response.data;
  }

  // System Status
  async getApiStatus(): Promise<ApiStatus> {
    // Use the available health endpoint
    const response = await axios.get('/health/', {
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

  // Authentication state
  private token: string | null = localStorage.getItem('accessToken');

  // Set authentication token
  setAuthToken(token: string) {
    this.token = token;
    localStorage.setItem('accessToken', token);
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // Clear authentication
  clearAuth() {
    this.token = null;
    localStorage.removeItem('accessToken');
    delete this.client.defaults.headers.common['Authorization'];
  }

  // Check if authenticated
  isAuthenticated(): boolean {
    return !!this.token;
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

  // Generic POST method with proper FormData handling
  async post<T>(endpoint: string, data?: any, config?: any): Promise<T> {
    // For FormData requests, ensure proper headers and auth
    if (data instanceof FormData) {
      const accessToken = localStorage.getItem('accessToken');
      const formDataConfig = {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          // Don't set Content-Type for FormData - let browser set boundary
        },
        ...config
      };
      const response = await this.client.post<T>(endpoint, data, formDataConfig);
      return response.data;
    }
    
    const response = await this.client.post<T>(endpoint, data, config);
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

  // Dashboard Statistics
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.client.get<DashboardStats>('/dashboard/stats/');
    return response.data;
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
