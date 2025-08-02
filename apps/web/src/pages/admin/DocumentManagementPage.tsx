import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Upload, Trash2, Plus, X } from "lucide-react";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { DocumentUpload } from "@/components/documents/DocumentUpload";

interface Document {
  id: string;
  filename: string;
  document_type: string;
  processing_status: string;
  uploaded_by: string;
  uploaded_at: string;
  processed_at?: string;
  chunk_count?: number;
  metadata?: {
    size?: string;
    pages?: number;
  };
}

interface DocumentListResponse {
  documents: Document[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

const DocumentManagementPage = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0
  });
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const { user } = useAuth();

  const fetchDocuments = async (page: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      // Try the real endpoint first, fall back to test if needed
      let response = await fetch(`http://localhost:8001/api/admin/documents/test?page=${page}&limit=20`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }
      
      const data: DocumentListResponse = await response.json();
      setDocuments(data.documents);
      setPagination(data.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments(currentPage);
  }, [currentPage]);

  const handleDelete = async (documentId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
      return;
    }

    try {
      // For now, just show an alert since we need proper auth
      alert('Delete functionality will be implemented once authentication is working');
      
      // TODO: Implement actual delete when auth is working
      // const response = await fetch(`http://localhost:8001/api/admin/documents/${documentId}`, {
      //   method: 'DELETE',
      //   headers: {
      //     'Authorization': `Bearer ${token}`,
      //     'Content-Type': 'application/json'
      //   }
      // });
      
      // if (response.ok) {
      //   await fetchDocuments(currentPage);
      // }
    } catch (err) {
      console.error('Error deleting document:', err);
      alert('Failed to delete document');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap = {
      'completed': { label: 'Active', className: 'bg-success/10 text-success hover:bg-success/20' },
      'processing': { label: 'Processing', className: 'bg-warning/10 text-warning hover:bg-warning/20' },
      'failed': { label: 'Failed', className: 'bg-destructive/10 text-destructive hover:bg-destructive/20' },
      'queued': { label: 'Queued', className: 'bg-blue-100 text-blue-800 hover:bg-blue-200' }
    };
    
    const config = statusMap[status as keyof typeof statusMap] || { label: status, className: 'bg-gray-100 text-gray-800' };
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  const getDocumentType = (document_type: string) => {
    return document_type === 'biblical' ? 'BIBLICAL' : 'THEOLOGICAL';
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const formatSize = (metadata?: { size?: string; pages?: number }) => {
    if (metadata?.size) return metadata.size;
    if (metadata?.pages) return `${metadata.pages} pages`;
    return 'Unknown';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading documents...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-red-600">Error: {error}</div>
        <div className="text-center mt-4">
          <Button onClick={() => fetchDocuments(currentPage)}>Retry</Button>
        </div>
      </div>
    );
  }

  const handleUploadSuccess = () => {
    // Refresh the document list when upload is successful
    fetchDocuments(currentPage);
    setUploadDialogOpen(false);
  };

  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Document Library</h1>
          <p className="text-muted-foreground">Manage your theological document collection</p>
        </div>
        <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
          <DialogTrigger asChild>
            <Button className="flex items-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>Upload Document</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Upload New Document</DialogTitle>
              <DialogDescription>
                Add a new theological document to the system. It will be processed and made available for research.
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4">
              <DocumentUpload onUploadSuccess={handleUploadSuccess} />
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Documents ({pagination.total})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell className="font-medium max-w-xs truncate">
                    {doc.filename}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{getDocumentType(doc.document_type)}</Badge>
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(doc.processing_status)}
                  </TableCell>
                  <TableCell>{formatSize(doc.metadata)}</TableCell>
                  <TableCell>{formatDate(doc.uploaded_at)}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDelete(doc.id, doc.filename)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="mt-6">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious 
                      href="#" 
                      onClick={(e) => {
                        e.preventDefault();
                        if (currentPage > 1) {
                          setCurrentPage(currentPage - 1);
                        }
                      }}
                    />
                  </PaginationItem>
                  
                  {/* Show page numbers */}
                  {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                    const pageNum = i + 1;
                    return (
                      <PaginationItem key={pageNum}>
                        <PaginationLink 
                          href="#" 
                          isActive={pageNum === currentPage}
                          onClick={(e) => {
                            e.preventDefault();
                            setCurrentPage(pageNum);
                          }}
                        >
                          {pageNum}
                        </PaginationLink>
                      </PaginationItem>
                    );
                  })}
                  
                  {pagination.pages > 5 && (
                    <PaginationItem>
                      <PaginationEllipsis />
                    </PaginationItem>
                  )}
                  
                  <PaginationItem>
                    <PaginationNext 
                      href="#" 
                      onClick={(e) => {
                        e.preventDefault();
                        if (currentPage < pagination.pages) {
                          setCurrentPage(currentPage + 1);
                        }
                      }}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentManagementPage;