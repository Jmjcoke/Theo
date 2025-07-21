import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Upload, Trash2 } from "lucide-react";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

const DocumentManagementPage = () => {
  const documents = [
    {
      filename: "Augustine_Confessions.pdf",
      type: "PDF",
      status: "Active",
      date: "2024-01-15",
      size: "2.4 MB"
    },
    {
      filename: "Aquinas_Summa_Theologica.pdf",
      type: "PDF",
      status: "Processing",
      date: "2024-01-14",
      size: "15.7 MB"
    },
    {
      filename: "Calvin_Institutes.pdf",
      type: "PDF",
      status: "Active",
      date: "2024-01-14",
      size: "8.2 MB"
    },
    {
      filename: "Luther_95_Theses.pdf",
      type: "PDF",
      status: "Failed",
      date: "2024-01-13",
      size: "0.5 MB"
    },
    {
      filename: "Barth_Church_Dogmatics.pdf",
      type: "PDF",
      status: "Active",
      date: "2024-01-12",
      size: "25.1 MB"
    },
    {
      filename: "Wesley_Sermons.docx",
      type: "DOCX",
      status: "Active",
      date: "2024-01-11",
      size: "3.8 MB"
    },
    {
      filename: "Edwards_Religious_Affections.pdf",
      type: "PDF",
      status: "Active",
      date: "2024-01-10",
      size: "4.2 MB"
    },
    {
      filename: "Bonhoeffer_Cost_of_Discipleship.pdf",
      type: "PDF",
      status: "Active",
      date: "2024-01-09",
      size: "6.5 MB"
    },
    {
      filename: "Spurgeon_Treasury_of_David.pdf",
      type: "PDF",
      status: "Processing",
      date: "2024-01-08",
      size: "18.9 MB"
    },
    {
      filename: "Owen_Glory_of_Christ.pdf",
      type: "PDF",
      status: "Active",
      date: "2024-01-07",
      size: "2.1 MB"
    }
  ];

  const handleUpload = () => {
    // TODO: Implement upload logic
    console.log("Upload document clicked");
  };

  const handleDelete = (filename: string) => {
    // TODO: Implement delete logic
    console.log("Deleting document:", filename);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Active":
        return <Badge className="bg-success/10 text-success hover:bg-success/20">Active</Badge>;
      case "Processing":
        return <Badge className="bg-warning/10 text-warning hover:bg-warning/20">Processing</Badge>;
      case "Failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Document Library</h1>
          <p className="text-muted-foreground">Manage your theological document collection</p>
        </div>
        <Button onClick={handleUpload} className="flex items-center space-x-2">
          <Upload className="h-4 w-4" />
          <span>Upload Document</span>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Documents ({documents.length})</CardTitle>
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
              {documents.map((doc, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium max-w-xs truncate">
                    {doc.filename}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{doc.type}</Badge>
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(doc.status)}
                  </TableCell>
                  <TableCell>{doc.size}</TableCell>
                  <TableCell>{doc.date}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDelete(doc.filename)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          <div className="mt-6">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious href="#" />
                </PaginationItem>
                <PaginationItem>
                  <PaginationLink href="#" isActive>
                    1
                  </PaginationLink>
                </PaginationItem>
                <PaginationItem>
                  <PaginationLink href="#">2</PaginationLink>
                </PaginationItem>
                <PaginationItem>
                  <PaginationLink href="#">3</PaginationLink>
                </PaginationItem>
                <PaginationItem>
                  <PaginationEllipsis />
                </PaginationItem>
                <PaginationItem>
                  <PaginationNext href="#" />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentManagementPage;