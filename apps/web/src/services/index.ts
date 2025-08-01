/**
 * Service Layer Index for Theo Frontend
 * 
 * Centralized export of all services with initialization and configuration.
 * Provides a single import point for all frontend services.
 */

// ============================================================================
// CORE SERVICES
// ============================================================================

export { authService, default as AuthService } from './authService';
export { apiService, default as ApiService, ApiError } from './api';
export { sseService, default as SSEService } from './sse';
export { chatService, default as ChatService } from './chatService';
export { adminService, default as AdminService } from './adminService';
export { editorService, default as EditorService } from './editorService';

// ============================================================================
// ERROR HANDLING
// ============================================================================

export { 
  errorHandler, 
  handleError, 
  handleErrorWithMessage, 
  handleErrorSilently, 
  handleCriticalError,
  ErrorSeverity,
  ErrorCategory
} from './errorHandler';

// ============================================================================
// STORES
// ============================================================================

export { useDocumentStore, useDocumentSelectors } from '../stores/documentStore';

// ============================================================================
// EDITOR TYPES
// ============================================================================

export type {
  EditorDocument,
  EditorTemplate,
  DocumentType as EditorDocumentType,
  DocumentStatus,
  CitationFormat,
  ExportFormat,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  Citation,
  UserDocumentStats
} from '../types/editor';

// ============================================================================
// TYPE EXPORTS
// ============================================================================

export type {
  // Authentication types
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
  
  // Document types
  Document,
  DocumentUploadRequest,
  DocumentUploadResponse,
  DocumentSearchRequest,
  DocumentSearchResponse,
  DocumentMetadata,
  DocumentType,
  ProcessingStatus,
  
  // Chat types
  ChatRequest,
  ChatResponse,
  ChatHistory,
  DocumentSource,
  
  // Job and SSE types
  JobStatus,
  JobStatusUpdate,
  SSEEventHandlers,
  
  // Admin types
  DashboardMetrics,
  UserManagementRequest,
  UserManagementResponse,
  SystemConfiguration,
  SystemHealth,
  
  // Export types
  ExportRequest,
  ExportResponse,
  
  // Utility types
  ApiError as ApiErrorType,
  PaginatedResponse,
  UploadProgress,
  StreamEvent,
  RoleType,
  PipelineType,
} from '../types/api';

// ============================================================================
// SERVICE INITIALIZATION
// ============================================================================

/**
 * Initialize all services with configuration
 */
export const initializeServices = (config: {
  apiBaseUrl?: string;
  enableErrorLogging?: boolean;
  autoRefreshDashboard?: boolean;
  defaultChatConfig?: {
    useAdvancedPipeline?: boolean;
    maxResults?: number;
  };
}) => {
  console.log('Initializing Theo services with config:', config);
  
  // Services are already initialized as singletons
  // This function can be used for any global configuration
  
  if (config.enableErrorLogging !== false) {
    // Error logging is enabled by default
    console.log('Error logging enabled');
  }
  
  if (config.autoRefreshDashboard) {
    console.log('Dashboard auto-refresh enabled');
  }
  
  console.log('Theo services initialized successfully');
};

// ============================================================================
// SERVICE HEALTH CHECK
// ============================================================================

/**
 * Check health of all services
 */
export const checkServicesHealth = async (): Promise<{
  api: boolean;
  auth: boolean;
  sse: boolean;
  errors: string[];
}> => {
  const errors: string[] = [];
  let apiHealthy = false;
  let authHealthy = false;
  let sseHealthy = false;

  try {
    // Check API health
    await apiService.healthCheck();
    apiHealthy = true;
  } catch (error) {
    errors.push(`API health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  try {
    // Check authentication status
    authHealthy = authService.isAuthenticated();
    if (!authHealthy) {
      errors.push('User not authenticated');
    }
  } catch (error) {
    errors.push(`Auth check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  try {
    // Check SSE connection state
    const sseStats = sseService.getStats();
    sseHealthy = sseStats.connected;
    if (!sseHealthy && sseStats.jobId) {
      errors.push('SSE connection not active');
    }
  } catch (error) {
    errors.push(`SSE check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  return {
    api: apiHealthy,
    auth: authHealthy,
    sse: sseHealthy,
    errors
  };
};

// ============================================================================
// SERVICE CLEANUP
// ============================================================================

/**
 * Cleanup all services (useful for app shutdown or logout)
 */
export const cleanupServices = () => {
  console.log('Cleaning up Theo services...');
  
  try {
    // Cleanup SSE connections
    sseService.cleanup();
    
    // Cleanup admin service auto-refresh
    adminService.cleanup();
    
    // Clear chat conversation
    chatService.clearConversation();
    
    // Clear error logs
    errorHandler.clearErrorLog();
    
    console.log('Theo services cleaned up successfully');
  } catch (error) {
    console.error('Error during service cleanup:', error);
  }
};

// ============================================================================
// CONVENIENCE HOOKS AND UTILITIES
// ============================================================================

/**
 * React hook for service health monitoring
 */
import { useState, useEffect } from 'react';

export const useServicesHealth = (checkInterval = 30000) => {
  const [health, setHealth] = useState<{
    api: boolean;
    auth: boolean;
    sse: boolean;
    errors: string[];
    lastCheck: string;
  }>({
    api: false,
    auth: false,
    sse: false,
    errors: [],
    lastCheck: new Date().toISOString()
  });

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const healthCheck = await checkServicesHealth();
        setHealth({
          ...healthCheck,
          lastCheck: new Date().toISOString()
        });
      } catch (error) {
        console.error('Health check failed:', error);
        setHealth(prev => ({
          ...prev,
          errors: [...prev.errors, 'Health check failed'],
          lastCheck: new Date().toISOString()
        }));
      }
    };

    // Initial check
    checkHealth();

    // Set up interval
    const interval = setInterval(checkHealth, checkInterval);

    return () => clearInterval(interval);
  }, [checkInterval]);

  return health;
};

// ============================================================================
// SERVICE CONSTANTS
// ============================================================================

export const SERVICE_CONFIG = {
  API_BASE_URL: 'http://localhost:8001',
  FRONTEND_URL: 'http://localhost:8080',
  SSE_RECONNECT_ATTEMPTS: 3,
  SSE_RECONNECT_DELAY: 2000,
  UPLOAD_MAX_SIZE: 52428800, // 50MB
  CHAT_MAX_MESSAGE_LENGTH: 2000,
  PAGINATION_DEFAULT_SIZE: 20,
  DASHBOARD_REFRESH_INTERVAL: 30000, // 30 seconds
  ERROR_LOG_MAX_SIZE: 1000,
} as const;

// ============================================================================
// DEFAULT EXPORT
// ============================================================================

export default {
  // Services
  auth: authService,
  api: apiService,
  sse: sseService,
  chat: chatService,
  admin: adminService,
  error: errorHandler,
  
  // Utilities
  initialize: initializeServices,
  checkHealth: checkServicesHealth,
  cleanup: cleanupServices,
  
  // Constants
  config: SERVICE_CONFIG,
};