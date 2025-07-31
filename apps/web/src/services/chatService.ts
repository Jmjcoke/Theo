/**
 * Chat Service for Theo Theological Research System
 * 
 * Specialized service for RAG-powered theological chat interactions.
 * Handles both basic and advanced pipeline routing with source citation management.
 */

import { apiService } from './api';
import type { 
  ChatRequest, 
  ChatResponse, 
  ChatHistory, 
  DocumentSource,
  PaginatedResponse 
} from '@/types/api';

/**
 * Chat conversation context for maintaining dialogue continuity
 */
interface ConversationContext {
  sessionId: string;
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    sources?: DocumentSource[];
  }>;
  totalMessages: number;
  startedAt: string;
}

/**
 * Chat service configuration options
 */
interface ChatServiceConfig {
  defaultMaxResults?: number;
  defaultUseAdvancedPipeline?: boolean;
  contextWindowSize?: number;
  enableConversationHistory?: boolean;
}

/**
 * Enhanced Chat Service with conversation management and context handling
 */
class ChatService {
  private currentConversation: ConversationContext | null = null;
  private config: ChatServiceConfig;

  constructor(config: ChatServiceConfig = {}) {
    this.config = {
      defaultMaxResults: 10,
      defaultUseAdvancedPipeline: true,
      contextWindowSize: 10,
      enableConversationHistory: true,
      ...config
    };
  }

  // ============================================================================
  // CORE CHAT METHODS
  // ============================================================================

  /**
   * Send a chat message with RAG processing
   */
  async sendMessage(
    message: string,
    options: {
      useAdvancedPipeline?: boolean;
      includeContext?: boolean;
      context?: string;
      sessionId?: string;
    } = {}
  ): Promise<ChatResponse> {
    // Ensure we have a session ID
    if (!this.currentConversation && !options.sessionId) {
      this.startNewConversation();
    }

    const sessionId = options.sessionId || this.currentConversation?.sessionId || this.startNewConversation();

    const request: ChatRequest = {
      message: message.trim(),
      sessionId: sessionId,
      useAdvancedPipeline: options.useAdvancedPipeline ?? this.config.defaultUseAdvancedPipeline,
      context: options.context || (options.includeContext ? this.getConversationContextString() : undefined),
    };

    try {
      const response = await apiService.sendChatMessage(request);
      
      // Update conversation context if enabled
      if (this.config.enableConversationHistory) {
        this.updateConversation(message, response);
      }

      return response;
    } catch (error) {
      console.error('Chat service error:', error);
      throw error;
    }
  }

  /**
   * Send message with streaming response (for future implementation)
   */
  async sendMessageStream(
    message: string,
    onChunk: (chunk: string) => void,
    options: {
      useAdvancedPipeline?: boolean;
      maxResults?: number;
    } = {}
  ): Promise<ChatResponse> {
    // For now, fall back to regular send
    // TODO: Implement streaming when backend supports it
    return this.sendMessage(message, options);
  }

  // ============================================================================
  // CONVERSATION MANAGEMENT
  // ============================================================================

  /**
   * Start a new conversation session
   */
  startNewConversation(): string {
    // Generate a proper UUID for backend compatibility
    const sessionId = crypto.randomUUID();
    
    this.currentConversation = {
      sessionId,
      messages: [],
      totalMessages: 0,
      startedAt: new Date().toISOString(),
    };

    return sessionId;
  }

  /**
   * Get current conversation
   */
  getCurrentConversation(): ConversationContext | null {
    return this.currentConversation;
  }

  /**
   * Clear current conversation
   */
  clearConversation(): void {
    this.currentConversation = null;
  }

  /**
   * Update conversation with new message and response
   */
  private updateConversation(userMessage: string, response: ChatResponse): void {
    if (!this.currentConversation) {
      this.startNewConversation();
    }

    if (this.currentConversation) {
      const timestamp = new Date().toISOString();

      // Add user message
      this.currentConversation.messages.push({
        id: `msg_${Date.now()}_user`,
        role: 'user',
        content: userMessage,
        timestamp,
      });

      // Add assistant response
      this.currentConversation.messages.push({
        id: response.messageId,
        role: 'assistant',
        content: response.response,
        timestamp,
        sources: response.sources,
      });

      this.currentConversation.totalMessages += 2;

      // Trim conversation to context window size
      const maxMessages = this.config.contextWindowSize! * 2; // user + assistant pairs
      if (this.currentConversation.messages.length > maxMessages) {
        this.currentConversation.messages = this.currentConversation.messages.slice(-maxMessages);
      }
    }
  }

  /**
   * Get conversation context for next message as a string
   */
  private getConversationContextString(): string {
    if (!this.currentConversation || this.currentConversation.messages.length === 0) {
      return '';
    }

    // Return last few messages as context
    const contextSize = Math.min(6, this.currentConversation.messages.length);
    const recentMessages = this.currentConversation.messages.slice(-contextSize);

    const contextMessages = recentMessages.map(msg => 
      `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
    );

    return contextMessages.join('\n\n');
  }

  // ============================================================================
  // CHAT HISTORY MANAGEMENT
  // ============================================================================

  /**
   * Get chat history from server
   */
  async getChatHistory(
    limit: number = 50,
    offset: number = 0
  ): Promise<PaginatedResponse<ChatHistory>> {
    return apiService.getChatHistory(limit, offset);
  }

  /**
   * Delete all chat history
   */
  async deleteChatHistory(): Promise<void> {
    await apiService.deleteChatHistory();
    this.clearConversation();
  }

  /**
   * Load conversation from chat history
   */
  async loadConversationFromHistory(
    historyItems: ChatHistory[]
  ): Promise<void> {
    if (historyItems.length === 0) return;

    const sessionId = `loaded_${Date.now()}`;
    
    this.currentConversation = {
      sessionId,
      messages: [],
      totalMessages: 0,
      startedAt: historyItems[0]?.created_at || new Date().toISOString(),
    };

    // Convert history items to conversation messages
    historyItems.forEach(item => {
      this.currentConversation!.messages.push(
        {
          id: `${item.id}_user`,
          role: 'user',
          content: item.message,
          timestamp: item.created_at,
        },
        {
          id: `${item.id}_assistant`,
          role: 'assistant',
          content: item.response,
          timestamp: item.created_at,
          sources: item.sources,
        }
      );
    });

    this.currentConversation.totalMessages = this.currentConversation.messages.length;
  }

  // ============================================================================
  // SOURCE CITATION HELPERS
  // ============================================================================

  /**
   * Group sources by document
   */
  groupSourcesByDocument(sources: DocumentSource[]): Map<string, DocumentSource[]> {
    const grouped = new Map<string, DocumentSource[]>();

    sources.forEach(source => {
      const key = source.documentId;
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(source);
    });

    return grouped;
  }

  /**
   * Format sources for display
   */
  formatSourcesForDisplay(sources: DocumentSource[]): Array<{
    document: string;
    filename: string;
    chunks: Array<{
      content: string;
      score: number;
      location?: string;
    }>;
  }> {
    const grouped = this.groupSourcesByDocument(sources);
    const formatted: Array<{
      document: string;
      filename: string;
      chunks: Array<{
        content: string;
        score: number;
        location?: string;
      }>;
    }> = [];

    grouped.forEach((sourcesForDoc, documentId) => {
      const firstSource = sourcesForDoc[0];
      
      formatted.push({
        document: documentId,
        filename: firstSource.title,
        chunks: sourcesForDoc.map(source => ({
          content: source.excerpt,
          score: source.relevance,
          location: source.citation,
        })),
      });
    });

    return formatted.sort((a, b) => {
      // Sort by highest similarity score
      const aMaxScore = Math.max(...a.chunks.map(c => c.score));
      const bMaxScore = Math.max(...b.chunks.map(c => c.score));
      return bMaxScore - aMaxScore;
    });
  }

  /**
   * Format source location (page, chapter, verse, etc.)
   */
  private formatSourceLocation(source: DocumentSource): string | undefined {
    const parts: string[] = [];

    if (source.chapter) {
      parts.push(`Ch. ${source.chapter}`);
    }

    if (source.verse) {
      parts.push(`v. ${source.verse}`);
    }

    if (source.page_number) {
      parts.push(`p. ${source.page_number}`);
    }

    return parts.length > 0 ? parts.join(', ') : undefined;
  }

  /**
   * Get unique document IDs from sources
   */
  getUniqueDocumentIds(sources: DocumentSource[]): string[] {
    const ids = new Set(sources.map(s => s.documentId));
    return Array.from(ids);
  }

  /**
   * Filter sources by relevance threshold
   */
  filterSourcesByThreshold(
    sources: DocumentSource[], 
    threshold: number = 0.7
  ): DocumentSource[] {
    return sources.filter(source => source.relevance >= threshold);
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  /**
   * Validate message content
   */
  validateMessage(message: string): { valid: boolean; error?: string } {
    const trimmed = message.trim();

    if (!trimmed) {
      return { valid: false, error: 'Message cannot be empty' };
    }

    if (trimmed.length > 2000) {
      return { valid: false, error: 'Message too long (max 2000 characters)' };
    }

    return { valid: true };
  }

  /**
   * Get conversation statistics
   */
  getConversationStats(): {
    hasActiveConversation: boolean;
    messageCount: number;
    sessionId: string | null;
    startedAt: string | null;
  } {
    return {
      hasActiveConversation: !!this.currentConversation,
      messageCount: this.currentConversation?.totalMessages || 0,
      sessionId: this.currentConversation?.sessionId || null,
      startedAt: this.currentConversation?.startedAt || null,
    };
  }

  /**
   * Export conversation as markdown
   */
  exportConversationAsMarkdown(): string | null {
    if (!this.currentConversation) return null;

    const lines: string[] = [
      `# Theological Research Conversation`,
      `**Session ID:** ${this.currentConversation.sessionId}`,
      `**Started:** ${new Date(this.currentConversation.startedAt).toLocaleString()}`,
      `**Messages:** ${this.currentConversation.totalMessages}`,
      '',
      '---',
      ''
    ];

    this.currentConversation.messages.forEach((message, index) => {
      const timestamp = new Date(message.timestamp).toLocaleTimeString();
      
      if (message.role === 'user') {
        lines.push(`## Question ${Math.floor(index / 2) + 1} (${timestamp})`);
        lines.push('');
        lines.push(message.content);
        lines.push('');
      } else {
        lines.push(`### Answer (${timestamp})`);
        lines.push('');
        lines.push(message.content);
        lines.push('');

        if (message.sources && message.sources.length > 0) {
          lines.push('#### Sources');
          lines.push('');
          message.sources.forEach((source, i) => {
            lines.push(`${i + 1}. **${source.filename}** (Score: ${source.similarity_score.toFixed(3)})`);
            if (source.page_number) {
              lines.push(`   - Page ${source.page_number}`);
            }
            lines.push(`   - "${source.chunk_content.substring(0, 100)}..."`);
            lines.push('');
          });
        }
        
        lines.push('---');
        lines.push('');
      }
    });

    return lines.join('\n');
  }
}

// Export singleton instance
export const chatService = new ChatService();
export default chatService;