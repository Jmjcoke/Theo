/**
 * Server-Sent Events (SSE) Service for Theo
 * 
 * Handles real-time job status updates via SSE connection to the FastAPI backend.
 * Provides robust connection management with automatic reconnection and error handling.
 */

import type { JobStatusUpdate, SSEEventHandlers } from '@/types/api';

/**
 * SSE Connection Manager
 * 
 * Manages WebSocket-like SSE connections for real-time updates with:
 * - Automatic reconnection on connection loss
 * - Proper cleanup and connection management  
 * - Type-safe event handling
 * - Authentication via query parameters (SSE limitation)
 */
class SSEService {
  private eventSource: EventSource | null = null;
  private reconnectTimer: number | null = null;
  private currentJobId: string | null = null;
  private currentToken: string | null = null;
  private handlers: SSEEventHandlers | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 2000; // 2 seconds
  private isConnecting = false;

  private readonly baseUrl = 'http://localhost:8001';

  /**
   * Connect to SSE endpoint for job status updates
   */
  connect(
    jobId: string, 
    token: string, 
    handlers: SSEEventHandlers
  ): void {
    // Store connection parameters
    this.currentJobId = jobId;
    this.currentToken = token;
    this.handlers = handlers;
    this.maxReconnectAttempts = handlers.reconnectAttempts || 3;
    this.reconnectDelay = handlers.reconnectDelay || 2000;
    this.reconnectAttempts = 0;

    // Clean up existing connection
    this.cleanup();

    // Establish new connection
    this.establishConnection();
  }

  /**
   * Establish SSE connection
   */
  private establishConnection(): void {
    if (this.isConnecting || !this.currentJobId || !this.currentToken) {
      return;
    }

    this.isConnecting = true;

    try {
      // EventSource doesn't support custom headers, so we use query parameters for auth
      const url = `${this.baseUrl}/api/jobs/${this.currentJobId}/events?token=${encodeURIComponent(this.currentToken)}`;
      
      this.eventSource = new EventSource(url);

      // Connection opened
      this.eventSource.onopen = () => {
        console.log('SSE connection established for job:', this.currentJobId);
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        
        if (this.handlers?.onOpen) {
          this.handlers.onOpen();
        }
      };

      // Message received
      this.eventSource.onmessage = (event) => {
        try {
          const update: JobStatusUpdate = JSON.parse(event.data);
          
          console.log('SSE job status update:', update);
          
          if (this.handlers?.onMessage) {
            this.handlers.onMessage(update);
          }

          // Auto-close connection on final states
          if (update.status === 'completed' || update.status === 'failed' || update.status === 'error') {
            console.log('Job reached final state, closing SSE connection');
            this.cleanup();
          }
        } catch (error) {
          console.error('Failed to parse SSE message:', error);
          if (this.handlers?.onError) {
            this.handlers.onError(new Error('Failed to parse server message'));
          }
        }
      };

      // Connection error
      this.eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        this.isConnecting = false;

        if (this.eventSource?.readyState === EventSource.CLOSED) {
          console.log('SSE connection closed by server');
          this.handleConnectionLoss();
        } else if (this.eventSource?.readyState === EventSource.CONNECTING) {
          console.log('SSE connection is reconnecting...');
        } else {
          console.log('SSE connection error, will attempt to reconnect');
          this.handleConnectionLoss();
        }
      };

      // Handle custom event types
      this.eventSource.addEventListener('job_status', (event) => {
        try {
          const update: JobStatusUpdate = JSON.parse(event.data);
          if (this.handlers?.onMessage) {
            this.handlers.onMessage(update);
          }
        } catch (error) {
          console.error('Failed to parse job_status event:', error);
        }
      });

      this.eventSource.addEventListener('error', (event) => {
        console.error('SSE error event:', event);
        if (this.handlers?.onError) {
          this.handlers.onError(new Error('Server sent error event'));
        }
      });

    } catch (error) {
      console.error('Failed to establish SSE connection:', error);
      this.isConnecting = false;
      
      if (this.handlers?.onError) {
        this.handlers.onError(new Error('Failed to connect to server'));
      }
      
      this.handleConnectionLoss();
    }
  }

  /**
   * Handle connection loss and attempt reconnection
   */
  private handleConnectionLoss(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached, giving up');
      
      if (this.handlers?.onError) {
        this.handlers.onError(new Error('Connection failed after multiple attempts'));
      }
      
      this.cleanup();
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = window.setTimeout(() => {
      this.establishConnection();
    }, delay);
  }

  /**
   * Manually reconnect
   */
  reconnect(): void {
    if (this.currentJobId && this.currentToken && this.handlers) {
      this.reconnectAttempts = 0;
      this.establishConnection();
    }
  }

  /**
   * Check if SSE connection is active
   */
  isConnected(): boolean {
    return this.eventSource?.readyState === EventSource.OPEN;
  }

  /**
   * Check if currently connecting
   */
  isConnecting(): boolean {
    return this.isConnecting || this.eventSource?.readyState === EventSource.CONNECTING;
  }

  /**
   * Get current connection state
   */
  getConnectionState(): 'connecting' | 'open' | 'closed' {
    if (!this.eventSource) return 'closed';
    
    switch (this.eventSource.readyState) {
      case EventSource.CONNECTING:
        return 'connecting';
      case EventSource.OPEN:
        return 'open';
      case EventSource.CLOSED:
      default:
        return 'closed';
    }
  }

  /**
   * Clean up SSE connection and resources
   */
  cleanup(): void {
    // Clear reconnection timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Close EventSource connection
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      console.log('SSE connection cleaned up');
    }

    // Call close handler
    if (this.handlers?.onClose) {
      this.handlers.onClose();
    }

    // Reset state
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.currentJobId = null;
    this.currentToken = null;
    this.handlers = null;
  }

  /**
   * Send a ping to test connection (if supported by server)
   */
  ping(): void {
    // SSE is unidirectional, so we can't send data back
    // But we can check connection state
    if (!this.isConnected()) {
      console.log('SSE connection not active, attempting to reconnect');
      this.reconnect();
    }
  }

  /**
   * Get connection statistics
   */
  getStats(): {
    connected: boolean;
    connectionState: string;
    reconnectAttempts: number;
    maxReconnectAttempts: number;
    jobId: string | null;
  } {
    return {
      connected: this.isConnected(),
      connectionState: this.getConnectionState(),
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      jobId: this.currentJobId,
    };
  }
}

// Export singleton instance
export const sseService = new SSEService();

// Export types for convenience
export type { JobStatusUpdate, SSEEventHandlers };

export default sseService;