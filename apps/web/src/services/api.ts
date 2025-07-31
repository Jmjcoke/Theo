/**
 * Core API Service for Theo Theological Research System
 * 
 * Comprehensive service that maps all FastAPI backend endpoints to frontend methods.
 * Provides type-safe, authenticated HTTP communication with proper error handling.
 */

import { authService } from './authService';
import type {
  // Authentication
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
  
  // Documents
  Document,
  DocumentUploadRequest,
  DocumentUploadResponse,
  DocumentSearchRequest,
  DocumentSearchResponse,
  DocumentMetadata,
  
  // Chat
  ChatRequest,
  ChatResponse,
  ChatHistory,
  
  // Jobs & SSE
  JobStatus,
  
  // Admin
  DashboardMetrics,
  UserManagementRequest,
  UserManagementResponse,
  SystemConfiguration,
  SystemHealth,
  
  // Export
  ExportRequest,
  ExportResponse,
  
  // Utility
  ApiError,
  PaginatedResponse,
  UploadProgress,
  StreamEvent
} from '@/types/api';

const API_BASE_URL = 'http://localhost:8001';

/**
 * Enhanced API Error class with detailed error information
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public type: string = 'api_error',
    public code: string = 'unknown',
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Core API Service Class
 * 
 * Provides all HTTP communication methods with the FastAPI backend.
 * Handles authentication, error processing, and response formatting.
 */
class ApiService {
  private readonly baseUrl = API_BASE_URL;

  // ============================================================================
  // CORE HTTP METHODS
  // ============================================================================

  /**
   * Make authenticated API request
   */
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authService.getAuthHeaders(),
        ...options.headers,
      },
    };

    try {
      const response = await authService.authenticatedFetch(url, config);
      
      if (!response.ok) {
        await this.handleErrorResponse(response);
      }

      // Handle empty responses (204 No Content)
      if (response.status === 204) {
        return {} as T;
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(
        error instanceof Error ? error.message : 'Network request failed',
        0,
        'network_error',
        'request_failed'
      );
    }
  }

  /**
   * Handle error responses with detailed error information
   */
  private async handleErrorResponse(response: Response): Promise<never> {
    let errorData: any = {};
    
    try {
      errorData = await response.json();
    } catch {
      // If JSON parsing fails, use status text
      errorData = { message: response.statusText };
    }

    const apiError = new ApiError(
      errorData.detail || errorData.message || `HTTP ${response.status}`,
      response.status,
      errorData.type || 'http_error',
      errorData.code || `http_${response.status}`,
      errorData
    );

    throw apiError;
  }

  /**
   * Upload file with progress tracking
   */
  private async uploadWithProgress(
    endpoint: string,
    file: File,
    additionalData: Record<string, any> = {},
    onProgress?: (progress: UploadProgress) => void
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      
      formData.append('file', file);
      
      // Add additional form data
      Object.entries(additionalData).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          formData.append(key, value.toString());
        }
      });

      // Progress tracking
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress: UploadProgress = {
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded / event.total) * 100)
          };
          onProgress(progress);
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText);
            resolve(result);
          } catch (error) {
            reject(new ApiError('Invalid JSON response', xhr.status));
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText);
            reject(new ApiError(
              errorData.detail || `Upload failed`,
              xhr.status,
              errorData.type || 'upload_error',
              errorData.code || 'upload_failed',
              errorData
            ));
          } catch {
            reject(new ApiError(`Upload failed: ${xhr.statusText}`, xhr.status));
          }
        }
      });

      // Handle network errors
      xhr.addEventListener('error', () => {
        reject(new ApiError('Upload failed due to network error', 0, 'network_error'));
      });

      // Set headers and send
      const token = authService.getToken();
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      
      xhr.open('POST', `${this.baseUrl}${endpoint}`);
      xhr.send(formData);
    });
  }

  // ============================================================================
  // AUTHENTICATION ENDPOINTS
  // ============================================================================

  /**
   * User login
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    return this.request<LoginResponse>('/api/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  /**
   * User registration
   */
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    return this.request<RegisterResponse>('/api/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/api/profile');
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<User> {
    return this.request<User>('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  // ============================================================================
  // DOCUMENT ENDPOINTS
  // ============================================================================

  /**
   * Upload document with progress tracking
   */
  async uploadDocument(
    file: File,
    documentType: string,
    category?: string,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<DocumentUploadResponse> {
    const additionalData: Record<string, any> = {
      documentType: documentType,  // Match FastAPI Form parameter name
    };
    
    if (category) {
      additionalData.category = category;
    }

    return this.uploadWithProgress(
      '/api/admin/upload',  // Correct backend endpoint
      file,
      additionalData,
      onProgress
    );
  }

  /**
   * Upload document with streaming events
   */
  async uploadDocumentWithStream(
    file: File,
    documentType: string,
    category?: string,
    onEvent?: (event: StreamEvent) => void
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('documentType', documentType);  // Match FastAPI Form parameter name
    if (category) {
      formData.append('category', category);
    }

    const token = authService.getToken();
    if (!token) {
      throw new ApiError('Authentication required', 401, 'auth_error');
    }

    const response = await fetch(`${this.baseUrl}/api/admin/upload-stream`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      await this.handleErrorResponse(response);
    }

    // Handle streaming response
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let result: DocumentUploadResponse | null = null;

    if (reader) {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const eventData = JSON.parse(line.slice(6));
                const event: StreamEvent = {
                  event: eventData.event || 'update',
                  data: eventData.data || eventData,
                  timestamp: new Date().toISOString()
                };

                if (onEvent) {
                  onEvent(event);
                }

                // Store final result
                if (eventData.event === 'upload_complete' || eventData.documentId) {
                  result = eventData.data || eventData;
                }
              } catch (error) {
                console.warn('Failed to parse SSE event:', line);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    }

    if (!result) {
      throw new ApiError('No upload result received', 500, 'upload_error');
    }

    return result;
  }

  /**
   * Get document by ID
   */
  async getDocument(documentId: string): Promise<Document> {
    return this.request<Document>(`/api/admin/documents/${documentId}`);
  }

  /**
   * Search documents
   */
  async searchDocuments(params: DocumentSearchRequest = {}): Promise<DocumentSearchResponse> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString());
      }
    });

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/api/admin/documents?${queryString}` : '/api/admin/documents';
    
    return this.request<DocumentSearchResponse>(endpoint);
  }

  /**
   * Delete document
   */
  async deleteDocument(documentId: string): Promise<void> {
    await this.request<void>(`/api/admin/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Reprocess document
   */
  async reprocessDocument(documentId: string): Promise<JobStatus> {
    return this.request<JobStatus>(`/api/admin/documents/${documentId}/reprocess`, {
      method: 'POST',
    });
  }

  // ============================================================================
  // CHAT ENDPOINTS
  // ============================================================================

  /**
   * Send chat message
   */
  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get chat history
   */
  async getChatHistory(limit?: number, offset?: number): Promise<PaginatedResponse<ChatHistory>> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const queryString = params.toString();
    const endpoint = queryString ? `/api/chat/history?${queryString}` : '/api/chat/history';
    
    return this.request<PaginatedResponse<ChatHistory>>(endpoint);
  }

  /**
   * Delete chat history
   */
  async deleteChatHistory(): Promise<void> {
    await this.request<void>('/api/chat/history', {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // JOB QUEUE ENDPOINTS
  // ============================================================================

  /**
   * Get job status
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.request<JobStatus>(`/api/jobs/${jobId}/status`);
  }

  /**
   * Cancel job
   */
  async cancelJob(jobId: string): Promise<void> {
    await this.request<void>(`/api/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  }

  /**
   * Get all jobs for current user
   */
  async getJobs(status?: string): Promise<JobStatus[]> {
    const params = status ? `?status=${status}` : '';
    return this.request<JobStatus[]>(`/api/jobs${params}`);
  }

  // ============================================================================
  // ADMIN ENDPOINTS
  // ============================================================================

  /**
   * Get dashboard metrics
   */
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return this.request<DashboardMetrics>('/api/admin/dashboard/metrics');
  }

  /**
   * Get all users (admin only)
   */
  async getUsers(
    page: number = 1, 
    perPage: number = 50,
    status?: string
  ): Promise<PaginatedResponse<User>> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    if (status) {
      params.append('status', status);
    }
    
    return this.request<PaginatedResponse<User>>(`/api/admin/users?${params}`);
  }

  /**
   * Manage user (admin only)
   */
  async manageUser(request: UserManagementRequest): Promise<UserManagementResponse> {
    return this.request<UserManagementResponse>('/api/admin/users/manage', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get system configuration (admin only)
   */
  async getSystemConfiguration(): Promise<SystemConfiguration> {
    return this.request<SystemConfiguration>('/api/admin/configuration');
  }

  /**
   * Update system configuration (admin only)
   */
  async updateSystemConfiguration(config: Partial<SystemConfiguration>): Promise<SystemConfiguration> {
    return this.request<SystemConfiguration>('/api/admin/configuration', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  /**
   * Get system health (admin only)
   */
  async getSystemHealth(): Promise<SystemHealth> {
    return this.request<SystemHealth>('/api/admin/health');
  }

  // ============================================================================
  // EXPORT ENDPOINTS
  // ============================================================================

  /**
   * Export content as PDF
   */
  async exportContentAsPDF(content: string, filename?: string): Promise<Blob> {
    const response = await authService.authenticatedFetch(`${this.baseUrl}/api/export/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify({
        content,
        filename
      }),
    });

    if (!response.ok) {
      await this.handleErrorResponse(response);
    }

    return response.blob();
  }

  /**
   * Download exported file
   */
  async downloadExport(downloadUrl: string): Promise<Blob> {
    const response = await authService.authenticatedFetch(downloadUrl);
    
    if (!response.ok) {
      await this.handleErrorResponse(response);
    }
    
    return response.blob();
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  /**
   * API health check
   */
  async apiHealthCheck(): Promise<{ status: string; service: string }> {
    return this.request<{ status: string; service: string }>('/api/health');
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;