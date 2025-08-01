import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileText, Users, Upload, CheckCircle } from "lucide-react";

const AdminDashboard = () => {
  const stats = [
    {
      title: "Total Documents",
      value: "1,204",
      icon: FileText,
      description: "Theological texts indexed"
    },
    {
      title: "Active Users",
      value: "89",
      icon: Users,
      description: "Registered researchers"
    },
    {
      title: "Recent Uploads",
      value: "23",
      icon: Upload,
      description: "This week"
    },
    {
      title: "System Status",
      value: "Healthy",
      icon: CheckCircle,
      description: "All systems operational"
    }
  ];

  const recentActivity = [
    {
      filename: "Augustine_Confessions.pdf",
      status: "Processed",
      uploadDate: "2024-01-15"
    },
    {
      filename: "Aquinas_Summa_Theologica.pdf",
      status: "Processing",
      uploadDate: "2024-01-14"
    },
    {
      filename: "Calvin_Institutes.pdf",
      status: "Processed",
      uploadDate: "2024-01-14"
    },
    {
      filename: "Luther_95_Theses.pdf",
      status: "Failed",
      uploadDate: "2024-01-13"
    },
    {
      filename: "Barth_Church_Dogmatics.pdf",
      status: "Processed",
      uploadDate: "2024-01-12"
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Activity Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Upload Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentActivity.map((activity, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">
                    {activity.filename}
                  </TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      activity.status === "Processed" 
                        ? "bg-success/10 text-success" 
                        : activity.status === "Processing"
                        ? "bg-warning/10 text-warning"
                        : "bg-destructive/10 text-destructive"
                    }`}>
                      {activity.status}
                    </span>
                  </TableCell>
                  <TableCell>{activity.uploadDate}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;