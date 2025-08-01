/**
 * TypeScript type definitions for Document Editor Module
 */

export type DocumentType = 'sermon' | 'article' | 'research_paper' | 'lesson_plan' | 'devotional';
export type DocumentStatus = 'draft' | 'published' | 'archived';
export type CitationFormat = 'apa' | 'mla' | 'chicago' | 'turabian';
export type ExportFormat = 'pdf' | 'docx' | 'markdown';
export type CommentStatus = 'active' | 'resolved' | 'deleted';

// Core document interface
export interface EditorDocument {
  id: number;
  user_id: number;
  title: string;
  content: string;
  template_id?: string;
  document_type: DocumentType;
  status: DocumentStatus;
  version: number;
  word_count: number;
  reading_time: number;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Lightweight document summary for lists
export interface EditorDocumentSummary {
  id: number;
  title: string;
  document_type: DocumentType;
  status: DocumentStatus;
  word_count: number;
  reading_time: number;
  created_at: string;
  updated_at: string;
}

// Template interfaces
export interface EditorTemplate {
  id: string;
  name: string;
  description?: string;
  template_content: string;
  document_type: DocumentType;
  is_system: boolean;
  created_by?: number;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface EditorTemplateSummary {
  id: string;
  name: string;
  description?: string;
  document_type: DocumentType;
  is_system: boolean;
}

// Citation interfaces
export interface Citation {
  id: number;
  document_id: number;
  source_id: string;
  citation_text: string;
  position_start?: number;
  position_end?: number;
  citation_format: CitationFormat;
  created_at: string;
}

// Comment interfaces
export interface Comment {
  id: number;
  document_id: number;
  user_id: number;
  parent_comment_id?: number;
  content: string;
  position_start?: number;
  position_end?: number;
  status: CommentStatus;
  created_at: string;
  author_name?: string;
  author_email?: string;
  replies?: Comment[];
}

// Version history
export interface DocumentVersion {
  id: number;
  document_id: number;
  version_number: number;
  content: string;
  change_summary?: string;
  created_at: string;
}

// Export interfaces
export interface ExportRequest {
  format: ExportFormat;
  include_citations?: boolean;
  custom_styling?: Record<string, any>;
}

export interface ExportStatus {
  id: number;
  document_id: number;
  export_format: ExportFormat;
  export_status: 'pending' | 'processing' | 'completed' | 'failed';
  file_path?: string;
  file_size?: number;
  error_message?: string;
  created_at: string;
  download_url?: string;
}

// Request/Response types
export interface CreateDocumentRequest {
  title: string;
  content?: string;
  template_id?: string;
  document_type: DocumentType;
  metadata?: Record<string, any>;
}

export interface UpdateDocumentRequest {
  title?: string;
  content?: string;
  template_id?: string;
  document_type?: DocumentType;
  status?: DocumentStatus;
  metadata?: Record<string, any>;
}

export interface CreateTemplateRequest {
  name: string;
  description?: string;
  template_content: string;
  document_type: DocumentType;
  metadata?: Record<string, any>;
}

export interface ContentTransferRequest {
  source_message_id: string;
  content: string;
  sources?: any[];
  suggested_template?: string;
  title?: string;
}

export interface FormatRequest {
  command: string;
  selected_text?: string;
  selection_start?: number;
  selection_end?: number;
}

export interface CreateCitationRequest {
  source_id: string;
  citation_text: string;
  position_start?: number;
  position_end?: number;
  citation_format?: CitationFormat;
}

export interface CreateCommentRequest {
  content: string;
  parent_comment_id?: number;
  position_start?: number;
  position_end?: number;
}

// Statistics interfaces
export interface DocumentStats {
  total_documents: number;
  documents_by_type: Record<string, number>;
  documents_by_status: Record<string, number>;
  average_word_count: number;
  total_exports: number;
  exports_by_format: Record<string, number>;
}

export interface TemplateStats {
  total_templates: number;
  system_templates: number;
  user_templates: number;
  usage_by_template: Record<string, number>;
  most_popular_template?: string;
}

export interface UserDocumentStats {
  total_documents: number;
  draft_documents: number;
  published_documents: number;
  total_words_written: number;
  average_document_length: number;
  most_used_template?: string;
  recent_activity: Array<{
    type: 'created' | 'updated' | 'exported';
    document_id: number;
    document_title: string;
    timestamp: string;
  }>;
}

// Bulk operations
export interface BulkDocumentOperation {
  document_ids: number[];
  operation: 'delete' | 'archive' | 'publish' | 'change_status';
  parameters?: Record<string, any>;
}

export interface BulkOperationResult {
  successful_ids: number[];
  failed_ids: number[];
  errors: Record<number, string>;
  total_processed: number;
}

// Error interfaces
export interface EditorError {
  error_type: string;
  message: string;
  details?: Record<string, any>;
}

export interface ValidationError extends EditorError {
  field_errors: Record<string, string[]>;
}

// UI State interfaces
export interface EditorUIState {
  isLoading: boolean;
  isSaving: boolean;
  isExporting: boolean;
  autoSaveStatus: 'saved' | 'saving' | 'error';
  selectedTemplate?: string;
  showTemplateSelector: boolean;
  showExportDialog: boolean;
  showCitationPanel: boolean;
  showCommentPanel: boolean;
  showVersionHistory: boolean;
  sidebarOpen: boolean;
  error?: string;
}

// Chat integration interfaces
export interface ChatContentTransfer {
  type: 'chat-content';
  data: {
    message_id: string;
    content: string;
    title?: string;
    sources?: Array<{
      id: string;
      title: string;
      content: string;
      metadata?: Record<string, any>;
    }>;
    suggested_template?: string;
  };
}

// Rich text editor interfaces
export interface EditorSelection {
  start: number;
  end: number;
  text: string;
}

export interface FormatCommand {
  type: 'bold' | 'italic' | 'heading' | 'bullet_list' | 'numbered_list' | 'quote' | 'code';
  selection?: EditorSelection;
  parameters?: Record<string, any>;
}

// Template system interfaces
export interface TemplateVariable {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'date' | 'select';
  required: boolean;
  default?: string;
  options?: string[]; // for select type
}

export interface TemplateMetadata {
  variables?: TemplateVariable[];
  styling?: {
    font_family?: string;
    font_size?: string;
    line_spacing?: string;
    margins?: string;
  };
  export_settings?: {
    default_format?: ExportFormat;
    citation_style?: CitationFormat;
    include_citations?: boolean;
  };
  word_target?: number;
  reading_time_target?: number;
}

// Search interfaces
export interface SearchFilters {
  document_type?: DocumentType;
  status?: DocumentStatus;
  template_id?: string;
  date_range?: {
    start: string;
    end: string;
  };
  word_count_range?: {
    min: number;
    max: number;
  };
}

export interface SearchResult {
  document: EditorDocumentSummary;
  relevance_score: number;
  matched_sections: Array<{
    content: string;
    position: number;
  }>;
}

// Collaboration interfaces (future)
export interface CollaborationState {
  active_users: Array<{
    user_id: number;
    user_name: string;
    cursor_position?: number;
    last_seen: string;
  }>;
  pending_changes: Array<{
    user_id: number;
    change_type: 'insert' | 'delete' | 'format';
    position: number;
    content: string;
    timestamp: string;
  }>;
}

// Export type for the entire module
export type {
  // Re-export all interfaces for convenience
  EditorDocument as Document,
  EditorTemplate as Template,
  Citation,
  Comment,
  DocumentVersion as Version,
  ExportStatus,
  DocumentStats,
  UserDocumentStats,
  BulkOperationResult,
  ChatContentTransfer,
  TemplateMetadata,
  SearchResult,
};