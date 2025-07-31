/**
 * Document Store for Theo Frontend
 * 
 * Zustand-based state management for document-related operations including
 * upload progress, document lists, filtering, and real-time job status updates.
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { apiService } from '@/services/api';
import { sseService } from '@/services/sse';
import type {
  Document,
  DocumentUploadResponse,
  DocumentSearchRequest,
  JobStatusUpdate,
  UploadProgress,
  StreamEvent,
  ProcessingStatus,
  DocumentType
} from '@/types/api';

// ============================================================================
// STORE INTERFACES
// ============================================================================

interface UploadState {
  isUploading: boolean;
  progress: UploadProgress | null;
  error: string | null;
  result: DocumentUploadResponse | null;
  jobStatus: JobStatusUpdate | null;
  sseConnected: boolean;
}

interface DocumentFilters {
  search?: string;
  documentType?: DocumentType;
  category?: string;
  processingStatus?: ProcessingStatus;
  dateRange?: {
    from: string;
    to: string;
  };
}

interface PaginationState {
  page: number;
  perPage: number;
  total: number;
  hasNext: boolean;
  hasPrev: boolean;
}

interface DocumentStoreState {
  // Document list state
  documents: Document[];
  loading: boolean;
  error: string | null;
  filters: DocumentFilters;
  pagination: PaginationState;
  selectedDocuments: Set<string>;

  // Upload state
  upload: UploadState;

  // Job tracking
  activeJobs: Map<string, JobStatusUpdate>;
  
  // Actions
  loadDocuments: (refresh?: boolean) => Promise<void>;
  searchDocuments: (filters: DocumentFilters) => Promise<void>;
  setFilters: (filters: Partial<DocumentFilters>) => void;
  clearFilters: () => void;
  
  // Pagination actions
  setPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  goToNextPage: () => void;
  goToPreviousPage: () => void;
  
  // Document selection
  selectDocument: (documentId: string) => void;
  deselectDocument: (documentId: string) => void;
  selectAllDocuments: () => void;
  clearSelection: () => void;
  toggleDocumentSelection: (documentId: string) => void;
  
  // Upload actions
  uploadDocument: (
    file: File,
    documentType: DocumentType,
    category?: string,
    useStreaming?: boolean
  ) => Promise<DocumentUploadResponse>;
  clearUploadState: () => void;
  
  // Job status actions
  connectToJobStatus: (jobId: string) => void;
  disconnectFromJobStatus: () => void;
  updateJobStatus: (jobId: string, status: JobStatusUpdate) => void;
  
  // Document management
  deleteDocument: (documentId: string) => Promise<void>;
  deleteSelectedDocuments: () => Promise<{ successful: string[]; failed: string[] }>;
  reprocessDocument: (documentId: string) => Promise<void>;
  
  // Utility actions
  refreshDocument: (documentId: string) => Promise<void>;
  getDocumentById: (documentId: string) => Document | undefined;
  resetStore: () => void;
}

// ============================================================================
// INITIAL STATE
// ============================================================================

const initialUploadState: UploadState = {
  isUploading: false,
  progress: null,
  error: null,
  result: null,
  jobStatus: null,
  sseConnected: false,
};

const initialPagination: PaginationState = {
  page: 1,
  perPage: 20,
  total: 0,
  hasNext: false,
  hasPrev: false,
};

const initialFilters: DocumentFilters = {};

// ============================================================================
// DOCUMENT STORE
// ============================================================================

export const useDocumentStore = create<DocumentStoreState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    documents: [],
    loading: false,
    error: null,
    filters: initialFilters,
    pagination: initialPagination,
    selectedDocuments: new Set(),
    upload: initialUploadState,
    activeJobs: new Map(),

    // ========================================================================
    // DOCUMENT LOADING AND SEARCHING
    // ========================================================================

    loadDocuments: async (refresh = false) => {
      const state = get();
      
      if (state.loading && !refresh) return;

      set({ loading: true, error: null });

      try {
        const searchRequest: DocumentSearchRequest = {
          ...state.filters,
          limit: state.pagination.perPage,
          offset: (state.pagination.page - 1) * state.pagination.perPage,
        };

        const response = await apiService.searchDocuments(searchRequest);

        set({
          documents: response.documents,
          pagination: {
            ...state.pagination,
            total: response.pagination.total,
            hasNext: response.pagination.page < response.pagination.pages,
            hasPrev: response.pagination.page > 1,
          },
          loading: false,
        });
      } catch (error) {
        set({
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to load documents',
        });
      }
    },

    searchDocuments: async (filters: DocumentFilters) => {
      set({
        filters,
        pagination: { ...initialPagination }, // Reset to first page
      });
      
      await get().loadDocuments();
    },

    setFilters: (newFilters: Partial<DocumentFilters>) => {
      set((state) => ({
        filters: { ...state.filters, ...newFilters },
        pagination: { ...state.pagination, page: 1 }, // Reset to first page
      }));
    },

    clearFilters: () => {
      set({
        filters: initialFilters,
        pagination: { ...initialPagination },
      });
    },

    // ========================================================================
    // PAGINATION
    // ========================================================================

    setPage: (page: number) => {
      set((state) => ({
        pagination: { ...state.pagination, page },
      }));
      get().loadDocuments();
    },

    setPerPage: (perPage: number) => {
      set((state) => ({
        pagination: { ...state.pagination, perPage, page: 1 },
      }));
      get().loadDocuments();
    },

    goToNextPage: () => {
      const { pagination } = get();
      if (pagination.hasNext) {
        get().setPage(pagination.page + 1);
      }
    },

    goToPreviousPage: () => {
      const { pagination } = get();
      if (pagination.hasPrev) {
        get().setPage(pagination.page - 1);
      }
    },

    // ========================================================================
    // DOCUMENT SELECTION
    // ========================================================================

    selectDocument: (documentId: string) => {
      set((state) => ({
        selectedDocuments: new Set([...state.selectedDocuments, documentId]),
      }));
    },

    deselectDocument: (documentId: string) => {
      set((state) => {
        const newSelection = new Set(state.selectedDocuments);
        newSelection.delete(documentId);
        return { selectedDocuments: newSelection };
      });
    },

    selectAllDocuments: () => {
      set((state) => ({
        selectedDocuments: new Set(state.documents.map(doc => doc.id)),
      }));
    },

    clearSelection: () => {
      set({ selectedDocuments: new Set() });
    },

    toggleDocumentSelection: (documentId: string) => {
      const { selectedDocuments } = get();
      if (selectedDocuments.has(documentId)) {
        get().deselectDocument(documentId);
      } else {
        get().selectDocument(documentId);
      }
    },

    // ========================================================================
    // UPLOAD OPERATIONS
    // ========================================================================

    uploadDocument: async (
      file: File,
      documentType: DocumentType,
      category?: string,
      useStreaming = false
    ): Promise<DocumentUploadResponse> => {
      set((state) => ({
        upload: {
          ...state.upload,
          isUploading: true,
          progress: null,
          error: null,
          result: null,
          jobStatus: null,
        },
      }));

      try {
        let result: DocumentUploadResponse;

        if (useStreaming) {
          result = await apiService.uploadDocumentWithStream(
            file,
            documentType,
            category,
            (event: StreamEvent) => {
              console.log('Upload stream event:', event);
              // Handle streaming events here if needed
            }
          );
        } else {
          result = await apiService.uploadDocument(
            file,
            documentType,
            category,
            (progress: UploadProgress) => {
              set((state) => ({
                upload: {
                  ...state.upload,
                  progress,
                },
              }));
            }
          );
        }

        set((state) => ({
          upload: {
            ...state.upload,
            result,
            isUploading: false,
          },
        }));

        // Connect to job status updates if job ID is available
        if (result.jobId) {
          get().connectToJobStatus(result.jobId);
        }

        // Refresh document list
        get().loadDocuments(true);

        return result;
      } catch (error) {
        set((state) => ({
          upload: {
            ...state.upload,
            isUploading: false,
            error: error instanceof Error ? error.message : 'Upload failed',
          },
        }));
        throw error;
      }
    },

    clearUploadState: () => {
      set({ upload: initialUploadState });
      get().disconnectFromJobStatus();
    },

    // ========================================================================
    // JOB STATUS TRACKING
    // ========================================================================

    connectToJobStatus: (jobId: string) => {
      const { authService } = require('@/services/authService');
      const token = authService.getToken();

      if (!token) {
        console.error('No authentication token available for SSE connection');
        return;
      }

      sseService.connect(jobId, token, {
        onMessage: (update: JobStatusUpdate) => {
          get().updateJobStatus(jobId, update);
          
          // Update upload state if this is the current upload
          set((state) => ({
            upload: {
              ...state.upload,
              jobStatus: update,
            },
          }));
        },
        onError: (error: Error) => {
          console.error('SSE connection error:', error);
          set((state) => ({
            upload: {
              ...state.upload,
              sseConnected: false,
            },
          }));
        },
        onOpen: () => {
          console.log('SSE connection opened');
          set((state) => ({
            upload: {
              ...state.upload,
              sseConnected: true,
            },
          }));
        },
        onClose: () => {
          console.log('SSE connection closed');
          set((state) => ({
            upload: {
              ...state.upload,
              sseConnected: false,
            },
          }));
        },
        reconnectAttempts: 3,
        reconnectDelay: 2000,
      });
    },

    disconnectFromJobStatus: () => {
      sseService.cleanup();
      set((state) => ({
        upload: {
          ...state.upload,
          sseConnected: false,
        },
      }));
    },

    updateJobStatus: (jobId: string, status: JobStatusUpdate) => {
      set((state) => {
        const newActiveJobs = new Map(state.activeJobs);
        newActiveJobs.set(jobId, status);
        return { activeJobs: newActiveJobs };
      });

      // If job is completed, refresh the document list
      if (status.status === 'completed') {
        setTimeout(() => {
          get().loadDocuments(true);
        }, 1000); // Small delay to ensure backend is updated
      }
    },

    // ========================================================================
    // DOCUMENT MANAGEMENT
    // ========================================================================

    deleteDocument: async (documentId: string) => {
      try {
        await apiService.deleteDocument(documentId);
        
        // Remove from local state
        set((state) => ({
          documents: state.documents.filter(doc => doc.id !== documentId),
          selectedDocuments: new Set([...state.selectedDocuments].filter(id => id !== documentId)),
        }));
        
        // Refresh to get accurate pagination
        get().loadDocuments(true);
      } catch (error) {
        throw error;
      }
    },

    deleteSelectedDocuments: async () => {
      const { selectedDocuments } = get();
      const successful: string[] = [];
      const failed: string[] = [];

      for (const documentId of selectedDocuments) {
        try {
          await get().deleteDocument(documentId);
          successful.push(documentId);
        } catch (error) {
          failed.push(documentId);
          console.error(`Failed to delete document ${documentId}:`, error);
        }
      }

      // Clear selection after operation
      get().clearSelection();

      return { successful, failed };
    },

    reprocessDocument: async (documentId: string) => {
      try {
        const jobStatus = await apiService.reprocessDocument(documentId);
        
        // Track the reprocessing job
        get().updateJobStatus(jobStatus.job_id, {
          status: jobStatus.status,
          progress: jobStatus.progress,
          step: jobStatus.step,
          job_id: jobStatus.job_id,
        });

        // Update document status in local state
        set((state) => ({
          documents: state.documents.map(doc =>
            doc.id === documentId
              ? { ...doc, processing_status: 'queued', job_id: jobStatus.job_id }
              : doc
          ),
        }));
      } catch (error) {
        throw error;
      }
    },

    // ========================================================================
    // UTILITY METHODS
    // ========================================================================

    refreshDocument: async (documentId: string) => {
      try {
        const document = await apiService.getDocument(documentId);
        
        set((state) => ({
          documents: state.documents.map(doc =>
            doc.id === documentId ? document : doc
          ),
        }));
      } catch (error) {
        console.error(`Failed to refresh document ${documentId}:`, error);
      }
    },

    getDocumentById: (documentId: string) => {
      return get().documents.find(doc => doc.id === documentId);
    },

    resetStore: () => {
      get().disconnectFromJobStatus();
      set({
        documents: [],
        loading: false,
        error: null,
        filters: initialFilters,
        pagination: initialPagination,
        selectedDocuments: new Set(),
        upload: initialUploadState,
        activeJobs: new Map(),
      });
    },
  }))
);

// ============================================================================
// STORE SELECTORS
// ============================================================================

// Computed selectors for common operations
export const useDocumentSelectors = () => {
  const store = useDocumentStore();
  
  return {
    // Document list selectors
    hasDocuments: store.documents.length > 0,
    totalDocuments: store.pagination.total,
    isLoading: store.loading,
    hasError: !!store.error,
    
    // Selection selectors
    selectedCount: store.selectedDocuments.size,
    hasSelection: store.selectedDocuments.size > 0,
    allSelected: store.documents.length > 0 && store.selectedDocuments.size === store.documents.length,
    
    // Upload selectors
    isUploading: store.upload.isUploading,
    uploadProgress: store.upload.progress?.percentage || 0,
    hasUploadError: !!store.upload.error,
    uploadComplete: !!store.upload.result,
    
    // Job status selectors
    activeJobCount: store.activeJobs.size,
    hasActiveJobs: store.activeJobs.size > 0,
    
    // Filter selectors
    hasFilters: Object.keys(store.filters).length > 0,
    
    // Pagination selectors
    canGoNext: store.pagination.hasNext,
    canGoPrev: store.pagination.hasPrev,
    currentPage: store.pagination.page,
    totalPages: Math.ceil(store.pagination.total / store.pagination.perPage),
  };
};

// Export store for direct access
export default useDocumentStore;