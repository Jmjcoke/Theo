import React from 'react';
import { Button } from "@/components/ui/button";
import { ArrowLeft, AlertCircle, StopCircle, RotateCcw, FileText } from "lucide-react";
import { Link } from "react-router-dom";
import { Alert, AlertDescription } from "@/components/ui/alert";
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import SourceCitationPanel from './SourceCitationPanel';
import EditorPanel from './EditorPanel';
import type { Message } from '@/types/chat';
import { useChatStore } from '@/stores/chatStore';

interface ChatInterfaceProps {
  onSendMessage: (message: string) => Promise<void>;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sessionId: string;
  onCancelRequest: () => void;
  onClearChat: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onSendMessage,
  messages,
  isLoading,
  error,
  sessionId,
  onCancelRequest,
  onClearChat
}) => {
  const { 
    sourcePanelState, 
    toggleSourcePanel, 
    getLatestSources,
    editorPanelState,
    toggleEditorPanel,
    toggleEditorPanelCollapse,
    updateEditorContent,
    exportAsMarkdown,
    exportAsPDF,
    undoFormatting,
    clearEditorContent
  } = useChatStore();
  
  const latestSources = getLatestSources();

  return (
    <div className="min-h-screen bg-background" role="application" aria-label="Chat interface">
      {/* Header */}
      <header className="h-16 bg-card border-b flex items-center justify-between px-6" role="banner">
        <div className="flex items-center space-x-4">
          <Link to="/dashboard">
            <Button variant="ghost" size="sm" aria-label="Return to dashboard">
              <ArrowLeft className="h-4 w-4 mr-2" aria-hidden="true" />
              Back to Dashboard
            </Button>
          </Link>
          <h1 className="text-xl font-bold text-primary">Theo Chat</h1>
        </div>
        <div className="flex items-center space-x-4" aria-label="Connection status and session information">
          {/* Chat Controls */}
          <div className="flex items-center space-x-2">
            {isLoading && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={onCancelRequest}
                aria-label="Stop current request"
                className="text-destructive hover:text-destructive"
              >
                <StopCircle className="h-4 w-4 mr-2" aria-hidden="true" />
                Stop
              </Button>
            )}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onClearChat}
              aria-label="Clear chat and start new session"
            >
              <RotateCcw className="h-4 w-4 mr-2" aria-hidden="true" />
              Clear
            </Button>
          </div>

          {/* Status */}
          <div className="flex items-center space-x-2">
            <div 
              className={`w-2 h-2 rounded-full ${error ? 'bg-destructive' : 'bg-green-500'}`}
              aria-hidden="true"
            ></div>
            <span className="text-sm text-muted-foreground">
              {error ? 'Offline' : 'Online'}
            </span>
            <span className="text-xs text-muted-foreground" aria-label={`Session ID: ${sessionId}`}>
              Session: {sessionId.slice(-8)}
            </span>
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="p-4" role="alert">
          <Alert variant="destructive" className="max-w-4xl mx-auto">
            <AlertCircle className="h-4 w-4" aria-hidden="true" />
            <AlertDescription>
              {typeof error === 'string' ? error : 'An error occurred while processing your request. Please try again.'}
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Main Content Area with Responsive Layout */}
      <div className="flex flex-col lg:flex-row h-[calc(100vh-4rem)]">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <div className="flex-1 flex flex-col" role="main">
            <MessageList messages={messages} />
            <MessageInput 
              onSendMessage={onSendMessage} 
              isLoading={isLoading}
              disabled={!!error}
            />
          </div>
        </div>

        {/* Mobile Bottom Panel for Editor (sm and below) */}
        <div className={`lg:hidden transition-all duration-300 ${
          editorPanelState.isVisible 
            ? editorPanelState.isCollapsed 
              ? 'h-12' 
              : 'h-96' 
            : 'h-0'
        } border-t overflow-hidden`}>
          <EditorPanel
            content={editorPanelState.content}
            onContentChange={updateEditorContent}
            onExportMarkdown={exportAsMarkdown}
            onExportPDF={exportAsPDF}
            isExporting={editorPanelState.isExporting}
            exportError={editorPanelState.exportError}
            isVisible={editorPanelState.isVisible}
            isCollapsed={editorPanelState.isCollapsed}
            onToggleVisibility={toggleEditorPanel}
            onToggleCollapse={toggleEditorPanelCollapse}
            isFormatting={editorPanelState.isFormatting}
            lastFormattingApplied={editorPanelState.lastFormattingApplied}
            hasUnsavedChanges={editorPanelState.hasUnsavedChanges}
            onUndoFormatting={undoFormatting}
            onClearContent={clearEditorContent}
            className="h-full"
          />
        </div>

        {/* Desktop Side Panels (lg and above) */}
        <div className="hidden lg:flex">
          {/* Editor Panel */}
          <div className={`transition-all duration-300 ${
            editorPanelState.isVisible 
              ? editorPanelState.isCollapsed 
                ? 'w-12' 
                : 'w-96' 
              : 'w-0'
          } overflow-hidden`}>
            <EditorPanel
              content={editorPanelState.content}
              onContentChange={updateEditorContent}
              onExportMarkdown={exportAsMarkdown}
              onExportPDF={exportAsPDF}
              isExporting={editorPanelState.isExporting}
              exportError={editorPanelState.exportError}
              isVisible={editorPanelState.isVisible}
              isCollapsed={editorPanelState.isCollapsed}
              onToggleVisibility={toggleEditorPanel}
              onToggleCollapse={toggleEditorPanelCollapse}
              isFormatting={editorPanelState.isFormatting}
              lastFormattingApplied={editorPanelState.lastFormattingApplied}
              hasUnsavedChanges={editorPanelState.hasUnsavedChanges}
              onUndoFormatting={undoFormatting}
              onClearContent={clearEditorContent}
              className="h-full"
            />
          </div>

          {/* Source Citation Panel */}
          <div className={`transition-all duration-300 h-full ${
            sourcePanelState.isVisible ? 'w-80' : 'w-0'
          } overflow-hidden`}>
            <SourceCitationPanel
              sources={latestSources}
              isVisible={sourcePanelState.isVisible}
              onToggle={toggleSourcePanel}
              className="h-full"
            />
          </div>
        </div>

        {/* Floating Sources Toggle Button (always available when sources exist) */}
        {latestSources.length > 0 && (
          <div className="fixed bottom-4 right-4 z-50 lg:bottom-6 lg:right-6">
            <Button
              onClick={toggleSourcePanel}
              className="rounded-full w-14 h-14 shadow-lg"
              aria-label={`Toggle ${latestSources.length} source citations`}
              title={`Toggle ${latestSources.length} source citations`}
            >
              <FileText className="h-6 w-6" />
              <span className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full w-6 h-6 flex items-center justify-center">
                {latestSources.length}
              </span>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;