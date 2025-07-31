import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, ArrowLeft, BookOpen, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { chatService } from "@/services/chatService";
import { authService } from "@/services/authService";
import type { DocumentSource } from "@/types/api";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: DocumentSource[];
  isLoading?: boolean;
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      type: "assistant",
      content: "Hello! I'm Theo, your theological research assistant. I can help you explore scripture, church history, systematic theology, and more from our library of 200+ theological documents. What would you like to discuss today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    // Validate message
    const validation = chatService.validateMessage(input);
    if (!validation.valid) {
      setError(validation.error || 'Invalid message');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    // Add loading message
    const loadingMessage: Message = {
      id: `loading_${Date.now()}`,
      type: "assistant",
      content: "Searching through 200+ theological documents...",
      timestamp: new Date(),
      isLoading: true
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Send message to RAG system
      const response = await chatService.sendMessage(input, {
        useAdvancedPipeline: true,
        includeContext: true
      });

      // Remove loading message and add real response
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isLoading);
        return [...filtered, {
          id: response.messageId,
          type: "assistant",
          content: response.response,
          timestamp: new Date(),
          sources: response.sources
        }];
      });

    } catch (error) {
      console.error('Chat error:', error);
      setError('Failed to get response. Please try again.');
      
      // Remove loading message and add error message
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isLoading);
        return [...filtered, {
          id: `error_${Date.now()}`,
          type: "assistant",
          content: "I apologize, but I'm having trouble connecting to the theological research system. Please check your connection and try again.",
          timestamp: new Date()
        }];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // Clear conversation
  const handleClearConversation = () => {
    chatService.clearConversation();
    setMessages([{
      id: "welcome",
      type: "assistant",
      content: "Hello! I'm Theo, your theological research assistant. I can help you explore scripture, church history, systematic theology, and more from our library of 200+ theological documents. What would you like to discuss today?",
      timestamp: new Date()
    }]);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 bg-card border-b flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <Link to="/admin">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Admin
              </Button>
            </Link>
            <h1 className="text-xl font-bold text-primary">Theo Chat</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleClearConversation}
              disabled={isLoading}
            >
              Clear Chat
            </Button>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-success rounded-full"></div>
              <span className="text-sm text-muted-foreground">Online</span>
            </div>
          </div>
        </header>

        {/* Chat Messages */}
        <div className="flex-1 flex flex-col">
          <ScrollArea className="flex-1 p-6">
            <div className="space-y-4 max-w-4xl mx-auto">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`flex max-w-[80%] ${
                      message.type === "user" ? "flex-row-reverse" : "flex-row"
                    }`}
                  >
                    <div
                      className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        message.type === "user"
                          ? "bg-primary text-primary-foreground ml-3"
                          : "bg-secondary text-secondary-foreground mr-3"
                      }`}
                    >
                      {message.type === "user" ? (
                        <User className="w-4 h-4" />
                      ) : (
                        <Bot className="w-4 h-4" />
                      )}
                    </div>
                    <div
                      className={`rounded-lg p-3 ${
                        message.type === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      <div className="prose prose-sm max-w-none">
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      </div>
                      
                      {/* Sources Display */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border/20">
                          <div className="flex items-center text-xs font-medium text-muted-foreground mb-2">
                            <BookOpen className="w-3 h-3 mr-1" />
                            Sources ({message.sources.length})
                          </div>
                          <div className="space-y-2">
                            {chatService.formatSourcesForDisplay(message.sources).slice(0, 3).map((source, idx) => (
                              <div key={idx} className="text-xs bg-background/50 rounded p-2">
                                <div className="font-medium text-foreground mb-1">
                                  {source.filename}
                                </div>
                                {source.chunks.map((chunk, chunkIdx) => (
                                  <div key={chunkIdx} className="mb-1">
                                    <div className="text-muted-foreground">
                                      "{chunk.content.substring(0, 100)}..."
                                    </div>
                                    {chunk.location && (
                                      <div className="text-xs text-muted-foreground mt-1">
                                        {chunk.location} • Score: {chunk.score.toFixed(2)}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            ))}
                            {message.sources.length > 3 && (
                              <div className="text-xs text-muted-foreground">
                                +{message.sources.length - 3} more sources
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      <p className="text-xs opacity-70 mt-2">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>

          {/* Error Display */}
          {error && (
            <div className="border-t bg-destructive/10 border-destructive/20 p-3">
              <div className="max-w-4xl mx-auto text-sm text-destructive">
                {error}
              </div>
            </div>
          )}

          {/* Chat Input */}
          <div className="border-t p-4">
            <div className="max-w-4xl mx-auto flex space-x-4">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about theology, scripture, church history..."
                className="flex-1"
                disabled={isLoading}
              />
              <Button 
                onClick={handleSend} 
                disabled={!input.trim() || isLoading}
              >
                {isLoading ? (
                  <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            {input.length > 1800 && (
              <div className="max-w-4xl mx-auto mt-2 text-xs text-muted-foreground">
                {2000 - input.length} characters remaining
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - Editor & Source Panel */}
      <div className="w-80 bg-card border-l">
        <Card className="h-full rounded-none border-0">
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <BookOpen className="w-5 h-5 mr-2" />
              Sources & References
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(() => {
              // Get all sources from recent messages
              const allSources = messages
                .filter(msg => msg.sources && msg.sources.length > 0)
                .flatMap(msg => msg.sources!)
                .slice(-10); // Show last 10 sources

              if (allSources.length === 0) {
                return (
                  <div className="text-sm text-muted-foreground">
                    <p>Sources will appear here as you chat with Theo.</p>
                    <div className="mt-4 p-3 bg-muted/50 rounded">
                      <p className="font-medium mb-2">Available in our library:</p>
                      <ul className="text-xs space-y-1">
                        <li>• 200+ Theological Documents</li>
                        <li>• Complete Bible (66 books)</li>
                        <li>• Systematic Theology</li>
                        <li>• Church History</li>
                        <li>• Biblical Commentaries</li>
                      </ul>
                    </div>
                  </div>
                );
              }

              const uniqueSources = Array.from(
                new Map(allSources.map(s => [s.documentId, s])).values()
              );

              return (
                <div>
                  <div className="text-sm text-muted-foreground mb-3">
                    Recent sources from this conversation:
                  </div>
                  <ScrollArea className="h-96">
                    <div className="space-y-2">
                      {uniqueSources.map((source, idx) => (
                        <div key={idx} className="p-2 bg-muted/50 rounded text-xs">
                          <div className="font-medium text-foreground mb-1">
                            {source.title}
                          </div>
                          <div className="text-muted-foreground mb-2">
                            "{source.excerpt.substring(0, 120)}..."
                          </div>
                          <div className="flex justify-between items-center text-xs">
                            {source.citation && (
                              <span className="text-muted-foreground">
                                {source.citation}
                              </span>
                            )}
                            <span className="text-muted-foreground">
                              Score: {source.relevance.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              );
            })()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ChatInterface;