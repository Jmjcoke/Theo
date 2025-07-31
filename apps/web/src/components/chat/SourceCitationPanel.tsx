import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChevronRight, ChevronLeft, Search, X } from "lucide-react";
import { DocumentSource } from '@/types/chat';
import SourceCard from './SourceCard';

interface SourceCitationPanelProps {
  sources: DocumentSource[];
  isVisible: boolean;
  onToggle: () => void;
  className?: string;
}

const SourceCitationPanel: React.FC<SourceCitationPanelProps> = ({
  sources,
  isVisible,
  onToggle,
  className = ""
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  // Filter sources based on search term
  const filteredSources = sources.filter(source =>
    source.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    source.excerpt.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (source.citation && source.citation.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const toggleSourceExpansion = (documentId: string) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(documentId)) {
      newExpanded.delete(documentId);
    } else {
      newExpanded.add(documentId);
    }
    setExpandedSources(newExpanded);
  };

  const clearSearch = () => {
    setSearchTerm('');
  };

  return (
    <div 
      className={`bg-card border-l transition-all duration-300 ease-in-out ${
        isVisible ? 'w-80' : 'w-12'
      } ${className}`}
      role="complementary" 
      aria-label="Source citations and references"
    >
      {/* Toggle Button */}
      <div className="h-16 border-b flex items-center justify-center">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          aria-label={isVisible ? "Collapse source panel" : "Expand source panel"}
          className={`p-2 ${!isVisible ? 'hover:bg-accent' : ''}`}
        >
          {isVisible ? (
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          ) : (
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          )}
        </Button>
      </div>

      {/* Collapsed state indicator */}
      {!isVisible && (
        <div 
          className="flex flex-col items-center justify-center h-32 text-muted-foreground space-y-1 cursor-pointer hover:bg-accent/50 transition-colors"
          onClick={onToggle}
          role="button"
          aria-label="Expand sources panel"
        >
          <div className="transform -rotate-90 text-xs font-medium whitespace-nowrap">
            Sources
          </div>
          <div className="text-xs bg-primary/10 rounded-full w-6 h-6 flex items-center justify-center">
            {sources.length}
          </div>
        </div>
      )}

      {/* Panel Content */}
      {isVisible && (
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="flex-shrink-0 p-6 pb-4 border-b">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Sources & References</h3>
              <span className="text-sm text-muted-foreground">
                {filteredSources.length} of {sources.length}
              </span>
            </div>
            
            {/* Search Input */}
            {sources.length > 0 && (
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <Input
                  type="text"
                  placeholder="Search sources..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-10"
                  aria-label="Search through source citations"
                />
                {searchTerm && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearSearch}
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                    aria-label="Clear search"
                  >
                    <X className="h-4 w-4" aria-hidden="true" />
                  </Button>
                )}
              </div>
            )}
          </div>
          
          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto px-6 pb-6">
            {filteredSources.length > 0 ? (
              <div className="space-y-3" role="list" aria-label="Source citations">
                {filteredSources.map((source, index) => (
                  <SourceCard
                    key={source.documentId || `source-${index}`}
                    source={source}
                    isExpanded={expandedSources.has(source.documentId)}
                    onToggleExpansion={() => toggleSourceExpansion(source.documentId)}
                    searchTerm={searchTerm}
                  />
                ))}
              </div>
            ) : sources.length > 0 ? (
              <div className="text-center text-sm text-muted-foreground py-8">
                <Search className="h-8 w-8 mx-auto mb-2 opacity-50" aria-hidden="true" />
                <p>No sources match your search.</p>
                <Button 
                  variant="link" 
                  size="sm" 
                  onClick={clearSearch}
                  className="mt-2"
                >
                  Clear search
                </Button>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">
                <p className="mb-4">Sources will appear here when you receive AI responses.</p>
                <div className="space-y-2">
                  <h4 className="font-medium">Types of sources:</h4>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Scripture references</li>
                    <li>Theological documents</li>
                    <li>Historical sources</li>
                    <li>Church tradition texts</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SourceCitationPanel;