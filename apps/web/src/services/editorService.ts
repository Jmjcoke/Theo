/**
 * Editor Service
 * Handles API communication for document editor functionality
 */

import { apiService } from './api';
import type { 
  EditorDocument, 
  EditorTemplate, 
  CreateDocumentRequest,
  UpdateDocumentRequest,
  ExportRequest,
  ExportStatus,
  DocumentStats,
  Citation
} from '@/types/editor';

export class EditorService {
  private baseUrl = '/api/editor';

  // Document operations
  async getDocuments(filters?: {
    document_type?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<EditorDocument[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }
    
    const url = `${this.baseUrl}/documents${params.toString() ? `?${params}` : ''}`;
    const response = await apiService.get(url);
    return response.data;
  }

  async getDocument(id: number): Promise<EditorDocument> {
    const response = await apiService.get(`${this.baseUrl}/documents/${id}`);
    return response.data;
  }

  async createDocument(document: CreateDocumentRequest): Promise<EditorDocument> {
    const response = await apiService.post(`${this.baseUrl}/documents`, document);
    return response.data;
  }

  async updateDocument(id: number, document: UpdateDocumentRequest): Promise<EditorDocument> {
    const response = await apiService.put(`${this.baseUrl}/documents/${id}`, document);
    return response.data;
  }

  async deleteDocument(id: number): Promise<void> {
    await apiService.delete(`${this.baseUrl}/documents/${id}`);
  }

  // Template operations
  async getTemplates(documentType?: string): Promise<EditorTemplate[]> {
    const params = documentType ? `?document_type=${documentType}` : '';
    const response = await apiService.get(`${this.baseUrl}/templates${params}`);
    return response.data;
  }

  async getTemplate(id: string): Promise<EditorTemplate> {
    const response = await apiService.get(`${this.baseUrl}/templates/${id}`);
    return response.data;
  }

  async createTemplate(template: {
    name: string;
    description?: string;
    template_content: string;
    document_type: string;
    metadata?: any;
  }): Promise<EditorTemplate> {
    const response = await apiService.post(`${this.baseUrl}/templates`, template);
    return response.data;
  }

  // Content processing
  async formatDocument(documentId: number, formatRequest: {
    command: string;
    selected_text?: string;
    selection_start?: number;
    selection_end?: number;
  }): Promise<{ formatted_content: string; changes: any[] }> {
    const response = await apiService.post(`${this.baseUrl}/documents/${documentId}/format`, formatRequest);
    return response.data;
  }

  async transferChatContent(documentId: number, transfer: {
    source_message_id: string;
    content: string;
    sources?: any[];
    suggested_template?: string;
    title?: string;
  }): Promise<{ success: boolean; citations_added: number }> {
    const response = await apiService.post(`${this.baseUrl}/documents/${documentId}/transfer-content`, transfer);
    return response.data;
  }

  // Export operations
  async exportDocument(
    documentId: number, 
    format: 'pdf' | 'docx' | 'markdown',
    options?: {
      include_citations?: boolean;
      custom_styling?: any;
    }
  ): Promise<{ export_id: number; status: string; message: string }> {
    const params = new URLSearchParams();
    if (options?.include_citations !== undefined) {
      params.append('include_citations', options.include_citations.toString());
    }
    if (options?.custom_styling) {
      params.append('custom_styling', JSON.stringify(options.custom_styling));
    }

    const url = `${this.baseUrl}/documents/${documentId}/export/${format}${params.toString() ? `?${params}` : ''}`;
    const response = await apiService.post(url);
    return response.data;
  }

  async getExportStatus(exportId: number): Promise<ExportStatus> {
    const response = await apiService.get(`${this.baseUrl}/exports/${exportId}/status`);
    return response.data;
  }

  async downloadExport(exportId: number): Promise<Blob> {
    const response = await apiService.get(`${this.baseUrl}/exports/${exportId}/download`, {
      responseType: 'blob'
    });
    return response.data;
  }

  // Citation management
  async getCitations(documentId: number): Promise<Citation[]> {
    const response = await apiService.get(`${this.baseUrl}/documents/${documentId}/citations`);
    return response.data;
  }

  async addCitation(documentId: number, citation: {
    source_id: string;
    citation_text: string;
    position_start?: number;
    position_end?: number;
    citation_format?: string;
  }): Promise<Citation> {
    const response = await apiService.post(`${this.baseUrl}/documents/${documentId}/citations`, citation);
    return response.data;
  }

  async deleteCitation(citationId: number): Promise<void> {
    await apiService.delete(`${this.baseUrl}/citations/${citationId}`);
  }

  // Version history
  async getDocumentVersions(documentId: number, limit = 10): Promise<any[]> {
    const response = await apiService.get(`${this.baseUrl}/documents/${documentId}/versions?limit=${limit}`);
    return response.data;
  }

  async restoreDocumentVersion(documentId: number, versionId: number): Promise<{ message: string }> {
    const response = await apiService.post(`${this.baseUrl}/documents/${documentId}/restore/${versionId}`);
    return response.data;
  }

  // Statistics
  async getUserStats(): Promise<DocumentStats> {
    const response = await apiService.get(`${this.baseUrl}/stats/user`);
    return response.data;
  }

  // Bulk operations
  async bulkDocumentOperation(operation: {
    document_ids: number[];
    operation: 'delete' | 'archive' | 'publish' | 'change_status';
    parameters?: any;
  }): Promise<{
    successful_ids: number[];
    failed_ids: number[];
    errors: Record<number, string>;
    total_processed: number;
  }> {
    const response = await apiService.post(`${this.baseUrl}/documents/bulk`, operation);
    return response.data;
  }

  // Health check
  async checkHealth(): Promise<{
    status: string;
    services: Record<string, string>;
    timestamp: string;
  }> {
    const response = await apiService.get(`${this.baseUrl}/health`);
    return response.data;
  }

  // Utility methods
  validateDocumentTitle(title: string): { valid: boolean; error?: string } {
    if (!title || title.trim().length === 0) {
      return { valid: false, error: 'Title is required' };
    }
    if (title.length > 255) {
      return { valid: false, error: 'Title must be less than 255 characters' };
    }
    return { valid: true };
  }

  validateDocumentContent(content: string): { valid: boolean; error?: string } {
    if (content.length > 100000) {
      return { valid: false, error: 'Content must be less than 100,000 characters' };
    }
    return { valid: true };
  }

  calculateReadingTime(content: string): number {
    const wordsPerMinute = 200;
    const words = content.trim().split(/\s+/).filter(word => word.length > 0);
    return Math.ceil(words.length / wordsPerMinute);
  }

  calculateWordCount(content: string): number {
    return content.trim().split(/\s+/).filter(word => word.length > 0).length;
  }

  // Content formatting utilities
  formatCitation(citation: Citation, format: 'apa' | 'mla' | 'chicago' | 'turabian' = 'apa'): string {
    // This would be expanded with proper citation formatting logic
    switch (format) {
      case 'apa':
        return `(${citation.source_id})`;
      case 'mla':
        return `(${citation.source_id})`;
      case 'chicago':
        return `¹`;
      case 'turabian':
        return `¹`;
      default:
        return citation.citation_text;
    }
  }

  // Template utilities
  applyTemplate(templateContent: string, variables: Record<string, string> = {}): string {
    let content = templateContent;
    
    // Replace placeholders with actual values
    Object.entries(variables).forEach(([key, value]) => {
      const placeholder = new RegExp(`\\[${key}\\]`, 'g');
      content = content.replace(placeholder, value);
    });
    
    return content;
  }

  extractTemplateVariables(templateContent: string): string[] {
    const matches = templateContent.match(/\[([^\]]+)\]/g);
    return matches ? matches.map(match => match.slice(1, -1)) : [];
  }

  // Search functionality
  async searchDocuments(query: string, filters?: {
    document_type?: string;
    status?: string;
  }): Promise<EditorDocument[]> {
    const params = new URLSearchParams({ q: query });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
    }
    
    const response = await apiService.get(`${this.baseUrl}/documents/search?${params}`);
    return response.data;
  }
}

// Export singleton instance
export const editorService = new EditorService();