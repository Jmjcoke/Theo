/**
 * Editor Service
 * Handles API communication for document editor functionality
 */

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
  private documents: Map<number, EditorDocument> = new Map();
  private nextDocumentId = 1;

  // Mock templates data
  private defaultTemplates: EditorTemplate[] = [
    {
      id: '1',
      name: 'Research Paper',
      description: 'Academic research paper with citations',
      template_content: '<h1>[Title]</h1>\n<h2>Abstract</h2>\n<p>[Abstract content]</p>\n<h2>Introduction</h2>\n<p>[Introduction content]</p>\n<h2>Methodology</h2>\n<p>[Methodology content]</p>\n<h2>Results</h2>\n<p>[Results content]</p>\n<h2>Discussion</h2>\n<p>[Discussion content]</p>\n<h2>Conclusion</h2>\n<p>[Conclusion content]</p>\n<h2>References</h2>\n<p>[References will be automatically added from citations]</p>',
      document_type: 'article',
      metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '2',
      name: 'Theological Essay',
      description: 'Structured theological essay format',
      template_content: '<h1>[Title]</h1>\n<h2>Introduction</h2>\n<p>[Introduce the theological topic and your thesis]</p>\n<h2>Biblical Foundation</h2>\n<p>[Present relevant biblical passages and their interpretation]</p>\n<h2>Historical Context</h2>\n<p>[Discuss historical and theological context]</p>\n<h2>Contemporary Application</h2>\n<p>[Apply the theological concepts to modern contexts]</p>\n<h2>Conclusion</h2>\n<p>[Summarize your argument and implications]</p>',
      document_type: 'essay',
      metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    {
      id: '3',
      name: 'Study Notes',
      description: 'Simple note-taking template',
      template_content: '<h1>[Study Topic]</h1>\n<h2>Key Points</h2>\n<ul>\n<li>[Point 1]</li>\n<li>[Point 2]</li>\n<li>[Point 3]</li>\n</ul>\n<h2>Questions</h2>\n<ul>\n<li>[Question 1]</li>\n<li>[Question 2]</li>\n</ul>\n<h2>Additional Notes</h2>\n<p>[Your notes here]</p>',
      document_type: 'notes',
      metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  ];

  // Document operations
  async getDocuments(filters?: {
    document_type?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<EditorDocument[]> {
    // Return empty array for now since we're using localStorage
    return [];
  }

  async getDocument(id: number): Promise<EditorDocument> {
    const doc = this.documents.get(id);
    if (!doc) {
      throw new Error(`Document ${id} not found`);
    }
    return doc;
  }

  async createDocument(document: CreateDocumentRequest): Promise<EditorDocument> {
    const now = new Date().toISOString();
    const newDoc: EditorDocument = {
      id: this.nextDocumentId++,
      title: document.title,
      content: document.content,
      document_type: document.document_type,
      template_id: document.template_id,
      status: 'draft',
      created_at: now,
      updated_at: now,
      metadata: document.metadata || {}
    };
    
    this.documents.set(newDoc.id, newDoc);
    return newDoc;
  }

  async updateDocument(id: number, document: UpdateDocumentRequest): Promise<EditorDocument> {
    const existingDoc = this.documents.get(id);
    if (!existingDoc) {
      throw new Error(`Document ${id} not found`);
    }
    
    const updatedDoc: EditorDocument = {
      ...existingDoc,
      ...document,
      updated_at: new Date().toISOString()
    };
    
    this.documents.set(id, updatedDoc);
    return updatedDoc;
  }

  async deleteDocument(id: number): Promise<void> {
    this.documents.delete(id);
  }

  // Template operations
  async getTemplates(documentType?: string): Promise<EditorTemplate[]> {
    if (documentType) {
      return this.defaultTemplates.filter(t => t.document_type === documentType);
    }
    return this.defaultTemplates;
  }

  async getTemplate(id: string): Promise<EditorTemplate> {
    const template = this.defaultTemplates.find(t => t.id === id);
    if (!template) {
      throw new Error(`Template ${id} not found`);
    }
    return template;
  }

  async createTemplate(template: {
    name: string;
    description?: string;
    template_content: string;
    document_type: string;
    metadata?: any;
  }): Promise<EditorTemplate> {
    // Mock implementation - in a real app this would save to backend
    throw new Error('Template creation not implemented in demo version');
  }

  // Export operations - simplified mock versions
  async exportDocument(
    documentId: number, 
    format: 'pdf' | 'docx' | 'markdown',
    options?: {
      include_citations?: boolean;
      custom_styling?: any;
    }
  ): Promise<{ export_id: number; status: string; message: string }> {
    // Mock export - in a real app this would trigger actual export
    return {
      export_id: Math.floor(Math.random() * 1000),
      status: 'completed',
      message: 'Export completed successfully'
    };
  }

  async getExportStatus(exportId: number): Promise<ExportStatus> {
    // Mock export status
    return {
      export_id: exportId,
      export_status: 'completed',
      file_url: '/mock/download/url',
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString()
    };
  }

  // Citation management - simplified mock versions
  async getCitations(documentId: number): Promise<Citation[]> {
    // Return empty citations array for mock
    return [];
  }

  async addCitation(documentId: number, citation: {
    source_id: string;
    citation_text: string;
    position_start?: number;
    position_end?: number;
    citation_format?: string;
  }): Promise<Citation> {
    // Mock citation creation
    return {
      id: Math.floor(Math.random() * 1000),
      document_id: documentId,
      source_id: citation.source_id,
      citation_text: citation.citation_text,
      position_start: citation.position_start,
      position_end: citation.position_end,
      citation_format: citation.citation_format || 'apa',
      created_at: new Date().toISOString()
    };
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

  // LLM-powered template formatting
  async formatContentWithTemplate(
    existingContent: string, 
    templateId: string,
    title?: string
  ): Promise<string> {
    try {
      const template = await this.getTemplate(templateId);
      
      const response = await fetch('http://localhost:8001/api/editor/format-template', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('theo_auth_token')}`,
        },
        body: JSON.stringify({
          content: existingContent,
          template_type: template.document_type,
          template_name: template.name,
          template_structure: template.description,
          title: title
        })
      });
      
      if (!response.ok) {
        throw new Error(`Template formatting failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      return result.formatted_content;
    } catch (error) {
      console.error('Template formatting error:', error);
      // Fallback to basic template application
      const template = await this.getTemplate(templateId);
      return this.applyTemplate(template.template_content, { Title: title || 'Document Title' });
    }
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