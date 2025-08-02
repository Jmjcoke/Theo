import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { 
  Save, 
  Download, 
  FileText, 
  Settings, 
  History, 
  BookOpen,
  ArrowLeft,
  Loader2,
  Plus,
  Search
} from "lucide-react";
import { Link } from "react-router-dom";
import { editorService } from "@/services/editorService";
import { authService } from "@/services/authService";
import type { EditorDocument, EditorTemplate, DocumentType } from "@/types/editor";

interface DocumentEditorProps {
  documentId?: number;
}

const DocumentEditor: React.FC<DocumentEditorProps> = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  
  // State management
  const [document, setDocument] = useState<EditorDocument | null>(null);
  const [templates, setTemplates] = useState<EditorTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoSaveStatus, setAutoSaveStatus] = useState<'saved' | 'saving' | 'error'>('saved');
  
  // Editor state
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [documentType, setDocumentType] = useState<DocumentType>('article');
  const [wordCount, setWordCount] = useState(0);
  const [readingTime, setReadingTime] = useState(0);
  
  // UI state
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Refs
  const autoSaveTimer = useRef<NodeJS.Timeout | null>(null);

  // Load document or initialize new document
  useEffect(() => {
    const initializeEditor = async () => {
      try {
        setIsLoading(true);
        
        // Load templates
        const templatesData = await editorService.getTemplates();
        setTemplates(templatesData);
        
        if (documentId && documentId !== 'new') {
          // Load existing document
          const docData = await editorService.getDocument(parseInt(documentId));
          setDocument(docData);
          setTitle(docData.title);
          setContent(docData.content);
          setDocumentType(docData.document_type);
          setSelectedTemplate(docData.template_id);
          updateWordCount(docData.content);
        } else {
          // Initialize new document
          setTitle('Untitled Document');
          setContent('');
          
          // Check if content is being imported from chat
          const importedContent = (location.state as any)?.importContent;
          if (importedContent) {
            setTitle(`Theological Research - ${new Date().toLocaleDateString()}`);
            const formattedContent = `<h2>Theological Research Notes</h2>
<h3>Question Asked</h3>
<p><em>From Theo Chat on ${importedContent.timestamp ? new Date(importedContent.timestamp).toLocaleString() : new Date().toLocaleString()}</em></p>
<blockquote>
<p><strong>Question:</strong> [Add the original question here]</p>
</blockquote>

<h3>Theo's Response</h3>
<blockquote>
${importedContent.content}
</blockquote>

${importedContent.sources && importedContent.sources.length > 0 ? `
<h3>Sources Referenced</h3>
<ul>
${importedContent.sources.map((source: any) => `<li><strong>${source.title || source.filename || 'Unknown Source'}:</strong> ${source.excerpt || source.content || 'No excerpt available'} (Relevance: ${source.relevance ? source.relevance.toFixed(2) : 'N/A'})</li>`).join('\n')}
</ul>
` : ''}

<h3>Your Analysis and Notes</h3>
<p>Add your own theological analysis, cross-references, and study notes here...</p>

<h3>Additional Research</h3>
<p>Use this section to expand on the topic with your own research and insights...</p>`;
            setContent(formattedContent);
            updateWordCount(formattedContent);
          } else {
            setShowTemplateSelector(true);
          }
        }
      } catch (err) {
        setError('Failed to load document');
        console.error('Editor initialization error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initializeEditor();
  }, [documentId]);

  // Auto-save functionality
  useEffect(() => {
    if (document && (title !== document.title || content !== document.content)) {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current);
      }
      
      setAutoSaveStatus('saving');
      autoSaveTimer.current = setTimeout(async () => {
        try {
          await handleSave(false); // Silent save
          setAutoSaveStatus('saved');
        } catch (err) {
          setAutoSaveStatus('error');
        }
      }, 3000); // Auto-save after 3 seconds of inactivity
    }

    return () => {
      if (autoSaveTimer.current) {
        clearTimeout(autoSaveTimer.current);
      }
    };
  }, [title, content, document]);

  // Update word count and reading time
  const updateWordCount = (text: string) => {
    // Strip HTML tags for accurate word count
    const plainText = text.replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, ' ');
    const words = plainText.trim().split(/\s+/).filter(word => word.length > 0);
    const count = words.length;
    const time = Math.ceil(count / 200); // Average reading speed
    setWordCount(count);
    setReadingTime(time);
  };

  // Handle content changes
  const handleContentChange = (value: string) => {
    setContent(value);
    updateWordCount(value);
  };

  // Handle template selection with LLM formatting
  const handleTemplateSelect = async (templateId: string) => {
    try {
      setIsLoading(true);
      const template = templates.find(t => t.id === templateId);
      if (template) {
        setSelectedTemplate(templateId);
        setDocumentType(template.document_type);
        
        // If there's existing content, use LLM to format it according to the template
        if (content && content.trim().length > 0) {
          const formattedContent = await editorService.formatContentWithTemplate(
            content,
            templateId,
            title
          );
          setContent(formattedContent);
          updateWordCount(formattedContent);
        } else {
          // If no content, just apply the empty template
          setContent(template.template_content);
          updateWordCount(template.template_content);
        }
        
        setShowTemplateSelector(false);
      }
    } catch (err) {
      setError('Failed to apply template');
      console.error('Template selection error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Save document
  const handleSave = async (showFeedback = true) => {
    try {
      if (showFeedback) setIsSaving(true);
      
      const docData = {
        title,
        content,
        template_id: selectedTemplate,
        document_type: documentType,
        metadata: {
          word_count: wordCount,
          reading_time: readingTime
        }
      };

      let savedDoc;
      if (document) {
        savedDoc = await editorService.updateDocument(document.id, docData);
      } else {
        savedDoc = await editorService.createDocument(docData);
        // Navigate to the new document URL
        navigate(`/editor/${savedDoc.id}`, { replace: true });
      }
      
      setDocument(savedDoc);
      if (showFeedback) {
        // Show success message
        console.log('Document saved successfully');
      }
    } catch (err) {
      setError('Failed to save document');
      throw err;
    } finally {
      if (showFeedback) setIsSaving(false);
    }
  };

  // Export document
  const handleExport = async (format: 'pdf' | 'docx' | 'markdown') => {
    if (!document) {
      setError('Please save the document before exporting');
      return;
    }

    try {
      setIsExporting(true);
      const exportResult = await editorService.exportDocument(document.id, format);
      
      // Poll for export completion
      const pollExport = async () => {
        const status = await editorService.getExportStatus(exportResult.export_id);
        if (status.export_status === 'completed') {
          // Download the file
          window.open(`/api/editor/exports/${exportResult.export_id}/download`, '_blank');
        } else if (status.export_status === 'failed') {
          throw new Error(status.error_message || 'Export failed');
        } else {
          // Continue polling
          setTimeout(pollExport, 2000);
        }
      };
      
      setTimeout(pollExport, 2000);
    } catch (err) {
      setError('Failed to export document');
      console.error('Export error:', err);
    } finally {
      setIsExporting(false);
      setShowExportDialog(false);
    }
  };

  // Handle drag and drop from chat
  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    try {
      const transferData = JSON.parse(event.dataTransfer.getData('application/json'));
      if (transferData.type === 'chat-content') {
        const insertText = `\n\n${transferData.data.content}\n\n`;
        const newContent = content + insertText;
        setContent(newContent);
        updateWordCount(newContent);
        
        // Suggest title if empty
        if (!title || title === 'Untitled Document') {
          setTitle(transferData.data.title || 'Untitled Document');
        }
      }
    } catch (err) {
      console.error('Drop error:', err);
    }
  };


  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading editor...</span>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      {sidebarOpen && (
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Document Tools</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(false)}
              >
                ×
              </Button>
            </div>
            
            {/* Document Stats */}
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="bg-gray-50 p-2 rounded">
                <div className="font-medium">{wordCount}</div>
                <div className="text-gray-600">Words</div>
              </div>
              <div className="bg-gray-50 p-2 rounded">
                <div className="font-medium">{readingTime}m</div>
                <div className="text-gray-600">Read Time</div>
              </div>
            </div>
          </div>

          {/* Templates */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium">Templates</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowTemplateSelector(true)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-2">
              {templates.slice(0, 5).map(template => (
                <button
                  key={template.id}
                  onClick={() => handleTemplateSelect(template.id)}
                  className={`w-full text-left p-2 rounded text-sm hover:bg-gray-50 ${
                    selectedTemplate === template.id ? 'bg-blue-50 border border-blue-200' : ''
                  }`}
                >
                  <div className="font-medium">{template.name}</div>
                  <div className="text-gray-600 text-xs">{template.document_type}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Citations */}
          <div className="p-4 flex-1">
            <h3 className="font-medium mb-2">Citations</h3>
            <div className="text-sm text-gray-600">
              Citations will appear here when you drag content from chat conversations.
            </div>
          </div>
        </div>
      )}

      {/* Main Editor */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link to="/chat">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Chat
                </Button>
              </Link>
              
              {!sidebarOpen && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(true)}
                >
                  <BookOpen className="h-4 w-4 mr-2" />
                  Tools
                </Button>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {/* Auto-save status */}
              <div className="text-sm text-gray-600">
                {autoSaveStatus === 'saving' && 'Saving...'}
                {autoSaveStatus === 'saved' && 'Saved'}
                {autoSaveStatus === 'error' && 'Save failed'}
              </div>

              <Button
                onClick={() => handleSave()}
                disabled={isSaving}
                size="sm"
              >
                {isSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Save
              </Button>

              <Button
                onClick={() => setShowExportDialog(true)}
                disabled={!document || isExporting}
                variant="outline"
                size="sm"
              >
                {isExporting ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Export
              </Button>
            </div>
          </div>
        </div>

        {/* Editor Content */}
        <div 
          className="flex-1 p-6"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <div className="max-w-4xl mx-auto">
            {/* Title Input */}
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Document title..."
              className="text-2xl font-bold border-none p-0 mb-6 focus:ring-0"
            />

            {/* Simple Textarea Editor */}
            <textarea
              value={content.replace(/<[^>]*>/g, '')} // Strip HTML tags for display
              onChange={(e) => handleContentChange(e.target.value)}
              placeholder="Start writing your document...

You can drag content from chat conversations directly into this editor."
              className="w-full h-96 p-4 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              style={{
                fontFamily: '-apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif',
                fontSize: '14px',
                lineHeight: '1.6'
              }}
            />
          </div>
        </div>
      </div>

      {/* Template Selector Modal */}
      {showTemplateSelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Select a Template</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map(template => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template.id)}
                    className="text-left p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="font-medium mb-2">{template.name}</div>
                    <div className="text-sm text-gray-600 mb-2">{template.description}</div>
                    <Badge variant="outline">{template.document_type}</Badge>
                  </button>
                ))}
              </div>
              <div className="flex justify-end mt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowTemplateSelector(false)}
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Export Dialog */}
      {showExportDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Export Document</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button
                  onClick={() => handleExport('pdf')}
                  className="w-full justify-start"
                  variant="outline"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Export as PDF
                </Button>
                <Button
                  onClick={() => handleExport('docx')}
                  className="w-full justify-start"
                  variant="outline"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Export as Word Document
                </Button>
                <Button
                  onClick={() => handleExport('markdown')}
                  className="w-full justify-start"
                  variant="outline"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Export as Markdown
                </Button>
              </div>
              <div className="flex justify-end mt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowExportDialog(false)}
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-4 text-white hover:text-gray-200"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentEditor;