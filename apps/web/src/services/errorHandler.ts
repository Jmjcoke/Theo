/**
 * Error Handling Service for Theo Frontend
 * 
 * Centralized error handling with user-friendly messages, logging,
 * and recovery strategies for the theological research system.
 */

import { toast } from 'sonner';
import type { ApiError } from '@/types/api';

// ============================================================================
// ERROR TYPES AND INTERFACES
// ============================================================================

export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export enum ErrorCategory {
  AUTHENTICATION = 'authentication',
  NETWORK = 'network',
  VALIDATION = 'validation',
  UPLOAD = 'upload',
  PROCESSING = 'processing',
  PERMISSION = 'permission',
  SERVER = 'server',
  CLIENT = 'client',
  UNKNOWN = 'unknown'
}

export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  documentId?: string;
  jobId?: string;
  metadata?: Record<string, any>;
}

export interface ErrorHandlingOptions {
  showToast?: boolean;
  logError?: boolean;
  severity?: ErrorSeverity;
  category?: ErrorCategory;
  context?: ErrorContext;
  recoverable?: boolean;
  retryable?: boolean;
  customMessage?: string;
}

// ============================================================================
// ERROR MESSAGE MAPPINGS
// ============================================================================

const ERROR_MESSAGES: Record<string, string> = {
  // Authentication errors
  'authentication_failed': 'Login failed. Please check your credentials.',
  'token_expired': 'Your session has expired. Please log in again.',
  'insufficient_permissions': 'You do not have permission to perform this action.',
  'account_suspended': 'Your account has been suspended. Please contact support.',
  'registration_failed': 'Account registration failed. Please try again.',
  
  // Network errors
  'network_error': 'Unable to connect to the server. Please check your internet connection.',
  'request_timeout': 'Request timed out. Please try again.',
  'server_unavailable': 'The server is temporarily unavailable. Please try again later.',
  
  // Upload errors
  'file_too_large': 'File is too large. Please select a smaller file.',
  'invalid_file_type': 'File type not supported. Please select a different file.',
  'upload_failed': 'File upload failed. Please try again.',
  'file_corrupted': 'File appears to be corrupted. Please try a different file.',
  'storage_full': 'Storage quota exceeded. Please delete some files or contact support.',
  
  // Processing errors
  'processing_failed': 'Document processing failed. The file may be corrupted or unsupported.',
  'extraction_failed': 'Unable to extract text from the document. Please try a different format.',
  'embedding_failed': 'Failed to generate document embeddings. Please try reprocessing.',
  'job_timeout': 'Processing took too long and was cancelled. Please try with a smaller file.',
  
  // Validation errors
  'required_field_missing': 'Please fill in all required fields.',
  'invalid_format': 'Invalid format. Please check your input.',
  'data_validation_failed': 'Data validation failed. Please check your input.',
  
  // Chat errors
  'chat_failed': 'Unable to process your question. Please try again.',
  'no_results_found': 'No relevant information found. Try rephrasing your question.',
  'query_too_long': 'Your question is too long. Please try a shorter version.',
  
  // Admin errors
  'admin_action_failed': 'Administrative action failed. Please try again.',
  'user_management_failed': 'User management operation failed. Please check permissions.',
  'system_config_failed': 'System configuration update failed. Please check the values.',
  
  // Generic fallbacks
  'unknown_error': 'An unexpected error occurred. Please try again or contact support.',
  'server_error': 'Server error occurred. Please try again later.',
  'client_error': 'A problem occurred in the application. Please refresh the page.',
};

// ============================================================================
// ERROR CATEGORIZATION
// ============================================================================

const ERROR_CATEGORY_MAP: Record<string, ErrorCategory> = {
  // Authentication
  'authentication_failed': ErrorCategory.AUTHENTICATION,
  'token_expired': ErrorCategory.AUTHENTICATION,
  'insufficient_permissions': ErrorCategory.PERMISSION,
  'account_suspended': ErrorCategory.AUTHENTICATION,
  'auth_error': ErrorCategory.AUTHENTICATION,
  
  // Network
  'network_error': ErrorCategory.NETWORK,
  'request_timeout': ErrorCategory.NETWORK,
  'server_unavailable': ErrorCategory.NETWORK,
  'connection_failed': ErrorCategory.NETWORK,
  
  // Upload
  'file_too_large': ErrorCategory.UPLOAD,
  'invalid_file_type': ErrorCategory.UPLOAD,
  'upload_failed': ErrorCategory.UPLOAD,
  'storage_error': ErrorCategory.UPLOAD,
  
  // Processing
  'processing_failed': ErrorCategory.PROCESSING,
  'job_error': ErrorCategory.PROCESSING,
  'extraction_failed': ErrorCategory.PROCESSING,
  
  // Validation
  'validation_error': ErrorCategory.VALIDATION,
  'client_validation_failed': ErrorCategory.VALIDATION,
  'required_field_missing': ErrorCategory.VALIDATION,
  
  // Server
  'server_error': ErrorCategory.SERVER,
  'database_error': ErrorCategory.SERVER,
  'service_unavailable': ErrorCategory.SERVER,
};

// ============================================================================
// ERROR SEVERITY MAPPING
// ============================================================================

const ERROR_SEVERITY_MAP: Record<string, ErrorSeverity> = {
  'network_error': ErrorSeverity.WARNING,
  'validation_error': ErrorSeverity.INFO,
  'authentication_failed': ErrorSeverity.WARNING,
  'processing_failed': ErrorSeverity.ERROR,
  'server_error': ErrorSeverity.CRITICAL,
  'database_error': ErrorSeverity.CRITICAL,
  'upload_failed': ErrorSeverity.ERROR,
};

// ============================================================================
// ERROR HANDLER CLASS
// ============================================================================

class ErrorHandler {
  private errorLog: Array<{
    timestamp: string;
    error: any;
    context?: ErrorContext;
    severity: ErrorSeverity;
    category: ErrorCategory;
  }> = [];

  private maxLogSize = 1000;

  /**
   * Handle any error with comprehensive processing
   */
  handle(
    error: any,
    options: ErrorHandlingOptions = {}
  ): void {
    const {
      showToast = true,
      logError = true,
      context,
      customMessage,
      severity,
      category,
      recoverable = true,
      retryable = false
    } = options;

    // Parse the error
    const parsedError = this.parseError(error);
    
    // Determine category and severity
    const errorCategory = category || this.categorizeError(parsedError);
    const errorSeverity = severity || this.determineSeverity(parsedError);
    
    // Get user-friendly message
    const userMessage = customMessage || this.getUserMessage(parsedError);
    
    // Log the error
    if (logError) {
      this.logError(parsedError, context, errorSeverity, errorCategory);
    }
    
    // Show toast notification
    if (showToast) {
      this.showToast(userMessage, errorSeverity, recoverable, retryable);
    }
    
    // Handle critical errors
    if (errorSeverity === ErrorSeverity.CRITICAL) {
      this.handleCriticalError(parsedError, context);
    }
  }

  /**
   * Parse any error into a standardized format
   */
  private parseError(error: any): {
    message: string;
    code: string;
    type: string;
    status?: number;
    details?: any;
  } {
    // Already an ApiError
    if (error instanceof Error && 'status' in error && 'type' in error && 'code' in error) {
      const apiError = error as ApiError;
      return {
        message: apiError.message,
        code: apiError.code,
        type: apiError.type,
        status: apiError.status,
        details: apiError.details
      };
    }
    
    // Standard Error object
    if (error instanceof Error) {
      return {
        message: error.message,
        code: 'client_error',
        type: 'client_error'
      };
    }
    
    // String error
    if (typeof error === 'string') {
      return {
        message: error,
        code: 'unknown_error',
        type: 'unknown_error'
      };
    }
    
    // Object with error information
    if (error && typeof error === 'object') {
      return {
        message: error.message || error.detail || 'Unknown error',
        code: error.code || 'unknown_error',
        type: error.type || 'unknown_error',
        status: error.status,
        details: error
      };
    }
    
    // Fallback
    return {
      message: 'An unexpected error occurred',
      code: 'unknown_error',
      type: 'unknown_error'
    };
  }

  /**
   * Categorize error based on type/code
   */
  private categorizeError(error: { type: string; code: string }): ErrorCategory {
    return ERROR_CATEGORY_MAP[error.type] || 
           ERROR_CATEGORY_MAP[error.code] || 
           ErrorCategory.UNKNOWN;
  }

  /**
   * Determine error severity
   */
  private determineSeverity(error: { type: string; code: string; status?: number }): ErrorSeverity {
    // Check by type/code first
    const mappedSeverity = ERROR_SEVERITY_MAP[error.type] || ERROR_SEVERITY_MAP[error.code];
    if (mappedSeverity) return mappedSeverity;
    
    // Check by HTTP status
    if (error.status) {
      if (error.status >= 500) return ErrorSeverity.CRITICAL;
      if (error.status >= 400) return ErrorSeverity.ERROR;
      if (error.status >= 300) return ErrorSeverity.WARNING;
    }
    
    return ErrorSeverity.ERROR;
  }

  /**
   * Get user-friendly error message
   */
  private getUserMessage(error: { message: string; code: string; type: string }): string {
    // Try to find mapped message by code
    if (ERROR_MESSAGES[error.code]) {
      return ERROR_MESSAGES[error.code];
    }
    
    // Try by type
    if (ERROR_MESSAGES[error.type]) {
      return ERROR_MESSAGES[error.type];
    }
    
    // Try to extract meaningful info from the original message
    const originalMessage = error.message.toLowerCase();
    
    // Common patterns
    if (originalMessage.includes('network') || originalMessage.includes('fetch')) {
      return ERROR_MESSAGES.network_error;
    }
    
    if (originalMessage.includes('unauthorized') || originalMessage.includes('authentication')) {
      return ERROR_MESSAGES.authentication_failed;
    }
    
    if (originalMessage.includes('file') && originalMessage.includes('large')) {
      return ERROR_MESSAGES.file_too_large;
    }
    
    if (originalMessage.includes('timeout')) {
      return ERROR_MESSAGES.request_timeout;
    }
    
    // Return original message if it's user-friendly, otherwise generic message
    if (error.message.length < 100 && !error.message.includes('Error:')) {
      return error.message;
    }
    
    return ERROR_MESSAGES.unknown_error;
  }

  /**
   * Log error to console and internal log
   */
  private logError(
    error: any,
    context?: ErrorContext,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    category: ErrorCategory = ErrorCategory.UNKNOWN
  ): void {
    const logEntry = {
      timestamp: new Date().toISOString(),
      error,
      context,
      severity,
      category
    };

    // Add to internal log
    this.errorLog.push(logEntry);
    
    // Trim log if too large
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(-this.maxLogSize / 2);
    }

    // Console logging based on severity
    const logMethod = severity === ErrorSeverity.CRITICAL ? 'error' :
                     severity === ErrorSeverity.ERROR ? 'error' :
                     severity === ErrorSeverity.WARNING ? 'warn' : 'info';

    console[logMethod]('Theo Error:', {
      message: error.message,
      code: error.code,
      type: error.type,
      severity,
      category,
      context
    });
  }

  /**
   * Show toast notification
   */
  private showToast(
    message: string,
    severity: ErrorSeverity,
    recoverable: boolean,
    retryable: boolean
  ): void {
    const toastOptions = {
      duration: severity === ErrorSeverity.CRITICAL ? 10000 : 5000,
    };

    switch (severity) {
      case ErrorSeverity.INFO:
        toast.info(message, toastOptions);
        break;
      case ErrorSeverity.WARNING:
        toast.warning(message, toastOptions);
        break;
      case ErrorSeverity.ERROR:
      case ErrorSeverity.CRITICAL:
        toast.error(message, toastOptions);
        break;
    }
  }

  /**
   * Handle critical errors that may require app-level recovery
   */
  private handleCriticalError(error: any, context?: ErrorContext): void {
    console.error('CRITICAL ERROR in Theo:', error, context);
    
    // Could implement app-level recovery strategies here:
    // - Force logout on auth system failure
    // - Redirect to error page on critical system failure
    // - Clear corrupted state
    // - Send error reports to monitoring service
    
    // For now, just ensure the error is prominently logged
    if (typeof window !== 'undefined' && 'localStorage' in window) {
      try {
        const criticalErrors = JSON.parse(localStorage.getItem('theo_critical_errors') || '[]');
        criticalErrors.push({
          timestamp: new Date().toISOString(),
          error: {
            message: error.message,
            code: error.code,
            type: error.type,
            status: error.status
          },
          context
        });
        
        // Keep only last 10 critical errors
        const trimmedErrors = criticalErrors.slice(-10);
        localStorage.setItem('theo_critical_errors', JSON.stringify(trimmedErrors));
      } catch (storageError) {
        console.error('Failed to log critical error to localStorage:', storageError);
      }
    }
  }

  /**
   * Get error log for debugging
   */
  getErrorLog(): typeof this.errorLog {
    return [...this.errorLog];
  }

  /**
   * Clear error log
   */
  clearErrorLog(): void {
    this.errorLog = [];
  }

  /**
   * Export error log as JSON
   */
  exportErrorLog(): string {
    return JSON.stringify(this.errorLog, null, 2);
  }

  /**
   * Check if error is retryable
   */
  isRetryable(error: any): boolean {
    const parsed = this.parseError(error);
    
    // Network errors are usually retryable
    if (this.categorizeError(parsed) === ErrorCategory.NETWORK) {
      return true;
    }
    
    // Server errors (5xx) are retryable
    if (parsed.status && parsed.status >= 500) {
      return true;
    }
    
    // Specific retryable error types
    const retryableTypes = ['timeout', 'server_unavailable', 'rate_limited'];
    return retryableTypes.some(type => 
      parsed.type.includes(type) || parsed.code.includes(type)
    );
  }

  /**
   * Get retry delay based on error type
   */
  getRetryDelay(error: any, attempt: number = 1): number {
    const parsed = this.parseError(error);
    
    // Exponential backoff for most errors
    const baseDelay = 1000; // 1 second
    const maxDelay = 30000; // 30 seconds
    
    let delay = Math.min(baseDelay * Math.pow(2, attempt - 1), maxDelay);
    
    // Rate limiting errors need longer delays
    if (parsed.type.includes('rate_limit') || parsed.code.includes('rate_limit')) {
      delay = Math.max(delay, 5000); // Minimum 5 seconds
    }
    
    return delay;
  }
}

// ============================================================================
// EXPORT SINGLETON
// ============================================================================

export const errorHandler = new ErrorHandler();

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Quick error handling for common scenarios
 */
export const handleError = (error: any, context?: ErrorContext) => {
  errorHandler.handle(error, { context });
};

/**
 * Handle error with custom message
 */
export const handleErrorWithMessage = (error: any, message: string, context?: ErrorContext) => {
  errorHandler.handle(error, { customMessage: message, context });
};

/**
 * Handle error without showing toast (silent logging only)
 */
export const handleErrorSilently = (error: any, context?: ErrorContext) => {
  errorHandler.handle(error, { showToast: false, context });
};

/**
 * Handle critical error
 */
export const handleCriticalError = (error: any, context?: ErrorContext) => {
  errorHandler.handle(error, { 
    severity: ErrorSeverity.CRITICAL,
    context 
  });
};

export default errorHandler;