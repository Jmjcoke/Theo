/**
 * Core API Type Definitions for Theo Theological Research System
 * 
 * Comprehensive TypeScript interfaces that map to the FastAPI backend models
 * and provide type safety across the entire frontend application.
 */

// ============================================================================
// AUTHENTICATION TYPES
// ============================================================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  user_role: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username?: string;
}

export interface RegisterResponse {
  message: string;
  user_id: string;
}

export interface User {
  id: string;
  email: string;
  role: 'user' | 'admin' | 'pending';
  username?: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

// ============================================================================
// DOCUMENT TYPES
// ============================================================================

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  document_type: 'biblical' | 'theological';
  category?: string;
  file_size: number;
  mime_type: string;
  processing_status: 'queued' | 'processing' | 'completed' | 'failed' | 'error';
  uploaded_at: string;
  processed_at?: string;
  uploaded_by: string;
  job_id?: string;
  error_message?: string;
  chunk_count?: number;
  metadata?: DocumentMetadata;
}

export interface DocumentMetadata {
  title?: string;
  author?: string;
  subject?: string;
  pages?: number;
  word_count?: number;
  theological_topics?: string[];
  biblical_references?: string[];
  language?: string;
  publication_year?: number;
  publisher?: string;
}

export interface DocumentUploadRequest {
  file: File;
  documentType: 'biblical' | 'theological';
  category?: string;
}

export interface DocumentUploadResponse {
  documentId: string;
  filename: string;
  documentType: string;
  processingStatus: string;
  uploadedAt: string;
  jobId: string;
}

export interface DocumentSearchRequest {
  query?: string;
  document_type?: 'biblical' | 'theological';
  category?: string;
  processing_status?: string;
  uploaded_by?: string;
  limit?: number;
  offset?: number;
}

export interface DocumentSearchResponse {
  documents: Document[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

// ============================================================================
// CHAT TYPES
// ============================================================================

export interface ChatRequest {
  message: string;
  sessionId: string;
  context?: string;
  useAdvancedPipeline?: boolean;
}

export interface DocumentSource {
  documentId: string;
  title: string;
  excerpt: string;
  relevance: number;
  citation?: string;
}

export interface ChatResponse {
  response: string;
  confidence: number;
  sources: DocumentSource[];
  processingTime: number;
  sessionId: string;
  messageId: string;
  intent: string;
  intentConfidence: number;
  advancedPipeline?: {
    reranking_applied: boolean;
    hermeneutics_applied: boolean;
    hermeneutics_version: string;
    pipeline_stages: {
      total_latency: number;
    };
  };
}

export interface ChatHistory {
  id: string;
  user_id: string;
  message: string;
  response: string;
  sources: DocumentSource[];
  created_at: string;
  pipeline_used: 'basic' | 'advanced';
}

// ============================================================================
// JOB QUEUE & SSE TYPES
// ============================================================================

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'error';
  progress: number; // 0.0 to 1.0
  step: string;
  message?: string;
  started_at?: string;
  completed_at?: string;
  error_details?: string;
  document_id?: string;
}

export interface JobStatusUpdate {
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'error';
  progress: number;
  step: string;
  message?: string;
  timestamp?: string;
  job_id?: string;
  document_id?: string;
}

export interface SSEEventHandlers {
  onMessage: (update: JobStatusUpdate) => void;
  onError: (error: Error) => void;
  onOpen: () => void;
  onClose: () => void;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

// ============================================================================
// ADMIN TYPES
// ============================================================================

export interface DashboardMetrics {
  users: {
    total: number;
    pending: number;
    approved: number;
    active_today: number;
  };
  documents: {
    total: number;
    processing: number;
    completed: number;
    failed: number;
    uploaded_today: number;
  };
  jobs: {
    queued: number;
    processing: number;
    completed_today: number;
    failed_today: number;
  };
  system: {
    uptime: string;
    memory_usage: number;
    disk_usage: number;
    redis_connected: boolean;
    database_connected: boolean;
  };
}

export interface UserManagementRequest {
  action: 'approve' | 'suspend' | 'delete' | 'promote' | 'demote';
  user_id: string;
  reason?: string;
}

export interface UserManagementResponse {
  success: boolean;
  message: string;
  user: User;
}

export interface SystemConfiguration {
  max_file_size: number;
  allowed_file_types: string[];
  max_upload_rate: number;
  max_concurrent_jobs: number;
  rag_settings: {
    max_results: number;
    similarity_threshold: number;
    use_reranking: boolean;
    hermeneutics_filtering: boolean;
  };
  ai_settings: {
    model: string;
    temperature: number;
    max_tokens: number;
  };
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    database: boolean;
    redis: boolean;
    openai: boolean;
    supabase: boolean;
  };
  metrics: {
    response_time: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
  };
  last_check: string;
}

// ============================================================================
// EXPORT TYPES
// ============================================================================

export interface ExportRequest {
  format: 'pdf' | 'markdown' | 'docx';
  content: string;
  title?: string;
  author?: string;
  include_sources?: boolean;
  template?: string;
}

export interface ExportResponse {
  download_url: string;
  filename: string;
  format: string;
  expires_at: string;
  file_size: number;
}

// ============================================================================
// API RESPONSE WRAPPERS
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
}

export interface ApiError {
  message: string;
  type: string;
  code: string;
  status?: number;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// ============================================================================
// UPLOAD PROGRESS TYPES
// ============================================================================

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface StreamEvent {
  event: string;
  data: any;
  timestamp: string;
}

// ============================================================================
// SEARCH AND FILTER TYPES
// ============================================================================

export interface SearchFilters {
  document_type?: 'biblical' | 'theological';
  category?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  user_id?: string;
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

export type RoleType = 'user' | 'admin' | 'pending';

export type ProcessingStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'error';

export type DocumentType = 'biblical' | 'theological';

export type PipelineType = 'basic' | 'advanced';