/**
 * Admin Service for Theo Theological Research System
 * 
 * Specialized service for administrative operations including user management,
 * system configuration, document oversight, and dashboard analytics.
 */

import { apiService } from './api';
import type {
  DashboardMetrics,
  User,
  UserManagementRequest,
  UserManagementResponse,
  SystemConfiguration,
  SystemHealth,
  Document,
  DocumentSearchRequest,
  JobStatus,
  PaginatedResponse
} from '@/types/api';

/**
 * Admin dashboard refresh configuration
 */
interface DashboardConfig {
  refreshInterval?: number; // milliseconds
  autoRefresh?: boolean;
  metricsHistorySize?: number;
}

/**
 * Admin service for comprehensive system management
 */
class AdminService {
  private dashboardConfig: DashboardConfig;
  private refreshTimer: number | null = null;
  private metricsHistory: Array<{ timestamp: string; metrics: DashboardMetrics }> = [];

  constructor(config: DashboardConfig = {}) {
    this.dashboardConfig = {
      refreshInterval: 30000, // 30 seconds
      autoRefresh: false,
      metricsHistorySize: 100,
      ...config
    };
  }

  // ============================================================================
  // DASHBOARD METRICS
  // ============================================================================

  /**
   * Get current dashboard metrics
   */
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    try {
      const metrics = await apiService.getDashboardMetrics();
      
      // Store in history
      this.addMetricsToHistory(metrics);
      
      return metrics;
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      throw error;
    }
  }

  /**
   * Start auto-refresh of dashboard metrics
   */
  startDashboardAutoRefresh(callback: (metrics: DashboardMetrics) => void): void {
    this.stopDashboardAutoRefresh();

    if (this.dashboardConfig.autoRefresh) {
      this.refreshTimer = window.setInterval(async () => {
        try {
          const metrics = await this.getDashboardMetrics();
          callback(metrics);
        } catch (error) {
          console.error('Auto-refresh failed:', error);
        }
      }, this.dashboardConfig.refreshInterval);
    }
  }

  /**
   * Stop auto-refresh
   */
  stopDashboardAutoRefresh(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Get metrics history for trending
   */
  getMetricsHistory(): Array<{ timestamp: string; metrics: DashboardMetrics }> {
    return [...this.metricsHistory];
  }

  /**
   * Add metrics to history with size limit
   */
  private addMetricsToHistory(metrics: DashboardMetrics): void {
    this.metricsHistory.push({
      timestamp: new Date().toISOString(),
      metrics
    });

    // Trim history to configured size
    if (this.metricsHistory.length > this.dashboardConfig.metricsHistorySize!) {
      this.metricsHistory = this.metricsHistory.slice(-this.dashboardConfig.metricsHistorySize!);
    }
  }

  // ============================================================================
  // USER MANAGEMENT
  // ============================================================================

  /**
   * Get all users with pagination and filtering
   */
  async getUsers(
    page: number = 1,
    perPage: number = 50,
    filters: {
      status?: string;
      role?: string;
      search?: string;
    } = {}
  ): Promise<PaginatedResponse<User>> {
    return apiService.getUsers(page, perPage, filters.status);
  }

  /**
   * Approve pending user
   */
  async approveUser(userId: string, reason?: string): Promise<UserManagementResponse> {
    return this.manageUser({
      action: 'approve',
      user_id: userId,
      reason
    });
  }

  /**
   * Suspend user account
   */
  async suspendUser(userId: string, reason?: string): Promise<UserManagementResponse> {
    return this.manageUser({
      action: 'suspend',
      user_id: userId,
      reason
    });
  }

  /**
   * Delete user account
   */
  async deleteUser(userId: string, reason?: string): Promise<UserManagementResponse> {
    return this.manageUser({
      action: 'delete',
      user_id: userId,
      reason
    });
  }

  /**
   * Promote user to admin
   */
  async promoteUser(userId: string, reason?: string): Promise<UserManagementResponse> {
    return this.manageUser({
      action: 'promote',
      user_id: userId,
      reason
    });
  }

  /**
   * Demote user from admin
   */
  async demoteUser(userId: string, reason?: string): Promise<UserManagementResponse> {
    return this.manageUser({
      action: 'demote',
      user_id: userId,
      reason
    });
  }

  /**
   * Generic user management method
   */
  private async manageUser(request: UserManagementRequest): Promise<UserManagementResponse> {
    return apiService.manageUser(request);
  }

  /**
   * Bulk user operations
   */
  async bulkUserOperation(
    userIds: string[],
    action: 'approve' | 'suspend' | 'delete',
    reason?: string
  ): Promise<UserManagementResponse[]> {
    const results: UserManagementResponse[] = [];
    
    for (const userId of userIds) {
      try {
        const result = await this.manageUser({
          action,
          user_id: userId,
          reason
        });
        results.push(result);
      } catch (error) {
        console.error(`Bulk operation failed for user ${userId}:`, error);
        results.push({
          success: false,
          message: error instanceof Error ? error.message : 'Operation failed',
          user: { id: userId } as User
        });
      }
    }

    return results;
  }

  // ============================================================================
  // DOCUMENT MANAGEMENT
  // ============================================================================

  /**
   * Get all documents with admin-level filtering
   */
  async getAllDocuments(
    filters: DocumentSearchRequest & {
      include_failed?: boolean;
      include_processing?: boolean;
    } = {}
  ): Promise<{
    documents: Document[];
    total: number;
    processing: number;
    failed: number;
  }> {
    const searchResult = await apiService.searchDocuments(filters);
    
    return {
      documents: searchResult.documents,
      total: searchResult.total,
      processing: searchResult.documents.filter(d => d.processing_status === 'processing').length,
      failed: searchResult.documents.filter(d => d.processing_status === 'failed').length,
    };
  }

  /**
   * Delete multiple documents
   */
  async bulkDeleteDocuments(documentIds: string[]): Promise<{
    successful: string[];
    failed: Array<{ id: string; error: string }>;
  }> {
    const successful: string[] = [];
    const failed: Array<{ id: string; error: string }> = [];

    for (const documentId of documentIds) {
      try {
        await apiService.deleteDocument(documentId);
        successful.push(documentId);
      } catch (error) {
        failed.push({
          id: documentId,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }

    return { successful, failed };
  }

  /**
   * Reprocess multiple documents
   */
  async bulkReprocessDocuments(documentIds: string[]): Promise<{
    successful: Array<{ id: string; jobId: string }>;
    failed: Array<{ id: string; error: string }>;
  }> {
    const successful: Array<{ id: string; jobId: string }> = [];
    const failed: Array<{ id: string; error: string }> = [];

    for (const documentId of documentIds) {
      try {
        const jobStatus = await apiService.reprocessDocument(documentId);
        successful.push({ id: documentId, jobId: jobStatus.job_id });
      } catch (error) {
        failed.push({
          id: documentId,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }

    return { successful, failed };
  }

  /**
   * Get document processing statistics
   */
  async getDocumentStats(): Promise<{
    byType: Record<string, number>;
    byStatus: Record<string, number>;
    byUploader: Record<string, number>;
    processingTrends: Array<{ date: string; count: number }>;
  }> {
    const { documents } = await this.getAllDocuments({ limit: 10000 });
    
    const byType: Record<string, number> = {};
    const byStatus: Record<string, number> = {};
    const byUploader: Record<string, number> = {};
    const processingTrends: Array<{ date: string; count: number }> = [];

    documents.forEach(doc => {
      // By type
      byType[doc.document_type] = (byType[doc.document_type] || 0) + 1;
      
      // By status
      byStatus[doc.processing_status] = (byStatus[doc.processing_status] || 0) + 1;
      
      // By uploader
      byUploader[doc.uploaded_by] = (byUploader[doc.uploaded_by] || 0) + 1;
      
      // Processing trends (by upload date)
      const uploadDate = new Date(doc.uploaded_at).toISOString().split('T')[0];
      const existing = processingTrends.find(t => t.date === uploadDate);
      if (existing) {
        existing.count++;
      } else {
        processingTrends.push({ date: uploadDate, count: 1 });
      }
    });

    // Sort trends by date
    processingTrends.sort((a, b) => a.date.localeCompare(b.date));

    return { byType, byStatus, byUploader, processingTrends };
  }

  // ============================================================================
  // JOB QUEUE MANAGEMENT
  // ============================================================================

  /**
   * Get all jobs with admin visibility
   */
  async getAllJobs(status?: string): Promise<JobStatus[]> {
    return apiService.getJobs(status);
  }

  /**
   * Cancel multiple jobs
   */
  async bulkCancelJobs(jobIds: string[]): Promise<{
    successful: string[];
    failed: Array<{ id: string; error: string }>;
  }> {
    const successful: string[] = [];
    const failed: Array<{ id: string; error: string }> = [];

    for (const jobId of jobIds) {
      try {
        await apiService.cancelJob(jobId);
        successful.push(jobId);
      } catch (error) {
        failed.push({
          id: jobId,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }

    return { successful, failed };
  }

  /**
   * Get job queue statistics
   */
  async getJobQueueStats(): Promise<{
    byStatus: Record<string, number>;
    avgProcessingTime: number;
    queueBacklog: number;
    failureRate: number;
  }> {
    const jobs = await this.getAllJobs();
    
    const byStatus: Record<string, number> = {};
    let totalProcessingTime = 0;
    let completedJobs = 0;
    let failedJobs = 0;

    jobs.forEach(job => {
      byStatus[job.status] = (byStatus[job.status] || 0) + 1;
      
      if (job.status === 'completed' && job.started_at && job.completed_at) {
        const processingTime = new Date(job.completed_at).getTime() - new Date(job.started_at).getTime();
        totalProcessingTime += processingTime;
        completedJobs++;
      }
      
      if (job.status === 'failed' || job.status === 'error') {
        failedJobs++;
      }
    });

    const avgProcessingTime = completedJobs > 0 ? totalProcessingTime / completedJobs : 0;
    const queueBacklog = (byStatus.queued || 0) + (byStatus.processing || 0);
    const totalJobs = jobs.length;
    const failureRate = totalJobs > 0 ? failedJobs / totalJobs : 0;

    return {
      byStatus,
      avgProcessingTime: Math.round(avgProcessingTime / 1000), // Convert to seconds
      queueBacklog,
      failureRate: Math.round(failureRate * 100) / 100 // Percentage with 2 decimal places
    };
  }

  // ============================================================================
  // SYSTEM CONFIGURATION
  // ============================================================================

  /**
   * Get system configuration
   */
  async getSystemConfiguration(): Promise<SystemConfiguration> {
    return apiService.getSystemConfiguration();
  }

  /**
   * Update system configuration
   */
  async updateSystemConfiguration(
    config: Partial<SystemConfiguration>
  ): Promise<SystemConfiguration> {
    return apiService.updateSystemConfiguration(config);
  }

  /**
   * Get system health status
   */
  async getSystemHealth(): Promise<SystemHealth> {
    return apiService.getSystemHealth();
  }

  /**
   * Validate configuration changes
   */
  validateConfiguration(config: Partial<SystemConfiguration>): {
    valid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate file size limits
    if (config.max_file_size !== undefined) {
      if (config.max_file_size < 1024 * 1024) { // 1MB minimum
        errors.push('Maximum file size must be at least 1MB');
      }
      if (config.max_file_size > 100 * 1024 * 1024) { // 100MB maximum
        warnings.push('File sizes above 100MB may cause performance issues');
      }
    }

    // Validate concurrent jobs
    if (config.max_concurrent_jobs !== undefined) {
      if (config.max_concurrent_jobs < 1) {
        errors.push('Must allow at least 1 concurrent job');
      }
      if (config.max_concurrent_jobs > 20) {
        warnings.push('High concurrent job limits may overload the system');
      }
    }

    // Validate RAG settings
    if (config.rag_settings) {
      if (config.rag_settings.max_results !== undefined && config.rag_settings.max_results < 1) {
        errors.push('RAG max results must be at least 1');
      }
      if (config.rag_settings.similarity_threshold !== undefined) {
        if (config.rag_settings.similarity_threshold < 0 || config.rag_settings.similarity_threshold > 1) {
          errors.push('Similarity threshold must be between 0 and 1');
        }
      }
    }

    // Validate AI settings
    if (config.ai_settings) {
      if (config.ai_settings.temperature !== undefined) {
        if (config.ai_settings.temperature < 0 || config.ai_settings.temperature > 2) {
          errors.push('AI temperature must be between 0 and 2');
        }
      }
      if (config.ai_settings.max_tokens !== undefined) {
        if (config.ai_settings.max_tokens < 1) {
          errors.push('AI max tokens must be at least 1');
        }
        if (config.ai_settings.max_tokens > 4000) {
          warnings.push('High token limits may increase API costs');
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  // ============================================================================
  // ANALYTICS AND REPORTING
  // ============================================================================

  /**
   * Generate comprehensive system report
   */
  async generateSystemReport(): Promise<{
    generatedAt: string;
    metrics: DashboardMetrics;
    systemHealth: SystemHealth;
    documentStats: any;
    jobQueueStats: any;
    userStats: {
      totalUsers: number;
      activeUsers: number;
      pendingUsers: number;
    };
  }> {
    const [metrics, health, documentStats, jobStats, users] = await Promise.all([
      this.getDashboardMetrics(),
      this.getSystemHealth(),
      this.getDocumentStats(),
      this.getJobQueueStats(),
      this.getUsers(1, 1000) // Get large batch for stats
    ]);

    return {
      generatedAt: new Date().toISOString(),
      metrics,
      systemHealth: health,
      documentStats,
      jobQueueStats: jobStats,
      userStats: {
        totalUsers: users.total,
        activeUsers: users.items.filter(u => u.is_active).length,
        pendingUsers: users.items.filter(u => u.role === 'pending').length,
      }
    };
  }

  // ============================================================================
  // CLEANUP
  // ============================================================================

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.stopDashboardAutoRefresh();
    this.metricsHistory = [];
  }
}

// Export singleton instance
export const adminService = new AdminService();
export default adminService;